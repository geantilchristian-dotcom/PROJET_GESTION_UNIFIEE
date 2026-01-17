# ==============================================================================
# ANASH ERP v6000 - SYSTÈME DE GESTION TITAN (ÉDITION BALIKA BUSINESS)
# DÉVELOPPÉ POUR : USAGE PROFESSIONNEL MOBILE & DESKTOP
# LIGNES : > 750 | DESIGN COBALT | ARCHITECTURE INTÉGRALE | AUCUNE SUPPRESSION
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
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION ESTHÉTIQUE & STYLE CSS (COBALT & WHITE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ANASH ERP v6000",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_titan_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');

    /* Fond d'écran Cobalt Master */
    .stApp {
        background: linear-gradient(160deg, #001a33 0%, #000d1a 100%) !important;
        color: #ffffff !important;
    }

    /* MESSAGE DÉFILANT CSS ULTRA FLUIDE */
    .marquee-host {
        position: fixed; top: 0; left: 0; width: 100%; background: #000000;
        color: #00ff00; z-index: 99999; height: 50px; display: flex;
        align-items: center; border-bottom: 3px solid #0044ff;
        box-shadow: 0 5px 15px rgba(0,0,0,0.8);
    }
    .marquee-text {
        white-space: nowrap; display: inline-block;
        animation: titan-scroll 45s linear infinite; font-size: 20px;
        font-weight: bold; font-family: 'Roboto Mono', monospace;
        text-transform: uppercase;
    }
    @keyframes titan-scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* DASHBOARD CLOCK (80MM MOBILE STYLE) */
    .titan-clock-container {
        background: rgba(0, 85, 255, 0.1); backdrop-filter: blur(20px);
        border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 50px;
        padding: 70px 20px; text-align: center; margin: 70px auto; 
        max-width: 900px; box-shadow: 0 30px 60px rgba(0,0,0,0.6);
    }
    .titan-time {
        font-family: 'Orbitron', sans-serif; font-size: 120px; font-weight: 900;
        color: #ffffff; text-shadow: 0 0 40px #0088ff; line-height: 1; margin: 0;
    }
    .titan-date {
        font-size: 30px; color: #00d9ff; text-transform: uppercase;
        letter-spacing: 6px; margin-top: 20px; font-weight: 300;
    }

    /* PANNEAUX D'AFFICHAGE COBALT */
    .cobalt-card {
        background: #0044ff !important; padding: 35px; border-radius: 30px;
        border-left: 12px solid #00d9ff; margin-bottom: 25px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4); transition: transform 0.3s;
    }
    .cobalt-card:hover { transform: translateY(-5px); }
    .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p, .cobalt-card b, .cobalt-card span {
        color: white !important; font-family: 'Inter', sans-serif;
    }

    /* CADRE NÉON TOTAL PANIER */
    .neon-frame-box {
        background: #000000 !important; border: 8px solid #00ff00 !important;
        color: #00ff00 !important; padding: 50px; border-radius: 40px;
        text-align: center; margin: 40px 0; box-shadow: 0 0 50px rgba(0, 255, 0, 0.4);
    }
    .neon-price { font-family: 'Orbitron', sans-serif; font-size: 75px; font-weight: 900; }

    /* BOUTONS XXL POUR ÉCRAN TACTILE */
    .stButton > button {
        width: 100% !important; height: 95px !important;
        background: linear-gradient(135deg, #0055ff, #002288) !important;
        color: white !important; border-radius: 25px !important;
        font-size: 26px !important; font-weight: 800 !important;
        border: 3px solid #ffffff !important; text-transform: uppercase;
        box-shadow: 0 12px 25px rgba(0,0,0,0.5);
    }
    .stButton > button:active { transform: scale(0.96); background: #00ff00 !important; color: #000 !important; }

    /* INPUTS & SELECTS FORM */
    input, select, textarea {
        background-color: #ffffff !important; color: #000000 !important;
        border-radius: 18px !important; padding: 18px !important;
        font-size: 20px !important; border: 4px solid #0044ff !important;
    }
    label { color: white !important; font-size: 20px !important; font-weight: bold !important; }

    /* STRUCTURE SIDEBAR BLANCHE */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important; border-right: 6px solid #0044ff;
    }
    [data-testid="stSidebar"] * { color: #000000 !important; font-weight: 900; font-size: 18px; }

    /* STYLES FACTURES */
    .receipt-80mm {
        background: white !important; color: black !important; padding: 25px;
        font-family: 'Courier New', monospace; width: 340px; margin: auto;
        border: 1px solid #000; line-height: 1.2;
    }
    .receipt-A4-admin {
        background: white !important; color: black !important; padding: 60px;
        font-family: 'Arial', sans-serif; width: 100%; min-height: 1100px;
        border: 1px solid #333; box-shadow: 0 0 20px rgba(0,0,0,0.2);
    }
    .table-a4 { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .table-a4 th, .table-a4 td { border: 1px solid black; padding: 12px; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. CORE DATABASE ENGINE (SQLITE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v6000_titan.db"

def db_query(sql, params=(), is_select=True):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        if is_select:
            return cursor.fetchall()
        return None

def titan_init_db():
    # Table Utilisateurs
    db_query("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, 
        status TEXT, name TEXT, tel TEXT, created_at TEXT)""", is_select=False)
    
    # Table Boutiques
    db_query("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL, 
        head TEXT, addr TEXT, tel TEXT, logo BLOB)""", is_select=False)
    
    # Table Stock (Détaillé)
    db_query("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
        buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""", is_select=False)
    
    # Table Ventes (Historique complet)
    db_query("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, 
        tot REAL, pay REAL, res REAL, date TEXT, time TEXT, 
        seller TEXT, sid TEXT, data TEXT, currency TEXT)""", is_select=False)
    
    # Table Dettes
    db_query("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, bal REAL, 
        ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_update TEXT)""", is_select=False)
    
    # Table Configuration Système
    db_query("CREATE TABLE IF NOT EXISTS sys_config (id INTEGER PRIMARY KEY, marquee_text TEXT)", is_select=False)

    # Comptes par défaut
    if not db_query("SELECT uid FROM users WHERE uid='admin'"):
        hpwd = hashlib.sha256("admin123".encode()).hexdigest()
        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                ('admin', hpwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR TITAN', '000', '2026-01-17'), is_select=False)
    
    if not db_query("SELECT id FROM sys_config"):
        db_query("INSERT INTO sys_config VALUES (1, 'BIENVENUE SUR ANASH ERP v6000 - GESTION TITAN POUR BALIKA BUSINESS - VOTRE RÉUSSITE NOTRE PRIORITÉ')", is_select=False)

titan_init_db()

# ------------------------------------------------------------------------------
# 3. ÉTAT DE LA SESSION (SESSION STATE)
# ------------------------------------------------------------------------------
if 'titan_session' not in st.session_state:
    st.session_state.titan_session = {
        'logged': False, 'uid': None, 'role': None, 'shop': None,
        'cart': {}, 'last_inv': None, 'view': 'home'
    }

inject_titan_ui()
marquee_val = db_query("SELECT marquee_text FROM sys_config WHERE id=1")[0][0]

# Injection du message défilant
st.markdown(f'<div class="marquee-host"><div class="marquee-text">{marquee_val}</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS (LOGIN / REGISTRATION)
# ------------------------------------------------------------------------------
if not st.session_state.titan_session['logged']:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    _, login_box, _ = st.columns([1, 2, 1])
    
    with login_box:
        st.markdown("<div class='titan-clock-container'><h1 class='titan-time'>ANASH ERP</h1></div>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["🔒 ACCÈS SYSTÈME", "📝 NOUVEAU GÉRANT"])
        
        with tab_in:
            u_input = st.text_input("Identifiant").lower().strip()
            p_input = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER"):
                user_check = db_query("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_input,))
                if user_check:
                    stored_p, s_role, s_shop, s_stat = user_check[0]
                    if hashlib.sha256(p_input.encode()).hexdigest() == stored_p:
                        if s_stat == "ACTIF":
                            st.session_state.titan_session.update({'logged': True, 'uid': u_input, 'role': s_role, 'shop': s_shop})
                            st.rerun()
                        else: st.error("Compte en attente d'activation par l'Admin.")
                    else: st.error("Mot de passe incorrect.")
                else: st.error("Utilisateur non enregistré.")

        with tab_up:
            with st.form("reg_form"):
                reg_uid = st.text_input("ID Utilisateur souhaité").lower()
                reg_nam = st.text_input("Nom Complet du Gérant")
                reg_tel = st.text_input("Numéro Téléphone")
                reg_pwd = st.text_input("Mot de passe secret", type="password")
                if st.form_submit_button("CRÉER MON COMPTE"):
                    if db_query("SELECT uid FROM users WHERE uid=?", (reg_uid,)):
                        st.error("Cet ID est déjà utilisé.")
                    else:
                        h_pwd = hashlib.sha256(reg_pwd.encode()).hexdigest()
                        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                                (reg_uid, h_pwd, 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', reg_nam, reg_tel, str(datetime.now())), is_select=False)
                        st.success("✅ Demande envoyée ! Veuillez patienter pour l'activation.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN (MODIFICATION USERS & LOGS)
# ------------------------------------------------------------------------------
if st.session_state.titan_session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛠️ TITAN ADMIN")
    adm_nav = st.sidebar.radio("Navigation", ["Gérer les Gérants", "Profil Admin", "Configuration Système", "Déconnexion"])
    
    if adm_nav == "Gérer les Gérants":
        st.header("👥 CONTRÔLE DES ACCÈS")
        all_u = db_query("SELECT uid, name, tel, status, created_at FROM users WHERE role='GERANT'")
        for u, n, t, s, c in all_u:
            with st.container():
                st.markdown(f"<div class='cobalt-card'><h3>{n} (@{u})</h3><p>📞 {t} | Créé le: {c} | Statut: <b>{s}</b></p></div>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                if col1.button("✅ ACTIVER", key=f"ac_{u}"):
                    db_query("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (u, u), is_select=False); st.rerun()
                if col2.button("🚫 BLOQUER", key=f"bl_{u}"):
                    db_query("UPDATE users SET status='BLOQUE' WHERE uid=?", (u,), is_select=False); st.rerun()
                if col3.button("🗑️ SUPPRIMER", key=f"de_{u}"):
                    db_query("DELETE FROM users WHERE uid=?", (u,), is_select=False); st.rerun()

    elif adm_nav == "Profil Admin":
        st.header("👤 MON PROFIL ADMIN")
        with st.form("adm_profile"):
            new_adm_uid = st.text_input("Nouvel ID Admin", st.session_state.titan_session['uid'])
            new_adm_pwd = st.text_input("Nouveau Mot de Passe (Optionnel)", type="password")
            if st.form_submit_button("METTRE À JOUR MES ACCÈS"):
                if new_adm_pwd:
                    nh = hashlib.sha256(new_adm_pwd.encode()).hexdigest()
                    db_query("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_adm_uid, nh, st.session_state.titan_session['uid']), is_select=False)
                else:
                    db_query("UPDATE users SET uid=? WHERE uid=?", (new_adm_uid, st.session_state.titan_session['uid']), is_select=False)
                st.session_state.titan_session['uid'] = new_adm_uid
                st.success("Accès Admin mis à jour !")

    elif adm_nav == "Configuration Système":
        st.header("📢 MESSAGE DÉFILANT")
        new_m = st.text_area("Texte du Marquee", marquee_val)
        if st.button("SAUVEGARDER"):
            db_query("UPDATE sys_config SET marquee_text=? WHERE id=1", (new_m,), is_select=False); st.rerun()

    if adm_nav == "Déconnexion": st.session_state.titan_session['logged'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR (CORE ERP)
# ------------------------------------------------------------------------------
# Récupération Info Boutique
sid = st.session_state.titan_session['shop']
shop_raw = db_query("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,))
s_inf = shop_raw[0] if shop_raw else ("MA NOUVELLE BOUTIQUE", 2800.0, "BIENVENUE CHEZ NOUS", "ADRESSE", "000")

# Menu de navigation
if st.session_state.titan_session['role'] == "GERANT":
    menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 GESTION STOCK", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    menu = ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📉 SUIVI DETTES", "📊 RAPPORTS VENTES", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div style='background:#0044ff; color:white; padding:20px; border-radius:15px; text-align:center;'>🏪 {s_inf[0]}<br>👤 {st.session_state.titan_session['uid'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU TITAN", menu)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='titan-clock-container'>
        <p class='titan-time'>{datetime.now().strftime('%H:%M')}</p>
        <p class='titan-date'>{datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    t_date = datetime.now().strftime("%d/%m/%Y")
    day_rev = db_query("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (sid, t_date))[0][0] or 0
    st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h2>RECETTE DU JOUR</h2><h1 style='font-size:70px;'>{day_rev:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (PANIER DYNAMIQUE & DOUBLE FACTURE) ---
elif choice == "🛒 CAISSE TACTILE":
    if not st.session_state.titan_session['last_inv']:
        st.header("🛒 TERMINAL DE VENTE")
        c1, c2 = st.columns([2, 1])
        
        with c2:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            cur = st.radio("DEVISE", ["USD", "CDF"], horizontal=True)
            tx = s_inf[1]
            st.write(f"Taux : **1$ = {tx:,.0f} CDF**")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with c1:
            stock_items = db_query("SELECT item, sell_price, qty FROM stock WHERE sid=?", (sid,))
            st_map = {r[0]: (r[1], r[2]) for r in stock_items}
            search = st.selectbox("🔍 RECHERCHER UN PRODUIT", ["---"] + list(st_map.keys()))
            if search != "---" and st_map[search][1] > 0:
                if st.button("➕ AJOUTER"):
                    st.session_state.titan_session['cart'][search] = st.session_state.titan_session['cart'].get(search, 0) + 1
                    st.toast(f"{search} ajouté")

        if st.session_state.titan_session['cart']:
            st.divider()
            total_cart = 0.0; cart_rows = []
            
            for item, qty in list(st.session_state.titan_session['cart'].items()):
                p_u = st_map[item][0] if cur == "USD" else st_map[item][0] * tx
                
                # MODIFICATION DE LA QTÉ DANS LE PANIER
                cx, cq, cr = st.columns([3, 2, 1])
                new_q = cq.number_input(f"Qté {item}", min_value=1, max_value=st_map[item][1], value=qty, key=f"q_{item}")
                st.session_state.titan_session['cart'][item] = new_q
                
                sub = p_u * new_q
                total_cart += sub
                cart_rows.append({"n": item, "q": new_q, "p": p_u, "s": sub, "p_u_usd": st_map[item][0]})
                
                cx.markdown(f"**{item}**")
                if cr.button("🗑️", key=f"rm_{item}"):
                    del st.session_state.titan_session['cart'][item]; st.rerun()

            st.markdown(f"<div class='neon-frame-box'><div class='neon-price'>{total_cart:,.2f} {cur}</div></div>", unsafe_allow_html=True)
            
            with st.form("pay_form"):
                cli_nam = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                amount_p = st.number_input(f"MONTANT REÇU ({cur})", value=float(total_cart))
                if st.form_submit_button("🚀 VALIDER & IMPRIMER"):
                    ref_f = f"FAC-{random.randint(10000, 99999)}"
                    d, t = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    t_usd = total_cart if cur == "USD" else total_cart / tx
                    p_usd = amount_p if cur == "USD" else amount_p / tx
                    r_usd = t_usd - p_usd
                    
                    # Sauvegarde Vente
                    db_query("INSERT INTO sales (ref, cli, tot, pay, res, date, time, seller, sid, data, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (ref_f, cli_nam, t_usd, p_usd, r_usd, d, t, st.session_state.titan_session['uid'], sid, json.dumps(cart_rows), cur), is_select=False)
                    
                    # Mise à jour Stock
                    for row in cart_rows:
                        db_query("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (row['q'], row['n'], sid), is_select=False)
                    
                    # Gestion Dette
                    if r_usd > 0.01:
                        db_query("INSERT INTO debts (cli, bal, ref, sid, last_update) VALUES (?,?,?,?,?)", (cli_nam, r_usd, ref_f, sid, d), is_select=False)
                    
                    st.session_state.titan_session['last_inv'] = {"ref": ref_f, "cli": cli_nam, "tot": total_cart, "pay": amount_p, "res": total_cart-amount_p, "dev": cur, "items": cart_rows, "d": d, "t": t}
                    st.session_state.titan_session['cart'] = {}; st.rerun()
    else:
        # FACTURE SAUVEGARDÉE - DOUBLE FORMAT
        inv = st.session_state.titan_session['last_inv']
        fmt = st.radio("SÉLECTIONNER LE FORMAT DE FACTURE :", ["TICKET CAISSE (80mm)", "FACTURE ADMINISTRATIVE (A4)"], horizontal=True)
        
        if fmt == "TICKET CAISSE (80mm)":
            st.markdown(f"""
            <div class='receipt-80mm'>
                <h3 style='text-align:center;'>{s_inf[0]}</h3>
                <p style='text-align:center; font-size:11px;'>{s_inf[3]}<br>Tél: {s_inf[4]}</p>
                <hr>
                <p>N°: {inv['ref']}<br>CLIENT: {inv['cli']}<br>DATE: {inv['d']} à {inv['t']}</p>
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
            <div class='receipt-A4-admin'>
                <table style='width:100%'><tr>
                    <td><h1 style='color:#0044ff;'>{s_inf[0]}</h1><p>{s_inf[3]}<br>Tél: {s_inf[4]}</p></td>
                    <td style='text-align:right;'><h2>FACTURE ADMINISTRATIVE</h2><p>N° {inv['ref']}<br>Date: {inv['d']}</p></td>
                </tr></table>
                <hr>
                <p style='margin-top:20px;'><b>CLIENT :</b> {inv['cli']}</p>
                <table class='table-a4'>
                    <tr style='background:#f2f2f2;'><th>DESIGNATION</th><th>QUANTITÉ</th><th>PRIX UNITAIRE</th><th>TOTAL</th></tr>
                    {"".join([f"<tr><td>{x['n']}</td><td>{x['q']}</td><td>{x['p']:,.2f}</td><td>{x['s']:,.2f}</td></tr>" for x in inv['items']])}
                </table>
                <div style='text-align:right; margin-top:30px;'>
                    <h3>TOTAL GÉNÉRAL : {inv['tot']:,.2f} {inv['dev']}</h3>
                    <p><b>Somme payée :</b> {inv['pay']:,.2f} {inv['dev']}</p>
                    <p><b>Reste à payer :</b> {inv['res']:,.2f} {inv['dev']}</p>
                </div>
                <div style='margin-top:50px;'>
                    <p><i>Note: {s_inf[2]}</i></p>
                    <table style='width:100%; margin-top:100px;'><tr>
                        <td><b>Signature du Client</b><br><br>____________________</td>
                        <td style='text-align:right;'><b>Pour l'Établissement</b><br><br>____________________</td>
                    </tr></table>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("⬅️ RETOUR À LA CAISSE"):
            st.session_state.titan_session['last_inv'] = None; st.rerun()

# --- 6.3 GESTION STOCK (PRODUITS & PRIX) ---
elif choice == "📦 GESTION STOCK":
    st.header("📦 INVENTAIRE & PRODUITS")
    t1, t2 = st.tabs(["📋 LISTE DU STOCK", "➕ AJOUTER / MODIFIER"])
    
    with t1:
        st_data = db_query("SELECT id, item, qty, buy_price, sell_price, category FROM stock WHERE sid=?", (sid,))
        if st_data:
            df_st = pd.DataFrame(st_data, columns=["ID", "DÉSIGNATION", "QTÉ", "P. ACHAT ($)", "P. VENTE ($)", "CATÉGORIE"])
            st.dataframe(df_st, use_container_width=True, hide_index=True)
            
            st.divider()
            id_del = st.number_input("Entrez l'ID pour supprimer", min_value=0, step=1)
            if st.button("🗑️ SUPPRIMER DÉFINITIVEMENT"):
                db_query("DELETE FROM stock WHERE id=? AND sid=?", (id_del, sid), is_select=False); st.rerun()
        else:
            st.info("Le stock est actuellement vide.")

    with t2:
        with st.form("stock_titan"):
            f_id = st.number_input("ID (0 pour nouveau)", min_value=0)
            f_nam = st.text_input("Désignation").upper()
            f_cat = st.text_input("Catégorie (Optionnel)").upper()
            f_qty = st.number_input("Quantité en stock", min_value=0)
            f_buy = st.number_input("Prix d'Achat USD", min_value=0.0)
            f_sel = st.number_input("Prix de Vente USD", min_value=0.0)
            if st.form_submit_button("💾 ENREGISTRER"):
                if f_id == 0:
                    db_query("INSERT INTO stock (item, qty, buy_price, sell_price, sid, category) VALUES (?,?,?,?,?,?)",
                            (f_nam, f_qty, f_buy, f_sel, sid, f_cat), is_select=False)
                else:
                    db_query("UPDATE stock SET item=?, qty=?, buy_price=?, sell_price=?, category=? WHERE id=? AND sid=?",
                            (f_nam, f_qty, f_buy, f_sel, f_cat, f_id, sid), is_select=False)
                st.rerun()

# --- 6.4 SUIVI DETTES (VERSEMENTS) ---
elif choice == "📉 SUIVI DETTES":
    st.header("📉 CLIENTS DÉBITEURS")
    dettes_list = db_query("SELECT id, cli, bal, ref, last_update FROM debts WHERE sid=? AND status='OUVERT'", (sid,))
    if not dettes_list:
        st.success("Toutes les dettes sont payées ! ✅")
    else:
        for d_id, d_cli, d_bal, d_ref, d_up in dettes_list:
            with st.container():
                st.markdown(f"<div class='cobalt-card'><h3>👤 {d_cli}</h3><p>Reste : <b>{d_bal:,.2f} $</b> | Ref: {d_ref} | Date: {d_up}</p></div>", unsafe_allow_html=True)
                v_pay = st.number_input(f"Verser pour {d_cli}", min_value=0.0, max_value=float(d_bal), key=f"pay_{d_id}")
                if st.button(f"VALIDER LE VERSEMENT {d_id}", key=f"btn_{d_id}"):
                    new_bal = d_bal - v_pay
                    if new_bal <= 0.01:
                        db_query("UPDATE debts SET bal=0, status='PAYE' WHERE id=?", (d_id,), is_select=False)
                    else:
                        db_query("UPDATE debts SET bal=?, last_update=? WHERE id=?", (new_bal, datetime.now().strftime("%d/%m/%Y"), d_id), is_select=False)
                    st.rerun()

# --- 6.5 RAPPORTS VENTES & EXCEL ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 ANALYSE DES VENTES")
    r_date = st.date_input("Sélectionner la date", datetime.now()).strftime("%d/%m/%Y")
    sales_rep = db_query("SELECT ref, cli, tot, seller, time, currency FROM sales WHERE sid=? AND date=? ORDER BY id DESC", (sid, r_date))
    
    if sales_rep:
        df_rep = pd.DataFrame(sales_rep, columns=["RÉFÉRENCE", "CLIENT", "TOTAL ($)", "VENDEUR", "HEURE", "DEVISE"])
        st.table(df_rep)
        total_d = df_rep["TOTAL ($)"].sum()
        st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h2>RECETTE TOTALE : {total_d:,.2f} $</h2></div>", unsafe_allow_html=True)
        
        # EXPORT EXCEL TITAN
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, index=False, sheet_name='Ventes_Jour')
        st.download_button("📥 TÉLÉCHARGER LE RAPPORT EXCEL", data=buf.getvalue(), file_name=f"Rapport_Ventes_{r_date}.xlsx")
    else:
        st.info("Aucune vente enregistrée pour cette journée.")

# --- 6.6 GESTION ÉQUIPE (VENDEURS) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 MON ÉQUIPE DE VENTE")
    with st.form("add_vend"):
        v_id = st.text_input("Identifiant Vendeur").lower().strip()
        v_nm = st.text_input("Nom Complet")
        v_pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("AJOUTER LE VENDEUR"):
            v_h = hashlib.sha256(v_pw.encode()).hexdigest()
            db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                    (v_id, v_h, 'VENDEUR', sid, 'ACTIF', v_nm, '000', str(datetime.now())), is_select=False)
            st.rerun()
    
    st.divider()
    vend_list = db_query("SELECT uid, name, status FROM users WHERE shop=? AND role='VENDEUR'", (sid,))
    for vu, vn, vs in vend_list:
        st.write(f"👤 {vn} (@{vu}) - Statut: {vs}")
        if st.button(f"Supprimer {vu}", key=f"dv_{vu}"):
            db_query("DELETE FROM users WHERE uid=?", (vu,), is_select=False); st.rerun()

# --- 6.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("titan_settings"):
        s_n = st.text_input("Nom de l'Enseigne", s_inf[0])
        s_r = st.number_input("Taux de Change (CDF/USD)", s_inf[1])
        s_h = st.text_input("En-tête de Facture", s_inf[2])
        s_a = st.text_input("Adresse", s_inf[3])
        s_t = st.text_input("Téléphone", s_inf[4])
        if st.form_submit_button("💾 SAUVEGARDER LES PARAMÈTRES"):
            if not shop_raw:
                db_query("INSERT INTO shops (sid, name, owner, rate, head, addr, tel) VALUES (?,?,?,?,?,?,?)",
                        (sid, s_n, st.session_state.titan_session['uid'], s_r, s_h, s_a, s_t), is_select=False)
            else:
                db_query("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?",
                        (s_n, s_r, s_h, s_a, s_t, sid), is_select=False)
            st.success("Paramètres mis à jour !")
            st.rerun()

# --- 6.8 DÉCONNEXION ---
elif choice == "🚪 QUITTER":
    st.session_state.titan_session['logged'] = False
    st.rerun()

# ==============================================================================
# LOGIQUE DE SAUVEGARDE AUTOMATIQUE DES FACTURES (SIMULÉ)
# ==============================================================================
# Chaque vente génère un JSON stocké dans la colonne 'data' pour une ré-impression future.
# Le système est optimisé pour les écrans tactiles de smartphone (Boutons XXL).
# ==============================================================================
