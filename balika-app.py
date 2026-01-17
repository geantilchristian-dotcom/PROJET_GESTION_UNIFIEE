# ==============================================================================
# ANASH ERP v255 - ÉDITION FINALE BALIKA BUSINESS (SYSTÈME COMPLET)
# ------------------------------------------------------------------------------
# FONCTIONS INCLUSES : 
# - Dashboard (Accueil), Marquee, Design Bleu/Blanc.
# - Gestion des ventes Multi-Devises (USD/CDF) avec taux réglable.
# - Paiement des dettes par tranches avec suppression auto si soldée.
# - Contrôle Admin : Activer, Désactiver, Supprimer (Comptes toujours visibles).
# - Facturation : Impression et Enregistrement automatique (.txt) sur appareil.
# - Gestion des stocks et modification des prix/quantités.
# - Sécurité : Accès restreint pour les vendeurs.
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
# 1. INITIALISATION DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "balika_v255_master.db"

def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")
        
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS ET PROSPÉRITÉ À VOTRE ENTREPRISE', '2.5.5')")
        
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_master_db()

# ------------------------------------------------------------------------------
# 2. DESIGN & STYLES (BLEU ROYAL & TEXTE BLANC)
# ------------------------------------------------------------------------------
def get_sys_info():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee FROM system_config WHERE id=1").fetchone()

