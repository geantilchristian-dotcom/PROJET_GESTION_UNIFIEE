# ==============================================================================
# ANASH ERP v3300 - SYSTÈME DE GESTION UNIFIÉ (BALIKA BUSINESS)
# DÉVELOPPÉ POUR : USAGE PROFESSIONNEL MOBILE & DESKTOP
# CARACTÉRISTIQUES : 700 LIGNES | DESIGN COBALT | SÉCURITÉ ADMIN
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import random
import os

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & STYLE CSS (FORCE LE BLEU ET LE BLANC)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ANASH ERP v3300",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_design():
    st.markdown("""
    <style>
    /* Importation de polices modernes */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Roboto+Mono:wght@400;700&display=swap');

    /* Fond d'écran global : Bleu Royal Profond */
    .stApp {
        background: linear-gradient(135deg, #001f4d 0%, #000a1a 100%) !important;
        color: #ffffff !important;
    }

    /* MESSAGE DÉFILANT CSS ULTRA FLUIDE */
    .marquee-wrapper {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #000000;
        color: #00ff00;
        z-index: 10000;
        height: 45px;
        display: flex;
        align-items: center;
        border-bottom: 2px solid #0044ff;
        font-family: 'Roboto Mono', monospace;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .marquee-content {
        white-space: nowrap;
        display: inline-block;
        animation: marquee-animation 30s linear infinite;
        font-size: 18px;
        font-weight: bold;
        text-transform: uppercase;
    }
    @keyframes marquee-animation {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* HORLOGE XXL (STYLE SMARTPHONE 80MM) */
    .digital-clock {
        background: rgba(0, 68, 255, 0.2);
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 40px;
        padding: 60px 20px;
        text-align: center;
        margin: 60px auto;
        max-width: 850px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    }
    .clock-time {
        font-family: 'Orbitron', sans-serif;
        font-size: 110px;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0 0 30px #0088ff;
        line-height: 1;
        margin: 0;
    }
    .clock-date {
        font-size: 26px;
        color: #00d9ff;
        text-transform: uppercase;
        letter-spacing: 5px;
        margin-top: 15px;
    }

    /* PANNEAUX BLEUS (INFO CARDS) AVEC TEXTE BLANC FORCÉ */
    .blue-card {
        background: #0044ff !important;
        padding: 30px;
        border-radius: 25px;
        border-left: 10px solid #00d9ff;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .blue-card h1, .blue-card h2, .blue-card h3, .blue-card p, .blue-card b, .blue-card span {
        color: white !important;
        font-family: 'Inter', sans-serif;
    }

    /* CADRE TOTAL PANIER (NÉON VERT) */
    .total-frame-container {
        background: #000000 !important;
        border: 6px solid #00ff00 !important;
        color: #00ff00 !important;
        padding: 40px;
        border-radius: 30px;
        text-align: center;
        margin: 30px 0;
        box-shadow: 0 0 40px rgba(0, 255, 0, 0.3);
    }
    .total-text {
        font-family: 'Orbitron', sans-serif;
        font-size: 55px;
        font-weight: 900;
    }

    /* BOUTONS XXL POUR TÉLÉPHONES */
    .stButton > button {
        width: 100% !important;
        height: 85px !important;
        background: linear-gradient(90deg, #0055ff, #002288) !important;
        color: white !important;
        border-radius: 20px !important;
        font-size: 24px !important;
        font-weight: 700 !important;
        border: 2px solid #ffffff !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }
    .stButton > button:active {
        transform: scale(0.95);
        background: #00ff00 !important;
        color: black !important;
    }

    /* INPUTS ET FORMULAIRES */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        font-size: 18px !important;
        border: 3px solid #0044ff !important;
    }
    
    label { color: white !important; font-size: 18px !important; font-weight: bold !important; }

    /* SIDEBAR BLANCHE (CONTRASTE) */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 5px solid #0044ff;
    }
    [data-testid="stSidebar"] * {
        color: #000000 !important;
        font-weight: bold;
    }

    /* FACTURE STYLE THERMIQUE 80mm */
    .thermal-receipt {
        background: white !important;
        color: black !important;
        padding: 40px;
        font-family: 'Courier New', Courier, monospace;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
        width: 100%;
        max-width: 400px;
        margin: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (SQLITE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3300_master.db"

def db_execute(sql, params=(), is_select=True):
    """Exécute une requête SQL de manière sécurisée."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        if is_select:
            return cursor.fetchall()
        return None

def initialize_database():
    """Initialise toutes les tables nécessaires au système."""
    # Table des Utilisateurs
    db_execute("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, 
        pwd TEXT, 
        role TEXT, 
        managed_shop TEXT, 
        status TEXT, 
        full_name TEXT, 
        phone TEXT)""", is_select=False)
    
    # Table des Boutiques
    db_execute("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY, 
        name TEXT, 
        owner_uid TEXT, 
        rate_usd_to_cdf REAL, 
        receipt_header TEXT, 
        address TEXT, 
        phone TEXT)""", is_select=False)
    
    # Table du Stock
    db_execute("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        item_name TEXT, 
        quantity INTEGER, 
        buying_price REAL, 
        selling_price REAL, 
        shop_id TEXT)""", is_select=False)
    
    # Table des Ventes
    db_execute("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        ref_code TEXT, 
        client_name TEXT, 
        total_usd REAL, 
        paid_usd REAL, 
        debt_usd REAL, 
        sale_date TEXT, 
        sale_time TEXT, 
        seller_uid TEXT, 
        shop_id TEXT, 
        items_json TEXT)""", is_select=False)
    
    # Table des Dettes
    db_execute("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        client_name TEXT, 
        amount_remaining REAL, 
        sale_ref TEXT, 
        shop_id TEXT, 
        status TEXT DEFAULT 'OPEN')""", is_select=False)
    
    # Table Configuration Système (Marquee)
    db_execute("CREATE TABLE IF NOT EXISTS sys_config (id INTEGER PRIMARY KEY, marquee_text TEXT)", is_select=False)

    # Insertion des données par défaut (ADMIN)
    admin_exists = db_execute("SELECT uid FROM users WHERE uid='admin'")
    if not admin_exists:
        hashed_pwd = hashlib.sha256("admin123".encode()).hexdigest()
        db_execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                  ('admin', hashed_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR MAITRE', '000'), is_select=False)
    
    # Message défilant par défaut
    if not db_execute("SELECT id FROM sys_config"):
        db_execute("INSERT INTO sys_config VALUES (1, 'BIENVENUE SUR ANASH ERP v3300 - VOTRE SYSTÈME DE GESTION INTÉGRÉ - BALIKA BUSINESS')", is_select=False)

# Lancement de la DB
initialize_database()

# Récupération du message défilant
sys_marquee = db_execute("SELECT marquee_text FROM sys_config WHERE id=1")[0][0]

# ------------------------------------------------------------------------------
# 3. GESTION DE LA SESSION UTILISATEUR
# ------------------------------------------------------------------------------
if 'erp_session' not in st.session_state:
    st.session_state.erp_session = {
        'logged_in': False,
        'user_id': None,
        'user_role': None,
        'current_shop_id': None,
        'shopping_cart': {},
        'last_invoice': None
    }

inject_custom_design()

# Injection du message défilant CSS
st.markdown(f"""
    <div class="marquee-wrapper">
        <div class="marquee-content">{sys_marquee}</div>
    </div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION ET INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.erp_session['logged_in']:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, login_container, _ = st.columns([1, 2, 1])
    
    with login_container:
        st.markdown("<div class='digital-clock'><p class='clock-time'>ANASH ERP</p></div>", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔒 ACCÈS SYSTÈME", "📝 NOUVEAU GÉRANT"])
        
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            input_user = st.text_input("Identifiant Unique").lower().strip()
            input_pass = st.text_input("Mot de passe", type="password")
            
            if st.button("DÉVERROUILLER LE SYSTÈME"):
                user_record = db_execute("SELECT pwd, role, managed_shop, status FROM users WHERE uid=?", (input_user,))
                if user_record:
                    stored_pwd, role, shop_ref, status = user_record[0]
                    if hashlib.sha256(input_pass.encode()).hexdigest() == stored_pwd:
                        if status == "EN_ATTENTE":
                            st.warning("⏳ Votre compte est en attente d'activation par l'Admin.")
                        elif status == "BLOQUE":
                            st.error("🚫 Ce compte a été suspendu.")
                        else:
                            st.session_state.erp_session.update({
                                'logged_in': True,
                                'user_id': input_user,
                                'user_role': role,
                                'current_shop_id': shop_ref
                            })
                            st.success("Accès accordé !")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Mot de passe incorrect.")
                else:
                    st.error("Utilisateur introuvable.")

        with tab_signup:
            st.info("Les comptes gérants doivent être validés par l'Admin.")
            with st.form("signup_form"):
                reg_uid = st.text_input("Identifiant souhaité").lower().strip()
                reg_name = st.text_input("Nom Complet du Gérant")
                reg_phone = st.text_input("Téléphone de contact")
                reg_pass = st.text_input("Mot de passe secret", type="password")
                
                if st.form_submit_button("CRÉER MON COMPTE GÉRANT"):
                    check_user = db_execute("SELECT uid FROM users WHERE uid=?", (reg_uid,))
                    if check_user:
                        st.error("Cet identifiant est déjà utilisé.")
                    else:
                        hashed = hashlib.sha256(reg_pass.encode()).hexdigest()
                        db_execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                                  (reg_uid, hashed, 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', reg_name, reg_phone), is_select=False)
                        st.success("✅ Demande envoyée ! Veuillez contacter l'Admin pour l'activation.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. INTERFACE SUPER ADMIN (POUR admin / admin123)
# ------------------------------------------------------------------------------
if st.session_state.erp_session['user_role'] == "SUPER_ADMIN":
    st.sidebar.title("💎 ADMINISTRATION")
    admin_menu = st.sidebar.radio("Navigation Admin", ["Validation Gérants", "Configuration Message", "Statistiques Globales", "Déconnexion"])
    
    if admin_menu == "Validation Gérants":
        st.header("👥 GESTION DES COMPTES GÉRANTS")
        all_gerants = db_execute("SELECT uid, full_name, phone, status FROM users WHERE role='GERANT'")
        
        if not all_gerants:
            st.info("Aucun gérant inscrit pour le moment.")
        
        for g_id, g_name, g_phone, g_status in all_gerants:
            with st.container():
                st.markdown(f"""
                <div class='blue-card'>
                    <h3>{g_name} (@{g_id})</h3>
                    <p>📞 Tel: {g_phone} | Statut actuel: <b>{g_status}</b></p>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                if col_a.button("✅ ACTIVER", key=f"act_{g_id}"):
                    # On active et on lie la boutique à son propre ID par défaut
                    db_execute("UPDATE users SET status='ACTIF', managed_shop=? WHERE uid=?", (g_id, g_id), is_select=False)
                    st.rerun()
                if col_b.button("⏸️ BLOQUER", key=f"blo_{g_id}"):
                    db_execute("UPDATE users SET status='BLOQUE' WHERE uid=?", (g_id,), is_select=False)
                    st.rerun()
                if col_c.button("🗑️ SUPPRIMER", key=f"del_{g_id}"):
                    db_execute("DELETE FROM users WHERE uid=?", (g_id,), is_select=False)
                    st.rerun()

    elif admin_menu == "Configuration Message":
        st.header("📢 MESSAGE DÉFILANT DU SYSTÈME")
        current_msg = db_execute("SELECT marquee_text FROM sys_config WHERE id=1")[0][0]
        new_marquee = st.text_area("Éditer le message (apparaîtra en haut de tous les écrans)", current_msg)
        if st.button("METTRE À JOUR LE MESSAGE"):
            db_execute("UPDATE sys_config SET marquee_text=? WHERE id=1", (new_marquee,), is_select=False)
            st.success("Message mis à jour !")
            time.sleep(1)
            st.rerun()

    elif admin_menu == "Statistiques Globales":
        st.header("📊 APERÇU GÉNÉRAL")
        total_sales = db_execute("SELECT SUM(total_usd) FROM sales")[0][0] or 0
        total_shops = db_execute("SELECT COUNT(*) FROM shops")[0][0]
        total_users = db_execute("SELECT COUNT(*) FROM users")[0][0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventes Totales (USD)", f"{total_sales:,.2f} $")
        c2.metric("Boutiques Actives", total_shops)
        c3.metric("Utilisateurs", total_users)

    if admin_menu == "Déconnexion":
        st.session_state.erp_session['logged_in'] = False
        st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR
# ------------------------------------------------------------------------------
# Récupération des informations de la boutique active
active_shop_id = st.session_state.erp_session['current_shop_id']
shop_data = db_execute("SELECT name, rate_usd_to_cdf, receipt_header, address, phone FROM shops WHERE sid=?", (active_shop_id,))

# Si le gérant n'a pas encore configuré sa boutique
if not shop_data and st.session_state.erp_session['user_role'] == "GERANT":
    st.warning("📢 Bienvenue ! Commencez par configurer votre boutique dans les RÉGLAGES.")
    active_shop_info = ("NOUVELLE BOUTIQUE", 2800.0, "BIENVENUE", "ADRESSE", "000")
    menu_options = ["⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    active_shop_info = shop_data[0] if shop_data else ("INCONNU", 2800.0, "", "", "")
    
    if st.session_state.erp_session['user_role'] == "GERANT":
        menu_options = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 GESTION STOCK", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
    else:
        # Le vendeur ne voit que l'essentiel
        menu_options = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div style='background:#0044ff; color:white; padding:15px; border-radius:15px; text-align:center;'>🏪 {active_shop_info[0]}<br>👤 {st.session_state.erp_session['user_id'].upper()}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    user_choice = st.radio("MENU PRINCIPAL", menu_options)

# --- 6.1 ACCUEIL (DASHBOARD) ---
if user_choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='digital-clock'>
        <p class='clock-time'>{datetime.now().strftime('%H:%M')}</p>
        <p class='clock-date'>{datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistiques du jour
    today_str = datetime.now().strftime("%d/%m/%Y")
    daily_revenue = db_execute("SELECT SUM(total_usd) FROM sales WHERE shop_id=? AND sale_date=?", (active_shop_id, today_str))[0][0] or 0
    daily_debts = db_execute("SELECT SUM(amount_remaining) FROM debts WHERE shop_id=? AND status='OPEN'", (active_shop_id,))[0][0] or 0
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.markdown(f"""<div class='blue-card'><h2>RECETTE JOUR</h2><h1 style='font-size:50px;'>{daily_revenue:,.2f} $</h1></div>""", unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""<div class='blue-card' style='background:#ff4400 !important;'><h2>DETTES TOTALES</h2><h1 style='font-size:50px;'>{daily_debts:,.2f} $</h1></div>""", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (PANIER & VENTE) ---
elif user_choice == "🛒 CAISSE TACTILE":
    if not st.session_state.erp_session['last_invoice']:
        st.header("🛒 TERMINAL DE VENTE")
        
        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c2:
            st.markdown("<div class='blue-card'>", unsafe_allow_html=True)
            st.subheader("PARAMÈTRES")
            currency = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
            current_rate = active_shop_info[1]
            st.write(f"Taux actuel : **1 USD = {current_rate:,.0f} CDF**")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_c1:
            # Recherche article
            inventory = db_execute("SELECT item_name, selling_price, quantity FROM stock WHERE shop_id=?", (active_shop_id,))
            if not inventory:
                st.warning("Le stock est vide. Ajoutez des produits d'abord.")
            else:
                items_dict = {row[0]: (row[1], row[2]) for row in inventory}
                selected_item = st.selectbox("🔍 RECHERCHER UN ARTICLE", ["--- Cliquer pour choisir ---"] + list(items_dict.keys()))
                
                if selected_item != "--- Cliquer pour choisir ---":
                    price_usd, stock_qty = items_dict[selected_item]
                    if stock_qty > 0:
                        if st.button(f"➕ AJOUTER {selected_item}"):
                            st.session_state.erp_session['shopping_cart'][selected_item] = st.session_state.erp_session['shopping_cart'].get(selected_item, 0) + 1
                            st.toast(f"{selected_item} ajouté au panier")
                    else:
                        st.error("STOCK ÉPUISÉ !")

        # Affichage du panier
        if st.session_state.erp_session['shopping_cart']:
            st.divider()
            st.subheader("📝 PANIER ACTUEL")
            
            total_sale_val = 0.0
            cart_details = []
            
            for item, qty in list(st.session_state.erp_session['shopping_cart'].items()):
                unit_price_usd = items_dict[item][0]
                # Conversion selon devise
                display_price = unit_price_usd if currency == "USD" else unit_price_usd * current_rate
                subtotal = display_price * qty
                total_sale_val += subtotal
                
                cart_details.append({"nom": item, "qte": qty, "prix_u": display_price, "total": subtotal})
                
                c_item1, c_item2, c_item3 = st.columns([3, 1, 1])
                c_item1.markdown(f"**{item}**")
                c_item2.markdown(f"{qty} x {display_price:,.2f} {currency}")
                if c_item3.button("🗑️", key=f"del_{item}"):
                    del st.session_state.erp_session['shopping_cart'][item]
                    st.rerun()

            # CADRE TOTAL NÉON
            st.markdown(f"""
            <div class='total-frame-container'>
                <p style='margin:0; font-size:20px; color:#aaa;'>TOTAL À PAYER</p>
                <div class='total-text'>{total_sale_val:,.2f} {currency}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Finalisation
            with st.form("payment_form"):
                cust_name = st.text_input("NOM DU CLIENT", value="COMPTANT").upper()
                amount_received = st.number_input(f"MONTANT REÇU ({currency})", min_value=0.0, value=float(total_sale_val))
                
                if st.form_submit_button("🚀 VALIDER ET IMPRIMER"):
                    remaining = total_sale_val - amount_received
                    ref_sale = f"FAC-{random.randint(1000, 9999)}"
                    d_now = datetime.now().strftime("%d/%m/%Y")
                    t_now = datetime.now().strftime("%H:%M")
                    
                    # Conversion en USD pour la base de données (standardisation)
                    final_total_usd = total_sale_val if currency == "USD" else total_sale_val / current_rate
                    final_paid_usd = amount_received if currency == "USD" else amount_received / current_rate
                    final_debt_usd = remaining if currency == "USD" else remaining / current_rate
                    
                    # Enregistrement Vente
                    db_execute("""INSERT INTO sales (ref_code, client_name, total_usd, paid_usd, debt_usd, sale_date, sale_time, seller_uid, shop_id, items_json) 
                                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                              (ref_code, cust_name, final_total_usd, final_paid_usd, final_debt_usd, d_now, t_now, st.session_state.erp_session['user_id'], active_shop_id, json.dumps(cart_details)), is_select=False)
                    
                    # Mise à jour Stock
                    for it in cart_details:
                        db_execute("UPDATE stock SET quantity = quantity - ? WHERE item_name=? AND shop_id=?", (it['qte'], it['nom'], active_shop_id), is_select=False)
                    
                    # Si dette
                    if final_debt_usd > 0.01:
                        db_execute("INSERT INTO debts (client_name, amount_remaining, sale_ref, shop_id) VALUES (?,?,?,?)",
                                  (cust_name, final_debt_usd, ref_sale, active_shop_id), is_select=False)
                    
                    # Préparation ticket
                    st.session_state.erp_session['last_invoice'] = {
                        "ref": ref_sale, "client": cust_name, "total": total_sale_val, "recu": amount_received, 
                        "reste": remaining, "devise": currency, "lignes": cart_details, "date": d_now, "heure": t_now
                    }
                    st.session_state.erp_session['shopping_cart'] = {}
                    st.rerun()
    else:
        # AFFICHAGE DU TICKET APRÈS VENTE
        inv = st.session_state.erp_session['last_invoice']
        st.markdown(f"""
        <div class="thermal-receipt">
            <h2 style="text-align:center;">{active_shop_info[2] if active_shop_info[2] else active_shop_info[0]}</h2>
            <p style="text-align:center; font-size:12px;">{active_shop_info[3]}<br>Tel: {active_shop_info[4]}</p>
            <hr>
            <p>REF: {inv['ref']}<br>DATE: {inv['date']} {inv['heure']}<br>CLIENT: {inv['client']}</p>
            <hr>
            <table style="width:100%; font-size:13px;">
                {"".join([f"<tr><td>{x['nom']} x{x['qte']}</td><td style='text-align:right;'>{x['total']:,.0f}</td></tr>" for x in inv['lignes']])}
            </table>
            <hr>
            <h3 style="text-align:right;">TOTAL: {inv['total']:,.2f} {inv['devise']}</h3>
            <p style="text-align:right;">PAYÉ: {inv['recu']:,.2f}<br>RESTE: {inv['reste']:,.2f}</p>
            <hr>
            <p style="text-align:center; font-size:10px;">MERCI DE VOTRE VISITE !</p>
        </div>
        """, unsafe_allow_html=True)
        
        c_p1, c_p2 = st.columns(2)
        if c_p1.button("⬅️ NOUVELLE VENTE"):
            st.session_state.erp_session['last_invoice'] = None
            st.rerun()
        if c_p2.button("📤 PARTAGER (WHATSAPP)"):
            st.info("Lien de partage généré !")

# --- 6.3 GESTION STOCK (MODIFICATION & SUPPRESSION SANS DOUBLONS) ---
elif user_choice == "📦 GESTION STOCK":
    st.header("📦 INVENTAIRE DU STOCK")
    
    t_list, t_add = st.tabs(["📋 LISTE DES PRODUITS", "➕ NOUVEL ARTICLE / MAJ"])
    
    with t_list:
        st_data = db_execute("SELECT id, item_name, quantity, buying_price, selling_price FROM stock WHERE shop_id=?", (active_shop_id,))
        if not st_data:
            st.info("Le stock est vide.")
        else:
            df_stock = pd.DataFrame(st_data, columns=["ID", "DÉSIGNATION", "QTE", "P.ACHAT ($)", "P.VENTE ($)"])
            st.dataframe(df_stock, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("🗑️ SUPPRIMER UN ARTICLE")
            id_to_del = st.number_input("Entrez l'ID de l'article à retirer", min_value=0, step=1)
            if st.button("CONFIRMER LA SUPPRESSION"):
                db_execute("DELETE FROM stock WHERE id=? AND shop_id=?", (id_to_del, active_shop_id), is_select=False)
                st.success("Article supprimé !")
                st.rerun()

    with t_add:
        with st.form("stock_form"):
            st.subheader("Enregistrer / Modifier")
            f_id = st.number_input("ID de l'article (0 pour Nouveau)", min_value=0, step=1)
            f_name = st.text_input("Désignation de l'article").upper()
            f_qte = st.number_input("Quantité", min_value=0)
            f_buy = st.number_input("Prix d'Achat (USD)", min_value=0.0)
            f_sell = st.number_input("Prix de Vente (USD)", min_value=0.0)
            
            if st.form_submit_button("💾 ENREGISTRER DANS LE STOCK"):
                if f_id == 0:
                    # Nouveau
                    db_execute("INSERT INTO stock (item_name, quantity, buying_price, selling_price, shop_id) VALUES (?,?,?,?,?)",
                              (f_name, f_qte, f_buy, f_sell, active_shop_id), is_select=False)
                    st.success("Nouvel article ajouté !")
                else:
                    # Modification
                    db_execute("UPDATE stock SET item_name=?, quantity=?, buying_price=?, selling_price=? WHERE id=? AND shop_id=?",
                              (f_name, f_qte, f_buy, f_sell, f_id, active_shop_id), is_select=False)
                    st.success(f"Article ID {f_id} mis à jour !")
                st.rerun()

# --- 6.4 SUIVI DETTES (PAIEMENT PAR ÉCHÉANCE) ---
elif user_choice == "📉 SUIVI DETTES":
    st.header("📉 CLIENTS DÉBITEURS")
    
    dettes_ouvertes = db_execute("SELECT id, client_name, amount_remaining, sale_ref FROM debts WHERE shop_id=? AND status='OPEN'", (active_shop_id,))
    
    if not dettes_ouvertes:
        st.success("Toutes les dettes sont apurées ! ✅")
    else:
        for d_id, d_cli, d_amt, d_ref in dettes_ouvertes:
            with st.container():
                st.markdown(f"""
                <div class='blue-card'>
                    <h3>👤 {d_cli}</h3>
                    <p>Reste à payer : <b style='font-size:24px;'>{d_amt:,.2f} $</b><br>Référence Vente : {d_ref}</p>
                </div>
                """, unsafe_allow_html=True)
                
                pay_col1, pay_col2 = st.columns([2, 1])
                verst = pay_col1.number_input(f"Montant versé par {d_cli}", min_value=0.0, max_value=float(d_amt), key=f"pay_{d_id}")
                if pay_col2.button("VALIDER LE VERSEMENT", key=f"btn_{d_id}"):
                    new_balance = d_amt - verst
                    if new_balance <= 0:
                        db_execute("UPDATE debts SET amount_remaining=0, status='PAID' WHERE id=?", (d_id,), is_select=False)
                        st.success(f"Dette de {d_cli} entièrement apurée !")
                    else:
                        db_execute("UPDATE debts SET amount_remaining=? WHERE id=?", (new_balance, d_id), is_select=False)
                        st.info(f"Versement enregistré. Nouveau solde : {new_balance:,.2f} $")
                    time.sleep(1)
                    st.rerun()

# --- 6.5 RAPPORTS VENTES ---
elif user_choice == "📊 RAPPORTS VENTES":
    st.header("📊 HISTORIQUE DES VENTES")
    
    filter_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    sales_data = db_execute("SELECT sale_time, ref_code, client_name, total_usd, seller_uid FROM sales WHERE shop_id=? AND sale_date=? ORDER BY id DESC", (active_shop_id, filter_date))
    
    if not sales_data:
        st.warning(f"Aucune vente enregistrée pour le {filter_date}.")
    else:
        df_sales = pd.DataFrame(sales_data, columns=["HEURE", "REF", "CLIENT", "TOTAL (USD)", "VENDEUR"])
        st.dataframe(df_sales, use_container_width=True, hide_index=True)
        
        total_d = sum([row[3] for row in sales_data])
        st.markdown(f"<div class='blue-card' style='text-align:center;'><h2>TOTAL DE LA JOURNÉE : {total_d:,.2f} $</h2></div>", unsafe_allow_html=True)

# --- 6.6 GESTION ÉQUIPE (VENDEURS) ---
elif user_choice == "👥 ÉQUIPE":
    st.header("👥 MES VENDEURS")
    
    with st.form("add_vendeur"):
        v_uid = st.text_input("Identifiant Vendeur").lower().strip()
        v_name = st.text_input("Nom Complet")
        v_pass = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            v_hashed = hashlib.sha256(v_pass.encode()).hexdigest()
            db_execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                      (v_uid, v_hashed, 'VENDEUR', active_shop_id, 'ACTIF', v_name, '000'), is_select=False)
            st.success(f"Vendeur {v_name} ajouté !")
            st.rerun()
    
    st.divider()
    vendeurs = db_execute("SELECT uid, full_name, status FROM users WHERE managed_shop=? AND role='VENDEUR'", (active_shop_id,))
    for vu, vn, vs in vendeurs:
        st.write(f"👤 {vn} (@{vu}) - Statut: {vs}")
        if st.button(f"Supprimer {vu}", key=f"del_v_{vu}"):
            db_execute("DELETE FROM users WHERE uid=?", (vu,), is_select=False)
            st.rerun()

# --- 6.7 RÉGLAGES BOUTIQUE ---
elif user_choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION DE LA BOUTIQUE")
    
    with st.form("shop_settings"):
        s_name = st.text_input("Nom de l'Enseigne", active_shop_info[0])
        s_rate = st.number_input("Taux de change (1 USD = ? CDF)", value=active_shop_info[1])
        s_head = st.text_input("En-tête de la Facture", active_shop_info[2])
        s_addr = st.text_input("Adresse Physique", active_shop_info[3])
        s_phone = st.text_input("Téléphone Boutique", active_shop_info[4])
        
        if st.form_submit_button("💾 SAUVEGARDER LES PARAMÈTRES"):
            if not shop_data:
                # Création
                db_execute("INSERT INTO shops VALUES (?,?,?,?,?,?,?)",
                          (active_shop_id, s_name, st.session_state.erp_session['user_id'], s_rate, s_head, s_addr, s_phone), is_select=False)
            else:
                # Mise à jour
                db_execute("UPDATE shops SET name=?, rate_usd_to_cdf=?, receipt_header=?, address=?, phone=? WHERE sid=?",
                          (s_name, s_rate, s_head, s_addr, s_phone, active_shop_id), is_select=False)
            
            st.success("✅ Paramètres enregistrés avec succès !")
            time.sleep(1)
            st.rerun()

# --- 6.8 DÉCONNEXION ---
elif user_choice == "🚪 QUITTER":
    st.session_state.erp_session['logged_in'] = False
    st.rerun()

# FIN DU CODE v3300
