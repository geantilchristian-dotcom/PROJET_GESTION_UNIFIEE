# ==============================================================================
# 💎 ANASH ERP v620 - ÉDITION BALIKA BUSINESS STABILISÉE
# ------------------------------------------------------------------------------
# - AUCUNE LIGNE SUPPRIMÉE DE LA v415 (CONSERVÉ TOUT LE STOCK/LOGIQUE)
# - STABILISATION LOGIN : Admin fixe (admin / admin123)
# - ADMIN DASHBOARD : Contrôle total (Activation, Blocage, Suppression, Thèmes)
# - DETTES : Paiement par tranches avec retrait automatique une fois soldé.
# - STYLE : Thème Cobalt (Bleu/Blanc), Marquee, Factures A4/80mm, Cart Coloré.
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

# TENTATIVE D'IMPORT DE PLOTLY POUR L'ADMIN (PROTECTION CRASH)
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES MASTER (v620)
# ------------------------------------------------------------------------------
DB_FILE = "balika_v620_master.db"
def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table Configuration
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', marquee_active INTEGER DEFAULT 1)""")
        
        # Table Utilisateurs (Ajout photo_url pour profil)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, 
            name TEXT, tel TEXT, photo_url TEXT DEFAULT '')""")
        
        # Table Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT DEFAULT 'VOTRE EN-TÊTE ICI', addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        
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
            
        # Table Dépenses
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, amount REAL, 
            date TEXT, sid TEXT, user TEXT)""")
            
        # Données de base
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '6.2.0', 'Cobalt', 1)")
        
        # Migration colonnes si nécessaire
        try: cursor.execute("ALTER TABLE system_config ADD COLUMN marquee_active INTEGER DEFAULT 1")
        except: pass
        try: cursor.execute("ALTER TABLE shops ADD COLUMN head TEXT DEFAULT 'VOTRE EN-TÊTE ICI'")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN photo_url TEXT DEFAULT ''")
        except: pass
        
        # COMPTE ADMIN STABLE (admin / admin123)
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users (uid, pwd, role, shop, status, name, tel) VALUES (?,?,?,?,?,?,?)", 
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
    "Forest": "#1b5e20", "Bordeaux": "#880e4f", "Ocean": "linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)",
    "Purple Dream": "linear-gradient(135deg, #4568dc 0%, #b06ab3 100%)",
    "Luxury Gold": "linear-gradient(135deg, #bf953f 0%, #fcf6ba 50%, #b38728 100%)",
    "Carbon": "#212121", "Classic Blue": "#0d47a1", "Deep Space": "linear-gradient(135deg, #000000 0%, #434343 100%)",
    "Neon Green": "linear-gradient(135deg, #000000 0%, #00ff00 500%)",
    "Soft Rose": "linear-gradient(135deg, #f857a6 0%, #ff5858 100%)",
    "Vibrant Teal": "#008080", "Steel": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    "Cyberpunk": "linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%)",
    "Solar": "linear-gradient(135deg, #f2994a 0%, #f2c94c 100%)",
    "Silver": "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)"
}

# ------------------------------------------------------------------------------
# 4. INTERFACE ET STYLES (OPTIMISÉ MOBILE)
# ------------------------------------------------------------------------------
SYS_DATA = load_sys()
APP_NAME, MARQUEE_TEXT, CURRENT_THEME, MARQUEE_ON = SYS_DATA[0], SYS_DATA[1], SYS_DATA[2], SYS_DATA[3]
SELECTED_BG = THEMES.get(CURRENT_THEME, THEMES["Cobalt"])
st.set_page_config(page_title=APP_NAME, layout="wide")

