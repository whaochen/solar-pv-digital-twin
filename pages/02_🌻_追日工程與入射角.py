import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="第 2 章：大氣層與光線的捕捉", page_icon="🌻", layout="wide")

# ==================== 頂部：故事引導 ====================
st.title("第二章：【穿越】大氣層與光線的捕捉（太陽光 ➔ 面板幾何）")
st.info(
    "🌟 **【故事引導】** 光子穿過厚重的大氣層後，分成了兩支隊伍：一支依然筆直前進，稱為**「直射光（DNI）」**；"
    "另一支被雲氣與空氣分子撞散，從四面八方溫柔落下，稱為**「散射光（DHI）」**。\n\n"
    "這時，地面上的太陽能板正等著接住它們——究竟是要**站在原地傻傻地等（固定式）**，"
    "還是要**像向日葵一樣轉頭迎接，把早晚斜射的陽光「扳正」（追日系統）**？讓我們進入 3D 競技場一探究竟！"
)

# ==================== 核心物理與 3D 幾何計算函數 ====================
def calc_sun_vector(day_n, hours_arr, phi_deg):
    """計算太陽單位向量 S = [Sx(東), Sy(北), Sz(天頂)] 與高度角"""
    phi_r = np.radians(phi_deg)
    d_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284 + day_n)))
    d_rad = np.radians(d_deg)
    w_rad = np.radians(15.0 * (hours_arr - 12.0))

    sz = np.sin(phi_r) * np.sin(d_rad) + np.cos(phi_r) * np.cos(d_rad) * np.cos(w_rad)
    sx = -np.cos(d_rad) * np.sin(w_rad)  # 東方為 +X
    sy = np.cos(phi_r) * np.sin(d_rad) - np.sin(phi_r) * np.cos(d_rad) * np.cos(w_rad)  # 北方為 +Y
    return sx, sy, sz, d_deg

def calc_tracker_normals_and_poa(sx, sy, sz, fixed_tilt_deg, dni, dhi, max_track_deg=60.0):
    """
    計算三種系統的面板法向量 N = [Nx, Ny, Nz]、入射角餘弦 cos(theta_i) 與面板總輻照度 POA (W/m^2)
    1. 固定式 (Fixed): 朝南傾斜 beta 度 -> N_fixed = [0, -sin(beta), cos(beta)]
    2. 單軸追日 (1-Axis, 水平南北軸東西向追日): 繞 Y 軸旋轉角度 rho = clip(arctan2(sx, sz), -60°, +60°)
    3. 雙軸追日 (2-Axis, 向日葵全追日): 法向量永遠對準太陽 N_dual = [sx, sy, sz]
    """
    is_day = sz > 0.01
    beta_r = np.radians(fixed_tilt_deg)

    # 1. 固定式 (朝正南傾斜 beta)
    nx_fix = np.zeros_like(sx)
    ny_fix = np.full_like(sy, -np.sin(beta_r))
    nz_fix = np.full_like(sz, np.cos(beta_r))
    cos_fix = np.where(is_day, np.clip(sx * nx_fix + sy * ny_fix + sz * nz_fix, 0.0, 1.0), 0.0)

    # 2. 單軸追日 (水平南北軸 HSAT，面板法向量在 X-Z 平面轉動迎接東西向太陽)
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

    # 計算面板接收總輻照度 POA = DNI * cos(theta_i) + DHI * (1 + cos(tilt)) / 2
    poa_fix = np.where(is_day, dni * cos_fix + dhi * (1.0 + nz_fix) / 2.0, 0.0)
    poa_1ax = np.where(is_day, dni * cos_1ax + dhi * (1.0 + nz_1ax) / 2.0, 0.0)
    poa_2ax = np.where(is_day, dni * cos_2ax + dhi * (1.0 + nz_2ax) / 2.0, 0.0)

    return (
        (nx_fix, ny_fix, nz_fix, cos_fix, poa_fix),
        (nx_1ax, ny_1ax, nz_1ax, cos_1ax, poa_1ax),
        (nx_2ax, ny_2ax, nz_2ax, cos_2ax, poa_2ax)
    )

