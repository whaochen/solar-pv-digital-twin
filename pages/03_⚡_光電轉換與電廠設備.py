import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 3 章：光電轉換與電廠設備", page_icon="⚡", layout="wide")

# ==================== 頂部：故事引導 ====================
st.title("第三章：【蛻變】光電魔術與太陽能電廠大解密（光子 ➔ 電網）")
st.info(
    "🌟 **【故事引導】** 經過 1.5 億公里的長途飛行與追日面板的精準捕捉，光子終於撞進了深藍色的太陽能板裡！\n\n"
    "但神奇的事情才剛要開始：**一顆沒有帶電的光子，到底是如何把矽晶圓裡沉睡的電子「敲」醒變成電流？**"
    "而面板產生的**直流電（DC）**，又必須經過電廠裡哪些重裝備的接力改造，才能變成我們家裡插座能用的**交流電（AC）**？"
    "現在，讓我們戴上工程帽走進 3D 太陽能電廠，親眼見證這場能量蛻變魔術！"
)

# ==================== 輔助 3D 幾何建模函數 ====================
def make_3d_box(cx, cy, cz, dx, dy, dz, color, name, opacity=0.9):
    """建立 3D 長方體設備模型"""
    x = [cx-dx, cx+dx, cx+dx, cx-dx, cx-dx, cx+dx, cx+dx, cx-dx]
    y = [cy-dy, cy-dy, cy+dy, cy+dy, cy-dy, cy-dy, cy+dy, cy+dy]
    z = [cz-dz, cz-dz, cz-dz, cz-dz, cz+dz, cz+dz, cz+dz, cz+dz]
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=opacity, name=name, showscale=False)


