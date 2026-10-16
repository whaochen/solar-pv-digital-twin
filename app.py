import streamlit as st
from utils.data_loader import load_cloud_database

st.set_page_config(
    page_title="一顆光子的奇幻旅程：太陽能光電數位孿生實驗室",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ 一顆光子的奇幻旅程：太陽能光電數位孿生實驗室")
st.markdown("""
歡迎來到**零本地端負擔（Zero-Local-Storage）**的次世代太陽能光電互動教學與數位孿生實驗室！
本系統結合**第一性原理物理推導**、**3D WebGL 空間幾何互動**與 **Google Colab 雲端機器學習模型**。

### 🗺️ 冒險地圖（請從左側選單點選章節開始探索）：
1. **【起程】太陽的四季華爾滋**：3D 天球穹頂、三大教學視角與赤緯角公式推導。
2. **【追光】向日葵工程**：固定式 vs 單軸 vs 雙軸追日系統的 3D 入射角幾何。
3. **【微氣候】高溫與風雨的洗禮**：為什麼太陽越大反而發電效率下降？Faiman 散熱模型解析。
4. **【AI 賦能】殘差修正與數位孿生**：當物理公式遇上真實世界的灰塵與雲層，AI 如何補足最後一哩路？
5. **【實戰】真實電廠比對與決策**：對標台灣真實環境與碳減排效益評估。
""")

st.markdown("---")
df_cloud = load_cloud_database()
if df_cloud is not None and not df_cloud.empty:
    st.success(f"🛰️ **雲端大腦連線正常**：已成功同步 Google Drive 雲端資料庫（共 {len(df_cloud)} 筆逐時氣象與 AI 預測數據）。")
    with st.expander("📊 點此快速預覽雲端資料庫最新 24 小時數據"):
        st.dataframe(df_cloud.head(24))
else:
    st.warning("⚠️ 雲端資料庫連線中或使用離線物理引擎模式。")
