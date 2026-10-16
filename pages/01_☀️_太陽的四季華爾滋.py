import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 1 章：太陽的四季華爾滋", page_icon="☀️", layout="wide")

# 注入緊湊化 CSS，減少多餘空白，確保「拉桿 + 數據 + 3D 圖」完美同框
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 10px 14px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：精簡故事引導 ====================
st.markdown("## 第一章：【起程】太陽的四季華爾滋（太陽 ➔ 地球座標）")
st.info(
    "🌟 **【故事引導】** 距離地球 1.5 億公里外，一顆光子誕生了。因為地球自轉軸傾斜了 **23.45°**，"
    "隨著地球公轉（四季更迭）與自轉（東升西落），光子每天在天空中劃出的軌跡高低與日照長短都截然不同……"
)

# ==================== 核心天文物理計算函數 ====================
def calc_sun_position(n_day, hours_array, phi_deg):
    """計算太陽赤緯角、日出日落時角、以及天球 3D 座標 (X:正東, Y:正北, Z:天頂)"""
    hours_arr = np.atleast_1d(hours_array).astype(float)
    phi_r = np.radians(phi_deg)
    d_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + n_day)))
    d_rad = np.radians(d_deg)
    
    # 日出日落時角
    cos_ws = -np.tan(phi_r) * np.tan(d_rad)
    if cos_ws <= -1.0:
        ws_deg = 180.0
    elif cos_ws >= 1.0:
        ws_deg = 0.0
    else:
        ws_deg = float(np.degrees(np.arccos(cos_ws)))
        
    daylight_hr = (2.0 / 15.0) * ws_deg
    sunrise = 12.0 - daylight_hr / 2.0
    sunset = 12.0 + daylight_hr / 2.0

    # 3D 座標 (X: 正東, Y: 正北, Z: 天頂高度 sin(alpha))
    w_rad = np.radians(15.0 * (hours_arr - 12.0))
    z = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    x = -np.cos(d_rad) * np.sin(w_rad)
    y = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    return float(d_deg), ws_deg, daylight_hr, sunrise, sunset, x, y, z


