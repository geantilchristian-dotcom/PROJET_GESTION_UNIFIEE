import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import hashlib
import random

# CONFIGURATION PAGE
st.set_page_config(page_title="BALIKA ERP v305", layout="wide")

# CONNEXION GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet):
    try:
        return conn.read(worksheet=worksheet, ttl="0s").dropna(how="all")
    except:
        return pd.DataFrame()

def save_data(df, worksheet):
    conn.update(worksheet=worksheet, data=df)

# --- AUTHENTIFICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

# CHARGEMENT CONFIG
try:
    df_cfg = get_data("config")
    if not df_cfg.empty:
        C_ENT = df_cfg.iloc[0]['entreprise']
        C_TAUX = float(df_cfg.iloc[0]['taux'])
    else:
        C_ENT, C_TAUX = "BALIKA ERP", 2850.0
except:
    C_ENT, C_TAUX = "BALIKA ERP", 2850.0

# --- INTERFACE DE CONNEXION ---
if not st.session_state.auth:
    st.title(f"🔑 Connexion {C_ENT}")
    u = st.text_input("Identifiant").lower().strip()
    p = st.text_input("Mot de passe", type="password").strip()
    if st.button("ENTRER"):
        if u == "admin" and p == "admin123":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# --- MENU PRINCIPAL ---
st.sidebar.title(f"🏢 {C_ENT}")
page = st.sidebar.radio("MENU", ["ACCUEIL", "STOCK", "CAISSE", "DETTES"])

if page == "ACCUEIL":
    st.title("Tableau de bord")
    st.write(f"Taux du jour : 1 USD = {C_TAUX} CDF")
    st.success("Application connectée avec succès à Google Sheets !")

elif page == "STOCK":
    st.title("📦 Gestion du Stock")
    df_p = get_data("produits")
    st.dataframe(df_p)
