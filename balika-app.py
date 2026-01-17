# ==============================================================================
# ANASH ERP v200 - ÉDITION BALIKA BUSINESS (VERSION LONGUE & COMPLÈTE)
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
DB_FILE = "anash_v200_core.db"

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

        # Insertion des données par défaut si vide
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'ANASH ERP v200', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE SUCCÈS COMMENCE ICI', '2.0.0')")
            
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
# 3. DESIGN CSS PERSONNALISÉ (STYLE COBALT & NÉON)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_custom_styles():
    st.markdown(f"""
    <style>
        /* Fond global sombre */
        .stApp {{
            background: linear-gradient(135deg, #001a33 0%, #000a1a 100%);
            color: #ffffff;
        }}

        /* Marquee Professionnel */
        .marquee-container {{
            background: #000; color: #00ff00; padding: 12px;
            font-family: 'Source Code Pro', monospace; font-size: 18px;
            border-bottom: 3px solid #0044ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
        }}

        /* Cartes Cobalt (Texte blanc sur fond bleu) */
        .cobalt-card {{
            background: #0044ff; color: white !important;
            padding: 25px; border-radius: 20px; border-left: 10px solid #00d9ff;
            margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p {{
            color: white !important;
        }}

        /* Cadre Néon pour les Totaux */
        .neon-frame {{
            border: 6px solid #00ff00; padding: 30px; border-radius: 25px;
            text-align: center; background: rgba(0,0,0,0.8);
            box-shadow: 0 0 25px #00ff00; margin: 20px 0;
        }}
        .neon-text {{
            color: #00ff00; font-family: 'Orbitron', sans-serif;
            font-size: 50px; font-weight: bold;
        }}

        /* Boutons pour Mobile */
        .stButton > button {{
            width: 100%; height: 75px; border-radius: 18px;
            background: linear-gradient(to right, #0055ff, #002288);
            color: white; font-size: 20px; font-weight: bold; border: 2px solid #fff;
        }}
        
        /* Sidebar custom */
        [data-testid="stSidebar"] {{
            background-color: #ffffff !important;
            border-right: 5px solid #0044ff;
        }}
        [data-testid="stSidebar"] * {{
            color: #001a33 !important; font-weight: bold;
        }}

        /* Inputs lisibles */
        input {{
            background: #ffffff !important; color: #000000 !important;
            font-size: 18px !important; font-weight: bold !important;
        }}
        
        .print-only {{ display: none; }}
        @media print {{
            .no-print {{ display: none !important; }}
            .print-only {{ display: block !important; color: black; }}
            .stApp {{ background: white !important; color: black !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# ------------------------------------------------------------------------------
# 4. GESTION DE LA SESSION UTILISATEUR
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

# ------------------------------------------------------------------------------
# 5. ÉCRAN D'ACCÈS (LOGIN ET INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["🔒 CONNEXION", "📝 CRÉER MON COMPTE"])
        
        with login_tab:
            u_id = st.text_input("Identifiant").lower().strip()
            u_pw = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU SYSTÈME"):
                with sqlite3.connect(DB_FILE) as conn:
                    user_data = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_id,)).fetchone()
                    if user_data and hashlib.sha256(u_pw.encode()).hexdigest() == user_data[0]:
                        if user_data[3] == "ACTIF":
                            st.session_state.session.update({
                                'logged_in': True, 'user': u_id, 'role': user_data[1], 'shop_id': user_data[2]
                            })
                            st.rerun()
                        else: st.warning("Votre compte est en attente d'activation par l'Admin.")
                    else: st.error("Identifiants incorrects.")
        
        with signup_tab:
            st.markdown("### Formulaire de demande")
            new_u = st.text_input("Choisir ID Utilisateur").lower().strip()
            new_n = st.text_input("Nom de votre Boutique")
            new_p = st.text_input("Créer un Mot de passe", type="password")
            new_t = st.text_input("Téléphone")
            if st.button("ENVOYER MA DEMANDE"):
                if new_u and new_p:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            hashed = hashlib.sha256(new_p.encode()).hexdigest()
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                       (new_u, hashed, 'GERANT', 'PENDING', 'EN_ATTENTE', new_n, new_t))
                            conn.commit()
                            st.success("Demande enregistrée ! L'administrateur va l'activer sous peu.")
                        except sqlite3.IntegrityError:
                            st.error("Cet identifiant est déjà utilisé.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMIN (ADMINISTRATION TOTALE)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMIN PANEL")
    adm_nav = st.sidebar.radio("Navigation", ["Validations Clients", "Réglages Système", "Déconnexion"])
    
    if adm_nav == "Validations Clients":
        st.header("✅ GESTION DES NOUVEAUX CLIENTS")
        with sqlite3.connect(DB_FILE) as conn:
            pending_users = conn.execute("SELECT uid, name, tel FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending_users:
                st.info("Aucune nouvelle demande d'inscription.")
            
            for p_uid, p_name, p_tel in pending_users:
                with st.expander(f"Client: {p_name} (@{p_uid})"):
                    st.write(f"📞 Tel: {p_tel}")
                    if st.button(f"ACTIVER & CRÉER BOUTIQUE POUR {p_uid}"):
                        # 1. Activation de l'utilisateur
                        conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (p_uid, p_uid))
                        # 2. Création automatique de la boutique (Essentiel !)
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", 
                                   (p_uid, p_name, p_uid))
                        conn.commit()
                        st.success(f"Compte {p_uid} est désormais opérationnel !")
                        st.rerun()

    elif adm_nav == "Réglages Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys_config"):
            new_title = st.text_input("Nom de l'Application", APP_NAME)
            new_marquee = st.text_area("Message Marquee", MARQUEE_TEXT)
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", 
                                (new_title, new_marquee))
                    conn.commit()
                st.success("Changements appliqués à tout le système ! Rechargement...")
                time.sleep(1)
                st.rerun()
    
    if adm_nav == "Déconnexion":
        st.session_state.session['logged_in'] = False
        st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (GÉRANTS & VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_info = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat, email FROM shops WHERE sid=?", (sid,)).fetchone()

# Si la boutique n'existe pas encore par erreur
if not shop_info:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (sid, "Ma Boutique", st.session_state.session['user']))
        conn.commit()
    st.rerun()

# ------------------------------------------------------------------------------
# 8. MENU PRINCIPAL BOUTIQUE
# ------------------------------------------------------------------------------
menu_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    menu_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card' style='padding:10px;'>🏪 {shop_info[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", menu_options)

# --- 8.1 TABLEAU DE BORD ---
if choice == "🏠 TABLEAU DE BORD":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Horloge 80mm style
    st.markdown(f"""
        <div style='text-align:center; padding: 40px; background: rgba(0, 85, 255, 0.1); border-radius: 30px; border: 2px solid white;'>
            <h1 style='font-size: 80px; margin:0;'>{datetime.now().strftime('%H:%M')}</h1>
            <h3>{datetime.now().strftime('%d %B %Y')}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Statistiques du jour
    today = datetime.now().strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        daily_sales = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        total_items = conn.execute("SELECT COUNT(*) FROM inventory WHERE sid=?", (sid,)).fetchone()[0]
        
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='cobalt-card'><h3>VENTES JOUR</h3><h1>{daily_sales:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='cobalt-card'><h3>ARTICLES EN STOCK</h3><h1>{total_items}</h1></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE TACTILE (MULTI-DEVISE) ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        # LOGIQUE D'AFFICHAGE DE FACTURE
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
        <div style='background: white; color: black; padding: 25px; border: 1px solid #000; font-family: sans-serif;'>
            <div style='text-align:center;'>
                <h2>{shop_info[0]}</h2>
                <p>{shop_info[5]} | {shop_info[6]}<br>{shop_info[3]}<br>Tél: {shop_info[4]}</p>
                <hr>
                <h4>FACTURE N° {inv['ref']}</h4>
            </div>
            <p><b>Client:</b> {inv['cli']} | <b>Date:</b> {inv['date']}</p>
            <table style='width:100%; border-collapse: collapse;'>
                <tr style='border-bottom: 2px solid #000;'><th>Article</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['p']:,.2f}</td><td>{(v['q']*v['p']):,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <h3 style='text-align:right;'>NET À PAYER: {inv['total']:,.2f} {inv['devise']}</h3>
            <p style='text-align:center;'>{shop_info[2]}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ RETOUR À LA CAISSE"):
            st.session_state.session['viewing_invoice'] = None
            st.rerun()
        if st.button("🖨️ IMPRIMER / PDF"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.header("🛒 TERMINAL DE VENTE")
        col_sel, col_mon = st.columns([2, 1])
        
        with col_mon:
            devise = st.radio("CHOIX DEVISE", ["USD", "CDF"], horizontal=True)
            taux_actuel = shop_info[1]
            st.info(f"Taux: 1$ = {taux_actuel} CDF")
            
        with col_sel:
            with sqlite3.connect(DB_FILE) as conn:
                prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
                options = ["--- Choisir un article ---"] + [f"{p[0]} ({p[2]} dispo) - {p[1]}$" for p in prods]
                search = st.selectbox("RECHERCHER ARTICLE", options)
                
                if search != "--- Choisir un article ---":
                    item_name = search.split(" (")[0]
                    if st.button("➕ AJOUTER AU PANIER"):
                        with sqlite3.connect(DB_FILE) as conn:
                            inf = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (item_name, sid)).fetchone()
                            st.session_state.session['cart'][item_name] = {'p': inf[0], 'q': 1, 'max': inf[1]}
                            st.rerun()

        if st.session_state.session['cart']:
            st.subheader("📋 PANIER EN COURS")
            total_panier_usd = 0.0
            
            for art, data in list(st.session_state.session['cart'].items()):
                c_n, c_q, c_d = st.columns([3, 2, 1])
                new_q = c_q.number_input(f"Qté {art}", 1, data['max'], data['q'], key=f"qte_{art}")
                st.session_state.session['cart'][art]['q'] = new_q
                stot = data['p'] * new_q
                total_panier_usd += stot
                c_n.markdown(f"**{art}**<br>{data['p']:,.2f} $", unsafe_allow_html=True)
                if c_d.button("🗑️", key=f"del_{art}"):
                    del st.session_state.session['cart'][art]
                    st.rerun()

            # Calcul conversion
            final_total = total_panier_usd if devise == "USD" else total_panier_usd * taux_actuel
            
            st.markdown(f"""
                <div class='neon-frame'>
                    <div style='font-size:20px; color:#00ff00;'>TOTAL À PAYER</div>
                    <div class='neon-text'>{final_total:,.2f} {devise}</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("vente_finale"):
                client_name = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                paiement_recu = st.number_input(f"MONTANT REÇU EN {devise}", value=float(final_total))
                
                if st.form_submit_button("✅ VALIDER & FACTURER"):
                    # Conversion en USD pour stockage
                    recu_usd = paiement_recu if devise == "USD" else paiement_recu / taux_actuel
                    reste_usd = total_panier_usd - recu_usd
                    
                    ref_fac = f"FAC-{random.randint(10000, 99999)}"
                    d_now = datetime.now().strftime("%d/%m/%Y")
                    t_now = datetime.now().strftime("%H:%M")
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        # Enregistrement vente
                        conn.execute("""INSERT INTO sales_history 
                            (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                            (ref_fac, client_name, total_panier_usd, recu_usd, reste_usd, d_now, t_now, 
                             st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        
                        # Déduction Stock
                        for art, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], art, sid))
                        
                        # Création dette si reste > 0
                        if reste_usd > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid) VALUES (?,?,?,?)", 
                                       (client_name, reste_usd, ref_fac, sid))
                        conn.commit()
                    
                    # Préparation vue facture
                    st.session_state.session['viewing_invoice'] = {
                        'ref': ref_fac, 'cli': client_name, 'total': final_total, 
                        'date': d_now, 'items': st.session_state.session['cart'], 'devise': devise
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()

# --- 8.3 STOCK (GESTION PRODUITS) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DES PRODUITS")
    
    with st.expander("🆕 AJOUTER UN PRODUIT"):
        with st.form("add_product"):
            p_name = st.text_input("Désignation de l'article").upper()
            p_cat = st.selectbox("Catégorie", ["BOISSON", "NOURRITURE", "DIVERS"])
            col1, col2 = st.columns(2)
            p_buy = col1.number_input("Prix d'Achat ($)", min_value=0.0)
            p_sell = col2.number_input("Prix de Vente ($)", min_value=0.0)
            p_qty = st.number_input("Quantité initiale", min_value=0)
            
            if st.form_submit_button("SAUVEGARDER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid, category) VALUES (?,?,?,?,?,?)",
                                (p_name, p_qty, p_buy, p_sell, sid, p_cat))
                    conn.commit()
                st.success("Produit ajouté au stock !"); st.rerun()

    st.divider()
    # Liste du stock avec modification/suppression
    with sqlite3.connect(DB_FILE) as conn:
        stock_data = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        for s_id, s_item, s_qty, s_buy, s_sell in stock_data:
            with st.expander(f"{s_item} | Qté: {s_qty} | Prix: {s_sell}$"):
                new_p = st.number_input(f"Modifier Prix ($)", value=s_sell, key=f"p_{s_id}")
                new_q = st.number_input(f"Modifier Qté", value=s_qty, key=f"q_{s_id}")
                col_m1, col_m2 = st.columns(2)
                if col_m1.button(f"Update {s_item}", key=f"up_{s_id}"):
                    conn.execute("UPDATE inventory SET sell_price=?, qty=? WHERE id=?", (new_p, new_q, s_id))
                    conn.commit(); st.rerun()
                if col_m2.button(f"Supprimer {s_item}", key=f"del_inv_{s_id}"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (s_id,))
                    conn.commit(); st.rerun()

# --- 8.4 DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉDITS CLIENTS")
    with sqlite3.connect(DB_FILE) as conn:
        debts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not debts:
            st.info("Aucune dette enregistrée.")
        
        for d_id, d_cli, d_bal, d_ref in debts:
            with st.expander(f"👤 {d_cli} | Reste: {d_bal:,.2f} $"):
                st.write(f"Référence Facture: {d_ref}")
                pay_tranche = st.number_input("Montant à payer ($)", min_value=0.0, max_value=d_bal, key=f"tranche_{d_id}")
                if st.button(f"ENREGISTRER PAIEMENT TRANCHE", key=f"btn_d_{d_id}"):
                    new_balance = d_bal - pay_tranche
                    if new_balance <= 0.01:
                        conn.execute("UPDATE client_debts SET balance=0, status='SOLDE' WHERE id=?", (d_id,))
                    else:
                        conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (new_balance, d_id))
                    conn.commit()
                    st.success("Paiement enregistré !"); st.rerun()

