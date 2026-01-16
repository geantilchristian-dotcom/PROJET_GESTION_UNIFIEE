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
# 1. CONFIGURATION & DESIGN (800 LIGNES LOGIQUE)
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
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET SANS ERREUR)
# ==============================================================================
def init_db():
    # Table des Utilisateurs et Abonnés
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        ent_id TEXT, status TEXT DEFAULT 'ACTIF', date_creation TEXT)""")
    
    # Configuration Globale (Gérée par Super Admin)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
        taux_global REAL, version TEXT)""")
    
    # Produits (Stock Utilisateur)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
        ent_id TEXT)""")
    
    # Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT)""")
    
    # Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        devise TEXT, ref_v TEXT, ent_id TEXT, status TEXT DEFAULT 'OUVERT')""")

    # Création Super Admin par défaut (admin / admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF'))
        
    # Correction de l'erreur de syntaxe ici avec une seule ligne propre
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global, version) VALUES (1, 'BALIKA APP', 'Bienvenue', 2850.0, 'v800')")

init_db()

# ==============================================================================
# 3. MOTEUR DE STYLE (ORANGE & BLEU)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 50px;
        z-index: 9999; border-bottom: 2px solid white;
        display: flex; align-items: center; overflow: hidden;
    }}
    marquee {{ font-size: 24px; font-weight: bold; }}
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 60px; width: 100%;
        border: 2px solid white; font-size: 18px;
    }}
    .white-box {{
        background: white; padding: 25px; border-radius: 15px; 
        border: 4px solid black; color: black; margin-bottom: 20px;
    }}
    div[data-baseweb="input"] {{ background-color: #FFFFFF !important; }}
    input {{ color: #000 !important; font-weight: bold !important; }}
    </style>
    <div class="marquee-wrapper"><marquee scrollamount="8">{MARQUEE}</marquee></div>
    <div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. AUTHENTIFICATION (LOGIN / REGISTER)
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["CONNEXION", "INSCRIPTION"])
    
    with t1:
        u_log = st.text_input("Utilisateur").lower()
        p_log = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_log,), fetch=True)
            if res:
                if res[0][3] == "PAUSE" and res[0][1] != "SUPER_ADMIN":
                    st.error("Compte suspendu par l'admin.")
                elif make_hashes(p_log) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_log, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Erreur de mot de passe.")
            else: st.error("Compte inexistant.")

    with t2:
        u_reg = st.text_input("Nouvel Identifiant").lower()
        p_reg = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("CRÉER MON COMPTE"):
            if run_db("SELECT * FROM users WHERE username=?", (u_reg,), fetch=True):
                st.warning("Déjà utilisé.")
            else:
                run_db("INSERT INTO users (username, password, role, ent_id, date_creation) VALUES (?,?,?,?,?)",
                       (u_reg, make_hashes(p_reg), "USER", u_reg, datetime.now().strftime("%d/%m/%Y")))
                st.success("Compte créé ! Connectez-vous.")
    st.stop()

# ==============================================================================
# 5. NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 MES ABONNÉS", "🛠️ PARAMÈTRES", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORT", "📉 DETTE", "👥 VENDEUR", "⚙️ PARAMETRE"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION"):
        st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. ESPACE SUPER ADMIN (admin)
# ==============================================================================
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("👥 GESTION DES ABONNÉS")
        abos = run_db("SELECT username, status, date_creation FROM users WHERE role='USER'", fetch=True)
        st.subheader(f"Total inscrits : {len(abos)}")
        for u, s, d in abos:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2,1,1,1])
                c1.write(f"**{u.upper()}** (Inscrit le {d})")
                c2.write(f"Statut : {s}")
                if c3.button("PAUSE/ACTIVER", key=f"s_{u}"):
                    new_s = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (new_s, u)); st.rerun()
                if c4.button("SUPPRIMER", key=f"d_{u}"):
                    run_db("DELETE FROM users WHERE username=?", (u)); st.rerun()

    elif st.session_state.page == "PROFIL":
        st.header("👤 MON PROFIL ADMIN")
        nu = st.text_input("Nouveau Username", value=st.session_state.user)
        np = st.text_input("Nouveau Password", type="password")
        if st.button("MODIFIER MES ACCÈS"):
            run_db("UPDATE users SET username=?, password=? WHERE username=?", (nu, make_hashes(np), st.session_state.user))
            st.session_state.user = nu; st.success("Fait !")

    elif st.session_state.page == "PARAMÈTRES":
        st.header("🛠️ PARAMÈTRES GÉNÉRAUX")
        na = st.text_input("Nom de l'App (Global)", value=APP_NAME)
        nm = st.text_area("Texte Défilant (Global)", value=MARQUEE)
        if st.button("METTRE À JOUR POUR TOUS"):
            run_db("UPDATE system_config SET app_name=?, marquee_text=? WHERE id=1", (na, nm)); st.rerun()

