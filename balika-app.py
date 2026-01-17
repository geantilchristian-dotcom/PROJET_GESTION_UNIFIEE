# ==============================================================================
# ANASH ERP - SYSTÈME DE GESTION PROFESSIONNEL v2500
# DESIGN : GLASSMORPHISM COBALT BLUE (STYLE SMARTPHONE)
# DÉVELOPPÉ POUR : BALIKA BUSINESS
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
import io

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE ET STYLE CSS AVANCÉ
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v2500", layout="wide", initial_sidebar_state="expanded")

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@300;400;700&display=swap');

    /* Fond principal Cobalt Blue de vos photos */
    .stApp {
        background: radial-gradient(circle at center, #0044cc 0%, #001133 100%) !important;
        background-attachment: fixed !important;
        color: white !important;
        font-family: 'Inter', sans-serif;
    }

    /* Marquee Admin Stylé */
    .admin-marquee {
        position: fixed; top: 0; left: 0; width: 100%; background: #000;
        color: #00ff00; z-index: 9999; height: 35px; line-height: 35px;
        font-weight: bold; border-bottom: 1px solid #ffffff; font-size: 14px;
        text-transform: uppercase; letter-spacing: 2px;
    }

    /* Horloge 80mm Géante */
    .clock-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 40px; padding: 60px; text-align: center;
        margin: 40px auto; max-width: 800px;
        box-shadow: 0 20px 80px rgba(0,0,0,0.7);
    }
    .main-time {
        font-family: 'Orbitron', sans-serif; font-size: 110px; font-weight: 900;
        color: #fff; text-shadow: 0 0 20px #00ccff, 0 0 50px #00ccff;
        line-height: 1; margin: 0;
    }
    .main-date {
        font-family: 'Inter', sans-serif; font-size: 28px; color: #00ccff;
        text-transform: uppercase; letter-spacing: 8px; margin-top: 20px;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 25px; padding: 25px; margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }

    /* Boutons XXL Tactiles */
    .stButton>button {
        width: 100% !important; height: 75px !important; border-radius: 20px !important;
        background: linear-gradient(135deg, #007bff, #0033aa) !important;
        color: white !important; font-size: 20px !important; font-weight: bold !important;
        border: 2px solid rgba(255,255,255,0.2) !important; transition: 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .stButton>button:active { transform: scale(0.92); }

    /* Panier & Cadre Total */
    .total-box {
        background: #000; color: #00ff00; padding: 30px; border-radius: 25px;
        border: 4px solid #00ff00; text-align: center; font-size: 40px;
        font-weight: 900; margin: 30px 0; box-shadow: 0 0 30px rgba(0,255,0,0.3);
        font-family: 'Orbitron', sans-serif;
    }

    /* Sidebar Glass */
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #ddd; }
    [data-testid="stSidebar"] * { color: #111 !important; font-weight: 600; }
    .sb-header { background: #0044cc; color: white !important; padding: 20px; text-align: center; border-radius: 0 0 20px 20px; margin-bottom: 20px; }

    /* Inputs Blanches pour visibilité */
    input, select, textarea {
        background-color: white !important; color: black !important;
        border-radius: 12px !important; height: 55px !important; border: 1px solid #ccc !important;
    }

    /* Print View */
    @media print {
        .no-print { display: none !important; }
        .print-only { display: block !important; color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. LOGIQUE BASE DE DONNÉES SQLITE (ROBUSTESSE TOTALE)
# ------------------------------------------------------------------------------
DB_ANASH = "anash_master_v2500.db"

def db_query(sql, params=(), fetch=True):
    with sqlite3.connect(DB_ANASH, timeout=60) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def init_db_structure():
    # Utilisateurs (Status: EN_ATTENTE, ACTIF, BLOQUE)
    db_query("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        owner_ref TEXT, status TEXT DEFAULT 'EN_ATTENTE', full_name TEXT, phone TEXT)""", fetch=False)
    
    # Boutiques (Chaque gérant a ses propres boutiques)
    db_query("""CREATE TABLE IF NOT EXISTS stores (
        id TEXT PRIMARY KEY, name TEXT, owner TEXT, 
        rate REAL DEFAULT 2850.0, header TEXT, address TEXT, phone TEXT)""", fetch=False)
    
    # Stock (ID, Nom, Quantité, Achat, Vente, Boutique)
    db_query("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, 
        qty INTEGER, buy_price REAL, sell_price REAL, store_id TEXT)""", fetch=False)
    
    # Ventes (Log Complet)
    db_query("""CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total_usd REAL, paid_usd REAL, debt_usd REAL, currency TEXT, 
        v_date TEXT, v_time TEXT, seller TEXT, store_id TEXT, items_blob TEXT)""", fetch=False)
    
    # Dettes (Suivi par tranches de paiement)
    db_query("""CREATE TABLE IF NOT EXISTS debts_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, 
        balance REAL, sale_ref TEXT, store_id TEXT, status TEXT DEFAULT 'OUVERT')""", fetch=False)
    
    # Paiements de dettes (Historique des tranches)
    db_query("""CREATE TABLE IF NOT EXISTS debt_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, debt_id INTEGER, 
        amount REAL, p_date TEXT, p_time TEXT)""", fetch=False)
    
    # Dépenses (Charges)
    db_query("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, reason TEXT, amount REAL, 
        e_date TEXT, store_id TEXT)""", fetch=False)
    
    # Paramètres Global (Marquee, etc)
    db_query("CREATE TABLE IF NOT EXISTS app_config (id INTEGER PRIMARY KEY, title TEXT, marquee TEXT)", fetch=False)

    # Initialisation Admin Par Défaut
    if not db_query("SELECT * FROM users WHERE username='admin'"):
        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR MAÎTRE', '000'), fetch=False)
    
    if not db_query("SELECT * FROM app_config"):
        db_query("INSERT INTO app_config VALUES (1, 'ANASH ERP', 'BIENVENUE SUR ANASH ERP v2500 - VOTRE PARTENAIRE DE GESTION')", fetch=False)

init_db_structure()
global_settings = db_query("SELECT title, marquee FROM app_config WHERE id=1")[0]

# ------------------------------------------------------------------------------
# 3. GESTION DES SESSIONS ET ÉTATS
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': None, 'role': None, 'owner': None,
        'active_st': None, 'cart': {}, 'invoice': None, 'v_id': None
    })

