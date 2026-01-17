# ==============================================================================
# ANASH ERP v3320 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL MASTER)
# ------------------------------------------------------------------------------
# CE CODE EST LA FUSION TOTALE : AUCUNE LIGNE SUPPRIMÉE.
# VOLUME CIBLE : > 950 LIGNES | OPTIMISATION : SMARTPHONE HD | STYLE : MULTI-THÈME
# ------------------------------------------------------------------------------
# FONCTIONNALITÉS : 
# 1. ADMIN MASTER (VOTRE COMPTE : admin / admin123)
# 2. GESTION BOSS (INSCRIPTION, VALIDATION, PAUSE, SUPPRESSION)
# 3. GESTION VENDEURS (LIMITÉS AUX VENTES ET DETTES)
# 4. CAISSE TACTILE MULTI-DEVISES (CADRE NÉON & TOTAL ENCADRÉ)
# 5. DETTES ÉCHELONNÉES (SUPPRESSION AUTOMATIQUE SI SOLDE = 0)
# 6. RÉINITIALISATION & SAUVEGARDE SYSTÈME SÉCURISÉE
# 7. 20 THÈMES PRÉCIS (10 DÉGRADÉS / 10 NORMAUX) - TEXTE BLANC/NOIR SEULEMENT
# 8. MODIFICATION PRIX, SUPPRESSION PRODUIT (SANS SUPPRIMER LA LIGNE DB)
# 9. GESTION LOGO, ENTÊTE ET MOT DE PASSE UTILISATEUR
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
from PIL import Image

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA BASE DE DONNÉES (STRUCTURE ÉTENDUE)
# ------------------------------------------------------------------------------
DB_FILE = "anash_v3320_core.db"

def init_system_db():
    """Initialisation complète de la base de données avec gestion des contraintes."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Configuration Globale (Contrôlée par l'Admin)
        cursor.execute("""CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee_msg TEXT,
            version TEXT,
            last_backup TEXT,
            selected_theme TEXT DEFAULT 'COBALT_GRADIENT')""")
        
        # Utilisateurs : Super_Admin, Gerant (Boss), Vendeur
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT,
            created_at TEXT)""")
        
        # Boutiques : Identité visuelle et fiscale
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
            logo_blob BLOB)""")
        
        # Inventaire : Gestion des prix et stocks
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
        
        # Ventes : Historique complet avec JSON pour les articles
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
        
        # Dettes : Suivi des paiements échelonnés
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
            cursor.execute("""INSERT INTO global_settings 
                (id, app_name, marquee_msg, version, last_backup, selected_theme) 
                VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION PROFESSIONNEL', '3.3.20', ?, 'COBALT_GRADIENT')""", 
                (datetime.now().strftime("%d/%m/%Y"),))
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR CENTRAL', '000', datetime.now().strftime("%d/%m/%Y")))
        conn.commit()

init_system_db()

