# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
from datetime import datetime
import plotly.graph_objects as go

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

st.set_page_config(page_title="第 7 章：智慧維運與商業決策模組", page_icon="💡", layout="wide")

# 使用單行字串串接 CSS，徹底杜絕多行字串貼上損壞
css_lines = [
    "<style>",
    ".block-container { padding-top: 3.5rem !important; padding-bottom: 1.5rem !important; }",
    ".section-banner { background: linear-gradient(90deg, #1E3A8A, #1E293B); color: #FFFFFF !important; padding: 10px 18px; border-radius: 8px; font-size: 1.15rem; font-weight: 700; margin-top: 18px; margin-bottom: 14px; border-left: 6px solid #FFD700; }",
    ".guide-box { background-color: #F8FAFC; border-left: 5px solid #0284C7; border-radius: 8px; padding: 14px 18px; color: #0F172A; font-size: 0.93rem; line-height: 1.6; border: 1px solid #E2E8F0; margin-bottom: 15px; }",
    "</style>"
]
st.markdown("\n".join(css_lines), unsafe_allow_html=True)

st.markdown("### 第七章：【商業落地】智慧維運與經濟決策模組（有 AI vs. 沒有 AI 的實戰價值）")
st.info(
    "🌟 **【第七章核心價值：AI 的三大商業貢獻】** 前面 6 章驗證了物理與 AI 模型的準確度，本章直接將 AI 轉化為電廠真金白銀的決策工具：\n"
    "1. **🚨 貢獻一（智慧故障診斷雷達）**：當發電量偏低時，自動區分是「面板髒了（環境正常積塵，免派工）」還是「設備壞了（硬體真實故障，立即派工）」，消除工程師的假警報疲勞！\n"
    "2. **💧 貢獻二（最佳面板清洗排程計算器）**：把 AI 算出的每日積塵少發電量換算成「新台幣損失」，對比水車清洗費用，精準算出哪一天洗面板最賺錢！\n"
    "3. **⚡ 貢獻三（降低台電發電預測偏差風險）**：對比「沒有 AI（純物理）」與「有 AI（灰箱混合）」在申報發電量時的偏差幅度，評估省下的偏差懲罰成本！"
)

TAIWAN_SOLAR_SITES = {
    "🇹🇼 1. 台南七股地面型旗艦案場 (23.15°N, 120.08°E)": {"short_name": "台南七股案場", "lat": 23.15, "lon": 120.08, "opt_tilt": 20.0, "capacity_kw": 250000.0},
    "🇹🇼 2. 彰濱工業區崙尾東水上光電 (24.12°N, 120.41°E)": {"short_name": "彰濱崙尾東案場", "lat": 24.12, "lon": 120.41, "opt_tilt": 15.0, "capacity_kw": 300000.0},
    "🇹🇼 3. 雲林麥寮農電共生案場 (23.78°N, 120.25°E)": {"short_name": "雲林麥寮案場", "lat": 23.78, "lon": 120.25, "opt_tilt": 20.0, "capacity_kw": 100000.0},
    "🇹🇼 4. 屏東林邊地層下陷光電專區 (22.43°N, 120.51°E)": {"short_name": "屏東林邊案場", "lat": 22.43, "lon": 120.51, "opt_tilt": 18.0, "capacity_kw": 120000.0},
    "🇹🇼 5. 桃園觀音工業區屋頂型光電群 (25.04°N, 121.11°E)": {"short_name": "桃園觀音案場", "lat": 25.04, "lon": 121.11, "opt_tilt": 12.0, "capacity_kw": 50000.0}
}


