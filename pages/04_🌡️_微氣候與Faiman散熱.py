import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 4 章：微氣候散熱與 Faiman 模型", page_icon="🌡️", layout="wide")

# 緊湊化版面與高亮度發光數據卡 CSS（與第 1~3 章 100% 視覺統一）
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; }
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

# ==================== 頂部：故事引導 ====================
st.markdown("### 第四章：【考驗】微氣候散熱與 Faiman 熱力學模型（光能餘熱 ➔ 面板溫升）")
st.info(
    "🌟 **【故事引導】** 在上一章我們發現，太陽能板只能把約 **21%** 的陽光轉成電力，剩下高達 **79%** 的光能全變成了**「熱能」**留在矽晶圓裡！"
    "可怕的是，半導體裡的自由電子最怕熱——**面板每超過標準溫度（25°C）1 度，發電效率就會往下掉約 0.35% ~ 0.45%！**\n\n"
    "這就是為什麼正午大太陽下，面板摸起來燙手（可達 65°C 以上），發電量反而大打折扣；而此時吹來的一陣**「案場微風」**，竟成了拯救電廠發電量的超級英雄！"
)

# ==================== 核心熱力學與發電計算函數 ====================
def calc_faiman_temperature_and_power(poa, t_amb, wind_speed, u0, u1, gamma_pct, p_stc_kw=215.0):
    """
    使用 Faiman (2008) 熱力學模型計算太陽能板工作溫度 T_cell 與溫度修正後功率
    poa: 入射輻照度 W/m^2
    t_amb: 環境氣溫 °C
    wind_speed: 風速 m/s
    u0: 自然對流與輻射散熱係數 W/(m^2·K)
    u1: 強制對流（風速）散熱係數 W/(m^2·K)/(m/s)
    gamma_pct: 功率溫度係數 %/°C (如 -0.40)
    p_stc_kw: 1,000 m^2 案場於 STC (1000 W/m^2, 25°C) 之額定功率 kW
    """
    poa_arr = np.atleast_1d(poa).astype(float)
    t_amb_arr = np.atleast_1d(t_amb).astype(float)
    v_arr = np.atleast_1d(wind_speed).astype(float)

    # Faiman 模型：T_cell = T_amb + POA / (U0 + U1 * v)
    u_total = u0 + u1 * v_arr
    delta_t_wind = poa_arr / np.maximum(u_total, 1e-4)
    t_cell = t_amb_arr + delta_t_wind

    # 理想無溫損功率 (假設恆溫 25°C)
    p_ideal = p_stc_kw * (poa_arr / 1000.0)

    # 溫度衰減因子 (相對於 STC 25°C)
    temp_diff_stc = t_cell - 25.0
    loss_factor = np.where(poa_arr > 1.0, (gamma_pct / 100.0) * temp_diff_stc, 0.0)
    # 實際功率
    p_actual = p_ideal * np.clip(1.0 + loss_factor, 0.2, 1.3)
    return t_cell, delta_t_wind, u_total, p_ideal, p_actual, loss_factor * 100.0


def get_thermal_color(t_cell_val):
    """根據面板溫度 (25°C ~ 75°C) 回傳直覺的熱像儀色彩 (藍 -> 綠 -> 黃 -> 橘 -> 紅)"""
    ratio = float(np.clip((t_cell_val - 25.0) / 48.0, 0.0, 1.0))
    if ratio < 0.25:
        return '#2563EB'  # 涼爽深藍 (25~37°C)
    elif ratio < 0.50:
        return '#10B981'  # 溫和翠綠 (37~49°C)
    elif ratio < 0.72:
        return '#F59E0B'  # 偏熱琥珀橘 (49~59°C)
    elif ratio < 0.88:
        return '#EA580C'  # 高溫深橘紅 (59~67°C)
    else:
        return '#DC2626'  # 嚴重發燒火紅 (>67°C)


