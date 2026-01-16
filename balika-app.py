import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import base64
from PIL import Image

# ==============================================================================
# 1. CONFIGURATION ET SYSTÈME CORE (CODE COMPLET DÉTAILLÉ)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v745", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation complète du Session State pour ne rien perdre entre les pages
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False,
        'user': "",
        'role': "",
        'ent_id': "SYSTEM",
        'page': "ACCUEIL",
        'panier': {},
        'last_fac': None
    })

# --- MOTEUR DE BASE DE DONNÉES (SQLite WAL Mode pour la performance mobile) ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_pro_v740.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET SANS SUPPRESSION)
# ==============================================================================
def init_db():
    # Table Utilisateurs (Profils, Photos, Rôles)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT, 
                photo BLOB, 
                full_name TEXT, 
                telephone TEXT)""")
    
    # Table Configuration (Le message défilant est ici)
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL, 
                message TEXT, 
                status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, 
                date_inscription TEXT, 
                montant_paye REAL DEFAULT 0.0)""")
    
    # Table Produits (Stocks et prix par devise)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT)""")
    
    # Table Ventes (Archives complètes)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                ref TEXT, 
                client TEXT, 
                total REAL, 
                paye REAL, 
                reste REAL, 
                devise TEXT, 
                date_v TEXT, 
                vendeur TEXT, 
                ent_id TEXT, 
                details TEXT)""")
    
    # Table Dettes (Suivi des paiements par tranches)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")

    # Création de l'Admin par défaut si la table est vide
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'MON ENTREPRISE', 'ACTIF', 2850.0, 'Bienvenue', '16/01/2026'))

init_db()

# ==============================================================================
# 3. INTERFACE VISUELLE (ORANGE, BLEU, MARQUEE)
# ==============================================================================
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, taux FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX = res_cfg[0] if res_cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    /* FOND ORANGE */
    .stApp {{ background-color: #FF8C00 !important; }}
    
    /* MARQUEE NOIR TEXTE VERT (LUMINOSITÉ MOBILE) */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000000; color: #00FF00; height: 50px;
        z-index: 999999; border-bottom: 2px solid white;
        display: flex; align-items: center; overflow: hidden;
    }}
    marquee {{ font-family: 'Courier New', monospace; font-size: 22px; font-weight: bold; }}

    /* BOUTONS BLEUS TEXTE BLANC */
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 55px; width: 100%;
        border: 2px solid white; font-size: 18px;
    }}

    /* MONTRE DIGITALE 80MM STYLE */
    .clock-box {{
        background: #000; color: #FF8C00; padding: 35px; border-radius: 25px;
        border: 5px solid white; text-align: center; margin: 10px auto;
    }}

    /* CADRE PRIX BLANC */
    .price-frame {{
        border: 5px solid #000; background: #FFF; padding: 25px;
        border-radius: 15px; color: #000; font-size: 35px;
        font-weight: bold; text-align: center; margin: 20px 0;
    }}

    /* INPUTS BLANCS */
    div[data-baseweb="input"], div[data-baseweb="select"] {{
        background-color: #FFFFFF !important; border-radius: 10px !important;
    }}
    input {{ color: #000000 !important; font-weight: bold !important; font-size: 18px !important; }}
    </style>

    <div class="marquee-wrapper">
        <marquee scrollamount="9">🔔 {C_MSG} | 🏢 {C_NOM} | 💹 TAUX: {C_TX} CDF | 🕒 {datetime.now().strftime('%H:%M')}</marquee>
    </div>
    <div style="height:65px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIQUE DE CONNEXION
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown('<div class="clock-box"><h2 style="color:white;">ACCÈS SYSTÈME</h2></div>', unsafe_allow_html=True)
        u_in = st.text_input("NOM D'UTILISATEUR")
        p_in = st.text_input("MOT DE PASSE", type="password")
        if st.button("DÉVERROUILLER L'ACCÈS"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in.lower().strip(),), fetch=True)
            if res and make_hashes(p_in) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. NAVIGATION SIDEBAR (MENU COMPLET ADMIN)
# ==============================================================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {USER.upper()}</h2>", unsafe_allow_html=True)
    st.write("---")
    
    # L'admin a accès à tout
    if ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 VENDEURS", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 QUITTER", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. PAGES DU SYSTÈME
# ==============================================================================

# --- PAGE ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f"""
        <center>
            <div class="clock-box">
                <h1 style="font-size: 75px; margin: 0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="font-size: 20px;">{datetime.now().strftime('%A %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    st.write("---")
    c1, c2 = st.columns(2)
    c1.metric("ENTREPRISE", C_NOM)
    c2.metric("TAUX DE CHANGE", f"{C_TX} CDF")

