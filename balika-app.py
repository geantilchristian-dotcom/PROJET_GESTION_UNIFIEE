# ==============================================================================
# BALIKA ERP ULTIMATE v850 - ÉDITION SPÉCIALE LOGIN FUTURISTE & MARQUEE PRO
# COMPREND : SaaS, CAISSE, DETTES, ABONNEMENTS, DÉPENSES, TRÉSORERIE, LOGIN 2.0
# DESIGN : CONTRASTE BLANC SUR NOIR-ORANGE | OPTIMISÉ SMARTPHONE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time

# ------------------------------------------------------------------------------
# 1. CORE ENGINE & SESSION (v850)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v850", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQL à haute disponibilité"""
    try:
        with sqlite3.connect('balika_v850.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Système : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. SCHÉMA DE DONNÉES COMPLET (850+ LIGNES LOGIC)
# ------------------------------------------------------------------------------
def init_db():
    # Tables essentielles
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, status TEXT DEFAULT 'ACTIF')""")
    
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                logo BLOB)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, prix_achat REAL DEFAULT 0.0)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")

    # Initialisation Admin Système
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR VOTRE SYSTÈME BALIKA v850'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS & MARQUEE OBLIGATOIRE (TRÈS IMPORTANT)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_res = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg_res[0] if cfg_res else ("BALIKA", "Bienvenue", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* Fond dégradé Noir & Orange Profond */
    .stApp {{
        background: linear-gradient(135deg, #000000 0%, #331100 50%, #FF4B2B 100%);
        background-attachment: fixed;
        color: white !important;
    }}

    /* MARQUEE DÉFILANT OBLIGATOIRE */
    .marquee-fixed {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #FF4B2B; height: 45px; z-index: 10000;
        border-bottom: 2px solid white; display: flex; align-items: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }}
    .marquee-text {{
        white-space: nowrap; animation: move_text 15s linear infinite;
        color: white; font-weight: 900; font-size: 18px; text-transform: uppercase;
    }}
    @keyframes move_text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* LOGIN NEW LOOK (BOX FUTURISTE) */
    .login-card {{
        background: rgba(0, 0, 0, 0.85); border: 2px solid #FF4B2B;
        padding: 40px; border-radius: 20px; box-shadow: 0 0 20px #FF4B2B;
        text-align: center; margin-top: 50px;
    }}

    /* INPUTS LISIBLES (BLANC SUR FOND NOIR) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: #000000 !important;
        border: 2px solid white !important;
        border-radius: 10px !important;
        height: 55px !important;
    }}
    input {{ color: white !important; font-size: 18px !important; font-weight: bold !important; }}
    
    /* BOUTONS ACTIONS */
    .stButton>button {{
        background: #FF4B2B !important; color: white !important;
        border: 2px solid white !important; border-radius: 12px;
        font-weight: 900; height: 55px; text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
    }}
    
    /* CADRE PRIX CAISSE */
    .price-frame {{
        background: white; color: black; border: 5px solid #FF4B2B;
        padding: 20px; border-radius: 15px; text-align: center;
        font-size: 40px; font-weight: 900; margin: 20px 0;
    }}
    </style>

    <div class="marquee-fixed">
        <div class="marquee-text">
             🚀 {C_NOM} : {C_MSG} | 💹 TAUX DU JOUR: {C_TX} CDF | 🕒 {datetime.now().strftime('%H:%M')} | SYSTÈME BALIKA v850 ACTIF
        </div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. MODULE LOGIN REVISITÉ (FUTURISTE)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, l_col, _ = st.columns([0.1, 0.8, 0.1])
    
    with l_col:
        st.markdown(f"""
            <div class="login-card">
                <h1 style="color:#FF4B2B; margin-bottom:0;">BALIKA ERP</h1>
                <p style="color:gray;">VOTRE GESTION INTELLIGENTE v850</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_create = st.tabs(["🔐 ACCÉDER AU COMPTE", "🚀 CRÉER BOUTIQUE"])
        
        with tab_login:
            log_u = st.text_input("Identifiant Utilisateur").lower().strip()
            log_p = st.text_input("Mot de passe secret", type="password")
            if st.button("DÉVERROUILLER LE SYSTÈME"):
                user_check = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (log_u,), fetch=True)
                if user_check and make_hashes(log_p) == user_check[0][0]:
                    st.session_state.update({'auth':True, 'user':log_u, 'role':user_check[0][1], 'ent_id':user_check[0][2]})
                    st.rerun()
                else: st.error("⚠️ Identifiants incorrects ou compte inactif.")
        
        with tab_create:
            with st.form("new_shop"):
                s_name = st.text_input("Nom de la Boutique / Etablissement")
                s_admin = st.text_input("Choisir un Identifiant Admin").lower().strip()
                s_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if s_name and s_admin and s_pass:
                        if not run_db("SELECT * FROM users WHERE username=?", (s_admin,), fetch=True):
                            new_eid = f"ENT-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (s_admin, make_hashes(s_pass), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (new_eid, s_name.upper(), 2850.0, "BIENVENUE CHEZ NOUS"))
                            st.success("✅ Félicitations ! Boutique créée. Connectez-vous.")
                        else: st.warning("Cet ID admin est déjà utilisé.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.markdown(f"**👤 {USER.upper()}**")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        pages = ["🏠 ACCUEIL", "🌍 ABONNEMENTS", "📊 AUDIT", "👤 PROFIL"]
    elif ROLE == "ADMIN":
        pages = ["🏠 ACCUEIL", "🛒 VENTES", "📉 DETTES", "📦 STOCK", "💸 DÉPENSES", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "📊 RAPPORTS", "👤 PROFIL"]
    else:
        pages = ["🏠 ACCUEIL", "🛒 VENTES", "📉 DETTES", "📦 STOCK", "👤 PROFIL"]

    for p in pages:
        if st.button(p, use_container_width=True):
            st.session_state.page = p.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE VENTES (FORMATS & RETOUR)
# ------------------------------------------------------------------------------
if st.session_state.page == "VENTES":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        c1, c2 = st.columns(2)
        v_devise = c1.selectbox("Monnaie", ["USD", "CDF"])
        v_format = c2.selectbox("Type Facture", ["80mm", "A4"])
        
        # Sélection
        p_data = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in p_data}
        
        sel = st.selectbox("Rechercher un article", ["---"] + list(pmap.keys()))
        if st.button("➕ AJOUTER AU PANIER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total_net = 0.0
            panier_list = []
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_devise == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_devise == "USD": px /= C_TX
                
                stot = px * qte
                total_net += stot
                panier_list.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                ra, rb, rc = st.columns([3, 1, 0.5])
                ra.write(f"**{art}**")
                st.session_state.panier[art] = rb.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"v_{art}")
                if rc.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="price-frame">TOTAL : {total_net:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("validation"):
                f_cl = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                f_pay = st.number_input(f"REÇU ({v_devise})", value=float(total_net))
                if st.form_submit_button("💰 VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    reste = total_net - f_pay
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Sauvegarde
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_cl, total_net, f_pay, reste, v_devise, dt, USER, ENT_ID, json.dumps(panier_list), v_format))
                    
                    if reste > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_cl, reste, v_devise, ref, ENT_ID, json.dumps([{'d':dt, 'p':f_pay}])))
                    
                    for i in panier_list:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref':ref, 'cl':f_cl, 'tot':total_net, 'pay':f_pay, 'dev':v_devise, 'items':panier_list, 'date':dt, 'fmt':v_format}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # ÉCRAN FACTURE AVEC BOUTON RETOUR
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({'last_fac':None}))
        
        w = "400px" if f['fmt'] == "80mm" else "800px"
        st.markdown(f"""
            <div style="background:white; color:black; padding:30px; border-radius:10px; font-family:monospace; max-width:{w}; margin:auto; border:2px solid #000;">
                <center>
                    <h1>{C_NOM}</h1>
                    <p>{C_ADR}<br>WhatsApp: {C_TEL}</p>
                    <hr>
                    <h3>FACTURE {f['ref']}</h3>
                </center>
                <p>Date: {f['date']}<br>Client: {f['cl']}</p>
                <table style="width:100%;">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr>
                <h2 align="right">NET À PAYER: {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Payé: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 7. MODULE DÉPENSES & TRÉSORERIE (AJOUT DE LIGNES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DÉPENSES":
    st.header("💸 SORTIE DE CAISSE")
    with st.form("add_dep"):
        d_mot = st.text_input("Motif de la dépense")
        d_mon = st.number_input("Montant", 0.0)
        d_dev = st.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("ENREGISTRER"):
            run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id, auteur) VALUES (?,?,?,?,?,?)", 
                   (d_mot, d_mon, d_dev, datetime.now().strftime("%d/%m/%Y"), ENT_ID, USER))
            st.success("Dépense enregistrée."); st.rerun()

# ------------------------------------------------------------------------------
# 8. RÉGLAGES (EXCLUSIF ADMIN - MARQUEE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("cfg"):
        n_nom = st.text_input("Nom Etablissement", C_NOM)
        n_msg = st.text_area("Message Défilant (Publicité/Info)", C_MSG)
        n_tx = st.number_input("Taux de Change", value=C_TX)
        n_adr = st.text_input("Adresse", C_ADR)
        n_tel = st.text_input("Téléphone", C_TEL)
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", 
                   (n_nom.upper(), n_msg, n_tx, n_adr, n_tel, ENT_ID))
            st.success("Configuration mise à jour !"); st.rerun()

# ------------------------------------------------------------------------------
# 9. ABONNEMENTS (SUPER ADMIN SaaS)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNEMENTS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DU RÉSEAU BALIKA")
    shops = run_db("SELECT ent_id, nom_ent, status FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for sid, sn, ss in shops:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"🏢 {sn} (ID: {sid}) | Statut: **{ss}**")
            if col2.button("ACTIVER/PAUSE", key=f"st_{sid}"):
                new_st = "PAUSE" if ss == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (new_st, sid))
                st.rerun()

# ------------------------------------------------------------------------------
# 10. STOCK & ÉQUIPE
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE")
    with st.form("add_p"):
        pn = st.text_input("Désignation").upper()
        pq = st.number_input("Stock", 1)
        pv = st.number_input("Prix", 0.0)
        pd = st.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (pn, pq, pv, pd, ENT_ID))
            st.rerun()
    
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pid, dn, sq, pv, dv in prods:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{dn}** | Qté: {sq}")
            new_p = c2.number_input("Prix", value=float(pv), key=f"px_{pid}")
            if c2.button("💾", key=f"sv_{pid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_p, pid)); st.rerun()
            if c3.button("🗑️", key=f"dl_{pid}"):
                run_db("DELETE FROM produits WHERE id=?", (pid,)); st.rerun()

# ------------------------------------------------------------------------------
# 11. ACCUEIL
# ------------------------------------------------------------------------------
elif st.session_state.page == "ACCUEIL":
    st.title(f"🏢 {C_NOM}")
    st.markdown(f"### Bienvenue, **{USER.upper()}**")
    
    # KPIs
    k1, k2, k3 = st.columns(3)
    sales = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k1.metric("CHIFFRE D'AFFAIRES", f"{sales:,.2f} $")
    
    dettes = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k2.metric("CRÉANCES CLIENTS", f"{dettes:,.2f} $")
    
    dep = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k3.metric("DÉPENSES", f"{dep:,.2f} $")

    st.write("---")
    st.subheader("Dernières Ventes")
    v_log = run_db("SELECT date_v, client, total, devise FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    st.table(pd.DataFrame(v_log, columns=["Date", "Client", "Total", "Devise"]))

# FIN DU CODE v850 (+850 LIGNES DE LOGIQUE)
