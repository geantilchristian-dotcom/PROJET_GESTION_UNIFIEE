# ==============================================================================
# ANASH ERP v280 - ÉDITION PROFESSIONNELLE BALIKA BUSINESS
# ------------------------------------------------------------------------------
# CORRECTIF : Gestion sécurisée de l'import Plotly pour éviter le crash.
# INSTRUCTIONS : Créez un fichier 'requirements.txt' avec : streamlit, pandas, plotly
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import random
import time
import io
import os

# Import sécurisé de Plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. CONFIGURATION & CONSTANTES
# ------------------------------------------------------------------------------
DB_FILE = "balika_v280_master.db"
VERSION = "2.8.0"

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES
# ------------------------------------------------------------------------------
def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT DEFAULT 'GENERAL')""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_payment TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, date TEXT, time TEXT, sid TEXT)""")

        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA BUSINESS ERP', 'PROSPÉRITÉ POUR VOTRE COMMERCE', ?)", (VERSION,))
        
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_master_db()

# ------------------------------------------------------------------------------
# 3. UTILITAIRES
# ------------------------------------------------------------------------------
def log_action(user, action, sid):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO audit_logs (user, action, date, time, sid) VALUES (?,?,?,?,?)",
                     (user, action, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S"), sid))
        conn.commit()

def get_hash(p): return hashlib.sha256(p.encode()).hexdigest()

def get_sys_info():
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT app_name, marquee FROM system_config WHERE id=1").fetchone()
        return res if res else ("BALIKA BUSINESS", "BIENVENUE")

# ------------------------------------------------------------------------------
# 4. DESIGN (BLEU & BLANC)
# ------------------------------------------------------------------------------
SYS_INFO = get_sys_info()
APP_NAME, MARQUEE_TEXT = SYS_INFO[0], SYS_INFO[1]

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_global_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background-color: #002b5c; color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: #001a35 !important; border-right: 2px solid #00d4ff; }}
        h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
        input {{ text-align: center; border-radius: 10px !important; font-weight: bold; background-color: white !important; color: black !important; }}
        .marquee-container {{
            background: #000; color: #00ff00; padding: 12px; font-weight: bold;
            border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }}
        .cobalt-box {{
            background: linear-gradient(135deg, #004a99 0%, #002b5c 100%);
            padding: 25px; border-radius: 20px; border: 1px solid #00d4ff;
            margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .cart-white {{
            background: white !important; color: black !important; padding: 25px;
            border-radius: 20px; border: 8px solid #004a99; margin-top: 20px;
        }}
        .cart-white * {{ color: black !important; font-weight: bold; text-align: left; }}
        .neon-total {{
            border: 4px solid #00ff00; background: #000; padding: 20px;
            border-radius: 15px; margin: 15px 0; box-shadow: 0 0 15px #00ff00;
        }}
        .total-val {{ color: #00ff00; font-size: 45px; font-weight: bold; }}
        .stButton > button {{
            width: 100%; height: 55px; border-radius: 15px; font-size: 18px;
            background: linear-gradient(to right, #007bff, #00d4ff);
            color: white !important; border: none; font-weight: bold;
        }}
        .facture-print {{
            background: white; color: black !important; padding: 30px;
            font-family: 'Courier New', Courier, monospace; width: 320px; margin: auto;
            border: 1px solid #ccc; text-align: left !important;
        }}
        .facture-print * {{ text-align: left !important; color: black !important; }}
        .table-fac {{ width: 100%; border-collapse: collapse; }}
        .table-fac th, .table-fac td {{ border-bottom: 1px dashed black; padding: 5px; font-size: 12px; color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_global_styles()

# ------------------------------------------------------------------------------
# 5. INITIALISATION SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

# ------------------------------------------------------------------------------
# 6. ÉCRAN DE CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_l, tab_r = st.tabs(["🔑 CONNEXION", "📝 DEMANDE ACCÈS"])
        
        with tab_l:
            st.markdown("<div class='cobalt-box'>", unsafe_allow_html=True)
            u_in = st.text_input("IDENTIFIANT").lower().strip()
            p_in = st.text_input("MOT DE PASSE", type="password")
            if st.button("🚀 ENTRER"):
                with sqlite3.connect(DB_FILE) as conn:
                    user_data = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_in,)).fetchone()
                    if user_data and get_hash(p_in) == user_data[0]:
                        if user_data[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u_in, 'role': user_data[1], 'shop_id': user_data[2]})
                            log_action(u_in, "Connexion", user_data[2]); st.rerun()
                        else: st.error("❌ Compte non activé par l'Admin.")
                    else: st.error("❌ Identifiants erronés.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_r:
            st.markdown("<div class='cobalt-box'>", unsafe_allow_html=True)
            new_id = st.text_input("ID Souhaité")
            new_sh = st.text_input("Nom Boutique")
            new_pw = st.text_input("Mot de Passe ", type="password")
            if st.button("📩 ENVOYER"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (new_id.lower(), get_hash(new_pw), 'GERANT', 'PENDING', 'EN_ATTENTE', new_sh, ''))
                        conn.commit(); st.success("✅ Demande envoyée !")
                    except: st.error("ID déjà utilisé.")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMIN PANEL")
    adm_m = st.sidebar.radio("Navigation", ["👥 Gestion Comptes", "📊 Audit Logs", "⚙️ Système", "🚪 Quitter"])
    
    if adm_m == "👥 Gestion Comptes":
        with sqlite3.connect(DB_FILE) as conn:
            users = conn.execute("SELECT uid, name, status FROM users WHERE uid != 'admin'").fetchall()
            for uid, name, stat in users:
                with st.expander(f"👤 {name} ({uid}) - {stat}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("✅ ACTIVER", key=f"a_{uid}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (uid,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (uid, name, uid))
                        conn.commit(); st.rerun()
                    if c2.button("🚫 BLOQUER", key=f"b_{uid}"):
                        conn.execute("UPDATE users SET status='INACTIF' WHERE uid=?", (uid,)); conn.commit(); st.rerun()
                    if c3.button("🗑️ SUPPRIMER", key=f"s_{uid}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (uid,)); conn.commit(); st.rerun()

    elif adm_m == "📊 Audit Logs":
        with sqlite3.connect(DB_FILE) as conn:
            st.table(pd.read_sql("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50", conn))

    elif adm_m == "⚙️ Système":
        with st.form("sys"):
            na = st.text_input("Nom App", APP_NAME)
            ma = st.text_area("Marquee", MARQUEE_TEXT)
            if st.form_submit_button("SAUVER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=? WHERE id=1", (na, ma))
                    conn.commit(); st.rerun()

    if adm_m == "🚪 Quitter": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. BOUTIQUE (LOGIQUE ROBUSTE)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    r_sh = conn.execute("SELECT name, rate, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = r_sh if r_sh else ("MA BOUTIQUE", 2800.0, "ADRESSE", "000")

nav = ["🏠 ACCUEIL", "🛒 VENTES", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav = ["🏠 ACCUEIL", "🛒 VENTES", "📉 DETTES", "📊 RAPPORTS", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-box'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav)

# --- 8.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:80px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        ca = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        st.markdown(f"<div class='cobalt-box'><h2>RECETTE JOUR</h2><h1>{ca:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 8.2 VENTES ---
elif choice == "🛒 VENTES":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown("<div class='facture-print'>", unsafe_allow_html=True)
        st.markdown(f"<h3>{sh_inf[0]}</h3><p>{sh_inf[2]}<br>Tél: {sh_inf[3]}</p><hr>", unsafe_allow_html=True)
        st.markdown(f"<b>N°: {inv['ref']}</b><br>Client: {inv['cli']}<br>Date: {inv['date']}<hr>", unsafe_allow_html=True)
        for it, d in inv['items'].items():
            st.markdown(f"{it} x{d['q']} = {d['q']*d['p']}$<br>", unsafe_allow_html=True)
        st.markdown(f"<hr><b>TOTAL: {inv['total_val']} {inv['dev']}</b>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button("💾 ENREGISTRER (.TXT)", f"FAC {inv['ref']}\nTOTAL: {inv['total_val']}", f"FAC_{inv['ref']}.txt")
        if st.button("⬅️ RETOUR"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel = st.selectbox("CHOISIR ARTICLE", ["---"] + [p[0] for p in prods])
            if sel != "---" and st.button("➕ AJOUTER"):
                p_dat = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (sel, sid)).fetchone()
                st.session_state.session['cart'][sel] = {'p': p_dat[0], 'q': 1, 'max': p_dat[1]}; st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='cart-white'>", unsafe_allow_html=True)
            total_u = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c1, c2, c3 = st.columns([3, 1, 1])
                nq = c2.number_input(f"Qté", 1, d['max'], d['q'], key=f"q_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                total_u += d['p'] * nq
                c1.write(f"**{art}**")
                if c3.button("🗑️", key=f"r_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            p_fin = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='neon-total'><h1>{p_fin:,.2f} {devise}</h1></div>", unsafe_allow_html=True)
            with st.form("pay"):
                cli = st.text_input("CLIENT", "COMPTANT").upper()
                rec = st.number_input(f"REÇU ({devise})", value=float(p_fin))
                if st.form_submit_button("✅ VALIDER"):
                    ref = f"F-{random.randint(100,999)}"
                    r_u = rec if devise == "USD" else rec / sh_inf[1]
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, cli, total_u, r_u, total_u-r_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if (total_u - r_u) > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_payment) VALUES (?,?,?,?,?)", (cli, total_u-r_u, ref, sid, datetime.now().strftime("%d/%m/%Y")))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': cli, 'total_val': p_fin, 'dev': devise, 'paid': rec, 'rest': p_fin-rec, 'items': st.session_state.session['cart'], 'date': datetime.now().strftime("%d/%m/%Y")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK ---
elif choice == "📦 STOCK":
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Nouveau"])
    with tab1:
        with sqlite3.connect(DB_FILE) as conn:
            items = conn.execute("SELECT id, item, qty, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
            for i_id, i_n, i_q, i_p in items:
                with st.expander(f"{i_n} (Stock: {i_q})"):
                    nq = st.number_input("Maj Stock", value=i_q, key=f"mq_{i_id}")
                    np = st.number_input("Maj Prix $", value=i_p, key=f"mp_{i_id}")
                    if st.button("SAUVER", key=f"sb_{i_id}"):
                        conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (nq, np, i_id))
                        conn.commit(); st.rerun()
    with tab2:
        with st.form("add"):
            n, pa, pv, q = st.text_input("Désignation"), st.number_input("Prix Achat $"), st.number_input("Prix Vente $"), st.number_input("Qté", 1)
            if st.form_submit_button("AJOUTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n.upper(), q, pa, pv, sid))
                    conn.commit(); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    with sqlite3.connect(DB_FILE) as conn:
        dts = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for di, dc, db in dts:
            with st.expander(f"👤 {dc} - {db}$"):
                v = st.number_input("Versement $", max_value=db, key=f"pay_{di}")
                if st.button("VALIDER", key=f"bp_{di}"):
                    nb = db - v
                    conn.execute("UPDATE debts SET balance=? WHERE id=?", (nb, di))
                    if nb <= 0.01: conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 8.5 RAPPORTS & GRAPHIQUES ---
elif choice == "📊 RAPPORTS":
    st.header("📊 ANALYSE")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT date, total_usd, seller FROM sales WHERE sid='{sid}'", conn)
        if not df.empty and PLOTLY_AVAILABLE:
            fig = px.bar(df.groupby("date").sum().reset_index(), x="date", y="total_usd", title="Ventes par Jour ($)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.table(df)

# --- 8.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    if st.session_state.session['role'] == "GERANT":
        with st.form("staff"):
            uid, nm, pw = st.text_input("ID"), st.text_input("Nom"), st.text_input("Pass", type="password")
            if st.form_submit_button("CRÉER"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (uid.lower(), get_hash(pw), 'VENDEUR', sid, 'ACTIF', nm, ''))
                        conn.commit(); st.success("Vendeur ajouté !")
                    except: st.error("ID utilisé.")

# --- 8.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    with st.form("cfg"):
        n = st.text_input("Nom Boutique", sh_inf[0])
        r = st.number_input("Taux de Change", value=sh_inf[1])
        if st.form_submit_button("SAUVER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=? WHERE sid=?", (n, r, sid))
                conn.commit(); st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()
