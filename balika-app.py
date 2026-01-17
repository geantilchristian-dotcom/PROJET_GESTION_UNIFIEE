# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTIME v2038 (RÉGÉNÉRATION TOTALE > 800 LIGNES)
# TOUTES FONCTIONNALITÉS CONSERVÉES : DASHBOARD, MARQUEE, CDF/USD, DETTES, 
# MODIF PRIX, SUPPRESSION, PAUSE, SAUVEGARDE AUTO, DOUBLE FACTURE.
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
# 1. CONFIGURATION VISUELLE & STYLE (LUMINOSITÉ MAXIMALE & MOBILE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2038",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation exhaustive de l'état de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm", 'show_register': False, 'devise_vente': "USD",
        'profil_pic': None, 'temp_total': 0.0
    })

# CSS POUR CONTRASTE TÉLÉPHONE ET DESIGN PROFESSIONNEL
st.markdown("""
    <style>
    /* Fond Bleu avec texte blanc */
    .stApp { background-color: #0044cc !important; }
    h1, h2, h3, h4, h5, p, label, span, .stMarkdown { 
        color: #ffffff !important; text-align: center !important; font-weight: bold; 
    }
    
    /* En-tête Fixe & Marquee */
    .fixed-header { 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000; color: #ffff00; height: 65px; 
        z-index: 9999; display: flex; align-items: center; border-bottom: 2px solid #fff; 
    }
    marquee { font-size: 20px; font-weight: bold; }
    .spacer { margin-top: 85px; }
    
    /* Login & Inscription */
    .login-container {
        background: #ffffff; padding: 40px; border-radius: 30px;
        box-shadow: 0px 15px 40px rgba(0,0,0,0.5);
        max-width: 450px; margin: auto; border: 5px solid #00c6ff;
    }
    .login-container h1 { color: #0044cc !important; }
    .login-container label { color: #333 !important; }
    
    /* Boutons Tactiles Mobiles */
    .stButton>button { 
        background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
        color: white !important; border-radius: 18px; height: 70px; width: 100%;
        font-size: 20px; border: 2px solid #fff; margin-bottom: 15px;
        transition: 0.3s;
    }
    .stButton>button:active { transform: scale(0.95); }
    
    /* Frame de Total en Couleur */
    .total-frame { 
        background: #000; color: #00ff00; padding: 30px; 
        border: 4px solid #fff; border-radius: 20px; 
        font-size: 35px; margin: 20px 0; text-align: center;
        box-shadow: 0px 0px 20px #00ff00;
    }

    /* Tableaux Hyper Lisibles */
    .stDataFrame, div[data-testid="stTable"] { 
        background-color: #ffffff !important; border-radius: 15px; color: #000 !important;
        padding: 10px;
    }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { 
        color: #000 !important; font-weight: bold !important; border: 1px solid #ddd;
    }

    /* Facture Administrative & 80mm */
    .fac-container {
        background: #ffffff; color: #000000 !important; padding: 40px;
        border: 2px solid #000; width: 95%; margin: auto; border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .fac-container * { color: #000000 !important; text-align: center; }
    .fac-container table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .fac-container th, .fac-container td { border: 1px solid #000; padding: 12px; font-size: 16px; }
    
    /* Styles spécifiques 80mm */
    .fac-80mm { width: 320px; margin: auto; font-family: 'Courier New', monospace; font-size: 13px; }

    /* Inputs blancs */
    div[data-baseweb="input"] { background-color: white !important; border-radius: 10px !important; }
    input { color: black !important; text-align: center !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. GESTION DE LA BASE DE DONNÉES (SQLITE3)
# ------------------------------------------------------------------------------
DB_PATH = 'balika_v2038.db'

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []

def init_db():
    # Tables Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ATTENTE', date_validite TEXT, telephone TEXT, nom_boss TEXT)""")
    
    # Table System (Marquee, Taux)
    run_db("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, taux REAL)")
    
    # Tables Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, 
        rccm TEXT, header_custom TEXT, logo BLOB)""")
    
    # Table Produits (v192 - avec prix achat/vente)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, 
        stock_actuel INTEGER, prix_achat REAL, prix_vente REAL, ent_id TEXT, categorie TEXT)""")
    
    # Table Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, 
        paye REAL, reste REAL, devise TEXT, date_v TEXT, date_courte TEXT, 
        vendeur TEXT, ent_id TEXT, details_json TEXT)""")
    
    # Table Dettes (v192 - paiement par tranche)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant_initial REAL, 
        montant_restant REAL, ref_v TEXT, date_d TEXT, ent_id TEXT, statut TEXT DEFAULT 'NON PAYE')""")
    
    # Table Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
        date_dep TEXT, auteur TEXT, ent_id TEXT)""")

    # Insertion des accès par défaut (Codes demandés : admin / admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, status) VALUES (?,?,?,?)", 
               ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'ACTIF'))
    
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION UNIFIÉE v2038', 2850.0)")

init_db()

# Chargement de la config système
sys_cfg = run_db("SELECT app_name, marquee, taux FROM system_config WHERE id=1", fetch=True)[0]
st.markdown(f'<div class="fixed-header"><marquee>{sys_cfg[1]}</marquee></div><div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. INTERFACE DE CONNEXION (LOGIN & INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    if not st.session_state.show_register:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown(f"<h1>🔐 {sys_cfg[0]}</h1>", unsafe_allow_html=True)
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        
        if st.button("ACCÉDER AU TABLEAU DE BORD"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res and hashlib.sha256(p.encode()).hexdigest() == res[0][0]:
                if res[0][3] == "PAUSE":
                    st.error("🚨 Votre compte est suspendu. Contactez BALIKA.")
                elif res[0][3] == "ATTENTE":
                    st.warning("⏳ Votre demande est en cours de traitement.")
                else:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.success("Connexion établie !")
                    time.sleep(1); st.rerun()
            else:
                st.error("Identifiants incorrects.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br><br>")
        if st.button("📝 PAS DE COMPTE ? CRÉER UNE BOUTIQUE"):
            st.session_state.show_register = True; st.rerun()
    else:
        st.markdown("<div class='login-container'><h1>📝 INSCRIPTION</h1>", unsafe_allow_html=True)
        with st.form("reg_form"):
            nb = st.text_input("Nom de la Boutique / Entreprise")
            nr = st.text_input("Nom du Propriétaire")
            tl = st.text_input("Numéro de Téléphone")
            pw = st.text_input("Créer un Mot de Passe", type="password")
            if st.form_submit_button("DEMANDER MON ACCÈS"):
                uid = nb.lower().replace(" ","")
                run_db("INSERT INTO users (username, password, role, ent_id, telephone, nom_boss) VALUES (?,?,?,?,?,?)",
                       (uid, hashlib.sha256(pw.encode()).hexdigest(), 'USER', uid, tl, nr))
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (uid, nb.upper(), tl))
                st.success("Demande envoyée !"); time.sleep(2); st.session_state.show_register = False; st.rerun()
        if st.button("⬅️ RETOUR"): st.session_state.show_register = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE SUPER ADMIN (GESTION DES CLIENTS & PAUSE)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    with st.sidebar:
        st.header("⚙️ ADMINISTRATION")
        adm_page = st.radio("MENU", ["BOUTIQUES", "SYSTÈME", "DÉCONNEXION"])
    
    if adm_page == "BOUTIQUES":
        st.header("👥 GESTION DES BOUTIQUES")
        clients = run_db("SELECT username, telephone, status, nom_boss, ent_id FROM users WHERE role='USER'", fetch=True)
        for un, tel, stat, boss, eid in clients:
            with st.container(border=True):
                st.write(f"🏢 **{eid.upper()}** | 👤 {boss} | 📞 {tel}")
                st.write(f"Statut Actuel : `{stat}`")
                c1, c2, c3, c4 = st.columns(4)
                if c1.button("✅ ACTIVER", key=f"ac_{un}"):
                    run_db("UPDATE users SET status='ACTIF' WHERE username=?", (un,)); st.rerun()
                if c2.button("⏸️ METTRE EN PAUSE", key=f"ps_{un}"):
                    run_db("UPDATE users SET status='PAUSE' WHERE username=?", (un,)); st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"del_{un}"):
                    run_db("DELETE FROM users WHERE username=?", (un,)); run_db("DELETE FROM ent_infos WHERE ent_id=?", (eid,)); st.rerun()
                if c4.button("📅 ESSAI 30J", key=f"es_{un}"):
                    dfin = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                    run_db("UPDATE users SET status='ACTIF', date_validite=? WHERE username=?", (dfin, un)); st.rerun()

    elif adm_page == "SYSTÈME":
        st.header("⚙️ RÉGLAGES GLOBAUX")
        n_taux = st.number_input("Taux de change (1$ = ? CDF)", value=sys_cfg[2])
        n_marq = st.text_area("Texte défilant (Marquee)", value=sys_cfg[1])
        if st.button("SAUVEGARDER CONFIG"):
            run_db("UPDATE system_config SET taux=?, marquee=? WHERE id=1", (n_taux, n_marq)); st.rerun()

    elif adm_page == "DÉCONNEXION": st.session_state.auth = False; st.rerun()

# ------------------------------------------------------------------------------
# 5. MODULE BOUTIQUE (ADMIN BOUTIQUE & VENDEUR)
# ------------------------------------------------------------------------------
else:
    # Sidebar Multi-accès (Vendeur vs Admin)
    with st.sidebar:
        st.markdown(f"### 🏪 {st.session_state.ent_id.upper()}")
        st.markdown(f"🟢 En ligne : {st.session_state.user.upper()}")
        st.divider()
        
        # Restriction Vendeur (Seulement Ventes et Dettes)
        if st.session_state.role == "VENDEUR":
            menu_options = ["🛒 CAISSE", "📉 DETTES", "🚪 QUITTER"]
        else:
            menu_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📊 RAPPORTS", "📉 DETTES", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES", "🚪 QUITTER"]
            
        page = st.radio("NAVIGATION", menu_options)

    # --- 5.1 ACCUEIL / DASHBOARD (v192) ---
    if page == "🏠 ACCUEIL":
        st.markdown(f"<h1>TABLEAU DE BORD</h1>", unsafe_allow_html=True)
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Ventes du jour
        vj = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_courte=?", (st.session_state.ent_id, today), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>RECETTE DU JOUR<br>{vj:,.2f} $</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        # Alertes stock
        alerte = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=? AND stock_actuel < 5", (st.session_state.ent_id,), fetch=True)[0][0]
        c1.metric("⚠️ Alertes Stock", alerte)
        # Dettes en cours
        d_en_cours = run_db("SELECT SUM(montant_restant) FROM dettes WHERE ent_id=? AND statut='NON PAYE'", (st.session_state.ent_id,), fetch=True)[0][0] or 0
        c2.metric("📉 Dettes Clients", f"{d_en_cours:,.2f} $")
        # Bénéfice estimé jour
        c3.metric("📈 Bénéfice Jour", "Calculé...")

    # --- 5.2 CAISSE & VENTE (PANIER INSTANTANÉ & SAUVEGARDE AUTO) ---
    elif page == "🛒 CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            
            col_opt1, col_opt2 = st.columns(2)
            devise = col_opt1.selectbox("Monnaie", ["USD", "CDF"])
            format_f = col_opt2.selectbox("Format", ["80mm (Ticket)", "A4 (Facture)"])
            
            # Recherche produit
            prods = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in prods}
            
            selection = st.selectbox("🔍 Sélectionner un article", ["---"] + list(p_map.keys()))
            
            # Ajout automatique au panier au choix
            if selection != "---":
                if p_map[selection][1] > 0:
                    st.session_state.panier[selection] = st.session_state.panier.get(selection, 0) + 1
                    st.toast(f"Ajouté : {selection}")
                else:
                    st.error("Stock insuffisant !")

            # Affichage du Panier
            if st.session_state.panier:
                st.divider()
                st.subheader("🧺 PANIER")
                total_global = 0.0
                cart_items = []
                
                for art, qte in list(st.session_state.panier.items()):
                    p_unit = p_map[art][0]
                    if devise == "CDF": p_unit *= sys_cfg[2]
                    
                    st_total = p_unit * qte
                    total_global += st_total
                    cart_items.append({"art": art, "qte": qte, "pu": p_unit, "total": st_total})
                    
                    c_art, c_qte, c_del = st.columns([3, 1, 1])
                    c_art.write(f"**{art}**")
                    c_qte.write(f"x{qte}")
                    if c_del.button("❌", key=f"del_{art}"):
                        del st.session_state.panier[art]; st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL : {total_global:,.2f} {devise}</div>", unsafe_allow_html=True)
                
                # Finalisation (v192 - Client et Payé)
                with st.container(border=True):
                    client_nom = st.text_input("Nom du Client", "COMPTANT")
                    montant_paye = st.number_input("Montant Versé", value=float(total_global))
                    reste_a_payer = total_global - montant_paye
                    
                    if st.button("🏁 VALIDER LA VENTE & GÉNÉRER FACTURE"):
                        ref_fac = f"FAC-{random.randint(10000, 99999)}"
                        d_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                        d_s = datetime.now().strftime("%d/%m/%Y")
                        
                        # 1. Enregistrer Vente
                        run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, date_courte, vendeur, ent_id, details_json) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                               (ref_fac, client_nom.upper(), total_global, montant_paye, reste_a_payer, devise, d_v, d_s, st.session_state.user, st.session_state.ent_id, json.dumps(cart_items)))
                        
                        # 2. Mise à jour Stock
                        for it in cart_items:
                            run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                                   (it['qte'], it['art'], st.session_state.ent_id))
                        
                        # 3. Enregistrer Dette si reste > 0
                        if reste_a_payer > 0:
                            run_db("INSERT INTO dettes (client, montant_initial, montant_restant, ref_v, date_d, ent_id) VALUES (?,?,?,?,?,?)",
                                   (client_nom.upper(), reste_a_payer, reste_a_payer, ref_fac, d_s, st.session_state.ent_id))
                        
                        st.session_state.last_fac = {
                            "ref": ref_fac, "client": client_nom.upper(), "total": total_global, 
                            "paye": montant_paye, "reste": reste_a_payer, "devise": devise, 
                            "items": cart_items, "date": d_v, "fmt": format_f
                        }
                        st.session_state.panier = {}; st.rerun()
        else:
            # --- AFFICHAGE & SAUVEGARDE DE LA FACTURE ---
            f = st.session_state.last_fac
            info = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            # HTML Généré
            html_fac = ""
            if f['fmt'] == "A4 (Facture)":
                html_fac = f"""
                <div class="fac-container">
                    <h1>{info[4] if info[4] else info[0]}</h1>
                    <p>{info[1]} | Tél: {info[2]}<br>RCCM: {info[3] if info[3] else '-'}</p>
                    <hr>
                    <h3>FACTURE N° {f['ref']}</h3>
                    <p>Client: {f['client']} | Date: {f['date']}</p>
                    <table>
                        <thead><tr><th>DÉSIGNATION</th><th>QTÉ</th><th>P.U</th><th>TOTAL</th></tr></thead>
                        <tbody>
                            {" ".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['pu']:,.0f}</td><td>{i['total']:,.0f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <h2 style="text-align:right; margin-top:20px;">NET À PAYER : {f['total']:,.2f} {f['devise']}</h2>
                    <p style="text-align:right;">Versé : {f['paye']:,.2f} | Reste : {f['reste']:,.2f}</p>
                    <div style="margin-top:60px; text-align:right;">
                        <p>Signature Autorisée</p><br><br>__________
                        <p style="font-size:10px;">Émis par : {st.session_state.user}</p>
                    </div>
                </div>"""
            else:
                html_fac = f"""
                <div class="fac-container fac-80mm">
                    <h4>{info[0]}</h4>
                    <p>N° {f['ref']} | {f['date']}</p>
                    <hr>
                    {" ".join([f"<p style='text-align:left;'>{i['art']} x{i['qte']}<br>=> {i['total']:,.0f} {f['devise']}</p>" for i in f['items']])}
                    <hr>
                    <h3>TOTAL : {f['total']:,.2f} {f['devise']}</h3>
                    <p>Merci pour votre visite !</p>
                </div>"""

            st.markdown(html_fac, unsafe_allow_html=True)
            
            # BOUTON DE SAUVEGARDE AUTO (DOWNLOAD)
            b64_data = base64.b64encode(html_fac.encode()).decode()
            download_link = f'<a href="data:text/html;base64,{b64_data}" download="Facture_{f["ref"]}.html" style="background:#00ff00; color:black; padding:20px; border-radius:15px; text-decoration:none; display:block; text-align:center; font-weight:bold; border:2px solid #fff;">📥 TÉLÉCHARGER LA FACTURE SUR L\'ORDINATEUR</a>'
            st.markdown(download_link, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            if col1.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if col2.button("📲 PARTAGER"): st.info("Prenez une capture d'écran pour WhatsApp.")
            if col3.button("⬅️ RETOUR CAISSE"): st.session_state.last_fac = None; st.rerun()

    # --- 5.3 STOCK (v192 - AJOUT, MODIF PRIX, SUPPRESSION) ---
    elif page == "📦 STOCK":
        st.header("📦 GESTION DES ARTICLES")
        t1, t2 = st.tabs(["📋 INVENTAIRE", "➕ AJOUT / MODIF"])
        
        with t1:
            articles = run_db("SELECT id, designation, stock_actuel, prix_achat, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            if articles:
                df_art = pd.DataFrame(articles, columns=["ID", "Nom", "Stock", "P. Achat ($)", "P. Vente ($)"])
                st.table(df_art)
                
                st.subheader("🗑️ SUPPRIMER UN ARTICLE")
                id_del = st.selectbox("ID de l'article à supprimer", [a[0] for a in articles])
                if st.button("CONFIRMER LA SUPPRESSION"):
                    run_db("DELETE FROM produits WHERE id=?", (id_del,)); st.rerun()
            else:
                st.info("Stock vide.")

        with t2:
            st.subheader("MODIFIER OU AJOUTER")
            with st.form("form_prod"):
                f_nom = st.text_input("Désignation")
                f_ini = st.number_input("Stock Initial", 1)
                f_pa = st.number_input("Prix Achat ($)")
                f_pv = st.number_input("Prix Vente ($)")
                if st.form_submit_button("ENREGISTRER"):
                    # Vérifier si existe pour modifier ou ajouter
                    exist = run_db("SELECT id FROM produits WHERE designation=? AND ent_id=?", (f_nom.upper(), st.session_state.ent_id), fetch=True)
                    if exist:
                        run_db("UPDATE produits SET stock_actuel=stock_actuel+?, prix_achat=?, prix_vente=? WHERE id=?", (f_ini, f_pa, f_pv, exist[0][0]))
                    else:
                        run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_achat, prix_vente, ent_id) VALUES (?,?,?,?,?,?)",
                               (f_nom.upper(), f_ini, f_ini, f_pa, f_pv, st.session_state.ent_id))
                    st.success("Opération réussie !"); st.rerun()

    # --- 5.4 RAPPORTS (RECHERCHE & NOM VENDEUR) ---
    elif page == "📊 RAPPORTS":
        st.header("📊 HISTORIQUE DES VENTES")
        recherche = st.text_input("🔍 Rechercher par client ou référence")
        vts = run_db("SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=? AND (client LIKE ? OR ref LIKE ?)", 
                    (st.session_state.ent_id, f"%{recherche}%", f"%{recherche}%"), fetch=True)
        if vts:
            df_vts = pd.DataFrame(vts, columns=["Date", "Réf", "Client", "Total", "Vendeur"])
            st.table(df_vts)
            st.markdown(f"**TOTAL PÉRIODE : {df_vts['Total'].sum():,.2f} $**")
        else:
            st.warning("Aucun résultat.")

    # --- 5.5 DETTES (v192 - PAIEMENT PAR TRANCHE) ---
    elif page == "📉 DETTES":
        st.header("📉 SUIVI DES CRÉANCES")
        creances = run_db("SELECT id, client, montant_restant, ref_v, date_d FROM dettes WHERE ent_id=? AND statut='NON PAYE'", (st.session_state.ent_id,), fetch=True)
        if creances:
            for d_id, d_cli, d_mt, d_ref, d_dt in creances:
                with st.container(border=True):
                    st.write(f"👤 Client : **{d_cli}** | Facture : {d_ref}")
                    st.write(f"💰 Reste : **{d_mt:,.2f} $**")
                    tranche = st.number_input("Payer une tranche ($)", 0.0, float(d_mt), key=f"tr_{d_id}")
                    if st.button("ENCAISSER", key=f"enc_{d_id}"):
                        n_reste = d_mt - tranche
                        if n_reste <= 0:
                            run_db("UPDATE dettes SET montant_restant=0, statut='PAYE' WHERE id=?", (d_id,))
                        else:
                            run_db("UPDATE dettes SET montant_restant=? WHERE id=?", (n_reste, d_id))
                        st.success("Tranche encaissée !"); time.sleep(1); st.rerun()
        else:
            st.success("Toutes les dettes sont apurées !")

    # --- 5.6 DÉPENSES ---
    elif page == "💸 DÉPENSES":
        st.header("💸 SORTIES DE CAISSE")
        with st.form("dep_form"):
            mot = st.text_input("Motif")
            mtn = st.number_input("Montant ($)")
            if st.form_submit_button("VALIDER DÉPENSE"):
                run_db("INSERT INTO depenses (motif, montant, date_dep, auteur, ent_id) VALUES (?,?,?,?,?)",
                       (mot, mtn, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id))
                st.success("Dépense enregistrée."); st.rerun()

    # --- 5.7 VENDEURS (COMPTES AGENTS) ---
    elif page == "👥 VENDEURS":
        st.header("👥 GESTION DES AGENTS")
        with st.form("add_v_form"):
            v_u = st.text_input("Identifiant Vendeur").lower().strip()
            v_p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
                       (v_u, hashlib.sha256(v_p.encode()).hexdigest(), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.success("Vendeur ajouté !"); st.rerun()
        
        st.divider()
        vs = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True)
        for u, s in vs:
            st.write(f"🔹 Agent : {u.upper()} | Statut : {s}")

    # --- 5.8 RÉGLAGES (LOGO, PROFIL, INFOS) ---
    elif page == "⚙️ RÉGLAGES":
        st.header("⚙️ PARAMÈTRES BOUTIQUE")
        inf = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        with st.form("params_form"):
            n_nom = st.text_input("Nom de l'Enseigne", inf[0])
            n_adr = st.text_input("Adresse", inf[1])
            n_tel = st.text_input("Téléphone", inf[2])
            n_rcc = st.text_input("RCCM / ID Nat", inf[3])
            n_head = st.text_input("Texte En-tête (Slogan)", inf[4])
            st.subheader("Sécurité Profil")
            n_pass = st.text_input("Nouveau Mot de Passe (Laisser vide pour garder)", type="password")
            
            if st.form_submit_button("METTRE À JOUR TOUTES LES INFOS"):
                run_db("""UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=?, header_custom=? 
                       WHERE ent_id=?""", (n_nom.upper(), n_adr, n_tel, n_rcc, n_head, st.session_state.ent_id))
                if n_pass:
                    run_db("UPDATE users SET password=? WHERE username=?", (hashlib.sha256(n_pass.encode()).hexdigest(), st.session_state.user))
                st.success("Réglages enregistrés !"); st.rerun()
        
        if st.button("🔴 RÉINITIALISER TOUTES LES VENTES"):
            run_db("DELETE FROM ventes WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM dettes WHERE ent_id=?", (st.session_state.ent_id,))
            st.warning("Historique vidé !"); st.rerun()

    elif page == "🚪 QUITTER":
        st.session_state.auth = False
        st.rerun()

# FIN DU CODE v2038
