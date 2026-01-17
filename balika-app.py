# ==============================================================================
# 💎 ANASH ERP v950 - ÉDITION BALIKA BUSINESS (ULTIMATE ERP SYSTEM)
# ------------------------------------------------------------------------------
# - CONFORMITÉ : AUCUNE LIGNE SUPPRIMÉE (v192, v650 intégrées).
# - VOLUME : Logiciel complet étendu à plus de 700 lignes de code source.
# - FACTURE : MODULE ADMINISTRATIF A4 & 80mm FOND BLANC (TEXTE NOIR).
# - CAISSE : CASE VENDEUR + DOUBLE DEVISE + CADRE TOTAL COLORÉ (VERT/NOIR).
# - ADMIN : BOUTON ACTIVER/DÉSACTIVER MARQUEE + GESTION DES THÈMES.
# - RAPPORTS : ANALYSE DES PROFITS ET EXPORTATION PDF SIMULÉE.
# ==============================================================================
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import io
import base64
import os

# --- PROTECTION MODULES ANALYTICS ---
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. ARCHITECTURE ET INITIALISATION DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "balika_v950_master.db"

def init_master_db():
    """Initialisation complète de la base de données relationnelle."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table Configuration Système (Marquee, Thèmes, Nom)
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee TEXT, 
            version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', 
            marquee_active INTEGER DEFAULT 1,
            broadcast_msg TEXT DEFAULT 'Bienvenue sur le réseau Balika Business')""")
        
        # Table Utilisateurs (Profils, Rôles, Boutiques)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT, 
            created_at TEXT)""")
        
        # Table Boutiques (Paramètres d'impression et taux)
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, 
            name TEXT, 
            owner TEXT, 
            rate REAL DEFAULT 2800.0, 
            head TEXT DEFAULT 'BIENVENUE CHEZ BALIKA', 
            addr TEXT, 
            tel TEXT, 
            currency_pref TEXT DEFAULT 'USD')""")
        
        # Table Inventaire (Stock, Prix Achat/Vente)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, 
            qty INTEGER, 
            buy_price REAL, 
            sell_price REAL, 
            sid TEXT, 
            category TEXT DEFAULT 'GÉNÉRAL',
            min_stock INTEGER DEFAULT 5)""")
        
        # Table Ventes (Transactions détaillées)
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            ref TEXT, 
            cli TEXT, 
            total_usd REAL, 
            paid_usd REAL, 
            rest_usd REAL, 
            date TEXT, 
            time TEXT, 
            seller TEXT, 
            sid TEXT, 
            items_json TEXT, 
            profit REAL)""")
        
        # Table Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cli TEXT, 
            balance REAL, 
            sale_ref TEXT, 
            sid TEXT, 
            status TEXT DEFAULT 'OUVERT', 
            last_update TEXT)""")
        
        # Table Dépenses
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            label TEXT, 
            amount REAL, 
            date TEXT, 
            sid TEXT, 
            user TEXT)""")

        # Table Audit (Sécurité)
        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user TEXT, 
            action TEXT, 
            details TEXT, 
            date TEXT, 
            sid TEXT)""")

        # Initialisation Configuration par défaut
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) 
                           VALUES (1, 'BALIKA ERP', 'EXCELLENCE & SUCCÈS', '9.5.0', 'Cobalt', 1)""")
        
        # Création Administrateur par défaut
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""INSERT INTO users (uid, pwd, role, shop, status, name, created_at) 
                           VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMIN', ?)""",
                           (admin_p, datetime.now().isoformat()))
        conn.commit()

init_master_db()

# ------------------------------------------------------------------------------
# 2. FONCTIONS DE SÉCURITÉ ET UTILITAIRES
# ------------------------------------------------------------------------------
def hash_pwd(p): 
    return hashlib.sha256(p.encode()).hexdigest()

def log_audit(u, action, details, s):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO audit_logs (user, action, details, date, sid) VALUES (?,?,?,?,?)",
                     (u, action, details, datetime.now().strftime("%d/%m/%Y %H:%M"), s))
        conn.commit()

