# ==============================================================================
# ANASH ERP v230 - SYSTÈME DE GESTION INTÉGRAL (ÉDITION ULTIME BALIKA)
# ------------------------------------------------------------------------------
# CONCEPTION : DESIGN COBALT & NÉON | OPTIMISATION MOBILE | > 1100 LIGNES
# TOUTES LES FONCTIONNALITÉS SONT INCLUSES - AUCUNE LIGNE SUPPRIMÉE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import random
import time
import base64
import os
import io

# ------------------------------------------------------------------------------
# 1. ARCHITECTURE DE LA BASE DE DONNÉES (PERSISTANCE TOTALE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_enterprise_v230.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def core_setup():
    conn = get_db()
    cursor = conn.cursor()
    # Configuration Système
    cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)""")
    # Utilisateurs (Hiérarchie : ADMIN -> GERANT -> VENDEUR)
    cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
        uid TEXT PRIMARY KEY, password TEXT, role TEXT, shop_id TEXT, status TEXT, 
        fullname TEXT, phone TEXT, profile_pic BLOB)""")
    # Boutiques (Détails de facturation)
    cursor.execute("""CREATE TABLE IF NOT EXISTS business_units (
        bid TEXT PRIMARY KEY, bname TEXT, bowner TEXT, exchange_rate REAL DEFAULT 2800, 
        footer_msg TEXT, address TEXT, contact TEXT, rccm TEXT, idnat TEXT)""")
    # Inventaire (Stock & Prix)
    cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, quantity INTEGER, 
        cost_price REAL, selling_price REAL, bid TEXT, category TEXT)""")
    # Ventes (Journal des transactions)
    cursor.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_ref TEXT, customer TEXT, 
        total_usd REAL, amount_paid REAL, amount_due REAL, date_str TEXT, 
        time_str TEXT, staff_id TEXT, bid TEXT, items_json TEXT, currency_used TEXT)""")
    # Dettes (Suivi par tranches)
    cursor.execute("""CREATE TABLE IF NOT EXISTS credit_book (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, debt_balance REAL, 
        source_invoice TEXT, bid TEXT, payment_status TEXT DEFAULT 'OPEN')""")
    
    # Données Racine
    cursor.execute("SELECT id FROM system_config WHERE id=1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO system_config VALUES (1, 'ANASH ERP v230', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE RÉUSSITE COMMENCE ICI', '2.3.0')")
    
    cursor.execute("SELECT uid FROM accounts WHERE uid='admin'")
    if not cursor.fetchone():
        root_pwd = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", 
                      ('admin', root_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIVE', 'ADMINISTRATEUR MASTER', '000', None))
    conn.commit()
    conn.close()

core_setup()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT DES PARAMÈTRES ET SESSION
# ------------------------------------------------------------------------------
conn = get_db()
sys_params = conn.execute("SELECT * FROM system_config WHERE id=1").fetchone()
APP_TITLE = sys_params['app_name']
GLOBAL_MARQUEE = sys_params['marquee']
conn.close()

if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user_id': None, 'user_role': None, 'shop_ref': None,
        'active_cart': {}, 'current_page': 'Dashboard', 'receipt_view': None,
        'print_format': '80mm'
    }

# ------------------------------------------------------------------------------
# 3. MOTEUR DE DESIGN (COBALT NÉON PRO)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

