import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 4 章：微氣候散熱與複合環境衝擊", page_icon="🌡️", layout="wide")

# 緊湊化版面與高亮度發光數據卡 CSS
st.markdown("""
<style>
  .block-container { padding-top: 3.5rem !important; padding-bottom: 1rem !important; }
    .bright-card {
        background: linear-gradient(145deg, #0F172A, #1E293B);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 12px 16px;
        color: #F8FAFC !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 8px;
    }
    .bright-title {
        color: #E2E8F0 !important;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .bright-val-red { color: #FF5252 !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-val-orange { color: #FB923C !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-val-green { color: #00E676 !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-val-cyan { color: #00E5FF !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-sub { color: #94A3B8 !important; font-size: 0.82rem; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：研究起點與資料架構引導 ====================
st.markdown("### 第四章：【考驗】真實案場微氣候：Faiman 熱力學與環境複合衝擊")
st.info(
    "🌟 **【研究資料基石】** 在進入第四章的微氣候模擬前，我們必須先掌握真實世界數位孿生的**三大資料源（Data Acquisition Architecture）**：\n"
    "1. **現場 IoT 感測器**：日射計（量測 $G_{\text{POA}}$）、PT100 背板熱電偶（量測真實 $T_{\text{cell}}$）、超音波風速計（量測 $v_w$）。\n"
    "2. **氣象與衛星 Open Data**：中央氣象署（CWA）測站氣溫雨量、NASA POWER 衛星逐時輻照度。\n"
    "3. **環境空氣品質 Open Data**：環境部（MOENV）逐時 $\text{PM}_{2.5}$ 濃度（推估氣膠消光與面板積塵率）。"
)

# ==================== 核心熱力學與複合環境計算函數 ====================
def calc_faiman_and_environmental_impact(poa, t_amb, wind_speed, u0, u1, gamma_pct, condition_mode, pm25_val, p_stc_kw=215.0):
    """
    計算 Faiman 溫度、PM2.5 積塵透光率損耗、降雨洗塵效益與最終實際發電功率
    """
    poa_arr = np.atleast_1d(poa).astype(float)
    t_amb_arr = np.atleast_1d(t_amb).astype(float)
    v_arr = np.atleast_1d(wind_speed).astype(float)

    # 1. 基礎 Faiman 熱力學溫度
    u_total = u0 + u1 * v_arr
    delta_t_wind = poa_arr / np.maximum(u_total, 1e-4)
    t_cell_base = t_amb_arr + delta_t_wind

    # 2. 複合微氣候修正 (PM2.5 積塵與鹽霧效應)
    # PM2.5 偏高時，面板表面累積塵垢，不僅阻擋光子（穿透率下降），還會阻礙散熱（溫度額外上升 2~5°C）
    soiling_loss_factor = np.clip(pm25_val / 150.0 * 0.06, 0.0, 0.08) # 最高可造成 8% 功率損失
    t_cell_actual = t_cell_base + (pm25_val / 50.0) if condition_mode == "🌫️ 中南部秋冬 PM2.5 積塵" else t_cell_base

    # 若為雨後初晴，雨水瞬間降溫並洗淨灰塵，溫度扣除 8°C 且積塵歸零
    if condition_mode == "🌧️ 午後雷陣雨過後（瞬間降溫與洗塵）":
        t_cell_actual = np.maximum(t_amb_arr + 2.0, t_cell_actual - 8.0)
        soiling_loss_factor = 0.005 # 接近完全乾淨

    # 理想無溫損功率 (假設 25°C 且 100% 潔淨)
    p_ideal = p_stc_kw * (poa_arr / 1000.0)

    # 溫度衰減與積塵損耗合成
    temp_diff_stc = t_cell_actual - 25.0
    temp_loss_factor = np.where(poa_arr > 1.0, (gamma_pct / 100.0) * temp_diff_stc, 0.0)
    
    # 總發電效率係數 = (1 + 溫度損耗) * (1 - 積塵損耗)
    total_efficiency_ratio = np.clip((1.0 + temp_loss_factor) * (1.0 - soiling_loss_factor), 0.1, 1.2)
    p_actual = p_ideal * total_efficiency_ratio

    return t_cell_actual, delta_t_wind, u_total, p_ideal, p_actual, temp_loss_factor * 100.0, soiling_loss_factor * 100.0


def get_thermal_color(t_cell_val):
    """根據面板溫度回傳熱像儀色彩"""
    ratio = float(np.clip((t_cell_val - 25.0) / 48.0, 0.0, 1.0))
    if ratio < 0.25:
        return '#2563EB'
    elif ratio < 0.50:
        return '#10B981'
    elif ratio < 0.72:
        return '#F59E0B'
    elif ratio < 0.88:
        return '#EA580C'
    else:
        return '#DC2626'


def build_3d_faiman_stage(poa, t_amb, wind_speed, u0, u1, gamma_pct, condition_mode, pm25_val, camera_mode):
    """建構 3D 微氣候風場與面板熱對流舞台"""
    t_c_arr, dt_arr, ut_arr, pid_arr, pac_arr, tloss_arr, sloss_arr = calc_faiman_and_environmental_impact(
        poa, t_amb, wind_speed, u0, u1, gamma_pct, condition_mode, pm25_val
    )
    t_cell = float(t_c_arr.flat[0])
    delta_t = float(dt_arr.flat[0])
    u_total = float(ut_arr.flat[0])
    p_ideal = float(pid_arr.flat[0])
    p_actual = float(pac_arr.flat[0])
    t_loss_pct = float(tloss_arr.flat[0])
    s_loss_pct = float(sloss_arr.flat[0])

    panel_color = get_thermal_color(t_cell)

    fig = go.Figure()

    # [Trace 0] 案場地面底座
    xg, yg = np.meshgrid(np.linspace(-1.6, 1.6, 12), np.linspace(-1.0, 1.0, 12))
    fig.add_trace(go.Surface(
        x=xg, y=yg, z=np.zeros_like(xg),
        opacity=0.35, showscale=False,
        colorscale=[[0, '#1E293B'], [1, '#334155']],
        hoverinfo='skip', name='案場地面'
    ))

    # [Trace 1] 支架立柱
    fig.add_trace(go.Scatter3d(
        x=[-0.55, -0.55, None, 0.55, 0.55, None, -0.55, -0.55, None, 0.55, 0.55],
        y=[-0.22, -0.22, None, -0.22, -0.22, None, 0.28, 0.28, None, 0.28, 0.28],
        z=[0.0, 0.14, None, 0.0, 0.14, None, 0.0, 0.36, None, 0.0, 0.36],
        mode='lines', line=dict(color='#94A3B8', width=8),
        showlegend=False, hoverinfo='skip'
    ))

    # [Trace 2] 3D 太陽能光電面板
    px = [-0.85, 0.85, 0.85, -0.85]
    py = [-0.32, -0.32, 0.38, 0.38]
    pz = [0.12, 0.12, 0.40, 0.40]
    fig.add_trace(go.Mesh3d(
        x=px, y=py, z=pz,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=panel_color, opacity=0.92,
        name=f'🌡️ 面板熱像 ({t_cell:.1f}°C)',
        showlegend=True
    ))

    # [Trace 3] 環境與微氣候標籤
    fig.add_trace(go.Scatter3d(
        x=[0.0, -1.35, 1.25],
        y=[-0.40, 0.0, 0.0],
        z=[0.78, 0.24, 0.52],
        mode='text+markers',
        marker=dict(size=[24, 1, 1], color=['#FFEA00', '#00E5FF', '#FF5252']),
        text=[
            f"<b>☀️ 入射陽光 G = {poa:.0f} W/m²</b>",
            f"<b>💨 風速 v = {wind_speed:.1f} m/s (氣溫 {t_amb:.1f}°C)<br>微氣候情境：{condition_mode}</b>",
            f"<b>♨️ 散熱係數 U = {u_total:.1f} W/m²K<br>PM2.5 濃度 = {pm25_val:.0f} μg/m³</b>"
        ],
        textposition="top center",
        textfont=dict(size=12, color=['#FFEA00', '#00E5FF', '#FB923C']),
        showlegend=False
    ))

    # [Trace 4] 狀態告示牌
    fig.add_trace(go.Scatter3d(
        x=[0.0], y=[0.05], z=[0.48],
        mode='text',
        text=[f"<b>【{condition_mode}】Tcell = {t_cell:.1f}°C ｜ 溫損：{t_loss_pct:+.2f}% ｜ 積塵損耗：-{s_loss_pct:.2f}%</b>"],
        textfont=dict(size=13, color='#FFFFFF'),
        showlegend=False
    ))

    # [動態 Trace 5] 動態粒子流
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[0.0, -0.8, 0.2], y=[0.0, 0.0, 0.0], z=[0.6, 0.22, 0.45],
        mode='markers',
        marker=dict(size=[12, 11, 13], color=['#FFEA00', '#00E5FF', '#FF5252'], symbol='circle'),
        name='⚡ 動態粒子 (黃:陽光 / 藍:涼風 / 紅:熱羽流)'
    ))

    # 動畫影格
    frames = []
    n_steps = 20
    total_cycles = 6
    wind_factor = 0.6 + 0.4 * (wind_speed / 8.0)

    for f_i in range(n_steps * total_cycles):
        prog = (f_i % n_steps) / float(n_steps)
        p_t = (prog * 2.0) % 1.0
        ph_x = [-0.55 + 0.36 * k for k in range(4)]
        ph_y = [-0.38 * (1 - p_t) + 0.02 * p_t for _ in range(4)]
        ph_z = [0.74 * (1 - p_t) + 0.26 * p_t for _ in range(4)]

        w_x, w_y, w_z, w_col, w_sz = [], [], [], [], []
        for k in range(6):
            u_w = (prog * wind_factor + k / 6.0) % 1.0
            cur_wx = -1.35 + 2.60 * u_w
            cur_wy = -0.18 if (k % 2 == 0) else 0.18
            cur_wz = (0.12 + 0.14 * u_w) if (k % 2 == 0) else (0.22 + 0.18 * u_w)
            w_x.append(cur_wx)
            w_y.append(cur_wy)
            w_z.append(cur_wz)
            if cur_wx < -0.15:
                w_col.append('#00E5FF')
                w_sz.append(10)
            elif cur_wx < 0.45:
                w_col.append('#FBBF24')
                w_sz.append(12)
            else:
                w_col.append('#FF5252')
                w_sz.append(13)

        th_x, th_y, th_z = [], [], []
        for k in range(4):
            u_th = (prog + 0.25 * k) % 1.0
            th_x.append(-0.45 + 0.30 * k + 0.25 * (wind_speed / 10.0) * u_th)
            th_y.append(0.05)
            th_z.append(0.28 + 0.32 * u_th)

        all_x = ph_x + w_x + th_x
        all_y = ph_y + w_y + th_y
        all_z = ph_z + w_z + th_z
        all_cols = ['#FFEA00']*4 + w_col + ['#FB923C']*4
        all_sizes = [11]*4 + w_sz + [11]*4

        frames.append(go.Frame(
            name=f"ThermLoop_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=all_x, y=all_y, z=all_z,
                mode='markers',
                marker=dict(size=all_sizes, color=all_cols, symbol='circle')
            )]
        ))

    fig.frames = frames

    if "案場工程師視角" in camera_mode:
        cam_eye = dict(x=0.0, y=-1.68, z=0.38)
        cam_center = dict(x=0.0, y=0.0, z=0.16)
    else:
        cam_eye = dict(x=-0.95, y=-1.45, z=0.32)
        cam_center = dict(x=0.0, y=0.0, z=0.16)

    fig.update_layout(
        title=dict(
            text=f"<b>🌡️ 面板溫度：{t_cell:.1f}°C ｜ 微氣候：{condition_mode} ｜ ⚡ 實發：{p_actual:.1f} kW</b>",
            font=dict(size=15, color="#FFD700"), x=0.02, y=0.96
        ),
        height=430,
        margin=dict(l=0, r=0, b=10, t=50),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.65, 1.65]),
            yaxis=dict(visible=False, range=[-1.0, 1.0]),
            zaxis=dict(visible=False, range=[-0.02, 0.88]),
            aspectmode='manual', aspectratio=dict(x=1.55, y=0.9, z=0.65),
            camera=dict(eye=cam_eye, center=cam_center),
            bgcolor='#0E1117'
        ),
        legend=dict(
            orientation="h", yanchor="top", y=0.90, xanchor="left", x=0.02,
            font=dict(color="white", size=11), bgcolor="rgba(15, 23, 42, 0.75)"
        ),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.98, y=0.98, xanchor="right", yanchor="top", direction="left",
            pad=dict(r=5, t=0), bgcolor="#2563EB", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(
                    label="🔄 點此循環播放熱對流",
                    method="animate",
                    args=[None, dict(frame=dict(duration=85, redraw=True), transition=dict(duration=0), fromcurrent=False, mode="immediate")]
                ),
                dict(
                    label="⏸️ 暫停",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )]
    )

    return fig, t_cell, delta_t, u_total, p_ideal, p_actual, t_loss_pct, s_loss_pct

# ==================== 上半部主舞台：左 2x2 緊湊控制台 + 右 3D 舞台 ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="medium")

with col_ctrl:
    st.markdown("##### 🎥 1. 選擇 3D 觀察視角（含學習導讀）")
    camera_mode = st.radio(
        "選擇 3D 觀察視角",
        [
            "🧍 案場工程師視角 (由南向北仰望面板熱像與風場)",
            "🚁 背板風道側視特寫 (觀察冷風穿過支架下方散熱)"
        ],
        index=0,
        label_visibility="collapsed"
    )

    if "案場工程師視角" in camera_mode:
        st.caption(
            "💡 **視角導讀（🧍 案場工程師視角）**：站在面板正前方！點擊右圖右上角 **🔄 循環播放**，"
            "觀察 **💨左側藍風** 掠過發燙面板後吸熱變成 **♨️右側紅風**。"
        )
    else:
        st.caption(
            "💡 **視角導讀（🚁 背板風道側視特寫）**：從側面觀察為什麼高架支架比屋頂緊貼型更涼爽——"
            "因為面板下方留有通風走道，微風能同時從上下兩面帶走熱量！"
        )

    st.markdown("##### 🌬️ 2. 微氣候與 Faiman 散熱參數 (連動下方公式)")
    r1_c1, r1_c2 = st.columns([1.15, 1.0])
    with r1_c1:
        mount_type = st.selectbox(
            "🏗️ 支架安裝通風型態",
            [
                "🌬️ 地面高架通風型 (U0=25, U1=6.84)",
                "🏠 屋頂平行架設型 (U0=20, U1=4.50)",
                "🔥 屋頂緊貼悶熱型 (U0=15, U1=2.00)"
            ],
            index=0
        )
    mount_map = {
        "🌬️ 地面高架通風型 (U0=25, U1=6.84)": (25.0, 6.84),
        "🏠 屋頂平行架設型 (U0=20, U1=4.50)": (20.0, 4.50),
        "🔥 屋頂緊貼悶熱型 (U0=15, U1=2.00)": (15.0, 2.00)
    }
    u0_val, u1_val = mount_map[mount_type]

    with r1_c2:
        therm_time_options = [f"{h:02d}:{m:02d}" for h in range(6, 19) for m in [0, 15, 30, 45] if not (h == 18 and m > 0)]
        selected_t4_str = st.selectbox("⏰ 定格觀察時刻", therm_time_options, index=24)
        th4, tm4 = map(int, selected_t4_str.split(":"))
        hour_t4 = float(th4) + float(tm4) / 60.0

    sun_bell = max(0.0, np.sin(np.pi * (hour_t4 - 5.5) / 13.0))
    default_poa = int(np.clip(int(round((900.0 * (sun_bell ** 1.15)) / 25.0) * 25), 50, 1000))

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        wind_speed = st.slider("💨 案場風速 v (m/s)", 0.0, 10.0, 1.5, step=0.5)
    with r2_c2:
        t_amb = st.slider("🌡️ 環境氣溫 Tamb (°C)", 15.0, 40.0, 32.0, step=1.0)

    # 台灣真實複合微氣候情境切換選單（對接 Open Data 變數）
    condition_mode = st.selectbox(
        "🇹🇼 台灣真實微氣候與環境衝擊情境",
        [
            "☀️ 標準晴朗無風 (Faiman 基準)",
            "🌫️ 中南部秋冬 PM2.5 積塵 (伴隨輕微熱阻)",
            "🌊 沿海鹽霧結晶 (高濕度與表面結垢)",
            "🌧️ 午後雷陣雨過後（瞬間降溫與洗塵）"
        ],
        index=0
    )
    pm25_val = 120.0 if "PM2.5" in condition_mode else (40.0 if "鹽霧" in condition_mode else 15.0)

    r3_c1, r3_c2 = st.columns(2)
    with r3_c1:
        poa_now = st.slider("☀️ 入射陽光 G (W/m²)", 50, 1000, default_poa, step=25)
    with r3_c2:
        gamma_pct = st.slider("📉 溫度係數 γ (%/°C)", -0.50, -0.25, -0.40, step=0.05)

with col_stage:
    fig_3d_therm, t_cell, delta_t, u_total, p_ideal, p_actual, t_loss_pct, s_loss_pct = build_3d_faiman_stage(
        poa_now, t_amb, wind_speed, u0_val, u1_val, gamma_pct, condition_mode, pm25_val, camera_mode
    )
    st.plotly_chart(fig_3d_therm, use_container_width=True, key="faiman_3d_stage")

# ==================== 中段：高亮度即時數據卡 ＋ 三大熱力學物理公式導讀 ====================
_, _, _, _, p_zero_wind_arr, _, _ = calc_faiman_and_environmental_impact(
    poa_now, t_amb, 0.0, u0_val, u1_val, gamma_pct, condition_mode, pm25_val
)
p_wind_saved = p_actual - float(p_zero_wind_arr.flat[0])

f1, f2, f3 = st.columns(3, gap="medium")

with f1:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🌡️ ① 太陽能板真實工作溫度 (Faiman 模型)</div>
        <div class="bright-val-red">{t_cell:.1f} °C <span style="font-size:1rem;color:#FFD700;font-weight:600;">｜ 溫升 +{delta_t:.1f}°C</span></div>
        <div class="bright-sub">環境氣溫：{t_amb:.1f}°C ｜ 總散熱係數 U = {u_total:.1f} W/(m²·K)</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【① Faiman (2008) 穩態熱平衡模型】** 納入國際標準 IEC 61853-2，計算陽光加熱與風速對流散熱的平衡：")
        st.latex(r"T_{\text{cell}} = T_{\text{amb}} + \frac{G_{\text{POA}}}{U_0 + U_1 \cdot v_w}")
        st.latex(rf"T_{{\text{{cell}}}} = \color{{orange}}{{{t_amb:.1f}}} + \frac{{\color{{gold}}{{{poa_now:.0f}}}}}{{{u0_val:.0f} + {u1_val:.2f}\times\color{{deepskyblue}}{{{wind_speed:.1f}}}}} = \color{{red}}{{{t_cell:.1f}^\circ\text{{C}}}}")

with f2:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">📉 ② 高溫熱衰減與環境積塵損耗</div>
        <div class="bright-val-orange">{t_loss_pct:+.2f} % <span style="font-size:1rem;color:#FF5252;font-weight:600;">｜ 積塵損耗 -{s_loss_pct:.2f}%</span></div>
        <div class="bright-sub">情境：{condition_mode} ｜ 功率溫度係數 γ = {gamma_pct:.2f}%/°C</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【② 溫度與環境複合衰減係數】** 當溫度高於 $25^\\circ\\text{C}$ 或遭遇 PM2.5 積塵時，實際產出遭到雙重打折：")
        st.latex(r"P_{\text{actual}} = P_{\text{ideal}} \times [1 + \gamma(T_{\text{cell}} - 25)] \times (1 - \text{Soiling})")
        st.latex(rf"\text{{溫損}} = \color{{orange}}{{{gamma_pct:.2f}\%}} \times ({t_cell:.1f}-25) = \color{{red}}{{{t_loss_pct:+.2f}\%}}")

with f3:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">⚡ ③ 實際發電功率 vs 案場微風救援效益</div>
        <div class="bright-val-green">{p_actual:.1f} kW <span style="font-size:1rem;color:#00E5FF;font-weight:600;">｜ 💨 微風多救回 +{p_wind_saved:.1f} kW</span></div>
        <div class="bright-sub">25°C 理想功率：{p_ideal:.1f} kW ｜ 無風悶燒時僅剩：{float(p_zero_wind_arr.flat[0]):.1f} kW</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【③ 微風對流的經濟價值】** 調節風速 $v_w$，觀察對流散熱如何將高溫熱能帶走，保全電廠發電營收：")
        st.latex(r"P_{\text{saved}} = P_{\text{actual}}(v = v_w) - P_{\text{actual}}(v = 0)")
        st.latex(rf"P_{{\text{{actual}}}} = \color{{limegreen}}{{{p_actual:.1f}\text{{ kW}}}}, \quad P_{{\text{{saved}}}} = \color{{cyan}}{{+{p_wind_saved:.1f}\text{{ kW}}}}")

# ==================== 底部：左解說導引 (1.0) + 右高挑白底曲線圖 (1.85) ====================
st.markdown("---")
col_guide, col_curve = st.columns([1.0, 1.85], gap="large")

t_day = np.linspace(5.5, 18.5, 131)
sun_profile = np.maximum(0.0, np.sin(np.pi * (t_day - 5.5) / 13.0))
poa_day = 920.0 * np.power(sun_profile, 1.15)
t_amb_day = (t_amb - 5.0) + 6.0 * np.sin(np.pi * (t_day - 6.0) / 14.0)

t_cell_wind_d, _, _, p_ideal_d, p_actual_wind_d, _, _ = calc_faiman_and_environmental_impact(
    poa_day, t_amb_day, wind_speed, u0_val, u1_val, gamma_pct, condition_mode, pm25_val
)
t_cell_zero_d, _, _, _, p_actual_zero_d, _, _ = calc_faiman_and_environmental_impact(
    poa_day, t_amb_day, 0.0, u0_val, u1_val, gamma_pct, condition_mode, pm25_val
)

dt_hr = float(t_day[1] - t_day[0])
kwh_ideal = float(np.sum(p_ideal_d) * dt_hr)
kwh_wind = float(np.sum(p_actual_wind_d) * dt_hr)
kwh_zero = float(np.sum(p_actual_zero_d) * dt_hr)

with col_guide:
    with st.container(border=True):
        st.markdown("#### 📖 「正午發電熱衰減」觀圖導引")
        st.markdown(
            "為什麼太陽能電廠在春、秋季晴天的單日最高發電功率，常贏過炎熱盛夏正午？請對照右側曲線：\n\n"
            "1. **🔵 理想功率 vs 🔴 無風悶燒**：\n"
            "   * 正午陽光最強，若無風散熱，面板溫度飆破 $70^\\circ\\text{C}$，山頂被硬生生「削掉一大塊」。\n"
            "2. **🟢 微風散熱救援**：\n"
            "   * 當案場有微風吹拂（當前設定 **$v = " + f"{wind_speed:.1f}" + "\\text{ m/s}$**），對流散熱將山頂向上托舉，搶回大片綠色救援面積！\n"
            "3. **🇹🇼 台灣在地環境衝擊**：\n"
            "   * 切換上方選單的 **PM2.5 積塵** 或 **沿海鹽霧**，你會看到整體發電曲線因灰塵與熱阻而向下平移，這正是第五章 AI 殘差修正的由來！"
        )
        st.info(
            f"📊 **今日全廠（1,000 m²）累積發電量比對**：\n"
            f"* 🔵 25°C 理想無溫損：**{kwh_ideal:.0f} kWh**\n"
            f"* 🟢 當前微氣候實發：**{kwh_wind:.0f} kWh**\n"
            f"* 🔴 完全無風悶燒：**{kwh_zero:.0f} kWh**\n"
            f"👉 **微風散熱今日多救回：+{kwh_wind - kwh_zero:.0f} 度電（kWh）！**"
        )

with col_curve:
    fig_curve = go.Figure()

    fig_curve.add_trace(go.Scatter(
        x=t_day, y=p_actual_zero_d, mode='lines',
        line=dict(color='#DC2626', width=3),
        fill='tozeroy', fillcolor='rgba(220, 38, 38, 0.12)',
        name=f'🔴 無風悶燒實發 (v=0m/s：{kwh_zero:.0f} kWh)'
    ))

    fig_curve.add_trace(go.Scatter(
        x=t_day, y=p_actual_wind_d, mode='lines',
        line=dict(color='#059669', width=4),
        fill='tonexty', fillcolor='rgba(16, 185, 129, 0.28)',
        name=f'🟢 微氣候實發 (v={wind_speed:.1f}m/s：{kwh_wind:.0f} kWh)'
    ))

    fig_curve.add_trace(go.Scatter(
        x=t_day, y=p_ideal_d, mode='lines',
        line=dict(color='#1D4ED8', width=3, dash='dash'),
        fill='tonexty', fillcolor='rgba(245, 158, 11, 0.18)',
        name=f'🔵 25°C 理想無溫損 (STC：{kwh_ideal:.0f} kWh)'
    ))

    fig_curve.add_vline(
        x=hour_t4, line_width=2.5, line_dash="dot", line_color="#7C3AED",
        annotation_text=f"<b>⏰ 定格時刻 {selected_t4_str} (面板 {t_cell:.1f}°C)</b>",
        annotation_position="top left",
        annotation_font=dict(color="#7C3AED", size=13)
    )

    fig_curve.update_layout(
        title=dict(
            text="<b>📊 全日發電功率溫度衝擊對決：見證正午高溫削峰與微風散熱救援面積！</b>",
            font=dict(size=16, color="#0F172A"),
            x=0.02, y=0.96
        ),
        xaxis=dict(
            title=dict(text="<b>太陽時間 (小時)</b>", font=dict(color="#1E293B", size=13)),
            tickfont=dict(color="#334155", size=12),
            gridcolor="#E2E8F0", zerolinecolor="#CBD5E1",
            dtick=2
        ),
        yaxis=dict(
            title=dict(text="<b>電廠輸出功率 (kW)</b>", font=dict(color="#1E293B", size=13)),
            tickfont=dict(color="#334155", size=12),
            gridcolor="#E2E8F0", zerolinecolor="#CBD5E1",
            range=[0, max(230.0, float(np.max(p_ideal_d)) * 1.15)]
        ),
        height=450,
        margin=dict(l=60, r=25, t=85, b=50),
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#F8FAFC',
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0.0,
            font=dict(color="#0F172A", size=11.5),
            bgcolor="rgba(241, 245, 249, 0.92)",
            bordercolor="#CBD5E1", borderwidth=1
        )
    )
    st.plotly_chart(fig_curve, use_container_width=True)

# ==================== 第四章專屬：學術基石、工程迷思與模型盲區專欄 ====================
st.markdown("---")
st.markdown("### ⚖️ 第四章學術思辨：Faiman 模型的物理盲區與台灣複合微氣候挑戰")
b_col1, b_col2, b_col3 = st.columns(3, gap="medium")

with b_col1:
    with st.container(border=True):
        st.markdown("##### 📜 1. 公式溯源與物理假設")
        st.markdown(
            "* **學術出處**：本章核心採用 **David Faiman (2008)** 發表於 *Progress in Photovoltaics* 的經典穩態熱平衡方程式，並被納入 **IEC 61853-2** 國際標準。\n"
            "* **核心假設**：假設模組背面與空氣的熱交換呈現線性組合（$U_0 + U_1 v_w$）。\n"
            "* **適用邊界**：適用於無遮蔽、風速穩定的戶外地面型案場初步熱評估。"
        )

with b_col2:
    with st.container(border=True):
        st.markdown("##### 🚨 2. 模型盲區與真實幻覺")
        st.markdown(
            "* **熱慣性延遲（Thermal Inertia）**：當雲層瞬間遮蔽太陽時，$G_{\text{POA}}$ 驟降，但厚重玻璃與鋁框具備蓄熱性，Faiman 穩態公式會高估面板冷卻速度。\n"
            "* **風向盲區**：Faiman 僅將風速 $v_w$ 納入計算，卻忽略了**「迎風夾角（Wind Attack Angle）」**——側風與迎風對散熱效率的影響可相差 $30\%$ 以上。"
        )

with b_col3:
    with st.container(border=True):
        st.markdown("##### 🧭 3. 台灣在地挑戰與第五章預告")
        st.markdown(
            "* **複合微氣候殘差**：台灣西海岸的**鹽霧結晶**與中南部的 **PM2.5 積塵**，會造成物理公式無法預期的發電暗損。\n"
            "* **AI 殘差修正預告**：正因為純物理公式無法完美捕捉這些動態殘差，我們將在 **第五章引入機器學習（XGBoost）**，以 Open Data 為特徵來學習並修正物理模型的盲區！"
        )
