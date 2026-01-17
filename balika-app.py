# ==============================================================================
# ANASH ERP v380 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL PRO)
# ------------------------------------------------------------------------------
# - CODE COMPLET (+600 LIGNES) - TOUTES VERSIONS FUSIONNÉES (v192 à v380)
# - AUCUNE LIGNE DE LOGIQUE PRÉCÉDENTE SUPPRIMÉE
# - AJOUT : BOUTONS ADMIN (ACTIVER/DÉSACTIVER MESSAGE DÉFILANT)
# - AJOUT : PAIEMENT DES DETTES PAR TRANCHES (SUPPRESSION AUTO SI 0)
# - AJOUT : PARTAGE WHATSAPP + DOUBLE FORMAT FACTURE (80mm/A4)
# - AJOUT : ÉDITEUR D'ENTÊTE PERSONNALISÉ DANS RÉGLAGES
# - OPTIMISATION : AFFICHAGE MOBILE (TEXTES BLANCS SUR FOND BLEU)
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
import urllib.parse

# ------------------------------------------------------------------------------
# 1. CONFIGURATION ET INITIALISATION DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "balika_v380_master.db"

def init_master_db():
    """Initialise la structure complète de la base de données sans perte de données."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table Configuration Système
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, 
            app_name TEXT, 
            marquee TEXT, 
            version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', 
            marquee_active INTEGER DEFAULT 1)""")
        
        # Table Utilisateurs (Admin, Gérants, Vendeurs)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pwd TEXT, 
            role TEXT, 
            shop TEXT, 
            status TEXT, 
            name TEXT, 
            tel TEXT)""")
        
        # Table Boutiques / Shops
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, 
            name TEXT, 
            owner TEXT, 
            rate REAL DEFAULT 2800.0, 
            head TEXT DEFAULT 'VOTRE EN-TÊTE ICI', 
            addr TEXT, 
            tel TEXT, 
            rccm TEXT, 
            idnat TEXT)""")
        
        # Table Inventaire (Stock)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, 
            qty INTEGER, 
            buy_price REAL, 
            sell_price REAL, 
            sid TEXT, 
            category TEXT DEFAULT 'GENERAL')""")
        
        # Table Ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
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
            currency TEXT)""")
        
        # Table Dettes (Gestion des tranches)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cli TEXT, 
            balance REAL, 
            sale_ref TEXT, 
            sid TEXT, 
            status TEXT DEFAULT 'OUVERT', 
            last_update TEXT)""")
        
        # Table Dépenses
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            label TEXT, 
            amount REAL, 
            date TEXT, 
            sid TEXT, 
            user TEXT)""")
        
        # Table Historique des paiements de dettes
        cursor.execute("""CREATE TABLE IF NOT EXISTS debt_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debt_id INTEGER,
            amount REAL,
            date TEXT,
            sid TEXT)""")

        # Insertion des données par défaut si vide
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO system_config 
                (id, app_name, marquee, version, theme_id, marquee_active) 
                VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '3.8.0', 'Cobalt', 1)""")
        
        # Création du compte Admin (admin / admin123)
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        
        conn.commit()

init_master_db()

# ------------------------------------------------------------------------------
# 2. FONCTIONS UTILITAIRES ET SÉCURITÉ
# ------------------------------------------------------------------------------
def get_hash(p): 
    """Hachage des mots de passe."""
    return hashlib.sha256(p.encode()).hexdigest()

def load_sys_config():
    """Charge la configuration globale du système."""
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee, theme_id, marquee_active FROM system_config WHERE id=1").fetchone()

def log_audit(user, action, sid):
    """Enregistre les actions critiques."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO audit_logs (user, action, date, time, sid) VALUES (?,?,?,?,?)",
                     (user, action, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S"), sid))
        conn.commit()

# ------------------------------------------------------------------------------
# 3. THÈMES ET PERSONNALISATION VISUELLE (STYLE v194)
# ------------------------------------------------------------------------------
THEMES = {
    "Cobalt": "linear-gradient(135deg, #004a99 0%, #002b5c 100%)",
    "Midnight": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    "Emerald": "linear-gradient(135deg, #004d40 0%, #00796b 100%)",
    "Carbon": "#212121",
    "Classic Blue": "#0d47a1",
    "Neon Green": "linear-gradient(135deg, #000000 0%, #00ff00 500%)"
}

SYS_DATA = load_sys_config()
APP_NAME, MARQUEE_TEXT, CURRENT_THEME, MARQUEE_ON = SYS_DATA[0], SYS_DATA[1], SYS_DATA[2], SYS_DATA[3]
SELECTED_BG = THEMES.get(CURRENT_THEME, THEMES["Cobalt"])

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

# Injection CSS pour le respect des contraintes (Texte blanc sur fond bleu, boutons larges)
st.markdown(f"""
<style>
    /* Global Background & Text */
    .stApp {{ background: {SELECTED_BG}; color: white !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid #00d4ff; }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
    
    /* Inputs */
    input {{ 
        text-align: center; border-radius: 12px !important; 
        background-color: white !important; color: black !important; 
        height: 50px !important; font-size: 18px !important; font-weight: bold; 
    }}
    
    /* Marquee Bar */
    .marquee-bar {{ 
        background: #000; color: #00ff00; padding: 15px; font-weight: bold; 
        border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; 
    }}
    
    /* Custom Cards */
    .cobalt-card {{ 
        background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px); 
        padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.3); 
        margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    }}
    
    /* Cart Styling (v194 Requirement) */
    .white-cart {{ 
        background: white !important; color: black !important; padding: 20px; 
        border-radius: 20px; border: 6px solid #004a99; margin: 15px 0; 
    }}
    .white-cart * {{ color: black !important; font-weight: bold; }}
    
    /* Total Frame (v194 Requirement) */
    .total-frame {{ 
        border: 5px solid #00ff00; background: #000; padding: 15px; 
        border-radius: 15px; margin: 15px 0; box-shadow: 0 0 20px rgba(0,255,0,0.4); 
    }}
    .total-text {{ color: #00ff00; font-size: 42px; font-weight: bold; }}
    
    /* Buttons */
    .stButton > button {{ 
        width: 100%; height: 60px; border-radius: 15px; font-size: 20px; 
        background: linear-gradient(to right, #007bff, #00d4ff); 
        color: white !important; font-weight: bold; border: none; margin-top: 10px;
        transition: transform 0.2s;
    }}
    .stButton > button:active {{ transform: scale(0.95); }}
    
    /* Invoices */
    .invoice-80mm {{ 
        background: white !important; color: black !important; padding: 15px; 
        font-family: 'Courier New', monospace; width: 100%; max-width: 320px; 
        margin: auto; border: 1px dashed #000; font-size: 14px; 
    }}
    .invoice-a4 {{ 
        background: white !important; color: black !important; padding: 50px; 
        font-family: 'Arial', sans-serif; width: 100%; max-width: 850px; 
        margin: auto; border: 1px solid #ccc; box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    .invoice-80mm *, .invoice-a4 * {{ color: black !important; text-align: left; }}
    
    /* WhatsApp Button */
    .btn-wa {{ 
        background-color: #25D366 !important; color: white !important; 
        text-decoration: none; padding: 18px; border-radius: 12px; 
        display: block; font-weight: bold; text-align: center; margin-top: 15px; font-size: 18px;
    }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. GESTION DES ÉTATS DE SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 
        'user': None, 
        'role': None, 
        'shop_id': None, 
        'cart': {}, 
        'viewing_invoice': None,
        'temp_sale_ref': None
    }

# ------------------------------------------------------------------------------
# 5. SYSTÈME DE CONNEXION (LOGIQUE v197)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='font-size: 50px;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
    
    col_l, col_main, col_r = st.columns([0.1, 0.8, 0.1])
    with col_main:
        st.markdown("<div class='cobalt-card'>", unsafe_allow_html=True)
        u_input = st.text_input("IDENTIFIANT (Login)").lower().strip()
        p_input = st.text_input("MOT DE PASSE", type="password")
        
        if st.button("🚀 SE CONNECTER"):
            with sqlite3.connect(DB_FILE) as conn:
                user_data = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_input,)).fetchone()
                if user_data and get_hash(p_input) == user_data[0]:
                    if user_data[3] == "ACTIF":
                        st.session_state.session.update({
                            'logged_in': True, 
                            'user': u_input, 
                            'role': user_data[1], 
                            'shop_id': user_data[2]
                        })
                        st.rerun()
                    else:
                        st.error("❌ Ce compte est suspendu.")
                else:
                    st.error("❌ Identifiants invalides.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 6. MENU ADMINISTRATEUR (SUPER_ADMIN)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMINISTRATION")
    a_menu = st.sidebar.radio("Navigation", ["⚙️ Configuration Système", "👥 Gestion des Boutiques", "🎨 Thèmes & Design", "🚪 Déconnexion"])
    
    if a_menu == "⚙️ Configuration Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        st.markdown(f"<div class='cobalt-card'>Statut du Marquee : {'🟢 ACTIVÉ' if MARQUEE_ON else '🔴 DÉSACTIVÉ'}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ ACTIVER LE MESSAGE"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET marquee_active=1 WHERE id=1")
                    conn.commit(); st.rerun()
        with col2:
            if st.button("🚫 DÉSACTIVER LE MESSAGE"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET marquee_active=0 WHERE id=1")
                    conn.commit(); st.rerun()
        
        new_marquee = st.text_area("Texte du message défilant", MARQUEE_TEXT)
        new_app_name = st.text_input("Nom de l'Application", APP_NAME)
        if st.button("💾 ENREGISTRER LA CONFIGURATION"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET marquee=?, app_name=? WHERE id=1", (new_marquee, new_app_name))
                conn.commit(); st.rerun()

    elif a_menu == "👥 Gestion des Boutiques":
        st.header("👥 BOUTIQUES & COMPTES GÉRANTS")
        with sqlite3.connect(DB_FILE) as conn:
            shops_list = conn.execute("SELECT sid, name, owner FROM shops").fetchall()
            for s_id, s_n, s_o in shops_list:
                with st.expander(f"🏪 {s_n} (ID: {s_id})"):
                    st.write(f"Propriétaire: {s_o}")
                    if st.button(f"Supprimer {s_n}", key=f"del_sh_{s_id}"):
                        conn.execute("DELETE FROM shops WHERE sid=?", (s_id,))
                        conn.execute("DELETE FROM users WHERE shop=?", (s_id,))
                        conn.commit(); st.rerun()
        
        st.divider()
        with st.form("create_shop"):
            st.subheader("🆕 CRÉER UNE NOUVELLE BOUTIQUE")
            n_sid = st.text_input("ID unique Boutique (ex: shop1)")
            n_sname = st.text_input("Nom de l'Etablissement")
            n_spass = st.text_input("Mot de passe Gérant", type="password")
            if st.form_submit_button("VALIDER LA CRÉATION"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name) VALUES (?,?,?,?,?,?)",
                                     (n_sid.lower(), get_hash(n_spass), 'GERANT', n_sid, 'ACTIF', n_sname))
                        conn.execute("INSERT INTO shops (sid, name, owner) VALUES (?,?,?)", (n_sid, n_sname, n_sid))
                        conn.commit(); st.success("Boutique créée avec succès !"); st.rerun()
                    except: st.error("L'identifiant existe déjà.")

    elif a_menu == "🎨 Thèmes & Design":
        st.header("🎨 PERSONNALISATION")
        choice_t = st.selectbox("Choisir le thème visuel", list(THEMES.keys()), index=list(THEMES.keys()).index(CURRENT_THEME))
        if st.button("APPLIQUER LE THÈME"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE system_config SET theme_id=? WHERE id=1", (choice_t,))
                conn.commit(); st.rerun()

    if a_menu == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE MÉTIER (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, addr, tel, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("BOUTIQUE", 2800.0, "ADRESSE", "000", "BIENVENUE")

# Construction du menu selon le rôle (v197 requirement)
nav_list = ["🏠 TABLEAU DE BORD", "🛒 VENDRE (CAISSE)", "📦 STOCK & PRODUITS", "📉 GESTION DES DETTES", "💸 DÉPENSES", "📊 RAPPORTS VENTES", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    nav_list = ["🏠 TABLEAU DE BORD", "🛒 VENDRE (CAISSE)", "📉 GESTION DES DETTES", "🚪 DÉCONNEXION"]

choice = st.sidebar.radio(f"🏪 {sh_inf[0]}", nav_list)

# --- 7.1 TABLEAU DE BORD (DASHBOARD) ---
if choice == "🏠 TABLEAU DE BORD":
    if MARQUEE_ON:
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='font-size: 70px; margin-bottom:0;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 20px;'>{datetime.now().strftime('%A %d %B %Y')}</p>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        ca_j = (conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        dep_j = (conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0)
        stock_val = (conn.execute("SELECT SUM(qty * sell_price) FROM inventory WHERE sid=?", (sid,)).fetchone()[0] or 0)
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cobalt-card'><h3>VENTES JOUR</h3><h2>{ca_j:,.2f} $</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cobalt-card'><h3>DÉPENSES JOUR</h3><h2>{dep_j:,.2f} $</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='cobalt-card'><h3>VALEUR STOCK</h3><h2>{stock_val:,.2f} $</h2></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='cobalt-card'><h1 style='color:#00ff00 !important;'>SOLDE NET : {(ca_j - dep_j):,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 7.2 CAISSE (LOGIQUE FUSIONNÉE v192 + v350) ---
elif choice == "🛒 VENDRE (CAISSE)":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        fmt = st.radio("FORMAT D'AFFICHAGE", ["TICKET MOBILE (80mm)", "FACTURE BUREAU (A4)"], horizontal=True)
        
        # Préparation HTML Facture
        h_head = f"<center><h3>{sh_inf[4]}</h3><p><b>{sh_inf[0]}</b><br>{sh_inf[2]}<br>Tél: {sh_inf[3]}</p></center>"
        h_body = f"<b>N° : {inv['ref']}</b><br>Client: {inv['cli']}<br>Date: {inv['date']}<hr>"
        h_body += "<table width='100%'><tr><th>Article</th><th>Qté</th><th>Total</th></tr>"
        
        msg_wa = f"*FACTURE {sh_inf[0]}*\nRef: {inv['ref']}\nClient: {inv['cli']}\n---\n"
        for it, d in inv['items'].items():
            h_body += f"<tr><td>{it}</td><td>{d['q']}</td><td>{(d['q']*d['p']):.1f}</td></tr>"
            msg_wa += f"- {it} [x{d['q']}] : {(d['q']*d['p']):.1f}$\n"
        
        h_body += f"</table><hr><h3>TOTAL : {inv['total_val']} {inv['dev']}</h3>"
        msg_wa += f"---\n*TOTAL À PAYER : {inv['total_val']} {inv['dev']}*\nMerci de votre fidélité !"
        
        st.markdown(f"<div class='{'invoice-80mm' if '80mm' in fmt else 'invoice-a4'}'>{h_head}{h_body}</div>", unsafe_allow_html=True)
        
        # Actions Facture
        wa_link = f"https://wa.me/?text={urllib.parse.quote(msg_wa)}"
        st.markdown(f'<a href="{wa_link}" target="_blank" class="btn-wa">📲 PARTAGER VIA WHATSAPP</a>', unsafe_allow_html=True)
        
        if st.button("🔄 NOUVELLE VENTE"):
            st.session_state.session['viewing_invoice'] = None
            st.rerun()
    else:
        # Interface de vente
        st.markdown("### 🛒 NOUVELLE VENTE")
        devise_v = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            sel_item = st.selectbox("RECHERCHER UN ARTICLE", ["--- Choisir ---"] + [f"{p[0]} (Stock: {p[2]})" for p in prods])
            
            if sel_item != "--- Choisir ---":
                name_p = sel_item.split(" (")[0]
                price_p = conn.execute("SELECT sell_price FROM inventory WHERE item=? AND sid=?", (name_p, sid)).fetchone()[0]
                qte_v = st.number_input("Quantité à vendre", 1, step=1)
                if st.button("➕ AJOUTER AU PANIER"):
                    st.session_state.session['cart'][name_p] = {'p': price_p, 'q': qte_v}
                    st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
            st.write("### 🛍️ VOTRE PANIER")
            t_usd = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
            t_final = t_usd if devise_v == "USD" else t_usd * sh_inf[1]
            
            st.markdown(f"<div class='total-frame'><span class='total-text'>{t_final:,.0f} {devise_v}</span></div>", unsafe_allow_html=True)
            
            for it, d in list(st.session_state.session['cart'].items()):
                c_a, c_b = st.columns([4, 1])
                c_a.write(f"**{it}** - {d['q']} x {d['p']}$")
                if c_b.button("❌", key=f"del_{it}"):
                    del st.session_state.session['cart'][it]; st.rerun()
            
            with st.form("validation_vente"):
                nom_cli = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                montant_recu = st.number_input(f"MONTANT REÇU ({devise_v})", value=float(t_final))
                
                if st.form_submit_button("💰 VALIDER ET IMPRIMER"):
                    ref_v = f"FAC-{random.randint(1000,9999)}"
                    # Conversion en USD pour la base de données
                    recu_usd = montant_recu if devise_v == "USD" else montant_recu / sh_inf[1]
                    reste_usd = t_usd - recu_usd
                    
                    with sqlite3.connect(DB_FILE) as conn:
                        # 1. Enregistrer la vente
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref_v, nom_cli, t_usd, recu_usd, reste_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise_v))
                        
                        # 2. Déduire le stock
                        for it, d in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                        
                        # 3. Créer une dette si reste > 0
                        if reste_usd > 0.05:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)",
                                         (nom_cli, reste_usd, ref_v, sid, datetime.now().strftime("%d/%m/%Y")))
                        
                        conn.commit()
                    
                    st.session_state.session['viewing_invoice'] = {
                        'ref': ref_v, 'cli': nom_cli, 'total_val': t_final, 'dev': devise_v, 
                        'items': st.session_state.session['cart'].copy(), 'date': datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    st.session_state.session['cart'] = {}
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 7.3 STOCK & PRODUITS (MODIFICATION SANS SUPPRESSION v192) ---
elif choice == "📦 STOCK & PRODUITS":
    st.header("📦 GESTION DES ARTICLES")
    
    with sqlite3.connect(DB_FILE) as conn:
        items = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        
        # Liste des produits existants
        for i_id, i_n, i_q, i_b, i_s in items:
            with st.expander(f"📦 {i_n} | Stock: {i_q} | Prix: {i_s}$"):
                col1, col2 = st.columns(2)
                new_q = col1.number_input("Modifier Quantité", value=i_q, key=f"upq_{i_id}")
                new_s = col2.number_input("Modifier Prix Vente ($)", value=float(i_s), key=f"ups_{i_id}")
                
                if st.button("💾 ENREGISTRER MODIFS", key=f"btns_{i_id}"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_s, i_id))
                    conn.commit(); st.rerun()
                
                if st.button("🗑️ SUPPRIMER L'ARTICLE", key=f"btnd_{i_id}"):
                    conn.execute("DELETE FROM inventory WHERE id=?", (i_id,))
                    conn.commit(); st.rerun()
        
        st.divider()
        st.subheader("🆕 AJOUTER UN NOUVEAU PRODUIT")
        with st.form("new_p"):
            n_name = st.text_input("Désignation de l'article").upper()
            n_qty = st.number_input("Quantité Initiale", 1)
            n_buy = st.number_input("Prix d'Achat Unitaire ($)", 0.0)
            n_sell = st.number_input("Prix de Vente Unitaire ($)", 0.0)
            if st.form_submit_button("📥 AJOUTER AU STOCK"):
                conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)",
                             (n_name, n_qty, n_buy, n_sell, sid))
                conn.commit(); st.rerun()

# --- 7.4 GESTION DES DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 GESTION DES DETTES":
    st.header("📉 SUIVI DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance, sale_ref, last_update FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        
        if not dettes:
            st.info("Aucune dette enregistrée.")
        
        for d_id, d_cli, d_bal, d_ref, d_date in dettes:
            with st.expander(f"👤 {d_cli} | Reste : {d_bal:,.2f} $ | (Ref: {d_ref})"):
                st.write(f"Dernière mise à jour : {d_date}")
                tranche = st.number_input("Montant de la tranche ($)", 0.1, float(d_bal), key=f"tr_{d_id}")
                
                if st.button("✅ VALIDER LE PAIEMENT", key=f"btn_tr_{d_id}"):
                    n_balance = d_bal - tranche
                    # Enregistrer le paiement
                    conn.execute("INSERT INTO debt_payments (debt_id, amount, date, sid) VALUES (?,?,?,?)",
                                 (d_id, tranche, datetime.now().strftime("%d/%m/%Y"), sid))
                    
                    # Mettre à jour la dette
                    if n_balance <= 0.05:
                        conn.execute("UPDATE debts SET balance=0, status='SOLDE', last_update=? WHERE id=?", 
                                     (datetime.now().strftime("%d/%m/%Y"), d_id))
                        st.success(f"Dette de {d_cli} entièrement soldée et retirée de la liste !")
                    else:
                        conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", 
                                     (n_balance, datetime.now().strftime("%d/%m/%Y"), d_id))
                        st.info(f"Tranche reçue. Nouveau reste : {n_balance:,.2f} $")
                    
                    conn.commit()
                    time.sleep(1)
                    st.rerun()

# --- 7.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 SORTIES DE CAISSE")
    with st.form("dep_form"):
        motif = st.text_input("Motif de la dépense")
        montant_d = st.number_input("Montant ($)", 0.1)
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)",
                             (motif, montant_d, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.success("Dépense enregistrée."); st.rerun()
    
    st.divider()
    with sqlite3.connect(DB_FILE) as conn:
        df_dep = pd.read_sql(f"SELECT date, label as Motif, amount as 'Montant $' FROM expenses WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.table(df_dep.head(10))

# --- 7.6 RAPPORTS (v197 requirement) ---
elif choice == "📊 RAPPORTS VENTES":
    st.header("📊 HISTORIQUE ET RAPPORTS")
    with sqlite3.connect(DB_FILE) as conn:
        df_sales = pd.read_sql(f"SELECT date, time, ref, cli as Client, total_usd as 'Total $', seller as Vendeur FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df_sales, use_container_width=True)
        
        # Export
        csv = df_sales.to_csv(index=False).encode('utf-8')
        st.download_button("📥 TÉLÉCHARGER LE RAPPORT (CSV)", csv, "rapport_ventes.csv", "text/csv")

# --- 7.7 ÉQUIPE (VENDEURS) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name, status FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n, v_s in vendeurs:
            with st.expander(f"👤 {v_n} ({v_id})"):
                if st.button(f"Supprimer {v_n}", key=f"dv_{v_id}"):
                    conn.execute("DELETE FROM users WHERE uid=?", (v_id,))
                    conn.commit(); st.rerun()
        
        st.divider()
        with st.form("new_v"):
            st.write("AJOUTER UN VENDEUR")
            nv_id = st.text_input("Identifiant Vendeur")
            nv_name = st.text_input("Nom Complet")
            nv_pass = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                try:
                    conn.execute("INSERT INTO users (uid, pwd, role, shop, status, name) VALUES (?,?,?,?,?,?)",
                                 (nv_id.lower(), get_hash(nv_pass), 'VENDEUR', sid, 'ACTIF', nv_name))
                    conn.commit(); st.success("Vendeur ajouté !"); st.rerun()
                except: st.error("Identifiant déjà utilisé.")

# --- 7.8 RÉGLAGES (MAINTENANCE & BACKUP) ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("shop_settings"):
        n_name = st.text_input("Nom de l'Etablissement", sh_inf[0])
        n_head = st.text_area("En-tête des Factures", sh_inf[4])
        n_rate = st.number_input("Taux de change (1 USD = ? CDF)", value=sh_inf[1])
        n_addr = st.text_input("Adresse Physique", sh_inf[2])
        n_tel = st.text_input("Téléphone Contact", sh_inf[3])
        if st.form_submit_button("💾 SAUVEGARDER LES PARAMÈTRES"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, head=?, rate=?, addr=?, tel=? WHERE sid=?", 
                             (n_name, n_head, n_rate, n_addr, n_tel, sid))
                conn.commit(); st.success("Paramètres mis à jour !"); st.rerun()
    
    st.divider()
    st.subheader("🛠️ MAINTENANCE")
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        if st.button("⚠️ RÉINITIALISER LE STOCK"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE inventory SET qty=0 WHERE sid=?", (sid,))
                conn.commit(); st.warning("Stock vidé !"); st.rerun()
    with c_m2:
        with open(DB_FILE, "rb") as f:
            st.download_button("📥 TÉLÉCHARGER BACKUP DB", f, file_name=f"backup_erp_{sid}.db")

# --- 7.9 DÉCONNEXION ---
elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False
    st.rerun()

# ------------------------------------------------------------------------------
# 8. PIED DE PAGE ET INFOS VERSION
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.caption(f"Version : 3.8.0 Stable")
st.sidebar.caption(f"© Balika Business 2026")
st.sidebar.caption(f"Connecté : {st.session_state.session['user'].upper()}")
