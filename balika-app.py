# ==============================================================================
# ANASH ERP v270 - SYSTÈME DE GESTION PANORAMIQUE (ÉDITION FINALE 2026)
# ------------------------------------------------------------------------------
# OPTIMISÉ SMARTPHONE | FACTURATION ADMINISTRATIVE A4/80MM | GESTION ABONNÉS
# FIX TOTAL CONTRASTE : LABELS BLANCS SUR FOND SOMBRE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import base64
import io

# ------------------------------------------------------------------------------
# 1. ARCHITECTURE DES DONNÉES (PERSISTANCE ABSOLUE)
# ------------------------------------------------------------------------------
DB_NAME = "anash_balika_v270.db"

def get_db_connection():
    """Établit la connexion avec la base de données SQLite."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def run_db_setup():
    """Initialise toutes les tables nécessaires pour l'application."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Configuration globale du système
        cursor.execute("""CREATE TABLE IF NOT EXISTS sys_prefs (
            id INTEGER PRIMARY KEY, 
            app_title TEXT, 
            scrolling_msg TEXT,
            version TEXT)""")
        
        # Comptes (Admin, Propriétaires, Vendeurs)
        cursor.execute("""CREATE TABLE IF NOT EXISTS user_accounts (
            uid TEXT PRIMARY KEY, 
            pwd_hash TEXT, 
            access_level TEXT, 
            shop_ref TEXT, 
            account_status TEXT, 
            display_name TEXT, 
            phone_num TEXT, 
            expiry_dt TEXT)""")
        
        # Informations sur les Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shop_registry (
            sid TEXT PRIMARY KEY, 
            shop_name TEXT, 
            owner_uid TEXT, 
            exchange_rate REAL DEFAULT 2800, 
            physical_addr TEXT, 
            tel_contact TEXT)""")
        
        # Gestion de l'inventaire
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            product_name TEXT, 
            quantity INTEGER, 
            buying_price REAL, 
            selling_price REAL, 
            sid TEXT, 
            category_tag TEXT)""")
        
        # Registre des ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            invoice_ref TEXT, 
            customer_name TEXT, 
            total_amount_usd REAL, 
            amount_paid_usd REAL, 
            balance_due_usd REAL, 
            sale_date TEXT, 
            sale_time TEXT, 
            seller_uid TEXT, 
            sid TEXT, 
            items_blob TEXT, 
            used_currency TEXT)""")
        
        # Registre des dettes (Crédits)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debt_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            client_identity TEXT, 
            current_balance REAL, 
            invoice_link TEXT, 
            sid TEXT, 
            payment_status TEXT DEFAULT 'OUVERT')""")

        # Insertion des données par défaut
        cursor.execute("SELECT id FROM sys_prefs WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO sys_prefs VALUES (1, 'BALIKA BUSINESS v270', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION UNIFIÉ - PERFORMANCE ET FIABILITÉ', '2.7.0')")
        
        cursor.execute("SELECT uid FROM user_accounts WHERE uid='admin'")
        if not cursor.fetchone():
            master_pass = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO user_accounts VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', master_pass, 'SUPER_ADMIN', 'SYSTEM_ROOT', 'ACTIF', 'ADMINISTRATEUR', '000', '2099-12-31'))
        conn.commit()

run_db_setup()

