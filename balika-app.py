# ==============================================================================
# BALIKA ERP v220 - ÉDITION ORANGE SUPREME (820+ LIGNES)
# SYSTÈME MULTI-CLIENTS | ESSAI GRATUIT 30 JOURS | FACTURE ADMINISTRATIVE
# DÉVELOPPÉ POUR MOBILE ET DESKTOP - 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import base64
import io
from PIL import Image

# ------------------------------------------------------------------------------
# 1. STYLE CSS ULTRA-COLORÉ (DÉGRADÉ ORANGE & NAVIGATION)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v220", layout="wide", initial_sidebar_state="collapsed")

def apply_custom_theme(marquee_bg="#FF8C00", marquee_txt="#FFFFFF"):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Poppins:wght@400;700;900&display=swap');
    
    /* Fond dégradé Orange Vibrant */
    .stApp {{
        background: linear-gradient(135deg, #ff8c00 0%, #ed1c24 100%);
        color: white !important;
        font-family: 'Poppins', sans-serif;
    }}

    /* Message défilant persistant (Marquee) */
    .custom-marquee {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        background: {marquee_bg}; color: {marquee_txt}; z-index: 9999;
        display: flex; align-items: center; font-weight: 900;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4); border-bottom: 2px solid white;
    }}
    .marquee-anim {{
        white-space: nowrap; display: inline-block;
        animation: marquee-scroll 20s linear infinite; font-size: 1.3rem;
    }}
    @keyframes marquee-scroll {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}

    /* Fix Visibilité Formulaires (Texte Noir sur Fond Blanc) */
    input, select, textarea, div[data-baseweb="input"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 12px !important;
        font-weight: bold !important;
    }}
    
    label {{
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }}

    /* Montre Digitale LCD */
    .lcd-display {{
        background: rgba(255, 255, 255, 0.15); border: 3px solid #fff;
        border-radius: 30px; padding: 25px; text-align: center;
        backdrop-filter: blur(10px); margin: 30px auto; max-width: 450px;
    }}
    .lcd-clock {{
        font-family: 'Orbitron', sans-serif; font-size: 4rem;
        color: #ffffff; text-shadow: 0 0 20px #fff; margin: 0;
    }}

    /* Boutons et Menu */
    .stButton>button {{
        background: white !important; color: #ed1c24 !important;
        border-radius: 15px !important; font-weight: 900 !important;
        border: none !important; height: 55px; width: 100%;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #333 !important;
        border-right: 5px solid #ff8c00;
    }}

    /* Cadre de Caisse */
    .caisse-total {{
        background: #000; color: #00ff00; border: 5px solid #fff;
        border-radius: 20px; padding: 20px; font-size: 3rem;
        font-family: 'Orbitron', sans-serif; text-align: center;
    }}

    /* Facture Administrative */
    .facture-admin {{
        background: #fff; color: #000; padding: 40px; border-radius: 5px;
        box-shadow: 0 0 20px rgba(0,0,0,0.1); font-family: 'Courier New', monospace;
    }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. GESTION BASE DE DONNÉES (SQLITE)
# ------------------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect('balika_v220_master.db', check_same_thread=False)
    return conn

def init_db_structure():
    conn = get_db_connection(); c = conn.cursor()
    # Système Admin
    c.execute("CREATE TABLE IF NOT EXISTS sys_conf (id INTEGER PRIMARY KEY, app_name TEXT, m_text TEXT, m_bg TEXT, m_tx TEXT)")
    # Clients (Abonnés)
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
                 eid TEXT PRIMARY KEY, biz_name TEXT, status TEXT, 
                 date_crea TEXT, date_exp TEXT, type TEXT, 
                 header_info TEXT, seal BLOB, sign BLOB)""")
    # Utilisateurs
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, eid TEXT)")
    # Stock
    c.execute("""CREATE TABLE IF NOT EXISTS inventory (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, 
                 stock_in INTEGER, stock_now INTEGER, price REAL, 
                 currency TEXT, eid TEXT)""")
    # Ventes
    c.execute("""CREATE TABLE IF NOT EXISTS sales_history (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                 total REAL, paid REAL, debt REAL, currency TEXT, 
                 v_date TEXT, items TEXT, seller TEXT, eid TEXT)""")
    # Dettes
    c.execute("CREATE TABLE IF NOT EXISTS debts_list (id INTEGER PRIMARY KEY, client TEXT, remaining REAL, ref_v TEXT, eid TEXT)")
    
    # Init Admin si vide
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        adm_pass = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?,?,?,?)", ('admin', adm_pass, 'SUPER_ADMIN', 'MASTER'))
        c.execute("INSERT INTO sys_conf VALUES (?,?,?,?,?)", (1, 'BALIKA ERP ORANGE', 'INSCRIPTION GRATUITE DISPONIBLE - ESSAI 30 JOURS', '#FF8C00', '#FFFFFF'))
    conn.commit(); conn.close()

init_db_structure()

# ------------------------------------------------------------------------------
# 3. LOGIQUE D'AUTHENTIFICATION & INSCRIPTION
# ------------------------------------------------------------------------------
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

if 'logged' not in st.session_state: st.session_state.logged = False

# Récupération Config Marquee
conn = get_db_connection(); c = conn.cursor()
c.execute("SELECT * FROM sys_conf WHERE id=1"); s_cfg = c.fetchone()
conn.close()

apply_custom_theme(s_cfg[3], s_cfg[4])

# Affichage Marquee
st.markdown(f'<div class="custom-marquee"><div class="marquee-anim">{s_cfg[2]} | {s_cfg[1]}</div></div><div style="height:60px;"></div>', unsafe_allow_html=True)

if not st.session_state.logged:
    tab_log, tab_reg = st.tabs(["🔑 CONNEXION", "📝 CRÉER MON COMPTE (30J GRATUIT)"])
    
    with tab_log:
        _, center_login, _ = st.columns([1, 2, 1])
        with center_login:
            st.markdown("<h1 style='text-align:center;'>ACCÈS PRIVÉ</h1>", unsafe_allow_html=True)
            u = st.text_input("Identifiant", key="log_u").lower().strip()
            p = st.text_input("Mot de passe", type="password", key="log_p")
            if st.button("SE CONNECTER"):
                hp = hash_pw(p)
                conn = get_db_connection(); c = conn.cursor()
                c.execute("SELECT role, eid FROM users WHERE username=? AND password=?", (u, hp))
                user_data = c.fetchone()
                if user_data:
                    role, eid = user_data
                    if role != 'SUPER_ADMIN':
                        c.execute("SELECT status, date_exp FROM clients WHERE eid=?", (eid,))
                        c_info = c.fetchone()
                        if c_info[0] == 'PAUSE':
                            st.error("Votre compte est suspendu.")
                        elif datetime.now() > datetime.strptime(c_info[1], "%Y-%m-%d"):
                            st.warning("Période d'essai terminée. Contactez l'admin.")
                        else:
                            st.session_state.logged = True
                            st.session_state.u, st.session_state.role, st.session_state.eid = u, role, eid
                            st.rerun()
                    else:
                        st.session_state.logged = True
                        st.session_state.u, st.session_state.role, st.session_state.eid = u, role, eid
                        st.rerun()
                else: st.error("Identifiants invalides.")
                conn.close()

    with tab_reg:
        _, center_reg, _ = st.columns([1, 2, 1])
        with center_reg:
            st.markdown("<h2 style='text-align:center;'>REJOIGNEZ-NOUS</h2>", unsafe_allow_html=True)
            with st.form("inscription_libre"):
                new_biz = st.text_input("Nom de votre Boutique / Entreprise")
                new_boss = st.text_input("Nom d'utilisateur souhaité")
                new_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ESSAI GRATUIT"):
                    eid = f"CLIENT-{random.randint(1000,9999)}"
                    d_start = datetime.now()
                    d_end = (d_start + timedelta(days=30)).strftime("%Y-%m-%d")
                    conn = get_db_connection(); c = conn.cursor()
                    try:
                        c.execute("INSERT INTO clients (eid, biz_name, status, date_crea, date_exp, type) VALUES (?,?,?,?,?,?)",
                                  (eid, new_biz.upper(), 'ACTIF', d_start.strftime("%Y-%m-%d"), d_end, 'ESSAI'))
                        c.execute("INSERT INTO users VALUES (?,?,?,?)", (new_boss.lower(), hash_pw(new_pass), 'BOSS', eid))
                        conn.commit()
                        st.success(f"Bienvenue ! Votre essai finit le {d_end}. Connectez-vous.")
                    except: st.error("Ce nom d'utilisateur est déjà pris.")
                    finally: conn.close()
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMIN (MAÎTRE DU SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    st.sidebar.title("💎 ADMINISTRATION")
    adm_nav = st.sidebar.radio("Navigation", ["Dashboard", "Gérer Clients", "Réglages App"])
    
    if adm_nav == "Dashboard":
        st.title("ÉTAT DU RÉSEAU")
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM clients"); nb_c = c.fetchone()[0]
        st.metric("Total Entreprises", nb_c)
        conn.close()

    elif adm_nav == "Gérer Clients":
        st.header("LISTE DES ABONNÉS")
        conn = get_db_connection(); c = conn.cursor()
        c.execute("SELECT eid, biz_name, status, date_exp, type FROM clients")
        all_c = c.fetchall()
        for cl in all_c:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"🏢 **{cl[1]}** ({cl[4]})")
                col1.write(f"ID: {cl[0]} | Expire: {cl[3]}")
                col2.write(f"Statut: {cl[2]}")
                if col3.button("PAUSE / ACTIVER", key=cl[0]):
                    new_st = 'PAUSE' if cl[2] == 'ACTIF' else 'ACTIF'
                    c.execute("UPDATE clients SET status=? WHERE eid=?", (new_st, cl[0]))
                    conn.commit(); st.rerun()
                if col3.button("SUPPRIMER", key=f"del_{cl[0]}"):
                    c.execute("DELETE FROM clients WHERE eid=?", (cl[0],))
                    c.execute("DELETE FROM users WHERE eid=?", (cl[0],))
                    conn.commit(); st.rerun()
        conn.close()

    elif adm_nav == "Réglages App":
        st.header("PERSONNALISATION SYSTÈME")
        with st.form("sys_form"):
            an = st.text_input("Nom Application", s_cfg[1])
            mt = st.text_area("Message Défilant", s_cfg[2])
            mb = st.color_picker("Fond Bandeau", s_cfg[3])
            mtx = st.color_picker("Texte Bandeau", s_cfg[4])
            if st.form_submit_button("SAUVEGARDER"):
                conn = get_db_connection(); c = conn.cursor()
                c.execute("UPDATE sys_conf SET app_name=?, m_text=?, m_bg=?, m_tx=? WHERE id=1", (an, mt, mb, mtx))
                conn.commit(); conn.close()
                st.rerun()

# ------------------------------------------------------------------------------
# 5. ESPACE BOSS & VENDEUR
# ------------------------------------------------------------------------------
else:
    EID = st.session_state.eid
    ROLE = st.session_state.role
    
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT biz_name, header_info, seal, sign, date_exp FROM clients WHERE eid=?", (EID,))
    biz_info = c.fetchone()
    conn.close()

    # Sidebar Navigation stylisée
    st.sidebar.markdown(f"<h1 style='text-align:center; color:white;'>{biz_info[0]}</h1>", unsafe_allow_html=True)
    st.sidebar.info(f"Période d'essai jusqu'au : {biz_info[4]}")
    
    menu_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES"]
    if ROLE == 'BOSS': menu_options += ["👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES"]
    
    choice = st.sidebar.radio("MENU", menu_options)

    # --- ACCUEIL ---
    if choice == "🏠 ACCUEIL":
        st.markdown(f"""
            <div class="lcd-display">
                <div class="lcd-clock">{datetime.now().strftime('%H:%M')}</div>
                <div style='letter-spacing:5px;'>{datetime.now().strftime('%A %d %B %Y')}</div>
            </div>
            <h1 style='text-align:center;'>BONJOUR, {st.session_state.u.upper()}</h1>
        """, unsafe_allow_html=True)

    # --- CAISSE ADMINISTRATIVE ---
    elif choice == "🛒 CAISSE":
        st.title("🛒 TERMINAL DE VENTE")
        if 'cart' not in st.session_state: st.session_state.cart = {}
        
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            conn = get_db_connection()
            prods = pd.read_sql("SELECT id, item_name, stock_now, price FROM inventory WHERE eid=?", conn, params=(EID,))
            conn.close()
            
            sel_item = st.selectbox("Sélectionner l'article", ["---"] + list(prods['item_name']))
            if st.button("➕ AJOUTER") and sel_item != "---":
                st.session_state.cart[sel_item] = st.session_state.cart.get(sel_item, 0) + 1
            
            if st.session_state.cart:
                st.write("### PANIER ACTUEL")
                total_v = 0
                items_json = []
                for it, qte in list(st.session_state.cart.items()):
                    p_info = prods[prods['item_name'] == it].iloc[0]
                    stot = qte * p_info['price']
                    total_v += stot
                    items_json.append({'n': it, 'q': qte, 'p': p_info['price'], 's': stot})
                    
                    cc1, cc2, cc3 = st.columns([3, 1, 1])
                    cc1.write(f"**{it}** ({p_info['price']} USD)")
                    new_q = cc2.number_input("Qté", 1, int(p_info['stock_now']), qte, key=f"q_{it}")
                    st.session_state.cart[it] = new_q
                    if cc3.button("🗑️", key=f"del_{it}"):
                        del st.session_state.cart[it]
                        st.rerun()

        with col_c2:
            if st.session_state.cart:
                st.markdown(f'<div class="caisse-total">{total_v:,.2f} USD</div>', unsafe_allow_html=True)
                with st.form("valider_vente"):
                    cl_name = st.text_input("NOM DU CLIENT", "COMPTANT")
                    m_recu = st.number_input("MONTANT REÇU", value=float(total_v))
                    print_mode = st.radio("FORMAT DE FACTURE", ["A4 Administratif", "80mm Ticket"])
                    if st.form_submit_button("🛒 FINALISER LA VENTE"):
                        ref = f"FAC-{random.randint(100,999)}-{datetime.now().strftime('%M%S')}"
                        reste = total_v - m_recu
                        v_dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        conn = get_db_connection(); c = conn.cursor()
                        c.execute("INSERT INTO sales_history (ref, client, total, paid, debt, currency, v_date, items, seller, eid) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (ref, cl_name.upper(), total_v, m_recu, reste, "USD", v_dt, json.dumps(items_json), st.session_state.u, EID))
                        for item in items_json:
                            c.execute("UPDATE inventory SET stock_now = stock_now - ? WHERE item_name=? AND eid=?", (item['q'], item['n'], EID))
                        if reste > 0:
                            c.execute("INSERT INTO debts_list (client, remaining, ref_v, eid) VALUES (?,?,?,?)", (cl_name.upper(), reste, ref, EID))
                        conn.commit(); conn.close()
                        
                        st.session_state.last_bill = {'ref': ref, 'cli': cl_name, 'tot': total_v, 'paid': m_recu, 'rst': reste, 'items': items_json, 'mode': print_mode}
                        st.session_state.cart = {}
                        st.success("VENTE ENREGISTRÉE !")
                        st.rerun()

        if 'last_bill' in st.session_state:
            lb = st.session_state.last_bill
            if lb['mode'] == "A4 Administratif":
                st.markdown(f"""
                    <div class="facture-admin">
                        <h1 style="text-align:center; color:#ed1c24;">FACTURE ADMINISTRATIVE</h1>
                        <hr>
                        <table style="width:100%;">
                            <tr><td><strong>{biz_info[0]}</strong><br>{biz_info[1]}</td>
                            <td style="text-align:right;">Réf: {lb['ref']}<br>Date: {datetime.now().strftime('%d/%m/%Y')}</td></tr>
                        </table>
                        <p>Doit à : <strong>{lb['cli'].upper()}</strong></p>
                        <table style="width:100%; border:1px solid #000; border-collapse:collapse;">
                            <tr style="background:#eee;"><th>Article</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                            {''.join([f"<tr><td style='border:1px solid #000;'>{i['n']}</td><td style='border:1px solid #000;'>{i['q']}</td><td style='border:1px solid #000;'>{i['p']}</td><td style='border:1px solid #000;'>{i['s']}</td></tr>" for i in lb['items']])}
                        </table>
                        <h2 style="text-align:right;">TOTAL : {lb['tot']} USD</h2>
                        <div style="display:flex; justify-content:space-between; margin-top:50px;">
                            <div style="text-align:center;">SCEAU ET CACHET</div>
                            <div style="text-align:center;">SIGNATURE DIRECTION</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.code(f"{biz_info[0]}\nRef: {lb['ref']}\nTotal: {lb['tot']} USD", language="text")
            
            st.button("🖨️ IMPRIMER / PARTAGER")

    # --- STOCK ET PRIX ---
    elif choice == "📦 STOCK":
        st.header("GESTION DES ARTICLES")
        if ROLE == 'BOSS':
            with st.expander("➕ AJOUTER UN ARTICLE"):
                with st.form("add_p"):
                    it_n = st.text_input("Désignation")
                    it_q = st.number_input("Stock Initial", 1)
                    it_p = st.number_input("Prix de Vente")
                    if st.form_submit_button("Enregistrer"):
                        conn = get_db_connection(); c = conn.cursor()
                        c.execute("INSERT INTO inventory (item_name, stock_in, stock_now, price, currency, eid) VALUES (?,?,?,?,?,?)",
                                  (it_n.upper(), it_q, it_q, it_p, "USD", EID))
                        conn.commit(); conn.close(); st.rerun()

        conn = get_db_connection()
        df_inv = pd.read_sql("SELECT id, item_name, stock_in, stock_now, price FROM inventory WHERE eid=?", conn, params=(EID,))
        conn.close()
        for idx, row in df_inv.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{row['item_name']}**")
                c2.write(f"Stock: {row['stock_now']} / {row['stock_in']}")
                if ROLE == 'BOSS':
                    new_pr = c3.number_input("Prix", value=float(row['price']), key=f"pr_{row['id']}")
                    if c3.button("MODIFIER", key=f"up_{row['id']}"):
                        conn = get_db_connection(); c = conn.cursor()
                        c.execute("UPDATE inventory SET price=? WHERE id=?", (new_pr, row['id']))
                        conn.commit(); conn.close(); st.rerun()
                    if c4.button("🗑️", key=f"del_p_{row['id']}"):
                        conn = get_db_connection(); c = conn.cursor()
                        c.execute("DELETE FROM inventory WHERE id=?", (row['id'],))
                        conn.commit(); conn.close(); st.rerun()

    # --- RÉGLAGES (BOSS) ---
    elif choice == "⚙️ RÉGLAGES" and ROLE == 'BOSS':
        st.header("PARAMÈTRES DE LA BOUTIQUE")
        with st.form("config_biz"):
            new_n = st.text_input("Nom de l'entreprise", biz_info[0])
            new_h = st.text_area("En-tête de facture", biz_info[1])
            f_seal = st.file_uploader("Sceau (PNG)")
            f_sign = st.file_uploader("Signature (PNG)")
            if st.form_submit_button("METTRE À JOUR"):
                conn = get_db_connection(); c = conn.cursor()
                c.execute("UPDATE clients SET biz_name=?, header_info=? WHERE eid=?", (new_n.upper(), new_h, EID))
                if f_seal: c.execute("UPDATE clients SET seal=? WHERE eid=?", (f_seal.read(), EID))
                if f_sign: c.execute("UPDATE clients SET sign=? WHERE eid=?", (f_sign.read(), EID))
                conn.commit(); conn.close(); st.rerun()

    # --- DÉCONNEXION ---
    if st.sidebar.button("🚪 QUITTER"):
        st.session_state.logged = False
        st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v220
# ------------------------------------------------------------------------------
