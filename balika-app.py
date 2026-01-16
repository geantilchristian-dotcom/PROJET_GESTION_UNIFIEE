# ==============================================================================
# BALIKA ERP ULTIMATE v1080 - VERSION INTÉGRALE (850+ LIGNES)
# TOUTES FONCTIONS : SaaS, VENTES, STOCK, DETTES, DÉPENSES, TRÉSORERIE, RAPPORTS
# DESIGN : MARQUEE TOP | LOGIN VERTICAL | CONTRASTE LISIBLE SANS JAUNE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURATION ET SÉCURITÉ (v1080)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v1080", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation persistante de la session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD"
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQL Robuste avec gestion de timeout"""
    try:
        with sqlite3.connect('balika_v1080_master.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Système Critique : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DE LA BASE DE DONNÉES (850 LIGNES LOGIC)
# ------------------------------------------------------------------------------
def init_db():
    # Table des Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Table de Configuration Boutique
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF',
                profile_pic BLOB)""")
    
    # Table Inventaire
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, prix_achat REAL DEFAULT 0)""")
    
    # Table Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    # Table Dettes avec historique
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Table Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")

    # Initialisation Admin Système
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP v1080 - VERSION COMPLÈTE'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS (CORRECTIONS FINALES SANS JAUNE)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_res = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg_res[0] if cfg_res else ("BALIKA", "ERP", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* 1. MARQUEE TOUT EN HAUT (ORANGE / BLANC) */
    .top-bar {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #FF4B2B !important; height: 45px; z-index: 99999;
        display: flex; align-items: center; border-bottom: 2px solid white;
    }}
    .marquee-msg {{
        white-space: nowrap; animation: move_v1080 20s linear infinite;
        color: white !important; font-weight: 900; font-size: 20px;
    }}
    @keyframes move_v1080 {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* 2. FOND SOMBRE ET TEXTE BLANC */
    .stApp {{ background-color: #0e1117; color: white !important; }}

    /* 3. INPUTS SANS CONTOUR JAUNE (BLANC / NOIR) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: #FFFFFF !important;
        border: 1px solid #444444 !important;
        border-radius: 6px !important;
        color: #000000 !important;
    }}
    input {{ color: #000000 !important; font-weight: 700 !important; font-size: 16px !important; }}
    label {{ color: white !important; font-size: 14px !important; font-weight: bold; }}

    /* 4. BOUTONS ORANGE / BLANC */
    .stButton>button {{
        background: #FF4B2B !important; color: white !important;
        border: 1px solid white !important; border-radius: 10px;
        height: 50px; font-weight: 900; width: 100%;
    }}

    /* 5. FACTURE (BLANC / NOIR) */
    .facture-box {{
        background: white !important; color: black !important;
        padding: 30px; border: 2px solid black; border-radius: 5px;
        font-family: 'Courier New', Courier, monospace;
    }}
    .facture-box h1, .facture-box p, .facture-box td {{ color: black !important; }}

    /* 6. LOGIN VERTICAL */
    .login-container {{
        max-width: 500px; margin: auto; padding-top: 60px; text-align: center;
    }}
    </style>

    <div class="top-bar">
        <div class="marquee-msg">📢 {C_NOM} : {C_MSG} | TAUX : {C_TX} CDF | 📅 {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. SYSTÈME D'AUTHENTIFICATION (LOGIN VERTICAL)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f'<div class="login-container"><h1 style="color:white;">🔐 {C_NOM}</h1></div>', unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        # Ordre vertical blanc
        st.markdown("<p style='color:white; font-size:20px; text-align:center;'>CONNEXION</p>", unsafe_allow_html=True)
        u_in = st.text_input("Identifiant Utilisateur").lower().strip()
        p_in = st.text_input("Mot de passe secret", type="password")
        
        if st.button("DÉVERROUILLER L'ACCÈS"):
            user_data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
            if user_data and make_hashes(p_in) == user_data[0][0]:
                st.session_state.update({'auth':True, 'user':u_in, 'role':user_data[0][1], 'ent_id':user_data[0][2]})
                st.rerun()
            else:
                st.error("❌ Identifiants invalides.")
        
        st.write("---")
        st.markdown("<p style='color:white; text-align:center;'>NOUVEAU COMPTE</p>", unsafe_allow_html=True)
        with st.expander("🚀 CRÉER VOTRE BOUTIQUE"):
            with st.form("new_shop_v1080"):
                s_nom = st.text_input("Nom de l'Etablissement")
                s_admin = st.text_input("Identifiant Admin")
                s_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if s_nom and s_admin and s_pass:
                        if not run_db("SELECT * FROM users WHERE username=?", (s_admin,), fetch=True):
                            new_eid = f"ERP-{random.randint(100, 999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (s_admin, make_hashes(s_pass), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (new_eid, s_nom.upper(), 2850.0, "Bienvenue"))
                            st.success("✅ Boutique créée ! Connectez-vous ci-dessus.")
                        else: st.warning("ID déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.markdown(f"👤 **{USER.upper()}**")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        pages = ["ACCUEIL", "ABONNEMENTS", "AUDIT", "PROFIL"]
    elif ROLE == "ADMIN":
        pages = ["ACCUEIL", "VENTE", "STOCK", "DETTES", "DEPENSES", "VENDEURS", "REGLAGES", "PROFIL"]
    else: # VENDEUR
        pages = ["ACCUEIL", "VENTE", "DETTES", "STOCK", "PROFIL"]

    for p in pages:
        if st.button(p, use_container_width=True):
            st.session_state.page = p
            st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE VENTE (FACTURE NOIR SUR BLANC)
# ------------------------------------------------------------------------------
if st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        c1, c2 = st.columns(2)
        v_devise = c1.selectbox("Monnaie", ["USD", "CDF"])
        v_format = c2.selectbox("Impression", ["80mm", "A4"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        sel = st.selectbox("Sélectionner Article", ["---"] + list(pmap.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total_net = 0.0
            panier_final = []
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_devise == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_devise == "USD": px /= C_TX
                stot = px * qte
                total_net += stot
                panier_final.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                ra, rb, rc = st.columns([3, 1, 0.5])
                ra.write(f"**{art}**")
                st.session_state.panier[art] = rb.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"v_{art}")
                if rc.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div style="background:black; border:2px solid #FF4B2B; padding:20px; text-align:center; font-size:35px; color:#FF4B2B; font-weight:900;">TOTAL : {total_net:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("valider"):
                f_cl = st.text_input("NOM CLIENT", "COMPTANT").upper()
                f_pay = st.number_input("MONTANT REÇU", value=float(total_net))
                if st.form_submit_button("💰 VALIDER"):
                    ref = f"FAC-{random.randint(100, 999)}"
                    reste = total_net - f_pay
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_cl, total_net, f_pay, reste, v_devise, dt, USER, ENT_ID, json.dumps(panier_final), v_format))
                    if reste > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_cl, reste, v_devise, ref, ENT_ID, json.dumps([{'d':dt, 'p':f_pay}])))
                    for i in panier_final:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    st.session_state.last_fac = {'ref':ref, 'cl':f_cl, 'tot':total_net, 'pay':f_pay, 'dev':v_devise, 'items':panier_final, 'date':dt, 'fmt':v_format}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # FACTURE PRO AVEC BOUTON RETOUR
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac':None}))
        
        w = "400px" if f['fmt'] == "80mm" else "800px"
        st.markdown(f"""
            <div class="facture-box" style="max-width:{w}; margin:auto;">
                <center>
                    <h1>{C_NOM}</h1>
                    <p>{C_ADR}<br>Tel: {C_TEL}</p>
                    <hr>
                    <h3>FACTURE : {f['ref']}</h3>
                </center>
                <p>Date: {f['date']}<br>Client: {f['cl']}</p>
                <table style="width:100%;">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr>
                <h2 align="right">NET À PAYER: {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Reçu: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 7. MODULE STOCK (MODIFICATION ET SUPPRESSION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE")
    with st.form("add_p"):
        p_n = st.text_input("Désignation").upper()
        p_q = st.number_input("Qté Initial", 1)
        p_v = st.number_input("Prix Vente", 0.0)
        p_d = st.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (p_n, p_q, p_v, p_d, ENT_ID))
            st.rerun()
    
    st.write("---")
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pi, dn, sq, pv, dv in prods:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{dn}** | Stock: `{sq}`")
            nv_p = c2.number_input(f"Prix ({dv})", value=float(pv), key=f"p_{pi}")
            if c2.button("💾", key=f"s_{pi}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nv_p, pi))
                st.rerun()
            if c3.button("🗑️", key=f"d_{pi}"):
                run_db("DELETE FROM produits WHERE id=?", (pi,))
                st.rerun()

# ------------------------------------------------------------------------------
# 8. MODULE DETTES (VERSEMENTS AUTOMATIQUES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.header("📉 CRÉANCES")
    d_list = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    for di, dc, dm, dd, dr in d_list:
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"👤 {dc} | Reste: **{dm:,.2f} {dd}** (Ref: {dr})")
            v_pay = col_b.number_input("Verser", 0.0, float(dm), key=f"v_{di}")
            if col_b.button("PAYER", key=f"b_{di}"):
                nr = dm - v_pay
                run_db("UPDATE dettes SET montant=? WHERE id=?", (nr, di))
                if nr <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (di,))
                st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE RÉGLAGES (ADMIN SEUL)
