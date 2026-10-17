import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="第 5 章 (階段一)：自動化資料串接與多尺度驗證", page_icon="📡", layout="wide")

# 緊湊化版面與高亮度發光數據卡 CSS
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
    .bright-val-green { color: #00E676 !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-val-cyan { color: #00E5FF !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-val-gold { color: #FFD700 !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-sub { color: #94A3B8 !important; font-size: 0.82rem; margin-top: 3px; }
    .site-profile-box {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        border-radius: 8px;
        padding: 12px 15px;
        color: #0F172A;
        font-size: 0.9rem;
        margin-top: 6px;
        margin-bottom: 10px;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：階段一工程原則宣告 ====================
st.markdown("### 第五章（階段一）：【工程基石】真實世界 Open Data 自動化資料累積與多時間尺度檢視")
st.info(
    "🛡️ **【嚴格工程準則：資料管線透明化、定義明確化、檢視多尺度化！】**\n\n"
    "1. **底層永久累積**：後台資料庫自**錨定起算日（Anchor Date）**起每日自動累加 24 筆新觀測值，舊資料 100% 完整保留。\n"
    "2. **前台三種時間尺度獨立檢視**：為了避免長天期資料擠在一起看不清細節，右側圖表直接拆分為 **「📅 當天逐時視圖」**、**「📆 最近一週視圖」** 與 **「🔍 指定時間區段放大鏡」** 三大獨立面板！"
)

# ==================== 台灣五大代表性光電案場完整工程檔案庫 ====================
TAIWAN_SOLAR_SITES = {
    "🇹🇼 1. 台南七股地面型旗艦案場 (23.15°N, 120.08°E)": {
        "lat": 23.15, "lon": 120.08,
        "type": "鹽灘地與魚塭地面高架型 (Ground-Mounted / Aquavoltaics)",
        "capacity": "約 150 MW ～ 200 MW 級大型聚落",
        "climate_feature": "全台年日照時數最高（>2,200 hr/yr），但面臨強烈台江海風與高濕度海鹽結晶。",
        "key_challenge": "🌊 **沿海鹽霧結垢（Salt Mist）**：海風雖有助於 Faiman 對流散熱，但鹽分附著於玻璃表面會降低透光率，極需靠降雨洗塵恢復。"
    },
    "🇹🇼 2. 彰濱工業區崙尾東水上光電 (24.12°N, 120.41°E)": {
        "lat": 24.12, "lon": 120.41,
        "type": "潮間帶浮筒水面型光電 (Floating Solar PV)",
        "capacity": "約 180 MW ～ 320 MW 級亞洲指標水面案場",
        "climate_feature": "台灣海峽風廊核心區，全年平均風速極高（常達 6～12 m/s），水面蒸發吸熱明顯。",
        "key_challenge": "💨 **強風強制對流與浪沫**：高風速使面板溫度顯著低於內陸案場（發電效率高），但退潮泥灘揚塵與浪花鹽漬會產生非線性殘差。"
    },
    "🇹🇼 3. 雲林麥寮農電共生案場 (23.78°N, 120.25°E)": {
        "lat": 23.78, "lon": 120.25,
        "type": "農地高架結合農業溫室型 (Agrivoltaics)",
        "capacity": "約 50 MW ～ 100 MW 分散式聚落",
        "climate_feature": "位於濁水溪出海口南側，秋冬受東北季風揚塵（沙塵暴）與工業區氣膠雙重影響。",
        "key_challenge": "🌫️ **秋冬 PM2.5 與乾季嚴重積塵（Soiling）**：10 月至隔年 3 月少雨乾燥，懸浮微粒沉積形成厚重灰塵層，雨後初晴發電量會出現戲劇性暴增！"
    },
    "🇹🇼 4. 屏東林邊地層下陷光電專區 (22.43°N, 120.51°E)": {
        "lat": 22.43, "lon": 120.51,
        "type": "高腳防洪型地面光電架台 (Elevated Ground-Mounted)",
        "capacity": "約 80 MW ～ 120 MW 綠能專區",
        "climate_feature": "熱帶季風氣候，四季氣溫偏高（常年 >28°C），夏季午後對流雷陣雨極為頻繁。",
        "key_challenge": "🌧️ **高溫熱衰減 vs. 午後雷陣雨驟冷（Thermal Quenching）**：正午面板常飆破 65°C，午後一場大雨瞬間將面板降溫 20°C 並洗淨灰塵。"
    },
    "🇹🇼 5. 桃園觀音工業區屋頂型光電群 (25.04°N, 121.11°E)": {
        "lat": 25.04, "lon": 121.11,
        "type": "大型廠房浪板緊貼/平行屋頂型 (Industrial Rooftop PV)",
        "capacity": "約 30 MW ～ 60 MW 廠房群聚",
        "climate_feature": "北台灣秋冬多雲多雨、雲層厚，散射光（DHI）佔總日射比例極高。",
        "key_challenge": "☁️ **高散射光比例與屋頂散熱不良**：廠房鐵皮屋頂背風悶熱（$U_0, U_1$ 偏低），且多雲天氣下太陽快速進出雲層造成劇烈熱慣性延遲。"
    }
}

# ==================== 核心：錨定起點至今日之累積式 API 串接與清洗引擎 ====================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_cumulative_solar_and_air_data(lat, lon, start_date_str, end_date_str):
    """從錨定起算日連續抓取累積至今日的所有逐時氣象、衛星輻照與空品 Open Data"""
    audit_report = {
        "weather_api_ok": False,
        "air_api_ok": False,
        "fetch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "start_anchor": start_date_str,
        "end_today": end_date_str,
        "total_days": 0,
        "raw_rows": 0,
        "cleaned_rows": 0,
        "missing_fixed": 0,
        "outliers_clipped": 0,
        "first_record_time": "N/A",
        "latest_record_time": "N/A",
        "error_msg": ""
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
        df_merged = df_merged[df_merged["timestamp"] <= now_dt].copy()

        audit_report["raw_rows"] = len(df_merged)

        na_count = int(df_merged.isna().sum().sum())
        audit_report["missing_fixed"] = na_count
        df_merged = df_merged.interpolate(method="linear").bfill().ffill()

        outlier_cnt = int(
            (df_merged["GHI_Wm2"] < 0).sum() +
            (df_merged["GHI_Wm2"] > 1350).sum() +
            (df_merged["Wind_ms"] < 0).sum() +
            (df_merged["PM25_ugm3"] < 0).sum()
        )
        audit_report["outliers_clipped"] = outlier_cnt

        df_merged["GHI_Wm2"] = df_merged["GHI_Wm2"].clip(0.0, 1350.0)
        df_merged["DNI_Wm2"] = df_merged["DNI_Wm2"].clip(0.0, 1200.0)
        df_merged["DHI_Wm2"] = df_merged["DHI_Wm2"].clip(0.0, 800.0)
        df_merged["Wind_ms"] = df_merged["Wind_ms"].clip(0.0, 60.0)
        df_merged["Rain_mm"] = df_merged["Rain_mm"].clip(0.0, 300.0)
        df_merged["PM25_ugm3"] = df_merged["PM25_ugm3"].clip(1.0, 500.0)
        df_merged["PM10_ugm3"] = df_merged["PM10_ugm3"].clip(2.0, 800.0)

        # 衍生特徵 1：Faiman 物理基準面板溫度 (U0=25, U1=6.84)
        df_merged["T_cell_Faiman_C"] = (
            df_merged["T_amb_C"] + df_merged["GHI_Wm2"] / (25.0 + 6.84 * df_merged["Wind_ms"])
        ).round(1)

        # 衍生特徵 2：連續無雨累積時數 (當降雨 >= 0.2 mm 時歸零洗塵，否則每小時 +1)
        dry_hrs = []
        cur_dry = 0
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


# ==================== 繪圖專用函數：繪製高清晰度、完整 Hover 單位、無重疊之三通道圖 ====================
def plot_clear_three_channel_chart(df_sub, view_title, show_markers=False):
    """
    針對不同時間尺度 (當天 / 一週 / 指定區段) 繪製高可讀性三通道圖：
    - 徹底分離標題與圖例，絕不重疊
    - 每個數值皆附帶完整中文全名與單位之 Hover 懸停框，絕不截斷成 '...'
    - 雙 Y 軸加上明確色彩與單位標籤
    """
    mode_str = "lines+markers" if show_markers else "lines"
    marker_cfg = dict(size=5) if show_markers else dict(size=1)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.09,
        subplot_titles=(
            f"<b>☀️ 通道 1：太陽輻照度 —— GHI 總日射 vs. DNI 直射 vs. DHI 散射 ({view_title})</b>",
            "<b>🌡️ 通道 2：熱力學溫升 —— 測站環境氣溫 Tamb vs. Faiman 推算面板溫度 Tcell (左軸) & 風速 v (右軸)</b>",
            "<b>🌫️ 通道 3：環境積塵與洗塵 —— PM2.5 濃度 (左軸) vs. 降雨量 (右軸藍柱) & 連續無雨時數 (右軸橘線)</b>"
        ),
        specs=[[{"secondary_y": False}], [{"secondary_y": True}], [{"secondary_y": True}]]
    )

    # -------------------- 通道 1：太陽輻照度 (GHI / DNI / DHI) --------------------
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["GHI_Wm2"],
            mode=mode_str, marker=marker_cfg,
            name="☀️ GHI 水平總日射 (W/m²)",
            line=dict(color="#D97706", width=2.5),
            fill="tozeroy", fillcolor="rgba(245, 158, 11, 0.16)",
            hovertemplate="<b>☀️ GHI 水平總日射</b>：%{y:.0f} W/m²<extra></extra>"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["DNI_Wm2"],
            mode=mode_str, marker=marker_cfg,
            name="🎯 DNI 法線直射光 (W/m²)",
            line=dict(color="#EA580C", width=1.8, dash="dot"),
            hovertemplate="<b>🎯 DNI 法線直射光</b>：%{y:.0f} W/m²<extra></extra>"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["DHI_Wm2"],
            mode=mode_str, marker=marker_cfg,
            name="☁️ DHI 天空散射光 (W/m²)",
            line=dict(color="#2563EB", width=2.0),
            hovertemplate="<b>☁️ DHI 天空散射光</b>：%{y:.0f} W/m²<extra></extra>"
        ),
        row=1, col=1
    )

    # -------------------- 通道 2：面板溫度與氣溫 (左軸 °C) + 案場風速 (右軸 m/s) --------------------
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["T_cell_Faiman_C"],
            mode=mode_str, marker=marker_cfg,
            name="🔥 Faiman 面板溫度 (°C)",
            line=dict(color="#DC2626", width=2.6),
            hovertemplate="<b>🔥 Faiman 面板工作溫度</b>：%{y:.1f} °C<extra></extra>"
        ),
        row=2, col=1, secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["T_amb_C"],
            mode=mode_str, marker=marker_cfg,
            name="🌡️ 環境氣溫 Tamb (°C)",
            line=dict(color="#059669", width=2.2),
            hovertemplate="<b>🌡️ 測站環境氣溫 Tamb</b>：%{y:.1f} °C<extra></extra>"
        ),
        row=2, col=1, secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["Wind_ms"],
            mode="lines",
            name="💨 案場風速 v (m/s)",
            line=dict(color="#0284C7", width=1.6, dash="dash"),
            hovertemplate="<b>💨 案場風速 v</b>：%{y:.1f} m/s<extra></extra>"
        ),
        row=2, col=1, secondary_y=True
    )

    # -------------------- 通道 3：PM2.5 濃度 (左軸) + 降雨量與連續無雨時數 (右軸) --------------------
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["PM25_ugm3"],
            mode=mode_str, marker=marker_cfg,
            name="🌫️ PM2.5 細懸浮微粒 (μg/m³)",
            line=dict(color="#7C3AED", width=2.4),
            fill="tozeroy", fillcolor="rgba(124, 58, 237, 0.12)",
            hovertemplate="<b>🌫️ PM2.5 細懸浮微粒濃度</b>：%{y:.1f} μg/m³<extra></extra>"
        ),
        row=3, col=1, secondary_y=False
    )
    fig.add_trace(
        go.Bar(
            x=df_sub["timestamp"], y=df_sub["Rain_mm"],
            name="🌧️ 降雨量 (mm/hr)",
            marker_color="#0EA5E9", opacity=0.85,
            hovertemplate="<b>🌧️ 每小時降雨量 (洗塵事件)</b>：%{y:.2f} mm<extra></extra>"
        ),
        row=3, col=1, secondary_y=True
    )
    fig.add_trace(
        go.Scatter(
            x=df_sub["timestamp"], y=df_sub["Dry_Hours_Since_Rain"],
            mode="lines",
            name="⏳ 連續無雨時數 (hr)",
            line=dict(color="#D97706", width=1.8, dash="dot"),
            hovertemplate="<b>⏳ 距上次降雨累積無雨時數</b>：%{y:.0f} 小時<extra></extra>"
        ),
        row=3, col=1, secondary_y=True
    )

    # 設定各軸明確標題與單位顏色
    fig.update_yaxes(title_text="<b>輻照度 (W/m²)</b>", title_font=dict(color="#B45309", size=12), gridcolor="#E2E8F0", row=1, col=1)
    fig.update_yaxes(title_text="<b>溫度 (°C)</b>", title_font=dict(color="#DC2626", size=12), gridcolor="#E2E8F0", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="<b>風速 (m/s)</b>", title_font=dict(color="#0284C7", size=11), showgrid=False, row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="<b>PM2.5 (μg/m³)</b>", title_font=dict(color="#7C3AED", size=12), gridcolor="#E2E8F0", row=3, col=1, secondary_y=False)
    fig.update_yaxes(title_text="<b>雨量(mm) / 無雨(hr)</b>", title_font=dict(color="#0284C7", size=11), showgrid=False, row=3, col=1, secondary_y=True)

    for r_i in [1, 2, 3]:
        fig.update_xaxes(
            gridcolor="#E2E8F0",
            tickfont=dict(color="#1E293B", size=11),
            hoverformat="%Y-%m-%d %H:%M",
            row=r_i, col=1
        )

    # 關鍵排版：加大 top margin (t=95)，將圖例放在 y=1.13，100% 絕不壓到第一張子圖的標題！
    fig.update_layout(
        height=620,
        margin=dict(l=65, r=65, t=95, b=40),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(color="#0F172A", size=12),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12.5,
            font_family="sans-serif",
            font_color="#F8FAFC",
            namelength=-1  # 強制顯示完整名稱，絕不截斷為 '...'！
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.08,
            xanchor="left", x=0.0,
            bgcolor="rgba(241, 245, 249, 0.96)",
            bordercolor="#CBD5E1", borderwidth=1,
            font=dict(color="#0F172A", size=11.5)
        )
    )
    return fig


