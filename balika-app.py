# ==============================================================================
# 💎 ANASH ERP v500 - INTEGRAL MASTER EDITION (BALIKA BUSINESS)
# ------------------------------------------------------------------------------
# LOGIQUE : Admin (Système) | Gérant (Boutique) | Vendeur (Ventes & Dettes)
# FONCTIONNALITÉS : 
# - Dashboard (Accueil) & Marquee v192
# - Gestion Stocks (Modif Prix/Suppression)
# - Ventes Multidevises (USD/CDF) avec Taux
# - Paiement Dettes par Tranches (Retrait Auto)
# - Interface Mobile Optimisée (Boutons +/-)
# - Impression Factures 80mm & A4 + Partage WhatsApp
# - Sécurité v350 (Hachage SHA-256)
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
# 1. INITIALISATION DE LA BASE DE DONNÉES (STRUCTURE v500)
# ------------------------------------------------------------------------------
DB_FILE = "balika_master_v500.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Configuration Système
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT, marquee_active INTEGER)""")
        
        # Utilisateurs & Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        
        # Inventaire & Mouvements
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
        
        # Ventes & Finance
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT, last_update TEXT)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, amount REAL, 
            date TEXT, sid TEXT, user TEXT)""")

        # Logs
        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, date TEXT, time TEXT, sid TEXT)""")

        # Données initiales
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA ERP', 'BIENVENUE CHEZ BALIKA BUSINESS', '5.0.0', 'Cobalt', 1)")
        
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMIN', '000'))
        conn.commit()

init_db()

# ------------------------------------------------------------------------------
# 2. FONCTIONS DE SÉCURITÉ & CORE
# ------------------------------------------------------------------------------
def get_hash(p): return hashlib.sha256(p.encode()).hexdigest()

def log_event(u, a, s):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO audit_logs (user, action, date, time, sid) VALUES (?,?,?,?,?)",
                     (u, a, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S"), s))

def load_sys_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee, theme_id, marquee_active FROM system_config").fetchone()

# ------------------------------------------------------------------------------
# 3. INTERFACE & STYLES (MOBILE FRIENDLY)
# ------------------------------------------------------------------------------
sys_data = load_sys_config()
APP_NAME, MARQUEE_TEXT, THEME_ID, MARQUEE_ON = sys_data

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="collapsed")

def apply_ui():
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(135deg, #004a99 0%, #000 100%); color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: #000 !important; border-right: 2px solid #00d4ff; min-width: 250px !important; }}
        h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
        input, select, textarea {{ text-align: center; border-radius: 15px !important; font-weight: bold; background: white !important; color: black !important; height: 50px !important; }}
        .marquee-container {{ background: #000; color: #00ff00; padding: 10px; font-weight: bold; border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 1000; }}
        .metric-card {{ background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255,255,255,0.3); padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .white-cart {{ background: white !important; color: black !important; padding: 20px; border-radius: 20px; border: 5px solid #004a99; margin: 15px 0; }}
        .white-cart * {{ color: black !important; font-weight: bold; font-size: 16px; }}
        .total-frame {{ border: 5px solid #00ff00; background: #000; padding: 15px; border-radius: 20px; margin: 15px 0; }}
        .total-text {{ color: #00ff00; font-size: 40px; font-weight: bold; }}
        .stButton > button {{ width: 100%; height: 60px; border-radius: 15px; font-size: 18px; font-weight: bold; transition: 0.3s; background: #007bff; color: white !important; }}
        .btn-plus {{ background: #28a745 !important; color: white !important; }}
        .btn-minus {{ background: #dc3545 !important; color: white !important; }}
        .invoice-box {{ background: white !important; color: black !important; padding: 20px; font-family: 'Courier New'; width: 100%; max-width: 350px; margin: auto; border: 1px solid #000; }}
        .invoice-box * {{ color: black !important; text-align: left; }}
    </style>
    """, unsafe_allow_html=True)

apply_ui()

# ------------------------------------------------------------------------------
# 4. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

