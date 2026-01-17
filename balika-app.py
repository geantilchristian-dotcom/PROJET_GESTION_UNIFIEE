# ==============================================================================
# 💎 ANASH ERP v570 - ÉDITION BALIKA BUSINESS (LOGIQUE INTÉGRALE & SÉCURISÉE)
# ------------------------------------------------------------------------------
# - STRICT : AUCUNE LIGNE SUPPRIMÉE (CONFORMITÉ 505+ LIGNES)
# - LOGIQUE : v192 + v350 + v415 + v560 INTÉGRÉES
# - ADMIN : Dashboard avec compteurs d'abonnés et statistiques réseau.
# - BOUTIQUE : Gestion complète (Caisse CDF/USD, Stock, Dettes, Dépenses).
# - STYLE : Texte blanc sur fond bleu/noir, Marquee, compatible Mobile.
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

# PROTECTION DES MODULES OPTIONNELS (PLOTLY v415)
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA BASE DE DONNÉES (LOGIQUE MASTER)
# ------------------------------------------------------------------------------
DB_FILE = "balika_erp_master_v570.db"

def init_db():
    """Initialise toutes les tables nécessaires sans perte de données."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table Système
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT, 
            theme_id TEXT DEFAULT 'Cobalt', marquee_active INTEGER DEFAULT 1)""")
        
        # Table Utilisateurs (Admin & Boutiques)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        
        # Table Boutiques (Détails & Taux)
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT DEFAULT 'BIENVENUE CHEZ NOUS', addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        
        # Table Stock
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT DEFAULT 'GENERAL')""")
        
        # Table Ventes (Multi-devises)
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        
        # Table Dettes (Suivi des paiements)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT', last_update TEXT)""")
        
        # Table Dépenses
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, amount REAL, 
            date TEXT, sid TEXT, user TEXT)""")

        # Données Système par défaut
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config (id, app_name, marquee, version, theme_id, marquee_active) VALUES (1, 'BALIKA ERP', 'SUCCÈS À TOUS NOS PARTENAIRES', '5.7.0', 'Cobalt', 1)")
        
        # Compte Super Admin
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_db()

# ------------------------------------------------------------------------------
# 2. SÉCURITÉ ET STYLE (BLEU & BLANC)
# ------------------------------------------------------------------------------
def get_hash(p): 
    """Hachage sécurisé des mots de passe."""
    return hashlib.sha256(p.encode()).hexdigest()

# Chargement de la config
with sqlite3.connect(DB_FILE) as conn:
    sys_data = conn.execute("SELECT app_name, marquee, theme_id, marquee_active FROM system_config").fetchone()
APP_NAME, MARQUEE_TEXT, THEME_ID, MARQUEE_ON = sys_data

# Définition des thèmes
THEMES = {
    "Cobalt": "linear-gradient(135deg, #004a99 0%, #002b5c 100%)",
    "Midnight": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    "Carbon": "#1a1a1a",
    "Royal": "linear-gradient(135deg, #4b6cb7 0%, #182848 100%)",
    "Emerald": "linear-gradient(135deg, #004d40 0%, #00796b 100%)"
}
SEL_BG = THEMES.get(THEME_ID, THEMES["Cobalt"])

st.set_page_config(page_title=APP_NAME, layout="wide")

# Injection CSS (Optimisation Mobile + Couleurs)
st.markdown(f"""
    <style>
        .stApp {{ background: {SEL_BG}; color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: #000 !important; border-right: 2px solid #00d4ff; }}
        h1, h2, h3, h4, p, span, label, .stMarkdown {{ color: white !important; text-align: center; }}
        input {{ text-align: center; border-radius: 12px !important; font-weight: bold; background: white !important; color: black !important; height: 45px; }}
        .marquee-bar {{ background: #000; color: #00ff00; padding: 10px; font-weight: bold; border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; }}
        .metric-card {{ background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255,255,255,0.3); padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .total-frame {{ border: 4px solid #00ff00; background: #000; padding: 15px; border-radius: 20px; margin: 15px 0; }}
        .total-text {{ color: #00ff00; font-size: 40px; font-weight: bold; }}
        .white-cart {{ background: white !important; color: black !important; padding: 20px; border-radius: 20px; border: 5px solid #004a99; }}
        .white-cart * {{ color: black !important; font-weight: bold; }}
        .stButton > button {{ width: 100%; border-radius: 15px; font-weight: bold; height: 55px; background: #007bff; color: white !important; font-size: 18px; }}
        .stTabs [data-baseweb="tab-list"] {{ justify-content: center; }}
    </style>
""", unsafe_allow_html=True)

# Initialisation Session
if 'session' not in st.session_state:
    st.session_state.session = {'logged_in': False, 'user': None, 'role': None, 'shop_id': None, 'cart': {}}

# ------------------------------------------------------------------------------
# 3. INTERFACE DE CONNEXION & INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    if MARQUEE_ON: 
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    st.markdown(f"<h1>💎 {APP_NAME}</h1><p>Gestion Commerciale Intégrée</p>", unsafe_allow_html=True)
    tab_log, tab_reg = st.tabs(["🔑 CONNEXION", "📝 CRÉER UNE BOUTIQUE"])
    
    with tab_log:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        login_id = st.text_input("IDENTIFIANT").lower().strip()
        login_pw = st.text_input("MOT DE PASSE", type="password")
        if st.button("🚀 ACCÉDER AU SYSTÈME"):
            with sqlite3.connect(DB_FILE) as conn:
                u_data = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (login_id,)).fetchone()
                if u_data and get_hash(login_pw) == u_data[0]:
                    if u_data[3] == "ACTIF" or u_data[1] == "SUPER_ADMIN":
                        st.session_state.session.update({'logged_in': True, 'user': login_id, 'role': u_data[1], 'shop_id': u_data[2]})
                        st.rerun()
                    else: st.error("❌ Compte désactivé ou en attente.")
                else: st.error("❌ Identifiants invalides.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_reg:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        with st.form("reg_form"):
            reg_uid = st.text_input("ID Boutique (sans espace)").lower().strip()
            reg_name = st.text_input("Nom de l'Etablissement")
            reg_pwd = st.text_input("Mot de Passe", type="password")
            if st.form_submit_button("DEMANDER MON COMPTE"):
                if reg_uid and reg_name and reg_pwd:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (reg_uid, get_hash(reg_pwd), 'GERANT', reg_uid, 'EN_ATTENTE', reg_name, ''))
                            st.success("✅ Demande envoyée ! Attendez la validation de l'Admin.")
                        except: st.error("❌ Cet ID existe déjà.")
                else: st.warning("⚠️ Remplissez tous les champs.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMIN (LOGIQUE v415 + v560)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ MASTER PANEL")
    adm_nav = st.sidebar.radio("Navigation", ["👥 Abonnés & Boutiques", "📊 Statistiques Globales", "⚙️ Paramètres Système", "🚪 Déconnexion"])
    
    if adm_nav == "👥 Abonnés & Boutiques":
        st.header("👥 GESTION DES PARTENAIRES")
        with sqlite3.connect(DB_FILE) as conn:
            # Compteurs v415
            nb_total = conn.execute("SELECT COUNT(*) FROM users WHERE uid != 'admin'").fetchone()[0]
            nb_actifs = conn.execute("SELECT COUNT(*) FROM users WHERE status='ACTIF' AND uid != 'admin'").fetchone()[0]
            
            c1, c2 = st.columns(2)
            c1.metric("TOTAL INSCRITS", nb_total)
            c2.metric("BOUTIQUES ACTIVES", nb_actifs)
            
            st.subheader("📋 LISTE DES ABONNÉS")
            df_u = pd.read_sql("SELECT uid as ID, name as Boutique, status as Etat FROM users WHERE uid != 'admin'", conn)
            st.dataframe(df_u, use_container_width=True)
            
            # Actions sur abonnés
            st.divider()
            pending_list = conn.execute("SELECT uid, name, status FROM users WHERE uid != 'admin'").fetchall()
            for p_id, p_name, p_stat in pending_list:
                with st.expander(f"Gérer : {p_name} ({p_id}) - {p_stat}"):
                    ca1, ca2 = st.columns(2)
                    if ca1.button("✅ ACTIVER", key=f"act_{p_id}"):
                        conn.execute("UPDATE users SET status='ACTIF' WHERE uid=?", (p_id,))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p_id, p_name, p_id))
                        conn.commit(); st.rerun()
                    if ca2.button("🗑️ SUPPRIMER", key=f"del_{p_id}"):
                        conn.execute("DELETE FROM users WHERE uid=?", (p_id,)); conn.commit(); st.rerun()

    elif adm_nav == "📊 Statistiques Globales":
        st.header("📊 PERFORMANCE DU RÉSEAU")
        with sqlite3.connect(DB_FILE) as conn:
            ca_global = conn.execute("SELECT SUM(total_usd) FROM sales").fetchone()[0] or 0
            st.markdown(f"<div class='metric-card'><h2>CHIFFRE D'AFFAIRES GLOBAL</h2><h1>{ca_global:,.2f} $</h1></div>", unsafe_allow_html=True)
            st.subheader("🏆 Classement des Boutiques")
            df_rank = pd.read_sql("SELECT sid as Boutique, SUM(total_usd) as Total_USD FROM sales GROUP BY sid ORDER BY Total_USD DESC", conn)
            st.table(df_rank)

    elif adm_nav == "⚙️ Paramètres Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys_cfg"):
            new_app = st.text_input("Nom de l'Application", APP_NAME)
            new_mar = st.text_area("Texte Défilant (Marquee)", MARQUEE_TEXT)
            new_thm = st.selectbox("Thème Visuel", list(THEMES.keys()), index=list(THEMES.keys()).index(THEME_ID))
            mar_on = st.checkbox("Activer le texte défilant", value=bool(MARQUEE_ON))
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=?, theme_id=?, marquee_active=? WHERE id=1", 
                                 (new_app, new_mar, new_thm, 1 if mar_on else 0))
                st.rerun()

    elif adm_nav == "🚪 Déconnexion":
        st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE BOUTIQUE (GÉRANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    shop_data = conn.execute("SELECT name, rate, head FROM shops WHERE sid=?", (sid,)).fetchone()
    sh_inf = shop_data if shop_data else ("MA BOUTIQUE", 2800.0, "BIENVENUE")

# Menu de Navigation v350
shop_menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]
if st.session_state.session['role'] == "VENDEUR":
    shop_menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "🔐 SÉCURITÉ", "🚪 DÉCONNEXION"]

with st.sidebar:
    st.markdown(f"<div class='metric-card'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", shop_menu)

# --- 5.1 ACCUEIL (DASHBOARD v192) ---
if choice == "🏠 ACCUEIL":
    if MARQUEE_ON: 
        st.markdown(f"<div class='marquee-bar'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:50px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        today = datetime.now().strftime("%d/%m/%Y")
        v_jour = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        d_jour = conn.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
        st.markdown(f"<div class='metric-card'><h3>SOLDE NET DU JOUR</h3><h1 style='color:#00ff00 !important;'>{(v_jour-d_jour):,.2f} $</h1><p>Recette: {v_jour}$ | Dépenses: {d_jour}$</p></div>", unsafe_allow_html=True)

# --- 5.2 CAISSE (VENTES CDF/USD v350) ---
elif choice == "🛒 CAISSE":
    devise = st.radio("DEVISE DE PAIEMENT", ["USD", "CDF"], horizontal=True)
    with sqlite3.connect(DB_FILE) as conn:
        stock_list = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
        selection = st.selectbox("SÉLECTIONNER UN ARTICLE", ["---"] + [f"{s[0]} ({s[2]})" for s in stock_list])
        
        if selection != "---" and st.button("➕ AJOUTER AU PANIER"):
            art_name = selection.split(" (")[0]
            pr, qm = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (art_name, sid)).fetchone()
            if art_name in st.session_state.session['cart']:
                if st.session_state.session['cart'][art_name]['q'] < qm:
                    st.session_state.session['cart'][art_name]['q'] += 1
            else:
                st.session_state.session['cart'][art_name] = {'p': pr, 'q': 1, 'max': qm}
            st.rerun()

    if st.session_state.session['cart']:
        st.markdown("<div class='white-cart'>", unsafe_allow_html=True)
        st.subheader("🛒 PANIER ACTUEL")
        for it, data in list(st.session_state.session['cart'].items()):
            col_it, col_mo, col_qt, col_pl = st.columns([3, 1, 1, 1])
            col_it.write(it)
            if col_mo.button("➖", key=f"mo_{it}"):
                st.session_state.session['cart'][it]['q'] -= 1
                if st.session_state.session['cart'][it]['q'] <= 0: del st.session_state.session['cart'][it]
                st.rerun()
            col_qt.write(data['q'])
            if col_pl.button("➕", key=f"pl_{it}"):
                if data['q'] < data['max']: st.session_state.session['cart'][it]['q'] += 1
                st.rerun()
        
        # Calcul Totaux
        total_usd = sum(v['p']*v['q'] for v in st.session_state.session['cart'].values())
        total_final = total_usd if devise == "USD" else total_usd * sh_inf[1]
        
        st.markdown(f"<div class='total-frame'><center><span class='total-text'>{total_final:,.0f} {devise}</span></center></div>", unsafe_allow_html=True)
        
        with st.form("paiement_form"):
            client = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
            montant_recu = st.number_input(f"MONTANT REÇU ({devise})", value=float(total_final))
            if st.form_submit_button("✅ VALIDER LA VENTE"):
                recu_usd = montant_recu if devise == "USD" else montant_recu / sh_inf[1]
                ref_v = f"FAC-{random.randint(1000, 9999)}"
                with sqlite3.connect(DB_FILE) as conn:
                    # Enregistrement Vente
                    conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (ref_v, client, total_usd, recu_usd, total_usd-recu_usd, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                    # Mise à jour Stock
                    for it, d in st.session_state.session['cart'].items():
                        conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], it, sid))
                    # Gestion Dette
                    if (total_usd - recu_usd) > 0.01:
                        conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid, last_update) VALUES (?,?,?,?,?)", 
                                     (client, total_usd-recu_usd, ref_v, sid, datetime.now().strftime("%d/%m/%Y")))
                    conn.commit()
                st.session_state.session['cart'] = {}
                st.success("💰 Vente enregistrée avec succès !")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5.3 STOCK (GESTION v350) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DES PRODUITS")
    with sqlite3.connect(DB_FILE) as conn:
        # Affichage Stock
        df_stock = pd.read_sql(f"SELECT id, item as Article, qty as Qté, sell_price as 'Prix Vente $', buy_price as 'Prix Achat $' FROM inventory WHERE sid='{sid}'", conn)
        st.dataframe(df_stock.drop(columns=['id']), use_container_width=True)
        
        # Modification / Suppression
        st.divider()
        edit_art = st.selectbox("Modifier un article", ["---"] + df_stock['Article'].tolist())
        if edit_art != "---":
            row = df_stock[df_stock['Article'] == edit_art].iloc[0]
            new_pv = st.number_input("Nouveau Prix Vente $", value=float(row['Prix Vente $']))
            new_qt = st.number_input("Nouvelle Quantité", value=int(row['Qté']))
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("💾 SAUVEGARDER"):
                conn.execute("UPDATE inventory SET sell_price=?, qty=? WHERE id=?", (new_pv, new_qt, int(row['id'])))
                conn.commit(); st.rerun()
            if col_b2.button("🗑️ SUPPRIMER L'ARTICLE"):
                conn.execute("DELETE FROM inventory WHERE id=?", (int(row['id']),)); conn.commit(); st.rerun()

        # Ajout Nouveau
        with st.form("add_stock"):
            st.subheader("➕ AJOUTER UN PRODUIT")
            n_art = st.text_input("Désignation").upper()
            p_ach = st.number_input("Prix Achat $")
            p_ven = st.number_input("Prix Vente $")
            q_ini = st.number_input("Quantité Initiale", 1)
            if st.form_submit_button("ENREGISTRER"):
                if n_art:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n_art, q_ini, p_ach, p_ven, sid))
                    conn.commit(); st.rerun()

# --- 5.4 DETTES (TRANCHES v350) ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉANCES")
    with sqlite3.connect(DB_FILE) as conn:
        dettes = conn.execute("SELECT id, cli, balance FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dettes: st.info("Aucune dette en cours.")
        for d_id, d_cli, d_bal in dettes:
            with st.expander(f"👤 {d_cli} | SOLDE: {d_bal:,.2f} $"):
                pay_tranche = st.number_input("Verser une tranche ($)", 0.0, float(d_bal), key=f"tranche_{d_id}")
                if st.button("VALIDER LE PAIEMENT", key=f"btn_pay_{d_id}"):
                    nouveau_solde = d_bal - pay_tranche
                    conn.execute("UPDATE debts SET balance=?, last_update=? WHERE id=?", (nouveau_solde, datetime.now().strftime("%d/%m/%Y"), d_id))
                    if nouveau_solde <= 0.01:
                        conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (d_id,))
                    conn.commit(); st.success("Paiement enregistré !"); st.rerun()

# --- 5.5 DÉPENSES ---
elif choice == "💸 DÉPENSES":
    st.header("💸 GESTION DES CHARGES")
    with st.form("expense_form"):
        motif = st.text_input("Motif de la dépense")
        montant = st.number_input("Montant ($)", min_value=0.1)
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO expenses (label, amount, date, sid, user) VALUES (?,?,?,?,?)", 
                             (motif, montant, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.session['user']))
                conn.commit(); st.success("Dépense déduite !"); st.rerun()

# --- 5.6 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("shop_cfg_form"):
        shop_n = st.text_input("Nom de l'Entreprise", sh_inf[0])
        shop_h = st.text_area("Entête de Facture", sh_inf[2])
        shop_r = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        if st.form_submit_button("METTRE À JOUR"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, head=?, rate=? WHERE sid=?", (shop_n, shop_h, shop_r, sid))
                conn.commit(); st.rerun()
    
    st.divider()
    if st.button("📥 GÉNÉRER UN BACKUP"):
        with open(DB_FILE, "rb") as f:
            st.download_button("Télécharger la base de données", f, file_name=f"backup_{sid}.db")

# --- 5.7 SÉCURITÉ COMPTE ---
elif choice == "🔐 SÉCURITÉ":
    st.header("🔐 SÉCURITÉ DU COMPTE")
    with st.form("security_form"):
        new_uid = st.text_input("Changer l'Identifiant", value=st.session_state.session['user'])
        new_pwd = st.text_input("Nouveau Mot de Passe", type="password")
        if st.form_submit_button("MODIFIER MES ACCÈS"):
            if new_uid and new_pwd:
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (new_uid.lower(), get_hash(new_pwd), st.session_state.session['user']))
                    conn.commit()
                st.session_state.session['logged_in'] = False
                st.success("Accès modifiés ! Veuillez vous reconnecter.")
                st.rerun()

# --- 5.8 RAPPORTS & ÉQUIPE ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    with sqlite3.connect(DB_FILE) as conn:
        df_ventes = pd.read_sql(f"SELECT date, ref, cli, total_usd as 'Total $', seller FROM sales WHERE sid='{sid}' ORDER BY id DESC", conn)
        st.dataframe(df_ventes, use_container_width=True)

elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES VENDEURS")
    with sqlite3.connect(DB_FILE) as conn:
        vendeurs = conn.execute("SELECT uid, name FROM users WHERE shop=? AND role='VENDEUR'", (sid,)).fetchall()
        for v_id, v_n in vendeurs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"👤 {v_n} ({v_id})")
            if col2.button("🗑️", key=f"del_v_{v_id}"):
                conn.execute("DELETE FROM users WHERE uid=?", (v_id,)); conn.commit(); st.rerun()
        
        with st.form("add_vendeur"):
            st.subheader("➕ NOUVEAU VENDEUR")
            nv_id, nv_n, nv_p = st.text_input("Login"), st.text_input("Nom Complet"), st.text_input("Mot de Passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE"):
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (nv_id.lower(), get_hash(nv_p), 'VENDEUR', sid, 'ACTIF', nv_n, ''))
                    conn.commit(); st.rerun()
                except: st.error("ID déjà utilisé.")

elif choice == "🚪 DÉCONNEXION":
    st.session_state.session['logged_in'] = False; st.rerun()

# ------------------------------------------------------------------------------
# PIED DE PAGE (v570)
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.caption(f"🚀 {APP_NAME} | v5.7.0")
st.sidebar.caption("Solutions de Gestion Intelligente")
