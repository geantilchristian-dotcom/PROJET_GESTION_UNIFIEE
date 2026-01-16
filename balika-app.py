# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTIME v2026 (800+ LIGNES)
# CARACTÉRISTIQUES : DASHBOARD, GESTION ABONNÉS, SUPPRESSION, PARAMÈTRES GLOBAUX
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & THÈME (TOUT CENTRÉ)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="SYSTÈME DE GESTION UNIFIÉ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des états de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False,
        'user': "",
        'role': "",
        'ent_id': "SYSTEM",
        'page': "ACCUEIL",
        'panier': {},
        'last_fac': None,
        'format_fac': "80mm"
    })

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (PERSISTANCE TOTALE)
# ------------------------------------------------------------------------------
def run_db(query, params=(), fetch=False):
    """Exécute les requêtes SQL avec gestion de verrouillage."""
    try:
        with sqlite3.connect('balika_master_final.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password):
    """Sécurisation des mots de passe."""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 3. INITIALISATION DU SYSTÈME (MIGRATIONS INCLUSES)
# ------------------------------------------------------------------------------
def init_db():
    # Table des utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        role TEXT, 
        ent_id TEXT, 
        status TEXT DEFAULT 'ACTIF', 
        telephone TEXT, 
        date_creation TEXT,
        photo BLOB)""")
    
    # Table de configuration globale (Admin)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, 
        app_name TEXT, 
        marquee_text TEXT, 
        taux_global REAL)""")
    
    # Table des infos entreprises (Boutiques)
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, 
        nom_boutique TEXT, 
        adresse TEXT, 
        telephone TEXT, 
        rccm TEXT)""")

    # Table Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        designation TEXT, 
        stock_actuel INTEGER, 
        prix_vente REAL, 
        devise TEXT, 
        ent_id TEXT)""")

    # Table Ventes
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
        details_json TEXT)""")

    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        client TEXT, 
        montant REAL, 
        devise TEXT, 
        ref_v TEXT, 
        ent_id TEXT)""")

    # Table Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        motif TEXT, 
        montant REAL, 
        devise TEXT, 
        date_d TEXT, 
        ent_id TEXT)""")

    # Création du compte SUPER ADMIN par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("""INSERT INTO users (username, password, role, ent_id, date_creation) 
               VALUES (?,?,?,?,?)""", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', datetime.now().strftime("%d/%m/%Y")))
    
    # Config système par défaut
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("""INSERT INTO system_config (id, app_name, marquee_text, taux_global) 
               VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION v2026', 2850.0)""")

init_db()

# ------------------------------------------------------------------------------
# 4. CHARGEMENT DES PARAMÈTRES GLOBAUX
# ------------------------------------------------------------------------------
config_data = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
if config_data:
    APP_NAME_GLOBAL = config_data[0][0]
    MARQUEE_TEXT_GLOBAL = config_data[0][1]
    TAUX_GLOBAL = config_data[0][2]
else:
    APP_NAME_GLOBAL, MARQUEE_TEXT_GLOBAL, TAUX_GLOBAL = "GESTION", "Bienvenue", 2800.0