def apply_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background: {SELECTED_BG}; color: white !important; font-size: 16px; }}
        [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid #00d4ff; width: 260px !important; }}
        h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
        input {{ 
            text-align: center; border-radius: 12px !important; font-weight: bold; 
            background-color: white !important; color: black !important; 
            height: 45px !important; font-size: 18px !important;
        }}
        .marquee-bar {{
            background: #000; color: #00ff00; padding: 12px; font-weight: bold;
            border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }}
        .cobalt-card {{
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px);
            padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3);
            margin-bottom: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        }}
        .white-cart {{
            background: white !important; color: black !important; padding: 15px;
            border-radius: 15px; border: 5px solid #004a99; margin: 10px 0;
        }}
        .white-cart * {{ color: black !important; font-weight: bold; }}
        .total-frame {{
            border: 4px solid #00ff00; background: #000; padding: 10px;
            border-radius: 15px; margin: 10px 0; box-shadow: 0 0 10px #00ff00;
        }}
        .total-text {{ color: #00ff00; font-size: 38px; font-weight: bold; }}
        .stButton > button {{
            width: 100%; height: 55px; border-radius: 15px; font-size: 18px;
            background: linear-gradient(to right, #007bff, #00d4ff);
            color: white !important; border: none; font-weight: bold; margin-bottom: 5px;
        }}
        .invoice-80mm {{
            background: white !important; color: black !important; padding: 10px;
            font-family: 'Courier New'; width: 100%; max-width: 300px; margin: auto; border: 1px dashed #000; font-size: 13px;
        }}
        .invoice-a4 {{
            background: white !important; color: black !important; padding: 40px;
            font-family: 'Arial'; width: 100%; max-width: 800px; margin: auto; border: 1px solid #ccc;
        }}
        .invoice-80mm *, .invoice-a4 * {{ color: black !important; text-align: left; }}
        .fac-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .fac-table th, .fac-table td {{ border-bottom: 1px solid #eee; padding: 5px; color: black !important; }}
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

# ------------------------------------------------------------------------------
# 6. CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_new = st.tabs(["🔑 CONNEXION", "📝 DEMANDE D'ACCÈS"])
        
        with tab_log:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            u_name = st.text_input("IDENTIFIANT").lower().strip()
            u_pass = st.text_input("MOT DE PASSE", type="password")
            if st.button("🚀 ACCÉDER AU SYSTÈME"):
                with sqlite3.connect(DB_FILE) as conn:
                    user = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_name,)).fetchone()
                    if user and get_hash(u_pass) == user[0]:
                        if user[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u_name, 'role': user[1], 'shop_id': user[2]})
                            log_event(u_name, "Connexion", user[2]); st.rerun()
                        else: st.error("❌ Compte Bloqué ou en attente d'activation")
                    else: st.error("❌ Erreur Identifiants")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_new:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            n_uid = st.text_input("ID Souhaité")
            n_shop = st.text_input("Nom de votre Entreprise")
            n_pass = st.text_input("Créer un Mot de Passe", type="password")
            if st.button("📩 ENVOYER LA DEMANDE"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name, tel) VALUES (?,?,?,?,?,?,?)", 
                                     (n_uid.lower(), get_hash(n_pass), 'GERANT', n_uid.lower(), 'EN_ATTENTE', n_shop, ''))
                        conn.commit(); st.success("✅ Demande envoyée ! Attendez la validation de l'administrateur.")
                    except: st.error("❌ Cet Identifiant est déjà utilisé")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. ESPACE SUPER ADMINISTRATEUR (CONTRÔLE TOTAL)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER ADMIN")
    a_nav = st.sidebar.radio("Navigation", ["👥 Abonnés & Boutiques", "📊 Statistiques Globales", "⚙️ Paramètres Système", "🎨 Thèmes & Design", "🔐 Sécurité Admin", "🚪 Déconnexion"])
    
    if a_nav == "👥 Abonnés & Boutiques":
        st.header("👥 GESTION DES PARTENAIRES")
        with sqlite3.connect(DB_FILE) as conn:
            # Stats rapides
            total_u = conn.execute("SELECT COUNT(*) FROM users WHERE uid != 'admin'").fetchone()[0]
            total_a = conn.execute("SELECT COUNT(*) FROM users WHERE status='ACTIF' AND uid != 'admin'").fetchone()[0]
            
            c1, c2 = st.columns(2)
            c1.metric("TOTAL INSCRITS", total_u)
            c2.metric("BOUTIQUES ACTIVES", total_a)
            
            st.markdown("### 📋 LISTE DES COMPTES")
            df_users = pd.read_sql("SELECT uid as Login, name as Boutique, role as Role, status as Etat FROM users WHERE uid != 'admin'", conn)
            st.dataframe(df_users, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### ⚡ ACTIONS DE GESTION")
            users_list = conn.execute("SELECT uid, name, status FROM users WHERE uid != 'admin'").fetchall()
            for u_id, u_name, u_stat in users_list:
                with st.expander(f"⚙️ Gérer : {u_name} ({u_id}) - [{u_stat}]"):
                    col_a, col_b, col_c, col_d = st.columns(4)
                    if col_a.button("✅ ACTIVER", key=f"ac_{u_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (u_id,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (u_id, u_name, u_id))
                        conn.commit(); st.success(f"{u_id} Activé !"); st.rerun()
                    if col_b.button("🚫 BLOQUER", key=f"bl_{u_id}"):
                        conn.execute("UPDATE users SET status='INACTIF' WHERE uid=?", (u_id,)); conn.commit(); st.rerun()
                    if col_c.button("🗑️ SUPPRIMER", key=f"de_{u_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (u_id,)); conn.commit(); st.rerun()
                    if col_d.button("🔑 RESET", key=f"rs_{u_id}"):
                        conn.execute("UPDATE users SET pwd=? WHERE uid=?", (get_hash("1234"), u_id))
                        conn.commit(); st.info("Pass réinitialisé à '1234'")

    elif a_nav == "📊 Statistiques Globales":
        st.header("📊 PERFORMANCE DU RÉSEAU")
        with sqlite3.connect(DB_FILE) as conn:
            ca_global = conn.execute("SELECT SUM(total_usd) FROM sales").fetchone()[0] or 0
            st.markdown(f"<div class='cobalt-card'><h2>CHIFFRE D'AFFAIRES GLOBAL</h2><h1>{ca_global:,.2f} $</h1></div>", unsafe_allow_html=True)
            
            st.markdown("### 🏆 Top Boutiques")
            df_top = pd.read_sql("SELECT sid as Boutique, SUM(total_usd) as Total FROM sales GROUP BY sid ORDER BY Total DESC", conn)
            st.table(df_top)

    elif a_nav == "⚙️ Paramètres Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys_config_form"):
            n_app = st.text_input("Nom de l'Application", APP_NAME)
            n_mar = st.text_area("Texte du Marquee", MARQUEE_TEXT)
            m_on = st.checkbox("Afficher le Marquee", value=bool(MARQUEE_ON))
            if st.form_submit_button("SAUVEGARDER LES CHANGEMENTS"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", (n_app, n_mar, 1 if m_on else 0))
                st.rerun()

    elif a_nav == "🎨 Thèmes & Design":
        st.header("🎨 PERSONNALISATION VISUELLE")
        new_theme = st.selectbox("Sélectionner un Thème", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
        if st.button("APPLIQUER LE THÈME"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=? WHERE id=1", (new_theme,))
                conn.commit(); st.rerun()

    elif a_nav == "🔐 Sécurité Admin":
        st.header("🔐 ACCÈS SUPER ADMIN")
        with st.form("sec_admin"):
            new_login = st.text_input("Identifiant Admin", "admin")
            new_pass = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("MODIFIER LES ACCÈS"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid='admin'", (new_login.lower(), get_hash(new_pass)))
                    conn.commit(); st.success("Accès mis à jour !"); time.sleep(1); st.session_state.session['logged_in'] = False; st.rerun()

    if a_nav == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. LOGIQUE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, addr, tel, rccm, idnat, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("BOUTIQUE", 2800.0, "ADRESSE", "000", "", "", "BIENVENUE")

# MENU NAVIGATION
nav_list = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "💸 DÉPENSES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    # Affichage Profil
    with sqlite3.connect(DB_FILE) as conn:
        u_prof = conn.execute("SELECT photo_url FROM users WHERE uid=?", (st.session_state.session['user'],)).fetchone()
        if u_prof and u_prof[0]: st.image(u_prof[0], width=80)
    
    st.markdown(f"<div class='cobalt-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav_list)
    if st.button("⬅️ RETOUR"):
        if len(st.session_state.session['page_history']) > 1:
            st.session_state.session['page_history'].pop(); st.rerun()

# --- 8.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:60px; margin-bottom:0;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        stats = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()
        dep = conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()
        ca = stats[0] if stats[0] else 0
        total_dep = dep[0] if dep[0] else 0
        st.markdown(f"<div class='cobalt-card'><h3>SOLDE DU JOUR (NET)</h3><h1 style='font-size:45px; color:#00ff00 !important;'>{(ca-total_dep):,.2f} $</h1><p>Recette: {ca}$ | Dépenses: {total_dep}$</p></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE & FACTURES ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        col_back, col_share = st.columns(2)
        if col_back.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        
        mode_fac = st.radio("FORMAT", ["TICKET 80mm", "FACTURE A4"], horizontal=True)
        if mode_fac == "TICKET 80mm":
            invoice_html = f"<center><div class='invoice-80mm'><h3>{sh_inf[6]}</h3><hr><b>REF: {inv['ref']}</b><br>Client: {inv['cli']}<br><table class='fac-table'>"
            for it, d in inv['items'].items(): invoice_html += f"<tr><td>{it}</td><td>{d['q']}</td><td>{(d['q']*d['p']):.1f}</td></tr>"
            invoice_html += f"</table><hr><b>TOTAL: {inv['total_val']:.2f} {inv['dev']}</b></div></center>"
        else:
            invoice_html = f"<div class='invoice-a4'><h1>{sh_inf[0]}</h1><p>{sh_inf[6]}</p><hr><h4>FACTURE N° {inv['ref']}</h4><p>Client: {inv['cli']} | Date: {inv['date']}</p><table class='fac-table'><tr><th>Désignation</th><th>Qté</th><th>Prix U.</th><th>Total</th></tr>"
            for it, d in inv['items'].items(): invoice_html += f"<tr><td>{it}</td><td>{d['q']}</td><td>{d['p']}$</td><td>{(d['q']*d['p']):.2f}$</td></tr>"
            invoice_html += f"</table><hr><h3>TOTAL : {inv['total_val']:.2f} {inv['dev']}</h3></div>"
        st.markdown(invoice_html, unsafe_allow_html=True)
    else:
        devise = st.radio("MONNAIE DE PAIEMENT", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_art = st.selectbox("ARTICLES EN STOCK", ["---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if sel_art != "---" and st.button("➕ AJOUTER AU PANIER"):
                name = sel_art.split(" (")[0]
                info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                st.session_state.session['cart'][name] = {'p': info[0], 'q': 1, 'max': info[1]}
                st.rerun()
        
        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            for it, d in list(st.session_state.session['cart'].items()):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(it)
                if c2.button("➖", key=f"m_{it}"):
                    st.session_state.session['cart'][it]['q'] -= 1
                    if st.session_state.session['cart'][it]['q'] <= 0: del st.session_state.session['cart'][it]
                    st.rerun()
                c3.write(d['q'])

            total_u = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
            p_final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{p_final:,.0f} {devise}</span></center></div>", unsafe_allow_html=True)
            
            with st.form("pay_form"):
                c_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                c_pay = st.number_input(f"MONTANT REÇU ({devise})", value=float(p_final))
                if st.form_submit_button("VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    r_usd = c_pay if devise == "USD" else c_pay / sh_inf[1]
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, c_name, total_u, r_usd, total_u-r_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if (total_u - r_usd) > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)", (c_name, total_u-r_usd, ref, sid, datetime.now().strftime("%d/%m/%Y")))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': c_name, 'total_val': p_final, 'dev': devise, 'items': st.session_state.session['cart'], 'date': datetime.now().strftime("%d/%m/%Y %H:%M")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK ---
elif choice == "📦 STOCK":
    st.header("📦 INVENTAIRE")
    with sqlite3.connect(DB_FILE) as conn:
        df_stock = pd.read_sql(f"SELECT id, item as Article, qty as Quantité, sell_price as 'PV $', buy_price as 'PA $' FROM inventory WHERE sid='{sid}'", conn)
        st.dataframe(df_stock.drop(columns=['id']), use_container_width=True)
        
        with st.expander("➕ AJOUTER / MODIFIER UN PRODUIT"):
            with st.form("add_stock"):
                n_art = st.text_input("Désignation").upper()
                p_buy = st.number_input("Prix Achat ($)")
                p_sell = st.number_input("Prix Vente ($)")
                q_init = st.number_input("Quantité", 1)
                if st.form_submit_button("ENREGISTRER PRODUIT"):
                    # Check if exists to update or insert
                    ex = conn.execute("SELECT id FROM inventory WHERE item=? AND sid=?", (n_art, sid)).fetchone()
                    if ex:
                        conn.execute("UPDATE inventory SET qty=qty+?, sell_price=?, buy_price=? WHERE id=?", (q_init, p_sell, p_buy, ex[0]))
                    else:
                        conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_art, q_init, p_buy, p_sell, sid))
                    conn.commit(); st.rerun()
        
        st.markdown("---")
        st.subheader("🗑️ SUPPRESSION")
        del_item = st.selectbox("Sélectionner article à supprimer", ["---"] + df_stock['Article'].tolist())
        if del_item != "---" and st.button("SUPPRIMER DÉFINITIVEMENT"):
            conn.execute("DELETE FROM inventory WHERE item=? AND sid=?", (del_item, sid))
            conn.commit(); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 PAIEMENT DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.info("Aucune dette en cours.")
        for di, dc, db, dr in dettes:
            with st.expander(f"👤 {dc} | Reste : {db:,.2f} $ (Réf: {dr})"):
                pay = st.number_input(f"Acompte ($)", 0.0, db, key=f"pay_{di}")
                if st.button("ENREGISTRER LE PAIEMENT", key=f"btn_{di}"):
                    n_bal = db - pay
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (n_bal, datetime.now().strftime("%d/%m/%Y"), di))
                    if n_bal <= 0.01:
                        conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.success("Paiement enregistré !"); st.rerun()

# --- 8.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 GESTION DES CHARGES")
    with st.form("exp_f"):
        motif = st.text_input("Motif de la dépense")
        montant = st.number_input("Montant ($)", min_value=0.1)
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)", (motif, montant, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.success("Dépense enregistrée !"); st.rerun()

# --- 8.6 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES ET ANALYSES")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT date as Date, ref as Facture, cli as Client, total_usd as 'Total $', seller as Vendeur FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True)
        
        c1, c2 = st.columns(2)
        csv = df.to_csv(index=False).encode('utf-8')
        c1.download_button("📥 EXPORTER CSV", csv, "rapport_ventes.csv", "text/csv")
        if c2.button("🖨️ IMPRIMER RAPPORT"): st.info("Utilisez l'option d'impression de votre navigateur (Ctrl+P)")

# --- 8.7 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n in vendeurs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"👤 {v_n} (ID: {v_id})")
            if col2.button("🗑️", key=f"del_v_{v_id}"):
                conn.execute("DELETE FROM users WHERE uid=?", (v_id,)); conn.commit(); st.rerun()
    
    with st.expander("➕ AJOUTER UN VENDEUR"):
        with st.form("new_v"):
            v_id, v_n, v_p = st.text_input("Identifiant (Login)"), st.text_input("Nom Complet"), st.text_input("Mot de Passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name, tel) VALUES (?,?,?,?,?,?,?)", 
                                     (v_id.lower(), get_hash(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                        conn.commit(); st.success("Vendeur ajouté !"); st.rerun()
                    except: st.error("ID déjà utilisé")

# --- 8.8 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("cfg_shop"):
        n_name = st.text_input("Nom de l'Entreprise", sh_inf[0])
        n_head = st.text_area("En-tête des Factures", sh_inf[6])
        n_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        n_pic = st.text_input("URL Photo de Profil (Lien Image)", value="")
        if st.form_submit_button("METTRE À JOUR LES INFOS"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, head=?, rate=? WHERE sid=?", (n_name, n_head, n_rate, sid))
                if n_pic: conn.execute("UPDATE users SET photo_url=? WHERE uid=?", (n_pic, st.session_state.session['user']))
                conn.commit(); st.success("Réglages enregistrés !"); st.rerun()

# --- 8.9 SÉCURITÉ COMPTE ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 SÉCURITÉ DU COMPTE")
    with st.form("pwd_change"):
        curr_id = st.session_state.session['user']
        new_uid = st.text_input("Changer mon Identifiant", value=curr_id)
        new_pwd = st.text_input("Nouveau Mot de Passe", type="password")
        if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_uid.lower(), get_hash(new_pwd), curr_id))
                    conn.commit(); st.success("Compte mis à jour ! Reconnexion requise."); time.sleep(2)
                    st.session_state.session['logged_in'] = False; st.rerun()
                except: st.error("Cet identifiant est déjà pris.")

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"v6.2.0 | BALIKA BUSINESS ERP STABLE")
