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
    """建立 3D 長方體設備模型 (用於逆變器、變壓器、半導體層)"""
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

    # [Trace 0] 案場地面與高空天際背景網格
    xg, yg = np.meshgrid(np.linspace(-1.6, 1.6, 12), np.linspace(-1.0, 1.0, 12))
    fig.add_trace(go.Surface(
        x=xg, y=yg, z=np.zeros_like(xg),
        opacity=0.35, showscale=False,
        colorscale=[[0, '#1E293B'], [1, '#334155']],
        hoverinfo='skip', name='案場地面'
    ))

    # [Trace 1] 東西南北與高空太陽標示 (讓案場工程師仰望時有強烈空間感)
    fig.add_trace(go.Scatter3d(
        x=[0.0, 0.0, -1.5, 1.5, -1.0],
        y=[-0.95, 0.95, 0.0, 0.0, -0.55],
        z=[0.05, 0.05, 0.05, 0.05, 1.15],
        mode='text+markers',
        marker=dict(size=[1, 1, 1, 1, 26], color=['#FFF', '#FFF', '#FFF', '#FFF', '#FFEA00']),
        text=[
            '<b>⬇️ 南方 (S) 陽光入射側</b>',
            '<b>⬆️ 北方 (N) 案場走道側</b>',
            '<b>🌅 東方 (E)</b>',
            '<b>🌇 西方 (W)</b>',
            '<b>☀️ 高空太陽 (光子發射源)</b>'
        ],
        textfont=dict(size=[12, 12, 12, 12, 14], color=['#FF6B6B', '#00E5FF', '#FFD700', '#FF8C00', '#FFEA00']),
        showlegend=False
    ))

    # [Trace 2 & 3] 設備 ①：太陽能光電陣列 (PV Array，兩排向南傾斜 20 度的深藍色面板)
    for row_idx, py_c in enumerate([-0.25, 0.20]):
        px_c = -1.0
        w, l = 0.35, 0.16
        tilt = np.radians(22.0)
        vx = [px_c - w, px_c + w, px_c + w, px_c - w]
        vy = [py_c - l*np.cos(tilt), py_c - l*np.cos(tilt), py_c + l*np.cos(tilt), py_c + l*np.cos(tilt)]
        vz = [0.12, 0.12, 0.12 + 2*l*np.sin(tilt), 0.12 + 2*l*np.sin(tilt)]
        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz, i=[0, 0], j=[1, 2], k=[2, 3],
            color='#1D4ED8', opacity=0.92,
            name=f'① 太陽能板陣列 #{row_idx+1} (產生直流電 DC)' if row_idx == 0 else '太陽能板陣列 #2',
            showlegend=(row_idx == 0)
        ))

    # [Trace 4] 設備 ②：智慧逆變器與匯流箱 (Inverter，橘色工業機櫃)
    fig.add_trace(make_3d_box(-0.20, 0.0, 0.16, 0.14, 0.14, 0.16, '#EA580C', '② 逆變器 Inverter (DC 直流轉 AC 交流)'))

    # [Trace 5] 設備 ③：升壓變壓器 (Step-Up Transformer，綠色電力設備箱)
    fig.add_trace(make_3d_box(0.50, 0.0, 0.20, 0.18, 0.18, 0.20, '#059669', '③ 升壓變壓器 (低壓升至 22.8kV 高壓)'))

    # [Trace 6] 設備 ④：台電高壓輸電鐵塔 (Power Grid Tower，銀白色立體桁架結構)
    tx_tower = [
        1.20, 1.30, None, 1.40, 1.30, None, 1.20, 1.30, None, 1.40, 1.30, None,
        1.12, 1.48, None, 1.16, 1.44, None, 1.30, 1.30
    ]
    ty_tower = [
        -0.12, 0.0, None, -0.12, 0.0, None, 0.12, 0.0, None, 0.12, 0.0, None,
        0.0, 0.0, None, 0.0, 0.0, None, 0.0, 0.0
    ]
    tz_tower = [
        0.0, 0.75, None, 0.0, 0.75, None, 0.0, 0.75, None, 0.0, 0.75, None,
        0.48, 0.48, None, 0.65, 0.65, None, 0.0, 0.82
    ]
    fig.add_trace(go.Scatter3d(
        x=tx_tower, y=ty_tower, z=tz_tower,
        mode='lines+markers',
        line=dict(color='#E2E8F0', width=6),
        marker=dict(size=4, color='#38BDF8'),
        name='④ 台電高壓電塔 (併入電網)'
    ))

    # [Trace 7] 設備上方懸浮的 3D 解說牌與即時功率標籤
    p_dc = irradiance * 1.0 * (panel_eff / 100.0)     # 假設 1000 m^2 面積 -> kW
    p_ac = p_dc * (inv_eff / 100.0)
    p_grid = p_ac * (tx_eff / 100.0)

    fig.add_trace(go.Scatter3d(
        x=[-1.0, -0.20, 0.50, 1.30],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.42, 0.42, 0.50, 0.90],
        mode='text',
        text=[
            f"<b>【① 太陽能光電板】</b><br>光電效應產生直流電<br>⚡ DC 輸出: {p_dc:.1f} kW",
            f"<b>【② 逆變器 Inverter】</b><br>DC 直流 ➔ AC 交流 + MPPT<br>⚡ AC 輸出: {p_ac:.1f} kW",
            f"<b>【③ 升壓變壓器】</b><br>380V 升壓至 22.8kV<br>⚡ 高壓輸出: {p_grid:.1f} kW",
            f"<b>【④ 台電高壓電網】</b><br>綠電正式併網供電！<br>🏠 可供 {int(p_grid/1.2)} 戶家庭即時用電"
        ],
        textfont=dict(size=11, color=['#93C5FD', '#FDBA74', '#6EE7B7', '#FDE047']),
        showlegend=False
    ))

    # [Trace 8] 靜態電纜管道 (連接四大設備)
    fig.add_trace(go.Scatter3d(
        x=[-1.0, -0.20, 0.50, 1.30],
        y=[0.0, 0.0, 0.0, 0.0],
        z=[0.16, 0.16, 0.22, 0.55],
        mode='lines',
        line=dict(color='#64748B', width=8),
        name='電力傳輸電纜'
    ))

    # ==================== 動態 Trace：光子降落 ➔ DC 電子 ➔ AC 電流 ➔ 電網 ====================
    dyn_idx = len(fig.data)
    # 初始顯示三種能量粒子
    fig.add_trace(go.Scatter3d(
        x=[-1.0, -0.6, 0.15, 0.90],
        y=[-0.2, 0.0, 0.0, 0.0],
        z=[0.8, 0.16, 0.19, 0.38],
        mode='markers+text',
        marker=dict(size=[14, 12, 14, 16], color=['#FFEA00', '#00E5FF', '#00E676', '#FDE047'], symbol='circle'),
        text=['☀️ 光子 (Photon)', '🔵 DC 直流電子', '🟢 AC 交流電能', '⚡ 高壓綠電'],
        textposition="top center",
        textfont=dict(size=11, color='#FFFFFF'),
        name='動態能量粒子流'
    ))

    # 建立 24 影格無閃爍循環能量流動畫
    frames = []
    slider_steps = []
    n_frames = 24

    for f_i in range(n_frames):
        prog = f_i / float(n_frames - 1)  # 0.0 -> 1.0

        # 1. 天空落下的 4 束金色光子 (從太陽 (-1.0, -0.55, 1.15) 飛向兩排面板 (-1.0, -0.25/0.20, 0.20))
        p_t = (prog * 2.0) % 1.0
        ph_x = [-1.15 + 0.1*k for k in range(4)]
        ph_y = [-0.55 * (1 - p_t) + (-0.25 if k % 2 == 0 else 0.20) * p_t for k in range(4)]
        ph_z = [1.10 * (1 - p_t) + 0.22 * p_t for k in range(4)]

        # 2. 面板到逆變器的藍色 DC 直流電子 (-1.0 -> -0.20)
        dc_t = (prog * 2.0 + 0.3) % 1.0
        dc_x = [-1.0 + 0.80 * ((dc_t + 0.33 * k) % 1.0) for k in range(3)]
        dc_y = [0.0, 0.0, 0.0]
        dc_z = [0.17, 0.17, 0.17]

        # 3. 逆變器到變壓器的綠色 AC 交流弦波粒子 (-0.20 -> 0.50)
        ac_x = [-0.20 + 0.70 * ((prog + 0.25 * k) % 1.0) for k in range(3)]
        ac_y = [0.06 * np.sin(2 * np.pi * ((prog + 0.25 * k) * 2.0)) for k in range(3)]
        ac_z = [0.19, 0.19, 0.19]

        # 4. 變壓器衝向高壓電塔的亮黃色高壓綠電 (0.50 -> 1.30, Z: 0.22 -> 0.55)
        hv_u = [(prog + 0.33 * k) % 1.0 for k in range(3)]
        hv_x = [0.50 + 0.80 * u for u in hv_u]
        hv_y = [0.0, 0.0, 0.0]
        hv_z = [0.22 + 0.33 * u + 0.05 * np.sin(np.pi * u) for u in hv_u]

        all_x = ph_x + dc_x + ac_x + hv_x
        all_y = ph_y + dc_y + ac_y + hv_y
        all_z = ph_z + dc_z + ac_z + hv_z
        all_colors = ['#FFEA00']*4 + ['#00E5FF']*3 + ['#00E676']*3 + ['#FDE047']*3
        all_sizes = [12]*4 + [11]*3 + [13]*3 + [15]*3
        all_texts = ['☀️光子']*4 + ['🔵DC直流']*3 + ['🟢AC交流']*3 + ['⚡高壓電']*3

        stage_label = (
            "① 光子撞擊矽晶圓 (光電效應)" if prog < 0.25 else
            "② 直流電 (DC) 匯流進入逆變器" if prog < 0.50 else
            "③ 逆變器將 DC 轉為三相交流電 (AC)" if prog < 0.75 else
            "④ 變壓器升壓至 22.8kV 併入台電電網！"
        )

        frames.append(go.Frame(
            name=f"Step_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=all_x, y=all_y, z=all_z,
                mode='markers+text',
                marker=dict(size=all_sizes, color=all_colors, symbol='circle'),
                text=all_texts,
                textposition="top center",
                textfont=dict(size=10, color='#FFFFFF')
            )],
            layout=go.Layout(
                title=dict(
                    text=f"<b>⚡ 能量轉換動態模擬：{stage_label} ｜ 最終併網功率：{p_grid:.1f} kW</b>",
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

    # 設定攝影機視角 (包含使用者指定的「案場工程師視角 (由南向北仰望天空)」)
    if "案場工程師視角" in camera_mode:
        # 站在案場南側地面 (y = -1.35, z = 0.12)，往北方與高空仰望 (center z = 0.45)
        cam_eye = dict(x=-0.35, y=-1.35, z=0.12)
        cam_center = dict(x=-0.10, y=0.20, z=0.45)
    elif "追隨電流特寫視角" in camera_mode:
        cam_eye = dict(x=0.15, y=-1.05, z=0.38)
        cam_center = dict(x=0.15, y=0.0, z=0.22)
    else:
        # 電廠無人機鳥瞰視角
        cam_eye = dict(x=0.0, y=-1.85, z=0.95)
        cam_center = dict(x=0.05, y=0.0, z=0.20)

    fig.update_layout(
        title=dict(
            text=f"<b>🏭 3D 太陽能電廠四大設備與能量流 ｜ 即時併網發電：{p_grid:.1f} kW</b>",
            font=dict(size=16, color="#FFD700"), x=0.02, y=0.96
        ),
        height=640, margin=dict(l=0, r=0, b=80, t=45),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.65, 1.65]),
            yaxis=dict(visible=False, range=[-1.1, 1.1]),
            zaxis=dict(visible=False, range=[0.0, 1.25]),
            aspectmode='manual', aspectratio=dict(x=1.5, y=0.9, z=0.65),
            camera=dict(eye=cam_eye, center=cam_center),
            bgcolor='#0E1117'
        ),
        legend=dict(yanchor="top", y=0.92, xanchor="left", x=0.02, font=dict(color="white", size=11), bgcolor="rgba(0,0,0,0.5)"),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.02, y=0.02, xanchor="left", yanchor="bottom", direction="left",
            pad=dict(r=10, t=10), bgcolor="#1E293B", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(
                    label="▶️ 播放「光子 ➔ 電網」能量轉換動畫",
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
            transition=dict(duration=0), pad=dict(b=10, t=10), len=0.65, x=0.32, y=0.02,
            font=dict(color="#CBD5E1", size=10), steps=slider_steps
        )]
    )
    return fig, p_dc, p_ac, p_grid


