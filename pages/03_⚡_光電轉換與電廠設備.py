import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 3 章：光電轉換與電廠設備", page_icon="⚡", layout="wide")

# 緊湊化版面與高亮度發光數據卡 CSS（與第 1、2 章視覺風格 100% 統一）
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
    .bright-val-blue { color: #38BDF8 !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-val-orange { color: #FB923C !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-val-green { color: #00E676 !important; font-size: 1.7rem; font-weight: 800; line-height: 1.2; }
    .bright-sub { color: #94A3B8 !important; font-size: 0.82rem; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：故事引導 ====================
st.markdown("### 第三章：【蛻變】光電魔術與太陽能電廠大解密（光子 ➔ 電網）")
st.info(
    "🌟 **【故事引導】** 光子終於撞進了深藍色的太陽能板裡！但**一顆不帶電的光子，是如何把矽晶圓裡沉睡的電子「敲」醒變成電流？**"
    "而面板產生的**直流電（DC）**，又必須經過電廠裡哪些重裝備接力改造，才能變成家裡插座能用的**交流電（AC）**？"
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


# ==================== 模式 A：宏觀 3D 太陽能電廠設備與能量流舞台 ====================
def build_macro_plant_3d(irradiance, panel_eff, inv_eff, tx_eff):
    fig = go.Figure()

    # [Trace 0] 案場地面
    xg, yg = np.meshgrid(np.linspace(-2.1, 2.1, 12), np.linspace(-0.9, 0.9, 12))
    fig.add_trace(go.Surface(
        x=xg, y=yg, z=np.zeros_like(xg),
        opacity=0.35, showscale=False,
        colorscale=[[0, '#1E293B'], [1, '#334155']],
        hoverinfo='skip', name='案場地面'
    ))

    # [Trace 1] 高空太陽
    fig.add_trace(go.Scatter3d(
        x=[-1.35], y=[-0.35], z=[0.75],
        mode='text+markers',
        marker=dict(size=[26], color=['#FFEA00']),
        text=['<b>☀️ 高空太陽 (光子發射源)</b>'],
        textposition="top center",
        textfont=dict(size=13, color='#FFEA00'),
        showlegend=False
    ))

    # [Trace 2 & 3] 設備 ①：太陽能光電陣列 (位於左側 X = -1.35)
    for row_idx, py_c in enumerate([-0.26, 0.22]):
        px_c = -1.35
        w, l = 0.38, 0.16
        tilt = np.radians(22.0)
        vx = [px_c - w, px_c + w, px_c + w, px_c - w]
        vy = [py_c - l*np.cos(tilt), py_c - l*np.cos(tilt), py_c + l*np.cos(tilt), py_c + l*np.cos(tilt)]
        vz = [0.08, 0.08, 0.08 + 2*l*np.sin(tilt), 0.08 + 2*l*np.sin(tilt)]
        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz, i=[0, 0], j=[1, 2], k=[2, 3],
            color='#2563EB', opacity=0.92,
            name='① 太陽能板陣列 (產生直流電 DC)' if row_idx == 0 else '太陽能板陣列 #2',
            showlegend=(row_idx == 0)
        ))

    # [Trace 4] 設備 ②：智慧逆變器 (X = -0.35)
    fig.add_trace(make_3d_box(-0.35, 0.0, 0.14, 0.15, 0.15, 0.14, '#EA580C', '② 逆變器 (DC 轉 AC)'))

    # [Trace 5] 設備 ③：升壓變壓器 (X = +0.55)
    fig.add_trace(make_3d_box(0.55, 0.0, 0.18, 0.18, 0.18, 0.18, '#059669', '③ 升壓變壓器 (升壓至 22.8kV)'))

    # [Trace 6] 設備 ④：台電高壓輸電鐵塔 (X = +1.55)
    tx_tower = [
        1.42, 1.55, None, 1.68, 1.55, None, 1.42, 1.55, None, 1.68, 1.55, None,
        1.32, 1.78, None, 1.38, 1.72, None, 1.55, 1.55
    ]
    ty_tower = [
        -0.12, 0.0, None, -0.12, 0.0, None, 0.12, 0.0, None, 0.12, 0.0, None,
        0.0, 0.0, None, 0.0, 0.0, None, 0.0, 0.0
    ]
    tz_tower = [
        0.0, 0.58, None, 0.0, 0.58, None, 0.0, 0.58, None, 0.0, 0.58, None,
        0.36, 0.36, None, 0.50, 0.50, None, 0.0, 0.64
    ]
    fig.add_trace(go.Scatter3d(
        x=tx_tower, y=ty_tower, z=tz_tower,
        mode='lines+markers',
        line=dict(color='#E2E8F0', width=6),
        marker=dict(size=4, color='#38BDF8'),
        name='④ 台電高壓電塔 (併入電網)'
    ))

    # [Trace 7] 設備頭頂標籤
    p_dc = irradiance * 1.0 * (panel_eff / 100.0)
    p_ac = p_dc * (inv_eff / 100.0)
    p_grid = p_ac * (tx_eff / 100.0)

    fig.add_trace(go.Scatter3d(
        x=[-1.35, -0.35, 0.55, 1.55],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.32, 0.36, 0.44, 0.70],
        mode='text',
        text=[
            f"<b>① 太陽能板 ({p_dc:.1f} kW)</b>",
            f"<b>② 逆變器 ({p_ac:.1f} kW)</b>",
            f"<b>③ 變壓器 (22.8 kV)</b>",
            f"<b>④ 台電電網 ({p_grid:.1f} kW)</b>"
        ],
        textfont=dict(size=12, color=['#93C5FD', '#FDBA74', '#6EE7B7', '#FDE047']),
        showlegend=False
    ))

    # [Trace 8] 靜態電纜管道
    fig.add_trace(go.Scatter3d(
        x=[-1.35, -0.35, 0.55, 1.55],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.12, 0.12, 0.18, 0.44],
        mode='lines',
        line=dict(color='#64748B', width=8),
        name='電力傳輸電纜'
    ))

    # [Trace 9] 動態能量粒子流
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-1.35, -0.85, 0.10, 1.05],
        y=[-0.20, 0.0, 0.0, 0.0],
        z=[0.55, 0.13, 0.16, 0.32],
        mode='markers',
        marker=dict(size=[13, 11, 13, 15], color=['#FFEA00', '#00E5FF', '#00E676', '#FDE047'], symbol='circle'),
        name='⚡ 能量粒子 (黃:光子 / 藍:DC / 綠:AC)'
    ))

    # 建立多週期連續循環動畫影格 (120 影格)
    frames = []
    n_steps_per_cycle = 20
    total_cycles = 6
    total_frames = n_steps_per_cycle * total_cycles

    for f_i in range(total_frames):
        prog = (f_i % n_steps_per_cycle) / float(n_steps_per_cycle)

        p_t = (prog * 2.0) % 1.0
        ph_x = [-1.50 + 0.10 * k for k in range(4)]
        ph_y = [-0.35 * (1 - p_t) + (-0.26 if k % 2 == 0 else 0.22) * p_t for k in range(4)]
        ph_z = [0.72 * (1 - p_t) + 0.15 * p_t for k in range(4)]

        dc_x = [-1.35 + 1.00 * ((prog + 0.33 * k) % 1.0) for k in range(3)]
        dc_y = [0.0, 0.0, 0.0]
        dc_z = [0.13, 0.13, 0.13]

        ac_x = [-0.35 + 0.90 * ((prog + 0.33 * k) % 1.0) for k in range(3)]
        ac_y = [0.06 * np.sin(2 * np.pi * ((prog + 0.33 * k) * 2.0)) for k in range(3)]
        ac_z = [0.16, 0.16, 0.16]

        hv_u = [(prog + 0.33 * k) % 1.0 for k in range(3)]
        hv_x = [0.55 + 1.00 * u for u in hv_u]
        hv_y = [0.0, 0.0, 0.0]
        hv_z = [0.18 + 0.26 * u + 0.04 * np.sin(np.pi * u) for u in hv_u]

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

    cam_eye = dict(x=0.0, y=-1.72, z=0.35)
    cam_center = dict(x=0.05, y=0.0, z=0.12)

    fig.update_layout(
        title=dict(
            text=f"<b>🧍 案場工程師視角 ｜ ☀️光子({irradiance:.0f}kW) ➔ 🔵DC({p_dc:.1f}kW) ➔ 🟢AC({p_ac:.1f}kW) ➔ ⚡併網：{p_grid:.1f} kW</b>",
            font=dict(size=15, color="#FFD700"), x=0.02, y=0.96
        ),
        # 高度精準設為 420px，與左側 2x2 緊湊控制台高度完全齊平，消除右下角白塊！
        height=420,
        margin=dict(l=0, r=0, b=10, t=50),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-2.15, 2.15]),
            yaxis=dict(visible=False, range=[-1.0, 1.0]),
            zaxis=dict(visible=False, range=[-0.02, 0.88]),
            aspectmode='manual', aspectratio=dict(x=1.75, y=0.85, z=0.65),
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
                    label="🔄 點此循環播放能量流",
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

    fig.add_trace(make_3d_box(-0.35, 0, 0.14, 0.55, 0.42, 0.03, '#64748B', '⑤ 底部金屬背電極 (+)', opacity=0.90))
    fig.add_trace(make_3d_box(-0.35, 0, 0.28, 0.55, 0.42, 0.09, '#1E3A8A', '④ P 型矽晶圓層 (電洞 h⁺)', opacity=0.40))
    fig.add_trace(make_3d_box(-0.35, 0, 0.44, 0.55, 0.42, 0.06, '#F59E0B', '③ P-N 接面內建電場區', opacity=0.35))
    fig.add_trace(make_3d_box(-0.35, 0, 0.58, 0.55, 0.42, 0.07, '#0284C7', '② N 型矽晶圓層 (電子 e⁻)', opacity=0.40))
    for idx_g, gx in enumerate([-0.75, -0.48, -0.22, 0.05]):
        fig.add_trace(make_3d_box(
            gx, 0, 0.68, 0.025, 0.42, 0.02, '#E2E8F0',
            '① 頂部銀導電柵線 (-)' if idx_g == 0 else '柵線', opacity=0.95
        ))

    fig.add_trace(go.Scatter3d(
        x=[0.32, 0.32, 0.32, 0.32, 0.32],
        y=[0, 0, 0, 0, 0],
        z=[0.68, 0.58, 0.44, 0.28, 0.14],
        mode='text',
        textposition="middle right",
        text=[
            '<b>◀ ① 頂部銀柵線 (收集電子負極)</b>',
            '<b>◀ ② N 型半導體 (自由電子往此衝)</b>',
            '<b>◀ ⚡ ③ P-N 接面 (內建電場分離區)</b>',
            '<b>◀ ④ P 型半導體 (正電洞往此跑)</b>',
            '<b>◀ ⑤ 底部金屬背電極 (正極回路)</b>'
        ],
        textfont=dict(size=12, color=['#FFFFFF', '#38BDF8', '#FDE047', '#93C5FD', '#CBD5E1']),
        showlegend=False
    ))

    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-0.62, -0.35, -0.08], y=[0, 0, 0], z=[0.88, 0.44, 0.44],
        mode='markers+text',
        marker=dict(size=14, color=['#FFEA00', '#00E5FF', '#FF5252']),
        text=['☀️ 光子', '🔵 e⁻↑', '🔴 h⁺↓'],
        textposition="top center",
        textfont=dict(size=11, color='#FFFFFF'),
        name='微觀光電粒子 (黃:光子 / 藍:電子 / 紅:電洞)'
    ))

    frames = []
    n_steps = 20
    total_cycles = 6
    for f_i in range(n_steps * total_cycles):
        t_p = (f_i % n_steps) / float(n_steps - 1)
        if t_p < 0.45:
            u = t_p / 0.45
            z_ph = 0.90 * (1 - u) + 0.44 * u
            xs = [-0.62, -0.35, -0.08]
            ys = [0.0, 0.0, 0.0]
            zs = [z_ph, z_ph, z_ph]
            cols = ['#FFEA00'] * 3
            txts = ['☀️ 光子', '☀️ 光子', '☀️ 光子']
        else:
            u = (t_p - 0.45) / 0.55
            z_elec = 0.44 * (1 - u) + 0.70 * u
            z_hole = 0.44 * (1 - u) + 0.15 * u
            xs = [-0.62, -0.35, -0.08, -0.62, -0.35, -0.08]
            ys = [0.0]*6
            zs = [z_elec]*3 + [z_hole]*3
            cols = ['#00E5FF']*3 + ['#FF5252']*3
            txts = ['🔵 e⁻↑']*3 + ['🔴 h⁺↓']*3

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
        title=dict(text="<b>🔬 太陽能電池微觀解剖（☀️光子撞擊 ➔ 🔵電子往上衝、🔴電洞往下跑）</b>", font=dict(size=15, color="#FFD700"), x=0.02, y=0.96),
        height=420,
        margin=dict(l=0, r=0, b=10, t=50), paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.15, 1.55]),
            yaxis=dict(visible=False, range=[-0.85, 0.85]),
            zaxis=dict(visible=False, range=[0.02, 0.98]),
            aspectmode='manual', aspectratio=dict(x=1.55, y=0.80, z=0.75),
            camera=dict(eye=dict(x=0.05, y=-1.65, z=0.45), center=dict(x=0.10, y=0.0, z=0.35)),
            bgcolor='#0E1117'
        ),
        legend=dict(orientation="h", yanchor="top", y=0.90, xanchor="left", x=0.02, font=dict(color="white", size=11), bgcolor="rgba(15, 23, 42, 0.75)"),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.98, y=0.98, xanchor="right", yanchor="top", direction="left",
            pad=dict(r=5, t=0), bgcolor="#2563EB", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(
                    label="🔄 點此循環播放微觀動畫",
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


# ==================== 上半部主舞台：左 2x2 緊湊控制台 (1.05) + 右 3D 主角舞台 (2.25) 齊平同框 ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="medium")

with col_ctrl:
    st.markdown("##### 🔍 1. 選擇 3D 探索尺度（含學習導讀）")
    scene_mode = st.radio(
        "選擇 3D 探索尺度",
        [
            "🏭 宏觀尺度：3D 電廠四大設備與電流輸出 (🧍 案場工程師視角)",
            "🔬 微觀尺度：太陽能板內部 P-N 接面「光敲出電」解剖圖"
        ],
        index=0,
        label_visibility="collapsed"
    )

    if "宏觀尺度" in scene_mode:
        st.caption(
            "💡 **視角導讀（🧍 案場工程師視角）**：由南向北仰望！點擊右圖右上角 **🔄 循環播放**，"
            "觀察 **☀️光子 ➔ 🔵DC直流 ➔ 🟢AC交流 ➔ ⚡高壓電網** 的能量接力！"
        )
    else:
        st.caption(
            "🔬 **微觀導讀（P-N 接面解剖）**：把矽晶圓放大一萬倍！點擊右圖右上角 **🔄 循環播放**，"
            "觀察金色光子撞擊 P-N 接面，激發 **🔵自由電子往上衝、🔴電洞往下跑**！"
        )

    st.markdown("##### ☀️ 2. 調整日照與四大設備效率 (連動下方卡片)")
    # 採用 2x2 雙欄緊湊排布，徹底消除單列過長與斷行問題！
    r1_c1, r1_c2 = st.columns(2)
    with r1_c1:
        irradiance = st.slider("☀️ 陽光強度 G (W/m²)", 200, 1000, 850, step=50)
    with r1_c2:
        panel_eff = st.slider("🟦 ① 面板轉換效率 (%)", 15.0, 26.0, 21.5, step=0.5)

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        inv_eff = st.slider("🟧 ② 逆變器效率 (%)", 90.0, 99.0, 97.5, step=0.5)
    with r2_c2:
        tx_eff = st.slider("🟩 ③ 變壓器效率 (%)", 95.0, 99.5, 98.5, step=0.5)

    st.caption(f"⚡ **案場基準**：以 **1,000 m²** 太陽能板面積計算，當前陽光總輸入功率為 **{irradiance:.0f} kW**。")

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

# ==================== 下半部：高亮度即時數據卡 ＋ 三大核心物理公式導讀（一體化同框連動） ====================
total_sys_eff = (p_grid / max(irradiance, 1e-4)) * 100.0
households = int(p_grid / 1.2)

c_doc1, c_doc2, c_doc3 = st.columns(3, gap="medium")

with c_doc1:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🟦 關卡 1：太陽能板 DC 直流產出 (光電效應)</div>
        <div class="bright-val-blue">{p_dc:.1f} kW <span style="font-size:1rem;color:#FFD700;font-weight:600;">｜ 轉換效率 {panel_eff:.1f}%</span></div>
        <div class="bright-sub">陽光總輸入：{irradiance:.0f} kW (1,000 m²) ➔ 餘熱散失：{irradiance - p_dc:.1f} kW</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【① 太陽能板為何能發電？光生伏打效應】** 能量大於矽能隙（$1.12\\text{ eV}$）的光子敲出自由電子，經 P-N 接面內建電場分離產生直流電：")
        st.latex(r"P_{\text{DC}} = G \cdot A \cdot \eta_{\text{panel}} \quad (E_{\text{photon}} = h\nu \ge 1.12\text{ eV})")
        st.latex(rf"P_{{\text{{DC}}}} = \color{{gold}}{{{irradiance:.0f}\text{{ kW}}}} \times \color{{deepskyblue}}{{{panel_eff:.1f}\%}} = \color{{deepskyblue}}{{{p_dc:.1f}\text{{ kW}}}}")

with c_doc2:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🟧 關卡 2：逆變器 AC 交流產出 (電廠心臟)</div>
        <div class="bright-val-orange">{p_ac:.1f} kW <span style="font-size:1rem;color:#F8FAFC;font-weight:500;">｜ DC➔AC 效率 {inv_eff:.1f}%</span></div>
        <div class="bright-sub">執行 MPPT 最大功率追蹤 ＋ 將直流電切碎重組為 60Hz 正弦交流電</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【② 逆變器 Inverter 在做什麼？】** 家電與電網使用交流電（AC），逆變器負責將直流電轉為交流電並時刻鎖定最大功率點（$V_{\\text{mp}} \\times I_{\\text{mp}}$）：")
        st.latex(r"P_{\text{AC}} = \eta_{\text{inv}} \cdot P_{\text{DC, MPPT}} = \eta_{\text{inv}} \cdot (V_{\text{mp}} \times I_{\text{mp}})")
        st.latex(rf"P_{{\text{{AC}}}} = \color{{orange}}{{{inv_eff:.1f}\%}} \times \color{{deepskyblue}}{{{p_dc:.1f}\text{{ kW}}}} = \color{{orange}}{{{p_ac:.1f}\text{{ kW}}}}")

with c_doc3:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🗼 關卡 3：升壓變壓器併網功率 (22.8 kV 高壓)</div>
        <div class="bright-val-green">{p_grid:.1f} kW <span style="font-size:1rem;color:#FFD700;font-weight:600;">｜ 總系統效率 {total_sys_eff:.1f}%</span></div>
        <div class="bright-sub">變壓器效率 {tx_eff:.1f}% ｜ 🏠 可供約 {households} 戶家庭即時用電！</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【③ 為什麼進電網前要升壓變壓器？】** 將電壓拉高 50 倍至 $22.8\\text{ kV}$，電流 $I$ 即縮小為 1/50，大幅消除長途電纜發熱損耗（$I^2 R$）：")
        st.latex(r"P_{\text{grid}} = \eta_{\text{tx}} \cdot P_{\text{AC}} = \sqrt{3}\,V_{\text{HV}}\,I_{\text{line}}\cos\phi - I_{\text{line}}^2 R")
        st.latex(rf"P_{{\text{{grid}}}} = \color{{limegreen}}{{{tx_eff:.1f}\%}} \times \color{{orange}}{{{p_ac:.1f}\text{{ kW}}}} = \color{{limegreen}}{{{p_grid:.1f}\text{{ kW}}}}")
