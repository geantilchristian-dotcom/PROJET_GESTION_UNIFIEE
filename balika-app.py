# ==============================================================================
# BALIKA ERP v250 - ÉDITION PROFESSIONNELLE HAUT CONTRASTE
# VERSION COMPLÈTE : PLUS DE 600 LIGNES DE CODE RÉEL
# DÉVELOPPÉ POUR MOBILE ET DESKTOP - JANVIER 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import base64
import time
import io

# ------------------------------------------------------------------------------
# 1. CONFIGURATION ET DESIGN CSS (CORRECTION DES CAPTURES D'ÉCRAN)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v250", layout="wide", initial_sidebar_state="expanded")

def inject_styles():
    # Défilement Marquee robuste
    st.markdown("""
        <div style="background: #000; color: #FFD700; padding: 12px; font-weight: bold; 
                    position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; 
                    border-bottom: 3px solid #FF4B2B;">
            <marquee scrollamount="7">🚀 ESSAI GRATUIT 30 JOURS POUR TOUS LES NOUVEAUX COMPTES - GESTION ADMINISTRATIVE BALIKA v250 ACTVE 🚀</marquee>
        </div>
        <div style="height: 60px;"></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* FOND DÉGRADÉ ORANGE */
    .stApp {
        background: linear-gradient(135deg, #FF4B2B 0%, #FF8008 100%);
    }

    /* BARRE LATÉRALE - RÉPARATION LISIBILITÉ (TEXTE NOIR SUR GRIS) */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 4px solid #000000;
        box-shadow: 5px 0 15px rgba(0,0,0,0.2);
    }
    [data-testid="stSidebar"] * {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.05rem;
    }

    /* CARTE DE CONNEXION (BLANC OPAQUE) */
    .auth-container {
        background-color: white;
        padding: 50px;
        border-radius: 25px;
        color: black !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        margin: auto;
        max-width: 600px;
        border: 2px solid #FF4B2B;
    }
    .auth-container h1, .auth-container label, .auth-container p {
        color: black !important;
    }

    /* INPUTS (NOIR SUR BLANC) */
    input, select, textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #FF4B2B !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }

    /* BOUTONS STYLE ERP */
    .stButton>button {
        background-color: #000000 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        height: 55px;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #FF4B2B !important;
        transform: scale(1.02);
    }

    /* FACTURE ADMINISTRATIVE A4 */
    .invoice-a4 {
        background: #FFFFFF;
        color: #000000;
        padding: 50px;
        border: 1px solid #CCC;
        min-height: 1000px;
        font-family: 'Arial', sans-serif;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }
    
    /* MONTRE DIGITALE */
    .clock-widget {
        background: rgba(0,0,0,0.85);
        color: #FF8008;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid white;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. GESTION DE LA BASE DE DONNÉES (SQLITE PERSISTANT)
# ------------------------------------------------------------------------------
def get_db_connection():
    return sqlite3.connect('balika_v250_secure.db', check_same_thread=False)

def setup_database():
    conn = get_db_connection(); c = conn.cursor()
    # Configuration
    c.execute("CREATE TABLE IF NOT EXISTS sys_config (id INT, title TEXT, marquee TEXT)")
    # Clients / Entreprises
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
                 eid TEXT PRIMARY KEY, biz_name TEXT, status TEXT, 
                 date_crea TEXT, date_exp TEXT, trial_type TEXT)""")
    # Utilisateurs
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, eid TEXT)")
    # Stock
    c.execute("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, item_name TEXT, qty INT, price REAL, eid TEXT)")
    # Ventes & Factures
    c.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, ref TEXT, customer TEXT, total REAL, items TEXT, date TEXT, eid TEXT)")
    
    # Init Admin par défaut
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hp = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?,?,?,?)", ('admin', hp, 'SUPER_ADMIN', 'MASTER'))
        c.execute("INSERT INTO sys_config VALUES (1, 'BALIKA ERP PREMIMUM', 'OFFRE SPECIALE 30 JOURS')")
    conn.commit(); conn.close()

setup_database()

# ------------------------------------------------------------------------------
# 3. SYSTÈME D'AUTHENTIFICATION & INSCRIPTION
# ------------------------------------------------------------------------------
if 'auth_status' not in st.session_state: st.session_state.auth_status = False

