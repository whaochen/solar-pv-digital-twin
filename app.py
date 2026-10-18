# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="台灣光電數位孿生與 AI 智慧維運平台",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入與全書 1~7 章完全統一的高亮度視覺 CSS (padding-top: 3.5rem 防止頂部標題被切掉)
css_lines = [
    "<style>",
    ".block-container { padding-top: 3.5rem !important; padding-bottom: 1.5rem !important; }",
    ".hero-box { background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #1E293B 100%); border: 1px solid #3B82F6; border-radius: 14px; padding: 22px 26px; color: #F8FAFC !important; box-shadow: 0 8px 20px rgba(0,0,0,0.22); margin-bottom: 18px; }",
    ".hero-title { color: #FFD700 !important; font-size: 1.65rem; font-weight: 800; margin-bottom: 8px; line-height: 1.3; }",
    ".hero-sub { color: #E2E8F0 !important; font-size: 1.0rem; line-height: 1.65; }",
    ".pillar-card { background: linear-gradient(145deg, #0F172A, #1E293B); border: 1px solid #475569; border-radius: 12px; padding: 15px 18px; color: #F8FAFC !important; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 10px; }",
    ".pillar-tag { color: #38BDF8 !important; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 4px; }",
    ".pillar-head { color: #FFD700 !important; font-size: 1.2rem; font-weight: 800; margin-bottom: 6px; }",
    ".pillar-body { color: #CBD5E1 !important; font-size: 0.88rem; line-height: 1.55; }",
    ".section-banner { background: linear-gradient(90deg, #1E3A8A, #1E293B); color: #FFFFFF !important; padding: 10px 18px; border-radius: 8px; font-size: 1.15rem; font-weight: 700; margin-top: 18px; margin-bottom: 14px; border-left: 6px solid #FFD700; }",
    ".ch-card { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-left: 6px solid #2563EB; border-radius: 10px; padding: 14px 18px; color: #0F172A; margin-bottom: 12px; }",
    ".ch-card-ai { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-left: 6px solid #7C3AED; border-radius: 10px; padding: 14px 18px; color: #0F172A; margin-bottom: 12px; }",
    ".ch-card-biz { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-left: 6px solid #059669; border-radius: 10px; padding: 14px 18px; color: #0F172A; margin-bottom: 12px; }",
    "</style>"
]
st.markdown("\n".join(css_lines), unsafe_allow_html=True)

