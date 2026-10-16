import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 1 章：太陽的四季華爾滋", page_icon="☀️", layout="wide")

# ==================== 頂部：故事引導 ====================
st.title("第一章：【起程】太陽的四季華爾滋（太陽 ➔ 地球座標）")
st.info(
    "🌟 **【故事引導】** 距離地球 1.5 億公里外，一顆光子誕生了。當它抵達地球時，因為地球自轉軸傾斜了 **23.45°**，"
    "隨著地球公轉（四季更迭）與自轉（東升西落），光子每天在天空中劃出的軌跡高低與日照長短都截然不同……"
)

# ==================== 核心天文物理計算函數 ====================
def calc_sun_position(n_day, hours_array, phi_deg):
    """計算太陽赤緯角、日出日落時角、以及天球 3D 座標 (X:正東, Y:正北, Z:天頂)"""
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
        ws_deg = np.degrees(np.arccos(cos_ws))
        
    daylight_hr = (2.0 / 15.0) * ws_deg
    sunrise = 12.0 - daylight_hr / 2.0
    sunset = 12.0 + daylight_hr / 2.0

    # 3D 座標 (X: 正東, Y: 正北, Z: 天頂高度 sin(alpha))
    w_rad = np.radians(15.0 * (hours_array - 12.0))
    z = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    x = -np.cos(d_rad) * np.sin(w_rad)  # 早上 (hour < 12) w_rad < 0 -> x > 0 (東方)
    y = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    return d_deg, ws_deg, daylight_hr, sunrise, sunset, x, y, z

