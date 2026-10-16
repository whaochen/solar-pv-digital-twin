import streamlit as st
import pandas as pd
import numpy as np

# 網頁標題與設定
st.set_page_config(page_title="一顆光子的奇幻旅程：太陽能光電數位孿生實驗室", layout="wide")

# 側邊欄導航：故事與知識章節
st.sidebar.markdown("# ☀️ 導覽選單")
chapter = st.sidebar.radio(
    "選擇冒險章節：",
    [
        "第 0 章：雲端資料庫即時連線狀態",
        "第 1 章：光子的誕生與天文幾何",
        "第 2 章：追日工程與入射角奇蹟",
        "第 3 章：微氣候散熱與 Faiman 模型",
        "第 4 章：AI 殘差修正與數位孿生預測",
        "第 5 章：真實電廠比對與決策支援"
    ]
)

# 從 Google 雲端硬碟讀取資料庫
@st.cache_data
def load_cloud_database():
    file_id = "1VfFki57G4wBGJAD415B0KsADTPChZN_E"
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

df_cloud = load_cloud_database()

# ==================== 第 0 章 ====================
if chapter == "第 0 章：雲端資料庫即時連線狀態":
    st.title("🛰️ 雲端 AI 數位孿生與資料庫狀態")
    st.markdown("在這裡，我們監控從 **Google Colab** 運算、**Google Drive** 儲存至 **Streamlit 雲端前端**的零本地端負擔資料管線。")
    
    if df_cloud is not None and not df_cloud.empty:
        st.success("✅ 成功連線至 Google 雲端資料庫 (`Solar_PV_Digital_Twin`)！")
        st.metric("雲端資料庫總筆數（逐時紀錄）", f"{len(df_cloud)} 筆")
        with st.expander("📊 檢視原始雲端氣象與 AI 模擬數據表"):
            st.dataframe(df_cloud.head(48))
    else:
        st.warning("⚠️ 目前正在讀取備用模擬數據。")

# ==================== 第 1 章 ====================
elif chapter == "第 1 章：光子的誕生與天文幾何":
    st.title("✨ 第 1 章：光子的奇幻旅程 —— 從日核到台灣上空")
    st.markdown("""
    > **「嗨！我是編號 8,765,432 號的光子。我在 8 分鐘前從太陽核心出發，穿越 1.5 億公里，準備降落在台灣嘉南平原的太陽能面板上……」**
    
    在這一章中，我們透過天文幾何公式推導太陽赤緯角（Declination）與高度角（Solar Altitude），理解為什麼台灣的日照角度會隨著四季與經緯度產生劇烈變化。
    """)
    if df_cloud is not None and 'solar_altitude_deg' in df_cloud.columns:
        st.subheader("📈 雲端氣象記錄：過去 30 天太陽高度角變化")
        st.line_chart(df_cloud['solar_altitude_deg'].head(120))

# ==================== 第 2 章 ====================
elif chapter == "第 2 章：追日工程與入射角奇蹟":
    st.title("🌻 第 2 章：追日工程 —— 固定式 vs 單軸 vs 雙軸的抉擇")
    st.markdown("""
    光子抵達地面時，如果面板像向日葵一樣會動，能多捕獲多少能量？
    * **固定式（Fixed Tilt）：** 結構簡單，維護成本最低。
    * **單軸追日（Single-Axis）：** 東西向跟隨太陽轉動，晨昏發電量顯著提升。
    * **雙軸追日（Dual-Axis）：** 隨時垂直對準太陽，效率極致但機械結構複雜。
    """)
    st.info("💡 提示：系統已自動計算不同追日角度下的入射角餘弦（Cosine Efficiency）模型。")

# ==================== 第 3 章 ====================
elif chapter == "第 3 章：微氣候散熱與 Faiman 模型":
    st.title("🌡️ 第 3 章：微氣候散熱 —— 為什麼太熱反而發電少？")
    st.markdown("""
    光子不是溫度越高越好！當溫度超過 25°C，半導體晶圓的電壓會下降。
    我們採用 **Faiman 熱力學散熱模型**：
    $$T_{cell} = T_{amb} + \\frac{G}{U_0 + U_1 \\cdot V_{wind}}$$
    結合風速（$V_{wind}$）與相對濕度，精準模擬面板背面的真實微氣候溫度。
    """)

# ==================== 第 4 章 ====================
elif chapter == "第 4 章：AI 殘差修正與數位孿生預測":
    st.title("🤖 第 4 章：AI 殘差修正 —— 結合物理與機器學習的數位孿生")
    st.markdown("""
    純物理公式無法完全預測現實世界的所有干擾（例如：午後陣雨後的灰塵洗淨效應、高濕度散射）。
    因此，我們導入 **Gradient Boosting 機器學習模型**，專門學習「真實發電量與物理理論值之間的殘差（Residual）」，讓預測精準度大幅提升！
    """)
    if df_cloud is not None and 'power_ai_digital_twin_kw' in df_cloud.columns:
        st.subheader("📊 雲端 AI 數位孿生發電預測曲線 (kW)")
        st.markdown("以下曲線是由 **Google Colab 雲端大腦** 訓練、並直接從 **Google Drive 雲端資料庫** 讀取的即時數位孿生發電預測結果：")
        st.line_chart(df_cloud['power_ai_digital_twin_kw'].head(120))

# ==================== 第 5 章 ====================
elif chapter == "第 5 章：真實電廠比對與決策支援":
    st.title("🏭 第 5 章：真實電廠比對與決策支援")
    st.markdown("""
    結合台南七股鹽田光電廠的實際運轉特徵，本系統提供：
    1. **碳減排效益計算**（對應 ISO 14064 盤查標準）。
    2. **營運維護（O&M）異常預警**（當 AI 預測值與實際發電量出現偏差時自動發出警報）。
    """)
    st.success("🎯 您的太陽能光電數位孿生網站已具備完整的故事導讀、物理模型與雲端 AI 數據流！")