# ==================== 模式 A：宏觀 3D 太陽能電廠設備與能量流舞台 (固定案場工程師視角) ====================
def build_macro_plant_3d(irradiance, panel_eff, inv_eff, tx_eff):
    fig = go.Figure()

    # [Trace 0] 案場地面
    xg, yg = np.meshgrid(np.linspace(-1.7, 1.7, 12), np.linspace(-1.0, 1.0, 12))
    fig.add_trace(go.Surface(
        x=xg, y=yg, z=np.zeros_like(xg),
        opacity=0.35, showscale=False,
        colorscale=[[0, '#1E293B'], [1, '#334155']],
        hoverinfo='skip', name='案場地面'
    ))

    # [Trace 1] 方位地標與高空太陽
    fig.add_trace(go.Scatter3d(
        x=[0.0, 0.0, -1.6, 1.6, -1.05],
        y=[-0.95, 0.95, 0.0, 0.0, -0.45],
        z=[0.04, 0.04, 0.04, 0.04, 0.95],
        mode='text+markers',
        marker=dict(size=[1, 1, 1, 1, 26], color=['#FFF', '#FFF', '#FFF', '#FFF', '#FFEA00']),
        text=[
            '<b>⬇️ 南方 (S) 工程師站立側</b>',
            '<b>⬆️ 北方 (N)</b>',
            '<b>🌅 東方 (E)</b>',
            '<b>🌇 西方 (W)</b>',
            '<b>☀️ 高空太陽 (光子源)</b>'
        ],
        textposition="top center",
        textfont=dict(size=[12, 12, 12, 12, 14], color=['#FF6B6B', '#00E5FF', '#FFD700', '#FF8C00', '#FFEA00']),
        showlegend=False
    ))

    # [Trace 2 & 3] 設備 ①：太陽能光電陣列 (PV Array，兩排向南傾斜 22 度的深藍色面板)
    for row_idx, py_c in enumerate([-0.28, 0.22]):
        px_c = -1.05
        w, l = 0.36, 0.16
        tilt = np.radians(22.0)
        vx = [px_c - w, px_c + w, px_c + w, px_c - w]
        vy = [py_c - l*np.cos(tilt), py_c - l*np.cos(tilt), py_c + l*np.cos(tilt), py_c + l*np.cos(tilt)]
        vz = [0.10, 0.10, 0.10 + 2*l*np.sin(tilt), 0.10 + 2*l*np.sin(tilt)]
        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz, i=[0, 0], j=[1, 2], k=[2, 3],
            color='#2563EB', opacity=0.92,
            name='① 太陽能板陣列 (產生直流電 DC)' if row_idx == 0 else '太陽能板陣列 #2',
            showlegend=(row_idx == 0)
        ))

    # [Trace 4] 設備 ②：智慧逆變器 (Inverter，橘色機櫃，X = -0.25)
    fig.add_trace(make_3d_box(-0.25, 0.0, 0.15, 0.14, 0.14, 0.15, '#EA580C', '② 逆變器 (DC 轉 AC)'))

    # [Trace 5] 設備 ③：升壓變壓器 (Transformer，綠色機櫃，X = +0.50)
    fig.add_trace(make_3d_box(0.50, 0.0, 0.19, 0.17, 0.17, 0.19, '#059669', '③ 升壓變壓器 (升壓至 22.8kV)'))

    # [Trace 6] 設備 ④：台電高壓輸電鐵塔 (X = +1.30)
    tx_tower = [
        1.18, 1.30, None, 1.42, 1.30, None, 1.18, 1.30, None, 1.42, 1.30, None,
        1.10, 1.50, None, 1.15, 1.45, None, 1.30, 1.30
    ]
    ty_tower = [
        -0.12, 0.0, None, -0.12, 0.0, None, 0.12, 0.0, None, 0.12, 0.0, None,
        0.0, 0.0, None, 0.0, 0.0, None, 0.0, 0.0
    ]
    tz_tower = [
        0.0, 0.68, None, 0.0, 0.68, None, 0.0, 0.68, None, 0.0, 0.68, None,
        0.42, 0.42, None, 0.58, 0.58, None, 0.0, 0.74
    ]
    fig.add_trace(go.Scatter3d(
        x=tx_tower, y=ty_tower, z=tz_tower,
        mode='lines+markers',
        line=dict(color='#E2E8F0', width=6),
        marker=dict(size=4, color='#38BDF8'),
        name='④ 台電高壓電塔 (併入電網)'
    ))

    # [Trace 7] 簡潔清晰的設備頭頂標籤
    p_dc = irradiance * 1.0 * (panel_eff / 100.0)
    p_ac = p_dc * (inv_eff / 100.0)
    p_grid = p_ac * (tx_eff / 100.0)

    fig.add_trace(go.Scatter3d(
        x=[-1.05, -0.25, 0.50, 1.30],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.40, 0.42, 0.50, 0.82],
        mode='text',
        text=[
            f"<b>① 太陽能板 ({p_dc:.0f} kW DC)</b>",
            f"<b>② 逆變器 ({p_ac:.0f} kW AC)</b>",
            f"<b>③ 變壓器 (22.8 kV)</b>",
            f"<b>④ 台電電網 ({p_grid:.0f} kW)</b>"
        ],
        textfont=dict(size=12, color=['#93C5FD', '#FDBA74', '#6EE7B7', '#FDE047']),
        showlegend=False
    ))

    # [Trace 8] 靜態電纜管道
    fig.add_trace(go.Scatter3d(
        x=[-1.05, -0.25, 0.50, 1.30],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.14, 0.14, 0.20, 0.50],
        mode='lines',
        line=dict(color='#64748B', width=8),
        name='電力傳輸電纜'
    ))

    # [Trace 9] 動態能量粒子流
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-1.05, -0.65, 0.12, 0.90],
        y=[-0.20, 0.0, 0.0, 0.0],
        z=[0.65, 0.15, 0.18, 0.35],
        mode='markers',
        marker=dict(size=[13, 11, 13, 15], color=['#FFEA00', '#00E5FF', '#00E676', '#FDE047'], symbol='circle'),
        name='⚡ 能量粒子 (黃:光子 / 藍:DC / 綠:AC)'
    ))

    # 建立多週期連續循環動畫影格 (120 影格 = 連續循環 6 次，按下播放即可長時間自動循環)
    frames = []
    n_steps_per_cycle = 20
    total_cycles = 6
    total_frames = n_steps_per_cycle * total_cycles

    for f_i in range(total_frames):
        prog = (f_i % n_steps_per_cycle) / float(n_steps_per_cycle)

        # 1. 金色光子從高空太陽 (-1.05, -0.45, 0.95) 連續飛向兩排面板
        p_t = (prog * 2.0) % 1.0
        ph_x = [-1.20 + 0.10 * k for k in range(4)]
        ph_y = [-0.45 * (1 - p_t) + (-0.28 if k % 2 == 0 else 0.22) * p_t for k in range(4)]
        ph_z = [0.92 * (1 - p_t) + 0.18 * p_t for k in range(4)]

        # 2. 面板到逆變器的藍色 DC 直流電子 (-1.05 -> -0.25)
        dc_x = [-1.05 + 0.80 * ((prog + 0.33 * k) % 1.0) for k in range(3)]
        dc_y = [0.0, 0.0, 0.0]
        dc_z = [0.15, 0.15, 0.15]

        # 3. 逆變器到變壓器的綠色 AC 交流弦波粒子 (-0.25 -> 0.50)
        ac_x = [-0.25 + 0.75 * ((prog + 0.33 * k) % 1.0) for k in range(3)]
        ac_y = [0.06 * np.sin(2 * np.pi * ((prog + 0.33 * k) * 2.0)) for k in range(3)]
        ac_z = [0.18, 0.18, 0.18]

        # 4. 變壓器衝向高壓電塔的亮黃色高壓綠電 (0.50 -> 1.30)
        hv_u = [(prog + 0.33 * k) % 1.0 for k in range(3)]
        hv_x = [0.50 + 0.80 * u for u in hv_u]
        hv_y = [0.0, 0.0, 0.0]
        hv_z = [0.20 + 0.30 * u + 0.05 * np.sin(np.pi * u) for u in hv_u]

        all_x = ph_x + dc_x + ac_x + hv_x
        all_y = ph_y + dc_y + ac_y + hv_y
        all_z = ph_z + dc_z + ac_z + hv_z
        all_colors = ['#FFEA00']*4 + ['#00E5FF']*3 + ['#00E676']*3 + ['#FDE047']*3
        all_sizes = [12]*4 + [11]*3 + [13]*3 + [15]*3

        frames.append(go.Frame(
            name=f"Loop_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=all_x, y=all_y, z=all_z,
                mode='markers',
                marker=dict(size=all_sizes, color=all_colors, symbol='circle')
            )]
        ))

    fig.frames = frames

    # 固定採用「🧍 案場工程師視角 (由南向北仰望天空與太陽能板)」最佳構圖
    cam_eye = dict(x=-0.15, y=-1.65, z=0.38)
    cam_center = dict(x=-0.05, y=0.0, z=0.32)

    fig.update_layout(
        title=dict(
            text=f"<b>🧍 案場工程師視角 (由南向北仰望) ｜ ☀️光子 ➔ 🔵DC直流 ➔ 🟢AC交流 ➔ ⚡併網功率：{p_grid:.1f} kW</b>",
            font=dict(size=16, color="#FFD700"), x=0.02, y=0.96
        ),
        height=640,
        margin=dict(l=0, r=0, b=65, t=45),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.7, 1.7]),
            yaxis=dict(visible=False, range=[-1.1, 1.1]),
            zaxis=dict(visible=False, range=[0.0, 1.15]),
            aspectmode='manual', aspectratio=dict(x=1.55, y=0.9, z=0.68),
            camera=dict(eye=cam_eye, center=cam_center),
            bgcolor='#0E1117'
        ),
        legend=dict(
            orientation="h", yanchor="top", y=0.93, xanchor="left", x=0.02,
            font=dict(color="white", size=11), bgcolor="rgba(15, 23, 42, 0.75)"
        ),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.02, y=0.02, xanchor="left", yanchor="bottom", direction="left",
            pad=dict(r=10, t=5), bgcolor="#1E293B", font=dict(color="#FFFFFF", size=14),
            buttons=[
                dict(
                    label="🔄 循環播放「光子 ➔ 電網」能量流",
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
    return fig, p_dc, p_ac, p_grid


# ==================== 模式 B：微觀 3D 太陽能板 P-N 接面光電效應解剖舞台 ====================
def build_micro_pn_junction_3d(irradiance, panel_eff):
    fig = go.Figure()

    # 分層爆炸圖結構
    fig.add_trace(make_3d_box(-0.15, 0, 0.07, 0.75, 0.50, 0.03, '#64748B', '⑤ 底部金屬背電極 (+)', opacity=0.88))
    fig.add_trace(make_3d_box(-0.15, 0, 0.25, 0.75, 0.50, 0.11, '#1E3A8A', '④ P 型矽晶圓層 (富含電洞 h⁺)', opacity=0.38))
    fig.add_trace(make_3d_box(-0.15, 0, 0.45, 0.75, 0.50, 0.07, '#F59E0B', '③ P-N 接面內建電場區', opacity=0.32))
    fig.add_trace(make_3d_box(-0.15, 0, 0.63, 0.75, 0.50, 0.09, '#0284C7', '② N 型矽晶圓層 (富含電子 e⁻)', opacity=0.38))
    for idx_g, gx in enumerate([-0.65, -0.32, 0.01, 0.35]):
        fig.add_trace(make_3d_box(
            gx, 0, 0.75, 0.03, 0.50, 0.02, '#E2E8F0',
            '① 頂部銀導電柵線 (-)' if idx_g == 0 else '柵線', opacity=0.95
        ))

    # 右側獨立對齊的結構導引文字
    fig.add_trace(go.Scatter3d(
        x=[0.92, 0.92, 0.92, 0.92, 0.92],
        y=[0, 0, 0, 0, 0],
        z=[0.75, 0.63, 0.45, 0.25, 0.07],
        mode='text',
        text=[
            '<b>◀ ① 頂部銀柵線 (收集電子負極)</b>',
            '<b>◀ ② N 型半導體 (電子往此衝)</b>',
            '<b>◀ ⚡ ③ P-N 接面 (內建電場分離區)</b>',
            '<b>◀ ④ P 型半導體 (電洞往此跑)</b>',
            '<b>◀ ⑤ 底部金屬背板 (正極回路)</b>'
        ],
        textfont=dict(size=12, color=['#FFFFFF', '#38BDF8', '#FDE047', '#93C5FD', '#CBD5E1']),
        showlegend=False
    ))

    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-0.45, -0.15, 0.15], y=[0, 0, 0], z=[0.98, 0.45, 0.45],
        mode='markers+text',
        marker=dict(size=15, color=['#FFEA00', '#00E5FF', '#FF5252']),
        text=['☀️ 光子', '🔵 e⁻ 電子↑', '🔴 h⁺ 電洞↓'],
        textposition="top center",
        textfont=dict(size=12, color='#FFFFFF'),
        name='微觀光電粒子'
    ))

    # 建立多週期連續循環微觀動畫 (120 影格 = 連續循環 6 次)
    frames = []
    n_steps = 20
    total_cycles = 6
    for f_i in range(n_steps * total_cycles):
        t_p = (f_i % n_steps) / float(n_steps - 1)
        if t_p < 0.45:
            u = t_p / 0.45
            z_ph = 1.02 * (1 - u) + 0.45 * u
            xs = [-0.45, -0.15, 0.15]
            ys = [0.0, 0.0, 0.0]
            zs = [z_ph, z_ph, z_ph]
            cols = ['#FFEA00'] * 3
            txts = ['☀️ 光子', '☀️ 光子', '☀️ 光子']
        else:
            u = (t_p - 0.45) / 0.55
            z_elec = 0.45 * (1 - u) + 0.77 * u
            z_hole = 0.45 * (1 - u) + 0.08 * u
            xs = [-0.45, -0.15, 0.15, -0.45, -0.15, 0.15]
            ys = [0.0]*6
            zs = [z_elec]*3 + [z_hole]*3
            cols = ['#00E5FF']*3 + ['#FF5252']*3
            txts = ['🔵 e⁻ 電子↑']*3 + ['🔴 h⁺ 電洞↓']*3

        frames.append(go.Frame(
            name=f"MicroLoop_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=xs, y=ys, z=zs, mode='markers+text',
                marker=dict(size=14, color=cols),
                text=txts, textposition="top center", textfont=dict(size=11, color='#FFFFFF')
            )]
        ))

    fig.frames = frames
    fig.update_layout(
        title=dict(text="<b>🔬 3D 太陽能電池微觀結構解剖（☀️光子撞擊 P-N 接面 ➔ 🔵電子往上衝、🔴電洞往下跑）</b>", font=dict(size=16, color="#FFD700"), x=0.02, y=0.96),
        height=640,
        margin=dict(l=0, r=0, b=65, t=45), paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.15, 1.45]),
            yaxis=dict(visible=False, range=[-0.9, 0.9]),
            zaxis=dict(visible=False, range=[0.0, 1.15]),
            aspectmode='manual', aspectratio=dict(x=1.45, y=0.85, z=0.80),
            camera=dict(eye=dict(x=0.15, y=-1.75, z=0.52), center=dict(x=0.05, y=0.0, z=0.45)),
            bgcolor='#0E1117'
        ),
        legend=dict(orientation="h", yanchor="top", y=0.93, xanchor="left", x=0.02, font=dict(color="white", size=11), bgcolor="rgba(15, 23, 42, 0.75)"),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.02, y=0.02, xanchor="left", yanchor="bottom", direction="left",
            pad=dict(r=10, t=5), bgcolor="#1E293B", font=dict(color="#FFFFFF", size=14),
            buttons=[
                dict(
                    label="🔄 循環播放「光子敲出電子」動畫",
                    method="animate",
                    args=[None, dict(frame=dict(duration=95, redraw=True), transition=dict(duration=0), fromcurrent=False, mode="immediate")]
                ),
                dict(
                    label="⏸️ 暫停",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )]
    )
    return fig


