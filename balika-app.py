# ==============================================================================
# ANASH ERP v3317 - SYSTÈME DE GESTION INTÉGRAL (ÉDITION BALIKA BUSINESS)
# ------------------------------------------------------------------------------
# FUSION TOTALE : AUCUNE LIGNE SUPPRIMÉE | OPTIMISATION SMARTPHONE HD
# VOLUME : > 750 LIGNES | THÈME : COBALT & NÉON | MULTI-DEVISES & DETTES
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import io
import base64

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES ET STRUCTURE
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3317_core.db"

def init_system_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table de Configuration Globale (Master Admin)
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee_msg TEXT,
            marquee_active INTEGER DEFAULT 1,
            selected_theme TEXT DEFAULT 'COBALT_NIGHT',
            version TEXT, 
            last_backup TEXT)""")
        
        # Table des Utilisateurs (Admin, Boss, Vendeurs)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT,
            created_at TEXT)""")
        
        # Table des Boutiques (Profils Business)
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
        
        # Table de Stock (Inventaire avec prix d'achat/vente)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, 
            qty INTEGER, 
            buy_price REAL, 
            sell_price REAL, 
            sid TEXT, 
            category TEXT,
            min_stock INTEGER DEFAULT 5,
            is_active INTEGER DEFAULT 1)""")
        
        # Table des Ventes (Historique complet)
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
        
        # Table des Dettes (Paiement échelonné)
        cursor.execute("""CREATE TABLE IF NOT EXISTS client_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cli TEXT, 
            balance REAL, 
            sale_ref TEXT, 
            sid TEXT, 
            status TEXT DEFAULT 'OUVERT',
            last_pay_date TEXT)""")

        # Insertion des données par défaut si nécessaire
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE CHEZ BALIKA BUSINESS - GESTION PROFESSIONNELLE', 1, 'COBALT_NIGHT', '3.3.17', ?)", (datetime.now().strftime("%d/%m/%Y"),))
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR CENTRAL', '000', datetime.now().strftime("%d/%m/%Y")))
        
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. DESIGN CSS & THÉMATISATION (COBALT & NÉON)
# ------------------------------------------------------------------------------
def apply_ui_styles():
    # Récupération de la config UI
    with sqlite3.connect(DB_FILE) as conn:
        cfg = conn.execute("SELECT app_name, marquee_active, selected_theme FROM global_settings WHERE id=1").fetchone()
    
    st.set_page_config(page_title=cfg[0], layout="wide", initial_sidebar_state="expanded")

    st.markdown("""
    <style>
        /* Fond global sombre Balika */
        .stApp {
            background: linear-gradient(145deg, #001220 0%, #000a1a 100%);
            color: #FFFFFF !important;
        }

        /* Marquee Professionnel */
        .marquee-container {
            background: #00d9ff; color: #000; padding: 10px 0;
            font-weight: 800; font-family: 'Segoe UI', sans-serif;
            position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
            box-shadow: 0 4px 10px rgba(0, 217, 255, 0.4);
        }

        /* Cartes Style Cobalt */
        .cobalt-card {
            background: #003366; color: white !important;
            padding: 22px; border-radius: 18px; border-left: 10px solid #00d9ff;
            margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            transition: 0.3s;
        }
        .cobalt-card:hover { transform: translateY(-5px); }
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3 { color: #00d9ff !important; margin: 0; }

        /* Cadre Néon pour les Totaux */
        .neon-frame {
            border: 5px solid #00ff00; padding: 30px; border-radius: 25px;
            text-align: center; background: rgba(0,0,0,0.85);
            box-shadow: 0 0 25px #00ff00; margin: 20px 0;
        }
        .neon-text {
            color: #00ff00; font-family: 'Courier New', sans-serif;
            font-size: 50px; font-weight: 900; text-shadow: 0 0 15px #00ff00;
        }

        /* Horloge XXL 80mm style */
        .clock-container {
            text-align:center; padding: 40px; background: rgba(255,255,255,0.05); 
            border-radius: 30px; border: 1px solid rgba(0, 217, 255, 0.3); 
            margin: 20px 0;
        }
        .clock-time { font-size: 90px; font-weight: 900; color: #ffffff; line-height: 1; text-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
        .clock-date { font-size: 24px; color: #00d9ff; font-weight: bold; letter-spacing: 2px; }

        /* Boutons Mobiles Haute Visibilité */
        .stButton > button {
            width: 100%; height: 70px; border-radius: 15px;
            background: linear-gradient(to right, #00d9ff, #0055ff);
            color: white !important; font-size: 20px; font-weight: bold;
            border: none; box-shadow: 0 4px 15px rgba(0, 217, 255, 0.3);
            text-transform: uppercase;
        }
        .stButton > button:active { transform: scale(0.95); }

        /* Sidebar White & Blue Text */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 6px solid #00d9ff;
        }
        [data-testid="stSidebar"] * { color: #003366 !important; font-weight: 800; font-size: 16px; }

        /* Champs de saisie */
        input { 
            background: #ffffff !important; color: #000 !important; 
            font-size: 20px !important; border-radius: 10px !important; 
            border: 2px solid #00d9ff !important;
        }

        /* Facture Impression */
        @media print {
            .no-print { display: none !important; }
            .stApp { background: white !important; color: black !important; }
            .print-area { 
                display: block !important; width: 80mm; 
                font-family: 'Courier New', Courier, monospace; 
                font-size: 12px; color: black !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

apply_ui_styles()

# ------------------------------------------------------------------------------
# 3. ÉTATS DE SESSION & SÉCURITÉ
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None,
        'real_name': ""
    }

def get_global_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg, marquee_active FROM global_settings WHERE id=1").fetchone()

APP_NAME, MARQUEE_MSG, M_ACTIVE = get_global_config()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(uid, pwd):
    with sqlite3.connect(DB_FILE) as conn:
        user = conn.execute("SELECT pwd, role, shop, status, name FROM users WHERE uid=?", (uid.lower().strip(),)).fetchone()
        if user and user[0] == hash_password(pwd):
            return user
        return None

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS (LOGIN & INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if M_ACTIVE == 1:
        st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        st.markdown(f"<h1 style='text-align:center; font-size:45px;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔒 CONNEXION", "🚀 CRÉER COMPTE BOSS"])
        
        with tab_log:
            with st.form("login_form"):
                u_id = st.text_input("Identifiant").lower().strip()
                u_pw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("S'IDENTIFIER MAINTENANT"):
                    user_info = verify_user(u_id, u_pw)
                    if user_info:
                        if user_info[3] == "ACTIF":
                            st.session_state.session.update({
                                'logged_in': True, 'user': u_id, 'role': user_info[1], 
                                'shop_id': user_info[2], 'real_name': user_info[4]
                            })
                            st.rerun()
                        elif user_info[3] == "PAUSE":
                            st.error("Compte suspendu (PAUSE).")
                        else:
                            st.warning("Compte en attente d'activation.")
                    else:
                        st.error("Identifiants incorrects.")
        
        with tab_reg:
            st.info("Créez votre espace de vente en 1 minute.")
            with st.form("signup_boss"):
                b_id = st.text_input("ID Utilisateur souhaité").lower().strip()
                b_name = st.text_input("Nom de la Boutique / Business")
                b_pw = st.text_input("Mot de passe", type="password")
                b_tel = st.text_input("Téléphone")
                if st.form_submit_button("ENVOYER MA DEMANDE"):
                    if b_id and b_pw and b_name:
                        with sqlite3.connect(DB_FILE) as conn:
                            try:
                                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                           (b_id, hash_password(b_pw), 'GERANT', 'PENDING', 'EN_ATTENTE', b_name, b_tel, datetime.now().strftime("%d/%m/%Y")))
                                conn.commit()
                                st.success("Demande enregistrée ! Attendez l'activation Admin.")
                            except: st.error("Cet ID est déjà pris.")
                    else: st.warning("Remplissez tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN (GESTION SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER ADMIN")
    adm_nav = st.sidebar.radio("Navigation", ["Validations Boss", "Audit Boutiques", "Réglages Système", "Déconnexion"])
    
    if adm_nav == "Validations Boss":
        st.header("✅ Approbation des Nouveaux Business")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, tel FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending: st.info("Aucune demande.")
            for p_uid, p_name, p_tel in pending:
                with st.expander(f"Demande de : {p_name}"):
                    st.write(f"ID: {p_uid} | Tel: {p_tel}")
                    if st.button(f"ACTIVER {p_uid}"):
                        conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (p_uid, p_uid))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_uid, p_name, p_uid))
                        conn.commit(); st.rerun()

    elif adm_nav == "Audit Boutiques":
        st.header("🏢 Surveillance Réseau")
        with sqlite3.connect(DB_FILE) as conn:
            shops = conn.execute("SELECT uid, name, status FROM users WHERE role='GERANT'").fetchall()
            for s_uid, s_name, s_stat in shops:
                st.markdown(f"<div class='cobalt-card'><b>{s_name}</b> (@{s_uid}) - Statut: {s_stat}</div>", unsafe_allow_html=True)

    elif adm_nav == "Réglages Système":
        st.header("⚙️ Configuration Globale")
        with st.form("global_cfg"):
            new_title = st.text_input("Nom Global", APP_NAME)
            new_msg = st.text_area("Message Marquee", MARQUEE_MSG)
            new_active = st.checkbox("Activer Marquee", value=(M_ACTIVE==1))
            if st.form_submit_button("DÉPLOYER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=?, marquee_active=? WHERE id=1", 
                               (new_title, new_msg, 1 if new_active else 0))
                    conn.commit(); st.rerun()

    if adm_nav == "Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE BOUTIQUE (POUR BOSS & VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (sid,)).fetchone()
    if not shop_data:
        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (sid, "Ma Boutique", st.session_state.session['user']))
        conn.commit(); st.rerun()

# Menu Navigation
if st.session_state.session['role'] == "GERANT":
    nav_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    nav_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {shop_data[0]}<br>👤 {st.session_state.session['real_name']}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PRINCIPAL", nav_options)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    if M_ACTIVE == 1:
        st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class='clock-container'>
            <div class='clock-time'>{datetime.now().strftime('%H:%M')}</div>
            <div class='clock-date'>{datetime.now().strftime('%d %B %Y')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Statistiques du jour
    today = datetime.now().strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        s_day = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        d_day = conn.execute("SELECT SUM(balance) FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
        
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='cobalt-card'><h3>VENTES JOUR</h3><h1>{s_day:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='cobalt-card' style='border-left-color:#ff9900;'><h3>DETTES ACTIVES</h3><h1>{d_day:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE (MULTI-DEVISES & INVOICE) ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
        <div class='print-area' style='background:white; color:black; padding:15px;'>
            <center>
                <h3>{shop_data[0]}</h3>
                <p>{shop_data[3]}<br>Tél: {shop_data[4]}</p>
                <hr>
                <b>FACTURE N° {inv['ref']}</b><br>
                Date: {inv['date']} | Heure: {datetime.now().strftime('%H:%M')}
                <hr>
            </center>
            <table width='100%'>
                <tr><td><b>Client:</b></td><td align='right'>{inv['cli']}</td></tr>
            </table>
            <hr>
            <table width='100%'>
                <tr><th>Art.</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td align='right'>{(v['q']*v['p']):.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <h3 align='right'>NET À PAYER: {inv['total']} {inv['devise']}</h3>
            <center><p>{shop_data[2]}</p></center>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        share_msg = f"Facture {shop_data[0]} - Total: {inv['total']} {inv['devise']}"
        c3.markdown(f"[📲 WHATSAPP](https://wa.me/?text={share_msg})")

    else:
        st.header("🛒 Terminal de Vente")
        taux = shop_data[1]
        devise = st.radio("DEVISE DU PAIEMENT", ["USD", "CDF"], horizontal=True)
        st.info(f"Taux: 1 USD = {taux} CDF")
        
        with sqlite3.connect(DB_FILE) as conn:
            items = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0 AND is_active=1", (sid,)).fetchall()
            options = ["--- Choisir un article ---"] + [f"{i[0]} (Dispo: {i[2]})" for i in items]
            pick = st.selectbox("Rechercher un article", options)
            
            if pick != "--- Choisir un article ---":
                it_name = pick.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                    st.session_state.session['cart'][it_name] = {'p': info[0], 'q': 1, 'max': info[1]}
                    st.rerun()

        if st.session_state.session['cart']:
            st.divider()
            t_usd = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c_n, c_q, c_r = st.columns([3, 2, 1])
                new_q = c_q.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"q_{art}")
                st.session_state.session['cart'][art]['q'] = new_q
                t_usd += d['p'] * new_q
                c_n.markdown(f"**{art}**<br>{d['p']:.2f} $")
                if c_r.button("🗑️", key=f"rm_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            f_total = t_usd if devise == "USD" else t_usd * taux
            st.markdown(f"<div class='neon-frame'><div class='neon-text'>{f_total:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("valider_vente"):
                nom_cli = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                recu = st.number_input(f"MONTANT REÇU ({devise})", value=float(f_total))
                if st.form_submit_button("✅ CONFIRMER & ENREGISTRER"):
                    recu_usd = recu if devise == "USD" else recu / taux
                    reste = t_usd - recu_usd
                    v_ref = f"FAC-{random.randint(10000, 99999)}"
                    d_now = datetime.now().strftime("%d/%m/%Y")
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used, rate_at_sale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (v_ref, nom_cli, t_usd, recu_usd, reste, d_now, datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise, taux))
                        if reste > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid, last_pay_date) VALUES (?,?,?,?,?)", (nom_cli, reste, v_ref, sid, d_now))
                        for it, dt in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], it, sid))
                        conn.commit()
                    
                    st.session_state.session['viewing_invoice'] = {
                        'ref': v_ref, 'cli': nom_cli, 'total': f_total, 'devise': devise, 'items': st.session_state.session['cart'], 'date': d_now
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()

# --- 6.3 GESTION STOCK (BOSS ONLY) ---
elif choice == "📦 STOCK":
    st.header("📦 Inventaire & Prix")
    tab_list, tab_add = st.tabs(["📋 LISTE STOCK", "➕ NOUVEL ARTICLE"])
    
    with tab_add:
        with st.form("add_item"):
            a_n = st.text_input("Désignation").upper()
            a_c = st.selectbox("Catégorie", ["DIVERS", "ALIMENTATION", "HABILLEMENT", "ÉLECTRONIQUE"])
            a_q = st.number_input("Quantité initiale", 0)
            a_bp = st.number_input("Prix d'Achat ($)", 0.0)
            a_sp = st.number_input("Prix de Vente ($)", 0.0)
            if st.form_submit_button("AJOUTER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid, category) VALUES (?,?,?,?,?,?)",
                               (a_n, a_q, a_bp, a_sp, sid, a_c))
                    conn.commit(); st.success("Article ajouté !"); st.rerun()

    with tab_list:
        with sqlite3.connect(DB_FILE) as conn:
            items = conn.execute("SELECT id, item, qty, buy_price, sell_price, min_stock FROM inventory WHERE sid=? AND is_active=1", (sid,)).fetchall()
            for i_id, i_item, i_qty, i_buy, i_sell, i_min in items:
                with st.expander(f"{i_item} | Qte: {i_qty} | Prix: {i_sell}$"):
                    with st.form(f"mod_{i_id}"):
                        new_q = st.number_input("Quantité", value=i_qty)
                        new_s = st.number_input("Prix Vente", value=i_sell)
                        if st.form_submit_button("MODIFIER"):
                            conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_s, i_id))
                            conn.commit(); st.rerun()
                    if st.button(f"🗑️ SUPPRIMER {i_item}", key=f"del_{i_id}"):
                        conn.execute("UPDATE inventory SET is_active=0 WHERE id=?", (i_id,))
                        conn.commit(); st.rerun()

# --- 6.4 DETTES ÉCHELONNÉES ---
elif choice == "📉 DETTES":
    st.header("📉 Suivi des Dettes")
    with sqlite3.connect(DB_FILE) as conn:
        debts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not debts: st.info("Aucune dette en cours.")
        for d_id, d_cli, d_bal, d_ref in debts:
            with st.expander(f"👤 {d_cli} | Reste: {d_bal:,.2f} $"):
                st.write(f"Référence Vente: {d_ref}")
                pay = st.number_input("Montant à payer ($)", 0.0, float(d_bal), key=f"pay_{d_id}")
                if st.button("ENREGISTRER LE PAIEMENT", key=f"btn_{d_id}"):
                    new_bal = d_bal - pay
                    if new_bal <= 0.01:
                        conn.execute("UPDATE client_debts SET balance=0, status='SOLDE' WHERE id=?", (d_id,))
                    else:
                        conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (new_bal, d_id))
                    conn.commit(); st.success("Paiement validé !"); st.rerun()

