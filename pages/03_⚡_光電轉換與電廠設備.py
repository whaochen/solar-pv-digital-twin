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


# ==================== 模式 A：宏觀 3D 太陽能電廠設備與能量流舞台 ====================
def build_macro_plant_3d(irradiance, panel_eff, inv_eff, tx_eff, camera_mode):
    fig = go.Figure()

    # [Trace 0] 案場地面
    xg, yg = np.meshgrid(np.linspace(-1.7, 1.7, 12), np.linspace(-1.0, 1.0, 12))
    fig.add_trace(go.Surface(
        x=xg, y=yg, z=np.zeros_like(xg),
        opacity=0.35, showscale=False,
        colorscale=[[0, '#1E293B'], [1, '#334155']],
        hoverinfo='skip', name='案場地面'
    ))

    # [Trace 1] 方位地標與高空太陽 (拉開間距，避免文字互撞)
    fig.add_trace(go.Scatter3d(
        x=[0.0, 0.0, -1.6, 1.6, -1.05],
        y=[-0.95, 0.95, 0.0, 0.0, -0.45],
        z=[0.04, 0.04, 0.04, 0.04, 0.92],
        mode='text+markers',
        marker=dict(size=[1, 1, 1, 1, 24], color=['#FFF', '#FFF', '#FFF', '#FFF', '#FFEA00']),
        text=[
            '<b>⬇️ 南方 (S)</b>',
            '<b>⬆️ 北方 (N)</b>',
            '<b>🌅 東方 (E)</b>',
            '<b>🌇 西方 (W)</b>',
            '<b>☀️ 高空太陽</b>'
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
            name='① 太陽能板陣列 (DC)' if row_idx == 0 else '太陽能板陣列 #2',
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
        name='④ 台電高壓電塔 (電網)'
    ))

    # [Trace 7] 簡潔清晰的設備頭頂標籤 (單行+功率，高度錯開不重疊)
    p_dc = irradiance * 1.0 * (panel_eff / 100.0)
    p_ac = p_dc * (inv_eff / 100.0)
    p_grid = p_ac * (tx_eff / 100.0)

    fig.add_trace(go.Scatter3d(
        x=[-1.05, -0.25, 0.50, 1.30],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.38, 0.42, 0.50, 0.82],
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

    # [Trace 9] 動態能量粒子流 (不顯示雜亂文字，改用圖例與鮮明色彩區分)
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-1.05, -0.65, 0.12, 0.90],
        y=[-0.20, 0.0, 0.0, 0.0],
        z=[0.65, 0.15, 0.18, 0.35],
        mode='markers',
        marker=dict(size=[13, 11, 13, 15], color=['#FFEA00', '#00E5FF', '#00E676', '#FDE047'], symbol='circle'),
        name='⚡ 能量粒子 (黃:光子 / 藍:DC / 綠:AC)'
    ))

    # 建立 24 影格無閃爍循環能量流動畫
    frames = []
    slider_steps = []
    n_frames = 24

    for f_i in range(n_frames):
        prog = f_i / float(n_frames - 1)

        # 1. 金色光子從高空太陽 (-1.05, -0.45, 0.92) 飛向面板
        p_t = (prog * 2.0) % 1.0
        ph_x = [-1.20 + 0.10 * k for k in range(4)]
        ph_y = [-0.45 * (1 - p_t) + (-0.28 if k % 2 == 0 else 0.22) * p_t for k in range(4)]
        ph_z = [0.88 * (1 - p_t) + 0.18 * p_t for k in range(4)]

        # 2. 面板到逆變器的藍色 DC 直流電子 (-1.05 -> -0.25)
        dc_t = (prog * 2.0 + 0.3) % 1.0
        dc_x = [-1.05 + 0.80 * ((dc_t + 0.33 * k) % 1.0) for k in range(3)]
        dc_y = [0.0, 0.0, 0.0]
        dc_z = [0.15, 0.15, 0.15]

        # 3. 逆變器到變壓器的綠色 AC 交流弦波粒子 (-0.25 -> 0.50)
        ac_x = [-0.25 + 0.75 * ((prog + 0.25 * k) % 1.0) for k in range(3)]
        ac_y = [0.06 * np.sin(2 * np.pi * ((prog + 0.25 * k) * 2.0)) for k in range(3)]
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

        stage_label = (
            "① 光子撞擊矽晶圓 (光電效應)" if prog < 0.25 else
            "② 藍色直流電 (DC) 進入逆變器" if prog < 0.50 else
            "③ 逆變器轉出綠色三相交流電 (AC)" if prog < 0.75 else
            "④ 變壓器升壓至 22.8kV 併入台電電網！"
        )

        frames.append(go.Frame(
            name=f"Step_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=all_x, y=all_y, z=all_z,
                mode='markers',
                marker=dict(size=all_sizes, color=all_colors, symbol='circle')
            )],
            layout=go.Layout(
                title=dict(
                    text=f"<b>⚡ {stage_label} ｜ 最終併網功率：{p_grid:.1f} kW</b>",
                    font=dict(size=16, color="#FFD700")
                )
            )
        ))

        slider_steps.append(dict(
            method="animate",
            args=[[f"Step_{f_i}"], dict(mode="immediate", frame=dict(duration=90, redraw=True), transition=dict(duration=0))],
            label=f"{int(prog*100)}%"
        ))

    fig.frames = frames

    # 重新調校攝影機視角：確保四大設備都在畫面正中央，絕不壓在底部！
    if "案場工程師視角" in camera_mode:
        # 站在案場南側走道微蹲仰望，同時清楚看到四大設備與上方太陽
        cam_eye = dict(x=-0.20, y=-1.65, z=0.42)
        cam_center = dict(x=-0.05, y=0.0, z=0.32)
    elif "追隨電流特寫視角" in camera_mode:
        cam_eye = dict(x=0.10, y=-1.25, z=0.45)
        cam_center = dict(x=0.10, y=0.0, z=0.22)
    else:
        # 電廠無人機鳥瞰視角 (全景最清楚)
        cam_eye = dict(x=0.0, y=-1.85, z=0.88)
        cam_center = dict(x=0.05, y=0.0, z=0.25)

    fig.update_layout(
        title=dict(
            text=f"<b>🏭 3D 太陽能電廠四大設備與能量流 ｜ 即時併網發電：{p_grid:.1f} kW</b>",
            font=dict(size=16, color="#FFD700"), x=0.02, y=0.96
        ),
        height=650,
        # 關鍵修正：加大底部 margin (b=110)，並把播放按鈕與時間軸移到畫布外圍下方 (y=-0.08)，完全不擋 3D 圖！
        margin=dict(l=0, r=0, b=110, t=45),
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
            x=0.01, y=-0.12, xanchor="left", yanchor="bottom", direction="left",
            pad=dict(r=10, t=5), bgcolor="#1E293B", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(
                    label="▶️ 播放能量轉換動畫",
                    method="animate",
                    args=[None, dict(frame=dict(duration=90, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")]
                ),
                dict(
                    label="⏸️ 暫停",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )],
        sliders=[dict(
            active=0, yanchor="bottom", xanchor="left",
            currentvalue=dict(font=dict(size=13, color="#FFD700"), prefix="轉換進度：", visible=True, xanchor="right"),
            transition=dict(duration=0), pad=dict(b=0, t=5), len=0.68, x=0.30, y=-0.12,
            font=dict(color="#CBD5E1", size=10), steps=slider_steps
        )]
    )
    return fig, p_dc, p_ac, p_grid


# ==================== 模式 B：微觀 3D 太陽能板 P-N 接面光電效應解剖舞台 ====================
def build_micro_pn_junction_3d(irradiance, panel_eff):
    fig = go.Figure()

    # 拉開垂直爆炸圖層次間距 (Z 軸從 0.05 分佈到 0.90)，讓內部粒子與文字清清楚楚！
    # 1. 底部鋁背板電極 (Z: 0.04 ~ 0.10)
    fig.add_trace(make_3d_box(-0.15, 0, 0.07, 0.75, 0.50, 0.03, '#64748B', '⑤ 底部金屬背電極 (+)', opacity=0.88))
    # 2. P 型矽半導體層 (Z: 0.14 ~ 0.36)
    fig.add_trace(make_3d_box(-0.15, 0, 0.25, 0.75, 0.50, 0.11, '#1E3A8A', '④ P 型矽晶圓層 (富含電洞 h⁺)', opacity=0.38))
    # 3. P-N 接面內建電場區 (Z: 0.38 ~ 0.52)
    fig.add_trace(make_3d_box(-0.15, 0, 0.45, 0.75, 0.50, 0.07, '#F59E0B', '③ P-N 接面內建電場區', opacity=0.32))
    # 4. N 型矽半導體層 (Z: 0.54 ~ 0.72)
    fig.add_trace(make_3d_box(-0.15, 0, 0.63, 0.75, 0.50, 0.09, '#0284C7', '② N 型矽晶圓層 (富含電子 e⁻)', opacity=0.38))
    # 5. 頂部銀導電柵線 (Z: 0.75)
    for idx_g, gx in enumerate([-0.65, -0.32, 0.01, 0.35]):
        fig.add_trace(make_3d_box(
            gx, 0, 0.75, 0.03, 0.50, 0.02, '#E2E8F0',
            '① 頂部銀導電柵線 (-)' if idx_g == 0 else '柵線', opacity=0.95
        ))

    # 右側獨立對齊的結構導引文字 (放在 X = +0.88 空白區，絕不壓在晶圓上)
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

    # 動態粒子：只用清爽標籤，避免重疊
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-0.45, -0.15, 0.15], y=[0, 0, 0], z=[0.98, 0.45, 0.45],
        mode='markers+text',
        marker=dict(size=15, color=['#FFEA00', '#00E5FF', '#FF5252']),
        text=['☀️ 入射光子', '🔵 自由電子 e⁻ (往上)', '🔴 電洞 h⁺ (往下)'],
        textposition="top center",
        textfont=dict(size=12, color='#FFFFFF'),
        name='微觀光電粒子'
    ))

    frames = []
    slider_steps = []
    for f_i in range(20):
        t_p = f_i / 19.0
        if t_p < 0.45:
            u = t_p / 0.45
            z_ph = 1.02 * (1 - u) + 0.45 * u
            xs = [-0.45, -0.15, 0.15]
            ys = [0.0, 0.0, 0.0]
            zs = [z_ph, z_ph, z_ph]
            cols = ['#FFEA00'] * 3
            txts = ['☀️ 光子', '☀️ 光子', '☀️ 光子']
            stage_msg = "階段 1：能量 > 1.12 eV 的光子穿透表面，撞擊 P-N 接面矽原子！"
        else:
            u = (t_p - 0.45) / 0.55
            z_elec = 0.45 * (1 - u) + 0.77 * u
            z_hole = 0.45 * (1 - u) + 0.08 * u
            xs = [-0.45, -0.15, 0.15, -0.45, -0.15, 0.15]
            ys = [0.0]*6
            zs = [z_elec]*3 + [z_hole]*3
            cols = ['#00E5FF']*3 + ['#FF5252']*3
            txts = ['🔵 e⁻ 電子↑']*3 + ['🔴 h⁺ 電洞↓']*3
            stage_msg = "階段 2：光生伏打效應！內建電場將電子推向頂部柵線、電洞推向底部背板！"

        frames.append(go.Frame(
            name=f"Micro_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=xs, y=ys, z=zs, mode='markers+text',
                marker=dict(size=14, color=cols),
                text=txts, textposition="top center", textfont=dict(size=11, color='#FFFFFF')
            )],
            layout=go.Layout(title=dict(text=f"<b>🔬 {stage_msg}</b>", font=dict(size=15, color="#FFD700")))
        ))
        slider_steps.append(dict(
            method="animate",
            args=[[f"Micro_{f_i}"], dict(mode="immediate", frame=dict(duration=100, redraw=True), transition=dict(duration=0))],
            label=f"{int(t_p*100)}%"
        ))

    fig.frames = frames
    fig.update_layout(
        title=dict(text="<b>🔬 3D 太陽能電池微觀結構解剖（P-N 接面與光生伏打效應）</b>", font=dict(size=16, color="#FFD700"), x=0.02, y=0.96),
        height=650,
        # 一樣把播放控制列移到畫布最下方外圍 (y=-0.12)，絕不擋住晶圓模型！
        margin=dict(l=0, r=0, b=110, t=45), paper_bgcolor='#0E1117',
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
            type="buttons", showactive=False, x=0.01, y=-0.12, xanchor="left", yanchor="bottom", direction="left",
            pad=dict(r=10, t=5), bgcolor="#1E293B", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(label="▶️ 播放「光子敲出電子」動畫", method="animate", args=[None, dict(frame=dict(duration=100, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")]),
                dict(label="⏸️ 暫停", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
            ]
        )],
        sliders=[dict(
            active=0, yanchor="bottom", xanchor="left",
            currentvalue=dict(font=dict(size=13, color="#FFD700"), prefix="微觀進度：", visible=True, xanchor="right"),
            pad=dict(b=0, t=5), len=0.66, x=0.32, y=-0.12,
            font=dict(color="#CBD5E1", size=10), steps=slider_steps
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
            "🏭 宏觀尺度：3D 太陽能電廠四大設備與電流輸出",
            "🔬 微觀尺度：太陽能板內部 P-N 接面「光敲出電」解剖圖"
        ],
        index=0
    )

    if "宏觀尺度" in scene_mode:
        st.markdown("#### 🎥 2. 切換 3D 觀察視角（含學習導讀）")
        camera_mode = st.radio(
            "選擇電廠教學鏡頭：",
            [
                "🚁 電廠無人機鳥瞰視角 (全廠四大設備與電網總覽)",
                "🧍 案場工程師視角 (由南向北仰望天空與太陽能板)",
                "⚡ 追隨電流特寫視角 (聚焦逆變器 DC 轉 AC 樞紐)"
            ],
            index=0
        )

        if "案場工程師視角" in camera_mode:
            st.info(
                "💡 **【視角導讀：🧍 案場工程師視角（由南向北仰望天空）】**\n\n"
                "* **👀 你會看到什麼**：站在案場南側走道向北與高空仰望，高掛的金色太陽正將光子灑向眼前的深藍色面板陣列。\n"
                "* **🎯 最佳操作時機**：點擊右圖下方 **「▶️ 播放能量轉換動畫」**！感受光子從頭頂俯衝撞進面板，再化為地面藍綠電流奔向高壓電塔的臨場感！"
            )
        elif "無人機鳥瞰" in camera_mode:
            st.info(
                "💡 **【視角導讀：🚁 電廠無人機鳥瞰視角（預設推薦）】**\n\n"
                "* **👀 你會看到什麼**：從空中清楚一覽太陽能電廠的四大設備接力線：**① 太陽能板陣列 (藍) ➔ ② 逆變器 (橘) ➔ ③ 升壓變壓器 (綠) ➔ ④ 台電高壓電塔 (銀)**。\n"
                "* **🎯 最佳操作時機**：初次認識太陽能電廠整體架構與電力線走向時最清晰！"
            )
        else:
            st.info(
                "💡 **【視角導讀：⚡ 追隨電流特寫視角】**\n\n"
                "* **👀 你會看到什麼**：鏡頭拉近至電廠中樞——觀察 **🔵 直流電（DC 直線粒子）** 進入橘色逆變器後，如何被調變為 **🟢 三相交流電（AC 波動粒子）** 並送入綠色升壓變壓器。"
            )
    else:
        camera_mode = "微觀預設"
        st.info(
            "🔬 **【微觀解剖導讀：太陽能板為什麼能捕捉陽光發電？】**\n\n"
            "* **👀 你會看到什麼**：把矽晶圓放大一萬倍的 3D 分層爆炸圖！上方是 **N 型矽（淺藍）**，下方是 **P 型矽（深藍）**，中間夾著黃色的 **P-N 接面內建電場**。\n"
            "* **🎯 最佳操作時機**：點擊右圖下方 **「▶️ 播放動畫」**，觀察金色光子敲出藍色自由電子往上衝、紅色電洞往下跑的分離過程！"
        )

    st.markdown("#### ☀️ 3. 調整日照與電廠設備效率")
    irradiance = st.slider("☀️ 入射陽光強度 G (W/m²)", 200, 1000, 850, step=50)
    panel_eff = st.slider("🟦 ① 太陽能板光電轉換效率 (%)", 15.0, 26.0, 21.5, step=0.5)
    inv_eff = st.slider("🟧 ② 逆變器 (DC ➔ AC) 轉換效率 (%)", 90.0, 99.0, 97.5, step=0.5)
    tx_eff = st.slider("🟩 ③ 升壓變壓器與線路傳輸效率 (%)", 95.0, 99.5, 98.5, step=0.5)

with col_stage:
    if "宏觀尺度" in scene_mode:
        fig_3d, p_dc, p_ac, p_grid = build_macro_plant_3d(irradiance, panel_eff, inv_eff, tx_eff, camera_mode)
        st.plotly_chart(fig_3d, use_container_width=True, key="macro_plant_stage")
    else:
        p_dc = irradiance * 1.0 * (panel_eff / 100.0)
        p_ac = p_dc * (inv_eff / 100.0)
        p_grid = p_ac * (tx_eff / 100.0)
        fig_micro = build_micro_pn_junction_3d(irradiance, panel_eff)
        st.plotly_chart(fig_micro, use_container_width=True, key="micro_pn_stage")

    st.caption("🎬 **互動指南**：播放按鈕與進度時間軸已移至黑底圖表最下方外圍，完全不遮擋 3D 設備！您隨時可用滑鼠左鍵拖曳旋轉、滾輪縮放。")

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