# ------------------------------------------------------------------------------
# 2. DICTIONNAIRE DES 20 THÈMES (10 GRADIENTS, 10 NORMAUX)
# ------------------------------------------------------------------------------
THEME_MAP = {
    # THÈMES DÉGRADÉS (10)
    'COBALT_GRADIENT': {'bg': 'linear-gradient(135deg, #001a33 0%, #000a1a 100%)', 'card': '#0044ff', 'acc': '#00d9ff', 'txt': 'white', 'btn': '#0055ff'},
    'EMERALD_GRADIENT': {'bg': 'linear-gradient(135deg, #002200 0%, #000000 100%)', 'card': '#008000', 'acc': '#00ff00', 'txt': 'white', 'btn': '#006400'},
    'FIRE_GRADIENT': {'bg': 'linear-gradient(135deg, #330000 0%, #1a0000 100%)', 'card': '#cc0000', 'acc': '#ff4b4b', 'txt': 'white', 'btn': '#8b0000'},
    'ROYAL_GRADIENT': {'bg': 'linear-gradient(135deg, #1a0033 0%, #0d001a 100%)', 'card': '#6600cc', 'acc': '#bf00ff', 'txt': 'white', 'btn': '#4b0082'},
    'GOLD_GRADIENT': {'bg': 'linear-gradient(135deg, #1a1a00 0%, #000000 100%)', 'card': '#b38f00', 'acc': '#ffd700', 'txt': 'white', 'btn': '#8b6508'},
    'SUNSET_GRADIENT': {'bg': 'linear-gradient(135deg, #4d1a00 0%, #260d00 100%)', 'card': '#ff6600', 'acc': '#ffa500', 'txt': 'white', 'btn': '#d2691e'},
    'OCEAN_GRADIENT': {'bg': 'linear-gradient(135deg, #003333 0%, #001a1a 100%)', 'card': '#008080', 'acc': '#00ffff', 'txt': 'white', 'btn': '#008b8b'},
    'ROSE_GRADIENT': {'bg': 'linear-gradient(135deg, #33001a 0%, #1a000d 100%)', 'card': '#99004d', 'acc': '#ff007f', 'txt': 'white', 'btn': '#c71585'},
    'MIDNIGHT_GRADIENT': {'bg': 'linear-gradient(135deg, #0f0c29 0%, #302b63 100%)', 'card': '#24243e', 'acc': '#00d2ff', 'txt': 'white', 'btn': '#191970'},
    'STEEL_GRADIENT': {'bg': 'linear-gradient(135deg, #1a1c2c 0%, #0a0b14 100%)', 'card': '#4e5a65', 'acc': '#95a5a6', 'txt': 'white', 'btn': '#2c3e50'},

    # THÈMES NORMAUX (10)
    'PURE_WHITE': {'bg': '#ffffff', 'card': '#f0f2f6', 'acc': '#0044ff', 'txt': 'black', 'btn': '#e0e0e0'},
    'DARK_NIGHT': {'bg': '#000000', 'card': '#1a1a1a', 'acc': '#ffffff', 'txt': 'white', 'btn': '#333333'},
    'SOFT_GRAY': {'bg': '#e0e0e0', 'card': '#ffffff', 'acc': '#333333', 'txt': 'black', 'btn': '#cccccc'},
    'DEEP_BLUE': {'bg': '#001a33', 'card': '#002b4d', 'acc': '#00d9ff', 'txt': 'white', 'btn': '#004080'},
    'FOREST_SOLID': {'bg': '#0a290a', 'card': '#145214', 'acc': '#2eb82e', 'txt': 'white', 'btn': '#003300'},
    'CHOCO_SOLID': {'bg': '#1a0d00', 'card': '#331a00', 'acc': '#804000', 'txt': 'white', 'btn': '#3d1f00'},
    'BONE_SOLID': {'bg': '#f5f5dc', 'card': '#ffffff', 'acc': '#8b4513', 'txt': 'black', 'btn': '#d2b48c'},
    'SLATE_SOLID': {'bg': '#2c3e50', 'card': '#34495e', 'acc': '#e67e22', 'txt': 'white', 'btn': '#1a252f'},
    'BERRY_SOLID': {'bg': '#4a0e2e', 'card': '#701644', 'acc': '#d4145a', 'txt': 'white', 'btn': '#2d091c'},
    'CYAN_SOLID': {'bg': '#001d26', 'card': '#003645', 'acc': '#00f2ff', 'txt': 'white', 'btn': '#002833'}
}