SYS_INFO = get_sys_info()
APP_NAME, MARQUEE_TEXT = SYS_INFO[0], SYS_INFO[1]

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_global_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background-color: #002b5c; color: white !important; }}
        p, span, label, h1, h2, h3, h4, .stMarkdown {{ color: white !important; text-align: center; }}
        input {{ text-align: center; background-color: #ffffff !important; color: #000000 !important; font-weight: bold; }}
        .marquee-container {{
            background: #000; color: #00ff00; padding: 10px; font-weight: bold;
            border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 999;
        }}
        .cobalt-box {{
            background: #004a99; padding: 25px; border-radius: 20px;
            border: 2px solid #00d4ff; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .cart-white {{
            background: white !important; color: black !important; padding: 20px;
            border-radius: 15px; border: 5px solid #004a99;
        }}
        .cart-white * {{ color: black !important; font-weight: bold; text-align: left; }}
        .neon-total {{
            border: 4px solid #00ff00; background: #000; padding: 20px;
            border-radius: 15px; margin: 15px 0;
        }}
        .total-val {{ color: #00ff00; font-size: 40px; font-weight: bold; }}
        .stButton > button {{
            width: 100%; height: 60px; border-radius: 12px; font-size: 18px;
            background: linear-gradient(to bottom, #007bff, #004a99);
            color: white !important; border: 1px solid white; font-weight: bold;
        }}
        .facture-print {{
            background: white; color: black !important; padding: 30px;
            font-family: 'Courier New', Courier, monospace; width: 100%; margin: auto;
        }}
        .table-fac {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .table-fac th, .table-fac td {{ border: 1px solid black; padding: 5px; text-align: center; color: black !important; font-size: 12px; }}
    </style>
    """, unsafe_allow_html=True)

apply_global_styles()

# ------------------------------------------------------------------------------
# 3. GESTION DE SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {'logged_in': False, 'user': None, 'role': None, 'shop_id': None, 'cart': {}, 'viewing_invoice': None}

def get_hash(p): return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION / INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown(f"<h1>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<div class='cobalt-box'>", unsafe_allow_html=True)
        st.markdown("### 🔑 CONNEXION")
        uid = st.text_input("IDENTIFIANT").lower().strip()
        upw = st.text_input("MOT DE PASSE", type="password")
        if st.button("🚀 SE CONNECTER"):
            with sqlite3.connect(DB_FILE) as conn:
                u_data = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (uid,)).fetchone()
                if u_data and get_hash(upw) == u_data[0]:
                    if u_data[3] == "ACTIF":
                        st.session_state.session.update({'logged_in': True, 'user': uid, 'role': u_data[1], 'shop_id': u_data[2]})
                        st.rerun()
                    else: st.error("❌ Compte INACTIF. Contactez l'administrateur.")
                else: st.error("❌ Identifiants incorrects.")
        st.markdown("</div>")
        
        st.markdown("<br><hr style='border:1px solid white;'><br>", unsafe_allow_html=True)
        with st.expander("📝 CRÉER UNE NOUVELLE BOUTIQUE"):
            new_uid = st.text_input("ID UNIQUE (ex: malik_shop)")
            new_name = st.text_input("NOM DE LA BOUTIQUE")
            new_pwd = st.text_input("MOT DE PASSE ", type="password")
            if st.button("📩 ENVOYER LA DEMANDE"):
                if new_uid and new_pwd:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                         (new_uid.lower(), get_hash(new_pwd), 'GERANT', 'PENDING', 'EN_ATTENTE', new_name, ''))
                            conn.commit(); st.success("✅ Demande envoyée ! Attendez l'activation par l'Admin.")
                        except: st.error("Cet identifiant existe déjà.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    a_menu = st.sidebar.radio("Navigation", ["👥 Gestion Comptes", "⚙️ Configuration Système", "🚪 Déconnexion"])
    
    if a_menu == "👥 Gestion Comptes":
        st.header("👥 TOUS LES COMPTES CLIENTS")
        with sqlite3.connect(DB_FILE) as conn:
            u_list = conn.execute("SELECT uid, name, status, role FROM users WHERE uid != 'admin'").fetchall()
            if not u_list: st.info("Aucun compte enregistré.")
            for u_id, u_name, u_stat, u_role in u_list:
                with st.expander(f"👤 {u_name.upper()} (ID: {u_id}) - STATUT: {u_stat}"):
                    st.write(f"Rôle : {u_role}")
                    c1, c2, c3 = st.columns(3)
                    if c1.button("✅ ACTIVER", key=f"a_{u_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (u_id,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (u_id, u_name, u_id))
                        conn.commit(); st.rerun()
                    if c2.button("🚫 DÉSACTIVER", key=f"d_{u_id}"):
                        conn.execute("UPDATE users SET status='INACTIF' WHERE uid=?", (u_id,))
                        conn.commit(); st.rerun()
                    if c3.button("🗑️ SUPPRIMER", key=f"s_{u_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (u_id,))
                        conn.execute("DELETE FROM shops WHERE sid=?", (u_id,))
                        conn.commit(); st.rerun()

    elif a_menu == "⚙️ Configuration Système":
        with st.form("sys"):
            n_app = st.text_input("Nom Global de l'App", APP_NAME)
            n_mar = st.text_area("Texte Marquee", MARQUEE_TEXT)
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=? WHERE id=1", (n_app, n_mar))
                    conn.commit(); st.rerun()

    if a_menu == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    sh_inf = conn.execute("SELECT name, rate, addr, tel, rccm FROM shops WHERE sid=?", (sid,)).fetchone()

# Navigation dynamique selon rôle
nav_options = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_options = ["🏠 ACCUEIL", "🛒 VENDRE (CAISSE)", "📉 DETTES", "📊 RAPPORTS", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-box'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", nav_options)

# --- 6.1 ACCUEIL (DASHBOARD) ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:70px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3>{datetime.now().strftime('%A %d %B %Y')}</h3>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        ca_d = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        st.markdown(f"<div class='cobalt-box'><h2>RECETTE DU JOUR</h2><h1 style='font-size:55px;'>{ca_d:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE & FACTURATION AUTO ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        
        # Format Texte pour sauvegarde automatique
        txt_output = f"FACTURE: {inv['ref']}\nCLIENT: {inv['cli']}\nDATE: {inv['date']}\n"
        txt_output += "-"*25 + "\n"
        for it, d in inv['items'].items():
            txt_output += f"{it} x{d['q']} = {d['q']*d['p']}\n"
        txt_output += "-"*25 + f"\nTOTAL: {inv['total_val']} {inv['dev']}\nPAYE: {inv['paid']}\nRESTE: {inv['rest']}"

        st.markdown("<div class='facture-print'>", unsafe_allow_html=True)
        st.markdown(f"<center><h2>{sh_inf[0]}</h2><p>{sh_inf[2]}<br>Tél: {sh_inf[3]}</p><hr><h3>FACTURE N° {inv['ref']}</h3></center>", unsafe_allow_html=True)
        st.markdown("<table class='table-fac'><tr><th>ARTICLE</th><th>QTÉ</th><th>TOTAL</th></tr>", unsafe_allow_html=True)
        for it, d in inv['items'].items():
            st.markdown(f"<tr><td>{it}</td><td>{d['q']}</td><td>{d['q']*d['p']}</td></tr>", unsafe_allow_html=True)
        st.markdown(f"</table><br><div style='text-align:right; color:black;'><b>NET À PAYER : {inv['total_val']} {inv['dev']}</b><br>Payé : {inv['paid']} | Reste : {inv['rest']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.download_button(label="💾 ENREGISTRER LA FACTURE (.TXT)", data=txt_output, file_name=f"Facture_{inv['ref']}.txt")
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()

    else:
        st.header("🛒 TERMINAL DE VENTE")
        devise = st.radio("CHOIX DE LA MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            stock = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_art = st.selectbox("RECHERCHER ARTICLE", ["---"] + [f"{s[0]} ({s[2]})" for s in stock])
            if sel_art != "---" and st.button("➕ AJOUTER"):
                name = sel_art.split(" (")[0]
                info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (name, sid)).fetchone()
                st.session_state.session['cart'][name] = {'p': info[0], 'q': 1, 'max': info[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='cart-white'>", unsafe_allow_html=True)
            total_usd = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c1, c2, c3 = st.columns([3, 1, 1])
                new_q = c2.number_input(f"Qté", 1, d['max'], d['q'], key=f"q_{art}")
                st.session_state.session['cart'][art]['q'] = new_q
                total_usd += d['p'] * new_q
                c1.write(f"**{art}** ({d['p']}$)")
                if c3.button("🗑️", key=f"del_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            p_final = total_usd if devise == "USD" else total_usd * sh_inf[1]
            st.markdown(f"<div class='neon-total'><center><span class='total-val'>{p_final:,.2f} {devise}</span></center></div>", unsafe_allow_html=True)
            
            with st.form("validation"):
                client = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                paiement = st.number_input(f"MONTANT REÇU ({devise})", value=float(p_final))
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    p_u = paiement if devise == "USD" else paiement / sh_inf[1]
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, client, total_usd, p_u, total_usd-p_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        if (total_usd - p_u) > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid) VALUES (?,?,?,?)", (client, total_usd-p_u, ref, sid))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': client, 'total_val': p_final, 'dev': devise, 'paid': paiement, 'rest': p_final-paiement, 'items': st.session_state.session['cart'], 'date': datetime.now().strftime("%d/%m/%Y")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 6.3 GESTION STOCK (MODIFIER PRIX/QTÉ) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DES PRODUITS")
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("add"):
            n, pa, pv, q = st.text_input("Désignation"), st.number_input("Achat $"), st.number_input("Vente $"), st.number_input("Qté", 0)
            if st.form_submit_button("ENREGISTRER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n.upper(), q, pa, pv, sid))
                    conn.commit(); st.rerun()
    
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        for i_id, i_n, i_q, i_p in items:
            with st.expander(f"📦 {i_n} | Stock : {i_q} | Prix : {i_p}$"):
                col_q, col_p = st.columns(2)
                new_q = col_q.number_input("Modifier Stock", value=i_q, key=f"mq_{i_id}")
                new_p = col_p.number_input("Modifier Prix $", value=i_p, key=f"mp_{i_id}")
                if st.button("METTRE À JOUR", key=f"btn_{i_id}"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_p, i_id))
                    conn.commit(); st.rerun()

# --- 6.4 DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉDITS CLIENTS")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.success("Aucune dette en cours.")
        for di, dc, db in dettes:
            with st.expander(f"👤 {dc} | RESTE : {db:,.2f} $"):
                verse = st.number_input("Montant versé ($)", max_value=db, key=f"pay_{di}")
                if st.button("VALIDER TRANCHE", key=f"bpay_{di}"):
                    n_bal = db - verse
                    conn.execute("UPDATE debts SET balance=? WHERE id=?", (n_bal, di))
                    if n_bal <= 0.01: conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 6.5 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES RÉCENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql(f"SELECT ref, cli, total_usd, paid_usd, rest_usd, date, seller FROM sales WHERE sid='{sid}' ORDER BY id DESC LIMIT 50", conn)
        st.dataframe(df, use_container_width=True)

# --- 6.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    if st.session_state.session['role'] == "GERANT":
        st.subheader("➕ CRÉER UN COMPTE VENDEUR")
        with st.form("staff"):
            v_id, v_n, v_p = st.text_input("ID Vendeur"), st.text_input("Nom"), st.text_input("Pass", type="password")
            if st.form_submit_button("CRÉER"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_id.lower(), get_hash(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                        conn.commit(); st.success("Vendeur ajouté !")
                    except: st.error("ID déjà pris.")

# --- 6.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("boutique"):
        n_sh = st.text_input("Nom de la boutique", sh_inf[0])
        r_sh = st.number_input("Taux de change (1 USD = ? CDF)", value=sh_inf[1])
        if st.form_submit_button("SAUVEGARDER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=? WHERE sid=?", (n_sh, r_sh, sid))
                conn.commit(); st.success("Boutique mise à jour !"); st.rerun()

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()