def build_3d_celestial_figure(day_n, phi_deg, hour_t, compare_seasons, camera_mode):
    """建構 3D 天球與東升西落視覺圖 (圖為主角)"""
    delta_deg, ws_deg, daylight_hr, sunrise, sunset, cur_x, cur_y, cur_z = calc_sun_position(
        day_n, np.array([hour_t]), phi_deg
    )
    cur_x, cur_y, cur_z = float(cur_x[0]), float(cur_y[0]), float(cur_z[0])
    alpha_s_deg = np.degrees(np.arcsin(np.clip(cur_z, -1.0, 1.0)))

    fig = go.Figure()

    # 1. 半透明 3D 天球穹頂
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

    # 2. 地面圓盤與東西南北十字座標線
    r_g, t_g = np.meshgrid(np.linspace(0, 1.05, 10), np.linspace(0, 2 * np.pi, 60))
    fig.add_trace(go.Surface(
        x=r_g * np.cos(t_g), y=r_g * np.sin(t_g), z=np.zeros_like(r_g),
        opacity=0.30, showscale=False,
        colorscale=[[0, '#134E5E'], [1, '#71B280']],
        hoverinfo='skip', name='地平線'
    ))

    # 東西向與南北向地面軸線
    fig.add_trace(go.Scatter3d(
        x=[-1.05, 1.05, None, 0, 0], y=[0, 0, None, -1.05, 1.05], z=[0, 0, None, 0, 0],
        mode='lines', line=dict(color='rgba(255,255,255,0.4)', width=3, dash='dot'),
        showlegend=False, hoverinfo='skip'
    ))

    # 醒目的東西南北與日出日落方位地標
    fig.add_trace(go.Scatter3d(
        x=[1.18, -1.18, 0, 0, 0],
        y=[0, 0, 1.18, -1.18, 0],
        z=[0.02, 0.02, 0.02, 0.02, 1.12],
        mode='text',
        text=[
            '<b>🌅 東方 (E)<br>日出升起側</b>',
            '<b>🌇 西方 (W)<br>日落西沉側</b>',
            '<b>⬆️ 北方 (N)</b>',
            '<b>⬇️ 南方 (S)</b>',
            '<b>✨ 天頂 (Zenith)</b>'
        ],
        textfont=dict(size=13, color=['#FFD700', '#FF8C00', '#00E5FF', '#FF6B6B', '#FFFFFF']),
        showlegend=False
    ))

    # 3. 繪製三季參考軌跡 (夏至、春秋分、冬至)
    t_full = np.linspace(0, 24, 241)
    if compare_seasons:
        for s_day, s_name, s_color in [
            (172, "夏至軌跡 (6/21 偏北較高)", "#FF5252"),
            (80,  "春分/秋分軌跡 (正東升正西落)", "#00E676"),
            (355, "冬至軌跡 (12/21 偏南較低)", "#40C4FF")
        ]:
            _, _, _, _, _, sx, sy, sz = calc_sun_position(s_day, t_full, phi_deg)
            m = sz >= 0
            fig.add_trace(go.Scatter3d(
                x=sx[m], y=sy[m], z=sz[m],
                mode='lines', line=dict(color=s_color, width=4, dash='dash'),
                name=s_name
            ))

    # 4. 繪製當日太陽完整白晝軌跡 + 整點時間刻度點 (讓使用者清楚看到東->西的時間推進)
    _, _, _, _, _, cx_arr, cy_arr, cz_arr = calc_sun_position(day_n, t_full, phi_deg)
    day_m = cz_arr >= 0
    fig.add_trace(go.Scatter3d(
        x=cx_arr[day_m], y=cy_arr[day_m], z=cz_arr[day_m],
        mode='lines', line=dict(color='#FFD700', width=8),
        name=f'當日太陽軌跡 (第 {day_n} 天)'
    ))

    # 加上從早上 6 點到下午 18 點的整點軌跡小圓點與時間標籤
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
            name='整點太陽位置', showlegend=False
        ))

    # 5. 繪製已走過的軌跡高亮線 (從日出到當前時刻 hour_t)
    t_past = np.linspace(max(0.0, sunrise), hour_t, 60)
    if hour_t > sunrise:
        _, _, _, _, _, px, py, pz = calc_sun_position(day_n, t_past, phi_deg)
        pm = pz >= 0
        fig.add_trace(go.Scatter3d(
            x=px[pm], y=py[pm], z=pz[pm],
            mode='lines', line=dict(color='#FFFFFF', width=10),
            name='今日已走過路徑', showlegend=False
        ))

    # 6. 中心 3D 太陽能板模型 (以立體矩形平面呈現)
    panel_w, panel_l = 0.14, 0.10
    tilt_rad = np.radians(20.0) # 假設向南傾斜 20 度
    px_corners = [-panel_w, panel_w, panel_w, -panel_w]
    py_corners = [-panel_l*np.cos(tilt_rad), -panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad)]
    pz_corners = [0.01, 0.01, 0.01 + 2*panel_l*np.sin(tilt_rad), 0.01 + 2*panel_l*np.sin(tilt_rad)]
    fig.add_trace(go.Mesh3d(
        x=px_corners, y=py_corners, z=pz_corners,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color='#1E88E5', opacity=0.9, name='地面太陽能板'
    ))

    # 7. 當前太陽球體與光子入射光束
    is_day = cur_z >= 0
    sun_color = '#FFEA00' if is_day else '#616161'
    beam_z = max(0.0, cur_z)
    fig.add_trace(go.Scatter3d(
        x=[0, cur_x], y=[0, cur_y], z=[0.02, beam_z],
        mode='lines+markers',
        line=dict(color='#FFEA00' if is_day else 'rgba(150,150,150,0.3)', width=7),
        marker=dict(size=[5, 20], color=['#FFFFFF', sun_color], symbol='circle'),
        name=f'當前太陽與光束 ({int(hour_t):02d}:{int((hour_t%1)*60):02d})'
    ))

    # 8. 攝影機視角設定 (新增最直覺的「東升西落全景視角」)
    if "東升西落全景視角" in camera_mode:
        # 站在北側往南看：左邊是東方(日出)，右邊是西方(日落)，完整看到太陽左升右落！
        cam_eye = dict(x=0.0, y=1.95, z=0.55)
        cam_center = dict(x=0.0, y=-0.1, z=0.25)
    elif "光子第一人稱視角" in camera_mode:
        cam_eye = dict(x=cur_x * 1.7 + 0.01, y=cur_y * 1.7 + 0.01, z=max(0.25, cur_z * 1.7))
        cam_center = dict(x=0, y=0, z=0)
    elif "案場工程師視角" in camera_mode:
        # 站在南側往北/天頂仰望
        cam_eye = dict(x=0.0, y=-1.85, z=0.45)
        cam_center = dict(x=0.0, y=0.1, z=0.3)
    else:
        # 第三者上帝視角 (東南偏南鳥瞰)
        cam_eye = dict(x=1.45, y=-1.35, z=0.95)
        cam_center = dict(x=0, y=0, z=0.15)

    status_tag = f"☀️ 白晝發電中 (仰角 {alpha_s_deg:.1f}°)" if is_day else f"🌙 夜晚無日照 (地平線下 {alpha_s_deg:.1f}°)"
    fig.update_layout(
        title=dict(
            text=f"<b>🕒 太陽時間：{int(hour_t):02d}:{int((hour_t%1)*60):02d} ｜ {status_tag}</b>",
            font=dict(size=18, color="#FFD700" if is_day else "#B0BEC5"),
            x=0.02, y=0.96
        ),
        height=640,
        margin=dict(l=0, r=0, b=0, t=40),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.3, 1.3]),
            yaxis=dict(visible=False, range=[-1.3, 1.3]),
            zaxis=dict(visible=False, range=[-0.05, 1.25]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.62),
            camera=dict(eye=cam_eye, center=cam_center),
            bgcolor='#0E1117'
        ),
        legend=dict(yanchor="top", y=0.90, xanchor="left", x=0.02, font=dict(color="white", size=12), bgcolor="rgba(0,0,0,0.5)")
    )
    return fig, delta_deg, ws_deg, daylight_hr, sunrise, sunset, alpha_s_deg, cur_z

