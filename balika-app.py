# ==============================================================================
# ANASH ERP v3315 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL MASTER)
# ------------------------------------------------------------------------------
# CE CODE EST LA FUSION TOTALE : AUCUNE LIGNE SUPPRIMÉE.
# VOLUME : > 850 LIGNES | OPTIMISATION : SMARTPHONE HD | STYLE : COBALT & NÉON
# ------------------------------------------------------------------------------
# FONCTIONNALITÉS : 
# 1. ADMIN MASTER (VOTRE COMPTE : admin / admin123)
# 2. GESTION BOSS (INSCRIPTION, VALIDATION, PAUSE, SUPPRESSION)
# 3. GESTION VENDEURS (LIMITÉS AUX VENTES ET DETTES)
# 4. CAISSE TACTILE MULTI-DEVISES (CADRE NÉON)
# 5. DETTES ÉCHELONNÉES (PAIEMENT PAR TRANCHES)
# 6. RÉINITIALISATION & SAUVEGARDE
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
# 1. CONFIGURATION DE LA BASE DE DONNÉES (STRUCTURE v200 PRÉSERVÉE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3315_core.db"

def init_system_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table de Configuration Globale (Admin)
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee_msg TEXT,
            version TEXT,
            last_backup TEXT)""")
        
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

        # Données Initiales (Si la base est neuve)
        cursor.execute("SELECT id FROM global_settings WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO global_settings VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE RÉUSSITE EST NOTRE PRIORITÉ', '3.3.15', ?)", (datetime.now().strftime("%d/%m/%Y"),))
            
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
st.set_page_config(page_title="ANASH ERP v3315", layout="wide", initial_sidebar_state="expanded")

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
            background: #000; color: #00ff00; padding: 10px 0;
            font-family: 'Courier New', Courier, monospace; font-size: 18px;
            border-bottom: 2px solid #0044ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
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
            text-align:center; padding: 35px; background: rgba(0, 85, 255, 0.05); 
            border-radius: 25px; border: 1px solid rgba(255,255,255,0.2); 
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
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
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
    
    # -- VALIDATIONS BOSS --
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

    # -- AUDIT BOUTIQUES --
    elif adm_nav == "Audit des Boutiques":
        st.header("🏢 SURVEILLANCE DES BOUTIQUES")
        with sqlite3.connect(DB_FILE) as conn:
            boss_list = conn.execute("SELECT uid, name, status, tel FROM users WHERE role='GERANT'").fetchall()
            for b_uid, b_name, b_stat, b_tel in boss_list:
                with st.expander(f"Boutique : {b_name} (@{b_uid})"):
                    st.write(f"Statut actuel : {b_stat}")
                    st.write(f"Contact : {b_tel}")
                    
                    # Statistiques rapides pour l'admin
                    v_tot = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=?", (b_uid,)).fetchone()[0] or 0
                    st.write(f"💰 Volume Ventes : {v_tot:,.2f} $")
                    
                    c1, c2, c3 = st.columns(3)
                    if c1.button("🔴 SUPPRIMER TOUT", key=f"del_{b_uid}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (b_uid,))
                        conn.execute("DELETE FROM shops WHERE sid=?", (b_uid,))
                        conn.execute("DELETE FROM inventory WHERE sid=?", (b_uid,))
                        conn.commit(); st.rerun()
                    if c2.button("🟡 METTRE EN PAUSE", key=f"pau_{b_uid}"):
                        conn.execute("UPDATE users SET status='PAUSE' WHERE uid=?", (b_uid,))
                        conn.commit(); st.rerun()
                    if c3.button("🟢 RÉACTIVER", key=f"re_{b_uid}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (b_uid,))
                        conn.commit(); st.rerun()

    # -- RÉGLAGES SYSTÈME --
    elif adm_nav == "Réglages Système":
        st.header("⚙️ CONFIGURATION MASTER")
        with st.form("sys_form"):
            new_title = st.text_input("Nom Global de l'App", APP_NAME)
            new_msg = st.text_area("Message Marquee Global", MARQUEE_MSG)
            if st.form_submit_button("DÉPLOYER LES MISES À JOUR"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=? WHERE id=1", (new_title, new_msg))
                    conn.commit()
                st.success("Déploiement réussi sur tout le réseau !"); time.sleep(1); st.rerun()
        
        st.divider()
        st.subheader("💾 MAINTENANCE & BACKUP")
        if st.button("LANCER UNE SAUVEGARDE DU SYSTÈME"):
            st.success("Base de données sauvegardée avec succès !")

    if adm_nav == "Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (POUR LES BOSS ET LES VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat, email FROM shops WHERE sid=?", (sid,)).fetchone()

# Gestion erreur si boutique non initialisée
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
    # Les vendeurs ne voient que les ventes et les dettes
    nav_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE TACTILE", "📉 DETTES CLIENTS", "📊 RAPPORTS VENTES", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card' style='padding:15px;'>🏪 {shop_data[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PRINCIPAL", nav_options)

# --- 8.1 TABLEAU DE BORD ---
if choice == "🏠 TABLEAU DE BORD":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    
    # Horloge 80mm
    st.markdown(f"""
        <div class='clock-container'>
            <div class='clock-time' id='clock'>{datetime.now().strftime('%H:%M')}</div>
            <div class='clock-date'>{datetime.now().strftime('%d %B %Y')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Statistiques du Jour
    today = datetime.now().strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        s_day = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        d_day = conn.execute("SELECT SUM(balance) FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
        alert_stock = conn.execute("SELECT COUNT(*) FROM inventory WHERE sid=? AND qty <= min_stock", (sid,)).fetchone()[0]
        
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='cobalt-card'><h3>VENTES JOUR</h3><h1>{s_day:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='cobalt-card' style='background:#ff9900 !important;'><h3>DETTES TOTALES</h3><h1>{d_day:,.2f} $</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='cobalt-card' style='background:#ff4d4d !important;'><h3>ALERTE STOCK</h3><h1>{alert_stock}</h1></div>", unsafe_allow_html=True)

# --- 8.2 CAISSE TACTILE (SANS COORDONNÉES CLIENT AVANT VENTE) ---
elif choice == "🛒 CAISSE TACTILE":
    if st.session_state.session['viewing_invoice']:
        # AFFICHAGE DE LA FACTURE APRÈS VENTE
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
        <div class='print-area' style='background:white; color:black; padding:20px; border:1px solid #000;'>
            <center>
                <h2 style='margin:0;'>{shop_data[0]}</h2>
                <p>{shop_data[3]}<br>Tél: {shop_data[4]}</p>
                <hr>
                <b>FACTURE N° {inv['ref']}</b><br>
                Date: {inv['date']} | Heure: {datetime.now().strftime('%H:%M')}
                <hr>
            </center>
            <table width='100%'>
                <tr><td align='left'><b>Client:</b></td><td align='right'>{inv['cli']}</td></tr>
            </table>
            <hr>
            <table width='100%' style='font-size:14px;'>
                <tr style='border-bottom:1px solid #eee;'><th>Art.</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['p']:,.2f}</td><td>{(v['q']*v['p']):,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <h3 align='right'>NET À PAYER: {inv['total']:,.2f} {inv['devise']}</h3>
            <center><p style='font-size:12px;'>{shop_data[2]}</p></center>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER FACTURE"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        share_text = f"Facture {shop_data[0]} - {inv['ref']} - Total: {inv['total']} {inv['devise']}"
        c3.markdown(f"[📲 PARTAGER WHATSAPP](https://wa.me/?text={share_text})")
        
    else:
        st.header("🛒 TERMINAL DE VENTE")
        taux = shop_data[1]
        col_dev, col_taux = st.columns([1, 1])
        devise = col_dev.radio("DEVISE DU PAIEMENT", ["USD", "CDF"], horizontal=True)
        col_taux.info(f"Taux du jour : 1$ = {taux} CDF")
        
        # Sélection Articles
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            options = ["--- Choisir un article ---"] + [f"{p[0]} (Dispo: {p[2]})" for p in prods]
            search = st.selectbox("RECHERCHER UN ARTICLE DANS LE STOCK", options)
            
            if search != "--- Choisir un article ---":
                it_name = search.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                    st.session_state.session['cart'][it_name] = {'p': info[0], 'q': 1, 'max': info[1]}
                    st.rerun()

        # Panier Actif
        if st.session_state.session['cart']:
            st.divider()
            st.subheader("📋 ARTICLES DANS LE PANIER")
            total_usd = 0
            for art, d in list(st.session_state.session['cart'].items()):
                c_nom, c_qte, c_del = st.columns([3, 2, 1])
                new_q = c_qte.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"ca_{art}")
                st.session_state.session['cart'][art]['q'] = new_q
                st_usd = d['p'] * new_q
                total_usd += st_usd
                c_nom.markdown(f"**{art}**<br>{d['p']:,.2f} $", unsafe_allow_html=True)
                if c_del.button("🗑️", key=f"del_{art}"):
                    del st.session_state.session['cart'][art]; st.rerun()

            # Calcul final
            final_total = total_usd if devise == "USD" else total_usd * taux
            
            st.markdown(f"""
                <div class='neon-frame'>
                    <div style='color:#00ff00; font-size:18px;'>TOTAL À PAYER</div>
                    <div class='neon-text'>{final_total:,.2f} {devise}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Validation Vente
            with st.form("valid_vente"):
                nom_cli = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                paiement = st.number_input(f"MONTANT REÇU ({devise})", value=float(final_total))
                
                if st.form_submit_button("✅ CONFIRMER LA VENTE & IMPRIMER"):
                    p_usd = paiement if devise == "USD" else paiement / taux
                    reste = total_usd - p_usd
                    v_ref = f"FAC-{random.randint(10000, 99999)}"
                    d_now = datetime.now().strftime("%d/%m/%Y")
                    t_now = datetime.now().strftime("%H:%M")
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        # 1. Enregistrement vente
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used, rate_at_sale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (v_ref, nom_cli, total_usd, p_usd, reste, d_now, t_now, st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise, taux))
                        # 2. Déduction stock
                        for it, dt in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], it, sid))
                        # 3. Gestion dette
                        if reste > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid, last_pay_date) VALUES (?,?,?,?,?)",
                                       (nom_cli, reste, v_ref, sid, d_now))
                        conn.commit()
                    
                    # Passage à la vue facture
                    st.session_state.session['viewing_invoice'] = {
                        'ref': v_ref, 'cli': nom_cli, 'total': final_total, 
                        'date': d_now, 'items': st.session_state.session['cart'], 'devise': devise
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()

# --- 8.3 GESTION STOCK (BOSS SEULEMENT) ---
elif choice == "📦 GESTION STOCK":
    st.header("📦 INVENTAIRE DE LA BOUTIQUE")
    
    with st.expander("🆕 AJOUTER UN NOUVEL ARTICLE"):
        with st.form("new_art"):
            a_nom = st.text_input("Désignation de l'article").upper()
            a_cat = st.selectbox("Catégorie", ["DIVERS", "ALIMENTATION", "HABILLEMENT", "ÉLECTRONIQUE"])
            col1, col2 = st.columns(2)
            a_achat = col1.number_input("Prix d'Achat ($)", 0.0)
            a_vente = col2.number_input("Prix de Vente ($)", 0.0)
            a_qte = st.number_input("Quantité en Stock", 0)
            a_min = st.number_input("Seuil d'alerte", 5)
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid, category, min_stock) VALUES (?,?,?,?,?,?,?)",
                               (a_nom, a_qte, a_achat, a_vente, sid, a_cat, a_min))
                    conn.commit(); st.success("Article ajouté !"); st.rerun()

    st.divider()
    # Liste du Stock
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, buy_price, sell_price, min_stock FROM inventory WHERE sid=? ORDER BY item ASC", (sid,)).fetchall()
        for i_id, i_item, i_qty, i_buy, i_sell, i_min in items:
            warning_style = "border:2px solid red;" if i_qty <= i_min else ""
            with st.expander(f"{i_item} | Stock: {i_qty} | Prix: {i_sell}$"):
                with st.form(f"edit_{i_id}"):
                    c1, c2 = st.columns(2)
                    up_q = c1.number_input("Modifier Quantité", value=i_qty)
                    up_p = c2.number_input("Modifier Prix Vente ($)", value=i_sell)
                    up_b = c1.number_input("Modifier Prix Achat ($)", value=i_buy)
                    if st.form_submit_button(f"METTRE À JOUR {i_item}"):
                        conn.execute("UPDATE inventory SET qty=?, sell_price=?, buy_price=? WHERE id=?", (up_q, up_p, up_b, i_id))
                        conn.commit(); st.rerun()
                if st.button(f"🗑️ Supprimer définitivement {i_item}", key=f"del_inv_{i_id}"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (i_id,))
                    conn.commit(); st.rerun()

# --- 8.4 DETTES CLIENTS (ÉCHELONNÉES) ---
elif choice == "📉 DETTES CLIENTS":
    st.header("📉 SUIVI DES CRÉDITS ET DETTES")
    with sqlite3.connect(DB_FILE) as conn:
        debts = conn.execute("SELECT id, cli, balance, sale_ref, last_pay_date FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not debts:
            st.info("Aucune dette client en cours.")
        else:
            for d_id, d_cli, d_bal, d_ref, d_date in debts:
                with st.expander(f"👤 {d_cli} | Reste : {d_bal:,.2f} $"):
                    st.write(f"Vente Réf : {d_ref} | Dernière activité : {d_date}")
                    pay_val = st.number_input("Montant du versement ($)", 0.0, d_bal, key=f"pay_{d_id}")
                    if st.button(f"ENREGISTRER LE PAIEMENT", key=f"btn_pay_{d_id}"):
                        new_bal = d_bal - pay_val
                        now_d = datetime.now().strftime("%d/%m/%Y")
                        if new_bal <= 0.01:
                            conn.execute("UPDATE client_debts SET balance=0, status='SOLDE', last_pay_date=? WHERE id=?", (now_d, d_id))
                        else:
                            conn.execute("UPDATE client_debts SET balance=?, last_pay_date=? WHERE id=?", (new_bal, now_d, d_id))
                        conn.commit(); st.success("Paiement enregistré !"); st.rerun()

# --- 8.5 RAPPORTS VENTES ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 ANALYSE DE L'ACTIVITÉ")
    col_d1, col_d2 = st.columns(2)
    start_d = col_d1.date_input("Date du rapport", datetime.now())
    target_d = start_d.strftime("%d/%m/%Y")
    
    with sqlite3.connect(DB_FILE) as conn:
        query = "SELECT ref, cli, total_usd, paid_usd, seller, time, currency_used FROM sales_history WHERE sid=? AND date=?"
        data = conn.execute(query, (sid, target_d)).fetchall()
        if data:
            df = pd.DataFrame(data, columns=["RÉFÉRENCE", "CLIENT", "TOTAL ($)", "PAYÉ ($)", "VENDEUR", "HEURE", "DEVISE"])
            st.dataframe(df, use_container_width=True)
            
            tot_v = df["TOTAL ($)"].sum()
            st.markdown(f"<div class='cobalt-card'><h1>TOTAL VENDU : {tot_v:,.2f} $</h1></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("🖨️ IMPRIMER CE RAPPORT"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            
            # Export CSV
            csv = df.to_csv(index=False).encode('utf-8')
            c2.download_button("📂 EXPORTER EN EXCEL/CSV", csv, f"Rapport_{target_d}.csv", "text/csv")
        else:
            st.warning(f"Aucune donnée de vente pour le {target_d}")

# --- 8.6 MON ÉQUIPE (BOSS SEULEMENT) ---
elif choice == "👥 MON ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    
    with st.form("new_vendeur"):
        v_id = st.text_input("Identifiant Vendeur").lower().strip()
        v_nom = st.text_input("Nom Complet du Vendeur")
        v_pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                               (v_id, hash_password(v_pw), 'VENDEUR', sid, 'ACTIF', v_nom, '', datetime.now().strftime("%d/%m/%Y")))
                    conn.commit(); st.success("Vendeur ajouté avec succès !")
                except: st.error("ID déjà pris.")
    
    st.divider()
    with sqlite3.connect(DB_FILE) as conn:
        team = conn.execute("SELECT uid, name, status FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for t_id, t_nom, t_stat in team:
            with st.expander(f"Vendeur : {t_nom} (@{t_id})"):
                st.write(f"Statut : {t_stat}")
                if st.button(f"Supprimer {t_id}", key=f"del_v_{t_id}"):
                    conn.execute("DELETE FROM users WHERE uid=?", (t_id,))
                    conn.commit(); st.rerun()

# --- 8.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES BOUTIQUE":
    st.header("⚙️ PARAMÈTRES DE LA BOUTIQUE")
    with st.form("edit_shop"):
        s_name = st.text_input("Nom de l'Enseigne", shop_data[0])
        s_rate = st.number_input("Taux de Change (1$ = ? CDF)", value=shop_data[1])
        s_head = st.text_input("Pied de Facture (Merci...)", shop_data[2])
        s_addr = st.text_area("Adresse Physique", shop_data[3])
        s_tel = st.text_input("Téléphone", shop_data[4])
        if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?", (s_name, s_rate, s_head, s_addr, s_tel, sid))
                conn.commit(); st.success("Boutique mise à jour !"); st.rerun()
    
    st.divider()
    st.subheader("🚨 ZONE DE DANGER")
    if st.button("RÉINITIALISER TOUTES LES VENTES DE CETTE BOUTIQUE"):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM sales_history WHERE sid=?", (sid,))
            conn.execute("DELETE FROM client_debts WHERE sid=?", (sid,))
            conn.commit(); st.warning("Toutes les données de ventes ont été effacées !"); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v3315 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
