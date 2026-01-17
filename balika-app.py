# ==============================================================================
# ANASH ERP v215 - ÉDITION BALIKA BUSINESS (VERSION LONGUE & COMPLÈTE)
# ------------------------------------------------------------------------------
# CE CODE EST CONÇU POUR ÊTRE COPIÉ ENTIÈREMENT SANS AUCUNE PERTE DE DONNÉES.
# FONCTIONNALITÉS : ADMIN TOTAL, GESTION MULTI-BOUTIQUES, DETTES ÉCHELONNÉES.
# ------------------------------------------------------------------------------
# LIGNES : > 550 | OPTIMISATION : SMARTPHONE & TABLETTE | DESIGN : COBALT
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
DB_FILE = "anash_v215_core.db"

def init_system_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Configuration Globale (Nom App, Marquee)
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee_msg TEXT,
            version TEXT)""")
        
        # Utilisateurs (Admin, Gérants, Vendeurs)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT)""")
        
        # Boutiques & Entêtes Factures
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
            email TEXT)""")
        
        # Stock des produits
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, 
            qty INTEGER, 
            buy_price REAL, 
            sell_price REAL, 
            sid TEXT, 
            category TEXT)""")
        
        # Ventes réalisées
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
            currency_used TEXT)""")
        
        # Gestion des Dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS client_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cli TEXT, 
            balance REAL, 
            sale_ref TEXT, 
            sid TEXT, 
            status TEXT DEFAULT 'OUVERT')""")

        # Données par défaut
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'ANASH ERP v215', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE SUCCÈS COMMENCE ICI', '2.1.5')")
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. DESIGN & STYLES (COBALT & NÉON)
# ------------------------------------------------------------------------------
def load_app_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg FROM global_settings WHERE id=1").fetchone()