# ==================== 主舞台配置：左拉桿控制台 (1) + 右 3D 主角視覺圖 (2.3) ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="large")

with col_ctrl:
    st.markdown("### 🎛️ 光電轉換與電廠控制台")

    st.markdown("#### 🔍 1. 選擇 3D 探索尺度")
    scene_mode = st.radio(
        "你想觀察哪一個層次的 3D 模擬？",
        [
            "🏭 宏觀尺度：3D 太陽能電廠四大設備與電流輸出 (🧍 案場工程師視角)",
            "🔬 微觀尺度：太陽能板內部 P-N 接面「光敲出電」解剖圖"
        ],
        index=0
    )

    if "宏觀尺度" in scene_mode:
        st.info(
            "💡 **【視角導讀：🧍 案場工程師視角（由南向北仰望天空與太陽能板）】**\n\n"
            "* **👀 你會看到什麼**：你正站在案場南側走道向北與高空仰望！高掛的金色太陽正將光子灑向眼前的深藍色面板陣列，右側依序連接**橘色逆變器**、**綠色升壓變壓器**與**銀色台電高壓電塔**。\n"
            "* **🎯 操作體驗**：點擊右圖左下角 **「🔄 循環播放」**，觀察 **☀️黃色光子 ➔ 🔵藍色DC直流電 ➔ 🟢綠色AC交流電 ➔ ⚡高壓電網** 源源不絕的能量轉換！"
        )
    else:
        st.info(
            "🔬 **【微觀解剖導讀：太陽能板內部 P-N 接面「光敲出電」】**\n\n"
            "* **👀 你會看到什麼**：把矽晶圓放大一萬倍的 3D 分層結構！上方是 **N 型矽（淺藍）**，下方是 **P 型矽（深藍）**，中間夾著黃色的 **P-N 接面內建電場**。\n"
            "* **🎯 操作體驗**：點擊右圖左下角 **「🔄 循環播放」**，觀察金色光子連續撞擊 P-N 接面，激發出藍色自由電子往上衝、紅色電洞往下跑的循環過程！"
        )

    st.markdown("#### ☀️ 2. 調整日照與電廠設備效率")
    irradiance = st.slider("☀️ 入射陽光強度 G (W/m²)", 200, 1000, 850, step=50)
    panel_eff = st.slider("🟦 ① 太陽能板光電轉換效率 (%)", 15.0, 26.0, 21.5, step=0.5)
    inv_eff = st.slider("🟧 ② 逆變器 (DC ➔ AC) 轉換效率 (%)", 90.0, 99.0, 97.5, step=0.5)
    tx_eff = st.slider("🟩 ③ 升壓變壓器與線路傳輸效率 (%)", 95.0, 99.5, 98.5, step=0.5)

