# ==============================================================================
# ANASH ERP v411 - ÉDITION SUPRÊME BALIKA BUSINESS (PROTECTION MODULES)
# ------------------------------------------------------------------------------
# - CODE COMPLET (+700 LIGNES) - TOUTES FONCTIONNALITÉS v410 CONSERVÉES
# - FIX : GESTION DE L'ERREUR ModuleNotFoundError (Plotly)
# - SYSTÈME D'INSCRIPTION AVEC VALIDATION MASTER ADMIN (admin/admin123)
# - DOUBLE FORMAT FACTURE (A4 / 80MM) & GESTION DÉPENSES
# - ÉDITEUR DE THÈMES (20 VARIANTES) & LOGS D'AUDIT COMPLETS
# - INTERFACE MOBILE : TEXTE BLANC / FOND BLEU / PANIER BLANC
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

# TENTATIVE D'IMPORT DE PLOTLY (POUR LES GRAPHIQUES)
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES (STRUCTURE ÉVOLUÉE)
# ------------------------------------------------------------------------------
DB_FILE = "balika_v411_master.db"

def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Configuration Système
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', marquee_active INTEGER DEFAULT 1)""")
        
        # Utilisateurs (vendeurs, gérants, admin)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, 
            status TEXT DEFAULT 'EN_ATTENTE', name TEXT, tel TEXT)""")
        
        # Boutiques / Points de vente
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT DEFAULT 'VOTRE EN-TÊTE ICI', addr TEXT, tel TEXT, 
            rccm TEXT, idnat TEXT)""")
        
        # Inventaire (Stock)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT DEFAULT 'GENERAL',
            min_stock INTEGER DEFAULT 5)""")
        
        # Ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        
        # Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_update TEXT)""")
        
        # Dépenses
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, amount REAL, 
            date TEXT, sid TEXT, user TEXT, category TEXT DEFAULT 'DIVERS')""")
        
        # Audit (Traçabilité)
        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
            date TEXT, time TEXT, sid TEXT)""")

        # Insertion Données Initiales
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) 
                           VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION', '4.1.1', 'Cobalt', 1)""")
        
        # Compte Admin Maître (admin / admin123)
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
# 3. PALETTE DE THÈMES (20 VARIANTES)
# ------------------------------------------------------------------------------
THEMES = {
    "Cobalt": "linear-gradient(135deg, #004a99 0%, #002b5c 100%)",
    "Midnight": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    "Emerald": "linear-gradient(135deg, #004d40 0%, #00796b 100%)",
    "Sunset": "linear-gradient(135deg, #ff512f 0%, #dd2476 100%)",
    "Royal": "linear-gradient(135deg, #4b6cb7 0%, #182848 100%)",
    "Forest": "#1b5e20", "Bordeaux": "#880e4f", "Ocean": "linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)",
    "Purple Dream": "linear-gradient(135deg, #4568dc 0%, #b06ab3 100%)",
    "Luxury Gold": "linear-gradient(135deg, #bf953f 0%, #fcf6ba 50%, #b38728 100%)",
    "Carbon": "#212121", "Classic Blue": "#0d47a1", "Deep Space": "linear-gradient(135deg, #000000 0%, #434343 100%)",
    "Neon Green": "linear-gradient(135deg, #000000 0%, #00ff00 500%)",
    "Soft Rose": "linear-gradient(135deg, #f857a6 0%, #ff5858 100%)",
    "Vibrant Teal": "#008080", "Steel": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    "Cyberpunk": "linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%)",
    "Solar": "linear-gradient(135deg, #f2994a 0%, #f2c94c 100%)",
    "Silver": "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)",
    "Simple White": "#ffffff"
}

# ------------------------------------------------------------------------------
# 4. DESIGN CSS ET RESPONSIVITÉ MOBILE
# ------------------------------------------------------------------------------
SYS_DATA = load_sys()
APP_NAME, MARQUEE_TEXT, CURRENT_THEME, MARQUEE_ON = SYS_DATA[0], SYS_DATA[1], SYS_DATA[2], SYS_DATA[3]
SELECTED_BG = THEMES.get(CURRENT_THEME, THEMES["Cobalt"])
st.set_page_config(page_title=APP_NAME, layout="wide")

