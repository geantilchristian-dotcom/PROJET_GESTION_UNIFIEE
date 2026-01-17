# ==============================================================================
# ANASH ERP v220 - ÉDITION BALIKA BUSINESS (FULL BLUE EDITION)
# ------------------------------------------------------------------------------
# CORRECTIF : Gestion des doublons ID (IntegrityError)
# DESIGN : Intégralité de l'application en BLEU avec texte BLANC.
# LIGNES : > 600 | OPTIMISATION : SMARTPHONE & TABLETTE
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
# 1. BASE DE DONNÉES (MOTEUR CENTRAL)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v220_core.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Paramètres globaux
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee_msg TEXT, version TEXT)""")
        
        # Utilisateurs (uid est UNIQUE)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        
        # Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT, email TEXT)""")
        
        # Inventaire
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
        
        # Ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency_used TEXT)""")
        
        # Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS client_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")

        # Initialisation Admin & Config
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION UNIFIÉ', '2.2.0')")
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_db()

# ------------------------------------------------------------------------------
# 2. DESIGN "ALL BLUE" (TEXTE BLANC SUR FOND BLEU)
# ------------------------------------------------------------------------------
def load_cfg():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg FROM global_settings WHERE id=1").fetchone()

APP_CFG = load_cfg()
APP_NAME, MARQUEE_TEXT = APP_CFG[0], APP_CFG[1]

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_blue_theme():
    st.markdown(f"""
    <style>
        /* Fond global Bleu */
        .stApp {{
            background: #003366 !important;
            color: white !important;
        }}
        
        /* Sidebar Bleue avec texte Blanc */
        [data-testid="stSidebar"] {{
            background-color: #002244 !important;
            border-right: 2px solid #0055ff;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}

        /* Marquee */
        .marquee-bar {{
            background: #001122; color: #00ffcc; padding: 10px; font-weight: bold;
            border-bottom: 2px solid white; position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
        }}

        /* Cartes Bleues */
        .blue-card {{
            background: #0055ff; color: white !important; padding: 20px; border-radius: 15px;
            border: 2px solid white; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}
        
        /* Panier spécial Lisibilité (Noir sur Blanc comme demandé avant) */
        .cart-white {{
            background: white !important; color: black !important; padding: 15px;
            border-radius: 10px; border: 3px solid #0055ff;
        }}
        .cart-white * {{ color: black !important; font-weight: bold; }}

        /* Cadre Néon pour le Total */
        .total-frame {{
            border: 5px solid #00ff00; padding: 20px; border-radius: 20px;
            background: black; text-align: center; margin: 15px 0;
        }}
        .total-text {{ color: #00ff00; font-size: 40px; font-weight: bold; }}

        /* Boutons larges */
        .stButton > button {{
            width: 100%; height: 60px; border-radius: 12px; font-size: 18px;
            background: #0077ff; color: white; border: 1px solid white; font-weight: bold;
        }}
        .stButton > button:hover {{ background: #0055cc; border: 2px solid #00ffcc; }}

        /* Inputs */
        input {{ background-color: white !important; color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_blue_theme()

# ------------------------------------------------------------------------------
# 3. LOGIQUE DE SÉCURITÉ
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {'logged_in': False, 'user': None, 'role': None, 'shop_id': None, 'cart': {}, 'viewing_invoice': None}

def hash_p(p): return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION / LOGIN
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 CONNEXION", "📝 DEMANDE D'ACCÈS"])
        with t1:
            u_in = st.text_input("Identifiant").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    res = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_in,)).fetchone()
                    if res and hash_p(p_in) == res[0]:
                        if res[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u_in, 'role': res[1], 'shop_id': res[2]})
                            st.rerun()
                        else: st.error("Compte inactif. Contactez l'administrateur.")
                    else: st.error("Identifiants invalides.")
        with t2:
            nu = st.text_input("Choisir un ID").lower().strip()
            nn = st.text_input("Nom de votre Boutique")
            np = st.text_input("Mot de passe souhaité", type="password")
            if st.button("ENVOYER LA DEMANDE"):
                if nu and np:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (nu, hash_p(np), 'GERANT', 'PENDING', 'EN_ATTENTE', nn, ''))
                            conn.commit(); st.success("Demande envoyée !")
                        except sqlite3.IntegrityError: st.error("Cet identifiant est déjà pris.")
                else: st.warning("Veuillez remplir tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.markdown("### 🛡️ ADMINISTRATION")
    adm_choice = st.sidebar.radio("Menu Admin", ["Demandes d'accès", "Gestion Utilisateurs", "Réglages Système", "Déconnexion"])
    
    if adm_choice == "Demandes d'accès":
        st.header("✅ VALIDATIONS")
        with sqlite3.connect(DB_FILE) as conn:
            pends = conn.execute("SELECT uid, name FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pends: st.info("Aucune demande en attente.")
            for u, n in pends:
                with st.expander(f"Boutique : {n} (ID: {u})"):
                    if st.button(f"ACTIVER {u}"):
                        conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (u, u))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (u, n, u))
                        conn.commit(); st.rerun()

    elif adm_choice == "Gestion Utilisateurs":
        st.header("👥 TOUS LES COMPTES")
        with sqlite3.connect(DB_FILE) as conn:
            users = pd.read_sql("SELECT uid, role, shop, status FROM users", conn)
            st.dataframe(users, use_container_width=True)
            uid_mod = st.text_input("Entrez un ID pour supprimer")
            if st.button("SUPPRIMER CET UTILISATEUR"):
                conn.execute("DELETE FROM users WHERE uid=?", (uid_mod,))
                conn.commit(); st.rerun()

    elif adm_choice == "Réglages Système":
        with st.form("sys"):
            n_name = st.text_input("Nom App", APP_NAME)
            n_msg = st.text_area("Texte défilant", MARQUEE_TEXT)
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", (n_name, n_msg))
                    conn.commit(); st.rerun()
    
    if adm_choice == "Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. PANEL BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop = conn.execute("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()

# Menu adaptatif
nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='blue-card'>🏪 {shop[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", nav)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; font-size:60px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>{datetime.now().strftime('%d/%m/%Y')}</h3>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        ca = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        st.markdown(f"<div class='blue-card' style='text-align:center;'><h2>CHIFFRE D'AFFAIRE JOUR</h2><h1 style='font-size:50px;'>{ca:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
            <div style='background:white; color:black; padding:20px; border-radius:10px; border:2px solid black;'>
                <center><h2>{shop[0]}</h2><p>{shop[3]}<br>Tél: {shop[4]}</p><hr>
                <h4>FACTURE N° {inv['ref']}</h4></center>
                <p>Date: {inv['date']} | Client: {inv['cli']}</p>
                <hr><h3>TOTAL: {inv['total']:,.2f} {inv['devise']}</h3>
            </div>
        """, unsafe_allow_html=True)
        if st.button("NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
    else:
        st.header("🛒 CAISSE")
        c_dev, c_ser = st.columns([1, 2])
        devise = c_dev.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            options = ["---"] + [f"{p[0]} ({p[2]}) - {p[1]}$" for p in prods]
            pick = c_ser.selectbox("Rechercher Article", options)
            if pick != "---" and st.button("➕ AJOUTER AU PANIER"):
                it_name = pick.split(" (")[0]
                p_inf = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                st.session_state.session['cart'][it_name] = {'p': p_inf[0], 'q': 1, 'max': p_inf[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='cart-white'>", unsafe_allow_html=True)
            st.subheader("📋 PANIER EN COURS")
            total_u = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c_n, c_q, c_d = st.columns([3, 2, 1])
                nq = c_q.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"c_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                total_u += d['p'] * nq
                c_n.write(f"**{art}** ({d['p']}$)")
                if c_d.button("🗑️", key=f"d_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            final_p = total_u if devise == "USD" else total_u * shop[1]
            st.markdown(f"<div class='total-frame'><div class='total-text'>{final_p:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("vente"):
                client = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                recu = st.number_input(f"MONTANT REÇU ({devise})", value=float(final_p))
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    r_u = recu if devise == "USD" else recu / shop[1]
                    rest = total_u - r_u
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref, client, total_u, r_u, rest, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for a, v in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (v['q'], a, sid))
                        if rest > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid) VALUES (?,?,?,?)", (client, rest, ref, sid))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref, 'cli': client, 'total': final_p, 'devise': devise, 'date': datetime.now().strftime("%d/%m/%Y")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 6.3 STOCK (MODIF PRIX & QTE SANS SUPPRIMER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DU STOCK")
    with st.expander("🆕 AJOUTER UN PRODUIT"):
        with st.form("add"):
            n = st.text_input("Nom de l'article")
            pa = st.number_input("Prix Achat ($)")
            pv = st.number_input("Prix Vente ($)")
            q = st.number_input("Quantité initiale", 0)
            if st.form_submit_button("AJOUTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n.upper(), q, pa, pv, sid))
                    conn.commit(); st.rerun()

    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        for idx, name, qty, bp, sp in items:
            with st.expander(f"⚙️ {name} (Stock: {qty})"):
                c1, c2 = st.columns(2)
                nq = c1.number_input("Nouvelle Qté", value=qty, key=f"q_{idx}")
                np = c2.number_input("Nouveau Prix Vente $", value=sp, key=f"p_{idx}")
                if st.button("METTRE À JOUR", key=f"btn_{idx}"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (nq, np, idx))
                    conn.commit(); st.success("Mis à jour !"); st.rerun()

# --- 6.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 PAIEMENT DES DETTES")
    with sqlite3.connect(DB_FILE) as conn:
        dts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dts: st.info("Aucun crédit en cours.")
        for di, dc, db, dr in dts:
            with st.expander(f"👤 {dc} | RESTANT : {db:,.2f} $"):
                tr = st.number_input("Somme versée ($)", max_value=db, key=f"tr_{di}")
                if st.button("ENREGISTRER TRANCHE", key=f"p_{di}"):
                    nb = db - tr
                    conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (nb, di))
                    if nb <= 0.01: conn.execute("UPDATE client_debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 6.5 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    with sqlite3.connect(DB_FILE) as conn:
        vens = pd.read_sql(f"SELECT DISTINCT seller FROM sales_history WHERE sid='{sid}'", conn)['seller'].tolist()
        fv = st.selectbox("Filtrer par Vendeur", ["TOUS"] + vens)
        dt = st.date_input("Choisir Date", datetime.now()).strftime("%d/%m/%Y")
        
        sql = f"SELECT ref, cli, total_usd, paid_usd, rest_usd, seller, time FROM sales_history WHERE sid='{sid}' AND date='{dt}'"
        if fv != "TOUS": sql += f" AND seller='{fv}'"
        
        df = pd.read_sql(sql, conn)
        st.dataframe(df, use_container_width=True)
        st.markdown(f"<div class='blue-card'>Total Sélection : {df['total_usd'].sum():,.2f} $</div>", unsafe_allow_html=True)

# --- 6.6 ÉQUIPE (CORRECTIF BUG INSERTION) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 MON ÉQUIPE")
    if st.session_state.session['role'] == "GERANT":
        with st.form("new_vendeur"):
            v_u = st.text_input("ID Vendeur (Unique)")
            v_n = st.text_input("Nom Complet")
            v_p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                with sqlite3.connect(DB_FILE) as conn:
                    # Vérification avant insertion pour éviter l'IntegrityError
                    exists = conn.execute("SELECT uid FROM users WHERE uid=?", (v_u.lower(),)).fetchone()
                    if exists:
                        st.error("❌ Cet ID existe déjà. Veuillez en choisir un autre.")
                    else:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_u.lower(), hash_p(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                        conn.commit(); st.success("Vendeur ajouté avec succès !")
    
    st.divider()
    with st.expander("🔐 MON MOT DE PASSE"):
        new_pw = st.text_input("Nouveau password", type="password")
        if st.button("CHANGER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (hash_p(new_pw), st.session_state.session['user']))
                conn.commit(); st.success("Mot de passe modifié !")

# --- 6.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ RÉGLAGES BOUTIQUE")
    with st.form("shop_cfg"):
        sn = st.text_input("Nom Enseigne", shop[0])
        sr = st.number_input("Taux de change (1$ = ? CDF)", value=shop[1])
        sa = st.text_area("Adresse", shop[3])
        st_ = st.text_input("Téléphone", shop[4])
        if st.form_submit_button("SAUVEGARDER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, addr=?, tel=? WHERE sid=?", (sn, sr, sa, st_, sid))
                conn.commit(); st.rerun()

elif choice == "🚪 QUITTER": st.session_state.session['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v220 - TOUT EN BLEU ET SÉCURISÉ
# ==============================================================================
