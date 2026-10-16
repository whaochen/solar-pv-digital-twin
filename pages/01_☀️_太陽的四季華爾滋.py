import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 1 章：太陽的四季華爾滋", page_icon="☀️", layout="wide")

st.title("第一章：【起程】太陽的四季華爾滋（太陽 ➔ 地球座標）")

st.info(
    "🌟 **【故事引導】** 距離地球 1.5 億公里外，一顆編號 #8765432 的光子誕生了。"
    "當它以光速飛行 8 分 20 秒抵達地球時，因為地球自轉軸傾斜了 **23.45°**，"
    "它在不同季節、不同緯度看到的土地與太陽能板角度完全不同……"
)

# 互動控制面板
st.markdown("### 🎛️ 天文幾何互動控制台（請拉動滑桿觀察公式與 3D 天球變化）")
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1.2, 1.2, 1.2, 1.4])

with col_ctrl1:
    season_preset = st.selectbox(
        "🎡 四季轉盤（快速節氣定位）",
        ["自訂日期 (拉動下方滑桿)", "🌸 春分 (3/21, 赤緯 0°)", "☀️ 夏至 (6/21, 赤緯 +23.45°)", "🍁 秋分 (9/23, 赤緯 0°)", "❄️ 冬至 (12/21, 赤緯 -23.45°)"],
        index=2
    )
    preset_map = {
        "🌸 春分 (3/21, 赤緯 0°)": 80,
        "☀️ 夏至 (6/21, 赤緯 +23.45°)": 172,
        "🍁 秋分 (9/23, 赤緯 0°)": 266,
        "❄️ 冬至 (12/21, 赤緯 -23.45°)": 355
    }
    default_n = preset_map.get(season_preset, 172)
    day_n = st.slider("📅 一年當中的第幾天 (n)", min_value=1, max_value=365, value=default_n)

with col_ctrl2:
    lat_preset = st.selectbox(
        "🌍 地理緯度快速定位",
        ["🇹🇼 台灣台南七股 (23.15°N)", "🇹🇼 台灣台北 (25.03°N)", "🌴 赤道新加坡 (1.35°N)", "🗼 日本東京 (35.68°N)", "🐻 北極圈斯瓦爾巴 (68.0°N)"]
    )
    lat_map = {
        "🇹🇼 台灣台南七股 (23.15°N)": 23.15,
        "🇹🇼 台灣台北 (25.03°N)": 25.03,
        "🌴 赤道新加坡 (1.35°N)": 1.35,
        "🗼 日本東京 (35.68°N)": 35.68,
        "🐻 北極圈斯瓦爾巴 (68.0°N)": 68.0
    }
    phi_deg = st.slider("🧭 觀察者所在緯度 φ (°N)", min_value=-66.5, max_value=70.0, value=lat_map[lat_preset], step=0.5)

with col_ctrl3:
    hour_t = st.slider("⏰ 太陽時間 (小時, 24hr制)", min_value=4.0, max_value=20.0, value=10.5, step=0.25)
    compare_seasons = st.checkbox("🌈 同時顯示春分/夏至/冬至三條軌道對比", value=True)

with col_ctrl4:
    camera_mode = st.radio(
        "🎥 3D 攝影機教學視角切換：",
        [
            "🔭 第三者上帝視角 (鳥瞰整座天球)",
            "☀️ 光子第一人稱視角 (從太陽往下看地球)",
            "🧍 操作者地面視角 (從南向北仰望天空)"
        ]
    )

# 天文物理核心計算
delta_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + day_n)))
delta_rad = np.radians(delta_deg)
phi_rad = np.radians(phi_deg)

cos_omega_s = -np.tan(phi_rad) * np.tan(delta_rad)
if cos_omega_s <= -1.0:
    omega_s_deg = 180.0
elif cos_omega_s >= 1.0:
    omega_s_deg = 0.0
else:
    omega_s_deg = np.degrees(np.arccos(cos_omega_s))

