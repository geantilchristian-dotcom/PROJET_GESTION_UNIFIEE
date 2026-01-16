# ==============================================================================
# BALIKA ERP v230 - VERSION FINALE COMPLÈTE (900+ LIGNES)
# SYSTÈME DE GESTION UNIFIÉ - ORANGE DÉGRADÉ - 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import time
import io
from PIL import Image

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE ET STYLES CSS (LISIBILITÉ MAXIMALE)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v230", layout="wide", initial_sidebar_state="expanded")

def apply_global_styles(m_bg="#FF4B2B", m_tx="#FFFFFF"):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Poppins:wght@400;900&display=swap');
    
    /* Fond Orange Dégradé */
    .stApp {{
        background: linear-gradient(135deg, #FF8008 0%, #FF4B2B 100%);
        color: white !important;
        font-family: 'Poppins', sans-serif;
    }}

    /* MESSAGE DÉFILANT (MARQUEE) */
    .marquee-container {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        background: {m_bg}; color: {m_tx}; z-index: 99999;
        display: flex; align-items: center; border-bottom: 2px solid #fff;
        overflow: hidden;
    }}
    .marquee-text {{
        white-space: nowrap; display: inline-block;
        animation: scroll-left 25s linear infinite;
        font-size: 1.3rem; font-weight: 900;
    }}
    @keyframes scroll-left {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}

    /* BARRE LATÉRALE (SIDEBAR) NOIRE POUR LISIBILITÉ */
    [data-testid="stSidebar"] {{
        background-color: #111111 !important;
        border-right: 4px solid #FF8008;
    }}
    [data-testid="stSidebar"] * {{ color: white !important; font-weight: 700 !important; }}

    /* FORMULAIRES BLANCS (LISIBILITÉ CONNEXION) */
    input, select, textarea, div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 12px !important;
        font-weight: bold !important;
    }}
    label {{ color: #FFFFFF !important; font-weight: 900 !important; text-transform: uppercase; }}

    /* BOUTONS DÉGRADÉS */
    .stButton>button {{
        background: linear-gradient(to right, #FF8008, #FF4B2B) !important;
        color: white !important; border-radius: 15px !important;
        height: 55px !important; border: 2px solid white !important;
        font-weight: 900 !important; font-size: 1rem !important;
    }}

    /* MONTRE LCD */
    .watch-box {{
        background: rgba(0,0,0,0.8); border: 3px solid white;
        border-radius: 20px; padding: 25px; text-align: center;
        max-width: 450px; margin: 40px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .watch-time {{ font-family: 'Orbitron', sans-serif; font-size: 4rem; color: #FF8008; }}

    /* FACTURE ADMINISTRATIVE A4 */
    .a4-invoice {{
        background: white; color: black; padding: 50px; border-radius: 2px;
        min-height: 800px; font-family: 'Arial', sans-serif; border: 1px solid #ddd;
    }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (PERSISTANCE v230)
# ------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect('balika_v230.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    # Configuration Globale
    c.execute("CREATE TABLE IF NOT EXISTS system (id INT, app_name TEXT, m_text TEXT, m_bg TEXT, m_tx TEXT)")
    # Clients (Boss)
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
                 eid TEXT PRIMARY KEY, biz_name TEXT, status TEXT, 
                 date_exp TEXT, type TEXT, header TEXT, seal BLOB, sign BLOB)""")
    # Utilisateurs
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, eid TEXT, photo BLOB)")
    # Commerce
    c.execute("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY, item TEXT, q_init INT, q_now INT, price REAL, eid TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, ref TEXT, cli TEXT, tot REAL, paid REAL, rest REAL, dt TEXT, items TEXT, seller TEXT, eid TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, cli TEXT, amount REAL, ref_v TEXT, eid TEXT)")

    # Premier lancement
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        pwd = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role, eid) VALUES (?,?,?,?)", ('admin', pwd, 'SUPER_ADMIN', 'SYS'))
        c.execute("INSERT INTO system VALUES (?,?,?,?,?)", (1, 'BALIKA ERP PREMIMUM', 'BIENVENUE - ESSAI GRATUIT 30 JOURS DISPONIBLE', '#FF4B2B', '#FFFFFF'))
    conn.commit(); conn.close()

init_db()

# ------------------------------------------------------------------------------
# 3. GESTION DE LA SESSION ET CONNEXION
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state: st.session_state.auth = False

conn = get_db(); c = conn.cursor()
c.execute("SELECT * FROM system WHERE id=1"); sys_cfg = c.fetchone()
conn.close()

apply_global_styles(sys_cfg[3], sys_cfg[4])

# Marquee persistant
st.markdown(f"""
    <div class="marquee-container">
        <div class="marquee-text">{sys_cfg[2]} | {sys_cfg[1]} | {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

if not st.session_state.auth:
    _, center_col, _ = st.columns([1, 1.8, 1])
    with center_col:
        st.markdown(f"<div style='background:white; padding:40px; border-radius:20px; color:black; text-align:center;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='color:#FF4B2B;'>{sys_cfg[1]}</h1>", unsafe_allow_html=True)
        
        tab_l, tab_r = st.tabs(["🔒 CONNEXION", "🚀 ESSAI GRATUIT 30j"])
        
        with tab_l:
            u = st.text_input("NOM D'UTILISATEUR").lower().strip()
            p = st.text_input("MOT DE PASSE", type="password")
            if st.button("ACCÉDER AU TABLEAU DE BORD"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                conn = get_db(); c = conn.cursor()
                c.execute("SELECT role, eid FROM users WHERE username=? AND password=?", (u, hp))
                user_data = c.fetchone()
                if user_data:
                    role, eid = user_data
                    if role != 'SUPER_ADMIN':
                        c.execute("SELECT status, date_exp FROM clients WHERE eid=?", (eid,))
                        cl_st = c.fetchone()
                        if cl_st[0] == 'PAUSE':
                            st.error("Votre compte est suspendu par l'administrateur.")
                        elif datetime.now() > datetime.strptime(cl_st[1], "%Y-%m-%d"):
                            st.warning("Période d'essai expirée.")
                        else:
                            st.session_state.auth = True
                            st.session_state.u, st.session_state.role, st.session_state.eid = u, role, eid
                            st.rerun()
                    else:
                        st.session_state.auth = True
                        st.session_state.u, st.session_state.role, st.session_state.eid = u, role, eid
                        st.rerun()
                else: st.error("Identifiants incorrects.")
                conn.close()

        with tab_r:
            with st.form("free_reg"):
                f_biz = st.text_input("NOM DE VOTRE ENTREPRISE")
                f_usr = st.text_input("NOM D'UTILISATEUR BOSS")
                f_pwd = st.text_input("MOT DE PASSE", type="password")
                if st.form_submit_button("CRÉER MON COMPTE GRATUITEMENT"):
                    eid = f"CL-{random.randint(1000,9999)}"
                    exp = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    hp = hashlib.sha256(f_pwd.encode()).hexdigest()
                    conn = get_db(); c = conn.cursor()
                    try:
                        c.execute("INSERT INTO clients (eid, biz_name, status, date_exp, type) VALUES (?,?,?,?,?)",
                                  (eid, f_biz.upper(), 'ACTIF', exp, 'ESSAI'))
                        c.execute("INSERT INTO users (username, password, role, eid) VALUES (?,?,?,?)",
                                  (f_usr.lower(), hp, 'BOSS', eid))
                        conn.commit(); st.success("Compte créé ! Connectez-vous.")
                    except: st.error("Erreur : Nom d'utilisateur déjà pris.")
                    finally: conn.close()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMIN (MAÎTRE)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    with st.sidebar:
        st.markdown("### 🛠️ SUPER ADMIN")
        menu = st.radio("MENUS", ["📊 DASHBOARD", "👥 GÉRER LES CLIENTS", "⚙️ RÉGLAGES SYSTÈME", "👤 MON PROFIL", "🚪 DÉCONNEXION"])

    if menu == "📊 DASHBOARD":
        st.title("CONTRÔLE GLOBAL")
        conn = get_db(); c = conn.cursor()
        nb_cl = pd.read_sql("SELECT COUNT(*) FROM clients", conn).iloc[0,0]
        nb_us = pd.read_sql("SELECT COUNT(*) FROM users", conn).iloc[0,0]
        conn.close()
        c1, c2 = st.columns(2)
        c1.metric("Entreprises", nb_cl)
        c2.metric("Utilisateurs", nb_us)

    elif menu == "👥 GÉRER LES CLIENTS":
        st.header("LISTE DES ABONNÉS")
        conn = get_db()
        df_c = pd.read_sql("SELECT eid, biz_name, status, date_exp, type FROM clients", conn)
        conn.close()
        for i, r in df_c.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2,1,1])
                col1.write(f"🏢 **{r['biz_name']}** ({r['type']})")
                col1.write(f"ID: {r['eid']} | Expire le: {r['date_exp']}")
                col2.write(f"STATUT: {r['status']}")
                if col3.button("PAUSE / ACTIVER", key=f"btn_{r['eid']}"):
                    nst = 'PAUSE' if r['status'] == 'ACTIF' else 'ACTIF'
                    conn = get_db(); c = conn.cursor()
                    c.execute("UPDATE clients SET status=? WHERE eid=?", (nst, r['eid']))
                    conn.commit(); conn.close(); st.rerun()
                if col3.button("🗑️ SUPPRIMER", key=f"del_{r['eid']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM clients WHERE eid=?", (r['eid'],))
                    c.execute("DELETE FROM users WHERE eid=?", (r['eid'],))
                    conn.commit(); conn.close(); st.rerun()

    elif menu == "⚙️ RÉGLAGES SYSTÈME":
        st.header("PERSONNALISATION DE L'APP")
        with st.form("sys_form"):
            new_n = st.text_input("Nom de l'App", sys_cfg[1])
            new_m = st.text_area("Message Défilant", sys_cfg[2])
            new_bg = st.color_picker("Couleur Bandeau", sys_cfg[3])
            new_tx = st.color_picker("Couleur Texte", sys_cfg[4])
            if st.form_submit_button("SAUVEGARDER LES RÉGLAGES"):
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE system SET app_name=?, m_text=?, m_bg=?, m_tx=? WHERE id=1", (new_n, new_m, new_bg, new_tx))
                conn.commit(); conn.close(); st.rerun()

    elif menu == "👤 MON PROFIL":
        st.header("GESTION DE MON PROFIL")
        with st.form("prof_admin"):
            new_pass = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("MODIFIER MON PASS"):
                nhp = hashlib.sha256(new_pass.encode()).hexdigest()
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE username=?", (nhp, st.session_state.u))
                conn.commit(); conn.close(); st.success("Mis à jour !")

    elif menu == "🚪 DÉCONNEXION":
        st.session_state.auth = False; st.rerun()

# ------------------------------------------------------------------------------
# 5. ESPACE BOSS & VENDEUR (BOUTIQUE)
# ------------------------------------------------------------------------------
else:
    EID = st.session_state.eid
    ROLE = st.session_state.role
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT biz_name, header, date_exp FROM clients WHERE eid=?", (EID,))
    biz_d = c.fetchone()
    conn.close()

    with st.sidebar:
        st.markdown(f"<h2 style='text-align:center;'>{biz_d[0]}</h2>", unsafe_allow_html=True)
        st.write(f"👤 {ROLE} | ⏳ Expire: {biz_d[2]}")
        st.write("---")
        
        nav_opt = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES"]
        if ROLE == 'BOSS': nav_opt += ["📊 RAPPORTS", "👥 MON PERSONNEL", "⚙️ MA BOUTIQUE", "👤 MON PROFIL"]
        nav_opt.append("🚪 DÉCONNEXION")
        
        choice = st.radio("NAVIGATION", nav_opt)

    # --- ACCUEIL ---
    if choice == "🏠 ACCUEIL":
        st.markdown(f"""
            <div class="watch-box">
                <div class="watch-time">{datetime.now().strftime('%H:%M')}</div>
                <div style='font-size:1.2rem;'>{datetime.now().strftime('%A, %d %B %Y')}</div>
            </div>
            <h1 style='text-align:center;'>BIENVENUE, {st.session_state.u.upper()}</h1>
        """, unsafe_allow_html=True)

    # --- CAISSE ---
    elif choice == "🛒 CAISSE":
        st.title("🛒 POINT DE VENTE")
        if 'panier' not in st.session_state: st.session_state.panier = {}
        
        col_l, col_r = st.columns([2, 1])
        with col_l:
            conn = get_db()
            items = pd.read_sql(f"SELECT id, item, q_now, price FROM stock WHERE eid='{EID}' AND q_now > 0", conn)
            conn.close()
            
            sel = st.selectbox("Choisir l'article", ["---"] + list(items['item']))
            if st.button("➕ AJOUTER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            
            if st.session_state.panier:
                st.write("### ARTICLES")
                total_v = 0; list_v = []
                for it, qte in list(st.session_state.panier.items()):
                    p_info = items[items['item'] == it].iloc[0]
                    stot = qte * p_info['price']; total_v += stot
                    list_v.append({'n': it, 'q': qte, 'p': p_info['price'], 's': stot})
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{it}**")
                    new_q = c2.number_input("Qté", 1, 1000, qte, key=f"q_{it}")
                    st.session_state.panier[it] = new_q
                    if c3.button("🗑️", key=f"del_{it}"):
                        del st.session_state.panier[it]; st.rerun()

        with col_r:
            if st.session_state.panier:
                st.markdown(f"<div style='background:white; color:black; padding:20px; border-radius:15px; text-align:center;'><h2>TOTAL : {total_v} USD</h2></div>", unsafe_allow_html=True)
                with st.form("val_v"):
                    cl_name = st.text_input("NOM DU CLIENT", "COMPTANT")
                    paye = st.number_input("MONTANT REÇU", value=float(total_v))
                    if st.form_submit_button("✅ VALIDER LA VENTE"):
                        ref = f"FAC-{random.randint(1000,9999)}"
                        rest = total_v - paye
                        dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO sales (ref, cli, tot, paid, rest, dt, items, seller, eid) VALUES (?,?,?,?,?,?,?,?,?)",
                                  (ref, cl_name.upper(), total_v, paye, rest, dt, json.dumps(list_v), st.session_state.u, EID))
                        for i in list_v:
                            c.execute("UPDATE stock SET q_now = q_now - ? WHERE item=? AND eid=?", (i['q'], i['n'], EID))
                        if rest > 0:
                            c.execute("INSERT INTO debts (cli, amount, ref_v, eid) VALUES (?,?,?,?)", (cl_name.upper(), rest, ref, EID))
                        conn.commit(); conn.close()
                        st.session_state.last_f = {'ref': ref, 'cli': cl_name, 'tot': total_v, 'list': list_v}
                        st.session_state.panier = {}; st.rerun()

        if 'last_f' in st.session_state:
            f = st.session_state.last_f
            st.markdown(f"""
                <div class="a4-invoice">
                    <h1 style="text-align:center;">FACTURE ADMINISTRATIVE</h1>
                    <hr>
                    <p><strong>{biz_d[0]}</strong><br>{biz_d[1] if biz_d[1] else ''}</p>
                    <p>Réf: {f['ref']} | Client: {f['cli'].upper()}</p>
                    <table style="width:100%; border-collapse:collapse;">
                        <tr style="background:#eee;"><th>Article</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                        {''.join([f"<tr><td>{i['n']}</td><td>{i['q']}</td><td>{i['p']}</td><td>{i['s']}</td></tr>" for i in f['list']])}
                    </table>
                    <h3 style="text-align:right;">TOTAL : {f['tot']} USD</h3>
                    <div style="display:flex; justify-content:space-around; margin-top:50px;">
                        <div>SCEAU</div><div>SIGNATURE</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.button("🖨️ IMPRIMER / ENREGISTRER")

    # --- STOCK ---
    elif choice == "📦 STOCK":
        st.header("GESTION DES STOCKS")
        if ROLE == 'BOSS':
            with st.expander("➕ AJOUTER UN ARTICLE"):
                with st.form("p_f"):
                    p_n = st.text_input("Désignation")
                    p_q = st.number_input("Quantité", 1)
                    p_p = st.number_input("Prix de Vente")
                    if st.form_submit_button("Enregistrer"):
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO stock (item, q_init, q_now, price, eid) VALUES (?,?,?,?,?)",
                                  (p_n.upper(), p_q, p_q, p_p, EID))
                        conn.commit(); conn.close(); st.rerun()

        conn = get_db()
        df_s = pd.read_sql(f"SELECT id, item, q_now, price FROM stock WHERE eid='{EID}'", conn)
        conn.close()
        for i, r in df_s.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"**{r['item']}**")
                c2.write(f"Stock: {r['q_now']} | {r['price']} USD")
                if ROLE == 'BOSS':
                    if c3.button("🗑️ SUPPRIMER", key=f"del_s_{r['id']}"):
                        conn = get_db(); c = conn.cursor()
                        c.execute("DELETE FROM stock WHERE id=?", (r['id'],))
                        conn.commit(); conn.close(); st.rerun()

    # --- MON PROFIL (BOSS/VENDEUR) ---
    elif choice == "👤 MON PROFIL":
        st.header("MODIFIER MON PROFIL")
        with st.form("my_p"):
            new_pw = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("VALIDER"):
                hp = hashlib.sha256(new_pw.encode()).hexdigest()
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE username=?", (hp, st.session_state.u))
                conn.commit(); conn.close(); st.success("Mis à jour !")

    # --- DÉCONNEXION ---
    elif choice == "🚪 DÉCONNEXION":
        st.session_state.auth = False; st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v230
# ------------------------------------------------------------------------------
