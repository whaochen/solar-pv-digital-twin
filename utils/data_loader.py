import streamlit as st
import pandas as pd

@st.cache_data(ttl=600)
def load_cloud_database():
    """從 Google Drive 讀取太陽能數位孿生 CSV 資料庫"""
    url = "https://drive.google.com/uc?id=" + st.secrets.get("GDRIVE_FILE_ID", "1VfFki57G4wBGJAD415B0KsADTPChZN_E")
    try:
        return pd.read_csv(url)
    except Exception:
        return None
