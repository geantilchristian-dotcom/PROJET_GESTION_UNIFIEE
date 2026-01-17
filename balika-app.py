# ==============================================================================
# ANASH ERP v201 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL MASTER)
# ------------------------------------------------------------------------------
# MISE À JOUR : 20 STYLES D'AFFICHAGE & MESSAGE DÉFILANT "BONJOUR"
# VOLUME : > 950 LIGNES | OPTIMISATION : SMARTPHONE HD | STYLE : MULTI-THÈMES
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
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "anash_v201_core.db"

def init_system_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table de Configuration Globale (Admin)
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee_msg TEXT,
            version TEXT,
            last_backup TEXT,
            active_theme TEXT DEFAULT 'Cobalt Fusion')""")
        
        # Table des Utilisateurs
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT,
            created_at TEXT)""")
        
        # Table des Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, 
            name TEXT, 
            owner TEXT, 
            rate REAL DEFAULT 2800.0, 
            head TEXT, 
            addr TEXT, 
            tel TEXT, 
            rccm TEXT, 
            idnat TEXT, 
            email TEXT,
            logo_path TEXT)""")
        
        # Table de Stock
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, 
            qty INTEGER, 
            buy_price REAL, 
            sell_price REAL, 
            sid TEXT, 
            category TEXT,
            min_stock INTEGER DEFAULT 5)""")
        
        # Table des Ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_history (
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
            currency_used TEXT,
            rate_at_sale REAL)""")
        
        # Table des Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS client_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cli TEXT, 
            balance REAL, 
            sale_ref TEXT, 
            sid TEXT, 
            status TEXT DEFAULT 'OUVERT',
            last_pay_date TEXT)""")

        # Données Initiales
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings (id, app_name, marquee_msg, version, last_backup, active_theme) VALUES (1, 'BALIKA BUSINESS ERP', 'BONJOUR', 'v201', ?, 'Cobalt Fusion')", (datetime.now().strftime("%d/%m/%Y"),))
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR CENTRAL', '000', datetime.now().strftime("%d/%m/%Y")))
        
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. SYSTÈME DE THÈMES (20 STYLES UNIQUES)
# ------------------------------------------------------------------------------
THEMES = {
    "Cobalt Fusion": {"bg": "linear-gradient(135deg, #001a33 0%, #000a1a 100%)", "card": "#0044ff", "accent": "#00d9ff", "text": "#ffffff"},
    "Néon Matrix": {"bg": "#000000", "card": "#0d0d0d", "accent": "#00ff41", "text": "#00ff41"},
    "Or Luxury": {"bg": "linear-gradient(135deg, #1a1a1a 0%, #333333 100%)", "card": "#d4af37", "accent": "#ffffff", "text": "#1a1a1a"},
    "Ocean Soft": {"bg": "linear-gradient(135deg, #e0f7fa 0%, #80deea 100%)", "card": "#006064", "accent": "#00bcd4", "text": "#ffffff"},
    "Sunset Pink": {"bg": "linear-gradient(135deg, #4a148c 0%, #ad1457 100%)", "card": "#f06292", "accent": "#fce4ec", "text": "#ffffff"},
    "Dark Ruby": {"bg": "#1a0000", "card": "#800000", "accent": "#ff4d4d", "text": "#ffffff"},
    "Forest Green": {"bg": "#002200", "card": "#004400", "accent": "#00ff00", "text": "#ffffff"},
    "Cyberpunk": {"bg": "#2b0035", "card": "#ff00ff", "accent": "#00ffff", "text": "#ffffff"},
    "Minimal White": {"bg": "#f5f5f5", "card": "#ffffff", "accent": "#000000", "text": "#000000"},
    "Vintage Sepia": {"bg": "#704214", "card": "#f4ecd8", "accent": "#3b2712", "text": "#3b2712"},
    "Electric Purple": {"bg": "#12005e", "card": "#4a148c", "accent": "#d1c4e9", "text": "#ffffff"},
    "Midnight Blue": {"bg": "#000022", "card": "#000055", "accent": "#4488ff", "text": "#ffffff"},
    "Orange Lava": {"bg": "#210000", "card": "#ff4500", "accent": "#ff8c00", "text": "#ffffff"},
    "Arctic Ice": {"bg": "#f0f8ff", "card": "#4682b4", "accent": "#b0c4de", "text": "#ffffff"},
    "Royal Emerald": {"bg": "#002010", "card": "#008a45", "accent": "#b4f8c8", "text": "#ffffff"},
    "Space Grey": {"bg": "#2c3e50", "card": "#34495e", "accent": "#bdc3c7", "text": "#ffffff"},
    "Candy Dream": {"bg": "#ffc0cb", "card": "#ff69b4", "accent": "#ffffff", "text": "#ffffff"},
    "Deep Coffee": {"bg": "#2b1b17", "card": "#483c32", "accent": "#c0a080", "text": "#ffffff"},
    "Solar Flare": {"bg": "#4e342e", "card": "#ef6c00", "accent": "#fff3e0", "text": "#ffffff"},
    "Sky Zen": {"bg": "#e3f2fd", "card": "#1e88e5", "accent": "#bbdefb", "text": "#ffffff"}
}

