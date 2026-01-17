# ==============================================================================
# ANASH ERP v400 - SYSTÈME BALIKA BUSINESS (ÉDITION ULTIME)
# ------------------------------------------------------------------------------
# OPTIMISÉ POUR SMARTPHONE | FACTURATION A4 & 80MM | GESTION DES DETTES AVANCÉE
# FIX : MESSAGE DÉFILANT PERSISTANT | ACTIVATION ADMIN INSTANTANÉE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import base64
import io

# ------------------------------------------------------------------------------
# 1. ARCHITECTURE DE LA BASE DE DONNÉES (SÉCURISÉE)
# ------------------------------------------------------------------------------
DB_NAME = "balika_business_v400.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # Système et Configuration
        cursor.execute("CREATE TABLE IF NOT EXISTS system_prefs (id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)")
        # Comptes Utilisateurs
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop_id TEXT, status TEXT, 
            full_name TEXT, phone TEXT, expiry_date TEXT)""")
        # Registre des Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, shop_name TEXT, rate REAL DEFAULT 2800, 
            address TEXT, contact TEXT, currency_pref TEXT DEFAULT 'USD')""")
        # Gestion des Stocks
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock_qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
        # Journal des Ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_ref TEXT, customer TEXT, 
            total_usd REAL, paid_usd REAL, debt_usd REAL, s_date TEXT, s_time TEXT, 
            seller_id TEXT, sid TEXT, items_json TEXT, currency_used TEXT)""")
        # Gestion des Dettes (Paiements par tranche)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debt_manager (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, balance REAL, 
            ref_invoice TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")
        
        # Données initiales
        cursor.execute("SELECT id FROM system_prefs WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_prefs VALUES (1, 'BALIKA BUSINESS', 'Bonjour et bienvenue chez BALIKA BUSINESS - Votre succès est notre priorité 2026', '4.0.0')")
        
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            master_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', master_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000', '2099-12-31'))
        conn.commit()

init_db()

# ------------------------------------------------------------------------------
# 2. DESIGN & STYLE COBALT (FIX VISUEL)
# ------------------------------------------------------------------------------
db = get_db()
config = db.execute("SELECT * FROM system_prefs WHERE id=1").fetchone()
APP_NAME, MARQUEE_MSG = config['app_name'], config['marquee']
db.close()

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_custom_ui():
    st.markdown(f"""
    <style>
        /* FOND COBALT ET TEXTE BLANC DÉFINITIF */
        .stApp {{ background-color: #000b1e; color: #ffffff !important; }}
        
        /* FORCE LA COULEUR BLANCHE SUR TOUT LE TEXTE */
        label, p, span, h1, h2, h3, h4, .stMarkdown, .stHeader {{ 
            color: #ffffff !important; font-weight: 700 !important; 
        }}
        
        /* FIX POUR LES INPUTS : TEXTE NOIR SUR FOND BLANC POUR LISIBILITÉ */
        input {{ color: #000000 !important; background-color: #ffffff !important; font-weight: bold !important; }}
        
        /* MESSAGE DÉFILANT (MARQUEE) RÉÉCRIT */
        .marquee-container {{
            position: fixed; top: 0; left: 0; width: 100%; height: 50px;
            background: #000000; border-bottom: 3px solid #00ff00;
            z-index: 999999; display: flex; align-items: center; overflow: hidden;
        }}
        .marquee-text {{
            white-space: nowrap; display: inline-block;
            animation: scroll-left 25s linear infinite;
            color: #00ff00; font-size: 22px; font-weight: bold; text-transform: uppercase;
        }}
        @keyframes scroll-left {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        /* CONTENEURS COBALT */
        .cobalt-card {{
            background: linear-gradient(145deg, #0044ff, #001a66);
            border: 2px solid #00d9ff; border-radius: 15px; padding: 20px;
            margin: 15px 0; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        
        /* BOUTONS ADAPTÉS AU MOBILE */
        .stButton > button {{
            width: 100% !important; height: 55px !important; border-radius: 12px !important;
            background: linear-gradient(to right, #0055ff, #002288) !important;
            color: white !important; font-weight: bold !important; border: 2px solid #ffffff !important;
        }}

        /* TABLEAUX LISIBLES */
        .stTable {{ background-color: #ffffff !important; color: #000000 !important; border-radius: 10px; }}
        th {{ background-color: #0044ff !important; color: white !important; text-align: center !important; }}
        td {{ color: black !important; font-weight: bold !important; text-align: center !important; }}

        .main-spacer {{ margin-top: 70px; }}
        @media print {{ .no-print {{ display: none !important; }} }}
    </style>
    <div class="marquee-container">
        <div class="marquee-text">🚀 {MARQUEE_MSG} 🚀</div>
    </div>
    <div class="main-spacer"></div>
    """, unsafe_allow_html=True)

apply_custom_ui()

# ------------------------------------------------------------------------------
# 3. GESTION DE LA CONNEXION
# ------------------------------------------------------------------------------
if 'user_session' not in st.session_state:
    st.session_state.user_session = {'logged': False, 'uid': None, 'role': None, 'sid': None, 'cart': {}, 'active_inv': None}

if not st.session_state.user_session['logged']:
    _, auth_col, _ = st.columns([1, 2, 1])
    with auth_col:
        st.markdown("<div class='cobalt-card'><h1>💎 BALIKA BUSINESS</h1><p>Connectez-vous pour gérer votre entreprise</p></div>", unsafe_allow_html=True)
        t_login, t_signup = st.tabs(["🔒 CONNEXION", "📝 CRÉER UN COMPTE"])
        
        with t_login:
            l_uid = st.text_input("Identifiant").lower().strip()
            l_pwd = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU TABLEAU DE BORD"):
                db = get_db()
                acc = db.execute("SELECT * FROM users WHERE uid=?", (l_uid,)).fetchone()
                db.close()
                if acc and hashlib.sha256(l_pwd.encode()).hexdigest() == acc['pwd']:
                    if acc['status'] == 'ACTIF' or acc['role'] == 'SUPER_ADMIN':
                        st.session_state.user_session.update({'logged': True, 'uid': l_uid, 'role': acc['role'], 'sid': acc['shop_id']})
                        st.rerun()
                    else: st.error("⚠️ Compte en attente d'activation par l'Admin.")
                else: st.error("❌ Identifiants invalides.")
        
        with t_signup:
            with st.form("signup_form"):
                s_uid = st.text_input("ID Utilisateur souhaité").lower()
                s_name = st.text_input("Nom de votre Commerce")
                s_pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("DEMANDER UNE ACTIVATION"):
                    db = get_db()
                    try:
                        hp = hashlib.sha256(s_pwd.encode()).hexdigest()
                        expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                        db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                  (s_uid, hp, 'BOSS', 'PENDING', 'ATTENTE', s_name, '', expiry))
                        db.commit(); st.success("✅ Demande envoyée ! Attendez l'activation de l'Admin.")
                    except: st.error("❌ Cet identifiant est déjà utilisé.")
                    finally: db.close()
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE SUPER ADMIN (FIX DÉFINITIF ACTIVATION)
# ------------------------------------------------------------------------------
if st.session_state.user_session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMINISTRATION")
    adm_menu = st.sidebar.radio("SÉLECTION", ["Abonnés", "Réglages App", "Mon Compte", "Quitter"])
    
    if adm_menu == "Abonnés":
        st.markdown("<div class='cobalt-card'><h1>VALIDER LES CLIENTS</h1></div>", unsafe_allow_html=True)
        db = get_db()
        all_u = db.execute("SELECT * FROM users WHERE role='BOSS'").fetchall()
        for u in all_u:
            with st.expander(f"👤 {u['full_name']} (@{u['uid']}) - {u['status']}"):
                c_status, c_expiry = st.columns(2)
                new_st = c_status.selectbox("Statut", ["ATTENTE", "ACTIF", "SUSPENDU"], index=["ATTENTE", "ACTIF", "SUSPENDU"].index(u['status']), key=f"st_{u['uid']}")
                new_ex = c_expiry.date_input("Expiration", datetime.strptime(u['expiry_date'], '%Y-%m-%d'), key=f"ex_{u['uid']}")
                
                if st.button(f"ACTIVER / METTRE À JOUR {u['uid'].upper()}", key=f"btn_{u['uid']}"):
                    # MISE À JOUR COMPTE + CRÉATION AUTOMATIQUE BOUTIQUE
                    db.execute("UPDATE users SET status=?, expiry_date=?, shop_id=? WHERE uid=?", 
                              (new_st, new_ex.strftime('%Y-%m-%d'), u['uid'], u['uid']))
                    db.execute("INSERT OR IGNORE INTO shops (sid, shop_name) VALUES (?,?)", (u['uid'], u['full_name']))
                    db.commit()
                    st.success(f"Compte {u['uid']} activé avec succès !"); st.rerun()
        db.close()

    elif adm_menu == "Réglages App":
        st.header("⚙️ CONFIGURATION SYSTÈME")
        with st.form("sys_form"):
            new_title = st.text_input("Titre de l'application", APP_NAME)
            new_marquee = st.text_area("Message défilant", MARQUEE_MSG)
            if st.form_submit_button("APPLIQUER"):
                db = get_db()
                db.execute("UPDATE system_prefs SET app_name=?, marquee=? WHERE id=1", (new_title, new_marquee))
                db.commit(); db.close(); st.rerun()

    if adm_menu == "Quitter": st.session_state.user_session['logged'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE BOUTIQUE (BOSS & VENDEUR)
# ------------------------------------------------------------------------------
curr_sid = st.session_state.user_session['sid']
db = get_db()
shop_info = db.execute("SELECT * FROM shops WHERE sid=?", (curr_sid,)).fetchone()
user_info = db.execute("SELECT expiry_date FROM users WHERE uid=?", (st.session_state.user_session['uid'],)).fetchone()
db.close()

if not shop_info:
    st.error("❌ Erreur : Boutique introuvable. Contactez l'administrateur.")
    st.stop()

# Navigation Boutique
nav_choices = ["🏠 TABLEAU DE BORD", "🛒 POINT DE VENTE", "📦 INVENTAIRE", "📉 CRÉDITS & DETTES", "📊 RAPPORTS", "👥 PROFIL & ÉQUIPE", "🚪 QUITTER"]
if st.session_state.user_session['role'] == "VENDEUR":
    nav_choices = ["🏠 TABLEAU DE BORD", "🛒 POINT DE VENTE", "📉 CRÉDITS & DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'><h3>{shop_info['shop_name']}</h3><p>Expire le: {user_info['expiry_date']}</p></div>", unsafe_allow_html=True)
    user_nav = st.radio("MENU", nav_choices)

# --- TABLEAU DE BORD ---
if user_nav == "🏠 TABLEAU DE BORD":
    st.markdown(f"<div class='cobalt-card'><h1>BIENVENUE CHEZ {shop_info['shop_name'].upper()}</h1></div>", unsafe_allow_html=True)
    db = get_db()
    today = datetime.now().strftime("%d/%m/%Y")
    sales_today = db.execute("SELECT SUM(total_usd) FROM sales_ledger WHERE sid=? AND s_date=?", (curr_sid, today)).fetchone()[0] or 0
    debts_total = db.execute("SELECT SUM(balance) FROM debt_manager WHERE sid=? AND status='OUVERT'", (curr_sid,)).fetchone()[0] or 0
    db.close()
    
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"<div style='border:4px solid #00ff00; border-radius:15px; text-align:center; padding:20px;'><h3 style='color:#00ff00;'>RECETTE JOUR</h3><h1 style='color:#00ff00;'>{sales_today:,.2f} $</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div style='border:4px solid #ff4444; border-radius:15px; text-align:center; padding:20px;'><h3 style='color:#ff4444;'>DETTES CLIENTS</h3><h1 style='color:#ff4444;'>{debts_total:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- POINT DE VENTE ---
elif user_nav == "🛒 POINT DE VENTE":
    if st.session_state.user_session['active_inv']:
        inv = st.session_state.user_session['active_inv']
        st.markdown("<div class='no-print'>")
        if st.button("⬅️ RETOURNER AU TERMINAL"): st.session_state.user_session['active_inv'] = None; st.rerun()
        st.markdown("</div>")

        st.markdown(f"""
        <div style="background:white; color:black; padding:30px; border-radius:10px; border:2px solid #000; font-family:monospace; max-width:600px; margin:auto;">
            <h2 style='text-align:center; margin:0;'>{shop_info['shop_name']}</h2>
            <p style='text-align:center;'>{shop_info['address']}<br>Tél: {shop_info['contact']}</p>
            <hr>
            <p>REF: {inv['ref']} | DATE: {inv['date']}</p>
            <p>CLIENT: {inv['cli']}</p>
            <table style='width:100%'>
                <tr style='border-bottom:1px solid #000;'><th>Désignation</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td style='text-align:right;'>{v['t']:,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <h3 style='text-align:right;'>TOTAL: {inv['total']:,.2f} {inv['cur']}</h3>
            <p style='text-align:center; margin-top:30px; font-size:12px;'>Merci de votre confiance !</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER LA FACTURE"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        db = get_db()
        stock_data = db.execute("SELECT * FROM inventory WHERE sid=? AND stock_qty > 0", (curr_sid,)).fetchall()
        db.close()
        
        col_m, col_v = st.columns([1, 2])
        with col_m: 
            sel_cur = st.radio("DEVISE", ["USD", "CDF"])
            tx_rate = shop_info['rate']
        with col_v:
            search_p = st.selectbox("RECHERCHER ARTICLE", ["---"] + [f"{s['item_name']} ({s['stock_qty']} dispo)" for s in stock_data])
            if search_p != "---":
                pure_n = search_p.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    db = get_db()
                    p_info = db.execute("SELECT sell_price, stock_qty FROM inventory WHERE item_name=? AND sid=?", (pure_n, curr_sid)).fetchone()
                    db.close()
                    st.session_state.user_session['cart'][pure_n] = {'p': p_info['sell_price'], 'q': 1, 'max': p_info['stock_qty']}
                    st.rerun()

        if st.session_state.user_session['cart']:
            st.subheader("📋 PANIER")
            total_usd = 0.0
            for item, details in list(st.session_state.user_session['cart'].items()):
                st.markdown(f"**{item}** | {details['p']}$ l'unité")
                cq, cr = st.columns([4, 1])
                st.session_state.user_session['cart'][item]['q'] = cq.number_input(f"Qté pour {item}", 1, details['max'], details['q'], key=f"v_{item}")
                total_usd += details['p'] * st.session_state.user_session['cart'][item]['q']
                if cr.button("🗑️", key=f"rm_{item}"): del st.session_state.user_session['cart'][item]; st.rerun()

            final_pay = total_usd if sel_cur == "USD" else total_usd * tx_rate
            st.markdown(f"<div class='cobalt-card'><h2>TOTAL À PAYER : {final_pay:,.2f} {sel_cur}</h2></div>", unsafe_allow_html=True)
            
            with st.form("pay_form"):
                cli_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                cli_paid = st.number_input(f"MONTANT REÇU ({sel_cur})", value=float(final_pay))
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    paid_usd = cli_paid if sel_cur == "USD" else cli_paid / tx_rate
                    rest_usd = total_usd - paid_usd
                    ref_id = f"BAL-{random.randint(1000, 9999)}"
                    d_n, t_n = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    db = get_db()
                    blob = {k: {'q': v['q'], 't': v['p']*v['q']} for k,v in st.session_state.user_session['cart'].items()}
                    db.execute("INSERT INTO sales_ledger (invoice_ref, customer, total_usd, paid_usd, debt_usd, s_date, s_time, seller_id, sid, items_json, currency_used) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (ref_id, cli_name, total_usd, paid_usd, rest_usd, d_n, t_n, st.session_state.user_session['uid'], curr_sid, json.dumps(blob), sel_cur))
                    for n, v in st.session_state.user_session['cart'].items():
                        db.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name=? AND sid=?", (v['q'], n, curr_sid))
                    if rest_usd > 0.01:
                        db.execute("INSERT INTO debt_manager (customer_name, balance, ref_invoice, sid) VALUES (?,?,?,?)", (cli_name, rest_usd, ref_id, curr_sid))
                    db.commit(); db.close()
                    
                    st.session_state.user_session['active_inv'] = {'ref': ref_id, 'cli': cli_name, 'total': final_pay, 'cur': sel_cur, 'items': blob, 'date': d_now}
                    st.session_state.user_session['cart'] = {}; st.rerun()

# --- INVENTAIRE ---
elif user_nav == "📦 INVENTAIRE":
    st.markdown("<div class='cobalt-card'><h1>GESTION DU STOCK</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("stock_form"):
            in_name = st.text_input("Désignation").upper()
            c_p1, c_p2 = st.columns(2)
            in_buy = c_p1.number_input("Prix d'Achat ($)")
            in_sell = c_p2.number_input("Prix de Vente ($)")
            in_qty = st.number_input("Quantité Initiale", 1)
            if st.form_submit_button("ENREGISTRER"):
                db = get_db()
                db.execute("INSERT INTO inventory (item_name, stock_qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", 
                          (in_name, in_qty, in_buy, in_sell, curr_sid))
                db.commit(); db.close(); st.success("Article ajouté !"); st.rerun()
    
    db = get_db()
    stk = db.execute("SELECT * FROM inventory WHERE sid=? ORDER BY item_name", (curr_sid,)).fetchall()
    db.close()
    if stk:
        df_stk = pd.DataFrame(stk, columns=["ID", "ARTICLE", "STOCK", "P.ACHAT", "P.VENTE", "SID", "CAT"])
        st.table(df_stk[["ARTICLE", "STOCK", "P.VENTE"]])
        for s in stk:
            with st.expander(f"MODIFIER : {s['item_name']}"):
                col_u1, col_u2 = st.columns(2)
                up_p = col_u1.number_input("Nouveau Prix ($)", value=s['sell_price'], key=f"up_p_{s['id']}")
                up_q = col_u2.number_input("Ajuster Stock", value=s['stock_qty'], key=f"up_q_{s['id']}")
                if st.button(f"SAUVEGARDER MAJ {s['id']}", key=f"btn_s_{s['id']}"):
                    db = get_db()
                    db.execute("UPDATE inventory SET sell_price=?, stock_qty=? WHERE id=?", (up_p, up_q, s['id']))
                    db.commit(); db.close(); st.rerun()

# --- DETTES ---
elif user_nav == "📉 CRÉDITS & DETTES":
    st.markdown("<div class='cobalt-card'><h1>SUIVI DES DETTES CLIENTS</h1></div>", unsafe_allow_html=True)
    db = get_db()
    debts = db.execute("SELECT * FROM debt_manager WHERE sid=? AND status='OUVERT'", (curr_sid,)).fetchall()
    db.close()
    if not debts: st.info("Aucune dette en cours.")
    for d in debts:
        with st.expander(f"👤 {d['customer_name']} | RESTE : {d['balance']:,.2f} $"):
            pay_part = st.number_input("Paiement reçu ($)", 0.0, d['balance'], key=f"d_{d['id']}")
            if st.button(f"ENREGISTRER TRANCHE {d['id']}"):
                new_bal = d['balance'] - pay_part
                db_u = get_db()
                if new_bal <= 0.01: db_u.execute("UPDATE debt_manager SET balance=0, status='SOLDE' WHERE id=?", (d['id'],))
                else: db_u.execute("UPDATE debt_manager SET balance=? WHERE id=?", (new_bal, d['id']))
                db_u.commit(); db_u.close(); st.success("Paiement validé !"); st.rerun()

# --- RAPPORTS ---
elif user_nav == "📊 RAPPORTS":
    st.markdown("<div class='cobalt-card'><h1>JOURNAL DES ACTIVITÉS</h1></div>", unsafe_allow_html=True)
    sel_date = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    db = get_db()
    rep = db.execute("SELECT * FROM sales_ledger WHERE sid=? AND s_date=?", (curr_sid, sel_date)).fetchall()
    db.close()
    if rep:
        df_rep = pd.DataFrame(rep, columns=["ID","REF","CLIENT","TOTAL","PAYÉ","DETTE","DATE","HEURE","VENDEUR","SID","JS","CUR"])
        st.table(df_rep[["REF", "CLIENT", "TOTAL", "HEURE", "VENDEUR"]])
        st.markdown(f"<div class='cobalt-card'><h2>RECETTE TOTALE : {df_rep['TOTAL'].sum():,.2f} $</h2></div>", unsafe_allow_html=True)
    else: st.info("Aucune vente pour cette date.")

# --- PROFIL & QUITTER ---
elif user_nav == "👥 PROFIL & ÉQUIPE":
    st.markdown("<div class='cobalt-card'><h1>RÉGLAGES BOUTIQUE</h1></div>", unsafe_allow_html=True)
    with st.form("shop_cfg"):
        sn = st.text_input("Nom de l'Enseigne", shop_info['shop_name'])
        rt = st.number_input("Taux de Change (1$ = ? CDF)", value=shop_info['rate'])
        ad = st.text_area("Adresse", shop_info['address'])
        if st.form_submit_button("METTRE À JOUR LA BOUTIQUE"):
            db = get_db()
            db.execute("UPDATE shops SET shop_name=?, rate=?, address=? WHERE sid=?", (sn, rt, ad, curr_sid))
            db.commit(); db.close(); st.success("Modifications enregistrées !"); st.rerun()

elif user_nav == "🚪 QUITTER":
    st.session_state.user_session['logged'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v400 - BALIKA BUSINESS ERP
# ==============================================================================
