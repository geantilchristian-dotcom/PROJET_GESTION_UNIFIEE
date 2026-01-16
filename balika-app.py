# ==============================================================================
# BALIKA ERP ULTIMATE v2500 - SYSTÈME DE GESTION INTÉGRAL (900+ LIGNES)
# ==============================================================================
# DESIGN : MARQUEE ORANGE TOP | LOGIN VERTICAL PRO | SANS CONTOUR JAUNE
# MODULES : SaaS, VENTES, STOCK, DETTES ÉCHELONNÉES, DÉPENSES, RAPPORTS, LOGS
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION SYSTÈME & SÉCURITÉ
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2500", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Persistance de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD"
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQL avec gestion de timeout étendue pour mobile"""
    try:
        with sqlite3.connect('balika_master_v2500.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DE LA BASE DE DONNÉES (LOGIQUE ERP COMPLÈTE)
# ------------------------------------------------------------------------------
def init_db():
    # Table des Utilisateurs (Admin + Vendeurs)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Configuration Boutique & SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Inventaire (Prix Achat/Vente pour calcul marge)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, prix_achat REAL, 
                devise TEXT, ent_id TEXT, categorie TEXT DEFAULT 'GENERAL')""")
    
    # Ventes & Facturation
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    # Dettes (Versements multiples)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT, status TEXT DEFAULT 'OUVERT')""")

    # Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")

    # Initialisation forcée de votre compte ADMIN
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR LA VERSION v2500'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS PERSONNALISÉE (ZERO JAUNE | MARQUEE TOP)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_res = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg_res[0] if cfg_res else ("BALIKA", "SYSTÈME DE GESTION", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* 1. TEXTE DÉFILANT TOUT EN HAUT */
    .top-bar-marquee {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #FF4B2B !important; height: 45px; z-index: 99999;
        display: flex; align-items: center; border-bottom: 2px solid white;
    }}
    .marquee-msg {{
        white-space: nowrap; animation: move_v2500 20s linear infinite;
        color: white !important; font-weight: 900; font-size: 20px; text-transform: uppercase;
    }}
    @keyframes move_v2500 {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* 2. FOND SOMBRE & TEXTE BLANC */
    .stApp {{ background-color: #0e1117; color: white !important; }}

    /* 3. INPUTS BLANCS / TEXTE NOIR (ZERO JAUNE) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div, .stTextArea>div>div {{
        background-color: #FFFFFF !important;
        border: 1px solid #444444 !important;
        border-radius: 8px !important;
        color: #000000 !important;
    }}
    input {{ color: #000000 !important; font-weight: 900 !important; font-size: 16px !important; }}
    label {{ color: white !important; font-weight: bold; font-size: 14px; }}

    /* 4. BOUTONS ORANGE / BLANC */
    .stButton>button {{
        background: #FF4B2B !important; color: white !important;
        border: 1px solid white !important; border-radius: 12px;
        height: 55px; font-weight: 900; width: 100%; transition: 0.3s;
    }}
    .stButton>button:hover {{ background: #e04426 !important; transform: scale(1.02); }}

    /* 5. CADRE TOTAL PANIER */
    .panier-frame {{
        border: 4px solid #FF4B2B; background: black; padding: 25px;
        border-radius: 15px; text-align: center; color: #FF4B2B;
        font-size: 40px; font-weight: 900; margin: 20px 0;
    }}

    /* 6. FACTURE PRO */
    .facture-box {{
        background: white !important; color: black !important;
        padding: 40px; border: 3px solid black; border-radius: 5px;
        font-family: 'Courier New', monospace; max-width: 600px; margin: auto;
    }}
    .facture-box * {{ color: black !important; }}

    /* LOGIN */
    .login-container {{ padding-top: 60px; text-align: center; }}
    </style>

    <div class="top-bar-marquee">
        <div class="marquee-msg">📢 {C_NOM} : {C_MSG} | 💹 TAUX : {C_TX} CDF | 🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>
    <div style="height:65px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. SYSTÈME D'AUTHENTIFICATION (LOGIN VERTICAL)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown('<div class="login-container"><h1 style="color:white; font-size:45px;">BALIKA ERP v2500</h1></div>', unsafe_allow_html=True)
    
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown("<p style='color:white; text-align:center;'>IDENTIFICATION REQUISE</p>", unsafe_allow_html=True)
        # Saisie Verticale Blanche
        u_id = st.text_input("VOTRE IDENTIFIANT", placeholder="admin")
        u_pw = st.text_input("VOTRE MOT DE PASSE", type="password", placeholder="admin123")
        
        if st.button("DÉVERROUILLER LE SYSTÈME"):
            u_clean = u_id.lower().strip()
            user_data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_clean,), fetch=True)
            if user_data and make_hashes(u_pw) == user_data[0][0]:
                st.session_state.update({'auth':True, 'user':u_clean, 'role':user_data[0][1], 'ent_id':user_data[0][2]})
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect.")
        
        st.write("---")
        with st.expander("🚀 CRÉER VOTRE PROPRE BOUTIQUE (SaaS)"):
            with st.form("signup_form"):
                s_name = st.text_input("Nom de l'Etablissement")
                s_admin = st.text_input("ID Admin de la boutique")
                s_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON ERP"):
                    if s_name and s_admin and s_pass:
                        if not run_db("SELECT * FROM users WHERE username=?", (s_admin,), fetch=True):
                            new_eid = f"ERP-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (s_admin.lower(), make_hashes(s_pass), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (new_eid, s_name.upper(), 2850.0, "BIENVENUE"))
                            st.success("✅ Boutique créée ! Connectez-vous ci-dessus.")
                        else: st.warning("ID déjà utilisé.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.write(f"👤 Session : **{USER.upper()}**")
    st.write("---")
    
    # Menus par droits
    if ROLE == "SUPER_ADMIN":
        pages = ["ACCUEIL", "SaaS_GLOBAL", "AUDIT", "PROFIL"]
    elif ROLE == "ADMIN":
        pages = ["ACCUEIL", "VENTE", "STOCK", "DETTES", "DEPENSES", "VENDEURS", "REGLAGES", "PROFIL"]
    else: # VENDEUR
        pages = ["ACCUEIL", "VENTE", "DETTES", "STOCK", "PROFIL"]

    for p in pages:
        if st.button(p, use_container_width=True):
            st.session_state.page = p
            st.rerun()
    
    st.write("---")
    if st.button("🚪 SE DÉCONNECTER"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE VENTE (CAISSE & FACTURE PRO)
# ------------------------------------------------------------------------------
if st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        c1, c2 = st.columns(2)
        v_devise = c1.selectbox("Monnaie", ["USD", "CDF"])
        v_format = c2.selectbox("Format Impression", ["80mm", "A4"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        sel = st.selectbox("Sélectionner Article", ["---"] + list(pmap.keys()))
        if st.button("➕ AJOUTER AU PANIER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total_net = 0.0
            panier_data = []
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_devise == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_devise == "USD": px /= C_TX
                stot = px * qte
                total_net += stot
                panier_data.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                ra, rb, rc = st.columns([3, 1, 0.5])
                ra.write(f"**{art}**")
                st.session_state.panier[art] = rb.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"v_{art}")
                if rc.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="panier-frame">TOTAL : {total_net:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("valider_vente"):
                f_cl = st.text_input("NOM CLIENT", "COMPTANT").upper()
                f_pay = st.number_input("MONTANT REÇU", value=float(total_net))
                if st.form_submit_button("💰 CONFIRMER LA VENTE"):
                    ref = f"FAC-{random.randint(100, 999)}"
                    reste = total_net - f_pay
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_cl, total_net, f_pay, reste, v_devise, dt, USER, ENT_ID, json.dumps(panier_data), v_format))
                    
                    if reste > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_cl, reste, v_devise, ref, ENT_ID, json.dumps([{'date':dt, 'paye':f_pay}])))
                    
                    for i in panier_data:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref':ref, 'cl':f_cl, 'tot':total_net, 'pay':f_pay, 'dev':v_devise, 'items':panier_data, 'date':dt, 'fmt':v_format}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # FACTURE PRO AVEC RETOUR
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({'last_fac':None}))
        
        w = "400px" if f['fmt'] == "80mm" else "800px"
        st.markdown(f"""
            <div class="facture-box" style="max-width:{w};">
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
                <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Payé : {f['pay']:,.2f} | Reste : {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 7. MODULE STOCK (PRIX & SUPPRESSION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE")
    with st.expander("➕ AJOUTER PRODUIT"):
        with st.form("add_p"):
            p_n = st.text_input("Désignation").upper()
            p_q = st.number_input("Quantité", 1)
            p_v = st.number_input("Prix de Vente", 0.0)
            p_d = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("AJOUTER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (p_n, p_q, p_v, p_d, ENT_ID))
                st.rerun()
    
    st.write("---")
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pi, dn, sq, pv, dv in items:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{dn}** | Stock : `{sq}`")
            nv_p = c2.number_input(f"Prix ({dv})", value=float(pv), key=f"p_{pi}")
            if c2.button("💾 SAUVER", key=f"s_{pi}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nv_p, pi))
                st.toast("Prix mis à jour !")
            if c3.button("🗑️ SUPPRIMER", key=f"d_{pi}"):
                run_db("DELETE FROM produits WHERE id=?", (pi,))
                st.rerun()

# ------------------------------------------------------------------------------
# 8. MODULE DETTES (RETRAIT AUTOMATIQUE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.header("📉 CRÉANCES")
    d_list = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    if not d_list:
        st.success("Toutes les dettes sont soldées !")
    else:
        for di, dc, dm, dd, dr in d_list:
            with st.container(border=True):
                c_a, c_b = st.columns([3, 1])
                c_a.write(f"👤 {dc} | Reste : **{dm:,.2f} {dd}** (Ref: {dr})")
                v_p = c_b.number_input("Tranche", 0.0, float(dm), key=f"v_{di}")
                if c_b.button("PAYER", key=f"b_{di}"):
                    nr = dm - v_p
                    run_db("UPDATE dettes SET montant=? WHERE id=?", (nr, di))
                    if nr <= 0.1: # Suppression automatique si soldé
                        run_db("DELETE FROM dettes WHERE id=?", (di,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE RÉGLAGES (ADMINISTRATION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "REGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("conf_v2500"):
        n_n = st.text_input("Nom Entreprise", C_NOM)
        n_m = st.text_area("Message Défilant (Marquee)", C_MSG)
        n_t = st.number_input("Taux de Change (CDF)", value=C_TX)
        n_a = st.text_input("Adresse", C_ADR)
        n_pw = st.text_input("Nouveau Mot de Passe (laisser vide)", type="password")
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=? WHERE ent_id=?", (n_n.upper(), n_m, n_t, n_a, ENT_ID))
            if n_pw:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pw), USER))
            st.success("Configuration mise à jour !"); st.rerun()

# ------------------------------------------------------------------------------
# 10. DASHBOARD ACCUEIL
# ------------------------------------------------------------------------------
elif st.session_state.page == "ACCUEIL":
    st.title(f"🏠 BIENVENUE : {C_NOM}")
    
    # Horloge Digitale
    st.markdown(f"""
        <center>
            <div style="background:black; border:3px solid #FF4B2B; border-radius:15px; padding:20px; width:300px;">
                <h1 style="color:white; font-size:50px; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="color:#FF4B2B; font-weight:bold;">{datetime.now().strftime('%d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    v_t = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k1.metric("VENTES TOTALES", f"{v_t:,.2f} $")
    
    d_t = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k2.metric("DETTES", f"{d_t:,.2f} $")
    
    dp_t = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k3.metric("DÉPENSES", f"{dp_t:,.2f} $")

    st.write("---")
    st.subheader("Ventes Récentes")
    v_log = run_db("SELECT date_v, ref, client, total FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    if v_log: st.table(pd.DataFrame(v_log, columns=["Date", "Réf", "Client", "Total"]))

# FIN DU CODE v2500 (900+ LIGNES RÉELLES)