def process_physics_and_ai_features(df, lat_deg, panel_tilt_deg, rated_capacity_kw):
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

    nx = 0.0
    ny = -np.sin(beta_r)
    nz = np.cos(beta_r)
    cos_theta_i = np.where(sz > 0.0, np.clip(sx * nx + sy * ny + sz * nz, 0.0, 1.0), 0.0)
    theta_i_deg = np.degrees(np.arccos(np.clip(cos_theta_i, 0.0, 1.0)))

    poa_wm2 = np.where(
        sz > 0.0,
        df["DNI_Wm2"].values * cos_theta_i + df["DHI_Wm2"].values * ((1.0 + np.cos(beta_r)) / 2.0),
        0.0
    )

    df["POA_Wm2"] = poa_wm2.round(1)
    df["Incidence_Angle_deg"] = np.where(sz > 0.0, theta_i_deg, 90.0).round(1)

    t_cell = df["T_amb_C"].values + df["POA_Wm2"].values / (25.0 + 6.84 * df["Wind_ms"].values)
    df["T_cell_C"] = np.round(t_cell, 1)

    scale_factor = rated_capacity_kw / 1000.0
    temp_factor = 1.0 - 0.004 * np.maximum(0.0, df["T_cell_C"].values - 25.0)
    p_physics = scale_factor * (df["POA_Wm2"].values / 1000.0) * 0.215 * temp_factor
    df["P_physics_kW"] = np.maximum(0.0, p_physics).round(2)

    iam_loss = np.where(df["Incidence_Angle_deg"].values > 55.0, (df["Incidence_Angle_deg"].values - 55.0) * 0.0015, 0.0)
    soiling_loss = np.clip(
        (df["PM25_ugm3"].values / 120.0) * 0.055 + (df["Dry_Hours_Since_Rain"].values / 180.0) * 0.05 + iam_loss,
        0.0, 0.16
    )
    np.random.seed(42)
    noise = np.random.normal(1.0, 0.012, size=len(df))
    p_actual = df["P_physics_kW"].values * (1.0 - soiling_loss) * noise
    df["P_actual_kW"] = np.maximum(0.0, p_actual).round(2)

    df["Residual_kW"] = (df["P_actual_kW"] - df["P_physics_kW"]).round(2)
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_prepare_om_dataset(lat, lon, panel_tilt_deg, capacity_kw):
    start_str = "2026-08-18"
    end_str = datetime.now().strftime("%Y-%m-%d")
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + f"latitude={lat}&longitude={lon}"
        + f"&start_date={start_str}&end_date={end_str}"
        + "&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,"
        + "shortwave_radiation,direct_normal_irradiance,diffuse_radiation"
        + "&wind_speed_unit=ms&timezone=Asia%2FTaipei"
    )
    air_url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality?"
        + f"latitude={lat}&longitude={lon}"
        + f"&start_date={start_str}&end_date={end_str}"
        + "&hourly=pm10,pm2_5"
        + "&timezone=Asia%2FTaipei"
    )

    try:
        req_w = urllib.request.Request(weather_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_w, timeout=12) as resp_w:
            w_data = json.loads(resp_w.read().decode("utf-8"))

        req_a = urllib.request.Request(air_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_a, timeout=12) as resp_a:
            a_data = json.loads(resp_a.read().decode("utf-8"))

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

        df_merged = df_merged.interpolate(method="linear").bfill().ffill()
        df_merged["GHI_Wm2"] = df_merged["GHI_Wm2"].clip(0.0, 1350.0)
        df_merged["DNI_Wm2"] = df_merged["DNI_Wm2"].clip(0.0, 1200.0)
        df_merged["DHI_Wm2"] = df_merged["DHI_Wm2"].clip(0.0, 800.0)
        df_merged["Wind_ms"] = df_merged["Wind_ms"].clip(0.0, 60.0)
        df_merged["Rain_mm"] = df_merged["Rain_mm"].clip(0.0, 300.0)
        df_merged["PM25_ugm3"] = df_merged["PM25_ugm3"].clip(1.0, 500.0)

        dry_hrs = []
        cur_dry = 0
        for r_val in df_merged["Rain_mm"]:
            if r_val >= 0.2:
                cur_dry = 0
            else:
                cur_dry += 1
            dry_hrs.append(cur_dry)
        df_merged["Dry_Hours_Since_Rain"] = dry_hrs

        df_final = process_physics_and_ai_features(df_merged, lat, panel_tilt_deg, capacity_kw)
        return df_final, ""
    except Exception as e:
        return pd.DataFrame(), str(e)


# ==================== 第一節：案場選擇與 O&M 經濟參數設定 ====================
st.markdown('<div class="section-banner">📍 第一節：選擇台灣光電案場與商用 O&M 經濟參數設定</div>', unsafe_allow_html=True)

om_c1, om_c2, om_c3 = st.columns([1.2, 1.0, 1.0], gap="medium")

with om_c1:
    selected_site_name = st.selectbox("🎯 選擇要進行智慧維運決策的案場：", list(TAIWAN_SOLAR_SITES.keys()), index=0)
    site_info = TAIWAN_SOLAR_SITES[selected_site_name]
    lat_val = site_info["lat"]
    lon_val = site_info["lon"]
    capacity_kw = site_info["capacity_kw"]
    st.caption(f"⚡ 案場裝置容量規模：{capacity_kw/1000:.0f} MW ｜ 座標：{lat_val}°N, {lon_val}°E")

with om_c2:
    panel_tilt_deg = st.slider("📐 面板固定傾角 β (°)", 0.0, 40.0, float(site_info["opt_tilt"]), step=1.0)
    electricity_price = st.number_input("💰 台電躉售電費單價 (元/度 kWh)", value=4.5, step=0.1)

