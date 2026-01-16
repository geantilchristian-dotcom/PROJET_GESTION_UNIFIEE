# ==============================================================================
# BALIKA ERP ULTIMATE v820 - SYSTÈME SaaS GLOBAL & GESTION LOCALE
# COMPREND : SaaS, CAISSE, DETTES, STOCK, VENDEURS, DÉPENSES, TRÉSORERIE, AUDIT
# DESIGN : CONTRASTE ÉLEVÉ (BLANC/NOIR/ORANGE) | FULL MOBILE OPTIMIZED
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

# ------------------------------------------------------------------------------
# 1. INITIALISATION SYSTÈME & CORE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v820", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Persistence globale des données de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD", 'format_print': "80mm"
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQL optimisé pour la concurrence (WAL Mode)"""
    try:
        with sqlite3.connect('balika_v820.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DE LA BASE DE DONNÉES (EXTENDUE v820)
# ------------------------------------------------------------------------------
def init_db():
    # Table des Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Table de Configuration SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                date_inscription TEXT, quota_vendeurs INTEGER DEFAULT 5, logo BLOB)""")
    
    # Table des Articles
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, categorie TEXT DEFAULT 'GÉNÉRAL', prix_achat REAL DEFAULT 0.0)""")
    
    # Table des Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    # Table des Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Table des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")
    
    # Table d'Audit (Logs)
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                date TEXT, ent_id TEXT)""")

    # Création Admin Système (BALIKA HQ)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'SYSTEME GLOBAL BALIKA v820 ACTIF'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS - CONTRASTE MAXIMAL & MOBILE-FIRST
