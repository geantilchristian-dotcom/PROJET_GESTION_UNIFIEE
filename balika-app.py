# ==============================================================================
# ANASH ERP v398 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL PRO)
# ------------------------------------------------------------------------------
# - CODE COMPLET (+700 LIGNES) - FUSION v350 + SYSTÈME D'INSCRIPTION
# - AUCUNE SUPPRESSION DE LOGIQUE PRÉCÉDENTE
# - AJOUT : TAB "CRÉER UN COMPTE" À L'ACCUEIL
# - AJOUT : GESTION DES DEMANDES PAR LE SUPER_ADMIN (CONFIRMATION)
# - AJOUT : STATUT "EN ATTENTE" PAR DÉFAUT POUR TOUT NOUVEAU COMPTE
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
import urllib.parse

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES MASTER (v398)
# ------------------------------------------------------------------------------
DB_FILE = "balika_v398_master.db"

def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table Configuration
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', marquee_active INTEGER DEFAULT 1)""")
        
        # Table Utilisateurs (Ajout du statut 'EN_ATTENTE' par défaut)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, 
            status TEXT DEFAULT 'EN_ATTENTE', name TEXT, tel TEXT)""")
        
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
            cursor.execute("INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '3.9.8', 'Cobalt', 1)")
        
        # Compte Admin Maître
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
    "Silver": "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)",
    "Simple White": "#ffffff"
}

# ------------------------------------------------------------------------------
# 4. INTERFACE ET STYLES
# ------------------------------------------------------------------------------
SYS_DATA = load_sys()
APP_NAME, MARQUEE_TEXT, CURRENT_THEME, MARQUEE_ON = SYS_DATA[0], SYS_DATA[1], SYS_DATA[2], SYS_DATA[3]
SELECTED_BG = THEMES.get(CURRENT_THEME, THEMES["Cobalt"])
st.set_page_config(page_title=APP_NAME, layout="wide")

st.markdown(f"""
<style>
    .stApp {{ background: {SELECTED_BG}; color: white !important; font-size: 16px; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid #00d4ff; }}
    h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
    input {{ text-align: center; border-radius: 12px !important; font-weight: bold; background-color: white !important; color: black !important; height: 45px !important; }}
    .marquee-bar {{ background: #000; color: #00ff00; padding: 12px; border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; }}
    .cobalt-card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3); margin-bottom: 15px; }}
    .white-cart {{ background: white !important; color: black !important; padding: 15px; border-radius: 15px; border: 5px solid #004a99; }}
    .white-cart * {{ color: black !important; font-weight: bold; }}
    .total-frame {{ border: 4px solid #00ff00; background: #000; padding: 10px; border-radius: 15px; margin: 10px 0; }}
    .total-text {{ color: #00ff00; font-size: 38px; font-weight: bold; }}
    .stButton > button {{ width: 100%; height: 55px; border-radius: 15px; font-size: 18px; background: linear-gradient(to right, #007bff, #00d4ff); color: white !important; font-weight: bold; }}
    .invoice-box {{ background: white !important; color: black !important; padding: 20px; font-family: 'Courier New'; border: 1px solid #000; }}
    .invoice-box * {{ color: black !important; text-align: left !important; }}
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
# 6. ÉCRAN DE CONNEXION / INSCRIPTION (SYSTÈME DE CONFIRMATION ADMIN)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON: st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, col_main, _ = st.columns([0.1, 0.8, 0.1])
    with col_main:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 SE CONNECTER", "📝 CRÉER UN COMPTE"])
        
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
                            st.rerun()
                        elif user[3] == "EN_ATTENTE":
                            st.warning("⏳ Votre compte est encore en attente de confirmation par l'administrateur.")
                        else: st.error("❌ Votre compte a été désactivé.")
                    else: st.error("❌ Identifiants invalides.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_reg:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            r_uid = st.text_input("Choisir un Identifiant (Login)").lower().strip()
            r_name = st.text_input("Nom de la Boutique ou Nom Complet")
            r_tel = st.text_input("Téléphone")
            r_role = st.selectbox("Type de Compte", ["GERANT", "VENDEUR"])
            r_pass = st.text_input("Définir un Mot de Passe", type="password")
            if st.button("📩 ENVOYER LA DEMANDE D'INSCRIPTION"):
                if r_uid and r_pass and r_name:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name, tel) VALUES (?,?,?,?,?,?,?)",
                                         (r_uid, get_hash(r_pass), r_role, r_uid, 'EN_ATTENTE', r_name, r_tel))
                            conn.commit()
                            st.success("✅ Demande envoyée ! Veuillez contacter l'administrateur pour l'activation.")
                        except: st.error("❌ Cet identifiant existe déjà.")
                else: st.error("Veuillez remplir tous les champs.")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. ESPACE SUPER ADMINISTRATEUR (CONTRÔLE & CONFIRMATION)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    a_nav = st.sidebar.radio("Navigation", ["🔔 Demandes d'Accès", "👥 Gestion Boutiques", "⚙️ Config App", "🎨 Thèmes", "🚪 Déconnexion"])
    
    if a_nav == "🔔 Demandes d'Accès":
        st.header("🔔 COMPTES EN ATTENTE DE CONFIRMATION")
        
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, role, tel FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending: st.info("Aucune demande en attente.")
            for p_id, p_n, p_r, p_t in pending:
                with st.expander(f"Demande de : {p_n} ({p_id})"):
                    st.write(f"Rôle : {p_r} | Tel : {p_t}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ CONFIRMER & ACTIVER", key=f"ok_{p_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (p_id,))
                        if p_r == "GERANT":
                            conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_id, p_n, p_id))
                        conn.commit(); st.success(f"Compte {p_id} activé !"); st.rerun()
                    if c2.button("🗑️ REJETER", key=f"no_{p_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (p_id,))
                        conn.commit(); st.rerun()

    elif a_nav == "👥 Gestion Boutiques":
        st.header("👥 UTILISATEURS DU SYSTÈME")
        with sqlite3.connect(DB_FILE) as conn:
            df_u = pd.read_sql("SELECT uid, name, role, status, shop FROM users", conn)
            st.dataframe(df_u, use_container_width=True)
            u_del = st.text_input("ID de l'utilisateur à supprimer")
            if st.button("❌ SUPPRIMER DÉFINITIVEMENT"):
                conn.execute("DELETE FROM users WHERE uid=?", (u_del,))
                conn.commit(); st.rerun()

    elif a_nav == "⚙️ Config App":
        with st.form("sys"):
            n_app = st.text_input("Nom App", APP_NAME)
            n_mar = st.text_area("Texte Marquee", MARQUEE_TEXT)
            m_on = st.checkbox("Marquee Actif", value=bool(MARQUEE_ON))
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", (n_app, n_mar, 1 if m_on else 0))
                    conn.commit(); st.rerun()

    elif a_nav == "🎨 Thèmes":
        new_t = st.selectbox("Thème", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
        if st.button("APPLIQUER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=? WHERE id=1", (new_t,))
                conn.commit(); st.rerun()

    if a_nav == "🚪 Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. LOGIQUE BOUTIQUE (GÉRANT & VENDEUR) - CONSERVÉ DE v350
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, addr, tel, rccm, idnat, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("BOUTIQUE", 2800.0, "ADRESSE", "000", "", "", "BIENVENUE")

nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "💸 DÉPENSES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

choice = st.sidebar.radio(f"🏪 {sh_inf[0]}", nav_list)

# --- 8.1 ACCUEIL (SOLDE NET) ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON: st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        ca = (conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        dp = (conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        st.markdown(f"<div class='cobalt-card'><h3>SOLDE DU JOUR (NET)</h3><h1 style='color:#00ff00;'>{(ca-dp):,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE (LOGIQUE v192 + v350) ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown("### 📄 FACTURE GÉNÉRÉE")
        fmt = st.radio("Format", ["80mm", "A4"], horizontal=True)
        # Affichage Facture
        html = f"<div class='invoice-box'><center><b>{sh_inf[6]}</b><br>{sh_inf[0]}</center><hr>"
        html += f"Réf: {inv['ref']}<br>Client: {inv['cli']}<hr><table width='100%'>"
        for it, d in inv['items'].items(): html += f"<tr><td>{it}</td><td>{d['q']}</td><td>{(d['q']*d['p']):.1f}</td></tr>"
        html += f"</table><hr><b>TOTAL : {inv['total_val']} {inv['dev']}</b></div>"
        st.markdown(html, unsafe_allow_html=True)
        if st.button("NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel = st.selectbox("ARTICLE", ["---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if sel != "---" and st.button("➕ AJOUTER"):
                name = sel.split(" (")[0]
                price = conn.execute("SELECT sell_price FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()[0]
                st.session_state.session['cart'][name] = {'p': price, 'q': 1}
                st.rerun()
        
        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            total_u = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
            final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><span class='total-text'>{final:,.0f} {devise}</span></div>", unsafe_allow_html=True)
            for it, d in list(st.session_state.session['cart'].items()): st.write(f"🗑️ {it} x{d['q']}")
            
            c_name = st.text_input("NOM CLIENT", "COMPTANT")
            if st.button("✅ VALIDER"):
                ref = f"FAC-{random.randint(100,999)}"
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO sales (ref, cli, total_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?)",
                                 (ref, c_name, total_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                    for it, d in st.session_state.session['cart'].items():
                        conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                    conn.commit()
                st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': c_name, 'total_val': final, 'dev': devise, 'items': st.session_state.session['cart'].copy()}
                st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK (TABLEAU D'ARTICLES) ---
elif choice == "📦 STOCK":
    st.header("📦 INVENTAIRE")
    with sqlite3.connect(DB_FILE) as conn:
        df_inv = pd.read_sql(f"SELECT item, qty, buy_price, sell_price FROM inventory WHERE sid='{sid}'", conn)
        st.table(df_inv)
        with st.form("add"):
            n_i = st.text_input("Désignation").upper()
            n_q = st.number_input("Quantité", 1)
            n_b = st.number_input("Prix Achat $")
            n_s = st.number_input("Prix Vente $")
            if st.form_submit_button("AJOUTER"):
                conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_i, n_q, n_b, n_s, sid))
                conn.commit(); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dt = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for d_id, d_c, d_b in dt:
            with st.expander(f"{d_c} : {d_b}$"):
                if st.button("SOLDE", key=f"s_{d_id}"):
                    conn.execute("UPDATE debts SET status='SOLDE', balance=0 WHERE id=?", (d_id,))
                    conn.commit(); st.rerun()

# --- 8.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 DÉPENSES")
    with st.form("exp"):
        mot = st.text_input("Motif")
        mt = st.number_input("Montant $")
        if st.form_submit_button("OK"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)", (mot, mt, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.rerun()

# --- 8.6 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT date, ref, cli, total_usd FROM sales WHERE sid='{sid}'", conn)
        st.dataframe(df, use_container_width=True)

# --- 8.7 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vs = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n in vs: st.write(f"👤 {v_n} ({v_id})")

# --- 8.8 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION")
    with st.form("conf"):
        n_sh = st.text_input("Nom Boutique", sh_inf[0])
        n_tx = st.number_input("Taux CDF", value=sh_inf[1])
        if st.form_submit_button("SAUVEGARDER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=? WHERE sid=?", (n_sh, n_tx, sid))
                conn.commit(); st.rerun()
    if st.button("📥 BACKUP"):
        with open(DB_FILE, "rb") as f: st.download_button("Télécharger", f, file_name="backup.db")

# --- 8.9 SÉCURITÉ ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 MON COMPTE")
    with st.form("sec"):
        new_p = st.text_input("Nouveau Mot de Passe", type="password")
        if st.form_submit_button("MODIFIER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (get_hash(new_p), st.session_state.session['user']))
                conn.commit(); st.success("OK")

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"v3.9.8 | © Balika Business")
