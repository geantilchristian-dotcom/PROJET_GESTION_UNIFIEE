# ==============================================================================
# ANASH ERP v310 - ÉDITION BALIKA BUSINESS (ULTRA-STABLE)
# ------------------------------------------------------------------------------
# - 20 THÈMES PERSONNALISABLES (ADMIN)
# - GESTION MARQUEE (ACTIVER/DÉSACTIVER)
# - SAUVEGARDE PDF AUTOMATIQUE
# - FACTURE OPTIMISÉE (TEXTE NOIR SUR BLANC)
# - SUPPRESSION ARTICLES & VENDEURS
# - TABLEAU D'INVENTAIRE COMPLET
# - PERMISSIONS VENDEUR RESTREINTES
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

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES MASTER
# ------------------------------------------------------------------------------
DB_FILE = "balika_v305_master.db"

def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table Configuration (Ajout colonne Theme et Marquee_Active)
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', marquee_active INTEGER DEFAULT 1)""")
        
        # Table Utilisateurs
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        
        # Table Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        
        # Table Inventaire
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT DEFAULT 'GENERAL')""")
        
        # Table Ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        
        # Table Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_update TEXT)""")
        
        # Table Logs
        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, date TEXT, time TEXT, sid TEXT)""")

        # Données de base
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '3.1.0', 'Cobalt', 1)")
        
        # Vérification colonne marquee_active (Migration si nécessaire)
        try:
            cursor.execute("ALTER TABLE system_config ADD COLUMN marquee_active INTEGER DEFAULT 1")
        except:
            pass

        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_master_db()

# ------------------------------------------------------------------------------
# 2. FONCTIONS DE SÉCURITÉ ET UTILITAIRES
# ------------------------------------------------------------------------------
def get_hash(p): return hashlib.sha256(p.encode()).hexdigest()

def log_event(u, a, s):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO audit_logs (user, action, date, time, sid) VALUES (?,?,?,?,?)",
                     (u, a, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S"), s))
        conn.commit()

def load_sys():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee, theme_id, marquee_active FROM system_config WHERE id=1").fetchone()

# ------------------------------------------------------------------------------
# 3. SYSTÈME DE THÈMES (20 VARIANTES)
# ------------------------------------------------------------------------------
THEMES = {
    "Cobalt": "linear-gradient(135deg, #004a99 0%, #002b5c 100%)",
    "Midnight": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    "Emerald": "linear-gradient(135deg, #004d40 0%, #00796b 100%)",
    "Sunset": "linear-gradient(135deg, #ff512f 0%, #dd2476 100%)",
    "Royal": "linear-gradient(135deg, #4b6cb7 0%, #182848 100%)",
    "Forest": "#1b5e20",
    "Bordeaux": "#880e4f",
    "Ocean": "linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)",
    "Purple Dream": "linear-gradient(135deg, #4568dc 0%, #b06ab3 100%)",
    "Luxury Gold": "linear-gradient(135deg, #bf953f 0%, #fcf6ba 50%, #b38728 100%)",
    "Carbon": "#212121",
    "Classic Blue": "#0d47a1",
    "Deep Space": "linear-gradient(135deg, #000000 0%, #434343 100%)",
    "Neon Green": "linear-gradient(135deg, #000000 0%, #00ff00 500%)",
    "Soft Rose": "linear-gradient(135deg, #f857a6 0%, #ff5858 100%)",
    "Vibrant Teal": "#008080",
    "Steel": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    "Cyberpunk": "linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%)",
    "Solar": "linear-gradient(135deg, #f2994a 0%, #f2c94c 100%)",
    "Silver": "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)"
}

# ------------------------------------------------------------------------------
# 4. INTERFACE ET STYLES
# ------------------------------------------------------------------------------
SYS_DATA = load_sys()
APP_NAME, MARQUEE_TEXT, CURRENT_THEME, MARQUEE_ON = SYS_DATA[0], SYS_DATA[1], SYS_DATA[2], SYS_DATA[3]
SELECTED_BG = THEMES.get(CURRENT_THEME, THEMES["Cobalt"])

st.set_page_config(page_title=APP_NAME, layout="wide")

def apply_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background: {SELECTED_BG}; color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid #00d4ff; }}
        h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
        
        /* Formulaires */
        input {{ text-align: center; border-radius: 10px !important; font-weight: bold; background-color: white !important; color: black !important; }}
        
        /* Barre Marquee */
        .marquee-bar {{
            background: #000; color: #00ff00; padding: 12px; font-weight: bold;
            border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }}
        
        /* Box Cobalt (Cartes) */
        .cobalt-card {{
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px);
            padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3);
            margin-bottom: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        }}
        
        /* Panier Blanc */
        .white-cart {{
            background: white !important; color: black !important; padding: 20px;
            border-radius: 20px; border: 6px solid #004a99; margin: 15px 0;
        }}
        .white-cart * {{ color: black !important; font-weight: bold; text-align: left; }}
        
        /* Total Section */
        .total-frame {{
            border: 4px solid #00ff00; background: #000; padding: 15px;
            border-radius: 15px; margin: 10px 0; box-shadow: 0 0 10px #00ff00;
        }}
        .total-text {{ color: #00ff00; font-size: 42px; font-weight: bold; }}
        
        /* Boutons */
        .stButton > button {{
            width: 100%; height: 50px; border-radius: 12px; font-size: 16px;
            background: linear-gradient(to right, #007bff, #00d4ff);
            color: white !important; border: none; font-weight: bold;
        }}
        
        /* Tableau Inventaire */
        .inventory-table {{ width: 100%; background: white; color: black !important; border-radius: 10px; overflow: hidden; }}
        .inventory-table th {{ background: #004a99; color: white !important; padding: 10px; }}
        .inventory-table td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: center; color: black !important; }}

        /* Facture Professionnelle (Noir sur Blanc) */
        .invoice-box {{
            background: white !important; color: black !important; padding: 30px;
            font-family: 'Arial', sans-serif;
            width: 100%; max-width: 600px; margin: auto;
            border: 2px solid #000; text-align: center !important;
            border-radius: 0px;
        }}
        .invoice-box h3, .invoice-box b, .invoice-box p, .invoice-box span, .invoice-box td, .invoice-box th {{ 
            color: black !important; 
        }}
        .fac-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; color: black !important; }}
        .fac-table th, .fac-table td {{ border: 1px solid #000; padding: 8px; font-size: 14px; color: black !important; }}
        .fac-footer {{ margin-top: 20px; display: flex; justify-content: space-between; font-size: 12px; color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# ------------------------------------------------------------------------------
# 5. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None,
        'page_history': ["🏠 ACCUEIL"]
    }

def navigate_to(page):
    st.session_state.session['page_history'].append(page)
    st.rerun()

# ------------------------------------------------------------------------------
# 6. CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_new = st.tabs(["🔑 CONNEXION", "📝 DEMANDE"])
        
        with tab_log:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            u_name = st.text_input("IDENTIFIANT").lower().strip()
            u_pass = st.text_input("MOT DE PASSE", type="password")
            if st.button("🚀 ACCÉDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    user = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_name,)).fetchone()
                    if user and get_hash(u_pass) == user[0]:
                        if user[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u_name, 'role': user[1], 'shop_id': user[2]})
                            log_event(u_name, "Connexion", user[2]); st.rerun()
                        else: st.error("❌ Compte Bloqué")
                    else: st.error("❌ Erreur Identifiants")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_new:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            n_uid = st.text_input("ID Choisi")
            n_shop = st.text_input("Nom Boutique")
            n_pass = st.text_input("Mot de Passe", type="password")
            if st.button("📩 ENVOYER"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                     (n_uid.lower(), get_hash(n_pass), 'GERANT', 'PENDING', 'EN_ATTENTE', n_shop, ''))
                        conn.commit(); st.success("✅ Demande envoyée !")
                    except: st.error("❌ ID déjà pris")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. ESPACE SUPER ADMINISTRATEUR
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMIN")
    a_nav = st.sidebar.radio("Navigation", ["👥 Boutiques", "📊 Logs", "⚙️ App Config", "🎨 Thèmes", "🔐 Sécurité", "🚪 Déconnexion"])
    
    if a_nav == "👥 Boutiques":
        st.header("👥 GESTION DES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            users = conn.execute("SELECT uid, name, status, role FROM users WHERE uid != 'admin'").fetchall()
            for u_id, u_name, u_stat, u_role in users:
                with st.expander(f"👤 {u_name} - {u_stat}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("✅ ACTIVER", key=f"ac_{u_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (u_id,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (u_id, u_name, u_id))
                        conn.commit(); st.rerun()
                    if c2.button("🚫 BLOQUER", key=f"bl_{u_id}"):
                        conn.execute("UPDATE users SET status='INACTIF' WHERE uid=?", (u_id,)); conn.commit(); st.rerun()
                    if c3.button("🗑️ SUPPRIMER", key=f"de_{u_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (u_id,)); conn.commit(); st.rerun()

    elif a_nav == "🎨 Thèmes":
        st.header("🎨 PERSONNALISATION VISUELLE")
        new_t = st.selectbox("Choisir un thème", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
        if st.button("APPLIQUER LE THÈME"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=? WHERE id=1", (new_t,))
                conn.commit(); st.rerun()

    elif a_nav == "⚙️ App Config":
        with st.form("global"):
            n_a = st.text_input("Nom App", APP_NAME)
            n_m = st.text_area("Texte du Marquee", MARQUEE_TEXT)
            m_status = st.checkbox("Activer le Marquee", value=bool(MARQUEE_ON))
            if st.form_submit_button("SAUVEGARDER CONFIGURATION"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", 
                                 (n_a, n_m, 1 if m_status else 0))
                    conn.commit(); st.rerun()

    if a_nav == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. LOGIQUE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, addr, tel, rccm, idnat FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("BOUTIQUE", 2800.0, "ADRESSE", "000", "", "")

# Menu filtré selon rôle
nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "📊 RAPPORTS", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav_list)
    if st.button("⬅️ RETOUR"):
        if len(st.session_state.session['page_history']) > 1:
            st.session_state.session['page_history'].pop()
            st.rerun()

# --- 8.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:80px; margin-bottom:0;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        stats = conn.execute("SELECT SUM(total_usd), COUNT(id) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()
        ca = stats[0] if stats[0] else 0
        st.markdown(f"<div class='cobalt-card'><h2>RECETTE DU JOUR</h2><h1 style='font-size:50px;'>{ca:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE & FACTURE ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        
        # Structure de la facture pour affichage et PDF
        invoice_html = f"""
        <div class='invoice-box'>
            <h3>{sh_inf[0]}</h3>
            <p style='font-size:12px;'>{sh_inf[2]} | Tél: {sh_inf[3]}<br>RCCM: {sh_inf[4]} | ID NAT: {sh_inf[5]}</p>
            <hr style='border:1px solid black;'>
            <b>FACTURE N° {inv['ref']}</b><br>
            <p style='font-size:12px; text-align:left;'>Date: {inv['date']}<br>Client: {inv['cli']}<br>Vendeur: {st.session_state.session['user']}</p>
            <table class='fac-table'>
                <thead><tr><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr></thead>
                <tbody>
        """
        for it, d in inv['items'].items():
            invoice_html += f"<tr><td>{it}</td><td>{d['q']}</td><td>{d['p']:.2f}</td><td>{(d['q']*d['p']):.2f}</td></tr>"
        
        invoice_html += f"""
                </tbody>
            </table>
            <h4 style='background:#f0f0f0; padding:10px; color:black !important; border:1px solid black;'>NET À PAYER: {inv['total_val']:.2f} {inv['dev']}</h4>
            <p style='font-size:11px;'>Acompte: {inv['paid']:.2f} | Reste: {inv['rest']:.2f}</p>
            <div class='fac-footer'>
                <span>Signature Client</span>
                <span>[ CACHET ]</span>
                <span>La Direction</span>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("⬅️ NOUVELLE VENTE"): 
                st.session_state.session['viewing_invoice'] = None
                st.rerun()
        with col_f2:
            # Bouton de sauvegarde automatique (Download)
            st.download_button(
                label="💾 SAUVEGARDER LA FACTURE",
                data=invoice_html.replace("white !important", "white").replace("black !important", "black"),
                file_name=f"Facture_{inv['ref']}.html",
                mime="text/html"
            )
    
    else:
        devise = st.radio("MONNAIE DE VENTE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_art = st.selectbox("RECHERCHER ARTICLE", ["---"] + [f"{p[0]} ({p[2]} dispo)" for p in prods])
            if sel_art != "---" and st.button("➕ AJOUTER AU PANIER"):
                name = sel_art.split(" (")[0]
                info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                st.session_state.session['cart'][name] = {'p': info[0], 'q': 1, 'max': info[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            total_u = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c1, c2, c3 = st.columns([3,1,1])
                nq = c2.number_input(f"Qté", 1, d['max'], d['q'], key=f"v_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                total_u += d['p'] * nq
                c1.write(f"**{art}**")
                if c3.button("🗑️", key=f"del_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            p_final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{p_final:,.2f} {devise}</span></center></div>", unsafe_allow_html=True)
            with st.form("pay"):
                c_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                c_pay = st.number_input(f"MONTANT REÇU ({devise})", value=float(p_final))
                if st.form_submit_button("VALIDER ET GÉNÉRER FACTURE"):
                    ref = f"BAL-{random.randint(100000,999999)}"
                    r_usd = c_pay if devise == "USD" else c_pay / sh_inf[1]
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, c_name, total_u, r_usd, total_u-r_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if (total_u - r_usd) > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)", (c_name, total_u-r_usd, ref, sid, datetime.now().strftime("%d/%m/%Y")))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {
                        'ref': ref, 'cli': c_name, 'total_val': p_final, 'dev': devise, 
                        'paid': c_pay, 'rest': p_final-c_pay, 'items': st.session_state.session['cart'], 
                        'date': datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK (Tableau & Suppression) ---
elif choice == "📦 STOCK":
    st.header("📦 INVENTAIRE")
    t1, t2 = st.tabs(["📋 TABLEAU DES ARTICLES", "➕ NOUVEAU"])
    
    with t1:
        with sqlite3.connect(DB_FILE) as conn:
            items = conn.execute("SELECT id, item, qty, sell_price, buy_price FROM inventory WHERE sid=?", (sid,)).fetchall()
            if items:
                st.markdown("<div style='background:white; padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
                for i_id, i_n, i_q, i_p, i_b in items:
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    col1.markdown(f"<span style='color:black;'>{i_n}</span>", unsafe_allow_html=True)
                    new_q = col2.number_input("Qté", value=i_q, key=f"q_{i_id}", label_visibility="collapsed")
                    new_p = col3.number_input("Prix", value=i_p, key=f"p_{i_id}", label_visibility="collapsed")
                    
                    sub_c1, sub_c2 = col4.columns(2)
                    if sub_c1.button("💾", key=f"sv_{i_id}"):
                        conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_p, i_id)); conn.commit(); st.rerun()
                    if sub_c2.button("🗑️", key=f"rm_it_{i_id}"):
                        conn.execute("DELETE FROM inventory WHERE id=?", (i_id,)); conn.commit(); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("Aucun article en stock")

    with t2:
        with st.form("add"):
            n_art = st.text_input("Désignation").upper()
            p_buy = st.number_input("Prix Achat ($)")
            p_sell = st.number_input("Prix Vente ($)")
            q_init = st.number_input("Quantité", 1)
            if st.form_submit_button("AJOUTER AU STOCK"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_art, q_init, p_buy, p_sell, sid))
                    conn.commit(); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉANCES CLIENTS")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for di, dc, db, dr in dettes:
            with st.expander(f"👤 {dc} | {db:,.2f} $"):
                pay = st.number_input("Versement ($)", 0.0, db, key=f"pay_{di}")
                if st.button("ENREGISTRER PAIEMENT", key=f"btn_pay_{di}"):
                    n_bal = db - pay
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (n_bal, datetime.now().strftime("%d/%m/%Y"), di))
                    if n_bal <= 0.01: conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 8.5 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES RÉCENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT ref, cli, total_usd, seller, date FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True)