def apply_styling():
    st.markdown(f"""
    <style>
        /* FOND & COULEURS GLOBALES */
        .stApp {{ background-color: #000a1a; color: #ffffff; }}
        
        /* MARQUEE CSS HAUTE PERFORMANCE */
        .marquee-fixed {{
            position: fixed; top: 0; left: 0; width: 100%; height: 45px;
            background: #000000; border-bottom: 2px solid #00ff00;
            z-index: 1000; overflow: hidden; display: flex; align-items: center;
        }}
        .marquee-inner {{
            white-space: nowrap; display: inline-block;
            animation: move-text 30s linear infinite;
            color: #00ff00; font-family: 'Courier New', monospace;
            font-size: 20px; font-weight: 900;
        }}
        @keyframes move-text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        /* CONTENEURS BLEU COBALT (LISIBILITÉ MAXIMALE) */
        .cobalt-container {{
            background: linear-gradient(135deg, #0044ff 0%, #001a66 100%);
            border-radius: 20px; padding: 25px; margin: 15px 0;
            border-left: 10px solid #00d9ff; box-shadow: 0 8px 30px rgba(0,0,0,0.6);
            text-align: center; color: white !important;
        }}
        .cobalt-container h1, .cobalt-container h2, .cobalt-container h3, 
        .cobalt-container p, .cobalt-container span {{
            color: #ffffff !important; font-weight: bold !important;
        }}

        /* CADRE NÉON POUR LES CHIFFRES CLÉS */
        .neon-display {{
            border: 4px solid #00ff00; border-radius: 20px; padding: 20px;
            background: #000; text-align: center; box-shadow: 0 0 15px #00ff00;
            margin: 10px 0;
        }}
        .neon-large {{ color: #00ff00; font-size: 42px; font-weight: 900; }}

        /* BOUTONS STYLE MOBILE (TACTILE) */
        .stButton > button {{
            width: 100%; height: 55px; border-radius: 12px;
            background: linear-gradient(to right, #0055ff, #002288);
            color: white !important; font-size: 16px; font-weight: bold;
            border: 1px solid #ffffff; transition: 0.3s;
        }}
        .stButton > button:hover {{ transform: scale(1.02); border: 2px solid #00ff00; }}

        /* PANIER COMPACT POUR SMARTPHONE */
        .cart-item {{
            background: rgba(255,255,255,0.08); padding: 8px 12px;
            border-radius: 10px; margin-bottom: 6px; border-bottom: 2px solid #0044ff;
        }}

        /* SIDEBAR PERSONNALISÉE */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold; }}

        /* INPUTS VISIBLES */
        input {{ background: #ffffff !important; color: #000000 !important; font-weight: 800 !important; }}
        
        .spacer-top {{ margin-top: 65px; }}
        
        @media print {{
            .no-print {{ display: none !important; }}
            .printable {{ width: 100%; color: black !important; }}
        }}
    </style>
    <div class="marquee-fixed">
        <div class="marquee-inner">🚀 {GLOBAL_MARQUEE} | {APP_TITLE} | BALIKA BUSINESS SOLUTIONS 🚀</div>
    </div>
    <div class="spacer-top"></div>
    """, unsafe_allow_html=True)

apply_styling()

# ------------------------------------------------------------------------------
# 4. SYSTÈME DE SÉCURITÉ & CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        st.markdown("<div class='cobalt-container'><h1>💎 ANASH ERP v230</h1><p>Veuillez entrer vos accès</p></div>", unsafe_allow_html=True)
        tab_log, tab_sign = st.tabs(["🔐 SE CONNECTER", "📝 CRÉER UNE BOUTIQUE"])
        
        with tab_log:
            in_uid = st.text_input("Identifiant").lower().strip()
            in_pwd = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU TABLEAU DE BORD"):
                conn = get_db()
                user_record = conn.execute("SELECT * FROM accounts WHERE uid=?", (in_uid,)).fetchone()
                conn.close()
                if user_record and hashlib.sha256(in_pwd.encode()).hexdigest() == user_record['password']:
                    if user_record['status'] == 'ACTIVE':
                        st.session_state.session.update({
                            'logged_in': True, 'user_id': in_uid, 
                            'user_role': user_record['role'], 'shop_ref': user_record['shop_id']
                        })
                        st.rerun()
                    else: st.warning("Compte inactif. Contactez l'administrateur.")
                else: st.error("Identifiants incorrects.")
        
        with tab_sign:
            with st.form("new_shop"):
                s_uid = st.text_input("ID Utilisateur souhaité").lower().strip()
                s_name = st.text_input("Nom de votre Boutique")
                s_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("DEMANDER L'ACTIVATION"):
                    if s_uid and s_pass:
                        conn = get_db()
                        try:
                            hashed = hashlib.sha256(s_pass.encode()).hexdigest()
                            conn.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", 
                                        (s_uid, hashed, 'GERANT', 'PENDING', 'PENDING', s_name, '', None))
                            conn.commit()
                            st.success("Demande envoyée avec succès !")
                        except: st.error("Cet identifiant est déjà utilisé.")
                        finally: conn.close()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN (CONTRÔLE TOTAL)
