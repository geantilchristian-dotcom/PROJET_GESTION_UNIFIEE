# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTIME EXPANSION v2028 (CODE LONG ET DÉTAILLÉ)
# AUCUNE LIGNE SUPPRIMÉE - INTÉGRATION TOTALE DES NOUVELLES EXIGENCES
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
# 1. CONFIGURATION DE LA PAGE & THÈME VISUEL (DESIGN CENTRÉ)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2028 - SYSTÈME UNIFIÉ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation exhaustive des états de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False,
        'user': "",
        'role': "",
        'ent_id': "SYSTEM",
        'page': "ACCUEIL",
        'panier': {},
        'last_fac': None,
        'format_fac': "80mm",
        'show_register': False,
        'devise_vente': "USD"
    })

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (RÉSILIENCE ET SÉCURITÉ)
# ------------------------------------------------------------------------------
def run_db(query, params=(), fetch=False):
    """Exécute les requêtes avec gestion de timeout pour éviter les blocages SQLite."""
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
    """Hachage SHA-256 pour la sécurité des mots de passe."""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 3. ARCHITECTURE DES TABLES ET MIGRATIONS (VERSION ÉTENDUE)
# ------------------------------------------------------------------------------
def init_db():
    # Table Utilisateurs enrichie (Nom, Prénom, Adresse...)
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        role TEXT, 
        ent_id TEXT, 
        status TEXT DEFAULT 'ACTIF', 
        telephone TEXT, 
        date_creation TEXT,
        nom TEXT, 
        prenom TEXT, 
        adresse_physique TEXT, 
        photo BLOB)""")
    
    # Table Configuration Système (Admin Global)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, 
        app_name TEXT, 
        marquee_text TEXT, 
        taux_global REAL)""")
    
    # Table Entreprises
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, 
        nom_boutique TEXT, 
        adresse TEXT, 
        telephone TEXT, 
        rccm TEXT)""")

    # Table Produits (Inventaire)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        designation TEXT, 
        stock_actuel INTEGER, 
        prix_vente REAL, 
        devise TEXT, 
        ent_id TEXT)""")

    # Table Ventes (Historique complet)
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

    # Table Dépenses (Mise à jour pour les rapports)
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        motif TEXT, 
        montant REAL, 
        devise TEXT, 
        date_d TEXT, 
        ent_id TEXT)""")

    # Compte SUPER ADMIN (Garanti)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("""INSERT INTO users (username, password, role, ent_id, date_creation) 
               VALUES (?,?,?,?,?)""", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', datetime.now().strftime("%d/%m/%Y")))
    
    # Configuration par défaut
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("""INSERT INTO system_config (id, app_name, marquee_text, taux_global) 
               VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION v2028', 2850.0)""")

init_db()

# ------------------------------------------------------------------------------
# 4. RÉCUPÉRATION DES PARAMÈTRES DYNAMIQUES
# ------------------------------------------------------------------------------
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
if cfg:
    APP_NAME_GLOBAL, MARQUEE_TEXT_GLOBAL, TX_G = cfg[0]
else:
    APP_NAME_GLOBAL, MARQUEE_TEXT_GLOBAL, TX_G = "BALIKA ERP", "Bienvenue", 2850.0