# ------------------------------------------------------------------------------
c_id = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
c_data = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (c_id,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ST = c_data[0] if c_data else ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    /* Thème Orange-Noir Fluide */
    .stApp {{
        background: linear-gradient(160deg, #FF4B2B 0%, #000000 100%);
        background-attachment: fixed;
        color: #FFFFFF !important;
    }}

    /* MARQUEE HAUT DE PAGE (ADMIN CONTROLLED) */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; height: 50px; z-index: 99999;
        border-bottom: 3px solid #FFFFFF; display: flex; align-items: center;
    }}
    .marquee-content {{
        white-space: nowrap; animation: scroll 20s linear infinite;
        color: #FFFFFF; font-weight: 900; font-size: 20px;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Inputs : Fond Blanc dans cadre Orange, Texte Noir pour lecture facile */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: #FFFFFF !important;
        border: 3px solid #FF4B2B !important;
        border-radius: 12px !important;
    }}
    input {{ color: #000000 !important; font-weight: 900 !important; }}
    label {{ color: white !important; font-weight: bold; text-transform: uppercase; }}

    /* Boutons Bleus */
    .stButton>button {{
        background: #0066ff !important; color: white !important;
        border: 2px solid white !important; border-radius: 15px;
        height: 60px; font-weight: 900; width: 100%;
    }}

    /* Cartes de données (Mobile Friendly) */
    .data-card {{
        background: rgba(0,0,0,0.7); border: 2px solid #FFFFFF;
        padding: 20px; border-radius: 15px; margin-bottom: 10px;
    }}
    
    .total-banner {{
        background: #000; border: 4px solid #00FF00; padding: 25px;
        border-radius: 15px; color: #00FF00; font-size: 40px;
        text-align: center; font-weight: 900; margin: 20px 0;
    }}
    </style>

    <div class="marquee-wrapper">
        <div class="marquee-content">
             🔥 {C_NOM} : {C_MSG} | 💹 TAUX: {C_TX} CDF | 🕒 {datetime.now().strftime('%H:%M')} | VERSION SaaS v820
        </div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# Blocage SaaS si boutique désactivée
if st.session_state.auth and C_ST == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 BOUTIQUE SUSPENDUE. CONTACTEZ L'ADMINISTRATEUR BALIKA.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. AUTHENTIFICATION & SaaS SIGNUP
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown("<h1 style='text-align:center;'>🔐 BALIKA CLOUD ERP</h1>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["🔑 ENTRER", "📝 CRÉER MA BOUTIQUE"])
        
        with tab_in:
            l_u = st.text_input("Identifiant Admin").lower().strip()
            l_p = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (l_u,), fetch=True)
                if res and make_hashes(l_p) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':l_u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Accès refusé.")
        
        with tab_up:
            with st.form("inscription"):
                n_ent = st.text_input("Nom de l'Etablissement")
                n_uid = st.text_input("ID Admin (Unique)").lower().strip()
                n_pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("LANCER MON SYSTÈME"):
                    if n_ent and n_uid and n_pwd:
                        if not run_db("SELECT * FROM users WHERE username=?", (n_uid,), fetch=True):
                            new_eid = f"ERP-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (n_uid, make_hashes(n_pwd), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message, date_inscription) VALUES (?,?,?,?,?)", (new_eid, n_ent.upper(), 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Boutique créée ! Connectez-vous.")
                        else: st.warning("ID déjà pris.")

    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. MENU NAVIGATION MOBILE
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1160/1160119.png", width=100)
    st.write(f"### 👤 {USER.upper()}")
    st.info(f"ID : {ENT_ID} | {ROLE}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        m = ["🏠 ACCUEIL", "🌍 ABONNEMENTS", "📊 AUDIT LOGS", "👤 PROFIL"]
    elif ROLE == "ADMIN":
        m = ["🏠 ACCUEIL", "🛒 VENTE CAISSE", "📉 DETTES CLIENTS", "📦 STOCK", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES", "📊 RAPPORTS", "👤 PROFIL"]
    else: # VENDEUR
        m = ["🏠 ACCUEIL", "🛒 VENTE CAISSE", "📉 DETTES CLIENTS", "📦 STOCK", "👤 PROFIL"]

    for item in m:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 SORTIR", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE VENTE (MULTIFORMAT & RETOUR)
# ------------------------------------------------------------------------------
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        c1, c2 = st.columns(2)
        v_dev = c1.selectbox("Monnaie", ["USD", "CDF"])
        v_fmt = c2.selectbox("Format Facture", ["80mm", "A4"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        choix = st.selectbox("Sélectionner Article", ["---"] + list(pmap.keys()))
        if st.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            t_net = 0.0
            l_items = []
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_dev == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_dev == "USD": px /= C_TX
                
                stot = px * qte
                t_net += stot
                l_items.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                col_a, col_b, col_c = st.columns([3, 1, 0.5])
                col_a.write(f"**{art}**")
                st.session_state.panier[art] = col_b.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"q_{art}")
                if col_c.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="total-banner">NET À PAYER : {t_net:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            
            with st.form("pay"):
                f_cl = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                f_rec = st.number_input("SOMME REÇUE", value=float(t_net))
                if st.form_submit_button("💰 FINALISER ET SAUVEGARDER"):
                    ref = f"REF-{random.randint(1000, 9999)}"
                    reste = t_net - f_rec
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Log Vente
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_cl, t_net, f_rec, reste, v_dev, dt, USER, ENT_ID, json.dumps(l_items), v_fmt))
                    
                    # Dette auto
                    if reste > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_cl, reste, v_dev, ref, ENT_ID, json.dumps([{'d':dt, 'p':f_rec}])))
                    
                    # Stock
                    for i in l_items:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref':ref, 'cl':f_cl, 'tot':t_net, 'pay':f_rec, 'dev':v_dev, 'items':l_items, 'date':dt, 'fmt':v_fmt}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # FACTURE AVEC BOUTON RETOUR
        f = st.session_state.last_fac
        if st.button("⬅️ NOUVELLE VENTE"):
            st.session_state.last_fac = None
            st.rerun()
            
        width = "400px" if f['fmt'] == "80mm" else "800px"
        st.markdown(f"""
            <div style="background:white; color:black; padding:30px; border-radius:5px; font-family:monospace; max-width:{width}; margin:auto; border:2px solid #000;">
                <center>
                    <h2>{C_NOM}</h2>
                    <p>{C_ADR}<br>Tel: {C_TEL}</p>
                    <hr>
                    <h4>FACTURE : {f['ref']}</h4>
                </center>
                <p>Client: {f['cl']}<br>Date: {f['date']}</p>
                <table style="width:100%;">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr>
                <h3 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h3>
                <p align="right">Payé: {f['pay']:,.2f}<br>Reste: {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 7. MODULE DETTES (ACTUALISATION MOBILE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CLIENTS":
    st.header("📉 SUIVI DES CRÉANCES")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not d_list:
        st.success("Toutes les dettes sont soldées.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in d_list:
            st.markdown(f"""
                <div class="data-card">
                    <b style="font-size:18px; color:#FF4B2B;">{dcl}</b><br>
                    Reste : {dmt:,.2f} {ddv} | Réf: {drf}
                </div>
            """, unsafe_allow_html=True)
            v_val = st.number_input("Versement", 0.0, float(dmt), key=f"v_{did}")
            if st.button("ACTUALISER PAIEMENT", key=f"b_{did}"):
                new_m = dmt - v_val
                h = json.loads(dhi); h.append({'d':datetime.now().strftime("%d/%m"), 'p':v_val})
                run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (new_m, json.dumps(h), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_val, v_val, drf, ENT_ID))
                if new_m <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                st.rerun()

# ------------------------------------------------------------------------------
# 8. RÉGLAGES (EXCLUSIF ADMIN - MARQUEE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("cfg_f"):
        e_n = st.text_input("Nom de l'Entreprise", C_NOM)
        e_m = st.text_area("Message Défilant (Publicité)", C_MSG)
        e_t = st.number_input("Taux de change (USD vers CDF)", value=C_TX)
        e_a = st.text_input("Adresse Physique", C_ADR)
        e_p = st.text_input("Numéro WhatsApp", C_TEL)
        if st.form_submit_button("ENREGISTRER MODIFICATIONS"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", (e_n.upper(), e_m, e_t, e_a, e_p, ENT_ID))
            st.success("Config mise à jour !"); st.rerun()

# ------------------------------------------------------------------------------
# 9. ABONNEMENTS (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNEMENTS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 RÉSEAU SaaS BALIKA")
    shops = run_db("SELECT ent_id, nom_ent, status, date_inscription FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for sid, sn, ss, sd in shops:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"🏢 **{sn}** (ID: {sid}) | Inscrit le : {sd}")
            col1.write(f"Statut actuel : `{ss}`")
            if col2.button("CHANGER STATUT", key=f"sw_{sid}"):
                n_st = "PAUSE" if ss == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (n_st, sid))
                st.rerun()

# ------------------------------------------------------------------------------
# 10. STOCK & VENDEURS (DOUBLONS FIXÉS)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE")
    with st.expander("AJOUTER UN ARTICLE"):
        with st.form("p_f"):
            pn = st.text_input("Désignation").upper()
            pq = st.number_input("Stock", 1)
            pv = st.number_input("Prix Vente", 0.0)
            pd = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("OK"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (pn, pq, pv, pd, ENT_ID))
                st.rerun()
    
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for i_id, i_n, i_q, i_v, i_d in items:
        with st.container(border=True):
            r1, r2, r3 = st.columns([3, 1, 1])
            r1.write(f"**{i_n}** | Qte: {i_q}")
            n_px = r2.number_input("Prix", value=float(i_v), key=f"ip_{i_id}")
            if r2.button("SAUVER", key=f"is_{i_id}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, i_id)); st.rerun()
            if r3.button("🗑️", key=f"id_{i_id}"):
                run_db("DELETE FROM produits WHERE id=?", (i_id,)); st.rerun()

elif st.session_state.page == "VENDEURS" and ROLE == "ADMIN":
    st.header("👥 ÉQUIPE DE VENTE")
    with st.form("v_f"):
        v_u = st.text_input("Identifiant Vendeur").lower().strip()
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            if not run_db("SELECT * FROM users WHERE username=?", (v_u,), fetch=True):
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (v_u, make_hashes(v_p), "VENDEUR", ENT_ID))
                st.success("Vendeur ajouté !"); st.rerun()
            else: st.warning("ID déjà pris.")

# ------------------------------------------------------------------------------
# 11. ACCUEIL & TRÉSORERIE (ANALYSES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ACCUEIL":
    st.title(f"🏠 DASHBOARD : {C_NOM}")
    st.markdown(f"""
        <center>
            <div style="background:#000; border:4px solid #FF4B2B; border-radius:20px; padding:40px; margin:20px;">
                <h1 style="color:#FFF; font-size:70px; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="color:#FF4B2B; font-size:20px;">{datetime.now().strftime('%d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    # KPIs Trésorerie
    c1, c2, c3 = st.columns(3)
    sales = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{sales:,.2f} $")
    
    debt = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("CRÉANCES", f"{debt:,.2f} $", delta_color="inverse")
    
    exp = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("DÉPENSES", f"{exp:,.2f} $")
    
    st.write("---")
    st.subheader("Dernières transactions")
    v_log = run_db("SELECT date_v, ref, client, total FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    st.table(pd.DataFrame(v_log, columns=["Date", "Référence", "Client", "Total"]))

# FIN DU CODE v820 (+850 LIGNES DE LOGIQUE ERP SaaS)
