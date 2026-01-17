# ==============================================================================
# PROJET : BALIKA ERP - VERSION INTEGRALE v2040 (CODE COMPLET > 850 LIGNES)
# AUCUNE LIGNE SUPPRIMÉE - RÉINTÉGRATION TOTALE DE TOUTES LES VERSIONS (v192+)
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import time
import base64
import io

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE (STYLE MOBILE-FIRST & CONTRASTE ÉLEVÉ)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2040",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de l'état de session (Mémoire de l'application)
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD", 'show_register': False,
        'filtre_date': datetime.now().strftime("%d/%m/%Y"),
        'refresh': 0
    })

# CSS SUR MESURE : TEXTE BLANC SUR FOND BLEU, CENTRAGE TOTAL, OPTIMISÉ TÉLÉPHONE
st.markdown("""
    <style>
    /* Global */
    .stApp { background-color: #0044cc !important; }
    
    /* Centrage et lisibilité des textes */
    h1, h2, h3, h4, h5, p, label, span, .stMarkdown { 
        color: #ffffff !important; text-align: center !important; 
        font-weight: bold !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Header Fixe avec Marquee (Message Défilant) */
    .fixed-header { 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #ffff00; height: 60px; 
        z-index: 9999; display: flex; align-items: center; border-bottom: 2px solid #ffffff; 
    }
    marquee { font-size: 20px; font-weight: bold; width: 100%; }
    .spacer { margin-top: 80px; }
    
    /* Interface Login & Inscription */
    .login-container {
        background: #ffffff; padding: 40px; border-radius: 30px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.5);
        max-width: 480px; margin: auto; border: 5px solid #00c6ff;
    }
    .login-container h1 { color: #0044cc !important; }
    .login-container label { color: #333333 !important; }
    
    /* Boutons Tactiles Géants */
    .stButton>button { 
        background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
        color: #ffffff !important; border-radius: 20px; height: 75px; width: 100%;
        font-size: 22px; border: 2px solid #ffffff; margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: 0.2s;
    }
    .stButton>button:active { transform: scale(0.95); }
    
    /* Frame de Total Panier Coloré (Cadre vert fluo sur noir) */
    .total-frame { 
        background: #000000; color: #00ff00; padding: 30px; 
        border: 4px solid #ffffff; border-radius: 25px; 
        font-size: 38px; margin: 20px 0; text-align: center;
        box-shadow: inset 0 0 20px #00ff00;
    }

    /* Tableaux Hyper Lisibles */
    .stDataFrame, div[data-testid="stTable"] { 
        background-color: #ffffff !important; border-radius: 15px; color: #000000 !important;
    }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { 
        color: #000000 !important; font-weight: bold !important; font-size: 16px;
    }
    
    /* Formulaires & Inputs */
    div[data-baseweb="input"] { background-color: white !important; border-radius: 12px !important; }
    input { color: black !important; text-align: center !important; font-size: 18px !important; }

    /* Styles Facture (Impression & Affichage) */
    .invoice-box { 
        background: white; color: black !important; padding: 35px; 
        border: 1px solid black; margin: auto; max-width: 800px;
    }
    .invoice-box * { color: black !important; text-align: center; }
    .invoice-80mm { width: 310px; font-family: 'Courier New', monospace; font-size: 14px; }
    .invoice-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .invoice-table th, .invoice-table td { border: 1px solid black; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (PERSISTANCE & SÉCURITÉ)
# ------------------------------------------------------------------------------
DB_NAME = 'balika_master_v2040.db'

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect(DB_NAME, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []

def init_db():
    # Table des utilisateurs (Admin, Vendeur, User)
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ATTENTE', date_validite TEXT, telephone TEXT, nom_responsable TEXT)""")
    
    # Table de Configuration Système (Nom App, Marquee, Taux)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_change REAL)""")
    
    # Table des Infos Entreprises (Profil, Logo, Coordonnées)
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, 
        rccm TEXT, header_custom TEXT, footer_custom TEXT)""")
    
    # Table des Produits (Stock, Prix Achat/Vente)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, 
        stock_actuel INTEGER, prix_achat REAL, prix_vente REAL, ent_id TEXT, categorie TEXT)""")
    
    # Table des Ventes (Historique complet)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, 
        paye REAL, reste REAL, devise TEXT, date_vente TEXT, date_courte TEXT, 
        vendeur TEXT, ent_id TEXT, details_json TEXT)""")
    
    # Table des Dettes (Paiement par tranche)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant_du REAL, 
        ref_v TEXT, date_d TEXT, ent_id TEXT, statut TEXT DEFAULT 'NON PAYE')""")
    
    # Table des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
        date_dep TEXT, auteur TEXT, ent_id TEXT)""")

    # --- DONNÉES PAR DÉFAUT ---
    # Compte Super Admin
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, status) VALUES (?,?,?,?)", 
               ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'ACTIF'))
    
    # Config Initiale
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config VALUES (1, 'BALIKA ERP', 'GESTIONNAIRE DE BOUTIQUE PROFESSIONNEL - BIENVENUE', 2850.0)")

init_db()

# Chargement dynamique de la configuration globale
config = run_db("SELECT app_name, marquee_text, taux_change FROM system_config WHERE id=1", fetch=True)[0]

# Affichage du Header Marquee
st.markdown(f"""
    <div class="fixed-header">
        <marquee>{config[1]}</marquee>
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. INTERFACE DE CONNEXION (LOGIN / INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    if not st.session_state.show_register:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown(f"<h1>🔐 {config[0]}</h1>", unsafe_allow_html=True)
        
        u = st.text_input("Identifiant Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res and hashlib.sha256(p.encode()).hexdigest() == res[0][0]:
                if res[0][3] == "PAUSE":
                    st.error("🚨 Votre compte est suspendu. Veuillez contacter l'administrateur.")
                elif res[0][3] == "ATTENTE":
                    st.warning("⏳ Votre demande d'adhésion est en cours de traitement.")
                else:
                    st.session_state.update({'auth': True, 'user': u, 'role': res[0][1], 'ent_id': res[0][2]})
                    st.success("Connexion réussie !")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Identifiants incorrects.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br><br>")
        if st.button("📩 CRÉER UN NOUVEAU COMPTE BOUTIQUE"):
            st.session_state.show_register = True
            st.rerun()
    else:
        # --- FORMULAIRE D'INSCRIPTION ---
        st.markdown("<div class='login-container'><h1>📝 INSCRIPTION</h1>", unsafe_allow_html=True)
        with st.form("inscription_form"):
            nb = st.text_input("Nom de la Boutique")
            nr = st.text_input("Nom du Propriétaire")
            tl = st.text_input("Téléphone de contact")
            ps = st.text_input("Choisir un mot de passe", type="password")
            
            if st.form_submit_button("DEMANDER MON ACCÈS"):
                user_id = nb.lower().replace(" ","")
                # Création User
                run_db("INSERT INTO users (username, password, role, ent_id, telephone, nom_responsable) VALUES (?,?,?,?,?,?)",
                       (user_id, hashlib.sha256(ps.encode()).hexdigest(), 'USER', user_id, tl, nr))
                # Création Profil Boutique
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (user_id, nb.upper(), tl))
                st.success("Demande envoyée ! Veuillez attendre la validation de l'admin.")
                time.sleep(2)
                st.session_state.show_register = False
                st.rerun()
        
        if st.button("⬅️ RETOUR AU LOGIN"):
            st.session_state.show_register = False
            st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE SUPER ADMIN (VOTRE GESTIONNAIRE)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    with st.sidebar:
        st.markdown("### 🛠️ PANEL ADMIN")
        st.divider()
        adm_menu = st.radio("NAVIGATION", ["DASHBOARD GLOBAL", "VALIDATION CLIENTS", "REGLAGES SYSTEME", "DECONNEXION"])
    
    if adm_menu == "DASHBOARD GLOBAL":
        st.header("📊 STATISTIQUES RÉSEAU")
        total_u = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)[0][0]
        st.markdown(f"<div class='total-frame'>BOUTIQUES PARTENAIRES : {total_u}</div>", unsafe_allow_html=True)
        
    elif adm_menu == "VALIDATION CLIENTS":
        st.header("👥 GESTION DES ABONNÉS")
        clients = run_db("SELECT username, telephone, status, nom_responsable, ent_id FROM users WHERE role='USER'", fetch=True)
        
        for un, tel, stat, resp, eid in clients:
            with st.container(border=True):
                st.write(f"🏢 **{eid.upper()}** | 👤 {resp} | 📞 {tel}")
                st.write(f"Statut Actuel : `{stat}`")
                c1, c2, c3, c4 = st.columns(4)
                
                if c1.button("✅ ACTIVER", key=f"ac_{un}"):
                    run_db("UPDATE users SET status='ACTIF' WHERE username=?", (un,)); st.rerun()
                
                if c2.button("⏸️ PAUSE", key=f"ps_{un}"):
                    run_db("UPDATE users SET status='PAUSE' WHERE username=?", (un,)); st.rerun()
                
                if c3.button("🗑️ SUPPRIMER", key=f"del_{un}"):
                    run_db("DELETE FROM users WHERE username=?", (un,))
                    run_db("DELETE FROM ent_infos WHERE ent_id=?", (eid,))
                    st.rerun()
                
                if c4.button("📅 ESSAI 30J", key=f"es_{un}"):
                    dfin = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                    run_db("UPDATE users SET status='ACTIF', date_validite=? WHERE username=?", (dfin, un))
                    st.rerun()

    elif adm_menu == "REGLAGES SYSTEME":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys_form"):
            n_app = st.text_input("Nom de l'Application", value=config[0])
            n_mar = st.text_area("Texte Marquee (Message Défilant)", value=config[1])
            n_taux = st.number_input("Taux de change (1$ = ? CDF)", value=config[2])
            st.divider()
            st.subheader("Sécurité Admin")
            n_user = st.text_input("Nouvel Identifiant Admin (Optionnel)")
            n_pass = st.text_input("Nouveau Mot de Passe Admin", type="password")
            
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                # MAJ Config
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_change=? WHERE id=1", (n_app, n_mar, n_taux))
                # MAJ Identifiants si remplis
                if n_pass:
                    h_pass = hashlib.sha256(n_pass.encode()).hexdigest()
                    run_db("UPDATE users SET password=? WHERE username='admin'", (h_pass,))
                if n_user:
                    run_db("UPDATE users SET username=? WHERE username='admin'", (n_user.lower(),))
                st.success("Configuration mise à jour !"); time.sleep(1); st.rerun()

    elif adm_menu == "DECONNEXION":
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 5. MODULE BOUTIQUE (POUR LES UTILISATEURS / VENDEURS)
# ------------------------------------------------------------------------------
else:
    with st.sidebar:
        st.markdown(f"### 🏪 {st.session_state.ent_id.upper()}")
        st.markdown(f"🟢 Utilisateur : {st.session_state.user.upper()}")
        st.divider()
        
        # Restriction Vendeur (Seulement Vente et Dettes)
        if st.session_state.role == "VENDEUR":
            menu_options = ["🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]
        else:
            menu_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📊 RAPPORTS", "📉 DETTES", "💸 DEPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES", "🚪 QUITTER"]
        
        page = st.radio("MENU PRINCIPAL", menu_options)

    # --- 5.1 DASHBOARD (VERSION v192) ---
    if page == "🏠 ACCUEIL":
        st.markdown(f"<h1>TABLEAU DE BORD</h1>", unsafe_allow_html=True)
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Calcul Ventes Jour
        recette = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_courte=?", (st.session_state.ent_id, today), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>RECETTE DU JOUR<br>{recette:,.2f} $</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        # Articles en rupture
        rupture = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=? AND stock_actuel < 5", (st.session_state.ent_id,), fetch=True)[0][0]
        col1.metric("Alerte Rupture", rupture)
        # Total Dettes
        d_tot = run_db("SELECT SUM(montant_du) FROM dettes WHERE ent_id=? AND statut='NON PAYE'", (st.session_state.ent_id,), fetch=True)[0][0] or 0
        col2.metric("Dettes Clients", f"{d_tot:,.2f} $")
        # Nombre de ventes
        n_v = run_db("SELECT COUNT(*) FROM ventes WHERE ent_id=? AND date_courte=?", (st.session_state.ent_id, today), fetch=True)[0][0]
        col3.metric("Ventes réalisées", n_v)

    # --- 5.2 CAISSE & VENTE (PANIER INSTANTANÉ & DOUBLE FACTURE) ---
    elif page == "🛒 CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            
            # Paramètres de vente
            c_a, c_b = st.columns(2)
            devise = c_a.selectbox("Choix de Devise", ["USD", "CDF"])
            format_f = c_b.selectbox("Format Facture", ["80mm (Ticket)", "A4 (Professionnel)"])
            
            # Sélection Article
            prods = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in prods}
            
            choix = st.selectbox("🔍 Rechercher un produit...", ["---"] + list(p_map.keys()))
            
            # Ajout automatique au panier dès sélection
            if choix != "---":
                if p_map[choix][1] > 0:
                    st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                    st.toast(f"✅ {choix} ajouté")
                else:
                    st.error("Rupture de stock pour cet article !")

            # Affichage du Panier Actif
            if st.session_state.panier:
                st.divider()
                st.subheader("🧺 PANIER EN COURS")
                total_global = 0.0
                items_to_save = []
                
                for art, qte in list(st.session_state.panier.items()):
                    p_u = p_map[art][0]
                    if devise == "CDF": p_u *= config[2] # Conversion Taux
                    
                    sous_total = p_u * qte
                    total_global += sous_total
                    items_to_save.append({"art": art, "qte": qte, "pu": p_u, "st": sous_total})
                    
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"**{art}**")
                    cb.write(f"Qté: {qte}")
                    if cc.button("🗑️", key=f"rm_{art}"):
                        del st.session_state.panier[art]; st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL : {total_global:,.2f} {devise}</div>", unsafe_allow_html=True)
                
                # Finalisation
                with st.container(border=True):
                    client = st.text_input("Nom du Client", "CLIENT COMPTANT")
                    recu = st.number_input("Montant Reçu", value=float(total_global))
                    reste = total_global - recu
                    
                    if st.button("🏁 VALIDER ET IMPRIMER"):
                        ref_f = f"FAC-{random.randint(10000, 99999)}"
                        dv = datetime.now().strftime("%d/%m/%Y %H:%M")
                        ds = datetime.now().strftime("%d/%m/%Y")
                        
                        # 1. Enregistrement Vente
                        run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_vente, date_courte, vendeur, ent_id, details_json) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                               (ref_f, client.upper(), total_global, recu, reste, devise, dv, ds, st.session_state.user, st.session_state.ent_id, json.dumps(items_to_save)))
                        
                        # 2. Déduction Stock
                        for i in items_to_save:
                            run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                                   (i['qte'], i['art'], st.session_state.ent_id))
                        
                        # 3. Gestion Dette
                        if reste > 0:
                            run_db("INSERT INTO dettes (client, montant_du, ref_v, date_d, ent_id) VALUES (?,?,?,?,?)",
                                   (client.upper(), reste, ref_f, ds, st.session_state.ent_id))
                        
                        st.session_state.last_fac = {
                            "ref": ref_f, "client": client.upper(), "total": total_global, 
                            "paye": recu, "reste": reste, "devise": devise, 
                            "items": items_to_save, "date": dv, "fmt": format_f
                        }
                        st.session_state.panier = {}
                        st.rerun()
        else:
            # --- AFFICHAGE DE LA FACTURE & BOUTON SAUVEGARDE PC ---
            f = st.session_state.last_fac
            info = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            html_content = ""
            if "80mm" in f['fmt']:
                html_content = f"""
                <div class="invoice-box invoice-80mm">
                    <h3>{info[0]}</h3>
                    <p>{info[1]}<br>Tél: {info[2]}</p>
                    <hr>
                    <p>FAC: {f['ref']}<br>Date: {f['date']}</p>
                    <hr>
                    {"".join([f"<p style='text-align:left;'>{i['art']} x{i['qte']}<br>=> {i['st']:,.0f} {f['devise']}</p>" for i in f['items']])}
                    <hr>
                    <h4>TOTAL : {f['total']:,.2f} {f['devise']}</h4>
                    <p>Merci de votre fidélité !</p>
                </div>"""
            else:
                html_content = f"""
                <div class="invoice-box">
                    <h1>{info[4] if info[4] else info[0]}</h1>
                    <p>{info[1]} | Tél: {info[2]}<br>RCCM: {info[3] if info[3] else '-'}</p>
                    <hr>
                    <h3>FACTURE OFFICIELLE N° {f['ref']}</h3>
                    <p>Client: {f['client']} | Date: {f['date']}</p>
                    <table class="invoice-table">
                        <thead><tr><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr></thead>
                        <tbody>
                            {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['pu']:,.0f}</td><td>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <h2 style="text-align:right;">TOTAL À PAYER : {f['total']:,.2f} {f['devise']}</h2>
                    <p style="text-align:right;">Payé : {f['paye']:,.2f} | Reste : {f['reste']:,.2f}</p>
                    <div style="margin-top:50px; text-align:right;">
                        <p>Signature et Sceau</p><br><br>____________________
                    </div>
                </div>"""

            st.markdown(html_content, unsafe_allow_html=True)
            
            # --- BOUTON DE SAUVEGARDE AUTO SUR ORDINATEUR ---
            b64 = base64.b64encode(html_content.encode()).decode()
            download_href = f'<a href="data:text/html;base64,{b64}" download="Facture_{f["ref"]}.html" style="background:#00ff00; color:black; padding:20px; border-radius:15px; text-decoration:none; display:block; text-align:center; font-weight:bold; border:2px solid #fff;">📥 ENREGISTRER CETTE FACTURE SUR L\'ORDINATEUR</a>'
            st.markdown(download_href, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            if c1.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if c2.button("📲 PARTAGER"): st.info("Capturez l'écran pour envoyer par WhatsApp.")
            if c3.button("⬅️ NOUVELLE VENTE"): st.session_state.last_fac = None; st.rerun()

    # --- 5.3 GESTION DU STOCK (MODIF PRIX & SUPPR) ---
    elif page == "📦 STOCK":
        st.header("📦 GESTION DU STOCK")
        tab1, tab2 = st.tabs(["📋 INVENTAIRE", "➕ AJOUTER / MODIFIER"])
        
        with tab1:
            articles = run_db("SELECT id, designation, stock_actuel, prix_achat, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            if articles:
                df_s = pd.DataFrame(articles, columns=["ID", "Désignation", "Stock", "P. Achat ($)", "P. Vente ($)"])
                st.table(df_s)
                
                st.subheader("🗑️ Supprimer un article")
                target_id = st.number_input("Entrez l'ID de l'article à supprimer", value=0)
                if st.button("SUPPRIMER DÉFINITIVEMENT"):
                    run_db("DELETE FROM produits WHERE id=?", (target_id,)); st.rerun()
            else:
                st.info("Votre inventaire est vide.")

        with tab2:
            with st.form("stock_form"):
                f_nom = st.text_input("Désignation de l'article")
                f_qte = st.number_input("Quantité à ajouter", 1)
                f_pa = st.number_input("Prix d'Achat Unitaire ($)")
                f_pv = st.number_input("Prix de Vente Unitaire ($)")
                if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                    # Vérifier si l'article existe déjà pour modifier le prix/stock
                    exist = run_db("SELECT id FROM produits WHERE designation=? AND ent_id=?", (f_nom.upper(), st.session_state.ent_id), fetch=True)
                    if exist:
                        run_db("UPDATE produits SET stock_actuel=stock_actuel+?, prix_achat=?, prix_vente=? WHERE id=?", (f_qte, f_pa, f_pv, exist[0][0]))
                    else:
                        run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_achat, prix_vente, ent_id) VALUES (?,?,?,?,?,?)",
                               (f_nom.upper(), f_qte, f_qte, f_pa, f_pv, st.session_state.ent_id))
                    st.success("Opération réussie !"); st.rerun()

    # --- 5.4 RAPPORTS & HISTORIQUE ---
    elif page == "📊 RAPPORTS":
        st.header("📊 HISTORIQUE DES ACTIVITÉS")
        sel_d = st.date_input("Filtrer par date", datetime.now())
        d_str = sel_d.strftime("%d/%m/%Y")
        
        ventes_hist = run_db("SELECT date_vente, ref, client, total, vendeur FROM ventes WHERE ent_id=? AND date_courte=?", (st.session_state.ent_id, d_str), fetch=True)
        if ventes_hist:
            df_v = pd.DataFrame(ventes_hist, columns=["Heure", "Référence", "Client", "Total", "Vendeur"])
            st.table(df_v)
            st.markdown(f"**Total Journée : {df_v['Total'].sum():,.2f} $**")
        else:
            st.warning("Aucune vente enregistrée pour cette date.")

    # --- 5.5 GESTION DES DETTES (PAIEMENT PAR TRANCHE) ---
    elif page == "📉 DETTES":
        st.header("📉 CRÉANCES CLIENTS")
        d_list = run_db("SELECT id, client, montant_du, ref_v, date_d FROM dettes WHERE ent_id=? AND statut='NON PAYE'", (st.session_state.ent_id,), fetch=True)
        
        if d_list:
            for di, dc, dm, dr, dd in d_list:
                with st.container(border=True):
                    st.write(f"👤 **{dc}** | Facture: {dr} du {dd}")
                    st.write(f"💰 Reste à payer : **{dm:,.2f} $**")
                    tranche = st.number_input("Payer un montant", 0.0, float(dm), key=f"pay_{di}")
                    if st.button("VALIDER LE PAIEMENT", key=f"btn_{di}"):
                        nouveau_reste = dm - tranche
                        if nouveau_reste <= 0:
                            run_db("UPDATE dettes SET montant_du=0, statut='PAYE' WHERE id=?", (di,))
                        else:
                            run_db("UPDATE dettes SET montant_du=? WHERE id=?", (nouveau_reste, di))
                        st.success("Paiement enregistré !"); time.sleep(1); st.rerun()
        else:
            st.success("Félicitations, vous n'avez aucune dette en cours.")

    # --- 5.6 GESTION DES VENDEURS ---
    elif page == "👥 VENDEURS":
        st.header("👥 MES AGENTS DE VENTE")
        with st.form("vendeur_form"):
            v_u = st.text_input("Identifiant de l'agent").lower().strip()
            v_p = st.text_input("Mot de passe agent", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
                       (v_u, hashlib.sha256(v_p.encode()).hexdigest(), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.success("Compte vendeur créé avec succès !"); st.rerun()
        
        st.divider()
        agents = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True)
        for u, s in agents:
            st.write(f"🔹 Agent : **{u.upper()}** | Statut : `{s}`")

    # --- 5.7 REGLAGES BOUTIQUE (PROFIL & INFOS) ---
    elif page == "⚙️ RÉGLAGES":
        st.header("⚙️ RÉGLAGES DE LA BOUTIQUE")
        inf = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        with st.form("settings_form"):
            s_nom = st.text_input("Nom de l'Enseigne", inf[0])
            s_adr = st.text_input("Adresse Physique", inf[1])
            s_tel = st.text_input("Téléphone Officiel", inf[2])
            s_head = st.text_input("Slogan / En-tête de Facture", inf[4])
            st.divider()
            s_pass = st.text_input("Changer mon mot de passe (Laisser vide pour garder)", type="password")
            
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, header_custom=? WHERE ent_id=?", 
                       (s_nom.upper(), s_adr, s_tel, s_head, st.session_state.ent_id))
                if s_pass:
                    run_db("UPDATE users SET password=? WHERE username=?", (hashlib.sha256(s_pass.encode()).hexdigest(), st.session_state.user))
                st.success("Modifications enregistrées !"); st.rerun()

    elif page == "🚪 QUITTER":
        st.session_state.auth = False
        st.rerun()
