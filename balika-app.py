# ==============================================================================
# BALIKA ERP ULTIMATE v751 - SYSTÈME ERP SaaS COMPLET
# COMPREND : SaaS, CAISSE, DETTES, STOCK, VENDEURS, AUDIT & CONFIGURATION
# DESIGN : ORANGE-NOIR | MARQUEE FIXE | ZÉRO CADRE BLANC | MOBILE FRIENDLY
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import io
import base64
import time
from PIL import Image

# ------------------------------------------------------------------------------
# 1. CONFIGURATION SYSTÈME CORE (v751)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v751", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State pour la persistance
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'notifs': [], 'audit_trail': []
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQLite avec gestion de verrouillage (WAL Mode)"""
    try:
        with sqlite3.connect('balika_pro_v751.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password):
    """Cryptage des mots de passe"""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. INITIALISATION DES TABLES (SCHÉMA v751 - 100% PRÉSERVÉ)
# ------------------------------------------------------------------------------
def init_db():
    # Table Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Table Configuration Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT, montant_paye REAL DEFAULT 0.0)""")
    
    # Table Inventaire
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, categorie TEXT DEFAULT 'GÉNÉRAL')""")
    
    # Table Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")
    
    # Table Journal d'Audit
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                date TEXT, ent_id TEXT)""")

    # Insertion Admin Maître (Si inexistant)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP v751', '16/01/2026'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS IMMERSIVE (ZÉRO CADRE BLANC & MARQUEE)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_data = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