def build_3d_faiman_stage(poa, t_amb, wind_speed, u0, u1, gamma_pct, camera_mode):
    """建構無閃爍 WebGL 3D 微氣候風場與面板熱對流舞台 (循環播放鈕置於右上角)"""
    t_c_arr, dt_arr, ut_arr, pid_arr, pac_arr, lpct_arr = calc_faiman_temperature_and_power(
        poa, t_amb, wind_speed, u0, u1, gamma_pct
    )
    t_cell = float(t_c_arr.flat[0])
    delta_t = float(dt_arr.flat[0])
    u_total = float(ut_arr.flat[0])
    p_ideal = float(pid_arr.flat[0])
    p_actual = float(pac_arr.flat[0])
    loss_pct = float(lpct_arr.flat[0])

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

    # [Trace 1] 太陽能板支架立柱
    fig.add_trace(go.Scatter3d(
        x=[-0.55, -0.55, None, 0.55, 0.55, None, -0.55, -0.55, None, 0.55, 0.55],
        y=[-0.22, -0.22, None, -0.22, -0.22, None, 0.28, 0.28, None, 0.28, 0.28],
        z=[0.0, 0.14, None, 0.0, 0.14, None, 0.0, 0.36, None, 0.0, 0.36],
        mode='lines', line=dict(color='#94A3B8', width=8),
        showlegend=False, hoverinfo='skip'
    ))

    # [Trace 2] 3D 太陽能光電面板 (隨溫度動態改變熱像儀顏色！)
    # 面板中心在 (0, 0.03)，寬 X: -0.85 ~ +0.85，長 Y: -0.32 ~ +0.38，高度 Z: 0.12 (南側低) ~ 0.40 (北側高)
    px = [-0.85, 0.85, 0.85, -0.85]
    py = [-0.32, -0.32, 0.38, 0.38]
    pz = [0.12, 0.12, 0.40, 0.40]
    fig.add_trace(go.Mesh3d(
        x=px, y=py, z=pz,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=panel_color, opacity=0.92,
        name=f'🌡️ 太陽能板熱像 (當前 {t_cell:.1f}°C)',
        showlegend=True
    ))

    # [Trace 3] 高空太陽與環境資訊地標 (高度精準控制，不擠壓底部)
    fig.add_trace(go.Scatter3d(
        x=[0.0, -1.35, 1.25],
        y=[-0.40, 0.0, 0.0],
        z=[0.78, 0.24, 0.52],
        mode='text+markers',
        marker=dict(size=[24, 1, 1], color=['#FFEA00', '#00E5FF', '#FF5252']),
        text=[
            f"<b>☀️ 入射陽光 G = {poa:.0f} W/m²</b>",
            f"<b>💨 涼風吹入 v = {wind_speed:.1f} m/s<br>(環境氣溫 {t_amb:.1f}°C)</b>",
            f"<b>♨️ 帶走面板餘熱！<br>散熱係數 U = {u_total:.1f} W/m²K</b>"
        ],
        textposition="top center",
        textfont=dict(size=12, color=['#FFEA00', '#00E5FF', '#FB923C']),
        showlegend=False
    ))

    # [Trace 4] 面板正上方即時溫度與效率狀態牌
    status_emoji = "🔥 高溫警戒" if t_cell >= 60.0 else ("⚠️ 溫升偏高" if t_cell >= 48.0 else "✅ 散熱良好")
    fig.add_trace(go.Scatter3d(
        x=[0.0], y=[0.05], z=[0.48],
        mode='text',
        text=[f"<b>【{status_emoji}】面板工作溫度 Tcell = {t_cell:.1f}°C (較氣溫高 +{delta_t:.1f}°C) ｜ 熱衰減：{loss_pct:.2f}%</b>"],
        textfont=dict(size=13, color='#FFFFFF'),
        showlegend=False
    ))

    # [動態 Trace 5] 三合一動態粒子：☀️ 金色入射光子 + 💨 藍色冷風對流粒子 + ♨️ 橘紅上升熱羽流
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[0.0, -0.8, 0.2], y=[0.0, 0.0, 0.0], z=[0.6, 0.22, 0.45],
        mode='markers',
        marker=dict(size=[12, 11, 13], color=['#FFEA00', '#00E5FF', '#FF5252'], symbol='circle'),
        name='⚡ 動態粒子 (黃:陽光 / 藍:涼風 / 紅:散熱氣流)'
    ))

    # 建立多週期無縫循環動畫 (120 影格 = 6 週期連續循環)
    frames = []
    n_steps = 20
    total_cycles = 6
    # 風速越快，風場粒子跨距與視覺速度越明顯
    wind_factor = 0.6 + 0.4 * (wind_speed / 8.0)

    for f_i in range(n_steps * total_cycles):
        prog = (f_i % n_steps) / float(n_steps)

        # 1. 金色陽光光子：從上方太陽 (y=-0.40, z=0.75) 俯衝打向面板表面 (z=0.26)
        p_t = (prog * 2.0) % 1.0
        ph_x = [-0.55 + 0.36 * k for k in range(4)]
        ph_y = [-0.38 * (1 - p_t) + 0.02 * p_t for _ in range(4)]
        ph_z = [0.74 * (1 - p_t) + 0.26 * p_t for _ in range(4)]

        # 2. 藍色涼風粒子：從左側 (x=-1.35) 穿過面板上下表面與背板風道流向右側 (x=+1.25)
        w_x, w_y, w_z, w_col, w_sz = [], [], [], [], []
        for k in range(6):
            u_w = (prog * wind_factor + k / 6.0) % 1.0
            cur_wx = -1.35 + 2.60 * u_w
            # 分成兩股風道：一股走面板下方背板風道 (z=0.10~0.24)，一股走面板上方表面 (z=0.20~0.38)
            cur_wy = -0.18 if (k % 2 == 0) else 0.18
            cur_wz = (0.12 + 0.14 * u_w) if (k % 2 == 0) else (0.22 + 0.18 * u_w)
            w_x.append(cur_wx)
            w_y.append(cur_wy)
            w_z.append(cur_wz)
            # 經過面板 (x > -0.1) 後，涼風吸熱變成橘紅色熱風！
            if cur_wx < -0.15:
                w_col.append('#00E5FF')  # 吸熱前：冰晶藍涼風
                w_sz.append(10)
            elif cur_wx < 0.45:
                w_col.append('#FBBF24')  # 吸熱中：溫熱黃風
                w_sz.append(12)
            else:
                w_col.append('#FF5252')  # 吸熱後：帶走熱量的紅熱氣流
                w_sz.append(13)

        # 3. 面板表面自然對流上升熱羽流 (Thermal Plume，當風速低時往上飄散的紅橘色熱氣)
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

    # 設定攝影機視角 (確保 center.z = 0.16 置中上提，絕不壓在畫面底部)
    if "案場工程師視角" in camera_mode:
        cam_eye = dict(x=0.0, y=-1.68, z=0.38)
        cam_center = dict(x=0.0, y=0.0, z=0.16)
    else:
        # 散熱氣流側視特寫 (從南偏東側觀察背板下方的通風散熱走道)
        cam_eye = dict(x=-0.95, y=-1.45, z=0.32)
        cam_center = dict(x=0.0, y=0.0, z=0.16)

    fig.update_layout(
        title=dict(
            text=f"<b>🌡️ 面板溫度：{t_cell:.1f}°C (溫升 +{delta_t:.1f}°C) ｜ 💨 風速：{wind_speed:.1f} m/s ｜ ⚡ 實發：{p_actual:.1f} kW</b>",
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
        # 播放與暫停按鈕固定於右上角 (x=0.98, y=0.98)，100% 不遮擋模型
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

    return fig, t_cell, delta_t, u_total, p_ideal, p_actual, loss_pct

# ==================== 上半部主舞台：左 2x2 緊湊控制台 (1.05) + 右 3D 散熱舞台 (2.25) 齊平同框 ====================
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
            "💡 **視角導讀（🧍 案場工程師視角）**：站在面板正前方仰望！點擊右圖右上角 **🔄 循環播放**，"
            "觀察 **💨左側藍風** 掠過發燙面板後吸熱變成 **♨️右側紅風**，並試著把下方風速拉到 0 觀察面板變紅發燒！"
        )
    else:
        st.caption(
            "💡 **視角導讀（🚁 背板風道側視特寫）**：從側面觀察為什麼**「地面高架型支架」比「貼屋頂型」更涼爽**——"
            "因為面板下方留有通風走道，微風能同時從上下兩面把熱量帶走！"
        )

    st.markdown("##### 🌬️ 2. 微氣候與 Faiman 散熱參數 (連動下方公式)")
    r1_c1, r1_c2 = st.columns([1.15, 1.0])
    with r1_c1:
        mount_type = st.selectbox(
            "🏗️ 支架安裝通風型態 (決定 U0, U1)",
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
        # 建立 06:00 ~ 18:00 直覺時分選單 (HH:MM)
        therm_time_options = []
        for h in range(6, 19):
            for m in [0, 15, 30, 45]:
                if h == 18 and m > 0:
                    continue
                therm_time_options.append(f"{h:02d}:{m:02d}")
        selected_t4_str = st.selectbox("⏰ 定格觀察時刻", therm_time_options, index=24)  # 預設 12:00 正午高溫
        th4, tm4 = map(int, selected_t4_str.split(":"))
        hour_t4 = float(th4) + float(tm4) / 60.0

    # 2x2 緊湊滑桿群組：環境氣溫、微風風速、陽光強度、溫度係數
    # 根據選擇時刻自動計算該時刻的典型陽光強度與氣溫基準，並允許微調
    sun_bell = max(0.0, np.sin(np.pi * (hour_t4 - 5.5) / 13.0))
    default_poa = int(round((900.0 * (sun_bell ** 1.15)) / 25.0) * 25)
    default_poa = int(np.clip(default_poa, 50, 1000))

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        wind_speed = st.slider("💨 案場風速 v (m/s)", 0.0, 10.0, 1.5, step=0.5)
    with r2_c2:
        t_amb = st.slider("🌡️ 環境氣溫 Tamb (°C)", 15.0, 40.0, 32.0, step=1.0)

    r3_c1, r3_c2 = st.columns(2)
    with r3_c1:
        poa_now = st.slider("☀️ 入射陽光 G (W/m²)", 50, 1000, default_poa, step=25)
    with r3_c2:
        gamma_pct = st.slider("📉 溫度係數 γ (%/°C)", -0.50, -0.25, -0.40, step=0.05)

with col_stage:
    fig_3d_therm, t_cell, delta_t, u_total, p_ideal, p_actual, loss_pct = build_3d_faiman_stage(
        poa_now, t_amb, wind_speed, u0_val, u1_val, gamma_pct, camera_mode
    )
    st.plotly_chart(fig_3d_therm, use_container_width=True, key="faiman_3d_stage")

# ==================== 中段：高亮度即時數據卡 ＋ 三大熱力學物理公式導讀（正下方一體化連動） ====================
# 同時計算如果「完全無風 (v=0)」時的溫度與發電量，展現微風救援效益
_, _, _, _, p_zero_wind_arr, _ = calc_faiman_temperature_and_power(poa_now, t_amb, 0.0, u0_val, u1_val, gamma_pct)
p_wind_saved = p_actual - float(p_zero_wind_arr.flat[0])

f1, f2, f3 = st.columns(3, gap="medium")

with f1:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🌡️ ① 太陽能板真實工作溫度 (Faiman 模型)</div>
        <div class="bright-val-red">{t_cell:.1f} °C <span style="font-size:1rem;color:#FFD700;font-weight:600;">｜ 較氣溫高 +{delta_t:.1f}°C</span></div>
        <div class="bright-sub">環境氣溫：{t_amb:.1f}°C ｜ 總散熱係數 U = {u_total:.1f} W/(m²·K)</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【① 為什麼大太陽下面板比氣溫燙這麼多？】** Faiman 模型指出，面板溫升取決於「陽光加熱 $G_{\\text{POA}}$」與「自然散熱 $U_0$ ＋ 風冷散熱 $U_1 v_w$」的拔河：")
        st.latex(r"T_{\text{cell}} = T_{\text{amb}} + \frac{G_{\text{POA}}}{U_0 + U_1 \cdot v_w}")
        st.latex(rf"T_{{\text{{cell}}}} = \color{{orange}}{{{t_amb:.1f}}} + \frac{{\color{{gold}}{{{poa_now:.0f}}}}}{{{u0_val:.0f} + {u1_val:.2f}\times\color{{deepskyblue}}{{{wind_speed:.1f}}}}} = \color{{red}}{{{t_cell:.1f}^\circ\text{{C}}}}")

with f2:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">📉 ② 高溫熱衰減率 (相較於 25°C 標準測試條件)</div>
        <div class="bright-val-orange">{loss_pct:+.2f} % <span style="font-size:1rem;color:#F8FAFC;font-weight:500;">｜ 超溫 +{t_cell - 25.0:.1f}°C</span></div>
        <div class="bright-sub">單晶矽溫度係數 γ = {gamma_pct:.2f}%/°C ｜ 白白蒸發功率：{p_ideal - p_actual:.1f} kW</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【② 為什麼面板發燒會害電壓與功率掉下來？】** 溫度超過 $25^\\circ\\text{C}$（STC 標準）時，半導體暗電流激增導致開路電壓 $V_{\\text{oc}}$ 下降：")
        st.latex(r"\Delta \eta_{\text{temp}} = \gamma \times (T_{\text{cell}} - 25^\circ\text{C})")
        st.latex(rf"\Delta \eta_{{\text{{temp}}}} = \color{{orange}}{{{gamma_pct:.2f}\%}} \times (\color{{red}}{{{t_cell:.1f}}} - 25) = \color{{red}}{{{loss_pct:+.2f}\%}}")

with f3:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">⚡ ③ 扣除溫損後實際功率 vs 微風散熱救援</div>
        <div class="bright-val-green">{p_actual:.1f} kW <span style="font-size:1rem;color:#00E5FF;font-weight:600;">｜ 💨 微風多救回 +{p_wind_saved:.1f} kW</span></div>
        <div class="bright-sub">25°C 理想功率：{p_ideal:.1f} kW ｜ 無風悶燒時僅剩：{float(p_zero_wind_arr.flat[0]):.1f} kW</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【③ 案場微風如何成為發電救星？】** 拉動上方 **「💨 案場風速 v」**，觀察風速提高如何幫面板降溫、把被高溫吃掉的電力搶回來：")
        st.latex(r"P_{\text{actual}} = P_{\text{ideal}} \times \left[1 + \gamma (T_{\text{cell}} - 25^\circ\text{C})\right]")
        st.latex(rf"P_{{\text{{actual}}}} = \color{{deepskyblue}}{{{p_ideal:.1f}\text{{ kW}}}} \times (1 \color{{red}}{{{loss_pct/100.0:+.3f}}}) = \color{{limegreen}}{{{p_actual:.1f}\text{{ kW}}}}")

# ==================== 底部：左解說導引 (1.0) + 右高挑飽滿「全日溫度衝擊對決曲線圖」(1.85) ====================
st.markdown("---")
col_guide, col_curve = st.columns([1.0, 1.85], gap="large")

# 計算全日 (05:30 ~ 18:30) 曲線
t_day = np.linspace(5.5, 18.5, 131)
sun_profile = np.maximum(0.0, np.sin(np.pi * (t_day - 5.5) / 13.0))
poa_day = 920.0 * np.power(sun_profile, 1.15)
# 氣溫在下午 13:30 達到最高
t_amb_day = (t_amb - 5.0) + 6.0 * np.sin(np.pi * (t_day - 6.0) / 14.0)

# 三種情境：1. 理想 25°C 無溫損  2. 當前風速 v 實際發電  3. 無風悶燒 (v=0) 發電
t_cell_wind_d, _, _, p_ideal_d, p_actual_wind_d, _ = calc_faiman_temperature_and_power(
    poa_day, t_amb_day, wind_speed, u0_val, u1_val, gamma_pct
)
t_cell_zero_d, _, _, _, p_actual_zero_d, _ = calc_faiman_temperature_and_power(
    poa_day, t_amb_day, 0.0, u0_val, u1_val, gamma_pct
)

dt_hr = float(t_day[1] - t_day[0])
kwh_ideal = float(np.sum(p_ideal_d) * dt_hr)
kwh_wind = float(np.sum(p_actual_wind_d) * dt_hr)
kwh_zero = float(np.sum(p_actual_zero_d) * dt_hr)

with col_guide:
    with st.container(border=True):
        st.markdown("#### 📖 「正午發電熱衰減」觀圖導引")
        st.markdown(
            "為什麼太陽能電廠在**「春、秋兩季晴天」**的單日最高發電功率，常常贏過炎熱的**「盛夏正午」**？請對照右側曲線觀察 **3 個核心現象**：\n\n"
            "1. **🔵 理想功率（藍虛線）vs 🔴 無風悶燒（紅線）**：\n"
            "   * 正午 11:00 ~ 14:30 陽光最強，但若無風散熱，面板溫度會飆破 **65°C ~ 70°C**！\n"
            "   * 曲線山頂被硬生生「削掉一大塊（紅色斜線損失區）」，全日白白蒸發掉數百度的電力！\n"
            "2. **🟢 微風散熱救援（綠實線）**：\n"
            "   * 當案場有微風吹拂（當前設定 **$v = " + f"{wind_speed:.1f}" + "\\text{ m/s}$**），對流散熱將山頂重新往上托舉，搶回中間的**綠色救援面積**！\n"
            "3. **🌊 漁電共生與水上型光電的隱藏優勢**：\n"
            "   * 水面與海邊案場因為微風穩定（$v_w$ 大）且水氣調節氣溫（$T_{\\text{amb}}$ 較低），散熱表現遠優於內陸鐵皮屋頂！"
        )
        st.info(
            f"📊 **今日全廠（1,000 m²）累積發電量比對**：\n"
            f"* 🔵 25°C 理想無溫損：**{kwh_ideal:.0f} kWh**\n"
            f"* 🟢 當前風速（{wind_speed:.1f} m/s）實發：**{kwh_wind:.0f} kWh**\n"
            f"* 🔴 完全無風（0 m/s）悶燒：**{kwh_zero:.0f} kWh**\n"
            f"👉 **微風散熱今日共為電廠多救回：+{kwh_wind - kwh_zero:.0f} 度電（kWh）！**"
        )

with col_curve:
    fig_curve = go.Figure()

    # 1. 無風悶燒情境 (v = 0 m/s，作為最差基準底線)
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=p_actual_zero_d, mode='lines',
        line=dict(color='#DC2626', width=3),
        fill='tozeroy', fillcolor='rgba(220, 38, 38, 0.12)',
        name=f'🔴 無風悶燒實發 (v=0m/s, 最高溫 {np.max(t_cell_zero_d):.0f}°C：{kwh_zero:.0f} kWh)'
    ))

    # 2. 當前風速散熱救援情境 (填滿與無風之間的綠色救援面積)
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=p_actual_wind_d, mode='lines',
        line=dict(color='#059669', width=4),
        fill='tonexty', fillcolor='rgba(16, 185, 129, 0.28)',
        name=f'🟢 當前風速實發 (v={wind_speed:.1f}m/s, 最高溫 {np.max(t_cell_wind_d):.0f}°C：{kwh_wind:.0f} kWh)'
    ))

    # 3. 25°C 理想無溫損功率 (藍色虛線封頂，中間代表仍殘留的溫損)
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=p_ideal_d, mode='lines',
        line=dict(color='#1D4ED8', width=3, dash='dash'),
        fill='tonexty', fillcolor='rgba(245, 158, 11, 0.18)',
        name=f'🔵 25°C 理想無溫損功率 (STC 基準：{kwh_ideal:.0f} kWh)'
    ))

    # 標示當前選擇時刻的垂直指標線
    fig_curve.add_vline(
        x=hour_t4, line_width=2.5, line_dash="dot", line_color="#7C3AED",
        annotation_text=f"<b>⏰ 定格時刻 {selected_t4_str} (面板 {t_cell:.1f}°C)</b>",
        annotation_position="top left",
        annotation_font=dict(color="#7C3AED", size=13)
    )

    # 清爽高對比白底科研主題（與第 2 章底部圖表風格 100% 統一，絕不壓扁或黑字撞黑底）
    fig_curve.update_layout(
        title=dict(
            text="<b>📊 全日發電功率溫度衝擊對決：見證正午「高溫削峰損失」與「微風散熱救援面積」！</b>",
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