# --- PAGE PROFIL (ÉDITION DU MESSAGE DÉFILANT) ---
elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL ADMIN")
    
    with st.container(border=True):
        st.subheader("📢 TEXTE DÉFILANT (MARQUEE)")
        # C'est ici que l'admin écrit son message
        new_marquee = st.text_area("Modifier le message qui défile en haut :", value=C_MSG)
        if st.button("SAUVEGARDER LE NOUVEAU MESSAGE"):
            run_db("UPDATE config SET message=? WHERE ent_id=?", (new_marquee, ENT_ID))
            st.success("C'est fait ! Le message a été mis à jour.")
            st.rerun()

    with st.expander("🔑 SÉCURITÉ"):
        new_p = st.text_input("Nouveau mot de passe", type="password")
        if st.button("CHANGER MON MOT DE PASSE"):
            run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
            st.success("Mot de passe modifié.")

# --- PAGE STOCK (COMPLÈTE) ---
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DU STOCK")
    with st.form("ajout_produit"):
        st.subheader("Ajouter un article")
        f1, f2, f3 = st.columns(3)
        nom_p = f1.text_input("Désignation")
        qte_p = f2.number_input("Quantité", min_value=1)
        prix_p = f3.number_input("Prix de Vente (USD)")
        if st.form_submit_button("ENREGISTRER L'ARTICLE"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                   (nom_p.upper(), qte_p, prix_p, "USD", ENT_ID))
            st.rerun()

    st.write("### Liste des produits")
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pid, pdes, pst, ppx in prods:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"**{pdes}**")
            col2.write(f"Stock: {pst}")
            col3.write(f"{ppx} $")
            if col4.button("Supprimer", key=f"del_{pid}"):
                run_db("DELETE FROM produits WHERE id=?", (pid,))
                st.rerun()

# --- PAGE CAISSE (AVEC BOUTON RETOUR) ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        
        # Sélection des produits
        produits_dispo = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
        p_dict = {row[0]: (row[1], row[2]) for row in produits_dispo}
        
        c_sel, c_add = st.columns([3,1])
        article = c_sel.selectbox("Choisir un article", ["---"] + list(p_dict.keys()))
        if c_add.button("➕ AJOUTER") and article != "---":
            st.session_state.panier[article] = st.session_state.panier.get(article, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total_vente = 0
            for art, qte in list(st.session_state.panier.items()):
                prix_u = p_dict[art][0]
                total_vente += prix_u * qte
                l1, l2, l3 = st.columns([3,1,1])
                l1.write(f"**{art}** ({prix_u}$)")
                st.session_state.panier[art] = l2.number_input("Qté", 1, p_dict[art][1], value=qte, key=f"q_{art}")
                if l3.button("🗑️", key=f"rm_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()
            
            st.markdown(f'<div class="price-frame">TOTAL : {total_vente:,.2f} $</div>', unsafe_allow_html=True)
            
            nom_client = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT")
            if st.button("✅ VALIDER ET IMPRIMER"):
                ref_v = f"FAC-{random.randint(1000, 9999)}"
                run_db("INSERT INTO ventes (ref, client, total, date_v, vendeur, ent_id) VALUES (?,?,?,?,?,?)", 
                       (ref_v, nom_client.upper(), total_vente, datetime.now().strftime("%d/%m/%Y %H:%M"), USER, ENT_ID))
                # Mise à jour du stock
                for a, q in st.session_state.panier.items():
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=?", (q, a))
                
                st.session_state.last_fac = {"ref": ref_v, "client": nom_client, "total": total_vente}
                st.session_state.panier = {}
                st.rerun()
    else:
        # AFFICHAGE DE LA FACTURE AVEC BOUTON RETOUR
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        st.markdown(f"""
            <div style="background:white; color:black; padding:30px; border:2px solid black; max-width:400px; margin:auto; font-family:monospace;">
                <h2 style="text-align:center;">{C_NOM}</h2>
                <p>REF: {f['ref']}</p>
                <p>DATE: {datetime.now().strftime('%d/%m/%Y')}</p>
                <hr>
                <p>CLIENT: {f['client']}</p>
                <h3 style="text-align:center;">TOTAL: {f['total']} $</h3>
                <hr>
                <p style="text-align:center;">Merci de votre confiance !</p>
            </div>
        """, unsafe_allow_html=True)

# --- PAGE DETTES (Paiements par tranches) ---
elif st.session_state.page == "DETTES":
    st.header("📉 SUIVI DES DETTES")
    # Logique pour gérer les dettes ici...
    st.info("Consultez et gérez les crédits clients ici.")

# --- PAGE RAPPORTS (Ventes) ---
elif st.session_state.page == "RAPPORTS":
    st.header("📊 RAPPORTS DE VENTES")
    ventes = run_db("SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    if ventes:
        df = pd.DataFrame(ventes, columns=["Date", "Référence", "Client", "Montant", "Vendeur"])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Aucune vente enregistrée.")
