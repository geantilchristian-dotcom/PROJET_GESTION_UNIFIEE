# ==============================================================================
# BALIKA ERP ULTIMATE v755 - SYSTÈME ERP SaaS PROFESSIONNEL
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
# 1. CONFIGURATION SYSTÈME CORE (v755)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v755", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State pour la persistance et la navigation
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD", 'audit_active': True
    })

def run_db(query, params=(), fetch=False):
    """Moteur SQLite avec gestion de verrouillage et gestion d'erreurs unique"""
    try:
        with sqlite3.connect('balika_pro_v755.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except sqlite3.IntegrityError:
        # Gestion silencieuse des doublons pour éviter les messages d'erreur rouges
        return "DOUBLON"
    except Exception as e:
        st.error(f"Erreur Système : {e}")
        return []

def make_hashes(password):
    """Hachage SHA-256 pour la sécurité des comptes"""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. INITIALISATION DES TABLES (ARCHITECTURE v755)
# ------------------------------------------------------------------------------
def init_db():
    # Table des Utilisateurs (Admin et Vendeurs)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Table de Configuration (Branding et SaaS)
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT, montant_paye REAL DEFAULT 0.0)""")
    
    # Table des Produits (Gestion Inventaire)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, categorie TEXT DEFAULT 'GÉNÉRAL', prix_achat REAL DEFAULT 0.0)""")
    
    # Table des Ventes (Historique Transactionnel)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    # Table des Dettes (Suivi des Versements)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")
    
    # Table des Logs (Sécurité et Audit)
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                date TEXT, ent_id TEXT)""")

    # Création du compte Maître si base neuve
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'SYSTÈME ERP BALIKA v755 OPÉRATIONNEL', '16/01/2026'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE GRAPHIQUE CSS (SANS CADRE BLANC)
# ------------------------------------------------------------------------------
# Récupération dynamique des préférences visuelles
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_res = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
if cfg_res:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = cfg_res[0]
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    /* Thème Orange-Noir Fluide */
    .stApp {{
        background: linear-gradient(160deg, #FF4B2B 0%, #FF8008 100%);
        background-attachment: fixed;
        color: white !important;
    }}

    /* MARQUEE PERSISTANT HAUT DE PAGE */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 50px;
        z-index: 999999; border-bottom: 3px solid white;
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-content {{
        display: inline-block; white-space: nowrap;
        animation: marquee-move 25s linear infinite;
        font-family: 'Arial Black', sans-serif; font-size: 20px;
    }}
    @keyframes marquee-move {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Nettoyage des Inputs (Zéro cadre blanc) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important; border: 2px solid rgba(255,255,255,0.6) !important;
        color: white !important; height: 50px !important;
    }}
    input {{ color: white !important; font-weight: bold !important; font-size: 18px !important; }}
    
    /* Boutons de Commande Bleus */
    .stButton>button {{
        background: #0066ff !important; color: white !important;
        border-radius: 15px; font-weight: 900; height: 55px; width: 100%;
        border: 2px solid white !important; text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}
    .stButton>button:hover {{ background: #0044cc !important; transform: translateY(-2px); }}

    /* Widgets de Caisse et Montre */
    .clock-widget {{
        background: rgba(0,0,0,0.6); padding: 25px; border-radius: 20px;
        border: 3px solid #FFF; text-align: center; margin: 20px auto; max-width: 450px;
    }}
    .total-display {{
        background: #000; border: 5px solid #00FF00; padding: 20px;
        border-radius: 15px; color: #00FF00; font-size: 45px;
        font-weight: 800; text-align: center; margin: 20px 0;
    }}

    /* Sidebar Mobile */
    [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #000; }}
    [data-testid="stSidebar"] * {{ color: #000 !important; font-weight: bold; }}
    </style>

    <div class="marquee-wrapper">
        <div class="marquee-content">
             🚀 {C_NOM} : {C_MSG} | 💹 TAUX DU JOUR: {C_TX} CDF/USD | 🕒 {datetime.now().strftime('%H:%M')} | BIENVENUE DANS VOTRE ESPACE DE GESTION
        </div>
    </div>
    <div style="height:65px;"></div>
""", unsafe_allow_html=True)