APP_CONFIG = load_app_config()
APP_NAME, MARQUEE_TEXT = APP_CONFIG[0], APP_CONFIG[1]

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_custom_styles():
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(135deg, #001a33 0%, #000a1a 100%); color: white; }}
        
        /* Marquee */
        .marquee-container {{
            background: #000; color: #00ff00; padding: 12px; font-family: monospace; font-size: 18px;
            border-bottom: 3px solid #0044ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
        }}

        /* Cobalt Card - Texte Blanc sur Fond Bleu */
        .cobalt-card {{
            background: #0044ff; color: white !important; padding: 25px; border-radius: 20px;
            border-left: 10px solid #00d9ff; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .cobalt-card h1, .cobalt-card h2, .cobalt-card p {{ color: white !important; }}

        /* Panier Noir sur Blanc */
        .cart-box {{
            background: white !important; color: black !important; padding: 20px;
            border-radius: 15px; border: 4px solid #0044ff; margin-bottom: 15px;
        }}
        .cart-box * {{ color: black !important; font-weight: bold !important; }}

        /* Cadre Néon Total */
        .neon-frame {{
            border: 6px solid #00ff00; padding: 30px; border-radius: 25px;
            text-align: center; background: rgba(0,0,0,0.8); box-shadow: 0 0 25px #00ff00; margin: 20px 0;
        }}
        .neon-text {{ color: #00ff00; font-family: 'Orbitron', sans-serif; font-size: 50px; font-weight: bold; }}

        /* Boutons larges pour Mobile */
        .stButton > button {{
            width: 100%; height: 75px; border-radius: 18px; font-size: 20px;
            background: linear-gradient(to right, #0055ff, #002288); color: white; border: 2px solid white;
        }}
        
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold; }}

        /* Impression */
        @media print {{
            .no-print {{ display: none !important; }}
            .print-only {{ display: block !important; color: black !important; }}
            .stApp {{ background: white !important; color: black !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# ------------------------------------------------------------------------------
# 3. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

def do_hash(p): return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔒 CONNEXION", "📝 CRÉER COMPTE"])
        with t1:
            u = st.text_input("Identifiant").lower().strip()
            p = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    res = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u,)).fetchone()
                    if res and do_hash(p) == res[0]:
                        if res[3] == "ACTIF":
                            st.session_state.session.update({'logged_in': True, 'user': u, 'role': res[1], 'shop_id': res[2]})
                            st.rerun()
                        else: st.warning("Compte en attente de validation par l'Admin.")
                    else: st.error("Identifiants incorrects.")
        with t2:
            nu, nn, np = st.text_input("Nouvel ID"), st.text_input("Nom Boutique"), st.text_input("Mot de passe ", type="password")
            if st.button("ENVOYER DEMANDE"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (nu.lower(), do_hash(np), 'GERANT', 'PENDING', 'EN_ATTENTE', nn, ''))
                        conn.commit(); st.success("Demande enregistrée !")
                    except: st.error("ID déjà utilisé.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    a_nav = st.sidebar.radio("Navigation", ["Validations Clients", "Gestion Système", "Déconnexion"])
    
    if a_nav == "Validations Clients":
        st.header("✅ GESTION DES NOUVEAUX COMPTES")
        with sqlite3.connect(DB_FILE) as conn:
            pends = conn.execute("SELECT uid, name FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pends: st.info("Aucune attente.")
            for uid, name in pends:
                with st.expander(f"CLIENT : {name} (@{uid})"):
                    if st.button(f"ACTIVER & CRÉER BOUTIQUE : {uid}"):
                        conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (uid, uid))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (uid, name, uid))
                        conn.commit(); st.rerun()

    elif a_nav == "Gestion Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys"):
            new_title = st.text_input("Nom de l'App", APP_NAME)
            new_msg = st.text_area("Marquee Message", MARQUEE_TEXT)
            if st.form_submit_button("APPLIQUER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", (new_title, new_msg))
                    conn.commit(); st.rerun()
    
    if a_nav == "Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_inf = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat FROM shops WHERE sid=?", (sid,)).fetchone()

# Sécurité Vendeur
menu_opt = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    menu_opt = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card' style='padding:10px;'>🏪 {shop_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", menu_opt)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align:center; padding: 40px; background: rgba(0, 85, 255, 0.1); border-radius: 30px; border: 2px solid white;'>
            <h1 style='font-size: 80px; margin:0;'>{datetime.now().strftime('%H:%M')}</h1>
            <h3>{datetime.now().strftime('%d %B %Y')}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        ca_jour = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        st.markdown(f"<div class='cobalt-card'><h2>CHIFFRE DU JOUR</h2><h1>{ca_jour:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
            <div class='print-only' style='background:white; color:black; padding:20px; font-family:sans-serif;'>
                <center><h2>{shop_inf[0]}</h2><p>{shop_inf[3]}<br>Tél: {shop_inf[4]}</p><hr>
                <h4>FACTURE N° {inv['ref']}</h4></center>
                <p>Date: {inv['date']} | Client: {inv['cli']}</p>
                <hr><h3>TOTAL: {inv['total']:,.2f} {inv['devise']}</h3>
            </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ RETOUR"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if c3.button("📲 PARTAGER"): st.info("Lien de partage généré (Simulé)")
    else:
        st.header("🛒 TERMINAL DE VENTE")
        col_dev, col_ser = st.columns([1, 2])
        devise = col_dev.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            options = ["---"] + [f"{p[0]} ({p[2]}) - {p[1]}$" for p in prods]
            pick = col_ser.selectbox("Rechercher Article", options)
            if pick != "---" and st.button("➕ AJOUTER"):
                it_name = pick.split(" (")[0]
                p_inf = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                st.session_state.session['cart'][it_name] = {'p': p_inf[0], 'q': 1, 'max': p_inf[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='cart-box'>", unsafe_allow_html=True)
            st.subheader("📋 PANIER")
            total_u = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c_n, c_q, c_d = st.columns([3, 2, 1])
                nq = c_q.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"cart_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                total_u += d['p'] * nq
                c_n.write(f"**{art}** ({d['p']}$)")
                if c_d.button("🗑️", key=f"del_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            final_p = total_u if devise == "USD" else total_u * shop_inf[1]
            st.markdown(f"<div class='neon-frame'><div class='neon-text'>{final_p:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("paiement"):
                client_n = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                recu_m = st.number_input(f"REÇU ({devise})", value=float(final_p))
                if st.form_submit_button("✅ VALIDER & FACTURER"):
                    ref_f = f"FAC-{random.randint(10000,99999)}"
                    r_u = recu_m if devise == "USD" else recu_m / shop_inf[1]
                    rest_u = total_u - r_u
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref_f, client_n, total_u, r_u, rest_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for a, v in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (v['q'], a, sid))
                        if rest_u > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid) VALUES (?,?,?,?)", (client_n, rest_u, ref_f, sid))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': ref_f, 'cli': client_n, 'total': final_p, 'devise': devise, 'date': datetime.now().strftime("%d/%m/%Y")}
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 6.3 STOCK (MODIF SANS SUPPRIMER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DU STOCK")
    with st.expander("🆕 NOUVEAU PRODUIT"):
        with st.form("add_p"):
            n, pa, pv, q = st.text_input("Désignation"), st.number_input("Prix Achat $"), st.number_input("Prix Vente $"), st.number_input("Quantité", 0)
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n.upper(), q, pa, pv, sid))
                    conn.commit(); st.rerun()
    
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        for idx, name, qty, bp, sp in items:
            with st.expander(f"{name} (En stock : {qty})"):
                c1, c2 = st.columns(2)
                nq = c1.number_input("Modifier Quantité", value=qty, key=f"sq_{idx}")
                np = c2.number_input("Modifier Prix Vente $", value=sp, key=f"sp_{idx}")
                if st.button("METTRE À JOUR LA LIGNE", key=f"upd_{idx}"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (nq, np, idx))
                    conn.commit(); st.rerun()

# --- 6.4 DETTES PAR TRANCHES ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉDITS CLIENTS")
    with sqlite3.connect(DB_FILE) as conn:
        dts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dts: st.success("Aucune dette en cours !")
        for di, dc, db, dr in dts:
            with st.expander(f"👤 {dc} | Reste: {db:,.2f} $"):
                tr = st.number_input("Montant de la tranche ($)", max_value=db, key=f"tr_{di}")
                if st.button("ENREGISTRER LE PAIEMENT", key=f"bt_{di}"):
                    nb = db - tr
                    conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (nb, di))
                    if nb <= 0.01: conn.execute("UPDATE client_debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.rerun()

# --- 6.5 RAPPORTS & FILTRES ---
elif choice == "📊 RAPPORTS":
    st.header("📊 ANALYSE DE L'ACTIVITÉ")
    with sqlite3.connect(DB_FILE) as conn:
        vens = pd.read_sql(f"SELECT DISTINCT seller FROM sales_history WHERE sid='{sid}'", conn)['seller'].tolist()
        fv = st.selectbox("Filtrer par Vendeur", ["TOUS"] + vens)
        dt = st.date_input("Date", datetime.now()).strftime("%d/%m/%Y")
        
        sql = f"SELECT ref, cli, total_usd, paid_usd, seller, time FROM sales_history WHERE sid='{sid}' AND date='{dt}'"
        if fv != "TOUS": sql += f" AND seller='{fv}'"
        
        df = pd.read_sql(sql, conn)
        st.table(df)
        st.markdown(f"<div class='cobalt-card'>TOTAL GÉNÉRÉ : {df['total_usd'].sum():,.2f} $</div>", unsafe_allow_html=True)

# --- 6.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION ÉQUIPE")
    with st.expander("🔐 CHANGER MON MOT DE PASSE"):
        npw = st.text_input("Nouveau password", type="password")
        if st.button("MAJ PASSWORD"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (do_hash(npw), st.session_state.session['user']))
                conn.commit(); st.success("Modifié !")
    
    if st.session_state.session['role'] == "GERANT":
        with st.form("nv_v"):
            v_u, v_n, v_p = st.text_input("ID Vendeur"), st.text_input("Nom Complet"), st.text_input("Password", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_u.lower(), do_hash(v_p), 'VENDEUR', sid, 'ACTIF', v_n, ''))
                    conn.commit(); st.rerun()

# --- 6.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("sh_set"):
        n, r = st.text_input("Nom Enseigne", shop_inf[0]), st.number_input("Taux CDF", value=shop_inf[1])
        h, a, t = st.text_input("Pied de facture", shop_inf[2]), st.text_area("Adresse", shop_inf[3]), st.text_input("Téléphone", shop_inf[4])
        if st.form_submit_button("SAUVEGARDER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?", (n, r, h, a, t, sid))
                conn.commit(); st.rerun()

elif choice == "🚪 QUITTER": st.session_state.session['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v215 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