def build_smooth_3d_celestial_figure(day_n, phi_deg, hour_t, compare_seasons, camera_mode):
    """建構內建原生 WebGL 無閃爍動畫 (Frames) 的 3D 天球視覺圖"""
    delta_deg, ws_deg, daylight_hr, sunrise, sunset, cur_x, cur_y, cur_z = calc_sun_position(
        day_n, np.array([hour_t]), phi_deg
    )
    cur_x, cur_y, cur_z = float(cur_x.flat[0]), float(cur_y.flat[0]), float(cur_z.flat[0])
    alpha_s_deg = float(np.degrees(np.arcsin(np.clip(cur_z, -1.0, 1.0))))

    fig = go.Figure()

    # [Trace 0] 半透明 3D 天球穹頂
    u_dome = np.linspace(0, 2 * np.pi, 36)
    v_dome = np.linspace(0, np.pi / 2, 18)
    fig.add_trace(go.Surface(
        x=np.outer(np.cos(u_dome), np.sin(v_dome)),
        y=np.outer(np.sin(u_dome), np.sin(v_dome)),
        z=np.outer(np.ones_like(u_dome), np.cos(v_dome)),
        opacity=0.10, showscale=False,
        colorscale=[[0, '#0F2027'], [1, '#4FACFE']],
        hoverinfo='skip', name='天球穹頂'
    ))

    # [Trace 1] 地面圓盤
    r_g, t_g = np.meshgrid(np.linspace(0, 1.05, 10), np.linspace(0, 2 * np.pi, 60))
    fig.add_trace(go.Surface(
        x=r_g * np.cos(t_g), y=r_g * np.sin(t_g), z=np.zeros_like(r_g),
        opacity=0.30, showscale=False,
        colorscale=[[0, '#134E5E'], [1, '#71B280']],
        hoverinfo='skip', name='地平線'
    ))

    # [Trace 2] 東西向與南北向地面軸線
    fig.add_trace(go.Scatter3d(
        x=[-1.05, 1.05, None, 0, 0], y=[0, 0, None, -1.05, 1.05], z=[0, 0, None, 0, 0],
        mode='lines', line=dict(color='rgba(255,255,255,0.4)', width=3, dash='dot'),
        showlegend=False, hoverinfo='skip'
    ))

    # [Trace 3] 東西南北與日出日落方位地標
    fig.add_trace(go.Scatter3d(
        x=[1.18, -1.18, 0, 0, 0],
        y=[0, 0, 1.18, -1.18, 0],
        z=[0.02, 0.02, 0.02, 0.02, 1.10],
        mode='text',
        text=[
            '<b>🌅 東方 (E) 日出</b>',
            '<b>🌇 西方 (W) 日落</b>',
            '<b>⬆️ 北方 (N)</b>',
            '<b>⬇️ 南方 (S)</b>',
            '<b>✨ 天頂</b>'
        ],
        textfont=dict(size=12, color=['#FFD700', '#FF8C00', '#00E5FF', '#FF6B6B', '#FFFFFF']),
        showlegend=False
    ))

    # [Trace 4] 中心 3D 太陽能板模型
    panel_w, panel_l = 0.14, 0.10
    tilt_rad = np.radians(20.0)
    px_corners = [-panel_w, panel_w, panel_w, -panel_w]
    py_corners = [-panel_l*np.cos(tilt_rad), -panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad)]
    pz_corners = [0.01, 0.01, 0.01 + 2*panel_l*np.sin(tilt_rad), 0.01 + 2*panel_l*np.sin(tilt_rad)]
    fig.add_trace(go.Mesh3d(
        x=px_corners, y=py_corners, z=pz_corners,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color='#1E88E5', opacity=0.9, name='地面太陽能板'
    ))

    # 繪製三季參考軌跡
    t_full = np.linspace(0, 24, 241)
    if compare_seasons:
        for s_day, s_name, s_color in [
            (172, "夏至 (偏北較高)", "#FF5252"),
            (80,  "春/秋分 (正東升西落)", "#00E676"),
            (355, "冬至 (偏南較低)", "#40C4FF")
        ]:
            _, _, _, _, _, sx, sy, sz = calc_sun_position(s_day, t_full, phi_deg)
            m = sz >= 0
            fig.add_trace(go.Scatter3d(
                x=sx[m], y=sy[m], z=sz[m],
                mode='lines', line=dict(color=s_color, width=4, dash='dash'),
                name=s_name
            ))

    # 當日太陽完整白晝軌跡
    _, _, _, _, _, cx_arr, cy_arr, cz_arr = calc_sun_position(day_n, t_full, phi_deg)
    day_m = cz_arr >= 0
    fig.add_trace(go.Scatter3d(
        x=cx_arr[day_m], y=cy_arr[day_m], z=cz_arr[day_m],
        mode='lines', line=dict(color='#FFD700', width=6),
        name=f'當日軌跡 (第{day_n}天)'
    ))

    # 整點時間刻度標籤 (6:00 ~ 18:00)
    hours_ticks = np.arange(6, 19, 2)
    _, _, _, _, _, tx, ty, tz = calc_sun_position(day_n, hours_ticks, phi_deg)
    valid_t = tz >= 0
    if np.any(valid_t):
        fig.add_trace(go.Scatter3d(
            x=tx[valid_t], y=ty[valid_t], z=tz[valid_t] + 0.04,
            mode='markers+text',
            marker=dict(size=4, color='#FFF59D'),
            text=[f"{int(h)}:00" for h in hours_ticks[valid_t]],
            textfont=dict(size=10, color='#FFF59D'),
            name='整點位置', showlegend=False
        ))

    # [動態 Trace A] 今日已走過的高亮軌跡尾翼
    if hour_t > sunrise:
        t_past = np.linspace(max(0.0, sunrise), hour_t, 50)
        _, _, _, _, _, px, py, pz = calc_sun_position(day_n, t_past, phi_deg)
        pm = pz >= 0
        past_x, past_y, past_z = px[pm], py[pm], pz[pm]
    else:
        past_x, past_y, past_z = [0.0], [0.0], [0.0]

    trace_idx_past = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=past_x, y=past_y, z=past_z,
        mode='lines', line=dict(color='#FFFFFF', width=10),
        name='今日已走過路徑'
    ))

    # [動態 Trace B] 當前太陽發光球體與光子入射光束
    is_day = cur_z >= 0
    sun_color = '#FFEA00' if is_day else '#616161'
    beam_z = max(0.0, cur_z)
    trace_idx_sun = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[0.0, cur_x], y=[0.0, cur_y], z=[0.02, beam_z],
        mode='lines+markers',
        line=dict(color='#FFEA00' if is_day else 'rgba(150,150,150,0.3)', width=8),
        marker=dict(size=[5, 20], color=['#FFFFFF', sun_color], symbol='circle'),
        name='當前太陽與光束'
    ))

    # 建構無閃爍 WebGL 動畫 Frames (05:00 ~ 19:30)
    anim_hours = np.arange(5.0, 19.5, 0.25)
    frames = []
    slider_steps = []

    for h_val in anim_hours:
        _, _, _, _, _, hx_a, hy_a, hz_a = calc_sun_position(day_n, np.array([h_val]), phi_deg)
        hx, hy, hz = float(hx_a.flat[0]), float(hy_a.flat[0]), float(hz_a.flat[0])
        h_is_day = hz >= 0
        h_alpha = float(np.degrees(np.arcsin(np.clip(hz, -1.0, 1.0))))
        h_str = f"{int(h_val):02d}:{int((h_val%1)*60):02d}"
        h_status = f"☀️ 白晝發電中 (仰角 {h_alpha:.1f}°)" if h_is_day else f"🌙 夜晚無日照 (地平線下 {h_alpha:.1f}°)"

        if h_val > sunrise:
            tp = np.linspace(max(0.0, sunrise), h_val, 40)
            _, _, _, _, _, f_px, f_py, f_pz = calc_sun_position(day_n, tp, phi_deg)
            fpm = f_pz >= 0
            f_px, f_py, f_pz = f_px[fpm], f_py[fpm], f_pz[fpm]
        else:
            f_px, f_py, f_pz = [], [], []

        frames.append(go.Frame(
            name=h_str,
            traces=[trace_idx_past, trace_idx_sun],
            data=[
                go.Scatter3d(x=f_px, y=f_py, z=f_pz),
                go.Scatter3d(
                    x=[0.0, hx], y=[0.0, hy], z=[0.02, max(0.0, hz)],
                    line=dict(color='#FFEA00' if h_is_day else 'rgba(150,150,150,0.3)', width=8),
                    marker=dict(size=[5, 20], color=['#FFFFFF', '#FFEA00' if h_is_day else '#616161'])
                )
            ],
            layout=go.Layout(
                title=dict(
                    text=f"<b>🕒 太陽時間：{h_str} ｜ {h_status}</b>",
                    font=dict(size=16, color="#FFD700" if h_is_day else "#B0BEC5")
                )
            )
        ))

        slider_steps.append(dict(
            method="animate",
            args=[[h_str], dict(mode="immediate", frame=dict(duration=60, redraw=True), transition=dict(duration=0))],
            label=h_str
        ))

    fig.frames = frames

    # 設定攝影機視角
    if "東升西落全景視角" in camera_mode:
        cam_eye = dict(x=0.0, y=1.85, z=0.52)
        cam_center = dict(x=0.0, y=-0.05, z=0.22)
    elif "光子第一人稱視角" in camera_mode:
        cam_eye = dict(x=cur_x * 1.65 + 0.01, y=cur_y * 1.65 + 0.01, z=max(0.25, cur_z * 1.65))
        cam_center = dict(x=0.0, y=0.0, z=0.0)
    elif "案場工程師視角" in camera_mode:
        cam_eye = dict(x=0.0, y=-1.75, z=0.42)
        cam_center = dict(x=0.0, y=0.1, z=0.28)
    else:
        cam_eye = dict(x=1.40, y=-1.30, z=0.90)
        cam_center = dict(x=0.0, y=0.0, z=0.15)

    status_tag = f"☀️ 白晝發電中 (仰角 {alpha_s_deg:.1f}°)" if is_day else f"🌙 夜晚無日照 (地平線下 {alpha_s_deg:.1f}°)"

    fig.update_layout(
        title=dict(
            text=f"<b>🕒 太陽時間：{int(hour_t):02d}:{int((hour_t%1)*60):02d} ｜ {status_tag}</b>",
            font=dict(size=16, color="#FFD700" if is_day else "#B0BEC5"),
            x=0.02, y=0.96
        ),
        # 高度精準控制在 500px，搭配上方 4 張數據卡，完美與左側控制面板齊平同框！
        height=500,
        margin=dict(l=0, r=0, b=65, t=40),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.28, 1.28]),
            yaxis=dict(visible=False, range=[-1.28, 1.28]),
            zaxis=dict(visible=False, range=[-0.04, 1.20]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.60),
            camera=dict(eye=cam_eye, center=cam_center),
            bgcolor='#0E1117'
        ),
        legend=dict(orientation="h", yanchor="top", y=0.91, xanchor="left", x=0.02, font=dict(color="white", size=11), bgcolor="rgba(15,23,42,0.75)"),
        # 播放按鈕移至右上角，時間軸放在底部外圍，完全不遮擋 3D 圖
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.98, y=0.98,
            xanchor="right", yanchor="top",
            direction="left",
            pad=dict(r=5, t=0),
            bgcolor="#2563EB",
            font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(
                    label="▶️ 播放一日東升西落",
                    method="animate",
                    args=[None, dict(frame=dict(duration=70, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")]
                ),
                dict(
                    label="⏸️ 暫停",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )],
        sliders=[dict(
            active=int(np.clip((hour_t - 5.0) / 0.25, 0, len(slider_steps) - 1)),
            yanchor="bottom", xanchor="left",
            currentvalue=dict(font=dict(size=12, color="#FFD700"), prefix="動畫時間軸：", visible=True, xanchor="right"),
            transition=dict(duration=0),
            pad=dict(b=5, t=5),
            len=0.94, x=0.03, y=-0.06,
            font=dict(color="#CBD5E1", size=10),
            steps=slider_steps
        )]
    )
    return fig, delta_deg, ws_deg, daylight_hr, sunrise, sunset, alpha_s_deg, cur_z

# ==================== 主舞台配置：左拉桿控制台 (1.05) + 右「即時數據卡 + 3D 舞台」(2.25) 同框 ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="medium")

with col_ctrl:
    st.markdown("#### 🎛️ 1. 選擇觀察視角")
    camera_mode = st.radio(
        "切換 3D 鏡頭角度：",
        [
            "🌅 東升西落全景視角 (左東升 ➔ 右西落)",
            "🔭 第三者上帝視角 (3D 天球立體鳥瞰)",
            "☀️ 光子第一人稱視角 (從太陽往下看土地)",
            "🧍 案場工程師視角 (由南向北仰望天空)"
        ],
        index=0,
        label_visibility="collapsed"
    )

    if "東升西落" in camera_mode:
        st.caption("💡 **視角導讀**：左邊東方日出、右邊西方日落。點擊右上角 **▶️ 播放一日東升西落** 最能體會整日太陽變化！")
    elif "上帝視角" in camera_mode:
        st.caption("💡 **視角導讀**：外太空鳥瞰紅（夏至）、綠（春秋分）、藍（冬至）三季軌道。**調整下方緯度與季節滑桿時必選！**")
    elif "光子第一人稱視角" in camera_mode:
        st.caption("💡 **視角導讀**：從太陽往下看面板！**拉動下方時間比較 06:30（斜射面積小）與 12:00（直射面積最大）**。")
    else:
        st.caption("💡 **視角導讀**：站在案場地面向北仰望，觀察夏至正午太陽直逼頭頂（近 90°）與冬至偏南的差異。")

    st.markdown("#### 🎡 2. 調整季節與第 n 天")
    c_s1, c_s2 = st.columns([1.1, 1.0])
    with c_s1:
        season_preset = st.selectbox(
            "節氣快速定位",
            ["☀️ 夏至 (6/21)", "🌸 春分 (3/21)", "🍁 秋分 (9/23)", "❄️ 冬至 (12/21)", "自訂日期"],
            index=0
        )
    preset_map = {"🌸 春分 (3/21)": 80, "☀️ 夏至 (6/21)": 172, "🍁 秋分 (9/23)": 266, "❄️ 冬至 (12/21)": 355}
    default_n = preset_map.get(season_preset, 172)
    with c_s2:
        day_n = st.slider("📅 第 n 天 (1~365)", 1, 365, default_n)

    st.markdown("#### 🌍 3. 調整地理緯度 φ")
    c_l1, c_l2 = st.columns([1.1, 1.0])
    with c_l1:
        lat_preset = st.selectbox(
            "地點快速定位",
            ["🇹🇼 台南七股 (23.15°N)", "🇹🇼 台北 (25.03°N)", "🌴 新加坡 (1.35°N)", "🗼 東京 (35.68°N)", "🐻 北極圈 (68.0°N)"]
        )
    lat_map = {
        "🇹🇼 台南七股 (23.15°N)": 23.15, "🇹🇼 台北 (25.03°N)": 25.03,
        "🌴 新加坡 (1.35°N)": 1.35, "🗼 東京 (35.68°N)": 35.68, "🐻 北極圈 (68.0°N)": 68.0
    }
    with c_l2:
        phi_deg = st.slider("🧭 緯度 φ (°N)", -66.5, 70.0, lat_map[lat_preset], step=0.5)

    st.markdown("#### ⏰ 4. 定格計算時刻 (連動右方數據)")
    hour_t = st.slider("拉動觀察單一時刻仰角與下方公式", 5.0, 19.25, 10.5, step=0.25)
    compare_seasons = st.checkbox("🌈 疊加顯示春分/夏至/冬至三條軌道", value=True)

with col_stage:
    # 先計算物理結果
    fig, delta_deg, ws_deg, daylight_hr, sunrise, sunset, alpha_s_deg, cur_z = build_smooth_3d_celestial_figure(
        day_n, phi_deg, hour_t, compare_seasons, camera_mode
    )

    # 【關鍵升級】把 4 張即時數據卡直接放在右側最上方！左邊拉滑桿，右邊數字與 3D 圖同畫面立刻跳動！
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📐 太陽赤緯角 (δ)", f"{delta_deg:+.2f}°", "決定四季直射緯度")
    m2.metric("🌅 日出 ～ 🌇 日落", f"{int(sunrise):02d}:{int((sunrise%1)*60):02d}～{int(sunset):02d}:{int((sunset%1)*60):02d}", f"日落時角 ωs={ws_deg:.1f}°")
    m3.metric("⏳ 今日可發電白晝", f"{daylight_hr:.2f} hr", f"{daylight_hr - 12.0:+.2f} hr (較春分)")
    m4.metric("☀️ 定格太陽仰角 (αs)", f"{alpha_s_deg:.1f}°", f"水平受光率 {max(0.0, cur_z)*100:.1f}%")

    # 緊接著在數據卡正下方渲染 3D 天球舞台
    st.plotly_chart(fig, use_container_width=True, key="celestial_3d_stage")

# ==================== 下方：三欄式物理公式白話導讀 ====================
st.markdown("### 📖 物理公式白話導讀（隨上方控制拉桿即時跳動）")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    with st.container(border=True):
        st.markdown("##### ① 為什麼四季太陽軌跡會南北移動？")
        st.caption("地球自轉軸傾斜 23.45°，使太陽直射緯度（赤緯角 $\\delta$）在 $+23.45^\\circ$ 與 $-23.45^\\circ$ 間擺盪：")
        st.latex(r"\delta = 23.45^\circ \times \sin\left[\frac{360^\circ}{365} \times (284 + n)\right]")
        st.latex(rf"n=\color{{orange}}{{{day_n}}} \implies \delta = \color{{red}}{{{delta_deg:+.2f}^\circ}}")

with f_col2:
    with st.container(border=True):
        st.markdown("##### ② 為什麼夏天白晝長、冬天白晝短？")
        st.caption("地球每小時自轉 $15^\\circ$。由緯度 $\\phi$ 與赤緯角 $\\delta$ 解出日落時角 $\\omega_s$ 與白晝時數 $N$：")
        st.latex(r"\omega_s = \arccos(-\tan\phi \cdot \tan\delta), \quad N = \frac{2\omega_s}{15^\circ}")
        st.latex(rf"\omega_s = \color{{deepskyblue}}{{{ws_deg:.1f}^\circ}} \implies N = \color{{limegreen}}{{{daylight_hr:.2f}\text{{ hr}}}}")

with f_col3:
    with st.container(border=True):
        st.markdown("##### ③ 太陽高度如何決定地面受光效率？")
        st.caption("隨時間 $t$ 推進（時角 $\\omega = 15^\\circ(t-12)$），太陽離地平線的高度角 $\\alpha_s$ 決定受光密度：")
        st.latex(r"\sin\alpha_s = \sin\phi\sin\delta + \cos\phi\cos\delta\cos\omega")
        omega_now = 15.0 * (hour_t - 12.0)
        st.latex(rf"\omega = \color{{orange}}{{{omega_now:+.1f}^\circ}} \implies \alpha_s = \color{{gold}}{{{alpha_s_deg:.1f}^\circ}}")
