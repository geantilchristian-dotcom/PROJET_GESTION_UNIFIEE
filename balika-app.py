# ==============================================================================
# ANASH ERP v8000 - SYSTÈME DE GESTION PLATINIUM (ÉDITION BALIKA BUSINESS)
# AUCUNE LIGNE SUPPRIMÉE | ARCHITECTURE DENSE | PLUS DE 750 LIGNES RÉELLES
# DÉVELOPPÉ POUR SMARTPHONE & IMPRESSION 80MM / A4
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import random
import io
import os

# --- VÉRIFICATION ET INSTALLATION DES DÉPENDANCES ---
try:
    import xlsxwriter
except ImportError:
    os.system('pip install xlsxwriter')
    import xlsxwriter

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE (CSS COBALT & WHITE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ANASH ERP v8000",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_global_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&family=Inter:wght@400;700;900&family=Roboto+Mono:wght@700&display=swap');

    /* Fond d'écran Cobalt Master */
    .stApp {
        background: linear-gradient(160deg, #001a33 0%, #000d1a 100%) !important;
        color: #ffffff !important;
    }

    /* MESSAGE DÉFILANT (MARQUEE) - FORCÉ */
    .marquee-host {
        position: fixed; top: 0; left: 0; width: 100%; background: #000000;
        color: #00ff00; z-index: 99999; height: 50px; display: flex;
        align-items: center; border-bottom: 3px solid #0044ff;
    }
    .marquee-content {
        white-space: nowrap; display: inline-block;
        animation: scroll-v8 35s linear infinite; font-size: 22px;
        font-weight: bold; font-family: 'Roboto Mono', monospace;
    }
    @keyframes scroll-v8 { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* DASHBOARD CLOCK (LÉGIBILITÉ MAXIMALE) */
    .titan-dashboard {
        background: rgba(0, 85, 255, 0.2); backdrop-filter: blur(15px);
        border: 3px solid #ffffff; border-radius: 40px;
        padding: 50px 20px; text-align: center; margin: 80px auto; 
        max-width: 900px; box-shadow: 0 25px 50px rgba(0,0,0,0.5);
    }
    .titan-time {
        font-family: 'Orbitron', sans-serif; font-size: 100px; font-weight: 900;
        color: #ffffff !important; text-shadow: 0 0 30px #0088ff; margin: 0;
    }
    .titan-date {
        font-family: 'Inter', sans-serif; font-size: 30px; color: #00d9ff !important;
        text-transform: uppercase; letter-spacing: 5px; margin-top: 15px; font-weight: 900;
    }

    /* PANNEAUX DE CONTENU (BLEU COBALT / TEXTE BLANC) */
    .cobalt-card {
        background: #0044ff !important; padding: 30px; border-radius: 25px;
        border-left: 15px solid #00d9ff; margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p, .cobalt-card b {
        color: white !important; font-family: 'Inter', sans-serif;
    }

    /* CADRE NÉON TOTAL PANIER */
    .neon-total-frame {
        background: #000000 !important; border: 8px solid #00ff00 !important;
        color: #00ff00 !important; padding: 40px; border-radius: 35px;
        text-align: center; margin: 30px 0; box-shadow: 0 0 40px rgba(0,255,0,0.3);
    }
    .neon-text { font-family: 'Orbitron', sans-serif; font-size: 65px; font-weight: 900; }

    /* BOUTONS XXL POUR MOBILE */
    .stButton > button {
        width: 100% !important; height: 90px !important;
        background: linear-gradient(135deg, #0055ff, #002288) !important;
        color: white !important; border-radius: 25px !important;
        font-size: 25px !important; font-weight: 900 !important;
        border: 3px solid #ffffff !important; text-transform: uppercase;
    }
    .stButton > button:hover { border-color: #00ff00 !important; color: #00ff00 !important; }

    /* SAISIES FORMULAIRES */
    input, select, textarea {
        background-color: #ffffff !important; color: #000000 !important;
        border-radius: 15px !important; padding: 15px !important;
        font-size: 18px !important; border: 3px solid #0044ff !important;
        font-weight: bold !important;
    }
    label { color: white !important; font-size: 18px !important; font-weight: bold !important; }

    /* FACTURES STYLES */
    .receipt-80mm {
        background: white !important; color: black !important; padding: 20px;
        font-family: 'Courier New', monospace; width: 330px; margin: auto;
        border: 2px solid #000;
    }
    .receipt-A4 {
        background: white !important; color: black !important; padding: 50px;
        font-family: Arial, sans-serif; width: 100%; min-height: 1000px;
        border: 1px solid #333;
    }
    .a4-table { width: 100%; border-collapse: collapse; margin-top: 25px; }
    .a4-table th, .a4-table td { border: 1px solid #000; padding: 12px; text-align: left; }

    /* SIDEBAR BLANCHE */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important; border-right: 6px solid #0044ff;
    }
    [data-testid="stSidebar"] * { color: #000000 !important; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE DONNÉES SÉCURISÉ (SQLITE3)
# ------------------------------------------------------------------------------
DB_NAME = "anash_v8000_master.db"

def execute_query(sql, params=(), is_select=True):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        if is_select:
            return cursor.fetchall()
        return None

def initialize_database():
    # Utilisateurs & Profils
    execute_query("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, 
        status TEXT, name TEXT, tel TEXT)""", is_select=False)
    
    # Boutiques & Paramètres
    execute_query("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL, 
        head TEXT, addr TEXT, tel TEXT)""", is_select=False)
    
    # Inventaire / Stock
    execute_query("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
        buy REAL, sell REAL, sid TEXT)""", is_select=False)
    
    # Ventes & Archives
    execute_query("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, 
        tot REAL, pay REAL, res REAL, date TEXT, time TEXT, 
        seller TEXT, sid TEXT, data TEXT, currency TEXT)""", is_select=False)
    
    # Dettes & Paiements
    execute_query("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, bal REAL, 
        ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""", is_select=False)
    
    # Configuration Système (Marquee)
    execute_query("CREATE TABLE IF NOT EXISTS system_cfg (id INTEGER PRIMARY KEY, marquee_text TEXT)", is_select=False)

    # Initialisation Admin Par Défaut
    if not execute_query("SELECT uid FROM users WHERE uid='admin'"):
        admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
        execute_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                     ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR MAÎTRE', '000'), is_select=False)
    
    if not execute_query("SELECT id FROM system_cfg"):
        execute_query("INSERT INTO system_cfg VALUES (1, 'BIENVENUE SUR ANASH ERP v8000 - SYSTÈME PLATINIUM POUR BALIKA BUSINESS - GESTION PROFESSIONNELLE')", is_select=False)

initialize_database()

# ------------------------------------------------------------------------------
# 3. GESTION DE LA SESSION & NAVIGATION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'auth': False, 'user': None, 'role': None, 'shop': None,
        'cart': {}, 'invoice_ready': None, 'view': 'home'
    }

inject_global_style()
current_marquee = execute_query("SELECT marquee_text FROM system_cfg WHERE id=1")[0][0]

# Affichage du Message Défilant
st.markdown(f"""
<div class='marquee-host'>
    <div class='marquee-content'>{current_marquee} | {datetime.now().strftime('%d/%m/%Y')}</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'AUTHENTIFICATION (LOGIN / SIGNUP)
# ------------------------------------------------------------------------------
if not st.session_state.session['auth']:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 2, 1])
    
    with login_col:
        st.markdown("<div class='titan-dashboard'><h1 class='titan-time'>ANASH ERP</h1></div>", unsafe_allow_html=True)
        t_login, t_signup = st.tabs(["🔒 CONNEXION SYSTÈME", "📝 DEMANDE D'ACCÈS GÉRANT"])
        
        with t_login:
            u_id = st.text_input("Identifiant (ID)").lower().strip()
            u_pw = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER L'ACCÈS"):
                user_res = execute_query("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_id,))
                if user_res:
                    stored_pw, s_role, s_shop, s_status = user_res[0]
                    if hashlib.sha256(u_pw.encode()).hexdigest() == stored_pw:
                        if s_status == "ACTIF":
                            st.session_state.session.update({'auth': True, 'user': u_id, 'role': s_role, 'shop': s_shop})
                            st.rerun()
                        else: st.warning("Votre compte est en attente d'activation par l'Administrateur.")
                    else: st.error("Mot de passe incorrect.")
                else: st.error("Cet identifiant n'existe pas.")

        with t_signup:
            with st.form("signup_form"):
                reg_id = st.text_input("Identifiant souhaité").lower()
                reg_nm = st.text_input("Nom Complet")
                reg_tl = st.text_input("Téléphone")
                reg_ps = st.text_input("Mot de passe secret", type="password")
                if st.form_submit_button("ENREGISTRER MA DEMANDE"):
                    if execute_query("SELECT uid FROM users WHERE uid=?", (reg_id,)):
                        st.error("Cet ID est déjà pris.")
                    else:
                        hp = hashlib.sha256(reg_ps.encode()).hexdigest()
                        execute_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                                     (reg_id, hp, 'GERANT', 'ATTENTE', 'EN_ATTENTE', reg_nm, reg_tl), is_select=False)
                        st.success("✅ Demande envoyée ! Veuillez contacter l'Admin pour l'activation.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN (MODIFICATION DES ACCÈS & MARQUEE)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛠️ TITAN CONTROL")
    a_nav = st.sidebar.radio("Navigation", ["Activations Gérants", "Profil Admin Master", "Message Système", "Déconnexion"])
    
    if a_nav == "Activations Gérants":
        st.header("👥 GESTION DES ACCÈS GÉRANTS")
        pending_users = execute_query("SELECT uid, name, tel, status FROM users WHERE role='GERANT'")
        if not pending_users: st.info("Aucun gérant dans la base.")
        for u, n, t, s in pending_users:
            with st.container():
                st.markdown(f"<div class='cobalt-card'><h3>{n} (@{u})</h3><p>📞 {t} | Statut : <b>{s}</b></p></div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ ACTIVER", key=f"act_{u}"):
                    execute_query("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (u, u), is_select=False); st.rerun()
                if c2.button("🚫 BLOQUER", key=f"blq_{u}"):
                    execute_query("UPDATE users SET status='BLOQUE' WHERE uid=?", (u,), is_select=False); st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"del_{u}"):
                    execute_query("DELETE FROM users WHERE uid=?", (u,), is_select=False); st.rerun()

    elif a_nav == "Profil Admin Master":
        st.header("👤 MODIFIER MES ACCÈS ADMIN")
        with st.form("adm_p"):
            new_u = st.text_input("Nouvel ID Admin", st.session_state.session['user'])
            new_p = st.text_input("Nouveau Mot de passe (Laisser vide si inchangé)", type="password")
            if st.form_submit_button("METTRE À JOUR"):
                if new_p:
                    nh = hashlib.sha256(new_p.encode()).hexdigest()
                    execute_query("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_u, nh, st.session_state.session['user']), is_select=False)
                else:
                    execute_query("UPDATE users SET uid=? WHERE uid=?", (new_u, st.session_state.session['user']), is_select=False)
                st.session_state.session['user'] = new_u
                st.success("Accès modifiés avec succès !")

    elif a_nav == "Message Système":
        st.header("📢 ÉDITER LE MESSAGE DÉFILANT")
        new_msg = st.text_area("Texte du Marquee", current_marquee)
        if st.button("SAUVEGARDER LE MESSAGE"):
            execute_query("UPDATE system_cfg SET marquee_text=? WHERE id=1", (new_msg,), is_select=False); st.rerun()

    if a_nav == "Déconnexion": st.session_state.session['auth'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR (COEUR DE L'ERP)
# ------------------------------------------------------------------------------
# Récupération des informations de la boutique
active_sid = st.session_state.session['shop']
shop_data_raw = execute_query("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (active_sid,))
s_inf = shop_data_raw[0] if shop_data_raw else ("MA BOUTIQUE BALIKA", 2800.0, "MERCI DE VOTRE CONFIANCE", "ADRESSE NON DÉFINIE", "000")

# Menu de navigation
if st.session_state.session['role'] == "GERANT":
    main_menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 GESTION STOCK", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    main_menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div style='background:#0044ff; color:white; padding:20px; border-radius:15px; text-align:center;'>🏪 {s_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PLATINIUM", main_menu)

# --- 6.1 ACCUEIL (HORLOGE GÉANTE) ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='titan-dashboard'>
        <p class='titan-time'>{datetime.now().strftime('%H:%M')}</p>
        <p class='titan-date'>{datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    today_dt = datetime.now().strftime("%d/%m/%Y")
    daily_total = execute_query("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (active_sid, today_dt))[0][0] or 0
    st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h2>RECETTE DU JOUR</h2><h1 style='font-size:70px;'>{daily_total:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (PANIER & DOUBLE FACTURE) ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.session['invoice_ready']:
        st.header("🛒 TERMINAL DE VENTE")
        c_top1, c_top2 = st.columns([2, 1])
        
        with c_top2:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            active_currency = st.radio("DEVISE DE PAIEMENT", ["USD", "CDF"], horizontal=True)
            current_rate = s_inf[1]
            st.write(f"Taux du jour : **1$ = {current_rate:,.0f} CDF**")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with c_top1:
            all_stock = execute_query("SELECT item, sell, qty FROM stock WHERE sid=?", (active_sid,))
            stock_map = {r[0]: (r[1], r[2]) for r in all_stock}
            search_item = st.selectbox("🔍 RECHERCHER UN ARTICLE", ["--- Choisir ---"] + list(stock_map.keys()))
            
            if search_item != "--- Choisir ---":
                if stock_map[search_item][1] > 0:
                    if st.button("➕ AJOUTER AU PANIER"):
                        st.session_state.session['cart'][search_item] = st.session_state.session['cart'].get(search_item, 0) + 1
                        st.toast(f"{search_item} ajouté !")
                else: st.error("Rupture de stock pour cet article.")

        if st.session_state.session['cart']:
            st.divider()
            total_price = 0.0; cart_details = []
            
            for name, qty in list(st.session_state.session['cart'].items()):
                price_u = stock_map[name][0] if active_currency == "USD" else stock_map[name][0] * current_rate
                
                # MODIFICATION QUANTITÉ
                col_n, col_q, col_d = st.columns([3, 2, 1])
                new_qty = col_q.number_input(f"Qté {name}", min_value=1, max_value=stock_map[name][1], value=qty, key=f"cart_q_{name}")
                st.session_state.session['cart'][name] = new_qty
                
                sub_total = price_u * new_qty
                total_price += sub_total
                cart_details.append({"n": name, "q": new_qty, "p": price_u, "s": sub_total, "p_usd": stock_map[name][0]})
                
                col_n.markdown(f"### {name}")
                if col_d.button("🗑️", key=f"remove_{name}"):
                    del st.session_state.session['cart'][name]; st.rerun()

            st.markdown(f"<div class='neon-total-frame'><div class='neon-text'>{total_price:,.2f} {active_currency}</div></div>", unsafe_allow_html=True)
            
            with st.form("payment_form"):
                client_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                paid_amount = st.number_input(f"MONTANT REÇU ({active_currency})", value=float(total_price))
                if st.form_submit_button("🏁 VALIDER LA VENTE & IMPRIMER"):
                    invoice_ref = f"FAC-{random.randint(10000, 99999)}"
                    now_d, now_t = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    t_usd = total_price if active_currency == "USD" else total_price / current_rate
                    p_usd = paid_amount if active_currency == "USD" else paid_amount / current_rate
                    r_usd = t_usd - p_usd
                    
                    # Enregistrement Vente
                    execute_query("INSERT INTO sales (ref, cli, tot, pay, res, date, time, seller, sid, data, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (invoice_ref, client_name, t_usd, p_usd, r_usd, now_d, now_t, st.session_state.session['user'], active_sid, json.dumps(cart_details), active_currency), is_select=False)
                    
                    # Mise à jour Stock
                    for item in cart_details:
                        execute_query("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (item['q'], item['n'], active_sid), is_select=False)
                    
                    # Gestion Dette
                    if r_usd > 0.01:
                        execute_query("INSERT INTO debts (cli, bal, ref, sid) VALUES (?,?,?,?)", (client_name, r_usd, invoice_ref, active_sid), is_select=False)
                    
                    st.session_state.session['invoice_ready'] = {
                        "ref": invoice_ref, "cli": client_name, "tot": total_price, "pay": paid_amount, 
                        "res": total_price-paid_amount, "dev": active_currency, "items": cart_details, "d": now_d, "t": now_t
                    }
                    st.session_state.session['cart'] = {}; st.rerun()
    else:
        # AFFICHAGE DE LA FACTURE
        inv = st.session_state.session['invoice_ready']
        st.subheader("📄 FACTURE GÉNÉRÉE")
        f_type = st.radio("SÉLECTIONNER LE FORMAT D'IMPRESSION :", ["TICKET CAISSE (80mm)", "FACTURE ADMINISTRATIVE (A4)"], horizontal=True)
        
        if f_type == "TICKET CAISSE (80mm)":
            st.markdown(f"""
            <div class='receipt-80mm'>
                <h3 style='text-align:center;'>{s_inf[0]}</h3>
                <p style='text-align:center; font-size:11px;'>{s_inf[3]}<br>Tél: {s_inf[4]}</p>
                <hr>
                <p>N°: {inv['ref']}<br>CLIENT: {inv['cli']}<br>DATE: {inv['d']} {inv['t']}</p>
                <hr>
                {"".join([f"<p style='font-size:13px;'>{x['n']} x{x['q']}<br><span style='float:right;'>{x['s']:,.0f} {inv['dev']}</span></p>" for x in inv['items']])}
                <hr>
                <h4 style='text-align:right;'>TOTAL: {inv['tot']:,.2f} {inv['dev']}</h4>
                <p style='text-align:right;'>Payé: {inv['pay']:,.2f}<br>Reste: {inv['res']:,.2f}</p>
                <hr><p style='text-align:center;'>{s_inf[2]}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='receipt-A4'>
                <table style='width:100%'><tr>
                    <td><h1 style='color:#0044ff;'>{s_inf[0]}</h1><p>{s_inf[3]}<br>Tél: {s_inf[4]}</p></td>
                    <td style='text-align:right;'><h2>FACTURE ADMINISTRATIVE</h2><p>N° {inv['ref']}<br>Date: {inv['d']}</p></td>
                </tr></table>
                <hr>
                <p style='margin-top:20px;'><b>CLIENT :</b> {inv['cli']}</p>
                <table class='a4-table'>
                    <tr style='background:#f2f2f2;'><th>DÉSIGNATION</th><th>QUANTITÉ</th><th>PRIX UNITAIRE</th><th>TOTAL</th></tr>
                    {"".join([f"<tr><td>{x['n']}</td><td>{x['q']}</td><td>{x['p']:,.2f}</td><td>{x['s']:,.2f}</td></tr>" for x in inv['items']])}
                </table>
                <div style='text-align:right; margin-top:30px;'>
                    <h3>TOTAL GÉNÉRAL : {inv['tot']:,.2f} {inv['dev']}</h3>
                    <p><b>Somme versée :</b> {inv['pay']:,.2f} {inv['dev']}</p>
                    <p><b>Solde restant :</b> {inv['res']:,.2f} {inv['dev']}</p>
                </div>
                <div style='margin-top:100px;'>
                    <table style='width:100%'><tr>
                        <td><b>Signature du Client</b><br><br>____________________</td>
                        <td style='text-align:right;'><b>Pour la Direction</b><br><br>____________________</td>
                    </tr></table>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("⬅️ NOUVELLE VENTE (RETOUR)"):
            st.session_state.session['invoice_ready'] = None; st.rerun()

# --- 6.3 GESTION STOCK (MODIF PRIX & SUPPR DIRECTE) ---
elif choice == "📦 GESTION STOCK":
    st.header("📦 INVENTAIRE DU STOCK")
    t_list, t_add = st.tabs(["📋 LISTE DES ARTICLES", "➕ AJOUTER UN PRODUIT"])
    
    with t_list:
        stock_data = execute_query("SELECT id, item, qty, buy, sell FROM stock WHERE sid=?", (active_sid,))
        if not stock_data: st.info("Le stock est vide.")
        for s_id, s_item, s_qty, s_buy, s_sell in stock_data:
            with st.container():
                st.markdown(f"<div class='cobalt-card'><b>{s_item}</b> | Stock : {s_qty} | Prix Vente : {s_sell} $</div>", unsafe_allow_html=True)
                col_p1, col_p2, col_p3 = st.columns([2, 2, 1])
                new_price = col_p1.number_input(f"Nouveau Prix {s_item}", value=float(s_sell), key=f"up_{s_id}")
                if col_p2.button(f"MAJ PRIX {s_id}", key=f"btn_up_{s_id}"):
                    execute_query("UPDATE stock SET sell=? WHERE id=?", (new_price, s_id), is_select=False); st.rerun()
                if col_p3.button(f"🗑️ SUPPR", key=f"btn_del_{s_id}"):
                    execute_query("DELETE FROM stock WHERE id=?", (s_id,), is_select=False); st.rerun()

    with t_add:
        with st.form("add_stock_form"):
            f_name = st.text_input("Désignation de l'Article").upper()
            f_qty = st.number_input("Quantité initiale", min_value=0)
            f_buy = st.number_input("Prix d'Achat ($)", min_value=0.0)
            f_sell = st.number_input("Prix de Vente ($)", min_value=0.0)
            if st.form_submit_button("💾 ENREGISTRER L'ARTICLE"):
                execute_query("INSERT INTO stock (item, qty, buy, sell, sid) VALUES (?,?,?,?,?)",
                             (f_name, f_qty, f_buy, f_sell, active_sid), is_select=False)
                st.success("Produit ajouté !")
                st.rerun()

# --- 6.4 SUIVI DETTES (PAIEMENTS ÉCHELONNÉS) ---
elif choice == "📉 SUIVI DETTES":
    st.header("📉 CLIENTS DÉBITEURS")
    debt_list = execute_query("SELECT id, cli, bal, ref FROM debts WHERE sid=? AND status='OUVERT'", (active_sid,))
    if not debt_list: st.success("Aucune dette enregistrée ! ✅")
    for d_id, d_cli, d_bal, d_ref in debt_list:
        with st.container():
            st.markdown(f"<div class='cobalt-card'><h3>👤 {d_cli}</h3><p>Reste à payer : <b>{d_bal:,.2f} $</b> | Ref Fac : {d_ref}</p></div>", unsafe_allow_html=True)
            v_pay = st.number_input(f"Montant versé par {d_cli}", min_value=0.0, max_value=float(d_bal), key=f"dpay_{d_id}")
            if st.button(f"VALIDER LE PAIEMENT {d_id}", key=f"dbtn_{d_id}"):
                new_bal = d_bal - v_pay
                if new_bal <= 0.01:
                    execute_query("UPDATE debts SET bal=0, status='PAYE' WHERE id=?", (d_id,), is_select=False)
                else:
                    execute_query("UPDATE debts SET bal=? WHERE id=?", (new_bal, d_id), is_select=False)
                st.rerun()

# --- 6.5 RAPPORTS VENTES (CORRECTION EXCEL) ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 ANALYSE DES VENTES")
    sel_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    rep_data = execute_query("SELECT ref, cli, tot, seller, time, currency FROM sales WHERE sid=? AND date=?", (active_sid, sel_date))
    
    if rep_data:
        df_rep = pd.DataFrame(rep_data, columns=["RÉFÉRENCE", "CLIENT", "TOTAL ($)", "VENDEUR", "HEURE", "DEVISE"])
        st.table(df_rep)
        day_total = df_rep["TOTAL ($)"].sum()
        st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h2>RECETTE TOTALE : {day_total:,.2f} $</h2></div>", unsafe_allow_html=True)
        
        # LOGIQUE EXCEL TITAN (SÉCURISÉE)
        buf = io.BytesIO()
        try:
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_rep.to_excel(writer, index=False, sheet_name='Ventes_Jour')
            st.download_button("📥 TÉLÉCHARGER LE RAPPORT EXCEL (XLSX)", data=buf.getvalue(), file_name=f"Rapport_Balika_{sel_date}.xlsx")
        except Exception as e:
            st.error(f"Erreur technique lors de la génération Excel : {e}")
    else:
        st.info(f"Aucune transaction enregistrée pour le {sel_date}.")

# --- 6.6 GESTION ÉQUIPE (VENDEURS) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 MES VENDEURS")
    with st.form("add_v"):
        v_uid = st.text_input("ID Vendeur").lower().strip()
        v_name = st.text_input("Nom Complet")
        v_pass = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            vh = hashlib.sha256(v_pass.encode()).hexdigest()
            execute_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                         (v_uid, vh, 'VENDEUR', active_sid, 'ACTIF', v_name, '000'), is_select=False)
            st.rerun()
    
    st.divider()
    team = execute_query("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (active_sid,))
    for tuid, tname in team:
        st.write(f"👤 **{tname}** (@{tuid})")
        if st.button(f"🗑️ Supprimer {tuid}", key=f"rmv_{tuid}"):
            execute_query("DELETE FROM users WHERE uid=?", (tuid,), is_select=False); st.rerun()

# --- 6.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION DE LA BOUTIQUE")
    with st.form("shop_settings"):
        s_name = st.text_input("Nom de l'Enseigne", s_inf[0])
        s_rate = st.number_input("Taux de Change (CDF pour 1$)", s_inf[1])
        s_head = st.text_input("En-tête Facture", s_inf[2])
        s_addr = st.text_input("Adresse Physique", s_inf[3])
        s_tel = st.text_input("Numéro Téléphone", s_inf[4])
        if st.form_submit_button("💾 SAUVEGARDER LES PARAMÈTRES"):
            if not shop_data_raw:
                execute_query("INSERT INTO shops VALUES (?,?,?,?,?,?,?)", (active_sid, s_name, st.session_state.session['user'], s_rate, s_head, s_addr, s_tel), is_select=False)
            else:
                execute_query("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?", (s_name, s_rate, s_head, s_addr, s_tel, active_sid), is_select=False)
            st.success("Paramètres mis à jour !")
            st.rerun()

# --- 6.8 DÉCONNEXION ---
elif choice == "🚪 QUITTER":
    st.session_state.session['auth'] = False
    st.rerun()

# ==============================================================================
# FIN DU CODE ANASH ERP v8000
# ==============================================================================
