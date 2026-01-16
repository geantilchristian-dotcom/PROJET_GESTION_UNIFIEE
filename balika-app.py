import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import base64
from PIL import Image

# ==============================================================================
# 1. CONFIGURATION & STYLE (FULL ORANGE & LUMINOSITÉ MOBILE)
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None, 'devise': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_pro_v740.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION BASE DE DONNÉES (SCHÉMA COMPLET)
# ==============================================================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS config (ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF')")
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", ('admin', make_hashes("admin123"), 'ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?, ?, ?, ?)", ('SYSTEM', 'MON ENTREPRISE', 2850.0, 'Bienvenue'))

init_db()

# --- RÉCUPÉRATION PARAMÈTRES ---
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg = run_db("SELECT nom_ent, message, taux FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 50px;
        z-index: 9999; border-bottom: 2px solid white;
        display: flex; align-items: center; overflow: hidden;
    }}
    marquee {{ font-size: 24px; font-weight: bold; }}
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 10px; font-weight: bold; border: 2px solid white; height: 50px;
    }}
    .clock-box {{
        background: #000; color: #FF8C00; padding: 25px; border-radius: 20px;
        border: 4px solid white; text-align: center; margin-bottom: 20px;
    }}
    .price-frame {{
        border: 5px solid #000; background: #FFF; padding: 15px;
        border-radius: 15px; color: #000; font-size: 30px; font-weight: bold; text-align: center;
    }}
    div[data-baseweb="input"] {{ background-color: #FFFFFF !important; }}
    input {{ color: #000 !important; font-weight: bold !important; }}
    </style>
    <div class="marquee-wrapper"><marquee scrollamount="8">{C_MSG}</marquee></div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. GESTION CONNEXION
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown('<div class="clock-box"><h2>ACCÈS SYSTÈME</h2></div>', unsafe_allow_html=True)
        u = st.text_input("ID Utilisateur").lower().strip()
        p = st.text_input("Code Secret", type="password")
        if st.button("DÉVERROUILLER"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 4. NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {USER.upper()}")
    if ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 VENDEURS", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    if st.button("🚪 QUITTER", type="primary"):
        st.session_state.auth = False; st.rerun()

# ==============================================================================
# 5. PAGES DU SYSTÈME
# ==============================================================================

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div class="clock-box"><h1 style="font-size:60px;margin:0;">{datetime.now().strftime("%H:%M")}</h1><p>{datetime.now().strftime("%d/%m/%Y")}</p></div></center>', unsafe_allow_html=True)
    st.metric("ENTREPRISE", C_NOM)

# --- PROFIL (MODIFIER MESSAGE) ---
elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL")
    if ROLE == "ADMIN":
        with st.container(border=True):
            st.subheader("📢 MESSAGE DÉFILANT")
            msg_in = st.text_area("Modifier le texte :", value=C_MSG)
            if st.button("ENREGISTRER"):
                run_db("UPDATE config SET message=? WHERE ent_id=?", (msg_in, ENT_ID)); st.rerun()
    
    with st.expander("🔐 SÉCURITÉ"):
        np = st.text_input("Nouveau mot de passe", type="password")
        if st.button("CHANGER"):
            run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(np), USER)); st.success("OK")

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.header("📦 STOCK")
    with st.form("add_p"):
        c1, c2, c3, c4 = st.columns(4)
        n = c1.text_input("Désignation")
        q = c2.number_input("Qté", 1)
        p = c3.number_input("Prix")
        d = c4.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n.upper(), q, p, d, ENT_ID)); st.rerun()
    
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pi, dn, sq, pv, dv in prods:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([3, 1, 0.5])
            cl1.write(f"**{dn}** - {pv} {dv}")
            cl2.write(f"Stock: {sq}")
            if cl3.button("🗑️", key=f"del_{pi}"):
                run_db("DELETE FROM produits WHERE id=?", (pi,)); st.rerun()

# --- CAISSE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        devise_caisse = st.radio("Vendre en:", ["USD", "CDF"], horizontal=True)
        pl = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in pl}
        
        sel = st.selectbox("Article", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
            
        if st.session_state.panier:
            total_v = 0.0
            for art, qty in list(st.session_state.panier.items()):
                info = p_map[art]
                px_final = info['px']
                if info['dv'] != devise_caisse:
                    px_final = px_final * C_TX if devise_caisse == "CDF" else px_final / C_TX
                
                total_v += px_final * qty
                l1, l2, l3 = st.columns([3, 1, 0.5])
                l1.write(art)
                st.session_state.panier[art] = l2.number_input("Qté", 1, info['st'], value=qty, key=f"v_{art}")
                if l3.button("🗑️", key=f"r_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="price-frame">TOTAL : {total_v:,.2f} {devise_caisse}</div>', unsafe_allow_html=True)
            cl_n = st.text_input("Client", "COMPTANT")
            pay = st.number_input("Montant Payé", value=float(total_v))
            
            if st.button("✅ VALIDER VENTE"):
                ref = f"FAC-{random.randint(100,999)}"
                reste = total_v - pay
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id) VALUES (?,?,?,?,?,?,?,?,?)", 
                       (ref, cl_n.upper(), total_v, pay, reste, devise_caisse, datetime.now().strftime("%d/%m/%Y %H:%M"), USER, ENT_ID))
                if reste > 0:
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cl_n.upper(), reste, devise_caisse, ref, ENT_ID))
                for a, q in st.session_state.panier.items():
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (q, a, ENT_ID))
                st.session_state.last_fac = {'ref': ref, 'cl': cl_n, 'tot': total_v, 'dev': devise_caisse}; st.session_state.panier = {}; st.rerun()
    else:
        # FACTURE + BOUTON RETOUR
        f = st.session_state.last_fac
        if st.button("⬅️ RETOUR À LA CAISSE"):
            st.session_state.last_fac = None; st.rerun()
        st.markdown(f'<div style="background:white; color:black; padding:20px; border:2px solid black; text-align:center;"><h2>{C_NOM}</h2><hr><h4>Facture: {f["ref"]}</h4><h3>Total: {f["tot"]} {f["dev"]}</h3></div>', unsafe_allow_html=True)

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.header("📉 DETTES")
    dts = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    for di, dc, dm, dd, dr in dts:
        with st.container(border=True):
            st.write(f"👤 {dc} | Solde: **{dm} {dd}**")
            vp = st.number_input("Versement", 0.0, float(dm), key=f"p_{di}")
            if st.button("PAYER", key=f"b_{di}"):
                nm = dm - vp
                run_db("UPDATE dettes SET montant=? WHERE id=?", (nm, di))
                if nm <= 0: run_db("DELETE FROM dettes WHERE id=?", (di,))
                st.rerun()

# --- VENDEURS ---
elif st.session_state.page == "VENDEURS":
    st.header("👥 VENDEURS")
    with st.form("v"):
        u_v = st.text_input("Nom Vendeur")
        p_v = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (u_v.lower(), make_hashes(p_v), "VENDEUR", ENT_ID)); st.rerun()

# --- RAPPORTS ---
elif st.session_state.page == "RAPPORTS":
    st.header("📊 RAPPORTS")
    if st.button("⬅️ RETOUR"):
        st.session_state.page = "ACCUEIL"; st.rerun()
    data = run_db("SELECT date_v, ref, client, total, devise, vendeur FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    if data: st.dataframe(pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Devise", "Vendeur"]))
