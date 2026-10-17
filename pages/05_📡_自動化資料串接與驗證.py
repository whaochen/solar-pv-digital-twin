import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="第 5 章 (階段一)：自動化資料串接與多尺度驗證", page_icon="📡", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 3.5rem !important; padding-bottom: 1.5rem !important; }
    .bright-card {
        background: linear-gradient(145deg, #0F172A, #1E293B);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 14px 18px;
        color: #F8FAFC !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 10px;
    }
    .bright-title {
        color: #E2E8F0 !important;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .site-profile-box {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        border-radius: 8px;
        padding: 14px 18px;
        color: #0F172A;
        font-size: 0.93rem;
        line-height: 1.6;
        border: 1px solid #E2E8F0;
    }
    .section-banner {
        background: linear-gradient(90deg, #1E3A8A, #1E293B);
        color: #FFFFFF !important;
        padding: 10px 18px;
        border-radius: 8px;
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 18px;
        margin-bottom: 14px;
        border-left: 6px solid #FFD700;
    }
</style>
""", unsafe_allow_html=True)

st.title("📡 第五章（階段一）：【工程基石】真實世界 Open Data 串接、案場太陽幾何與多尺度驗證")
st.info(
    "🛡️ **【研究設計架構】** 本章採用**「三段式獨立展開架構」**：\n"
    "* **【第一節】台灣五大光電案場空間地圖 ＆ 第 1、2 章太陽入射角幾何聯動**\n"
    "* **【第二節】後台資料庫「錨定起算日（自 2026-08-18 起）」設定與健康度檢核**\n"
    "* **【第三節】全寬度獨立三尺度監測面板（當天逐時 ／ 最近一週 ／ 指定區段放大鏡，每張通道圖皆配備獨立專屬圖例！）**"
)

TAIWAN_SOLAR_SITES = {
    "🇹🇼 1. 台南七股地面型旗艦案場 (23.15°N, 120.08°E)": {
        "short_name": "台南七股案場", "lat": 23.15, "lon": 120.08, "opt_tilt": 20.0,
        "type": "鹽灘地與魚塭地面高架型 (Ground-Mounted / Aquavoltaics)",
        "capacity": "約 150 MW ～ 200 MW 級大型聚落",
        "climate_feature": "全台年日照時數最高（>2,200 hr/yr），但面臨強烈台江海風與高濕度海鹽結晶。",
        "key_challenge": "🌊 **沿海鹽霧結垢（Salt Mist）**：海風雖有助於 Faiman 對流散熱，但鹽分附著於玻璃表面會降低透光率。"
    },
    "🇹🇼 2. 彰濱工業區崙尾東水上光電 (24.12°N, 120.41°E)": {
        "short_name": "彰濱崙尾東案場", "lat": 24.12, "lon": 120.41, "opt_tilt": 15.0,
        "type": "潮間帶浮筒水面型光電 (Floating Solar PV)",
        "capacity": "約 180 MW ～ 320 MW 級亞洲指標水面案場",
        "climate_feature": "台灣海峽風廊核心區，全年平均風速極高（常達 6～12 m/s），水面蒸發吸熱明顯。",
        "key_challenge": "💨 **強風強制對流與浪沫**：高風速使面板溫度顯著低於內陸案場，但退潮泥灘揚塵與浪花鹽漬會產生非線性殘差。"
    },
    "🇹🇼 3. 雲林麥寮農電共生案場 (23.78°N, 120.25°E)": {
        "short_name": "雲林麥寮案場", "lat": 23.78, "lon": 120.25, "opt_tilt": 20.0,
        "type": "農地高架結合農業溫室型 (Agrivoltaics)",
        "capacity": "約 50 MW ～ 100 MW 分散式聚落",
        "climate_feature": "位於濁水溪出海口南側，秋冬受東北季風揚塵（沙塵暴）與工業區氣膠雙重影響。",
        "key_challenge": "🌫️ **秋冬 PM2.5 與乾季嚴重積塵（Soiling）**：10 月至隔年 3 月少雨乾燥，懸浮微粒沉積形成厚重灰塵層。"
    },
    "🇹🇼 4. 屏東林邊地層下陷光電專區 (22.43°N, 120.51°E)": {
        "short_name": "屏東林邊案場", "lat": 22.43, "lon": 120.51, "opt_tilt": 18.0,
        "type": "高腳防洪型地面光電架台 (Elevated Ground-Mounted)",
        "capacity": "約 80 MW ～ 120 MW 綠能專區",
        "climate_feature": "熱帶季風氣候，四季氣溫偏高（常年 >28°C），夏季午後對流雷陣雨極為頻繁。",
        "key_challenge": "🌧️ **高溫熱衰減 vs. 午後雷陣雨驟冷（Thermal Quenching）**：正午面板常飆破 65°C，午後大雨瞬間將面板降溫。"
    },
    "🇹🇼 5. 桃園觀音工業區屋頂型光電群 (25.04°N, 121.11°E)": {
        "short_name": "桃園觀音案場", "lat": 25.04, "lon": 121.11, "opt_tilt": 12.0,
        "type": "大型廠房浪板緊貼/平行屋頂型 (Industrial Rooftop PV)",
        "capacity": "約 30 MW ～ 60 MW 廠房群聚",
        "climate_feature": "北台灣秋冬多雲多雨、雲層厚，散射光（DHI）佔總日射比例極高。",
        "key_challenge": "☁️ **高散射光比例與屋頂散熱不良**：廠房鐵皮屋頂背風悶熱，且多雲天氣下太陽快速進出雲層造成劇烈熱慣性延遲。"
    }
}

def calc_ch1_ch2_solar_geometry_for_df(df, lat_deg, panel_tilt_deg):
    phi_r = np.radians(lat_deg)
    beta_r = np.radians(panel_tilt_deg)
    doy = df["timestamp"].dt.dayofyear.values
    hour_val = df["timestamp"].dt.hour.values + 0.5

    delta_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284.0 + doy)))
    delta_r = np.radians(delta_deg)
    omega_r = np.radians(15.0 * (hour_val - 12.0))

    sz = np.sin(phi_r) * np.sin(delta_r) + np.cos(phi_r) * np.cos(delta_r) * np.cos(omega_r)
    sx = -np.cos(delta_r) * np.sin(omega_r)
    sy = np.cos(phi_r) * np.sin(delta_r) - np.sin(phi_r) * np.cos(delta_r) * np.cos(omega_r)
    alpha_s_deg = np.degrees(np.arcsin(np.clip(sz, -1.0, 1.0)))

    nx, ny, nz = 0.0, -np.sin(beta_r), np.cos(beta_r)
    cos_theta_i = np.where(sz > 0.0, np.clip(sx * nx + sy * ny + sz * nz, 0.0, 1.0), 0.0)
    theta_i_deg = np.degrees(np.arccos(np.clip(cos_theta_i, 0.0, 1.0)))

    poa_wm2 = np.where(
        sz > 0.0,
        df["DNI_Wm2"].values * cos_theta_i + df["DHI_Wm2"].values * ((1.0 + np.cos(beta_r)) / 2.0),
        0.0
    )

    df["Sun_Elevation_deg"] = np.maximum(0.0, alpha_s_deg).round(1)
    df["Incidence_Angle_deg"] = np.where(sz > 0.0, theta_i_deg, 90.0).round(1)
    df["Cosine_Eff_pct"] = (cos_theta_i * 100.0).round(1)
    df["POA_Wm2"] = poa_wm2.round(1)
    return df

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_cumulative_solar_and_air_data(lat, lon, panel_tilt_deg, start_date_str, end_date_str):
    audit_report = {
        "weather_api_ok": False, "air_api_ok": False,
        "fetch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "start_anchor": start_date_str, "end_today": end_date_str,
        "total_days": 0, "raw_rows": 0, "cleaned_rows": 0,
        "missing_fixed": 0, "outliers_clipped": 0,
        "first_record_time": "N/A", "latest_record_time": "N/A", "error_msg": ""
    }

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_date_str}&end_date={end_date_str}"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,"
        f"shortwave_radiation,direct_normal_irradiance,diffuse_radiation"
        f"&wind_speed_unit=ms&timezone=Asia%2FTaipei"
    )

    air_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_date_str}&end_date={end_date_str}"
        f"&hourly=pm10,pm2_5"
        f"&timezone=Asia%2FTaipei"
    )

    try:
        req_w = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_w, timeout=12) as resp_w:
            if resp_w.status == 200:
                w_data = json.loads(resp_w.read().decode('utf-8'))
                audit_report["weather_api_ok"] = True

        req_a = urllib.request.Request(air_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_a, timeout=12) as resp_a:
            if resp_a.status == 200:
                a_data = json.loads(resp_a.read().decode('utf-8'))
                audit_report["air_api_ok"] = True

        df_w = pd.DataFrame({
            "timestamp": pd.to_datetime(w_data["hourly"]["time"]),
            "T_amb_C": pd.to_numeric(w_data["hourly"]["temperature_2m"], errors="coerce"),
            "RH_pct": pd.to_numeric(w_data["hourly"]["relative_humidity_2m"], errors="coerce"),
            "Rain_mm": pd.to_numeric(w_data["hourly"]["precipitation"], errors="coerce"),
            "Wind_ms": pd.to_numeric(w_data["hourly"]["wind_speed_10m"], errors="coerce"),
            "GHI_Wm2": pd.to_numeric(w_data["hourly"]["shortwave_radiation"], errors="coerce"),
            "DNI_Wm2": pd.to_numeric(w_data["hourly"]["direct_normal_irradiance"], errors="coerce"),
            "DHI_Wm2": pd.to_numeric(w_data["hourly"]["diffuse_radiation"], errors="coerce")
        })

        df_a = pd.DataFrame({
            "timestamp": pd.to_datetime(a_data["hourly"]["time"]),
            "PM25_ugm3": pd.to_numeric(a_data["hourly"]["pm2_5"], errors="coerce"),
            "PM10_ugm3": pd.to_numeric(a_data["hourly"]["pm10"], errors="coerce")
        })

        df_merged = pd.merge(df_w, df_a, on="timestamp", how="left")

        now_dt = pd.Timestamp.now(tz="Asia/Taipei").tz_localize(None)
        valid_anchor_dt = pd.Timestamp("2026-08-18 00:00:00")
        df_merged = df_merged[
            (df_merged["timestamp"] >= valid_anchor_dt) &
            (df_merged["timestamp"] <= now_dt)
        ].copy()

        valid_mask = df_merged["T_amb_C"].notna() & df_merged["GHI_Wm2"].notna()
        if valid_mask.any():
            first_valid_idx = valid_mask.idxmax()
            df_merged = df_merged.loc[first_valid_idx:].reset_index(drop=True)

        audit_report["raw_rows"] = len(df_merged)
        audit_report["missing_fixed"] = int(df_merged.isna().sum().sum())
        df_merged = df_merged.interpolate(method="linear").bfill().ffill()

        audit_report["outliers_clipped"] = int(
            (df_merged["GHI_Wm2"] < 0).sum() + (df_merged["GHI_Wm2"] > 1350).sum() +
            (df_merged["Wind_ms"] < 0).sum() + (df_merged["PM25_ugm3"] < 0).sum()
        )

        df_merged["GHI_Wm2"] = df_merged["GHI_Wm2"].clip(0.0, 1350.0)
        df_merged["DNI_Wm2"] = df_merged["DNI_Wm2"].clip(0.0, 1200.0)
        df_merged["DHI_Wm2"] = df_merged["DHI_Wm2"].clip(0.0, 800.0)
        df_merged["Wind_ms"] = df_merged["Wind_ms"].clip(0.0, 60.0)
        df_merged["Rain_mm"] = df_merged["Rain_mm"].clip(0.0, 300.0)
        df_merged["PM25_ugm3"] = df_merged["PM25_ugm3"].clip(1.0, 500.0)
        df_merged["PM10_ugm3"] = df_merged["PM10_ugm3"].clip(2.0, 800.0)

        df_merged = calc_ch1_ch2_solar_geometry_for_df(df_merged, lat, panel_tilt_deg)
        df_merged["T_cell_Faiman_C"] = (
            df_merged["T_amb_C"] + df_merged["POA_Wm2"] / (25.0 + 6.84 * df_merged["Wind_ms"])
        ).round(1)

        dry_hrs, cur_dry = [], 0
        for r_val in df_merged["Rain_mm"]:
            if r_val >= 0.2:
                cur_dry = 0
            else:
                cur_dry += 1
            dry_hrs.append(cur_dry)
        df_merged["Dry_Hours_Since_Rain"] = dry_hrs

        audit_report["cleaned_rows"] = len(df_merged)
        audit_report["total_days"] = round(len(df_merged) / 24.0, 1)
        audit_report["first_record_time"] = df_merged["timestamp"].min().strftime("%Y-%m-%d %H:%M")
        audit_report["latest_record_time"] = df_merged["timestamp"].max().strftime("%Y-%m-%d %H:%M")

        return df_merged, audit_report

    except Exception as e:
        audit_report["error_msg"] = str(e)
        return pd.DataFrame(), audit_report

def build_taiwan_sites_map(selected_site_key):
    lats, lons, names, colors, sizes, texts = [], [], [], [], [], []
    for k, v in TAIWAN_SOLAR_SITES.items():
        is_sel = (k == selected_site_key)
        lats.append(v["lat"])
        lons.append(v["lon"])
        names.append(v["short_name"])
        colors.append("#DC2626" if is_sel else "#2563EB")
        sizes.append(16 if is_sel else 10)
        tag = "🎯【當前監測案場】" if is_sel else "📍 候選案場："
        texts.append(f"{tag}{v['short_name']} ({v['lat']}°N, {v['lon']}°E)<br>型態：{v['type']}<br>容量：{v['capacity']}")

    sel_info = TAIWAN_SOLAR_SITES[selected_site_key]

    fig_map = go.Figure(go.Scattergeo(
        lat=lats,
        lon=lons,
        mode="markers+text",
        marker=dict(size=sizes, color=colors, opacity=0.92, symbol="circle"),
        text=names,
        textposition="top right",
        textfont=dict(size=12, color="#0F172A", family="sans-serif"),
        hovertext=texts,
        hoverinfo="text"
    ))

    fig_map.update_geos(
        projection_type="natural earth",
        center=dict(lat=23.75, lon=120.85),
        lonaxis_range=[119.5, 122.2],
        lataxis_range=[21.8, 25.5],
        showcountries=True, countrycolor="#CBD5E1",
        showland=True, landcolor="#F1F5F9",
        showocean=True, oceancolor="#E0F2FE"
    )

    fig_map.update_layout(
        title=dict(
            text=f"<b>🗺️ 台灣五大光電案場空間分布圖 ｜ 當前鎖定：{sel_info['short_name']}</b>",
            font=dict(size=14, color="#0F172A"), x=0.02, y=0.96
        ),
        height=390,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="#FFFFFF"
    )
    return fig_map

def build_ch1_ch2_angle_chart(df_day, site_short_name, panel_tilt_deg, target_date):
    fig_ang = make_subplots(specs=[[{"secondary_y": True}]])

    fig_ang.add_trace(
        go.Scatter(
            x=df_day["timestamp"], y=df_day["Sun_Elevation_deg"],
            mode="lines+markers", marker=dict(size=5),
            name="☀️ 第1章：太陽天球仰角 αs (°)",
            line=dict(color="#D97706", width=2.5),
            hovertemplate="<b>☀️ 太陽仰角 αs</b>：%{y:.1f}°<extra></extra>"
        ),
        secondary_y=False
    )

    fig_ang.add_trace(
        go.Scatter(
            x=df_day["timestamp"], y=df_day["Incidence_Angle_deg"],
            mode="lines+markers", marker=dict(size=5),
            name=f"📐 第2章：面板太陽入射角 θi (°) [傾角 β={panel_tilt_deg:.0f}°]",
            line=dict(color="#2563EB", width=2.2, dash="dot"),
            hovertemplate="<b>📐 面板入射角 θi</b>：%{y:.1f}°<extra></extra>"
        ),
        secondary_y=False
    )

    fig_ang.add_trace(
        go.Scatter(
            x=df_day["timestamp"], y=df_day["Cosine_Eff_pct"],
            mode="lines",
            name="🎯 第2章：餘弦受光率 cos(θi) (%)",
            line=dict(color="#059669", width=2.8),
            fill="tozeroy", fillcolor="rgba(16, 185, 129, 0.15)",
            hovertemplate="<b>🎯 面板餘弦受光率 cos(θi)</b>：%{y:.1f}%<extra></extra>"
        ),
        secondary_y=True
    )

    fig_ang.update_yaxes(title_text="<b>角度 (°)</b>", range=[0, 95], gridcolor="#E2E8F0", secondary_y=False)
    fig_ang.update_yaxes(title_text="<b>餘弦受光率 (%)</b>", range=[0, 105], showgrid=False, secondary_y=True)
    fig_ang.update_xaxes(gridcolor="#E2E8F0", hoverformat="%H:%M")

    fig_ang.update_layout(
        title=dict(
            text=f"<b>📐 {site_short_name} ({target_date}) —— 第 1 章太陽仰角 αs vs. 第 2 章面板入射角 θi 與餘弦受光率</b>",
            font=dict(size=14, color="#0F172A"), x=0.01, y=0.96
        ),
        height=340,
        margin=dict(l=60, r=60, t=75, b=30),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC",
        font=dict(color="#0F172A", size=11.5),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0F172A", font_size=12, font_color="#F8FAFC", namelength=-1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0, bgcolor="rgba(241,245,249,0.95)", bordercolor="#CBD5E1", borderwidth=1)
    )
    return fig_ang


# ==================== 【升級重點】將三張通道圖拆開獨立繪製，各自擁有專屬圖例！ ====================
def render_separated_three_channel_charts(df_sub, view_title, key_prefix, show_markers=False):
    """
    將通道 1、通道 2、通道 3 拆分為三張獨立的 Plotly 圖表，
    讓每張圖的頂部只顯示屬於自己的 3~4 個圖例，視覺清爽、對照直覺！
    """
    mode_str = "lines+markers" if show_markers else "lines"
    marker_cfg = dict(size=5) if show_markers else dict(size=1)

    common_layout = dict(
        height=275,
        margin=dict(l=60, r=60, t=75, b=30),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(color="#0F172A", size=11.5),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0F172A", font_size=12, font_color="#F8FAFC", namelength=-1),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0,
            bgcolor="rgba(241, 245, 249, 0.96)", bordercolor="#CBD5E1", borderwidth=1,
            font=dict(color="#0F172A", size=11.5)
        )
    )

    # -------------------- 獨立圖表 1：通道 1（太陽輻照與幾何捕捉，專屬 4 個圖例） --------------------
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["POA_Wm2"], mode=mode_str, marker=marker_cfg,
                   name="🎯 POA 面板斜面有效輻照 (W/m²)", line=dict(color="#E11D48", width=2.6),
                   hovertemplate="<b>🎯 POA 斜面輻照度</b>：%{y:.0f} W/m²<extra></extra>"),
        secondary_y=False
    )
    fig1.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["GHI_Wm2"], mode=mode_str, marker=marker_cfg,
                   name="☀️ GHI 水平總日射 (W/m²)", line=dict(color="#D97706", width=2.2),
                   fill="tozeroy", fillcolor="rgba(245, 158, 11, 0.14)",
                   hovertemplate="<b>☀️ GHI 水平總日射</b>：%{y:.0f} W/m²<extra></extra>"),
        secondary_y=False
    )
    fig1.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["DHI_Wm2"], mode="lines",
                   name="☁️ DHI 天空散射光 (W/m²)", line=dict(color="#2563EB", width=1.9),
                   hovertemplate="<b>☁️ DHI 天空散射光</b>：%{y:.0f} W/m²<extra></extra>"),
        secondary_y=False
    )
    fig1.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["Incidence_Angle_deg"], mode="lines",
                   name="📐 太陽入射角 θi (°)", line=dict(color="#059669", width=1.6, dash="dot"),
                   hovertemplate="<b>📐 太陽入射角 θi</b>：%{y:.1f}°<extra></extra>"),
        secondary_y=True
    )
    fig1.update_yaxes(title_text="<b>輻照度 (W/m²)</b>", title_font=dict(color="#B45309", size=11.5), gridcolor="#E2E8F0", secondary_y=False)
    fig1.update_yaxes(title_text="<b>入射角 θi (°)</b>", title_font=dict(color="#059669", size=11), range=[0, 95], showgrid=False, secondary_y=True)
    fig1.update_xaxes(gridcolor="#E2E8F0", tickfont=dict(color="#1E293B", size=11), hoverformat="%Y-%m-%d %H:%M")
    fig1.update_layout(
        title=dict(text=f"<b>☀️ 通道 1：太陽輻照與幾何捕捉 —— 斜面有效輻照度 POA vs. 水平總日射 GHI vs. 散射光 DHI ({view_title})</b>", font=dict(size=14, color="#0F172A"), x=0.01, y=0.96),
        **common_layout
    )
    st.plotly_chart(fig1, use_container_width=True, key=f"{key_prefix}_ch1")

    # -------------------- 獨立圖表 2：通道 2（熱力學溫升與風速，專屬 3 個圖例） --------------------
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["T_cell_Faiman_C"], mode=mode_str, marker=marker_cfg,
                   name="🔥 Faiman 面板工作溫度 (°C)", line=dict(color="#DC2626", width=2.6),
                   hovertemplate="<b>🔥 Faiman 面板工作溫度</b>：%{y:.1f} °C<extra></extra>"),
        secondary_y=False
    )
    fig2.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["T_amb_C"], mode=mode_str, marker=marker_cfg,
                   name="🌡️ 測站環境氣溫 Tamb (°C)", line=dict(color="#059669", width=2.2),
                   hovertemplate="<b>🌡️ 環境氣溫 Tamb</b>：%{y:.1f} °C<extra></extra>"),
        secondary_y=False
    )
    fig2.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["Wind_ms"], mode="lines",
                   name="💨 案場風速 v (m/s)", line=dict(color="#0284C7", width=1.7, dash="dash"),
                   hovertemplate="<b>💨 案場風速 v</b>：%{y:.1f} m/s<extra></extra>"),
        secondary_y=True
    )
    fig2.update_yaxes(title_text="<b>溫度 (°C)</b>", title_font=dict(color="#DC2626", size=11.5), gridcolor="#E2E8F0", secondary_y=False)
    fig2.update_yaxes(title_text="<b>風速 (m/s)</b>", title_font=dict(color="#0284C7", size=11), showgrid=False, secondary_y=True)
    fig2.update_xaxes(gridcolor="#E2E8F0", tickfont=dict(color="#1E293B", size=11), hoverformat="%Y-%m-%d %H:%M")
    fig2.update_layout(
        title=dict(text=f"<b>🌡️ 通道 2：熱力學溫升 —— 測站氣溫 Tamb vs. Faiman 面板溫度 Tcell (左軸 °C) & 案場風速 v (右軸 m/s) ({view_title})</b>", font=dict(size=14, color="#0F172A"), x=0.01, y=0.96),
        **common_layout
    )
    st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_ch2")

    # -------------------- 獨立圖表 3：通道 3（PM2.5 積塵、降雨洗塵與無雨累積，專屬 3 個圖例） --------------------
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["PM25_ugm3"], mode=mode_str, marker=marker_cfg,
                   name="🌫️ PM2.5 細懸浮微粒 (μg/m³)", line=dict(color="#7C3AED", width=2.4),
                   fill="tozeroy", fillcolor="rgba(124, 58, 237, 0.12)",
                   hovertemplate="<b>🌫️ PM2.5 濃度</b>：%{y:.1f} μg/m³<extra></extra>"),
        secondary_y=False
    )
    fig3.add_trace(
        go.Bar(x=df_sub["timestamp"], y=df_sub["Rain_mm"], name="🌧️ 降雨量 (mm/hr)",
               marker_color="#0EA5E9", opacity=0.85,
               hovertemplate="<b>🌧️ 每小時降雨量</b>：%{y:.2f} mm<extra></extra>"),
        secondary_y=True
    )
    fig3.add_trace(
        go.Scatter(x=df_sub["timestamp"], y=df_sub["Dry_Hours_Since_Rain"], mode="lines",
                   name="⏳ 連續無雨時數 (hr)", line=dict(color="#D97706", width=2.0, dash="dot"),
                   hovertemplate="<b>⏳ 累積無雨時數</b>：%{y:.0f} 小時<extra></extra>"),
        secondary_y=True
    )
    fig3.update_yaxes(title_text="<b>PM2.5 (μg/m³)</b>", title_font=dict(color="#7C3AED", size=11.5), gridcolor="#E2E8F0", secondary_y=False)
    fig3.update_yaxes(title_text="<b>雨量(mm) / 無雨(hr)</b>", title_font=dict(color="#0284C7", size=11), showgrid=False, secondary_y=True)
    fig3.update_xaxes(gridcolor="#E2E8F0", tickfont=dict(color="#1E293B", size=11), hoverformat="%Y-%m-%d %H:%M")
    fig3.update_layout(
        title=dict(text=f"<b>🌫️ 通道 3：環境積塵與洗塵 —— PM2.5 濃度 (左軸) vs. 降雨量 (右軸藍柱) & 連續無雨時數 (右軸橘線) ({view_title})</b>", font=dict(size=14, color="#0F172A"), x=0.01, y=0.96),
        **common_layout
    )
    st.plotly_chart(fig3, use_container_width=True, key=f"{key_prefix}_ch3")


# ==================== 第一節：案場選擇、地圖與幾何聯動 ====================
st.markdown('<div class="section-banner">📍 第一節：選擇台灣代表性光電案場、空間地圖與太陽入射角幾何（連動第 1、2 章理論）</div>', unsafe_allow_html=True)

sec1_left, sec1_right = st.columns([1.15, 1.35], gap="large")

with sec1_left:
    selected_site_name = st.selectbox("🎯 請選擇要進行深度研究與資料串接的台灣光電案場：", list(TAIWAN_SOLAR_SITES.keys()), index=0)
    site_info = TAIWAN_SOLAR_SITES[selected_site_name]
    lat_val, lon_val = site_info["lat"], site_info["lon"]

    c_tilt1, c_tilt2 = st.columns([1.2, 1.0])
    with c_tilt1:
        panel_tilt_deg = st.slider(
            "📐 設定案場太陽能板固定傾角 β (導入第 2 章入射角計算)",
            0.0, 40.0, float(site_info["opt_tilt"]), step=1.0
        )
    with c_tilt2:
        today_doy = datetime.now().timetuple().tm_yday
        delta_today = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284.0 + today_doy)))
        noon_alpha = 90.0 - abs(lat_val - delta_today)
        noon_theta_i = abs((lat_val - delta_today) - panel_tilt_deg)
        noon_cos_eff = np.cos(np.radians(noon_theta_i)) * 100.0
        st.metric("☀️ 今日正午面板入射角 θi", f"{noon_theta_i:.1f}°", f"正午受光率 {noon_cos_eff:.1f}%")

    st.markdown(f"""
    <div class="site-profile-box">
        <b>🏗️ 案場工程型態</b>：{site_info['type']}<br>
        <b>⚡ 裝置容量規模</b>：{site_info['capacity']} ｜ <b>🧭 經緯度</b>：{lat_val}°N, {lon_val}°E<br>
        <b>📐 太陽幾何特性（第1、2章導入）</b>：今日赤緯角 $\\delta = {delta_today:+.2f}^\\circ$，正午仰角 $\\alpha_s = {noon_alpha:.1f}^\\circ$；當傾斜 $\\beta = {panel_tilt_deg:.0f}^\\circ$ 時，正午入射角 $\\theta_i = {noon_theta_i:.1f}^\\circ$。<br>
        <b>🌤️ 區域微氣候特徵</b>：{site_info['climate_feature']}<br>
        <b>🎯 數位孿生研究痛點</b>：{site_info['key_challenge']}
    </div>
    """, unsafe_allow_html=True)

with sec1_right:
    fig_map = build_taiwan_sites_map(selected_site_name)
    st.plotly_chart(fig_map, use_container_width=True, key="tw_solar_map")

# ==================== 第二節：後台起算日設定與管線驗證 ====================
st.markdown('<div class="section-banner">🗄️ 第二節：後台資料庫「錨定起算日 (Anchor Date)」設定與自動化管線檢核（已嚴格鎖定自 2026-08-18 起算）</div>', unsafe_allow_html=True)

today_date = datetime.now().date()
min_valid_anchor = date(2026, 8, 18)

sec2_c1, sec2_c2, sec2_c3 = st.columns([1.3, 1.0, 1.2], gap="medium")

with sec2_c1:
    anchor_mode = st.radio(
        "📌 選擇後台資料庫累積起點模式（最早鎖定自 2026-08-18 起算）：",
        [
            "📅 自 2026-08-18 完整累積至今（推薦用於跨月研究！）",
            "📌 自 2026-10-01 本月起算累積至今",
            "🗓️ 自訂錨定起算日（限 2026-08-18 之後）"
        ],
        index=0
    )

with sec2_c2:
    if "2026-08-18" in anchor_mode:
        start_d = min_valid_anchor
        st.info("🔒 **起算日已錨定為 `2026-08-18`**：已自動過濾 8/18 以前無效區間。")
    elif "2026-10-01" in anchor_mode:
        start_d = date(2026, 10, 1)
        st.info("🔒 **起算日已錨定為 `2026-10-01`**。")
    else:
        start_d = st.date_input("選擇自訂起算日（最早 2026-08-18）：", value=date(2026, 9, 1), min_value=min_valid_anchor, max_value=today_date)

    if st.button("🔄 立即重新同步雲端累積資料庫", use_container_width=True):
        st.cache_data.clear()

start_str = start_d.strftime("%Y-%m-%d")
end_str = today_date.strftime("%Y-%m-%d")

df_live, audit = fetch_cumulative_solar_and_air_data(lat_val, lon_val, panel_tilt_deg, start_str, end_str)
pipeline_healthy = audit["weather_api_ok"] and audit["air_api_ok"] and (audit["cleaned_rows"] >= 12)

with sec2_c3:
    if pipeline_healthy:
        st.success(
            f"✅ **【管線驗證通過】**\n"
            f"* **📌 首筆真實紀錄**：`{audit['first_record_time']}`\n"
            f"* **📡 最新入庫紀錄**：`{audit['latest_record_time']}`\n"
            f"* **📊 有效累積樣本**：共 **{audit['cleaned_rows']:,} 筆**（連續 **{audit['total_days']} 天**）"
        )
    else:
        st.error(f"❌ 連線異常：{audit['error_msg']}")

# ==================== 第三節：獨立三尺度監測面板（每張圖配備專屬圖例） ====================
st.markdown('<div class="section-banner">🔭 第三節：選擇時間檢視尺度（三通道各自擁有獨立專屬圖例，不再混雜！）</div>', unsafe_allow_html=True)

if pipeline_healthy and not df_live.empty:
    tab_day, tab_week, tab_custom = st.tabs([
        "📅 視圖 A：【當天 24 小時逐時精細圖】（含第 1、2 章太陽仰角 αs 與面板入射角 θi）",
        "📆 視圖 B：【最近一週 7 天趨勢圖】（過去 168 小時晴雨與溫升週期）",
        "🔍 視圖 C：【指定時間區段放大鏡】（自訂研究區間，預設聚焦 9/25 ～ 10/05 降雨洗塵事件）"
    ])

    min_avail_date = df_live["timestamp"].dt.date.min()
    max_avail_date = df_live["timestamp"].dt.date.max()

    with tab_day:
        d_col1, d_col2 = st.columns([1.0, 2.5], gap="medium")
        with d_col1:
            target_single_date = st.date_input("📅 選擇要研究的單一日期：", value=max_avail_date, min_value=min_avail_date, max_value=max_avail_date, key="single_day_picker")
        df_day = df_live[df_live["timestamp"].dt.date == target_single_date].copy()
        with d_col2:
            if not df_day.empty:
                st.info(
                    f"📊 **{site_info['short_name']} — {target_single_date} 單日摘要**：\n"
                    f"最高太陽仰角 **{df_day['Sun_Elevation_deg'].max():.1f}°** ｜ "
                    f"最小入射角 **θi = {df_day['Incidence_Angle_deg'].min():.1f}° (受光率 {df_day['Cosine_Eff_pct'].max():.1f}%)** ｜ "
                    f"最高斜面輻照 **POA = {df_day['POA_Wm2'].max():.0f} W/m²** ｜ "
                    f"最高面板溫 **{df_day['T_cell_Faiman_C'].max():.1f} °C**"
                )

        if not df_day.empty:
            fig_ang_day = build_ch1_ch2_angle_chart(df_day, site_info["short_name"], panel_tilt_deg, target_single_date)
            st.plotly_chart(fig_ang_day, use_container_width=True, key="chart_day_angles")

            render_separated_three_channel_charts(df_day, f"單日逐時：{target_single_date}", "day_view", show_markers=True)

    with tab_week:
        cutoff_7d = df_live["timestamp"].max() - pd.Timedelta(days=7)
        df_week = df_live[df_live["timestamp"] >= cutoff_7d].copy()
        st.info(
            f"📆 **【最近一週（7 天 / {len(df_week)} 小時）觀測區間】**：`{df_week['timestamp'].min().strftime('%Y-%m-%d %H:%M')}` ～ "
            f"`{df_week['timestamp'].max().strftime('%Y-%m-%d %H:%M')}` ｜ "
            f"最高斜面輻照 **POA = {df_week['POA_Wm2'].max():.0f} W/m²** ｜ "
            f"最高面板溫 **{df_week['T_cell_Faiman_C'].max():.1f} °C** ｜ 累積雨量 **{df_week['Rain_mm'].sum():.1f} mm**"
        )
        render_separated_three_channel_charts(df_week, "最近 7 天趨勢", "week_view", show_markers=False)

    with tab_custom:
        default_c_start = max(min_avail_date, date(2026, 9, 25)) if min_avail_date <= date(2026, 9, 25) else min_avail_date
        default_c_end = min(max_avail_date, date(2026, 10, 5)) if max_avail_date >= date(2026, 10, 5) else max_avail_date
        if default_c_start > default_c_end:
            default_c_start = max(min_avail_date, max_avail_date - timedelta(days=10))
            default_c_end = max_avail_date

        c_r1, c_r2, c_r3 = st.columns([1.0, 1.0, 2.2], gap="medium")
        with c_r1:
            custom_start = st.date_input("🔍 研究區段開始日期：", value=default_c_start, min_value=min_avail_date, max_value=max_avail_date, key="cust_s")
        with c_r2:
            custom_end = st.date_input("🔍 研究區段結束日期：", value=default_c_end, min_value=min_avail_date, max_value=max_avail_date, key="cust_e")

        if custom_start > custom_end:
            custom_start, custom_end = custom_end, custom_start

        df_custom = df_live[
            (df_live["timestamp"].dt.date >= custom_start) &
            (df_live["timestamp"].dt.date <= custom_end)
        ].copy()

        with c_r3:
            if not df_custom.empty:
                st.info(
                    f"🎯 **【{custom_start} ～ {custom_end} 區段統計（共 {len(df_custom)} 小時）】**：\n"
                    f"PM2.5 波動 **{df_custom['PM25_ugm3'].min():.1f} ～ {df_custom['PM25_ugm3'].max():.1f} μg/m³** ｜ "
                    f"區間總雨量 **{df_custom['Rain_mm'].sum():.1f} mm** ｜ 最長無雨 **{df_custom['Dry_Hours_Since_Rain'].max()} hr**"
                )

        if not df_custom.empty:
            use_mk = len(df_custom) <= 96
            render_separated_three_channel_charts(df_custom, f"指定區段：{custom_start} ～ {custom_end}", "custom_view", show_markers=use_mk)

# ==================== 第四節：物理定義與來源總表 ====================
st.markdown('<div class="section-banner">📖 第四節：監測數值物理定義、跨章節公式整合與真實資料來源總表</div>', unsafe_allow_html=True)

dict_col1, dict_col2 = st.columns([1.4, 1.0], gap="large")

with dict_col1:
    df_dict = pd.DataFrame([
        {
            "變數名稱與符號": "☀️ 太陽仰角 αs & 📐 入射角 θi",
            "單位": "度 (°)",
            "物理與工程定義": "由第 1、2 章球面三角學計算太陽高度角與面板法線夾角，決定餘弦受光效率。",
            "真實資料來源 (Provenance)": "第 1、2 章天文物理引擎 (經緯度、傾角 β 與時間演算)"
        },
        {
            "變數名稱與符號": "🎯 POA 面板斜面有效輻照度",
            "單位": "W/m²",
            "物理與工程定義": "整合第 2 章公式，為面板真正接收到的光功率。",
            "真實資料來源 (Provenance)": "向日葵衛星反演 DNI/DHI 結合第 2 章面板幾何合成"
        },
        {
            "變數名稱與符號": "☀️ GHI 水平總日射 / ☁️ DHI 散射",
            "單位": "W/m²",
            "物理與工程定義": "地表水平面接收之總短波輻照度與天空散射輻照度。",
            "真實資料來源 (Provenance)": "日本向日葵 8/9 號氣象衛星反演 + ECMWF ERA5 (Open-Meteo API)"
        },
        {
            "變數名稱與符號": "🔥 Faiman 面板溫度 Tcell",
            "單位": "°C",
            "物理與工程定義": "依據第 4 章 IEC 61853-2 標準公式推算之太陽能板工作溫度。",
            "真實資料來源 (Provenance)": "第 4 章熱力學引擎由實測氣溫、風速與 POA 演算"
        },
        {
            "變數名稱與符號": "🌫️ PM2.5 細懸浮微粒",
            "單位": "μg/m³",
            "物理與工程定義": "微粒濃度，造成大氣消光與面板表面乾季積塵 (Soiling)。",
            "真實資料來源 (Provenance)": "環境空品監測網與 CAMS 哥白尼大氣同化服務 (`pm2_5`)"
        },
        {
            "變數名稱與符號": "🌧️ 降雨量 & ⏳ 連續無雨時數",
            "單位": "mm / hr",
            "物理與工程定義": "每小時降雨觸發自然洗塵與水冷降溫；未降雨時累加無雨時數以量化積塵累積。",
            "真實資料來源 (Provenance)": "氣象雷達與雨量計同化資料 (`precipitation`) + 系統特徵工程"
        }
    ])
    st.dataframe(df_dict, use_container_width=True, hide_index=True, height=295)

with dict_col2:
    with st.container(border=True):
        st.markdown("##### 🔗 第一～四章理論如何在此會師？")
        st.markdown(
            "1. **第一章（天文座標）➔ 太陽仰角 $\\alpha_s$**：根據案場緯度即時算出每一小時太陽高度。\n"
            "2. **第二章（追日與入射幾何）➔ 入射角 $\\theta_i$ 與 $G_{\\text{POA}}$**：結合面板傾角 $\\beta$ 與衛星實測 $\\text{DNI}, \\text{DHI}$。\n"
            "3. **第四章（微氣候散熱）➔ $T_{\\text{cell}}$ 與積塵/雨洗特徵**：用 `POA_Wm2`、氣溫與風速算出 Faiman 溫度。"
        )