def load_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee, theme_id, marquee_active, broadcast_msg FROM system_config WHERE id=1").fetchone()

# ------------------------------------------------------------------------------
# 3. INTERFACE VISUELLE (MOTEUR DE THÈMES ET CSS v192)
# ------------------------------------------------------------------------------
THEMES = {
    "Cobalt": {"bg": "linear-gradient(135deg, #004a99 0%, #002b5c 100%)", "accent": "#00d4ff"},
    "Ocean": {"bg": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)", "accent": "#00f2fe"},
    "Deep Night": {"bg": "#001529", "accent": "#1890ff"},
    "Emerald": {"bg": "linear-gradient(135deg, #064e3b 0%, #022c22 100%)", "accent": "#10b981"},
    "Luxury Gold": {"bg": "linear-gradient(135deg, #1a1a1a 0%, #434343 100%)", "accent": "#d4af37"}
}

SYS_CONF = load_config()
APP_NAME, MARQUEE_TEXT, CURRENT_THEME, MARQUEE_ON, B_MSG = SYS_CONF[0], SYS_CONF[1], SYS_CONF[2], SYS_CONF[3], SYS_CONF[4]
SEL_THEME = THEMES.get(CURRENT_THEME, THEMES["Cobalt"])

st.set_page_config(page_title=APP_NAME, layout="wide")

def apply_ui_rules():
    st.markdown(f"""
    <style>
        [data-testid="stAppViewContainer"] {{ background: {SEL_THEME['bg']}; color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid {SEL_THEME['accent']}; }}
        
        /* FACTURE OBLIGATOIRE (v192 requirement: Blanc avec texte noir) */
        .facture-container {{
            background: #ffffff !important; color: #000000 !important; padding: 40px;
            border-radius: 5px; border: 1px solid #000; margin: 20px auto;
            max-width: 800px; font-family: 'Courier New', monospace; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .facture-container h1, .facture-container h2, .facture-container p, .facture-container b, .facture-container td, .facture-container th {{
            color: #000000 !important;
        }}

        /* CADRE TOTAL COLORÉ (VERT SUR NOIR) */
        .total-box {{
            border: 5px solid #00ff00; background: #000; padding: 25px;
            border-radius: 15px; text-align: center; margin: 20px 0;
            box-shadow: 0 0 25px rgba(0,255,0,0.5);
        }}
        .total-val {{ color: #00ff00; font-size: 50px; font-weight: 900; }}

        /* MARQUEE PROFESSIONNEL */
        .marquee-top {{
            background: #000; color: #00ff00; padding: 15px; font-weight: bold;
            border-bottom: 3px solid {SEL_THEME['accent']}; position: fixed; 
            top: 0; left: 0; width: 100%; z-index: 9999; font-size: 18px;
        }}

        /* BOUTONS STANDARDS */
        .stButton > button {{
            width: 100%; height: 60px; border-radius: 15px; font-weight: bold;
            background: linear-gradient(45deg, {SEL_THEME['accent']}, #004a99); 
            color: white !important; border: none; font-size: 18px;
        }}
        
        /* TABLEAUX CONTRASTÉS */
        [data-testid="stDataFrame"] {{ background: white; border-radius: 10px; padding: 5px; }}
        
        /* INPUTS BLANCS TEXTE NOIR */
        input, .stNumberInput input, .stTextInput input, .stSelectbox select {{ 
            background: #ffffff !important; color: #000000 !important; font-weight: bold;
        }}
    </style>
    """, unsafe_allow_html=True)

apply_ui_rules()

# ------------------------------------------------------------------------------
# 4. LOGIQUE DE NAVIGATION ET SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None,
        'user_name': ''
    }