daylight_hours = (2.0 / 15.0) * omega_s_deg
sunrise_hr = 12.0 - daylight_hours / 2.0
sunset_hr = 12.0 + daylight_hours / 2.0
omega_deg = 15.0 * (hour_t - 12.0)

def calc_sun_xyz(n_day, hours_array, phi_r):
    d_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + n_day)))
    d_rad = np.radians(d_deg)
    w_rad = np.radians(15.0 * (hours_array - 12.0))
    z = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    x = -np.cos(d_rad) * np.sin(w_rad)
    y = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    return x, y, z

cur_x, cur_y, cur_z = calc_sun_xyz(day_n, np.array([hour_t]), phi_rad)
cur_x, cur_y, cur_z = float(cur_x[0]), float(cur_y[0]), float(cur_z[0])
alpha_s_deg = np.degrees(np.arcsin(np.clip(cur_z, -1.0, 1.0)))

# 左右分欄：左邊動態公式推導，右邊 3D 天球渲染
col_math, col_3d = st.columns([1.05, 1.45])

with col_math:
    st.markdown("### 📐 即時動態物理公式推導")
    st.markdown("#### ① 太陽赤緯角（Solar Declination, $\\delta$）")
    st.latex(r"\delta = 23.45^\circ \times \sin\left[\frac{360^\circ}{365} \times (284 + n)\right]")
    st.latex(rf"\delta = 23.45^\circ \times \sin\left[\frac{{360^\circ}}{{365}} \times (284 + \color{{orange}}{{{day_n}}})\right] = \color{{red}}{{{delta_deg:+.2f}^\circ}}")

    st.markdown("#### ② 日出日落時角（$\\omega_s$）與日照時數（$N$）")
    st.latex(r"\omega_s = \arccos(-\tan\phi \cdot \tan\delta), \quad N_{\text{day}} = \frac{2}{15^\circ}\omega_s")
    st.latex(rf"\omega_s = \arccos(-\tan(\color{{orange}}{{{phi_deg:.1f}^\circ}}) \cdot \tan(\color{{red}}{{{delta_deg:+.2f}^\circ}})) = \color{{deepskyblue}}{{{omega_s_deg:.1f}^\circ}}")
    st.latex(rf"N_{{\text{{day}}}} = \color{{limegreen}}{{{daylight_hours:.2f} \text{{ 小時}}}} \quad (\text{{日出 }} {int(sunrise_hr):02d}:{int((sunrise_hr%1)*60):02d} \sim \text{{日落 }} {int(sunset_hr):02d}:{int((sunset_hr%1)*60):02d})")

    st.markdown("#### ③ 當前時刻太陽高度角（Solar Altitude, $\\alpha_s$）")
    st.latex(r"\sin\alpha_s = \sin\phi\sin\delta + \cos\phi\cos\delta\cos\omega")
    if alpha_s_deg > 0:
        st.success(f"☀️ **目前太陽位於地平線之上！** 仰角 $\\alpha_s = {alpha_s_deg:.1f}^\\circ$，水平投影效率 $\\sin\\alpha_s = {cur_z:.3f}$。")
    else:
        st.warning(f"🌙 **目前太陽已落入地平線之下（夜晚）！** 仰角 $\\alpha_s = {alpha_s_deg:.1f}^\\circ$。")

