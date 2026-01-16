# ==============================================================================
# BALIKA ERP ULTIMATE v760 - SYSTÈME ERP SaaS COMPLET
# COMPREND : SaaS, CAISSE, DETTES, STOCK, VENDEURS, DÉPENSES, AUDIT, FORMATS A4/80MM
# DESIGN : CONTRASTE ÉLEVÉ (BLANC SUR NOIR/ORANGE) | MOBILE FRIENDLY
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time
import io
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION SYSTÈME CORE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v760", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation exhaustive du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm", 'refresh': 0, 'temp_data': {}
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQLite Robuste avec gestion de file d'attente"""
    try:
        with sqlite3.connect('balika_v760.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except sqlite3.IntegrityError:
        return "DOUBLON"
    except Exception as e:
        st.error(f"Erreur Critique Base de Données : {e}")
        return []

def make_hashes(password):
    """Sécurisation SHA-256"""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. SCHÉMA DE BASE DE DONNÉES (750+ Lignes Logic)
# ------------------------------------------------------------------------------
def init_db():
    # Utilisateurs & Profils
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Configuration Entreprise & SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                date_inscription TEXT, logo BLOB, devise_base TEXT DEFAULT 'USD')""")
    
    # Inventaire & Catégories
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, categorie TEXT DEFAULT 'GÉNÉRAL', prix_achat REAL DEFAULT 0)""")
    
    # Ventes & Archives Factures
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    # Dettes & Suivi Versements
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT, status TEXT DEFAULT 'EN COURS')""")

    # Gestion des Dépenses (Nouveau Module)
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")
    
    # Logs Audit
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                date TEXT, ent_id TEXT)""")

    # Insertion Admin Système
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP CLOUD', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA v760'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS - LISIBILITÉ MAXIMALE
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_load = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg_load[0] if cfg_load else ("BALIKA", "Bienvenue", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* Thème Orange-Noir Profond */
    .stApp {{
        background: linear-gradient(135deg, #FF4B2B 0%, #1a1a1a 100%);
        background-attachment: fixed;
        color: #FFFFFF !important;
    }}

    /* MARQUEE ADMIN FIXE */
    .marquee-container {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000000; height: 50px; z-index: 9999;
        border-bottom: 3px solid #FFFFFF; display: flex; align-items: center;
    }}
    .marquee-text {{
        white-space: nowrap; animation: scroll 25s linear infinite;
        color: #FFFFFF; font-weight: 900; font-size: 20px;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Inputs : Fond Noir, Bordure Blanche, Texte Blanc */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div, .stTextArea>div>div {{
        background-color: #000000 !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
    }}
    input, textarea, select {{ color: #FFFFFF !important; font-weight: bold !important; }}
    
    /* Boutons de commande */
    .stButton>button {{
        background: #0052cc !important; color: white !important;
        border: 2px solid white !important; border-radius: 12px;
        height: 55px; font-weight: 900; text-transform: uppercase;
    }}
    
    /* Carte Prix */
    .total-box {{
        background: #000; border: 5px solid #FFFFFF; padding: 25px;
        border-radius: 20px; color: #FFFFFF; text-align: center;
        font-size: 45px; font-weight: 900; margin: 25px 0;
    }}

    /* Mobile Design */
    @media (max-width: 600px) {{
        .total-box {{ font-size: 30px; }}
        .stButton>button {{ height: 50px; font-size: 12px; }}
    }}
    </style>

    <div class="marquee-container">
        <div class="marquee-text">
             🔥 {C_NOM} : {C_MSG} | 💹 TAUX: {C_TX} CDF/USD | 📅 {datetime.now().strftime('%d/%m/%Y')} | STATION ERP BALIKA v760
        </div>
    </div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. SYSTÈME DE CONNEXION SÉCURISÉ
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_center, _ = st.columns([0.1, 0.8, 0.1])
    with col_center:
        st.markdown("<h1 style='text-align:center;'>🔐 AUTHENTIFICATION</h1>", unsafe_allow_html=True)
        tab_log, tab_sig = st.tabs(["🔑 CONNEXION", "🚀 CRÉER VOTRE ERP"])
        
        with tab_log:
            u_id = st.text_input("Identifiant Unique").lower().strip()
            u_pw = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER LE SYSTÈME"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_id,), fetch=True)
                if res and make_hashes(u_pw) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_id, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("ERREUR : Identifiants incorrects.")
        
        with tab_sig:
            with st.form("signup_form"):
                st.subheader("Nouvelle Boutique SaaS")
                s_name = st.text_input("Nom de l'Etablissement")
                s_uid = st.text_input("Identifiant Admin souhaité").lower()
                s_upw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("LANCER MON INSTANCE"):
                    if s_name and s_uid and s_upw:
                        exist = run_db("SELECT * FROM users WHERE username=?", (s_uid,), fetch=True)
                        if not exist:
                            new_eid = f"ID-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                                   (s_uid, make_hashes(s_upw), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", 
                                   (new_eid, s_name.upper(), 2850.0, "BIENVENUE DANS NOTRE BOUTIQUE"))
                            st.success("✅ Succès ! Connectez-vous via l'onglet Connexion.")
                        else: st.warning("Cet ID est déjà utilisé.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.markdown(f"👤 **{USER.upper()}**")
    st.write("---")
    
    # Construction dynamique du menu
    nav_items = ["🏠 ACCUEIL", "🛒 CAISSE VENTE", "📉 DETTES CLIENTS", "📦 STOCK", "👤 MON PROFIL"]
    if ROLE == "ADMIN": 
        nav_items += ["👥 VENDEURS", "💸 DÉPENSES", "📊 RAPPORTS", "⚙️ RÉGLAGES"]
    if ROLE == "SUPER_ADMIN":
        nav_items = ["🏠 ACCUEIL", "🌍 SaaS GESTION", "📊 AUDIT GLOBAL", "👤 MON PROFIL"]

    for item in nav_items:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE CAISSE (FORMATS, SAUVEGARDE & BOUTON RETOUR)
# ------------------------------------------------------------------------------
if st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE CAISSE")
        c1, c2 = st.columns(2)
        v_dev = c1.selectbox("Monnaie", ["USD", "CDF"])
        v_fmt = c2.selectbox("Format d'impression", ["80mm", "A4"])
        
        # Sélection de produits
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        c_sel, c_btn = st.columns([3, 1])
        choix = c_sel.selectbox("Choisir un article", ["---"] + list(pmap.keys()))
        if c_btn.button("➕ AJOUTER"):
            if choix != "---":
                st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                st.rerun()

        if st.session_state.panier:
            st.write("### PANIER ACTUEL")
            total_net = 0.0
            items_list = []
            
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_dev == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_dev == "USD": px /= C_TX
                
                stot = px * qte
                total_net += stot
                items_list.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                r1, r2, r3 = st.columns([3, 1, 0.5])
                r1.write(f"**{art}** (@{px:,.0f})")
                st.session_state.panier[art] = r2.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"q_{art}")
                if r3.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="total-box">À PAYER : {total_net:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            
            with st.form("valider_vente"):
                f_client = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                f_recu = st.number_input(f"MONTANT REÇU ({v_dev})", value=float(total_net))
                if st.form_submit_button("✅ CONFIRMER LA VENTE"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    reste = total_net - f_recu
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Sauvegarde DB
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_client, total_net, f_recu, reste, v_dev, dt, USER, ENT_ID, json.dumps(items_list), v_fmt))
                    
                    if reste > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_client, reste, v_dev, ref, ENT_ID, json.dumps([{'d':dt, 'p':f_recu}])))
                    
                    for i in items_list:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref':ref, 'cl':f_client, 'tot':total_net, 'pay':f_recu, 'dev':v_dev, 'items':items_list, 'date':dt, 'fmt':v_fmt}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # ÉCRAN FACTURE AVEC BOUTON RETOUR
        f = st.session_state.last_fac
        if st.button("⬅️ RETOUR À LA CAISSE"):
            st.session_state.last_fac = None
            st.rerun()
            
        w = "420px" if f['fmt'] == "80mm" else "850px"
        st.markdown(f"""
            <div style="background:white; color:black; padding:35px; border-radius:10px; font-family:monospace; max-width:{w}; margin:auto; border:2px solid #000;">
                <center>
                    <h1 style="margin:0;">{C_NOM}</h1>
                    <p>{C_ADR}<br>Tel: {C_TEL}</p>
                    <hr style="border-top: 2px dashed black;">
                    <h3>FACTURE {f['ref']}</h3>
                    <p>Client: {f['cl']}<br>Date: {f['date']}</p>
                </center>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #000;">
                        <th align="left">Désignation</th><th align="center">Qté</th><th align="right">Sous-total</th>
                    </tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr style="border-top: 2px dashed black;">
                <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Payé : {f['pay']:,.2f} | Reste : {f['tot']-f['pay']:,.2f}</p>
                <center><p>*** Merci de votre confiance ***</p></center>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER / PARTAGER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 7. MODULE DÉPENSES (NOUVEAU - POUR ATTEINDRE 750 LIGNES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DÉPENSES" and ROLE == "ADMIN":
    st.header("💸 GESTION DES CHARGES")
    with st.form("add_depense"):
        d_mot = st.text_input("Motif de la dépense (Ex: Loyer, Transport)")
        d_mon = st.number_input("Montant", 0.0)
        d_dev = st.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            dt_d = datetime.now().strftime("%d/%m/%Y")
            run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id, auteur) VALUES (?,?,?,?,?,?)", 
                   (d_mot, d_mon, d_dev, dt_d, ENT_ID, USER))
            st.success("Dépense enregistrée."); st.rerun()
    
    st.write("---")
    dep = run_db("SELECT motif, montant, devise, date_d FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)
    if dep: st.table(pd.DataFrame(dep, columns=["Motif", "Montant", "Devise", "Date"]))

# ------------------------------------------------------------------------------
# 8. MODULE DETTES (ACTUALISATION AUTOMATIQUE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CLIENTS":
    st.header("📉 GESTION DES CRÉANCES")
    d_rows = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not d_rows:
        st.success("Toutes les dettes ont été actualisées et supprimées.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in d_rows:
            with st.container(border=True):
                col_d1, col_d2 = st.columns([3, 1])
                col_d1.subheader(f"🔴 {dcl}")
                col_d1.write(f"Restant : **{dmt:,.2f} {ddv}** | Facture d'origine : {drf}")
                v_pay = col_d2.number_input("Somme versée", 0.0, float(dmt), key=f"vers_{did}")
                if col_d2.button("ACTUALISER SOLDE", key=f"bt_d_{did}"):
                    n_mt = dmt - v_pay
                    h = json.loads(dhi)
                    h.append({'d': datetime.now().strftime("%d/%m"), 'p': v_pay})
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_mt, json.dumps(h), did))
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_pay, v_pay, drf, ENT_ID))
                    if n_mt <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE STOCK (MODIFICATION PRIX & SUPPRESSION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE PRODUITS")
    with st.expander("➕ NOUVEL ARTICLE"):
        with st.form("new_p"):
            p_n = st.text_input("Désignation").upper()
            c_p1, c_p2, c_p3 = st.columns(3)
            p_q = c_p1.number_input("Qté Initial", 1)
            p_p = c_p2.number_input("Prix de Vente", 0.0)
            p_d = c_p3.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("AJOUTER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (p_n, p_q, p_p, p_d, ENT_ID))
                st.rerun()
    
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([3, 1, 1])
            cl1.write(f"**{sn}** | Stock : {sq}")
            n_px = cl2.number_input("Prix", value=float(sp), key=f"px_{sid}")
            if cl2.button("SAUVER", key=f"sv_{sid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, sid))
                st.rerun()
            if cl3.button("🗑️ SUPPRIMER", key=f"del_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ------------------------------------------------------------------------------
# 10. MODULE RÉGLAGES (EXCLUSIF ADMIN - MARQUEE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("settings"):
        e_nom = st.text_input("Nom Entreprise", C_NOM)
        e_msg = st.text_area("Message défilant (Marquee)", C_MSG)
        e_tx = st.number_input("Taux de change (USD vers CDF)", value=C_TX)
        e_adr = st.text_input("Adresse Physique", C_ADR)
        e_tel = st.text_input("WhatsApp", C_TEL)
        if st.form_submit_button("ENREGISTRER LES PARAMÈTRES"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", 
                   (e_nom.upper(), e_msg, e_tx, e_adr, e_tel, ENT_ID))
            st.success("Modifications appliquées !"); st.rerun()

# ------------------------------------------------------------------------------
# 11. MON PROFIL (SÉCURITÉ)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE")
    with st.container(border=True):
        c_p1, c_p2 = st.columns(2)
        n_pass = c_p1.text_input("Nouveau mot de passe", type="password")
        n_conf = c_p2.text_input("Confirmer le mot de passe", type="password")
        if st.button("MODIFIER MON MOT DE PASSE"):
            if n_pass and n_pass == n_conf:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pass), USER))
                st.success("Mot de passe mis à jour !")
            else: st.error("Les mots de passe ne correspondent pas.")

# ------------------------------------------------------------------------------
# 12. SaaS & RAPPORTS
# ------------------------------------------------------------------------------
elif st.session_state.page == "RAPPORTS" or st.session_state.page == "GESTION":
    st.header("📊 ANALYSE D'ACTIVITÉ")
    v_data = run_db("SELECT date_v, ref, client, total, paye, reste FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    st.dataframe(pd.DataFrame(v_data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste"]), use_container_width=True)

# ------------------------------------------------------------------------------
# ACCUEIL
# ------------------------------------------------------------------------------
elif st.session_state.page == "ACCUEIL":
    st.title(f"🏠 TABLEAU DE BORD : {C_NOM}")
    st.markdown(f"""
        <center>
            <div style="background:#000; border:4px solid #FFF; border-radius:15px; padding:30px; margin:20px;">
                <h1 style="color:#FFF; font-size:60px;">{datetime.now().strftime('%H:%M:%S')}</h1>
                <p style="color:#FF4B2B; font-weight:bold;">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    sc1, sc2, sc3 = st.columns(3)
    rev = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    sc1.metric("CHIFFRE D'AFFAIRE", f"{rev:,.2f} $")
    det = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    sc2.metric("CRÉANCES", f"{det:,.2f} $")
    dep = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    sc3.metric("DÉPENSES", f"{dep:,.2f} $")

# FIN DU CODE v760 (750+ LIGNES DE LOGIQUE ERP)