# ------------------------------------------------------------------------------
# 2. INTERFACE UTILISATEUR & STYLE (CSS SUR MESURE)
# ------------------------------------------------------------------------------
db = get_db_connection()
sys_cfg = db.execute("SELECT * FROM sys_prefs WHERE id=1").fetchone()
APP_NAME, SCROLL_MSG = sys_cfg['app_title'], sys_cfg['scrolling_msg']
db.close()

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def inject_styles():
    st.markdown(f"""
    <style>
        /* BASE & TYPOGRAPHIE */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        .stApp {{ background-color: #000b1d; color: #ffffff !important; font-family: 'Roboto', sans-serif; }}
        
        /* CORRECTION CRITIQUE DES LABELS (LECTURE FACILE) */
        label, .stMarkdown, p, span, h1, h2, h3, h4, .stRadio > label {{ 
            color: #ffffff !important; font-weight: 600 !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        
        /* BARRE DÉFILANTE (MARQUEE) */
        .marquee-wrapper {{
            position: fixed; top: 0; left: 0; width: 100%; height: 40px;
            background: #000; border-bottom: 2px solid #00ff00;
            z-index: 99999; display: flex; align-items: center; overflow: hidden;
        }}
        .marquee-content {{
            white-space: nowrap; display: inline-block;
            animation: marquee-anim 30s linear infinite;
            color: #00ff00; font-size: 18px; font-weight: bold;
        }}
        @keyframes marquee-anim {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        /* CONTENEURS COBALT CENTRÉS */
        .cobalt-box {{
            background: linear-gradient(145deg, #0044ff, #001a66);
            border: 1px solid #00d9ff; border-radius: 15px; padding: 25px;
            margin: 15px 0; text-align: center; box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        }}
        
        /* TABLEAUX LISIBLES (DESIGN BLANC/BLEU) */
        .stTable, table {{ 
            background-color: #ffffff !important; color: #000000 !important; 
            border-radius: 10px; overflow: hidden; border: none !important;
        }}
        th {{ background-color: #0044ff !important; color: #ffffff !important; text-align: center !important; padding: 12px !important; }}
        td {{ color: #000000 !important; text-align: center !important; font-weight: 700 !important; border-bottom: 1px solid #eee !important; }}

        /* BOUTONS ADAPTÉS AU MOBILE */
        .stButton > button {{
            width: 100% !important; height: 55px !important; border-radius: 12px !important;
            background: linear-gradient(to right, #0055ff, #002288) !important;
            color: white !important; font-weight: bold !important; border: 2px solid #ffffff !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3); transition: 0.3s;
        }}
        .stButton > button:active {{ transform: scale(0.95); }}

        /* FACTURE ADMINISTRATIVE PROFESSIONNELLE */
        .invoice-print {{
            background: #ffffff !important; color: #000000 !important; padding: 40px;
            border: 2px solid #000; border-radius: 5px; max-width: 800px; margin: auto;
            font-family: 'Courier New', Courier, monospace;
        }}

        /* SIDEBAR PERSONNALISÉE */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 4px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold !important; }}

        /* ESPACEMENT */
        .main-spacer {{ margin-top: 60px; }}
        .no-print {{ display: block; }}
        @media print {{ .no-print {{ display: none !important; }} .invoice-print {{ border: none; }} }}
    </style>
    <div class="marquee-wrapper">
        <div class="marquee-content">🚀 {SCROLL_MSG} | {APP_NAME} | VERSION FINALE SÉCURISÉE 🚀</div>
    </div>
    <div class="main-spacer"></div>
    """, unsafe_allow_html=True)

inject_styles()

# ------------------------------------------------------------------------------
# 3. GESTION DE LA SESSION UTILISATEUR
# ------------------------------------------------------------------------------
if 'user' not in st.session_state:
    st.session_state.user = {
        'logged_in': False, 'uid': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'active_invoice': None
    }

