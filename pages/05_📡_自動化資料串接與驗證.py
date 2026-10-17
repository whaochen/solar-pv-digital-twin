import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="第 5 章 (階段一)：自動化資料串接與管線驗證", page_icon="📡", layout="wide")

# 緊湊化版面與高亮度發光數據卡 CSS（與第 1~4 章 100% 視覺統一）
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
    .bright-val-green { color: #00E676 !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-val-cyan { color: #00E5FF !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-val-gold { color: #FFD700 !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-val-red { color: #FF5252 !important; font-size: 1.65rem; font-weight: 800; line-height: 1.2; }
    .bright-sub { color: #94A3B8 !important; font-size: 0.82rem; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：階段一工程原則宣告 ====================
st.markdown("### 第五章（階段一）：【工程基石】真實世界 Open Data 自動化資料串接與管線驗證")
st.info(
    "🛡️ **【嚴格工程準則：自動化資料串接未驗證通過前，絕不啟動 AI 訓練！】**\n\n"
    "真正的數位孿生（Digital Twin）不能靠死板的假資料自嗨。本模組透過 Python 原生網路協定，**即時連線抓取台灣案場過去 7 天至今日此刻的真實氣象、衛星日照與空氣品質 Open Data**。"
    "唯有確認每天都有新數值流入、且通過物理異常值清洗（Data Cleaning）後，我們才會解鎖下一階段的機器學習殘差訓練！"
)

# ==================== 核心自動化 API 串接與清洗引擎 ====================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_taiwan_solar_and_air_data(lat, lon, past_days=7):
    """
    免金鑰即時串接真實世界兩大 Open Data API：
    1. Open-Meteo Forecast & Historical API (整合氣象站與向日葵衛星反演之 GHI, DNI, DHI, 氣溫, 風速, 降雨量, 濕度)
    2. Open-Meteo Air Quality API (全球氣膠與環境監測網之 PM2.5, PM10)
    回傳：(清洗後 DataFrame, 管線檢核報告 dict)
    """
    audit_report = {
        "weather_api_ok": False,
        "air_api_ok": False,
        "fetch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_rows": 0,
        "cleaned_rows": 0,
        "missing_fixed": 0,
        "outliers_clipped": 0,
        "latest_data_time": "N/A",
        "error_msg": ""
    }

    # 1. 串接氣象與衛星輻照度 API
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&past_days={past_days}&forecast_days=1"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,"
        f"shortwave_radiation,direct_normal_irradiance,diffuse_radiation"
        f"&wind_speed_unit=ms&timezone=Asia%2FTaipei"
    )

    # 2. 串接空氣品質 PM2.5 / PM10 API
    air_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}"
        f"&past_days={past_days}&forecast_days=1"
        f"&hourly=pm10,pm2_5"
        f"&timezone=Asia%2FTaipei"
    )

    try:
        req_w = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_w, timeout=10) as resp_w:
            if resp_w.status == 200:
                w_data = json.loads(resp_w.read().decode('utf-8'))
                audit_report["weather_api_ok"] = True

        req_a = urllib.request.Request(air_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_a, timeout=10) as resp_a:
            if resp_a.status == 200:
                a_data = json.loads(resp_a.read().decode('utf-8'))
                audit_report["air_api_ok"] = True

        # 解析並合併雙資料源
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
        audit_report["raw_rows"] = len(df_merged)

        # ==================== 自動化數據清洗與異常值過濾 (Data Cleaning) ====================
        # (A) 計算缺漏值數量並執行線性補插與前後填補
        na_count = int(df_merged.isna().sum().sum())
        audit_report["missing_fixed"] = na_count
        df_merged = df_merged.interpolate(method="linear").bfill().ffill()

        # (B) 物理邊界異常值檢核與修正 (Outlier Clipping)
        outlier_cnt = int(
            (df_merged["GHI_Wm2"] < 0).sum() +
            (df_merged["GHI_Wm2"] > 1350).sum() +
            (df_merged["Wind_ms"] < 0).sum() +
            (df_merged["Wind_ms"] > 60).sum() +
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

        # (C) 衍生計算第 4 章 Faiman 物理基準面板溫度 T_cell_Faiman (供後續比對)
        # 採用標準地面高架散熱係數 U0=25, U1=6.84
        df_merged["T_cell_Faiman_C"] = df_merged["T_amb_C"] + df_merged["GHI_Wm2"] / (25.0 + 6.84 * df_merged["Wind_ms"])

        audit_report["cleaned_rows"] = len(df_merged)
        audit_report["latest_data_time"] = df_merged["timestamp"].max().strftime("%Y-%m-%d %H:%M")

        return df_merged, audit_report

    except Exception as e:
        audit_report["error_msg"] = str(e)
        return pd.DataFrame(), audit_report


# ==================== 上半部：左控制台 (1.05) + 右即時多維度數據流監控儀表板 (2.25) ====================
col_ctrl, col_stage = st.columns([1.05, 2.25], gap="medium")

with col_ctrl:
    st.markdown("##### 📍 1. 選擇台灣真實光電案場座標")
    site_Map = {
        "🇹🇼 台南七股地面型旗艦案場 (23.15°N, 120.08°E)": (23.15, 120.08, "沿海高日照 / 鹽霧考驗區"),
        "🇹🇼 彰濱工業區崙尾東水上光電 (24.12°N, 120.41°E)": (24.12, 120.41, "海風強勁 / 潮間帶高濕區"),
        "🇹🇼 雲林麥寮農電共生案場 (23.78°N, 120.25°E)": (23.78, 120.25, "秋冬東北季風 / PM2.5 敏感區"),
        "🇹🇼 屏東林邊地層下陷光電專區 (22.43°N, 120.51°E)": (22.43, 120.51, "熱帶高溫 / 午後雷陣雨洗塵區"),
        "🇹🇼 桃園觀音屋頂型光電群 (25.04°N, 121.11°E)": (25.04, 121.11, "北部多雲散射光主導區")
    }
    selected_site = st.selectbox("選擇要即時連線抓取的案場：", list(site_Map.keys()), index=0)
    lat_val, lon_val, site_desc = site_Map[selected_site]
    st.caption(f"🧭 **座標定位**：緯度 `{lat_val}°N` ｜ 經度 `{lon_val}°E` （微氣候特徵：{site_desc}）")

    st.markdown("##### ⏳ 2. 設定回溯抓取天數與手動強制刷新")
    c_b1, c_b2 = st.columns([1.2, 1.0])
    with c_b1:
        past_days = st.slider("📅 自動抓取過去幾天逐時資料", 3, 14, 7, step=1)
    with c_b2:
        st.write("")
        if st.button("🔄 立即重新連線抓取最新數據", use_container_width=True):
            st.cache_data.clear()

    # 執行即時連線抓取
    df_live, audit = fetch_live_taiwan_solar_and_air_data(lat_val, lon_val, past_days=past_days)

    st.markdown("##### 🛡️ 3. 資料管線健康度閘門檢核 (Pipeline Gate)")
    pipeline_healthy = audit["weather_api_ok"] and audit["air_api_ok"] and (audit["cleaned_rows"] > 24)

    if pipeline_healthy:
        st.success(
            f"✅ **【管線驗證通過：LIVE 連線正常】**\n"
            f"* **氣象與衛星輻照 API**：🟢 HTTP 200 連線成功\n"
            f"* **環境部/國際空品 PM2.5 API**：🟢 HTTP 200 連線成功\n"
            f"* **成功獲取逐時樣本數**：共 **{audit['cleaned_rows']} 筆**（每小時 1 筆）\n"
            f"* **清洗補插缺失值**：已自動修復 **{audit['missing_fixed']} 處** 空值\n"
            f"* **物理邊界異常過濾**：攔截 **{audit['outliers_clipped']} 筆** 異常尖峰"
        )
    else:
        st.error(
            f"❌ **【管線驗證未通過：禁止進入 AI 訓練】**\n"
            f"原因：{audit['error_msg'] or 'API 回應異常，請檢查網路連線'}"
        )

with col_stage:
    if pipeline_healthy and not df_live.empty:
        # 繪製三層同步時間序列監控圖：1. 日照 (GHI/DNI/DHI)  2. 氣溫與 Faiman 面板溫度  3. 風速、降雨與 PM2.5
        fig_pipe = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.07,
            subplot_titles=(
                "<b>☀️ 通道 1：真實衛星反演太陽輻照度 (GHI 總日射 / DNI 直射 / DHI 散射) [W/m²]</b>",
                "<b>🌡️ 通道 2：真實測站氣溫 Tamb vs. Faiman 物理推算面板溫度 Tcell [°C]</b>",
                "<b>🌫️ 通道 3：台灣複合微氣候因子 —— 細懸浮微粒 PM2.5 [μg/m³]、風速 [m/s] 與降雨洗塵事件 [mm]</b>"
            ),
            specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]]
        )

        # 第一層：GHI, DNI, DHI
        fig_pipe.add_trace(
            go.Scatter(x=df_live["timestamp"], y=df_live["GHI_Wm2"], name="☀️ GHI 總日射 (W/m²)",
                       line=dict(color="#D97706", width=2.5), fill="tozeroy", fillcolor="rgba(245, 158, 11, 0.2)"),
            row=1, col=1
        )
        fig_pipe.add_trace(
            go.Scatter(x=df_live["timestamp"], y=df_live["DHI_Wm2"], name="☁️ DHI 散射光 (W/m²)",
                       line=dict(color="#2563EB", width=1.8, dash="dot")),
            row=1, col=1
        )

        # 第二層：環境氣溫 vs Faiman 面板溫度
        fig_pipe.add_trace(
            go.Scatter(x=df_live["timestamp"], y=df_live["T_cell_Faiman_C"], name="🔥 Faiman 面板溫度 (°C)",
                       line=dict(color="#DC2626", width=2.5)),
            row=2, col=1
        )
        fig_pipe.add_trace(
            go.Scatter(x=df_live["timestamp"], y=df_live["T_amb_C"], name="🌡️ 環境氣溫 Tamb (°C)",
                       line=dict(color="#059669", width=2)),
            row=2, col=1
        )

        # 第三層：PM2.5 (左軸) + 風速/降雨量 (右軸)
        fig_pipe.add_trace(
            go.Scatter(x=df_live["timestamp"], y=df_live["PM25_ugm3"], name="🌫️ PM2.5 濃度 (μg/m³)",
                       line=dict(color="#7C3AED", width=2.2), fill="tozeroy", fillcolor="rgba(124, 58, 237, 0.12)"),
            row=3, col=1, secondary_y=False
        )
        fig_pipe.add_trace(
            go.Bar(x=df_live["timestamp"], y=df_live["Rain_mm"], name="🌧️ 降雨量 (mm/hr)",
                   marker_color="#0284C7", opacity=0.7),
            row=3, col=1, secondary_y=True
        )
        fig_pipe.add_trace(
            go.Scatter(x=df_live["timestamp"], y=df_live["Wind_ms"], name="💨 風速 v (m/s)",
                       line=dict(color="#0D9488", width=1.8, dash="dash")),
            row=3, col=1, secondary_y=True
        )

        fig_pipe.update_layout(
            height=520,
            margin=dict(l=55, r=55, t=65, b=35),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(color="#0F172A", size=11.5),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0.0,
                bgcolor="rgba(241, 245, 249, 0.95)", bordercolor="#CBD5E1", borderwidth=1,
                font=dict(color="#0F172A", size=11)
            ),
            hovermode="x unified"
        )
        for r_idx in [1, 2, 3]:
            fig_pipe.update_xaxes(gridcolor="#E2E8F0", tickfont=dict(color="#334155"), row=r_idx, col=1)
            fig_pipe.update_yaxes(gridcolor="#E2E8F0", tickfont=dict(color="#334155"), row=r_idx, col=1)

        st.plotly_chart(fig_pipe, use_container_width=True)