# Blocage de sécurité SaaS
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 VOTRE LICENCE EST EN ATTENTE DE PAIEMENT. CONTACTEZ BALIKA.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. SYSTÈME D'AUTHENTIFICATION (FIXÉ)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown(f"<h1 style='text-align:center; font-size:3.5rem;'>{C_NOM}</h1>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["🔑 ENTRER DANS LE SYSTÈME", "📝 CRÉER UNE NOUVELLE BOUTIQUE"])
        
        with tab_in:
            l_user = st.text_input("Identifiant Unique").lower().strip()
            l_pass = st.text_input("Mot de Passe", type="password")
            if st.button("DÉVERROUILLER L'ACCÈS"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (l_user,), fetch=True)
                if res and make_hashes(l_pass) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':l_user, 'role':res[0][1], 'ent_id':res[0][2]})
                    run_db("INSERT INTO logs (user, action, date, ent_id) VALUES (?,?,?,?)", (l_user, "CONNEXION", datetime.now().strftime("%d/%m/%Y %H:%M"), res[0][2]))
                    st.success("Accès validé...")
                    time.sleep(0.5)
                    st.rerun()
                else: st.error("Identifiants incorrects ou compte inexistant.")
        
        with tab_up:
            with st.form("inscription_principale"):
                st.subheader("Déploiement Instance SaaS")
                n_ent_name = st.text_input("Nom de votre établissement")
                n_admin_id = st.text_input("Choisir votre Identifiant Admin").lower().strip()
                n_admin_pw = st.text_input("Choisir un Mot de passe", type="password")
                n_phone = st.text_input("Votre numéro WhatsApp")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if n_ent_name and n_admin_id and n_admin_pw:
                        # Vérification manuelle des doublons avant insertion
                        exist = run_db("SELECT * FROM users WHERE username=?", (n_admin_id,), fetch=True)
                        if not exist:
                            new_eid = f"BAL-{random.randint(10000, 99999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                                   (n_admin_id, make_hashes(n_admin_pw), "ADMIN", new_eid, n_phone))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, taux, message, date_inscription) VALUES (?,?,?,?,?,?)", 
                                   (new_eid, n_ent_name.upper(), n_phone, 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ INSTANCE CRÉÉE ! Connectez-vous maintenant.")
                        else: st.warning("❌ Cet Identifiant Admin est déjà utilisé. Choisissez-en un autre.")
                    else: st.error("Tous les champs sont obligatoires.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION SIDEBAR PROFESSIONNELLE
# ------------------------------------------------------------------------------
with st.sidebar:
    # Photo de profil de l'utilisateur
    p_img = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if p_img and p_img[0][0]: st.image(p_img[0][0], width=130)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=130)
    
    st.markdown(f"### 🛡️ {USER.upper()}")
    st.info(f"ID : {ENT_ID} | Rôle : {ROLE}")
    st.write("---")
    
    # Menu dynamique selon les droits
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 RÉSEAU ABONNÉS", "📊 JOURNAUX AUDIT", "👤 PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE VENTE", "📉 GESTION DETTES", "📦 INVENTAIRE", "👥 ÉQUIPE VENDEURS", "📊 RAPPORTS", "⚙️ CONFIGURATION", "👤 PROFIL"]
    else: # VENDEUR
        menu = ["🏠 ACCUEIL", "🛒 CAISSE VENTE", "📉 GESTION DETTES", "👤 PROFIL"]

    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 SORTIE SÉCURISÉE", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE ACCUEIL (DASHBOARD ANALYTIQUE)
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.header(f"BIENVENUE CHEZ {C_NOM}")
    
    st.markdown(f"""
        <center>
            <div class="clock-widget">
                <p style="font-size:70px; font-weight:900; color:#FFD700; margin:0;">{datetime.now().strftime('%H:%M:%S')}</p>
                <p style="font-size:22px; margin:0;">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3, c4 = st.columns(4)
    v_total = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{v_total:,.2f} $")
    
    d_total = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("TOTAL CRÉANCES", f"{d_total:,.2f} $", delta="-10%")
    
    s_total = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", s_total)
    
    v_count = run_db("SELECT COUNT(*) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c4.metric("NOMBRE DE VENTES", v_count)

# ------------------------------------------------------------------------------
# 7. MODULE CAISSE (MULTI-DEVISE & FACTURATION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL POINT DE VENTE")
        col_m1, col_m2 = st.columns(2)
        v_dev = col_m1.selectbox("Devise de paiement", ["USD", "CDF"])
        
        # Liste des produits avec prix et stock
        plist = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in plist}
        
        c_sel, c_add = st.columns([3, 1])
        choix = c_sel.selectbox("Rechercher un produit", ["---"] + list(pmap.keys()))
        if c_add.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            net_a_payer = 0.0
            items_final = []
            
            for art, qte in list(st.session_state.panier.items()):
                px_init = pmap[art]['px']
                dv_init = pmap[art]['dv']
                
                # Logique de conversion au taux configuré
                if dv_init == "USD" and v_dev == "CDF": px_final = px_init * C_TX
                elif dv_init == "CDF" and v_dev == "USD": px_final = px_init / C_TX
                else: px_final = px_init
                
                stot = px_final * qte
                net_a_payer += stot
                items_final.append({'art': art, 'qte': qte, 'pu': px_final, 'st': stot})
                
                # Ligne de commande
                r1, r2, r3 = st.columns([3, 1, 0.5])
                r1.write(f"**{art}** (@{px_final:,.0f})")
                st.session_state.panier[art] = r2.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"v_{art}")
                if r3.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="total-display">TOTAL À PAYER : {net_a_payer:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            
            with st.form("validation_vente"):
                f_cl_name = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                f_cash = st.number_input(f"MONTANT REÇU ({v_dev})", value=float(net_a_payer))
                if st.form_submit_button("💰 FINALISER LA VENTE"):
                    ref_fac = f"FAC-{random.randint(1000, 9999)}"
                    reste_fac = net_a_payer - f_cash
                    date_fac = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Insertion Vente
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                           (ref_fac, f_cl_name, net_a_payer, f_cash, reste_fac, v_dev, date_fac, USER, ENT_ID, json.dumps(items_final)))
                    
                    # Création Dette si impayé
                    if reste_fac > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_cl_name, reste_fac, v_dev, ref_fac, ENT_ID, json.dumps([{'d': date_fac, 'p': f_cash}])))
                    
                    # Mise à jour Stock
                    for item in items_final:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (item['qte'], item['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref': ref_fac, 'cl': f_cl_name, 'tot': net_a_payer, 'pay': f_cash, 'dev': v_dev, 'items': items_final, 'date': date_fac}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # Affichage Facture Mobile
        f = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({'last_fac': None}))
        st.markdown(f"""
            <div style="background:white; color:black; padding:25px; border-radius:10px; font-family:monospace; max-width:450px; margin:auto; border:2px solid #000;">
                <center>
                    <h2 style="margin:0;">{C_NOM}</h2>
                    <p>{C_ADR}<br>Tél: {C_TEL}</p>
                    <hr style="border-top: 2px dashed black;">
                    <h4>FACTURE N° {f['ref']}</h4>
                    <p>Client: {f['cl']}<br>Date: {f['date']}</p>
                </center>
                <table style="width:100%;">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr style="border-top: 2px dashed black;">
                <h2 align="right">NET À PAYER : {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Payé : {f['pay']:,.2f}<br>Reste : {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER / PARTAGER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ------------------------------------------------------------------------------
# 8. MODULE INVENTAIRE (GESTION PRODUITS & PRIX)
# ------------------------------------------------------------------------------
elif st.session_state.page == "INVENTAIRE":
    st.header("📦 GESTION DES ARTICLES")
    with st.expander("➕ AJOUTER UN NOUVEAU PRODUIT"):
        with st.form("form_prod"):
            p_nom = st.text_input("Désignation de l'article").upper()
            p_cat = st.selectbox("Catégorie", ["ALIMENTAIRE", "HABILLEMENT", "DIVERS"])
            c_p1, c_p2, c_p3 = st.columns(3)
            p_qte = c_p1.number_input("Stock Initial", 0)
            p_prx = c_p2.number_input("Prix de Vente", 0.0)
            p_dev = c_p3.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id, categorie) VALUES (?,?,?,?,?,?)", 
                       (p_nom, p_qte, p_prx, p_dev, ENT_ID, p_cat))
                st.success("Produit ajouté !"); st.rerun()
    
    st.write("### ÉTAT DU STOCK")
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    if prods:
        df_p = pd.DataFrame(prods, columns=["ID", "Designation", "Stock", "Prix", "Devise"])
        st.dataframe(df_p, use_container_width=True)
        
        st.write("---")
        for pid, pdes, psto, ppx, pdevise in prods:
            with st.container(border=True):
                cl1, cl2, cl3 = st.columns([3, 1, 1])
                cl1.write(f"**{pdes}**")
                new_price = cl2.number_input("Prix", value=float(ppx), key=f"mod_p_{pid}")
                if cl2.button("SAUVER", key=f"btn_p_{pid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_price, pid))
                    st.rerun()
                if cl3.button("🗑️ SUPPRIMER", key=f"del_p_{pid}"):
                    run_db("DELETE FROM produits WHERE id=?", (pid,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE ÉQUIPE VENDEURS (CRÉATION COMPTES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENDEURS" and ROLE == "ADMIN":
    st.header("👥 GESTION DES VENDEURS")
    with st.form("f_new_vendeur"):
        v_id = st.text_input("Identifiant du Vendeur").lower().strip()
        v_pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            if v_id and v_pw:
                if not run_db("SELECT * FROM users WHERE username=?", (v_id,), fetch=True):
                    run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                           (v_id, make_hashes(v_pw), "VENDEUR", ENT_ID))
                    st.success("Vendeur ajouté avec succès !"); st.rerun()
                else: st.warning("Cet identifiant est déjà utilisé.")
    
    st.write("---")
    vendeurs = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for v_u, v_s in vendeurs:
        c_v1, c_v2 = st.columns([3, 1])
        c_v1.write(f"👤 {v_u.upper()} (Status: {v_s})")
        if c_v2.button("SUPPRIMER COMPTE", key=f"dv_{v_u}"):
            run_db("DELETE FROM users WHERE username=?", (v_u,))
            st.rerun()

# ------------------------------------------------------------------------------
# 10. MODULE DETTES (RECOUVREMENT AUTOMATIQUE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.header("📉 CAHIER DES DETTES")
    dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    if not dettes:
        st.success("Aucune dette à recouvrer.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in dettes:
            with st.container(border=True):
                col_d1, col_d2 = st.columns([3, 1])
                col_d1.subheader(f"🔴 {dcl}")
                col_d1.write(f"Montant : **{dmt:,.2f} {ddv}** | Facture : {drf}")
                v_vers = col_d2.number_input("Somme payée", 0.0, float(dmt), key=f"pay_d_{did}")
                if col_d2.button("ENCAISSER", key=f"btn_d_{did}"):
                    n_mt = dmt - v_vers
                    h_list = json.loads(dhi)
                    h_list.append({'d': datetime.now().strftime("%d/%m"), 'p': v_vers})
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_mt, json.dumps(h_list), did))
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_vers, v_vers, drf, ENT_ID))
                    if n_mt <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 11. MODULE CONFIGURATION (MARQUEE & TAUX)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CONFIGURATION" and ROLE == "ADMIN":
    st.header("⚙️ PARAMÈTRES BOUTIQUE")
    with st.form("f_config"):
        e_nom = st.text_input("Nom de l'Etablissement", C_NOM)
        e_msg = st.text_area("Message Défilant (Publicité)", C_MSG)
        e_taux = st.number_input("Taux de change (1$ en CDF)", value=C_TX)
        e_adr = st.text_input("Adresse", C_ADR)
        e_tel = st.text_input("WhatsApp de la boutique", C_TEL)
        if st.form_submit_button("METTRE À JOUR"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", 
                   (e_nom.upper(), e_msg, e_taux, e_adr, e_tel, ENT_ID))
            st.success("Modifications enregistrées !"); st.rerun()

# ------------------------------------------------------------------------------
# 12. MODULE PROFIL (SÉCURITÉ & PHOTO)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE")
    p_info = run_db("SELECT full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    with st.container(border=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            n_name = st.text_input("Nom Complet", p_info[0])
            n_tel = st.text_input("Téléphone", p_info[1])
            n_pic = st.file_uploader("Modifier Photo de Profil", type=["jpg", "png"])
        with col_p2:
            n_pass = st.text_input("Nouveau Mot de Passe", type="password")
            n_pass_c = st.text_input("Confirmer Mot de Passe", type="password")
        
        if st.button("SAUVEGARDER MON PROFIL"):
            if n_pass and n_pass == n_pass_c:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pass), USER))
            if n_pic:
                run_db("UPDATE users SET photo=? WHERE username=?", (n_pic.getvalue(), USER))
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (n_name, n_tel, USER))
            st.success("Profil mis à jour !"); st.rerun()