if cfg_data:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = cfg_data[0]
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    /* Design Global Dégradé */
    .stApp {{
        background: linear-gradient(135deg, #FF4B2B 0%, #FF8008 100%);
        background-attachment: fixed;
        color: white !important;
    }}

    /* MARQUEE FIXE HAUT DE PAGE */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #39FF14; height: 50px;
        z-index: 999999; border-bottom: 2px solid white;
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-content {{
        display: inline-block; white-space: nowrap;
        animation: marquee-move 20s linear infinite;
        font-family: 'Courier New', monospace; font-size: 20px; font-weight: bold;
    }}
    @keyframes marquee-move {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Suppression des cadres blancs sur les inputs */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important; border: 1px solid white !important;
        color: white !important;
    }}
    input {{ color: white !important; font-weight: bold !important; }}
    
    /* Boutons de commande Bleus */
    .stButton>button {{
        background: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 50px; width: 100%;
        border: 2px solid white !important; transition: 0.3s;
    }}
    .stButton>button:hover {{ background: #003399 !important; transform: scale(1.02); }}

    /* Montre Digitale */
    .clock-container {{
        background: rgba(0,0,0,0.4); padding: 30px; border-radius: 20px;
        border: 3px solid white; text-align: center; margin: 20px auto; max-width: 500px;
    }}
    .clock-h {{ font-size: 60px; font-weight: 900; color: #FFD700; margin: 0; }}

    /* Cadre Total Caisse */
    .total-box {{
        background: #000; border: 4px solid #39FF14; padding: 20px;
        border-radius: 15px; color: #39FF14; font-size: 40px;
        font-weight: bold; text-align: center; margin: 20px 0;
    }}
    
    /* Sidebar style */
    [data-testid="stSidebar"] {{ background-color: #f8f9fa !important; }}
    [data-testid="stSidebar"] * {{ color: black !important; font-weight: bold; }}
    </style>

    <div class="marquee-wrapper">
        <div class="marquee-content">
             ✨ {C_NOM} : {C_MSG} | 💹 TAUX: {C_TX} CDF/USD | 📅 {datetime.now().strftime('%d/%m/%Y')} | SYSTÈME BALIKA v751
        </div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# Sécurité SaaS : Blocage si compte suspendu
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 ACCÈS BLOQUÉ. CONTACTEZ LE SERVICE TECHNIQUE BALIKA.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE DE CONNEXION (LOGIQUE FIXÉE)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown("<h1 style='text-align:center;'>🔐 TERMINAL BALIKA</h1>", unsafe_allow_html=True)
        t_login, t_signup = st.tabs(["🔑 CONNEXION", "📝 CRÉER MON ERP"])
        
        with t_login:
            u_name = st.text_input("Identifiant").lower().strip()
            u_pass = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_name,), fetch=True)
                if res and make_hashes(u_pass) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_name, 'role':res[0][1], 'ent_id':res[0][2]})
                    run_db("INSERT INTO logs (user, action, date, ent_id) VALUES (?,?,?,?)", (u_name, "LOGIN", datetime.now().strftime("%d/%m/%Y %H:%M"), res[0][2]))
                    st.success("Connexion réussie...")
                    time.sleep(0.5)
                    st.rerun()
                else: st.error("ERREUR : Identifiants invalides.")
        
        with t_signup:
            with st.form("f_reg"):
                st.subheader("Nouvelle Instance ERP")
                s_ent = st.text_input("Nom de l'Entreprise")
                s_tel = st.text_input("Numéro WhatsApp")
                s_usr = st.text_input("Identifiant Admin").lower().strip()
                s_pas = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON COMPTE"):
                    if s_ent and s_usr and s_pas:
                        check = run_db("SELECT * FROM users WHERE username=?", (s_usr,), fetch=True)
                        if not check:
                            new_id = f"E-{random.randint(1000, 9999)}"
                            # Création Utilisateur
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                                   (s_usr, make_hashes(s_pas), "ADMIN", new_id, s_tel))
                            # Création Config
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, taux, message, date_inscription) VALUES (?,?,?,?,?,?)", 
                                   (new_id, s_ent.upper(), s_tel, 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ COMPTE CRÉÉ ! Connectez-vous maintenant.")
                        else: st.warning("Cet identifiant existe déjà.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    # Photo de profil dynamique
    p_data = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if p_data and p_data[0][0]: st.image(p_data[0][0], width=120)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        m = ["🏠 ACCUEIL", "🌍 ABONNÉS", "📊 AUDIT", "👤 PROFIL"]
    elif ROLE == "ADMIN":
        m = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 PROFIL"]
    else: # VENDEUR
        m = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "👤 PROFIL"]

    for item in m:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. PAGE D'ACCUEIL (DASHBOARD AVEC MONTRE)
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.title("TABLEAU DE BORD")
    
    st.markdown(f"""
        <center>
            <div class="clock-container">
                <p class="clock-h">{datetime.now().strftime('%H:%M:%S')}</p>
                <p style="font-size:20px; color:white;">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    v_cumul = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{v_cumul:,.2f} $")
    d_cumul = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES À RÉCUPÉRER", f"{d_cumul:,.2f} $")
    s_count = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", s_count)

# ------------------------------------------------------------------------------
# 7. MODULE CAISSE (VERSION v199+)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        col_v1, col_v2 = st.columns(2)
        v_devise = col_v1.selectbox("Monnaie", ["USD", "CDF"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        c_sel, c_add = st.columns([3, 1])
        choix = c_sel.selectbox("Choisir Produit", ["---"] + list(p_dict.keys()))
        if c_add.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_net = 0.0
            items_list = []
            for art, qte in list(st.session_state.panier.items()):
                px_base = p_dict[art]['px']
                dv_base = p_dict[art]['dv']
                
                if dv_base == "USD" and v_devise == "CDF": px_final = px_base * C_TX
                elif dv_base == "CDF" and v_devise == "USD": px_final = px_base / C_TX
                else: px_final = px_base
                
                stot = px_final * qte
                total_net += stot
                items_list.append({'art': art, 'qte': qte, 'pu': px_final, 'st': stot})
                
                r1, r2, r3 = st.columns([3, 1, 0.5])
                r1.write(f"**{art}**")
                st.session_state.panier[art] = r2.number_input("Qté", 1, p_dict[art]['st'], value=qte, key=f"q_{art}")
                if r3.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="total-box">TOTAL : {total_net:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("f_valide"):
                f_cl = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                f_pay = st.number_input("MONTANT PAYÉ", value=float(total_net))
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    ref_f = f"F-{random.randint(1000, 9999)}"
                    reste_f = total_net - f_pay
                    date_f = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                           (ref_f, f_cl, total_net, f_pay, reste_f, v_devise, date_f, USER, ENT_ID, json.dumps(items_list)))
                    
                    if reste_f > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_cl, reste_f, v_devise, ref_f, ENT_ID, json.dumps([{'d': date_f, 'p': f_pay}])))
                    
                    for i in items_list:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref': ref_f, 'cl': f_cl, 'tot': total_net, 'pay': f_pay, 'dev': v_devise, 'items': items_list, 'date': date_f}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # Facture Card
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac': None}))
        st.markdown(f"""
            <div style="background:white; color:black; padding:30px; border-radius:10px; font-family:monospace; max-width:500px; margin:auto;">
                <center><h2>{C_NOM}</h2><p>{C_ADR}<br>{C_TEL}</p><hr>
                <h3>FACTURE {f['ref']}</h3><p>Client: {f['cl']}<br>Date: {f['date']}</p></center>
                <table style="width:100%;">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table><hr>
                <h2 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Payé: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 8. MODULE STOCK (MODIFICATION SÉCURISÉE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE")
    with st.expander("➕ NOUVEL ARTICLE"):
        with st.form("f_stock"):
            s_nom = st.text_input("Désignation").upper()
            s_qty = st.number_input("Quantité", 1)
            s_prx = st.number_input("Prix", 0.0)
            s_dev = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (s_nom, s_qty, s_prx, s_dev, ENT_ID))
                st.rerun()
    
    st.write("### LISTE DES PRODUITS")
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            c_s1, c_s2, c_s3, c_s4 = st.columns([3, 1, 1, 0.5])
            c_s1.write(f"**{sn}**")
            c_s2.write(f"Stock: {sq}")
            n_px = c_s3.number_input("Prix", value=float(sp), key=f"p_{sid}")
            if c_s3.button("💾", key=f"s_{sid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, sid))
                st.rerun()
            if c_s4.button("🗑️", key=f"d_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE VENDEURS (NOUVEAU - v195+)
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENDEURS" and ROLE == "ADMIN":
    st.header("👥 ÉQUIPE DE VENTE")
    with st.form("f_vendeur"):
        v_user = st.text_input("Identifiant Vendeur").lower().strip()
        v_pass = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            if v_user and v_pass:
                check = run_db("SELECT * FROM users WHERE username=?", (v_user,), fetch=True)
                if not check:
                    run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                           (v_user, make_hashes(v_pass), "VENDEUR", ENT_ID))
                    st.success("Vendeur ajouté !")
                    st.rerun()
                else: st.warning("ID déjà pris.")
    
    st.write("---")
    vendeurs = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for v_u, v_s in vendeurs:
        c_v1, c_v2 = st.columns([3, 1])
        c_v1.write(f"👤 {v_u.upper()} (Statut: {v_s})")
        if c_v2.button("SUPPRIMER", key=f"del_v_{v_u}"):
            run_db("DELETE FROM users WHERE username=?", (v_u,))
            st.rerun()

# ------------------------------------------------------------------------------
# 10. MODULE DETTES (SOLDE AUTOMATIQUE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.header("📉 CRÉANCES CLIENTS")
    d_rows = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    if not d_rows:
        st.success("Aucune dette en cours.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in d_rows:
            with st.expander(f"🔴 {dcl} : {dmt:,.2f} {ddv}"):
                v_pay = st.number_input("Versement", 0.0, float(dmt), key=f"pay_{did}")
                if st.button("ENREGISTRER", key=f"btn_p_{did}"):
                    n_mt = dmt - v_pay
                    h = json.loads(dhi)
                    h.append({'d': datetime.now().strftime("%d/%m"), 'p': v_pay})
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_mt, json.dumps(h), did))
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_pay, v_pay, drf, ENT_ID))
                    if n_mt <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 11. MODULE RÉGLAGES (FIX MARQUEE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION")
    with st.form("f_cfg"):
        e_nom = st.text_input("Nom Entreprise", C_NOM)
        e_msg = st.text_area("Message Défilant", C_MSG)
        e_tx = st.number_input("Taux de change", value=C_TX)
        e_adr = st.text_input("Adresse", C_ADR)
        e_tel = st.text_input("WhatsApp", C_TEL)
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", 
                   (e_nom.upper(), e_msg, e_tx, e_adr, e_tel, ENT_ID))
            st.success("Réglages mis à jour !")
            st.rerun()

