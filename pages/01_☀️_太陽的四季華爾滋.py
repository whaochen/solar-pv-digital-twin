import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 1 章：太陽的四季華爾滋", page_icon="☀️", layout="wide")

# 初始化教學實驗 Session State
if "c1_cam" not in st.session_state:
    st.session_state.c1_cam = "🌅 東升西落全景視角 (左東升 ➔ 右西落)"
if "c1_day" not in st.session_state:
    st.session_state.c1_day = 172
if "c1_lat" not in st.session_state:
    st.session_state.c1_lat = 23.15
if "c1_hr" not in st.session_state:
    st.session_state.c1_hr = 10.5

# ==================== 頂部：故事引導 ====================
st.title("第一章：【起程】太陽的四季華爾滋（太陽 ➔ 地球座標）")
st.info(
    "🌟 **【故事引導】** 距離地球 1.5 億公里外，一顆光子誕生了。當它抵達地球時，因為地球自轉軸傾斜了 **23.45°**，"
    "隨著地球公轉（四季更迭）與自轉（東升西落），光子每天在天空中劃出的軌跡高低與日照長短都截然不同……"
)

# ==================== 核心天文物理計算函數 ====================
def calc_sun_position(n_day, hours_array, phi_deg):
    """計算太陽赤緯角、日出日落時角、以及天球 3D 座標 (X:正東, Y:正北, Z:天頂)"""
    hours_arr = np.atleast_1d(hours_array).astype(float)
    phi_r = np.radians(phi_deg)
    d_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + n_day)))
    d_rad = np.radians(d_deg)
    
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

    w_rad = np.radians(15.0 * (hours_arr - 12.0))
    z = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    x = -np.cos(d_rad) * np.sin(w_rad)  # 東方為 +X
    y = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)  # 北方為 +Y
    return d_deg, ws_deg, daylight_hr, sunrise, sunset, x, y, z