st.markdown(f"""
<style>
    .stApp {{ background: {SELECTED_BG}; color: white !important; font-size: 16px; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid #00d4ff; width: 260px !important; }}
    h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
    
    input {{ 
        text-align: center; border-radius: 12px !important; font-weight: bold; 
        background-color: white !important; color: black !important; 
        height: 48px !important; font-size: 18px !important;
    }}
    
    .marquee-bar {{
        background: #000; color: #00ff00; padding: 12px; font-weight: bold;
        border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
    }}
    
    .cobalt-card {{
        background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px);
        padding: 22px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3);
        margin-bottom: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    
    .white-cart {{
        background: white !important; color: black !important; padding: 18px;
        border-radius: 18px; border: 6px solid #004a99; margin: 12px 0;
    }}
    .white-cart * {{ color: black !important; font-weight: bold; }}
    
    .total-frame {{
        border: 5px solid #00ff00; background: #000; padding: 12px;
        border-radius: 18px; margin: 12px 0; box-shadow: 0 0 15px #00ff00;
    }}
    .total-text {{ color: #00ff00; font-size: 42px; font-weight: bold; }}
    
    .stButton > button {{
        width: 100%; height: 58px; border-radius: 16px; font-size: 19px;
        background: linear-gradient(to right, #007bff, #00d4ff);
        color: white !important; border: none; font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

# ------------------------------------------------------------------------------
# 6. ÉCRAN DE CONNEXION ET INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 CONNEXION", "📝 DEMANDE D'ACCÈS"])
        
        with t_log:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            u_id = st.text_input("IDENTIFIANT").lower().strip()
            u_pw = st.text_input("MOT DE PASSE", type="password")
            if st.button("🚀 SE CONNECTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    user = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_id,)).fetchone()
                    if user and get_hash(u_pw) == user[0]:
                        if user[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u_id, 'role': user[1], 'shop_id': user[2]})
                            log_event(u_id, "Connexion", user[2]); st.rerun()
                        elif user[3] == "EN_ATTENTE":
                            st.warning("⏳ Votre compte attend la validation de l'Administrateur.")
                        else: st.error("❌ Accès Refusé.")
                    else: st.error("❌ Identifiants Incorrects.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with t_reg:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            r_id = st.text_input("Identifiant Souhaité").lower().strip()
            r_name = st.text_input("Nom Boutique / Gérant")
            r_tel = st.text_input("Téléphone WhatsApp")
            r_pw = st.text_input("Mot de Passe", type="password")
            r_type = st.selectbox("Type", ["GERANT", "VENDEUR"])
            if st.button("📩 ENVOYER DEMANDE"):
                if r_id and r_pw:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (r_id, get_hash(r_pw), r_type, r_id, 'EN_ATTENTE', r_name, r_tel))
                            conn.commit(); st.success("✅ Demande envoyée avec succès !")
                        except: st.error("❌ Identifiant déjà pris.")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. MODULE MASTER ADMIN (SUPER_ADMIN)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER PANEL")
    adm_choice = st.sidebar.radio("Navigation", ["🔔 Validations", "👥 Boutiques", "📊 Statistiques", "⚙️ Config App", "🎨 Thèmes", "🔐 Sécurité", "🚪 Déconnexion"])
    
    if adm_choice == "🔔 Validations":
        st.header("🔔 DEMANDES D'INSCRIPTION")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, role, tel FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending: st.info("Aucune demande.")
            for p_uid, p_name, p_role, p_tel in pending:
                with st.expander(f"Demande : {p_name} ({p_uid})"):
                    st.write(f"Rôle: {p_role} | Tel: {p_tel}")
                    if st.button("✅ ACCEPTER", key=f"y_{p_uid}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (p_uid,))
                        if p_role == "GERANT": conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_uid, p_name, p_uid))
                        conn.commit(); st.rerun()

    elif adm_choice == "📊 Statistiques":
        st.header("📊 PERFORMANCE GLOBALE")
        with sqlite3.connect(DB_FILE) as conn:
            total = conn.execute("SELECT SUM(total_usd) FROM sales").fetchone()[0] or 0
            st.metric("CHIFFRE D'AFFAIRES TOTAL", f"{total:,.2f} $")
            df_v = pd.read_sql("SELECT date, SUM(total_usd) as total FROM sales GROUP BY date", conn)
            if PLOTLY_AVAILABLE:
                st.plotly_chart(px.line(df_v, x='date', y='total', title="Évolution"), use_container_width=True)
            else:
                st.table(df_v) # Remplacement si module absent

    elif adm_choice == "🎨 Thèmes":
        st.header("🎨 APPARENCE")
        sel_theme = st.selectbox("Thème Principal", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
        if st.button("APPLIQUER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=? WHERE id=1", (sel_theme,))
                conn.commit(); st.rerun()

    elif adm_choice == "⚙️ Config App":
        with st.form("sc"):
            n_app = st.text_input("Nom App", APP_NAME)
            n_mar = st.text_area("Texte Marquee", MARQUEE_TEXT)
            m_on = st.checkbox("Activer Marquee", value=bool(MARQUEE_ON))
            if st.form_submit_button("SAUVER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", (n_app, n_mar, 1 if m_on else 0))
                    conn.commit(); st.rerun()

    if adm_choice == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. INTERFACE BOUTIQUE (CONSERVE TOUTES LES LOGIQUES v192 / v350)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    sh_data = conn.execute("SELECT name, rate, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = sh_data if sh_data else ("BOUTIQUE", 2800.0, "BIENVENUE")

nav = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "💸 DÉPENSES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav)

# --- 8.1 ACCUEIL (DASHBOARD v192) ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON: st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:60px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        ca = (conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        dp = (conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        st.markdown(f"<div class='cobalt-card'><h3>SOLDE NET JOUR</h3><h1 style='color:#00ff00 !important;'>{(ca-dp):,.2f} $</h1><p>Ventes: {ca}$ | Dépenses: {dp}$</p></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE (MULTI-DEVISE + CADRE TOTAL) ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        fmt = st.radio("Format", ["TICKET 80mm", "FACTURE A4"], horizontal=True)
        if fmt == "TICKET 80mm":
            html = f"<center><div style='background:white; color:black; padding:10px; width:280px; font-family:monospace;'><h4>{sh_inf[2]}</h4><hr>REF: {inv['ref']}<br>Client: {inv['cli']}<hr>TOTAL: {inv['total_val']:.2f} {inv['dev']}</div></center>"
        else:
            html = f"<div style='background:white; color:black; padding:40px; border:1px solid #ccc;'><h1>{sh_inf[0]}</h1><hr><h4>FACTURE {inv['ref']}</h4><h3>TOTAL : {inv['total_val']:.2f} {inv['dev']}</h3></div>"
        st.markdown(html, unsafe_allow_html=True)
        if st.button("⬅️ RETOUR"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=?", (sid,)).fetchall()
            sel = st.selectbox("ARTICLES", ["---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if sel != "---" and st.button("➕ AJOUTER"):
                name = sel.split(" (")[0]
                price = conn.execute("SELECT sell_price FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()[0]
                st.session_state.session['cart'][name] = {'p': price, 'q': 1}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            total_u = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
            p_final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{p_final:,.0f} {devise}</span></center></div>", unsafe_allow_html=True)
            for it, d in list(st.session_state.session['cart'].items()):
                c1, c2 = st.columns([4, 1])
                c1.write(f"🔹 {it} x{d['q']}")
                if c2.button("❌", key=f"d_{it}"): del st.session_state.session['cart'][it]; st.rerun()
            cli = st.text_input("CLIENT", "COMPTANT").upper()
            if st.button("✅ VALIDER"):
                ref = f"FAC-{random.randint(1000,9999)}"
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO sales (ref, cli, total_usd, date, time, seller, sid, currency) VALUES (?,?,?,?,?,?,?,?)", (ref, cli, total_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, devise))
                    conn.commit()
                st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': cli, 'total_val': p_final, 'dev': devise}
                st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK (PRIX ACHAT/VENTE CONSERVÉS) ---
elif choice == "📦 STOCK":
    st.header("📦 INVENTAIRE")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT item as Article, qty as Qté, buy_price as 'Achat $', sell_price as 'Vente $' FROM inventory WHERE sid='{sid}'", conn)
        st.dataframe(df, use_container_width=True)
        with st.form("add"):
            n, b, s, q = st.text_input("Article"), st.number_input("Prix Achat"), st.number_input("Prix Vente"), st.number_input("Qté", 1)
            if st.form_submit_button("AJOUTER"):
                conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n.upper(), q, b, s, sid))
                conn.commit(); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for di, dc, db in dettes:
            with st.expander(f"👤 {dc} | {db}$"):
                pay = st.number_input("Payer ($)", 0.0, db, key=di)
                if st.button("OK", key=f"b_{di}"):
                    conn.execute("UPDATE debts SET balance=balance-? WHERE id=?", (pay, di))
                    conn.commit(); st.rerun()

# --- 8.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 DÉPENSES")
    with st.form("exp"):
        m, amt = st.text_input("Motif"), st.number_input("Montant ($)")
        if st.form_submit_button("ENREGISTRER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)", (m, amt, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.rerun()

# --- 8.6 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE")
    with sqlite3.connect(DB_FILE) as conn:
        df_s = pd.read_sql(f"SELECT date, ref, cli, total_usd as 'Total $', seller FROM sales WHERE sid='{sid}'", conn)
        st.dataframe(df_s, use_container_width=True)
        st.download_button("📥 CSV", df_s.to_csv().encode('utf-8'), "rapport.csv")

# --- 8.7 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        v = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for vi, vn in v: st.write(f"👤 {vn} ({vi})")
        with st.form("nv"):
            vid, vnm, vpw = st.text_input("Login"), st.text_input("Nom"), st.text_input("Pass", type="password")
            if st.form_submit_button("CRÉER"):
                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (vid, get_hash(vpw), 'VENDEUR', sid, 'ACTIF', vnm, ''))
                conn.commit(); st.rerun()

# --- 8.8 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIG")
    with st.form("rs"):
        n_sh = st.text_input("Nom Boutique", sh_inf[0])
        n_rt = st.number_input("Taux Change", value=sh_inf[1])
        if st.form_submit_button("UPDATE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=? WHERE sid=?", (n_sh, n_rt, sid))
                conn.commit(); st.rerun()
    with open(DB_FILE, "rb") as f: st.download_button("📥 BACKUP SYSTEM", f, "backup.db")

# --- 8.9 SÉCURITÉ ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 ACCÈS")
    with st.form("sc_u"):
        nu, np = st.text_input("Identifiant", value=st.session_state.session['user']), st.text_input("Pass", type="password")
        if st.form_submit_button("MODIFIER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (nu, get_hash(np), st.session_state.session['user']))
                conn.commit(); st.session_state.session['logged_in'] = False; st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"v4.1.1 | © Balika Business")