inject_custom_css()
st.markdown(f'<div class="admin-marquee"><marquee scrollamount="10">{global_settings[1]}</marquee></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. SYSTÈME DE CONNEXION ET INSCRIPTION LIBRE
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    cl1, cl2, cl3 = st.columns([1, 2, 1])
    with cl2:
        st.markdown(f"<div class='clock-container'><h1>{global_settings[0]}</h1><p>Veuillez vous authentifier</p></div>", unsafe_allow_html=True)
        
        login_tab, signup_tab = st.tabs(["🔑 SE CONNECTER", "📝 CRÉER UN COMPTE"])
        
        with login_tab:
            u_name = st.text_input("Identifiant").lower().strip()
            u_pass = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU TABLEAU DE BORD"):
                res = db_query("SELECT password, role, owner_ref, status FROM users WHERE username=?", (u_name,))
                if res and hashlib.sha256(u_pass.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "EN_ATTENTE":
                        st.warning("⚠️ Compte en attente de validation par l'Administrateur.")
                    elif res[0][3] == "BLOQUE":
                        st.error("🚫 Accès refusé. Compte bloqué.")
                    else:
                        st.session_state.update({'auth':True, 'user':u_name, 'role':res[0][1], 'owner':res[0][2]})
                        # Chargement Boutique
                        if res[0][1] == "GERANT":
                            st_list = db_query("SELECT id FROM stores WHERE owner=?", (u_name,))
                            if st_list: st.session_state.active_st = st_list[0][0]
                        elif res[0][1] == "VENDEUR":
                            st.session_state.active_st = res[0][2]
                        st.success("Connexion réussie !"); time.sleep(1); st.rerun()
                else: st.error("❌ Identifiant ou mot de passe incorrect.")

        with signup_tab:
            st.info("L'inscription est libre. L'administrateur confirmera votre accès.")
            with st.form("signup_form"):
                reg_u = st.text_input("Identifiant souhaité").lower()
                reg_n = st.text_input("Nom Complet")
                reg_t = st.text_input("Téléphone")
                reg_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("VALIDER L'INSCRIPTION"):
                    if db_query("SELECT username FROM users WHERE username=?", (reg_u,)):
                        st.error("❌ Identifiant déjà pris.")
                    else:
                        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                                (reg_u, hashlib.sha256(reg_p.encode()).hexdigest(), 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', reg_n, reg_t), fetch=False)
                        st.success("✅ Inscription enregistrée ! Contactez l'admin pour l'activation.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN (MODÉRATION ET CONFIG)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.markdown("<div class='sb-header'>💎 SUPER ADMIN</div>", unsafe_allow_html=True)
    a_menu = st.sidebar.radio("Menu Admin", ["Comptes à Valider", "Toutes les Boutiques", "Message Défilant", "Déconnexion"])
    
    if a_menu == "Comptes à Valider":
        st.header("👥 VALIDATION DES NOUVEAUX GÉRANTS")
        pending = db_query("SELECT username, full_name, phone, status FROM users WHERE role='GERANT'")
        for u, n, t, s in pending:
            with st.container():
                st.markdown(f"<div class='glass-card'><h3>{n} (@{u})</h3><p>Tel: {t} | Statut: <b>{s}</b></p></div>", unsafe_allow_html=True)
                ca, cb, cc = st.columns(3)
                if ca.button("✅ ACTIVER", key=f"ac_{u}"):
                    db_query("UPDATE users SET status='ACTIF', owner_ref=? WHERE username=?", (u, u), fetch=False)
                    st.rerun()
                if cb.button("⏸️ BLOQUER", key=f"bl_{u}"):
                    db_query("UPDATE users SET status='BLOQUE' WHERE username=?", (u,), fetch=False)
                    st.rerun()
                if cc.button("🗑️ SUPPRIMER", key=f"dl_{u}"):
                    db_query("DELETE FROM users WHERE username=?", (u,), fetch=False)
                    st.rerun()

    elif a_menu == "Message Défilant":
        st.header("📢 MESSAGE GLOBAL")
        n_marq = st.text_area("Texte du Marquee", global_settings[1])
        if st.button("METTRE À JOUR"):
            db_query("UPDATE app_config SET marquee=? WHERE id=1", (n_marq,), fetch=False)
            st.rerun()

    if a_menu == "Déconnexion": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR (CORE LOGIC)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div class='sb-header'>👤 {st.session_state.user.upper()}<br><small>{st.session_state.role}</small></div>", unsafe_allow_html=True)
    
    # Sélecteur Multi-Boutique pour Gérant
    if st.session_state.role == "GERANT":
        my_shops = db_query("SELECT id, name FROM stores WHERE owner=?", (st.session_state.user,))
        if my_shops:
            s_map = {s[1]: s[0] for s in my_shops}
            s_choice = st.selectbox("Ma Boutique Active", list(s_map.keys()))
            st.session_state.active_st = s_map[s_choice]
        
        menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 STOCK PAR ID", "📉 DETTES & TRANCHES", "💸 DÉPENSES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE VENDEURS", "⚙️ RÉGLAGES BOUTIQUE", "🚪 QUITTER"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 DETTES & TRANCHES", "📊 RAPPORTS VENTES", "🚪 QUITTER"]
    
    choice = st.radio("NAVIGATION", menu)

# Infos de la boutique active
current_shop = db_query("SELECT name, rate, header, address, phone FROM stores WHERE id=?", (st.session_state.active_st,))
if not current_shop:
    if st.session_state.role == "GERANT":
        st.warning("⚠️ Aucune boutique configurée. Veuillez en créer une dans RÉGLAGES.")
        choice = "⚙️ RÉGLAGES BOUTIQUE"
    else: st.error("Accès boutique restreint."); st.stop()
else: current_shop = current_shop[0]

# --- 6.1 ACCUEIL (HORLOGE ET STATS) ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='clock-container'>
        <div class='main-time'>{datetime.now().strftime('%H:%M')}</div>
        <div class='main-date'>{datetime.now().strftime('%A, %d %B %Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calcul des performances du jour
    t_date = datetime.now().strftime("%d/%m/%Y")
    ventes_j = db_query("SELECT SUM(total_usd) FROM sales_history WHERE store_id=? AND v_date=?", (st.session_state.active_st, t_date))[0][0] or 0
    frais_j = db_query("SELECT SUM(amount) FROM expenses WHERE store_id=? AND e_date=?", (st.session_state.active_st, t_date))[0][0] or 0
    benef_j = ventes_j - frais_j
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(f"<div class='glass-card'><p>CHIFFRE D'AFFAIRES JOUR</p><h2>{ventes_j:,.2f} $</h2></div>", unsafe_allow_html=True)
    with col_s2:
        c_b = "#00ff00" if benef_j >= 0 else "#ff4b4b"
        st.markdown(f"<div class='glass-container' style='border:2px solid {c_b};'><p>BÉNÉFICE NET ESTIMÉ</p><h2 style='color:{c_b}'>{benef_j:,.2f} $</h2></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (PIÈCE MAÎTRESSE) ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.invoice:
        st.header("🛒 TERMINAL DE VENTE")
        c_mode = st.radio("Paiement en :", ["USD", "CDF"], horizontal=True)
        tx = current_shop[1]
        
        inv_data = db_query("SELECT item_name, sell_price, qty FROM inventory WHERE store_id=?", (st.session_state.active_st,))
        items_dict = {i[0]: (i[1], i[2]) for i in inv_data}
        
        search_p = st.selectbox("🔎 Rechercher un article...", ["---"] + list(items_dict.keys()))
        if search_p != "---":
            if items_dict[search_p][1] > 0:
                st.session_state.cart[search_p] = st.session_state.cart.get(search_p, 0) + 1
                st.toast(f"✅ {search_p} ajouté")
            else: st.error("❌ Article en rupture de stock !")

        if st.session_state.cart:
            st.divider()
            total_sum = 0.0; cart_items = []
            for name, q in list(st.session_state.cart.items()):
                pu_usd = items_dict[name][0]
                pu_curr = pu_usd if c_mode == "USD" else pu_usd * tx
                sub = pu_curr * q
                total_sum += sub
                cart_items.append({"nom": name, "qte": q, "pu": pu_curr, "st": sub})
                
                with st.container():
                    st.markdown(f"<div class='glass-card' style='padding:15px; margin-bottom:10px;'><b>{name}</b><br>{q} x {pu_curr:,.0f} = {sub:,.0f} {c_mode}</div>", unsafe_allow_html=True)
                    if st.button(f"🗑️ Enlever {name}"): del st.session_state.cart[name]; st.rerun()

            st.markdown(f"<div class='total-box'>TOTAL : {total_sum:,.2f} {c_mode}</div>", unsafe_allow_html=True)
            
            cli_name = st.text_input("NOM DU CLIENT", "COMPTANT")
            m_verse = st.number_input(f"MONTANT REÇU ({c_mode})", value=float(total_sum))
            m_reste = total_sum - m_verse
            
            if st.button("🏁 VALIDER ET IMPRIMER LA FACTURE"):
                v_ref = f"FAC-{random.randint(10000,99999)}"
                vd, vh = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                
                # Conversion USD pour la DB
                total_usd = total_sum if c_mode == "USD" else total_sum / tx
                paid_usd = m_verse if c_mode == "USD" else m_verse / tx
                debt_usd = m_reste if c_mode == "USD" else m_reste / tx
                
                db_query("""INSERT INTO sales_history (ref, client, total_usd, paid_usd, debt_usd, currency, v_date, v_time, seller, store_id, items_blob) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (v_ref, cli_name.upper(), total_usd, paid_usd, debt_usd, c_mode, vd, vh, st.session_state.user, st.session_state.active_st, json.dumps(cart_items)), fetch=False)
                
                # Update Stock
                for ci in cart_items:
                    db_query("UPDATE inventory SET qty = qty - ? WHERE item_name=? AND store_id=?", (ci['qte'], ci['nom'], st.session_state.active_st), fetch=False)
                
                # Gestion Dette
                if debt_usd > 0:
                    db_query("INSERT INTO debts_tracking (client_name, balance, sale_ref, store_id) VALUES (?,?,?,?)",
                            (cli_name.upper(), debt_usd, v_ref, st.session_state.active_st), fetch=False)
                
                st.session_state.invoice = {"ref": v_ref, "cli": cli_name, "tot": total_sum, "pay": m_verse, "res": m_reste, "dev": c_mode, "items": cart_items, "d": vd, "h": vh}
                st.session_state.cart = {}; st.rerun()
    else:
        # APERÇU FACTURE
        inv = st.session_state.invoice
        st.markdown(f"""
        <div style='background:white; color:black; padding:40px; border:2px dashed #000; font-family:monospace;'>
            <h2 style='text-align:center;'>{current_shop[2] if current_shop[2] else current_shop[0]}</h2>
            <p style='text-align:center;'>{current_shop[3]}<br>Tél: {current_shop[4]}</p>
            <hr>
            <p><b>REF: {inv['ref']}</b> | Date: {inv['d']} {inv['h']}</p>
            <p>Client: {inv['cli'].upper()}</p>
            <hr>
            {"".join([f"<p>{x['nom']} x{x['qte']} : {x['st']:,.0f} {inv['dev']}</p>" for x in inv['items']])}
            <hr>
            <h3>TOTAL: {inv['tot']:,.2f} {inv['dev']}</h3>
            <p>VERSÉ: {inv['pay']:,.2f} | RESTE: {inv['res']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.invoice = None; st.rerun()

# --- 6.3 STOCK PAR ID (MODIF & SUPPR) ---
elif choice == "📦 STOCK PAR ID":
    st.header("📦 GESTION DU STOCK")
    t_tab1, t_tab2 = st.tabs(["📋 INVENTAIRE GLOBAL", "🛠️ AJOUTER / MODIFIER"])
    
    with t_tab1:
        data = db_query("SELECT id, item_name, qty, buy_price, sell_price FROM inventory WHERE store_id=?", (st.session_state.active_st,))
        if data:
            df_stock = pd.DataFrame(data, columns=["ID", "Désignation", "Quantité", "Achat ($)", "Vente ($)"])
            st.dataframe(df_stock, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ Supprimer un article")
        target_id = st.number_input("ID de l'article à supprimer", min_value=0)
        if st.button("SUPPRIMER DÉFINITIVEMENT"):
            db_query("DELETE FROM inventory WHERE id=? AND store_id=?", (target_id, st.session_state.active_st), fetch=False)
            st.success("Article supprimé."); st.rerun()

    with t_tab2:
        with st.form("form_stock"):
            m_mode = st.radio("Action", ["Nouveau Produit", "Modification par ID"])
            m_id = st.number_input("ID (si modification)", 0)
            m_nom = st.text_input("Désignation")
            m_qte = st.number_input("Quantité", 0)
            m_pa = st.number_input("Prix d'Achat ($)")
            m_pv = st.number_input("Prix de Vente ($)")
            if st.form_submit_button("VALIDER L'ENREGISTREMENT"):
                if m_mode == "Nouveau Produit":
                    db_query("INSERT INTO inventory (item_name, qty, buy_price, sell_price, store_id) VALUES (?,?,?,?,?)",
                            (m_nom.upper(), m_qte, m_pa, m_pv, st.session_state.active_st), fetch=False)
                else:
                    db_query("UPDATE inventory SET item_name=?, qty=?, buy_price=?, sell_price=? WHERE id=? AND store_id=?",
                            (m_nom.upper(), m_qte, m_pa, m_pv, m_id, st.session_state.active_st), fetch=False)
                st.success("Opération réussie !"); st.rerun()

# --- 6.4 DETTES ET TRANCHES ---
elif choice == "📉 DETTES & TRANCHES":
    st.header("📉 SUIVI DES CRÉANCES")
    dettes = db_query("SELECT id, client_name, balance, sale_ref FROM debts_tracking WHERE store_id=? AND status='OUVERT'", (st.session_state.active_st,))
    
    if not dettes: st.success("Aucune dette enregistrée.")
    for d_id, d_cli, d_bal, d_ref in dettes:
        with st.container():
            st.markdown(f"""
            <div class='glass-card'>
                <h3>{d_cli}</h3>
                <p>Reste à payer : <b style='color:red;'>{d_bal:,.2f} $</b></p>
                <p><small>Référence Vente : {d_ref}</small></p>
            </div>
            """, unsafe_allow_html=True)
            t_pay = st.number_input(f"Verser une tranche ($) pour {d_cli}", 0.0, float(d_bal), key=f"tr_{d_id}")
            if st.button("ENREGISTRER LE PAIEMENT", key=f"bt_{d_id}"):
                new_bal = d_bal - t_pay
                db_query("INSERT INTO debt_payments (debt_id, amount, p_date, p_time) VALUES (?,?,?,?)", 
                        (d_id, t_pay, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")), fetch=False)
                if new_bal <= 0:
                    db_query("UPDATE debts_tracking SET balance=0, status='PAYE' WHERE id=?", (d_id,), fetch=False)
                else:
                    db_query("UPDATE debts_tracking SET balance=? WHERE id=?", (new_bal, d_id), fetch=False)
                st.success("✅ Tranche encaissée !"); st.rerun()

# --- 6.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 CHARGES DE LA BOUTIQUE")
    with st.form("form_exp"):
        e_mot = st.text_input("Motif de la dépense")
        e_val = st.number_input("Montant ($)")
        if st.form_submit_button("VALIDER"):
            db_query("INSERT INTO expenses (reason, amount, e_date, store_id) VALUES (?,?,?,?)",
                    (e_mot.upper(), e_val, datetime.now().strftime("%d/%m/%Y"), st.session_state.active_st), fetch=False)
            st.rerun()
    
    st.divider()
    exp_logs = db_query("SELECT reason, amount, e_date FROM expenses WHERE store_id=? ORDER BY id DESC", (st.session_state.active_st,))
    for r, a, d in exp_logs:
        st.write(f"📅 {d} | {r} : **{a:,.2f} $**")

# --- 6.6 ÉQUIPE VENDEURS (CONTRÔLE GÉRANT) ---
elif choice == "👥 ÉQUIPE VENDEURS":
    st.header("👥 GESTION DU PERSONNEL")
    with st.form("form_staff"):
        s_user = st.text_input("ID Vendeur").lower()
        s_pass = st.text_input("Mot de passe", type="password")
        s_name = st.text_input("Nom Complet")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            db_query("INSERT INTO users (username, password, role, owner_ref, status, full_name) VALUES (?,?,?,?,?,?)",
                    (s_user, hashlib.sha256(s_pass.encode()).hexdigest(), 'VENDEUR', st.session_state.active_st, 'ACTIF', s_name), fetch=False)
            st.success("Vendeur ajouté !"); st.rerun()
    
    st.subheader("Vendeurs Actifs")
    staff = db_query("SELECT username, full_name FROM users WHERE owner_ref=? AND role='VENDEUR'", (st.session_state.active_st,))
    for su, sn in staff:
        st.write(f"👤 {sn} (ID: {su})")
        if st.button(f"Supprimer {su}"): db_query("DELETE FROM users WHERE username=?", (su,), fetch=False); st.rerun()

# --- 6.7 RÉGLAGES & RESET ---
elif choice == "⚙️ RÉGLAGES BOUTIQUE":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    
    with st.expander("➕ AJOUTER UN NOUVEAU DÉPÔT / BOUTIQUE"):
        with st.form("new_st"):
            n_id = st.text_input("ID Unique (ex: depot_A)").lower()
            n_nm = st.text_input("Nom de l'Enseigne")
            n_tx = st.number_input("Taux de change (CDF)", 2850.0)
            if st.form_submit_button("CRÉER"):
                db_query("INSERT INTO stores (id, name, owner, rate) VALUES (?,?,?,?)", (n_id, n_nm, st.session_state.user, n_tx), fetch=False)
                st.session_state.active_st = n_id; st.rerun()

    st.subheader(f"Paramètres de : {current_shop[0]}")
    with st.form("edit_st"):
        u_nm = st.text_input("Nom Enseigne", current_shop[0])
        u_tx = st.number_input("Taux de Change", current_shop[1])
        u_hd = st.text_input("Slogan Facture", current_shop[2])
        u_ad = st.text_input("Adresse", current_shop[3])
        u_ph = st.text_input("Téléphone", current_shop[4])
        if st.form_submit_button("SAUVEGARDER"):
            db_query("UPDATE stores SET name=?, rate=?, header=?, address=?, phone=? WHERE id=?", (u_nm, u_tx, u_hd, u_ad, u_ph, st.session_state.active_st), fetch=False)
            st.rerun()

    st.divider()
    st.subheader("🔴 ZONE DANGER")
    if st.button("❗ RÉINITIALISER CETTE BOUTIQUE (EFFACER TOUT)"):
        for table in ["inventory", "sales_history", "debts_tracking", "expenses"]:
            db_query(f"DELETE FROM {table} WHERE store_id=?", (st.session_state.active_st,), fetch=False)
        st.error("Données effacées."); st.rerun()

# --- 6.8 RAPPORTS VENTES ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 HISTORIQUE D'ACTIVITÉ")
    f_date = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    logs = db_query("SELECT v_time, ref, client, total_usd, seller FROM sales_history WHERE store_id=? AND v_date=? ORDER BY id DESC", (st.session_state.active_st, f_date))
    
    if logs:
        for t, r, c, tot, s in logs:
            st.markdown(f"<div class='glass-card'>{t} | {r} | <b>{tot:,.2f} $</b> | Client: {c} | Vnd: {s}</div>", unsafe_allow_html=True)
    else: st.info("Aucune donnée pour cette date.")

elif choice == "🚪 QUITTER":
    st.session_state.auth = False; st.rerun()