# ------------------------------------------------------------------------------
# 5. PAGE DE CONNEXION (SÉCURISÉE)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON: st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, login_col, _ = st.columns([0.1, 0.8, 0.1])
    with login_col:
        st.markdown(f"<h1>💎 {APP_NAME}</h1><p>Veuillez vous identifier</p>", unsafe_allow_html=True)
        u_name = st.text_input("IDENTIFIANT", placeholder="Entrez votre nom").lower().strip()
        u_pass = st.text_input("MOT DE PASSE", type="password", placeholder="••••••••")
        
        if st.button("🚀 SE CONNECTER"):
            with sqlite3.connect(DB_FILE) as conn:
                user = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_name,)).fetchone()
                if user and get_hash(u_pass) == user[0]:
                    if user[3] == "ACTIF" or user[1] == "SUPER_ADMIN":
                        st.session_state.session.update({
                            'logged_in': True, 'user': u_name, 
                            'role': user[1], 'shop_id': user[2]
                        })
                        log_event(u_name, "Connexion Réussie", user[2])
                        st.rerun()
                    else: st.error("❌ Compte désactivé.")
                else: st.error("❌ Identifiants incorrects.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE SUPER_ADMIN (GESTION SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    adm_nav = st.sidebar.radio("MENU", ["👥 Boutiques/Gérants", "⚙️ Paramètres Système", "📊 Audit Logs", "🚪 Déconnexion"])
    
    if adm_nav == "👥 Boutiques/Gérants":
        st.header("👥 GESTION DES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            users = conn.execute("SELECT uid, name, status, shop FROM users WHERE role='GERANT'").fetchall()
            for u_id, u_name, u_stat, u_shop in users:
                with st.expander(f"🏪 {u_name} (Boutique: {u_id})"):
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Activer", key=f"act_{u_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (u_id,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, rate) VALUES (?,?,?)", (u_id, u_name, 2800.0))
                        conn.commit(); st.rerun()
                    if col2.button("🚫 Bloquer", key=f"blo_{u_id}"):
                        conn.execute("UPDATE users SET status='INACTIF' WHERE uid=?", (u_id,))
                        conn.commit(); st.rerun()
            
            st.markdown("---")
            st.subheader("➕ Nouvelle Boutique")
            with st.form("add_shop"):
                new_id = st.text_input("ID Boutique (unique)").lower()
                new_name = st.text_input("Nom de la Boutique / Gérant")
                new_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER BOUTIQUE"):
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                     (new_id, get_hash(new_pass), 'GERANT', new_id, 'ACTIF', new_name, ''))
                        conn.execute("INSERT INTO shops (sid, name, rate) VALUES (?,?,?)", (new_id, new_name, 2800.0))
                        conn.commit(); st.success("Boutique créée !"); st.rerun()
                    except: st.error("ID déjà pris")

    elif adm_nav == "⚙️ Paramètres Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys_form"):
            new_app = st.text_input("Nom de l'App", APP_NAME)
            new_marq = st.text_area("Texte Défilant", MARQUEE_TEXT)
            marq_on = st.checkbox("Activer le texte défilant", value=MARQUEE_ON)
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, marquee_active=? WHERE id=1", 
                                 (new_app, new_marq, 1 if marq_on else 0))
                st.rerun()

    elif adm_nav == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("MA BOUTIQUE", 2800.0, "BIENVENUE", "ADRESSE", "000")

# Menu de Navigation v350
nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='metric-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav_list)

# --- ACCUEIL (DASHBOARD v192) ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON: st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:50px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        ca = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        dep = conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        st.markdown(f"<div class='metric-card'><h3>SOLDE DU JOUR (NET)</h3><h1 style='font-size:45px; color:#00ff00 !important;'>{(ca-dep):,.2f} $</h1></div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'>💰 Recette<br><b>{ca:,.2f} $</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>📉 Dépenses<br><b>{dep:,.2f} $</b></div>", unsafe_allow_html=True)

