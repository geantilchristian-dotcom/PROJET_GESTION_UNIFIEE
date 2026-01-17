# ==============================================================================
# ANASH ERP v6002 - SYSTÈME DE GESTION TITAN (ÉDITION BALIKA BUSINESS)
# ------------------------------------------------------------------------------
# FUSION TOTALE | FACTURES NORMÉES (A4 & 80mm) | PANIER NOIR SUR BLANC
# ------------------------------------------------------------------------------

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
# 1. CONFIGURATION ESTHÉTIQUE & STYLE CSS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ANASH ERP v6002",
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

    /* FORÇAGE TEXTE BLANC (Hors Panier et Factures) */
    p, span, label, div, h1, h2, h3, small, b, .stMarkdown { 
        color: #ffffff !important; 
    }
    
    /* STYLE PANIER : NOIR SUR BLANC (Votre demande) */
    .cart-container {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 20px;
        border-radius: 20px;
        border: 4px solid #00d9ff;
    }
    .cart-container * {
        color: #000000 !important;
        font-weight: bold !important;
    }

    .marquee-host {
        position: fixed; top: 0; left: 0; width: 100%; background: #000000;
        color: #00ff00; z-index: 99999; height: 50px; display: flex;
        align-items: center; border-bottom: 3px solid #0044ff;
    }
    .marquee-text {
        white-space: nowrap; display: inline-block;
        animation: titan-scroll 45s linear infinite; font-size: 20px;
        font-weight: bold; font-family: 'Roboto Mono', monospace;
        color: #00ff00 !important;
    }
    @keyframes titan-scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* FACTURE 80mm AUX NORMES */
    .receipt-80mm-pro {
        background: white !important; color: black !important; padding: 15px;
        font-family: 'Courier New', monospace; width: 80mm; margin: auto;
        border: 1px solid #000; font-size: 13px; line-height: 1.1;
    }
    .receipt-80mm-pro * { color: black !important; }
    .dashed-line { border-top: 1px dashed black; margin: 5px 0; }

    /* FACTURE A4 AUX NORMES */
    .receipt-A4-pro {
        background: white !important; color: black !important; padding: 50px;
        font-family: 'Arial', sans-serif; width: 210mm; min-height: 297mm;
        margin: auto; border: 1px solid #ddd;
    }
    .receipt-A4-pro * { color: black !important; }
    .table-a4-pro { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .table-a4-pro th { background: #f0f0f0; border: 1px solid black; padding: 10px; text-align: left; }
    .table-a4-pro td { border: 1px solid black; padding: 10px; }

    .cobalt-card {
        background: #0044ff !important; padding: 35px; border-radius: 30px;
        border-left: 12px solid #00d9ff; margin-bottom: 25px;
    }
    .neon-frame-box {
        background: #000000 !important; border: 8px solid #00ff00 !important;
        color: #00ff00 !important; padding: 30px; border-radius: 40px; text-align: center;
    }
    .stButton > button {
        width: 100% !important; height: 80px !important;
        background: linear-gradient(135deg, #0055ff, #002288) !important;
        color: white !important; border-radius: 20px !important;
        font-size: 22px !important; font-weight: 800 !important;
    }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 6px solid #0044ff; }
    [data-testid="stSidebar"] * { color: #000000 !important; font-weight: 900; }

    @media print {
        .no-print { display: none !important; }
        .stApp { background: white !important; }
        .receipt-80mm-pro, .receipt-A4-pro { border: none !important; box-shadow: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. CORE DATABASE ENGINE
# ------------------------------------------------------------------------------
DB_FILE = "anash_v6002_titan.db"

def db_query(sql, params=(), is_select=True):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        if is_select: return cursor.fetchall()
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
        db_query("INSERT INTO sys_config VALUES (1, 'BIENVENUE SUR ANASH ERP v6002 - BALIKA BUSINESS')", is_select=False)

titan_init_db()

# ------------------------------------------------------------------------------
# 3. ÉTAT DE LA SESSION
# ------------------------------------------------------------------------------
if 'titan_session' not in st.session_state:
    st.session_state.titan_session = {'logged': False, 'uid': None, 'role': None, 'shop': None, 'cart': {}, 'last_inv': None}

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
        st.markdown("<h1 style='text-align:center;'>🔐 CONNEXION</h1>", unsafe_allow_html=True)
        u_input = st.text_input("Identifiant").lower().strip()
        p_input = st.text_input("Mot de passe", type="password")
        if st.button("DÉVERROUILLER"):
            user_check = db_query("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_input,))
            if user_check and hashlib.sha256(p_input.encode()).hexdigest() == user_check[0][0]:
                if user_check[0][3] == "ACTIF":
                    st.session_state.titan_session.update({'logged': True, 'uid': u_input, 'role': user_check[0][1], 'shop': user_check[0][2]})
                    st.rerun()
                else: st.error("Compte inactif. Contactez l'Admin.")
            else: st.error("Accès refusé.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.titan_session['role'] == "SUPER_ADMIN":
    st.sidebar.title("ADMIN")
    adm_nav = st.sidebar.radio("Actions", ["Utilisateurs", "Déconnexion"])
    if adm_nav == "Utilisateurs":
        all_u = db_query("SELECT uid, name, status FROM users WHERE uid != 'admin'")
        for u, n, s in all_u:
            st.write(f"**{n}** (@{u}) - Statut: {s}")
            c1, c2, c3 = st.columns(3)
            if c1.button(f"ACTIVER {u}"): db_query("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (u, u), is_select=False); st.rerun()
            if c2.button(f"BLOQUER {u}"): db_query("UPDATE users SET status='INACTIF' WHERE uid=?", (u,), is_select=False); st.rerun()
            if c3.button(f"SUPPRIMER {u}"): db_query("DELETE FROM users WHERE uid=?", (u,), is_select=False); st.rerun()
    if adm_nav == "Déconnexion": st.session_state.titan_session['logged'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR
# ------------------------------------------------------------------------------
sid = st.session_state.titan_session['shop']
shop_raw = db_query("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,))
s_inf = shop_raw[0] if shop_raw else ("BALIKA BUSINESS", 2800.0, "BIENVENUE", "ADRESSE", "000")

menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]
choice = st.sidebar.radio("MENU", menu)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h1>BIENVENUE</h1><h2>{s_inf[0]}</h2></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (PANIER BLANC / TEXTE NOIR) ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.titan_session['last_inv']:
        st.header("🛒 TERMINAL DE VENTE")
        cur = st.radio("DEVISE", ["USD", "CDF"], horizontal=True)
        tx = s_inf[1]
        
        stock_items = db_query("SELECT item, sell_price, qty FROM stock WHERE sid=?", (sid,))
        st_map = {r[0]: (r[1], r[2]) for r in stock_items}
        search = st.selectbox("RECHERCHE", ["---"] + list(st_map.keys()))
        if search != "---" and st.button("AJOUTER"):
            st.session_state.titan_session['cart'][search] = st.session_state.titan_session['cart'].get(search, 0) + 1

        if st.session_state.titan_session['cart']:
            st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
            total_cart = 0.0; cart_rows = []
            for item, qty in list(st.session_state.titan_session['cart'].items()):
                p_u = st_map[item][0] if cur == "USD" else st_map[item][0] * tx
                c_q1, c_q2, c_q3 = st.columns([3, 2, 1])
                new_q = c_q2.number_input(f"Qté {item}", 1, st_map[item][1], qty, key=f"q_{item}")
                st.session_state.titan_session['cart'][item] = new_q
                sub = p_u * new_q
                total_cart += sub
                cart_rows.append({"n": item, "q": new_q, "p": p_u, "s": sub})
                c_q1.write(f"{item} ({p_u:,.2f})")
                if c_q3.button("🗑️", key=f"rm_{item}"): del st.session_state.titan_session['cart'][item]; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"<div class='neon-frame-box'><h2>TOTAL : {total_cart:,.2f} {cur}</h2></div>", unsafe_allow_html=True)
            
            with st.form("pay_f"):
                cli = st.text_input("CLIENT", "COMPTANT")
                pay = st.number_input(f"REÇU ({cur})", value=float(total_cart))
                if st.form_submit_button("VALIDER LA VENTE"):
                    ref_f = f"FAC-{random.randint(100, 999)}"
                    d, t = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    t_usd = total_cart if cur == "USD" else total_cart / tx
                    p_usd = pay if cur == "USD" else pay / tx
                    db_query("INSERT INTO sales (ref, cli, tot, pay, res, date, time, seller, sid, data, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (ref_f, cli, t_usd, p_usd, t_usd-p_usd, d, t, st.session_state.titan_session['uid'], sid, json.dumps(cart_rows), cur), is_select=False)
                    for row in cart_rows: db_query("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (row['q'], row['n'], sid), is_select=False)
                    st.session_state.titan_session['last_inv'] = {"ref": ref_f, "cli": cli, "tot": total_cart, "pay": pay, "res": total_cart-pay, "dev": cur, "items": cart_rows, "d": d, "t": t}
                    st.session_state.titan_session['cart'] = {}; st.rerun()
    else:
        # --- FACTURATION AUX NORMES (A4 & 80mm) ---
        inv = st.session_state.titan_session['last_inv']
        fmt = st.radio("FORMAT DE FACTURE", ["TICKET 80mm", "ADMINISTRATIF A4"], horizontal=True)
        
        if fmt == "TICKET 80mm":
            st.markdown(f"""
            <div class='receipt-80mm-pro'>
                <center><b>{s_inf[0]}</b><br>{s_inf[3]}<br>Tél: {s_inf[4]}</center>
                <div class='dashed-line'></div>
                N°: {inv['ref']}<br>Date: {inv['d']} {inv['t']}<br>Cli: {inv['cli']}
                <div class='dashed-line'></div>
                {"".join([f"<div style='display:flex; justify-content:space-between;'><span>{x['n']} x{x['q']}</span><span>{x['s']:,.0f}</span></div>" for x in inv['items']])}
                <div class='dashed-line'></div>
                <div style='display:flex; justify-content:space-between; font-weight:bold;'><span>TOTAL</span><span>{inv['tot']:,.2f} {inv['dev']}</span></div>
                <div style='display:flex; justify-content:space-between;'><span>Payé</span><span>{inv['pay']:,.2f}</span></div>
                <div style='display:flex; justify-content:space-between;'><span>Reste</span><span>{inv['res']:,.2f}</span></div>
                <div class='dashed-line'></div>
                <center>{s_inf[2]}<br>ANASH ERP v6002</center>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='receipt-A4-pro'>
                <table style='width:100%'><tr>
                    <td><h1 style='color:#0044ff;'>{s_inf[0]}</h1><p>{s_inf[3]}<br>{s_inf[4]}</p></td>
                    <td style='text-align:right;'><h2>FACTURE</h2><p>N° {inv['ref']}<br>Date: {inv['d']}</p></td>
                </tr></table>
                <hr><p><b>DOIT :</b> {inv['cli']}</p>
                <table class='table-a4-pro'>
                    <tr><th>DÉSIGNATION</th><th>QTÉ</th><th>P.U</th><th>TOTAL</th></tr>
                    {"".join([f"<tr><td>{x['n']}</td><td>{x['q']}</td><td>{x['p']:,.2f}</td><td>{x['s']:,.2f}</td></tr>" for x in inv['items']])}
                    <tr style='font-weight:bold;'><td colspan='3' style='text-align:right;'>TOTAL GÉNÉRAL ({inv['dev']})</td><td>{inv['tot']:,.2f}</td></tr>
                </table>
                <div style='margin-top:30px; text-align:right;'>
                    <p>Net à payer : {inv['tot']:,.2f} {inv['dev']}</p>
                    <p>Somme payée : {inv['pay']:,.2f} {inv['dev']}</p>
                    <p>Reste : {inv['res']:,.2f} {inv['dev']}</p>
                </div>
                <table style='width:100%; margin-top:80px;'><tr>
                    <td style='text-align:center;'>Signature du Client<br><br>________________</td>
                    <td style='text-align:center;'>Le Gérant & Cachet<br><br>________________</td>
                </tr></table>
            </div>
            """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("⬅️ RETOUR"): st.session_state.titan_session['last_inv'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# --- 6.3 STOCK ---
elif choice == "📦 STOCK":
    st.header("📦 INVENTAIRE")
    with st.form("st_f"):
        n = st.text_input("Désignation").upper()
        q = st.number_input("Qté", 0)
        p = st.number_input("Prix Vente USD", 0.0)
        if st.form_submit_button("SAUVEGARDER"):
            db_query("INSERT INTO stock (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n, q, 0, p, sid), is_select=False); st.rerun()
    st_data = db_query("SELECT id, item, qty, sell_price FROM stock WHERE sid=?", (sid,))
    st.table(pd.DataFrame(st_data, columns=["ID", "NOM", "QTÉ", "PRIX"]))

# --- 6.8 DÉCONNEXION ---
elif choice == "🚪 QUITTER":
    st.session_state.titan_session['logged'] = False; st.rerun()
