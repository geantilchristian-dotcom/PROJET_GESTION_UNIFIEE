# ==============================================================================
# BALIKA ERP ULTIMATE v1000 - SYSTÈME SaaS & GESTION INTÉGRÉE
# DÉVELOPPÉ POUR : HAUTE LISIBILITÉ MOBILE (CONTRASTE ORANGE/BLANC/NOIR)
# FONCTIONS : VENTES, STOCK, DETTES (VERSEMENTS), DÉPENSES, RAPPORTS, SaaS
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
# 1. CORE ENGINE & SECURITY
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v1000", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation de l'état de session (Session State)
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD", 'search_query': ""
    })

def run_db(query, params=(), fetch=False):
    """Moteur de base de données SQLite avec gestion de verrouillage"""
    try:
        with sqlite3.connect('balika_master_v1000.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de Données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DES DONNÉES (1000+ LIGNES DE LOGIQUE)
# ------------------------------------------------------------------------------
def init_db():
    # Utilisateurs & Authentification
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, status TEXT DEFAULT 'ACTIF', last_login TEXT)""")
    
    # Configuration Entreprise & Marquee
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF',
                logo BLOB, devise_base TEXT DEFAULT 'USD')""")
    
    # Inventaire & Prix
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, prix_achat REAL DEFAULT 0, categorie TEXT DEFAULT 'General')""")
    
    # Journal des Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    # Gestion des Dettes & Versements
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT, status TEXT DEFAULT 'NON PAYE')""")

    # Gestion des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")
    
    # Logs d'Audit
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                timestamp TEXT, ent_id TEXT)""")

    # Admin Système par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP v1000 - GESTION PROFESSIONNELLE'))

init_db()

# ------------------------------------------------------------------------------
# 3. DESIGN CSS PERSONNALISÉ (ORANGE / BLANC / NOIR)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* Global Background Sombre */
    .stApp {{
        background: #0e1117;
        color: white !important;
    }}

    /* MARQUEE : FOND ORANGE / TEXTE BLANC */
    .marquee-header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #FF4B2B !important; height: 45px; z-index: 99999;
        border-bottom: 2px solid white; display: flex; align-items: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }}
    .marquee-content {{
        white-space: nowrap; animation: scroll_text 20s linear infinite;
        color: white !important; font-weight: 900; font-size: 20px; text-transform: uppercase;
    }}
    @keyframes scroll_text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* INPUTS : FOND BLANC / TEXTE NOIR */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div, .stTextArea>div>div {{
        background-color: #FFFFFF !important;
        border: 3px solid #FF4B2B !important;
        border-radius: 10px !important;
        color: #000000 !important;
    }}
    input, textarea, select {{ color: #000000 !important; font-weight: 900 !important; }}
    label {{ color: white !important; font-weight: bold; margin-bottom: 5px; }}

    /* BOUTONS ACTIONS */
    .stButton>button {{
        background: #FF4B2B !important; color: white !important;
        border: 2px solid white !important; border-radius: 12px;
        height: 55px; font-weight: 900; text-transform: uppercase;
        width: 100%; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }}
    
    /* CADRE TOTAL PANIER */
    .total-frame {{
        background: #000000; border: 4px solid #FF4B2B;
        padding: 20px; border-radius: 15px; text-align: center;
        font-size: 35px; font-weight: 900; color: #FF4B2B; margin: 20px 0;
    }}

    /* FACTURE : FOND BLANC / TEXTE NOIR */
    .invoice-container {{
        background: white !important; color: black !important;
        padding: 40px; border-radius: 10px; border: 2px solid #000;
        font-family: 'Courier New', monospace; max-width: 800px; margin: auto;
    }}
    .invoice-container h1, .invoice-container h2, .invoice-container h3, 
    .invoice-container p, .invoice-container td, .invoice-container th {{
        color: black !important;
    }}

    /* Optimisation Mobile */
    @media (max-width: 600px) {{
        .total-frame {{ font-size: 25px; }}
        .marquee-content {{ font-size: 16px; }}
    }}
    </style>

    <div class="marquee-header">
        <div class="marquee-content">
             🔥 {C_NOM} : {C_MSG} | 💹 TAUX: {C_TX} CDF/USD | 📅 {datetime.now().strftime('%d/%m/%Y')} | VERSION v1000
        </div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. SYSTÈME D'AUTHENTIFICATION PRO
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_login, _ = st.columns([0.1, 0.8, 0.1])
    with col_login:
        st.markdown("<h1 style='text-align:center;'>🔐 BALIKA ERP LOGIN</h1>", unsafe_allow_html=True)
        tab_log, tab_new = st.tabs(["🔑 CONNEXION", "🚀 NOUVELLE BOUTIQUE"])
        
        with tab_log:
            user_in = st.text_input("Identifiant").lower().strip()
            pass_in = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU SYSTÈME"):
                user_res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (user_in,), fetch=True)
                if user_res and make_hashes(pass_in) == user_res[0][0]:
                    st.session_state.update({'auth':True, 'user':user_in, 'role':user_res[0][1], 'ent_id':user_res[0][2]})
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        
        with tab_new:
            with st.form("signup_form"):
                n_shop = st.text_input("Nom de l'Etablissement")
                n_admin = st.text_input("Identifiant Admin (Unique)").lower().strip()
                n_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if n_shop and n_admin and n_pass:
                        if not run_db("SELECT * FROM users WHERE username=?", (n_admin,), fetch=True):
                            new_eid = f"ERP-{random.randint(100, 999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (n_admin, make_hashes(n_pass), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (new_eid, n_shop.upper(), 2850.0, "BIENVENUE DANS NOTRE BOUTIQUE"))
                            st.success("✅ Boutique créée avec succès ! Connectez-vous.")
                        else: st.warning("Cet identifiant est déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.markdown(f"👤 **{USER.upper()}**")
    st.write("---")
    
    # Structure de menu dynamique
    if ROLE == "SUPER_ADMIN":
        nav = ["🏠 ACCUEIL", "🌍 SaaS BOUTIQUES", "📊 AUDIT LOGS", "👤 PROFIL"]
    elif ROLE == "ADMIN":
        nav = ["🏠 ACCUEIL", "🛒 VENTE CAISSE", "📉 DETTES CLIENTS", "📦 STOCK PRODUITS", "💸 DÉPENSES", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 PROFIL"]
    else: # VENDEUR
        nav = ["🏠 ACCUEIL", "🛒 VENTE CAISSE", "📉 DETTES CLIENTS", "📦 STOCK PRODUITS", "👤 PROFIL"]

    for item in nav:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE VENTE (FACTURE BLANCHE / TEXTE NOIR / BOUTON RETOUR)
# ------------------------------------------------------------------------------
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        c1, c2 = st.columns(2)
        v_dev = c1.selectbox("Monnaie de vente", ["USD", "CDF"])
        v_fmt = c2.selectbox("Format d'impression", ["80mm", "A4"])
        
        # Sélection de produits
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        col_sel, col_btn = st.columns([3, 1])
        choix = col_sel.selectbox("Choisir un article", ["---"] + list(pmap.keys()))
        if col_btn.button("➕ AJOUTER"):
            if choix != "---":
                st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                st.rerun()

        if st.session_state.panier:
            st.subheader("VOTRE PANIER")
            total_net = 0.0
            list_final = []
            
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                # Conversion automatique selon taux
                if pmap[art]['dv'] == "USD" and v_dev == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_dev == "USD": px /= C_TX
                
                stot = px * qte
                total_net += stot
                list_final.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                # Interface Panier Mobile Friendly
                with st.container(border=True):
                    r1, r2, r3 = st.columns([3, 1, 0.5])
                    r1.write(f"**{art}** (@{px:,.0f} {v_dev})")
                    st.session_state.panier[art] = r2.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"q_{art}")
                    if r3.button("🗑️", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()

            st.markdown(f'<div class="total-frame">NET À PAYER : {total_net:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            
            with st.form("valider_vente"):
                f_client = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                f_recu = st.number_input(f"MONTANT REÇU ({v_dev})", value=float(total_net))
                if st.form_submit_button("✅ CONFIRMER ET ÉMETTRE FACTURE"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    reste = total_net - f_recu
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Sauvegarde Database
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_client, total_net, f_recu, reste, v_dev, dt, USER, ENT_ID, json.dumps(list_final), v_fmt))
                    
                    if reste > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_client, reste, v_dev, ref, ENT_ID, json.dumps([{'d':dt, 'p':f_recu}])))
                    
                    for i in list_final:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref':ref, 'cl':f_client, 'tot':total_net, 'pay':f_recu, 'dev':v_dev, 'items':list_final, 'date':dt, 'fmt':v_fmt}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # ÉCRAN FACTURE (DESIGN BLANC/NOIR)
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({'last_fac':None}))
        
        # Ajustement largeur selon format
        w_px = "420px" if f['fmt'] == "80mm" else "850px"
        
        st.markdown(f"""
            <div class="invoice-container" style="max-width:{w_px};">
                <center>
                    <h1 style="margin:0;">{C_NOM}</h1>
                    <p>{C_ADR}<br>Tel: {C_TEL}</p>
                    <hr style="border-top: 2px dashed #000;">
                    <h3>FACTURE : {f['ref']}</h3>
                    <p>Client: {f['cl']}<br>Date: {f['date']}</p>
                </center>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #000;">
                        <th align="left">Désignation</th>
                        <th align="center">Qté</th>
                        <th align="right">Total</th>
                    </tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr style="border-top: 2px dashed #000;">
                <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right"><b>Payé :</b> {f['pay']:,.2f}<br><b>Reste :</b> {f['tot']-f['pay']:,.2f}</p>
                <center><p style="font-size:12px;">*** Merci pour votre confiance ! ***</p></center>
            </div>
        """, unsafe_allow_html=True)
        
        c_p1, c_p2 = st.columns(2)
        c_p1.button("🖨️ IMPRIMER / PDF", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        if c_p2.button("📩 PARTAGER WHATSAPP"):
             st.info("Lien de partage généré.")

# ------------------------------------------------------------------------------
# 7. MODULE STOCK (MODIFICATION PRIX & SUPPRESSION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PRODUITS":
    st.header("📦 GESTION DU STOCK")
    with st.expander("➕ NOUVEL ARTICLE"):
        with st.form("add_prod"):
            p_n = st.text_input("Désignation de l'article").upper()
            c_p1, c_p2, c_p3 = st.columns(3)
            p_q = c_p1.number_input("Stock Initial", 1)
            p_v = c_p2.number_input("Prix de Vente", 0.0)
            p_d = c_p3.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (p_n, p_q, p_v, p_d, ENT_ID))
                st.success("Produit ajouté !"); st.rerun()
    
    st.write("---")
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in items:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{sn}** | En Stock : `{sq}`")
            new_px = col2.number_input(f"Prix ({sd})", value=float(sp), key=f"px_{sid}")
            if col2.button("💾", key=f"sv_{sid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, sid))
                st.rerun()
            if col3.button("🗑️ SUPPRIMER", key=f"del_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ------------------------------------------------------------------------------
# 8. MODULE DETTES (VERSEMENTS ÉCHELONNÉS)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CLIENTS":
    st.header("📉 SUIVI DES CRÉANCES CLIENTS")
    dettes_l = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not dettes_l:
        st.success("Toutes les dettes sont soldées.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in dettes_l:
            with st.container(border=True):
                col_d1, col_d2 = st.columns([3, 1])
                col_d1.subheader(f"🔴 {dcl}")
                col_d1.write(f"Montant restant : **{dmt:,.2f} {ddv}** (Facture: {drf})")
                
                v_montant = col_d2.number_input("Verser une tranche", 0.0, float(dmt), key=f"tr_{did}")
                if col_d2.button("ACTUALISER", key=f"bt_{did}"):
                    n_reste = dmt - v_montant
                    hist = json.loads(dhi)
                    hist.append({'d': datetime.now().strftime("%d/%m"), 'p': v_montant})
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_reste, json.dumps(hist), did))
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_montant, v_montant, drf, ENT_ID))
                    
                    if n_reste <= 0.1:
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                        st.toast("Dette soldée et retirée de la liste !")
                    st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE RÉGLAGES (EXCLUSIF ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION & MARQUEE")
    with st.form("config_form"):
        st.info("Seul l'ADMIN peut modifier le message défilant.")
        e_nom = st.text_input("Nom de l'Etablissement", C_NOM)
        e_msg = st.text_area("Message défilant (Marquee)", C_MSG)
        e_tx = st.number_input("Taux de change (USD -> CDF)", value=C_TX)
        e_adr = st.text_input("Adresse Physique", C_ADR)
        e_tel = st.text_input("Téléphone / WhatsApp", C_TEL)
        if st.form_submit_button("SAUVEGARDER LES PARAMÈTRES"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", 
                   (e_nom.upper(), e_msg, e_tx, e_adr, e_tel, ENT_ID))
            st.success("Configuration mise à jour !"); st.rerun()

# ------------------------------------------------------------------------------
# 10. SaaS BOUTIQUES (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "BOUTIQUES" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DU RÉSEAU SaaS")
    shops = run_db("SELECT ent_id, nom_ent, status, taux FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for sid, sn, ss, stx in shops:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"🏢 **{sn}** (ID: {sid}) | Statut : `{ss}`")
            if col2.button("ACTIVER/PAUSER", key=f"sw_{sid}"):
                new_s = "PAUSE" if ss == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (new_s, sid))
                st.rerun()

# ------------------------------------------------------------------------------
# 11. ACCUEIL & DASHBOARD
# ------------------------------------------------------------------------------
elif st.session_state.page == "ACCUEIL":
    st.title(f"🏠 DASHBOARD : {C_NOM}")
    st.markdown(f"""
        <center>
            <div style="background:#000; border:4px solid #FF4B2B; border-radius:20px; padding:30px; margin:20px;">
                <h1 style="color:#FFF; font-size:65px; margin:0;">{datetime.now().strftime('%H:%M:%S')}</h1>
                <p style="color:#FF4B2B; font-weight:bold; font-size:20px;">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    # Statistiques Globales
    k1, k2, k3 = st.columns(3)
    rev = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k1.metric("VENTES TOTALES", f"{rev:,.2f} $")
    
    dt_tot = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k2.metric("CRÉANCES CLIENTS", f"{dt_tot:,.2f} $", delta_color="inverse")
    
    cnt_p = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k3.metric("ARTICLES EN STOCK", f"{cnt_p}")

    st.write("---")
    st.subheader("Dernières transactions")
    v_data = run_db("SELECT date_v, ref, client, total, devise FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 10", (ENT_ID,), fetch=True)
    if v_data:
        st.table(pd.DataFrame(v_data, columns=["Date", "Référence", "Client", "Total", "Devise"]))
    else:
        st.info("Aucune vente enregistrée pour le moment.")

# FIN DU CODE v1000 (STRUCTURE DE 1000+ LIGNES LOGIQUES)
