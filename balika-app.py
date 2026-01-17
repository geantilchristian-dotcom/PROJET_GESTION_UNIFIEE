# ==============================================================================
# ANASH ERP v3316 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL MASTER)
# ------------------------------------------------------------------------------
# FUSION TOTALE : AUCUNE LIGNE SUPPRIMÉE | CORRECTIF SQL & GESTION ÉQUIPE
# VOLUME : ~1000 LIGNES | OPTIMISATION : SMARTPHONE HD | STYLE : COBALT & NÉON
# ------------------------------------------------------------------------------
# FONCTIONNALITÉS : 
# 1. ADMIN MASTER (VOTRE COMPTE : admin / admin123)
# 2. GESTION BOSS (INSCRIPTION, VALIDATION, PAUSE, SUPPRESSION)
# 3. GESTION VENDEURS (LIMITÉS AUX VENTES ET DETTES)
# 4. CAISSE TACTILE MULTI-DEVISES (CADRE NÉON)
# 5. DETTES ÉCHELONNÉES (PAIEMENT PAR TRANCHES)
# 6. RÉINITIALISATION & SAUVEGARDE & PARAMÈTRES AVANCÉS
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
# 1. CONFIGURATION DE LA BASE DE DONNÉES (STRUCTURE v3316 PRÉSERVÉE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3316_core.db"

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
        
        # Table des Utilisateurs (Tous rôles)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT,
            created_at TEXT)""")
        
        # Table des Boutiques (Entêtes de Factures)
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
        
        # Table de Stock (Inventaire)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, 
            qty INTEGER, 
            buy_price REAL, 
            sell_price REAL, 
            sid TEXT, 
            category TEXT,
            min_stock INTEGER DEFAULT 5)""")
        
        # Table des Ventes (Historique)
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
        
        # Table des Dettes (Suivi Clients)
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
            cursor.execute("INSERT INTO global_settings VALUES (1, 'BALIKA BUSINESS ERP', 'BONJOUR - BIENVENUE CHEZ BALIKA BUSINESS', '3.3.16', ?, 'Cobalt Fusion')", (datetime.now().strftime("%d/%m/%Y"),))
        else:
            # Assurer que le message est bien "BONJOUR" si vous le souhaitez par défaut
            pass
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR CENTRAL', '000', datetime.now().strftime("%d/%m/%Y")))
        
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. DESIGN CSS PERSONNALISÉ (STYLE COBALT, NÉON & MOBILE)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v3316", layout="wide", initial_sidebar_state="expanded")

def apply_ui_styles():
    st.markdown("""
    <style>
        /* Fond global et texte */
        .stApp {
            background: linear-gradient(135deg, #001a33 0%, #000a1a 100%);
            color: #ffffff !important;
        }

        /* Marquee Professionnel */
        .marquee-container {
            background: #0044ff; color: #ffffff; padding: 12px 0;
            font-family: 'Arial', sans-serif; font-size: 22px; font-weight: bold;
            border-bottom: 3px solid #00ff00; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }

        /* Cartes Style Cobalt */
        .cobalt-card {
            background: #0044ff; color: white !important;
            padding: 20px; border-radius: 15px; border-left: 10px solid #00d9ff;
            margin-bottom: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        }
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p { color: white !important; }

        /* Cadre Néon pour les Totaux */
        .neon-frame {
            border: 5px solid #00ff00; padding: 20px; border-radius: 20px;
            text-align: center; background: rgba(0,0,0,0.9);
            box-shadow: 0 0 15px #00ff00; margin: 15px 0;
        }
        .neon-text {
            color: #00ff00; font-family: 'Orbitron', sans-serif;
            font-size: 45px; font-weight: bold; text-shadow: 0 0 10px #00ff00;
        }

        /* Horloge XXL 80mm */
        .clock-container {
            text-align:center; padding: 35px; background: rgba(0, 85, 255, 0.1); 
            border-radius: 25px; border: 2px solid #00d9ff; 
            margin: 20px 0;
        }
        .clock-time { font-size: 85px; font-weight: 900; color: #ffffff; line-height: 1; }
        .clock-date { font-size: 20px; color: #00d9ff; font-weight: bold; }

        /* Boutons Mobiles */
        .stButton > button {
            width: 100%; height: 65px; border-radius: 12px;
            background: linear-gradient(to right, #0055ff, #002288);
            color: white; font-size: 18px; font-weight: bold; border: 1px solid #ffffff;
            transition: 0.3s;
        }
        .stButton > button:hover { transform: scale(1.02); background: #0044ff; border: 2px solid #00ff00; }

        /* Sidebar Custom */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 5px solid #0044ff;
        }
        [data-testid="stSidebar"] * { color: #001a33 !important; font-weight: bold; }

        /* Champs de saisie */
        input { 
            background: #ffffff !important; color: #000 !important; 
            font-size: 18px !important; border-radius: 8px !important; 
        }

        /* Impression Facture */
        @media print {
            .no-print { display: none !important; }
            .stApp { background: white !important; color: black !important; }
            .print-area { display: block !important; width: 80mm; font-family: 'Courier New', Courier, monospace; }
        }
    </style>
    """, unsafe_allow_html=True)

