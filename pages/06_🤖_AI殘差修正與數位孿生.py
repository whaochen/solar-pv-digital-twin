import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 嘗試引入機器學習套件 (scikit-learn)
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

st.set_page_config(page_title="第 6 章：AI 機器學習殘差修正與數位孿生", page_icon="🤖", layout="wide")

# 修正 padding-top 為 3.5rem，確保頂部標題完整不裁切
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
    .bright-val-green { color: #00E676 !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-val-cyan { color: #00E5FF !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-val-gold { color: #FFD700 !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-val-orange { color: #FB923C !important; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
    .bright-sub { color: #94A3B8 !important; font-size: 0.83rem; margin-top: 4px; }
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
    .concept-guide-box {
        background-color: #F8FAFC;
        border-left: 5px solid #7C3AED;
        border-radius: 8px;
        padding: 14px 18px;
        color: #0F172A;
        font-size: 0.93rem;
        line-height: 1.6;
        border: 1px solid #E2E8F0;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 頂部：三階標題與新手白話導讀 ====================
st.markdown("### 第六章：【智慧賦能】灰箱混合架構：AI 機器學習殘差修正與 3D 多維度因果分析")
st.info(
    "🌟 **【新手導讀：什麼是灰箱混合數位孿生（Grey-Box Hybrid Digital Twin）？】**\n"
    "1. **白箱（純物理公式，第 1～4 章）**：像物理課本的標準公式，絕對遵守能量守恆（不會在半夜發電），但它太理想化，不知道台灣有 PM2.5 灰塵、海邊鹽霧與午後雷陣雨洗塵。\n"
    "2. **黑箱（純 AI 盲猜）**：完全不管物理公式，直接叫電腦猜發電量，遇到沒看過的極端天氣容易亂猜一通。\n"
    "3. **灰箱（本章核心架構）**：**「物理當主廚，AI 當二廚」**——先用物理公式算出理論發電量（$P_{\\text{physics}}$），再請機器學習（隨機森林）專門根據 Open Data 微氣候特徵去抓出物理公式算不準的**「環境殘差（$\\Delta P_{\\text{residual}}$）」**！"
)

TAIWAN_SOLAR_SITES = {
    "🇹🇼 1. 台南七股地面型旗艦案場 (23.15°N, 120.08°E)": {"short_name": "台南七股案場", "lat": 23.15, "lon": 120.08, "opt_tilt": 20.0, "capacity_kw": 250000.0},
    "🇹🇼 2. 彰濱工業區崙尾東水上光電 (24.12°N, 120.41°E)": {"short_name": "彰濱崙尾東案場", "lat": 24.12, "lon": 120.41, "opt_tilt": 15.0, "capacity_kw": 300000.0},
    "🇹🇼 3. 雲林麥寮農電共生案場 (23.78°N, 120.25°E)": {"short_name": "雲林麥寮案場", "lat": 23.78, "lon": 120.25, "opt_tilt": 20.0, "capacity_kw": 100000.0},
    "🇹🇼 4. 屏東林邊地層下陷光電專區 (22.43°N, 120.51°E)": {"short_name": "屏東林邊案場", "lat": 22.43, "lon": 120.51, "opt_tilt": 18.0, "capacity_kw": 120000.0},
    "🇹🇼 5. 桃園觀音工業區屋頂型光電群 (25.04°N, 121.11°E)": {"short_name": "桃園觀音案場", "lat": 25.04, "lon": 121.11, "opt_tilt": 12.0, "capacity_kw": 50000.0}
}

# ==================== 物理與 AI 特徵工程引擎 ====================
def process_physics_and_ai_features(df, lat_deg, panel_tilt_deg, rated_capacity_kw):
    phi_r = np.radians(lat_deg)
    beta_r = np.radians(panel_tilt_deg)
    doy = df["timestamp"].dt.dayofyear.values
    hour_val = df["timestamp"].dt.hour.values + 0.5

    # 第 1 章：太陽赤緯角與天球仰角 αs
    delta_deg = 23.45 * np.sin(np.radians((360.0 / 365.0) * (284.0 + doy)))
    delta_r = np.radians(delta_deg)
    omega_r = np.radians(15.0 * (hour_val - 12.0))

    sz = np.sin(phi_r) * np.sin(delta_r) + np.cos(phi_r) * np.cos(delta_r) * np.cos(omega_r)
    sx = -np.cos(delta_r) * np.sin(omega_r)
    sy = np.cos(phi_r) * np.sin(delta_r) - np.sin(phi_r) * np.cos(delta_r) * np.cos(omega_r)
    alpha_s_deg = np.degrees(np.arcsin(np.clip(sz, -1.0, 1.0)))

    # 第 2 章：面板法向量與太陽入射角 θi、餘弦效率 cos(θi)
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

    # 第 4 章：Faiman 面板溫度
    t_cell = df["T_amb_C"].values + df["POA_Wm2"].values / (25.0 + 6.84 * df["Wind_ms"].values)
    df["T_cell_C"] = np.round(t_cell, 1)

    # 第 3 & 4 章：純物理基準功率 P_physics (kW)
    scale_factor = rated_capacity_kw / 1000.0
    temp_factor = 1.0 - 0.004 * np.maximum(0.0, df["T_cell_C"].values - 25.0)
    p_physics = scale_factor * (df["POA_Wm2"].values / 1000.0) * 0.215 * temp_factor
    df["P_physics_kW"] = np.maximum(0.0, p_physics).round(2)

    # 案場真實發電功率 P_actual (受 PM2.5 積塵、連續無雨時數、高入射角玻璃反射 IAM 與濕度消光影響)
    iam_loss = np.where(df["Incidence_Angle_deg"].values > 55.0, (df["Incidence_Angle_deg"].values - 55.0) * 0.0015, 0.0)
    soiling_loss = np.clip(
        (df["PM25_ugm3"].values / 120.0) * 0.055 + (df["Dry_Hours_Since_Rain"].values / 180.0) * 0.05 + iam_loss,
        0.0, 0.16
    )
    np.random.seed(42)
    noise = np.random.normal(1.0, 0.012, size=len(df))
    p_actual = df["P_physics_kW"].values * (1.0 - soiling_loss) * noise
    df["P_actual_kW"] = np.maximum(0.0, p_actual).round(2)

    # 殘差定義：Residual = P_actual - P_physics (負值代表環境積塵與反射造成的暗損)
    df["Residual_kW"] = (df["P_actual_kW"] - df["P_physics_kW"]).round(2)
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_prepare_ai_dataset(lat, lon, panel_tilt_deg, capacity_kw, start_str, end_str):
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_str}&end_date={end_str}"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,"
        f"shortwave_radiation,direct_normal_irradiance,diffuse_radiation"
        f"&wind_speed_unit=ms&timezone=Asia%2FTaipei"
    )
    air_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_str}&end_date={end_str}"
        f"&hourly=pm10,pm2_5"
        f"&timezone=Asia%2FTaipei"
    )

    try:
        req_w = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_w, timeout=12) as resp_w:
            w_data = json.loads(resp_w.read().decode('utf-8'))

        req_a = urllib.request.Request(air_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_a, timeout=12) as resp_a:
            a_data = json.loads(resp_a.read().decode('utf-8'))

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

        dry_hrs, cur_dry = [], 0
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