def build_smooth_3d_celestial_figure(day_n, phi_deg, hour_t, compare_seasons, camera_mode):
    """建構內建原生 WebGL 無閃爍動畫 (Frames) 的 3D 天球視覺圖"""
    delta_deg, ws_deg, daylight_hr, sunrise, sunset, cur_x, cur_y, cur_z = calc_sun_position(
        day_n, hour_t, phi_deg
    )
    cur_x, cur_y, cur_z = float(cur_x.flat[0]), float(cur_y.flat[0]), float(cur_z.flat[0])
    alpha_s_deg = np.degrees(np.arcsin(np.clip(cur_z, -1.0, 1.0)))

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

    # [Trace 4] 中心 3D 太陽能板模型
    panel_w, panel_l = 0.14, 0.10
    tilt_rad = np.radians(20.0)
    px_corners = [-panel_w, panel_w, panel_w, -panel_w]
    py_corners = [-panel_l*np.cos(tilt_rad), -panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad)]
    pz_corners = [0.01, 0.01, 0.01 + 2*panel_l*np.sin(tilt_rad), 0.01 + 2*panel_l*np.sin(tilt_rad)]
    fig.add_trace(go.Mesh3d(
        x=px_corners, y=py_corners, z=pz_corners,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color='#1E88E5', opacity=0.9, name='地面太陽能板 (朝南傾角20°)'
    ))

    # 繪製三季參考軌跡
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

    # 當日太陽完整白晝軌跡
    _, _, _, _, _, cx_arr, cy_arr, cz_arr = calc_sun_position(day_n, t_full, phi_deg)
    day_m = cz_arr >= 0
    fig.add_trace(go.Scatter3d(
        x=cx_arr[day_m], y=cy_arr[day_m], z=cz_arr[day_m],
        mode='lines', line=dict(color='#FFD700', width=6),
        name=f'當日太陽軌跡 (第 {day_n} 天)'
    ))

    # 整點時間刻度標籤 (6:00 ~ 18:00)
    hours_ticks = np.arange(6, 19, 2)
    _, _, _, _, _, tx, ty, tz = calc_sun_position(為了讓讀者在切換視角時，不只是「覺得 3D 畫面很炫」，而是帶著明確的**「物理觀察任務（Learning Mission）」**去操作，最糟糕的設計就是把導讀藏在折疊選單（Expander）裡，或者只放靜態文字。

真正的「教學互動體驗」，應該要做到**「智慧情境連動導讀」**——當讀者切換不同視角、或是拉動時間/緯度滑桿時，**左側控制台與右側 3D 畫布上方會即時跳出「🎯 當前視角學習任務」與「⚡ 動態實驗引導（告訴你現在該拉哪個滑桿、看哪個角落）」**！

下面我為你將 **第一章** 與 **第二章** 的完整程式碼全面升級（同時包含上一輪修復的 `IndexError` 防呆機制），直接內建**「動態視角導師系統（Interactive POV Tutor）」**。

---

### 🌟 這次升級的「三大教學設計亮點」

1. **選視角即跳出「3 步驟實驗任務卡」**（不再藏在折疊選單）：
   * 點選每一個 3D 鏡頭時，下方立刻亮起一張專屬的**「🔬 視角觀察指南」**，明確回答三個問題：
     1. **👁️ 選這個視角會看到什麼？**
     2. **⏱️ 什麼時機點選它最適合？**
     3. **🧪 現在請跟著這樣做（動手實驗步驟）！**
2. **「情境感知（Context-Aware）」即時回饋**：
   * 例如在第二章，當讀者切換到 `☀️ 光子第一人稱視角`，但如果他的時間滑桿還停在中午 12:00（此時三塊板子面積差不多），系統會主動跳出黃色提示：**「⚠️ 教學提示：目前是正午 12 點，斜射效應不明顯！請立刻把下方時間滑桿拉到『早上 07:00』，你將親眼見證固定式面板縮小成一條線的『餘弦損失』震撼畫面！」**
   * 當讀者真的把時間拉到 07:00 時，提示會瞬間變成綠色過關訊息：**「🎯 實驗成功！請看右圖：藍板受光面積只剩 31%，而橘板（雙軸）是 100% 正方形！」**
3. **3D 畫布內嵌「視覺焦點標註（HUD 抬頭顯示器）」**：
   * 在 3D 黑底畫面的上方，直接把該視角的「觀察口訣」印在畫布上，眼睛看著 3D 圖就能直接對照物理概念。

---

### 📄 第一章完整程式碼：請更新 `pages/01_☀️_太陽的四季華爾滋.py`

請打開 GitHub 的 **`pages/01_☀️_太陽的四季華爾滋.py`**，將內容完整替換為以下程式碼並按 **Commit changes**：

```python
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
    hours_arr = np.atleast_1d(hours_array).astype(float)
    phi_r = np.radians(phi_deg)
    d_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + n_day)))
    d_rad = np.radians(d_deg)
    
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

    w_rad = np.radians(15.0 * (hours_arr - 12.0))
    z = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    x = -np.cos(d_rad) * np.sin(w_rad)  # 早上 (hour < 12) w_rad < 0 -> x > 0 (東方)
    y = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    return d_deg, ws_deg, daylight_hr, sunrise, sunset, x, y, z


def build_smooth_3d_celestial_figure(day_n, phi_deg, hour_t, compare_seasons, camera_mode, hud_subtitle):
    """建構內建原生 WebGL 無閃爍動畫 (Frames) 與教學 HUD 的 3D 天球視覺圖"""
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

    # [Trace 4] 中心 3D 太陽能板模型
    panel_w, panel_l = 0.14, 0.10
    tilt_rad = np.radians(20.0)
    px_corners = [-panel_w, panel_w, panel_w, -panel_w]
    py_corners = [-panel_l*np.cos(tilt_rad), -panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad), panel_l*np.cos(tilt_rad)]
    pz_corners = [0.01, 0.01, 0.01 + 2*panel_l*np.sin(tilt_rad), 0.01 + 2*panel_l*np.sin(tilt_rad)]
    fig.add_trace(go.Mesh3d(
        x=px_corners, y=py_corners, z=pz_corners,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color='#1E88E5', opacity=0.9, name='地面太陽能板 (朝南傾角20°)'
    ))

    # 三季參考軌跡
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

    # 當日太陽完整白晝軌跡
    _, _, _, _, _, cx_arr, cy_arr, cz_arr = calc_sun_position(day_n, t_full, phi_deg)
    day_m = cz_arr >= 0
    fig.add_trace(go.Scatter3d(
        x=cx_arr[day_m], y=cy_arr[day_m], z=cz_arr[day_m],
        mode='lines', line=dict(color='#FFD700', width=6),
        name=f'當日太陽軌跡 (第 {day_n} 天)'
    ))

    # 整點時間刻度標籤
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

    # ==================== 動態變化的 2 個主角 Trace ====================
    t_past = np.linspace(max(0.0, sunrise), hour_t, 50)
    if hour_t > sunrise:
        _, _, _, _, _, px, py, pz = calc_sun_position(day_n, t_past, phi_deg)
        pm = pz >= 0
        past_x, past_y, past_z = px[pm], py[pm], pz[pm]
    else:
        past_x, past_y, past_z = [0], [0], [0]

    trace_idx_past = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=past_x, y=past_y, z=past_z,
        mode='lines', line=dict(color='#FFFFFF', width=10),
        name='今日已走過路徑'
    ))

    is_day = cur_z >= 0
    sun_color = '#FFEA00' if is_day else '#616161'
    beam_z = max(0.0, cur_z)
    trace_idx_sun = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[0, cur_x], y=[0, cur_y], z=[0.02, beam_z],
        mode='lines+markers',
        line=dict(color='#FFEA00' if is_day else 'rgba(150,150,150,0.3)', width=8),
        marker=dict(size=[5, 22], color=['#FFFFFF', sun_color], symbol='circle'),
        name='當前太陽與光子光束'
    ))

    # ==================== 建構無閃爍 WebGL 動畫 Frames ====================
    anim_hours = np.arange(5.0, 19.5, 0.25)
    frames = []
    slider_steps = []

    for h_val in anim_hours:
        _, _, _, _, _, hx, hy, hz = calc_sun_position(day_n, np.array([h_val]), phi_deg)
        hx, hy, hz = float(hx.flat[0]), float(hy.flat[0]), float(hz.flat[0])
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
                    x=[0, hx], y=[0, hy], z=[0.02, max(0.0, hz)],
                    line=dict(color='#FFEA00' if h_is_day else 'rgba(150,150,150,0.3)', width=8),
                    marker=dict(size=[5, 22], color=['#FFFFFF', '#FFEA00' if h_is_day else '#616161'])
                )
            ],
            layout=go.Layout(
                title=dict(
                    text=f"<b>🕒 太陽時間：{h_str} ｜ {h_status}</b><br><span style='font-size:13px;color:#38BDF8;'>{hud_subtitle}</span>",
                    font=dict(size=17, color="#FFD700" if h_is_day else "#B0BEC5")
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
        cam_eye = dict(x=0.0, y=1.95, z=0.55)
        cam_center = dict(x=0.0, y=-0.1, z=0.25)
    elif "光子第一人稱視角" in camera_mode:
        cam_eye = dict(x=cur_x * 1.7 + 0.01, y=cur_y * 1.7 + 0.01, z=max(0.25, cur_z * 1.7))
        cam_center = dict(x=0, y=0, z=0)
    elif "案場工程師視角" in camera_mode:
        cam_eye = dict(x=0.0, y=-1.85, z=0.45)
        cam_center = dict(x=0.0, y=0.1, z=0.3)
    else:
        cam_eye = dict(x=1.45, y=-1.35, z=0.95)
        cam_center = dict(x=0, y=0, z=0.15)

    status_tag = f"☀️ 白晝發電中 (仰角 {alpha_s_deg:.1f}°)" if is_day else f"🌙 夜晚無日照 (地平線下 {alpha_s_deg:.1f}°)"

    fig.update_layout(
        title=dict(
            text=f"<b>🕒 太陽時間：{int(hour_t):02d}:{int((hour_t%1)*60):02d} ｜ {status_tag}</b><br><span style='font-size:13px;color:#38BDF8;'>{hud_subtitle}</span>",
            font=dict(size=17, color="#FFD700" if is_day else "#B0BEC5"),
            x=0.02, y=0.96
        ),
        height=680,
        margin=dict(l=0, r=0, b=80, t=60),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.3, 1.3]),
            yaxis=dict(visible=False, range=[-1.3, 1.3]),
            zaxis=dict(visible=False, range=[-0.05, 1.25]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.62),
            camera=dict(eye=cam_
