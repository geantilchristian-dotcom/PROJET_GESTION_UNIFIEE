# ==============================================================================
# ANASH ERP v3318 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL MASTER)
# ------------------------------------------------------------------------------
# INTERFACE SÉCURISÉE | GESTION DE STOCK | CAISSE MULTI-DEVISES | FACTURATION PHOTO
# ------------------------------------------------------------------------------
# RÈGLE STRICTE : AUCUNE LIGNE SUPPRIMÉE. ACCUMULATION DE FONCTIONNALITÉS.
# DÉVELOPPÉ POUR : USAGE SUR SMARTPHONE ET ORDINATEUR
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import random
import time
import io
import base64
from PIL import Image

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES (STRUCTURE GLOBALE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3318_master.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table de Configuration du Système
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee_text TEXT,
            marquee_active INTEGER DEFAULT 1,
            selected_theme TEXT DEFAULT 'COBALT',
            current_version TEXT)""")
        
        # Table des Utilisateurs (Admin, Gérants, Vendeurs)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop_id TEXT, 
            status TEXT, 
            full_name TEXT, 
            phone TEXT,
            reg_date TEXT)""")
        
        # Table des Boutiques (Profils détaillés)
        cursor.execute("""CREATE TABLE IF NOT EXISTS stores (
            sid TEXT PRIMARY KEY, 
            store_name TEXT, 
            manager TEXT, 
            rate_cdf REAL DEFAULT 2800.0, 
            header_info TEXT, 
            address TEXT, 
            contact TEXT, 
            rccm TEXT, 
            idnat TEXT, 
            email TEXT,
            profile_pic BLOB)""")
        
        # Table du Stock / Inventaire
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            product_name TEXT, 
            stock_qty INTEGER, 
            purchase_price REAL, 
            selling_price REAL, 
            sid TEXT, 
            category TEXT,
            min_alert INTEGER DEFAULT 5)""")
        
        # Table des Ventes (Historique complet)
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            invoice_ref TEXT, 
            customer_name TEXT, 
            total_usd REAL, 
            paid_amount REAL, 
            debt_remaining REAL, 
            sale_date TEXT, 
            sale_time TEXT, 
            seller_id TEXT, 
            sid TEXT, 
            items_data TEXT, 
            currency TEXT,
            exchange_rate REAL)""")
        
        # Table des paiements de dettes (Échelonnement)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debt_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            sale_ref TEXT, 
            amount_paid REAL, 
            payment_date TEXT, 
            sid TEXT)""")

        # Données de démarrage
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE CHEZ BALIKA BUSINESS - GESTION PROFESSIONNELLE', 1, 'COBALT', '3.3.18')")
        
        cursor.execute("SELECT uid FROM users WHERE role='SUPER_ADMIN'")
        if not cursor.fetchone():
            master_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', master_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR MASTER', '000', '01/01/2026'))
        
        conn.commit()

init_db()

# ------------------------------------------------------------------------------
# 2. MOTEUR DE DESIGN ET THÈMES (CSS PERSONNALISÉ INTÉGRAL)
# ------------------------------------------------------------------------------
def load_theme(theme_name):
    themes = {
        'COBALT': {"bg": "linear-gradient(135deg, #001a33 0%, #000a1a 100%)", "card": "#002b4d", "accent": "#00d9ff", "text": "#ffffff"},
        'DARK_PREMIUM': {"bg": "#000000", "card": "#121212", "accent": "#ffffff", "text": "#ffffff"},
        'GOLD_EDITION': {"bg": "#0d0d0d", "card": "#1a1a1a", "accent": "#ffd700", "text": "#ffffff"},
        'MATRIX': {"bg": "#000000", "card": "#001a00", "accent": "#00ff41", "text": "#00ff41"},
        'SOFT_BLUE': {"bg": "#f0f2f6", "card": "#ffffff", "accent": "#007bff", "text": "#000000"},
        'ARDOISE': {"bg": "#2c3e50", "card": "#34495e", "accent": "#e67e22", "text": "#ffffff"},
        'SOLARIZED': {"bg": "#fdf6e3", "card": "#eee8d5", "accent": "#b58900", "text": "#073642"},
        'PURPLE_VIBE': {"bg": "#1a0033", "card": "#2d004d", "accent": "#bf00ff", "text": "#ffffff"},
        'APPLE_WHITE': {"bg": "#ffffff", "card": "#f5f5f7", "accent": "#007aff", "text": "#1d1d1f"},
        'RED_EXTREME': {"bg": "#1a0000", "card": "#330000", "accent": "#ff4b4b", "text": "#ffffff"}
    }
    t = themes.get(theme_name, themes['COBALT'])
    
    st.markdown(f"""
    <style>
        .stApp {{ background: {t['bg']}; color: {t['text']} !important; }}
        [data-testid="stSidebar"] {{ background-color: white !important; border-right: 4px solid {t['accent']}; }}
        [data-testid="stSidebar"] * {{ color: black !important; font-weight: bold; }}
        
        .stat-card {{ 
            background: {t['card']}; border-left: 8px solid {t['accent']}; 
            padding: 25px; border-radius: 15px; margin-bottom: 20px;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        }}
        .stat-card h1, .stat-card h3 {{ margin: 0; color: {t['text']} !important; }}

        .price-frame {{ 
            border: 5px solid {t['accent']}; padding: 25px; border-radius: 20px; 
            text-align: center; background: rgba(0,0,0,0.5); margin: 25px 0;
            box-shadow: 0px 0px 20px {t['accent']};
        }}
        .price-text {{ color: {t['accent']}; font-size: 55px; font-weight: 900; }}
        
        .stButton > button {{ 
            width: 100%; height: 60px; border-radius: 12px; font-weight: bold; font-size: 18px;
            background: {t['card']}; color: white; border: 2px solid {t['accent']};
            transition: 0.3s;
        }}
        .stButton > button:hover {{ background: {t['accent']}; color: black; transform: scale(1.02); }}
        
        /* STYLE FACTURE PHOTO AMÉLIORÉ */
        .photo-invoice {{ 
            background: white; color: black; padding: 40px; border: 2px solid #000;
            width: 210mm; min-height: 150mm; margin: auto; font-family: 'Courier New', Courier, monospace;
        }}
        .invoice-head {{ text-align: center; border-bottom: 4px double black; padding-bottom: 15px; margin-bottom: 20px; }}
        .invoice-table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
        .invoice-table th {{ background: #000; color: #fff; border: 1px solid black; padding: 12px; }}
        .invoice-table td {{ border: 1px solid black; padding: 12px; text-align: center; font-weight: bold; }}
        .invoice-footer {{ margin-top: 30px; border-top: 2px solid black; padding-top: 10px; text-align: right; }}

        /* FIX POUR MOBILE */
        @media (max-width: 600px) {{
            .price-text {{ font-size: 35px; }}
            .photo-invoice {{ width: 100%; padding: 10px; }}
        }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. FONCTIONS UTILITAIRES (IMAGES, MOTS DE PASSE)
# ------------------------------------------------------------------------------
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def get_image_base64(binary_data):
    if binary_data:
        return f"data:image/png;base64,{base64.b64encode(binary_data).decode()}"
    return None

# ------------------------------------------------------------------------------
# 4. ÉTAT DE LA SESSION
# ------------------------------------------------------------------------------
if 'state' not in st.session_state:
    st.session_state.state = {
        'logged': False, 'user': None, 'role': None, 
        'shop': None, 'cart': {}, 'invoice': None, 'name': ""
    }

def fetch_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_text, marquee_active, selected_theme FROM system_config WHERE id=1").fetchone()

APP_NAME, MARQUEE_TXT, MARQUEE_ON, THEME_ACTIF = fetch_config()
load_theme(THEME_ACTIF)

# ------------------------------------------------------------------------------
# 5. SYSTÈME DE CONNEXION ET INSCRIPTION (INTERFACE INITIALE)
# ------------------------------------------------------------------------------
if not st.session_state.state['logged']:
    if MARQUEE_ON == 1:
        st.markdown(f"<div style='background:black; color:lime; padding:10px; font-weight:bold; border-bottom:2px solid lime;'><marquee>🌟 {MARQUEE_TXT} 🌟</marquee></div>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='text-align:center; padding:40px; font-size:50px;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
    
    _, central_col, _ = st.columns([1,3,1])
    with central_col:
        t_log, t_reg = st.tabs(["🔒 ACCÈS UTILISATEUR", "🚀 CRÉATION BUSINESS"])
        
        with t_log:
            with st.form("login_form"):
                u_input = st.text_input("Identifiant").lower().strip()
                p_input = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("SE CONNECTER AU TERMINAL"):
                    with sqlite3.connect(DB_FILE) as conn:
                        res = conn.execute("SELECT pwd, role, shop_id, status, full_name FROM users WHERE uid=?", (u_input,)).fetchone()
                        if res and res[0] == hash_pass(p_input):
                            if res[3] == "ACTIF":
                                st.session_state.state.update({'logged': True, 'user': u_input, 'role': res[1], 'shop': res[2], 'name': res[4]})
                                st.rerun()
                            else: st.error("Compte en attente de validation.")
                        else: st.error("Identifiants incorrects.")
        
        with t_reg:
            st.info("Devenez partenaire Balika Business. Remplissez ce formulaire.")
            with st.form("signup_form"):
                r_uid = st.text_input("ID Admin souhaité").lower().strip()
                r_name = st.text_input("Nom de votre Boutique / Société")
                r_pass = st.text_input("Mot de passe de sécurité", type="password")
                r_tel = st.text_input("Numéro WhatsApp")
                if st.form_submit_button("ENVOYER MA DEMANDE"):
                    if r_uid and r_pass:
                        with sqlite3.connect(DB_FILE) as conn:
                            try:
                                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                           (r_uid, hash_pass(r_pass), 'GERANT', 'ATTENTE', 'ATTENTE', r_name, r_tel, datetime.now().strftime("%d/%m/%Y")))
                                conn.commit(); st.success("Demande transmise à l'Administration Master.")
                            except: st.error("Cet identifiant est déjà utilisé.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMIN (PANEL DE CONTRÔLE CENTRAL)
# ------------------------------------------------------------------------------
if st.session_state.state['role'] == "SUPER_ADMIN":
    st.sidebar.markdown("<div style='background:red; color:white; padding:10px; border-radius:5px; text-align:center;'>MODE MASTER</div>", unsafe_allow_html=True)
    adm_choice = st.sidebar.radio("Menu Master", ["Validations Boss", "Audit Boutiques", "Configuration Système", "Sécurité Admin", "Quitter"])
    
    if adm_choice == "Validations Boss":
        st.header("⏳ DEMANDES EN ATTENTE")
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute("SELECT uid, full_name, phone, reg_date FROM users WHERE status='ATTENTE'").fetchall()
            if not data: st.info("Aucun nouveau dossier.")
            for u, n, t, d in data:
                with st.expander(f"DOSSIER: {n} (@{u})"):
                    st.write(f"📱 Tél: {t} | 📅 Date: {d}")
                    if st.button(f"APPROUVER {u}"):
                        conn.execute("UPDATE users SET status='ACTIF', shop_id=? WHERE uid=?", (u, u))
                        conn.execute("INSERT OR IGNORE INTO stores (sid, store_name, manager) VALUES (?,?,?)", (u, n, u))
                        conn.commit(); st.success(f"Boutique {u} activée !"); st.rerun()

    elif adm_choice == "Configuration Système":
        st.header("⚙️ RÉGLAGES GLOBAUX")
        with st.form("global_cfg"):
            n_title = st.text_input("Nom de l'ERP", APP_NAME)
            n_theme = st.selectbox("Ambiance Visuelle", ['COBALT', 'DARK_PREMIUM', 'GOLD_EDITION', 'MATRIX', 'SOFT_BLUE', 'ARDOISE', 'SOLARIZED', 'PURPLE_VIBE', 'APPLE_WHITE', 'RED_EXTREME'])
            n_marquee = st.text_area("Texte Défilant", MARQUEE_TXT)
            m_status = st.checkbox("Activer le Marquee", value=(MARQUEE_ON == 1))
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee_text=?, selected_theme=?, marquee_active=? WHERE id=1", 
                               (n_title, n_marquee, n_theme, 1 if m_status else 0))
                    conn.commit(); st.success("Modifications appliquées !"); st.rerun()

    elif adm_choice == "Sécurité Admin":
        st.header("👤 COMPTE MASTER")
        with st.form("sec_admin"):
            old_u = st.session_state.state['user']
            new_u = st.text_input("Nouvel ID Master", value=old_u)
            new_p = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("CHANGER MES ACCÈS"):
                if len(new_p) >= 4:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("DELETE FROM users WHERE uid=?", (old_u,))
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                   (new_u, hash_pass(new_p), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMIN MASTER', '000', '2026'))
                        conn.commit()
                    st.success("Accès modifiés. Reconnectez-vous."); st.session_state.state['logged'] = False; st.rerun()

    elif adm_choice == "Quitter":
        st.session_state.state['logged'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE MÉTIER (BOUTIQUES & VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.state['shop']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT store_name, rate_cdf, header_info, address, contact, rccm, idnat, email, profile_pic FROM stores WHERE sid=?", (sid,)).fetchone()

# Construction du menu selon le rôle
if st.session_state.state['role'] == "GERANT":
    nav = ["🏠 DASHBOARD", "🛒 CAISSE TACTILE", "📦 INVENTAIRE", "📉 PAIEMENTS CLIENTS", "📊 ANALYSE VENTES", "👥 ÉQUIPE VENDEURS", "⚙️ PARAMÈTRES BOUTIQUE", "🚪 DÉCONNEXION"]
else:
    nav = ["🏠 DASHBOARD", "🛒 CAISSE TACTILE", "📉 PAIEMENTS CLIENTS", "📊 ANALYSE VENTES", "🚪 DÉCONNEXION"]

with st.sidebar:
    # Affichage Logo si présent
    if shop_data[8]:
        st.image(shop_data[8], width=100)
    st.markdown(f"<div style='padding:10px; background:#eee; color:black; border-radius:10px; text-align:center;'><b>{shop_data[0]}</b><br><small>Taux: {shop_data[1]} CDF</small></div>", unsafe_allow_html=True)
    user_choice = st.radio("NAVIGATION", nav)

# --- 7.1 DASHBOARD ---
if user_choice == "🏠 DASHBOARD":
    if MARQUEE_ON == 1:
        st.markdown(f"<marquee style='color:orange; font-weight:bold;'>{MARQUEE_TXT}</marquee>", unsafe_allow_html=True)
    
    # Horloge XXL et Date
    st.markdown(f"""
    <div style="text-align:center; padding:60px 0;">
        <h1 style="font-size:130px; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
        <h3 style="color:#888;">{datetime.now().strftime('%A, %d %B %Y')}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        v_jr = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND sale_date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        d_tt = conn.execute("SELECT SUM(debt_remaining) FROM sales WHERE sid=? AND debt_remaining > 0", (sid,)).fetchone()[0] or 0
        s_low = conn.execute("SELECT COUNT(*) FROM inventory WHERE sid=? AND stock_qty <= min_alert", (sid,)).fetchone()[0]
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='stat-card'><h3>VENTES/JOUR</h3><h1>{v_jr:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-card' style='border-left-color:orange;'><h3>CRÉANCES</h3><h1>{d_tt:,.2f} $</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-card' style='border-left-color:red;'><h3>ALERTES STOCK</h3><h1>{s_low}</h1></div>", unsafe_allow_html=True)

# --- 7.2 CAISSE TACTILE (AVEC FACTURE PHOTO A4/80MM) ---
elif user_choice == "🛒 CAISSE TACTILE":
    if st.session_state.state['invoice']:
        inv = st.session_state.state['invoice']
        f_mode = st.radio("CHOIX DU FORMAT", ["PHOTO A4", "TICKET 80mm"], horizontal=True)
        
        if f_mode == "PHOTO A4":
            st.markdown(f"""
            <div class="photo-invoice">
                <div class="invoice-head">
                    <h1 style="font-size:35px;">{shop_data[0].upper()}</h1>
                    <p>{shop_data[3]} | Tél: {shop_data[4]}<br>RCCM: {shop_data[5]} | IDNAT: {shop_data[6]}</p>
                    <hr style="border:1px solid #000;">
                    <h2 style="text-decoration:underline;">FACTURE OFFICIELLE N° {inv['ref']}</h2>
                    <div style="text-align:left; font-size:18px;">
                        DATE : <b>{inv['date']}</b><br>CLIENT : <b>{inv['cli']}</b>
                    </div>
                </div>
                <table class="invoice-table">
                    <tr><th>ARTICLE</th><th>QTÉ</th><th>P.U ({inv['devise']})</th><th>TOTAL</th></tr>
                    {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['p']:,.2f}</td><td>{(v['q']*v['p']):,.2f}</td></tr>" for k,v in inv['items'].items()])}
                </table>
                <div class="invoice-footer">
                    <h2 style="font-size:28px;">NET À PAYER : {inv['total']:,.2f} {inv['devise']}</h2>
                    <p>Montant Payé : {inv['paid']:,.2f} | Reste à Payer : {inv['rest']:,.2f}</p>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:60px; font-weight:bold; border:1px dashed #000; padding:10px;">
                    <div style="text-align:center;">SIGNATURE CLIENT<br><br><br>...................</div>
                    <div style="text-align:center;">CACHET DIRECTION<br><br><br>...................</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <center><div style="width:80mm; background:white; color:black; padding:15px; font-family:monospace; text-align:left; border:1px solid #000;">
                <h2 style="text-align:center;">{shop_data[0]}</h2>
                <hr>Ref: {inv['ref']}<br>Date: {inv['date']}<hr>
                {"".join([f"{k} x{v['q']} : {(v['q']*v['p']):,.2f}<br>" for k,v in inv['items'].items()])}
                <hr><b>TOTAL : {inv['total']:,.2f} {inv['devise']}</b><br><center>MERCI DE VOTRE CONFIANCE</center>
            </div></center>
            """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("🔄 NOUVELLE VENTE"): st.session_state.state['invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRESSION"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        
    else:
        st.header("🛒 TERMINAL DE VENTE")
        tx = shop_data[1]
        c_dev, c_tx = st.columns(2)
        devise = c_dev.selectbox("DEVISE DE TRANSACTION", ["USD", "CDF"])
        c_tx.metric("TAUX DU JOUR", f"{tx} CDF")
        
        with sqlite3.connect(DB_FILE) as conn:
            stock = conn.execute("SELECT product_name, selling_price, stock_qty FROM inventory WHERE sid=? AND stock_qty > 0", (sid,)).fetchall()
            search_item = st.selectbox("RECHERCHER UN ARTICLE", ["---"] + [f"{s[0]} ({s[1]}$)" for s in stock])
            
            if search_item != "---":
                name_p = search_item.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    p_info = conn.execute("SELECT selling_price, stock_qty FROM inventory WHERE product_name=? AND sid=?", (name_p, sid)).fetchone()
                    st.session_state.state['cart'][name_p] = {'p': p_info[0], 'q': 1, 'max': p_info[1]}
                    st.rerun()

        if st.session_state.state['cart']:
            st.divider()
            t_usd = 0
            for k, v in list(st.session_state.state['cart'].items()):
                cc1, cc2, cc3 = st.columns([3, 2, 1])
                v['q'] = cc2.number_input(f"Qté {k}", 1, v['max'], v['q'], key=f"q_{k}")
                t_usd += v['p'] * v['q']
                if cc3.button("🗑️", key=f"del_{k}"): del st.session_state.state['cart'][k]; st.rerun()
            
            total_final = t_usd if devise == "USD" else t_usd * tx
            st.markdown(f"<div class='price-frame'><div style='color:white; font-size:20px;'>SOMME TOTAL À PAYER</div><div class='price-text'>{total_final:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("validation_vente"):
                nom_client = st.text_input("NOM DU CLIENT", "CLIENT DE PASSAGE").upper()
                versement = st.number_input(f"MONTANT REÇU EN {devise}", value=float(total_final))
                if st.form_submit_button("✅ VALIDER ET ÉDITER FACTURE"):
                    v_usd = versement if devise == "USD" else versement / tx
                    r_usd = t_usd - v_usd
                    v_ref = f"BL-FACT-{random.randint(1000, 9999)}"
                    now_d = datetime.now().strftime("%d/%m/%Y")
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (invoice_ref, customer_name, total_usd, paid_amount, debt_remaining, sale_date, sale_time, seller_id, sid, items_data, currency, exchange_rate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (v_ref, nom_client, t_usd, v_usd, r_usd, now_d, datetime.now().strftime("%H:%M"), st.session_state.state['user'], sid, json.dumps(st.session_state.state['cart']), devise, tx))
                        for it, obj in st.session_state.state['cart'].items():
                            conn.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE product_name=? AND sid=?", (obj['q'], it, sid))
                        conn.commit()
                    
                    st.session_state.state['invoice'] = {'ref': v_ref, 'cli': nom_client, 'total': total_final, 'paid': versement, 'rest': total_final - versement, 'date': now_d, 'items': st.session_state.state['cart'], 'devise': devise}
                    st.session_state.state['cart'] = {}; st.rerun()

# --- 7.3 INVENTAIRE ---
elif user_choice == "📦 INVENTAIRE":
    st.header("📦 GESTION DU STOCK")
    with st.expander("➕ NOUVEL ARTICLE"):
        with st.form("add_stock"):
            st_name = st.text_input("Désignation").upper()
            st_cat = st.selectbox("Catégorie", ["DIVERS", "ALIMENTAIRE", "HABILLEMENT", "ÉLECTRONIQUE"])
            sc1, sc2, sc3 = st.columns(3)
            st_qty = sc1.number_input("Qté Initiale", 0)
            st_buy = sc2.number_input("Prix Achat ($)")
            st_sell = sc3.number_input("Prix Vente ($)")
            st_min = st.number_input("Seuil d'alerte", 5)
            if st.form_submit_button("ENREGISTRER AU STOCK"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (product_name, stock_qty, purchase_price, selling_price, sid, category, min_alert) VALUES (?,?,?,?,?,?,?)", (st_name, st_qty, st_buy, st_sell, sid, st_cat, st_min))
                    conn.commit(); st.success("Stock mis à jour !"); st.rerun()

    st.divider()
    with sqlite3.connect(DB_FILE) as conn:
        all_items = conn.execute("SELECT id, product_name, stock_qty, selling_price FROM inventory WHERE sid=? ORDER BY product_name ASC", (sid,)).fetchall()
        for i_id, i_name, i_qty, i_price in all_items:
            with st.expander(f"{i_name} | {i_qty} unités | {i_price} $"):
                with st.form(f"f_edit_{i_id}"):
                    u_q = st.number_input("Stock Réel", value=i_qty)
                    u_p = st.number_input("Prix de Vente ($)", value=i_price)
                    if st.form_submit_button("MODIFIER"):
                        conn.execute("UPDATE inventory SET stock_qty=?, selling_price=? WHERE id=?", (u_q, u_p, i_id))
                        conn.commit(); st.rerun()
                if st.button(f"🗑️ SUPPRIMER L'ARTICLE {i_name}", key=f"del_inv_{i_id}"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (i_id,)); conn.commit(); st.rerun()

# --- 7.4 PAIEMENTS CLIENTS (DETTES ÉCHELONNÉES) ---
elif user_choice == "📉 PAIEMENTS CLIENTS":
    st.header("📉 SUIVI DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        active_debts = conn.execute("SELECT id, customer_name, debt_remaining, invoice_ref FROM sales WHERE sid=? AND debt_remaining > 0.01", (sid,)).fetchall()
        if not active_debts: st.info("Aucune dette à recouvrer.")
        for d_id, d_name, d_rem, d_ref in active_debts:
            with st.expander(f"👤 {d_name} | RESTE : {d_rem:,.2f} $ (Facture: {d_ref})"):
                v_montant = st.number_input(f"Montant versé ($)", 0.0, d_rem, key=f"v_{d_id}")
                if st.button("VALIDER LE PAIEMENT", key=f"bv_{d_id}"):
                    new_debt = d_rem - v_montant
                    conn.execute("UPDATE sales SET debt_remaining=? WHERE id=?", (new_debt, d_id))
                    conn.execute("INSERT INTO debt_payments (sale_ref, amount_paid, payment_date, sid) VALUES (?,?,?,?)", (d_ref, v_montant, datetime.now().strftime("%d/%m/%Y"), sid))
                    conn.commit(); st.success("Versement enregistré !"); st.rerun()

# --- 7.5 ANALYSE VENTES ---
elif user_choice == "📊 ANALYSE VENTES":
    st.header("📊 ÉTAT DES VENTES")
    f_date = st.date_input("Date du Rapport", datetime.now())
    target_d = f_date.strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        s_data = conn.execute("SELECT invoice_ref, customer_name, total_usd, paid_amount, debt_remaining, seller_id, sale_time FROM sales WHERE sid=? AND sale_date=?", (sid, target_d)).fetchall()
        if s_data:
            df_v = pd.DataFrame(s_data, columns=["FACTURE", "CLIENT", "TOTAL ($)", "PAYÉ ($)", "DETTE ($)", "VENDEUR", "HEURE"])
            st.table(df_v)
            st.markdown(f"<div class='stat-card'><h3>TOTAL GÉNÉRAL : {df_v['TOTAL ($)'].sum():,.2f} $</h3></div>", unsafe_allow_html=True)
            if st.button("🖨️ IMPRIMER RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        else: st.warning("Pas d'activité ce jour.")

# --- 7.6 ÉQUIPE VENDEURS ---
elif user_choice == "👥 ÉQUIPE VENDEURS":
    st.header("👥 GESTION DES COMPTES")
    with st.form("add_user_form"):
        new_u_id = st.text_input("Identifiant Vendeur").lower().strip()
        new_u_name = st.text_input("Nom Complet")
        new_u_pass = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (new_u_id, hash_pass(new_u_pass), 'VENDEUR', sid, 'ACTIF', new_u_name, '', ''))
                    conn.commit(); st.success("Vendeur ajouté à l'équipe !")
                except: st.error("L'identifiant est déjà pris.")

# --- 7.7 PARAMÈTRES BOUTIQUE (PROFIL, PASS, LOGO) ---
elif user_choice == "⚙️ PARAMÈTRES BOUTIQUE":
    st.header("⚙️ CONFIGURATION ET SÉCURITÉ")
    
    t1, t2, t3 = st.tabs(["🏢 PROFIL BOUTIQUE", "🔐 SÉCURITÉ", "🖼️ LOGO"])
    
    with t1:
        with st.form("update_shop"):
            st_nom = st.text_input("Dénomination", shop_data[0])
            st_taux = st.number_input("Taux de change (CDF)", value=shop_data[1])
            st_adr = st.text_input("Adresse Physique", shop_data[3])
            st_cont = st.text_input("Contact Tél", shop_data[4])
            st_rc = st.text_input("RCCM", shop_data[5])
            st_idat = st.text_input("ID National", shop_data[6])
            if st.form_submit_button("SAUVEGARDER PROFIL"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE stores SET store_name=?, rate_cdf=?, address=?, contact=?, rccm=?, idnat=? WHERE sid=?", (st_nom, st_taux, st_adr, st_cont, st_rc, st_idat, sid))
                    conn.commit(); st.success("Boutique mise à jour !"); st.rerun()

    with t2:
        with st.form("update_pass"):
            curr_pass = st.text_input("Ancien Mot de Passe", type="password")
            new_pass1 = st.text_input("Nouveau Mot de Passe", type="password")
            new_pass2 = st.text_input("Confirmer Nouveau", type="password")
            if st.form_submit_button("CHANGER MOT DE PASSE"):
                if new_pass1 == new_pass2 and len(new_pass1) >= 4:
                    with sqlite3.connect(DB_FILE) as conn:
                        res = conn.execute("SELECT pwd FROM users WHERE uid=?", (st.session_state.state['user'],)).fetchone()
                        if res[0] == hash_pass(curr_pass):
                            conn.execute("UPDATE users SET pwd=? WHERE uid=?", (hash_pass(new_pass1), st.session_state.state['user']))
                            conn.commit(); st.success("Mot de passe modifié !")
                        else: st.error("Ancien mot de passe incorrect.")

    with t3:
        st.subheader("IMAGE DE PROFIL / LOGO")
        img_file = st.file_uploader("Choisir une image", type=['png', 'jpg', 'jpeg'])
        if img_file:
            img_bytes = img_file.read()
            if st.button("APPLIQUER LE LOGO"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE stores SET profile_pic=? WHERE sid=?", (img_bytes, sid))
                    conn.commit(); st.success("Logo enregistré !"); st.rerun()

elif user_choice == "🚪 DÉCONNEXION":
    st.session_state.state['logged'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE INTÉGRAL ANASH v3318
# ==============================================================================
