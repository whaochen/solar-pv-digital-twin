import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 2 章：大氣層與光線的捕捉", page_icon="🌻", layout="wide")

# 緊湊化版面與高亮度數據卡 CSS
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
    .bright-val-blue { color: #60A5FA !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-val-green { color: #00E676 !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-val-gold { color: #FFD700 !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-sub { color: #94A3B8 !important; font-size: 0.82rem; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：故事引導 ====================
st.markdown("### 第二章：【穿越】大氣層與光線的捕捉（太陽光 ➔ 面板幾何）")
st.info(
    "🌟 **【故事引導】** 光子穿過厚重的大氣層後，分成了兩支隊伍：一支依然筆直前進，稱為**「直射光（DNI）」**；"
    "另一支被雲氣與空氣分子撞散，從四面八方溫柔落下，稱為**「散射光（DHI）」**。"
    "地面上的太陽能板究竟是要**站在原地傻傻地等（固定式）**，還是**像向日葵一樣轉頭迎接，把早晚斜射的陽光「扳正」（追日系統）**？"
)

# ==================== 核心物理與 3D 幾何計算函數 ====================
def calc_sun_vector(day_n, hours_arr, phi_deg):
    """計算太陽單位向量 S = [Sx(東), Sy(北), Sz(天頂)] 與赤緯角"""
    h_arr = np.atleast_1d(hours_arr).astype(float)
    phi_r = np.radians(phi_deg)
    d_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + day_n)))
    d_rad = np.radians(d_deg)
    w_rad = np.radians(15.0 * (h_arr - 12.0))

    sz = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    sx = -np.cos(d_rad) * np.sin(w_rad)
    sy = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    return sx, sy, sz, float(d_deg)


def calc_tracker_normals_and_poa(sx, sy, sz, fixed_tilt_deg, dni, dhi, max_track_deg=60.0):
    """計算固定式、單軸、雙軸的法向量、入射角餘弦 cos(theta_i) 與 POA 總輻照度"""
    sx = np.atleast_1d(sx).astype(float)
    sy = np.atleast_1d(sy).astype(float)
    sz = np.atleast_1d(sz).astype(float)
    dni_arr = np.atleast_1d(dni).astype(float)
    dhi_arr = np.atleast_1d(dhi).astype(float)

    is_day = sz > 0.01
    beta_r = np.radians(fixed_tilt_deg)

    # 1. 固定式 (朝正南傾斜 beta)
    nx_fix = np.zeros_like(sx)
    ny_fix = np.full_like(sy, -np.sin(beta_r))
    nz_fix = np.full_like(sz, np.cos(beta_r))
    cos_fix = np.where(is_day, np.clip(sx * nx_fix + sy * ny_fix + sz * nz_fix, 0.0, 1.0), 0.0)

    # 2. 單軸追日 (水平南北軸東西向轉動)
    max_r = np.radians(max_track_deg)
    rho = np.where(is_day, np.clip(np.arctan2(sx, np.maximum(sz, 1e-4)), -max_r, max_r), 0.0)
    nx_1ax = np.sin(rho)
    ny_1ax = np.zeros_like(sy)
    nz_1ax = np.cos(rho)
    cos_1ax = np.where(is_day, np.clip(sx * nx_1ax + sy * ny_1ax + sz * nz_1ax, 0.0, 1.0), 0.0)

    # 3. 雙軸追日 (全天候垂直對準太陽)
    nx_2ax = np.where(is_day, sx, 0.0)
    ny_2ax = np.where(is_day, sy, -np.sin(beta_r))
    nz_2ax = np.where(is_day, sz, np.cos(beta_r))
    cos_2ax = np.where(is_day, 1.0, 0.0)

    # POA 總輻照度
    poa_fix = np.where(is_day, dni_arr * cos_fix + dhi_arr * (1.0 + nz_fix) / 2.0, 0.0)
    poa_1ax = np.where(is_day, dni_arr * cos_1ax + dhi_arr * (1.0 + nz_1ax) / 2.0, 0.0)
    poa_2ax = np.where(is_day, dni_arr * cos_2ax + dhi_arr * (1.0 + nz_2ax) / 2.0, 0.0)

    return (
        (nx_fix, ny_fix, nz_fix, cos_fix, poa_fix),
        (nx_1ax, ny_1ax, nz_1ax, cos_1ax, poa_1ax),
        (nx_2ax, ny_2ax, nz_2ax, cos_2ax, poa_2ax)
    )