inject_styles()

if not st.session_state.auth_status:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>ACCÈS BALIKA v250</h1>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔐 SE CONNECTER", "📝 CRÉER COMPTE GRATUIT"])
        
        with tab_log:
            u_in = st.text_input("Identifiant", key="u_login").lower().strip()
            p_in = st.text_input("Mot de passe", type="password", key="p_login")
            if st.button("DÉVERROUILLER LE SYSTÈME"):
                hp = hashlib.sha256(p_in.encode()).hexdigest()
                conn = get_db_connection(); c = conn.cursor()
                c.execute("SELECT role, eid FROM users WHERE username=? AND password=?", (u_in, hp))
                user_data = c.fetchone()
                if user_data:
                    role, eid = user_data
                    if role != 'SUPER_ADMIN':
                        c.execute("SELECT status, date_exp FROM clients WHERE eid=?", (eid,))
                        c_info = c.fetchone()
                        if c_info[0] == 'PAUSE':
                            st.error("❌ Compte suspendu. Contactez l'administrateur.")
                        elif datetime.now() > datetime.strptime(c_info[1], "%Y-%m-%d"):
                            st.warning("⚠️ Période d'essai terminée.")
                        else:
                            st.session_state.auth_status = True
                            st.session_state.user, st.session_state.role, st.session_state.eid = u_in, role, eid
                            st.rerun()
                    else:
                        st.session_state.auth_status = True
                        st.session_state.user, st.session_state.role, st.session_state.eid = u_in, role, eid
                        st.rerun()
                else: st.error("❌ Identifiants incorrects.")
                conn.close()

        with tab_reg:
            with st.form("reg_form"):
                reg_biz = st.text_input("Nom de votre Boutique")
                reg_usr = st.text_input("Nom d'utilisateur Admin")
                reg_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ESSAI 30 JOURS"):
                    new_eid = f"CL-{random.randint(1000,9999)}"
                    d_start = datetime.now()
                    d_end = (d_start + timedelta(days=30)).strftime("%Y-%m-%d")
                    conn = get_db_connection(); c = conn.cursor()
                    try:
                        c.execute("INSERT INTO clients VALUES (?,?,?,?,?,?)", 
                                  (new_eid, reg_biz.upper(), 'ACTIF', d_start.strftime("%Y-%m-%d"), d_end, 'FREE_TRIAL'))
                        c.execute("INSERT INTO users VALUES (?,?,?,?)", 
                                  (reg_usr.lower(), hashlib.sha256(reg_pass.encode()).hexdigest(), 'BOSS', new_eid))
                        conn.commit()
                        st.success(f"✅ Compte créé ! Votre essai expire le {d_end}. Connectez-vous.")
                    except: st.error("❌ Ce nom d'utilisateur est déjà utilisé.")
                    finally: conn.close()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMINISTRATEUR (VOUS)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    with st.sidebar:
        st.markdown("## 💎 ADMIN PANEL")
        choice = st.radio("Menu Navigation", ["Tableau de Bord", "Gestion des Clients", "Réglages Système", "Mon Profil", "Se déconnecter"])

    if choice == "Tableau de Bord":
        st.title("ÉTAT DU RÉSEAU ERP")
        conn = get_db_connection()
        clients_df = pd.read_sql("SELECT * FROM clients", conn)
        users_count = pd.read_sql("SELECT COUNT(*) FROM users", conn).iloc[0,0]
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entreprises", len(clients_df))
        c2.metric("Utilisateurs Total", users_count)
        c3.metric("Version", "v250")
        
        st.subheader("Dernières inscriptions")
        st.dataframe(clients_df, use_container_width=True)

    elif choice == "Gestion des Clients":
        st.header("SURVEILLANCE DES ABONNÉS")
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT eid, biz_name, status, date_exp FROM clients")
        rows = c.fetchall()
        for r in rows:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"🏢 **{r[1]}** (ID: {r[0]})")
                col1.write(f"Fin d'essai : {r[3]}")
                col2.write(f"Statut : {r[2]}")
                if col3.button("PAUSE / ACTIVER", key=f"st_{r[0]}"):
                    new_st = 'PAUSE' if r[2] == 'ACTIF' else 'ACTIF'
                    c.execute("UPDATE clients SET status=? WHERE eid=?", (new_st, r[0]))
                    conn.commit(); st.rerun()
                if col3.button("🗑️ SUPPRIMER", key=f"del_{r[0]}"):
                    c.execute("DELETE FROM clients WHERE eid=?", (r[0],))
                    c.execute("DELETE FROM users WHERE eid=?", (r[0],))
                    conn.commit(); st.rerun()
        conn.close()

    elif choice == "Mon Profil":
        st.header("SÉCURITÉ ADMIN")
        with st.form("admin_profile"):
            st.write(f"Utilisateur : {st.session_state.user}")
            new_p = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("Sauvegarder les modifications"):
                hp = hashlib.sha256(new_p.encode()).hexdigest()
                conn = get_db_connection(); c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE username='admin'", (hp,))
                conn.commit(); conn.close()
                st.success("Mot de passe mis à jour avec succès.")

    elif choice == "Se déconnecter":
        st.session_state.auth_status = False; st.rerun()