with col_stage:
    if "宏觀尺度" in scene_mode:
        fig_3d, p_dc, p_ac, p_grid = build_macro_plant_3d(irradiance, panel_eff, inv_eff, tx_eff)
        st.plotly_chart(fig_3d, use_container_width=True, key="macro_plant_stage")
    else:
        p_dc = irradiance * 1.0 * (panel_eff / 100.0)
        p_ac = p_dc * (inv_eff / 100.0)
        p_grid = p_ac * (tx_eff / 100.0)
        fig_micro = build_micro_pn_junction_3d(irradiance, panel_eff)
        st.plotly_chart(fig_micro, use_container_width=True, key="micro_pn_stage")

    st.caption("🎬 **互動指南**：點擊上方 3D 舞台左下角的 **「🔄 循環播放」** 即可觀看連續能量流動畫；隨時可用滑鼠左鍵按住拖曳微調視角、滾輪縮放！")

# ==================== 下方：電廠能量轉換鏈儀表板 + 三大核心知識導讀 ====================
st.markdown("---")
st.markdown("### ⚡ 太陽能電廠「四大關卡」即時能量轉換儀表板（以 1,000 m² 案場面積為例）")

k1, k2, k3, k4 = st.columns(4)
k1.metric("☀️ 關卡 0：陽光總輸入功率", f"{irradiance:.0f} kW", "1,000 m² 接收之光能")
k2.metric("🟦 關卡 1：太陽能板 DC 直流產出", f"{p_dc:.1f} kW", f"面板轉換效率 {panel_eff:.1f}% (光電效應)")
k3.metric("🟧 關卡 2：逆變器 AC 交流產出", f"{p_ac:.1f} kW", f"DC 轉 AC 效率 {inv_eff:.1f}% (含 MPPT)")
k4.metric("🗼 關卡 3：變壓器升壓併網功率", f"{p_grid:.1f} kW", f"最終總系統效率 {(p_grid/irradiance)*100:.1f}%")