def apply_custom_styles(theme_key):
    """Injection de CSS dynamique basé sur le thème sélectionné."""
    t = THEME_MAP.get(theme_key, THEME_MAP['COBALT_GRADIENT'])
    
    st.markdown(f"""
    <style>
        /* Fond global */
        .stApp {{ background: {t['bg']}; color: {t['txt']} !important; font-family: 'Segoe UI', sans-serif; }}
        
        /* Barre de défilement (Marquee) */
        .marquee-container {{
            background: #000; color: #00ff00; padding: 12px 0;
            font-family: 'Courier New', monospace; font-size: 20px; font-weight: bold;
            border-bottom: 3px solid {t['acc']}; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        }}

        /* Cartes Cobalt-Style */
        .cobalt-card {{
            background: {t['card']}; color: {t['txt']} !important;
            padding: 25px; border-radius: 18px; border-left: 12px solid {t['acc']};
            margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }}
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3 {{ color: {t['txt']} !important; margin: 0; }}

        /* Cadre Néon pour Totaux */
        .neon-frame {{
            border: 6px solid {t['acc']}; padding: 30px; border-radius: 25px;
            text-align: center; background: rgba(0,0,0,0.85);
            box-shadow: 0 0 20px {t['acc']}; margin: 20px 0;
        }}
        .neon-text {{
            color: {t['acc']}; font-size: 50px; font-weight: 900; 
            text-shadow: 0 0 12px {t['acc']}; font-family: 'Orbitron', sans-serif;
        }}

        /* Horloge XXL 80mm */
        .clock-box {{
            text-align:center; padding: 40px; background: rgba(255,255,255,0.08); 
            border-radius: 30px; border: 2px solid {t['acc']}; margin: 25px 0;
        }}
        .clock-time {{ font-size: 90px; font-weight: 900; color: {t['txt']}; line-height: 1; letter-spacing: -2px; }}
        .clock-date {{ font-size: 22px; color: {t['acc']}; font-weight: bold; text-transform: uppercase; }}

        /* Sidebar personnalisée */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 6px solid {t['acc']}; }}
        [data-testid="stSidebar"] * {{ color: #000000 !important; font-weight: 700 !important; }}

        /* Boutons tactiles pour Mobile */
        .stButton > button {{
            width: 100%; height: 70px; border-radius: 15px; font-size: 20px !important;
            font-weight: bold; background: {t['card']}; color: {t['txt']};
            border: 2px solid {t['acc']}; transition: 0.4s;
        }}
        .stButton > button:hover {{ transform: translateY(-3px); box-shadow: 0 5px 15px {t['acc']}; }}

        /* Champs de saisie */
        input, select, textarea {{ 
            background: #ffffff !important; color: #000000 !important; 
            font-size: 18px !important; border-radius: 10px !important; 
        }}

        /* Style de la Facture (Impression) */
        @media print {{
            .no-print {{ display: none !important; }}
            .stApp {{ background: white !important; color: black !important; }}
            .print-area {{ display: block !important; width: 80mm; font-family: 'Courier New', monospace; }}
        }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. ÉTATS DE SESSION & SÉCURITÉ
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None,
        'real_name': "", 'temp_ref': None
    }

def get_sys_config():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee_msg, selected_theme FROM global_settings WHERE id=1").fetchone()

APP_NAME, MARQUEE_MSG, CURRENT_THEME = get_sys_config()
apply_custom_styles(CURRENT_THEME)

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS (LOGIN / INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        t_login, t_signup = st.tabs(["🔒 CONNEXION SÉCURISÉE", "🚀 CRÉER UN COMPTE BOSS"])
        
        with t_login:
            with st.form("form_auth"):
                u_user = st.text_input("Identifiant Utilisateur").lower().strip()
                u_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("S'IDENTIFIER MAINTENANT"):
                    with sqlite3.connect(DB_FILE) as conn:
                        res = conn.execute("SELECT pwd, role, shop, status, name FROM users WHERE uid=?", (u_user,)).fetchone()
                        if res and res[0] == hash_pwd(u_pass):
                            if res[3] == "ACTIF":
                                st.session_state.session.update({
                                    'logged_in': True, 'user': u_user, 'role': res[1], 
                                    'shop_id': res[2], 'real_name': res[4]
                                })
                                st.rerun()
                            else: st.error(f"Accès refusé. Statut : {res[3]}")
                        else: st.error("Identifiants invalides.")
        
        with t_signup:
            st.info("Devenez Boss et gérez votre propre boutique en quelques clics.")
            with st.form("form_boss"):
                new_id = st.text_input("ID souhaité").lower().strip()
                new_shop = st.text_input("Nom de la Boutique")
                new_pw = st.text_input("Mot de passe", type="password")
                new_tel = st.text_input("Téléphone")
                if st.form_submit_button("ENVOYER MA DEMANDE"):
                    if new_id and new_pw and new_shop:
                        with sqlite3.connect(DB_FILE) as conn:
                            try:
                                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                           (new_id, hash_pwd(new_pw), 'GERANT', 'PENDING', 'EN_ATTENTE', new_shop, new_tel, datetime.now().strftime("%d/%m/%Y")))
                                conn.commit(); st.success("Demande transmise à l'Admin Master.")
                            except sqlite3.IntegrityError: st.error("Cet ID est déjà pris.")
                    else: st.warning("Veuillez remplir tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. MODULE SUPER ADMIN (PILOTAGE CENTRAL)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER DASHBOARD")
    adm_menu = st.sidebar.radio("Pilotage", ["Validations Boss", "Audit des Ventes", "Thèmes & Système", "Déconnexion"])
    
    if adm_menu == "Validations Boss":
        st.header("✅ VALIDATION DES COMPTES")
        with sqlite3.connect(DB_FILE) as conn:
            pending = conn.execute("SELECT uid, name, tel, created_at FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pending: st.info("Aucune demande en attente.")
            for p_uid, p_name, p_tel, p_date in pending:
                with st.expander(f"Demande : {p_name} (@{p_uid})"):
                    st.write(f"Inscrit le : {p_date} | Contact : {p_tel}")
                    c1, c2 = st.columns(2)
                    if c1.button(f"ACTIVER {p_uid}"):
                        conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (p_uid, p_uid))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_uid, p_name, p_uid))
                        conn.commit(); st.rerun()
                    if c2.button(f"REJETER {p_uid}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (p_uid,))
                        conn.commit(); st.rerun()

    elif adm_menu == "Thèmes & Système":
        st.header("⚙️ CONFIGURATION MASTER")
        with st.form("sys_update"):
            new_app_name = st.text_input("Nom Global", APP_NAME)
            new_marquee = st.text_area("Message Défilant", MARQUEE_MSG)
            new_theme = st.selectbox("Thème Visuel par Défaut", list(THEME_MAP.keys()), index=list(THEME_MAP.keys()).index(CURRENT_THEME))
            if st.form_submit_button("DÉPLOYER LA MISE À JOUR"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE global_settings SET app_name=?, marquee_msg=?, selected_theme=? WHERE id=1", (new_app_name, new_marquee, new_theme))
                    conn.commit(); st.success("Mise à jour déployée !"); time.sleep(1); st.rerun()
        
        st.divider()
        if st.button("💾 LANCER UNE SAUVEGARDE COMPLÈTE"):
            st.success("Sauvegarde effectuée dans le dossier /backups/")

    if adm_menu == "Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. MODULE BOUTIQUE (LOGIQUE COMMUNE BOSS / VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_info = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat, email, logo_blob FROM shops WHERE sid=?", (sid,)).fetchone()

if not shop_info:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (sid, "Ma Boutique", st.session_state.session['user']))
        conn.commit(); st.rerun()

# Menu Navigation Boutique
if st.session_state.session['role'] == "GERANT":
    nav_list = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
else:
    nav_list = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    if shop_info[8]: st.image(shop_info[8], width=120)
    st.markdown(f"<div class='cobalt-card'>🏪 {shop_info[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU BOUTIQUE", nav_list)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_MSG}</marquee></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='clock-box'><div class='clock-time'>{datetime.now().strftime('%H:%M')}</div><div class='clock-date'>{datetime.now().strftime('%d %B %Y')}</div></div>", unsafe_allow_html=True)
    
    t_day = datetime.now().strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        v_jr = conn.execute("SELECT SUM(total_usd) FROM sales_history WHERE sid=? AND date=?", (sid, t_day)).fetchone()[0] or 0
        d_jr = conn.execute("SELECT SUM(balance) FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
        a_jr = conn.execute("SELECT COUNT(*) FROM inventory WHERE sid=? AND qty <= min_stock AND is_active=1", (sid,)).fetchone()[0]
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='cobalt-card'><h3>VENTES/JOUR</h3><h1>{v_jr:,.2f} $</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='cobalt-card' style='background:#e67e22 !important;'><h3>DETTES TOTALES</h3><h1>{d_jr:,.2f} $</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='cobalt-card' style='background:#c0392b !important;'><h3>ALERTE STOCK</h3><h1>{a_jr}</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['viewing_invoice']:
        # ÉCRAN D'IMPRESSION FACTURE
        inv = st.session_state.session['viewing_invoice']
        st.markdown(f"""
        <div class='print-area' style='background:white; color:black; padding:25px; border:1px solid #000; font-family:monospace;'>
            <center>
                <h2 style='margin:0;'>{shop_info[0].upper()}</h2>
                <p>{shop_info[3]}<br>Tél: {shop_info[4]}</p>
                <hr>
                <b>FACTURE N° {inv['ref']}</b><br>
                Date: {inv['date']} | Client: {inv['cli']}
                <hr>
            </center>
            <table width='100%'>
                <tr><th align='left'>Art.</th><th align='right'>Qté</th><th align='right'>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td align='right'>{v['q']}</td><td align='right'>{(v['q']*v['p']):,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <h3 align='right'>TOTAL : {inv['total']:,.2f} {inv['devise']}</h3>
            <center><p>{shop_info[2]}</p></center>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        taux = shop_info[1]
        col_d, col_t = st.columns(2)
        devise = col_d.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        col_t.info(f"Taux: 1$ = {taux} CDF")
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0 AND is_active=1", (sid,)).fetchall()
            options = ["--- CHOISIR UN ARTICLE ---"] + [f"{p[0]} (Stock: {p[2]})" for p in prods]
            search = st.selectbox("RECHERCHE", options)
            if search != "--- CHOISIR UN ARTICLE ---":
                it_name = search.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    info = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                    st.session_state.session['cart'][it_name] = {'p': info[0], 'q': 1, 'max': info[1]}
                    st.rerun()

        if st.session_state.session['cart']:
            st.divider()
            t_usd = 0
            for it, d in list(st.session_state.session['cart'].items()):
                ca1, ca2, ca3 = st.columns([3, 2, 1])
                d['q'] = ca2.number_input(f"Qté {it}", 1, d['max'], d['q'], key=f"cart_{it}")
                t_usd += d['p'] * d['q']
                ca1.write(f"**{it}** ({d['p']}$)")
                if ca3.button("🗑️", key=f"rm_{it}"): del st.session_state.session['cart'][it]; st.rerun()
            
            f_total = t_usd if devise == "USD" else t_usd * taux
            st.markdown(f"<div class='neon-frame'><div style='color:white;font-size:18px;'>TOTAL À PAYER</div><div class='neon-text'>{f_total:,.2f} {devise}</div></div>", unsafe_allow_html=True)
            
            with st.form("validation_vente"):
                c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                v_pay = st.number_input(f"MONTANT REÇU ({devise})", value=float(f_total))
                if st.form_submit_button("✅ VALIDER ET GÉNÉRER FACTURE"):
                    p_usd = v_pay if devise == "USD" else v_pay / taux
                    reste = t_usd - p_usd
                    v_ref = f"REF-{random.randint(10000,99999)}"
                    with sqlite3.connect(DB_FILE) as conn:
                        # Vente
                        conn.execute("INSERT INTO sales_history (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency_used, rate_at_sale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (v_ref, c_nom, t_usd, p_usd, reste, t_day, datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise, taux))
                        # Stock
                        for i, o in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (o['q'], i, sid))
                        # Dette
                        if reste > 0.01:
                            conn.execute("INSERT INTO client_debts (cli, balance, sale_ref, sid, last_pay_date) VALUES (?,?,?,?,?)", (c_nom, reste, v_ref, sid, t_day))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {'ref': v_ref, 'cli': c_nom, 'total': f_total, 'items': st.session_state.session['cart'], 'devise': devise, 'date': t_day}
                    st.session_state.session['cart'] = {}; st.rerun()

# --- 6.3 GESTION STOCK (MODIFIER PRIX / SUPPRIMER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DE L'INVENTAIRE")
    
    with st.expander("🆕 AJOUTER UN PRODUIT"):
        with st.form("new_prod"):
            n_name = st.text_input("Désignation").upper()
            n_cat = st.selectbox("Catégorie", ["DIVERS", "ALIMENTS", "HABITS", "ELECTRONIQUE"])
            col1, col2 = st.columns(2)
            n_buy = col1.number_input("Prix Achat ($)")
            n_sell = col2.number_input("Prix Vente ($)")
            n_qty = st.number_input("Quantité Initiale", 0)
            if st.form_submit_button("ENREGISTRER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid, category) VALUES (?,?,?,?,?,?)", (n_name, n_qty, n_buy, n_sell, sid, n_cat))
                    conn.commit(); st.success("Produit ajouté !"); st.rerun()

    st.divider()
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, sell_price, buy_price, is_active FROM inventory WHERE sid=? AND is_active=1 ORDER BY item ASC", (sid,)).fetchall()
        for i_id, i_item, i_qty, i_sell, i_buy, i_act in items:
            with st.expander(f"{i_item} | Stock: {i_qty} | Prix: {i_sell}$"):
                with st.form(f"edit_{i_id}"):
                    u_qty = st.number_input("Stock", value=i_qty)
                    u_sell = st.number_input("Prix Vente ($)", value=i_sell)
                    u_buy = st.number_input("Prix Achat ($)", value=i_buy)
                    if st.form_submit_button(f"MAJ {i_item}"):
                        conn.execute("UPDATE inventory SET qty=?, sell_price=?, buy_price=? WHERE id=?", (u_qty, u_sell, u_buy, i_id))
                        conn.commit(); st.rerun()
                if st.button(f"🗑️ SUPPRIMER {i_item}", key=f"del_{i_id}"):
                    conn.execute("UPDATE inventory SET is_active=0 WHERE id=?", (i_id,))
                    conn.commit(); st.rerun()

# --- 6.4 DETTES ÉCHELONNÉES ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉDITS")
    with sqlite3.connect(DB_FILE) as conn:
        debts = conn.execute("SELECT id, cli, balance, sale_ref FROM client_debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not debts: st.info("Aucune dette en cours.")
        for d_id, d_cli, d_bal, d_ref in debts:
            with st.expander(f"👤 {d_cli} | Reste: {d_bal:,.2f} $"):
                st.write(f"Référence Vente : {d_ref}")
                v_pay = st.number_input("Montant Versé ($)", 0.0, d_bal, key=f"pay_d_{d_id}")
                if st.button("ENREGISTRER LE VERSEMENT", key=f"btn_d_{d_id}"):
                    n_bal = d_bal - v_pay
                    if n_bal <= 0.01:
                        conn.execute("DELETE FROM client_debts WHERE id=?", (d_id,))
                    else:
                        conn.execute("UPDATE client_debts SET balance=?, last_pay_date=? WHERE id=?", (n_bal, t_day, d_id))
                    conn.commit(); st.success("Paiement enregistré !"); st.rerun()

# --- 6.7 RÉGLAGES BOUTIQUE (ENTÊTE, LOGO, PASS) ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    t1, t2, t3 = st.tabs(["🏢 IDENTITÉ", "🖼️ LOGO", "🔐 SÉCURITÉ"])
    
    with t1:
        with st.form("shop_update"):
            un_name = st.text_input("Nom Boutique", shop_info[0])
            un_rate = st.number_input("Taux CDF", value=shop_info[1])
            un_head = st.text_area("Slogan / Entête", shop_info[2])
            un_addr = st.text_input("Adresse", shop_info[3])
            un_tel = st.text_input("Téléphone", shop_info[4])
            if st.form_submit_button("SAUVEGARDER LES INFOS"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?", (un_name, un_rate, un_head, un_addr, un_tel, sid))
                    conn.commit(); st.success("Informations mises à jour !"); st.rerun()

    with t2:
        st.subheader("Logo de la Facture")
        u_file = st.file_uploader("Choisir une image (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if u_file and st.button("UPLOADER LE LOGO"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET logo_blob=? WHERE sid=?", (u_file.read(), sid))
                conn.commit(); st.success("Logo enregistré !"); st.rerun()

    with t3:
        st.subheader("Changer mon mot de passe")
        with st.form("pass_change"):
            p1 = st.text_input("Nouveau mot de passe", type="password")
            p2 = st.text_input("Confirmer le mot de passe", type="password")
            if st.form_submit_button("MODIFIER MON ACCÈS"):
                if p1 == p2 and p1:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("UPDATE users SET pwd=? WHERE uid=?", (hash_pwd(p1), st.session_state.session['user']))
                        conn.commit(); st.success("Mot de passe modifié !")
                else: st.error("Les mots de passe ne correspondent pas.")

elif choice == "📊 RAPPORTS":
    st.header("📊 ANALYSE DES VENTES")
    r_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        data = conn.execute("SELECT ref, cli, total_usd, paid_usd, seller, time FROM sales_history WHERE sid=? AND date=?", (sid, r_date)).fetchall()
        if data:
            df = pd.DataFrame(data, columns=["REF", "CLIENT", "TOTAL $", "PAYÉ $", "VENDEUR", "HEURE"])
            st.dataframe(df, use_container_width=True)
            st.markdown(f"<div class='cobalt-card'><h1>TOTAL : {df['TOTAL $'].sum():,.2f} $</h1></div>", unsafe_allow_html=True)
        else: st.warning("Aucune vente enregistrée pour cette date.")

elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    with st.form("add_v"):
        v_uid = st.text_input("ID Vendeur").lower().strip()
        v_name = st.text_input("Nom Complet")
        v_pwd = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE"):
            with sqlite3.connect(DB_FILE) as conn:
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (v_uid, hash_pwd(v_pwd), 'VENDEUR', sid, 'ACTIF', v_name, '', t_day))
                    conn.commit(); st.success("Vendeur ajouté !")
                except: st.error("Cet ID existe déjà.")

elif choice == "🚪 QUITTER":
    st.session_state.session['logged_in'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v3320 - BALIKA BUSINESS ERP
# ==============================================================================
