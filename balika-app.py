import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import base64

# ==============================================================================
# 1. CONFIGURATION & DESIGN (SAUVEGARDE v801 - FIX MARQUEE)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation des états de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_v800_pro.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES
# ==============================================================================
def init_db():
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        ent_id TEXT, status TEXT DEFAULT 'ACTIF', date_creation TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
        taux_global REAL, version TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
        ent_id TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        devise TEXT, ref_v TEXT, ent_id TEXT, status TEXT DEFAULT 'OUVERT')""")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF'))
        
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global, version) VALUES (1, 'BALIKA APP', 'Bienvenue sur BALIKA ERP', 2850.0, 'v801')")

init_db()

# ==============================================================================
# 3. FIX DU MESSAGE DÉFILANT (MARQUEE) & STYLE
# ==============================================================================
config_data = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE_MSG, TX_G = config_data[0] if config_data else ("BALIKA", "Bienvenue", 2850.0)

# Injection CSS forcée pour le Marquee et l'interface Orange
st.markdown(f"""
    <style>
    /* Fond de l'application */
    .stApp {{
        background-color: #FF8C00 !important;
    }}

    /* BANDEAU DÉFILANT FIXÉ EN HAUT */
    .marquee-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #000000;
        color: #00FF00;
        padding: 10px 0;
        z-index: 999999;
        border-bottom: 2px solid #FFFFFF;
        font-family: 'Courier New', Courier, monospace;
        height: 50px;
        display: flex;
        align-items: center;
    }}

    marquee {{
        font-size: 22px;
        font-weight: bold;
    }}

    /* Ajustement pour que le contenu ne soit pas caché par le bandeau */
    .main-content {{
        margin-top: 60px;
    }}

    /* Boutons Bleus Texte Blanc */
    .stButton>button {{
        background-color: #0055ff !important;
        color: white !important;
        border-radius: 12px;
        font-weight: bold;
        height: 60px;
        width: 100%;
        border: 2px solid white;
        font-size: 18px;
    }}

    /* Inputs blancs pour lisibilité */
    div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
    }}
    input {{
        color: #000000 !important;
        font-weight: bold !important;
    }}
    </style>

    <div class="marquee-container">
        <marquee scrollamount="7">{MARQUEE_MSG}</marquee>
    </div>
    <div class="main-content"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SYSTÈME DE CONNEXION / INSCRIPTION
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["CONNEXION", "INSCRIPTION"])
    
    with t1:
        u_log = st.text_input("Utilisateur").lower().strip()
        p_log = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_log,), fetch=True)
            if res:
                if res[0][3] == "PAUSE" and res[0][1] != "SUPER_ADMIN":
                    st.error("Compte suspendu par l'administrateur.")
                elif make_hashes(p_log) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_log, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Mot de passe incorrect.")
            else: st.error("Utilisateur introuvable.")

    with t2:
        u_reg = st.text_input("Créer Identifiant").lower().strip()
        p_reg = st.text_input("Créer Mot de passe", type="password")
        if st.button("S'INSCRIRE MAINTENANT"):
            if run_db("SELECT * FROM users WHERE username=?", (u_reg,), fetch=True):
                st.warning("Cet identifiant existe déjà.")
            else:
                run_db("INSERT INTO users (username, password, role, ent_id, date_creation) VALUES (?,?,?,?,?)",
                       (u_reg, make_hashes(p_reg), "USER", u_reg, datetime.now().strftime("%d/%m/%Y")))
                st.success("Compte créé avec succès !")
    st.stop()

# ==============================================================================
# 5. NAVIGATION SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    st.write("---")
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 MES ABONNÉS", "🛠️ PARAMÈTRES", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORT", "📉 DETTE", "👥 VENDEUR", "⚙️ PARAMETRE"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. LOGIQUE SUPER ADMIN (admin)
# ==============================================================================
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("👥 GESTION DES ABONNÉS")
        abos = run_db("SELECT username, status, date_creation FROM users WHERE role='USER'", fetch=True)
        st.subheader(f"Total des inscriptions : {len(abos)}")
        for u, s, d in abos:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2,1,1,1])
                c1.write(f"**{u.upper()}** (Inscrit le {d})")
                c2.write(f"Statut : {s}")
                if c3.button("SUSPENDRE / ACTIVER", key=f"s_{u}"):
                    new_s = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (new_s, u)); st.rerun()
                if c4.button("SUPPRIMER DÉFINITIVEMENT", key=f"d_{u}"):
                    run_db("DELETE FROM users WHERE username=?", (u)); st.rerun()

    elif st.session_state.page == "PROFIL":
        st.header("👤 MON PROFIL ADMIN")
        nu = st.text_input("Modifier mon Identifiant", value=st.session_state.user)
        np = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("SAUVEGARDER"):
            run_db("UPDATE users SET username=?, password=? WHERE username=?", (nu, make_hashes(np), st.session_state.user))
            st.session_state.user = nu; st.success("Profil mis à jour !")

    elif st.session_state.page == "PARAMÈTRES":
        st.header("🛠️ PARAMÈTRES GLOBAUX")
        na = st.text_input("Nom de l'Application", value=APP_NAME)
        nm = st.text_area("Texte défilant (Marquee)", value=MARQUEE_MSG)
        if st.button("APPLIQUER À TOUS LES UTILISATEURS"):
            run_db("UPDATE system_config SET app_name=?, marquee_text=? WHERE id=1", (na, nm)); st.rerun()