# ------------------------------------------------------------------------------
# 12. MODULE PROFIL (PHOTO & PASS)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL")
    p_info = run_db("SELECT full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    with st.container(border=True):
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            n_fn = st.text_input("Nom Complet", p_info[0])
            n_tl = st.text_input("Téléphone", p_info[1])
            n_img = st.file_uploader("Photo", type=["jpg", "png"])
        with c_p2:
            n_pw = st.text_input("Nouveau Pass", type="password")
            n_pc = st.text_input("Confirmer Pass", type="password")
        if st.button("METTRE À JOUR"):
            if n_pw and n_pw == n_pc: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pw), USER))
            if n_img: run_db("UPDATE users SET photo=? WHERE username=?", (n_img.getvalue(), USER))
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (n_fn, n_tl, USER))
            st.success("Profil actualisé !"); st.rerun()

# ------------------------------------------------------------------------------
# 13. MODULE SaaS (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION SaaS")
    # Ajout du message global via Super Admin
    with st.expander("📢 DIFFUSER UN MESSAGE GLOBAL"):
        msg_g = st.text_input("Message pour tous les abonnés")
        if st.button("DÉPLOYER"):
            run_db("UPDATE config SET message=?", (msg_g,))
            st.success("Message déployé !")
    
    abos = run_db("SELECT ent_id, nom_ent, status, montant_paye FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for eid, en, es, em in abos:
        with st.container(border=True):
            col_a1, col_a2, col_a3 = st.columns([2, 1, 1])
            col_a1.write(f"🏢 **{en}** ({eid})")
            col_a2.write(f"Status: {es} | Payé: {em}$")
            if col_a3.button("PAUSE/ACTIF", key=eid):
                ns = "PAUSE" if es == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid))
                st.rerun()

# ------------------------------------------------------------------------------
# 14. MODULE RAPPORTS & AUDIT
# ------------------------------------------------------------------------------
elif st.session_state.page == "RAPPORTS" or st.session_state.page == "AUDIT":
    st.header("📊 HISTORIQUE & AUDIT")
    if ROLE == "SUPER_ADMIN":
        logs = run_db("SELECT * FROM logs ORDER BY id DESC LIMIT 100", fetch=True)
        st.table(pd.DataFrame(logs, columns=["ID", "User", "Action", "Date", "Entité"]))
    else:
        ventes = run_db("SELECT date_v, ref, client, total, paye, reste FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
        st.dataframe(pd.DataFrame(ventes, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste"]), use_container_width=True)

# FIN DU CODE v751 (+750 LIGNES DE LOGIQUE ERP)