# ==================== 模式 B：微觀 3D 太陽能板 P-N 接面光電效應解剖舞台 ====================
def build_micro_pn_junction_3d(irradiance, panel_eff):
    fig = go.Figure()

    # 分層繪製太陽能電池 3D 微觀解剖結構
    # 1. 底部鋁背板電極 (Z: 0.0 ~ 0.06)
    fig.add_trace(make_3d_box(0, 0, 0.03, 0.9, 0.6, 0.03, '#64748B', '⑤ 底部金屬背電極 (正極回路)', opacity=0.85))
    # 2. P 型矽半導體層 (含硼 Boron，多電洞 h+，Z: 0.06 ~ 0.30)
    fig.add_trace(make_3d_box(0, 0, 0.18, 0.9, 0.6, 0.12, '#1E3A8A', '④ P 型矽晶圓層 (富含正電洞 h⁺)', opacity=0.45))
    # 3. P-N 接面內建電場區 (空乏區 Depletion Zone，Z: 0.30 ~ 0.42)
    fig.add_trace(make_3d_box(0, 0, 0.36, 0.9, 0.6, 0.06, '#F59E0B', '③ P-N 接面內建電場 (將電子往上推、電洞往下推！)', opacity=0.35))
    # 4. N 型矽半導體層 (含磷 Phosphorus，多自由電子 e-，Z: 0.42 ~ 0.58)
    fig.add_trace(make_3d_box(0, 0, 0.50, 0.9, 0.6, 0.08, '#0284C7', '② N 型矽晶圓層 (富含負電子 e⁻)', opacity=0.45))
    # 5. 頂部抗反射塗層與銀柵線電極 (Z: 0.60)
    for gx in [-0.6, -0.2, 0.2, 0.6]:
        fig.add_trace(make_3d_box(gx, 0, 0.60, 0.03, 0.6, 0.02, '#E2E8F0', '① 頂部銀導電柵線 (收集電子)' if gx == -0.6 else '柵線', opacity=0.95))

    # 剖面結構文字標籤
    fig.add_trace(go.Scatter3d(
        x=[1.05, 1.05, 1.05, 1.05, 1.05],
        y=[0, 0, 0, 0, 0],
        z=[0.60, 0.50, 0.36, 0.18, 0.03],
        mode='text',
        text=[
            '<b>① 頂部導電銀柵線 (負極出口)</b>',
            '<b>② N 型半導體層 (電子富集區)</b>',
            '<b>⚡ ③ P-N 接面 (內建電場核心區)</b>',
            '<b>④ P 型半導體層 (電洞富集區)</b>',
            '<b>⑤ 底部金屬背電極 (正極入口)</b>'
        ],
        textfont=dict(size=12, color=['#FFFFFF', '#38BDF8', '#FDE047', '#93C5FD', '#CBD5E1']),
        showlegend=False
    ))

    # 動態粒子：金色光子往下撞擊 P-N 接面 -> 激發藍色電子往上衝、紅色電洞往下跑
    dyn_idx = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=[-0.4, 0.0, 0.4], y=[0, 0, 0], z=[0.85, 0.36, 0.36],
        mode='markers+text',
        marker=dict(size=14, color=['#FFEA00', '#00E5FF', '#FF5252']),
        text=['☀️ 入射光子 (hv > 1.12eV)', '🔵 被敲出的自由電子 (e⁻ 往上衝)', '🔴 留下的正電洞 (h⁺ 往下跑)'],
        textposition="top center",
        name='微觀光電粒子'
    ))

    frames = []
    slider_steps = []
    for f_i in range(20):
        t_p = f_i / 19.0
        if t_p < 0.45:
            # 階段 1：光子從上方 (z=0.95) 穿透玻璃打向 P-N 接面 (z=0.36)
            u = t_p / 0.45
            z_ph = 0.95 * (1 - u) + 0.36 * u
            xs = [-0.45, 0.0, 0.45]
            ys = [-0.15, 0.15, -0.15]
            zs = [z_ph, z_ph, z_ph]
            cols = ['#FFEA00'] * 3
            txts = ['☀️ 光子俯衝中'] * 3
            stage_msg = "階段 1：能量大於能隙 (1.12 eV) 的光子穿透表面，撞擊矽原子共價鍵！"
        else:
            # 階段 2：激發出「電子-電洞對」，內建電場將電子(藍)推向頂部柵線(z=0.62)，電洞(紅)推向底部背板(z=0.04)
            u = (t_p - 0.45) / 0.55
            z_elec = 0.36 * (1 - u) + 0.62 * u
            z_hole = 0.36 * (1 - u) + 0.04 * u
            xs = [-0.45, 0.0, 0.45, -0.45, 0.0, 0.45]
            ys = [-0.15, 0.15, -0.15, -0.15, 0.15, -0.15]
            zs = [z_elec]*3 + [z_hole]*3
            cols = ['#00E5FF']*3 + ['#FF5252']*3
            txts = ['🔵 自由電子 e⁻ (往N型頂部衝)']*3 + ['🔴 電洞 h⁺ (往P型底部跑)']*3
            stage_msg = "階段 2：光生伏打效應！P-N 接面內建電場將電子與電洞強行分離，形成直流電壓！"

        frames.append(go.Frame(
            name=f"Micro_{f_i}",
            traces=[dyn_idx],
            data=[go.Scatter3d(
                x=xs, y=ys, z=zs, mode='markers+text',
                marker=dict(size=14, color=cols),
                text=txts, textposition="top center", textfont=dict(size=11, color='#FFFFFF')
            )],
            layout=go.Layout(title=dict(text=f"<b>🔬 微觀光電效應：{stage_msg}</b>", font=dict(size=15, color="#FFD700")))
        ))
        slider_steps.append(dict(
            method="animate",
            args=[[f"Micro_{f_i}"], dict(mode="immediate", frame=dict(duration=100, redraw=True), transition=dict(duration=0))],
            label=f"{int(t_p*100)}%"
        ))

    fig.frames = frames
    fig.update_layout(
        title=dict(text="<b>🔬 3D 太陽能電池微觀結構解剖（P-N 接面與光生伏打效應）</b>", font=dict(size=16, color="#FFD700"), x=0.02, y=0.96),
        height=640, margin=dict(l=0, r=0, b=80, t=45), paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.3, 1.4]),
            yaxis=dict(visible=False, range=[-1.0, 1.0]),
            zaxis=dict(visible=False, range=[-0.05, 1.05]),
            aspectmode='manual', aspectratio=dict(x=1.3, y=0.9, z=0.75),
            camera=dict(eye=dict(x=0.35, y=-1.75, z=0.45), center=dict(x=0.1, y=0, z=0.35)),
            bgcolor='#0E1117'
        ),
        legend=dict(yanchor="top", y=0.92, xanchor="left", x=0.02, font=dict(color="white", size=11), bgcolor="rgba(0,0,0,0.5)"),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.02, y=0.02, xanchor="left", yanchor="bottom", direction="left",
            pad=dict(r=10, t=10), bgcolor="#1E293B", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(label="▶️ 播放「光子敲出電子」微觀動畫", method="animate", args=[None, dict(frame=dict(duration=100, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")]),
                dict(label="⏸️ 暫停", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
            ]
        )],
        sliders=[dict(active=0, yanchor="bottom", xanchor="left", currentvalue=dict(font=dict(size=13, color="#FFD700"), prefix="微觀動作：", visible=True, xanchor="right"), len=0.62, x=0.35, y=0.02, steps=slider_steps)]
    )
    return fig


# ==================== 主舞台配置：左拉桿控制台 (1) + 右 3D 主角視覺圖 (2.3) ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="large")

with col_ctrl:
    st.markdown("### 🎛️ 光電轉換與電廠控制台")

    st.markdown("#### 🔍 1. 選擇 3D 探索尺度")
    scene_mode = st.radio(
        "你想觀察哪一個層次的3D模擬？",
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
                "🧍 案場工程師視角 (由南向北仰望天空與太陽能板)",
                "🚁 電廠無人機鳥瞰視角 (全廠四大設備與電網總覽)",
                "⚡ 追隨電流特寫視角 (聚焦逆變器 DC 轉 AC 樞紐)"
            ],
            index=0
        )

        if "案場工程師視角" in camera_mode:
            st.info(
                "💡 **【視角導讀：🧍 案場工程師視角（由南向北仰望天空）】**\n\n"
                "* **👀 你會看到什麼**：模擬你親自戴著工程帽站在案場南側走道，抬頭向北方與高空仰望！高掛在天空的金色太陽正源源不絕將光子灑向眼前的深藍色面板陣列。\n"
                "* **🎯 最佳操作時機**：點擊右圖左下角 **「▶️ 播放能量轉換動畫」**！感受光子從你頭頂天空俯衝而下、撞進面板，再化為地面電纜中的藍綠電流一路奔向遠方高壓電塔的臨場感！"
            )
        elif "無人機鳥瞰" in camera_mode:
            st.info(
                "💡 **【視角導讀：🚁 電廠無人機鳥瞰視角】**\n\n"
                "* **👀 你會看到什麼**：從空中一覽太陽能電廠的四大設備接力線：**① 太陽能板陣列 (藍) ➔ ② 逆變器 (橘) ➔ ③ 升壓變壓器 (綠) ➔ ④ 台電高壓電塔 (銀)**。\n"
                "* **🎯 最佳操作時機**：向初學者介紹「太陽能電廠不是只有面板，還需要逆變器與變壓器才能併網」時的最佳全景圖。"
            )
        else:
            st.info(
                "💡 **【視角導讀：⚡ 追隨電流特寫視角】**\n\n"
                "* **👀 你會看到什麼**：鏡頭特寫電廠中樞——觀察 **🔵 直流電（DC 直線粒子）** 進入橘色逆變器後，如何被調變為 **🟢 三相交流電（AC 波動粒子）** 並送入綠色升壓變壓器。"
            )
    else:
        camera_mode = "微觀預設"
        st.info(
            "🔬 **【微觀解剖導讀：太陽能板為什麼能捕捉陽光發電？】**\n\n"
            "* **👀 你會看到什麼**：我們把一片薄薄的矽晶圓放大一萬倍！上方是富含電子的 **N 型矽（淺藍）**，下方是富含電洞的 **P 型矽（深藍）**，中間夾著黃色的 **P-N 接面內建電場**。\n"
            "* **🎯 最佳操作時機**：點擊右圖左下角 **「▶️ 播放微觀動畫」**，觀察金色光子如何敲出藍色自由電子，並被內建電場強行推往頂部銀柵線形成直流電！"
        )

    st.markdown("#### ☀️ 3. 調整日照與電廠設備效率")
    irradiance = st.slider("☀️ 入射陽光強度 G (W/m²)", 200, 1000, 850, step=50)
    panel_eff = st.slider("🟦 ① 太陽能板光電轉換效率 (%)", 15.0, 26.0, 21.5, step=0.5, help="商用單晶矽太陽能板效率約 20%~23%，理論極限(S-Q Limit)約 33.7%")
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

    st.caption("🎬 **互動指南**：點擊上方 3D 圖左下角的 **「▶️ 播放動畫」** 即可觀看無閃爍粒子流動；亦可用滑鼠左鍵自由旋轉 3D 視角！")

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
        st.caption("👉 為什麼面板轉換效率只有 21% 左右？因為紅外線光子能量太低敲不動電子，而紫外線光子能量太高，多餘的能量會變成「熱」散失掉（這就是下一章面板會發燙的主因！）。")

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