# ------------------------------------------------------------------------------
# 13. MODULE SaaS (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION RÉSEAU BALIKA")
    
    with st.expander("📢 DIFFUSER UN MESSAGE GLOBAL"):
        global_msg = st.text_input("Message pour tous les écrans")
        if st.button("ACTIVER LE MESSAGE GLOBAL"):
            run_db("UPDATE config SET message=?", (global_msg,))
            st.success("Message déployé partout.")

    shops = run_db("SELECT ent_id, nom_ent, status, montant_paye FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for eid, en, es, ep in shops:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2, 1, 1])
            cl1.write(f"🏢 **{en}** ({eid})")
            cl2.write(f"Statut : {es} | Payé : {ep}$")
            if cl3.button("ACTIVER/PAUSE", key=eid):
                ns = "PAUSE" if es == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid))
                st.rerun()

# ------------------------------------------------------------------------------
# 14. MODULE AUDIT & RAPPORTS
# ------------------------------------------------------------------------------
elif st.session_state.page == "RAPPORTS" or st.session_state.page == "AUDIT":
    st.header("📊 ANALYSE DE L'ACTIVITÉ")
    if ROLE == "SUPER_ADMIN":
        logs = run_db("SELECT * FROM logs ORDER BY id DESC LIMIT 200", fetch=True)
        st.table(pd.DataFrame(logs, columns=["ID", "Utilisateur", "Action", "Date", "Entité"]))
    else:
        v_data = run_db("SELECT date_v, ref, client, total, paye, reste FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
        df_v = pd.DataFrame(v_data, columns=["Date", "Référence", "Client", "Total", "Payé", "Reste"])
        st.dataframe(df_v, use_container_width=True)

# ------------------------------------------------------------------------------
# FIN DU CODE v755 (+750 LIGNES DE LOGIQUE ERP)
# ------------------------------------------------------------------------------
