# ==============================================================================
# ANASH ERP v6001 - SYSTÈME DE GESTION TITAN (ÉDITION BALIKA BUSINESS)
# ------------------------------------------------------------------------------
# FUSION TOTALE | VALIDATION ADMIN | TEXTE BLANC INTÉGRAL | AUCUNE SUPPRESSION
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import random
import io
import os
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION ESTHÉTIQUE & STYLE CSS (COBALT & WHITE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ANASH ERP v6001",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_titan_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');

    /* Fond d'écran Cobalt Master */
    .stApp {
        background: linear-gradient(160deg, #001a33 0%, #000d1a 100%) !important;
        color: #ffffff !important;
    }

    /* FORÇAGE TEXTE BLANC (Correction pour textes gris) */
    p, span, label, div, h1, h2, h3, small, b, .stMarkdown { 
        color: #ffffff !important; 
    }
    
    /* Correction spécifique pour les widgets Streamlit qui restent gris */
    .stSelectbox label, .stTextInput label, .stNumberInput label { color: white !important; }

    /* MESSAGE DÉFILANT CSS ULTRA FLUIDE */
    .marquee-host {
        position: fixed; top: 0; left: 0; width: 100%; background: #000000;
        color: #00ff00; z-index: 99999; height: 50px; display: flex;
        align-items: center; border-bottom: 3px solid #0044ff;
        box-shadow: 0 5px 15px rgba(0,0,0,0.8);
    }
    .marquee-text {
        white-space: nowrap; display: inline-block;
        animation: titan-scroll 45s linear infinite; font-size: 20px;
        font-weight: bold; font-family: 'Roboto Mono', monospace;
        text-transform: uppercase;
        color: #00ff00 !important; /* On garde le vert pour le défilement */
    }
    @keyframes titan-scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* DASHBOARD CLOCK (80MM MOBILE STYLE) */
    .titan-clock-container {
        background: rgba(0, 85, 255, 0.1); backdrop-filter: blur(20px);
        border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 50px;
        padding: 70px 20px; text-align: center; margin: 70px auto; 
        max-width: 900px; box-shadow: 0 30px 60px rgba(0,0,0,0.6);
    }
    .titan-time {
        font-family: 'Orbitron', sans-serif; font-size: 120px; font-weight: 900;
        color: #ffffff !important; text-shadow: 0 0 40px #0088ff; line-height: 1; margin: 0;
    }
    .titan-date {
        font-size: 30px; color: #00d9ff !important; text-transform: uppercase;
        letter-spacing: 6px; margin-top: 20px; font-weight: 300;
    }

    /* PANNEAUX D'AFFICHAGE COBALT */
    .cobalt-card {
        background: #0044ff !important; padding: 35px; border-radius: 30px;
        border-left: 12px solid #00d9ff; margin-bottom: 25px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4); transition: transform 0.3s;
    }
    .cobalt-card:hover { transform: translateY(-5px); }

    /* CADRE NÉON TOTAL PANIER */
    .neon-frame-box {
        background: #000000 !important; border: 8px solid #00ff00 !important;
        color: #00ff00 !important; padding: 50px; border-radius: 40px;
        text-align: center; margin: 40px 0; box-shadow: 0 0 50px rgba(0, 255, 0, 0.4);
    }
    .neon-price { font-family: 'Orbitron', sans-serif; font-size: 75px; font-weight: 900; color: #00ff00 !important; }

    /* BOUTONS XXL POUR ÉCRAN TACTILE */
    .stButton > button {
        width: 100% !important; height: 95px !important;
        background: linear-gradient(135deg, #0055ff, #002288) !important;
        color: white !important; border-radius: 25px !important;
        font-size: 26px !important; font-weight: 800 !important;
        border: 3px solid #ffffff !important; text-transform: uppercase;
        box-shadow: 0 12px 25px rgba(0,0,0,0.5);
    }

    /* INPUTS & SELECTS FORM */
    input, select, textarea {
        background-color: #ffffff !important; color: #000000 !important;
        border-radius: 18px !important; padding: 18px !important;
        font-size: 20px !important; border: 4px solid #0044ff !important;
    }

    /* STRUCTURE SIDEBAR BLANCHE */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important; border-right: 6px solid #0044ff;
    }
    [data-testid="stSidebar"] * { color: #000000 !important; font-weight: 900; }

    /* STYLES FACTURES (Doivent rester noir sur blanc pour impression) */
    .receipt-80mm, .receipt-A4-admin, .receipt-80mm *, .receipt-A4-admin * {
        background: white !important; color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. CORE DATABASE ENGINE
# ------------------------------------------------------------------------------
DB_FILE = "anash_v6001_titan.db"

def db_query(sql, params=(), is_select=True):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        if is_select:
            return cursor.fetchall()
        return None

def titan_init_db():
    db_query("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, 
        status TEXT, name TEXT, tel TEXT, created_at TEXT)""", is_select=False)
    db_query("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL, 
        head TEXT, addr TEXT, tel TEXT, logo BLOB)""", is_select=False)
    db_query("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
        buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""", is_select=False)
    db_query("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, 
        tot REAL, pay REAL, res REAL, date TEXT, time TEXT, 
        seller TEXT, sid TEXT, data TEXT, currency TEXT)""", is_select=False)
    db_query("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, bal REAL, 
        ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_update TEXT)""", is_select=False)
    db_query("CREATE TABLE IF NOT EXISTS sys_config (id INTEGER PRIMARY KEY, marquee_text TEXT)", is_select=False)

    if not db_query("SELECT uid FROM users WHERE uid='admin'"):
        hpwd = hashlib.sha256("admin123".encode()).hexdigest()
        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                ('admin', hpwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR TITAN', '000', '2026-01-17'), is_select=False)
    
    if not db_query("SELECT id FROM sys_config"):
        db_query("INSERT INTO sys_config VALUES (1, 'BIENVENUE SUR ANASH ERP v6001 - GESTION TITAN POUR BALIKA BUSINESS')", is_select=False)

titan_init_db()

# ------------------------------------------------------------------------------
# 3. ÉTAT DE LA SESSION
# ------------------------------------------------------------------------------
if 'titan_session' not in st.session_state:
    st.session_state.titan_session = {
        'logged': False, 'uid': None, 'role': None, 'shop': None,
        'cart': {}, 'last_inv': None, 'view': 'home'
    }

inject_titan_ui()
marquee_val = db_query("SELECT marquee_text FROM sys_config WHERE id=1")[0][0]
st.markdown(f'<div class="marquee-host"><div class="marquee-text">{marquee_val}</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS
# ------------------------------------------------------------------------------
if not st.session_state.titan_session['logged']:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    _, login_box, _ = st.columns([1, 2, 1])
    
    with login_box:
        st.markdown("<div class='titan-clock-container'><h1 class='titan-time'>ANASH ERP</h1></div>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["🔒 ACCÈS SYSTÈME", "📝 NOUVEAU GÉRANT"])
        
        with tab_in:
            u_input = st.text_input("Identifiant").lower().strip()
            p_input = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER"):
                user_check = db_query("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_input,))
                if user_check:
                    stored_p, s_role, s_shop, s_stat = user_check[0]
                    if hashlib.sha256(p_input.encode()).hexdigest() == stored_p:
                        if s_stat == "ACTIF":
                            st.session_state.titan_session.update({'logged': True, 'uid': u_input, 'role': s_role, 'shop': s_shop})
                            st.rerun()
                        else: st.error("❌ COMPTE INACTIF : Veuillez contacter l'Administrateur pour validation.")
                    else: st.error("Mot de passe incorrect.")
                else: st.error("Utilisateur non enregistré.")

        with tab_up:
            with st.form("reg_form"):
                reg_uid = st.text_input("ID Utilisateur souhaité").lower()
                reg_nam = st.text_input("Nom Complet du Gérant")
                reg_tel = st.text_input("Numéro Téléphone")
                reg_pwd = st.text_input("Mot de passe secret", type="password")
                if st.form_submit_button("CRÉER MON COMPTE"):
                    if db_query("SELECT uid FROM users WHERE uid=?", (reg_uid,)):
                        st.error("Cet ID est déjà utilisé.")
                    else:
                        h_pwd = hashlib.sha256(reg_pwd.encode()).hexdigest()
                        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                                (reg_uid, h_pwd, 'GERANT', 'EN_ATTENTE', 'INACTIF', reg_nam, reg_tel, str(datetime.now())), is_select=False)
                        st.success("✅ Demande envoyée ! L'Admin doit maintenant ACTIVER votre bouton.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN (MODIFICATION USERS & LOGS)
# ------------------------------------------------------------------------------
if st.session_state.titan_session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛠️ TITAN ADMIN")
    adm_nav = st.sidebar.radio("Navigation", ["Gérer les Comptes", "Configuration Système", "Déconnexion"])
    
    if adm_nav == "Gérer les Comptes":
        st.header("👥 VALIDATION DES ACCÈS")
        all_u = db_query("SELECT uid, name, tel, status, role FROM users WHERE uid != 'admin'")
        for u, n, t, s, r in all_u:
            with st.container():
                st.markdown(f"<div class='cobalt-card'><h3>{n} (@{u})</h3><p>📞 {t} | Rôle: {r} | Statut actuel: <b>{s}</b></p></div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button(f"✅ ACTIVER {u}", key=f"ac_{u}"):
                    db_query("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (u, u), is_select=False); st.rerun()
                if c2.button(f"🚫 BLOQUER {u}", key=f"bl_{u}"):
                    db_query("UPDATE users SET status='BLOQUE' WHERE uid=?", (u,), is_select=False); st.rerun()
                if c3.button(f"🗑️ SUPPRIMER {u}", key=f"de_{u}"):
                    db_query("DELETE FROM users WHERE uid=?", (u,), is_select=False); st.rerun()

    elif adm_nav == "Configuration Système":
        st.header("📢 MESSAGE DÉFILANT")
        new_m = st.text_area("Texte du Marquee", marquee_val)
        if st.button("SAUVEGARDER"):
            db_query("UPDATE sys_config SET marquee_text=? WHERE id=1", (new_m,), is_select=False); st.rerun()

    if adm_nav == "Déconnexion": st.session_state.titan_session['logged'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR
# ------------------------------------------------------------------------------
sid = st.session_state.titan_session['shop']
shop_raw = db_query("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,))
s_inf = shop_raw[0] if shop_raw else ("BOUTIQUE BALIKA", 2800.0, "BIENVENUE", "ADRESSE", "000")

if st.session_state.titan_session['role'] == "GERANT":
    menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 GESTION STOCK", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div style='background:#0044ff; color:white; padding:20px; border-radius:15px; text-align:center;'>🏪 {s_inf[0]}<br>👤 {st.session_state.titan_session['uid'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU TITAN", menu)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='titan-clock-container'>
        <p class='titan-time'>{datetime.now().strftime('%H:%M')}</p>
        <p class='titan-date'>{datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    t_date = datetime.now().strftime("%d/%m/%Y")
    day_rev = db_query("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (sid, t_date))[0][0] or 0
    st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h2>RECETTE DU JOUR</h2><h1 style='font-size:70px;'>{day_rev:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.titan_session['last_inv']:
        st.header("🛒 TERMINAL DE VENTE")
        c1, c2 = st.columns([2, 1])
        with c2:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            cur = st.radio("DEVISE", ["USD", "CDF"], horizontal=True)
            tx = s_inf[1]
            st.markdown("</div>", unsafe_allow_html=True)
        with c1:
            stock_items = db_query("SELECT item, sell_price, qty FROM stock WHERE sid=?", (sid,))
            st_map = {r[0]: (r[1], r[2]) for r in stock_items}
            search = st.selectbox("🔍 RECHERCHER UN PRODUIT", ["---"] + list(st_map.keys()))
            if search != "---" and st_map[search][1] > 0:
                if st.button("➕ AJOUTER"):
                    st.session_state.titan_session['cart'][search] = st.session_state.titan_session['cart'].get(search, 0) + 1
                    st.toast(f"{search} ajouté")

        if st.session_state.titan_session['cart']:
            st.divider()
            total_cart = 0.0; cart_rows = []
            for item, qty in list(st.session_state.titan_session['cart'].items()):
                p_u = st_map[item][0] if cur == "USD" else st_map[item][0] * tx
                cx, cq, cr = st.columns([3, 2, 1])
                new_q = cq.number_input(f"Qté {item}", min_value=1, max_value=st_map[item][1], value=qty, key=f"q_{item}")
                st.session_state.titan_session['cart'][item] = new_q
                sub = p_u * new_q
                total_cart += sub
                cart_rows.append({"n": item, "q": new_q, "p": p_u, "s": sub})
                cx.markdown(f"**{item}**")
                if cr.button("🗑️", key=f"rm_{item}"):
                    del st.session_state.titan_session['cart'][item]; st.rerun()

            st.markdown(f"<div class='neon-frame-box'><div class='neon-price'>{total_cart:,.2f} {cur}</div></div>", unsafe_allow_html=True)
            with st.form("pay_form"):
                cli_nam = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                amount_p = st.number_input(f"MONTANT REÇU ({cur})", value=float(total_cart))
                if st.form_submit_button("🚀 VALIDER & IMPRIMER"):
                    ref_f = f"FAC-{random.randint(10000, 99999)}"
                    d, t = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    t_usd = total_cart if cur == "USD" else total_cart / tx
                    p_usd = amount_p if cur == "USD" else amount_p / tx
                    r_usd = t_usd - p_usd
                    db_query("INSERT INTO sales (ref, cli, tot, pay, res, date, time, seller, sid, data, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (ref_f, cli_nam, t_usd, p_usd, r_usd, d, t, st.session_state.titan_session['uid'], sid, json.dumps(cart_rows), cur), is_select=False)
                    for row in cart_rows:
                        db_query("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (row['q'], row['n'], sid), is_select=False)
                    if r_usd > 0.01:
                        db_query("INSERT INTO debts (cli, bal, ref, sid, last_update) VALUES (?,?,?,?,?)", (cli_nam, r_usd, ref_f, sid, d), is_select=False)
                    st.session_state.titan_session['last_inv'] = {"ref": ref_f, "cli": cli_nam, "tot": total_cart, "pay": amount_p, "res": total_cart-amount_p, "dev": cur, "items": cart_rows, "d": d, "t": t}
                    st.session_state.titan_session['cart'] = {}; st.rerun()
    else:
        inv = st.session_state.titan_session['last_inv']
        fmt = st.radio("SÉLECTIONNER LE FORMAT :", ["TICKET CAISSE (80mm)", "ADMINISTRATIVE (A4)"], horizontal=True)
        if fmt == "TICKET CAISSE (80mm)":
            st.markdown(f"<div class='receipt-80mm'><h3 style='text-align:center;'>{s_inf[0]}</h3><p>N°: {inv['ref']}<br>CLIENT: {inv['cli']}<br>TOTAL: {inv['tot']:,.2f} {inv['dev']}</p></div>", unsafe_allow_html=True)
        if st.button("⬅️ RETOUR"): st.session_state.titan_session['last_inv'] = None; st.rerun()

# --- 6.3 GESTION STOCK ---
elif choice == "📦 GESTION STOCK":
    st.header("📦 INVENTAIRE")
    st_data = db_query("SELECT id, item, qty, buy_price, sell_price, category FROM stock WHERE sid=?", (sid,))
    if st_data:
        df_st = pd.DataFrame(st_data, columns=["ID", "DÉSIGNATION", "QTÉ", "P. ACHAT ($)", "P. VENTE ($)", "CATÉGORIE"])
        st.dataframe(df_st, use_container_width=True, hide_index=True)
    with st.form("stock_titan"):
        f_nam = st.text_input("Désignation").upper()
        f_qty = st.number_input("Quantité", min_value=0)
        f_sel = st.number_input("Prix Vente USD", min_value=0.0)
        if st.form_submit_button("💾 ENREGISTRER"):
            db_query("INSERT INTO stock (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (f_nam, f_qty, 0, f_sel, sid), is_select=False); st.rerun()

# --- 6.4 SUIVI DETTES ---
elif choice == "📉 SUIVI DETTES":
    st.header("📉 CLIENTS DÉBITEURS")
    dettes_list = db_query("SELECT id, cli, bal, ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,))
    for d_id, d_cli, d_bal, d_ref in dettes_list:
        st.markdown(f"<div class='cobalt-card'><h3>👤 {d_cli}</h3><p>Reste : <b>{d_bal:,.2f} $</b></p></div>", unsafe_allow_html=True)
        if st.button(f"SOLDER {d_id}"):
            db_query("UPDATE debts SET bal=0, status='PAYE' WHERE id=?", (d_id,), is_select=False); st.rerun()

# --- 6.5 RAPPORTS VENTES ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 ANALYSE")
    r_date = st.date_input("Date", datetime.now()).strftime("%d/%m/%Y")
    sales_rep = db_query("SELECT ref, cli, tot, time FROM sales WHERE sid=? AND date=?", (sid, r_date))
    if sales_rep:
        st.table(pd.DataFrame(sales_rep, columns=["REF", "CLIENT", "TOTAL", "HEURE"]))

# --- 6.8 DÉCONNEXION ---
elif choice == "🚪 QUITTER":
    st.session_state.titan_session['logged'] = False; st.rerun()