# ------------------------------------------------------------------------------
# 5. STYLE CSS AVANCÉ (80MM, A4, MOBILE, CENTRAGE)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    /* Fond principal orange */
    .stApp {{ background-color: #FF8C00 !important; }}
    
    /* Centrage de tous les textes et éléments */
    h1, h2, h3, h4, p, label, .stMarkdown, .stText {{ 
        color: white !important; 
        text-align: center !important; 
    }}
    
    /* Header défilant noir fixe */
    .fixed-header {{ 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #00FF00; height: 60px; 
        z-index: 999999; display: flex; align-items: center; 
        border-bottom: 3px solid #ffffff; 
    }}
    marquee {{ font-size: 24px; font-weight: bold; font-family: 'Courier New'; }}
    
    .spacer {{ margin-top: 90px; }}
    
    /* Boutons stylisés */
    .stButton>button {{ 
        background-color: #0055ff !important; 
        color: white !important; 
        border-radius: 12px; 
        font-weight: bold; 
        height: 50px; 
        width: 100%; 
        border: 2px solid #ffffff;
    }}
    
    /* Frame de Total Panier */
    .total-frame {{ 
        background: #000000; color: #00FF00; 
        padding: 30px; border: 4px solid #ffffff; 
        border-radius: 20px; text-align: center; 
        margin: 20px 0; font-size: 32px; 
    }}
    
    /* FACTURE 80mm */
    .fac-80mm {{ 
        background: #ffffff; color: #000000 !important; 
        padding: 15px; width: 300px; margin: auto; 
        border: 1px dashed black; font-family: 'Courier New';
    }}
    .fac-80mm p, .fac-80mm h3, .fac-80mm h4 {{ color: #000000 !important; text-align: left !important; }}
    
    /* FACTURE A4 */
    .fac-a4 {{ 
        background: #ffffff; color: #000000 !important; 
        padding: 40px; width: 90%; max-width: 850px; 
        margin: auto; border: 1px solid #000; min-height: 800px;
    }}
    .fac-a4 * {{ color: #000000 !important; }}
    .fac-a4 table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
    .fac-a4 th, .fac-a4 td {{ border: 1px solid #000; padding: 12px; text-align: left; }}

    /* Inputs blancs avec texte noir */
    div[data-baseweb="input"], div[data-baseweb="select"] {{ 
        background-color: white !important; 
        border-radius: 10px !important; 
    }}
    input {{ color: black !important; font-weight: bold !important; text-align: center !important; }}
    
    /* Responsive phone */
    @media (max-width: 600px) {{
        .fac-a4 {{ width: 100%; padding: 10px; }}
        .total-frame {{ font-size: 22px; }}
    }}
    </style>
    
    <div class="fixed-header">
        <marquee scrollamount="10">{MARQUEE_TEXT_GLOBAL}</marquee>
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. FONCTIONS UTILES (ENTÊTE, CALCULS)
# ------------------------------------------------------------------------------
def get_entete(eid):
    res = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (eid,), fetch=True)
    return res[0] if res else (eid.upper(), "Non spécifiée", "0000", "Non spécifié")

# ------------------------------------------------------------------------------
# 7. INTERFACE DE CONNEXION ET INSCRIPTION (CACHÉE)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f"<h1>🏢 {APP_NAME_GLOBAL}</h1>", unsafe_allow_html=True)
    
    if not st.session_state.show_register:
        # Formulaire de Login
        with st.container():
            st.markdown("### CONNEXION")
            login_u = st.text_input("Identifiant (Username)").lower().strip()
            login_p = st.text_input("Mot de passe", type="password")
            
            if st.button("ACCÉDER AU SYSTÈME"):
                res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (login_u,), fetch=True)
                if res and make_hashes(login_p) == res[0][0]:
                    if res[0][3] == "PAUSE":
                        st.error("❌ Ce compte est suspendu. Veuillez contacter l'administrateur.")
                    else:
                        st.session_state.update({'auth':True, 'user':login_u, 'role':res[0][1], 'ent_id':res[0][2]})
                        st.rerun()
                else:
                    st.error("🚫 Identifiant ou mot de passe incorrect.")
            
            st.write("---")
            if st.button("🆕 CRÉER UN COMPTE BOUTIQUE"):
                st.session_state.show_register = True
                st.rerun()
    else:
        # Formulaire d'inscription complet
        st.markdown("### 📝 INSCRIPTION NOUVELLE BOUTIQUE")
        with st.container():
            col1, col2 = st.columns(2)
            reg_nom = col1.text_input("Nom du Propriétaire")
            reg_prenom = col2.text_input("Prénom du Propriétaire")
            reg_ent = st.text_input("Nom de l'Entreprise / Boutique")
            reg_tel = st.text_input("Téléphone de contact")
            reg_adr = st.text_area("Adresse de la Boutique")
            
            col3, col4 = st.columns(2)
            reg_pw1 = col3.text_input("Créer un Mot de passe (6 car. min)", type="password")
            reg_pw2 = col4.text_input("Confirmer le Mot de passe", type="password")
            
            if st.button("VALIDER L'INSCRIPTION"):
                if len(reg_pw1) < 6:
                    st.error("⚠️ Le mot de passe doit comporter au moins 6 caractères.")
                elif reg_pw1 != reg_pw2:
                    st.error("⚠️ Les mots de passe ne correspondent pas.")
                elif not reg_ent or not reg_nom:
                    st.error("⚠️ Veuillez remplir au moins le nom de l'entreprise et du propriétaire.")
                else:
                    # Création de l'ID utilisateur unique
                    u_id = reg_ent.lower().replace(" ", "_") + str(random.randint(10,99))
                    # Insertion Utilisateur
                    run_db("""INSERT INTO users (username, password, role, ent_id, telephone, date_creation, nom, prenom, adresse_physique) 
                           VALUES (?,?,?,?,?,?,?,?,?)""", 
                           (u_id, make_hashes(reg_pw1), 'USER', u_id, reg_tel, datetime.now().strftime("%d/%m/%Y"), reg_nom, reg_prenom, reg_adr))
                    # Insertion Infos Entreprise
                    run_db("INSERT INTO ent_infos (ent_id, nom_boutique, adresse, telephone) VALUES (?,?,?,?)", 
                           (u_id, reg_ent.upper(), reg_adr, reg_tel))
                    
                    st.success(f"✅ Compte créé ! Votre identifiant de connexion est : {u_id}")
                    st.info("Utilisez cet identifiant pour vous connecter maintenant.")
                    time.sleep(4)
                    st.session_state.show_register = False
                    st.rerun()
            
            if st.button("🔙 RETOUR AU LOGIN"):
                st.session_state.show_register = False
                st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. NAVIGATION SIDEBAR (MENUS COMPLETS)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color: #00FF00;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"**Rôle : {st.session_state.role}**")
    st.divider()
    
    if st.session_state.role == "SUPER_ADMIN":
        menu_items = {
            "🏠 ACCUEIL": "ACCUEIL",
            "👥 MES ABONNÉS": "ABONNES",
            "👤 MON PROFIL": "PROFIL",
            "⚙️ PARAMÈTRES": "PARAMETRES"
        }
    elif st.session_state.role == "VENDEUR":
        menu_items = {
            "🏠 ACCUEIL": "ACCUEIL",
            "🛒 CAISSE": "CAISSE",
            "📉 MES DETTES": "DETTES"
        }
    else: # USER (Propriétaire)
        menu_items = {
            "🏠 ACCUEIL": "ACCUEIL",
            "📦 GESTION STOCK": "STOCK",
            "🛒 CAISSE": "CAISSE",
            "📊 RAPPORTS": "RAPPORTS",
            "📉 DETTES": "DETTES",
            "💸 DÉPENSES": "DEPENSES",
            "👥 VENDEURS": "VENDEURS",
            "⚙️ RÉGLAGES": "REGLAGES"
        }
    
    for label, target in menu_items.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = target
            st.rerun()
            
    st.divider()
    if st.button("🚪 DÉCONNEXION", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 9. LOGIQUE SUPER ADMIN (IDENTIFIANT : admin)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    
    if st.session_state.page == "ACCUEIL":
        st.markdown("<h1>🌟 DASHBOARD ADMIN</h1>", unsafe_allow_html=True)
        stats = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)
        nb_users = stats[0][0] if stats else 0
        st.markdown(f"<div class='total-frame'>TOTAL DES ENTREPRISES INSCRITES : {nb_users}</div>", unsafe_allow_html=True)
        
        # Liste rapide des activités
        st.subheader("Inscriptions Récentes")
        recents = run_db("SELECT username, date_creation, telephone FROM users WHERE role='USER' ORDER BY date_creation DESC LIMIT 5", fetch=True)
        st.table(pd.DataFrame(recents, columns=["Identifiant", "Date", "Contact"]))

    elif st.session_state.page == "ABONNES":
        st.markdown("<h1>👥 GESTION DES ABONNÉS</h1>", unsafe_allow_html=True)
        users_list = run_db("SELECT username, status, telephone, date_creation, nom, prenom FROM users WHERE role='USER'", fetch=True)
        
        for u_id, u_stat, u_tel, u_date, u_nom, u_pre in users_list:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.markdown(f"**{u_nom} {u_pre}** ({u_id.upper()})<br>📅 Inscrit le : {u_date}", unsafe_allow_html=True)
                c2.write(f"📞 {u_tel}")
                
                # Action Pause/Play
                color = "🟢" if u_stat == "ACTIF" else "🔴"
                if c3.button(f"{color} {u_stat}", key=f"stat_{u_id}"):
                    new_s = "PAUSE" if u_stat == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (new_s, u_id))
                    st.rerun()
                
                # ACTION SUPPRIMER (DEMANDÉ)
                if c4.button("🗑️ SUPPRIMER", key=f"del_{u_id}"):
                    run_db("DELETE FROM users WHERE username=?", (u_id,))
                    run_db("DELETE FROM ent_infos WHERE ent_id=?", (u_id,))
                    st.warning(f"Compte {u_id} supprimé.")
                    time.sleep(1)
                    st.rerun()

    elif st.session_state.page == "PROFIL":
        st.markdown("<h1>👤 MON PROFIL ADMIN</h1>", unsafe_allow_html=True)
        with st.form("admin_edit"):
            new_admin_u = st.text_input("Changer Identifiant Admin", value=st.session_state.user)
            new_admin_p = st.text_input("Changer Mot de passe Admin", type="password", help="Laissez vide pour ne pas changer")
            if st.form_submit_button("MODIFIER MON PROFIL"):
                if new_admin_p:
                    run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_admin_u.lower(), make_hashes(new_admin_p), st.session_state.user))
                else:
                    run_db("UPDATE users SET username=? WHERE username=?", (new_admin_u.lower(), st.session_state.user))
                st.session_state.user = new_admin_u.lower()
                st.success("Profil admin mis à jour.")

    elif st.session_state.page == "PARAMETRES":
        st.markdown("<h1>⚙️ RÉGLAGES GLOBAUX DU SYSTÈME</h1>", unsafe_allow_html=True)
        with st.form("sys_config_form"):
            new_app_name = st.text_input("Nom de l'application (Pour tous)", value=APP_NAME_GLOBAL)
            new_marquee = st.text_area("Texte défilant (Marquee)", value=MARQUEE_TEXT_GLOBAL)
            new_taux = st.number_input("Taux de change Global (1$ = ? CDF)", value=TX_G)
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", 
                       (new_app_name, new_marquee, new_taux))
                st.success("Configuration mise à jour pour tous les utilisateurs.")
                st.rerun()

# ------------------------------------------------------------------------------
# 10. LOGIQUE UTILISATEUR (BOUTIQUE)
# ------------------------------------------------------------------------------
else:
    # --- PAGE ACCUEIL ---
    if st.session_state.page == "ACCUEIL":
        st.markdown(f"<h1>🏠 BIENVENUE CHEZ {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        today = datetime.now().strftime("%d/%m/%Y")
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{today}%"), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>VENTES DU JOUR :<br>{v_jr:,.2f} $</div>", unsafe_allow_html=True)
        
        # Petit tableau des alertes stock
        st.subheader("⚠️ Alertes Stock Bas")
        low_stock = run_db("SELECT designation, stock_actuel FROM produits WHERE ent_id=? AND stock_actuel < 5", (st.session_state.ent_id,), fetch=True)
        if low_stock:
            st.table(pd.DataFrame(low_stock, columns=["Article", "Quantité"]))
        else:
            st.success("Tout votre stock est suffisant.")

    # --- PAGE STOCK (MODIFIABLE MANUELLEMENT) ---
    elif st.session_state.page == "STOCK":
        st.markdown("<h1>📦 GESTION DES ARTICLES</h1>", unsafe_allow_html=True)
        
        with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
            with st.form("new_art_form"):
                d = st.text_input("Nom de l'article")
                q = st.number_input("Stock de départ", min_value=0)
                p = st.number_input("Prix de vente ($)", min_value=0.0)
                if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                           (d.upper(), q, p, "USD", st.session_state.ent_id))
                    st.rerun()

        st.subheader("Liste des articles en stock")
        mes_prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        
        for pi, pd, ps, pp in mes_prods:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
                u_n = c1.text_input("Nom", pd, key=f"n_{pi}")
                u_q = c2.number_input("Stock", value=ps, key=f"q_{pi}")
                u_p = c3.number_input("Prix $", value=pp, key=f"p_{pi}")
                if c4.button("💾", key=f"up_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_n.upper(), u_q, u_p, pi))
                    st.success("Mis à jour")
                    st.rerun()
                if c5.button("🗑️", key=f"del_p_{pi}"):
                    run_db("DELETE FROM produits WHERE id=?", (pi,))
                    st.rerun()

    # --- PAGE CAISSE (LE PANIER ET LES 2 FORMATS) ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.markdown("<h1>🛒 CAISSE & FACTURATION</h1>", unsafe_allow_html=True)
            
            # Choix devise et Format
            cf1, cf2 = st.columns(2)
            st.session_state.devise_vente = cf1.selectbox("Monnaie de paiement", ["USD", "CDF"])
            st.session_state.format_fac = cf2.selectbox("Type de Facture", ["80mm", "A4"])
            
            # Sélection Articles
            p_data = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in p_data}
            
            selection = st.selectbox("Choisir un article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER AU PANIER") and selection != "---":
                if p_map[selection][1] > 0:
                    st.session_state.panier[selection] = st.session_state.panier.get(selection, 0) + 1
                    st.rerun()
                else:
                    st.error("Rupture de stock pour cet article.")

            # Affichage du panier
            if st.session_state.panier:
                st.markdown("### 📋 PANIER ACTUEL")
                total_vente = 0.0
                save_list = []
                
                for art, qte in list(st.session_state.panier.items()):
                    p_unit = p_map[art][0]
                    if st.session_state.devise_vente == "CDF":
                        p_unit = p_unit * TX_G
                    
                    cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 1])
                    cc1.write(f"**{art}**")
                    new_qte = cc2.number_input("Qté", 1, p_map[art][1], value=qte, key=f"pan_{art}")
                    st.session_state.panier[art] = new_qte
                    
                    subtotal = p_unit * new_qte
                    total_vente += subtotal
                    save_list.append({"art": art, "qty": new_qte, "pu": p_unit})
                    
                    cc3.write(f"{subtotal:,.0f}")
                    if cc4.button("❌", key=f"rem_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL À PAYER : {total_vente:,.2f} {st.session_state.devise_vente}</div>", unsafe_allow_html=True)
                
                # Validation
                nom_client = st.text_input("NOM DU CLIENT", "COMPTANT")
                montant_recu = st.number_input("MONTANT REÇU", value=float(total_vente))
                
                if st.button("✅ VALIDER ET GÉNÉRER FACTURE"):
                    ref_fac = f"FAC-{random.randint(100000, 999999)}"
                    reste_a_payer = total_vente - montant_recu
                    
                    # Enregistrement Vente
                    run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) 
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                           (ref_fac, nom_client.upper(), total_vente, montant_recu, reste_a_payer, st.session_state.devise_vente,
                            datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(save_list)))
                    
                    # Enregistrement Dette si reste > 0
                    if reste_a_payer > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)",
                               (nom_client.upper(), reste_a_payer, st.session_state.devise_vente, ref_fac, st.session_state.ent_id))
                    
                    # Mise à jour Stock
                    for item in save_list:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                               (item['qty'], item['art'], st.session_state.ent_id))
                    
                    st.session_state.update({
                        'last_fac': {
                            'ref': ref_fac, 'cli': nom_client.upper(), 'total': total_vente, 
                            'paye': montant_recu, 'reste': reste_a_payer, 'dev': st.session_state.devise_vente,
                            'items': save_list
                        },
                        'panier': {}
                    })
                    st.rerun()
        else:
            # AFFICHAGE DE LA FACTURE (80mm vs A4)
            f = st.session_state.last_fac
            e = get_entete(st.session_state.ent_id)
            
            if st.session_state.format_fac == "80mm":
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
                    <p>PAYÉ: <span style='float:right;'>{f['paye']:,.2f}</span></p>
                    <p>RESTE: <span style='float:right;'>{f['reste']:,.2f}</span></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # FORMAT A4 PROFESSIONNEL
                st.markdown(f"""
                <div class="fac-a4">
                    <table style="border:none;"><tr>
                        <td style="border:none; width:50%;"><h2>{e[0]}</h2><p>{e[1]}<br>Tél: {e[2]}<br>RCCM: {e[3]}</p></td>
                        <td style="border:none; width:50%; text-align:right;"><h1>FACTURE</h1><p>Date: {datetime.now().strftime('%d/%m/%Y')}<br>Référence: {f['ref']}</p></td>
                    </tr></table>
                    <br><p><b>DOIT À :</b> {f['cli']}</p>
                    <table>
                        <thead><tr style="background:#eee;"><th>Désignation</th><th>Quantité</th><th>P.U</th><th>Total</th></tr></thead>
                        <tbody>
                            {"".join([f"<tr><td>{i['art']}</td><td>{i['qty']}</td><td>{i['pu']:,.2f}</td><td>{i['pu']*i['qty']:,.2f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <div style="text-align:right; margin-top:20px;">
                        <h3>TOTAL GÉNÉRAL : {f['total']:,.2f} {f['dev']}</h3>
                        <p>NET À PAYER : {f['total']:,.2f} {f['dev']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            c_f1, c_f2 = st.columns(2)
            if c_f1.button("⬅️ NOUVELLE VENTE"):
                st.session_state.last_fac = None
                st.rerun()
            if c_f2.button("🖨️ IMPRIMER FACTURE"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    # --- PAGE RAPPORTS (CORRECTS ET MIS À JOUR) ---
    elif st.session_state.page == "RAPPORTS":
        st.markdown("<h1>📊 RAPPORTS ET STATISTIQUES</h1>", unsafe_allow_html=True)
        
        # Données Ventes
        v_data = run_db("SELECT date_v, total, paye, reste FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        df_v = pd.DataFrame(v_data, columns=["Date", "Total", "Payé", "Reste"])
        
        # Données Dépenses
        d_data = run_db("SELECT date_d, montant, motif FROM depenses WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        df_d = pd.DataFrame(d_data, columns=["Date", "Montant", "Motif"])
        
        col_r1, col_r2, col_r3 = st.columns(3)
        t_v = df_v["Total"].sum() if not df_v.empty else 0
        t_d = df_d["Montant"].sum() if not df_d.empty else 0
        
        col_r1.metric("TOTAL VENTES", f"{t_v:,.2f} $")
        col_r2.metric("TOTAL DÉPENSES", f"{t_d:,.2f} $")
        col_r3.metric("RÉSULTAT NET", f"{(t_v - t_d):,.2f} $")
        
        st.divider()
        st.subheader("Historique des ventes")
        st.dataframe(df_v, use_container_width=True)
        
        st.subheader("Historique des dépenses")
        st.dataframe(df_d, use_container_width=True)

    # --- PAGE DÉPENSES (MISE À JOUR DES RAPPORTS) ---
    elif st.session_state.page == "DEPENSES":
        st.markdown("<h1>💸 GESTION DES DÉPENSES</h1>", unsafe_allow_html=True)
        with st.form("form_dep"):
            mot = st.text_input("Motif de la dépense")
            mon = st.number_input("Montant ($)", min_value=0.0)
            if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)",
                       (mot, mon, "USD", datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id))
                st.success("Dépense enregistrée. Le rapport est mis à jour.")
                st.rerun()

    # --- PAGE DETTES ---
    elif st.session_state.page == "DETTES":
        st.markdown("<h1>📉 SUIVI DES CRÉANCES</h1>", unsafe_allow_html=True)
        mes_dettes = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        
        if not mes_dettes:
            st.success("Toutes vos dettes sont apurées !")
        else:
            for di, dc, dm, dv, dr in mes_dettes:
                with st.container(border=True):
                    cl1, cl2, cl3 = st.columns([2, 1, 1])
                    cl1.write(f"👤 **{dc}**<br>Facture: {dr}", unsafe_allow_html=True)
                    cl2.write(f"💰 {dm:,.2f} {dv}")
                    p_tranche = cl3.number_input("Remboursement", 0.0, float(dm), key=f"tr_{di}")
                    if cl3.button("ENCAISSER", key=f"btn_d_{di}"):
                        run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (p_tranche, di))
                        st.success("Montant déduit.")
                        st.rerun()

    # --- PAGE VENDEURS ---
    elif st.session_state.page == "VENDEURS":
        st.markdown("<h1>👥 GESTION DE VOS VENDEURS</h1>", unsafe_allow_html=True)
        with st.form("new_vendeur"):
            v_u = st.text_input("Identifiant Vendeur").lower()
            v_p = st.text_input("Mot de passe Vendeur", type="password")
            if st.form_submit_button("AJOUTER LE VENDEUR"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
                       (v_u, make_hashes(v_p), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.success(f"Vendeur {v_u} ajouté.")
                st.rerun()
        
        st.subheader("Vos vendeurs actifs")
        list_v = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True)
        for v in list_v:
            st.write(f"🔹 {v[0]}")

    # --- PAGE RÉGLAGES ---
    elif st.session_state.page == "REGLAGES":
        st.markdown("<h1>⚙️ RÉGLAGES DE LA BOUTIQUE</h1>", unsafe_allow_html=True)
        e_info = get_entete(st.session_state.ent_id)
        
        with st.form("reg_bout_form"):
            st.subheader("Informations de Facturation")
            b_nom = st.text_input("Nom de l'Enseigne", e_info[0])
            b_adr = st.text_input("Adresse", e_info[1])
            b_tel = st.text_input("Téléphone", e_info[2])
            b_rcm = st.text_input("RCCM / ID Nat", e_info[3])
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=? WHERE ent_id=?", 
                       (b_nom, b_adr, b_tel, b_rcm, st.session_state.ent_id))
                st.success("Infos mises à jour.")
                st.rerun()
