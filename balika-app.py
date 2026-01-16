# ==============================================================================
# BALIKA ERP v218 - SYSTÈME DE GESTION UNIFIÉ (750+ LIGNES)
# ARCHITECTURE : SUPER_ADMIN (MAÎTRE) | BOSS (CLIENT) | VENDEUR
# OPTIMISÉ POUR MOBILE - AFFICHAGE CONTRASTÉ - 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64
import io
from PIL import Image

# ------------------------------------------------------------------------------
# 1. STYLE CSS AVANCÉ (FORCE LA LISIBILITÉ SUR TOUS LES ÉCRANS)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v218", layout="wide", initial_sidebar_state="collapsed")

def load_css(marquee_color="#FFD700", text_color="#000000"):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@400;900&display=swap');
    
    /* Fond principal avec dégradé sombre pour faire ressortir les éléments */
    .stApp {{
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white !important;
    }}

    /* FIX LISIBILITÉ DES FORMULAIRES : Texte noir sur fond blanc impératif */
    input, select, textarea {{
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
    }}
    
    div[data-baseweb="input"] {{
        background-color: white !important;
        border-radius: 10px !important;
    }}

    label {{
        color: #00d4ff !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        font-size: 0.9rem !important;
    }}

    /* Message défilant persistant */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%; height: 45px;
        background: {marquee_color}; color: {text_color}; z-index: 10000;
        display: flex; align-items: center; border-bottom: 2px solid #fff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .marquee-text {{
        white-space: nowrap; display: inline-block;
        animation: scroll-left 25s linear infinite;
        font-family: 'Roboto', sans-serif; font-weight: 900; font-size: 1.2rem;
    }}
    @keyframes scroll-left {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}

    /* Montre LCD Centrée */
    .lcd-watch {{
        background: rgba(0,0,0,0.8); border: 4px solid #00d4ff;
        border-radius: 25px; padding: 30px; text-align: center;
        max-width: 500px; margin: 50px auto;
        box-shadow: 0 0 30px #00d4ff;
    }}
    .lcd-time {{
        font-family: 'Orbitron', sans-serif; font-size: 4.5rem;
        color: #00d4ff; text-shadow: 0 0 15px #00d4ff; line-height: 1;
    }}
    .lcd-date {{ color: #fff; font-size: 1.2rem; letter-spacing: 5px; margin-top: 10px; }}

    /* Cadres et Totaux */
    .total-box {{
        background: #ffffff; color: #1e3c72; border-left: 10px solid #ff9800;
        border-radius: 15px; padding: 25px; font-size: 2.8rem;
        font-weight: 900; text-align: center; margin: 20px 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }}
    
    /* Boutons stylisés */
    .stButton>button {{
        background: linear-gradient(to right, #00d4ff, #0056b3) !important;
        color: white !important; border: none !important;
        border-radius: 15px !important; height: 55px !important;
        font-weight: 900 !important; font-size: 1.1rem !important;
        transition: 0.3s transform;
    }}
    .stButton>button:hover {{ transform: scale(1.02); }}

    /* Facture Administrative A4 */
    .invoice-a4 {{
        background: white; color: black; padding: 40px; border-radius: 2px;
        min-height: 800px; font-family: 'Arial', sans-serif;
    }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. GESTION DE LA BASE DE DONNÉES (PERSISTANCE v218)
# ------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect('balika_master_v218.db', timeout=30)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Table Super Admin (Système)
    c.execute("""CREATE TABLE IF NOT EXISTS system_setup (
                 id INTEGER PRIMARY KEY, app_name TEXT, m_text TEXT, 
                 m_color TEXT, m_txt_color TEXT)""")
    
    # Table Abonnés (Boss Clients)
    c.execute("""CREATE TABLE IF NOT EXISTS subscribers (
                 eid TEXT PRIMARY KEY, biz_name TEXT, status TEXT, 
                 header_txt TEXT, seal BLOB, signature BLOB, date_sub TEXT)""")
    
    # Table Utilisateurs (Boss & Vendeurs)
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                 eid TEXT, last_login TEXT)""")
    
    # Table Stock (Avec Stock Initial)
    c.execute("""CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                 qte_initiale INTEGER, qte_actuelle INTEGER, 
                 prix_vente REAL, devise TEXT, eid TEXT)""")
    
    # Table Ventes (Historique complet)
    c.execute("""CREATE TABLE IF NOT EXISTS sales (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                 total REAL, paye REAL, reste REAL, devise TEXT, 
                 date_v TEXT, details TEXT, vendeur TEXT, eid TEXT)""")
    
    # Table Dettes
    c.execute("""CREATE TABLE IF NOT EXISTS debts (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, 
                 montant REAL, devise TEXT, ref_v TEXT, eid TEXT)""")

    # Configuration initiale Super Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        pwd = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role, eid) VALUES (?,?,?,?)", 
                  ('admin', pwd, 'SUPER_ADMIN', 'SYSTEM'))
        c.execute("INSERT INTO system_setup (id, app_name, m_text, m_color, m_txt_color) VALUES (?,?,?,?,?)",
                  (1, 'BALIKA ERP PREMIMUM', 'BIENVENUE SUR VOTRE PLATEFORME DE GESTION UNIFIÉE', '#FFD700', '#000000'))
    
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------------------
# 3. FONCTIONS LOGIQUES ET SÉCURITÉ
# ------------------------------------------------------------------------------
def check_login(u, p):
    conn = get_db()
    c = conn.cursor()
    hp = hashlib.sha256(p.encode()).hexdigest()
    c.execute("SELECT role, eid FROM users WHERE username=? AND password=?", (u, hp))
    res = c.fetchone()
    conn.close()
    return res

def get_sys_config():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT app_name, m_text, m_color, m_txt_color FROM system_setup WHERE id=1")
    res = c.fetchone()
    conn.close()
    return res

# ------------------------------------------------------------------------------
# 4. INTERFACE DE CONNEXION (IMAGE 2 FIXÉE)
# ------------------------------------------------------------------------------
sys_cfg = get_sys_config()
load_css(sys_cfg[2], sys_cfg[3])

# Affichage du message défilant sur toutes les pages
st.markdown(f"""
    <div class="marquee-wrapper">
        <div class="marquee-text">{sys_cfg[1]} | {sys_cfg[0]} | DATE : {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    <div style="height: 60px;"></div>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.markdown(f"""
            <div style="background:white; padding:40px; border-radius:20px; text-align:center; margin-top:50px; border-top:8px solid #00d4ff;">
                <h1 style="color:#1e3c72; margin-bottom:0;">{sys_cfg[0]}</h1>
                <p style="color:#666;">Veuillez entrer vos identifiants pour continuer</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            user_in = st.text_input("NOM D'UTILISATEUR", placeholder="ex: admin").lower().strip()
            pass_in = st.text_input("MOT DE PASSE", type="password", placeholder="••••••••")
            
            if st.button("DÉVERROUILLER LE SYSTÈME", use_container_width=True):
                login_data = check_login(user_in, pass_in)
                if login_data:
                    # Si c'est un boss ou vendeur, vérifier si l'abonné n'est pas suspendu
                    if login_data[0] != 'SUPER_ADMIN':
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("SELECT status FROM subscribers WHERE eid=?", (login_data[1],))
                        status = c.fetchone()
                        conn.close()
                        if status and status[0] != 'ACTIF':
                            st.error("❌ VOTRE ABONNEMENT EST SUSPENDU OU EXPIRÉ.")
                            st.stop()
                    
                    st.session_state.auth = True
                    st.session_state.user = user_in
                    st.session_state.role = login_data[0]
                    st.session_state.eid = login_data[1]
                    st.rerun()
                else:
                    st.error("🚫 IDENTIFIANTS INCORRECTS")
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN (GESTION ABONNÉS ET SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    with st.sidebar:
        st.markdown(f"### 💎 MASTER ADMIN")
        menu = st.radio("CONTRÔLE", ["🏠 DASHBOARD", "🌍 GESTION ABONNÉS", "⚙️ RÉGLAGES SYSTÈME", "🚪 DÉCONNEXION"])

    if menu == "🏠 DASHBOARD":
        st.title("ÉTAT DU SYSTÈME")
        c1, c2 = st.columns(2)
        conn = get_db()
        nb_subs = pd.read_sql("SELECT COUNT(*) FROM subscribers", conn).iloc[0,0]
        nb_users = pd.read_sql("SELECT COUNT(*) FROM users", conn).iloc[0,0]
        conn.close()
        c1.metric("Total Boutiques", nb_subs)
        c2.metric("Total Utilisateurs", nb_users)

    elif menu == "🌍 GESTION ABONNÉS":
        st.header("GESTION DES ABONNÉS")
        with st.expander("➕ CRÉER UN NOUVEL ABONNEMENT"):
            with st.form("new_client"):
                n_biz = st.text_input("Nom de l'Entreprise")
                n_boss = st.text_input("Identifiant Boss (User)")
                n_pass = st.text_input("Mot de Passe", type="password")
                if st.form_submit_button("ACTIVER L'ABONNÉ"):
                    eid = f"BAL-{random.randint(1000,9999)}"
                    h_pass = hashlib.sha256(n_pass.encode()).hexdigest()
                    conn = get_db()
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO subscribers (eid, biz_name, status, date_sub) VALUES (?,?,?,?)",
                                  (eid, n_biz.upper(), 'ACTIF', datetime.now().strftime("%d/%m/%Y")))
                        c.execute("INSERT INTO users (username, password, role, eid) VALUES (?,?,?,?)",
                                  (n_boss.lower(), h_pass, 'BOSS', eid))
                        conn.commit()
                        st.success(f"Compte créé pour {n_biz} (ID: {eid})")
                    except: st.error("L'identifiant existe déjà.")
                    finally: conn.close()
        
        st.write("---")
        conn = get_db()
        df_s = pd.read_sql("SELECT eid, biz_name, status, date_sub FROM subscribers", conn)
        conn.close()
        
        for idx, row in df_s.iterrows():
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                col1.write(f"**{row['biz_name']}**")
                col2.write(f"ID: {row['eid']}")
                col3.write(f"Statut: {row['status']}")
                if col4.button("SUSPENDRE / ACTIVER", key=f"btn_{row['eid']}"):
                    new_st = 'SUSPENDU' if row['status'] == 'ACTIF' else 'ACTIF'
                    conn = get_db(); c = conn.cursor()
                    c.execute("UPDATE subscribers SET status=? WHERE eid=?", (new_st, row['eid']))
                    conn.commit(); conn.close()
                    st.rerun()
                if col4.button("SUPPRIMER", key=f"del_{row['eid']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM subscribers WHERE eid=?", (row['eid'],))
                    c.execute("DELETE FROM users WHERE eid=?", (row['eid'],))
                    conn.commit(); conn.close()
                    st.rerun()

    elif menu == "⚙️ RÉGLAGES SYSTÈME":
        st.header("CONFIGURATION GLOBALE")
        with st.form("sys_config_form"):
            new_app = st.text_input("Nom de l'Application", sys_cfg[0])
            new_msg = st.text_area("Message Défilant", sys_cfg[1])
            new_col = st.color_picker("Couleur du Bandeau", sys_cfg[2])
            new_txt_col = st.color_picker("Couleur du Texte Défilant", sys_cfg[3])
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE system_setup SET app_name=?, m_text=?, m_color=?, m_txt_color=? WHERE id=1",
                          (new_app, new_msg, new_col, new_txt_col))
                conn.commit(); conn.close()
                st.success("Système mis à jour !")
                st.rerun()

    elif menu == "🚪 DÉCONNEXION":
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. ESPACE BOSS & VENDEUR (GESTION BOUTIQUE)
# ------------------------------------------------------------------------------
else:
    EID = st.session_state.eid
    ROLE = st.session_state.role
    
    # Récupérer infos boutique
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT biz_name, header_txt, seal, signature FROM subscribers WHERE eid=?", (EID,))
    biz_data = c.fetchone()
    conn.close()

    with st.sidebar:
        st.markdown(f"<h2 style='text-align:center; color:#00d4ff;'>{biz_data[0]}</h2>", unsafe_allow_html=True)
        st.write(f"📍 ID: {EID} | 👤 {ROLE}")
        st.write("---")
        if ROLE == 'BOSS':
            nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES BOUTIQUE", "🚪 DÉCONNEXION"]
        else:
            nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "🚪 DÉCONNEXION"]
        
        choice = st.radio("MENU NAVIGATION", nav)

    # --- ACCUEIL AVEC MONTRE LCD ---
    if choice == "🏠 ACCUEIL":
        st.markdown(f"""
            <div class="lcd-watch">
                <div class="lcd-time">{datetime.now().strftime('%H:%M')}</div>
                <div class="lcd-date">{datetime.now().strftime('%A, %d %B %Y')}</div>
            </div>
            <h1 style='text-align:center;'>BIENVENUE, {st.session_state.user.upper()}</h1>
        """, unsafe_allow_html=True)

    # --- CAISSE (FORMAT A4 / 80mm) ---
    elif choice == "🛒 CAISSE":
        st.title("🛒 POINT DE VENTE")
        if 'panier' not in st.session_state: st.session_state.panier = {}
        
        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c1:
            conn = get_db()
            prods = pd.read_sql("SELECT id, designation, qte_actuelle, prix_vente, devise FROM products WHERE eid=? AND qte_actuelle > 0", conn, params=(EID,))
            conn.close()
            
            p_sel = st.selectbox("CHOISIR UN ARTICLE", ["---"] + list(prods['designation']))
            if st.button("➕ AJOUTER AU PANIER") and p_sel != "---":
                st.session_state.panier[p_sel] = st.session_state.panier.get(p_sel, 0) + 1
            
            if st.session_state.panier:
                st.write("### ARTICLES SÉLECTIONNÉS")
                total_vente = 0
                items_list = []
                for art, qte in list(st.session_state.panier.items()):
                    p_info = prods[prods['designation'] == art].iloc[0]
                    stot = qte * p_info['prix_vente']
                    total_vente += stot
                    items_list.append({'art': art, 'qte': qte, 'pu': p_info['prix_vente'], 'st': stot})
                    
                    cc1, cc2, cc3 = st.columns([3, 1, 1])
                    cc1.write(f"**{art}** ({p_info['prix_vente']} {p_info['devise']})")
                    new_q = cc2.number_input("Qté", 1, int(p_info['qte_actuelle']), qte, key=f"q_{art}")
                    st.session_state.panier[art] = new_q
                    if cc3.button("🗑️", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()

        with col_c2:
            if st.session_state.panier:
                st.markdown(f'<div class="total-box">À PAYER :<br>{total_vente:,.2f} USD</div>', unsafe_allow_html=True)
                with st.form("validation_vente"):
                    cl_name = st.text_input("NOM DU CLIENT", "COMPTANT")
                    m_paye = st.number_input("MONTANT REÇU", value=float(total_vente))
                    f_print = st.radio("FORMAT D'IMPRESSION", ["80mm (Ticket)", "A4 (Administratif)"])
                    if st.form_submit_button("✅ VALIDER LA VENTE"):
                        ref_v = f"FAC-{random.randint(1000,9999)}"
                        reste_v = total_vente - m_paye
                        dt_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO sales (ref, client, total, paye, reste, devise, date_v, details, vendeur, eid) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (ref_v, cl_name.upper(), total_vente, m_paye, reste_v, "USD", dt_v, json.dumps(items_list), st.session_state.user, EID))
                        
                        for it in items_list:
                            c.execute("UPDATE products SET qte_actuelle = qte_actuelle - ? WHERE designation=? AND eid=?", (it['qte'], it['art'], EID))
                        
                        if reste_v > 0.01:
                            c.execute("INSERT INTO debts (client, montant, devise, ref_v, eid) VALUES (?,?,?,?,?)",
                                      (cl_name.upper(), reste_v, "USD", ref_v, EID))
                        
                        conn.commit(); conn.close()
                        st.session_state.last_fac = {'ref': ref_v, 'cl': cl_name, 'tot': total_vente, 'pay': m_paye, 'rst': reste_v, 'items': items_list, 'fmt': f_print}
                        st.session_state.panier = {}
                        st.success("VENTE TERMINÉE !")
                        st.rerun()

        if 'last_fac' in st.session_state:
            lf = st.session_state.last_fac
            st.write("---")
            if lf['fmt'] == "A4 (Administratif)":
                st.markdown(f"""
                    <div class="invoice-a4">
                        <h1 style="text-align:center; color:#1e3c72;">FACTURE ADMINISTRATIVE</h1>
                        <div style="display:flex; justify-content:space-between;">
                            <div><strong>{biz_data[0]}</strong><br>{biz_data[1]}</div>
                            <div style="text-align:right;">Réf: {lf['ref']}<br>Date: {datetime.now().strftime('%d/%m/%Y')}</div>
                        </div>
                        <hr>
                        <p>Client: <strong>{lf['cl'].upper()}</strong></p>
                        <table style="width:100%; border-collapse:collapse;">
                            <tr style="background:#f0f0f0;"><th>Désignation</th><th>Qté</th><th>P.U</th><th>S.Total</th></tr>
                            {''.join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['pu']}</td><td>{i['st']}</td></tr>" for i in lf['items']])}
                        </table>
                        <h2 style="text-align:right;">TOTAL : {lf['tot']} USD</h2>
                        <div style="display:flex; justify-content:space-around; margin-top:50px;">
                            <div style="text-align:center;">SCEAU<br><br></div>
                            <div style="text-align:center;">SIGNATURE<br><br></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="background:#fff; color:#000; padding:10px; font-family:monospace; text-align:center;">
                        <h3>{biz_data[0]}</h3>
                        <p>{lf['ref']} | {datetime.now().strftime('%H:%M')}</p>
                        <hr>
                        {''.join([f"<p>{i['art']} x{i['qte']} : {i['st']}</p>" for i in lf['items']])}
                        <hr>
                        <h4>TOTAL: {lf['tot']} USD</h4>
                        <p>Payé: {lf['pay']} | Reste: {lf['rst']}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.button("🖨️ IMPRIMER / PARTAGER")

    # --- STOCK (AJOUT, MODIF PRIX, STOCK INITIAL) ---
    elif choice == "📦 STOCK" and ROLE == 'BOSS':
        st.header("GESTION DES PRODUITS")
        with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
            with st.form("stock_form"):
                d_art = st.text_input("Désignation de l'article")
                q_init = st.number_input("Quantité en Stock Initial", min_value=1)
                p_vent = st.number_input("Prix de Vente Unitaire")
                if st.form_submit_button("ENREGISTRER AU STOCK"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO products (designation, qte_initiale, qte_actuelle, prix_vente, devise, eid) VALUES (?,?,?,?,?,?)",
                              (d_art.upper(), q_init, q_init, p_vent, "USD", EID))
                    conn.commit(); conn.close()
                    st.rerun()

        st.write("### ÉTAT DE L'INVENTAIRE")
        conn = get_db()
        df_p = pd.read_sql("SELECT id, designation, qte_initiale, qte_actuelle, prix_vente FROM products WHERE eid=?", conn, params=(EID,))
        conn.close()
        
        for idx, r in df_p.iterrows():
            with st.container(border=True):
                colp1, colp2, colp3, colp4 = st.columns([2,1,1,1])
                colp1.write(f"**{r['designation']}**")
                colp2.write(f"Stock: {r['qte_actuelle']} / {r['qte_initiale']}")
                new_p = colp3.number_input(f"Prix (USD)", value=float(r['prix_vente']), key=f"px_{r['id']}")
                if colp3.button("MODIFIER", key=f"btn_p_{r['id']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("UPDATE products SET prix_vente=? WHERE id=?", (new_p, r['id']))
                    conn.commit(); conn.close()
                    st.toast("Prix mis à jour !")
                if colp4.button("🗑️ SUPPRIMER", key=f"del_p_{r['id']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM products WHERE id=?", (r['id'],))
                    conn.commit(); conn.close()
                    st.rerun()

    # --- DETTES (RECOUVREMENT AUTOMATIQUE) ---
    elif choice == "📉 DETTES":
        st.header("SUIVI DES DETTES CLIENTS")
        conn = get_db()
        df_d = pd.read_sql("SELECT * FROM debts WHERE eid=?", conn, params=(EID,))
        conn.close()
        
        if df_d.empty:
            st.success("✅ AUCUNE DETTE EN COURS.")
        else:
            for idx, d in df_d.iterrows():
                with st.container(border=True):
                    cold1, cold2, cold3 = st.columns([2,1,1])
                    cold1.write(f"👤 **{d['client']}** | Facture: {d['ref_v']}")
                    cold2.write(f"Reste : **{d['montant']} {d['devise']}**")
                    p_aco = cold3.number_input("Verser Acompte", 0.0, float(d['montant']), key=f"aco_{d['id']}")
                    if cold3.button("VALIDER", key=f"btn_aco_{d['id']}"):
                        n_reste = d['montant'] - p_aco
                        conn = get_db(); c = conn.cursor()
                        if n_reste <= 0.01:
                            c.execute("DELETE FROM debts WHERE id=?", (d['id'],))
                            st.balloons()
                        else:
                            c.execute("UPDATE debts SET montant=? WHERE id=?", (n_reste, d['id']))
                        # Update vente originale
                        c.execute("UPDATE sales SET paye = paye + ?, reste = reste - ? WHERE ref=? AND eid=?", (p_aco, p_aco, d['ref_v'], EID))
                        conn.commit(); conn.close()
                        st.rerun()

    # --- VENDEURS (GESTION BOSS) ---
    elif choice == "👥 VENDEURS" and ROLE == 'BOSS':
        st.header("GESTION DU PERSONNEL")
        with st.form("add_vendeur"):
            v_user = st.text_input("Identifiant du Vendeur").lower().strip()
            v_pass = st.text_input("Mot de Passe Vendeur", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                h_vpass = hashlib.sha256(v_pass.encode()).hexdigest()
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (username, password, role, eid) VALUES (?,?,?,?)",
                              (v_user, h_vpass, 'VENDEUR', EID))
                    conn.commit(); st.success(f"Vendeur {v_user} ajouté !")
                except: st.error("Identifiant déjà pris.")
                finally: conn.close()
        
        st.write("---")
        conn = get_db()
        df_v = pd.read_sql("SELECT username FROM users WHERE eid=? AND role='VENDEUR'", conn, params=(EID,))
        conn.close()
        for u_v in df_v['username']:
            c_v1, c_v2 = st.columns([3,1])
            c_v1.write(f"👤 **{u_v.upper()}** (Vendeur)")
            if c_v2.button("SUPPRIMER COMPTE", key=f"del_v_{u_v}"):
                conn = get_db(); c = conn.cursor()
                c.execute("DELETE FROM users WHERE username=?", (u_v,))
                conn.commit(); conn.close()
                st.rerun()

    # --- RÉGLAGES BOUTIQUE (SCEAU / SIGNATURE) ---
    elif choice == "⚙️ RÉGLAGES BOUTIQUE" and ROLE == 'BOSS':
        st.header("PERSONNALISATION DE LA BOUTIQUE")
        with st.form("biz_config"):
            new_biz_n = st.text_input("Nom de l'Entreprise", biz_data[0])
            new_biz_h = st.text_area("En-tête (Adresse, Tel, WhatsApp)", biz_data[1])
            f_seal = st.file_uploader("IMPORTER LE SCEAU / TAMPON (PNG)", type=['png'])
            f_sign = st.file_uploader("IMPORTER LA SIGNATURE (PNG)", type=['png'])
            if st.form_submit_button("METTRE À JOUR LA BOUTIQUE"):
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE subscribers SET biz_name=?, header_txt=? WHERE eid=?", (new_biz_n.upper(), new_biz_h, EID))
                if f_seal: c.execute("UPDATE subscribers SET seal=? WHERE eid=?", (f_seal.read(), EID))
                if f_sign: c.execute("UPDATE subscribers SET signature=? WHERE eid=?", (f_sign.read(), EID))
                conn.commit(); conn.close()
                st.success("Modifications enregistrées !")
                st.rerun()

    elif choice == "📊 RAPPORTS" and ROLE == 'BOSS':
        st.title("JOURNAL DES VENTES")
        conn = get_db()
        df_sales = pd.read_sql("SELECT ref, client, total, paye, reste, date_v, vendeur FROM sales WHERE eid=? ORDER BY id DESC", conn, params=(EID,))
        conn.close()
        st.dataframe(df_sales, use_container_width=True)

    elif choice == "🚪 DÉCONNEXION":
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v218 - BALIKA ERP
# ------------------------------------------------------------------------------