# --- 6.5 RAPPORTS & BÉNÉFICES ---
elif choice == "📊 RAPPORTS":
    st.header("📊 Analyse Financière")
    target_d = st.date_input("Date du rapport", datetime.now()).strftime("%d/%m/%Y")
    
    with sqlite3.connect(DB_FILE) as conn:
        sales = conn.execute("SELECT items_json, total_usd, paid_usd FROM sales_history WHERE sid=? AND date=?", (sid, target_d)).fetchall()
        
        t_vendu = sum([s[1] for s in sales])
        t_recu = sum([s[2] for s in sales])
        
        # Calcul du bénéfice (P.Vente - P.Achat)
        benefice = 0
        for s_json, t_usd, p_usd in sales:
            items = json.loads(s_json)
            for it_name, data in items.items():
                # On récupère le prix d'achat historique ou actuel
                buy_p = conn.execute("SELECT buy_price FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                if buy_p:
                    benefice += (data['p'] - buy_p[0]) * data['q']

        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cobalt-card'><h3>VOLUME</h3><h2>{t_vendu:,.2f} $</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cobalt-card'><h3>ENCAISSÉ</h3><h2>{t_recu:,.2f} $</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='cobalt-card' style='border-left-color:#00ff00;'><h3>BÉNÉFICE</h3><h2>{benefice:,.2f} $</h2></div>", unsafe_allow_html=True)

# --- 6.6 ÉQUIPE (BOSS ONLY) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 Mes Vendeurs")
    with st.form("add_vendeur"):
        v_id = st.text_input("ID Vendeur").lower().strip()
        v_nm = st.text_input("Nom du Vendeur")
        v_pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                               (v_id, hash_password(v_pw), 'VENDEUR', sid, 'ACTIF', v_nm, '', datetime.now().strftime("%d/%m/%Y")))
                    conn.commit(); st.success("Vendeur ajouté !")
                except: st.error("ID déjà utilisé.")

# --- 6.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ Configuration Boutique")
    with st.form("shop_cfg"):
        s_name = st.text_input("Nom de la Boutique", shop_data[0])
        s_rate = st.number_input("Taux de change (CDF)", value=shop_data[1])
        s_head = st.text_area("Message bas de facture", shop_data[2])
        if st.form_submit_button("SAUVEGARDER LES RÉGLAGES"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, head=? WHERE sid=?", (s_name, s_rate, s_head, sid))
                conn.commit(); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()

# ------------------------------------------------------------------------------
# 7. PIED DE PAGE & CRÉDITS
# ------------------------------------------------------------------------------
st.markdown("<br><hr><center><small>ANASH ERP v3.3.17 | © 2026 BALIKA BUSINESS SOLUTIONS</small></center>", unsafe_allow_html=True)
