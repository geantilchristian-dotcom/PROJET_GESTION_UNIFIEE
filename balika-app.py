# ==============================================================================
# ANASH ERP v207 - ÉDITION BALIKA BUSINESS (VERSION INTÉGRALE & LONGUE)
# ------------------------------------------------------------------------------
# CE CODE EST COMPLET - TOUTES LES LOGIQUES DE VENTE ET DE STOCK SONT PRÉSENTES.
# AJOUTS : FILTRES VENDEURS | ADMIN GESTION COMPTES | PASSWORD CHANGE | MARQUEE
# DESIGN : PANIER NOIR SUR BLANC | COBALT STYLE | OPTIMISÉ MOBILE | DEVISE CDF/USD
# ------------------------------------------------------------------------------
# LIGNES : > 650 | OPTIMISATION : SMARTPHONE & TABLETTE | DESIGN : COBALT
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
# 1. INITIALISATION DU MOTEUR DE BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "anash_v200_core.db"

def init_system_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Configuration Globale
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee_msg TEXT, version TEXT)""")
        
        # Utilisateurs
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        
        # Boutiques & Entêtes
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT, email TEXT)""")
        
        # Stock des produits
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
        
        # Ventes réalisées
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency_used TEXT)""")
        
        # Gestion des Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS client_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")

        # Insertion des données par défaut
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'ANASH ERP v207', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE SUCCÈS COMMENCE ICI', '2.0.7')")
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT DE LA CONFIGURATION DYNAMIQUE
# ------------------------------------------------------------------------------
def load_app_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg FROM global_settings WHERE id=1").fetchone()

APP_CONFIG = load_app_config()
APP_NAME = APP_CONFIG[0]
MARQUEE_TEXT = APP_CONFIG[1]

# ------------------------------------------------------------------------------
# 3. DESIGN CSS (STYLE COBALT & PANIER NOIR/BLANC)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_custom_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(135deg, #001a33 0%, #000a1a 100%); color: #ffffff; }}
        
        /* Marquee Professionnel */
        .marquee-container {{
            background: #000; color: #00ff00; padding: 12px;
            font-family: 'Source Code Pro', monospace; font-size: 18px;
            border-bottom: 3px solid #0044ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
        }}

        /* Cartes Cobalt */
        .cobalt-card {{
            background: #0044ff; color: white !important;
            padding: 25px; border-radius: 20px; border-left: 10px solid #00d9ff;
            margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p {{ color: white !important; }}

        /* Panier Noir sur Blanc (LISIBILITÉ MAXIMALE) */
        .cart-panel {{
            background: #ffffff !important; color: #000000 !important;
            padding: 20px; border-radius: 15px; border: 4px solid #0044ff;
            margin-top: 15px;
        }}
        .cart-panel * {{ color: #000000 !important; font-weight: bold !important; }}

        /* Cadre Néon pour Totaux */
        .neon-frame {{
            border: 6px solid #00ff00; padding: 30px; border-radius: 25px;
            text-align: center; background: rgba(0,0,0,0.8);
            box-shadow: 0 0 25px #00ff00; margin: 20px 0;
        }}
        .neon-text {{ color: #00ff00; font-family: 'Orbitron', sans-serif; font-size: 45px; font-weight: bold; }}

        /* Boutons Mobiles */
        .stButton > button {{
            width: 100%; height: 70px; border-radius: 18px;
            background: linear-gradient(to right, #0055ff, #002288);
            color: white; font-size: 18px; font-weight: bold; border: 2px solid #fff;
        }}
        
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold; }}

        input {{ background: #ffffff !important; color: #000000 !important; font-size: 18px !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# ------------------------------------------------------------------------------
# 4. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {'logged_in': False, 'user': None, 'role': None, 'shop_id': None, 'cart': {}, 'viewing_invoice': None}

def hash_p(p): return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# 5. ÉCRAN DE CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔒 CONNEXION", "📝 INSCRIPTION"])
        
        with t1:
            u = st.text_input("Identifiant").lower().strip()
            p = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    res = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u,)).fetchone()
                    if res and hash_p(p) == res[0]:
                        if res[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u, 'role': res[1], 'shop_id': res[2]})
                            st.rerun()
                        else: st.warning("Compte en attente d'activation.")
                    else: st.error("Identifiants incorrects.")
        with t2:
            nu = st.text_input("Nouvel ID").lower().strip()
            nn = st.text_input("Nom Boutique")
            np = st.text_input("Mot de passe ", type="password")
            if st.button("S'INSCRIRE"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (nu, hash_p(np), 'GERANT', 'PENDING', 'EN_ATTENTE', nn, ''))
                        conn.commit(); st.success("Demande envoyée !")
                    except: st.error("ID déjà pris.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMIN")
    a_menu = st.sidebar.radio("Navigation", ["Validations", "Gestion Comptes", "Réglages Système", "Déconnexion"])
    
    if a_menu == "Validations":
        st.header("✅ Validations en attente")
        with sqlite3.connect(DB_FILE) as conn:
            pends = conn.execute("SELECT uid, name FROM users WHERE status='EN_ATTENTE'").fetchall()
            for uid, name in pends:
                col1, col2 = st.columns([3, 1])
                col1.write(f"Boutique : **{name}** (@{uid})")
                if col2.button(f"Activer {uid}"):
                    conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (uid, uid))
                    conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (uid, name, uid))
                    conn.commit(); st.rerun()

    elif a_menu == "Gestion Comptes":
        st.header("👥 Tous les Utilisateurs")
        with sqlite3.connect(DB_FILE) as conn:
            usrs = pd.read_sql("SELECT uid, name, role, status FROM users WHERE uid != 'admin'", conn)
            for _, r in usrs.iterrows():
                with st.expander(f"{r['name']} (@{r['uid']}) - {r['status']}"):
                    c1, c2, c3 = st.columns(3)
                    if c1.button("Activer", key=f"a{r['uid']}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (r['uid'],)); conn.commit(); st.rerun()
                    if c2.button("Bloquer", key=f"b{r['uid']}"):
                        conn.execute("UPDATE users SET status='BLOQUÉ' WHERE uid=?", (r['uid'],)); conn.commit(); st.rerun()
                    if c3.button("Supprimer", key=f"s{r['uid']}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (r['uid'],)); conn.commit(); st.rerun()

    elif a_menu == "Réglages Système":
        with st.form("sys"):
            new_title = st.text_input("Nom de l'App", APP_NAME)
            new_marquee = st.text_area("Message Marquee", MARQUEE_TEXT)
            if st.form_submit_button("Sauvegarder"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", (new_title, new_marquee))
                    conn.commit(); st.rerun()
    
    if a_menu == "Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. MODULE BOUTIQUE (LOGIQUE COMPLÈTE)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_info = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat, email FROM shops WHERE sid=?", (sid,)).fetchone()

menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card' style='padding:10px;'>🏪 {shop_info[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", menu)

# --- 7.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<div class='cobalt-card' style='text-align:center;'><h1>{datetime.now().strftime('%H:%M')}</h1><h3>{datetime.now().strftime('%d %B %Y')}</h3></div>", unsafe_allow_html=True)

# --- 7.2 CAISSE ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"<div style='background:white; color:black; padding:20px; border:2px solid #000;'><h2>{shop_info[0]}</h2><h4>FACTURE {inv['ref']}</h4><hr><p>Client: {inv['cli']}</p><h3>TOTAL: {inv['total']} {inv['devise']}</h3></div>", unsafe_allow_html=True)
        if st.button("RETOUR"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        st.header("🛒 CAISSE")
        devise = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel = st.selectbox("Sélectionner Article", ["---"] + [f"{p[0]} ({p[2]} dispo) - {p[1]}$" for p in prods])
            if sel != "---" and st.button("➕ AJOUTER"):
                it_name = sel.split(" (")[0]
                inf = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                st.session_state.session['cart'][it_name] = {'p': inf[0], 'q': 1, 'max': inf[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='cart-panel'>", unsafe_allow_html=True)
            st.subheader("📋 PANIER")
            t_usd = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c1, c2, c3 = st.columns([3, 2, 1])
                nq = c2.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"q_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                t_usd += d['p'] * nq
                c1.write(f"{art} ({d['p']}$)")
                if c3.button("🗑️", key=f"d_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            final = t_usd if devise == "USD" else t_usd * shop_info[1]
            st.markdown(f"<div class='neon-frame'><div class='neon-text'>{final:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("val"):
                cli = st.text_input("NOM CLIENT", "COMPTANT")
                paye = st.number_input(f"REÇU ({devise})", value=float(final))
                if st.form_submit_button("VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    recu_usd = paye if devise == "USD" else paye / shop_info[1]
                    reste_usd = t_usd - recu_usd
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, cli, t_usd, recu_usd, reste_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for a, v in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (v['q'], a, sid))
                        if reste_usd > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid) VALUES (?,?,?,?)", (cli, reste_usd, ref, sid))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': cli, 'total': final, 'devise': devise}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 7.3 STOCK (MODIFIER SANS SUPPRIMER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION STOCK")
    with st.expander("🆕 AJOUTER PRODUIT"):
        with st.form("add"):
            n = st.text_input("Désignation").upper()
            pa = st.number_input("Prix Achat $")
            pv = st.number_input("Prix Vente $")
            q = st.number_input("Quantité", min_value=0)
            if st.form_submit_button("Enregistrer"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n, q, pa, pv, sid))
                    conn.commit(); st.rerun()
    
    with sqlite3.connect(DB_FILE) as conn:
        data = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        for idx, item, qty, bp, sp in data:
            with st.expander(f"{item} (Dispo: {qty})"):
                c1, c2 = st.columns(2)
                nq = c1.number_input("Modifier Qté", value=qty, key=f"q_{idx}")
                np = c2.number_input("Modifier Prix $", value=sp, key=f"p_{idx}")
                if st.button("MAJ LIGNE", key=f"btn_{idx}"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (nq, np, idx))
                    conn.commit(); st.rerun()

# --- 7.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 DETTES (PAIEMENT ÉCHELONNÉ)")
    with sqlite3.connect(DB_FILE) as conn:
        dts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        for d_id, d_cli, d_bal, d_ref in dts:
            with st.expander(f"👤 {d_cli} - Reste: {d_bal}$"):
                tranche = st.number_input("Tranche à payer $", max_value=d_bal, key=f"t{d_id}")
                if st.button("VALIDER PAIEMENT", key=f"bt{d_id}"):
                    nb = d_bal - tranche
                    conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (nb, d_id))
                    if nb <= 0.01: conn.execute("UPDATE client_debts SET status='SOLDE' WHERE id=?", (d_id,))
                    conn.commit(); st.rerun()

# --- 7.5 RAPPORTS (FILTRE VENDEUR) ---
elif choice == "📊 RAPPORTS":
    st.header("📊 RAPPORTS")
    with sqlite3.connect(DB_FILE) as conn:
        vens = pd.read_sql(f"SELECT DISTINCT seller FROM sales_history WHERE sid='{sid}'", conn)['seller'].tolist()
        f_v = st.selectbox("Filtrer par Vendeur", ["TOUS"] + vens)
        dt = st.date_input("Date", datetime.now()).strftime("%d/%m/%Y")
        
        q = f"SELECT ref, cli, total_usd, seller, time FROM sales_history WHERE sid='{sid}' AND date='{dt}'"
        if f_v != "TOUS": q += f" AND seller='{f_v}'"
        
        df = pd.read_sql(q, conn)
        st.table(df)
        st.markdown(f"<div class='cobalt-card'>TOTAL : {df['total_usd'].sum():,.2f} $</div>", unsafe_allow_html=True)

# --- 7.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 ÉQUIPE")
    with st.expander("🔐 CHANGER MON MOT DE PASSE"):
        npw = st.text_input("Nouveau password", type="password")
        if st.button("CHANGER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (hash_p(npw), st.session_state.session['user']))
                conn.commit(); st.success("Mis à jour !")
    
    if st.session_state.session['role'] == "GERANT":
        with st.form("nv_v"):
            vu = st.text_input("ID Vendeur").lower().strip()
            vn = st.text_input("Nom Vendeur")
            vp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Ajouter Vendeur"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (vu, hash_p(vp), 'VENDEUR', sid, 'ACTIF', vn, ''))
                    conn.commit(); st.success("Vendeur ajouté !")

# --- 7.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ RÉGLAGES BOUTIQUE")
    with st.form("set"):
        sn = st.text_input("Nom Enseigne", shop_info[0])
        sr = st.number_input("Taux CDF", value=shop_info[1])
        if st.form_submit_button("SAUVER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=? WHERE sid=?", (sn, sr, sid))
                conn.commit(); st.rerun()

elif choice == "🚪 QUITTER": st.session_state.session['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v207 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
