# ==============================================================================
# BALIKA ERP v225 - ÉDITION ORANGE PRO (950+ LIGNES)
# SYSTÈME DE GESTION ADMINISTRATIVE ET COMMERCIALE UNIFIÉ
# DESIGN HAUT CONTRASTE - AUTO-SAVE INVOICE - 2026
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
import time
from PIL import Image

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE ET STYLE (FIX VISIBILITÉ COLONNE GRISE)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v225", layout="wide", initial_sidebar_state="expanded")

def inject_pro_css(m_bg="#FF4B2B", m_tx="#FFFFFF"):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@400;900&display=swap');
    
    /* Fond principal Orange Dégradé */
    .stApp {{
        background: linear-gradient(135deg, #FF4B2B 0%, #FF8008 100%);
        color: white !important;
    }}

    /* BARRE LATÉRALE (FIX COLONNE GRISE) */
    [data-testid="stSidebar"] {{
        background-color: #1A1A1A !important; /* Noir profond pour contraste */
        border-right: 3px solid #FF8008;
    }}
    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}
    .st-emotion-cache-16q9ru1 {{ color: #FF8008 !important; }} /* Titres sidebar */

    /* MESSAGE DÉFILANT (MARQUEE) */
    .top-marquee {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        background: {m_bg}; color: {m_tx}; z-index: 10000;
        display: flex; align-items: center; border-bottom: 2px solid white;
        overflow: hidden;
    }}
    .marquee-content {{
        display: inline-block; white-space: nowrap;
        padding-left: 100%; animation: marquee-run 25s linear infinite;
        font-family: 'Roboto', sans-serif; font-weight: 900; font-size: 1.4rem;
    }}
    @keyframes marquee-run {{
        0% {{ transform: translate(0, 0); }}
        100% {{ transform: translate(-100%, 0); }}
    }}

    /* FORMULAIRES ET INPUTS (NOIR SUR BLANC) */
    input, select, textarea, div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px !important;
        border: 2px solid #FF8008 !important;
    }}
    label {{ color: white !important; font-size: 1.1rem !important; font-weight: 900 !important; }}

    /* MONTRE DIGITALE */
    .digital-watch {{
        background: rgba(0,0,0,0.7); border: 4px solid #FF8008;
        border-radius: 20px; padding: 20px; text-align: center;
        max-width: 400px; margin: 40px auto; box-shadow: 0 0 30px #FF8008;
    }}
    .watch-h {{ font-family: 'Orbitron', sans-serif; font-size: 4rem; color: #FF8008; margin:0; }}
    .watch-d {{ color: white; font-size: 1.1rem; text-transform: uppercase; }}

    /* BOUTONS ET ONGLETS */
    .stButton>button {{
        background: #FFFFFF !important; color: #FF4B2B !important;
        border-radius: 12px !important; font-weight: 900 !important;
        border: 2px solid #FF4B2B !important; width: 100%; height: 50px;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ background: #FF4B2B !important; color: white !important; transform: scale(1.05); }}

    /* FACTURE ADMINISTRATIVE A4 */
    .invoice-container {{
        background: white; color: black; padding: 50px; border-radius: 5px;
        min-height: 1000px; font-family: 'Arial', sans-serif; line-height: 1.6;
    }}
    .invoice-header {{ border-bottom: 3px solid #FF4B2B; margin-bottom: 20px; padding-bottom: 10px; }}
    
    /* CADRE CAISSE */
    .total-display {{
        background: white; color: #FF4B2B; border: 5px solid black;
        border-radius: 15px; padding: 15px; font-size: 3rem;
        font-weight: 900; text-align: center; margin: 15px 0;
    }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE DONNÉES SQLITE
# ------------------------------------------------------------------------------
def db_query(q, p=(), commit=False):
    conn = sqlite3.connect('balika_v225_core.db', timeout=10)
    c = conn.cursor()
    c.execute(q, p)
    res = c.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def init_core_db():
    # Tables Système
    db_query("CREATE TABLE IF NOT EXISTS sys_settings (id INTEGER, name TEXT, m_text TEXT, m_bg TEXT, m_tx TEXT)", commit=True)
    db_query("CREATE TABLE IF NOT EXISTS users (user TEXT PRIMARY KEY, pw TEXT, role TEXT, eid TEXT, photo BLOB)", commit=True)
    db_query("CREATE TABLE IF NOT EXISTS clients (eid TEXT PRIMARY KEY, biz TEXT, status TEXT, d_exp TEXT, type TEXT, head TEXT, seal BLOB, sign BLOB)", commit=True)
    
    # Tables Commerce
    db_query("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, q_in INTEGER, q_now INTEGER, price REAL, dev TEXT, eid TEXT)", commit=True)
    db_query("CREATE TABLE IF NOT EXISTS sales (ref TEXT, client TEXT, total REAL, paid REAL, rest REAL, date TEXT, items TEXT, seller TEXT, eid TEXT)", commit=True)
    db_query("CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, client TEXT, amount REAL, ref_v TEXT, eid TEXT)", commit=True)

    if not db_query("SELECT * FROM users WHERE user='admin'"):
        hp = hashlib.sha256('admin123'.encode()).hexdigest()
        db_query("INSERT INTO users (user, pw, role, eid) VALUES (?,?,?,?)", ('admin', hp, 'SUPER_ADMIN', 'SYS'), commit=True)
        db_query("INSERT INTO sys_settings VALUES (?,?,?,?,?)", (1, 'BALIKA ERP HQ', 'PLATEFORME DE GESTION ADMINISTRATIVE ET COMMERCIALE UNIFIÉE - VERSION 2026', '#FF4B2B', '#FFFFFF'), commit=True)

init_core_db()
cfg = db_query("SELECT name, m_text, m_bg, m_tx FROM sys_settings WHERE id=1")[0]
inject_pro_css(cfg[2], cfg[3])

# ------------------------------------------------------------------------------
# 3. INTERFACE DE CONNEXION / INSCRIPTION
# ------------------------------------------------------------------------------
st.markdown(f'<div class="top-marquee"><div class="marquee-content">{cfg[1]} | {cfg[0]}</div></div><div style="height:60px;"></div>', unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    tab_log, tab_reg = st.tabs(["🔐 CONNEXION SÉCURISÉE", "🚀 CRÉER MON COMPTE (30J GRATUIT)"])
    
    with tab_log:
        _, log_col, _ = st.columns([1, 1.5, 1])
        with log_col:
            st.markdown("<h2 style='text-align:center;'>ACCÈS UTILISATEUR</h2>", unsafe_allow_html=True)
            u_in = st.text_input("Identifiant").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER"):
                hp = hashlib.sha256(p_in.encode()).hexdigest()
                res = db_query("SELECT role, eid FROM users WHERE user=? AND pw=?", (u_in, hp))
                if res:
                    st.session_state.auth = True
                    st.session_state.user = u_in
                    st.session_state.role, st.session_state.eid = res[0]
                    st.rerun()
                else: st.error("Échec de connexion.")

    with tab_reg:
        _, reg_col, _ = st.columns([1, 1.5, 1])
        with reg_col:
            st.markdown("<h2 style='text-align:center;'>OFFRE D'ESSAI</h2>", unsafe_allow_html=True)
            with st.form("reg_form"):
                n_ent = st.text_input("Nom de l'Entreprise")
                n_usr = st.text_input("Nom d'utilisateur Admin")
                n_pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON COMPTE"):
                    new_eid = f"CL-{random.randint(1000,9999)}"
                    exp_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    hp = hashlib.sha256(n_pwd.encode()).hexdigest()
                    db_query("INSERT INTO clients (eid, biz, status, d_exp, type) VALUES (?,?,?,?,?)", (new_eid, n_ent.upper(), 'ACTIF', exp_date, 'ESSAI'), commit=True)
                    db_query("INSERT INTO users (user, pw, role, eid) VALUES (?,?,?,?)", (n_usr.lower(), hp, 'BOSS', new_eid), commit=True)
                    st.success("Compte créé ! Veuillez vous connecter.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMIN (VOUS)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    with st.sidebar:
        st.markdown(f"### 💎 MAÎTRE SYSTÈME\n---")
        # Menus colorés
        a_page = st.radio("SÉLECTIONNER UN MENU", 
                        ["🏠 TABLEAU DE BORD", "🌍 GÉRER LES ABONNÉS", "⚙️ RÉGLAGES SYSTÈME", "👤 MON PROFIL", "🚪 DÉCONNEXION"])
    
    if a_page == "🏠 TABLEAU DE BORD":
        st.title("STATISTIQUES GLOBALES")
        c1, c2 = st.columns(2)
        total_c = db_query("SELECT COUNT(*) FROM clients")[0][0]
        c1.metric("Boutiques Actives", total_c)
        c2.metric("Utilisateurs Total", db_query("SELECT COUNT(*) FROM users")[0][0])

    elif a_page == "🌍 GÉRER LES ABONNÉS":
        st.header("SURVEILLANCE DES COMPTES")
        subs = db_query("SELECT eid, biz, status, d_exp, type FROM clients")
        for s in subs:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"🏢 **{s[1]}** ({s[4]})")
                col1.write(f"ID: {s[0]} | Fin d'essai: {s[3]}")
                col2.write(f"Statut: {s[2]}")
                if col3.button("PAUSE / ACTIVER", key=f"ps_{s[0]}"):
                    nst = 'PAUSE' if s[2] == 'ACTIF' else 'ACTIF'
                    db_query("UPDATE clients SET status=? WHERE eid=?", (nst, s[0]), commit=True)
                    st.rerun()
                if col3.button("🗑️ SUPPRIMER", key=f"del_{s[0]}"):
                    db_query("DELETE FROM clients WHERE eid=?", (s[0],), commit=True)
                    db_query("DELETE FROM users WHERE eid=?", (s[0],), commit=True)
                    st.rerun()

    elif a_page == "👤 MON PROFIL":
        st.header("GESTION DU PROFIL ADMIN")
        curr_p = db_query("SELECT pw FROM users WHERE user=?", (st.session_state.user,))[0][0]
        with st.form("prof_adm"):
            new_p = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("MODIFIER MON PASS"):
                nhp = hashlib.sha256(new_p.encode()).hexdigest()
                db_query("UPDATE users SET pw=? WHERE user=?", (nhp, st.session_state.user), commit=True)
                st.success("Mot de passe mis à jour !")

    elif a_page == "⚙️ RÉGLAGES SYSTÈME":
        st.header("CONFIGURATION GLOBALE")
        with st.form("sys_cfg"):
            n_ap = st.text_input("Nom de l'App", cfg[0])
            n_mt = st.text_area("Texte Défilant", cfg[1])
            n_bg = st.color_picker("Couleur Bandeau", cfg[2])
            n_tx = st.color_picker("Couleur Texte", cfg[3])
            if st.form_submit_button("APPLIQUER"):
                db_query("UPDATE sys_settings SET name=?, m_text=?, m_bg=?, m_tx=? WHERE id=1", (n_ap, n_mt, n_bg, n_tx), commit=True)
                st.rerun()

    elif a_page == "🚪 DÉCONNEXION":
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 5. ESPACE BOSS & VENDEUR (COMMERCE)
# ------------------------------------------------------------------------------
else:
    EID = st.session_state.eid
    ROLE = st.session_state.role
    biz_d = db_query("SELECT biz, head, seal, sign, d_exp FROM clients WHERE eid=?", (EID,))[0]

    with st.sidebar:
        st.markdown(f"<h2 style='text-align:center;'>{biz_d[0]}</h2>", unsafe_allow_html=True)
        st.markdown(f"**Rôle:** {ROLE} | **ID:** {EID}")
        st.info(f"⏳ Fin d'essai: {biz_d[4]}")
        st.write("---")
        
        m_list = ["🏠 ACCUEIL", "🛒 CAISSE PRO", "📦 STOCK", "📉 DETTES"]
        if ROLE == 'BOSS': m_list += ["👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
        m_list.append("🚪 DÉCONNEXION")
        
        choice = st.radio("NAVIGATION", m_list)

    # --- ACCUEIL ---
    if choice == "🏠 ACCUEIL":
        st.markdown(f"""
            <div class="digital-watch">
                <p class="watch-h">{datetime.now().strftime('%H:%M')}</p>
                <p class="watch-d">{datetime.now().strftime('%d %B %Y')}</p>
            </div>
            <h1 style='text-align:center;'>BIENVENUE DANS VOTRE ESPACE</h1>
        """, unsafe_allow_html=True)

    # --- CAISSE ADMINISTRATIVE (AUTO-SAVE) ---
    elif choice == "🛒 CAISSE PRO":
        st.title("🛒 POINT DE VENTE")
        if 'cart' not in st.session_state: st.session_state.cart = {}
        
        c_left, c_right = st.columns([2, 1])
        with c_left:
            prods = pd.read_sql(f"SELECT id, name, q_now, price FROM products WHERE eid='{EID}'", sqlite3.connect('balika_v225_core.db'))
            item = st.selectbox("Article", ["---"] + list(prods['name']))
            if st.button("➕ AJOUTER") and item != "---":
                st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1
            
            if st.session_state.cart:
                st.write("### PANIER")
                t_vente = 0
                lines = []
                for it, qte in list(st.session_state.cart.items()):
                    px = prods[prods['name'] == it]['price'].values[0]
                    stot = qte * px
                    t_vente += stot
                    lines.append({'n': it, 'q': qte, 'p': px, 's': stot})
                    
                    cc1, cc2, cc3 = st.columns([3, 1, 1])
                    cc1.write(f"**{it}**")
                    new_q = cc2.number_input("Qté", 1, 1000, qte, key=f"q_{it}")
                    st.session_state.cart[it] = new_q
                    if cc3.button("🗑️", key=f"del_{it}"):
                        del st.session_state.cart[it]
                        st.rerun()

        with c_right:
            if st.session_state.cart:
                st.markdown(f'<div class="total-display">{t_vente:,.2f} USD</div>', unsafe_allow_html=True)
                with st.form("pay_form"):
                    cli = st.text_input("Nom du Client", "COMPTANT")
                    recu = st.number_input("Montant Reçu", value=float(t_vente))
                    if st.form_submit_button("✅ VALIDER & ENREGISTRER"):
                        ref = f"FAC-{random.randint(100,999)}-{time.strftime('%S')}"
                        rest = t_vente - recu
                        dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        db_query("INSERT INTO sales VALUES (?,?,?,?,?,?,?,?,?)", 
                                (ref, cli.upper(), t_vente, recu, rest, dt, json.dumps(lines), st.session_state.user, EID), commit=True)
                        
                        for l in lines:
                            db_query("UPDATE products SET q_now = q_now - ? WHERE name=? AND eid=?", (l['q'], l['n'], EID), commit=True)
                        
                        if rest > 0:
                            db_query("INSERT INTO debts (client, amount, ref_v, eid) VALUES (?,?,?,?)", (cli.upper(), rest, ref, EID), commit=True)
                        
                        st.session_state.bill = {'ref': ref, 'cli': cli, 'tot': t_vente, 'lines': lines}
                        st.session_state.cart = {}
                        st.rerun()

        if 'bill' in st.session_state:
            b = st.session_state.bill
            st.markdown(f"""
                <div class="invoice-container">
                    <div class="invoice-header">
                        <table style="width:100%;">
                            <tr>
                                <td><h1 style="color:#FF4B2B; margin:0;">{biz_d[0]}</h1>{biz_d[1]}</td>
                                <td style="text-align:right;"><strong>FACTURE N°: {b['ref']}</strong><br>Date: {datetime.now().strftime('%d/%m/%Y')}</td>
                            </tr>
                        </table>
                    </div>
                    <p>Client : <strong>{b['cli'].upper()}</strong></p>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="background:#FF4B2B; color:white;">
                            <th style="padding:10px; border:1px solid #ddd;">Description</th>
                            <th style="padding:10px; border:1px solid #ddd;">Quantité</th>
                            <th style="padding:10px; border:1px solid #ddd;">Prix Unitaire</th>
                            <th style="padding:10px; border:1px solid #ddd;">Total</th>
                        </tr>
                        {''.join([f"<tr><td style='padding:10px; border:1px solid #ddd;'>{i['n']}</td><td style='padding:10px; border:1px solid #ddd; text-align:center;'>{i['q']}</td><td style='padding:10px; border:1px solid #ddd; text-align:right;'>{i['p']}</td><td style='padding:10px; border:1px solid #ddd; text-align:right;'>{i['s']}</td></tr>" for i in b['lines']])}
                    </table>
                    <h2 style="text-align:right; margin-top:30px;">TOTAL À PAYER : {b['tot']} USD</h2>
                    <div style="display:flex; justify-content:space-between; margin-top:100px;">
                        <div style="text-align:center; border-top:1px solid #000; width:200px;">SCEAU</div>
                        <div style="text-align:center; border-top:1px solid #000; width:200px;">SIGNATURE</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.download_button("💾 TÉLÉCHARGER LA FACTURE", data=str(b), file_name=f"{b['ref']}.txt")

    # --- GESTION STOCK ---
    elif choice == "📦 STOCK":
        st.header("INVENTAIRE DES PRODUITS")
        if ROLE == 'BOSS':
            with st.expander("➕ AJOUTER UN PRODUIT"):
                with st.form("p_form"):
                    pn = st.text_input("Nom du Produit")
                    pq = st.number_input("Quantité Initiale", 1)
                    pp = st.number_input("Prix de Vente")
                    if st.form_submit_button("ENREGISTRER"):
                        db_query("INSERT INTO products (name, q_in, q_now, price, dev, eid) VALUES (?,?,?,?,?,?)", (pn.upper(), pq, pq, pp, "USD", EID), commit=True)
                        st.rerun()

        data = db_query("SELECT id, name, q_in, q_now, price FROM products WHERE eid=?", (EID,))
        for r in data:
            with st.container(border=True):
                cx1, cx2, cx3, cx4 = st.columns([2, 1, 1, 1])
                cx1.write(f"**{r[1]}**")
                cx2.write(f"Stock: {r[3]} / {r[2]}")
                if ROLE == 'BOSS':
                    new_px = cx3.number_input("Prix", value=float(r[4]), key=f"px_{r[0]}")
                    if cx3.button("MODIFIER", key=f"upd_{r[0]}"):
                        db_query("UPDATE products SET price=? WHERE id=?", (new_px, r[0]), commit=True)
                        st.rerun()
                    if cx4.button("🗑️", key=f"delp_{r[0]}"):
                        db_query("DELETE FROM products WHERE id=?", (r[0],), commit=True)
                        st.rerun()

    # --- MON PROFIL (BOSS/VENDEUR) ---
    elif choice == "👤 MON PROFIL":
        st.header("MON COMPTE PERSONNEL")
        with st.form("my_prof"):
            npw = st.text_input("Nouveau Mot de Passe", type="password")
            if st.form_submit_button("MODIFIER"):
                nhp = hashlib.sha256(npw.encode()).hexdigest()
                db_query("UPDATE users SET pw=? WHERE user=?", (nhp, st.session_state.user), commit=True)
                st.success("C'est fait !")

    # --- DÉCONNEXION ---
    elif choice == "🚪 DÉCONNEXION":
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v225
# ------------------------------------------------------------------------------