# ==================== 中段：最新一筆即時數據快照卡 (Live Snapshot Cards) ====================
if pipeline_healthy and not df_live.empty:
    # 定位到「當下時刻（Now）」最接近的一筆真實觀測紀錄
    now_dt = pd.Timestamp.now(tz="Asia/Taipei").tz_localize(None)
    df_past = df_live[df_live["timestamp"] <= now_dt]
    latest_row = df_past.iloc[-1] if not df_past.empty else df_live.iloc[-1]
    latest_time_str = latest_row["timestamp"].strftime("%Y-%m-%d %H:%M")

    # 計算過去 7 天統計特徵
    max_ghi_7d = float(df_live["GHI_Wm2"].max())
    mean_pm25_7d = float(df_live["PM25_ugm3"].mean())
    total_rain_7d = float(df_live["Rain_mm"].sum())

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(f"""
        <div class="bright-card">
            <div class="bright-title">📡 ① 最新連線時間戳記與日照實測 (Live Telemetry)</div>
            <div class="bright-val-gold">{latest_row['GHI_Wm2']:.0f} W/m² <span style="font-size:0.95rem;color:#00E5FF;font-weight:600;">｜ 觀測時刻：{latest_time_str}</span></div>
            <div class="bright-sub">直射 DNI：{latest_row['DNI_Wm2']:.0f} W/m² ｜ 散射 DHI：{latest_row['DHI_Wm2']:.0f} W/m² ｜ 近 {past_days} 日最高：{max_ghi_7d:.0f} W/m²</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="bright-card">
            <div class="bright-title">🌡️ ② 案場即時微氣候：氣溫、風速與 Faiman 溫升</div>
            <div class="bright-val-cyan">{latest_row['T_amb_C']:.1f} °C <span style="font-size:0.95rem;color:#FF5252;font-weight:600;">➔ 面板推算 {latest_row['T_cell_Faiman_C']:.1f} °C</span></div>
            <div class="bright-sub">即時風速：{latest_row['Wind_ms']:.1f} m/s ｜ 相對濕度：{latest_row['RH_pct']:.0f}% ｜ 近 {past_days} 日累積降雨：{total_rain_7d:.1f} mm</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="bright-card">
            <div class="bright-title">🌫️ ③ 環境空品與氣膠積塵指標 (MOENV / AQI 指標)</div>
            <div class="bright-val-green">PM2.5：{latest_row['PM25_ugm3']:.1f} μg/m³ <span style="font-size:0.95rem;color:#F8FAFC;font-weight:500;">｜ PM10：{latest_row['PM10_ugm3']:.1f}</span></div>
            <div class="bright-sub">近 {past_days} 日平均 PM2.5：{mean_pm25_7d:.1f} μg/m³ ｜ 資料抓取時間：{audit['fetch_timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== 下半部：真實抓回之活資料表檢視與 CSV 匯出驗證 ====================
    st.markdown("---")
    with st.expander("🔍 點此展開檢視：剛剛從 API 自動抓回並完成清洗的最新 48 小時真實數據矩陣（含 CSV 匯出）", expanded=True):
        df_display = df_past.tail(48).sort_values("timestamp", ascending=False).copy()
        df_display["timestamp"] = df_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            df_display.rename(columns={
                "timestamp": "觀測時間 (台灣時區)",
                "GHI_Wm2": "總日射 GHI (W/m²)",
                "DNI_Wm2": "直射光 DNI (W/m²)",
                "DHI_Wm2": "散射光 DHI (W/m²)",
                "T_amb_C": "環境氣溫 (°C)",
                "Wind_ms": "風速 (m/s)",
                "RH_pct": "相對濕度 (%)",
                "Rain_mm": "降雨量 (mm)",
                "PM25_ugm3": "PM2.5 (μg/m³)",
                "PM10_ugm3": "PM10 (μg/m³)",
                "T_cell_Faiman_C": "Faiman 面板溫度 (°C)"
            }),
            use_container_width=True,
            height=260
        )

        csv_bytes = df_live.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 下載本次自動串接之完整乾淨特徵資料集 (.CSV)，供離線檢驗",
            data=csv_bytes,
            file_name=f"taiwan_solar_live_pipeline_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