# --- 8.5 RAPPORTS & EXPORT ---
elif choice == "📊 RAPPORTS":
    st.header("📊 ANALYSE DE L'ACTIVITÉ")
    rep_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    
    with sqlite3.connect(DB_FILE) as conn:
        r_data = conn.execute("SELECT ref, cli, total_usd, paid_usd, seller, time FROM sales_history WHERE sid=? AND date=?", (sid, rep_date)).fetchall()
        if r_data:
            df = pd.DataFrame(r_data, columns=["REF", "CLIENT", "TOTAL ($)", "PAYÉ ($)", "VENDEUR", "HEURE"])
            st.table(df)
            st.markdown(f"<div class='cobalt-card'>TOTAL GÉNÉRÉ LE {rep_date} : {df['TOTAL ($)'].sum():,.2f} $</div>", unsafe_allow_html=True)
            if st.button("🖨️ IMPRIMER CE RAPPORT"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        else:
            st.warning(f"Aucune vente enregistrée pour le {rep_date}.")

# --- 8.6 ÉQUIPE (MODIFICATION PWD) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES UTILISATEURS")
    
    # Modifier mon propre mot de passe
    with st.expander("🔐 CHANGER MON MOT DE PASSE"):
        with st.form("my_pwd"):
            nv_p = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("METTRE À JOUR"):
                h_p = hashlib.sha256(nv_p.encode()).hexdigest()
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE users SET pwd=? WHERE uid=?", (h_p, st.session_state.session['user']))
                    conn.commit()
                st.success("Mot de passe modifié !")

    st.divider()
    # Ajouter un vendeur
    if st.session_state.session['role'] == "GERANT":
        with st.form("add_vendeur"):
            v_u = st.text_input("ID Vendeur").lower()
            v_n = st.text_input("Nom Complet")
            v_p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                h_v = hashlib.sha256(v_p.encode()).hexdigest()
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                               (v_u, h_v, 'VENDEUR', sid, 'ACTIF', v_n, ''))
                    conn.commit()
                st.success("Vendeur créé !"); st.rerun()

# --- 8.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES DE LA BOUTIQUE")
    with st.form("shop_edit"):
        c1, c2 = st.columns(2)
        s_name = c1.text_input("Nom de l'Enseigne", shop_info[0])
        s_rate = c2.number_input("Taux de change (1$ = ? CDF)", value=shop_info[1])
        s_tel = c1.text_input("N° de Téléphone", shop_info[4])
        s_mail = c2.text_input("Email", shop_info[7])
        s_rccm = c1.text_input("N° RCCM", shop_info[5])
        s_idnat = c2.text_input("ID National", shop_info[6])
        s_addr = st.text_area("Adresse Physique", shop_info[3])
        s_head = st.text_input("Message de pied de facture", shop_info[2])
        
        if st.form_submit_button("💾 ENREGISTRER TOUT"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=?, rccm=?, idnat=?, email=? 
                             WHERE sid=?""", (s_name, s_rate, s_head, s_addr, s_tel, s_rccm, s_idnat, s_mail, sid))
                conn.commit()
            st.success("Informations boutique mises à jour !"); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False
    st.rerun()

# ==============================================================================
# FIN DU CODE v200 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