# ==================== 頂部：系統主視覺英雄橫幅 (Hero Banner) ====================
st.markdown(
    '<div class="hero-box">'
    '<div class="hero-title">☀️ 台灣太陽能光電案場：物理引導灰箱數位孿生與 Open Data 智慧維運分析平台</div>'
    '<div class="hero-sub">'
    '<b>Physics-Guided Grey-Box Digital Twin & Automated Open Data Analytics for Solar PV Plants in Taiwan</b><br>'
    '本平台以<b>「一顆光子的奇幻旅程」</b>為敘事主軸，從距離地球 1.5 億公里的太陽出發，完整貫穿<b>球面天文幾何（第 1 章）</b>、<b>追日與大氣輻射（第 2 章）</b>、'
    '<b>半導體光電轉換與變電設備（第 3 章）</b>、<b>微氣候熱力學散熱（第 4 章）</b>，並即時介接<b>國際衛星與環境空品 Open Data 累積管線（第 5 章）</b>，'
    '最終透過<b>AI 隨機森林殘差修正（第 6 章）</b>與<b>智慧維運商業決策模組（第 7 章）</b>，打造具備學術嚴謹度與產業實戰價值的全息數位孿生系統。'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ==================== 第一節：系統架構四大核心支柱 (4 Pillars) ====================
p1, p2, p3, p4 = st.columns(4, gap="medium")

with p1:
    st.markdown(
        '<div class="pillar-card">'
        '<div class="pillar-tag">STAGE 01 ｜ 第 1 ～ 4 章</div>'
        '<div class="pillar-head">📐 第一性原理物理基石</div>'
        '<div class="pillar-body">'
        '建立嚴格遵守能量守恆之「白箱物理模型」：涵蓋 Cooper 赤緯角、球面三角天球軌跡、Liu & Jordan 斜面輻照、P-N 接面光電效應與 IEC 61853-2 Faiman 風冷熱平衡方程式。'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

with p2:
    st.markdown(
        '<div class="pillar-card">'
        '<div class="pillar-tag">STAGE 02 ｜ 第 5 章</div>'
        '<div class="pillar-head">📡 真實 Open Data 管線</div>'
        '<div class="pillar-body">'
        '免金鑰自動串接向日葵衛星反演輻照（GHI/DNI/DHI）、地面測站氣溫風速與環境 PM2.5 空品數據。自 2026-08-18 錨定起點每日自動累加 24 筆活資料，零本地儲存負擔。'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

with p3:
    st.markdown(
        '<div class="pillar-card">'
        '<div class="pillar-tag">STAGE 03 ｜ 第 6 章</div>'
        '<div class="pillar-head">🤖 AI 灰箱混合殘差修正</div>'
        '<div class="pillar-body">'
        '採用「物理當主廚、AI 當二廚」之灰箱架構（Grey-Box Hybrid Twin）。以嚴格時序分割訓練隨機森林模型，精準學習 PM2.5 積塵、連續無雨時數與鹽霧造成之非線性發電殘差。'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

with p4:
    st.markdown(
        '<div class="pillar-card">'
        '<div class="pillar-tag">STAGE 04 ｜ 第 7 章</div>'
        '<div class="pillar-head">💡 智慧維運與商業變現</div>'
        '<div class="pillar-body">'
        '將 AI 預測轉化為三大營運決策：(1) 自動過濾環境積塵假警報、抓出真硬體故障；(2) 計算水車清洗損益平衡點；(3) 降低台電發電申報偏差（MAE/RMSE）罰款風險。'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

# ==================== 第二節：貫穿全書 7 章之數位孿生數學總架構 ====================
st.markdown('<div class="section-banner">🧮 數位孿生核心數學架構：從第一性原理物理基準到 AI 殘差修正之閉環方程式</div>', unsafe_allow_html=True)

eq_c1, eq_c2 = st.columns([1.35, 1.0], gap="large")

with eq_c1:
    with st.container(border=True):
        st.markdown("##### 📜 全系統灰箱混合預測總公式（Physics-Guided Hybrid Equation）")
        st.latex(
            r"\hat{P}_{\text{Hybrid}}(t) = \underbrace{P_{\text{Physics}}\big(\alpha_s(t),\, \theta_i(t),\, G_{\text{POA}}(t),\, T_{\text{cell}}(t)\big)}_{\text{第 1～4 章：第一性原理物理基準模型 (White-Box)}} + \underbrace{\hat{f}_{\text{RF}}\big(\text{PM}_{2.5}(t),\, \text{DryHours}(t),\, \text{RH}(t),\, v_w(t),\, \theta_i(t)\big)}_{\text{第 5～6 章：Open Data 驅動之 AI 環境殘差模型 }\Delta \hat{P}_{\text{residual}}(t)}"
        )
        st.markdown(
            "* **物理基準項 $P_{\\text{Physics}}(t)$**：確保數位孿生永遠不會違反熱力學與能量守恆定律（例如夜晚 $G_{\\text{POA}}=0$ 時發電量必為 $0$）。\n"
            "* **AI 殘差修正項 $\\Delta \\hat{P}_{\\text{residual}}(t)$**：專門捕捉傳統物理公式無法表達的**「台灣在地複合微氣候暗損」**（乾季積塵、降雨洗塵跳升、沿海鹽霧與大角度玻璃反射）。\n"
            "* **智慧維運診斷準則（第 7 章）**：當實測功率 $P_{\\text{actual}}(t)$ 顯著低於 $\\hat{P}_{\\text{Hybrid}}(t)$ 超過安全閾值時，即刻排除環境積塵干擾，觸發真實硬體故障派工警報！"
        )

with eq_c2:
    # 繪製 7 章節知識與數據流向雷達/階層示意圖
    fig_arch = go.Figure(go.Funnel(
        y=[
            "第 1 章：太陽天球幾何 (δ, ω, αs)",
            "第 2 章：追日與斜面輻照 (θi, POA)",
            "第 3 章：半導體與變電損耗 (DC➔AC)",
            "第 4 章：微氣候 Faiman 散熱 (Tcell)",
            "第 5 章：Open Data 每日累積管線",
            "第 6 章：AI 隨機森林殘差修正 (ΔP)",
            "第 7 章：智慧故障診斷與清洗決策"
        ],
        x=[100, 92, 85, 78, 72, 66, 60],
        textinfo="label",
        marker=dict(
            color=["#1D4ED8", "#2563EB", "#0284C7", "#0D9488", "#7C3AED", "#9333EA", "#059669"]
        )
    ))
    fig_arch.update_layout(
        title=dict(text="<b>🔗 全書七大章節物理與數據流向漏斗圖</b>", font=dict(size=14, color="#0F172A"), x=0.02, y=0.96),
        height=310,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        showlegend=False
    )
    st.plotly_chart(fig_arch, use_container_width=True, key="home_funnel_chart")

# ==================== 第三節：全書七大章節完整導覽地圖 ====================
st.markdown('<div class="section-banner">🗺️ 全書七大章節探索地圖（請點選左側欄或下方卡片依序體驗）</div>', unsafe_allow_html=True)

st.markdown("#### 🟦 第一部曲：【物理白箱基石】光子從太陽到電網的第一性原理（第 1 ～ 4 章）")
c_ch1, c_ch2 = st.columns(2, gap="medium")

with c_ch1:
    st.markdown(
        '<div class="ch-card">'
        '<b>☀️ 第 1 章：【起程】太陽的四季華爾滋（太陽 ➔ 地球座標）</b><br>'
        '• <b>核心物理</b>：Cooper (1969) 赤緯角 $\\delta$、球面三角日落時角 $\\omega_s$、天球仰角 $\\alpha_s$。<br>'
        '• <b>互動舞台</b>：無閃爍 WebGL 3D 天球穹頂、四季軌道對比與四種觀察視角。<br>'
        '• <b>學術思辨</b>：揭開「手錶正午 12 點太陽不在正南方（均時差 EoT）」與「山稜線遮蔭」之工程盲區。'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="ch-card">'
        '<b>⚡ 第 3 章：【蛻變】光電轉換與太陽能電廠大解密（光子 ➔ 電網）</b><br>'
        '• <b>核心物理</b>：矽能隙 $1.12\\text{ eV}$ 光生伏打效應、逆變器 MPPT 最大功率追蹤、$22.8\\text{ kV}$ 升壓變壓器減損。<br>'
        '• <b>互動舞台</b>：3D 宏觀電廠設備能量粒子流 ＋ 3D 微觀 P-N 接面電子電洞分離解剖圖。<br>'
        '• <b>學術思辨</b>：剖析「串聯木桶效應與熱斑（Hot Spot）」以及「容配比超配（DC/AC Ratio > 1.2）削峰哲學」。'
        '</div>',
        unsafe_allow_html=True
    )

with c_ch2:
    st.markdown(
        '<div class="ch-card">'
        '<b>🌻 第 2 章：【穿越】大氣層與追日工程（太陽光 ➔ 面板幾何）</b><br>'
        '• <b>核心物理</b>：法線直射光（DNI）vs. 天空散射光（DHI）、餘弦損失 $\\cos\\theta_i$、Liu & Jordan 斜面總輻照度 $G_{\\text{POA}}$。<br>'
        '• <b>互動舞台</b>：固定式、單軸追日、雙軸追日 3D 同場競技場 ＋「胖鐘型」發電增益曲線。<br>'
        '• <b>學術思辨</b>：為何台灣大型電廠幾乎不用雙軸追日？（颱風風險、土地佔用率 GCR 與清晨逆追日 Backtracking）。'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="ch-card">'
        '<b>🌡️ 第 4 章：【考驗】微氣候熱力學與 Faiman 風冷散熱（面板溫度 ➔ 熱衰減）</b><br>'
        '• <b>核心物理</b>：IEC 61853-2 標準 Faiman 熱平衡公式 $T_{\\text{cell}} = T_{\\text{amb}} + G/(U_0 + U_1 v_w)$ 與功率溫度係數 $\\gamma$。<br>'
        '• <b>互動舞台</b>：3D 太陽能板紅外線熱成像（Thermal IR）與海風強制對流冷卻粒子流。<br>'
        '• <b>學術思辨</b>：打破「夏天日照最長發電功率一定最高？」迷思，探討熱慣性延遲與台灣複合微氣候挑戰。'
        '</div>',
        unsafe_allow_html=True
    )

st.markdown("#### 🟪 第二部曲：【數據與 AI 賦能】Open Data 自動化串接、灰箱機器學習與智慧維運（第 5 ～ 7 章）")
c_ch5, c_ch6, c_ch7 = st.columns(3, gap="medium")

with c_ch5:
    st.markdown(
        '<div class="ch-card-ai">'
        '<b>📡 第 5 章：【工程基石】Open Data 自動化串接與多尺度驗證</b><br>'
        '• <b>核心技術</b>：錨定 `2026-08-18` 起算點，每日自動抓取向日葵衛星輻照、氣象與 PM2.5 活數據，舊資料永不遺失。<br>'
        '• <b>跨章整合</b>：導入台灣 5 大案場地圖與第 1、2 章太陽仰角 $\\alpha_s$、入射角 $\\theta_i$ 實時演算。<br>'
        '• <b>多尺度視圖</b>：獨立拆分「當天逐時」、「最近一週」、「指定時間區段放大鏡」，各通道配備專屬獨立圖例。'
        '</div>',
        unsafe_allow_html=True
    )

with c_ch6:
    st.markdown(
        '<div class="ch-card-ai">'
        '<b>🤖 第 6 章：【智慧賦能】AI 灰箱殘差修正與 3D 多維度因果分析</b><br>'
        '• <b>核心技術</b>：以時序前 80% 訓練隨機森林模型學習環境殘差 $\\Delta P$，後 20% 進行嚴格盲測驗證（Time-Series Split）。<br>'
        '• <b>科普導讀</b>：白話解說樹模型超參數、RMSE 與 $R^2$ 成績單、正午尖峰山頂放大視圖與中文特徵重要度排行。<br>'
        '• <b>3D 全息關係圖</b>：自由旋轉探索「入射角 $\\theta_i$ ✕ 面板溫度 $T_{\\text{cell}}$ ✕ PM2.5 ✕ 發電功率」之立體物理曲面。'
        '</div>',
        unsafe_allow_html=True
    )

with c_ch7:
    st.markdown(
        '<div class="ch-card-biz">'
        '<b>💡 第 7 章：【商業落地】智慧維運與經濟決策模組（Smart O&M）</b><br>'
        '• <b>回答核心問題</b>：「有 AI 和沒有 AI 到底差在哪裡？AI 的實質貢獻是什麼？」<br>'
        '• <b>三大商業功能</b>：<br>'
        '  1. 🚨 <b>智慧故障診斷雷達</b>：自動區分環境積塵與真硬體故障，過濾假警報。<br>'
        '  2. 💧 <b>最佳清洗排程計算器</b>：累積少發電費損失 vs. 水車清洗成本損益平衡分析。<br>'
        '  3. ⚡ <b>台電申報偏差評估</b>：量化 AI 降低發電預測偏差之經濟效益。'
        '</div>',
        unsafe_allow_html=True
    )

# ==================== 第四節：台灣五大代表性光電案場環境特徵總覽表 ====================
st.markdown('<div class="section-banner">🇹🇼 本平台實時監測與 AI 訓練之台灣五大代表性光電案場總覽</div>', unsafe_allow_html=True)

df_sites_overview = pd.DataFrame([
    {
        "案場編號與名稱": "🇹🇼 1. 台南七股地面型旗艦案場",
        "經緯度座標": "23.15°N, 120.08°E",
        "工程架設型態": "鹽灘地與魚塭高架型 (Aquavoltaics)",
        "規模容量": "250 MW 級",
        "最佳傾角 β": "20°",
        "核心微氣候特徵與 AI 殘差學習目標": "全台日照最高，但受台江海風鹽霧結垢（Salt Mist）影響，需靠降雨洗塵恢復透光率。"
    },
    {
        "案場編號與名稱": "🇹🇼 2. 彰濱工業區崙尾東水上光電",
        "經緯度座標": "24.12°N, 120.41°E",
        "工程架設型態": "潮間帶浮筒水面型 (Floating PV)",
        "規模容量": "300 MW 級",
        "最佳傾角 β": "15°",
        "核心微氣候特徵與 AI 殘差學習目標": "台灣海峽強風走廊，Faiman 風冷散熱極佳，但退潮泥灘揚塵與浪沫鹽漬具非線性影響。"
    },
    {
        "案場編號與名稱": "🇹🇼 3. 雲林麥寮農電共生案場",
        "經緯度座標": "23.78°N, 120.25°E",
        "工程架設型態": "農地高架結合溫室型 (Agrivoltaics)",
        "規模容量": "100 MW 級",
        "最佳傾角 β": "20°",
        "核心微氣候特徵與 AI 殘差學習目標": "秋冬東北季風河川揚塵與 PM2.5 雙重衝擊，乾季連續無雨時數長，積塵衰減最顯著。"
    },
    {
        "案場編號與名稱": "🇹🇼 4. 屏東林邊地層下陷光電專區",
        "經緯度座標": "22.43°N, 120.51°E",
        "工程架設型態": "高腳防洪型地面光電架台",
        "規模容量": "120 MW 級",
        "最佳傾角 β": "18°",
        "核心微氣候特徵與 AI 殘差學習目標": "熱帶常年高溫導致正午熱衰減嚴重，夏季頻繁午後雷陣雨帶來瞬間水冷驟降與洗塵效應。"
    },
    {
        "案場編號與名稱": "🇹🇼 5. 桃園觀音工業區屋頂型光電群",
        "經緯度座標": "25.04°N, 121.11°E",
        "工程架設型態": "大型廠房浪板緊貼屋頂型 (Rooftop)",
        "規模容量": "50 MW 級",
        "最佳傾角 β": "12°",
        "核心微氣候特徵與 AI 殘差學習目標": "北台灣多雲散射光（DHI）佔比高，且鐵皮屋頂背風散熱不良（U0, U1 低），熱慣性明顯。"
    }
])

st.dataframe(df_sites_overview, use_container_width=True, hide_index=True)

st.success("👈 **請直接點選畫面左側導覽列（Sidebar）的「第 1 章 ～ 第 7 章」，立即展開光子與 AI 數位孿生的探索之旅！**")

# END OF FILE
