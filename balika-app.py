# ==============================================================================
# ANASH ERP (BY BALIKA BUSINESS) - VERSION MASTER v2700
# DESIGN : GLASSMORPHISM COBALT BLUE (SPÉCIAL MOBILE)
# ARCHITECTURE : MULTI-SHOP / MULTI-DEVISE / DETTES PAR TRANCHES
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
# 1. CONFIGURATION VISUELLE ET INJECTION CSS (COBALT BLUE & GLASS)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v2700", layout="wide", initial_sidebar_state="expanded")

def apply_ultra_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@300;400;700&display=swap');

    /* Fond Royal Cobalt Blue */
    .stApp {
        background: radial-gradient(circle at center, #0044ff 0%, #001133 100%) !important;
        background-attachment: fixed !important;
        color: white !important;
        font-family: 'Inter', sans-serif;
    }

    /* Marquee Admin (Fixé en haut) */
    .marquee-container {
        position: fixed; top: 0; left: 0; width: 100%; background: rgba(0,0,0,0.9);
        color: #00ff00; z-index: 99999; height: 35px; line-height: 35px;
        font-weight: bold; border-bottom: 2px solid #ffffff; font-size: 14px;
        text-transform: uppercase;
    }

    /* Horloge Géante 80mm style Néon */
    .hero-clock-box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(25px); border-radius: 40px; padding: 60px 20px;
        text-align: center; border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 40px auto; max-width: 800px;
        box-shadow: 0 20px 70px rgba(0,0,0,0.8);
    }
    .clock-time {
        font-family: 'Orbitron', sans-serif; font-size: 110px; font-weight: 900;
        color: #ffffff; text-shadow: 0 0 15px #00ccff, 0 0 40px #00ccff;
        line-height: 1; margin: 0;
    }
    .clock-date {
        font-size: 26px; color: #00ccff; letter-spacing: 6px; 
        margin-top: 20px; text-transform: uppercase;
    }

    /* Cards Glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 25px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.4);
    }

    /* Boutons XXL pour Smartphone */
    .stButton>button {
        width: 100% !important; height: 75px !important; border-radius: 20px !important;
        background: linear-gradient(135deg, #0077ff, #0033aa) !important;
        color: white !important; font-size: 20px !important; font-weight: bold !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
        transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .stButton>button:active { transform: scale(0.94); }

    /* Cadre de Total (Caisse) */
    .total-frame {
        background: #000; color: #00ff00; padding: 25px; border-radius: 20px;
        border: 4px solid #00ff00; text-align: center; font-size: 42px;
        font-weight: 900; margin: 30px 0; box-shadow: 0 0 30px rgba(0,255,0,0.4);
        font-family: 'Orbitron', sans-serif;
    }

    /* Sidebar Personnalisée */
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #ddd; }
    [data-testid="stSidebar"] * { color: #111 !important; font-weight: 600; }
    .sb-header { padding: 20px; text-align: center; background: #0044cc; color: white !important; border-radius: 0 0 20px 20px; }

    /* Inputs Visibilité Maximale */
    input, select, textarea {
        background-color: white !important; color: black !important;
        border-radius: 12px !important; height: 50px !important; border: 1px solid #ccc !important;
    }

    /* Tables Mobile-Friendly */
    .mobile-table-row {
        background: white; color: black; padding: 20px; border-radius: 15px;
        margin-bottom: 15px; border-left: 10px solid #0044ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (PERSISTANCE TOTALE)
# ------------------------------------------------------------------------------
DB_ANASH = "anash_system_v2700.db"

def execute_db(sql, params=(), fetch=True):
    with sqlite3.connect(DB_ANASH, timeout=60) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def boot_system():
    # Table des Utilisateurs (Status: EN_ATTENTE par défaut)
    execute_db("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, owner_ref TEXT, 
        status TEXT DEFAULT 'EN_ATTENTE', full_name TEXT, tel TEXT)""", fetch=False)
    
    # Table des Boutiques
    execute_db("""CREATE TABLE IF NOT EXISTS shops (
        shop_id TEXT PRIMARY KEY, shop_name TEXT, owner_uid TEXT, 
        rate REAL DEFAULT 2800.0, header TEXT, address TEXT, phone TEXT)""", fetch=False)
    
    # Table Stock (ID unique, Nom, Qte, Achat, Vente, Shop_ID)
    execute_db("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, 
        qty INTEGER, buy_price REAL, sell_price REAL, shop_id TEXT)""", fetch=False)
    
    # Table Ventes
    execute_db("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total_usd REAL, paid_usd REAL, debt_usd REAL, currency TEXT, 
        date_v TEXT, time_v TEXT, seller TEXT, shop_id TEXT, details TEXT)""", fetch=False)
    
    # Table Dettes (Solde Restant)
    execute_db("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, 
        balance REAL, sale_ref TEXT, shop_id TEXT, status TEXT DEFAULT 'ACTIF')""", fetch=False)
    
    # Historique des tranches de paiement
    execute_db("""CREATE TABLE IF NOT EXISTS debt_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, debt_id INTEGER, 
        amount REAL, p_date TEXT)""", fetch=False)
    
    # Dépenses
    execute_db("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, reason TEXT, amount REAL, 
        e_date TEXT, shop_id TEXT)""", fetch=False)
    
    # Configuration Globale (Marquee)
    execute_db("CREATE TABLE IF NOT EXISTS app_config (id INTEGER PRIMARY KEY, title TEXT, marquee TEXT)", fetch=False)

    # Création du Super Admin (S'il n'existe pas)
    if not execute_db("SELECT * FROM users WHERE uid='admin'"):
        execute_db("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                  ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'), fetch=False)
    
    if not execute_db("SELECT * FROM app_config"):
        execute_db("INSERT INTO app_config VALUES (1, 'ANASH ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION PROFESSIONNEL v2700')", fetch=False)

boot_system()
cfg = execute_db("SELECT title, marquee FROM app_config WHERE id=1")[0]

# ------------------------------------------------------------------------------
# 3. GESTION DES SESSIONS
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'uid': "", 'role': "", 'owner': "",
        'shop_active': None, 'cart': {}, 'last_receipt': None
    })

apply_ultra_theme()
st.markdown(f'<div class="marquee-container"><marquee scrollamount="8">{cfg[1]}</marquee></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS (CONNEXION & INSCRIPTION LIBRE)
# ------------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown(f"<div class='hero-clock-box'><h1>{cfg[0]}</h1><p>Connectez-vous pour continuer</p></div>", unsafe_allow_html=True)
        t_login, t_signup = st.tabs(["🔒 CONNEXION", "📝 CRÉER UN COMPTE"])
        
        with t_login:
            in_user = st.text_input("Identifiant").lower().strip()
            in_pass = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU SYSTÈME"):
                res = execute_db("SELECT pwd, role, owner_ref, status FROM users WHERE uid=?", (in_user,))
                if res and hashlib.sha256(in_pass.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "EN_ATTENTE":
                        st.warning("⏳ Compte en attente de validation par l'Administrateur.")
                    elif res[0][3] == "BLOQUE":
                        st.error("🚫 Accès refusé. Ce compte est suspendu.")
                    else:
                        st.session_state.update({'logged_in':True, 'uid':in_user, 'role':res[0][1], 'owner':res[0][2]})
                        # Assigner la boutique par défaut
                        if res[0][1] == "GERANT":
                            b_list = execute_db("SELECT shop_id FROM shops WHERE owner_uid=?", (in_user,))
                            if b_list: st.session_state.shop_active = b_list[0][0]
                        elif res[0][1] == "VENDEUR":
                            st.session_state.shop_active = res[0][2]
                        st.rerun()
                else: st.error("❌ Identifiants incorrects.")

        with t_signup:
            st.info("L'inscription est libre. Un administrateur devra valider votre accès.")
            with st.form("signup_form"):
                new_uid = st.text_input("Choisir Identifiant").lower()
                new_name = st.text_input("Nom Complet")
                new_tel = st.text_input("Numéro de Téléphone")
                new_pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("S'INSCRIRE COMME GÉRANT"):
                    if execute_db("SELECT uid FROM users WHERE uid=?", (new_uid,)):
                        st.error("❌ Identifiant déjà utilisé.")
                    else:
                        execute_db("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                                  (new_uid, hashlib.sha256(new_pwd.encode()).hexdigest(), 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', new_name, new_tel), fetch=False)
                        st.success("✅ Inscription réussie ! Patientez pour la validation Admin.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. DASHBOARD SUPER ADMIN (GESTION DES ACCÈS)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.markdown("<div class='sb-header'>🛠️ SUPER ADMIN</div>", unsafe_allow_html=True)
    adm_nav = st.sidebar.radio("Navigation", ["Validation des Comptes", "Réglages Système", "Quitter"])
    
    if adm_nav == "Validation des Comptes":
        st.header("👥 COMPTES EN ATTENTE & GESTION")
        users_list = execute_db("SELECT uid, full_name, tel, status FROM users WHERE role='GERANT'")
        for uid, name, tel, status in users_list:
            with st.container():
                st.markdown(f"<div class='glass-card'><h3>{name} (@{uid})</h3><p>Tel: {tel} | Statut: <b>{status}</b></p></div>", unsafe_allow_html=True)
                ca, cb, cc = st.columns(3)
                if ca.button("✅ ACTIVER", key=f"ok_{uid}"):
                    execute_db("UPDATE users SET status='ACTIF', owner_ref=? WHERE uid=?", (uid, uid), fetch=False)
                    st.rerun()
                if cb.button("⏸️ BLOQUER", key=f"bl_{uid}"):
                    execute_db("UPDATE users SET status='BLOQUE' WHERE uid=?", (uid,), fetch=False)
                    st.rerun()
                if cc.button("🗑️ SUPPRIMER", key=f"rm_{uid}"):
                    execute_db("DELETE FROM users WHERE uid=?", (uid,), fetch=False)
                    st.rerun()

    elif adm_nav == "Réglages Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("global_cfg"):
            a_title = st.text_input("Nom de l'Application", cfg[0])
            a_marq = st.text_area("Texte défilant", cfg[1])
            if st.form_submit_button("SAUVEGARDER"):
                execute_db("UPDATE app_config SET title=?, marquee=? WHERE id=1", (a_title, a_marq), fetch=False)
                st.rerun()

    if adm_nav == "Quitter": st.session_state.logged_in = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE GÉRANT & VENDEUR (CORE APPLICATION)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div class='sb-header'>👤 <b>{st.session_state.uid.upper()}</b><br><small>{st.session_state.role}</small></div>", unsafe_allow_html=True)
    
    # Gestion des boutiques pour le Gérant
    if st.session_state.role == "GERANT":
        mes_boutiques = execute_db("SELECT shop_id, shop_name FROM shops WHERE owner_uid=?", (st.session_state.uid,))
        if mes_boutiques:
            s_map = {b[1]: b[0] for b in mes_boutiques}
            s_choice = st.selectbox("Ma Boutique Active", list(s_map.keys()))
            st.session_state.shop_active = s_map[s_choice]
        
        main_menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 STOCK PAR ID", "📉 DETTES CLIENTS", "💸 DÉPENSES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE VENDEURS", "⚙️ RÉGLAGES BOUTIQUE", "🚪 DÉCONNEXION"]
    else:
        # Interface Vendeur : Accès limité
        main_menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 DETTES CLIENTS", "📊 RAPPORTS VENTES", "🚪 DÉCONNEXION"]
    
    choice = st.radio("MENU PRINCIPAL", main_menu)

# Chargement des données de la boutique active
shop_info = execute_db("SELECT shop_name, rate, header, address, phone FROM shops WHERE shop_id=?", (st.session_state.shop_active,))
if not shop_info:
    if st.session_state.role == "GERANT":
        st.warning("⚠️ Aucune boutique configurée. Veuillez créer une boutique dans le menu RÉGLAGES.")
        choice = "⚙️ RÉGLAGES BOUTIQUE"
    else: st.error("❌ Accès boutique non configuré."); st.stop()
else: shop_info = shop_info[0]

# --- 6.1 ACCUEIL (HORLOGE & STATS) ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='hero-clock-box'>
        <div class='clock-time'>{datetime.now().strftime('%H:%M')}</div>
        <div class='clock-date'>{datetime.now().strftime('%A, %d %B %Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard Financier Rapide
    today_d = datetime.now().strftime("%d/%m/%Y")
    recette_j = execute_db("SELECT SUM(total_usd) FROM sales WHERE shop_id=? AND date_v=?", (st.session_state.shop_active, today_d))[0][0] or 0
    depense_j = execute_db("SELECT SUM(amount) FROM expenses WHERE shop_id=? AND e_date=?", (st.session_state.shop_active, today_d))[0][0] or 0
    
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown(f"<div class='glass-card'><h4>RECETTE JOUR</h4><h2>{recette_j:,.2f} $</h2></div>", unsafe_allow_html=True)
    with col_2:
        st.markdown(f"<div class='glass-card'><h4>BÉNÉFICE ESTIMÉ</h4><h2>{(recette_j - depense_j):,.2f} $</h2></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (MULTI-DEVISE) ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.last_receipt:
        st.header("🛒 TERMINAL DE VENTE")
        devise_p = st.radio("Devise de paiement :", ["USD", "CDF"], horizontal=True)
        taux_change = shop_info[1]
        
        # Charger Stock
        articles = execute_db("SELECT item_name, sell_price, qty FROM items WHERE shop_id=?", (st.session_state.shop_active,))
        a_dict = {a[0]: (a[1], a[2]) for a in articles}
        
        # Recherche
        recherche = st.selectbox("🔎 Sélectionner un produit...", ["---"] + list(a_dict.keys()))
        if recherche != "---":
            if a_dict[recherche][1] > 0:
                st.session_state.cart[recherche] = st.session_state.cart.get(recherche, 0) + 1
                st.toast(f"✅ {recherche} ajouté !")
            else: st.error("❌ Stock insuffisant !")

        if st.session_state.cart:
            st.divider()
            total_panier = 0.0; cart_data = []
            for art, qte in list(st.session_state.cart.items()):
                p_usd = a_dict[art][0]
                p_final = p_usd if devise_p == "USD" else p_usd * taux_change
                stot = p_final * qte
                total_panier += stot
                cart_data.append({"nom": art, "qte": qte, "pu": p_final, "st": stot})
                
                with st.container():
                    st.markdown(f"<div class='glass-card' style='padding:15px; margin-bottom:10px;'><b>{art}</b><br>{qte} x {p_final:,.0f} = {stot:,.0f} {devise_p}</div>", unsafe_allow_html=True)
                    if st.button(f"🗑️ Retirer {art}"): del st.session_state.cart[art]; st.rerun()

            st.markdown(f"<div class='total-frame'>TOTAL : {total_panier:,.2f} {devise_p}</div>", unsafe_allow_html=True)
            
            client_nom = st.text_input("Nom du Client", "COMPTANT").upper()
            m_verse = st.number_input(f"Montant Reçu ({devise_p})", value=float(total_panier))
            m_reste = total_panier - m_verse
            
            if st.button("🏁 CONFIRMER ET IMPRIMER"):
                v_ref = f"FAC-{random.randint(10000,99999)}"
                d_v, h_v = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                
                # Conversion USD pour la BD
                t_usd = total_panier if devise_p == "USD" else total_panier / taux_change
                v_usd = m_verse if devise_p == "USD" else m_verse / taux_change
                r_usd = m_reste if devise_p == "USD" else m_reste / taux_change
                
                execute_db("""INSERT INTO sales (ref, client, total_usd, paid_usd, debt_usd, currency, date_v, time_v, seller, shop_id, details) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (v_ref, client_nom, t_usd, v_usd, r_usd, devise_p, d_v, h_v, st.session_state.uid, st.session_state.shop_active, json.dumps(cart_data)), fetch=False)
                
                # Mise à jour Stock
                for c in cart_data:
                    execute_db("UPDATE items SET qty = qty - ? WHERE item_name=? AND shop_id=?", (c['qte'], c['nom'], st.session_state.shop_active), fetch=False)
                
                # Gestion Dette
                if r_usd > 0:
                    execute_db("INSERT INTO debts (client_name, balance, sale_ref, shop_id) VALUES (?,?,?,?)", (client_nom, r_usd, v_ref, st.session_state.shop_active), fetch=False)
                
                st.session_state.last_receipt = {"ref": v_ref, "cli": client_nom, "tot": total_panier, "pay": m_verse, "res": m_reste, "dev": devise_p, "items": cart_data, "d": d_v, "h": h_v}
                st.session_state.cart = {}; st.rerun()
    else:
        # AFFICHAGE DU TICKET
        tr = st.session_state.last_receipt
        st.markdown(f"""
        <div style='background:white; color:black; padding:35px; border-radius:10px; font-family:monospace; box-shadow:0 0 20px #000;'>
            <h2 style='text-align:center;'>{shop_info[2] if shop_info[2] else shop_info[0]}</h2>
            <p style='text-align:center;'>{shop_info[3]}<br>Tél: {shop_info[4]}</p>
            <hr>
            <p>REF: {tr['ref']} | {tr['d']} {tr['h']}</p>
            <p>CLIENT: {tr['cli']}</p>
            <hr>
            {"".join([f"<p>{x['nom']} x{x['qte']} : {x['st']:,.0f} {tr['dev']}</p>" for x in tr['items']])}
            <hr>
            <h3>TOTAL: {tr['tot']:,.2f} {tr['dev']}</h3>
            <p>PAYÉ: {tr['pay']:,.2f} | RESTE: {tr['res']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ RETOUR À LA CAISSE"): st.session_state.last_receipt = None; st.rerun()

# --- 6.3 STOCK PAR ID (MODIF & SUPPR) ---
elif choice == "📦 STOCK PAR ID":
    st.header("📦 GESTION DU STOCK")
    t_inv, t_edit = st.tabs(["📋 INVENTAIRE", "🛠️ MODIFIER / AJOUTER"])
    
    with t_inv:
        data = execute_db("SELECT id, item_name, qty, buy_price, sell_price FROM items WHERE shop_id=?", (st.session_state.shop_active,))
        if data:
            df = pd.DataFrame(data, columns=["ID", "Désignation", "Quantité", "Prix Achat ($)", "Prix Vente ($)"])
            st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ Supprimer un article")
        target_del = st.number_input("Entrez l'ID du produit à supprimer", min_value=0)
        if st.button("CONFIRMER LA SUPPRESSION"):
            execute_db("DELETE FROM items WHERE id=? AND shop_id=?", (target_del, st.session_state.shop_active), fetch=False)
            st.success("Produit supprimé !"); st.rerun()

    with t_edit:
        with st.form("stk_form"):
            s_mode = st.radio("Opération", ["Nouveau Produit", "Modification via ID"])
            s_id = st.number_input("ID (si modification)", 0)
            s_nom = st.text_input("Désignation du produit")
            s_qte = st.number_input("Quantité", 0)
            s_pa = st.number_input("Prix d'Achat ($)")
            s_pv = st.number_input("Prix de Vente ($)")
            if st.form_submit_button("VALIDER L'ENREGISTREMENT"):
                if s_mode == "Nouveau Produit":
                    execute_db("INSERT INTO items (item_name, qty, buy_price, sell_price, shop_id) VALUES (?,?,?,?,?)",
                              (s_nom.upper(), s_qte, s_pa, s_pv, st.session_state.shop_active), fetch=False)
                else:
                    execute_db("UPDATE items SET item_name=?, qty=?, buy_price=?, sell_price=? WHERE id=? AND shop_id=?",
                              (s_nom.upper(), s_qte, s_pa, s_pv, s_id, st.session_state.shop_active), fetch=False)
                st.success("✅ Stock mis à jour !"); st.rerun()

# --- 6.4 DETTES CLIENTS (TRANCHES & AUTO-DELETE) ---
elif choice == "📉 DETTES CLIENTS":
    st.header("📉 SUIVI DES DETTES")
    créances = execute_db("SELECT id, client_name, balance, sale_ref FROM debts WHERE shop_id=? AND status='ACTIF'", (st.session_state.shop_active,))
    
    if not créances: st.success("🎉 Aucune dette en cours !")
    for d_id, d_cli, d_bal, d_ref in créances:
        with st.container():
            st.markdown(f"<div class='glass-card'><h3>{d_cli}</h3><p>Reste à payer : <b style='color:#ff4b4b;'>{d_bal:,.2f} $</b></p><p><small>Référence Facture: {d_ref}</small></p></div>", unsafe_allow_html=True)
            v_tranche = st.number_input(f"Verser une tranche ($) - {d_cli}", 0.0, float(d_bal), key=f"tr_{d_id}")
            if st.button(f"VALIDER LE PAIEMENT PARTIEL", key=f"btn_{d_id}"):
                new_balance = d_bal - v_tranche
                execute_db("INSERT INTO debt_payments (debt_id, amount, p_date) VALUES (?,?,?)", (d_id, v_tranche, datetime.now().strftime("%d/%m/%Y")), fetch=False)
                if new_balance <= 0:
                    execute_db("UPDATE debts SET balance=0, status='PAYE' WHERE id=?", (d_id,), fetch=False)
                    st.success(f"✅ Dette de {d_cli} entièrement soldée et retirée de la liste !")
                else:
                    execute_db("UPDATE debts SET balance=? WHERE id=?", (new_balance, d_id), fetch=False)
                    st.success(f"✅ Tranche de {v_tranche} $ acceptée. Nouveau solde : {new_balance} $")
                time.sleep(1); st.rerun()

# --- 6.5 DÉPENSES BOUTIQUE ---
elif choice == "💸 DÉPENSES":
    st.header("💸 GESTION DES CHARGES")
    with st.form("exp_form"):
        e_mot = st.text_input("Motif de la dépense")
        e_val = st.number_input("Montant ($)")
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            execute_db("INSERT INTO expenses (reason, amount, e_date, shop_id) VALUES (?,?,?,?)",
                      (e_mot.upper(), e_val, datetime.now().strftime("%d/%m/%Y"), st.session_state.shop_active), fetch=False)
            st.rerun()
    
    st.divider()
    logs_e = execute_db("SELECT reason, amount, e_date FROM expenses WHERE shop_id=? ORDER BY id DESC", (st.session_state.shop_active,))
    for reason, amount, date in logs_e:
        st.write(f"📅 {date} | {reason} : **{amount:,.2f} $**")

# --- 6.6 ÉQUIPE VENDEURS ---
elif choice == "👥 ÉQUIPE VENDEURS":
    st.header("👥 MES VENDEURS")
    with st.form("vendor_form"):
        v_uid = st.text_input("ID de Connexion Vendeur").lower()
        v_pwd = st.text_input("Mot de passe", type="password")
        v_nom = st.text_input("Nom du Vendeur")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            execute_db("INSERT INTO users (uid, pwd, role, owner_ref, status, full_name) VALUES (?,?,?,?,?,?)",
                      (v_uid, hashlib.sha256(v_pwd.encode()).hexdigest(), 'VENDEUR', st.session_state.shop_active, 'ACTIF', v_nom), fetch=False)
            st.success("✅ Vendeur ajouté !"); st.rerun()
    
    st.subheader("Personnel Actif")
    v_list = execute_db("SELECT uid, full_name FROM users WHERE owner_ref=? AND role='VENDEUR'", (st.session_state.shop_active,))
    for uid, name in v_list:
        st.write(f"👤 {name} (ID: {uid})")
        if st.button(f"Supprimer {uid}"):
            execute_db("DELETE FROM users WHERE uid=?", (uid,), fetch=False); st.rerun()

# --- 6.7 RÉGLAGES BOUTIQUE & MULTI-SHOP ---
elif choice == "⚙️ RÉGLAGES BOUTIQUE":
    st.header("⚙️ CONFIGURATION DES BOUTIQUES")
    
    with st.expander("➕ CRÉER UN NOUVEAU POINT DE VENTE"):
        with st.form("new_shop_f"):
            ns_id = st.text_input("ID Boutique Unique (ex: boutique_02)").lower()
            ns_nm = st.text_input("Nom de l'Enseigne")
            ns_tx = st.number_input("Taux de change (CDF/USD)", 2800.0)
            if st.form_submit_button("CRÉER LA BOUTIQUE"):
                execute_db("INSERT INTO shops (shop_id, shop_name, owner_uid, rate) VALUES (?,?,?,?)", (ns_id, ns_nm, st.session_state.uid, ns_tx), fetch=False)
                st.session_state.shop_active = ns_id; st.rerun()

    st.subheader(f"Modifier : {shop_info[0]}")
    with st.form("edit_shop_f"):
        u_nm = st.text_input("Nom", shop_info[0])
        u_tx = st.number_input("Taux de change", shop_info[1])
        u_hd = st.text_input("Slogan / En-tête", shop_info[2])
        u_ad = st.text_input("Adresse", shop_info[3])
        u_tl = st.text_input("Téléphone", shop_info[4])
        if st.form_submit_button("METTRE À JOUR"):
            execute_db("UPDATE shops SET shop_name=?, rate=?, header=?, address=?, phone=? WHERE shop_id=?", (u_nm, u_tx, u_hd, u_ad, u_tl, st.session_state.shop_active), fetch=False)
            st.rerun()

    st.divider()
    st.subheader("🔴 RÉINITIALISATION")
    if st.button("❗ EFFACER TOUTES LES DONNÉES DE CETTE BOUTIQUE"):
        for table in ["items", "sales", "debts", "expenses"]:
            execute_db(f"DELETE FROM {table} WHERE shop_id=?", (st.session_state.shop_active,), fetch=False)
        st.error("Données de la boutique effacées !"); st.rerun()

# --- 6.8 RAPPORTS VENTES ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 HISTORIQUE DES VENTES")
    r_date = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    logs = execute_db("SELECT time_v, ref, client, total_usd, seller FROM sales WHERE shop_id=? AND date_v=? ORDER BY id DESC", (st.session_state.shop_active, r_date))
    
    if logs:
        for t, r, c, tot, s in logs:
            st.markdown(f"<div class='glass-card'>{t} | REF: {r} | <b>{tot:,.2f} $</b> | Client: {c} | Vendeur: {s}</div>", unsafe_allow_html=True)
    else: st.info("Aucune vente enregistrée pour cette date.")

elif choice == "🚪 DÉCONNEXION":
    st.session_state.logged_in = False; st.rerun()