# --- CAISSE (VENDRE / MULTIDEVISE / BOUTONS +/-) ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
        <center><div class='invoice-box'>
            <center><h3>{sh_inf[0]}</h3><p>{sh_inf[2]}</p></center>
            <hr>
            <b>REF: {inv['ref']}</b><br>
            Date: {inv['date']} à {inv['time']}<br>
            Client: {inv['cli']}<br>
            <hr>
            <table style='width:100%'>
                <tr><th>Art.</th><th>Q.</th><th>P.U</th></tr>
        """, unsafe_allow_html=True)
        for it, d in inv['items'].items():
            st.markdown(f"<tr><td>{it}</td><td>{d['q']}</td><td>{d['p']}$</td></tr>", unsafe_allow_html=True)
        
        st.markdown(f"""
            </table>
            <hr>
            <b>TOTAL: {inv['total_val']:,.0f} {inv['dev']}</b><br>
            Vendeur: {inv['seller']}
        </div></center>
        """, unsafe_allow_html=True)
        
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    
    else:
        devise = st.radio("CHOIX DEVISE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            options = ["---"] + [f"{p[0]} ({p[2]}) - {p[1]}$" for p in prods]
            selection = st.selectbox("RECHERCHER ARTICLE", options)
            
            if selection != "---" and st.button("➕ AJOUTER AU PANIER"):
                name = selection.split(" (")[0]
                price, max_q = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                if name in st.session_state.session['cart']:
                    if st.session_state.session['cart'][name]['q'] < max_q:
                        st.session_state.session['cart'][name]['q'] += 1
                else:
                    st.session_state.session['cart'][name] = {'p': price, 'q': 1, 'max': max_q}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            for it, data in list(st.session_state.session['cart'].items()):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(f"**{it}**")
                if c2.button("➖", key=f"minus_{it}"):
                    st.session_state.session['cart'][it]['q'] -= 1
                    if st.session_state.session['cart'][it]['q'] <= 0: del st.session_state.session['cart'][it]
                    st.rerun()
                c3.write(f"**{data['q']}**")
                if c4.button("➕", key=f"plus_{it}"):
                    if data['q'] < data['max']: st.session_state.session['cart'][it]['q'] += 1
                    st.rerun()
            
            total_usd = sum(v['p'] * v['q'] for v in st.session_state.session['cart'].values())
            total_final = total_usd if devise == "USD" else total_usd * sh_inf[1]
            
            st.markdown(f"<div class='total-frame'><center><span class='total-text'>{total_final:,.0f} {devise}</span></center></div>", unsafe_allow_html=True)
            
            with st.form("validation_vente"):
                client_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                montant_paye = st.number_input(f"REÇU EN {devise}", value=float(total_final))
                if st.form_submit_button("✅ VALIDER & IMPRIMER"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    paye_usd = montant_paye if devise == "USD" else montant_paye / sh_inf[1]
                    reste_usd = total_usd - paye_usd
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, client_name, total_usd, paye_usd, reste_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        
                        if reste_usd > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, status, last_update) VALUES (?,?,?,?,?,?)",
                                         (client_name, reste_usd, ref, sid, 'OUVERT', datetime.now().strftime("%d/%m/%Y")))
                        conn.commit()
                    
                    st.session_state.session['viewing_invoice'] = {
                        'ref': ref, 'cli': client_name, 'total_val': total_final, 
                        'dev': devise, 'items': st.session_state.session['cart'], 
                        'date': datetime.now().strftime("%d/%m/%Y"), 'time': datetime.now().strftime("%H:%M"),
                        'seller': st.session_state.session['user']
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- STOCK (MODIFIER PRIX / SUPPRIMER / AJOUTER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DU STOCK")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT id, item as Article, qty as Quantité, sell_price as 'PV ($)', buy_price as 'PA ($)' FROM inventory WHERE sid='{sid}'", conn)
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
        
        st.subheader("🛠️ MODIFIER / SUPPRIMER")
        target = st.selectbox("Choisir un article", ["---"] + df['Article'].tolist())
        if target != "---":
            row = df[df['Article'] == target].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                new_q = st.number_input("Stock", value=int(row['Quantité']))
                new_pv = st.number_input("Prix Vente ($)", value=float(row['PV ($)']))
            with col2:
                if st.button("💾 SAUVEGARDER"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_pv, int(row['id'])))
                    conn.commit(); st.rerun()
                if st.button("🗑️ SUPPRIMER L'ARTICLE"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (int(row['id']),))
                    conn.commit(); st.rerun()

        st.markdown("---")
        st.subheader("➕ NOUVEL ARTICLE")
        with st.form("add_stock"):
            n_art = st.text_input("Désignation").upper()
            pa, pv, q = st.number_input("Prix Achat ($)"), st.number_input("Prix Vente ($)"), st.number_input("Quantité", 1)
            if st.form_submit_button("AJOUTER AU STOCK"):
                conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid, category) VALUES (?,?,?,?,?,?)",
                             (n_art, q, pa, pv, sid, 'GENERAL'))
                conn.commit(); st.rerun()

# --- DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉANCES CLIENTS")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.info("Aucune dette en cours.")
        for d_id, d_cli, d_bal, d_ref in dettes:
            with st.expander(f"👤 {d_cli} | 💰 {d_bal:,.2f} $ (Ref: {d_ref})"):
                tranche = st.number_input("Montant à payer ($)", min_value=0.0, max_value=float(d_bal), key=f"tr_{d_id}")
                if st.button("ENREGISTRER LE PAIEMENT", key=f"btn_{d_id}"):
                    nouveau_solde = d_bal - tranche
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (nouveau_solde, datetime.now().strftime("%d/%m/%Y"), d_id))
                    if nouveau_solde <= 0.01:
                        conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (d_id,))
                    conn.commit(); st.success("Paiement enregistré !"); st.rerun()

# --- DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 DÉPENSES BOUTIQUE")
    with st.form("form_dep"):
        motif = st.text_input("Motif de la dépense")
        montant = st.number_input("Montant ($)", 0.1)
        if st.form_submit_button("VALIDER DÉPENSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)",
                             (motif, montant, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.rerun()

# --- RAPPORTS (IMPRIMER & PARTAGER) ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES RÉCENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df_v = pd.read_sql(f"SELECT date as Date, ref as 'N° Fac', cli as Client, total_usd as 'Total $', seller as Vendeur FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df_v, use_container_width=True)
        
        st.download_button("📥 Télécharger CSV", df_v.to_csv(index=False).encode('utf-8'), "rapport_ventes.csv", "text/csv")

# --- ÉQUIPE (GÉRANT UNIQUEMENT) ---
elif choice == "👥 ÉQUIPE":
    if st.session_state.session['role'] != "GERANT": st.error("Accès réservé au Gérant"); st.stop()
    st.header("👥 GESTION DE L'ÉQUIPE")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name, status FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n, v_s in vendeurs:
            col1, col2 = st.columns([3, 1])
            col1.write(f"👤 {v_n} ({v_id}) - {v_s}")
            if col2.button("🗑️", key=f"del_{v_id}"):
                conn.execute("DELETE FROM users WHERE uid=?", (v_id,)); conn.commit(); st.rerun()
        
        st.markdown("---")
        with st.form("add_v"):
            st.subheader("➕ Ajouter un Vendeur")
            v_login = st.text_input("Login").lower()
            v_nom = st.text_input("Nom Complet")
            v_pass = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE"):
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_login, get_hash(v_pass), 'VENDEUR', sid, 'ACTIF', v_nom, ''))
                    conn.commit(); st.rerun()
                except: st.error("Login déjà pris.")

# --- RÉGLAGES (TAUX & INFOS) ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("shop_cfg"):
        sh_name = st.text_input("Nom de l'Etablissement", sh_inf[0])
        sh_head = st.text_area("Entête (Facture)", sh_inf[2])
        sh_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, head=?, rate=? WHERE sid=?", (sh_name, sh_head, sh_rate, sid))
                conn.commit(); st.rerun()
    
    if st.button("📥 GÉNÉRER BACKUP DB"):
        with open(DB_FILE, "rb") as f:
            st.download_button("Télécharger Backup", f, file_name=f"backup_{sid}.db")

# --- SÉCURITÉ ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 MON COMPTE")
    with st.form("pwd_form"):
        new_u = st.text_input("Nouvel Identifiant", value=st.session_state.session['user'])
        new_p = st.text_input("Nouveau Mot de Passe", type="password")
        if st.form_submit_button("MODIFIER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_u.lower(), get_hash(new_p), st.session_state.session['user']))
                conn.commit(); st.session_state.session['logged_in'] = False; st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

# ------------------------------------------------------------------------------
# PIED DE PAGE
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.caption(f"v5.0.0-PRO | © 2026 BALIKA BUSINESS")