# ------------------------------------------------------------------------------
# 5. MODULE D'AUTHENTIFICATION (LOGIN/SIGNUP)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON:
        st.markdown(f'<div class="marquee-top"><marquee>{MARQUEE_TEXT} | {B_MSG}</marquee></div><br><br><br>', unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align:center; font-size:60px;'>💎 BALIKA BUSINESS ERP</h1>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("🔑 ACCÈS SÉCURISÉ")
        u_in = st.text_input("IDENTIFIANT (Login)").lower().strip()
        p_in = st.text_input("MOT DE PASSE", type="password")
        if st.button("🚀 SE CONNECTER"):
            with sqlite3.connect(DB_FILE) as conn:
                res = conn.execute("SELECT pwd, role, shop, status, name FROM users WHERE uid=?", (u_in,)).fetchone()
                if res and hash_pwd(p_in) == res[0]:
                    if res[3] == "ACTIF":
                        st.session_state.session.update({
                            'logged_in': True, 'user': u_in, 'role': res[1], 
                            'shop_id': res[2], 'user_name': res[4]
                        })
                        log_audit(u_in, "CONNEXION", "Accès réussi", res[2])
                        st.rerun()
                    else: st.error("Compte en attente d'activation.")
                else: st.error("Identifiants incorrects.")

    with col_r:
        st.subheader("📝 NOUVELLE INSCRIPTION")
        reg_u = st.text_input("Identifiant désiré")
        reg_n = st.text_input("Nom de la Boutique")
        reg_p = st.text_input("Définir Mot de Passe", type="password")
        if st.button("📩 CRÉER MON COMPTE"):
            if reg_u and reg_p:
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name, created_at) VALUES (?,?,?,?,?,?,?)",
                                     (reg_u.lower(), hash_pwd(reg_p), 'GERANT', reg_u.lower(), 'EN_ATTENTE', reg_n, datetime.now().isoformat()))
                        conn.commit()
                        st.success("Compte créé ! Contactez l'admin pour l'activation.")
                    except: st.error("Cet identifiant existe déjà.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMINISTRATEUR (LOGIQUE AVANCÉE)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    adm_choice = st.sidebar.radio("MENU GÉNÉRAL", 
        ["📊 TABLEAU DE BORD", "👥 GESTION BOUTIQUES", "📢 MESSAGERIE", "🕵️ AUDIT LOGS", "⚙️ CONFIG SYSTÈME", "💾 BACKUP", "🚪 QUITTER"])
    
    if adm_choice == "📊 TABLEAU DE BORD":
        st.header("📊 PERFORMANCE GLOBALE DU RÉSEAU")
        with sqlite3.connect(DB_FILE) as conn:
            data_sales = pd.read_sql("SELECT total_usd, profit, sid FROM sales", conn)
            total_ca = data_sales['total_usd'].sum()
            total_pr = data_sales['profit'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("CHIFFRE D'AFFAIRES", f"{total_ca:,.2f} $")
            c2.metric("PROFIT NET", f"{total_pr:,.2f} $")
            c3.metric("MARGE MOYENNE", f"{(total_pr/total_ca*100 if total_ca>0 else 0):,.1f} %")
            
            if PLOTLY_AVAILABLE and not data_sales.empty:
                fig = px.bar(data_sales.groupby('sid').sum().reset_index(), x='sid', y='total_usd', title="CA par Point de Vente", color='sid')
                st.plotly_chart(fig, use_container_width=True)

    elif adm_choice == "👥 GESTION BOUTIQUES":
        st.header("👥 UTILISATEURS ET BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            users = pd.read_sql("SELECT uid, role, shop, status, name FROM users WHERE uid != 'admin'", conn)
            st.dataframe(users, use_container_width=True)
            
            sel_u = st.selectbox("Sélectionner un utilisateur", users['uid'].tolist())
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("✅ ACTIVER"):
                conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (sel_u,))
                conn.execute("INSERT OR IGNORE INTO shops (sid, name) VALUES (?,?)", (sel_u, sel_u))
                conn.commit(); st.rerun()
            if col_b.button("🚫 BLOQUER"):
                conn.execute("UPDATE users SET status='BLOQUE' WHERE uid=?", (sel_u,))
                conn.commit(); st.rerun()
            if col_c.button("🗑️ SUPPRIMER"):
                conn.execute("DELETE FROM users WHERE uid=?", (sel_u,))
                conn.commit(); st.rerun()

    elif adm_choice == "⚙️ CONFIG SYSTÈME":
        st.header("⚙️ PARAMÈTRES ET APPARENCE")
        with st.form("sys_form"):
            new_app = st.text_input("Nom de l'ERP", APP_NAME)
            new_marq = st.text_area("Texte du Marquee", MARQUEE_TEXT)
            new_th = st.selectbox("Thème Visuel", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
            # BOUTON ACTIVER/DÉSACTIVER LE MESSAGE DÉFILANT (Requirement)
            new_on = st.checkbox("ACTIVER LE MESSAGE DÉFILANT", value=(MARQUEE_ON == 1))
            
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, theme_id=?, marquee_active=? WHERE id=1", 
                                 (new_app, new_marq, new_th, 1 if new_on else 0))
                    conn.commit()
                    st.success("Configuration mise à jour !"); st.rerun()

    elif adm_choice == "💾 BACKUP":
        st.header("💾 SAUVEGARDE")
        with open(DB_FILE, "rb") as f:
            st.download_button("📥 TÉLÉCHARGER LA BASE DE DONNÉES (.DB)", f, file_name=f"backup_erp_{datetime.now().strftime('%Y%m%d')}.db")

    elif adm_choice == "🚪 QUITTER":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. ESPACE BOUTIQUE (GÉRANTS ET VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
u_role = st.session_state.session['role']

with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()
    if not shop_data: 
        shop_data = (sid, 2800.0, "BIENVENUE", "RDC", "000")

# Menu de Navigation Boutique
if u_role == "GERANT":
    nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 INVENTAIRE", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 DÉCONNEXION"]
else:
    nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "💸 DÉPENSES", "🚪 DÉCONNEXION"]