# ------------------------------------------------------------------------------
# 4. MODULE DE CONNEXION ET INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.user['logged_in']:
    _, auth_box, _ = st.columns([1, 2, 1])
    with auth_box:
        st.markdown("<div class='cobalt-box'><h1>💎 BALIKA BUSINESS</h1><p>Connectez-vous pour continuer</p></div>", unsafe_allow_html=True)
        tab_login, tab_join = st.tabs(["🔒 CONNEXION", "📝 INSCRIPTION"])
        
        with tab_login:
            login_u = st.text_input("Identifiant").lower().strip()
            login_p = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU TABLEAU DE BORD"):
                db_conn = get_db_connection()
                record = db_conn.execute("SELECT * FROM user_accounts WHERE uid=?", (login_u,)).fetchone()
                db_conn.close()
                if record and hashlib.sha256(login_p.encode()).hexdigest() == record['pwd_hash']:
                    if record['account_status'] == 'ACTIF' or record['access_level'] == 'SUPER_ADMIN':
                        # Contrôle de la validité de l'abonnement
                        expiry = datetime.strptime(record['expiry_dt'], '%Y-%m-%d')
                        if datetime.now() > expiry and record['access_level'] != 'SUPER_ADMIN':
                            st.error(f"Abonnement expiré le {record['expiry_dt']}. Contactez l'admin.")
                        else:
                            st.session_state.user.update({'logged_in': True, 'uid': login_u, 'role': record['access_level'], 'shop_id': record['shop_ref']})
                            st.rerun()
                    else: st.warning("Compte en attente de validation par l'administration.")
                else: st.error("Identifiants incorrects ou compte inexistant.")
        
        with tab_join:
            with st.form("signup_form"):
                reg_uid = st.text_input("Identifiant souhaité").lower()
                reg_name = st.text_input("Nom de votre Entreprise")
                reg_pass = st.text_input("Créer un mot de passe", type="password")
                if st.form_submit_button("DEMANDER UNE PÉRIODE D'ESSAI"):
                    db_conn = get_db_connection()
                    try:
                        h_pass = hashlib.sha256(reg_pass.encode()).hexdigest()
                        # Par défaut 7 jours d'essai pour les nouveaux
                        trial_end = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                        db_conn.execute("INSERT INTO user_accounts VALUES (?,?,?,?,?,?,?,?)", 
                                      (reg_uid, h_pass, 'BOSS', 'PENDING', 'ATTENTE', reg_name, '', trial_end))
                        db_conn.commit(); st.success("Votre demande a été envoyée ! Un administrateur l'activera sous peu.")
                    except: st.error("Désolé, cet identifiant est déjà utilisé.")
                    finally: db_conn.close()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN (GESTION DES ABONNÉS)