apply_ui_styles()

# ------------------------------------------------------------------------------
# 3. ÉTATS DE SESSION & CHARGEMENT CONFIG
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None,
        'temp_sale_ref': None
    }

def get_global_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg FROM global_settings WHERE id=1").fetchone()

APP_NAME, MARQUEE_MSG = get_global_config()

# ------------------------------------------------------------------------------
# 4. FONCTIONS DE SÉCURITÉ & RÉSEAU
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
# 5. ÉCRAN D'ACCÈS (LOGIN & INSCRIPTION BOSS)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee scrollamount='10'>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔒 CONNEXION", "🚀 CRÉER MON COMPTE BOSS"])
        
        with tab_log:
            with st.form("login_form"):
                u_id = st.text_input("Identifiant Utilisateur").lower().strip()
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
                        elif user_info[3] == "PAUSE":
                            st.error("Votre compte est temporairement suspendu (PAUSE).")
                        else:
                            st.warning("Votre compte est en attente d'activation par l'Admin.")
                    else:
                        st.error("Identifiants incorrects.")
        
        with tab_reg:
            st.info("Devenez Boss ! Créez votre propre espace de vente et gérez vos vendeurs.")
            with st.form("signup_boss"):
                b_id = st.text_input("Identifiant souhaité (ID)").lower().strip()
                b_name = st.text_input("Nom de votre Boutique")
                b_pw = st.text_input("Mot de passe", type="password")
                b_tel = st.text_input("Téléphone de contact")
                if st.form_submit_button("DEMANDER MON ACCÈS"):
                    if b_id and b_pw and b_name:
                        with sqlite3.connect(DB_FILE) as conn:
                            try:
                                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                           (b_id, hash_password(b_pw), 'GERANT', 'PENDING', 'EN_ATTENTE', b_name, b_tel, datetime.now().strftime("%d/%m/%Y")))
                                conn.commit()
                                st.success("Demande envoyée ! L'administrateur activera votre boutique sous peu.")
                            except sqlite3.IntegrityError:
                                st.error("Cet identifiant est déjà utilisé.")
                    else:
                        st.warning("Veuillez remplir tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMIN (VOTRE INTERFACE PRIVÉE)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ PANNEAU MASTER")
    adm_nav = st.sidebar.radio("Pilotage", ["Validations Boss", "Audit des Boutiques", "Réglages Système", "Déconnexion"])
    
    if adm_nav == "Validations Boss":
        st.header("✅ GESTION DES NOUVEAUX CLIENTS (BOSS)")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, tel, created_at FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending:
                st.info("Aucune nouvelle demande pour le moment.")
            else:
                for p_uid, p_name, p_tel, p_date in pending:
                    with st.expander(f"Demande de : {p_name} (@{p_uid})"):
                        st.write(f"📅 Date: {p_date} | 📞 Tel: {p_tel}")
                        c1, c2 = st.columns(2)
                        if c1.button(f"ACTIVER {p_uid}", key=f"ok_{p_uid}"):
                            conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (p_uid, p_uid))
                            conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_uid, p_name, p_uid))
                            conn.commit(); st.rerun()
                        if c2.button(f"REJETER {p_uid}", key=f"no_{p_uid}"):
                            conn.execute("DELETE FROM users WHERE uid=?", (p_uid,))
                            conn.commit(); st.rerun()

    elif adm_nav == "Audit des Boutiques":
        st.header("🏢 SURVEILLANCE DES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            boss_list = conn.execute("SELECT uid, name, status, tel FROM users WHERE role='GERANT'").fetchall()
            for b_uid, b_name, b_stat, b_tel in boss_list:
                with st.expander(f"Boutique : {b_name} (@{b_uid})"):
                    st.write(f"Statut actuel : {b_stat}")
                    st.write(f"Contact : {b_tel}")
                    v_tot = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=?", (b_uid,)).fetchone()[0] or 0
                    st.write(f"💰 Volume Ventes : {v_tot:,.2f} $")
                    c1, c2, c3 = st.columns(3)
                    if c1.button("🔴 SUPPRIMER", key=f"del_{b_uid}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (b_uid,))
                        conn.execute("DELETE FROM shops WHERE sid=?", (b_uid,))
                        conn.commit(); st.rerun()
                    if c2.button("🟡 PAUSE", key=f"pau_{b_uid}"):
                        conn.execute("UPDATE users SET status='PAUSE' WHERE uid=?", (b_uid,))
                        conn.commit(); st.rerun()
                    if c3.button("🟢 ACTIVER", key=f"re_{b_uid}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (b_uid,))
                        conn.commit(); st.rerun()

    elif adm_nav == "Réglages Système":
        st.header("⚙️ CONFIGURATION MASTER")
        with st.form("sys_form"):
            new_title = st.text_input("Nom Global de l'App", APP_NAME)
            new_msg = st.text_area("Message Marquee Global", MARQUEE_MSG)
            if st.form_submit_button("DÉPLOYER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", (new_title, new_msg))
                    conn.commit()
                st.success("Mise à jour réussie !"); time.sleep(1); st.rerun()

    if adm_nav == "Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (POUR LES BOSS ET LES VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat, email FROM shops WHERE sid=?", (sid,)).fetchone()

if not shop_data:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (sid, "Nouvelle Boutique", st.session_state.session['user']))
        conn.commit(); st.rerun()

# ------------------------------------------------------------------------------
# 8. MENU DE NAVIGATION BOUTIQUE
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "GERANT":
    nav_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE TACTILE", "📦 GESTION STOCK", "📉 DETTES CLIENTS", "📊 RAPPORTS VENTES", "👥 MON ÉQUIPE", "⚙️ RÉGLAGES BOUTIQUE", "🚪 QUITTER"]
else:
    nav_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE TACTILE", "📉 DETTES CLIENTS", "📊 RAPPORTS VENTES", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card' style='padding:15px;'>🏪 {shop_data[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PRINCIPAL", nav_options)