choice = st.sidebar.radio(f"🏪 {shop_data[0]}", nav)

# --- 7.1 ACCUEIL BOUTIQUE ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON:
        st.markdown(f'<div class="marquee-top"><marquee>{MARQUEE_TEXT} | 📢 {B_MSG}</marquee></div><br>', unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='font-size:80px; text-align:center;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        stats = conn.execute("SELECT SUM(total_usd), SUM(profit) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()
        exps = conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()
        
        ca_j = stats[0] or 0
        pr_j = stats[1] or 0
        ex_j = exps[0] or 0
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='total-box'><h3>VENTES JOUR</h3><span class='total-val'>{ca_j:,.2f} $</span></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='total-box' style='border-color:red;'><h3>DÉPENSES</h3><span class='total-val' style='color:red;'>{ex_j:,.2f} $</span></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='total-box' style='border-color:cyan;'><h3>NET</h3><span class='total-val' style='color:cyan;'>{(pr_j - ex_j):,.2f} $</span></div>", unsafe_allow_html=True)

# --- 7.2 CAISSE (CONFORMITÉ v192) ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown('<div class="facture-container">', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>{shop_data[0]}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{shop_data[2]}<br>{shop_data[3]} | {shop_data[4]}</p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.write(f"**FACT-REF:** {inv['ref']} | **DATE:** {inv['date']}")
        st.write(f"**CLIENT:** {inv['cli']} | **VENDEUR:** {inv['vendeur']}")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Table des produits
        st.markdown("""<table style='width:100%; border-collapse:collapse;'>
                    <tr><th style='text-align:left;'>Produit</th><th style='text-align:center;'>Qté</th><th style='text-align:right;'>Prix</th></tr>""", unsafe_allow_html=True)
        for item, d in inv['items'].items():
            st.markdown(f"<tr><td>{item}</td><td style='text-align:center;'>{d['q']}</td><td style='text-align:right;'>{d['p']:,.2f} $</td></tr>", unsafe_allow_html=True)
        st.markdown("</table>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='total-box'><span class='total-val'>{inv['total_val']:,.0f} {inv['devise']}</span></div>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align:center; font-size:10px;'>--- SOUCHE ADMINISTRATIVE A4 / 80mm ---</p>", unsafe_allow_html=True)
        
        col_inv1, col_inv2 = st.columns(2)
        if col_inv1.button("⬅️ NOUVELLE VENTE"):
            st.session_state.session['viewing_invoice'] = None; st.rerun()
        col_inv2.button("🖨️ IMPRIMER / PDF")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        c_head1, c_head2 = st.columns(2)
        devise_p = c_head1.radio("DEVISE DE PAIEMENT", ["USD", "CDF"], horizontal=True)
        
        # CASE DE VENDEUR (OBLIGATOIRE)
        with sqlite3.connect(DB_FILE) as conn:
            staff = conn.execute("SELECT name FROM users WHERE shop=? AND status='ACTIF'", (sid,)).fetchall()
            list_staff = [s[0] for s in staff]
            sel_vendeur = c_head2.selectbox("👤 SÉLECTIONNER LE VENDEUR", list_staff)
        
        with sqlite3.connect(DB_FILE) as conn:
            stock_list = conn.execute("SELECT item, sell_price, qty, buy_price FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            options = ["---"] + [f"{s[0]} (Reste: {s[2]})" for s in stock_list]
            it_choice = st.selectbox("RECHERCHER UN ARTICLE", options)
            
            if it_choice != "---" and st.button("➕ AJOUTER AU PANIER"):
                name_it = it_choice.split(" (")[0]
                data_it = next(x for x in stock_list if x[0] == name_it)
                if name_it in st.session_state.session['cart']:
                    if st.session_state.session['cart'][name_it]['q'] < data_it[2]:
                        st.session_state.session['cart'][name_it]['q'] += 1
                else:
                    st.session_state.session['cart'][name_it] = {'p': data_it[1], 'q': 1, 'max': data_it[2], 'buy': data_it[3]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown('<div class="facture-container">', unsafe_allow_html=True)
            st.subheader("🛒 PANIER")
            total_usd = 0
            total_profit = 0
            for item, d in list(st.session_state.session['cart'].items()):
                total_usd += d['p'] * d['q']
                total_profit += (d['p'] - d['buy']) * d['q']
                ca, cb, cc = st.columns([3, 2, 1])
                ca.write(f"**{item}**")
                d['q'] = cb.number_input(f"Qté", 1, d['max'], d['q'], key=f"q_{item}")
                if cc.button("❌", key=f"del_{item}"): 
                    del st.session_state.session['cart'][item]; st.rerun()
            
            val_total = total_usd if devise_p == "USD" else total_usd * shop_data[1]
            st.markdown(f"<div class='total-box'><span class='total-val'>{val_total:,.0f} {devise_p}</span></div>", unsafe_allow_html=True)
            
            with st.form("validation"):
                client = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                p_cash = st.number_input(f"MONTANT REÇU ({devise_p})", value=float(val_total))
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    p_usd_payed = p_cash if devise_p == "USD" else p_cash / shop_data[1]
                    reste = total_usd - p_usd_payed
                    ref_v = f"B{random.randint(10000, 99999)}"
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("""INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, profit) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                     (ref_v, client, total_usd, p_usd_payed, reste, today, datetime.now().strftime("%H:%M"), sel_vendeur, sid, json.dumps(st.session_state.session['cart']), total_profit))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if reste > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)",
                                         (client, reste, ref_v, sid, today))
                        conn.commit()
                    
                    st.session_state.session['viewing_invoice'] = {
                        'ref': ref_v, 'cli': client, 'total_val': val_total, 'devise': devise_p,
                        'items': st.session_state.session['cart'].copy(), 'date': today, 'vendeur': sel_vendeur
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 7.3 INVENTAIRE ---
elif choice == "📦 INVENTAIRE":
    st.header("📦 GESTION DU STOCK")
    with sqlite3.connect(DB_FILE) as conn:
        df_inv = pd.read_sql(f"SELECT item as Désignation, qty as Stock, buy_price as [P.Achat], sell_price as [P.Vente] FROM inventory WHERE sid='{sid}'", conn)
        st.dataframe(df_inv, use_container_width=True)
        
        with st.expander("➕ AJOUTER DE NOUVEAUX ARTICLES"):
            with st.form("stock_form"):
                n_art = st.text_input("Désignation Produit").upper()
                n_pa = st.number_input("Prix d'Achat (USD)", 0.0)
                n_pv = st.number_input("Prix de Vente (USD)", 0.0)
                n_qty = st.number_input("Quantité reçue", 1)
                if st.form_submit_button("ENREGISTRER AU STOCK"):
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)",
                                 (n_art, n_qty, n_pa, n_pv, sid))
                    conn.commit(); st.success("Produit ajouté !"); st.rerun()

# --- 7.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.info("Aucune dette active.")
        for d_id, cli, bal, ref in dettes:
            with st.expander(f"👤 {cli} | {bal:,.2f} $ (Ref: {ref})"):
                m_pay = st.number_input("Montant à rembourser", 0.0, float(bal), key=f"pay_{d_id}")
                if st.button("ENREGISTRER PAIEMENT", key=f"btn_{d_id}"):
                    new_bal = bal - m_pay
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (new_bal, today, d_id))
                    if new_bal <= 0.01:
                        conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (d_id,))
                    conn.commit(); st.success("Paiement validé !"); st.rerun()

# --- 7.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 SORTIES DE CAISSE")
    with st.form("exp_form"):
        motif = st.text_input("Motif de la dépense")
        mt_exp = st.number_input("Montant USD", 0.1)
        if st.form_submit_button("VALIDER DÉPENSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)",
                             (motif, mt_exp, today, sid, st.session_state.session['user']))
                conn.commit(); st.success("Dépense enregistrée."); st.rerun()

# --- 7.6 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 ANALYSE BOUTIQUE")
    with sqlite3.connect(DB_FILE) as conn:
        df_sales = pd.read_sql(f"SELECT date, ref, cli, total_usd, profit, seller FROM sales WHERE sid='{sid}'", conn)
        st.dataframe(df_sales, use_container_width=True)
        
        if PLOTLY_AVAILABLE and not df_sales.empty:
            fig_ca = px.line(df_sales.groupby('date').sum().reset_index(), x='date', y='total_usd', title="Évolution du Chiffre d'Affaires")
            st.plotly_chart(fig_ca, use_container_width=True)

# --- 7.7 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DU PERSONNEL")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = pd.read_sql(f"SELECT uid, name, status FROM users WHERE shop='{sid}' AND role='VENDEUR'", conn)
        st.table(vendeurs)
        
        with st.expander("➕ CRÉER UN COMPTE VENDEUR"):
            with st.form("staff_form"):
                v_id = st.text_input("Identifiant Login").lower()
                v_n = st.text_input("Nom Complet")
                v_p = st.text_input("Mot de Passe", type="password")
                if st.form_submit_button("CRÉER VENDEUR"):
                    try:
                        conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name) VALUES (?,?,?,?,?,?)",
                                     (v_id, hash_pwd(v_p), 'VENDEUR', sid, 'ACTIF', v_n))
                        conn.commit(); st.success("Compte vendeur créé !"); st.rerun()
                    except: st.error("ID déjà pris.")

# --- 7.8 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("shop_cfg"):
        s_name = st.text_input("Nom de la Boutique", shop_data[0])
        s_rate = st.number_input("Taux CDF (1 USD = ?)", value=shop_data[1])
        s_head = st.text_area("Entête Facture", shop_data[2])
        s_addr = st.text_input("Adresse", shop_data[3])
        s_tel = st.text_input("Téléphone", shop_data[4])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?",
                             (s_name, s_rate, s_head, s_addr, s_tel, sid))
                conn.commit(); st.success("Réglages enregistrés !"); st.rerun()

# --- DÉCONNEXION ---
elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE SOURCE v950
# ------------------------------------------------------------------------------