# ==============================================================================
# 7. LOGIQUE UTILISATEUR (LA BOUTIQUE)
# ==============================================================================
else:
    if st.session_state.page == "STOCK":
        st.header("📦 GESTION DU STOCK")
        with st.form("add_prod"):
            c1, c2, c3 = st.columns(3)
            dn = c1.text_input("Désignation Article")
            sq = c2.number_input("Quantité en stock", 1)
            pv = c3.number_input("Prix de vente ($)")
            if st.form_submit_button("AJOUTER AU STOCK"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                       (dn.upper(), sq, pv, "USD", st.session_state.ent_id)); st.rerun()
        
        st.write("---")
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for i, d, q, p in prods:
            with st.container(border=True):
                cl1, cl2, cl3, cl4 = st.columns([3,1,1,1])
                ud = cl1.text_input("Désignation", d, key=f"d_{i}")
                uq = cl2.number_input("Stock", value=q, key=f"q_{i}")
                up = cl3.number_input("Prix $", value=p, key=f"p_{i}")
                if cl4.button("MODIFIER", key=f"b_{i}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (ud.upper(), uq, up, i)); st.rerun()

    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            dev = st.radio("Devise de paiement :", ["USD", "CDF"], horizontal=True)
            items = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {r[0]: (r[1], r[2]) for r in items}
            sel = st.selectbox("Sélectionner Article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER AU PANIER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()

            if st.session_state.panier:
                tot = 0.0
                for a, q in list(st.session_state.panier.items()):
                    px = p_map[a][0]
                    if dev == "CDF": px *= TX_G
                    tot += px * q
                    l1, l2, l3 = st.columns([3,1,1])
                    l1.write(f"**{a}** ({px:,.0f} {dev})")
                    st.session_state.panier[a] = l2.number_input("Quantité", 1, p_map[a][1], value=q, key=f"v_{a}")
                    if l3.button("🗑️", key=f"r_{a}"): del st.session_state.panier[a]; st.rerun()
                
                st.markdown(f"## TOTAL : {tot:,.2f} {dev}")
                cli = st.text_input("Nom du Client", "COMPTANT")
                pay = st.number_input("Montant Reçu", value=float(tot))
                if st.button("VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id) VALUES (?,?,?,?,?,?,?,?,?)",
                           (ref, cli.upper(), tot, pay, tot-pay, dev, datetime.now().strftime("%d/%m/%Y"), st.session_state.user, st.session_state.ent_id))
                    if tot-pay > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cli.upper(), tot-pay, dev, ref, st.session_state.ent_id))
                    for art, qty in st.session_state.panier.items():
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (qty, art, st.session_state.ent_id))
                    st.session_state.last_fac = {"ref": ref, "tot": tot, "dev": dev}; st.session_state.panier = {}; st.rerun()
        else:
            if st.button("⬅️ RETOUR À LA CAISSE"): st.session_state.last_fac = None; st.rerun()
            st.success(f"Vente validée ! Facture {st.session_state.last_fac['ref']}")

    elif st.session_state.page == "DETTE":
        st.header("📉 GESTION DES DETTES")
        dt = run_db("SELECT id, client, montant, devise FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        if not dt: st.info("Aucune dette en cours.")
        for di, dc, dm, dv in dt:
            with st.container(border=True):
                st.write(f"Client: **{dc}** | Reste à payer: **{dm:,.2f} {dv}**")
                vp = st.number_input("Montant Versement", 0.0, float(dm), key=f"p_{di}")
                if st.button("ENREGISTRER LE PAIEMENT", key=f"b_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (vp, di))
                    st.rerun()

    elif st.session_state.page == "RAPPORT":
        st.header("📊 HISTORIQUE DES VENTES")
        if st.button("⬅️ RETOUR"): st.session_state.page = "ACCUEIL"; st.rerun()
        data = run_db("SELECT date_v, ref, client, total, devise, vendeur FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if data:
            st.table(pd.DataFrame(data, columns=["Date", "Référence", "Client", "Total", "Devise", "Vendeur"]))

    elif st.session_state.page == "PARAMETRE":
        st.header("⚙️ PARAMÈTRES BOUTIQUE")
        st.write(f"Identifiant Boutique : {st.session_state.user.upper()}")
        if st.button("Modifier mon mot de passe"):
            st.info("Utilisez l'option de modification dans votre profil.")