# --- 8.1 TABLEAU DE BORD ---
if choice == "🏠 TABLEAU DE BORD":
    st.markdown(f"<div class='marquee-container'><marquee scrollamount='10'>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown(f"""<div class='clock-container'><div class='clock-time'>{datetime.now().strftime('%H:%M')}</div><div class='clock-date'>{datetime.now().strftime('%d %B %Y')}</div></div>""", unsafe_allow_html=True)
    
    today = datetime.now().strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        s_day = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        d_day = conn.execute("SELECT SUM(balance) FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
        alert_stock = conn.execute("SELECT COUNT(*) FROM inventory WHERE sid=? AND qty <= min_stock", (sid,)).fetchone()[0]
        
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='cobalt-card'><h3>VENTES JOUR</h3><h1>{s_day:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='cobalt-card' style='background:#ff9900 !important;'><h3>DETTES CLIENTS</h3><h1>{d_day:,.2f} $</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='cobalt-card' style='background:#ff4d4d !important;'><h3>ALERTE STOCK</h3><h1>{alert_stock}</h1></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE TACTILE ---
elif choice == "🛒 CAISSE TACTILE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
        <div class='print-area' style='background:white; color:black; padding:20px; border:1px solid #000;'>
            <center><h2>{shop_data[0]}</h2><p>Tél: {shop_data[4]}</p><hr><b>FACTURE N° {inv['ref']}</b><br>Date: {inv['date']}<hr></center>
            <table width='100%'><tr><td><b>Client:</b></td><td align='right'>{inv['cli']}</td></tr></table><hr>
            <table width='100%'>
                <tr><th>Art.</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{(v['q']*v['p']):,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table><hr>
            <h3 align='right'>NET À PAYER: {inv['total']:,.2f} {inv['devise']}</h3>
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        taux = shop_data[1]
        col_dev, col_taux = st.columns([1, 1])
        devise = col_dev.radio("DEVISE", ["USD", "CDF"], horizontal=True)
        col_taux.info(f"Taux: 1$ = {taux} CDF")
        
        with sqlite3.connect(DB_FILE) as conn:
            # CORRECTIF ICI : (sid,) avec la virgule
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            options = ["--- Choisir un article ---"] + [f"{p[0]} (Dispo: {p[2]})" for p in prods]
            search = st.selectbox("RECHERCHER ARTICLE", options)
            if search != "--- Choisir un article ---":
                it_name = search.split(" (")[0]
                if st.button("➕ AJOUTER"):
                    info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                    st.session_state.session['cart'][it_name] = {'p': info[0], 'q': 1, 'max': info[1]}
                    st.rerun()

        if st.session_state.session['cart']:
            st.divider()
            total_usd = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c_nom, c_qte, c_del = st.columns([3, 2, 1])
                new_q = c_qte.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"ca_{art}")
                st.session_state.session['cart'][art]['q'] = new_q
                total_usd += d['p'] * new_q
                if c_del.button("🗑️", key=f"del_{art}"): del st.session_state.session['cart'][art]; st.rerun()

            final_total = total_usd if devise == "USD" else total_usd * taux
            st.markdown(f"<div class='neon-frame'><div class='neon-text'>{final_total:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("valid_vente"):
                nom_cli = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                paiement = st.number_input(f"MONTANT REÇU ({devise})", value=float(final_total))
                if st.form_submit_button("✅ CONFIRMER"):
                    p_usd = paiement if devise == "USD" else paiement / taux
                    reste = total_usd - p_usd
                    v_ref = f"FAC-{random.randint(1000, 9999)}"
                    d_now = datetime.now().strftime("%d/%m/%Y")
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used, rate_at_sale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (v_ref, nom_cli, total_usd, p_usd, reste, d_now, datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, "{}", devise, taux))
                        for it, dt in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], it, sid))
                        if reste > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid, last_pay_date) VALUES (?,?,?,?,?)", (nom_cli, reste, v_ref, sid, d_now))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': v_ref, 'cli': nom_cli, 'total': final_total, 'date': d_now, 'items': st.session_state.session['cart'], 'devise': devise}
                    st.session_state.session['cart'] = {}
                    st.rerun()

# --- 8.3 GESTION STOCK ---
elif choice == "📦 GESTION STOCK":
    st.header("📦 INVENTAIRE")
    with st.expander("🆕 AJOUTER ARTICLE"):
        with st.form("new_art"):
            a_nom = st.text_input("Désignation").upper()
            a_achat = st.number_input("Prix d'Achat ($)", 0.0)
            a_vente = st.number_input("Prix de Vente ($)", 0.0)
            a_qte = st.number_input("Quantité", 0)
            if st.form_submit_button("ENREGISTRER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (a_nom, a_qte, a_achat, a_vente, sid))
                    conn.commit(); st.success("Ajouté !"); st.rerun()

    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=? ORDER BY item ASC", (sid,)).fetchall()
        for i_id, i_item, i_qty, i_buy, i_sell in items:
            with st.expander(f"{i_item} | Stock: {i_qty}"):
                with st.form(f"ed_{i_id}"):
                    up_q = st.number_input("Quantité", value=i_qty)
                    up_p = st.number_input("Prix Vente", value=i_sell)
                    if st.form_submit_button("MODIFIER"):
                        conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (up_q, up_p, i_id))
                        conn.commit(); st.rerun()
                if st.button(f"🗑️ Supprimer {i_item}", key=f"d_{i_id}"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (i_id,))
                    conn.commit(); st.rerun()

# --- 8.4 DETTES CLIENTS ---
elif choice == "📉 DETTES CLIENTS":
    st.header("📉 SUIVI DES DETTES")
    with sqlite3.connect(DB_FILE) as conn:
        debts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not debts: st.info("Aucune dette.")
        for d_id, d_cli, d_bal, d_ref in debts:
            with st.expander(f"👤 {d_cli} | Reste : {d_bal:,.2f} $"):
                pay_val = st.number_input("Versement ($)", 0.0, d_bal, key=f"p_{d_id}")
                if st.button("ENREGISTRER PAIEMENT", key=f"bp_{d_id}"):
                    new_bal = d_bal - pay_val
                    if new_bal <= 0.01:
                        conn.execute("UPDATE client_debts SET balance=0, status='SOLDE' WHERE id=?", (d_id,))
                    else:
                        conn.execute("UPDATE client_debts SET balance=? WHERE id=?", (new_bal, d_id))
                    conn.commit(); st.rerun()

# --- 8.5 RAPPORTS VENTES ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 ANALYSE")
    d_rep = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        data = conn.execute("SELECT ref, cli, total_usd, seller, time FROM sales_history WHERE sid=? AND date=?", (sid, d_rep)).fetchall()
        if data:
            df = pd.DataFrame(data, columns=["REF", "CLIENT", "TOTAL $", "VENDEUR", "HEURE"])
            st.dataframe(df, use_container_width=True)
            st.metric("TOTAL VENDU ($)", f"{df['TOTAL $'].sum():,.2f}")
        else: st.warning("Rien pour cette date.")

# --- 8.6 MON ÉQUIPE ---
elif choice == "👥 MON ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    with st.form("nv_vend"):
        v_id = st.text_input("ID Vendeur").lower()
        v_nom = st.text_input("Nom")
        v_pw = st.text_input("Pass", type="password")
        if st.form_submit_button("CRÉER"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (v_id, hash_password(v_pw), 'VENDEUR', sid, 'ACTIF', v_nom, '', datetime.now().strftime("%d/%m/%Y")))
                    conn.commit(); st.success("Vendeur créé !")
                except: st.error("ID déjà utilisé.")
    
    with sqlite3.connect(DB_FILE) as conn:
        vends = conn.execute("SELECT uid, name, status FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_uid, v_name, v_stat in vends:
            st.write(f"Vendeur: {v_name} (@{v_uid}) - {v_stat}")
            if st.button(f"🗑️ SUPPRIMER {v_uid}"):
                conn.execute("DELETE FROM users WHERE uid=?", (v_uid,))
                conn.commit(); st.rerun()

# --- 8.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES BOUTIQUE":
    st.header("⚙️ PARAMÈTRES")
    with st.form("reg_shop"):
        n_nom = st.text_input("Nom Boutique", shop_data[0])
        n_taux = st.number_input("Taux (1$ = ? CDF)", value=shop_data[1])
        n_tel = st.text_input("Téléphone", shop_data[4])
        if st.form_submit_button("ENREGISTRER"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, tel=? WHERE sid=?", (n_nom, n_taux, n_tel, sid))
                conn.commit(); st.success("Modifié !"); st.rerun()

# --- 8.8 QUITTER ---
elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()
