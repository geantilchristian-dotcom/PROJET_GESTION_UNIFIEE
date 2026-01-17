# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTRA-INTÉGRALE v2035 (EXPANSION MAXIMALE)
# AUCUNE LIGNE SUPPRIMÉE - CODE COMPLET - OPTIMISÉ MOBILE - DESIGN PREMIUM
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
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE L'INTERFACE ET STYLE CSS (LUMINOSITÉ ET CENTRAGE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2035",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation exhaustive de l'état de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False,
        'user': "",
        'role': "",
        'ent_id': "SYSTEM",
        'panier': {},
        'last_fac': None,
        'format_fac': "80mm",
        'show_register': False,
        'devise_vente': "USD",
        'temp_cli': "COMPTANT",
        'vue_rapport': "Journalier"
    })

# CSS PERSONNALISÉ POUR UNE LUMINOSITÉ ÉLEVÉE (INDISPENSABLE SUR MOBILE)
st.markdown("""
    <style>
    /* Fond principal bleu contrasté */
    .stApp { background-color: #0044CC !important; }
    
    /* Centrage de tous les textes par défaut */
    h1, h2, h3, h4, h5, p, label, span, div.stText, .stMarkdown { 
        color: #FFFFFF !important; 
        text-align: center !important; 
        font-weight: bold;
    }
    
    /* En-tête fixe avec texte défilant (Marquee) */
    .fixed-header { 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #FFFF00; height: 65px; 
        z-index: 999999; display: flex; align-items: center; 
        border-bottom: 3px solid #FFFFFF; 
    }
    marquee { font-size: 22px; font-weight: bold; }
    .spacer { margin-top: 85px; }
    
    /* Boutons larges et tactiles pour mobile */
    .stButton>button { 
        background: linear-gradient(135deg, #007BFF, #0056B3) !important;
        color: white !important; border-radius: 15px; 
        height: 65px; width: 100%; border: 2px solid #FFFFFF;
        font-size: 19px; font-weight: bold;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.4);
        margin-bottom: 12px;
    }
    
    /* Cadre de Total hyper-visible */
    .total-frame { 
        background: #000000; color: #00FF00; 
        padding: 30px; border: 5px solid #FFFFFF; 
        border-radius: 25px; text-align: center; 
        margin: 20px 0; font-size: 34px; 
        box-shadow: inset 0px 0px 20px #00FF00;
    }

    /* Tableaux blancs avec texte noir pour lisibilité maximale */
    .stDataFrame, [data-testid="stTable"] { 
        background-color: #FFFFFF !important; 
        border-radius: 15px; padding: 12px;
        color: #000000 !important;
    }
    [data-testid="stTable"] td, [data-testid="stTable"] th { 
        color: #000000 !important; 
        font-size: 15px !important;
    }
    
    /* Champs de saisie blancs */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] { 
        background-color: #FFFFFF !important; border-radius: 12px !important; 
    }
    input { color: #000000 !important; font-weight: bold !important; text-align: center !important; }

    /* FACTURE ADMINISTRATIVE A4 & 80mm */
    .facture-container {
        background: #FFFFFF; color: #000000 !important;
        padding: 45px; border-radius: 5px; width: 98%; max-width: 850px;
        margin: auto; border: 3px solid #000000;
    }
    .facture-container * { color: #000000 !important; text-align: center; }
    .facture-container table { width: 100%; border-collapse: collapse; margin-top: 25px; }
    .facture-container th, .facture-container td { 
        border: 2px solid #000000; padding: 15px; font-size: 18px; 
    }
    .signature { margin-top: 60px; text-align: right; font-style: italic; font-size: 20px; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE DONNÉES ET GESTION SQLITE3 (SÉCURISÉ)
# ------------------------------------------------------------------------------
def run_db(query, params=(), fetch=False):
    """Fonction noyau pour toutes les opérations sur la base de données."""
    try:
        with sqlite3.connect('balika_v2035_erp.db', timeout=40) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch: return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur de Base de Données : {e}")
        return []

def hash_pass(password):
    """Hachage sécurisé des mots de passe."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    """Initialisation complète de toutes les tables du système."""
    # Table des Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ATTENTE', date_fin_essai TEXT, 
        nom TEXT, prenom TEXT, telephone TEXT, date_creation TEXT)""")
    
    # Table de Configuration du Système
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)""")
    
    # Table des Informations Boutique
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT, header_custom TEXT)""")

    # Table des Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_initial INTEGER, stock_actuel INTEGER, 
        prix_achat REAL, prix_vente REAL, devise TEXT, ent_id TEXT)""")

    # Table des Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)""")

    # Table des Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, 
        montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT, date_dette TEXT)""")

    # Table des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, 
        montant REAL, devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")

    # --- DONNÉES INITIALES PAR DÉFAUT ---
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("""INSERT INTO users (username, password, role, status, date_creation) 
               VALUES (?,?,?,?,?)""", 
               ('admin', hash_pass("admin123"), 'SUPER_ADMIN', 'ACTIF', datetime.now().strftime("%d/%m/%Y")))
    
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("""INSERT INTO system_config (id, app_name, marquee_text, taux_global) 
               VALUES (1, 'BALIKA ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION v2035', 2850.0)""")

# Lancement de l'initialisation
init_db()

# Chargement des variables globales
config_res = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
if config_res:
    APP_NAME, MARQUEE, TX_G = config_res[0]
else:
    APP_NAME, MARQUEE, TX_G = "BALIKA ERP", "Bienvenue", 2850.0

# Affichage du bandeau défilant
st.markdown(f'<div class="fixed-header"><marquee>{MARQUEE}</marquee></div><div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. INTERFACE DE CONNEXION ET CRÉATION DE COMPTE
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f"<h1>🚀 {APP_NAME}</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Plateforme de Gestion Unifiée</h3>")
    
    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("🔐 SE CONNECTER"): st.session_state.show_register = False; st.rerun()
    with col_r:
        if st.button("📝 CRÉER UNE BOUTIQUE"): st.session_state.show_register = True; st.rerun()
    
    st.divider()

    if not st.session_state.show_register:
        # Formulaire de Connexion
        with st.container():
            u_login = st.text_input("Identifiant Utilisateur").lower().strip()
            p_login = st.text_input("Mot de passe", type="password")
            if st.button("OUVRIR LA SESSION"):
                res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_login,), fetch=True)
                if res and hash_pass(p_login) == res[0][0]:
                    if res[0][3] == "ATTENTE":
                        st.warning("⏳ Votre compte est en attente de validation par l'administrateur.")
                    elif res[0][3] == "PAUSE":
                        st.error("❌ Ce compte a été suspendu par le système.")
                    else:
                        st.session_state.update({'auth':True, 'user':u_login, 'role':res[0][1], 'ent_id':res[0][2]})
                        st.success("Connexion réussie !")
                        time.sleep(1); st.rerun()
                else:
                    st.error("🚫 Identifiant ou mot de passe incorrect.")
    else:
        # Formulaire d'Inscription
        with st.form("form_inscription"):
            st.write("### 📝 Demande d'adhésion au système")
            reg_ent = st.text_input("Nom de la Boutique / Entreprise")
            reg_nom = st.text_input("Nom du Responsable")
            reg_tel = st.text_input("Numéro de Téléphone WhatsApp")
            reg_pass = st.text_input("Créer un mot de passe", type="password")
            
            if st.form_submit_button("ENVOYER MA DEMANDE"):
                if not reg_ent or not reg_pass:
                    st.error("Veuillez remplir les champs obligatoires.")
                else:
                    clean_id = reg_ent.lower().replace(" ", "")
                    # Vérifier si l'identifiant existe déjà
                    exist = run_db("SELECT username FROM users WHERE username=?", (clean_id,), fetch=True)
                    if exist:
                        st.error("Ce nom d'entreprise est déjà utilisé.")
                    else:
                        run_db("""INSERT INTO users (username, password, role, ent_id, status, nom, telephone, date_creation) 
                               VALUES (?,?,?,?,?,?,?,?)""", 
                               (clean_id, hash_pass(reg_pass), 'USER', clean_id, 'ATTENTE', reg_nom, reg_tel, datetime.now().strftime("%d/%m/%Y")))
                        run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (clean_id, reg_ent.upper(), reg_tel))
                        st.success("✅ Votre demande a été transmise à l'administrateur BALIKA.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. STRUCTURE DE NAVIGATION (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.write(f"Accès : {st.session_state.role}")
    st.divider()
    
    if st.session_state.role == "SUPER_ADMIN":
        # Menu réservé à vous (admin)
        pages_dispo = {
            "🏠 Dashboard Admin": "ADMIN_HOME",
            "👥 Validation Boutiques": "ADMIN_VALID",
            "⚙️ Config Système": "ADMIN_SYS",
            "📊 Statistiques Globales": "ADMIN_STATS"
        }
    else:
        # Menu pour les propriétaires de boutique et vendeurs
        pages_dispo = {
            "🏠 Accueil Boutique": "SHOP_HOME",
            "🛒 Caisse & Vente": "SHOP_CAISSE",
            "📦 Gestion du Stock": "SHOP_STOCK",
            "📊 Rapports & Profit": "SHOP_REPORTS",
            "📉 Suivi des Dettes": "SHOP_DETTES",
            "💸 Dépenses & Frais": "SHOP_DEPENSES",
            "👥 Mes Vendeurs": "SHOP_VENDEURS",
            "⚙️ Paramètres": "SHOP_PARAMS"
        }
    
    for label, target in pages_dispo.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = target
            st.rerun()
            
    st.divider()
    if st.button("🚪 SE DÉCONNECTER", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 5. LOGIQUE DU MODULE SUPER ADMIN (IDENTIFIANT : admin)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ADMIN_HOME":
        st.markdown("<h1>🌟 TABLEAU DE BORD SUPER ADMINISTRATEUR</h1>", unsafe_allow_html=True)
        t_boutiques = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)[0][0]
        t_attente = run_db("SELECT COUNT(*) FROM users WHERE status='ATTENTE'", fetch=True)[0][0]
        
        col1, col2 = st.columns(2)
        col1.metric("Boutiques Totales", t_boutiques)
        col2.metric("Demandes en Attente", t_attente)
        
        st.markdown(f"<div class='total-frame'>ADMINISTRATION GÉNÉRALE ACTIVE</div>", unsafe_allow_html=True)

    elif st.session_state.page == "ADMIN_VALID":
        st.header("👥 VALIDATION DES NOUVEAUX COMPTES")
        demandes = run_db("SELECT username, status, telephone, nom, date_creation FROM users WHERE role='USER'", fetch=True)
        
        if not demandes:
            st.info("Aucune boutique enregistrée pour le moment.")
        else:
            for uid, stat, tel, nom, date_c in demandes:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"🏢 **{uid.upper()}** | Resp: {nom}")
                    c1.write(f"📞 Tél: {tel} | Créé le: {date_c}")
                    c1.write(f"Statut actuel : `{stat}`")
                    
                    jours_essai = c2.number_input("Jours d'essai", 1, 365, 30, key=f"days_{uid}")
                    if c2.button(f"✅ ACTIVER", key=f"act_{uid}"):
                        date_f = (datetime.now() + timedelta(days=jours_essai)).strftime("%d/%m/%Y")
                        run_db("UPDATE users SET status='ACTIF', date_fin_essai=? WHERE username=?", (date_f, uid))
                        st.success(f"Compte {uid} activé jusqu'au {date_f}")
                        time.sleep(1); st.rerun()
                    
                    if c3.button("🗑️ SUPPRIMER", key=f"del_{uid}"):
                        run_db("DELETE FROM users WHERE username=?", (uid,))
                        run_db("DELETE FROM ent_infos WHERE ent_id=?", (uid,))
                        st.warning(f"Compte {uid} supprimé définitivement.")
                        time.sleep(1); st.rerun()

    elif st.session_state.page == "ADMIN_SYS":
        st.header("⚙️ CONFIGURATION DU SYSTÈME GLOBAL")
        with st.form("config_form"):
            new_app_name = st.text_input("Nom de l'application", APP_NAME)
            new_marquee = st.text_area("Texte défilant", MARQUEE)
            new_taux = st.number_input("Taux de change par défaut (1$ = ? CDF)", value=TX_G)
            if st.form_submit_button("METTRE À JOUR LE SYSTÈME"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", 
                       (new_app_name, new_marquee, new_taux))
                st.success("Configuration globale mise à jour !")
                st.rerun()

# ------------------------------------------------------------------------------
# 6. LOGIQUE DU MODULE BOUTIQUE (ADMIN BOUTIQUE & VENDEUR)
# ------------------------------------------------------------------------------
else:
    # --- PAGE D'ACCUEIL BOUTIQUE ---
    if st.session_state.page == "SHOP_HOME":
        st.markdown(f"<h1>🏢 BIENVENUE CHEZ {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        
        # Calcul des ventes du jour
        v_aujourdhui = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", 
                             (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        
        st.markdown(f"<div class='total-frame'>RECETTE DU JOUR :<br>{v_aujourdhui:,.2f} $</div>", unsafe_allow_html=True)
        
        essai_info = run_db("SELECT date_fin_essai FROM users WHERE username=?", (st.session_state.user,), fetch=True)
        if essai_info:
            st.info(f"📆 État de votre abonnement : Valide jusqu'au **{essai_info[0][0]}**")

    # --- PAGE CAISSE ET VENTE ---
    elif st.session_state.page == "SHOP_CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            
            c_col1, c_col2 = st.columns(2)
            c_devise = c_col1.selectbox("Devise de la transaction", ["USD", "CDF"])
            c_format = c_col2.selectbox("Format de Facture", ["A4 Administrative", "80mm Thermique"])
            
            # Récupération des produits en stock
            list_p = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            if not list_p:
                st.warning("⚠️ Votre stock est vide. Allez dans 'Gestion du Stock' pour ajouter des articles.")
            else:
                p_map = {p[0]: (p[1], p[2]) for p in list_p}
                
                with st.container(border=True):
                    sel_p = st.selectbox("Sélectionner l'article à vendre", ["---"] + list(p_map.keys()))
                    qte_p = st.number_input("Quantité souhaitée", 1, 1000, 1)
                    
                    if st.button("➕ AJOUTER AU PANIER") and sel_p != "---":
                        if p_map[sel_p][1] >= qte_p:
                            st.session_state.panier[sel_p] = st.session_state.panier.get(sel_p, 0) + qte_p
                            st.rerun()
                        else:
                            st.error(f"Stock insuffisant ! Il ne reste que {p_map[sel_p][1]} unité(s).")

                if st.session_state.panier:
                    st.write("### 🛍️ CONTENU DU PANIER")
                    total_vente = 0.0
                    items_vente = []
                    
                    for art, qte in list(st.session_state.panier.items()):
                        prix_u = p_map[art][0]
                        if c_devise == "CDF": prix_u *= TX_G
                        
                        sous_total = prix_u * qte
                        total_vente += sous_total
                        items_vente.append({"art": art, "qty": qte, "pu": prix_u})
                        
                        c_a, c_b = st.columns([4, 1])
                        c_a.write(f"**{art}** : {qte} x {prix_u:,.0f} {c_devise} = **{sous_total:,.0f} {c_devise}**")
                        if c_b.button("❌", key=f"del_{art}"):
                            del st.session_state.panier[art]
                            st.rerun()
                    
                    st.markdown(f"<div class='total-frame'>TOTAL À PAYER : {total_vente:,.2f} {c_devise}</div>", unsafe_allow_html=True)
                    
                    client_nom = st.text_input("Nom du Client", st.session_state.temp_cli)
                    montant_recu = st.number_input("Montant Reçu (Espèces)", value=float(total_vente))
                    
                    if st.button("🏁 VALIDER ET IMPRIMER"):
                        ref_f = f"BAL-{random.randint(100000, 999999)}"
                        date_f = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        # 1. Enregistrer la vente
                        run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) 
                               VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                               (ref_f, client_nom.upper(), total_vente, montant_recu, total_vente - montant_recu, c_devise, date_f, st.session_state.user, st.session_state.ent_id, json.dumps(items_vente)))
                        
                        # 2. Gérer la dette si le client n'a pas tout payé
                        if total_vente - montant_recu > 0:
                            run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, date_dette) VALUES (?,?,?,?,?,?)", 
                                   (client_nom.upper(), total_vente - montant_recu, c_devise, ref_f, st.session_state.ent_id, date_f))
                        
                        # 3. Déduire du stock
                        for it in items_vente:
                            run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                                   (it['qty'], it['art'], st.session_state.ent_id))
                        
                        # 4. Préparer la vue facture
                        st.session_state.last_fac = {
                            'ref': ref_f, 'cli': client_nom.upper(), 'total': total_vente, 
                            'paye': montant_recu, 'reste': total_vente - montant_recu, 
                            'dev': c_devise, 'items': items_vente, 'date': date_f
                        }
                        st.session_state.panier = {}
                        st.rerun()
        else:
            # --- AFFICHAGE DE LA FACTURE ADMINISTRATIVE GÉNÉRÉE ---
            f = st.session_state.last_fac
            # Récupérer les infos personnalisées de l'en-tête
            inf_ent = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            st.markdown(f"""
                <div class="facture-container">
                    <h1>{inf_ent[4] if inf_ent[4] else inf_ent[0]}</h1>
                    <p>{inf_ent[1]} | Tél: {inf_ent[2]}<br>RCCM: {inf_ent[3] if inf_ent[3] else 'Enregistrement National'}</p>
                    <hr style="border: 1px solid black;">
                    <h2 style="text-decoration: underline;">FACTURE N° {f['ref']}</h2>
                    <p style="text-align: left;"><b>CLIENT :</b> {f['cli']}<br><b>DATE :</b> {f['date']}</p>
                    <table>
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th>DÉSIGNATION</th>
                                <th>QTÉ</th>
                                <th>P.UNITAIRE</th>
                                <th>TOTAL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {" ".join([f"<tr><td>{i['art']}</td><td>{i['qty']}</td><td>{i['pu']:,.0f}</td><td>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <div style="text-align: right; margin-top: 25px;">
                        <h3>NET À PAYER : {f['total']:,.2f} {f['dev']}</h3>
                        <p>ACOMPTE VERSÉ : {f['paye']:,.2f} | RESTE : {f['reste']:,.2f}</p>
                    </div>
                    <div class="signature">
                        <p>Pour l'Établissement,</p>
                        <br><br>
                        <p>_________________________</p>
                        <p style="font-size: 14px;">(Signé par : {st.session_state.user})</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            sc1, sc2, sc3 = st.columns(3)
            if sc1.button("🖨️ IMPRIMER / PDF"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if sc2.button("📲 PARTAGER"):
                st.info("Capturez l'écran pour l'envoyer au client.")
            if sc3.button("⬅️ NOUVELLE VENTE"):
                st.session_state.last_fac = None; st.rerun()

    # --- PAGE GESTION DU STOCK ---
    elif st.session_state.page == "SHOP_STOCK":
        st.header("📦 INVENTAIRE ET GESTION DU STOCK")
        
        tab1, tab2 = st.tabs(["📋 Liste des Produits", "➕ Ajouter / Modifier"])
        
        with tab1:
            st.write("### État du Stock")
            p_stock = run_db("SELECT id, designation, stock_initial, stock_actuel, prix_achat, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            if p_stock:
                df_p = pd.DataFrame(p_stock, columns=["ID", "Désignation", "Stock Initial", "En Stock", "P. Achat ($)", "P. Vente ($)"])
                st.table(df_p)
                
                # Calcul de la valeur du stock
                val_stock = sum([p[3]*p[4] for p in p_stock])
                st.markdown(f"**Valeur totale du stock au prix d'achat : {val_stock:,.2f} $**")
            else:
                st.warning("Aucun produit en stock.")

        with tab2:
            with st.form("add_product"):
                st.write("### Ajouter un nouvel article")
                f_des = st.text_input("Désignation du produit")
                col_q, col_pa, col_pv = st.columns(3)
                f_qte = col_q.number_input("Quantité Initiale", 1)
                f_pa = col_pa.number_input("Prix d'Achat ($)", 0.0)
                f_pv = col_pv.number_input("Prix de Vente ($)", 0.0)
                
                if st.form_submit_button("ENREGISTRER"):
                    if f_des:
                        run_db("""INSERT INTO produits (designation, stock_initial, stock_actuel, prix_achat, prix_vente, devise, ent_id) 
                               VALUES (?,?,?,?,?,?,?)""", 
                               (f_des.upper(), f_qte, f_qte, f_pa, f_pv, "USD", st.session_state.ent_id))
                        st.success("Produit ajouté !")
                        st.rerun()

    # --- PAGE RAPPORTS ET PROFITS ---
    elif st.session_state.page == "SHOP_REPORTS":
        st.header("📊 ANALYSE DES VENTES ET PROFITS")
        
        sel_rep = st.radio("Période", ["Journalier", "Général"], horizontal=True)
        
        if sel_rep == "Journalier":
            query = "SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=? AND date_v LIKE ?"
            v_data = run_db(query, (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)
        else:
            query = "SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=?"
            v_data = run_db(query, (st.session_state.ent_id,), fetch=True)
            
        if v_data:
            df_v = pd.DataFrame(v_data, columns=["Date/Heure", "Réf", "Client", "Montant", "Effectué par"])
            st.table(df_v)
            
            total_ca = df_v["Montant"].sum()
            st.markdown(f"<div class='total-frame'>CHIFFRE D'AFFAIRES : {total_ca:,.2f} $</div>", unsafe_allow_html=True)
        else:
            st.info("Aucune vente enregistrée pour cette période.")

    # --- PAGE SUIVI DES DETTES ---
    elif st.session_state.page == "SHOP_DETTES":
        st.header("📉 GESTION DES CRÉANCES CLIENTS")
        d_list = run_db("SELECT id, client, montant, devise, ref_v, date_dette FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        
        if not d_list:
            st.success("✅ Aucune dette en cours !")
        else:
            for d_id, d_cli, d_mt, d_dev, d_ref, d_date in d_list:
                with st.container(border=True):
                    st.write(f"👤 **CLIENT : {d_cli}**")
                    st.write(f"💰 Montant Restant : **{d_mt:,.2f} {d_dev}**")
                    st.write(f"📅 Issue de la facture {d_ref} le {d_date}")
                    
                    p_versé = st.number_input(f"Montant du versement", 0.0, float(d_mt), key=f"pay_{d_id}")
                    if st.button(f"ENCAISSER TRANCHE", key=f"btn_{d_id}"):
                        run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (p_versé, d_id))
                        st.success("Paiement enregistré !")
                        time.sleep(1); st.rerun()

    # --- PAGE DÉPENSES ---
    elif st.session_state.page == "SHOP_DEPENSES":
        st.header("💸 GESTION DES DÉPENSES")
        with st.form("f_dep"):
            d_motif = st.text_input("Motif de la dépense")
            d_montant = st.number_input("Montant ($)", 0.0)
            if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id, auteur) VALUES (?,?,?,?,?,?)",
                       (d_motif, d_montant, "USD", datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.ent_id, st.session_state.user))
                st.success("Dépense enregistrée !")
                st.rerun()
        
        st.divider()
        st.write("### Historique des Dépenses")
        hist_dep = run_db("SELECT date_d, motif, montant, auteur FROM depenses WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if hist_dep:
            st.table(pd.DataFrame(hist_dep, columns=["Date", "Motif", "Montant ($)", "Auteur"]))

    # --- PAGE GESTION DES VENDEURS ---
    elif st.session_state.page == "SHOP_VENDEURS":
        st.header("👥 COMPTES VENDEURS")
        with st.form("form_vendeur"):
            v_user = st.text_input("Identifiant du Vendeur").lower().strip()
            v_pass = st.text_input("Mot de passe Vendeur", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
                       (v_user, hash_pass(v_pass), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.success(f"Compte vendeur {v_user} créé avec succès !")
                st.rerun()
        
        st.divider()
        st.write("### Vos Vendeurs Actifs")
        vend_list = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True)
        for v_u, v_s in vend_list:
            st.write(f"🔹 **{v_u.upper()}** | Statut : {v_s}")

    # --- PAGE PARAMÈTRES BOUTIQUE ---
    elif st.session_state.page == "SHOP_PARAMS":
        st.header("⚙️ RÉGLAGES DE LA BOUTIQUE")
        # Récupérer les données actuelles
        e_inf = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        with st.form("params_boutique"):
            st.write("### Informations de la Facture")
            p_nom = st.text_input("Nom de l'Enseigne (Facture)", e_inf[0])
            p_head = st.text_input("En-tête personnalisé (Slogan)", e_inf[4])
            p_adr = st.text_input("Adresse Physique", e_inf[1])
            p_tel = st.text_input("Téléphone Contact", e_inf[2])
            p_rccm = st.text_input("RCCM / ID National", e_inf[3])
            
            st.divider()
            st.write("### Sécurité")
            p_pass = st.text_input("Changer mon mot de passe (Boss)", type="password")
            
            if st.form_submit_button("ENREGISTRER LES MODIFICATIONS"):
                # Mise à jour des informations
                run_db("""UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=?, header_custom=? 
                       WHERE ent_id=?""", (p_nom.upper(), p_adr, p_tel, p_rccm, p_head, st.session_state.ent_id))
                
                # Mise à jour du mot de passe si rempli
                if p_pass:
                    run_db("UPDATE users SET password=? WHERE username=?", (hash_pass(p_pass), st.session_state.user))
                
                st.success("✅ Modifications enregistrées !")
                time.sleep(1); st.rerun()
        
        st.divider()
        if st.button("🔴 RÉINITIALISER TOUTE LA BOUTIQUE (DANGEREUX)"):
            run_db("DELETE FROM ventes WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM dettes WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM produits WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM depenses WHERE ent_id=?", (st.session_state.ent_id,))
            st.warning("Toutes vos données de vente et de stock ont été effacées.")
            time.sleep(2); st.rerun()

# FIN DU CODE v2035