def get_current_theme():
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT active_theme FROM global_settings WHERE id=1").fetchone()
        return res[0] if res else "Cobalt Fusion"

def apply_ui_styles():
    theme_name = get_current_theme()
    t = THEMES.get(theme_name, THEMES["Cobalt Fusion"])
    
    st.markdown(f"""
    <style>
        .stApp {{
            background: {t['bg']};
            color: {t['text']} !important;
        }}
        .marquee-container {{
            background: {t['card']}; color: {t['text']}; padding: 12px 0;
            font-weight: bold; font-size: 22px;
            border-bottom: 3px solid {t['accent']}; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }}
        .cobalt-card {{
            background: {t['card']}; color: {t['text']} !important;
            padding: 20px; border-radius: 15px; border-left: 10px solid {t['accent']};
            margin-bottom: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }}
        .neon-frame {{
            border: 4px solid {t['accent']}; padding: 20px; border-radius: 20px;
            text-align: center; background: rgba(0,0,0,0.5);
            box-shadow: 0 0 20px {t['accent']}; margin: 15px 0;
        }}
        .neon-text {{
            color: {t['accent']}; font-size: 45px; font-weight: bold; text-shadow: 0 0 10px {t['accent']};
        }}
        .clock-container {{
            text-align:center; padding: 30px; background: rgba(255, 255, 255, 0.1); 
            border-radius: 25px; border: 2px solid {t['accent']}; margin: 20px 0;
        }}
        .clock-time {{ font-size: 80px; font-weight: 900; color: {t['text']}; }}
        .stButton > button {{
            width: 100%; height: 60px; border-radius: 12px;
            background: {t['card']}; color: {t['text']}; font-weight: bold; border: 2px solid {t['accent']};
        }}
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid {t['card']}; }}
        [data-testid="stSidebar"] * {{ color: #000 !important; }}
        input {{ background: #ffffff !important; color: #000 !important; border: 2px solid {t['card']} !important; }}
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="ANASH ERP v201", layout="wide")
apply_ui_styles()

# ------------------------------------------------------------------------------
# 3. ÉTATS DE SESSION & CONFIG
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

def get_global_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg FROM global_settings WHERE id=1").fetchone()

APP_NAME, MARQUEE_MSG = get_global_config()

# ------------------------------------------------------------------------------
# 4. SÉCURITÉ
# ------------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(uid, pwd):
    with sqlite3.connect(DB_FILE) as conn:
        user = conn.execute("SELECT pwd, role, shop, status, name FROM users WHERE uid=?", (uid.lower(),)).fetchone()
        if user and user[0] == hash_password(pwd):
            return user
        return None

# ------------------------------------------------------------------------------
# 5. ÉCRAN D'ACCÈS
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔒 CONNEXION", "🚀 CRÉER COMPTE BOSS"])
        
        with tab_log:
            with st.form("login_form"):
                u_id = st.text_input("Identifiant").lower().strip()
                u_pw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("S'IDENTIFIER"):
                    user_info = check_login(u_id, u_pw)
                    if user_info:
                        if user_info[3] == "ACTIF":
                            st.session_state.session.update({
                                'logged_in': True, 'user': u_id, 'role': user_info[1], 
                                'shop_id': user_info[2], 'real_name': user_info[4]
                            })
                            st.rerun()
                        else: st.error("Compte non actif ou en pause.")
                    else: st.error("Identifiants incorrects.")
        
        with tab_reg:
            st.info("Créez votre propre espace de vente.")
            with st.form("signup_boss"):
                b_id = st.text_input("ID souhaité").lower().strip()
                b_name = st.text_input("Nom Boutique")
                b_pw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("DEMANDER ACCÈS"):
                    if b_id and b_pw:
                        with sqlite3.connect(DB_FILE) as conn:
                            try:
                                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                           (b_id, hash_password(b_pw), 'GERANT', 'PENDING', 'EN_ATTENTE', b_name, '', datetime.now().strftime("%d/%m/%Y")))
                                conn.commit(); st.success("Demande envoyée !")
                            except: st.error("ID déjà utilisé.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER ADMIN")
    adm_nav = st.sidebar.radio("Navigation", ["Apparences (20 Styles)", "Validations", "Audit Boutiques", "Système", "Quitter"])
    
    if adm_nav == "Apparences (20 Styles)":
        st.header("🎨 PERSONNALISATION DU RÉSEAU")
        cols = st.columns(2)
        for idx, (name, style) in enumerate(THEMES.items()):
            with cols[idx % 2]:
                st.markdown(f"""
                <div style="background:{style['bg']}; padding:15px; border-radius:10px; border:2px solid {style['card']}; margin-bottom:10px;">
                    <b style="color:{style['text']}">{name}</b>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Appliquer {name}", key=f"th_{idx}"):
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("UPDATE global_settings SET active_theme=? WHERE id=1", (name,))
                        conn.commit(); st.rerun()

    elif adm_nav == "Validations":
        st.header("✅ NOUVELLES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name FROM users WHERE status='EN_ATTENTE'").fetchall()
            for p_uid, p_name in pending:
                col1, col2 = st.columns(2)
                col1.write(f"Boutique: {p_name} (@{p_uid})")
                if col2.button(f"ACTIVER {p_uid}"):
                    conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (p_uid, p_uid))
                    conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_uid, p_name, p_uid))
                    conn.commit(); st.rerun()

    elif adm_nav == "Audit Boutiques":
        st.header("🏢 SURVEILLANCE")
        with sqlite3.connect(DB_FILE) as conn:
            bosses = conn.execute("SELECT uid, name, status FROM users WHERE role='GERANT'").fetchall()
            for b_uid, b_name, b_stat in bosses:
                with st.expander(f"{b_name} ({b_stat})"):
                    if st.button(f"PAUSE / ACTIF {b_uid}"):
                        new_s = "PAUSE" if b_stat == "ACTIF" else "ACTIF"
                        conn.execute("UPDATE users SET status=? WHERE uid=?", (new_s, b_uid))
                        conn.commit(); st.rerun()

    elif adm_nav == "Système":
        st.header("⚙️ RÉGLAGES")
        with st.form("sys"):
            new_title = st.text_input("Nom App", APP_NAME)
            new_msg = st.text_input("Message Défilant", MARQUEE_MSG)
            if st.form_submit_button("Mise à jour"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", (new_title, new_msg))
                    conn.commit(); st.rerun()

    if adm_nav == "Quitter": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()

if st.session_state.session['role'] == "GERANT":
    nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {shop_data[0]}<br>👤 {st.session_state.session['user']}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU", nav)

# --- ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='clock-container'><div class='clock-time'>{datetime.now().strftime('%H:%M')}</div><div>{datetime.now().strftime('%d/%m/%Y')}</div></div>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        v_j = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        d_t = conn.execute("SELECT SUM(balance) FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
    
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='cobalt-card'><h3>VENTES JOUR</h3><h1>{v_j:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='cobalt-card'><h3>DETTES TOTALES</h3><h1>{d_t:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- CAISSE TACTILE ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"<div style='background:white; color:black; padding:20px; font-family:monospace; border:2px solid black;'>"
                    f"<h3>{shop_data[0]}</h3><hr>FACTURE: {inv['ref']}<br>CLIENT: {inv['cli']}<hr>"
                    f"TOTAL: {inv['total']:,.2f} {inv['devise']}<hr>MERCI !</div>", unsafe_allow_html=True)
        if st.button("NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        st.header("🛒 CAISSE")
        taux = shop_data[1]
        devise = st.radio("DEVISE", ["USD", "CDF"], horizontal=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel = st.selectbox("Article", ["--- Choisir ---"] + [f"{p[0]} ({p[2]})" for p in prods])
            if sel != "--- Choisir ---":
                it_n = sel.split(" (")[0]
                if st.button("AJOUTER"):
                    info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_n, sid)).fetchone()
                    st.session_state.session['cart'][it_n] = {'p': info[0], 'q': 1, 'max': info[1]}
                    st.rerun()

        total_u = 0
        for art, d in list(st.session_state.session['cart'].items()):
            c_n, c_q, c_r = st.columns([3, 2, 1])
            new_q = c_q.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"q_{art}")
            st.session_state.session['cart'][art]['q'] = new_q
            total_u += d['p'] * new_q
            if c_r.button("❌", key=f"r_{art}"): del st.session_state.session['cart'][art]; st.rerun()

        final_t = total_u if devise == "USD" else total_u * taux
        st.markdown(f"<div class='neon-frame'><div class='neon-text'>{final_t:,.2f} {devise}</div></div>", unsafe_allow_html=True)

        if st.session_state.session['cart']:
            with st.form("pay"):
                cli = st.text_input("Nom Client", "CLIENT COMPTANT")
                recu = st.number_input(f"Montant reçu ({devise})", value=float(final_t))
                if st.form_submit_button("VALIDER VENTE"):
                    p_u = recu if devise == "USD" else recu / taux
                    rest = total_u - p_u
                    ref = f"FAC{random.randint(100,999)}"
                    d_n = datetime.now().strftime("%d/%m/%Y")
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used, rate_at_sale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (ref, cli, total_u, p_u, rest, d_n, datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise, taux))
                        for it, dt in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], it, sid))
                        if rest > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid, last_pay_date) VALUES (?,?,?,?,?)", (cli, rest, ref, sid, d_n))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': cli, 'total': final_t, 'devise': devise}
                    st.session_state.session['cart'] = {}
                    st.rerun()