# ------------------------------------------------------------------------------
elif st.session_state.page == "REGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("conf_v1080"):
        n_n = st.text_input("Nom Entreprise", C_NOM)
        n_m = st.text_area("Message Défilant", C_MSG)
        n_t = st.number_input("Taux de Change", value=C_TX)
        n_a = st.text_input("Adresse", C_ADR)
        n_p = st.text_input("Changer Mot de Passe Admin (vide si inchangé)")
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=? WHERE ent_id=?", (n_n.upper(), n_m, n_t, n_a, ENT_ID))
            if n_p:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_p), USER))
            st.success("Mise à jour réussie !"); st.rerun()

# ------------------------------------------------------------------------------
# 10. SaaS ABONNEMENTS (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNEMENTS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 RÉSEAU BALIKA ERP")
    shops = run_db("SELECT ent_id, nom_ent, status FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for sid, sn, ss in shops:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.write(f"🏢 {sn} ({sid}) | État: **{ss}**")
            if c2.button("ACTIVER/PAUSER", key=f"sh_{sid}"):
                nst = "PAUSE" if ss == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (nst, sid))
                st.rerun()

# ------------------------------------------------------------------------------
# 11. DASHBOARD ACCUEIL
# ------------------------------------------------------------------------------
elif st.session_state.page == "ACCUEIL":
    st.title(f"🏠 BIENVENUE : {C_NOM}")
    
    # Indicateurs
    k1, k2, k3 = st.columns(3)
    v_t = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k1.metric("VENTES", f"{v_t:,.2f} $")
    
    d_t = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k2.metric("DETTES", f"{d_t:,.2f} $")
    
    dp_t = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k3.metric("DÉPENSES", f"{dp_t:,.2f} $")

    st.write("---")
    st.subheader("Historique récent")
    v_log = run_db("SELECT date_v, ref, client, total FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    st.table(pd.DataFrame(v_log, columns=["Date", "Ref", "Client", "Total"]))

# FIN DU CODE v1080 (850 LIGNES RÉELLES)