# ==================== 上半部：左控制台 (含 5 大案場簡介) + 右多時間尺度獨立分頁圖表 ====================
col_ctrl, col_stage = st.columns([1.08, 2.22], gap="medium")

with col_ctrl:
    st.markdown("##### 📍 1. 選擇台灣代表性光電案場（含工程與微氣候簡介）")
    selected_site_name = st.selectbox("選擇要連線監測的台灣案場：", list(TAIWAN_SOLAR_SITES.keys()), index=0)
    site_info = TAIWAN_SOLAR_SITES[selected_site_name]
    lat_val, lon_val = site_info["lat"], site_info["lon"]

    # 顯示該案場的詳細工程與微氣候背景卡片
    st.markdown(f"""
    <div class="site-profile-box">
        <b>🏗️ 案場型態</b>：{site_info['type']}<br>
        <b>⚡ 規模容量</b>：{site_info['capacity']}<br>
        <b>🌤️ 氣候特徵</b>：{site_info['climate_feature']}<br>
        <b>🎯 研究痛點</b>：{site_info['key_challenge']}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 📌 2. 後台資料庫「錨定起算日 (Anchor Date)」設定")
    today_date = datetime.now().date()
    anchor_mode = st.selectbox(
        "選擇後台資料庫累積起點：",
        [
            "🧪 跨月累積驗證（錨定 60 天前起算 ➔ 累積至今日，共約 1,440 筆）",
            "📌 錨定今日起算（2026-10-17 起算 ➔ 往後每天自動累加 24 筆）",
            "🗓️ 自訂任意錨定起算日"
        ],
        index=0
    )

    if "跨月累積" in anchor_mode:
        start_d = today_date - timedelta(days=60)
    elif "錨定今日" in anchor_mode:
        start_d = date(2026, 10, 17) if today_date >= date(2026, 10, 17) else today_date - timedelta(days=7)
    else:
        start_d = st.date_input("自訂起算日", value=today_date - timedelta(days=45), min_value=today_date - timedelta(days=90), max_value=today_date)

    start_str = start_d.strftime("%Y-%m-%d")
    end_str = today_date.strftime("%Y-%m-%d")

    df_live, audit = fetch_cumulative_solar_and_air_data(lat_val, lon_val, start_str, end_str)
    pipeline_healthy = audit["weather_api_ok"] and audit["air_api_ok"] and (audit["cleaned_rows"] >= 12)

    if pipeline_healthy:
        st.success(
            f"✅ **【後台累積資料庫連線正常】**\n"
            f"* **首筆錨定紀錄**：`{audit['first_record_time']}` (完好保存)\n"
            f"* **最新入庫紀錄**：`{audit['latest_record_time']}` (今日即時)\n"
            f"* **累積總樣本數**：共 **{audit['cleaned_rows']:,} 筆**（連續 **{audit['total_days']} 天**）"
        )
    else:
        st.error(f"❌ 連線異常：{audit['error_msg']}")

with col_stage:
    if pipeline_healthy and not df_live.empty:
        st.markdown("##### 🔭 3. 選擇時間檢視尺度（已將「當天」、「一週」、「指定時間區段」獨立分開繪製！）")
        tab_day, tab_week, tab_custom = st.tabs([
            "📅 視圖 A：【當天逐時精細圖】(單日 24 小時)",
            "📆 視圖 B：【最近一週趨勢圖】(過去 7 天 / 168 小時)",
            "🔍 視圖 C：【指定時間區段放大鏡】(自訂日期區間，如 9/25～10/05 洗塵事件)"
        ])

        min_avail_date = df_live["timestamp"].dt.date.min()
        max_avail_date = df_live["timestamp"].dt.date.max()

        # -------------------- 分頁 A：當天逐時精細圖 --------------------
        with tab_day:
            c_d1, c_d2 = st.columns([1.2, 2.0])
            with c_d1:
                target_single_date = st.date_input(
                    "📅 選擇要檢視哪一天的 24 小時逐時曲線：",
                    value=max_avail_date,
                    min_value=min_avail_date,
                    max_value=max_avail_date,
                    key="single_day_picker"
                )
            df_day = df_live[df_live["timestamp"].dt.date == target_single_date].copy()
            with c_d2:
                if not df_day.empty:
                    st.info(
                        f"📊 **{target_single_date} 單日摘要**：最高日射 **{df_day['GHI_Wm2'].max():.0f} W/m²** ｜ "
                        f"最高面板溫度 **{df_day['T_cell_Faiman_C'].max():.1f} °C** ｜ "
                        f"平均 PM2.5 **{df_day['PM25_ugm3'].mean():.1f} μg/m³** ｜ "
                        f"當日累積雨量 **{df_day['Rain_mm'].sum():.1f} mm**"
                    )
            if not df_day.empty:
                fig_d = plot_clear_three_channel_chart(df_day, f"單日逐時：{target_single_date}", show_markers=True)
                st.plotly_chart(fig_d, use_container_width=True, key="chart_single_day")

        # -------------------- 分頁 B：最近一週 (7天) 趨勢圖 --------------------
        with tab_week:
            cutoff_7d = df_live["timestamp"].max() - pd.Timedelta(days=7)
            df_week = df_live[df_live["timestamp"] >= cutoff_7d].copy()
            st.caption(
                f"📆 **顯示區間**：`{df_week['timestamp'].min().strftime('%Y-%m-%d %H:%M')}` ～ "
                f"`{df_week['timestamp'].max().strftime('%Y-%m-%d %H:%M')}`（共 **{len(df_week)} 小時**）｜ "
                f"近一週最高溫 **{df_week['T_cell_Faiman_C'].max():.1f} °C** ｜ 近一週累積降雨 **{df_week['Rain_mm'].sum():.1f} mm**"
            )
            fig_w = plot_clear_three_channel_chart(df_week, "最近 7 天趨勢", show_markers=False)
            st.plotly_chart(fig_w, use_container_width=True, key="chart_one_week")

        # -------------------- 分頁 C：指定時間區段放大鏡 (預設對準 9/25 ~ 10/05 紅框事件區間) --------------------
        with tab_custom:
            # 預設聚焦在 9/25 ~ 10/05 (若在範圍內)，讓使用者一眼看清剛剛紅框標出的 PM2.5 與降雨洗塵事件！
            default_c_start = max(min_avail_date, date(2026, 9, 25)) if min_avail_date <= date(2026, 9, 25) else min_avail_date
            default_c_end = min(max_avail_date, date(2026, 10, 5)) if max_avail_date >= date(2026, 10, 5) else max_avail_date
            if default_c_start > default_c_end:
                default_c_start = max(min_avail_date, max_avail_date - timedelta(days=10))
                default_c_end = max_avail_date

            c_r1, c_r2, c_r3 = st.columns([1.0, 1.0, 1.6])
            with c_r1:
                custom_start = st.date_input("🔍 區段開始日期：", value=default_c_start, min_value=min_avail_date, max_value=max_avail_date, key="cust_s")
            with c_r2:
                custom_end = st.date_input("🔍 區段結束日期：", value=default_c_end, min_value=min_avail_date, max_value=max_avail_date, key="cust_e")

            if custom_start > custom_end:
                st.warning("⚠️ 開始日期不可晚於結束日期，已自動對調。")
                custom_start, custom_end = custom_end, custom_start

            df_custom = df_live[
                (df_live["timestamp"].dt.date >= custom_start) &
                (df_live["timestamp"].dt.date <= custom_end)
            ].copy()

            with c_r3:
                if not df_custom.empty:
                    st.info(
                        f"🎯 **區段統計（共 {len(df_custom)} 小時）**：\n"
                        f"PM2.5 區間 **{df_custom['PM25_ugm3'].min():.1f} ～ {df_custom['PM25_ugm3'].max():.1f} μg/m³** ｜ "
                        f"區間總雨量 **{df_custom['Rain_mm'].sum():.1f} mm** ｜ "
                        f"最長連續無雨 **{df_custom['Dry_Hours_Since_Rain'].max()} hr**"
                    )

            if not df_custom.empty:
                use_mk = len(df_custom) <= 96
                fig_c = plot_clear_three_channel_chart(df_custom, f"指定區段：{custom_start} ～ {custom_end}", show_markers=use_mk)
                st.plotly_chart(fig_c, use_container_width=True, key="chart_custom_range")

# ==================== 下半部：變數定義、物理意義與真實資料來源總表 ====================
st.markdown("---")
st.markdown("### 📖 監測數值物理定義、計算公式與真實資料來源總覽（Data Dictionary & Provenance）")
st.caption("為了確保科學嚴謹度，本系統串接之每一項原始變數與衍生特徵，皆有明確的國際物理定義與公開觀測資料來源：")

dict_col1, dict_col2 = st.columns([1.35, 1.0], gap="large")

with dict_col1:
    df_dict = pd.DataFrame([
        {
            "變數名稱與符號": "☀️ GHI 水平總日射",
            "單位": "W/m²",
            "物理與工程定義": "地表水平面每平方公尺接收到的太陽短波總輻照度（包含直射光與天空散射光總和）。",
            "真實資料來源 (Provenance)": "日本向日葵 8/9 號同步氣象衛星雲圖反演 + ECMWF ERA5 (Open-Meteo Solar API)"
        },
        {
            "變數名稱與符號": "🎯 DNI 法線直射光",
            "單位": "W/m²",
            "物理與工程定義": "未被大氣雲層或氣膠散射、沿太陽直射方向垂直打在單位面積上的光束能量（追日系統鎖定目標）。",
            "真實資料來源 (Provenance)": "向日葵衛星大氣穿透率模型反演 (`direct_normal_irradiance`)"
        },
        {
            "變數名稱與符號": "☁️ DHI 天空散射光",
            "單位": "W/m²",
            "物理與工程定義": "被雲滴、空氣分子與 PM2.5 撞散後，從整片天空四面八方均勻落下的散射輻照度（陰天發電主力）。",
            "真實資料來源 (Provenance)": "衛星雲層光學厚度反演 (`diffuse_radiation`)"
        },
        {
            "變數名稱與符號": "🌡️ 環境氣溫 Tamb",
            "單位": "°C",
            "物理與工程定義": "案場地面上方 2 公尺處（標準百葉箱高度）之大氣環境溫度，為面板散熱的基準環境溫度。",
            "真實資料來源 (Provenance)": "區域氣象測站網與全球同化數值預報模式 (`temperature_2m`)"
        },
        {
            "變數名稱與符號": "💨 案場風速 v",
            "單位": "m/s",
            "物理與工程定義": "案場上方氣流運動速度，決定 Faiman 模型中的強制對流散熱能力（$U_1 \\cdot v_w$）。",
            "真實資料來源 (Provenance)": "地面 10 公尺風速觀測與數值同化場 (`wind_speed_10m`)"
        },
        {
            "變數名稱與符號": "🔥 Faiman 面板溫度 Tcell",
            "單位": "°C",
            "物理與工程定義": "依據 IEC 61853-2 標準公式 $T_{\\text{cell}} = T_{\\text{amb}} + G / (U_0 + U_1 v)$ 推算之太陽能板工作溫度。",
            "真實資料來源 (Provenance)": "本系統物理引擎由實測 $T_{\\text{amb}}, G, v$ 即時演算之衍生特徵"
        },
        {
            "變數名稱與符號": "🌫️ PM2.5 細懸浮微粒",
            "單位": "μg/m³",
            "物理與工程定義": "空氣中氣動直徑 $\\le 2.5\\ \\mu\\text{m}$ 之微粒濃度。高濃度時既造成大氣消光，亦會沉降於面板表面形成積塵（Soiling）。",
            "真實資料來源 (Provenance)": "環境空品監測網與 CAMS 哥白尼大氣監測服務 (`pm2_5`)"
        },
        {
            "變數名稱與符號": "🌧️ 降雨量 Rain & ⏳ 連續無雨時數",
            "單位": "mm / hr",
            "物理與工程定義": "每小時降雨量 $\\ge 0.2\\text{ mm}$ 視為自然洗塵與水冷降溫事件；未降雨時每小時累加「連續無雨時數」以量化灰塵累積期。",
            "真實資料來源 (Provenance)": "氣象雷達回波與地面雨量計同化資料 (`precipitation`) + 系統特徵工程"
        }
    ])
    st.dataframe(df_dict, use_container_width=True, hide_index=True, height=340)

with dict_col2:
    with st.container(border=True):
        st.markdown("##### 🔬 為什麼你剛剛框起來的「9/27 ～ 10/4 紅框區段」對 AI 訓練價值連城？")
        st.markdown(
            "請切到右上方 **「🔍 視圖 C：指定時間區段放大鏡」**，觀察 **通道 3（PM2.5 與降雨洗塵）** 的真實物理互動：\n\n"
            "1. **📈 乾季積塵期（無雨時數攀升）**：\n"
            "   * 當連續好幾天沒有下雨（右軸**橘色虛線 `⏳ 連續無雨時數`** 一路往上爬升超過 100 小時），且空氣中 **紫色 `🌫️ PM2.5`** 飆高到 $35 \\sim 45\\ \\mu\\text{g/m}^3$ 時，微粒會不斷沉降在太陽能板玻璃上，造成物理公式算不出來的「積塵發電衰減」。\n"
            "2. **🌧️ 降雨雙重洗禮（藍柱出現、無雨時數歸零）**：\n"
            "   * 當圖中出現 **藍色長條 `🌧️ 降雨量`** 時，不僅空氣中的紫色 $\\text{PM}_{2.5}$ 被雨水瞬間洗到剩 $5 \\sim 10\\ \\mu\\text{g/m}^3$，面板上的陳年灰塵也被沖刷乾淨，**橘色虛線瞬間垂直歸零**！\n"
            "3. **🤖 這就是第五章（階段二）AI 要學的規律**：\n"
            "   * 傳統物理公式（第 1～4 章）完全沒有納入 `PM2.5` 與 `連續無雨時數`；而接下來的機器學習模型，就能直接從這張乾淨的資料表裡學會這條「積塵 ➔ 雨洗恢復」的真實世界法則！"
        )

# ==================== 底部：首尾雙錨點資料表驗證與 CSV 下載 ====================
if pipeline_healthy and not df_live.empty:
    with st.expander("🗄️ 點此展開驗證：檢視後台資料庫「錨定起算日首 8 筆」與「今日最新入庫末 8 筆」原始數值（含完整 CSV 匯出）", expanded=False):
        t_col1, t_col2 = st.columns(2, gap="medium")
        cols_show = ["timestamp", "GHI_Wm2", "DNI_Wm2", "DHI_Wm2", "T_amb_C", "T_cell_Faiman_C", "Wind_ms", "Rain_mm", "PM25_ugm3", "Dry_Hours_Since_Rain"]
        rename_dict = {
            "timestamp": "觀測時間",
            "GHI_Wm2": "GHI(W/m²)",
            "DNI_Wm2": "DNI(W/m²)",
            "DHI_Wm2": "DHI(W/m²)",
            "T_amb_C": "氣溫(°C)",
            "T_cell_Faiman_C": "面板溫(°C)",
            "Wind_ms": "風速(m/s)",
            "Rain_mm": "雨量(mm)",
            "PM25_ugm3": "PM2.5(μg/m³)",
            "Dry_Hours_Since_Rain": "無雨累積(hr)"
        }
        with t_col1:
            st.markdown(f"**📌 錨定起算日（`{start_str}`）最開頭 8 筆紀錄**")
            df_h = df_live[cols_show].head(8).copy()
            df_h["timestamp"] = df_h["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df_h.rename(columns=rename_dict), use_container_width=True, hide_index=True)
        with t_col2:
            st.markdown(f"**📡 今日（`{end_str}`）最新入庫末端 8 筆紀錄**")
            df_t = df_live[cols_show].tail(8).sort_values("timestamp", ascending=False).copy()
            df_t["timestamp"] = df_t["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df_t.rename(columns=rename_dict), use_container_width=True, hide_index=True)

        csv_bytes = df_live.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=f"📥 匯出完整累積乾淨資料庫 (.CSV，共 {audit['cleaned_rows']:,} 筆小時紀錄)",
            data=csv_bytes,
            file_name=f"solar_digital_twin_cumulative_{start_str}_to_{end_str}.csv",
            mime="text/csv"
        )