def make_panel_mesh_vertices(center_x, center_y, center_z, nx, ny, nz, w=0.22, h=0.16):
    """根據面板中心點與法向量 N=(nx,ny,nz)，計算 3D 矩形面板的 4 個頂點座標與法向量箭頭"""
    N = np.array([nx, ny, nz], dtype=float)
    norm_len = np.linalg.norm(N)
    if norm_len < 1e-6:
        N = np.array([0.0, 0.0, 1.0])
    else:
        N = N / norm_len

    # 建立面板局部座標系的兩個正交切向量 U (水平向), V (傾斜向上)
    ref = np.array([0.0, 1.0, 0.0]) if abs(N[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    U = np.cross(ref, N)
    U = U / np.linalg.norm(U)
    V = np.cross(N, U)

    C = np.array([center_x, center_y, center_z])
    p0 = C - w * U - h * V
    p1 = C + w * U - h * V
    p2 = C + w * U + h * V
    p3 = C - w * U + h * V

    vx = [p0[0], p1[0], p2[0], p3[0]]
    vy = [p0[1], p1[1], p2[1], p3[1]]
    vz = [p0[2], p1[2], p2[2], p3[2]]

    # 法向量箭頭終點
    arrow_tip = C + 0.28 * N
    return vx, vy, vz, C, arrow_tip

def build_3d_tracker_arena(day_n, phi_deg, hour_t, fixed_tilt_deg, dni_peak, dhi_base, camera_mode):
    """建構無閃爍 WebGL 3D 追日同場競技舞台 (左：固定式、中：單軸、右：雙軸)"""
    # 單一時刻計算 (強制確保輸入為陣列)
    sx_arr, sy_arr, sz_arr, delta_deg = calc_sun_vector(day_n, np.atleast_1d(hour_t), phi_deg)
    sx, sy, sz = float(sx_arr.flat[0]), float(sy_arr.flat[0]), float(sz_arr.flat[0])
    is_day = sz > 0.02

    # 大氣消光模型 (純量安全計算)
    am_val = float(np.power(np.clip(sz, 0.02, 1.0), 0.35)) if is_day else 0.0
    cur_dni = float(dni_peak * am_val) if is_day else 0.0
    cur_dhi = float(dhi_base * (0.4 + 0.6 * max(0.0, sz))) if is_day else 0.0

    fix_res, ax1_res, ax2_res = calc_tracker_normals_and_poa(
        np.array([sx]), np.array([sy]), np.array([sz]), fixed_tilt_deg, cur_dni, cur_dhi
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
            '<b>🟦 ① 固定式面板<br>(朝南固定傾角)</b>',
            '<b>🟩 ② 單軸追日系統<br>(東西向轉頭)</b>',
            '<b>🟧 ③ 雙軸追日向日葵<br>(全天候垂直鎖定)</b>'
        ],
        textfont=dict(
            size=[13, 13, 12, 12, 12, 12, 12],
            color=['#FFD700', '#FF8C00', '#00E5FF', '#FF6B6B', '#60A5FA', '#34D399', '#FBBF24']
        ),
        showlegend=False
    ))

    # [Trace 2] 當日太陽高空軌跡弧線 (高度放大於 Z 軸上方方便觀察)
    t_full = np.linspace(5.5, 18.5, 131)
    tsx, tsy, tsz, _ = calc_sun_vector(day_n, t_full, phi_deg)
    m_day = tsz >= 0
    fig.add_trace(go.Scatter3d(
        x=tsx[m_day] * 1.15, y=tsy[m_day] * 0.75, z=tsz[m_day] * 0.85 + 0.15,
        mode='lines', line=dict(color='rgba(255, 215, 0, 0.45)', width=5, dash='dot'),
        name='太陽今日空中軌跡'
    ))

    # [Trace 3] 三座太陽能板的立柱支架 (靜態)
    fig.add_trace(go.Scatter3d(
        x=[-0.75, -0.75, None, 0.0, 0.0, None, 0.75, 0.75],
        y=[0, 0, None, 0, 0, None, 0, 0],
        z=[0, 0.18, None, 0, 0.18, None, 0, 0.18],
        mode='lines', line=dict(color='#94A3B8', width=9),
        showlegend=False, hoverinfo='skip'
    ))

    # ==================== 動態 Trace 區 (隨時間動畫更新) ====================
    # 我們為三塊面板建立 Mesh3d，加上法向量與太陽光束線條
    centers_x = [-0.75, 0.0, 0.75]
    colors_panel = ['#2563EB', '#059669', '#D97706']
    names_panel = ['① 固定式面板', '② 單軸追日面板', '③ 雙軸追日面板']
    normals_now = [
        (float(fix_res[0][0]), float(fix_res[1][0]), float(fix_res[2][0])),
        (float(ax1_res[0][0]), float(ax1_res[1][0]), float(ax1_res[2][0])),
        (float(ax2_res[0][0]), float(ax2_res[1][0]), float(ax2_res[2][0]))
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

    # [動態 Trace D] 三塊面板的「綠色法向量箭頭 (面板正對方向)」
    norm_lines_x, norm_lines_y, norm_lines_z = [], [], []
    for idx in range(3):
        nx_i, ny_i, nz_i = normals_now[idx]
        _, _, _, c_pt, tip_pt = make_panel_mesh_vertices(centers_x[idx], 0.0, 0.18, nx_i, ny_i, nz_i)
        norm_lines_x.extend([c_pt[0], tip_pt[0], None])
        norm_lines_y.extend([c_pt[1], tip_pt[1], None])
        norm_lines_z.extend([c_pt[2], tip_pt[2], None])

    dynamic_trace_indices.append(len(fig.data))
    fig.add_trace(go.Scatter3d(
        x=norm_lines_x, y=norm_lines_y, z=norm_lines_z,
        mode='lines+markers',
        line=dict(color='#00FFCC', width=6),
        marker=dict(size=4, color='#00FFCC'),
        name='面板法向量 n (面板正對方向)'
    ))

    # [動態 Trace E] 太陽球體與打向三塊面板的金色直射光束 (DNI)
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
        marker=dict(size=[3, 18, 3, 3, 18, 3, 3, 18, 3], color='#FFEA00' if is_day else '#555555'),
        name='太陽直射光束 (DNI)'
    ))

    # ==================== 建立 WebGL 無閃爍動畫 Frames (06:00 ~ 18:00) ====================
    anim_hours = np.arange(6.0, 18.25, 0.25)
    frames = []
    slider_steps = []

    for h_val in anim_hours:
        hsx, hsy, hsz, _ = calc_sun_vector(day_n, np.array([h_val]), phi_deg)
        hsx, hsy, hsz = float(hsx[0]), float(hsy[0]), float(hsz[0])
        h_day = hsz > 0.02
        h_am = np.power(np.clip(hsz, 0.02, 1.0), 0.35) if h_day else 0.0
        h_dni = dni_peak * h_am
        h_dhi = dhi_base * (0.4 + 0.6 * max(0.0, hsz)) if h_day else 0.0

        f_fix, f_1ax, f_2ax = calc_tracker_normals_and_poa(
            np.array([hsx]), np.array([hsy]), np.array([hsz]), fixed_tilt_deg, h_dni, h_dhi
        )
        f_normals = [
            (float(f_fix[0][0]), float(f_fix[1][0]), float(f_fix[2][0])),
            (float(f_1ax[0][0]), float(f_1ax[1][0]), float(f_1ax[2][0])),
            (float(f_2ax[0][0]), float(f_2ax[1][0]), float(f_2ax[2][0]))
        ]

        frame_data = []
        f_nlx, f_nly, f_nlz = [], [], []
        for idx in range(3):
            vx, vy, vz, c_pt, tip_pt = make_panel_mesh_vertices(
                centers_x[idx], 0.0, 0.18, f_normals[idx][0], f_normals[idx][1], f_normals[idx][2]
            )
            frame_data.append(go.Mesh3d(x=vx, y=vy, z=vz))
            f_nlx.extend([c_pt[0], tip_pt[0], None])
            f_nly.extend([c_pt[1], tip_pt[1], None])
            f_nlz.extend([c_pt[2], tip_pt[2], None])

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
            marker=dict(size=[3, 18, 3, 3, 18, 3, 3, 18, 3], color='#FFEA00' if h_day else '#555555')
        ))

        h_str = f"{int(h_val):02d}:{int((h_val%1)*60):02d}"
        c_fix_val, c_1ax_val, c_2ax_val = float(f_fix[3][0])*100, float(f_1ax[3][0])*100, float(f_2ax[3][0])*100
        frames.append(go.Frame(
            name=h_str,
            traces=dynamic_trace_indices,
            data=frame_data,
            layout=go.Layout(
                title=dict(
                    text=(
                        f"<b>🕒 {h_str} 受光效率 cos(θi) 對決 ｜ "
                        f"🟦固定式: {c_fix_val:.0f}% vs 🟩單軸追日: {c_1ax_val:.0f}% vs 🟧雙軸追日: {c_2ax_val:.0f}%</b>"
                    ),
                    font=dict(size=16, color="#FFD700")
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
        # 從太陽位置往下看三塊板子，直觀感受「斜射面積縮小 vs 垂直面積最大」
        cam_eye = dict(x=sx * 1.65, y=sy * 1.65 - 0.2, z=max(0.35, sz * 1.65))
        cam_center = dict(x=0, y=0, z=0.15)
    elif "由北向南全景視角" in camera_mode:
        # 左邊東方日出，右邊西方日落
        cam_eye = dict(x=0.0, y=1.85, z=0.65)
        cam_center = dict(x=0.0, y=-0.1, z=0.2)
    else:
        # 預設：競技場正前方鳥瞰視角 (由南往北看三塊面板轉動)
        cam_eye = dict(x=0.15, y=-1.85, z=0.75)
        cam_center = dict(x=0.0, y=0.0, z=0.2)

    c0, c1, c2 = float(fix_res[3][0])*100, float(ax1_res[3][0])*100, float(ax2_res[3][0])*100
    fig.update_layout(
        title=dict(
            text=(
                f"<b>🕒 {int(hour_t):02d}:{int((hour_t%1)*60):02d} 受光效率 cos(θi) 對決 ｜ "
                f"🟦固定式: {c0:.0f}% vs 🟩單軸追日: {c1:.0f}% vs 🟧雙軸追日: {c2:.0f}%</b>"
            ),
            font=dict(size=16, color="#FFD700"),
            x=0.02, y=0.96
        ),
        height=640,
        margin=dict(l=0, r=0, b=80, t=45),
        paper_bgcolor='#0E1117',
        scene=dict(
            xaxis=dict(visible=False, range=[-1.4, 1.4]),
            yaxis=dict(visible=False, range=[-1.0, 1.0]),
            zaxis=dict(visible=False, range=[0.0, 1.2]),
            aspectmode='manual',
            aspectratio=dict(x=1.35, y=0.9, z=0.65),
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
            active=int(np.clip((hour_t - 6.0) / 0.25, 0, len(slider_steps)-1)),
            yanchor="bottom", xanchor="left",
            currentvalue=dict(font=dict(size=14, color="#FFD700"), prefix="拖曳時間軸：", visible=True, xanchor="right"),
            transition=dict(duration=0),
            pad=dict(b=10, t=10), len=0.70, x=0.28, y=0.02,
            font=dict(color="#CBD5E1", size=10),
            steps=slider_steps
        )]
    )

    return fig, fix_res, ax1_res, ax2_res, cur_dni, cur_dhi

# ==================== 主舞台配置：左拉桿控制台 (1) + 右 3D 追日競技場 (2.3) ====================
col_ctrl, col_stage = st.columns([1.0, 2.3], gap="large")

with col_ctrl:
    st.markdown("### 🎛️ 追日工程控制台")
    st.success("🎬 **動態體驗**：點擊右圖左下角 **「▶️ 播放一日追日對決」**，觀察中間與右邊的面板如何轉頭迎接陽光！")

    st.markdown("#### 🎥 1. 切換 3D 觀察視角")
    camera_mode = st.radio(
        "選擇教學鏡頭：",
        [
            "🏟️ 競技場正面鳥瞰 (觀察三板同步轉動)",
            "☀️ 光子第一人稱視角 (直擊餘弦投影面積差異！)",
            "🌅 由北向南全景視角 (左東升 ➔ 右西落)"
        ],
        index=0
    )

    st.markdown("#### 🌤️ 2. 大氣層與季節設定")
    weather_preset = st.selectbox(
        "大氣層雲霧狀態（影響直射 DNI 與散射 DHI）：",
        [
            "☀️ 晴朗無雲 (高直射光 DNI=850, 散射 DHI=120)",
            "⛅ 薄雲微霾 (中直射光 DNI=550, 散射 DHI=260)",
            "☁️ 陰天厚雲 (無直射光 DNI=80, 全散射 DHI=350)"
        ],
        index=0
    )
    weather_map = {
        "☀️ 晴朗無雲 (高直射光 DNI=850, 散射 DHI=120)": (850.0, 120.0),
        "⛅ 薄雲微霾 (中直射光 DNI=550, 散射 DHI=260)": (550.0, 260.0),
        "☁️ 陰天厚雲 (無直射光 DNI=80, 全散射 DHI=350)": (80.0, 350.0)
    }
    dni_peak, dhi_base = weather_map[weather_preset]

    season_opt = st.selectbox(
        "選擇季節：",
        ["☀️ 夏至 (6/21, 太陽偏北高空)", "🌸 春分/秋分 (太陽正東升西落)", "❄️ 冬至 (12/21, 太陽偏南低空)"],
        index=0
    )
    day_n = {"☀️ 夏至 (6/21, 太陽偏北高空)": 172, "🌸 春分/秋分 (太陽正東升西落)": 80, "❄️ 冬至 (12/21, 太陽偏南低空)": 355}[season_opt]

    st.markdown("#### 🔧 3. 面板工程參數與定格時間")
    fixed_tilt_deg = st.slider("🟦 固定式面板朝南傾角 β (°)", 0.0, 45.0, 20.0, step=2.5, help="台灣最佳年發電固定傾角約為 20°~23.5°")
    hour_t = st.slider("⏰ 定格觀察時刻 (推薦拉到早上 07:30 比較！)", 6.0, 18.0, 7.5, step=0.25)
    phi_deg = 23.15  # 預設台灣台南七股緯度

with col_stage:
    fig_arena, fix_res, ax1_res, ax2_res, cur_dni, cur_dhi = build_3d_tracker_arena(
        day_n, phi_deg, hour_t, fixed_tilt_deg, dni_peak, dhi_base, camera_mode
    )
    st.plotly_chart(fig_arena, use_container_width=True, key="tracker_arena_3d")
    st.caption(
        "💡 **強烈推薦教學實驗**：將左方時間滑桿拉到 **早上 07:30**，然後將視角切換為 **「☀️ 光子第一人稱視角」**！"
        "你會親眼看到藍色的固定式面板因為斜射看起來『扁扁窄窄的』，而橘色的雙軸追日面板則是『正對著你』接滿全部光子！"
    )

# ==================== 全日同場競技曲線：把早晚陽光「扳正」的胖鐘型發電曲線 ====================
st.markdown("---")
st.markdown("### 📈 同場競技模擬：全日面板接收輻照度曲線（見證早晚陽光被「扳正」的奇蹟！）")

t_day = np.linspace(5.5, 18.5, 131)
sx_d, sy_d, sz_d, _ = calc_sun_vector(day_n, t_day, phi_deg)
am_d = np.where(sz_d > 0.02, np.power(np.clip(sz_d, 0.02, 1.0), 0.35), 0.0)
dni_d = dni_peak * am_d
dhi_d = np.where(sz_d > 0.02, dhi_base * (0.4 + 0.6 * np.maximum(0.0, sz_d)), 0.0)

fix_d, ax1_d, ax2_d = calc_tracker_normals_and_poa(sx_d, sy_d, sz_d, fixed_tilt_deg, dni_d, dhi_d)

# 計算全日累積能量 (kWh/m^2/day) 與增益百分比
dt_hr = t_day[1] - t_day[0]
energy_fix = float(np.sum(fix_d[4]) * dt_hr / 1000.0)
energy_1ax = float(np.sum(ax1_d[4]) * dt_hr / 1000.0)
energy_2ax = float(np.sum(ax2_d[4]) * dt_hr / 1000.0)

gain_1ax = ((energy_1ax - energy_fix) / max(energy_fix, 1e-4)) * 100.0
gain_2ax = ((energy_2ax - energy_fix) / max(energy_fix, 1e-4)) * 100.0

col_curve, col_kpi = st.columns([1.8, 1.0], gap="large")

with col_curve:
    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=fix_d[4], mode='lines',
        line=dict(color='#3B82F6', width=3),
        fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.15)',
        name=f'🟦 固定式 (傾角 {fixed_tilt_deg:.0f}°)'
    ))
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=ax1_d[4], mode='lines',
        line=dict(color='#10B981', width=3, dash='dash'),
        fill='tonexty', fillcolor='rgba(16, 185, 129, 0.18)',
        name=f'🟩 單軸追日 (+{gain_1ax:.1f}% 發電增益)'
    ))
    fig_curve.add_trace(go.Scatter(
        x=t_day, y=ax2_d[4], mode='lines',
        line=dict(color='#F59E0B', width=4),
        fill='tonexty', fillcolor='rgba(245, 158, 11, 0.20)',
        name=f'🟧 雙軸追日 (+{gain_2ax:.1f}% 發電增益)'
    ))
    # 標示當前選擇時刻的垂直線
    fig_curve.add_vline(x=hour_t, line_width=2, line_dash="dot", line_color="#FFEA00", annotation_text=f"當前時刻 {hour_t:.2f}h")

    fig_curve.update_layout(
        title="<b>📊 三種系統全日接收總輻照度 POA (W/m²) —— 注意看早上 7~10 點與下午 14~17 點的多榨出電力面積！</b>",
        xaxis_title="太陽時間 (小時)",
        yaxis_title="面板有效總輻照度 POA (W/m²)",
        height=380,
        margin=dict(l=20, r=20, t=45, b=20),
        paper_bgcolor='#0E1117', plot_bgcolor='#1E293B',
        font=dict(color='white'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_curve, use_container_width=True)

with col_kpi:
    st.markdown("#### 🏆 同場競技計分板（今日累計）")
    st.metric(
        "🟦 ① 固定式系統 (基準組)",
        f"{energy_fix:.2f} kWh/m²",
        f"當前時刻受光率 cos(θi) = {float(fix_res[3][0])*100:.1f}%"
    )
    st.metric(
        "🟩 ② 單軸追日系統 (東西向轉頭)",
        f"{energy_1ax:.2f} kWh/m²",
        f"+{gain_1ax:.1f}% 總發電量提升！(當前受光率 {float(ax1_res[3][0])*100:.1f}%)"
    )
    st.metric(
        "🟧 ③ 雙軸追日系統 (全向向日葵)",
        f"{energy_2ax:.2f} kWh/m²",
        f"+{gain_2ax:.1f}% 總發電量提升！(當前受光率 {float(ax2_res[3][0])*100:.1f}%)"
    )

# ==================== 下方：物理公式白話導讀區 ====================
st.markdown("---")
st.markdown("### 📐 物理公式與知識白話導讀（隨上方控制拉桿即時跳動）")

f1, f2, f3 = st.columns(3)

with f1:
    with st.container(border=True):
        st.markdown("#### ① 什麼是「餘弦損失（Cosine Loss）」？")
        st.markdown(
            "**【白話導讀】** 拿手電筒垂直照桌面，光斑最小、最亮（$\cos 0^\\circ = 100\\%$）；"
            "但如果你斜著照，同樣一束光會被**攤平在更大的面積上**，單位面積分到的光子密度就打折了！"
            "打折的比例剛好就是**太陽光線 $\\vec{S}$ 與面板法向量 $\\vec{n}$ 夾角 $\\theta_i$ 的餘弦值**："
        )
        st.latex(r"\eta_{\text{cosine}} = \cos\theta_i = \vec{S} \cdot \vec{n}")
        theta_fix_deg = np.degrees(np.arccos(np.clip(float(fix_res[3][0]), 0.0, 1.0)))
        st.latex(
            rf"\text{{固定式當前夾角 }} \theta_i = \color{{orange}}{{{theta_fix_deg:.1f}^\circ}} \implies \cos\theta_i = \color{{deepskyblue}}{{{float(fix_res[3][0])*100:.1f}\%}}"
        )
        st.caption("👉 雙軸追日因為隨時轉頭讓 $\\theta_i = 0^\\circ$，所以永遠保持 $\\cos 0^\\circ = 100\\%$ 零餘弦損失！")

with f2:
    with st.container(border=True):
        st.markdown("#### ② 大氣層的雙胞胎：直射光 vs 散射光")
        st.markdown(
            "**【白話導讀】** 面板真正吃到的總陽光（$G_{\\text{POA}}$），是由需要對準角度的**直射光（DNI）**，"
            "加上不需要對準角度、從整片天空均勻灑落的**散射光（DHI）**合體而成："
        )
        st.latex(r"G_{\text{POA}} = \text{DNI} \cdot \cos\theta_i + \text{DHI} \cdot \left(\frac{1 + \cos\beta}{2}\right)")
        st.latex(
            rf"G_{{\text{{POA,固定}}}} = \color{{gold}}{{{cur_dni:.0f}}} \times \color{{deepskyblue}}{{{float(fix_res[3][0]):.2f}}} + \color{{limegreen}}{{{cur_dhi:.0f}}} \times 0.97 = \color{{red}}{{{float(fix_res[4][0]):.0f}\text{{ W/m}}^2}}"
        )
        st.caption("👉 試著把左上方天氣切換成 **「☁️ 陰天厚雲」**！你會發現當沒有直射光（DNI 很低）時，追日系統就失去優勢了！")

with f3:
    with st.container(border=True):
        st.markdown("#### ③ 為什麼追日系統能多榨出 25%~30% 電力？")
        st.markdown(
            "**【白話導讀】** 固定式面板只在正午 12 點前後能正面吃到陽光，早晚 6~9 點與 15~18 點的光線幾乎從側面擦過。"
            "**追日系統把早晚原本斜射浪費的 $\\cos\\theta_i$ 硬生生「扳正」回 $95\\% \\sim 100\\%$**，讓尖峰發電曲線變成寬廣的「胖鐘型」："
        )
        st.latex(r"\text{Gain}_{\%} = \frac{\int G_{\text{POA, Tracker}}\,dt - \int G_{\text{POA, Fixed}}\,dt}{\int G_{\text{POA, Fixed}}\,dt}")
        st.latex(
            rf"\text{{單軸增益}} = \color{{limegreen}}{{+{gain_1ax:.1f}\%}}, \quad \text{{雙軸增益}} = \color{{orange}}{{+{gain_2ax:.1f}\%}}"
        )
        st.caption("👉 雖然雙軸發電最多，但考量機械造價與抗颱風結構，大型電廠最常採用 CP 值最高的「單軸追日」或「20°固定式」。")
