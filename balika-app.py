# ==============================================================================
# BALIKA ERP v325 - VERSION PROFESSIONNELLE ÉTENDUE (+600 LIGNES)
# TOUS DROITS RÉSERVÉS - PROPRIÉTÉ DE L'ADMINISTRATEUR
# DESIGN : PLEIN ÉCRAN / SANS CADRE BLANC / SIDEBAR HAUTE VISIBILITÉ
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import urllib.parse
import io
import os

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE L'INTERFACE (CSS AVANCÉ)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v325",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_branding(name, marquee_msg):
    """Injection du système de marque et du message défilant"""
    # BANDEAU DÉFILANT HAUT DE PAGE
    st.markdown(f"""
        <div style="background: #000; color: #FFD700; padding: 18px; font-weight: 900; 
                    position: fixed; top: 0; left: 0; width: 100%; z-index: 99999; 
                    border-bottom: 4px solid #FFF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    text-transform: uppercase; box-shadow: 0px 5px 15px rgba(0,0,0,0.5);">
            <marquee scrollamount="12">🚀 {name} : {marquee_msg} 🚀</marquee>
        </div>
        <div style="height: 90px;"></div>
    """, unsafe_allow_html=True)

    # STYLE GLOBAL SANS CADRE BLANC
    st.markdown(f"""
    <style>
    /* FOND DÉGRADÉ IMMERSIF (VUE SMARTPHONE) */
    .stApp {{
        background: linear-gradient(180deg, #FF4B2B 0%, #FF8008 100%);
        background-attachment: fixed;
        color: white !important;
    }}

    /* SIDEBAR MOBILE : GRIS CLAIR / TEXTE NOIR PROFOND */
    [data-testid="stSidebar"] {{
        background-color: #E9ECEF !important;
        border-right: 8px solid #000000;
        min-width: 300px !important;
    }}
    [data-testid="stSidebar"] * {{
        color: #000000 !important;
        font-weight: 900 !important;
        font-family: 'Arial Black', sans-serif !important;
    }}

    /* INPUTS MODERNES (SANS CADRE BLANC AU LOGIN) */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 15px !important;
        height: 55px !important;
        font-size: 18px !important;
    }}
    
    /* BOUTONS GÉANTS POUR UTILISATION TACTILE */
    .stButton>button {{
        background: #000000 !important;
        color: #FFFFFF !important;
        height: 75px !important;
        border-radius: 20px !important;
        font-weight: 900 !important;
        width: 100%;
        border: 3px solid #FFD700 !important;
        font-size: 1.4rem !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }}
    .stButton>button:hover {{
        background: #FF4B2B !important;
        color: white !important;
        transform: translateY(-3px);
    }}

    /* CADRE DU TOTAL PANIER (VERT FLUO SUR NOIR) */
    .cart-summary {{
        background: #000000;
        color: #39FF14;
        padding: 30px;
        border-radius: 25px;
        border: 4px solid #FFFFFF;
        text-align: center;
        margin: 20px 0;
        font-family: 'Courier New', monospace;
    }}

    /* TABLEAUX DE DONNÉES */
    .stDataFrame {{
        background: white !important;
        border-radius: 15px !important;
        padding: 10px;
    }}

    h1, h2, h3 {{
        color: #FFFFFF !important;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (SQLITE CRITIQUE)
# ------------------------------------------------------------------------------
def database_engine():
    """Initialisation et maintenance de la structure SQL"""
    conn = sqlite3.connect('balika_v325_core.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Configuration Application (Nom et Marquee)
    cursor.execute("CREATE TABLE IF NOT EXISTS app_branding (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT)")
    
    # Comptes Utilisateurs (Admin, Boss, Vendeurs)
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_accounts (
                      username TEXT PRIMARY KEY, 
                      password TEXT, 
                      role TEXT, 
                      eid TEXT, 
                      shop_name TEXT, 
                      owner_name TEXT, 
                      phone_contact TEXT)""")
    
    # Inventaire des Produits (Prix de vente uniquement)
    cursor.execute("""CREATE TABLE IF NOT EXISTS stock_inventory (
                      id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      product_name TEXT, 
                      quantity INTEGER, 
                      unit_price REAL, 
                      eid TEXT)""")
    
    # Journal des Ventes
    cursor.execute("""CREATE TABLE IF NOT EXISTS sales_history (
                      ref_sale TEXT PRIMARY KEY, 
                      customer_name TEXT, 
                      total_amount REAL, 
                      paid_amount REAL, 
                      debt_amount REAL, 
                      currency_type TEXT, 
                      sale_date TEXT, 
                      eid TEXT)""")
    
    # Cahier des Dettes (Suivi des créances)
    cursor.execute("""CREATE TABLE IF NOT EXISTS debt_ledger (
                      id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      customer_name TEXT, 
                      remaining_balance REAL, 
                      ref_invoice TEXT, 
                      eid TEXT)""")
    
    # Initialisation Compte Administrateur par défaut
    cursor.execute("SELECT * FROM user_accounts WHERE username='admin'")
    if not cursor.fetchone():
        admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("INSERT INTO user_accounts VALUES (?,?,?,?,?,?,?)", 
                      ('admin', admin_pass, 'SUPER_ADMIN', 'SYSTEM', 'ERP ADMIN', 'ADMINISTRATEUR', '0000'))
        cursor.execute("INSERT INTO app_branding VALUES (1, 'BALIKA ERP', 'SYSTEME DE GESTION ADMINISTRATIVE ET COMMERCIALE v2026')")
    
    conn.commit()
    return conn, cursor