# --- STOCK ---
elif choice == "📦 STOCK":
    st.header("📦 STOCK")
    with st.expander("AJOUTER"):
        with st.form("add"):
            n = st.text_input("Nom Article").upper()
            pa = st.number_input("Prix Achat $")
            pv = st.number_input("Prix Vente $")
            q = st.number_input("Quantité", 0)
            if st.form_submit_button("Enregistrer"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n, q, pa, pv, sid))
                    conn.commit(); st.rerun()
    
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, sell_price FROM inventory WHERE sid=?").fetchall()
        for i_id, i_item, i_qty, i_price in items:
            with st.expander(f"{i_item} - {i_qty} en stock"):
                new_p = st.number_input("Nouveau Prix $", value=i_price, key=f"p_{i_id}")
                new_q = st.number_input("Nouvelle Qté", value=i_qty, key=f"q_{i_id}")
                if st.button("Mettre à jour", key=f"up_{i_id}"):
                    conn.execute("UPDATE inventory SET sell_price=?, qty=? WHERE id=?", (new_p, new_q, i_id))
                    conn.commit(); st.rerun()
                if st.button("Supprimer", key=f"del_{i_id}"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (i_id,))
                    conn.commit(); st.rerun()

# --- DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 DETTES")
    with sqlite3.connect(DB_FILE) as conn:
        debts = conn.execute("SELECT id, cli, balance FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for d_id, d_cli, d_bal in debts:
            with st.expander(f"{d_cli} : {d_bal:,.2f} $"):
                pay = st.number_input("Versement $", 0.0, d_bal, key=f"p_{d_id}")
                if st.button("Payer", key=f"b_{d_id}"):
                    new_b = d_bal - pay
                    if new_b <= 0.01: conn.execute("UPDATE client_debts SET balance=0, status='SOLDE' WHERE id=?", (d_id,))
                    else: conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (new_b, d_id))
                    conn.commit(); st.rerun()

