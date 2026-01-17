# ==============================================================================
# ANASH ERP v399 - ÉDITION BALIKA BUSINESS (LOGIQUE INTÉGRALE CONSERVÉE)
# ------------------------------------------------------------------------------
# - AUCUNE LIGNE SUPPRIMÉE DE v350
# - TOUT LE SYSTÈME DE THÈMES (20 VARIANTES) EST PRÉSENT
# - TOUTE LA STRUCTURE DES TABLES (RCCM, IDNAT, LOGS) EST CONSERVÉE
# - AJOUT : SYSTÈME D'AUTO-INSCRIPTION AVEC CONFIRMATION ADMIN
# - AFFICHAGE : TEXTE BLANC / FOND BLEU / PANIER BLANC / TOTAL ENCADRÉ
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
# 1. INITIALISATION DE LA BASE DE DONNÉES MASTER (v399)
# ------------------------------------------------------------------------------
DB_FILE = "balika_v399_master.db"
def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table Configuration
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', marquee_active INTEGER DEFAULT 1)""")
        
        # Table Utilisateurs (Statut EN_ATTENTE par défaut pour les nouveaux)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT DEFAULT 'EN_ATTENTE', name TEXT, tel TEXT)""")
        
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
            cursor.execute("INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '3.9.9', 'Cobalt', 1)")
        
        # Admin par défaut (Toujours ACTIF)
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
# 3. SYSTÈME DE THÈMES (20 VARIANTES - TOUTES CONSERVÉES)
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
        input {{ text-align: center; border-radius: 12px !important; font-weight: bold; background-color: white !important; color: black !important; height: 45px !important; font-size: 18px !important; }}
        .marquee-bar {{ background: #000; color: #00ff00; padding: 12px; font-weight: bold; border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; }}
        .cobalt-card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3); margin-bottom: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.4); }}
        .white-cart {{ background: white !important; color: black !important; padding: 15px; border-radius: 15px; border: 5px solid #004a99; margin: 10px 0; }}
        .white-cart * {{ color: black !important; font-weight: bold; }}
        .total-frame {{ border: 4px solid #00ff00; background: #000; padding: 10px; border-radius: 15px; margin: 10px 0; box-shadow: 0 0 10px #00ff00; }}
        .total-text {{ color: #00ff00; font-size: 38px; font-weight: bold; }}
        .stButton > button {{ width: 100%; height: 55px; border-radius: 15px; font-size: 18px; background: linear-gradient(to right, #007bff, #00d4ff); color: white !important; border: none; font-weight: bold; margin-bottom: 5px; }}
        .invoice-80mm {{ background: white !important; color: black !important; padding: 10px; font-family: 'Courier New'; width: 100%; max-width: 300px; margin: auto; border: 1px dashed #000; font-size: 13px; }}
        .invoice-a4 {{ background: white !important; color: black !important; padding: 40px; font-family: 'Arial'; width: 100%; max-width: 800px; margin: auto; border: 1px solid #ccc; }}
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
# 6. CONNEXION ET CRÉATION DE COMPTE (AUTO-INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_new = st.tabs(["🔑 CONNEXION", "📝 CRÉER UN COMPTE"])
        
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
                        elif user[3] == "EN_ATTENTE":
                            st.warning("⏳ Votre compte est en attente de confirmation par l'administrateur.")
                        else: st.error("❌ Compte Bloqué")
                    else: st.error("❌ Erreur Identifiants")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_new:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            n_uid = st.text_input("ID Choisi (Login)").lower().strip()
            n_shop = st.text_input("Nom de votre Boutique")
            n_tel = st.text_input("Téléphone")
            n_pass = st.text_input("Mot de Passe", type="password")
            n_role = st.selectbox("Type", ["GERANT", "VENDEUR"])
            if st.button("📩 ENVOYER LA DEMANDE"):
                if n_uid and n_pass and n_shop:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                         (n_uid, get_hash(n_pass), n_role, n_uid, 'EN_ATTENTE', n_shop, n_tel))
                            conn.commit(); st.success("✅ Demande envoyée ! Attendez la confirmation de l'admin.")
                        except: st.error("❌ Cet ID est déjà utilisé")
                else: st.error("Veuillez remplir tous les champs")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 7. ESPACE SUPER ADMINISTRATEUR (CONTRÔLE TOTAL)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER ADMIN")
    a_nav = st.sidebar.radio("Navigation", ["🔔 Demandes d'Accès", "👥 Boutiques", "📊 Logs", "⚙️ App Config", "🎨 Thèmes", "🔐 Sécurité", "🚪 Déconnexion"])
    
    if a_nav == "🔔 Demandes d'Accès":
        st.header("🔔 NOUVELLES INSCRIPTIONS")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, role, tel FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending: st.info("Aucune demande en attente.")
            for p_id, p_n, p_r, p_t in pending:
                with st.expander(f"Demande : {p_n} ({p_id})"):
                    st.write(f"Rôle: {p_r} | Tel: {p_t}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ CONFIRMER", key=f"ok_{p_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (p_id,))
                        if p_r == "GERANT":
                            conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_id, p_n, p_id))
                        conn.commit(); st.success(f"Compte {p_id} activé !"); st.rerun()
                    if c2.button("🗑️ REJETER", key=f"no_{p_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (p_id,))
                        conn.commit(); st.rerun()

    elif a_nav == "👥 Boutiques":
        st.header("👥 GESTION DES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            users = conn.execute("SELECT uid, name, status, role FROM users WHERE uid != 'admin'").fetchall()
            for u_id, u_name, u_stat, u_role in users:
                with st.expander(f"👤 {u_name} - {u_stat}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("✅ ACTIVER", key=f"ac_{u_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (u_id,)); conn.commit(); st.rerun()
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
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", (n_a, n_m, 1 if m_status else 0))
                    conn.commit(); st.rerun()
    
    elif a_nav == "📊 Logs":
        with sqlite3.connect(DB_FILE) as conn:
            logs = pd.read_sql("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100", conn)
            st.dataframe(logs, use_container_width=True)

    elif a_nav == "🔐 Sécurité":
        st.header("🔐 ACCÈS ADMINISTRATEUR")
        with st.form("admin_sec"):
            curr_u = st.text_input("Nouvel Identifiant Admin", st.session_state.session['user'])
            new_p = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("CHANGER MES ACCÈS"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (curr_u.lower(), get_hash(new_p), st.session_state.session['user']))
                    conn.commit(); st.success("Accès Admin mis à jour !"); st.session_state.session['logged_in'] = False; st.rerun()

    if a_nav == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. LOGIQUE BOUTIQUE (GÉRANT & VENDEUR) - v350 CONSERVÉ
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, addr, tel, rccm, idnat, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("BOUTIQUE", 2800.0, "ADRESSE", "000", "", "", "BIENVENUE")

nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "💸 DÉPENSES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav_list)

# --- 8.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON: st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:60px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        ca = (conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        dp = (conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        st.markdown(f"<div class='cobalt-card'><h3>SOLDE DU JOUR (NET)</h3><h1 style='font-size:45px; color:#00ff00 !important;'>{(ca-dp):,.2f} $</h1><p>Ventes: {ca}$ | Dépenses: {dp}$</p></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE (LOGIQUE FACTURE v350) ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
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
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_art = st.selectbox("ARTICLES EN STOCK", ["---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if sel_art != "---" and st.button("➕ AJOUTER AU PANIER"):
                name = sel_art.split(" (")[0]
                info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                st.session_state.session['cart'][name] = {'p': info[0], 'q': 1}
                st.rerun()
        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            total_u = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
            p_final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{p_final:,.0f} {devise}</span></center></div>", unsafe_allow_html=True)
            for it, d in list(st.session_state.session['cart'].items()):
                col1, col2 = st.columns([4, 1])
                col1.write(f"🔹 {it} x{d['q']}")
                if col2.button("❌", key=f"del_{it}"): del st.session_state.session['cart'][it]; st.rerun()
            c_name = st.text_input("CLIENT", "COMPTANT").upper()
            if st.button("✅ VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(1000,9999)}"
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO sales (ref, cli, total_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?)",
                                 (ref, c_name, total_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                    for it, d in st.session_state.session['cart'].items():
                        conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                    conn.commit()
                st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': c_name, 'total_val': p_final, 'dev': devise, 'items': st.session_state.session['cart'].copy(), 'date': datetime.now().strftime("%d/%m/%Y")}
                st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 8.3 STOCK (TABLEAU COMPLET v350) ---
elif choice == "📦 STOCK":
    st.header("📦 INVENTAIRE")
    with sqlite3.connect(DB_FILE) as conn:
        df_stock = pd.read_sql(f"SELECT item as Article, qty as Quantité, sell_price as 'Prix Vente $', buy_price as 'Prix Achat $' FROM inventory WHERE sid='{sid}'", conn)
        st.dataframe(df_stock, use_container_width=True)
        with st.form("add_p"):
            n_art = st.text_input("Désignation").upper()
            p_buy = st.number_input("Prix Achat ($)")
            p_sell = st.number_input("Prix Vente ($)")
            q_init = st.number_input("Quantité", 1)
            if st.form_submit_button("AJOUTER"):
                conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_art, q_init, p_buy, p_sell, sid))
                conn.commit(); st.rerun()

# --- 8.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for di, dc, db in dettes:
            with st.expander(f"👤 {dc} | {db:,.2f} $"):
                pay = st.number_input("Verser ($)", 0.0, db, key=f"p_{di}")
                if st.button("ENREGISTRER", key=f"btn_{di}"):
                    n_bal = db - pay
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (n_bal, datetime.now().strftime("%d/%m/%Y"), di))
                    if n_bal <= 0.01: conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 8.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 DÉPENSES")
    with st.form("exp_f"):
        motif = st.text_input("Motif")
        montant = st.number_input("Montant ($)", min_value=0.1)
        if st.form_submit_button("ENREGISTRER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)", (motif, montant, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.success("Dépense enregistrée !"); st.rerun()

# --- 8.6 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT date, ref, cli, total_usd as 'Total $', seller FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 EXPORTER (CSV)", csv, "rapport.csv")

# --- 8.7 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n in vendeurs: st.write(f"👤 {v_n} ({v_id})")
        with st.form("new_v"):
            v_id, v_n, v_p = st.text_input("Login"), st.text_input("Nom"), st.text_input("Mot de Passe", type="password")
            if st.form_submit_button("CRÉER"):
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_id.lower(), get_hash(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                    conn.commit(); st.rerun()
                except: st.error("ID déjà pris")

# --- 8.8 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION")
    with st.form("cfg_shop"):
        n_name = st.text_input("Nom Entreprise", sh_inf[0])
        n_head = st.text_area("Entête Facture", sh_inf[6])
        n_rate = st.number_input("Taux Change", value=sh_inf[1])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, head=?, rate=? WHERE sid=?", (n_name, n_head, n_rate, sid))
                conn.commit(); st.rerun()
    if st.button("📥 BACKUP SYSTEM"):
        with open(DB_FILE, "rb") as f: st.download_button("Télécharger Backup", f, file_name="backup.db")

# --- 8.9 SÉCURITÉ ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 COMPTE")
    with st.form("pwd_ch"):
        new_u = st.text_input("Nouvel Identifiant", value=st.session_state.session['user'])
        new_p = st.text_input("Nouveau Mot de Passe", type="password")
        if st.form_submit_button("CHANGER MES ACCÈS"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_u.lower(), get_hash(new_p), st.session_state.session['user']))
                conn.commit(); st.session_state.session['logged_in'] = False; st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"v3.9.9 | © Balika Business")
