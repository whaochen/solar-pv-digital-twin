def build_3d_solar_climate_power_surface(df_subset, site_name):
    """
    建構 3D 多維度關係圖：
    - X 軸：太陽入射角 θi (°)
    - Y 軸：Faiman 面板溫度 T_cell (°C)
    - Z 軸：實際發電功率 P_actual (kW)
    - 色彩 (Color)：PM2.5 濃度 (μg/m³)
    """
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df_subset["Incidence_Angle_deg"],
        y=df_subset["T_cell_C"],
        z=df_subset["P_actual_kW"],
        mode='markers',
        marker=dict(
            size=5,
            color=df_subset["PM25_ugm3"],
            colorscale='Viridis',  # 顏色越黃代表 PM2.5 越高或環境越嚴苛
            colorbar=dict(title="<b>PM2.5 (μg/m³)</b>"),
            opacity=0.85
        ),
        text=[
            f"時間: {t}<br>入射角 θi: {ang:.1f}°<br>面板溫 Tcell: {tc:.1f}°C<br>實發功率 P: {p:.1f} kW<br>PM2.5: {pm:.1f}"
            for t, ang, tc, p, pm in zip(
                df_subset["timestamp"].dt.strftime("%m-%d %H:%M"),
                df_subset["Incidence_Angle_deg"],
                df_subset["T_cell_C"],
                df_subset["P_actual_kW"],
                df_subset["PM25_ugm3"]
            )
        ],
        hoverinfo="text"
    )])

    fig_3d.update_layout(
        title=dict(
            text=f"<b>🌐 {site_name} —— 3D 多維度因果關係圖（入射角 θi ✕ 面板溫度 Tcell ✕ 實發功率 P）</b>",
            font=dict(size=14, color="#0F172A"), x=0.01, y=0.95
        ),
        scene=dict(
            xaxis=dict(title='<b>太陽入射角 θi (°) [幾何因子]</b>', backgroundcolor="#F8FAFC", gridcolor="#CBD5E1"),
            yaxis=dict(title='<b>面板溫度 Tcell (°C) [熱力學因子]</b>', backgroundcolor="#F8FAFC", gridcolor="#CBD5E1"),
            zaxis=dict(title='<b>實際發電量 P_actual (kW) [輸出結果]</b>', backgroundcolor="#F8FAFC", gridcolor="#CBD5E1"),
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.8))
        ),
        height=550,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#FFFFFF"
    )
    return fig_3d
