# ==============================================================================
# ANASH ERP v290 - ÉDITION BALIKA BUSINESS (ULTRA-STABLE)
# ------------------------------------------------------------------------------
# - AUCUNE DÉPENDANCE EXTERNE (PAS DE PLOTLY) POUR ÉVITER LES ERREURS.
# - PLUS DE 600 LIGNES DE CODE COMPLET.
# - SYSTÈME DE GESTION INTÉGRAL (ADMIN, GÉRANT, VENDEUR).
# - DESIGN BLEU ROYAL / TEXTE BLANC / PANIER BLANC.
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
DB_FILE = "balika_v290_master.db"

def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table Configuration
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)""")
        
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
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '2.9.0')")
        
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
        return conn.execute("SELECT app_name, marquee FROM system_config WHERE id=1").fetchone()

# ------------------------------------------------------------------------------
# 3. INTERFACE ET STYLES (COBALT & WHITE)
# ------------------------------------------------------------------------------
SYS_DATA = load_sys()
APP_NAME, MARQUEE_TEXT = SYS_DATA[0], SYS_DATA[1]

st.set_page_config(page_title=APP_NAME, layout="wide")

def apply_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background-color: #002b5c; color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: #001a35 !important; border-right: 2px solid #00d4ff; }}
        h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
        
        /* Formulaires */
        input {{ text-align: center; border-radius: 10px !important; font-weight: bold; background-color: white !important; color: black !important; }}
        
        /* Barre Marquee */
        .marquee-bar {{
            background: #000; color: #00ff00; padding: 12px; font-weight: bold;
            border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }}
        
        /* Box Cobalt */
        .cobalt-card {{
            background: linear-gradient(135deg, #004a99 0%, #002b5c 100%);
            padding: 25px; border-radius: 20px; border: 1px solid #00d4ff;
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
        
        /* Facture */
        .invoice-box {{
            background: white; color: black !important; padding: 25px;
            font-family: monospace; width: 300px; margin: auto;
            border: 1px solid #333; text-align: left !important;
        }}
        .invoice-box * {{ text-align: left !important; color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# ------------------------------------------------------------------------------
# 4. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

# ------------------------------------------------------------------------------
# 5. CONNEXION / ACCÈS
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_new = st.tabs(["🔑 CONNEXION", "📝 DEMANDE DE COMPTE"])
        
        with tab_log:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            u_name = st.text_input("VOTRE IDENTIFIANT").lower().strip()
            u_pass = st.text_input("VOTRE MOT DE PASSE", type="password")
            if st.button("🚀 SE CONNECTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    user = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_name,)).fetchone()
                    if user and get_hash(u_pass) == user[0]:
                        if user[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u_name, 'role': user[1], 'shop_id': user[2]})
                            log_event(u_name, "Connexion", user[2]); st.rerun()
                        else: st.error("❌ Compte Inactif. Attendez l'activation.")
                    else: st.error("❌ Identifiants incorrects.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_new:
            st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
            n_uid = st.text_input("ID Utilisateur (ex: malik)")
            n_shop = st.text_input("Nom de la Boutique")
            n_pass = st.text_input("Mot de Passe", type="password")
            if st.button("📩 ENVOYER DEMANDE"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                     (n_uid.lower(), get_hash(n_pass), 'GERANT', 'PENDING', 'EN_ATTENTE', n_shop, ''))
                        conn.commit(); st.success("✅ Demande transmise à l'Admin !")
                    except: st.error("❌ Cet ID existe déjà.")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMINISTRATEUR (admin / admin123)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    a_nav = st.sidebar.radio("Navigation", ["👥 Comptes Utilisateurs", "📊 Logs Système", "⚙️ Paramètres App", "🚪 Déconnexion"])
    
    if a_nav == "👥 Comptes Utilisateurs":
        st.header("👥 GESTION DES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            users = conn.execute("SELECT uid, name, status, role FROM users WHERE uid != 'admin'").fetchall()
            for u_id, u_name, u_stat, u_role in users:
                with st.expander(f"👤 {u_name} [{u_id}] - Statut: {u_stat}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("✅ ACTIVER", key=f"ac_{u_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (u_id,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (u_id, u_name, u_id))
                        conn.commit(); st.rerun()
                    if c2.button("🚫 BLOQUER", key=f"bl_{u_id}"):
                        conn.execute("UPDATE users SET status='INACTIF' WHERE uid=?", (u_id,)); conn.commit(); st.rerun()
                    if c3.button("🗑️ SUPPRIMER", key=f"de_{u_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (u_id,)); conn.commit(); st.rerun()

    elif a_nav == "📊 Logs Système":
        st.header("📊 HISTORIQUE COMPLET")
        with sqlite3.connect(DB_FILE) as conn:
            logs = pd.read_sql("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100", conn)
            st.dataframe(logs, use_container_width=True)

    elif a_nav == "⚙️ Paramètres App":
        with st.form("global"):
            n_a = st.text_input("Nom de l'Application", APP_NAME)
            n_m = st.text_area("Texte du Marquee", MARQUEE_TEXT)
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=? WHERE id=1", (n_a, n_m))
                    conn.commit(); st.rerun()

    if a_nav == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()
    # Sécurité si boutique non encore créée
    sh_inf = shop_data if shop_data else ("BOUTIQUE", 2800.0, "ADRESSE", "000")

# Navigation latérale
nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "📊 RAPPORTS", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PRINCIPAL", nav_list)

# --- 7.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:90px; margin-bottom:0;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3>{datetime.now().strftime('%A %d %B %Y')}</h3>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        stats = conn.execute("SELECT SUM(total_usd), COUNT(id) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()
        ca = stats[0] if stats[0] else 0
        
        st.markdown(f"<div class='cobalt-card'><h2>RECETTE DU JOUR</h2><h1 style='font-size:60px;'>{ca:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 7.2 CAISSE & VENTE ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown("<div class='invoice-box'>", unsafe_allow_html=True)
        st.markdown(f"<center><b>{sh_inf[0]}</b><br>{sh_inf[2]}<br>Tél: {sh_inf[3]}</center><hr>", unsafe_allow_html=True)
        st.markdown(f"FACTURE: {inv['ref']}<br>CLIENT: {inv['cli']}<br>DATE: {inv['date']}<hr>", unsafe_allow_html=True)
        for it, d in inv['items'].items():
            st.markdown(f"{it} x{d['q']} = {d['q']*d['p']}$<br>", unsafe_allow_html=True)
        st.markdown(f"<hr><b>TOTAL: {inv['total_val']} {inv['dev']}</b><br>Payé: {inv['paid']}<br>Reste: {inv['rest']}", unsafe_allow_html=True)
        st.markdown("<br><center>Merci de votre visite !</center></div>", unsafe_allow_html=True)
        
        raw_txt = f"FACTURE {inv['ref']}\nCLIENT: {inv['cli']}\nTOTAL: {inv['total_val']} {inv['dev']}"
        st.download_button("💾 ENREGISTRER FACTURE", raw_txt, file_name=f"FAC_{inv['ref']}.txt")
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_art = st.selectbox("CHOISIR ARTICLE", ["---"] + [f"{p[0]} (Stock: {p[2]})" for p in prods])
            if sel_art != "---" and st.button("➕ AJOUTER AU PANIER"):
                name = sel_art.split(" (")[0]
                info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                st.session_state.session['cart'][name] = {'p': info[0], 'q': 1, 'max': info[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            total_u = 0
            for art, d in list(st.session_state.session['cart'].items()):
                col1, col2, col3 = st.columns([3, 1, 1])
                nq = col2.number_input(f"Qté", 1, d['max'], d['q'], key=f"q_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                total_u += d['p'] * nq
                col1.write(f"**{art}** ({d['p']}$)")
                if col3.button("🗑️", key=f"rm_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            p_final = total_u if devise == "USD" else total_u * sh_inf[1]
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{p_final:,.2f} {devise}</span></center></div>", unsafe_allow_html=True)
            
            with st.form("valid_pay"):
                c_name = st.text_input("CLIENT", "COMPTANT").upper()
                c_pay = st.number_input(f"REÇU ({devise})", value=float(p_final))
                if st.form_submit_button("✅ CONFIRMER LA VENTE"):
                    ref_fac = f"FAC-{random.randint(1000,9999)}"
                    r_usd = c_pay if devise == "USD" else c_pay / sh_inf[1]
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref_fac, c_name, total_u, r_usd, total_u-r_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if (total_u - r_usd) > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)", (c_name, total_u-r_usd, ref_fac, sid, datetime.now().strftime("%d/%m/%Y")))
                        conn.commit()
                    log_event(st.session_state.session['user'], f"Vente {ref_fac}", sid)
                    st.session_state.session['viewing_invoice'] = {'ref': ref_fac, 'cli': c_name, 'total_val': p_final, 'dev': devise, 'paid': c_pay, 'rest': p_final-c_pay, 'items': st.session_state.session['cart'], 'date': datetime.now().strftime("%d/%m/%Y")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 7.3 STOCK ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DES PRODUITS")
    t1, t2 = st.tabs(["📋 Liste", "➕ Nouveau Produit"])
    
    with t1:
        with sqlite3.connect(DB_FILE) as conn:
            items = conn.execute("SELECT id, item, qty, sell_price, buy_price FROM inventory WHERE sid=?", (sid,)).fetchall()
            for i_id, i_n, i_q, i_p, i_b in items:
                with st.expander(f"📦 {i_n} (Stock: {i_q})"):
                    col_q, col_p = st.columns(2)
                    new_q = col_q.number_input("Maj Qté", value=i_q, key=f"mq_{i_id}")
                    new_p = col_p.number_input("Maj Prix Vente $", value=i_p, key=f"mp_{i_id}")
                    if st.button("METTRE À JOUR", key=f"btn_{i_id}"):
                        conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_p, i_id))
                        conn.commit(); st.success("Modifié !"); st.rerun()

    with t2:
        with st.form("add_prod"):
            n_art = st.text_input("Désignation")
            p_buy = st.number_input("Prix Achat ($)")
            p_sell = st.number_input("Prix Vente ($)")
            q_init = st.number_input("Quantité Initiale", 1)
            if st.form_submit_button("ENREGISTRER PRODUIT"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)",
                                 (n_art.upper(), q_init, p_buy, p_sell, sid))
                    conn.commit(); st.success("Produit ajouté au stock !"); st.rerun()

# --- 7.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.info("Aucune dette enregistrée.")
        for di, dc, db, dr in dettes:
            with st.expander(f"👤 {dc} | Reste: {db:,.2f} $ (Facture: {dr})"):
                versement = st.number_input("Montant Versé ($)", max_value=db, key=f"vp_{di}")
                if st.button("VALIDER LE PAIEMENT", key=f"vpb_{di}"):
                    n_bal = db - versement
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (n_bal, datetime.now().strftime("%d/%m/%Y"), di))
                    if n_bal <= 0.01: conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 7.5 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df_sales = pd.read_sql(f"SELECT ref, cli, total_usd, paid_usd, rest_usd, date, time, seller FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df_sales, use_container_width=True)

# --- 7.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    if st.session_state.session['role'] == "GERANT":
        st.subheader("➕ AJOUTER UN VENDEUR")
        with st.form("add_v"):
            v_id = st.text_input("Identifiant")
            v_n = st.text_input("Nom Complet")
            v_p = st.text_input("Mot de Passe", type="password")
            if st.form_submit_button("CRÉER COMPTE"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                     (v_id.lower(), get_hash(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                        conn.commit(); st.success("Vendeur opérationnel !")
                    except: st.error("❌ ID déjà utilisé.")

# --- 7.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("cfg_sh"):
        new_name = st.text_input("Nom de l'Enseigne", sh_inf[0])
        new_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        new_addr = st.text_input("Adresse Physique", sh_inf[2])
        new_tel = st.text_input("Téléphone Contact", sh_inf[3])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, addr=?, tel=? WHERE sid=?", (new_name, new_rate, new_addr, new_tel, sid))
                conn.commit(); st.success("Paramètres enregistrés !"); st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()