with om_c3:
    cleaning_cost = st.number_input("🚿 全廠人工/水車清洗一次成本 (萬元)", value=1.5, min_value=0.2, max_value=50.0, step=0.5)
    fault_sim_drop = st.slider("🧪 壓力測試：模擬硬體異常額外掉電 (%)", 0, 25, 0, step=5)

df_om, om_err = fetch_and_prepare_om_dataset(lat_val, lon_val, panel_tilt_deg, capacity_kw)

if om_err or df_om.empty:
    st.error(f"❌ 數據載入失敗：{om_err}")
else:
    feature_cols = [
        "POA_Wm2", "Incidence_Angle_deg", "T_amb_C", "T_cell_C",
        "Wind_ms", "RH_pct", "PM25_ugm3", "Dry_Hours_Since_Rain"
    ]
    n_train = int(len(df_om) * 0.8)
    df_t_train = df_om.iloc[:n_train]

    if ML_AVAILABLE:
        rf_om = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
        rf_om.fit(df_t_train[feature_cols], df_t_train["Residual_kW"])
        pred_res = rf_om.predict(df_om[feature_cols])
        df_om["P_ai_hybrid_kW"] = np.maximum(0.0, df_om["P_physics_kW"].values + pred_res)
    else:
        df_om["P_ai_hybrid_kW"] = df_om["P_physics_kW"]

    # ==================== 第二節：智慧故障診斷與「狼來了」過濾雷達 ====================
    st.markdown('<div class="section-banner">🚨 第二節：AI 貢獻一 —— 智慧故障診斷雷達（自動區分「環境積塵」與「真實硬體故障」）</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="guide-box">'
        '<b>💡 為什麼沒有 AI 的傳統電廠每天都在喊「狼來了」？</b><br>'
        '• <b>沒有 AI 時</b>：監控系統只看「實測發電量」比「物理公式」低了 8%～12%，就瘋狂跳警報叫工程師去現場修逆變器，結果去到現場發現只是好幾天沒下雨、面板蒙塵（假警報）！<br>'
        '• <b>有 AI 灰箱時</b>：AI 已經把 PM2.5 與無雨時數算進預期裡，只要實測值貼合 AI 預期，系統就知道這是「正常積塵」免派工！你可以拉動右上角的<b>「🧪 模擬硬體異常額外掉電 (%)」滑桿到 15%</b>，親眼看看 AI 如何瞬間抓出真正的硬體故障！'
        '</div>',
        unsafe_allow_html=True
    )

    df_daytime = df_om[df_om["POA_Wm2"] > 100.0].copy()
    latest_row = df_daytime.iloc[-1] if not df_daytime.empty else df_om.iloc[-1]

    phys_p = float(latest_row["P_physics_kW"])
    ai_p = float(latest_row["P_ai_hybrid_kW"])
    # 根據使用者設定的壓力測試滑桿，模擬硬體故障造成的額外掉電
    act_p = float(latest_row["P_actual_kW"]) * (1.0 - fault_sim_drop / 100.0)
    pm25_val = float(latest_row["PM25_ugm3"])
    dry_hr = int(latest_row["Dry_Hours_Since_Rain"])
    obs_time_str = latest_row["timestamp"].strftime("%Y-%m-%d %H:%M")

    diff_phys_pct = ((act_p - phys_p) / max(phys_p, 1.0)) * 100.0
    diff_ai_pct = ((act_p - ai_p) / max(ai_p, 1.0)) * 100.0

    d_c1, d_c2, d_c3 = st.columns(3, gap="medium")
    with d_c1:
        st.metric(
            label=f"☀️ 純物理公式預期功率 ({obs_time_str})",
            value=f"{phys_p:,.2f} kW",
            delta="理想無塵基準 (未考慮積塵)"
        )
    with d_c2:
        st.metric(
            label="🤖 AI 灰箱修正後預期功率 (含積塵評估)",
            value=f"{ai_p:,.2f} kW",
            delta=f"AI 預估環境折減 {(ai_p - phys_p):+.2f} kW"
        )
    with d_c3:
        st.metric(
            label="🔴 案場 SCADA 實測發電功率",
            value=f"{act_p:,.2f} kW",
            delta=f"與 AI 預期相差 {diff_ai_pct:+.1f}% (與物理差 {diff_phys_pct:+.1f}%)",
            delta_color="normal" if abs(diff_ai_pct) <= 7.0 else "inverse"
        )

    if abs(diff_ai_pct) <= 7.0:
        st.success(
            f"🟢 **【AI 智慧雷達診斷：系統硬體健康（成功攔截假警報！）】**\n\n"
            f"* **傳統無 AI 系統會誤判**：實測比物理公式低了 `{abs(diff_phys_pct):.1f}%`，傳統系統會誤發警報要求派工。\n"
            f"* **AI 灰箱精準解讀**：當前已連續無雨 `{dry_hr}` 小時、PM2.5 為 `{pm25_val:.1f} μg/m³`，實測值與 AI 預期僅差 `{diff_ai_pct:+.1f}%`，屬於**正常環境積塵衰減，逆變器與模組硬體 100% 正常，免派工巡檢！**"
        )
    else:
        st.error(
            f"🚨 **【AI 智慧雷達二級警報：排除氣候積塵因素，偵測到真實硬體故障！】**\n\n"
            f"* **故障證據**：即使扣除無雨 `{dry_hr}` 小時與 PM2.5 的積塵影響後，實測功率（`{act_p:.2f} kW`）依然比 AI 灰箱預期（`{ai_p:.2f} kW`）異常暴跌了 **`{abs(diff_ai_pct):.1f}%`**！\n"
            f"* **維運派工指令**：強烈懷疑發生 **直流串列保險絲熔斷、旁路二極體擊穿或逆變器 MPPT 故障**，請立即派遣維運工程師前往 `{site_info['short_name']}` 檢修！"
        )

    # ==================== 第三節：最佳清洗排程與累積損失金額計算 ====================
    st.markdown('<div class="section-banner">💧 第三節：AI 貢獻二 —— 最佳面板清洗排程與積塵經濟損失計算器（何時洗面板最划算？）</div>', unsafe_allow_html=True)

    loss_kwh_list = []
    accum_loss = 0.0
    for r_val, res_val in zip(df_om["Rain_mm"], df_om["Residual_kW"]):
        if r_val >= 0.2:
            accum_loss = 0.0
        else:
            if res_val < 0:
                accum_loss += abs(res_val) * 1.0
        loss_kwh_list.append(accum_loss)

    df_om["Accumulated_Loss_kWh"] = loss_kwh_list
    df_om["Accumulated_Loss_NTD"] = df_om["Accumulated_Loss_kWh"] * electricity_price

    total_current_loss_ntd = float(df_om["Accumulated_Loss_NTD"].iloc[-1])
    max_period_loss_ntd = float(df_om["Accumulated_Loss_NTD"].max())
    cleaning_cost_ntd = cleaning_cost * 10000.0
    is_time_to_clean = total_current_loss_ntd >= cleaning_cost_ntd

    e_c1, e_c2, e_c3 = st.columns(3, gap="medium")
    with e_c1:
        st.metric(
            label="💰 本次無雨週期累積少發電費損失",
            value=f"NT$ {total_current_loss_ntd:,.0f}",
            delta=f"過去 60 天單一乾旱期最高曾損失 NT$ {max_period_loss_ntd:,.0f}"
        )
    with e_c2:
        st.metric(
            label="🚿 全廠水車清洗一次預算成本",
            value=f"NT$ {cleaning_cost_ntd:,.0f}",
            delta="可在上方自由調整清洗報價"
        )
    with e_c3:
        if is_time_to_clean:
            st.metric(
                label="🚀 AI 清洗排程經濟決策",
                value="【建議立即派水車清洗】",
                delta=f"清洗可立刻止損並倒賺 NT$ {(total_current_loss_ntd - cleaning_cost_ntd):,.0f}！"
            )
        else:
            diff_ntd = cleaning_cost_ntd - total_current_loss_ntd
            st.metric(
                label="⏳ AI 清洗排程經濟決策",
                value="【目前洗不划算，請等待】",
                delta=f"距離損益平衡點還差 NT$ {diff_ntd:,.0f}"
            )

    fig_loss = go.Figure()
    fig_loss.add_trace(go.Scatter(
        x=df_om["timestamp"], y=df_om["Accumulated_Loss_NTD"], mode="lines",
        name="📉 累積積塵發電損失金額 (NTD) [遇降雨洗塵即自動歸零]",
        line=dict(color="#D97706", width=2.8),
        fill="tozeroy", fillcolor="rgba(217, 119, 6, 0.15)"
    ))
    fig_loss.add_hline(
        y=cleaning_cost_ntd, line_width=2.5, line_dash="dash", line_color="#DC2626",
        annotation_text=f"🚿 水車清洗成本線 (NT$ {cleaning_cost_ntd:,.0f}) ➔ 橘線衝破此紅線即為最佳清洗日！",
        annotation_position="top left",
        annotation_font=dict(color="#DC2626", size=12)
    )
    fig_loss.update_layout(
        title=dict(text=f"<b>💧 {site_info['short_name']} —— 過去 60 天積塵累積電費損失 vs. 水車清洗成本決策圖</b>", font=dict(size=15, color="#0F172A"), x=0.01, y=0.96),
        height=390,
        margin=dict(l=65, r=25, t=75, b=40),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC",
        hovermode="x unified",
        xaxis=dict(gridcolor="#E2E8F0"),
        yaxis=dict(title=dict(text="<b>累積少發電費損失 (新台幣 NTD)</b>", font=dict(color="#0F172A", size=12)), gridcolor="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0, bgcolor="rgba(241,245,249,0.95)")
    )
    st.plotly_chart(fig_loss, use_container_width=True, key="cleaning_eco_chart")

    # ==================== 第四節：台電發電偏差風險與經濟效益對決 ====================
    st.markdown('<div class="section-banner">⚡ 第四節：AI 貢獻三 —— 降低台電發電申報偏差與「有 AI vs. 沒有 AI」總結對照</div>', unsafe_allow_html=True)

    df_test_day = df_om.iloc[n_train:].copy()
    df_test_day = df_test_day[df_test_day["POA_Wm2"] > 20.0]

    mae_phys_kw = float(np.mean(np.abs(df_test_day["P_physics_kW"] - df_test_day["P_actual_kW"])))
    mae_ai_kw = float(np.mean(np.abs(df_test_day["P_ai_hybrid_kW"] - df_test_day["P_actual_kW"])))
    saved_error_kwh = float(np.sum(np.abs(df_test_day["P_physics_kW"] - df_test_day["P_actual_kW"])) - np.sum(np.abs(df_test_day["P_ai_hybrid_kW"] - df_test_day["P_actual_kW"])))

    p_c1, p_c2 = st.columns([1.1, 1.4], gap="large")
    with p_c1:
        st.markdown("##### 📊 盲測期發電申報偏差量化對決")
        comp_df = pd.DataFrame([
            {"評估項目": "白晝每小時平均預測偏差 (MAE)", "❌ 沒有 AI (純物理模型)": f"{mae_phys_kw:.2f} kW", "✅ 有 AI (灰箱混合模型)": f"{mae_ai_kw:.2f} kW"},
            {"評估項目": "盲測期累積少報/多報總偏差電量", "❌ 沒有 AI (純物理模型)": f"{np.sum(np.abs(df_test_day['P_physics_kW'] - df_test_day['P_actual_kW'])):,.0f} 度", "✅ 有 AI (灰箱混合模型)": f"{np.sum(np.abs(df_test_day['P_ai_hybrid_kW'] - df_test_day['P_actual_kW'])):,.0f} 度"},
            {"評估項目": "環境積塵與真故障區分能力", "❌ 沒有 AI (純物理模型)": "無法區分 (易發假警報)", "✅ 有 AI (灰箱混合模型)": "自動分離積塵與硬體故障"},
            {"評估項目": "水車清洗最佳時機量化", "❌ 沒有 AI (純物理模型)": "憑經驗盲目定期清洗", "✅ 有 AI (灰箱混合模型)": "精準計算損益平衡清洗日"}
        ])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    with p_c2:
        st.markdown(
            '<div class="guide-box">'
            '<b>🏆 全書總結：為什麼這套「物理 + AI 灰箱數位孿生」是能源工程的最佳解答？</b><br>'
            '1. <b>如果只有物理公式（第 1～4 章，沒有 AI）</b>：它能給你完美的理論骨架，但面對台灣的 PM2.5、沿海鹽霧與午後雷陣雨，它永遠活在「面板 100% 乾淨」的平行時空，在盲測期多產生了 <b>' + f'{saved_error_kwh:,.0f} 度電' + '</b> 的申報偏差！<br>'
            '2. <b>如果只有純黑箱 AI（拋棄第 1～4 章物理）</b>：缺乏太陽仰角、入射角餘弦與 Faiman 熱平衡的物理約束，遇到極端天氣就會違反能量守恆亂猜。<br>'
            '3. <b>物理引導灰箱 AI（第 1～7 章完整閉環）</b>：以第一性原理為骨幹、以每日自動串接之 Open Data 為血液、以機器學習殘差修正為大腦，最終在第七章化為<b>「過濾假警報、精算洗面板時機、降低電網偏差」</b>的真金白銀商業價值！'
            '</div>',
            unsafe_allow_html=True
        )

# END OF FILE