# --- 8.6 ÉQUIPE (Suppression vendeur) ---
elif choice == "👥 ÉQUIPE":
    st.subheader("👥 GESTION DES VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n in vendeurs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"👤 {v_n} ({v_id})")
            if col2.button("🗑️", key=f"del_v_{v_id}"):
                conn.execute("DELETE FROM users WHERE uid=?", (v_id,)); conn.commit(); st.rerun()
    
    st.markdown("---")
    with st.form("new_v"):
        st.write("➕ Ajouter un vendeur")
        v_id, v_n, v_p = st.text_input("Identifiant (Login)"), st.text_input("Nom Complet"), st.text_input("Mot de Passe", type="password")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_id.lower(), get_hash(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                    conn.commit(); st.success("Vendeur ajouté !"); st.rerun()
                except: st.error("ID déjà utilisé")

# --- RÉGLAGES, SÉCURITÉ, DÉCONNEXION ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("cfg"):
        n_name = st.text_input("Nom de l'Entreprise", sh_inf[0])
        n_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        n_addr = st.text_input("Adresse Physique", sh_inf[2])
        n_tel = st.text_input("Téléphone Contact", sh_inf[3])
        n_rccm = st.text_input("RCCM", sh_inf[4])
        n_idnat = st.text_input("ID NAT", sh_inf[5])
        if st.form_submit_button("METTRE À JOUR LA BOUTIQUE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, addr=?, tel=?, rccm=?, idnat=? WHERE sid=?", 
                             (n_name, n_rate, n_addr, n_tel, n_rccm, n_idnat, sid))
                conn.commit(); st.rerun()

elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 SÉCURITÉ COMPTE")
    with st.form("pwd"):
        old = st.text_input("Mot de passe actuel", type="password")
        new = st.text_input("Nouveau mot de passe", type="password")
        if st.form_submit_button("CHANGER LE MOT DE PASSE"):
            with sqlite3.connect(DB_FILE) as conn:
                curr = conn.execute("SELECT pwd FROM users WHERE uid=?", (st.session_state.session['user'],)).fetchone()[0]
                if curr == get_hash(old):
                    conn.execute("UPDATE users SET pwd=? WHERE uid=?", (get_hash(new), st.session_state.session['user']))
                    conn.commit(); st.success("Mot de passe mis à jour avec succès !")
                else: st.error("L'ancien mot de passe est incorrect")

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()