# ==============================================================================
# 7. ESPACE UTILISATEUR (LA BOUTIQUE)
# ==============================================================================
else:
    if st.session_state.page == "STOCK":
        st.header("📦 GESTION DU STOCK")
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            dn = c1.text_input("Article")
            sq = c2.number_input("Quantité", 1)
            pv = c3.number_input("Prix ($)")
            if st.form_submit_button("AJOUTER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                       (dn.upper(), sq, pv, "USD", st.session_state.ent_id)); st.rerun()
        
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for i, d, q, p in prods:
            with st.container(border=True):
                cl1, cl2, cl3, cl4 = st.columns([3,1,1,1])
                ud = cl1.text_input("Nom", d, key=f"d_{i}")
                uq = cl2.number_input("Qté", value=q, key=f"q_{i}")
                up = cl3.number_input("Prix", value=p, key=f"p_{i}")
                if cl4.button("MODIFIER", key=f"b_{i}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (ud.upper(), uq, up, i)); st.rerun()

    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 CAISSE")
            dev = st.radio("Devise :", ["USD", "CDF"], horizontal=True)
            items = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {r[0]: (r[1], r[2]) for r in items}
            sel = st.selectbox("Article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()

            if st.session_state.panier:
                tot = 0.0
                for a, q in list(st.session_state.panier.items()):
                    px = p_map[a][0]
                    if dev == "CDF": px *= TX_G
                    tot += px * q
                    l1, l2, l3 = st.columns([3,1,1])
                    l1.write(f"**{a}**")
                    st.session_state.panier[a] = l2.number_input("Qté", 1, p_map[a][1], value=q, key=f"v_{a}")
                    if l3.button("🗑️", key=f"r_{a}"): del st.session_state.panier[a]; st.rerun()
                
                st.markdown(f"### TOTAL : {tot:,.2f} {dev}")
                cli = st.text_input("Client", "COMPTANT")
                pay = st.number_input("Payé", value=float(tot))
                if st.button("VALIDER VENTE"):
                    ref = f"FAC-{random.randint(100,999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id) VALUES (?,?,?,?,?,?,?,?,?)",
                           (ref, cli.upper(), tot, pay, tot-pay, dev, datetime.now().strftime("%d/%m/%Y"), st.session_state.user, st.session_state.ent_id))
                    if tot-pay > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cli.upper(), tot-pay, dev, ref, st.session_state.ent_id))
                    for art, qty in st.session_state.panier.items():
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (qty, art, st.session_state.ent_id))
                    st.session_state.last_fac = {"ref": ref, "tot": tot, "dev": dev}; st.session_state.panier = {}; st.rerun()
        else:
            if st.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()
            st.success(f"Facture {st.session_state.last_fac['ref']} validée !")

    elif st.session_state.page == "DETTE":
        st.header("📉 DETTES")
        dt = run_db("SELECT id, client, montant, devise FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv in dt:
            with st.container(border=True):
                st.write(f"Client: {dc} | Reste: {dm} {dv}")
                vp = st.number_input("Versement", 0.0, float(dm), key=f"p_{di}")
                if st.button("PAYER", key=f"b_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (vp, di))
                    st.rerun()

    elif st.session_state.page == "RAPPORT":
        st.header("📊 RAPPORT")
        if st.button("⬅️ RETOUR"): st.session_state.page = "ACCUEIL"; st.rerun()
        data = run_db("SELECT * FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        st.table(pd.DataFrame(data))

    elif st.session_state.page == "PARAMETRE":
        st.header("⚙️ PARAMÈTRES")
        st.write("Gestion de la boutique.")