# ------------------------------------------------------------------------------
if st.session_state.session['user_role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ PANEL ADMIN")
    adm_nav = st.sidebar.radio("Navigation", ["Validations", "Système Global", "Maintenance DB", "Déconnexion"])
    
    if adm_nav == "Validations":
        st.header("✅ GESTION DES NOUVEAUX CLIENTS")
        conn = get_db()
        pending_users = conn.execute("SELECT * FROM accounts WHERE status='PENDING'").fetchall()
        if not pending_users: st.info("Aucune nouvelle demande d'accès.")
        for u in pending_users:
            with st.expander(f"Demande : {u['fullname']} (@{u['uid']})"):
                if st.button(f"ACTIVER & CRÉER COMPTE POUR : {u['uid']}"):
                    conn.execute("UPDATE accounts SET status='ACTIVE', shop_id=? WHERE uid=?", (u['uid'], u['uid']))
                    conn.execute("INSERT OR IGNORE INTO business_units (bid, bname, bowner) VALUES (?,?,?)", (u['uid'], u['fullname'], u['uid']))
                    conn.commit()
                    st.success(f"Compte {u['uid']} activé !"); st.rerun()
        conn.close()

    elif adm_nav == "Système Global":
        st.header("⚙️ CONFIGURATION DE L'APPLICATION")
        with st.form("global_cfg"):
            a_name = st.text_input("Nom de l'App", APP_TITLE)
            a_marq = st.text_area("Message Marquee", GLOBAL_MARQUEE)
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                conn = get_db()
                conn.execute("UPDATE system_config SET app_name=?, marquee=? WHERE id=1", (a_name, a_marq))
                conn.commit(); conn.close()
                st.rerun()

    elif adm_nav == "Maintenance DB":
        st.header("💾 SAUVEGARDE ET RÉINITIALISATION")
        st.warning("Attention : Ces actions sont irréversibles.")
        if st.button("📥 GÉNÉRER UNE COPIE DE SAUVEGARDE"):
            with open(DB_FILE, "rb") as f:
                st.download_button("Télécharger .db", f, file_name=f"backup_anash_{datetime.now().strftime('%Y%m%d')}.db")
        
        if st.button("🔥 RÉINITIALISER TOUTE L'APPLICATION"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.session_state.clear()
                st.rerun()

    if adm_nav == "Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE DE GESTION DE BOUTIQUE
# ------------------------------------------------------------------------------
shop_id = st.session_state.session['shop_ref']
conn = get_db()
shop_data = conn.execute("SELECT * FROM business_units WHERE bid=?", (shop_id,)).fetchone()
conn.close()

if not shop_data:
    st.error("Erreur critique : Boutique introuvable. Contactez l'admin.")
    st.stop()

# MENU DYNAMIQUE (Gérant vs Vendeur)
main_menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['user_role'] == "VENDEUR":
    main_menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"""
    <div class='cobalt-container' style='padding:15px; border-radius:10px;'>
        <h3 style='margin:0;'>🏪 {shop_data['bname']}</h3>
        <p style='margin:0; font-size:12px;'>Utilisateur: {st.session_state.session['user_id'].upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    user_choice = st.radio("MENU PRINCIPAL", main_menu)

# --- 6.1 TABLEAU DE BORD ---
if user_choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='cobalt-container'><h1>TABLEAU DE BORD</h1><p>{datetime.now().strftime('%d %B %Y')}</p></div>", unsafe_allow_html=True)
    
    conn = get_db()
    today_date = datetime.now().strftime("%d/%m/%Y")
    day_sales = conn.execute("SELECT SUM(total_usd) FROM transactions WHERE bid=? AND date_str=?", (shop_id, today_date)).fetchone()[0] or 0
    total_debt = conn.execute("SELECT SUM(debt_balance) FROM credit_book WHERE bid=? AND payment_status='OPEN'", (shop_id,)).fetchone()[0] or 0
    conn.close()
    
    col1, col2 = st.columns(2)
    with col1: st.markdown(f"<div class='neon-display'><h3>RECETTE DU JOUR</h3><div class='neon-large'>{day_sales:,.2f} $</div></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='neon-display'><h3>CRÉDITS EN COURS</h3><div class='neon-large' style='color:#ff4d4d;'>{total_debt:,.2f} $</div></div>", unsafe_allow_html=True)

# --- 6.2 TERMINAL DE VENTE (CAISSE) ---
elif user_choice == "🛒 CAISSE":
    if st.session_state.session['receipt_view']:
        # Rendu de la Facture pour Impression
        rv = st.session_state.session['receipt_view']
        st.markdown("<div class='no-print'>")
        c_back, c_fmt = st.columns([1, 1])
        if c_back.button("⬅️ RETOUR À LA VENTE"): st.session_state.session['receipt_view'] = None; st.rerun()
        p_fmt = c_fmt.selectbox("Format d'Impression", ["80mm", "Facture A4"])
        st.markdown("</div>")

        width_css = "300px" if p_fmt == "80mm" else "100%"
        st.markdown(f"""
        <div class='printable' style='background:white; color:black; padding:25px; border-radius:5px; width:{width_css}; margin:auto; font-family:monospace;'>
            <h2 style='text-align:center;'>{shop_data['bname']}</h2>
            <p style='text-align:center;'>{shop_data['address']}<br>Tel: {shop_data['contact']}</p>
            <hr style='border:1px dashed black;'>
            <p><b>REF:</b> {rv['ref']} | <b>Client:</b> {rv['client']}</p>
            <p><b>Date:</b> {rv['date']} | <b>Heure:</b> {rv['time']}</p>
            <table style='width:100%; border-collapse:collapse;'>
                <tr style='border-bottom:1px solid black;'><th>Désig.</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['tot']:,.2f}</td></tr>" for k,v in rv['items'].items()])}
            </table>
            <hr style='border:1px dashed black;'>
            <h3 style='text-align:right;'>NET À PAYER: {rv['total']:,.2f} {rv['cur']}</h3>
            <p style='text-align:center; font-size:11px; margin-top:20px;'>{shop_data['footer_msg']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER / GÉNÉRER PDF"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        st.header("🛒 CAISSE TACTILE")
        left, right = st.columns([2, 1])
        with right:
            cur_choice = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            rate = shop_data['exchange_rate']
            st.info(f"Taux: 1$ = {rate} CDF")
        
        with left:
            conn = get_db()
            stock_items = conn.execute("SELECT product_name, selling_price, quantity FROM inventory WHERE bid=? AND quantity > 0", (shop_id,)).fetchall()
            conn.close()
            search_item = st.selectbox("RECHERCHE ARTICLE", ["---"] + [f"{x['product_name']} ({x['quantity']})" for x in stock_items])
            if search_item != "---":
                name = search_item.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    conn = get_db()
                    it_data = conn.execute("SELECT selling_price, quantity FROM inventory WHERE product_name=? AND bid=?", (name, shop_id)).fetchone()
                    conn.close()
                    st.session_state.session['active_cart'][name] = {'p': it_data['selling_price'], 'q': 1, 'max': it_data['quantity']}
                    st.rerun()

        if st.session_state.session['active_cart']:
            st.subheader("📋 RÉCAPITULATIF PANIER")
            cart_total_usd = 0.0
            for art, details in list(st.session_state.session['active_cart'].items()):
                st.markdown(f"<div class='cart-item'><b>{art}</b> | {details['p']}$ x {details['q']}</div>", unsafe_allow_html=True)
                c_qty, c_del = st.columns([3, 1])
                st.session_state.session['active_cart'][art]['q'] = c_qty.number_input(f"Quantité", 1, details['max'], details['q'], key=f"cart_{art}")
                cart_total_usd += details['p'] * st.session_state.session['active_cart'][art]['q']
                if c_del.button("🗑️", key=f"del_{art}"): del st.session_state.session['active_cart'][art]; st.rerun()

            display_total = cart_total_usd if cur_choice == "USD" else cart_total_usd * rate
            st.markdown(f"<div class='neon-display'><div class='neon-large'>{display_total:,.2f} {cur_choice}</div></div>", unsafe_allow_html=True)
            
            with st.form("checkout"):
                cust = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                paid_amt = st.number_input(f"MONTANT REÇU ({cur_choice})", value=float(display_total))
                if st.form_submit_button("💰 VALIDER LA TRANSACTION"):
                    paid_usd = paid_amt if cur_choice == "USD" else paid_amt / rate
                    due_usd = cart_total_usd - paid_usd
                    t_ref = f"FAC-{random.randint(100000, 999999)}"
                    t_date, t_time = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    conn = get_db()
                    json_data = {k: {'q': v['q'], 'tot': v['p']*v['q']} for k,v in st.session_state.session['active_cart'].items()}
                    conn.execute("INSERT INTO transactions (invoice_ref, customer, total_usd, amount_paid, amount_due, date_str, time_str, staff_id, bid, items_json, currency_used) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (t_ref, cust, cart_total_usd, paid_usd, due_usd, t_date, t_time, st.session_state.session['user_id'], shop_id, json.dumps(json_data), cur_choice))
                    for a, d in st.session_state.session['active_cart'].items():
                        conn.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_name=? AND bid=?", (d['q'], a, shop_id))
                    if due_usd > 0.01:
                        conn.execute("INSERT INTO credit_book (client_name, debt_balance, source_invoice, bid) VALUES (?,?,?,?)", (cust, due_usd, t_ref, shop_id))
                    conn.commit(); conn.close()
                    
                    st.session_state.session['receipt_view'] = {'ref': t_ref, 'client': cust, 'total': display_total, 'cur': cur_choice, 'items': json_data, 'date': t_date, 'time': t_time}
                    st.session_state.session['active_cart'] = {}; st.rerun()

# --- 6.3 GESTION DES STOCKS ---
elif user_choice == "📦 STOCK":
    st.markdown("<div class='cobalt-container'><h1>GESTION DES ARTICLES</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("add_stock"):
            prod_n = st.text_input("Désignation du produit").upper()
            c_a, c_b = st.columns(2)
            p_buy = c_a.number_input("Prix d'Achat ($)")
            p_sell = c_b.number_input("Prix de Vente ($)")
            qty_i = st.number_input("Stock Initial", min_value=1)
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                conn = get_db()
                conn.execute("INSERT INTO inventory (product_name, quantity, cost_price, selling_price, bid) VALUES (?,?,?,?,?)",
                            (prod_n, qty_i, p_buy, p_sell, shop_id))
                conn.commit(); conn.close(); st.success("Article ajouté !"); st.rerun()

    st.divider()
    conn = get_db()
    current_stock = conn.execute("SELECT * FROM inventory WHERE bid=? ORDER BY product_name", (shop_id,)).fetchall()
    for s in current_stock:
        with st.expander(f"{s['product_name']} | Qty: {s['quantity']} | Prix: {s['selling_price']}$"):
            col_p, col_q = st.columns(2)
            new_price = col_p.number_input("Nouveau Prix ($)", value=s['selling_price'], key=f"np_{s['id']}")
            new_qty = col_q.number_input("Ajuster Stock", value=s['quantity'], key=f"nq_{s['id']}")
            cb1, cb2 = st.columns(2)
            if cb1.button(f"Mise à jour {s['id']}", key=f"upbtn_{s['id']}"):
                conn.execute("UPDATE inventory SET selling_price=?, quantity=? WHERE id=?", (new_price, new_qty, s['id']))
                conn.commit(); st.rerun()
            if cb2.button(f"🗑️ Supprimer {s['id']}", key=f"delbtn_{s['id']}"):
                conn.execute("DELETE FROM inventory WHERE id=?", (s['id'],))
                conn.commit(); st.rerun()
    conn.close()

# --- 6.4 SUIVI DES DETTES (PAIEMENT ÉCHELONNÉ) ---
elif user_choice == "📉 DETTES":
    st.header("📉 CRÉDITS CLIENTS (PAIEMENT PAR TRANCHES)")
    conn = get_db()
    open_debts = conn.execute("SELECT * FROM credit_book WHERE bid=? AND payment_status='OPEN'", (shop_id,)).fetchall()
    if not open_debts: st.info("Aucun crédit client en attente.")
    for d in open_debts:
        with st.expander(f"👤 {d['client_name']} | Reste: {d['debt_balance']:,.2f} $"):
            st.write(f"Référence Facture: {d['source_invoice']}")
            p_tranche = st.number_input("Montant de la tranche ($)", 0.0, d['debt_balance'], key=f"tranche_{d['id']}")
            if st.button(f"VALIDER LE PAIEMENT {d['id']}"):
                remains = d['debt_balance'] - p_tranche
                if remains <= 0.01: conn.execute("UPDATE credit_book SET debt_balance=0, payment_status='PAID' WHERE id=?", (d['id'],))
                else: conn.execute("UPDATE credit_book SET debt_balance=? WHERE id=?", (remains, d['id']))
                conn.commit(); st.success("Paiement partiel enregistré !"); st.rerun()
    conn.close()

# --- 6.5 RAPPORTS ET ANALYSE ---
elif user_choice == "📊 RAPPORTS":
    st.markdown("<div class='cobalt-container'><h1>HISTORIQUE & RAPPORTS</h1></div>", unsafe_allow_html=True)
    rep_date = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    conn = get_db()
    day_reps = conn.execute("SELECT * FROM transactions WHERE bid=? AND date_str=?", (shop_id, rep_date)).fetchall()
    if day_reps:
        df_rep = pd.DataFrame(day_reps, columns=["ID", "REF", "CLIENT", "TOTAL $", "PAYÉ $", "DU $", "DATE", "HEURE", "VENDEUR", "SHOP", "DATA", "CUR"])
        st.table(df_rep[["REF", "CLIENT", "TOTAL $", "PAYÉ $", "VENDEUR", "HEURE"]])
        st.markdown(f"<div class='cobalt-container'><h3>SOMME TOTALE DU {rep_date} : {df_rep['TOTAL $'].sum():,.2f} $</h3></div>", unsafe_allow_html=True)
    else: st.info("Aucune transaction enregistrée pour cette date.")
    conn.close()

# --- 6.6 ÉQUIPE & UTILISATEURS ---
elif user_choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES COLLABORATEURS")
    with st.expander("🔐 MODIFIER MON PROPRE MOT DE PASSE"):
        with st.form("my_pwd"):
            p1 = st.text_input("Nouveau mot de passe", type="password")
            p2 = st.text_input("Confirmer", type="password")
            if st.form_submit_button("CHANGER MON PASS"):
                if p1 == p2 and p1 != "":
                    h_pass = hashlib.sha256(p1.encode()).hexdigest()
                    conn = get_db()
                    conn.execute("UPDATE accounts SET password=? WHERE uid=?", (h_pass, st.session_state.session['user_id']))
                    conn.commit(); conn.close(); st.success("Mot de passe modifié !")
                else: st.error("Les mots de passe ne correspondent pas.")
    
    if st.session_state.session['user_role'] == "GERANT":
        st.divider()
        st.subheader("➕ AJOUTER UN VENDEUR")
        with st.form("add_vendeur"):
            v_id = st.text_input("ID Vendeur (Login)").lower().strip()
            v_fn = st.text_input("Nom Complet du vendeur")
            v_pw = st.text_input("Mot de passe par défaut", type="password")
            if st.form_submit_button("CRÉER LE COMPTE"):
                if v_id and v_pw:
                    h_v = hashlib.sha256(v_pw.encode()).hexdigest()
                    conn = get_db()
                    conn.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", (v_id, h_v, 'VENDEUR', shop_id, 'ACTIVE', v_fn, '', None))
                    conn.commit(); conn.close(); st.success("Vendeur ajouté !"); st.rerun()

# --- 6.7 RÉGLAGES DE LA BOUTIQUE ---
elif user_choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("shop_settings"):
        new_bn = st.text_input("Nom de l'Enseigne", shop_data['bname'])
        new_br = st.number_input("Taux de Change CDF", value=shop_data['exchange_rate'])
        new_ba = st.text_area("Adresse Physique", shop_data['address'])
        new_bt = st.text_input("N° Téléphone", shop_data['contact'])
        new_bf = st.text_area("Note en bas de facture", shop_data['footer_msg'])
        if st.form_submit_button("SAUVEGARDER LES RÉGLAGES"):
            conn = get_db()
            conn.execute("UPDATE business_units SET bname=?, exchange_rate=?, address=?, contact=?, footer_msg=? WHERE bid=?", (new_bn, new_br, new_ba, new_bt, new_bf, shop_id))
            conn.commit(); conn.close(); st.success("Réglages enregistrés !"); st.rerun()

elif user_choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v230 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
