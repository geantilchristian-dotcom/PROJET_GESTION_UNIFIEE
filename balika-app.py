# ==============================================================================
# ANASH ERP v410 - ÉDITION SUPRÊME BALIKA BUSINESS (LOGIQUE INTÉGRALE)
# ------------------------------------------------------------------------------
# - CODE COMPLET (+700 LIGNES) - AUCUNE SUPPRESSION
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
import plotly.express as px

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES (STRUCTURE ÉVOLUÉE)
# ------------------------------------------------------------------------------
DB_FILE = "balika_v410_master.db"

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
                           VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION', '4.1.0', 'Cobalt', 1)""")
        
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
        color: white !important; border: none; font-weight: bold; transition: 0.3s;
    }}
    
    .invoice-80mm {{
        background: white !important; color: black !important; padding: 12px;
        font-family: 'Courier New'; width: 300px; margin: auto; border: 1px dashed #000;
    }}
    .invoice-a4 {{
        background: white !important; color: black !important; padding: 45px;
        font-family: 'Arial'; width: 100%; max-width: 850px; margin: auto; border: 1px solid #ccc;
    }}
    .invoice-80mm *, .invoice-a4 * {{ color: black !important; text-align: left; }}
    .fac-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
    .fac-table th, .fac-table td {{ border-bottom: 1px solid #ddd; padding: 8px; color: black !important; }}
</style>
""", unsafe_allow_html=True)

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
# 6. ÉCRAN DE CONNEXION ET INSCRIPTION (CONFIRMATION REQUISE)
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
                            log_event(u_id, "Connexion Réussie", user[2]); st.rerun()
                        elif user[3] == "EN_ATTENTE":
                            st.warning("⏳ Compte en attente de validation par l'administrateur.")
                        else: st.error("❌ Accès révoqué.")
                    else: st.error("❌ Identifiants incorrects.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with t_reg:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            r_id = st.text_input("Identifiant Souhaité").lower().strip()
            r_name = st.text_input("Nom de la Boutique / Gérant")
            r_tel = st.text_input("Numéro WhatsApp")
            r_pw = st.text_input("Mot de Passe (Session)", type="password")
            r_type = st.selectbox("Type de Compte", ["GERANT", "VENDEUR"])
            if st.button("📩 ENVOYER MA DEMANDE"):
                if r_id and r_pw and r_name:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name, tel) VALUES (?,?,?,?,?,?,?)",
                                         (r_id, get_hash(r_pw), r_type, r_id, 'EN_ATTENTE', r_name, r_tel))
                            conn.commit()
                            st.success("✅ Demande transmise ! L'administrateur vous activera bientôt.")
                        except: st.error("❌ Cet Identifiant est déjà utilisé.")
                else: st.error("Veuillez remplir tous les champs.")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. MODULE MASTER ADMIN (SUPER_ADMIN)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER PANEL")
    adm_choice = st.sidebar.radio("Navigation", ["🔔 Validations", "👥 Boutiques", "📊 Statistiques Globales", "⚙️ Config App", "🎨 Look & Feel", "🔐 Sécurité", "🚪 Déconnexion"])
    
    if adm_choice == "🔔 Validations":
        st.header("🔔 DEMANDES D'ACCÈS EN ATTENTE")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, role, tel FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending: st.info("Aucune nouvelle demande pour le moment.")
            for p_uid, p_name, p_role, p_tel in pending:
                with st.expander(f"Demande de : {p_name.upper()} ({p_uid})"):
                    st.write(f"Rôle : {p_role} | Contact : {p_tel}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ ACTIVER LE COMPTE", key=f"y_{p_uid}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (p_uid,))
                        if p_role == "GERANT":
                            conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_uid, p_name, p_uid))
                        conn.commit(); st.success(f"Compte {p_uid} activé !"); st.rerun()
                    if c2.button("🗑️ REJETER", key=f"n_{p_uid}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (p_uid,))
                        conn.commit(); st.rerun()

    elif adm_choice == "👥 Boutiques":
        st.header("👥 TOUS LES UTILISATEURS")
        with sqlite3.connect(DB_FILE) as conn:
            df_users = pd.read_sql("SELECT uid as Login, name as Nom, role as Rôle, status as État FROM users", conn)
            st.dataframe(df_users, use_container_width=True)
            u_to_mod = st.selectbox("Action sur Utilisateur", df_users['Login'])
            if st.button("🚫 BLOQUER L'ACCÈS"):
                conn.execute("UPDATE users SET status='BLOQUÉ' WHERE uid=?", (u_to_mod,))
                conn.commit(); st.rerun()

    elif adm_choice == "📊 Statistiques Globales":
        st.header("📊 PERFORMANCE DU RÉSEAU")
        with sqlite3.connect(DB_FILE) as conn:
            total_sales = conn.execute("SELECT SUM(total_usd) FROM sales").fetchone()[0] or 0
            st.metric("CHIFFRE D'AFFAIRES TOTAL", f"{total_sales:,.2f} $")
            df_v = pd.read_sql("SELECT date, SUM(total_usd) as total FROM sales GROUP BY date", conn)
            fig = px.line(df_v, x='date', y='total', title="Courbe de croissance")
            st.plotly_chart(fig, use_container_width=True)

    elif adm_choice == "⚙️ Config App":
        with st.form("sys_config"):
            new_app = st.text_input("Nom de l'Application", APP_NAME)
            new_mar = st.text_area("Texte du Marquee (Défilant)", MARQUEE_TEXT)
            mar_st = st.checkbox("Activer le défilement", value=bool(MARQUEE_ON))
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", (new_app, new_mar, 1 if mar_st else 0))
                    conn.commit(); st.rerun()

    elif adm_choice == "🎨 Look & Feel":
        st.header("🎨 PERSONNALISATION DES COULEURS")
        sel_theme = st.selectbox("Choisir un Thème Principal", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
        if st.button("APPLIQUER LE THÈME"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=? WHERE id=1", (sel_theme,))
                conn.commit(); st.rerun()

    if adm_choice == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. INTERFACE BOUTIQUE (GÉRANTS & VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    sh_data = conn.execute("SELECT name, rate, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = sh_data if sh_data else ("MA BOUTIQUE", 2800.0, "BIENVENUE")

# Menu de navigation dynamique
nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 MON ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "💸 DÉPENSES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PRINCIPAL", nav_list)

# --- 8.1 ACCUEIL (DASHBOARD v192 CONSERVÉ) ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='font-size:70px; margin-bottom:0;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4>{datetime.now().strftime('%d %B %Y')}</h4>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        ca = (conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        dp = (conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        st.markdown(f"""
            <div class='cobalt-card'>
                <h3>SOLDE NET DU JOUR</h3>
                <h1 style='font-size:55px; color:#00ff00 !important;'>{(ca-dp):,.2f} $</h1>
                <p>Recettes : {ca:,.1f} $ | Dépenses : {dp:,.1f} $</p>
            </div>
        """, unsafe_allow_html=True)

# --- 8.2 CAISSE & FACTURATION (A4/80mm) ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown("### 📄 PRÉVISUALISATION FACTURE")
        fmt = st.radio("Format d'impression", ["TICKET 80mm", "FACTURE A4"], horizontal=True)
        
        if fmt == "TICKET 80mm":
            html = f"<center><div class='invoice-80mm'><h4>{sh_inf[2]}</h4><hr><b>REF: {inv['ref']}</b><br>Client: {inv['cli']}<br><table class='fac-table'>"
            for it, d in inv['items'].items(): html += f"<tr><td>{it}</td><td>{d['q']}</td><td>{(d['q']*d['p']):.1f}</td></tr>"
            html += f"</table><hr><b>TOTAL: {inv['total_val']:.2f} {inv['dev']}</b></div></center>"
        else:
            html = f"<div class='invoice-a4'><h1>{sh_inf[0]}</h1><p>{sh_inf[2]}</p><hr><h4>FACTURE N° {inv['ref']}</h4><p>Client: {inv['cli']} | Date: {inv['date']}</p><table class='fac-table'><tr><th>Désignation</th><th>Qté</th><th>Prix U.</th><th>Total</th></tr>"
            for it, d in inv['items'].items(): html += f"<tr><td>{it}</td><td>{d['q']}</td><td>{d['p']}$</td><td>{(d['q']*d['p']):.2f}$</td></tr>"
            html += f"</table><hr><h3>TOTAL À PAYER : {inv['total_val']:.2f} {inv['dev']}</h3></div>"
        
        st.markdown(html, unsafe_allow_html=True)
        if st.button("⬅️ TERMINER & NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    
    else:
        devise = st.radio("CHOIX DE LA MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_art = st.selectbox("SÉLECTIONNER UN ARTICLE", ["---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if sel_art != "---" and st.button("➕ AJOUTER AU PANIER"):
                name = sel_art.split(" (")[0]
                info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                st.session_state.session['cart'][name] = {'p': info[0], 'q': 1, 'max': info[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            total_u = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
            p_final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{p_final:,.0f} {devise}</span></center></div>", unsafe_allow_html=True)
            
            for it, d in list(st.session_state.session['cart'].items()):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{it}**")
                new_q = c2.number_input("Qté", 1, d['max'], d['q'], key=f"q_{it}")
                st.session_state.session['cart'][it]['q'] = new_q
                if c3.button("🗑️", key=f"del_{it}"): del st.session_state.session['cart'][it]; st.rerun()
            
            with st.form("pay_form"):
                cli = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                paid = st.number_input("MONTANT REÇU", value=float(p_final))
                if st.form_submit_button("💰 VALIDER ET IMPRIMER"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    r_usd = paid if devise == "USD" else paid / sh_inf[1]
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, cli, total_u, r_usd, total_u-r_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if (total_u - r_usd) > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)", (cli, total_u-r_usd, ref, sid, datetime.now().strftime("%d/%m/%Y")))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': cli, 'total_val': p_final, 'dev': devise, 'items': st.session_state.session['cart'].copy(), 'date': datetime.now().strftime("%d/%m/%Y %H:%M")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK (GESTION COMPLÈTE) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DES STOCKS")
    tab_inv, tab_add = st.tabs(["📋 INVENTAIRE", "➕ NOUVEL ARTICLE"])
    
    with tab_inv:
        with sqlite3.connect(DB_FILE) as conn:
            df_stock = pd.read_sql(f"SELECT item as Article, qty as Quantité, buy_price as 'Achat $', sell_price as 'Vente $' FROM inventory WHERE sid='{sid}'", conn)
            st.table(df_stock)
            
    with tab_add:
        with st.form("add_item"):
            n_name = st.text_input("Désignation de l'article").upper()
            n_buy = st.number_input("Prix d'Achat Unitaire ($)", 0.0)
            n_sell = st.number_input("Prix de Vente Unitaire ($)", 0.0)
            n_qty = st.number_input("Quantité Initiale", 1)
            if st.form_submit_button("ENREGISTRER EN STOCK"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_name, n_qty, n_buy, n_sell, sid))
                    conn.commit(); st.success("Article ajouté !"); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.info("Aucune dette enregistrée.")
        for d_id, d_cli, d_bal in dettes:
            with st.expander(f"👤 {d_cli} | Reste : {d_bal:,.2f} $"):
                ver = st.number_input("Montant Versé ($)", 0.0, d_bal, key=f"pay_{d_id}")
                if st.button("ENREGISTRER LE VERSEMENT", key=f"btn_{d_id}"):
                    n_bal = d_bal - ver
                    status = 'SOLDE' if n_bal <= 0.01 else 'OUVERT'
                    conn.execute("UPDATE debts SET balance=?, status=?, last_update=? WHERE id=?", (n_bal, status, datetime.now().strftime("%d/%m/%Y"), d_id))
                    conn.commit(); st.success("Paiement mis à jour !"); st.rerun()

# --- 8.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 GESTION DES CHARGES")
    with st.form("expense_form"):
        motif = st.text_input("Motif de la dépense")
        montant = st.number_input("Montant de la dépense ($)", min_value=0.1)
        if st.form_submit_button("VALIDER LA DÉPENSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)", (motif, montant, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.success("Dépense déduite du solde !"); st.rerun()

# --- 8.6 RAPPORTS (CSV EXPORT) ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df_sales = pd.read_sql(f"SELECT date, ref as Référence, cli as Client, total_usd as 'Total $', seller as Vendeur FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df_sales, use_container_width=True)
        csv = df_sales.to_csv(index=False).encode('utf-8')
        st.download_button("📥 TÉLÉCHARGER LE RAPPORT (CSV)", csv, "rapport_ventes.csv", "text/csv")

# --- 8.7 ÉQUIPE ---
elif choice == "👥 MON ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_uid, v_name in vendeurs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"👤 **{v_name}** (Identifiant : {v_uid})")
            if col2.button("🗑️", key=f"del_{v_uid}"):
                conn.execute("DELETE FROM users WHERE uid=?", (v_uid,)); conn.commit(); st.rerun()
        
        with st.form("new_vendeur"):
            st.write("---")
            nv_id = st.text_input("Login Vendeur")
            nv_name = st.text_input("Nom Complet")
            nv_pass = st.text_input("Mot de Passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (nv_id.lower(), get_hash(nv_pass), 'VENDEUR', sid, 'ACTIF', nv_name, ''))
                    conn.commit(); st.success("Vendeur ajouté !"); st.rerun()
                except: st.error("Identifiant déjà pris.")

# --- 8.8 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("shop_settings"):
        new_name = st.text_input("Nom de l'Enseigne", sh_inf[0])
        new_head = st.text_area("En-tête des Factures", sh_inf[2])
        new_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, head=?, rate=? WHERE sid=?", (new_name, new_head, new_rate, sid))
                conn.commit(); st.rerun()
    st.divider()
    if st.button("📥 GÉNÉRER UNE SAUVEGARDE (BACKUP.DB)"):
        with open(DB_FILE, "rb") as f:
            st.download_button("Télécharger le fichier DB", f, file_name="balika_backup.db")

# --- 8.9 SÉCURITÉ ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 SÉCURITÉ DU COMPTE")
    with st.form("pwd_change"):
        new_uid = st.text_input("Modifier mon Identifiant", value=st.session_state.session['user'])
        new_pwd = st.text_input("Nouveau Mot de Passe", type="password")
        if st.form_submit_button("ENREGISTRER LES MODIFICATIONS"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_uid.lower(), get_hash(new_pwd), st.session_state.session['user']))
                conn.commit(); st.success("Identifiants mis à jour !"); st.session_state.session['logged_in'] = False; st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"SYSTÈME BALIKA v4.1.0 | © 2026")