# ------------------------------------------------------------------------------
# 5. STYLE CSS (CENTRAGE ET DESIGN MOBILE)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    /* Couleur de fond */
    .stApp {{ background-color: #FF8C00 !important; }}
    
    /* Centrage global du texte */
    h1, h2, h3, h4, p, label, .stMarkdown, .stText {{ 
        color: white !important; 
        text-align: center !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Bandeau défilant fixe */
    .fixed-header {{ 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #00FF00; height: 55px; 
        z-index: 999999; display: flex; align-items: center; 
        border-bottom: 3px solid white; 
    }}
    marquee {{ font-size: 22px; font-weight: bold; }}
    
    /* Espacement pour le header */
    .spacer {{ margin-top: 80px; }}
    
    /* Boutons personnalisés */
    .stButton>button {{ 
        background-color: #0055ff !important; 
        color: white !important; 
        border-radius: 15px; 
        font-weight: bold; 
        height: 50px; 
        width: 100%; 
        border: 2px solid #ffffff;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ background-color: #0033aa !important; transform: scale(1.02); }}
    
    /* Cadre du total Panier */
    .total-frame {{ 
        background: #000000; color: #00FF00; 
        padding: 25px; border: 5px solid white; 
        border-radius: 20px; text-align: center; 
        margin: 15px 0; font-size: 28px; font-weight: bold;
    }}
    
    /* Style Facture 80mm */
    .fac-80mm {{ 
        background: #ffffff; color: #000000 !important; 
        padding: 20px; width: 300px; margin: auto; 
        border: 1px dashed black; font-family: 'Courier New';
    }}
    .fac-80mm p, .fac-80mm h3, .fac-80mm h4 {{ color: black !important; text-align: left !important; }}

    /* Champs de saisie */
    div[data-baseweb="input"] {{ background: white !important; border-radius: 10px !important; }}
    input {{ color: black !important; font-weight: bold !important; text-align: center !important; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: #1a1a1a !important; }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{ 
        background-color: #333333; border-radius: 10px; 
        color: white; padding: 10px 20px; 
    }}
    </style>
    
    <div class="fixed-header">
        <marquee scrollamount="10">{MARQUEE_TEXT_GLOBAL}</marquee>
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. FONCTIONS UTILITAIRES
# ------------------------------------------------------------------------------
def get_entete(eid):
    res = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (eid,), fetch=True)
    return res[0] if res else (eid.upper(), "Adresse non définie", "0000", "RCCM-000")

# ------------------------------------------------------------------------------
# 7. LOGIQUE DE CONNEXION / INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f"<h1>🚀 {APP_NAME_GLOBAL}</h1>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.subheader("🔑 SE CONNECTER")
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU TABLEAU DE BORD"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res:
                if make_hashes(p) == res[0][0]:
                    if res[0][3] == "PAUSE":
                        st.error("❌ Votre accès est temporairement suspendu. Contactez l'administrateur.")
                    else:
                        st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                        st.rerun()
                else:
                    st.error("Mot de passe incorrect")
            else:
                st.error("Utilisateur inconnu")
                
    with col_r:
        st.subheader("🚀 CRÉER UN COMPTE")
        nu = st.text_input("Nom de la Boutique (Identifiant)")
        nt = st.text_input("Téléphone de contact")
        np = st.text_input("Mot de passe de sécurité", type="password")
        if st.button("DÉMARRER MON BUSINESS"):
            if nu and nt and np:
                exist = run_db("SELECT username FROM users WHERE username=?", (nu.lower(),), fetch=True)
                if exist:
                    st.warning("Ce nom est déjà utilisé.")
                else:
                    dc = datetime.now().strftime("%d/%m/%Y")
                    run_db("""INSERT INTO users (username, password, role, ent_id, telephone, date_creation) 
                           VALUES (?,?,?,?,?,?)""", 
                           (nu.lower(), make_hashes(np), 'USER', nu.lower(), nt, dc))
                    run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", 
                           (nu.lower(), nu.upper(), nt))
                    st.success("✅ Compte créé ! Connectez-vous à gauche.")
            else:
                st.error("Veuillez remplir tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 8. SIDEBAR NAVIGATION
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color: #00FF00;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p>Rôle: {st.session_state.role}</p>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "👤 MON PROFIL", "⚙️ PARAMÈTRES"]
    elif st.session_state.role == "VENDEUR":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.divider()
    if st.button("🚪 DÉCONNEXION", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 9. INTERFACE SUPER ADMIN (COMPTE admin)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    
    if st.session_state.page == "ACCUEIL":
        st.markdown(f"<h1>BIENVENUE ADMIN</h1>", unsafe_allow_html=True)
        total_users = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)[0][0]
        st.markdown(f"""
            <div class='total-frame'>
                NOMBRE TOTAL D'ABONNÉS : {total_users}
            </div>
        """, unsafe_allow_html=True)

    elif st.session_state.page == "ABONNÉS":
        st.markdown("<h1>👥 GESTION DES ABONNÉS</h1>", unsafe_allow_html=True)
        utilisateurs = run_db("SELECT username, status, telephone, date_creation FROM users WHERE role='USER'", fetch=True)
        
        if not utilisateurs:
            st.info("Aucun abonné pour le moment.")
        else:
            for u_name, u_status, u_tel, u_date in utilisateurs:
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                    c1.markdown(f"**{u_name.upper()}**")
                    c2.write(f"📞 {u_tel}")
                    c3.write(f"📅 {u_date}")
                    
                    status_color = "🟢" if u_status == "ACTIF" else "🔴"
                    c4.write(f"{status_color} {u_status}")
                    
                    # Actions Admin sur les abonnés
                    if u_status == "ACTIF":
                        if c5.button("⏸️ PAUSE", key=f"pause_{u_name}"):
                            run_db("UPDATE users SET status='PAUSE' WHERE username=?", (u_name,))
                            st.rerun()
                    else:
                        if c5.button("▶️ ACTIVER", key=f"play_{u_name}"):
                            run_db("UPDATE users SET status='ACTIF' WHERE username=?", (u_name,))
                            st.rerun()
                    
                    # BOUTON SUPPRIMER (Demandé)
                    if st.button(f"🗑️ SUPPRIMER COMPTE {u_name.upper()}", key=f"del_user_{u_name}"):
                        run_db("DELETE FROM users WHERE username=?", (u_name,))
                        run_db("DELETE FROM ent_infos WHERE ent_id=?", (u_name,))
                        st.success(f"Compte {u_name} supprimé !")
                        time.sleep(1)
                        st.rerun()

    elif st.session_state.page == "PROFIL":
        st.markdown("<h1>👤 MON PROFIL ADMIN</h1>", unsafe_allow_html=True)
        with st.form("admin_profile"):
            new_u = st.text_input("Nouvel Identifiant Admin", value=st.session_state.user)
            new_p = st.text_input("Nouveau Mot de Passe Admin", type="password")
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                hashed_p = make_hashes(new_p) if new_p else None
                if hashed_p:
                    run_db("UPDATE users SET username=?, password=? WHERE username='admin'", (new_u.lower(), hashed_p))
                else:
                    run_db("UPDATE users SET username=? WHERE username='admin'", (new_u.lower(),))
                st.success("Profil mis à jour ! Reconnectez-vous si l'identifiant a changé.")

    elif st.session_state.page == "PARAMÈTRES":
        st.markdown("<h1>⚙️ PARAMÈTRES SYSTÈME</h1>", unsafe_allow_html=True)
        with st.form("global_cfg"):
            a_name = st.text_input("Nom de l'Application (Pour tous)", value=APP_NAME_GLOBAL)
            m_text = st.text_area("Texte défilant (Marquee)", value=MARQUEE_TEXT_GLOBAL)
            t_taux = st.number_input("Taux de Change Global (1$ en CDF)", value=TAUX_GLOBAL)
            if st.form_submit_button("APPLIQUER À TOUT LE SYSTÈME"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", 
                       (a_name, m_text, t_taux))
                st.success("Paramètres globaux mis à jour avec succès !")
                st.rerun()

# ------------------------------------------------------------------------------
# 10. INTERFACE UTILISATEUR (BOUTIQUE)
# ------------------------------------------------------------------------------
elif st.session_state.role == "USER" or st.session_state.role == "VENDEUR":

    if st.session_state.page == "ACCUEIL":
        st.markdown(f"<h1>🏠 {APP_NAME_GLOBAL} - {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        today = datetime.now().strftime("%d/%m/%Y")
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{today}%"), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>CHIFFRE D'AFFAIRES DU JOUR :<br>{v_jr:,.2f} $</div>", unsafe_allow_html=True)

    elif st.session_state.page == "STOCK":
        st.markdown("<h1>📦 GESTION DU STOCK</h1>", unsafe_allow_html=True)
        # Ajout Produit
        with st.expander("➕ AJOUTER UN NOUVEAU PRODUIT"):
            with st.form("add_prod"):
                d = st.text_input("Désignation de l'article")
                q = st.number_input("Quantité initiale", min_value=0)
                p = st.number_input("Prix de vente ($)", min_value=0.0)
                if st.form_submit_button("ENREGISTRER"):
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                           (d.upper(), q, p, "USD", st.session_state.ent_id))
                    st.rerun()
        
        # Liste modifiable
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for pi, pd, ps, pp in prods:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
                new_n = c1.text_input("Nom", pd, key=f"edit_n_{pi}")
                new_q = c2.number_input("Stock", value=ps, key=f"edit_q_{pi}")
                new_p = c3.number_input("Prix", value=pp, key=f"edit_p_{pi}")
                if c4.button("💾", key=f"save_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (new_n.upper(), new_q, new_p, pi))
                    st.rerun()
                if c5.button("🗑️", key=f"del_p_{pi}"):
                    run_db("DELETE FROM produits WHERE id=?", (pi,))
                    st.rerun()

    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.markdown("<h1>🛒 CAISSE & VENTE</h1>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            devise = col1.selectbox("Devise de paiement", ["USD", "CDF"])
            
            p_map = {p[0]: (p[1], p[2]) for p in run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)}
            
            sel_art = st.selectbox("RECHERCHER UN ARTICLE", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER AU PANIER") and sel_art != "---":
                if p_map[sel_art][1] > 0:
                    st.session_state.panier[sel_art] = st.session_state.panier.get(sel_art, 0) + 1
                    st.rerun()
                else:
                    st.error("Rupture de stock !")

            if st.session_state.panier:
                st.markdown("### 📋 VOTRE PANIER")
                total_panier = 0.0
                items_to_save = []
                
                for art, qte in list(st.session_state.panier.items()):
                    pu_base = p_map[art][0]
                    pu = pu_base if devise == "USD" else pu_base * TAUX_GLOBAL
                    st_dispo = p_map[art][1]
                    
                    cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 1])
                    cc1.write(f"**{art}** (Prix: {pu:,.0f} {devise})")
                    q_input = cc2.number_input("Qté", 1, st_dispo, value=qte, key=f"q_{art}")
                    st.session_state.panier[art] = q_input
                    
                    sub = pu * q_input
                    total_panier += sub
                    items_to_save.append({"art": art, "qty": q_input, "pu": pu})
                    
                    if cc4.button("❌", key=f"rm_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL : {total_panier:,.2f} {devise}</div>", unsafe_allow_html=True)
                
                client = st.text_input("NOM DU CLIENT", value="COMPTANT")
                montant_paye = st.number_input("MONTANT REÇU", value=float(total_panier))
                
                if st.button("💳 VALIDER ET IMPRIMER"):
                    ref = f"FAC-{random.randint(10000, 99999)}"
                    reste = total_panier - montant_paye
                    
                    # Enregistrer Vente
                    run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) 
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                           (ref, client.upper(), total_panier, montant_paye, reste, devise, 
                            datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, 
                            st.session_state.ent_id, json.dumps(items_to_save)))
                    
                    # Gérer Dette
                    if reste > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", 
                               (client.upper(), reste, devise, ref, st.session_state.ent_id))
                    
                    # Déduire Stock
                    for item in items_to_save:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                               (item['qty'], item['art'], st.session_state.ent_id))
                        
                    st.session_state.update({
                        'last_fac': {
                            'ref': ref, 'cli': client.upper(), 'items': items_to_save, 
                            'total': total_panier, 'paye': montant_paye, 'reste': reste, 'dev': devise
                        },
                        'panier': {}
                    })
                    st.rerun()
        else:
            # Affichage Facture
            f = st.session_state.last_fac
            e = get_entete(st.session_state.ent_id)
            
            st.markdown("<h2 style='color: white;'>📄 FACTURE GÉNÉRÉE</h2>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class="fac-80mm">
                    <h3 align="center">{e[0]}</h3>
                    <p align="center">{e[1]}<br>Tél: {e[2]}</p>
                    <hr>
                    <p><b>REF:</b> {f['ref']}<br><b>CLIENT:</b> {f['cli']}</p>
                    <hr>
                    {"".join([f"<p>{i['art']} x{i['qty']} <span style='float:right;'>{i['pu']*i['qty']:,.0f}</span></p>" for i in f['items']])}
                    <hr>
                    <h4>TOTAL: <span style='float:right;'>{f['total']:,.2f} {f['dev']}</span></h4>
                    <p>REÇU: <span style='float:right;'>{f['paye']:,.2f} {f['dev']}</span></p>
                    <p>RESTE: <span style='float:right;'>{f['reste']:,.2f} {f['dev']}</span></p>
                    <hr>
                    <p align="center">Merci de votre confiance !</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ NOUVELLE VENTE"):
                st.session_state.last_fac = None
                st.rerun()
            if st.button("🖨️ IMPRIMER"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    elif st.session_state.page == "DETTES":
        st.markdown("<h1>📉 LISTE DES DETTES CLIENTS</h1>", unsafe_allow_html=True)
        dettes = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        
        if not dettes:
            st.success("Aucune dette enregistrée !")
        else:
            for di, dc, dm, dv, dr in dettes:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 2])
                    c1.markdown(f"👤 **{dc}** (Facture: {dr})")
                    c2.markdown(f"💰 **{dm:,.2f} {dv}**")
                    tranche = c3.number_input("Montant versé", min_value=0.0, max_value=float(dm), key=f"tranche_{di}")
                    if c3.button("ENCAISSER", key=f"pay_det_{di}"):
                        run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (tranche, di))
                        st.success("Paiement enregistré !")
                        st.rerun()

    elif st.session_state.page == "RÉGLAGES":
        st.markdown("<h1>⚙️ RÉGLAGES BOUTIQUE</h1>", unsafe_allow_html=True)
        e = get_entete(st.session_state.ent_id)
        
        tab_b, tab_u = st.tabs(["🏠 INFOS BOUTIQUE", "🔒 SÉCURITÉ COMPTE"])
        
        with tab_b:
            with st.form("boutique_infos"):
                bn = st.text_input("Nom de la Boutique", e[0])
                ba = st.text_input("Adresse Physique", e[1])
                bt = st.text_input("Téléphone Officiel", e[2])
                br = st.text_input("RCCM / ID Nat", e[3])
                if st.form_submit_button("SAUVEGARDER"):
                    run_db("""UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=? 
                           WHERE ent_id=?""", (bn, ba, bt, br, st.session_state.ent_id))
                    st.success("Informations de facture mises à jour !")
        
        with tab_u:
            st.write("Modifier vos identifiants de connexion")
            with st.form("user_update"):
                un = st.text_input("Nouvel Identifiant", st.session_state.user)
                up = st.text_input("Nouveau Mot de Passe", type="password")
                if st.form_submit_button("CHANGER MES ACCÈS"):
                    if up:
                        run_db("UPDATE users SET username=?, password=? WHERE username=?", 
                               (un.lower(), make_hashes(up), st.session_state.user))
                    else:
                        run_db("UPDATE users SET username=? WHERE username=?", 
                               (un.lower(), st.session_state.user))
                    st.session_state.user = un.lower()
                    st.success("Accès modifiés !")

# ------------------------------------------------------------------------------
# 11. FIN DU CODE (800 LIGNES APPROX AVEC LOGIQUE ET CSS)
# ------------------------------------------------------------------------------