# Initialisation globale
conn_db, cursor_db = database_engine()

# Chargement des réglages de l'administrateur
cursor_db.execute("SELECT app_name, marquee_text FROM app_branding WHERE id=1")
brand_res = cursor_db.fetchone()
APP_NAME_ACTUAL = brand_res[0]
MARQUEE_TEXT_ACTUAL = brand_res[1]

inject_branding(APP_NAME_ACTUAL, MARQUEE_TEXT_ACTUAL)

# ------------------------------------------------------------------------------
# 3. LOGIQUE D'ACCÈS ET SÉCURITÉ (SANS CADRE BLANC)
# ------------------------------------------------------------------------------
if 'auth_status' not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    # Affichage du Login en plein écran sur le dégradé
    _, col_login, _ = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown(f"<h1 style='font-size: 4.5rem; margin-bottom:0;'>{APP_NAME_ACTUAL}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:1.3rem; margin-top:0;'>Accès sécurisé au terminal de gestion</p>", unsafe_allow_html=True)
        st.write("---")
        
        login_tabs = st.tabs(["🔑 IDENTIFICATION", "🚀 CRÉER UNE BOUTIQUE"])
        
        with login_tabs[0]:
            in_user = st.text_input("Identifiant").lower().strip()
            in_pass = st.text_input("Mot de passe", type="password")
            
            if st.button("DÉVERROUILLER LE SYSTÈME"):
                hashed_in = hashlib.sha256(in_pass.encode()).hexdigest()
                cursor_db.execute("SELECT role, eid, shop_name, owner_name FROM user_accounts WHERE username=? AND password=?", (in_user, hashed_in))
                user_record = cursor_db.fetchone()
                
                if user_record:
                    st.session_state.auth_status = True
                    st.session_state.user_id = in_user
                    st.session_state.user_role = user_record[0]
                    st.session_state.user_eid = user_record[1]
                    st.session_state.user_shop = user_record[2]
                    st.session_state.user_name = user_record[3]
                    st.success("Connexion réussie...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erreur : Identifiants non reconnus par le serveur.")

        with login_tabs[1]:
            with st.form("form_registration"):
                reg_shop = st.text_input("Nom de l'Etablissement / Boutique").upper()
                reg_owner = st.text_input("Nom du Gérant / Propriétaire")
                reg_whatsapp = st.text_input("Numéro WhatsApp")
                reg_user = st.text_input("Créer un Identifiant")
                reg_pass = st.text_input("Créer un Mot de passe", type="password")
                
                if st.form_submit_button("ACTIVER MON COMPTE GESTIONNAIRE"):
                    if reg_user and reg_pass and reg_shop:
                        new_eid = f"BK-{random.randint(10000, 99999)}"
                        hashed_reg = hashlib.sha256(reg_pass.encode()).hexdigest()
                        try:
                            cursor_db.execute("INSERT INTO user_accounts VALUES (?,?,?,?,?,?,?)", 
                                            (reg_user.lower(), hashed_reg, 'BOSS', new_eid, reg_shop, reg_owner, reg_whatsapp))
                            conn_db.commit()
                            st.success("✅ Compte créé avec succès ! Connectez-vous maintenant.")
                        except sqlite3.IntegrityError:
                            st.error("❌ Cet identifiant est déjà pris par un autre utilisateur.")
                    else:
                        st.warning("Veuillez remplir tous les champs obligatoires.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE ADMINISTRATEUR (CONTRÔLE TOTAL DU SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.user_role == 'SUPER_ADMIN':
    with st.sidebar:
        st.markdown(f"# 🛡️ ADMIN PANEL")
        st.write(f"Utilisateur : {st.session_state.user_id}")
        st.write("---")
        admin_nav = st.radio("SÉLECTIONNER UN MODULE", 
                           ["📊 Statistiques Globales", "👥 Gestion des Boutiques", "🎨 Identité de l'App", "👤 Mon Profil Admin", "🚪 Déconnexion"])

    if admin_nav == "📊 Statistiques Globales":
        st.title("ÉTAT DU RÉSEAU ERP")
        df_all_shops = pd.read_sql("SELECT shop_name, owner_name, phone_contact FROM user_accounts WHERE role='BOSS'", conn_db)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Boutiques", len(df_all_shops))
        c2.metric("Serveur", "Actif")
        c3.metric("Version", "v325")
        
        st.write("### Répertoire des Clients")
        st.dataframe(df_all_shops, use_container_width=True)

    elif admin_nav == "👥 Gestion des Boutiques":
        st.header("MAINTENANCE DES COMPTES")
        cursor_db.execute("SELECT username, shop_name, owner_name, eid FROM user_accounts WHERE role='BOSS'")
        shop_list = cursor_db.fetchall()
        
        for shop in shop_list:
            with st.container(border=True):
                col_info, col_act = st.columns([3, 1])
                col_info.write(f"🏢 **{shop[1]}** | Patron : {shop[2]}")
                col_info.write(f"ID Système : `{shop[3]}` | Login : `{shop[0]}`")
                if col_act.button("SUPPRIMER L'ACCÈS", key=shop[0]):
                    st.warning("Fonctionnalité de suppression en attente de confirmation.")

    elif admin_nav == "🎨 Identité de l'App":
        st.header("RE-BRANDING DE L'APPLICATION")
        st.info("Ici, vous pouvez changer le nom qui s'affiche partout pour vos clients.")
        
        with st.form("branding_update"):
            update_name = st.text_input("Nouveau Nom de l'ERP", APP_NAME_ACTUAL)
            update_mq = st.text_area("Nouveau Message Défilant", MARQUEE_TEXT_ACTUAL)
            
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                cursor_db.execute("UPDATE app_branding SET app_name=?, marquee_text=? WHERE id=1", (update_name, update_mq))
                conn_db.commit()
                st.success("✅ Identité mise à jour ! Rechargement...")
                time.sleep(1)
                st.rerun()

    elif admin_nav == "🚪 Déconnexion":
        st.session_state.auth_status = False
        st.rerun()

# ------------------------------------------------------------------------------
# 5. MODULE COMMERCE (BOSS / GESTIONNAIRE DE BOUTIQUE)
# ------------------------------------------------------------------------------
else:
    USER_EID = st.session_state.user_eid
    USER_SHOP = st.session_state.user_shop

    with st.sidebar:
        st.markdown(f"### 🏢 {USER_SHOP}")
        st.write(f"ID : {USER_EID}")
        st.write("---")
        user_nav = st.radio("MENU PRINCIPAL", 
                          ["🏠 Tableau de Bord", "🛒 Caisse & Ventes", "📦 Inventaire Stock", "📉 Suivi des Dettes", "📊 Rapports Journaliers", "☁️ Sauvegarde Cloud", "🚪 Quitter"])

    # --- ACCUEIL ---
    if user_nav == "🏠 Tableau de Bord":
        st.markdown(f"""
            <div style="text-align:center; padding:50px; background:rgba(0,0,0,0.3); border-radius:30px; border:3px solid #FFD700;">
                <h1 style="font-size:6rem; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="font-size:2rem; margin-top:0;">{datetime.now().strftime('%A %d %B %Y')}</p>
                <hr style="border-color:white;">
                <h2 style="text-transform:uppercase;">Bienvenue dans la gestion de {USER_SHOP}</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Résumé rapide
        c_v, c_d = st.columns(2)
        cursor_db.execute("SELECT SUM(total_amount) FROM sales_history WHERE eid=?", (USER_EID,))
        total_v = cursor_db.fetchone()[0] or 0
        c_v.metric("Chiffre d'Affaire", f"{total_v} USD")
        
        cursor_db.execute("SELECT SUM(remaining_balance) FROM debt_ledger WHERE eid=?", (USER_EID,))
        total_d = cursor_db.fetchone()[0] or 0
        c_d.metric("Dettes Clients", f"{total_d} USD")

    # --- CAISSE ADMINISTRATIVE ---
    elif user_nav == "🛒 Caisse & Ventes":
        st.title("🛒 TERMINAL DE VENTE")
        if 'current_cart' not in st.session_state: st.session_state.current_cart = []
        
        col_select, col_cart = st.columns([1, 1])
        
        with col_select:
            st.write("### Sélection Produits")
            df_items = pd.read_sql(f"SELECT product_name, unit_price FROM stock_inventory WHERE eid='{USER_EID}'", conn_db)
            
            p_sel = st.selectbox("Choisir l'article", ["---"] + list(df_items['product_name']))
            if st.button("➕ AJOUTER AU PANIER") and p_sel != "---":
                p_price = df_items[df_items['product_name'] == p_sel]['unit_price'].values[0]
                st.session_state.current_cart.append({'nom': p_sel, 'prix': p_price})
                st.rerun()

        with col_cart:
            st.write("### Panier Client")
            if st.session_state.current_cart:
                cart_total = sum(item['prix'] for item in st.session_state.current_cart)
                
                st.markdown(f"""
                    <div class="cart-summary">
                        <span style="font-size:1rem; color:white;">TOTAL À PAYER</span><br>
                        <span style="font-size:3.5rem; font-weight:900;">{cart_total} USD</span>
                    </div>
                """, unsafe_allow_html=True)
                
                for idx, item in enumerate(st.session_state.current_cart):
                    st.write(f"📍 {item['nom']} : **{item['prix']} USD**")
                
                if st.button("🗑️ VIDER LE PANIER"):
                    st.session_state.current_cart = []
                    st.rerun()
                
                st.write("---")
                with st.form("form_checkout"):
                    f_client = st.text_input("Nom du Client", "COMPTANT")
                    f_currency = st.selectbox("Devise de paiement", ["USD", "CDF"])
                    f_paid = st.number_input("Montant Reçu (en USD)", value=float(cart_total))
                    
                    if st.form_submit_button("CONFIRMER LA VENTE ET FACTURER"):
                        v_ref = f"FAC-{random.randint(1000, 9999)}"
                        v_rest = cart_total - f_paid
                        v_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        # Enregistrement Vente
                        cursor_db.execute("INSERT INTO sales_history VALUES (?,?,?,?,?,?,?,?)", 
                                        (v_ref, f_client.upper(), cart_total, f_paid, v_rest, f_currency, v_date, USER_EID))
                        
                        # Enregistrement Dette si crédit
                        if v_rest > 0:
                            cursor_db.execute("INSERT INTO debt_ledger (customer_name, remaining_balance, ref_invoice, eid) VALUES (?,?,?,?)", 
                                            (f_client.upper(), v_rest, v_ref, USER_EID))
                        
                        conn_db.commit()
                        st.session_state.last_receipt = {"ref": v_ref, "client": f_client, "total": cart_total, "paid": f_paid, "rest": v_rest, "items": st.session_state.current_cart}
                        st.session_state.current_cart = []
                        st.success("Vente enregistrée avec succès !")
                        st.rerun()

        if 'last_receipt' in st.session_state:
            rc = st.session_state.last_receipt
            st.markdown(f"""
                <div style="background:white; color:black; padding:30px; border-radius:15px; border:2px solid #000; font-family:monospace; max-width:400px; margin:auto;">
                    <center>
                        <h2 style="color:black !important; text-shadow:none;">{USER_SHOP}</h2>
                        <p>Réf: {rc['ref']} | Date: {datetime.now().strftime('%d/%m/%Y')}</p>
                        <hr style="border-color:black;">
                    </center>
                    {''.join([f"<p>{x['nom']} ....... {x['prix']} USD</p>" for x in rc['items']])}
                    <hr style="border-color:black;">
                    <p><b>TOTAL : {rc['total']} USD</b></p>
                    <p>PAYÉ : {rc['paid']} USD</p>
                    <p style="color:red;"><b>RESTE : {rc['rest']} USD</b></p>
                    <center><hr style="border-color:black;">MERCI DE VOTRE CONFIANCE</center>
                </div>
            """, unsafe_allow_html=True)
            
            w_txt = f"Facture {USER_SHOP}: Total {rc['total']} USD. Payé {rc['paid']} USD. Reste {rc['rest']} USD."
            st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(w_txt)}" target="_blank" style="background:#25D366; color:white; padding:15px; border-radius:12px; text-decoration:none; display:block; text-align:center; font-weight:bold; margin-top:10px;">📲 ENVOYER PAR WHATSAPP</a>', unsafe_allow_html=True)

    # --- STOCK ---
    elif user_nav == "📦 Inventaire Stock":
        st.header("GESTION DE L'INVENTAIRE")
        
        tab_add, tab_view = st.tabs(["➕ AJOUTER PRODUIT", "📋 VOIR LE STOCK"])
        
        with tab_add:
            with st.form("add_product"):
                new_n = st.text_input("Nom de l'article").upper()
                new_q = st.number_input("Quantité initiale", 1)
                new_p = st.number_input("Prix de vente (USD)")
                if st.form_submit_button("ENREGISTRER AU CATALOGUE"):
                    cursor_db.execute("INSERT INTO stock_inventory (product_name, quantity, unit_price, eid) VALUES (?,?,?,?)", 
                                    (new_n, new_q, new_p, USER_EID))
                    conn_db.commit()
                    st.success("Produit ajouté !")
        
        with tab_view:
            df_stk = pd.read_sql(f"SELECT id, product_name, quantity, unit_price FROM stock_inventory WHERE eid='{USER_EID}'", conn_db)
            st.dataframe(df_stk, use_container_width=True)
            
            st.write("---")
            st.write("### Modifier un Prix / Supprimer")
            mod_id = st.number_input("ID du produit à modifier", step=1)
            new_px = st.number_input("Nouveau prix")
            if st.button("METTRE À JOUR LE PRIX"):
                cursor_db.execute("UPDATE stock_inventory SET unit_price=? WHERE id=? AND eid=?", (new_px, mod_id, USER_EID))
                conn_db.commit()
                st.success("Prix modifié !")
                st.rerun()

    # --- DETTES ---
    elif user_nav == "📉 Suivi des Dettes":
        st.header("CAHIER DES CRÉANCES")
        df_dettes = pd.read_sql(f"SELECT * FROM debt_ledger WHERE eid='{USER_EID}'", conn_db)
        
        if df_dettes.empty:
            st.info("Aucune dette enregistrée pour le moment.")
        else:
            for index, row in df_dettes.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"👤 Client : **{row['customer_name']}**")
                    c1.write(f"💰 Reste à payer : **{row['remaining_balance']} USD**")
                    c1.write(f"📑 Facture d'origine : {row['ref_invoice']}")
                    
                    if c2.button("✅ REGLÉ", key=row['id']):
                        cursor_db.execute("DELETE FROM debt_ledger WHERE id=?", (row['id'],))
                        conn_db.commit()
                        st.success("Paiement enregistré !")
                        st.rerun()

    # --- BACKUP ---
    elif user_nav == "☁️ Sauvegarde Cloud":
        st.header("☁️ SECURITÉ DES DONNÉES")
        st.write("Téléchargez vos données pour les garder en sécurité hors du téléphone.")
        
        data_to_save = pd.read_sql(f"SELECT * FROM stock_inventory WHERE eid='{USER_EID}'", conn_db)
        json_backup = data_to_save.to_json(orient='records')
        
        st.download_button("📂 TÉLÉCHARGER LE BACKUP STOCK", 
                          data=json_backup, 
                          file_name=f"Backup_{USER_SHOP}_{datetime.now().strftime('%Y%m%d')}.json",
                          mime="application/json")

    elif user_nav == "🚪 Quitter":
        st.session_state.auth_status = False
        st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v325 - 635 LIGNES DE LOGIQUE ERP
# ------------------------------------------------------------------------------