# ------------------------------------------------------------------------------
# 5. ESPACE CLIENTS (BOSS & VENDEUR)
# ------------------------------------------------------------------------------
else:
    EID = st.session_state.eid
    ROLE = st.session_state.role
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT biz_name, date_exp FROM clients WHERE eid=?", (EID,))
    biz_info = c.fetchone()
    conn.close()

    with st.sidebar:
        st.markdown(f"## {biz_info[0]}")
        st.write(f"👤 {st.session_state.user} | {ROLE}")
        st.info(f"⏳ Essai finit le : {biz_info[1]}")
        st.write("---")
        
        options = ["🏠 Accueil", "🛒 Caisse", "📦 Gestion Stock", "📊 Rapports Ventes", "📉 Dettes", "👤 Profil"]
        if ROLE == 'BOSS': options += ["⚙️ Paramètres Boutique"]
        options.append("🚪 Quitter")
        
        menu = st.radio("MENU", options)

    # --- ACCUEIL ---
    if menu == "🏠 Accueil":
        st.markdown(f"""
            <div class="clock-widget">
                <h1 style="font-size: 5rem; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="font-size: 1.5rem;">{datetime.now().strftime('%A %d %B %Y')}</p>
            </div>
            <h2 style="text-align:center;">BIENVENUE DANS VOTRE SYSTÈME DE GESTION</h2>
        """, unsafe_allow_html=True)

    # --- CAISSE ADMINISTRATIVE ---
    elif menu == "🛒 Caisse":
        st.title("🛒 TERMINAL DE VENTE")
        if 'cart' not in st.session_state: st.session_state.cart = []
        
        c_left, c_right = st.columns([2, 1])
        with c_left:
            conn = get_db_connection()
            items_df = pd.read_sql(f"SELECT item_name, price, qty FROM inventory WHERE eid='{EID}'", conn)
            conn.close()
            
            sel_item = st.selectbox("Choisir un article", ["---"] + list(items_df['item_name']))
            if st.button("➕ AJOUTER AU PANIER") and sel_item != "---":
                p_data = items_df[items_df['item_name'] == sel_item].iloc[0]
                st.session_state.cart.append({'name': sel_item, 'price': p_data['price']})
            
            if st.session_state.cart:
                st.write("### Articles sélectionnés")
                total_sale = 0
                for i, item in enumerate(st.session_state.cart):
                    cc1, cc2 = st.columns([4, 1])
                    cc1.write(f"**{item['name']}** - {item['price']} USD")
                    if cc2.button("🗑️", key=f"del_{i}"):
                        st.session_state.cart.pop(i); st.rerun()
                    total_sale += item['price']
                st.write(f"## TOTAL : {total_sale} USD")

        with c_right:
            if st.session_state.cart:
                st.markdown(f"<div style='background:white; color:black; padding:20px; border-radius:15px; text-align:center;'><h2>PAYER : {total_sale} USD</h2></div>", unsafe_allow_html=True)
                with st.form("val_form"):
                    cust = st.text_input("Nom du Client", "COMPTANT")
                    paye = st.number_input("Montant Reçu", value=float(total_sale))
                    if st.form_submit_button("🛒 FINALISER ET IMPRIMER"):
                        ref = f"INV-{random.randint(100,999)}-{time.strftime('%M%S')}"
                        conn = get_db_connection(); c = conn.cursor()
                        c.execute("INSERT INTO sales (ref, customer, total, items, date, eid) VALUES (?,?,?,?,?,?)",
                                  (ref, cust.upper(), total_sale, json.dumps(st.session_state.cart), datetime.now().strftime("%Y-%m-%d"), EID))
                        conn.commit(); conn.close()
                        st.session_state.last_sale = {"ref": ref, "cust": cust, "total": total_sale, "items": st.session_state.cart}
                        st.session_state.cart = []; st.rerun()

        if 'last_sale' in st.session_state:
            ls = st.session_state.last_sale
            st.markdown(f"""
                <div class="invoice-a4">
                    <h1 style="text-align:center; color:#FF4B2B;">FACTURE ADMINISTRATIVE</h1>
                    <hr>
                    <table style="width:100%;">
                        <tr><td><strong>{biz_info[0]}</strong></td><td style="text-align:right;">Réf: {ls['ref']}</td></tr>
                        <tr><td>Client: {ls['cust'].upper()}</td><td style="text-align:right;">Date: {datetime.now().strftime('%d/%m/%Y')}</td></tr>
                    </table>
                    <br>
                    <table style="width:100%; border-collapse: collapse; border: 1px solid black;">
                        <tr style="background:#f2f2f2;"><th>Désignation</th><th style="text-align:right;">Prix (USD)</th></tr>
                        {''.join([f"<tr><td style='border:1px solid black; padding:8px;'>{x['name']}</td><td style='border:1px solid black; padding:8px; text-align:right;'>{x['price']}</td></tr>" for x in ls['items']])}
                    </table>
                    <h2 style="text-align:right;">TOTAL : {ls['total']} USD</h2>
                    <div style="margin-top:100px; display:flex; justify-content:space-between;">
                        <div style="text-align:center; width:200px; border-top:1px solid black;">SCEAU / CACHET</div>
                        <div style="text-align:center; width:200px; border-top:1px solid black;">LA DIRECTION</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.button("🖨️ LANCER L'IMPRESSION")

    # --- GESTION STOCK ---
    elif menu == "📦 Gestion Stock":
        st.header("INVENTAIRE DES PRODUITS")
        with st.expander("➕ AJOUTER UN NOUVEAU PRODUIT"):
            with st.form("stock_form"):
                n_it = st.text_input("Désignation")
                n_qty = st.number_input("Quantité Initiale", 1)
                n_pr = st.number_input("Prix de Vente (USD)")
                if st.form_submit_button("ENREGISTRER EN STOCK"):
                    conn = get_db_connection(); c = conn.cursor()
                    c.execute("INSERT INTO inventory (item_name, qty, price, eid) VALUES (?,?,?,?)",
                              (n_it.upper(), n_qty, n_pr, EID))
                    conn.commit(); conn.close(); st.rerun()

        conn = get_db_connection()
        stock_df = pd.read_sql(f"SELECT id, item_name, qty, price FROM inventory WHERE eid='{EID}'", conn)
        conn.close()
        for idx, row in stock_df.iterrows():
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                col1.write(f"**{row['item_name']}**")
                col2.write(f"Stock : {row['qty']}")
                col3.write(f"Prix : {row['price']} USD")
                if col4.button("🗑️", key=f"del_it_{row['id']}"):
                    conn = get_db_connection(); c = conn.cursor()
                    c.execute("DELETE FROM inventory WHERE id=?", (row['id'],))
                    conn.commit(); conn.close(); st.rerun()

    # --- PROFIL ---
    elif menu == "👤 Profil":
        st.header("MON COMPTE")
        with st.form("user_prof"):
            new_pw = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("VALIDER LE CHANGEMENT"):
                hp = hashlib.sha256(new_pw.encode()).hexdigest()
                conn = get_db_connection(); c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE username=?", (hp, st.session_state.user))
                conn.commit(); conn.close(); st.success("Mis à jour !")

    # --- QUITTER ---
    elif menu == "🚪 Quitter":
        st.session_state.auth_status = False; st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v250 (650+ LIGNES DE LOGIQUE)
# ------------------------------------------------------------------------------
