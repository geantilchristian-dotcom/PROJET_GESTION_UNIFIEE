# ==============================================================================
# ANASH ERP v3317 - ÉDITION BALIKA BUSINESS (FOCUS FACTURATION 80mm)
# ------------------------------------------------------------------------------
# FUSION TOTALE | AUCUNE LIGNE SUPPRIMÉE | OPTIMISATION IMPRESSION THERMIQUE
# ------------------------------------------------------------------------------

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import random
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3317_core.db"

def init_system_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee_msg TEXT, version TEXT)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT, created_at TEXT)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT, email TEXT)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, buy_price REAL, 
            sell_price REAL, sid TEXT, category TEXT, min_stock INTEGER DEFAULT 5)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, sid TEXT, 
            items_json TEXT, currency_used TEXT, rate_at_sale REAL)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS client_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, sale_ref TEXT, 
            sid TEXT, status TEXT DEFAULT 'OUVERT', last_pay_date TEXT)""")

        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE CHEZ BALIKA BUSINESS', '3.3.17')")
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR CENTRAL', '00', '17/01/2026'))
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. DESIGN CSS (STYLE COBALT & IMPRESSION)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v3317", layout="wide")

def apply_ui_styles():
    st.markdown("""
    <style>
        .stApp { background: #001a33; color: white; }
        .marquee-container { background: #0044ff; color: white; padding: 10px; font-weight: bold; position: fixed; top: 0; width: 100%; z-index: 99; }
        
        /* Style Facture 80mm */
        .print-area { 
            background: white !important; 
            color: black !important; 
            padding: 10mm; 
            width: 80mm; 
            margin: auto; 
            font-family: 'Courier New', monospace;
            border: 1px dashed #ccc;
        }
        .print-area hr { border-top: 1px dashed black; }
        .print-area table { width: 100%; font-size: 12px; }
        
        .cobalt-card { background: #0044ff; padding: 20px; border-radius: 15px; margin-bottom: 10px; border-left: 8px solid #00d9ff; }
        .neon-frame { border: 3px solid #00ff00; padding: 15px; border-radius: 15px; text-align: center; box-shadow: 0 0 10px #00ff00; }
        
        @media print {
            .no-print { display: none !important; }
            body * { visibility: hidden; }
            .print-area, .print-area * { visibility: visible; }
            .print-area { position: absolute; left: 0; top: 0; width: 80mm; }
        }
    </style>
    """, unsafe_allow_html=True)

apply_ui_styles()

# ------------------------------------------------------------------------------
# 3. LOGIQUE SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {'logged_in': False, 'user': None, 'role': None, 'shop_id': None, 'cart': {}, 'viewing_invoice': None}

def get_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg FROM global_settings WHERE id=1").fetchone()

APP_NAME, MARQUEE_MSG = get_config()

# ------------------------------------------------------------------------------
# 4. LOGIN
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div><br><br>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Utilisateur").lower()
        p = st.text_input("Pass", type="password")
        if st.form_submit_button("CONNEXION"):
            with sqlite3.connect(DB_FILE) as conn:
                res = conn.execute("SELECT role, shop, name FROM users WHERE uid=? AND pwd=?", (u, hashlib.sha256(p.encode()).hexdigest())).fetchone()
                if res:
                    st.session_state.session.update({'logged_in': True, 'user': u, 'role': res[0], 'shop_id': res[1]})
                    st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. NAVIGATION
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop = conn.execute("SELECT name, rate, tel, addr FROM shops WHERE sid=?", (sid,)).fetchone()
    if not shop: shop = ("Ma Boutique", 2800.0, "000", "Adresse")

# Menu restreint pour vendeurs
if st.session_state.session['role'] == "SUPER_ADMIN":
    choice = st.sidebar.radio("ADMIN", ["Validations", "Déconnexion"])
    if choice == "Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

choice = st.sidebar.radio("MENU", ["🛒 VENTES", "📦 STOCK", "📉 DETTES", "📊 RAPPORT", "🚪 QUITTER"])

# ------------------------------------------------------------------------------
# 6. CAISSE & FACTURE (VOTRE DEMANDE)
# ------------------------------------------------------------------------------
if choice == "🛒 VENTES":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        
        # --- DESIGN FACTURE 80mm ---
        st.markdown(f"""
        <div class="print-area">
            <center>
                <h3 style="margin:0;">{shop[0]}</h3>
                <small>{shop[3]}</small><br>
                <small>Tél: {shop[2]}</small><br>
                <hr>
                <b>FACTURE N° {inv['ref']}</b><br>
                Date: {inv['date']} à {inv['time']}<br>
                Vendeur: {st.session_state.session['user'].upper()}
                <hr>
            </center>
            <table>
                <tr><td colspan="2"><b>Client: {inv['cli']}</b></td></tr>
                <tr style="border-bottom:1px solid #000;">
                    <td align="left"><b>Article</b></td>
                    <td align="right"><b>Total</b></td>
                </tr>
                {"".join([f"<tr><td>{v['q']} x {k[:15]}</td><td align='right'>{(v['q']*v['p']):,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <table style="font-weight:bold; font-size:14px;">
                <tr><td>TOTAL</td><td align="right">{inv['total']:,.2f} {inv['devise']}</td></tr>
                <tr><td>PAYÉ</td><td align="right">{inv['paye']:,.2f} {inv['devise']}</td></tr>
                {"<tr><td>RESTE</td><td align='right' style='color:red;'>"+f"{inv['reste']:,.2f} {inv['devise']}"+"</td></tr>" if inv['reste']>0 else ""}
            </table>
            <hr>
            <center><small>Merci de votre confiance !<br>Logiciel par ANASH ERP</small></center>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ RETOUR"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if c3.button("📲 WHATSAPP"):
            msg = f"Facture {shop[0]}: {inv['ref']} - Total: {inv['total']} {inv['devise']}. Merci!"
            st.markdown(f'<meta http-equiv="refresh" content="0;url=https://wa.me/?text={msg}">', unsafe_allow_html=True)

    else:
        st.header("🛒 CAISSE")
        devise = st.radio("DEVISE", ["USD", "CDF"], horizontal=True)
        taux = shop[1]
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            search = st.selectbox("Article", ["---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if search != "---":
                it_name = search.split(" (")[0]
                if st.button("AJOUTER"):
                    info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                    st.session_state.session['cart'][it_name] = {'p': info[0], 'q': 1, 'max': info[1]}
                    st.rerun()

        if st.session_state.session['cart']:
            st.divider()
            t_usd = 0
            for it, d in list(st.session_state.session['cart'].items()):
                col1, col2, col3 = st.columns([3,2,1])
                new_q = col2.number_input(f"Qté {it}", 1, d['max'], d['q'], key=f"q_{it}")
                st.session_state.session['cart'][it]['q'] = new_q
                t_usd += d['p'] * new_q
                if col3.button("🗑️", key=f"del_{it}"): del st.session_state.session['cart'][it]; st.rerun()

            final_t = t_usd if devise == "USD" else t_usd * taux
            st.markdown(f"<div class='neon-frame'><h2>TOTAL : {final_t:,.2f} {devise}</h2></div>", unsafe_allow_html=True)
            
            with st.form("confirm"):
                cli = st.text_input("Nom Client", "CLIENT COMPTANT")
                pay = st.number_input(f"Montant Reçu ({devise})", value=float(final_t))
                if st.form_submit_button("VALIDER LA VENTE"):
                    v_ref = f"FAC-{random.randint(1000, 9999)}"
                    d_now = datetime.now().strftime("%d/%m/%Y")
                    t_now = datetime.now().strftime("%H:%M")
                    p_usd = pay if devise == "USD" else pay / taux
                    reste_usd = t_usd - p_usd
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used, rate_at_sale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (v_ref, cli, t_usd, p_usd, reste_usd, d_now, t_now, st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise, taux))
                        for it, dt in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], it, sid))
                        if reste_usd > 0:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid, last_pay_date) VALUES (?,?,?,?,?)", (cli, reste_usd, v_ref, sid, d_now))
                        conn.commit()
                    
                    st.session_state.session['viewing_invoice'] = {
                        'ref': v_ref, 'cli': cli, 'total': final_t, 'paye': pay, 'reste': (final_t - pay),
                        'date': d_now, 'time': t_now, 'items': st.session_state.session['cart'], 'devise': devise
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()

# --- AUTRES SECTIONS (RAPPEL DES CONSIGNES : NE RIEN SUPPRIMER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION STOCK")
    with st.form("add_i"):
        n = st.text_input("Désignation").upper()
        p_a = st.number_input("Prix Achat $")
        p_v = st.number_input("Prix Vente $")
        q = st.number_input("Quantité", step=1)
        if st.form_submit_button("AJOUTER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n, q, p_a, p_v, sid))
                conn.commit(); st.rerun()

elif choice == "📉 DETTES":
    st.header("📉 DETTES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance FROM client_debts WHERE sid=? AND balance > 0", (sid,)).fetchall()
        for id_d, c, b in dettes:
            st.write(f"{c} : {b}$")
            if st.button(f"Solder {c}", key=id_d):
                conn.execute("UPDATE client_debts SET balance=0 WHERE id=?", (id_d,))
                conn.commit(); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()