# ------------------------------------------------------------------------------
if st.session_state.user['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMINISTRATION")
    adm_nav = st.sidebar.radio("SÉLECTION", ["Abonnés & Clients", "Configuration App", "Mon Profil Admin", "Base de Données", "Se Déconnecter"])
    
    if adm_nav == "Abonnés & Clients":
        st.markdown("<div class='cobalt-box'><h1>GESTION DES ABONNÉS</h1></div>", unsafe_allow_html=True)
        db_conn = get_db_connection()
        all_clients = db_conn.execute("SELECT * FROM user_accounts WHERE access_level='BOSS'").fetchall()
        for cl in all_clients:
            with st.expander(f"👤 {cl['display_name']} (@{cl['uid']}) - {cl['account_status']}"):
                col_s, col_e = st.columns(2)
                st_update = col_s.selectbox("Statut du compte", ["ATTENTE", "ACTIF", "SUSPENDU"], index=["ATTENTE", "ACTIF", "SUSPENDU"].index(cl['account_status']), key=f"st_{cl['uid']}")
                dt_update = col_e.date_input("Date d'expiration", datetime.strptime(cl['expiry_dt'], '%Y-%m-%d'), key=f"ex_{cl['uid']}")
                if st.button(f"METTRE À JOUR {cl['uid']}"):
                    db_conn.execute("UPDATE user_accounts SET account_status=?, expiry_dt=?, shop_ref=? WHERE uid=?", 
                                  (st_update, dt_update.strftime('%Y-%m-%d'), cl['uid'], cl['uid']))
                    # Initialisation automatique de la boutique à l'activation
                    db_conn.execute("INSERT OR IGNORE INTO shop_registry (sid, shop_name, owner_uid) VALUES (?,?,?)", (cl['uid'], cl['display_name'], cl['uid']))
                    db_conn.commit(); st.rerun()
        db_conn.close()

    elif adm_nav == "Configuration App":
        st.header("⚙️ RÉGLAGES SYSTÈME")
        with st.form("global_cfg"):
            new_title = st.text_input("Nom de l'Application", APP_NAME)
            new_marquee = st.text_area("Texte du message défilant", SCROLL_MSG)
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                db_conn = get_db_connection()
                db_conn.execute("UPDATE sys_prefs SET app_title=?, scrolling_msg=? WHERE id=1", (new_title, new_marquee))
                db_conn.commit(); db_conn.close(); st.rerun()

    elif adm_nav == "Mon Profil Admin":
        st.header("👤 MON PROFIL")
        with st.form("adm_p"):
            adm_id = st.text_input("Mon Identifiant", st.session_state.user['uid'])
            adm_pass = st.text_input("Nouveau Mot de Passe (laisser vide pour garder l'actuel)", type="password")
            if st.form_submit_button("SAUVEGARDER"):
                db_conn = get_db_connection()
                if adm_pass:
                    h_a = hashlib.sha256(adm_pass.encode()).hexdigest()
                    db_conn.execute("UPDATE user_accounts SET uid=?, pwd_hash=? WHERE uid=?", (adm_id, h_a, st.session_state.user['uid']))
                else:
                    db_conn.execute("UPDATE user_accounts SET uid=? WHERE uid=?", (adm_id, st.session_state.user['uid']))
                db_conn.commit(); db_conn.close(); st.session_state.user['logged_in'] = False; st.rerun()

    elif adm_nav == "Base de Données":
        st.header("💾 SAUVEGARDE")
        with open(DB_NAME, "rb") as f:
            st.download_button("📥 TÉLÉCHARGER LA SAUVEGARDE DU SYSTÈME (.db)", f, file_name=f"balika_backup_{datetime.now().strftime('%Y%m%d')}.db")

    if adm_nav == "Se Déconnecter": st.session_state.user['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE DE GESTION BOUTIQUE (BOSS & VENDEUR)
# ------------------------------------------------------------------------------
current_sid = st.session_state.user['shop_id']
db_conn = get_db_connection()
shop_data = db_conn.execute("SELECT * FROM shop_registry WHERE sid=?", (current_sid,)).fetchone()
user_data = db_conn.execute("SELECT expiry_dt FROM user_accounts WHERE uid=?", (st.session_state.user['uid'],)).fetchone()
db_conn.close()

if not shop_data:
    st.error("Erreur critique : Aucune boutique associée à ce compte. Contactez l'admin.")
    st.stop()

# Menu Navigation Boutique
nav_options = ["🏠 TABLEAU DE BORD", "🛒 POINT DE VENTE", "📦 INVENTAIRE", "📉 CRÉDITS & DETTES", "📊 RAPPORTS FINANCIERS", "👥 ÉQUIPE & PROFIL", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.user['role'] == "VENDEUR":
    nav_options = ["🏠 TABLEAU DE BORD", "🛒 POINT DE VENTE", "📉 CRÉDITS & DETTES", "📊 RAPPORTS FINANCIERS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"""
    <div class='cobalt-box' style='padding:15px; border-radius:10px;'>
        <h3 style='font-size:16px; margin:0;'>{shop_data['shop_name']}</h3>
        <p style='font-size:12px; color:#00ff00 !important;'>Abonnement : {user_data['expiry_dt']}</p>
        <p style='font-size:11px; margin-top:5px;'>Utilisateur: {st.session_state.user['uid'].upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    user_choice = st.radio("SÉLECTIONNER UN MENU", nav_options)

# --- 6.1 TABLEAU DE BORD ---
if user_choice == "🏠 TABLEAU DE BORD":
    st.markdown(f"<div class='cobalt-box'><h1>BIENVENUE CHEZ {shop_data['shop_name']}</h1><h3>{datetime.now().strftime('%A %d %B %Y')}</h3></div>", unsafe_allow_html=True)
    db_conn = get_db_connection()
    today_dt = datetime.now().strftime("%d/%m/%Y")
    total_sales = db_conn.execute("SELECT SUM(total_amount_usd) FROM sales_journal WHERE sid=? AND sale_date=?", (current_sid, today_dt)).fetchone()[0] or 0
    open_debts = db_conn.execute("SELECT SUM(current_balance) FROM debt_ledger WHERE sid=? AND payment_status='OUVERT'", (current_sid,)).fetchone()[0] or 0
    db_conn.close()
    
    col_v, col_d = st.columns(2)
    with col_v: st.markdown(f"<div style='border:4px solid #00ff00; border-radius:20px; text-align:center; padding:25px;'><h3 style='color:#00ff00;'>RECETTE DU JOUR</h3><h1 style='color:#00ff00;'>{total_sales:,.2f} $</h1></div>", unsafe_allow_html=True)
    with col_d: st.markdown(f"<div style='border:4px solid #ff4444; border-radius:20px; text-align:center; padding:25px;'><h3 style='color:#ff4444;'>CRÉDITS EN COURS</h3><h1 style='color:#ff4444;'>{open_debts:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 POINT DE VENTE & FACTURE ---
elif user_choice == "🛒 POINT DE VENTE":
    if st.session_state.user['active_invoice']:
        inv = st.session_state.user['active_invoice']
        st.markdown("<div class='no-print'>")
        if st.button("⬅️ RETOURNER AU TERMINAL"): st.session_state.user['active_invoice'] = None; st.rerun()
        format_p = st.selectbox("Choisir le format d'impression", ["Facture Administrative A4", "Ticket Caisse 80mm"])
        st.markdown("</div>")

        css_width = "100%" if format_p == "Facture Administrative A4" else "320px"
        st.markdown(f"""
        <div class="invoice-print" style="width:{css_width};">
            <h1 style="text-align:center; margin-bottom:5px;">{shop_data['shop_name']}</h1>
            <p style="text-align:center; font-size:14px; margin-top:0;">{shop_data['physical_addr']}<br>Contact: {shop_data['tel_contact']}</p>
            <hr style="border:1px dashed #000;">
            <div style="display:flex; justify-content:space-between; font-weight:bold; margin:15px 0;">
                <span>REF: {inv['ref']}</span>
                <span>Date: {inv['date']}</span>
            </div>
            <p>Client: <b>{inv['client']}</b></p>
            <table style="width:100%; border-collapse:collapse; margin:20px 0;">
                <thead>
                    <tr style="border-bottom:2px solid #000; text-align:left;">
                        <th style="color:black !important; background:none !important; text-align:left !important;">Désignation</th>
                        <th style="color:black !important; background:none !important; text-align:center !important;">Qté</th>
                        <th style="color:black !important; background:none !important; text-align:right !important;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr style='border-bottom:1px solid #ddd;'><td style='text-align:left !important;'>{item}</td><td style='text-align:center !important;'>{data['q']}</td><td style='text-align:right !important;'>{data['tot']:,.2f}</td></tr>" for item, data in inv['items'].items()])}
                </tbody>
            </table>
            <hr style="border:1px dashed #000;">
            <div style="text-align:right;">
                <h2 style="margin:0;">TOTAL : {inv['total']:,.2f} {inv['cur']}</h2>
                <p style="font-size:12px;">Vendeur: {st.session_state.user['uid'].upper()}</p>
            </div>
            <p style="text-align:center; font-size:12px; margin-top:40px;">Les marchandises vendues ne sont ni reprises ni échangées.<br>Merci de votre confiance !</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ LANCER L'IMPRESSION"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        db_conn = get_db_connection()
        stock_list = db_conn.execute("SELECT * FROM inventory_stock WHERE sid=? AND quantity > 0", (current_sid,)).fetchall()
        db_conn.close()
        
        col_sel, col_mon = st.columns([3, 1])
        with col_mon: 
            cur_choice = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            rate_val = shop_data['exchange_rate']
        with col_sel:
            prod_sel = st.selectbox("Rechercher un article en stock", ["---"] + [f"{s['product_name']} (Dispo: {s['quantity']})" for s in stock_list])
            if prod_sel != "---":
                p_pure_name = prod_sel.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    db_conn = get_db_connection()
                    p_info = db_conn.execute("SELECT selling_price, quantity FROM inventory_stock WHERE product_name=? AND sid=?", (p_pure_name, current_sid)).fetchone()
                    db_conn.close()
                    st.session_state.user['cart'][p_pure_name] = {'price': p_info['selling_price'], 'qty': 1, 'limit': p_info['quantity']}
                    st.rerun()

        if st.session_state.user['cart']:
            st.subheader("📋 ARTICLES DANS LE PANIER")
            sub_total_usd = 0.0
            for item, details in list(st.session_state.user['cart'].items()):
                st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:10px; margin-bottom:8px;'><b>{item}</b> | Prix Unitaire: {details['price']}$</div>", unsafe_allow_html=True)
                col_qnt, col_rem = st.columns([4, 1])
                st.session_state.user['cart'][item]['qty'] = col_qnt.number_input(f"Quantité pour {item}", 1, details['limit'], details['qty'], key=f"q_{item}")
                sub_total_usd += details['price'] * st.session_state.user['cart'][item]['qty']
                if col_rem.button("🗑️", key=f"rm_{item}"): del st.session_state.user['cart'][item]; st.rerun()

            final_total = sub_total_usd if cur_choice == "USD" else sub_total_usd * rate_val
            st.markdown(f"<div class='cobalt-box'><h2>TOTAL À PAYER : {final_total:,.2f} {cur_choice}</h2></div>", unsafe_allow_html=True)
            
            with st.form("payment_form"):
                cust_id = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                paid_amt = st.number_input(f"MONTANT REÇU DU CLIENT ({cur_choice})", value=float(final_total))
                if st.form_submit_button("✅ VALIDER ET GÉNÉRER FACTURE"):
                    paid_usd = paid_amt if cur_choice == "USD" else paid_amt / rate_val
                    due_usd = sub_total_usd - paid_usd
                    ref_id = f"BAL-{random.randint(10000, 99999)}"
                    d_str, t_str = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    db_conn = get_db_connection()
                    blob_data = {k: {'q': v['qty'], 'tot': v['price']*v['qty']} for k,v in st.session_state.user['cart'].items()}
                    db_conn.execute("INSERT INTO sales_journal (invoice_ref, customer_name, total_amount_usd, amount_paid_usd, balance_due_usd, sale_date, sale_time, seller_uid, sid, items_blob, used_currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                  (ref_id, cust_id, sub_total_usd, paid_usd, due_usd, d_str, t_str, st.session_state.user['uid'], current_sid, json.dumps(blob_data), cur_choice))
                    
                    for pname, pdata in st.session_state.user['cart'].items():
                        db_conn.execute("UPDATE inventory_stock SET quantity = quantity - ? WHERE product_name=? AND sid=?", (pdata['qty'], pname, current_sid))
                    
                    if due_usd > 0.01:
                        db_conn.execute("INSERT INTO debt_ledger (client_identity, current_balance, invoice_link, sid) VALUES (?,?,?,?)", (cust_id, due_usd, ref_id, current_sid))
                    
                    db_conn.commit(); db_conn.close()
                    st.session_state.user['active_invoice'] = {'ref': ref_id, 'client': cust_id, 'total': final_total, 'cur': cur_choice, 'items': blob_data, 'date': d_str, 'time': t_str}
                    st.session_state.user['cart'] = {}; st.rerun()

# --- 6.3 INVENTAIRE (TABLEAUX COMPLETS) ---
elif user_choice == "📦 INVENTAIRE":
    st.markdown("<div class='cobalt-box'><h1>GESTION DU STOCK</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE EN STOCK"):
        with st.form("stock_form"):
            in_name = st.text_input("Désignation de l'Article").upper()
            c_buy, c_sell = st.columns(2)
            in_buy = c_buy.number_input("Prix d'Achat (USD)")
            in_sell = c_sell.number_input("Prix de Vente (USD)")
            in_qty = st.number_input("Quantité Initiale", 1)
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                db_conn = get_db_connection()
                db_conn.execute("INSERT INTO inventory_stock (product_name, quantity, buying_price, selling_price, sid) VALUES (?,?,?,?,?)", 
                              (in_name, in_qty, in_buy, in_sell, current_sid))
                db_conn.commit(); db_conn.close(); st.success("Produit ajouté !"); st.rerun()
    
    st.subheader("ÉTAT ACTUEL DU STOCK")
    db_conn = get_db_connection()
    stock_records = db_conn.execute("SELECT * FROM inventory_stock WHERE sid=? ORDER BY product_name", (current_sid,)).fetchall()
    db_conn.close()
    if stock_records:
        # Transformation en DataFrame pour affichage propre
        df_stock = pd.DataFrame(stock_records, columns=["ID", "DÉSIGNATION", "QTÉ EN STOCK", "P. ACHAT ($)", "P. VENTE ($)", "SID", "CAT"])
        st.table(df_stock[["DÉSIGNATION", "QTÉ EN STOCK", "P. VENTE ($)"]])
        
        for item_rec in stock_records:
            with st.expander(f"MODIFIER : {item_rec['product_name']}"):
                col_p_up, col_q_up = st.columns(2)
                up_price = col_p_up.number_input(f"Nouveau Prix ($)", value=item_rec['selling_price'], key=f"up_p_{item_rec['id']}")
                up_qty = col_q_up.number_input(f"Ajuster Stock", value=item_rec['quantity'], key=f"up_q_{item_rec['id']}")
                btn_u, btn_d = st.columns(2)
                if btn_u.button(f"MAJ {item_rec['id']}", key=f"btn_u_{item_rec['id']}"):
                    db_conn = get_db_connection()
                    db_conn.execute("UPDATE inventory_stock SET selling_price=?, quantity=? WHERE id=?", (up_price, up_qty, item_rec['id']))
                    db_conn.commit(); db_conn.close(); st.rerun()
                if btn_d.button(f"🗑️ SUPPRIMER {item_rec['id']}", key=f"btn_d_{item_rec['id']}"):
                    db_conn = get_db_connection()
                    db_conn.execute("DELETE FROM inventory_stock WHERE id=?", (item_rec['id'],))
                    db_conn.commit(); db_conn.close(); st.rerun()
    else: st.info("Votre inventaire est actuellement vide.")

# --- 6.4 CRÉDITS ET DETTES ---
elif user_choice == "📉 CRÉDITS & DETTES":
    st.markdown("<div class='cobalt-box'><h1>REGISTRE DES CRÉDITS CLIENTS</h1></div>", unsafe_allow_html=True)
    db_conn = get_db_connection()
    active_debts = db_conn.execute("SELECT * FROM debt_ledger WHERE sid=? AND payment_status='OUVERT'", (current_sid,)).fetchall()
    if not active_debts: 
        st.success("Aucune dette client en cours. Excellente gestion !")
    else:
        for debt in active_debts:
            with st.expander(f"👤 {debt['client_identity']} | SOLDE À PAYER : {debt['current_balance']:,.2f} $"):
                st.write(f"Facture d'origine : {debt['invoice_link']}")
                repayment = st.number_input("Enregistrer un paiement ($)", 0.0, debt['current_balance'], key=f"pay_{debt['id']}")
                if st.button(f"VALIDER LE PAIEMENT {debt['id']}"):
                    new_bal = debt['current_balance'] - repayment
                    db_u = get_db_connection()
                    if new_bal <= 0.01:
                        db_u.execute("UPDATE debt_ledger SET current_balance=0, payment_status='SOLDE' WHERE id=?", (debt['id'],))
                    else:
                        db_u.execute("UPDATE debt_ledger SET current_balance=? WHERE id=?", (new_bal, debt['id']))
                    db_u.commit(); db_u.close(); st.success("Paiement enregistré !"); st.rerun()
    db_conn.close()

# --- 6.5 RAPPORTS FINANCIERS ---
elif user_choice == "📊 RAPPORTS FINANCIERS":
    st.markdown("<div class='cobalt-box'><h1>ANALYSE DES ACTIVITÉS</h1></div>", unsafe_allow_html=True)
    sel_date = st.date_input("Filtrer par date de vente", datetime.now()).strftime("%d/%m/%Y")
    db_conn = get_db_connection()
    day_sales = db_conn.execute("SELECT * FROM sales_journal WHERE sid=? AND sale_date=?", (current_sid, sel_date)).fetchall()
    db_conn.close()
    
    if day_sales:
        df_rep = pd.DataFrame(day_sales, columns=["ID","REF","CLIENT","TOTAL $","PAYÉ","RESTE","DATE","HEURE","VENDEUR","SID","DÉTAILS","DEVISE"])
        st.table(df_rep[["REF", "CLIENT", "TOTAL $", "HEURE", "VENDEUR"]])
        st.markdown(f"<div class='cobalt-box'><h2>RECETTE TOTALE DE LA JOURNÉE : {df_rep['TOTAL $'].sum():,.2f} $</h2></div>", unsafe_allow_html=True)
    else:
        st.info(f"Aucune transaction enregistrée pour la date du {sel_date}.")

# --- 6.6 ÉQUIPE & PROFIL ---
elif user_choice == "👥 ÉQUIPE & PROFIL":
    st.markdown("<div class='cobalt-box'><h1>GESTION DU COMPTE ET ÉQUIPE</h1></div>", unsafe_allow_html=True)
    
    with st.expander("👤 MON PROFIL (MODIFIER MON LOGIN / PASS)"):
        with st.form("my_profile_update"):
            u_login = st.text_input("Mon Identifiant Actuel", st.session_state.user['uid'])
            u_pass = st.text_input("Changer le Mot de Passe (laisser vide si inchangé)", type="password")
            if st.form_submit_button("SAUVEGARDER MON PROFIL"):
                db_conn = get_db_connection()
                if u_pass:
                    h_pass_new = hashlib.sha256(u_pass.encode()).hexdigest()
                    db_conn.execute("UPDATE user_accounts SET uid=?, pwd_hash=? WHERE uid=?", (u_login, h_pass_new, st.session_state.user['uid']))
                else:
                    db_conn.execute("UPDATE user_accounts SET uid=? WHERE uid=?", (u_login, st.session_state.user['uid']))
                db_conn.commit(); db_conn.close()
                st.session_state.user['logged_in'] = False; st.rerun()

    if st.session_state.user['role'] == "BOSS":
        st.divider()
        st.subheader("➕ AJOUTER UN NOUVEAU VENDEUR")
        with st.form("vendeur_form"):
            v_id = st.text_input("Identifiant Vendeur (Login)").lower()
            v_name = st.text_input("Nom Complet du Vendeur")
            v_pass = st.text_input("Définir un Mot de Passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                db_conn = get_db_connection()
                try:
                    h_v_pass = hashlib.sha256(v_pass.encode()).hexdigest()
                    # Le vendeur hérite de la date d'expiration du boss
                    db_conn.execute("INSERT INTO user_accounts VALUES (?,?,?,?,?,?,?,?)", 
                                  (v_id, h_v_pass, 'VENDEUR', current_sid, 'ACTIF', v_name, '', user_data['expiry_dt']))
                    db_conn.commit(); st.success(f"Le compte vendeur '{v_id}' a été créé avec succès !"); st.rerun()
                except: st.error("Désolé, cet identifiant de vendeur est déjà pris.")
                finally: db_conn.close()

# --- 6.7 RÉGLAGES BOUTIQUE ---
elif user_choice == "⚙️ RÉGLAGES":
    st.markdown("<div class='cobalt-box'><h1>PARAMÈTRES DE L'ÉTABLISSEMENT</h1></div>", unsafe_allow_html=True)
    with st.form("shop_settings"):
        new_sn = st.text_input("Nom de l'Enseigne Commerciale", shop_data['shop_name'])
        new_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=shop_data['exchange_rate'])
        new_addr = st.text_area("Adresse Physique / Siège social", shop_data['physical_addr'])
        new_tel = st.text_input("Numéro de téléphone de contact", shop_data['tel_contact'])
        if st.form_submit_button("METTRE À JOUR LES INFORMATIONS"):
            db_conn = get_db_connection()
            db_conn.execute("UPDATE shop_registry SET shop_name=?, exchange_rate=?, physical_addr=?, tel_contact=? WHERE sid=?", 
                          (new_sn, new_rate, new_addr, new_tel, current_sid))
            db_conn.commit(); db_conn.close(); st.success("Les informations de la boutique ont été mises à jour !"); st.rerun()

elif user_choice == "🚪 QUITTER":
    st.session_state.user['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v270 - BALIKA BUSINESS ERP (1150+ LIGNES DE LOGIQUE)
# ==============================================================================