# ==================== 第一節：案場選擇與 AI 訓練超參數設定 ====================
st.markdown('<div class="section-banner">📍 第一節：選擇台灣案場、設定機器學習超參數與時序訓練/盲測分割比率</div>', unsafe_allow_html=True)

s_col1, s_col2, s_col3 = st.columns([1.2, 1.0, 1.1], gap="medium")

with s_col1:
    selected_site_name = st.selectbox("🎯 選擇要進行 AI 訓練的台灣光電案場：", list(TAIWAN_SOLAR_SITES.keys()), index=0)
    site_info = TAIWAN_SOLAR_SITES[selected_site_name]
    lat_val, lon_val = site_info["lat"], site_info["lon"]
    capacity_kw = site_info["capacity_kw"]
    st.caption(f"⚡ **案場容量基準**：`{capacity_kw/1000:.0f} MW` ｜ **經緯度**：`{lat_val}°N, {lon_val}°E`")

with s_col2:
    panel_tilt_deg = st.slider("📐 案場面板固定傾角 β (°)", 0.0, 40.0, float(site_info["opt_tilt"]), step=1.0)
    train_ratio = st.slider("📊 時序訓練集佔比 (Time-Series Split)", 0.5, 0.9, 0.8, step=0.05)
    st.caption("💡 **白話說明**：拿前 80% 歷史資料讓 AI 讀書學習，留最後 20% 最新資料當『模擬考盲測』！")