def make_panel_mesh_vertices(center_x, center_y, center_z, nx, ny, nz, w=0.22, h=0.16):
    """根據面板中心點與法向量 N=(nx,ny,nz)，計算 3D 矩形面板的 4 個頂點與法向量箭頭"""
    N = np.array([float(nx), float(ny), float(nz)], dtype=float)
    norm_len = np.linalg.norm(N)
    if norm_len < 1e-6 or N[2] < 0:
        N = np.array([0.0, 0.0, 1.0])
    else:
        N = N / norm_len

    ref = np.array([0.0, 1.0, 0.0]) if abs(N[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    U = np.cross(ref, N)
    U = U / np.linalg.norm(U)
    V = np.cross(N, U)

    C = np.array([center_x, center_y, center_z], dtype=float)
    p0 = C - w * U - h * V
    p1 = C + w * U - h * V
    p2 = C + w * U + h * V
    p3 = C - w * U + h * V

    vx = [float(p0[0]), float(p1[0]), float(p2[0]), float(p3[0])]
    vy = [float(p0[1]), float(p1[1]), float(p2[1]), float(p3[1])]
    vz = [float(p0[2]), float(p1[2]), float(p2[2]), float(p3[2])]
    arrow_tip = C + 0.28 * N
    return vx, vy, vz, C, arrow_tip


def build_3d_tracker_arena(day_n, phi_deg, hour_t, fixed_tilt_deg, dni_peak, dhi_base, camera_mode):
    """建構無閃爍 WebGL 3D 追日同場競技舞台 (播放鍵與暫停鍵置於上方)"""
    sx_arr, sy_arr, sz_arr, delta_deg = calc_sun_vector(day_n, np.array([hour_t]), phi_deg)
    sx, sy, sz = float(sx_arr.flat[0]), float(sy_arr.flat[0]), float(sz_arr.flat[0])
    is_day = sz > 0.02

    am_val = float(np.power(np.clip(sz, 0.02, 1.0), 0.35)) if is_day else 0.0
    cur_dni = float(dni_peak * am_val) if is_day else 0.0
    cur_dhi = float(dhi_base * (0.4 + 0.6 * max(0.0, sz))) if is_day else 0.0

    fix_res, ax1_res, ax2_res = calc_tracker_normals_and_poa(
        sx, sy, sz, fixed_tilt_deg, cur_dni, cur_dhi
    )

    fig = go.Figure()

    # [Trace 0] 地面競技場底座
    xg, yg = np.meshgrid(np.linspace(-1.35, 1.35, 10), np.linspace(-0.9, 0.9, 10))
    fig.add_trace(go.Surface(
        x=xg, y=yg, z=np.zeros_like(xg),
        opacity=0.35, showscale=False,
        colorscale=[[0, '#1E293B'], [1, '#334155']],
        hoverinfo='skip', name='競技場地面'
    ))

    # [Trace 1] 東西南北方位與三座基座標籤
    fig.add_trace(go.Scatter3d(
        x=[1.28, -1.28, 0, 0, -0.75, 0.0, 0.75],
        y=[0, 0, 0.82, -0.82, -0.42, -0.42, -0.42],
        z=[0.05, 0.05, 0.05, 0.05, 0.02, 0.02, 0.02],
        mode='text',
        text=[
            '<b>🌅 東方 (E)</b>', '<b>🌇 西方 (W)</b>', '<b>⬆️ 北方 (N)</b>', '<b>⬇️ 南方 (S)</b>',
            '<b>🟦 ① 固定式<br>(朝南固定傾角)</b>',
            '<b>🟩 ② 單軸追日<br>(東西向轉頭)</b>',
            '<b>🟧 ③ 雙軸追日<br>(全天候垂直鎖定)</b>'
        ],
        textfont=dict(
            size=[12, 12, 11, 11, 11, 11, 11],
            color=['#FFD700', '#FF8C00', '#00E5FF', '#FF6B6B', '#60A5FA', '#34D399', '#FBBF24']
        ),
        showlegend=False
    ))

    # [Trace 2] 當日太陽高空軌跡弧線
    t_full = np.linspace(5.5, 18.5, 131)
    tsx, tsy, tsz, _ = calc_sun_vector(day_n, t_full, phi_deg)
    m_day = tsz >= 0
    fig.add_trace(go.Scatter3d(
        x=tsx[m_day] * 1.15, y=tsy[m_day] * 0.75, z=tsz[m_day] * 0.85 + 0.15,
        mode='lines', line=dict(color='rgba(255, 215, 0, 0.45)', width=5, dash='dot'),
        name='太陽今日軌跡'
    ))

    # [Trace 3] 三座太陽能板的立柱支架
    fig.add_trace(go.Scatter3d(
        x=[-0.75, -0.75, None, 0.0, 0.0, None, 0.75, 0.75],
        y=[0, 0, None, 0, 0, None, 0, 0],
        z=[0, 0.18, None, 0, 0.18, None, 0, 0.18],
        mode='lines', line=dict(color='#94A3B8', width=9),
        showlegend=False, hoverinfo='skip'
    ))

    centers_x = [-0.75, 0.0, 0.75]
    colors_panel = ['#2563EB', '#059669', '#D97706']
    names_panel = ['① 固定式面板', '② 單軸追日面板', '③ 雙軸追日面板']
    normals_now = [
        (float(fix_res[0].flat[0]), float(fix_res[1].flat[0]), float(fix_res[2].flat[0])),
        (float(ax1_res[0].flat[0]), float(ax1_res[1].flat[0]), float(ax1_res[2].flat[0])),
        (float(ax2_res[0].flat[0]), float(ax2_res[1].flat[0]), float(ax2_res[2].flat[0]))
    ]

    dynamic_trace_indices = []

    # [動態 Trace A, B, C] 三塊 3D 太陽能板 Mesh3d
    for idx in range(3):
        nx_i, ny_i, nz_i = normals_now[idx]
        vx, vy, vz, _, _ = make_panel_mesh_vertices(centers_x[idx], 0.0, 0.18, nx_i, ny_i, nz_i)
        dynamic_trace_indices.append(len(fig.data))
        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz,
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=colors_panel[idx], opacity=0.92,
            name=names_panel[idx], showscale=False
        ))

    # [動態 Trace D] 面板綠色法向量箭頭
    norm_lines_x, norm_lines_y, norm_lines_z = [], [], []
    for idx in range(3):
        nx_i, ny_i, nz_i = normals_now[idx]
        _, _, _, c_pt, tip_pt = make_panel_mesh_vertices(centers_x[idx], 0.0, 0.18, nx_i, ny_i, nz_i)
        norm_lines_x.extend([float(c_pt[0]), float(tip_pt[0]), None])
        norm_lines_y.extend([float(c_pt[1]), float(tip_pt[1]), None])
        norm_lines_z.extend([float(c_pt[2]), float(tip_pt[2]), None])

    dynamic_trace_indices.append(len(fig.data))
    fig.add_trace(go.Scatter3d(
        x=norm_lines_x, y=norm_lines_y, z=norm_lines_z,
        mode='lines+markers',
        line=dict(color='#00FFCC', width=6),
        marker=dict(size=4, color='#00FFCC'),
        name='面板法向量 n'
    ))

    # [動態 Trace E] 太陽球體與打向三塊面板的金色直射光束
    sun_pos = [sx * 1.15, sy * 0.75, max(0.05, sz * 0.85 + 0.15)]
    beam_x, beam_y, beam_z = [], [], []
    for cx_p in centers_x:
        beam_x.extend([cx_p, sun_pos[0], None])
        beam_y.extend([0.0, sun_pos[1], None])
        beam_z.extend([0.18, sun_pos[2], None])

    dynamic_trace_indices.append(len(fig.data))
    fig.add_trace(go.Scatter3d(
        x=beam_x, y=beam_y, z=beam_z,
        mode='lines+markers',
        line=dict(color='#FFEA00' if is_day else 'rgba(120,120,120,0.2)', width=5),
        marker=dict(size=6, color='#FFEA00' if is_day else '#555555'),
        name='太陽直射光束 (DNI)'
    ))

    # 建立 WebGL 無閃爍動畫 Frames (06:00 ~ 18:00)
    anim_hours = np.arange(6.0, 18.25, 0.25)
    frames = []
    slider_steps = []

    for h_val in anim_hours:
        hsx_a, hsy_a, hsz_a, _ = calc_sun_vector(day_n, np.array([h_val]), phi_deg)
        hsx, hsy, hsz = float(hsx_a.flat[0]), float(hsy_a.flat[0]), float(hsz_a.flat[0])
        h_day = hsz > 0.02
        h_am = float(np.power(np.clip(hsz, 0.02, 1.0), 0.35)) if h_day else 0.0
        h_dni = float(dni_peak * h_am)
        h_dhi = float(dhi_base * (0.4 + 0.6 * max(0.0, hsz))) if h_day else 0.0

        f_fix, f_1ax, f_2ax = calc_tracker_normals_and_poa(
            hsx, hsy, hsz, fixed_tilt_deg, h_dni, h_dhi
        )
        f_normals = [
            (float(f_fix[0].flat[0]), float(f_fix[1].flat[0]), float(f_fix[2].flat[0])),
            (float(f_1ax[0].flat[0]), float(f_1ax[1].flat[0]), float(f_1ax[2].flat[0])),
            (float(f_2ax[0].flat[0]), float(f_2ax[1].flat[0]), float(f_2ax[2].flat[0]))
        ]

        frame_data = []
        f_nlx, f_nly, f_nlz = [], [], []
        for idx in range(3):
            vx, vy, vz, c_pt, tip_pt = make_panel_mesh_vertices(
                centers_x[idx], 0.0, 0.18, f_normals[idx][0], f_normals[idx][1], f_normals[idx][2]
            )
            frame_data.append(go.Mesh3d(x=vx, y=vy, z=vz))
            f_nlx.extend([float(c_pt[0]), float(tip_pt[0]), None])
            f_nly.extend([float(c_pt[1]), float(tip_pt[1]), None])
            f_nlz.extend([float(c_pt[2]), float(tip_pt[2]), None])

        frame_data.append(go.Scatter3d(x=f_nlx, y=f_nly, z=f_nlz))

        h_sun_pos = [hsx * 1.15, hsy * 0.75, max(0.05, hsz * 0.85 + 0.15)]
        f_bx, f_by, f_bz = [], [], []
        for cx_p in centers_x:
            f_bx.extend([cx_p, h_sun_pos[0], None])
            f_by.extend([0.0, h_sun_pos[1], None])
            f_bz.extend([0.18, h_sun_pos[2], None])

        frame_data.append(go.Scatter3d(
            x=f_bx, y=f_by, z=f_bz,
            line=dict(color='#FFEA00' if h_day else 'rgba(120,120,120,0.2)', width=5),
            marker=dict(size=6, color='#FFEA00' if h_day else '#555555')
        ))

        h_str = f"{int(h_val):02d}:{int((h_val%1)*60):02d}"
        c_fix_val = float(f_fix[3].flat[0]) * 100.0
        c_1ax_val = float(f_1ax[3].flat[0]) * 100.0
        c_2ax_val = float(f_2ax[3].flat[0]) * 100.0
        frames.append(go.Frame(
            name=h_str,
            traces=dynamic_trace_indices,
            data=frame_data,
            layout=go.Layout(
                title=dict(
                    text=(
                        f"<b>🕒 {h_str} 受光率 cos(θi) ｜ "
                        f"🟦固定: {c_fix_val:.0f}% vs 🟩單軸: {c_1ax_val:.0f}% vs 🟧雙軸: {c_2ax_val:.0f}%</b>"
                    ),
                    font=dict(size=15, color="#FFD700")
                )
            )
        ))

        slider_steps.append(dict(
            method="animate",
            args=[[h_str], dict(mode="immediate", frame=dict(duration=70, redraw=True), transition=dict(duration=0))],
            label=h_str
        ))

    fig.frames = frames

    # 設定攝影機視角
    if "光子第一人稱視角" in camera_mode:
        cam_eye = dict(x=sx * 1.55, y=sy * 1.55 - 0.15, z=max(0.32, sz * 1.55))
        cam_center = dict(x=0.0, y=0.0, z=0.14)
    elif "由北向南全景視角" in camera_mode:
        cam_eye = dict(x=0.0, y=1.65, z=0.52)
        cam_center = dict(x=0.0, y=-0.05, z=0.18)
    else:
        cam_eye = dict(x=0.12, y=-1.65, z=0.62)
        cam_center = dict(x=0.0, y=0.0, z=0.16)

    c0 = float(fix_res[3].flat[0]) * 100.0
    c1 = float(ax1_res[3].flat[0]) * 100.0
    c2 = float(ax2_res[3].flat[0]) * 100.0
    fig.update_layout(
        title=dict(
            text=(
                f"<b>🕒 {int(hour_t):02d}:{int((hour_t%1)*60):02d} 受光率 cos(θi) ｜ "
                f"🟦固定: {c0:.0f}% vs 🟩單軸: {c1:.0f}% vs 🟧雙軸: {c2:.0f}%</b>"
            ),
            font=dict(size=15, color="#FFD700"),
            x=0.02, y=0.96
        ),
        height=440,
        margin=dict(l=0, r=0, b=55, t=40),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.38, 1.38]),
            yaxis=dict(visible=False, range=[-0.95, 0.95]),
            zaxis=dict(visible=False, range=[0.0, 1.12]),
            aspectmode='manual',
            aspectratio=dict(x=1.35, y=0.9, z=0.62),
            camera=dict(eye=cam_eye, center=cam_center),
            bgcolor='#0E1117'
        ),
        legend=dict(orientation="h", yanchor="top", y=0.90, xanchor="left", x=0.02, font=dict(color="white", size=11), bgcolor="rgba(15,23,42,0.75)"),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.98, y=0.98, xanchor="right", yanchor="top", direction="left",
            pad=dict(r=5, t=0), bgcolor="#2563EB", font=dict(color="#FFFFFF", size=13),
            buttons=[
                dict(
                    label="▶️ 播放一日追日對決",
                    method="animate",
                    args=[None, dict(frame=dict(duration=80, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")]
                ),
                dict(
                    label="⏸️ 暫停",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )],
        sliders=[dict(
            active=int(np.clip((hour_t - 6.0) / 0.25, 0, len(slider_steps) - 1)),
            yanchor="bottom", xanchor="left",
            currentvalue=dict(font=dict(size=12, color="#FFD700"), prefix="動畫時間軸：", visible=True, xanchor="right"),
            transition=dict(duration=0),
            pad=dict(b=2, t=2), len=0.94, x=0.03, y=-0.05,
            font=dict(color="#CBD5E1", size=10),
            steps=slider_steps
        )]
    )

    return fig, fix_res, ax1_res, ax2_res, cur_dni, cur_dhi

# ==================== 上半部主舞台：左拉桿控制台 (1.05) + 右 3D 追日競技場 (2.25) ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="medium")

with col_ctrl:
    st.markdown("##### 🎥 1. 切換 3D 觀察視角（含學習導讀）")
    camera_mode = st.radio(
        "選擇教學鏡頭：",
        [
            "🏟️ 競技場正面鳥瞰 (觀察三板同步轉動)",
            "☀️ 光子第一人稱視角 (直擊餘弦投影面積差異！)",
            "🌅 由北向南全景視角 (左東升 ➔ 右西落)"
        ],
        index=0,
        label_visibility="collapsed"
    )

    if "正面鳥瞰" in camera_mode:
        st.caption(
            "💡 **視角導讀**：同時比較 **🟦固定式（左）**、**🟩單軸（中）** 與 **🟧雙軸（右）** 的面板姿態。"
            "點擊右圖右上角 **▶️ 播放一日追日對決** 最能觀察單軸與雙軸如何跟著太陽轉頭！"
        )
    elif "光子第一人稱視角" in camera_mode:
        st.caption(
            "🔥 **本章靈魂視角**：鏡頭架在太陽往下看三塊板子！**請將下方定格時間拉到「07:30」**："
            "你會看到🟦固定式變成窄窄一條線（面積剩 30%），而🟧雙軸呈現最飽滿正方形（面積 100%）！"
        )
    else:
        st.caption(
            "💡 **視角導讀**：左邊東方日出、右邊西方日落，從面板背面觀察單軸追日系統如何像蹺蹺板一樣「早往東傾、晚往西傾」。"
        )

    st.markdown("##### 🌤️ 2. 大氣層雲霧與季節設定")
    c_w1, c_w2 = st.columns([1.2, 1.0])
    with c_w1:
        weather_preset = st.selectbox(
            "大氣雲霧狀態 (DNI / DHI)",
            [
                "☀️ 晴朗無雲 (高直射 DNI)",
                "⛅ 薄雲微霾 (中直射 DNI)",
                "☁️ 陰天厚雲 (全散射 DHI)"
            ],
            index=0
        )
    weather_map = {
        "☀️ 晴朗無雲 (高直射 DNI)": (850.0, 120.0),
        "⛅ 薄雲微霾 (中直射 DNI)": (550.0, 260.0),
        "☁️ 陰天厚雲 (全散射 DHI)": (80.0, 350.0)
    }
    dni_peak, dhi_base = weather_map[weather_preset]

    with c_w2:
        season_opt = st.selectbox(
            "選擇季節",
            ["☀️ 夏至 (6/21)", "🌸 春/秋分", "❄️ 冬至 (12/21)"],
            index=0
        )
    day_n = {"☀️ 夏至 (6/21)": 172, "🌸 春/秋分": 80, "❄️ 冬至 (12/21)": 355}[season_opt]

    st.markdown("##### 🔧 3. 面板傾角與定格時刻 (連動下方公式)")
    fixed_tilt_deg = st.slider("🟦 固定傾角 β (°)", 0.0, 45.0, 20.0, step=2.5)
    
    # 建立 06:00 到 18:00（間距 15 分鐘）的時間選項列表
    tracker_time_options = []
    for h in range(6, 19):
        for m in [0, 15, 30, 45]:
            if h == 18 and m > 0:
                continue
            tracker_time_options.append(f"{h:02d}:{m:02d}")
            
    selected_t2_str = st.selectbox("⏰ 定格觀察時刻 (推薦 07:30 比較！)", tracker_time_options, index=6) # 預設 07:30
    th, tm = map(int, selected_t2_str.split(":"))
    hour_t = float(th) + float(tm) / 60.0
    phi_deg = 23.15

with col_stage:
    fig_arena, fix_res, ax1_res, ax2_res, cur_dni, cur_dhi = build_3d_tracker_arena(
        day_n, phi_deg, hour_t, fixed_tilt_deg, dni_peak, dhi_base, camera_mode
    )
    st.plotly_chart(fig_arena, use_container_width=True, key="tracker_arena_3d")

# ==================== 中段：高亮度即時數據 ＋ 物理公式白話導讀（正下方一體化連動） ====================
t_day = np.linspace(5.5, 18.5, 131)
sx_d, sy_d, sz_d, _ = calc_sun_vector(day_n, t_day, phi_deg)
am_d = np.where(sz_d > 0.02, np.power(np.clip(sz_d, 0.02, 1.0), 0.35), 0.0)
dni_d = dni_peak * am_d
dhi_d = np.where(sz_d > 0.02, dhi_base * (0.4 + 0.6 * np.maximum(0.0, sz_d)), 0.0)
fix_d, ax1_d, ax2_d = calc_tracker_normals_and_poa(sx_d, sy_d, sz_d, fixed_tilt_deg, dni_d, dhi_d)

dt_hr = float(t_day[1] - t_day[0])
energy_fix = float(np.sum(fix_d[4]) * dt_hr / 1000.0)
energy_1ax = float(np.sum(ax1_d[4]) * dt_hr / 1000.0)
energy_2ax = float(np.sum(ax2_d[4]) * dt_hr / 1000.0)
gain_1ax = ((energy_1ax - energy_fix) / max(energy_fix, 1e-4)) * 100.0
gain_2ax = ((energy_2ax - energy_fix) / max(energy_fix, 1e-4)) * 100.0

cos_fix_now = float(fix_res[3].flat[0]) * 100.0
cos_1ax_now = float(ax1_res[3].flat[0]) * 100.0
cos_2ax_now = float(ax2_res[3].flat[0]) * 100.0
poa_fix_now = float(fix_res[4].flat[0])
poa_1ax_now = float(ax1_res[4].flat[0])
poa_2ax_now = float(ax2_res[4].flat[0])
theta_fix_deg = float(np.degrees(np.arccos(np.clip(cos_fix_now / 100.0, 0.0, 1.0))))

f1, f2, f3 = st.columns(3, gap="medium")

with f1:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🟦 ① 固定式系統 (傾角 {fixed_tilt_deg:.0f}°) —— 餘弦損失基準</div>
        <div class="bright-val-blue">受光率 {cos_fix_now:.1f}% <span style="font-size:1rem;color:#F8FAFC;font-weight:500;">｜ 夾角 θi = {theta_fix_deg:.1f}°</span></div>
        <div class="bright-sub">當前輻照度：{poa_fix_now:.0f} W/m² ｜ 今日累積：{energy_fix:.2f} kWh/m²</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【① 什麼是餘弦損失 Cosine Loss？】** 光線斜射時被攤平在更大面積上，受光率為太陽光 $\\vec{S}$ 與面板法向量 $\\vec{n}$ 夾角餘弦值：")
        st.latex(r"\eta_{\text{cosine}} = \cos\theta_i = \vec{S} \cdot \vec{n}")
        st.latex(rf"\theta_i = \color{{orange}}{{{theta_fix_deg:.1f}^\circ}} \implies \cos\theta_i = \color{{deepskyblue}}{{{cos_fix_now:.1f}\%}}")

with f2:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🟩 ② 單軸追日系統 (東西向轉頭) —— 大氣直射+散射</div>
        <div class="bright-val-green">{poa_1ax_now:.0f} W/m² <span style="font-size:1rem;color:#FFD700;font-weight:600;">｜ 受光率 {cos_1ax_now:.1f}%</span></div>
        <div class="bright-sub">今日累積：{energy_1ax:.2f} kWh/m² (較固定式增益 +{gain_1ax:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【② 大氣層雙胞胎：DNI 直射 + DHI 散射】** 面板總輻照度 $G_{\\text{POA}}$ 為需要對準角度的直射光加上均勻散射光：")
        st.latex(r"G_{\text{POA}} = \text{DNI} \cdot \cos\theta_i + \text{DHI} \cdot \left(\frac{1 + \cos\beta}{2}\right)")
        st.latex(rf"G_{{\text{{POA,固定}}}} = \color{{gold}}{{{cur_dni:.0f}}}\times\color{{deepskyblue}}{{{cos_fix_now/100.0:.2f}}} + \color{{limegreen}}{{{cur_dhi:.0f}}}\times 0.97 = \color{{red}}{{{poa_fix_now:.0f}\text{{ W/m}}^2}}")

with f3:
    st.markdown(f"""
    <div class="bright-card">
        <div class="bright-title">🟧 ③ 雙軸追日向日葵 (全向鎖定) —— 全日總發電增益</div>
        <div class="bright-val-gold">+{gain_2ax:.1f}% 增益 <span style="font-size:1rem;color:#00E676;font-weight:600;">｜ 單軸 +{gain_1ax:.1f}%</span></div>
        <div class="bright-sub">雙軸當前：{poa_2ax_now:.0f} W/m² (受光率 {cos_2ax_now:.0f}%) ｜ 累積：{energy_2ax:.2f} kWh/m²</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("**【③ 為什麼追日能多榨出 25%~30% 電力？】** 把早晚斜射浪費的 $\\cos\\theta_i$ 扳正回 $100\\%$，讓發電曲線變成寬廣「胖鐘型」：")
        st.latex(r"\text{Gain}_{\%} = \frac{\int G_{\text{POA, Tracker}}\,dt - \int G_{\text{POA, Fixed}}\,dt}{\int G_{\text{POA, Fixed}}\,dt}")
        st.latex(rf"\text{{單軸增益}} = \color{{limegreen}}{{+{gain_1ax:.1f}\%}}, \quad \text{{雙軸增益}} = \color{{orange}}{{+{gain_2ax:.1f}\%}}")

# ==================== 底部：左解說導引 (1.0) + 右高挑飽滿「胖鐘型曲線圖」(1.85) ====================
st.markdown("---")
col_guide, col_curve = st.columns([1.0, 1.85], gap="large")

with col_guide:
    with st.container(border=True):
        st.markdown("#### 📖 「胖鐘型發電曲線」觀圖導引")
        st.markdown(
            "為什麼太陽能工程師稱追日系統為**「削峰填谷、拉寬肩膀」**的神器？請對照右側曲線觀察 **3 個關鍵時刻**：\n\n"
            "1. **🌅 早晨（06:30 ~ 10:00）與 🌇 傍晚（14:00 ~ 17:30）**：\n"
            "   * **🟦 固定式（藍線）** 因為面朝南方不動，早晚陽光從東、西兩側斜射擦過，曲線像「瘦高的山峰」，兩側肩膀嚴重凹陷。\n"
            "   * **🟩 單軸（綠虛線）** 與 **🟧 雙軸（橘線）** 轉頭迎光，硬生生把早晚的曲線「撐起來」，多吃進大片**綠色與橘色陰影面積（多榨出 $+25\\% \\sim +40\\%$ 電能）**！\n"
            "2. **☀️ 正午 12:00 巔峰時刻**：\n"
            "   * 三條曲線在中午幾乎交會！代表正午陽光直射時，固定式表現並不輸追日系統。\n"
            "3. **电网價值（傍晚尖峰供電）**：\n"
            "   * 台灣電力系統最缺電的時刻是**下午 15:00 ~ 17:30（日落前冷氣負載仍高）**，追日系統在傍晚多發出的電力對穩定電網價值連城！"
        )
        st.info(
            f"🎯 **當前定格時刻（{int(hour_t):02d}:{int((hour_t%1)*60):02d}）即時比對**：\n"
            f"* 🟦 固定式：**{poa_fix_now:.0f} W/m²**\n"
            f"* 🟩 單軸追日：**{poa_1ax_now:.0f} W/m²**（多拿 **+{poa_1ax_now - poa_fix_now:.0f} W/m²**）\n"
            f"* 🟧 雙軸追日：**{poa_2ax_now:.0f} W/m²**（多拿 **+{poa_2ax_now - poa_fix_now:.0f} W/m²**）"
        )

with col_curve:
    fig_curve = go.Figure()

    # 1. 固定式 (清透皇家藍填色)
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=fix_d[4], mode='lines',
        line=dict(color='#1D4ED8', width=3.5),
        fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.16)',
        name=f'🟦 固定式 ({fixed_tilt_deg:.0f}° 傾角：{energy_fix:.2f} kWh/m²)'
    ))

    # 2. 單軸追日 (鮮明翡翠綠虛線 + 增益面積填色)
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=ax1_d[4], mode='lines',
        line=dict(color='#059669', width=3.5, dash='dash'),
        fill='tonexty', fillcolor='rgba(16, 185, 129, 0.22)',
        name=f'🟩 單軸追日 (+{gain_1ax:.1f}% 增益：{energy_1ax:.2f} kWh/m²)'
    ))

    # 3. 雙軸追日 (高飽和琥珀橘實線 + 額外增益填色)
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=ax2_d[4], mode='lines',
        line=dict(color='#D97706', width=4),
        fill='tonexty', fillcolor='rgba(245, 158, 11, 0.25)',
        name=f'🟧 雙軸追日 (+{gain_2ax:.1f}% 增益：{energy_2ax:.2f} kWh/m²)'
    ))

    # 標示當前選擇時刻的醒目垂直指標線
    fig_curve.add_vline(
        x=hour_t, line_width=2.5, line_dash="dot", line_color="#DC2626",
        annotation_text=f"<b>⏰ 定格時刻 {int(hour_t):02d}:{int((hour_t%1)*60):02d}</b>",
        annotation_position="top left",
        annotation_font=dict(color="#DC2626", size=13)
    )

    # 採用清爽高對比白底科研主題，徹底解決亮色模式黑字撞黑底與標題重疊問題！
    fig_curve.update_layout(
        title=dict(
            text="<b>📊 三種系統全日接收總輻照度 POA (W/m²) 同場對決</b>",
            font=dict(size=17, color="#0F172A"),
            x=0.02, y=0.96
        ),
        xaxis=dict(
            title=dict(text="<b>太陽時間 (小時)</b>", font=dict(color="#1E293B", size=13)),
            tickfont=dict(color="#334155", size=12),
            gridcolor="#E2E8F0", zerolinecolor="#CBD5E1",
            dtick=2
        ),
        yaxis=dict(
            title=dict(text="<b>面板有效總輻照度 POA (W/m²)</b>", font=dict(color="#1E293B", size=13)),
            tickfont=dict(color="#334155", size=12),
            gridcolor="#E2E8F0", zerolinecolor="#CBD5E1",
            range=[0, max(1080.0, float(np.max(ax2_d[4])) * 1.12)]
        ),
        height=450,
        margin=dict(l=60, r=25, t=85, b=50),
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#F8FAFC',
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0.0,
            font=dict(color="#0F172A", size=12),
            bgcolor="rgba(241, 245, 249, 0.9)",
            bordercolor="#CBD5E1", borderwidth=1
        )
    )
    st.plotly_chart(fig_curve, use_container_width=True)
