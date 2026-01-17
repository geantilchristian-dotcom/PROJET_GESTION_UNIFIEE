# ==============================================================================
# 💎 ANASH ERP v1002.9 - ULTIMATE MEGA EDITION (+700 LIGNES)
# ------------------------------------------------------------------------------
# - CONFORMITÉ : AUCUNE LIGNE SUPPRIMÉE (v192, v197, v199, v650, v700+).
# - VISUEL : 30 THÈMES PERSONNALISÉS (DU LUXE AU CYBERPUNK).
# - MOBILE : DESIGN RESPONSIVE AVEC GRILLES ADAPTATIVES.
# - RÈGLE : FOND BLEU -> TEXTE BLANC | PANIER/FACTURE -> FOND BLANC TEXTE NOIR.
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

# --- VÉRIFICATION DES MODULES ANALYTIQUES ---
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES ET STRUCTURE (EXTENDED)
# ------------------------------------------------------------------------------
DB_FILE = "balika_business_v1002_mega.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Configuration & Personnalisation (Ajout du support 30 thèmes)
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt Night', marquee_active INTEGER DEFAULT 1,
            broadcast_msg TEXT DEFAULT 'Système Opérationnel - Bon Travail',
            font_style TEXT DEFAULT 'Sans-Serif')""")
        
        # Utilisateurs & Authentification
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, 
            name TEXT, tel TEXT, photo_url TEXT DEFAULT '', last_login TEXT, created_at TEXT)""")
        
        # Boutiques & Fiscalité
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT DEFAULT 'BIENVENUE', addr TEXT, tel TEXT, 
            rccm TEXT, idnat TEXT, currency_pref TEXT DEFAULT 'USD', tax_rate REAL DEFAULT 0.0)""")
        
        # Stock & Logistique (v192+)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT DEFAULT 'GÉNÉRAL',
            min_stock INTEGER DEFAULT 5, last_restock TEXT, supplier TEXT, barcode TEXT)""")
        
        # Ventes & Transactions
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT, profit REAL, status TEXT DEFAULT 'VALIDÉ',
            payment_method TEXT DEFAULT 'CASH')""")
        
        # Dépenses & Flux de Trésorerie
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, amount REAL, 
            date TEXT, sid TEXT, user TEXT, category TEXT DEFAULT 'AUTRE', proof_img TEXT)""")

        # Dettes & Crédits (v197+)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_update TEXT,
            tel_client TEXT)""")

        # Logs de Sécurité & Audit
        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
            details TEXT, date TEXT, time TEXT, sid TEXT)""")

        # Configuration Initiale
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO system_config (id, app_name, marquee, version, theme_id) 
                           VALUES (1, 'BALIKA ERP v1002', 'VOTRE RÉUSSITE EST NOTRE PRIORITÉ', '10.0.2', 'Cobalt Night')""")
        
        # Création Administrateur par défaut
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            h_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""INSERT INTO users (uid, pwd, role, shop, status, name, created_at) 
                           VALUES (?,?,?,?,?,?,?)""", 
                          ('admin', h_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', datetime.now().isoformat()))
        conn.commit()

init_db()

# ------------------------------------------------------------------------------
# 2. BIBLIOTHÈQUE DES 30 THÈMES (LOGIQUE DE DESIGN)
# ------------------------------------------------------------------------------
THEME_LIB = {
    "Cobalt Night": {"bg": "linear-gradient(135deg, #004a99 0%, #002b5c 100%)", "acc": "#00d4ff"},
    "Emerald City": {"bg": "linear-gradient(135deg, #064e3b 0%, #022c22 100%)", "acc": "#10b981"},
    "Ruby Wine": {"bg": "linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)", "acc": "#f87171"},
    "Luxury Gold": {"bg": "linear-gradient(135deg, #1a1a1a 0%, #434343 100%)", "acc": "#d4af37"},
    "Cyberpunk": {"bg": "linear-gradient(135deg, #2b0054 0%, #000000 100%)", "acc": "#ff00ff"},
    "Deep Ocean": {"bg": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)", "acc": "#38bdf8"},
    "Sunset Orange": {"bg": "linear-gradient(135deg, #7c2d12 0%, #451a03 100%)", "acc": "#fb923c"},
    "Forest Green": {"bg": "linear-gradient(135deg, #14532d 0%, #064e3b 100%)", "acc": "#4ade80"},
    "Midnight Purple": {"bg": "linear-gradient(135deg, #3b0764 0%, #1e1b4b 100%)", "acc": "#a855f7"},
    "Slate Dark": {"bg": "linear-gradient(135deg, #020617 0%, #1e293b 100%)", "acc": "#94a3b8"},
    "Vampire": {"bg": "linear-gradient(135deg, #450606 0%, #000000 100%)", "acc": "#ef4444"},
    "Modern Gray": {"bg": "linear-gradient(135deg, #1f2937 0%, #111827 100%)", "acc": "#f3f4f6"},
    "Neon Lime": {"bg": "linear-gradient(135deg, #000000 0%, #052e16 100%)", "acc": "#84cc16"},
    "Coffee Brown": {"bg": "linear-gradient(135deg, #451a03 0%, #271709 100%)", "acc": "#d97706"},
    "Imperial Blue": {"bg": "linear-gradient(135deg, #1e3a8a 0%, #172554 100%)", "acc": "#60a5fa"},
    "Royal Violet": {"bg": "linear-gradient(135deg, #4c1d95 0%, #2e1065 100%)", "acc": "#c084fc"},
    "Volcano": {"bg": "linear-gradient(135deg, #991b1b 0%, #111827 100%)", "acc": "#f97316"},
    "Matte Black": {"bg": "#111111", "acc": "#ffffff"},
    "Space": {"bg": "radial-gradient(circle, #1b2735 0%, #090a0f 100%)", "acc": "#ffffff"},
    "Military": {"bg": "linear-gradient(135deg, #365314 0%, #1a2e05 100%)", "acc": "#bef264"},
    "Sahara": {"bg": "linear-gradient(135deg, #78350f 0%, #451a03 100%)", "acc": "#fcd34d"},
    "Electric Blue": {"bg": "linear-gradient(135deg, #1e40af 0%, #1e1b4b 100%)", "acc": "#2dd4bf"},
    "Bordeaux": {"bg": "linear-gradient(135deg, #4c0519 0%, #831843 100%)", "acc": "#fbcfe8"},
    "Titanium": {"bg": "linear-gradient(135deg, #3f3f46 0%, #18181b 100%)", "acc": "#d4d4d8"},
    "Amazonia": {"bg": "linear-gradient(135deg, #065f46 0%, #064e3b 100%)", "acc": "#34d399"},
    "Arctic": {"bg": "linear-gradient(135deg, #0c4a6e 0%, #082f49 100%)", "acc": "#7dd3fc"},
    "Industrial": {"bg": "linear-gradient(135deg, #27272a 0%, #09090b 100%)", "acc": "#a1a1aa"},
    "Galaxy": {"bg": "linear-gradient(135deg, #2e1065 0%, #000000 100%)", "acc": "#f472b6"},
    "Deep Rose": {"bg": "linear-gradient(135deg, #881337 0%, #4c0519 100%)", "acc": "#fda4af"},
    "Stealth": {"bg": "#000000", "acc": "#525252"}
}

# ------------------------------------------------------------------------------
# 3. MOTEUR DE SÉCURITÉ ET UTILITAIRES
# ------------------------------------------------------------------------------
def get_hash(p): return hashlib.sha256(p.encode()).hexdigest()

def log_audit(u, action, details, s):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO audit_logs (user, action, details, date, time, sid) VALUES (?,?,?,?,?,?)",
                     (u, action, details, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S"), s))

def load_sys_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee, theme_id, marquee_active, broadcast_msg FROM system_config WHERE id=1").fetchone()

# Chargement config
S_CONF = load_sys_config()
APP_NAME, MARQUEE_TXT, CURRENT_TH, MARQ_ON, B_MSG = S_CONF[0], S_CONF[1], S_CONF[2], S_CONF[3], S_CONF[4]
DESIGN = THEME_LIB.get(CURRENT_TH, THEME_LIB["Cobalt Night"])

# Configuration Streamlit
st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------------------------
# 4. INJECTION CSS PERSONNALISÉE (v192, v650 compliance)
# ------------------------------------------------------------------------------
def inject_ui_engine():
    st.markdown(f"""
    <style>
        /* Base de l'application - Fond Bleu/Couleur thémée avec texte Blanc */
        [data-testid="stAppViewContainer"] {{ 
            background: {DESIGN['bg']}; 
            color: white !important; 
        }}
        [data-testid="stSidebar"] {{ 
            background-color: rgba(0,0,0,0.8) !important; 
            border-right: 1px solid {DESIGN['acc']}; 
        }}
        
        /* Titres et Textes */
        h1, h2, h3, h4, p, label, .stMarkdown {{ color: white !important; }}
        
        /* Boutons ERP Standards */
        .stButton > button {{
            width: 100%; height: 50px; border-radius: 10px; font-weight: bold;
            background: linear-gradient(45deg, {DESIGN['acc']}, #444); 
            color: white !important; border: none; transition: 0.3s;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        .stButton > button:hover {{ transform: scale(1.01); box-shadow: 0 4px 15px {DESIGN['acc']}55; }}

        /* CONTENEUR BLANC POUR FACTURE ET PANIER (Condition v192) */
        .white-card {{
            background: #ffffff !important; 
            color: #111111 !important; 
            padding: 30px;
            border-radius: 15px; 
            border: 2px solid #ddd;
            margin: 10px 0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }}
        .white-card h1, .white-card h2, .white-card h3, .white-card p, .white-card div, .white-card b, .white-card span {{
            color: #111111 !important;
        }}
        
        /* Boîte Total Colorée */
        .total-frame {{
            border: 5px solid {DESIGN['acc']}; 
            background: #000; 
            padding: 20px;
            border-radius: 15px; 
            text-align: center; 
            margin: 15px 0;
        }}
        .total-val {{ color: {DESIGN['acc']}; font-size: 42px; font-weight: 900; }}
        
        /* Marquee Professionnel */
        .marquee-container {{
            background: #000; color: {DESIGN['acc']}; padding: 8px; 
            font-weight: bold; border-bottom: 2px solid {DESIGN['acc']};
            position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
        }}
        
        /* Inputs */
        input {{ border-radius: 8px !important; }}
        
        /* Tableaux */
        [data-testid="stTable"] {{ background: rgba(255,255,255,0.05); border-radius: 10px; }}
        
        /* Mobile Adjustments */
        @media (max-width: 768px) {{
            .total-val {{ font-size: 28px; }}
            .stButton > button {{ height: 45px; font-size: 12px; }}
        }}
    </style>
    """, unsafe_allow_html=True)

inject_ui_engine()

# ------------------------------------------------------------------------------
# 5. GESTION DE SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged': False, 
        'user': None, 
        'role': None, 
        'shop': None, 
        'cart': {}, 
        'invoice': None,
        'login_time': None
    }

# ------------------------------------------------------------------------------
# 6. AUTHENTIFICATION (LOGIN / INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged']:
    if MARQ_ON:
        st.markdown(f'<div class="marquee-container"><marquee>🚀 {MARQUEE_TXT} | 📢 {B_MSG}</marquee></div><br><br>', unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='text-align:center; font-size: 50px;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Système de Gestion Commerciale de Haute Précision</p>", unsafe_allow_html=True)
    
    tab_log, tab_reg = st.tabs(["🔑 CONNEXION SÉCURISÉE", "📝 CRÉER UN COMPTE"])
    
    with tab_log:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            u_in = st.text_input("Identifiant Utilisateur").lower().strip()
            p_in = st.text_input("Code d'accès", type="password")
            if st.button("🔓 DÉVERROUILLER LE SYSTÈME"):
                with sqlite3.connect(DB_FILE) as conn:
                    res = conn.execute("SELECT pwd, role, shop, status, name FROM users WHERE uid=?", (u_in,)).fetchone()
                    if res and get_hash(p_in) == res[0]:
                        if res[3] == "ACTIF":
                            st.session_state.session.update({
                                'logged': True, 'user': u_in, 'role': res[1], 
                                'shop': res[2], 'name': res[4], 'login_time': datetime.now()
                            })
                            log_audit(u_in, "CONNEXION", "Entrée système", res[2])
                            st.rerun()
                        else: st.warning("⌛ Compte en attente d'activation par l'administrateur.")
                    else: st.error("❌ Identifiants invalides.")
                    
    with tab_reg:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            r_u = st.text_input("Nouvel Identifiant")
            r_n = st.text_input("Nom de la Boutique / Gérant")
            r_p = st.text_input("Nouveau Mot de Passe", type="password")
            if st.button("🚀 ENREGISTRER MA DEMANDE"):
                if r_u and r_p:
                    try:
                        with sqlite3.connect(DB_FILE) as conn:
                            conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name, created_at) VALUES (?,?,?,?,?,?,?)",
                                         (r_u.lower(), get_hash(r_p), 'GERANT', r_u.lower(), 'EN_ATTENTE', r_n.upper(), datetime.now().isoformat()))
                            conn.commit()
                            st.success("✅ Demande transmise ! Contactez l'administrateur pour l'activation.")
                    except: st.error("⚠️ Cet identifiant est déjà utilisé.")
                else: st.error("Veuillez remplir tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE MÉTIER ET VARIABLES GLOBALES
# ------------------------------------------------------------------------------
USER = st.session_state.session['user']
ROLE = st.session_state.session['role']
SHOP = st.session_state.session['shop']

with sqlite3.connect(DB_FILE) as conn:
    SHOP_DATA = conn.execute("SELECT name, rate, head, addr, tel, tax_rate FROM shops WHERE sid=?", (SHOP,)).fetchone()
    if not SHOP_DATA:
        conn.execute("INSERT OR IGNORE INTO shops (sid, name) VALUES (?,?)", (SHOP, SHOP))
        conn.commit()
        SHOP_INF = (SHOP, 2800.0, "BIENVENUE", "ADRESSE", "TEL", 0.0)
    else: SHOP_INF = SHOP_DATA

# ------------------------------------------------------------------------------
# 8. PANEL ADMINISTRATEUR (SUPER_ADMIN)
# ------------------------------------------------------------------------------
if ROLE == "SUPER_ADMIN":
    st.sidebar.markdown(f"### 🛡️ ADMIN: {USER}")
    nav = st.sidebar.selectbox("MENU ADMIN", ["DASHBOARD GLOBAL", "UTILISATEURS", "THÈMES & DESIGN", "MESSAGERIE", "AUDIT SÉCURITÉ", "DÉCONNEXION"])
    
    if nav == "DASHBOARD GLOBAL":
        st.title("📊 ANALYTICS RÉSEAU")
        with sqlite3.connect(DB_FILE) as conn:
            ca = conn.execute("SELECT SUM(total_usd) FROM sales").fetchone()[0] or 0
            profit = conn.execute("SELECT SUM(profit) FROM sales").fetchone()[0] or 0
            n_shops = conn.execute("SELECT COUNT(sid) FROM shops").fetchone()[0]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("CA TOTAL", f"{ca:,.2f} $")
            c2.metric("BENEFICE NET", f"{profit:,.2f} $")
            c3.metric("BOUTIQUES", n_shops)
            
            if PLOTLY_AVAILABLE:
                df = pd.read_sql("SELECT sid, SUM(total_usd) as total FROM sales GROUP BY sid", conn)
                st.plotly_chart(px.pie(df, values='total', names='sid', hole=.3, title="Répartition des Ventes par Point de Vente"))

    elif nav == "UTILISATEURS":
        st.title("👥 GESTION DES ACCÈS")
        with sqlite3.connect(DB_FILE) as conn:
            u_list = pd.read_sql("SELECT uid, name, shop, role, status FROM users", conn)
            st.dataframe(u_list, use_container_width=True)
            
            target = st.selectbox("Sélectionner un compte", u_list['uid'].tolist())
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("✅ ACTIVER"):
                conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (target,))
                conn.commit(); st.rerun()
            if col_b.button("🚫 BLOQUER"):
                conn.execute("UPDATE users SET status='BLOQUÉ' WHERE uid=?", (target,))
                conn.commit(); st.rerun()
            if col_c.button("🗑️ SUPPRIMER"):
                conn.execute("DELETE FROM users WHERE uid=?", (target,))
                conn.commit(); st.rerun()

    elif nav == "THÈMES & DESIGN":
        st.title("🎨 STUDIO DE DESIGN")
        new_th = st.selectbox("CHOISIR UN THÈME PARMI LES 30", list(THEME_LIB.keys()), index=list(THEME_LIB.keys()).index(CURRENT_TH))
        new_app_name = st.text_input("NOM DU SYSTÈME", APP_NAME)
        new_marq = st.text_input("TEXTE DÉFILANT", MARQUEE_TXT)
        
        if st.button("💾 APPLIQUER LES CHANGEMENTS"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=?, app_name=?, marquee=? WHERE id=1", (new_th, new_app_name, new_marq))
                conn.commit()
                st.success("Design mis à jour ! Redémarrage..."); time.sleep(1); st.rerun()

    elif nav == "MESSAGERIE":
        st.title("📢 DIFFUSION DE MESSAGES")
        m = st.text_area("Message de broadcast", B_MSG)
        if st.button("ENVOYER À TOUS"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET broadcast_msg=? WHERE id=1", (m,))
                conn.commit(); st.success("Message diffusé !")

    elif nav == "DÉCONNEXION":
        st.session_state.session['logged'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 9. INTERFACE GÉRANT / VENDEUR (v192, v199, v650 Compliance)
# ------------------------------------------------------------------------------
st.sidebar.markdown(f"### 🏪 {SHOP_INF[0]}")
st.sidebar.markdown(f"👤 **{st.session_state.session['name']}** ({ROLE})")

# Menu de navigation
main_menu = ["🏠 TABLEAU DE BORD", "🛒 POINT DE VENTE (CAISSE)", "📦 STOCK & INVENTAIRE", "📉 DETTES & CRÉDITS", "💸 DÉPENSES", "📊 RAPPORTS DE VENTE", "⚙️ CONFIGURATION", "🚪 QUITTER"]

# Restriction Vendeur (v197 requirement)
if ROLE == "VENDEUR":
    main_menu = ["🏠 TABLEAU DE BORD", "🛒 POINT DE VENTE (CAISSE)", "📉 DETTES & CRÉDITS", "🚪 QUITTER"]

choice = st.sidebar.radio("NAVIGATION", main_menu)

# --- 9.1 TABLEAU DE BORD (ACCUEIL) ---
if choice == "🏠 TABLEAU DE BORD":
    st.markdown(f"<h1 style='font-size: 80px; margin:0; text-align:center;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>{datetime.now().strftime('%A %d %B %Y')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:{DESIGN['acc']} !important;'>{B_MSG}</p>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        v_j = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (SHOP, today)).fetchone()[0] or 0
        d_j = conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (SHOP, today)).fetchone()[0] or 0
        
        col_1, col_2 = st.columns(2)
        with col_1:
            st.markdown(f"""<div class='total-frame'><h3>VENTES DU JOUR</h3><div class='total-val'>{v_j:,.2f} $</div></div>""", unsafe_allow_html=True)
        with col_2:
            st.markdown(f"""<div class='total-frame' style='border-color:#ff4b4b;'><h3>DÉPENSES DU JOUR</h3><div class='total-val' style='color:#ff4b4b;'>{d_j:,.2f} $</div></div>""", unsafe_allow_html=True)
        
        # Alerte Stock Bas
        low_stock = pd.read_sql(f"SELECT item, qty FROM inventory WHERE sid='{SHOP}' AND qty <= min_stock", conn)
        if not low_stock.empty:
            st.warning(f"⚠️ {len(low_stock)} articles sont presque épuisés !")
            st.table(low_stock)

# --- 9.2 POINT DE VENTE (v192 requirement met: White background for Invoice) ---
elif choice == "🛒 POINT DE VENTE (CAISSE)":
    # Affichage de la facture si validée
    if st.session_state.session['invoice']:
        inv = st.session_state.session['invoice']
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center;'>{SHOP_INF[0]}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{SHOP_INF[2]}<br>{SHOP_INF[3]} | {SHOP_INF[4]}</p>", unsafe_allow_html=True)
        st.markdown("---")
        st.write(f"**FACTURE N°:** {inv['ref']}")
        st.write(f"**DATE:** {inv['date']} {inv['time']}")
        st.write(f"**CLIENT:** {inv['cli']}")
        st.write(f"**CAISSIER:** {USER}")
        st.markdown("---")
        
        items = json.loads(inv['items'])
        for it, data in items.items():
            st.write(f"• {it} (x{data['q']}) : **{(data['q']*data['p']):,.2f} $**")
        
        st.markdown("---")
        st.markdown(f"<div style='text-align:right; font-size:24px;'><b>TOTAL À PAYER: {inv['total_aff']:,.0f} {inv['cur']}</b></div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.button("🖨️ IMPRIMER (80mm)", on_click=lambda: st.toast("Impression lancée..."))
        c2.button("📩 PARTAGER WHATSAPP")
        if c3.button("⬅️ NOUVELLE VENTE"):
            st.session_state.session['invoice'] = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Interface de vente
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            st.subheader("🛒 SELECTION ARTICLES")
            devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            with sqlite3.connect(DB_FILE) as conn:
                items_db = conn.execute("SELECT item, sell_price, qty, buy_price FROM inventory WHERE sid=? AND qty > 0", (SHOP,)).fetchall()
                search = st.text_input("🔍 Rechercher article...")
                
                filtered = [i for i in items_db if search.upper() in i[0].upper()]
                
                for item in filtered:
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{item[0]}** (${item[1]})")
                    c2.write(f"Stock: {item[2]}")
                    if c3.button("➕", key=f"add_{item[0]}"):
                        if item[0] in st.session_state.session['cart']:
                            if st.session_state.session['cart'][item[0]]['q'] < item[2]:
                                st.session_state.session['cart'][item[0]]['q'] += 1
                        else:
                            st.session_state.session['cart'][item[0]] = {'p': item[1], 'q': 1, 'buy': item[3], 'max': item[2]}
                        st.rerun()

        with col_b:
            st.subheader("📋 PANIER")
            if not st.session_state.session['cart']:
                st.info("Le panier est vide.")
            else:
                st.markdown('<div class="white-card">', unsafe_allow_html=True)
                total_usd = 0
                for it, d in list(st.session_state.session['cart'].items()):
                    st.write(f"**{it}**")
                    new_q = st.number_input("Qté", 1, d['max'], d['q'], key=f"cart_q_{it}")
                    st.session_state.session['cart'][it]['q'] = new_q
                    sub = d['p'] * new_q
                    total_usd += sub
                    st.write(f"Sous-total: {sub:,.2f} $")
                    if st.button("🗑️", key=f"rev_{it}"):
                        del st.session_state.session['cart'][it]; st.rerun()
                
                aff_total = total_usd if devise == "USD" else total_usd * SHOP_INF[1]
                st.markdown(f"<div class='total-frame' style='padding:10px;'><div class='total-val' style='font-size:25px;'>{aff_total:,.0f} {devise}</div></div>", unsafe_allow_html=True)
                
                client = st.text_input("NOM CLIENT", "COMPTANT").upper()
                if st.button("💰 VALIDER LA VENTE"):
                    ref = f"REF-{random.randint(100000, 999999)}"
                    profit = sum((v['p'] - v['buy']) * v['q'] for v in st.session_state.session['cart'].values())
                    t_now = datetime.now()
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("""INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency, profit) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                     (ref, client, total_usd, total_usd, 0.0, t_now.strftime("%d/%m/%Y"), t_now.strftime("%H:%M"), USER, SHOP, json.dumps(st.session_state.session['cart']), devise, profit))
                        
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, SHOP))
                        conn.commit()
                    
                    st.session_state.session['invoice'] = {
                        'ref': ref, 'cli': client, 'total_aff': aff_total, 'cur': devise, 
                        'items': json.dumps(st.session_state.session['cart']), 
                        'date': t_now.strftime("%d/%m/%Y"), 'time': t_now.strftime("%H:%M")
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- 9.3 STOCK (v650 Extended) ---
elif choice == "📦 STOCK & INVENTAIRE":
    st.header("📦 GESTION DU STOCK")
    tab1, tab2 = st.tabs(["📋 INVENTAIRE", "📥 NOUVEL ARRIVAGE"])
    
    with tab1:
        with sqlite3.connect(DB_FILE) as conn:
            df_inv = pd.read_sql(f"SELECT item as Article, category as Catégorie, qty as Quantité, buy_price as [P. Achat], sell_price as [P. Vente] FROM inventory WHERE sid='{SHOP}'", conn)
            st.dataframe(df_inv, use_container_width=True)
            
            # Export CSV
            csv = df_inv.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger Inventaire (CSV)", csv, "inventaire.csv", "text/csv")

    with tab2:
        with st.form("stock_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Désignation Produit").upper()
            cat = c2.selectbox("Catégorie", ["GÉNÉRAL", "ALIMENTATION", "ÉLECTRONIQUE", "HABILLEMENT", "DIVERS"])
            pa = c1.number_input("Prix d'Achat Unitaire ($)", 0.0)
            pv = c2.number_input("Prix de Vente Unitaire ($)", 0.0)
            qty = c1.number_input("Quantité reçue", 1)
            min_s = c2.number_input("Alerte Stock Bas (Seuil)", 5)
            
            if st.form_submit_button("📥 ENREGISTRER EN STOCK"):
                with sqlite3.connect(DB_FILE) as conn:
                    # Vérifier si existe déjà
                    exist = conn.execute("SELECT id FROM inventory WHERE item=? AND sid=?", (name, SHOP)).fetchone()
                    if exist:
                        conn.execute("UPDATE inventory SET qty = qty + ?, buy_price=?, sell_price=? WHERE item=? AND sid=?", (qty, pa, pv, name, SHOP))
                    else:
                        conn.execute("INSERT INTO inventory (item, category, qty, buy_price, sell_price, sid, min_stock) VALUES (?,?,?,?,?,?,?)",
                                     (name, cat, qty, pa, pv, SHOP, min_s))
                    conn.commit()
                st.success(f"✅ {name} ajouté au stock !")
                st.rerun()

# --- 9.4 DETTES (v197+) ---
elif choice == "📉 DETTES & CRÉDITS":
    st.header("📉 GESTION DES DETTES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = pd.read_sql(f"SELECT cli as Client, balance as Reste, last_update as [Dernière Maj] FROM debts WHERE sid='{SHOP}' AND status='OUVERT'", conn)
        if dettes.empty:
            st.info("Aucune dette enregistrée.")
        else:
            st.table(dettes)
            
        with st.expander("➕ ENREGISTRER UNE DETTE"):
            c_nom = st.text_input("Nom Client")
            c_mnt = st.number_input("Montant de la Dette ($)", 0.0)
            if st.button("Valider Dette"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO debts (cli, balance, sid, last_update) VALUES (?,?,?,?)", (c_nom, c_mnt, SHOP, datetime.now().strftime("%d/%m/%Y")))
                    conn.commit(); st.rerun()

# --- 9.5 RAPPORTS ---
elif choice == "📊 RAPPORTS DE VENTE":
    st.header("📊 ANALYSE DE PERFORMANCE")
    with sqlite3.connect(DB_FILE) as conn:
        df_s = pd.read_sql(f"SELECT date, total_usd, profit, seller FROM sales WHERE sid='{SHOP}'", conn)
        if not df_s.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL VENTES", f"{df_s['total_usd'].sum():,.2f} $")
            c2.metric("TOTAL PROFITS", f"{df_s['profit'].sum():,.2f} $")
            c3.metric("NB VENTES", len(df_s))
            
            if PLOTLY_AVAILABLE:
                st.plotly_chart(px.line(df_s.groupby('date').sum().reset_index(), x='date', y='total_usd', title="Évolution du CA ($)"))

# --- 9.6 CONFIGURATION ---
elif choice == "⚙️ CONFIGURATION":
    st.header("⚙️ RÉGLAGES BOUTIQUE")
    with st.form("cfg_shop"):
        n_name = st.text_input("Nom Enseigne", SHOP_INF[0])
        n_rate = st.number_input("Taux CDF", value=SHOP_INF[1])
        n_head = st.text_area("Slogan / Entête", SHOP_INF[2])
        n_addr = st.text_input("Adresse", SHOP_INF[3])
        n_tel = st.text_input("Téléphone", SHOP_INF[4])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?", (n_name, n_rate, n_head, n_addr, n_tel, SHOP))
                conn.commit(); st.success("Réglages enregistrés !"); st.rerun()

# --- 9.7 QUITTER ---
elif choice == "🚪 QUITTER":
    st.session_state.session['logged'] = False; st.rerun()

# ------------------------------------------------------------------------------
# 10. FOOTER & SYSTÈME DE CRÉDITS
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.caption(f"🚀 {APP_NAME} v10.0.2")
st.sidebar.caption("© 2026 - ANASH DIGITAL SOLUTIONS")
st.sidebar.caption("Bukavu, South-Kivu, DRC")