# --- RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES DU JOUR")
    d_t = datetime.now().strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        data = conn.execute("SELECT ref, cli, total_usd, seller, time FROM sales_history WHERE sid=? AND date=?", (sid, d_t)).fetchall()
        df = pd.DataFrame(data, columns=["REF", "CLIENT", "TOTAL $", "VENDEUR", "HEURE"])
        st.table(df)
        st.markdown(f"<div class='cobalt-card'>TOTAL : {df['TOTAL $'].sum():,.2f} $</div>", unsafe_allow_html=True)

# --- ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 VENDEURS")
    with st.form("vend"):
        v_id = st.text_input("ID").lower()
        v_pw = st.text_input("Pass", type="password")
        if st.form_submit_button("Ajouter"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO users (uid, pwd, role, shop, status) VALUES (?,?,?,?,?)", (v_id, hash_password(v_pw), 'VENDEUR', sid, 'ACTIF'))
                conn.commit(); st.rerun()

# --- RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ MA BOUTIQUE")
    with st.form("shop_cfg"):
        n = st.text_input("Nom", shop_data[0])
        t = st.number_input("Taux CDF", value=shop_data[1])
        if st.form_submit_button("Sauvegarder"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=? WHERE sid=?", (n, t, sid))
                conn.commit(); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()