# ==================== 主舞台配置：左拉桿控制台 (1) + 右 3D 主角視覺圖 (2.3) ====================
col_ctrl, col_stage = st.columns([1.0, 2.3], gap="large")

with col_ctrl:
    st.markdown("### 🎛️ 互動控制台")
    
    # 【亮點 1】動態播放東升西落按鈕
    st.markdown("#### 🎬 一日東升西落動態模擬")
    play_speed = st.select_slider(
        "播放流暢度",
        options=["慢速教學", "標準速度", "快速瀏覽"],
        value="標準速度"
    )
    play_btn = st.button("▶️ 點擊播放「太陽東升西落」一日動畫", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🎥 1. 選擇觀察者視角")
    camera_mode = st.radio(
        "切換 3D 鏡頭角度：",
        [
            "🌅 東升西落全景視角 (左東升 ➔ 右西落)",
            "🔭 第三者上帝視角 (3D 天球立體鳥瞰)",
            "☀️ 光子第一人稱視角 (從太陽往下看土地)",
            "🧍 案場工程師視角 (由南向北仰望天空)"
        ],
        index=0
    )

    st.markdown("#### 🎡 2. 調整季節與緯度")
    season_preset = st.selectbox(
        "快速節氣定位：",
        ["☀️ 夏至 (6/21, 太陽直射北回歸線)", "🌸 春分 (3/21, 太陽直射赤道)", "🍁 秋分 (9/23, 太陽直射赤道)", "❄️ 冬至 (12/21, 太陽直射南回歸線)", "自訂日期"],
        index=0
    )
    preset_map = {
        "🌸 春分 (3/21, 太陽直射赤道)": 80,
        "☀️ 夏至 (6/21, 太陽直射北回歸線)": 172,
        "🍁 秋分 (9/23, 太陽直射赤道)": 266,
        "❄️ 冬至 (12/21, 太陽直射南回歸線)": 355
    }
    default_n = preset_map.get(season_preset, 172)
    day_n = st.slider("📅 一年中的第幾天 (n)", 1, 365, default_n)

    lat_preset = st.selectbox(
        "地理緯度定位：",
        ["🇹🇼 台灣台南七股 (23.15°N)", "🇹🇼 台灣台北 (25.03°N)", "🌴 赤道新加坡 (1.35°N)", "🗼 日本東京 (35.68°N)", "🐻 北極圈斯瓦爾巴 (68.0°N)"]
    )
    lat_map = {
        "🇹🇼 台灣台南七股 (23.15°N)": 23.15,
        "🇹🇼 台灣台北 (25.03°N)": 25.03,
        "🌴 赤道新加坡 (1.35°N)": 1.35,
        "🗼 日本東京 (35.68°N)": 35.68,
        "🐻 北極圈斯瓦爾巴 (68.0°N)": 68.0
    }
    phi_deg = st.slider("🧭 所在緯度 φ (°N)", -66.5, 70.0, lat_map[lat_preset], step=0.5)

    st.markdown("#### ⏰ 3. 手動定格太陽時間")
    hour_t = st.slider("拉動觀察單一時刻 (24小時制)", 5.0, 19.5, 10.5, step=0.25)
    compare_seasons = st.checkbox("🌈 疊加顯示春分/夏至/冬至三條軌道", value=True)

with col_stage:
    # 建立一個空白容器供靜態或動態播放渲染 3D 圖
    chart_placeholder = st.empty()
    
    if play_btn:
        # 根據選擇的速度決定步進與延遲
        step_map = {"慢速教學": (0.25, 0.08), "標準速度": (0.5, 0.05), "快速瀏覽": (1.0, 0.03)}
        hr_step, sleep_sec = step_map[play_speed]
        
        for anim_hr in np.arange(5.0, 19.5 + hr_step, hr_step):
            fig_anim, delta_deg, ws_deg, daylight_hr, sunrise, sunset, alpha_s_deg, cur_z = build_3d_celestial_figure(
                day_n, phi_deg, float(anim_hr), compare_seasons, camera_mode
            )
            chart_placeholder.plotly_chart(fig_anim, use_container_width=True)
            time.sleep(sleep_sec)
        # 動畫結束後停留在使用者原本設定的時間或正午
        fig, delta_deg, ws_deg, daylight_hr, sunrise, sunset, alpha_s_deg, cur_z = build_3d_celestial_figure(
            day_n, phi_deg, hour_t, compare_seasons, camera_mode
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)
    else:
        fig, delta_deg, ws_deg, daylight_hr, sunrise, sunset, alpha_s_deg, cur_z = build_3d_celestial_figure(
            day_n, phi_deg, hour_t, compare_seasons, camera_mode
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)

    st.caption("💡 **互動小撇步**：你可以直接用滑鼠在上方 3D 圖內「左鍵按住拖曳旋轉」、「滾輪放大縮小」，或點擊左上角的 **▶️ 播放一日動畫** 觀察太陽從東邊升起、西邊落下的完整軌跡！")

# ==================== 下方：數據變化儀表板 + 物理公式白話導讀 ====================
st.markdown("---")
st.markdown("### 📊 太陽幾何即時數據與物理公式導讀（隨上方控制拉桿連動）")

# 第一排：4 張關鍵數據指標卡
m1, m2, m3, m4 = st.columns(4)
m1.metric("📐 太陽赤緯角 (δ)", f"{delta_deg:+.2f}°", "決定四季直射緯度")
m2.metric("🌅 日出 ～ 🌇 日落時刻", f"{int(sunrise):02d}:{int((sunrise%1)*60):02d} ～ {int(sunset):02d}:{int((sunset%1)*60):02d}", f"日落時角 ωs = {ws_deg:.1f}°")
m3.metric("⏳ 今日可發電白晝時數", f"{daylight_hr:.2f} 小時", f"{daylight_hr - 12.0:+.2f} hr (相較春分12小時)")
m4.metric("☀️ 當前太陽仰角 (αs)", f"{alpha_s_deg:.1f}°", f"地面水平受光率 {max(0.0, cur_z)*100:.1f}%")

# 第二排：三欄式「故事導讀 + 動態公式」
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    with st.container(border=True):
        st.markdown("#### ① 為什麼四季太陽軌跡會南北移動？")
        st.markdown(
            "**【公式導讀】** 因為地球自轉軸傾斜了 **23.45°**，導致一年 365 天當中，太陽直射地球的緯度（稱為**赤緯角 $\\delta$**）"
            "會在北緯 $+23.45^\\circ$（夏至）與南緯 $-23.45^\\circ$（冬至）之間像跳華爾滋一樣來回擺盪："
        )
        st.latex(r"\delta = 23.45^\circ \times \sin\left[\frac{360^\circ}{365} \times (284 + n)\right]")
        st.latex(rf"\text{{代入 }} n=\color{{orange}}{{{day_n}}} \implies \delta = \color{{red}}{{{delta_deg:+.2f}^\circ}}")
        st.caption("👉 在 3D 圖中，這決定了整條金色軌跡是往北偏（紅線）還是往南偏（藍線）。")

with f_col2:
    with st.container(border=True):
        st.markdown("#### ② 為什麼夏天白晝長、冬天白晝短？")
        st.markdown(
            "**【公式導讀】** 地球每小時自轉 $15^\\circ$。當太陽從正午（$0^\\circ$）轉到地平線落下時所走過的角度，"
            "稱為**日落時角 $\\omega_s$**。它由你所在的緯度 $\\phi$ 與赤緯角 $\\delta$ 共同決定："
        )
        st.latex(r"\omega_s = \arccos(-\tan\phi \cdot \tan\delta)")
        st.latex(rf"\omega_s = \arccos(-\tan(\color{{orange}}{{{phi_deg:.1f}^\circ}})\tan(\color{{red}}{{{delta_deg:+.2f}^\circ}})) = \color{{deepskyblue}}{{{ws_deg:.1f}^\circ}}")
        st.latex(rf"\text{{白晝總時數 }} N = \frac{{2 \times \color{{deepskyblue}}{{{ws_deg:.1f}^\circ}}}}{{15^\circ/\text{{hr}}}} = \color{{limegreen}}{{{daylight_hr:.2f} \text{{ 小時}}}}")

with f_col3:
    with st.container(border=True):
        st.markdown("#### ③ 太陽高度如何決定地面受光效率？")
        st.markdown(
            "**【公式導讀】** 隨著時間 $t$ 推進（時角 $\\omega = 15^\\circ(t-12)$），太陽離地平線的高度角 $\\alpha_s$ 會從東邊 $0^\\circ$ "
            "爬升到正午最高點，再落回西邊 $0^\\circ$："
        )
        st.latex(r"\sin\alpha_s = \sin\phi\sin\delta + \cos\phi\cos\delta\cos\omega")
        omega_now = 15.0 * (hour_t - 12.0)
        st.latex(rf"\text{{當前時角 }} \omega = \color{{orange}}{{{omega_now:+.1f}^\circ}} \implies \alpha_s = \color{{gold}}{{{alpha_s_deg:.1f}^\circ}}")
        st.caption("👉 太陽仰角越高（越接近頭頂 $90^\\circ$），單位面積土地接收到的光子密度就越高！")