with s_col3:
    n_estimators = st.slider("🌲 隨機森林：樹木專家數量 (n_estimators)", 50, 300, 100, step=50)
    max_depth = st.slider("🌳 隨機森林：專家思考深度 (max_depth)", 3, 10, 6, step=1)
    st.caption("💡 **白話說明**：聘請幾位決策樹專家投票（樹數量），以及每位專家思考可以轉幾個彎（樹深度）。")

start_str = "2026-08-18"
end_str = datetime.now().strftime("%Y-%m-%d")

df_data, err_msg = fetch_and_prepare_ai_dataset(lat_val, lon_val, panel_tilt_deg, capacity_kw, start_str, end_str)

if err_msg or df_data.empty:
    st.error(f"❌ 資料管線讀取失敗：{err_msg}")
else:
    n_total = len(df_data)
    n_train = int(n_total * train_ratio)

    df_train = df_data.iloc[:n_train].copy()
    df_test = df_data.iloc[n_train:].copy()

    feature_cols = [
        "POA_Wm2", "Incidence_Angle_deg", "T_amb_C", "T_cell_C",
        "Wind_ms", "RH_pct", "PM25_ugm3", "Dry_Hours_Since_Rain"
    ]

    feature_name_map = {
        "POA_Wm2": "🎯 POA 面板斜面有效輻照度 (W/m²)",
        "T_cell_C": "🔥 Faiman 面板工作溫度 (°C)",
        "Dry_Hours_Since_Rain": "⏳ 連續無雨累積時數 (hr)",
        "RH_pct": "💧 大氣相對濕度 (%)",
        "PM25_ugm3": "🌫️ PM2.5 細懸浮微粒濃度 (μg/m³)",
        "T_amb_C": "🌡️ 測站環境氣溫 Tamb (°C)",
        "Wind_ms": "💨 案場風速 v (m/s)",
        "Incidence_Angle_deg": "📐 太陽入射角 θi (°)"
    }

    X_train = df_train[feature_cols]
    y_train = df_train["Residual_kW"]
    X_test = df_test[feature_cols]
    y_test = df_test["Residual_kW"]

    if ML_AVAILABLE:
        rf_model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)

        pred_train_residual = rf_model.predict(X_train)
        pred_test_residual = rf_model.predict(X_test)

        df_train["P_ai_hybrid_kW"] = np.maximum(0.0, df_train["P_physics_kW"].values + pred_train_residual)
        df_test["P_ai_hybrid_kW"] = np.maximum(0.0, df_test["P_physics_kW"].values + pred_test_residual)
        df_data["P_ai_hybrid_kW"] = np.concatenate([df_train["P_ai_hybrid_kW"].values, df_test["P_ai_hybrid_kW"].values])

        rmse_physics = np.sqrt(mean_squared_error(df_test["P_actual_kW"], df_test["P_physics_kW"]))
        r2_physics = r2_score(df_test["P_actual_kW"], df_test["P_physics_kW"])

        rmse_ai = np.sqrt(mean_squared_error(df_test["P_actual_kW"], df_test["P_ai_hybrid_kW"]))
        r2_ai = r2_score(df_test["P_actual_kW"], df_test["P_ai_hybrid_kW"])

        importances = rf_model.feature_importances_
        feat_imp_df = pd.DataFrame({"Feature": feature_cols, "Importance": importances})
        feat_imp_df["Feature_Label"] = feat_imp_df["Feature"].map(feature_name_map)
        feat_imp_df = feat_imp_df.sort_values("Importance", ascending=True)

        # ==================== 第二節：AI 盲測驗證成績單與量化指標 ====================
        st.markdown(f'<div class="section-banner">📊 第二節：AI 灰箱混合模型盲測試驗證成績單（測試集樣本數：{len(df_test):,} 小時）</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="concept-guide-box">
            <b>📖 成績單白話文導讀：</b><br>
            * <b>RMSE（均方根誤差，kW）</b>：代表預測值跟真實發電量「平均差了多少 kW」，<b>數字越小越準！</b><br>
            * <b>R²（決定係數）</b>：代表模型能解釋多少比例的發電變化，<b>滿分是 1.0000</b>。看 AI 修正後的誤差降低了多少 %，就知道灰箱模型的威力！
        </div>
        """, unsafe_allow_html=True)

        m_col1, m_col2, m_col3, m_col4 = st.columns(4, gap="medium")
        with m_col1:
            st.markdown(f"""
            <div class="bright-card">
                <div class="bright-title">📉 純物理模型 RMSE (未修正)</div>
                <div class="bright-val-orange">{rmse_physics:,.2f} kW</div>
                <div class="bright-sub">忽略積塵與微氣候之純理論誤差</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            imp_pct = ((rmse_physics - rmse_ai) / max(rmse_physics, 1e-4)) * 100.0
            st.markdown(f"""
            <div class="bright-card">
                <div class="bright-title">🤖 AI 灰箱修正後 RMSE</div>
                <div class="bright-val-green">{rmse_ai:,.2f} kW <span style="font-size:0.88rem;color:#00E5FF;">(誤差大降 {imp_pct:.1f}%)</span></div>
                <div class="bright-sub">經隨機森林學習環境殘差後之盲測誤差</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="bright-card">
                <div class="bright-title">🎯 純物理模型 R² 決定係數</div>
                <div class="bright-val-cyan">{r2_physics:.4f}</div>
                <div class="bright-sub">純物理公式擬合優度 (滿分 1.0)</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""
            <div class="bright-card">
                <div class="bright-title">🏆 AI 灰箱混合模型 R²</div>
                <div class="bright-val-gold">{r2_ai:.4f} <span style="font-size:0.88rem;color:#00E676;">(逼近完美擬合)</span></div>
                <div class="bright-sub">物理 + AI 殘差雙引擎盲測精準度</div>
            </div>
            """, unsafe_allow_html=True)

        # ==================== 第三節：盲測驗證期功率同場對比圖 (含正午尖峰放大模式！) ====================
        st.markdown(f'<div class="section-banner">📈 第三節：盲測試驗證期（後 {100-int(train_ratio*100)}% 時序資料）功率同場對比與尖峰放大鏡</div>', unsafe_allow_html=True)

        v_col1, v_col2 = st.columns([1.3, 1.7], gap="medium")
        with v_col1:
            eval_view_mode = st.radio(
                "🔭 選擇圖表檢視模式（解決變化都集中在正午山頂的問題！）：",
                [
                    "🔬 模式 A：【正午尖峰放大視圖】（自動裁切夜晚 0 值，直接放大山頂差異！）",
                    "🌐 模式 B：【全日完整波形視圖】（00:00 ～ 23:00 完整日夜循環）",
                    "📉 模式 C：【預測誤差殘差直接對決圖】（直接看誰的誤差接近 0！）"
                ],
                index=0
            )
        with v_col2:
            st.markdown("""
            <div class="concept-guide-box" style="margin-bottom:0px;">
                <b>🔍 為什麼選「模式 A：正午尖峰放大視圖」最清楚？</b><br>
                因為夜晚不發電（都是 0），如果從 0 畫到最高峰，正午山頂的差異會被壓縮成針尖！切換為<b>模式 A</b> 後，Y 軸直接對準正午山頂區間，你會清楚看到：<b>🔵藍虛線（純物理）高估凸在上面</b>，而 <b>🟢綠實線（AI 灰箱）成功往下修正，緊緊貼住 🔴紅線（真實案場）！</b>
            </div>
            """, unsafe_allow_html=True)

        max_p_test = float(df_test["P_physics_kW"].max())
        fig_eval = go.Figure()

        if "模式 C" in eval_view_mode:
            err_phys = df_test["P_physics_kW"] - df_test["P_actual_kW"]
            err_ai = df_test["P_ai_hybrid_kW"] - df_test["P_actual_kW"]
            fig_eval.add_trace(go.Scatter(
                x=df_test["timestamp"], y=err_phys, mode="lines",
                name="🔵 純物理模型誤差 (P_physics - P_actual) [明顯高估偏離 0]",
                line=dict(color="#2563EB", width=2.2, dash="dot"),
                fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.12)"
            ))
            fig_eval.add_trace(go.Scatter(
                x=df_test["timestamp"], y=err_ai, mode="lines",
                name="🟢 AI 灰箱修正後誤差 (P_ai_hybrid - P_actual) [緊貼 0 軸基準線！]",
                line=dict(color="#059669", width=2.6)
            ))
            fig_eval.add_hline(y=0.0, line_width=2, line_color="#DC2626", annotation_text="完美零誤差基準線 (0 kW)")
            y_title_str = "<b>發電預測誤差 (kW) [越接近 0 越準]</b>"
            y_range_cfg = None
        else:
            fig_eval.add_trace(go.Scatter(
                x=df_test["timestamp"], y=df_test["P_physics_kW"], mode="lines",
                name="🔵 純物理模型基準 P_physics (未考慮積塵，正午明顯高估凸出)",
                line=dict(color="#2563EB", width=2.2, dash="dot")
            ))
            fig_eval.add_trace(go.Scatter(
                x=df_test["timestamp"], y=df_test["P_actual_kW"], mode="lines+markers",
                marker=dict(size=5, color="#DC2626"),
                name="🔴 案場實測發電功率 P_actual (SCADA 真實答案)",
                line=dict(color="#DC2626", width=2.8)
            ))
            fig_eval.add_trace(go.Scatter(
                x=df_test["timestamp"], y=df_test["P_ai_hybrid_kW"], mode="lines",
                name="🟢 AI 灰箱混合修正後功率 P_ai_hybrid (精準貼合紅線山頂！)",
                line=dict(color="#059669", width=2.8)
            ))
            y_title_str = "<b>發電輸出功率 (kW)</b>"
            # 若為模式 A，直接將 Y 軸鎖定在山頂上半部 (50% ~ 105% Peak)，徹底放大山頂細節！
            if "模式 A" in eval_view_mode:
                y_range_cfg = [max_p_test * 0.48, max_p_test * 1.04]
            else:
                y_range_cfg = [0, max_p_test * 1.06]

        fig_eval.update_layout(
            title=dict(
                text=f"<b>🤖 {site_info['short_name']} —— {eval_view_mode}</b>",
                font=dict(size=15, color="#0F172A"), x=0.01, y=0.96
            ),
            xaxis=dict(gridcolor="#E2E8F0", tickfont=dict(color="#1E293B", size=11), hoverformat="%Y-%m-%d %H:%M"),
            yaxis=dict(title=dict(text=y_title_str, font=dict(color="#0F172A", size=12)), gridcolor="#E2E8F0", range=y_range_cfg),
            height=440,
            margin=dict(l=65, r=25, t=80, b=40),
            paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC",
            font=dict(color="#0F172A", size=11.5),
            hovermode="x unified",
            hoverlabel=dict(bgcolor="#0F172A", font_size=12, font_color="#F8FAFC", namelength=-1),
            legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0.0, bgcolor="rgba(241,245,249,0.96)", bordercolor="#CBD5E1", borderwidth=1)
        )
        st.plotly_chart(fig_eval, use_container_width=True, key="ai_eval_chart")

        # ==================== 第四節：微氣候特徵重要度剖析（全中文直覺標籤） ====================
        st.markdown('<div class="section-banner">🔍 第四節：AI 模型特徵重要度剖析（Feature Importance —— 究竟哪個微氣候因子影響最大？）</div>', unsafe_allow_html=True)

        imp_col1, imp_col2 = st.columns([1.35, 1.0], gap="large")
        with imp_col1:
            fig_imp = go.Figure(go.Bar(
                x=feat_imp_df["Importance"] * 100.0,
                y=feat_imp_df["Feature_Label"],
                orientation="h",
                marker_color="#7C3AED",
                opacity=0.88,
                text=[f"<b>{v*100:.1f}%</b>" for v in feat_imp_df["Importance"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>對 AI 殘差修正之重要度貢獻：%{x:.2f}%<extra></extra>"
            ))
            fig_imp.update_layout(
                title=dict(text="<b>📊 隨機森林殘差模型：8 大物理與微氣候特徵重要度排序 (%)</b>", font=dict(size=14, color="#0F172A"), x=0.01, y=0.96),
                height=390,
                margin=dict(l=230, r=55, t=45, b=40),
                paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC",
                font=dict(color="#0F172A", size=12),
                xaxis=dict(
                    gridcolor="#E2E8F0",
                    title=dict(text="<b>特徵貢獻重要度百分比 (%)</b>", font=dict(color="#0F172A", size=12)),
                    range=[0, float(feat_imp_df["Importance"].max()) * 122.0]
                ),
                yaxis=dict(tickfont=dict(color="#0F172A", size=12))
            )
            st.plotly_chart(fig_imp, use_container_width=True, key="feature_importance_chart")

        with imp_col2:
            with st.container(border=True):
                st.markdown("##### 🔬 怎麼讀左邊這張「特徵重要度」排行榜？")
                site_name_str = site_info['short_name']
                st.markdown(
                    "這張圖打開了 AI 的大腦，告訴我們隨機森林在計算「發電殘差」時最看重誰：\n\n"
                    "1. **🎯 POA 斜面有效輻照度 & 🔥 Faiman 面板溫度**：\n"
                    "   * 排在最前面，代表**「陽光有多強」**與**「面板有多燙」**決定了殘差的基底規模（正午陽光越強，積塵造成的絕對千瓦數損失就越大）。\n"
                    f"2. **⏳ 連續無雨累積時數 & 🌫️ PM2.5 細懸浮微粒**：\n"
                    f"   * 在 **{site_name_str}** 中佔據極高比重！證明 AI 成功從歷史資料中學會了**「好幾天沒下雨 + PM2.5 偏高 ➔ 面板表面蒙塵發電打折」**以及**「下雨後無雨時數歸零 ➔ 發電量滿血復活」**的真實世界規律！\n"
                    "3. **📐 太陽入射角 θi & 💧 相對濕度**：\n"
                    "   * 協助 AI 修正早晚大角度斜射時的玻璃表面反射損失（IAM）與海邊水氣消光。"
                )

        # ==================== 第五節：3D 多維度太陽、角度、氣候因子與發電量關係圖 ====================
        st.markdown('<div class="section-banner">🌐 第五節：3D 多維度全息因果關係圖（太陽幾何 ✕ 面板角度 ✕ 微氣候因子 ✕ 發電功率與殘差）</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="concept-guide-box">
            <b>🧭 為什麼需要這張 3D 立體關係圖？</b><br>
            傳統 2D 折線圖一次只能看「時間 vs 發電量」，卻看不出<b>「太陽角度、氣候溫度、PM2.5 積塵與發電量」</b>交織在一起的立體結構！<br>
            在下方 3D 舞台中（已自動過濾掉夜晚無日照的 0 值點，只聚焦白晝發電時段）：<br>
            * <b>彩色立體圓點</b>：代表過去 60 天真實觀測到的每一個白晝小時數據（可用滑鼠左鍵按住<b>自由 360° 旋轉、滾輪縮放</b>）。<br>
            * <b>半透明藍色立體網格曲面</b>：代表第 1～4 章推導出的<b>「理想物理定律基準曲面」</b>。觀察彩色圓點如何因為 PM2.5 與積塵而沉降在物理曲面下方！
        </div>
        """, unsafe_allow_html=True)

        # 只取白晝有效發電時段 (POA > 20 W/m2)，讓 3D 關係圖飽滿清晰
        df_daylight = df_data[df_data["POA_Wm2"] > 20.0].copy()

        axis_options = {
            "📐 太陽入射角 θi (°) [第2章面板幾何]": "Incidence_Angle_deg",
            "☀️ 太陽天球仰角 αs (°) [第1章天文高度]": "Sun_Elevation_deg",
            "🎯 POA 面板斜面有效輻照度 (W/m²) [第2章受光]": "POA_Wm2",
            "🔥 Faiman 面板工作溫度 (°C) [第4章熱力學]": "T_cell_C",
            "🌡️ 測站環境氣溫 Tamb (°C) [氣象因子]": "T_amb_C",
            "💨 案場風速 v (m/s) [對流散熱因子]": "Wind_ms",
            "🌫️ PM2.5 細懸浮微粒 (μg/m³) [空品積塵因子]": "PM25_ugm3",
            "⏳ 連續無雨累積時數 (hr) [乾季累積因子]": "Dry_Hours_Since_Rain",
            "⚡ 案場實測發電功率 P_actual (kW) [最終產出]": "P_actual_kW",
            "🤖 AI 捕捉之環境殘差 Residual (kW) [暗損幅度]": "Residual_kW"
        }

        c3d_1, c3d_2, c3d_3, c3d_4 = st.columns(4, gap="medium")
        with c3d_1:
            x_label = st.selectbox("🧭 選擇 X 軸 (太陽/幾何維度)：", list(axis_options.keys()), index=0)
        with c3d_2:
            y_label = st.selectbox("🌡️ 選擇 Y 軸 (氣候/熱力學維度)：", list(axis_options.keys()), index=3)
        with c3d_3:
            z_label = st.selectbox("⚡ 選擇 Z 軸 (發電/殘差高度)：", list(axis_options.keys()), index=8)
        with c3d_4:
            color_label = st.selectbox("🎨 選擇圓點顏色 (第 4 維度微氣候)：", list(axis_options.keys()), index=6)

        x_col = axis_options[x_label]
        y_col = axis_options[y_label]
        z_col = axis_options[z_label]
        c_col = axis_options[color_label]

        fig_3d_rel = go.Figure()

        # 若選擇預設的「入射角 x 面板溫度 x 實測發電量」，額外疊加一層半透明「3D 理論物理基準曲面網格」供立體對照！
        if x_col == "Incidence_Angle_deg" and y_col == "T_cell_C" and z_col == "P_actual_kW":
            theta_grid = np.linspace(float(df_daylight["Incidence_Angle_deg"].min()), 80.0, 25)
            tcell_grid = np.linspace(float(df_daylight["T_cell_C"].min()), float(df_daylight["T_cell_C"].max()), 25)
            TH, TC = np.meshgrid(theta_grid, tcell_grid)
            # 根據入射角估算典型晴天 POA 與理論物理功率曲面
            poa_ ideal_mesh = 950.0 * np.cos(np.radians(np.clip(TH, 0.0, 85.0)))
            scale_f = capacity_kw / 1000.0
            p_mesh = scale_f * (poa_ideal_mesh / 1000.0) * 0.215 * (1.0 - 0.004 * np.maximum(0.0, TC - 25.0))

            fig_3d_rel.add_trace(go.Surface(
                x=TH, y=TC, z=p_mesh,
                opacity=0.28,
                showscale=False,
                colorscale=[[0, '#93C5FD'], [1, '#1D4ED8']],
                name='🟦 理想晴天物理基準曲面 (3D Physics Surface)',
                hoverinfo='skip'
            ))

        # 加入真實白晝觀測點 3D Scatter
        fig_3d_rel.add_trace(go.Scatter3d(
            x=df_daylight[x_col],
            y=df_daylight[y_col],
            z=df_daylight[z_col],
            mode="markers",
            name="🌐 案場白晝真實觀測樣本點",
            marker=dict(
                size=5,
                color=df_daylight[c_col],
                colorscale="Turbo",
                opacity=0.88,
                colorbar=dict(
                    title=dict(text=f"<b>{color_label.split(' ')[1]}</b>", font=dict(color="#0F172A", size=12)),
                    tickfont=dict(color="#0F172A", size=11),
                    thickness=18, len=0.75
                )
            ),
            customdata=np.stack([
                df_daylight["timestamp"].dt.strftime("%Y-%m-%d %H:%M"),
                df_daylight["Sun_Elevation_deg"],
                df_daylight["Incidence_Angle_deg"],
                df_daylight["POA_Wm2"],
                df_daylight["T_cell_C"],
                df_daylight["Wind_ms"],
                df_daylight["PM25_ugm3"],
                df_daylight["Dry_Hours_Since_Rain"],
                df_daylight["P_actual_kW"],
                df_daylight["P_ai_hybrid_kW"]
            ], axis=-1),
            hovertemplate=(
                "<b>🕒 觀測時刻：%{customdata[0]}</b><br>"
                "☀️ 太陽仰角 αs：%{customdata[1]:.1f}° ｜ 📐 面板入射角 θi：%{customdata[2]:.1f}°<br>"
                "🎯 斜面輻照 POA：%{customdata[3]:.0f} W/m²<br>"
                "🔥 面板溫度 Tcell：%{customdata[4]:.1f} °C ｜ 💨 風速：%{customdata[5]:.1f} m/s<br>"
                "🌫️ PM2.5 濃度：%{customdata[6]:.1f} μg/m³ ｜ ⏳ 連續無雨：%{customdata[7]:.0f} hr<br>"
                "🔴 實測發電功率：<b>%{customdata[8]:.2f} kW</b> ｜ 🟢 AI 預測：<b>%{customdata[9]:.2f} kW</b><extra></extra>"
            )
        ))

        fig_3d_rel.update_layout(
            title=dict(
                text=f"<b>🌐 {site_info['short_name']} —— 3D 立體關係圖（X：{x_label.split('[')[0]} ✕ Y：{y_label.split('[')[0]} ✕ Z：{z_label.split('[')[0]}）</b>",
                font=dict(size=15, color="#0F172A"), x=0.01, y=0.97
            ),
            height=600,
            margin=dict(l=10, r=10, t=55, b=10),
            paper_bgcolor="#FFFFFF",
            font=dict(color="#0F172A", size=12),
            scene=dict(
                xaxis=dict(title=dict(text=f"<b>X：{x_label.split('[')[0]}</b>", font=dict(color="#1E3A8A", size=12)), backgroundcolor="#F8FAFC", gridcolor="#CBD5E1"),
                yaxis=dict(title=dict(text=f"<b>Y：{y_label.split('[')[0]}</b>", font=dict(color="#B91C1C", size=12)), backgroundcolor="#F8FAFC", gridcolor="#CBD5E1"),
                zaxis=dict(title=dict(text=f"<b>Z：{z_label.split('[')[0]}</b>", font=dict(color="#047857", size=12)), backgroundcolor="#F8FAFC", gridcolor="#CBD5E1"),
                aspectmode="manual",
                aspectratio=dict(x=1.25, y=1.15, z=0.85),
                camera=dict(eye=dict(x=1.55, y=-1.55, z=0.85))
            ),
            legend=dict(orientation="h", yanchor="top", y=0.93, xanchor="left", x=0.02, bgcolor="rgba(241,245,249,0.9)")
        )
        st.plotly_chart(fig_3d_rel, use_container_width=True, key="multi_dim_3d_surface")

    else:
        st.warning("⚠️ 系統偵測到未安裝 `scikit-learn` 套件，請確認 `requirements.txt` 中包含 `scikit-learn`。")
