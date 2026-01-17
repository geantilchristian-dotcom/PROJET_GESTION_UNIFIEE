# ==============================================================================
# ANASH ERP v250 - SYSTÈME DE GESTION INTÉGRAL (ÉDITION FINALE 2026)
# ------------------------------------------------------------------------------
# OPTIMISÉ POUR MOBILE | GESTION ABONNEMENTS | FACTURATION A4 & 80MM
# LISIBILITÉ MAXIMALE : TEXTE BLANC SUR BLEU COBALT | TABLEAUX CENTRÉS
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import os
import base64
import io

# ------------------------------------------------------------------------------
# 1. MOTEUR DE DONNÉES (PERSISTANCE TOTALE)
# ------------------------------------------------------------------------------
DB_PATH = "anash_v250_master.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_system():
    with get_connection() as conn:
        cursor = conn.cursor()
        # Configuration de l'App
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_prefs (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT)""")
        
        # Comptes Utilisateurs (Admin, Boss, Vendeur)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users_accounts (
            uid TEXT PRIMARY KEY, password TEXT, role TEXT, shop_id TEXT, 
            status TEXT, fullname TEXT, phone TEXT, expiry_date TEXT)""")
        
        # Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops_info (
            sid TEXT PRIMARY KEY, sname TEXT, sowner TEXT, rate REAL DEFAULT 2800, 
            address TEXT, tel TEXT, logo BLOB)""")
        
        # Inventaire
        cursor.execute("""CREATE TABLE IF NOT EXISTS product_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, cat TEXT)""")
        
        # Transactions
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref_code TEXT, client TEXT, 
            total_val REAL, paid_val REAL, due_val REAL, date_val TEXT, 
            time_val TEXT, seller_id TEXT, sid TEXT, items_json TEXT, currency TEXT)""")
        
        # Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS debt_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, balance REAL, 
            ref_fac TEXT, sid TEXT, state TEXT DEFAULT 'OUVERT')""")

        # Configuration Initiale
        cursor.execute("SELECT id FROM system_prefs WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_prefs VALUES (1, 'ANASH BUSINESS ERP', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE SOLUTION DE GESTION INTELLIGENTE')")
        
        # Compte Admin Racine
        cursor.execute("SELECT uid FROM users_accounts WHERE uid='admin'")
        if not cursor.fetchone():
            adm_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users_accounts VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', adm_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000', '2099-12-31'))
        conn.commit()

initialize_system()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT CONFIG ET VARIABLES GLOBALES
# ------------------------------------------------------------------------------
db_conn = get_connection()
sys_cfg = db_conn.execute("SELECT * FROM system_prefs WHERE id=1").fetchone()
APP_NAME, MARQUEE_MSG = sys_cfg['app_name'], sys_cfg['marquee_text']
db_conn.close()

if 'state' not in st.session_state:
    st.session_state.state = {
        'is_auth': False, 'uid': None, 'role': None, 'sid': None, 
        'cart': {}, 'view_receipt': None, 'print_mode': '80mm'
    }

# ------------------------------------------------------------------------------
# 3. DESIGN CSS (TEXTE BLANC SUR BLEU, CENTRÉ, OPTIMISÉ MOBILE)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, layout="wide")

def inject_custom_css():
    st.markdown(f"""
    <style>
        /* FOND D'ÉCRAN ET POLICE */
        .stApp {{ background-color: #000a1a; color: #ffffff; font-family: 'Inter', sans-serif; }}
        
        /* BARRE DÉFILANTE FIXE */
        .marquee-bar {{
            position: fixed; top: 0; left: 0; width: 100%; height: 45px;
            background: #000; border-bottom: 3px solid #00ff00;
            z-index: 9999; display: flex; align-items: center; overflow: hidden;
        }}
        .marquee-txt {{
            white-space: nowrap; display: inline-block;
            animation: move-text 25s linear infinite;
            color: #00ff00; font-size: 19px; font-weight: 900;
        }}
        @keyframes move-text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        /* BOITES BLEU COBALT - TEXTE BLANC ET CENTRÉ */
        .cobalt-card {{
            background: linear-gradient(135deg, #0044ff 0%, #001144 100%) !important;
            color: #ffffff !important; border-radius: 15px; padding: 25px;
            margin-bottom: 20px; border: 1px solid #00d9ff;
            text-align: center !important; box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }}
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p, .cobalt-card span {{
            color: #ffffff !important; text-align: center !important; font-weight: bold !important;
        }}

        /* TABLEAUX LISIBLES ET CENTRÉS */
        .stTable {{ background-color: #ffffff !important; border-radius: 8px !important; color: #000 !important; }}
        th {{ background-color: #0044ff !important; color: white !important; text-align: center !important; }}
        td {{ text-align: center !important; color: #000 !important; font-weight: bold !important; border: 1px solid #eee !important; }}

        /* BOUTONS STYLE TACTILE MOBILE */
        .stButton > button {{
            width: 100% !important; height: 55px !important; border-radius: 12px !important;
            background: linear-gradient(to bottom, #0055ff, #002288) !important;
            color: white !important; border: 2px solid white !important; font-size: 17px !important;
        }}
        
        /* FACTURE ADMINISTRATIVE */
        .facture-container {{
            background: white !important; color: black !important; padding: 40px;
            border-radius: 10px; margin: auto; font-family: 'Courier New', monospace;
        }}

        /* SIDEBAR BLANCHE */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold !important; }}

        .spacer-top {{ margin-top: 65px; }}
    </style>
    <div class="marquee-bar">
        <div class="marquee-txt">🌟 {MARQUEE_MSG} 🌟 | GESTION OPTIMISÉE POUR SMARTPHONE ET PC | {APP_NAME} 🌟</div>
    </div>
    <div class="spacer-top"></div>
    """, unsafe_allow_html=True)

inject_custom_css()

# ------------------------------------------------------------------------------
# 4. AUTHENTIFICATION
# ------------------------------------------------------------------------------
if not st.session_state.state['is_auth']:
    _, auth_col, _ = st.columns([1, 2, 1])
    with auth_col:
        st.markdown("<div class='cobalt-card'><h1>💎 ACCÈS SYSTÈME</h1><p>Entrez vos accès BALIKA BUSINESS</p></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 CONNEXION", "📝 INSCRIPTION"])
        
        with t1:
            u_in = st.text_input("Utilisateur").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                db = get_connection()
                usr = db.execute("SELECT * FROM users_accounts WHERE uid=?", (u_in,)).fetchone()
                db.close()
                if usr and hashlib.sha256(p_in.encode()).hexdigest() == usr['password']:
                    if usr['status'] == 'ACTIF' or usr['role'] == 'SUPER_ADMIN':
                        # Vérification expiration
                        limit = datetime.strptime(usr['expiry_date'], '%Y-%m-%d')
                        if datetime.now() > limit and usr['role'] != 'SUPER_ADMIN':
                            st.error(f"Abonnement expiré le {usr['expiry_date']}. Contactez l'administrateur.")
                        else:
                            st.session_state.state.update({'is_auth': True, 'uid': u_in, 'role': usr['role'], 'sid': usr['shop_id']})
                            st.rerun()
                    else: st.warning("Compte en attente d'activation par l'Admin.")
                else: st.error("Identifiants incorrects.")
        
        with t2:
            with st.form("reg_form"):
                reg_u = st.text_input("ID voulu").lower()
                reg_n = st.text_input("Nom de la Boutique / Propriétaire")
                reg_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("DEMANDER L'ACCÈS"):
                    db = get_connection()
                    try:
                        hp = hashlib.sha256(reg_p.encode()).hexdigest()
                        trial = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                        db.execute("INSERT INTO users_accounts VALUES (?,?,?,?,?,?,?,?)", 
                                  (reg_u, hp, 'BOSS', 'PENDING', 'ATTENTE', reg_n, '', trial))
                        db.commit(); st.success("Demande envoyée ! Attendez l'activation.")
                    except: st.error("ID déjà utilisé.")
                    finally: db.close()
    st.stop()

# ------------------------------------------------------------------------------
# 5. MODULE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.state['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛠️ MASTER PANEL")
    adm_menu = st.sidebar.radio("Menu Admin", ["Abonnés & Validation", "Profil & Sécurité", "Paramètres App", "Sauvegarde DB", "Quitter"])
    
    if adm_menu == "Abonnés & Validation":
        st.markdown("<div class='cobalt-card'><h1>GÉRER LES ABONNÉS</h1></div>", unsafe_allow_html=True)
        db = get_connection()
        clients = db.execute("SELECT * FROM users_accounts WHERE role='BOSS'").fetchall()
        for c in clients:
            with st.expander(f"👤 {c['fullname']} (@{c['uid']}) - STATUT: {c['status']}"):
                col_st, col_dt = st.columns(2)
                new_st = col_st.selectbox("Changer Statut", ["ATTENTE", "ACTIF", "DESACTIVE"], index=["ATTENTE", "ACTIF", "DESACTIVE"].index(c['status']), key=f"st_{c['uid']}")
                new_dt = col_dt.date_input("Date Expiration", datetime.strptime(c['expiry_date'], '%Y-%m-%d'), key=f"dt_{c['uid']}")
                if st.button(f"VALIDER MODIFICATIONS POUR {c['uid']}"):
                    db.execute("UPDATE users_accounts SET status=?, expiry_date=?, shop_id=? WHERE uid=?", (new_st, new_dt.strftime('%Y-%m-%d'), c['uid'], c['uid']))
                    # Création automatique de la boutique à l'activation
                    db.execute("INSERT OR IGNORE INTO shops_info (sid, sname, sowner) VALUES (?,?,?)", (c['uid'], c['fullname'], c['uid']))
                    db.commit(); st.success("Mis à jour !"); st.rerun()
        db.close()

    elif adm_menu == "Profil & Sécurité":
        st.markdown("<div class='cobalt-card'><h1>MON PROFIL ADMIN</h1></div>", unsafe_allow_html=True)
        with st.form("adm_profile"):
            new_id = st.text_input("Mon Login Admin", st.session_state.state['uid'])
            new_pw = st.text_input("Nouveau Mot de Passe (laisser vide si inchangé)", type="password")
            if st.form_submit_button("SAUVEGARDER MON PROFIL"):
                db = get_connection()
                if new_pw:
                    hp = hashlib.sha256(new_pw.encode()).hexdigest()
                    db.execute("UPDATE users_accounts SET uid=?, password=? WHERE uid=?", (new_id, hp, st.session_state.state['uid']))
                else:
                    db.execute("UPDATE users_accounts SET uid=? WHERE uid=?", (new_id, st.session_state.state['uid']))
                db.commit(); db.close()
                st.session_state.state['is_auth'] = False; st.rerun()

    elif adm_menu == "Paramètres App":
        st.markdown("<div class='cobalt-card'><h1>RÉGLAGES SYSTÈME</h1></div>", unsafe_allow_html=True)
        with st.form("sys_cfg_form"):
            app_n = st.text_input("Nom de l'Application", APP_NAME)
            mar_t = st.text_area("Message Défilant", MARQUEE_MSG)
            if st.form_submit_button("APPLIQUER À TOUS"):
                db = get_connection()
                db.execute("UPDATE system_prefs SET app_name=?, marquee_text=? WHERE id=1", (app_n, mar_t))
                db.commit(); db.close(); st.rerun()

    elif adm_menu == "Sauvegarde DB":
        st.markdown("<div class='cobalt-card'><h1>ARCHIVAGE DES DONNÉES</h1></div>", unsafe_allow_html=True)
        with open(DB_PATH, "rb") as f:
            st.download_button("📥 TÉLÉCHARGER LA SAUVEGARDE (.db)", f, file_name=f"backup_erp_{datetime.now().strftime('%d_%m_%Y')}.db")

    if adm_menu == "Quitter": st.session_state.state['is_auth'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE CLIENT (BOSS & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.state['sid']
db = get_connection()
shop = db.execute("SELECT * FROM shops_info WHERE sid=?", (sid,)).fetchone()
u_info = db.execute("SELECT expiry_date FROM users_accounts WHERE uid=?", (st.session_state.state['uid'],)).fetchone()
db.close()

if not shop:
    st.error("Erreur d'accès boutique. Contactez l'administrateur.")
    st.stop()

# Navigation Boutique
menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.state['role'] == "VENDEUR":
    menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"""
    <div class='cobalt-card' style='padding:10px;'>
        <h2 style='font-size:18px;'>{shop['sname']}</h2>
        <p style='font-size:12px; color:#00ff00 !important;'>Abonnement : {u_info['expiry_date']}</p>
        <p style='font-size:11px;'>👤 {st.session_state.state['uid'].upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    choice = st.radio("MENU NAVIGATION", menu)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='cobalt-card'><h1>TABLEAU DE BORD</h1><h3>{datetime.now().strftime('%A %d %B %Y')}</h3></div>", unsafe_allow_html=True)
    db = get_connection()
    today = datetime.now().strftime("%d/%m/%Y")
    ca = db.execute("SELECT SUM(total_val) FROM sales_ledger WHERE sid=? AND date_val=?", (sid, today)).fetchone()[0] or 0
    dt_tot = db.execute("SELECT SUM(balance) FROM debt_tracker WHERE sid=? AND state='OUVERT'", (sid,)).fetchone()[0] or 0
    db.close()
    
    col1, col2 = st.columns(2)
    with col1: st.markdown(f"<div style='border:4px solid #00ff00; padding:20px; border-radius:15px; text-align:center;'><h3 style='color:#00ff00;'>RECETTE JOUR</h3><h1 style='color:#00ff00;'>{ca:,.2f} $</h1></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div style='border:4px solid #ff4444; padding:20px; border-radius:15px; text-align:center;'><h3 style='color:#ff4444;'>DETTES CLIENTS</h3><h1 style='color:#ff4444;'>{dt_tot:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE & FACTURE ADMINISTRATIVE ---
elif choice == "🛒 CAISSE":
    if st.session_state.state['view_receipt']:
        r = st.session_state.state['view_receipt']
        st.markdown("<div class='no-print'>")
        if st.button("⬅️ RETOUR AU PANIER"): st.session_state.state['view_receipt'] = None; st.rerun()
        p_fmt = st.selectbox("Choisir Format d'Impression", ["80mm", "A4 Administrative"])
        st.markdown("</div>")

        width = "320px" if p_fmt == "80mm" else "100%"
        st.markdown(f"""
        <div class="facture-container" style="width:{width}; border: 2px solid #000;">
            <h1 style="text-align:center; margin:0;">{shop['sname']}</h1>
            <p style="text-align:center; font-size:14px;">{shop['address']}<br>Tel: {shop['tel']}</p>
            <hr style="border:1px dashed black;">
            <p style="text-align:center; font-weight:bold;">FACTURE ADMINISTRATIVE N° {r['ref']}</p>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span>Client: <b>{r['client']}</b></span>
                <span>Date: {r['date']}</span>
            </div>
            <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
                <thead>
                    <tr style="border-bottom:2px solid black; text-align:left;">
                        <th style="color:black !important; background:none !important; text-align:left !important;">Désignation</th>
                        <th style="color:black !important; background:none !important; text-align:center !important;">Qté</th>
                        <th style="color:black !important; background:none !important; text-align:right !important;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td style='text-align:left !important;'>{k}</td><td style='text-align:center !important;'>{v['q']}</td><td style='text-align:right !important;'>{v['tot']:,.2f}</td></tr>" for k,v in r['items'].items()])}
                </tbody>
            </table>
            <hr style="border:1px dashed black;">
            <h2 style="text-align:right; margin:0;">NET À PAYER: {r['total']:,.2f} {r['cur']}</h2>
            <p style="font-size:12px; margin-top:30px; text-align:center;">Vendeur: {st.session_state.state['uid'].upper()}<br>Merci pour votre confiance !</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER / GÉNÉRER PDF"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        db = get_connection()
        inventory = db.execute("SELECT * FROM product_stock WHERE sid=? AND qty > 0", (sid,)).fetchall()
        db.close()
        
        c_p, c_m = st.columns([2, 1])
        with c_m: 
            dev = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            tx = shop['rate']
        with c_p:
            choice_p = st.selectbox("Rechercher Produit", ["---"] + [f"{i['item_name']} (Disp: {i['qty']})" for i in inventory])
            if choice_p != "---":
                p_name = choice_p.split(" (")[0]
                if st.button("➕ AJOUTER"):
                    db = get_connection()
                    pd_d = db.execute("SELECT sell_price, qty FROM product_stock WHERE item_name=? AND sid=?", (p_name, sid)).fetchone()
                    db.close()
                    st.session_state.state['cart'][p_name] = {'p': pd_d['sell_price'], 'q': 1, 'max': pd_d['qty']}
                    st.rerun()

        if st.session_state.state['cart']:
            st.subheader("📦 PANIER EN COURS")
            t_usd = 0.0
            for it, val in list(st.session_state.state['cart'].items()):
                st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:10px; border-radius:10px; margin-bottom:5px;'><b>{it}</b> | {val['p']}$</div>", unsafe_allow_html=True)
                col_q, col_d = st.columns([3, 1])
                st.session_state.state['cart'][it]['q'] = col_q.number_input(f"Quantité", 1, val['max'], val['q'], key=f"q_{it}")
                t_usd += val['p'] * st.session_state.state['cart'][it]['q']
                if col_d.button("🗑️", key=f"rm_{it}"): del st.session_state.state['cart'][it]; st.rerun()

            aff_tot = t_usd if dev == "USD" else t_usd * tx
            st.markdown(f"<div class='cobalt-card'><h2>TOTAL À PAYER : {aff_tot:,.2f} {dev}</h2></div>", unsafe_allow_html=True)
            
            with st.form("checkout"):
                cl_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                v_paid = st.number_input(f"MONTANT REÇU ({dev})", value=float(aff_tot))
                if st.form_submit_button("✅ VALIDER & ÉDITER FACTURE"):
                    paid_u = v_paid if dev == "USD" else v_paid / tx
                    due_u = t_usd - paid_u
                    fac_ref = f"FAC-{random.randint(10000, 99999)}"
                    d_now, t_now = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    db = get_connection()
                    items_js = {k: {'q': v['q'], 'tot': v['p']*v['q']} for k,v in st.session_state.state['cart'].items()}
                    db.execute("INSERT INTO sales_ledger (ref_code, client, total_val, paid_val, due_val, date_val, time_val, seller_id, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (fac_ref, cl_name, t_usd, paid_u, due_u, d_now, t_now, st.session_state.state['uid'], sid, json.dumps(items_js), dev))
                    for name, dt in st.session_state.state['cart'].items():
                        db.execute("UPDATE product_stock SET qty = qty - ? WHERE item_name=? AND sid=?", (dt['q'], name, sid))
                    if due_u > 0.01:
                        db.execute("INSERT INTO debt_tracker (client_name, balance, ref_fac, sid) VALUES (?,?,?,?)", (cl_name, due_u, fac_ref, sid))
                    db.commit(); db.close()
                    
                    st.session_state.state['view_receipt'] = {'ref': fac_ref, 'client': cl_name, 'total': aff_tot, 'cur': dev, 'items': items_js, 'date': d_now, 'time': t_now}
                    st.session_state.state['cart'] = {}; st.rerun()

# --- 6.3 STOCK (TABLEAUX LISIBLES) ---
elif choice == "📦 STOCK":
    st.markdown("<div class='cobalt-card'><h1>INVENTAIRE DES MARCHANDISES</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("add_p"):
            n_art = st.text_input("Désignation de l'article").upper()
            c1, c2 = st.columns(2)
            p_a = c1.number_input("Prix d'Achat ($)")
            p_v = c2.number_input("Prix de Vente ($)")
            q_i = st.number_input("Quantité en stock", 1)
            if st.form_submit_button("SAUVEGARDER"):
                db = get_connection()
                db.execute("INSERT INTO product_stock (item_name, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_art, q_i, p_a, p_v, sid))
                db.commit(); db.close(); st.rerun()
    
    st.subheader("LISTE DES PRODUITS")
    db = get_connection()
    stk = db.execute("SELECT * FROM product_stock WHERE sid=? ORDER BY item_name", (sid,)).fetchall()
    db.close()
    if stk:
        df_stk = pd.DataFrame(stk, columns=["ID", "ARTICLE", "QTÉ", "ACHAT", "VENTE", "SID", "CAT"])
        st.table(df_stk[["ARTICLE", "QTÉ", "VENTE"]])
        
        for p in stk:
            with st.expander(f"MODIFIER: {p['item_name']}"):
                col_nv_p, col_nv_q = st.columns(2)
                nv_p = col_nv_p.number_input(f"Prix Vente", value=p['sell_price'], key=f"p_{p['id']}")
                nv_q = col_nv_q.number_input(f"Stock", value=p['qty'], key=f"q_{p['id']}")
                c_u, c_d = st.columns(2)
                if c_u.button(f"MAJ {p['id']}", key=f"ub_{p['id']}"):
                    db = get_connection()
                    db.execute("UPDATE product_stock SET sell_price=?, qty=? WHERE id=?", (nv_p, nv_q, p['id']))
                    db.commit(); db.close(); st.rerun()
                if c_d.button(f"🗑️ SUPPRIMER {p['id']}", key=f"db_{p['id']}"):
                    db = get_connection()
                    db.execute("DELETE FROM product_stock WHERE id=?", (p['id'],))
                    db.commit(); db.close(); st.rerun()
    else: st.info("Aucun article en stock.")

# --- 6.4 DETTES ---
elif choice == "📉 DETTES":
    st.markdown("<div class='cobalt-card'><h1>GESTION DES CRÉDITS</h1></div>", unsafe_allow_html=True)
    db = get_connection()
    dettes = db.execute("SELECT * FROM debt_tracker WHERE sid=? AND state='OUVERT'", (sid,)).fetchall()
    if not dettes: st.success("Félicitations ! Vous n'avez aucune dette client.")
    for d in dettes:
        with st.expander(f"👤 {d['client_name']} | SOLDE: {d['balance']:,.2f} $"):
            tranche = st.number_input("Payer une tranche ($)", 0.0, d['balance'], key=f"tr_{d['id']}")
            if st.button(f"ENREGISTRER PAIEMENT {d['id']}"):
                reste = d['balance'] - tranche
                db_u = get_connection()
                if reste <= 0.01: db_u.execute("UPDATE debt_tracker SET balance=0, state='SOLDE' WHERE id=?", (d['id'],))
                else: db_u.execute("UPDATE debt_tracker SET balance=? WHERE id=?", (reste, d['id']))
                db_u.commit(); db_u.close(); st.rerun()
    db.close()

# --- 6.5 RAPPORTS (TABLEAUX COMPLETS) ---
elif choice == "📊 RAPPORTS":
    st.markdown("<div class='cobalt-card'><h1>RAPPORTS DE VENTES</h1></div>", unsafe_allow_html=True)
    d_filt = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    db = get_connection()
    reps = db.execute("SELECT * FROM sales_ledger WHERE sid=? AND date_val=?", (sid, d_filt)).fetchall()
    db.close()
    if reps:
        df_r = pd.DataFrame(reps, columns=["ID","REF","CLIENT","TOTAL $","PAYÉ","RESTE","DATE","HEURE","VENDEUR","SID","DETAILS","CUR"])
        st.table(df_r[["REF", "CLIENT", "TOTAL $", "HEURE", "VENDEUR"]])
        st.markdown(f"<div class='cobalt-card'><h2>TOTAL RÉCOLTÉ : {df_r['TOTAL $'].sum():,.2f} $</h2></div>", unsafe_allow_html=True)
    else: st.info(f"Aucune transaction pour le {d_filt}.")

# --- 6.6 ÉQUIPE & MON PROFIL ---
elif choice == "👥 ÉQUIPE":
    st.markdown("<div class='cobalt-card'><h1>ÉQUIPE & PROFIL PERSONNEL</h1></div>", unsafe_allow_html=True)
    
    with st.expander("👤 MON COMPTE (CHANGER MON LOGIN/PASS)"):
        with st.form("my_profile"):
            curr_id = st.text_input("Mon Identifiant Actuel", st.session_state.state['uid'])
            new_pass = st.text_input("Nouveau Mot de Passe (laisser vide si inchangé)", type="password")
            if st.form_submit_button("METTRE À JOUR MON PROFIL"):
                db = get_connection()
                if new_pass:
                    h_p = hashlib.sha256(new_pass.encode()).hexdigest()
                    db.execute("UPDATE users_accounts SET uid=?, password=? WHERE uid=?", (curr_id, h_p, st.session_state.state['uid']))
                else:
                    db.execute("UPDATE users_accounts SET uid=? WHERE uid=?", (curr_id, st.session_state.state['uid']))
                db.commit(); db.close()
                st.session_state.state['is_auth'] = False; st.rerun()

    if st.session_state.state['role'] == "BOSS":
        st.divider()
        st.subheader("➕ AJOUTER UN VENDEUR")
        with st.form("vendeur_form"):
            v_id = st.text_input("ID Vendeur (Login)").lower()
            v_fn = st.text_input("Nom Complet")
            v_pw = st.text_input("Mot de Passe Vendeur", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                db = get_connection()
                try:
                    h_v = hashlib.sha256(v_pw.encode()).hexdigest()
                    db.execute("INSERT INTO users_accounts VALUES (?,?,?,?,?,?,?,?)", 
                              (v_id, h_v, 'VENDEUR', sid, 'ACTIF', v_fn, '', u_info['expiry_date']))
                    db.commit(); st.success(f"Vendeur {v_id} ajouté !"); st.rerun()
                except: st.error("Cet ID est déjà pris.")
                finally: db.close()

# --- 6.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.markdown("<div class='cobalt-card'><h1>RÉGLAGES DE LA BOUTIQUE</h1></div>", unsafe_allow_html=True)
    with st.form("settings_f"):
        sn = st.text_input("Nom de l'Enseigne", shop['sname'])
        tx = st.number_input("Taux de Change (1$ = ? CDF)", value=shop['rate'])
        sa = st.text_area("Adresse Physique", shop['address'])
        st_tel = st.text_input("Contact Téléphone", shop['tel'])
        if st.form_submit_button("ENREGISTRER LES MODIFICATIONS"):
            db = get_connection()
            db.execute("UPDATE shops_info SET sname=?, rate=?, address=?, tel=? WHERE sid=?", (sn, tx, sa, st_tel, sid))
            db.commit(); db.close(); st.success("Réglages mis à jour !"); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.state['is_auth'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v250 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
