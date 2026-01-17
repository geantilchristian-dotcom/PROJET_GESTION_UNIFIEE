# ==============================================================================
# ANASH ERP (BY BALIKA BUSINESS) - VERSION MASTER v2300
# DESIGN : GLASSMORPHISM COBALT BLUE (STYLE SMARTPHONE)
# ARCHITECTURE : MULTI-BOUTIQUE / MULTI-VENDEUR / TAUX INDIVIDUEL
# SÉCURITÉ : INSCRIPTION LIBRE / VALIDATION PAR ADMIN
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import base64
import random
import os

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE & DESIGN CSS (PIXEL PERFECT)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v2300", layout="wide", initial_sidebar_state="expanded")

def apply_ultra_design():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Poppins:wght@300;400;600&display=swap');

    /* Fond Global Cobalt Blue */
    .stApp {
        background: radial-gradient(circle at top right, #0044ff, #001133) !important;
        background-attachment: fixed !important;
        color: white !important;
        font-family: 'Poppins', sans-serif;
    }

    /* Message Défilant Admin */
    .marquee-wrapper {
        position: fixed; top: 0; left: 0; width: 100%; background: rgba(0,0,0,0.9);
        color: #00ff00; z-index: 9999; height: 35px; line-height: 35px;
        font-weight: bold; border-bottom: 2px solid #fff; font-size: 14px;
    }

    /* Horloge Géante 80mm Stylée */
    .hero-clock-box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 30px; padding: 50px; text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 40px 0; box-shadow: 0 15px 60px rgba(0,0,0,0.6);
    }
    .clock-text {
        font-family: 'Orbitron', sans-serif; font-size: 85px; font-weight: 900;
        color: #ffffff; text-shadow: 0 0 20px #00ccff, 0 0 40px #00ccff;
    }
    .date-text {
        font-size: 24px; color: #00ccff; text-transform: uppercase;
        letter-spacing: 5px; margin-top: 15px; font-weight: 300;
    }

    /* Cartes Glassmorphism */
    .glass-container {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 25px; padding: 25px; margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.4);
    }

    /* Boutons Tactiles Mobiles XXL */
    .stButton>button {
        width: 100% !important; height: 70px !important; border-radius: 18px !important;
        background: linear-gradient(135deg, #0088ff, #0044bb) !important;
        color: white !important; font-size: 18px !important; font-weight: bold !important;
        border: 2px solid rgba(255,255,255,0.2) !important; transition: 0.4s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 20px #0088ff; }

    /* Panier & Totaux Encadrés */
    .price-frame {
        background: #000; color: #00ff00; padding: 25px; border-radius: 20px;
        border: 3px solid #00ff00; text-align: center; font-size: 35px;
        font-weight: 900; margin: 30px 0; box-shadow: 0 0 25px rgba(0,255,0,0.4);
    }

    /* Inputs Visibilité Maximale */
    input, select, textarea {
        background-color: #ffffff !important; color: #000000 !important;
        border-radius: 12px !important; height: 50px !important; font-size: 16px !important;
    }

    /* Sidebar Personnalisée */
    [data-testid="stSidebar"] { background: #fdfdfd !important; border-right: 1px solid #ccc; }
    [data-testid="stSidebar"] * { color: #222 !important; font-weight: 600; }
    .sidebar-header { padding: 20px; border-bottom: 2px solid #eee; margin-bottom: 20px; text-align:center; }
    .online-dot { color: #28a745; font-size: 14px; }
    
    /* Tables adaptatives */
    .mobile-row {
        background: white; color: black; padding: 15px; border-radius: 12px;
        margin-bottom: 12px; border-left: 10px solid #0044ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE DONNÉES SQLITE (CORE ENGINE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v2300_ultimate.db"

def db_exec(sql, params=(), fetch=False):
    with sqlite3.connect(DB_FILE, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def boot_database():
    # Utilisateurs (Confirmation Admin requise via status 'EN_ATTENTE')
    db_exec("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, owner_id TEXT, 
        status TEXT DEFAULT 'EN_ATTENTE', full_name TEXT, tel TEXT)""")
    
    # Boutiques (Chaque gérant est indépendant)
    db_exec("""CREATE TABLE IF NOT EXISTS shops (
        shop_id TEXT PRIMARY KEY, shop_name TEXT, owner_uid TEXT, 
        rate REAL DEFAULT 2800.0, header_text TEXT, address TEXT, phone TEXT)""")
    
    # Stock (Identifiant unique, prix achat caché aux vendeurs)
    db_exec("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, 
        quantity INTEGER, buy_price REAL, sell_price REAL, shop_id TEXT)""")
    
    # Ventes (Log complet)
    db_exec("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total_usd REAL, paid_usd REAL, debt_usd REAL, currency TEXT, 
        v_date TEXT, v_time TEXT, seller TEXT, shop_id TEXT, items_data TEXT)""")
    
    # Dettes (Suivi par tranches)
    db_exec("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, 
        balance REAL, sale_ref TEXT, shop_id TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Dépenses
    db_exec("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motive TEXT, amount REAL, 
        e_date TEXT, shop_id TEXT)""")
    
    # Paramètres Système
    db_exec("CREATE TABLE IF NOT EXISTS sys_settings (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT)")

    # Création Super Admin
    if not db_exec("SELECT * FROM users WHERE uid='admin'", fetch=True):
        db_exec("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
               ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'SUPER ADMINISTRATEUR', '000'))
    
    if not db_exec("SELECT * FROM sys_settings", fetch=True):
        db_exec("INSERT INTO sys_settings VALUES (1, 'ANASH ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION MULTI-BOUTIQUE v2300')")

boot_database()
sys_cfg = db_exec("SELECT app_name, marquee_text FROM sys_settings WHERE id=1", fetch=True)[0]

# ------------------------------------------------------------------------------
# 3. GESTION DES SESSIONS
# ------------------------------------------------------------------------------
if 'user_data' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'uid': "", 'role': "", 'owner': "",
        'active_shop': None, 'cart': {}, 'last_invoice': None
    })

apply_ultra_design()
st.markdown(f'<div class="marquee-wrapper"><marquee scrollamount="8">{sys_cfg[1]}</marquee></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION ET INSCRIPTION LIBRE
# ------------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    
    with c2:
        st.markdown(f"<div class='hero-clock-box'><h1>{sys_cfg[0]}</h1><p>Gérez vos boutiques avec excellence</p></div>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔑 CONNEXION", "📝 INSCRIPTION LIBRE"])
        
        with tab_log:
            u_in = st.text_input("Identifiant").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER À L'INTERFACE"):
                res = db_exec("SELECT pwd, role, owner_id, status FROM users WHERE uid=?", (u_in,), fetch=True)
                if res and hashlib.sha256(p_in.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "EN_ATTENTE":
                        st.warning("⏳ Votre compte est en attente de confirmation par l'Administrateur.")
                    elif res[0][3] == "BLOQUE":
                        st.error("🚫 Ce compte a été suspendu.")
                    else:
                        st.session_state.update({'logged_in':True, 'uid':u_in, 'role':res[0][1], 'owner':res[0][2]})
                        # Charger boutique par défaut si Gérant
                        if res[0][1] == "GERANT":
                            b_list = db_exec("SELECT shop_id FROM shops WHERE owner_uid=?", (u_in,), fetch=True)
                            if b_list: st.session_state.active_shop = b_list[0][0]
                        elif res[0][1] == "VENDEUR":
                            st.session_state.active_shop = res[0][2]
                        st.rerun()
                else: st.error("❌ Identifiants incorrects.")

        with tab_reg:
            st.info("L'inscription est libre. Un administrateur devra valider votre accès.")
            with st.form("reg_form"):
                reg_uid = st.text_input("Choisir un Identifiant").lower()
                reg_name = st.text_input("Nom Complet")
                reg_tel = st.text_input("Numéro de Téléphone")
                reg_pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON COMPTE GÉRANT"):
                    if db_exec("SELECT uid FROM users WHERE uid=?", (reg_uid,), fetch=True):
                        st.error("❌ Cet identifiant existe déjà.")
                    else:
                        db_exec("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                               (reg_uid, hashlib.sha256(reg_pwd.encode()).hexdigest(), 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', reg_name, reg_tel))
                        st.success("✅ Inscription réussie ! Attendez la validation de l'Admin.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. DASHBOARD SUPER ADMIN (CONFIRMATION & SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.markdown("<div class='sidebar-header'>🛠️ SUPER ADMIN</div>", unsafe_allow_html=True)
    adm_menu = st.sidebar.radio("Navigation", ["Validation Comptes", "Paramètres Globaux", "Déconnexion"])
    
    if adm_menu == "Validation Comptes":
        st.header("👥 COMPTES EN ATTENTE & GESTION")
        users = db_exec("SELECT uid, full_name, tel, status FROM users WHERE role='GERANT'", fetch=True)
        for u, n, t, s in users:
            with st.container():
                st.markdown(f"""
                <div class='glass-container'>
                    <h3>{n} (@{u})</h3>
                    <p>Tel: {t} | Statut actuel: <b>{s}</b></p>
                </div>
                """, unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3)
                if col_a.button("✅ CONFIRMER / ACTIVER", key=f"ok_{u}"): 
                    db_exec("UPDATE users SET status='ACTIF', owner_id=? WHERE uid=?", (u, u))
                    st.rerun()
                if col_b.button("⏸️ BLOQUER", key=f"no_{u}"):
                    db_exec("UPDATE users SET status='BLOQUE' WHERE uid=?", (u,))
                    st.rerun()
                if col_c.button("🗑️ SUPPRIMER", key=f"del_{u}"):
                    db_exec("DELETE FROM users WHERE uid=?", (u,))
                    st.rerun()

    elif adm_menu == "Paramètres Globaux":
        st.header("⚙️ CONFIGURATION SYSTÈME")
        with st.form("sys_form"):
            new_title = st.text_input("Nom de l'Application", sys_cfg[0])
            new_marquee = st.text_area("Message Défilant", sys_cfg[1])
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                db_exec("UPDATE sys_settings SET app_name=?, marquee_text=? WHERE id=1", (new_title, new_marquee))
                st.rerun()

    if adm_menu == "Déconnexion": st.session_state.logged_in = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. INTERFACE GÉRANT & VENDEUR (CORE APP)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div class='sidebar-header'>🏪 <b>{st.session_state.active_shop if st.session_state.active_shop else 'ANASH'}</b><br><span class='online-dot'>●</span> {st.session_state.uid.upper()}</div>", unsafe_allow_html=True)
    
    # Sélecteur de Boutique pour Gérant
    if st.session_state.role == "GERANT":
        boutiques = db_exec("SELECT shop_id, shop_name FROM shops WHERE owner_uid=?", (st.session_state.uid,), fetch=True)
        if boutiques:
            shop_map = {b[1]: b[0] for b in boutiques}
            choice_shop = st.selectbox("Ma Boutique Active", list(shop_map.keys()))
            st.session_state.active_shop = shop_map[choice_shop]
        
        main_menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 STOCK PAR ID", "📉 DETTES CLIENTS", "💸 DÉPENSES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE VENDEURS", "⚙️ RÉGLAGES", "🚪 QUITTER"]
    else:
        # Vendeur : Uniquement Vente et Dettes
        main_menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 DETTES CLIENTS", "📊 RAPPORTS VENTES", "🚪 QUITTER"]
    
    choice = st.radio("MENU", main_menu)

# Chargement des infos de la boutique
shop_info = db_exec("SELECT shop_name, rate, header_text, address, phone FROM shops WHERE shop_id=?", (st.session_state.active_shop,), fetch=True)
if not shop_info:
    if st.session_state.role == "GERANT":
        st.warning("⚠️ Aucune boutique créée. Allez dans RÉGLAGES.")
        choice = "⚙️ RÉGLAGES"
    else: st.error("Accès boutique non configuré."); st.stop()
else: shop_info = shop_info[0]

# --- 6.1 ACCUEIL (HORLOGE 80MM & BÉNÉFICE) ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='hero-clock-box'>
        <div class='clock-text'>{datetime.now().strftime('%H:%M')}</div>
        <div class='date-text'>{datetime.now().strftime('%A, %d %B %Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard Financier
    today = datetime.now().strftime("%d/%m/%Y")
    recettes = db_exec("SELECT SUM(total_usd) FROM sales WHERE shop_id=? AND v_date=?", (st.session_state.active_shop, today), fetch=True)[0][0] or 0
    frais = db_exec("SELECT SUM(amount) FROM expenses WHERE shop_id=? AND e_date=?", (st.session_state.active_shop, today), fetch=True)[0][0] or 0
    benef_net = recettes - frais
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='glass-container'><p>CHIFFRE D'AFFAIRES (JOUR)</p><h2>{recettes:,.2f} $</h2></div>", unsafe_allow_html=True)
    with c2:
        color_net = "#00ff00" if benef_net >= 0 else "#ff4b4b"
        st.markdown(f"<div class='glass-container' style='border-color:{color_net}'><p>BÉNÉFICE NET</p><h2 style='color:{color_net}'>{benef_net:,.2f} $</h2></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (MULTI-DEVISE) ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.last_invoice:
        st.header("🛒 TERMINAL DE VENTE")
        devise = st.radio("Devise", ["USD", "CDF"], horizontal=True)
        taux_btq = shop_info[1]
        
        prods = db_exec("SELECT item_name, sell_price, quantity FROM inventory WHERE shop_id=?", (st.session_state.active_shop,), fetch=True)
        p_map = {p[0]: (p[1], p[2]) for p in prods}
        
        search = st.selectbox("🔍 Sélectionner un article...", ["---"] + list(p_map.keys()))
        if search != "---":
            if p_map[search][1] > 0:
                st.session_state.cart[search] = st.session_state.cart.get(search, 0) + 1
                st.toast(f"✅ {search} ajouté")
            else: st.error("❌ Stock épuisé !")

        if st.session_state.cart:
            st.divider()
            total_panier = 0.0; items_list = []
            for art, qte in list(st.session_state.cart.items()):
                p_usd = p_map[art][0]
                p_final = p_usd if devise == "USD" else p_usd * taux_btq
                stot = p_final * qte
                total_panier += stot
                items_list.append({"nom": art, "qte": qte, "pu": p_final, "st": stot})
                
                with st.container():
                    st.markdown(f"<div class='glass-container' style='padding:15px; margin-bottom:5px;'><b>{art}</b> | {qte} x {p_final:,.0f} = {stot:,.0f} {devise}</div>", unsafe_allow_html=True)
                    if st.button(f"🗑️ Retirer {art}"): del st.session_state.cart[art]; st.rerun()

            st.markdown(f"<div class='price-frame'>TOTAL : {total_panier:,.2f} {devise}</div>", unsafe_allow_html=True)
            
            client_n = st.text_input("Nom du Client", "COMPTANT")
            vers_n = st.number_input(f"Montant Versé ({devise})", value=float(total_panier))
            reste_n = total_panier - vers_n
            
            if st.button("🏁 CONFIRMER LA VENTE"):
                ref_v = f"AN-{random.randint(1000,9999)}"
                d_v, h_v = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                
                # Conversion USD pour Archivage
                t_usd = total_panier if devise == "USD" else total_panier / taux_btq
                v_usd = vers_n if devise == "USD" else vers_n / taux_btq
                r_usd = reste_n if devise == "USD" else reste_n / taux_btq
                
                db_exec("""INSERT INTO sales (ref, client, total_usd, paid_usd, debt_usd, currency, v_date, v_time, seller, shop_id, items_data) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (ref_v, client_n.upper(), t_usd, v_usd, r_usd, devise, d_v, h_v, st.session_state.uid, st.session_state.active_shop, json.dumps(items_list)))
                
                for itm in items_list:
                    db_exec("UPDATE inventory SET quantity = quantity - ? WHERE item_name=? AND shop_id=?", (itm['qte'], itm['nom'], st.session_state.active_shop))
                
                if r_usd > 0:
                    db_exec("INSERT INTO debts (client_name, balance, sale_ref, shop_id) VALUES (?,?,?,?)", (client_n.upper(), r_usd, ref_v, st.session_state.active_shop))
                
                st.session_state.last_invoice = {"ref": ref_v, "cli": client_n, "tot": total_panier, "pay": vers_n, "res": reste_n, "dev": devise, "items": items_list, "d": d_v, "h": h_v}
                st.session_state.cart = {}; st.rerun()
    else:
        # AFFICHAGE DE LA FACTURE POUR IMPRESSION
        f = st.session_state.last_invoice
        st.markdown(f"""
        <div style='background:white; color:black; padding:30px; border-radius:10px; font-family:monospace; box-shadow:0 0 20px #000;'>
            <h2 style='text-align:center;'>{shop_info[2] if shop_info[2] else shop_info[0]}</h2>
            <p style='text-align:center;'>{shop_info[3]}<br>Tél: {shop_info[4]}</p>
            <hr>
            <p><b>REF: {f['ref']}</b> | Date: {f['d']} {f['h']}</p>
            <p>Client: {f['cli'].upper()}</p>
            <hr>
            {"".join([f"<p>{x['nom']} x{x['qte']} : {x['st']:,.0f} {f['dev']}</p>" for x in f['items']])}
            <hr>
            <h3>TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            <p>PAYÉ: {f['pay']:,.2f} | RESTE: {f['res']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ RETOUR À LA CAISSE"): st.session_state.last_invoice = None; st.rerun()

# --- 6.3 STOCK PAR ID (MODIFICATION SANS SUPPRESSION) ---
elif choice == "📦 STOCK PAR ID":
    st.header("📦 GESTION DES PRODUITS")
    t_inv, t_mod = st.tabs(["📋 INVENTAIRE", "🛠️ AJOUT / MODIFICATION PAR ID"])
    
    with t_inv:
        articles = db_exec("SELECT id, item_name, quantity, sell_price FROM inventory WHERE shop_id=?", (st.session_state.active_shop,), fetch=True)
        for i_id, i_nm, i_q, i_sp in articles:
            with st.container():
                st.markdown(f"<div class='glass-container'><h4>ID: {i_id} | {i_nm}</h4><p>Stock : <b>{i_q}</b> | Prix Vente : <b>{i_sp:,.2f} $</b></p></div>", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🗑️ Supprimer un article")
        del_target = st.number_input("Entrez l'ID du produit à retirer", min_value=0)
        if st.button("CONFIRMER SUPPRESSION DÉFINITIVE"):
            db_exec("DELETE FROM inventory WHERE id=? AND shop_id=?", (del_target, st.session_state.active_shop))
            st.success("Produit supprimé."); st.rerun()

    with t_mod:
        with st.form("stock_form"):
            s_mode = st.radio("Type d'opération", ["Nouveau Produit", "Mise à jour via ID"])
            s_id = st.number_input("ID (uniquement pour Mise à jour)", 0)
            s_nom = st.text_input("Désignation du produit")
            s_qte = st.number_input("Quantité", 0)
            s_pa = st.number_input("Prix d'Achat ($)")
            s_pv = st.number_input("Prix de Vente ($)")
            if st.form_submit_button("VALIDER L'ENREGISTREMENT"):
                if s_mode == "Nouveau Produit":
                    db_exec("INSERT INTO inventory (item_name, quantity, buy_price, sell_price, shop_id) VALUES (?,?,?,?,?)",
                           (s_nom.upper(), s_qte, s_pa, s_pv, st.session_state.active_shop))
                else:
                    db_exec("UPDATE inventory SET item_name=?, quantity=?, buy_price=?, sell_price=? WHERE id=? AND shop_id=?",
                           (s_nom.upper(), s_qte, s_pa, s_pv, s_id, st.session_state.active_shop))
                st.success("✅ Stock mis à jour !"); st.rerun()

# --- 6.4 DETTES CLIENTS (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 DETTES CLIENTS":
    st.header("📉 SUIVI DES CRÉANCES")
    dettes_list = db_exec("SELECT id, client_name, balance, sale_ref FROM debts WHERE shop_id=? AND status='ACTIF'", (st.session_state.active_shop,), fetch=True)
    
    if not dettes_list: st.success("🎉 Aucune dette en cours !")
    for d_id, d_cli, d_bal, d_ref in dettes_list:
        with st.container():
            st.markdown(f"<div class='glass-container'><h3>Client: {d_cli}</h3><p>Solde restant : <b style='color:#ff4b4b;'>{d_bal:,.2f} $</b></p><p>Facture : {d_ref}</p></div>", unsafe_allow_html=True)
            v_pay = st.number_input(f"Montant versé par {d_cli} ($)", 0.0, float(d_bal), key=f"pay_{d_id}")
            if st.button("VALIDER LE PAIEMENT PARTIEL", key=f"btn_{d_id}"):
                new_bal = d_bal - v_pay
                if new_bal <= 0: db_exec("UPDATE debts SET balance=0, status='PAYE' WHERE id=?", (d_id,))
                else: db_exec("UPDATE debts SET balance=? WHERE id=?", (new_bal, d_id))
                st.success("✅ Tranche de paiement enregistrée !"); st.rerun()

# --- 6.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 GESTION DES CHARGES")
    with st.form("exp_f"):
        m_exp = st.text_input("Motif de la dépense")
        a_exp = st.number_input("Montant ($)")
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            db_exec("INSERT INTO expenses (motive, amount, e_date, shop_id) VALUES (?,?,?,?)", 
                   (m_exp.upper(), a_exp, datetime.now().strftime("%d/%m/%Y"), st.session_state.active_shop))
            st.rerun()

# --- 6.6 ÉQUIPE VENDEURS ---
elif choice == "👥 ÉQUIPE VENDEURS":
    st.header("👥 MES EMPLOYÉS")
    with st.form("vend_form"):
        v_uid = st.text_input("Identifiant de Connexion").lower()
        v_pwd = st.text_input("Mot de passe", type="password")
        v_name = st.text_input("Nom du Vendeur")
        if st.form_submit_button("CRÉER LE COMPTE"):
            db_exec("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                   (v_uid, hashlib.sha256(v_pwd.encode()).hexdigest(), 'VENDEUR', st.session_state.active_shop, 'ACTIF', v_name, ""))
            st.success("✅ Vendeur ajouté !"); st.rerun()
    
    st.subheader("Vendeurs actifs")
    staff = db_exec("SELECT uid, full_name FROM users WHERE owner_id=? AND role='VENDEUR'", (st.session_state.active_shop,), fetch=True)
    for sid, snm in staff:
        st.write(f"👤 {snm} (ID: {sid})")
        if st.button(f"Supprimer {sid}"): db_exec("DELETE FROM users WHERE uid=?", (sid,)); st.rerun()

# --- 6.7 RÉGLAGES & RESET TOTAL ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    
    # Ajouter une boutique
    with st.expander("➕ CRÉER UNE NOUVELLE BOUTIQUE / DÉPÔT"):
        with st.form("new_shop"):
            ns_id = st.text_input("ID Unique (ex: boutique_nord)").lower()
            ns_nm = st.text_input("Nom de l'Enseigne")
            ns_rt = st.number_input("Taux de change (USD vers CDF)", 2800.0)
            if st.form_submit_button("CRÉER LA BOUTIQUE"):
                db_exec("INSERT INTO shops (shop_id, shop_name, owner_uid, rate) VALUES (?,?,?,?)", (ns_id, ns_nm, st.session_state.uid, ns_rt))
                st.session_state.active_shop = ns_id; st.rerun()

    # Paramètres Boutique
    st.subheader(f"Réglages : {shop_info[0]}")
    with st.form("shop_edit"):
        e_nm = st.text_input("Nom", shop_info[0])
        e_rt = st.number_input("Taux de change", shop_info[1])
        e_hd = st.text_input("En-tête Facture", shop_info[2])
        e_ad = st.text_input("Adresse", shop_info[3])
        e_tl = st.text_input("Téléphone", shop_info[4])
        if st.form_submit_button("METTRE À JOUR"):
            db_exec("UPDATE shops SET shop_name=?, rate=?, header_text=?, address=?, phone=? WHERE shop_id=?", (e_nm, e_rt, e_hd, e_ad, e_tl, st.session_state.active_shop))
            st.rerun()

    st.divider()
    st.subheader("🔴 ZONE DANGER")
    if st.button("❗ RÉINITIALISER CETTE BOUTIQUE (EFFACER TOUT)"):
        for tbl in ["inventory", "sales", "debts", "expenses"]:
            db_exec(f"DELETE FROM {tbl} WHERE shop_id=?", (st.session_state.active_shop,))
        st.error("💥 Données de la boutique effacées."); st.rerun()

# --- 6.8 RAPPORTS VENTES ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 HISTORIQUE D'ACTIVITÉ")
    day_sel = st.date_input("Date").strftime("%d/%m/%Y")
    logs = db_exec("SELECT v_time, ref, client, total_usd, seller FROM sales WHERE shop_id=? AND v_date=? ORDER BY id DESC", (st.session_state.active_shop, day_sel), fetch=True)
    if logs:
        for t, r, c, tot, s in logs:
            st.markdown(f"<div class='glass-container'>{t} | {r} | <b>{tot:,.2f} $</b> | {c} (Vendeur: {s})</div>", unsafe_allow_html=True)
    else: st.info("Aucune vente enregistrée pour cette date.")

elif choice == "🚪 QUITTER":
    st.session_state.logged_in = False; st.rerun()