st.markdown("### 📖 從光子到插座：三大核心原理與電廠設備白話導讀")
c_doc1, c_doc2, c_doc3 = st.columns(3)

with c_doc1:
    with st.container(border=True):
        st.markdown("#### ① 太陽能板為何能捕捉陽光發電？")
        st.markdown(
            "**【光生伏打效應 Photovoltaic Effect】**\n"
            "太陽能板並不是「把熱能拿去燒水」，而是利用**半導體量子物理**！\n"
            "1. **敲醒電子**：當光子的能量大於矽晶圓的**能隙（Bandgap, $E_g = 1.12\\text{ eV}$）**時，光子會像撞球一樣把矽原子裡的電子敲出來，產生「自由電子（$-$）」與「電洞（$+$）」。\n"
            "2. **單向收費站（P-N 接面）**：透過在矽晶圓上下分別摻雜磷（N型）與硼（P型），中間會形成一道**內建電場**，強迫所有被敲出來的電子只能往頂部金屬線跑，接上電線就形成了**直流電（DC）**！"
        )
        st.latex(r"E_{\text{photon}} = h\nu = \frac{hc}{\lambda} \ge E_g \ (1.12\text{ eV})")
        st.caption("👉 為什麼面板轉換效率只有 21% 左右？因為紅外線光子能量太低敲不動電子，而藍紫光能量太高，多餘的能量會變成「熱」散失掉（這就是下一章面板會發燙的主因！）。")

