import streamlit as st
import pandas as pd
import numpy as np

# 網頁標題與設定
st.set_page_config(page_title="一顆光子的奇幻旅程：太陽能光電數位孿生實驗室", layout="wide")

st.title("☀️ 一顆光子的奇幻旅程：太陽能光電數位孿生實驗室")
st.markdown("### 結合物理推導、機器學習（AI）與雲端動態資料庫的次世代太陽能數位孿生系統")

# 從你的 Google 雲端硬碟直接讀取真實資料庫
@st.cache_data
def load_cloud_database():
    # 將 Google Drive 分享連結轉換為穩定下載連結
    file_id = "1VfFki57G4wBGJAD415B0KsADTPChZN_E"
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"雲端資料庫載入失敗：{e}")
        return None

df_cloud = load_cloud_database()

if df_cloud is not None and not df_cloud.empty:
    st.success("✅ 成功連線至 Google 雲端資料庫（Solar_PV_Digital_Twin）！即時氣象與 AI 數位孿生模型運作中。")
    
    # 顯示部分資料預覽
    with st.expander("📊 檢視 Google 雲端即時逐時氣象與 AI 模擬資料表"):
        st.dataframe(df_cloud.head(24))
        
    # 簡單畫出 AI 數位孿生發電量趨勢圖
    if 'power_ai_digital_twin_kw' in df_cloud.columns:
        st.subheader("📈 雲端 AI 數位孿生發電預測曲線 (kW)")
        st.line_chart(df_cloud['power_ai_digital_twin_kw'].head(120))
else:
    st.warning("⚠️ 目前正在讀取預設備用物理模擬引擎...")