with col_3d:
    st.markdown("### 🌐 3D 天球穹頂與太陽四季軌跡 (可用滑鼠旋轉/縮放)")
    fig = go.Figure()

    u_dome = np.linspace(0, 2 * np.pi, 36)
    v_dome = np.linspace(0, np.pi / 2, 18)
    fig.add_trace(go.Surface(
        x=np.outer(np.cos(u_dome), np.sin(v_dome)),
        y=np.outer(np.sin(u_dome), np.sin(v_dome)),
        z=np.outer(np.ones_like(u_dome), np.cos(v_dome)),
        opacity=0.12, showscale=False, colorscale=[[0, '#1E90FF'], [1, '#87CEFA']], hoverinfo='skip', name='天球穹頂'
    ))

    r_g, t_g = np.meshgrid(np.linspace(0, 1.0, 10), np.linspace(0, 2 * np.pi, 60))
    fig.add_trace(go.Surface(
        x=r_g * np.cos(t_g), y=r_g * np.sin(t_g), z=np.zeros_like(r_g),
        opacity=0.25, showscale=False, colorscale=[[0, '#2E8B57'], [1, '#3CB371']], hoverinfo='skip', name='地面'
    ))

    fig.add_trace(go.Scatter3d(
        x=[1.12, -1.12, 0, 0, 0], y=[0, 0, 1.12, -1.12, 0], z=[0, 0, 0, 0, 1.12],
        mode='text', text=['<b>東 (E)</b>', '<b>西 (W)</b>', '<b>北 (N)</b>', '<b>南 (S)</b>', '<b>天頂 (Zenith)</b>'],
        textfont=dict(size=13, color=['#FFD700', '#FFD700', '#00BFFF', '#FF6347', '#FFFFFF']), showlegend=False
    ))

    t_full = np.linspace(0, 24, 240)
    if compare_seasons:
        for s_day, s_name, s_color in [(172, "夏至 (6/21)", "#FF4500"), (80, "春/秋分", "#00FA9A"), (355, "冬至 (12/21)", "#00BFFF")]:
            sx, sy, sz = calc_sun_xyz(s_day, t_full, phi_rad)
            m = sz >= 0
            fig.add_trace(go.Scatter3d(x=sx[m], y=sy[m], z=sz[m], mode='lines', line=dict(color=s_color, width=4, dash='dash'), name=s_name))

    cx_arr, cy_arr, cz_arr = calc_sun_xyz(day_n, t_full, phi_rad)
    day_m = cz_arr >= 0
    fig.add_trace(go.Scatter3d(x=cx_arr[day_m], y=cy_arr[day_m], z=cz_arr[day_m], mode='lines', line=dict(color='#FFD700', width=8), name=f'當日軌跡 (第{day_n}天)'))

    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[0.02], mode='markers', marker=dict(size=10, color='#1E3A8A', symbol='square'), name='地面太陽能板'))
    sun_c = '#FFEA00' if cur_z >= 0 else '#555555'
    fig.add_trace(go.Scatter3d(x=[0, cur_x], y=[0, cur_y], z=[0, max(0.0, cur_z)], mode='lines+markers', line=dict(color='#FFEA00', width=6), marker=dict(size=[4, 16], color=['#FFFFFF', sun_c]), name=f'光子方向 ({hour_t:.1f}時)'))

    if "光子第一人稱視角" in camera_mode:
        cam_eye, cam_center = dict(x=cur_x * 1.8 + 0.01, y=cur_y * 1.8 + 0.01, z=max(0.2, cur_z * 1.8)), dict(x=0, y=0, z=0)
    elif "操作者地面視角" in camera_mode:
        cam_eye, cam_center = dict(x=0.0, y=0.35, z=0.08), dict(x=0.0, y=-0.6, z=0.45)
    else:
        cam_eye, cam_center = dict(x=1.45, y=-1.35, z=0.95), dict(x=0, y=0, z=0.1)

    fig.update_layout(
        height=600, margin=dict(l=0, r=0, b=0, t=30), paper_bgcolor='rgba(0,0,0,0)',
        scene=dict(xaxis=dict(visible=False, range=[-1.25, 1.25]), yaxis=dict(visible=False, range=[-1.25, 1.25]), zaxis=dict(visible=False, range=[-0.1, 1.25]), aspectmode='manual', aspectratio=dict(x=1, y=1, z=0.65), camera=dict(eye=cam_eye, center=cam_center), bgcolor='#0E1117'),
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02, font=dict(color="white"), bgcolor="rgba(0,0,0,0.5)")
    )
    st.plotly_chart(fig, use_container_width=True)