with c_doc2:
    with st.container(border=True):
        st.markdown("#### ② 電廠的心臟：逆變器（Inverter）在做什麼？")
        st.markdown(
            "**【為什麼不能直接把太陽能板插進家裡插座？】**\n"
            "太陽能板發出來的是電壓與電流方向固定的**直流電（DC，像電池一樣）**；但台電電網與冷氣、冰箱使用的是每秒正負交替 60 次（$60\\text{ Hz}$）的**交流電（AC）**。\n"
            "* **功能 A（DC 轉 AC）**：透過高速電力電子開關（IGBT），將直流電切碎並重組為完美的正弦波交流電。\n"
            "* **功能 B（MPPT 最大功率點追蹤）**：雲飄過時日照強弱瞬間改變，逆變器會每毫秒動態調整電阻負載，找出能讓 $P = V \\times I$ 乘積最大的黃金工作點！"
        )
        st.latex(r"P_{\text{AC}} = \eta_{\text{inv}} \cdot P_{\text{DC, MPPT}} = \eta_{\text{inv}} \cdot (V_{\text{mp}} \times I_{\text{mp}})")
        st.latex(rf"P_{{\text{{AC}}}} = \color{{orange}}{{{inv_eff/100.0:.3f}}} \times \color{{deepskyblue}}{{{p_dc:.1f}\text{{ kW}}}} = \color{{limegreen}}{{{p_ac:.1f}\text{{ kW}}}}")

with c_doc3:
    with st.container(border=True):
        st.markdown("#### ③ 為什麼進電網前還要「升壓變壓器」？")
        st.markdown(
            "**【高壓輸電的物理智慧】**\n"
            "逆變器剛轉出來的交流電通常只有 $380\\text{ V} \\sim 800\\text{ V}$。如果直接用低電壓把幾百萬瓦的電力傳送到幾十公里外的城市，電線上的電流 $I$ 會大到把電纜燒融（熱損耗 $P_{\\text{loss}} = I^2 R$）！\n"
            "* **升壓變壓器（Step-Up Transformer）**：利用電磁感應將電壓一口氣拉高到 **$22.8\\text{ kV}$（配電級）或 $161\\text{ kV}$（輸電級）**。\n"
            "* 電壓提高 50 倍，電流就縮小為 1/50，電線上的發熱損耗直接暴降為 **1/2500**！"
        )
        st.latex(r"P_{\text{grid}} = \sqrt{3} \, V_{\text{line}} \, I_{\text{line}} \cos\phi - I_{\text{line}}^2 R_{\text{cable}}")
        st.caption(f"👉 經過這四大設備接力後，當前每小時可穩定併網輸出 **{p_grid:.1f} 度電（kWh）**！")
