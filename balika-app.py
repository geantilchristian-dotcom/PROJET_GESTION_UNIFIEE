import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v280 - ARCHITECTURE SaaS ROBUSTE)
# ==========================================
st.set_page_config(page_title="BALIKA CLOUD ERP", layout="wide", initial_sidebar_state="collapsed")

# Initialisation complète des états
states = {
    'auth': False, 'user': "", 'role': "", 'ent_id': "", 
    'page': "ACCUEIL", 'panier': {}, 'last_fac': None
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_cloud_master.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 2. INITIALISATION DES TABLES (ARCHITECTURE MULTI-TENANT)
# ==========================================
def init_db():
    # Table Utilisateurs : lie un humain à une entreprise et un rôle
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        role TEXT, 
        ent_id TEXT)""")
    
    # Table Stock : Chaque produit appartient à une ent_id
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        designation TEXT, 
        stock_actuel INTEGER, 
        prix_vente REAL, 
        devise TEXT, 
        ent_id TEXT)""")
    
    # Table Ventes : Historique complet
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
    
    # Table Dettes : Suivi des paiements échelonnés
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        client TEXT, 
        montant REAL, 
        devise TEXT, 
        ref_v TEXT, 
        ent_id TEXT)""")
    
    # Table Configuration Entreprise : Gère le nom, le taux ET le statut (ACTIF/PAUSE)
    run_db("""CREATE TABLE IF NOT EXISTS config (
        ent_id TEXT PRIMARY KEY, 
        nom_ent TEXT, 
        adresse TEXT, 
        tel TEXT, 
        taux REAL, 
        message TEXT, 
        status TEXT DEFAULT 'ACTIF',
        date_creation TEXT)""")

    # Création du Super-Admin (Vous) s'il n'existe pas
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM')", (make_hashes("admin123"),))
        run_db("INSERT INTO config VALUES ('SYSTEM', 'BALIKA CLOUD CONTROL', 'Cloud HQ', '000', 2850.0, 'Système de Contrôle Global', 'ACTIF', '2026-01-16')")

init_db()

# ==========================================
# 3. DESIGN & STYLE ANTI-BUG (FORCÉ BLANC)
# ==========================================
if st.session_state.auth:
    res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if res_cfg: C_NOM, C_MSG, C_TAUX, C_ADR, C_TEL = res_cfg[0]
    else: C_NOM, C_MSG, C_TAUX, C_ADR, C_TEL = "ERP", "Bienvenue", 2850.0, "---", "---"
else:
    C_NOM, C_MSG = "BALIKA CLOUD", "Bienvenue sur le portail de gestion unifiée"

st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #FFFFFF !important; color: #000 !important; }}
    .stButton>button {{ background: linear-gradient(135deg, #FF8C00, #FF4500) !important; color: white !important; border-radius: 10px; height: 55px; font-weight: bold; border: none; width: 100%; }}
    .total-frame {{ border: 3px solid #FF8C00; background: #FFF3E0; padding: 20px; border-radius: 12px; text-align: center; font-size: 26px; color: #E65100; font-weight: bold; margin: 10px 0; }}
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 12px 0; position: fixed; top: 0; z-index: 9999; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 18s linear infinite; font-size: 18px; font-weight: bold; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    [data-testid="stSidebar"] {{ background-color: #F8F9FA !important; border-right: 1px solid #EEE; }}
    .stTextInput>div>div>input {{ background-color: #F0F2F6 !important; color: #000 !important; border: 2px solid #FF8C00 !important; }}
    h1, h2, h3, label, p {{ color: #000 !important; }}
    @media print {{ .no-print {{ display: none !important; }} }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🚀 {C_NOM} : {C_MSG}</div></div>
    <div style="margin-top: 80px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. ÉCRAN D'ACCÈS (LOGIN ET INSCRIPTION SANS DUPLICATE ID)
# ==========================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:#FF8C00;'>{C_NOM}</h1>", unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["🔐 ACCÈS UTILISATEUR", "🏢 CRÉER UNE ENTREPRISE"])
    
    with tab_login:
        with st.form("form_login"):
            u_name = st.text_input("Identifiant Utilisateur", key="login_user").lower().strip()
            u_pass = st.text_input("Mot de passe", type="password", key="login_pass").strip()
            if st.form_submit_button("SE CONNECTER"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_name,), fetch=True)
                if res and make_hashes(u_pass) == res[0][0]:
                    # Vérifier si l'entreprise est active
                    status_res = run_db("SELECT status FROM config WHERE ent_id=?", (res[0][2],), fetch=True)
                    if status_res and status_res[0][0] == 'ACTIF' or res[0][1] == 'SUPER_ADMIN':
                        st.session_state.auth = True
                        st.session_state.user = u_name
                        st.session_state.role = res[0][1]
                        st.session_state.ent_id = res[0][2]
                        st.rerun()
                    else:
                        st.error("❌ Votre entreprise est suspendue. Contactez l'administrateur BALIKA.")
                else: st.error("Identifiants incorrects.")

    with tab_register:
        st.info("Devenez partenaire. Créez votre espace de gestion en 1 minute.")
        with st.form("form_reg"):
            reg_ent = st.text_input("Nom de l'Entreprise / Boutique", key="reg_ent_name").upper().strip()
            reg_user = st.text_input("Identifiant Administrateur (Privé)", key="reg_user_name").lower().strip()
            reg_pass = st.text_input("Mot de passe de sécurité", type="password", key="reg_pass_val").strip()
            if st.form_submit_button("ACTIVER MON ESPACE"):
                if reg_ent and reg_user and reg_pass:
                    if not run_db("SELECT * FROM users WHERE username=?", (reg_user,), fetch=True):
                        new_eid = f"ENT-{random.randint(10000, 99999)}"
                        today = datetime.now().strftime("%Y-%m-%d")
                        run_db("INSERT INTO users VALUES (?, ?, 'ADMIN', ?)", (reg_user, make_hashes(reg_pass), new_eid))
                        run_db("INSERT INTO config VALUES (?, ?, 'Adresse à compléter', '000', 2850.0, 'Bienvenue chez nous', 'ACTIF', ?)", (new_eid, reg_ent, today))
                        st.success("✅ Entreprise créée avec succès ! Connectez-vous sur l'onglet de gauche.")
                    else: st.error("Cet identifiant est déjà utilisé.")
                else: st.warning("Veuillez remplir tous les champs.")
    st.stop()

# ==========================================
# 5. MENU DE NAVIGATION
# ==========================================
USER = st.session_state.user
ROLE = st.session_state.role
ENT_ID = st.session_state.ent_id

with st.sidebar:
    st.markdown(f"### 🛡️ {USER.upper()}\n**Rôle : {ROLE}**")
    st.markdown(f"**🏢 {C_NOM}**")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 MES ABONNÉS", "📊 STATS GLOBALES"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "👥 MES VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: # VENDEUR
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
        
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION"):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 6. LOGIQUE : ESPACE SUPER-ADMIN (VOTRE ESPACE)
# ==========================================
if ROLE == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.title("🌍 Gestion des Entreprises Abonnées")
        clients = run_db("SELECT ent_id, nom_ent, status, date_creation, tel FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
        
        if clients:
            df_cl = pd.DataFrame(clients, columns=["ID Entreprise", "Nom", "Statut", "Inscrit le", "Téléphone"])
            st.dataframe(df_cl, use_container_width=True)
            
            st.write("---")
            st.subheader("🛠️ Contrôle des accès")
            target_id = st.selectbox("Choisir une entreprise à modifier", [c[0] for c in clients])
            target_info = [c for c in clients if c[0] == target_id][0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Entreprise : **{target_info[1]}**")
                st.write(f"Statut Actuel : **{target_info[2]}**")
            with col2:
                if target_info[2] == 'ACTIF':
                    if st.button("⏸️ METTRE EN PAUSE (BLOQUER)"):
                        run_db("UPDATE config SET status='PAUSE' WHERE ent_id=?", (target_id,))
                        st.rerun()
                else:
                    if st.button("▶️ RÉACTIVER LE COMPTE"):
                        run_db("UPDATE config SET status='ACTIF' WHERE ent_id=?", (target_id,))
                        st.rerun()
            
            if st.button("🗑️ SUPPRIMER DÉFINITIVEMENT"):
                if st.checkbox("Confirmer la suppression de toutes les données de cette entreprise ?"):
                    run_db("DELETE FROM config WHERE ent_id=?", (target_id,))
                    run_db("DELETE FROM users WHERE ent_id=?", (target_id,))
                    run_db("DELETE FROM produits WHERE ent_id=?", (target_id,))
                    st.success("Entreprise supprimée.")
                    st.rerun()
        else:
            st.info("Aucun abonné pour le moment.")

# ==========================================
# 7. LOGIQUE : ESPACE CLIENT (ADMIN & VENDEUR)
# ==========================================
else:
    if st.session_state.page == "ACCUEIL":
        st.title(f"Bienvenue, {USER.upper()}")
        st.write(f"Gestionnaire de l'entreprise : **{C_NOM}**")
        # Résumé rapide
        v_data = run_db("SELECT total, devise FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
        if v_data:
            df_v = pd.DataFrame(v_data, columns=["T", "D"])
            c1, c2 = st.columns(2)
            c1.metric("Ventes USD", f"{df_v[df_v['D']=='USD']['T'].sum():,.2f} $")
            c2.metric("Ventes CDF", f"{df_v[df_v['D']=='CDF']['T'].sum():,.0f} FC")

    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.title("🛒 Terminal de Vente")
            dev_v = st.radio("Devise de la transaction", ["USD", "CDF"], horizontal=True)
            
            # Produits filtrés par entreprise
            items = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
            i_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in items}
            
            choix = st.selectbox("Rechercher Article", ["---"] + list(i_map.keys()))
            if st.button("📥 AJOUTER AU PANIER") and choix != "---":
                st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                st.rerun()
            
            if st.session_state.panier:
                st.write("---")
                net_total = 0.0; detail_items = []
                for art, qte in list(st.session_state.panier.items()):
                    p_orig = i_map[art]['p']
                    # Conversion dynamique selon le taux de l'entreprise
                    if i_map[art]['d'] == "USD" and dev_v == "CDF": p_u = p_orig * C_TAUX
                    elif i_map[art]['d'] == "CDF" and dev_v == "USD": p_u = p_orig / C_TAUX
                    else: p_u = p_orig
                    
                    st_val = p_u * qte
                    net_total += st_val
                    detail_items.append({'art': art, 'qte': qte, 'p_u': p_u, 'st': st_val})
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{art}** ({p_u:,.2f} {dev_v})")
                    st.session_state.panier[art] = c2.number_input("Qté", 1, i_map[art]['s'], value=qte, key=f"qte_{art}")
                    if c3.button("🗑️", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()
                
                st.markdown(f'<div class="total-frame">NET À PAYER : {net_total:,.2f} {dev_v}</div>', unsafe_allow_html=True)
                
                c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                c_pay = st.number_input("MONTANT REÇU", 0.0)
                
                if st.button("💳 VALIDER ET FACTURER"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref, c_nom, net_total, c_pay, net_total-c_pay, dev_v, dt, USER, ENT_ID, str(detail_items)))
                    
                    if net_total - c_pay > 0:
                        run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?)", (c_nom, net_total-c_pay, dev_v, ref, ENT_ID))
                    
                    for i in detail_items:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {"ref": ref, "cl": c_nom, "tot": net_total, "pay": c_pay, "dev": dev_v, "items": detail_items, "date": dt}
                    st.session_state.panier = {}
                    st.rerun()
        else:
            f = st.session_state.last_fac
            st.markdown(f"""
            <div style="background:white; padding:20px; border:1px solid #000; color:black; font-family:monospace; width:320px; margin:auto;">
                <h2 align="center">{C_NOM}</h2>
                <p align="center">{C_ADR}<br>Tél: {C_TEL}</p><hr>
                <p>Date: {f['date']}<br>Facture: {f['ref']}<br>Client: {f['cl']}<br>Vendeur: {USER.upper()}</p><hr>
                <table style="width:100%">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table><hr>
                <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
                <p align="right">Payé: {f['pay']}<br>Reste: {f['tot']-f['pay']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⬅️ NOUVELLE VENTE"):
                st.session_state.last_fac = None; st.rerun()

    elif st.session_state.page == "VENDEURS" and ROLE == "ADMIN":
        st.title("👥 Gestion de mes Vendeurs")
        st.info("Créez des comptes pour vos employés. Ils n'auront accès qu'à la Caisse et aux Dettes.")
        with st.form("add_vendeur"):
            v_u = st.text_input("Identifiant du vendeur").lower().strip()
            v_p = st.text_input("Mot de passe", type="password").strip()
            if st.form_submit_button("✅ CRÉER LE COMPTE"):
                if v_u and v_p:
                    if not run_db("SELECT * FROM users WHERE username=?", (v_u,), fetch=True):
                        run_db("INSERT INTO users VALUES (?, ?, 'VENDEUR', ?)", (v_u, make_hashes(v_p), ENT_ID))
                        st.success(f"Compte vendeur '{v_u}' activé.")
                    else: st.error("Cet identifiant existe déjà.")
        
        st.write("---")
        staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
        for s in staff:
            c1, c2 = st.columns([4, 1])
            c1.write(f"👤 **{s[0].upper()}**")
            if c2.button("Supprimer", key=f"del_{s[0]}"):
                run_db("DELETE FROM users WHERE username=?", (s[0],))
                st.rerun()

    elif st.session_state.page == "STOCK" and ROLE == "ADMIN":
        st.title("📦 Inventaire des Articles")
        with st.form("add_prod"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            n = c1.text_input("Désignation")
            q = c2.number_input("Quantité", 1)
            p = c3.number_input("Prix Vente")
            d = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("📦 ENREGISTRER L'ARTICLE"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (n.upper(), q, p, d, ENT_ID)); st.rerun()
        
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
        for r in prods:
            with st.expander(f"{r[1]} - Stock: {r[2]} {r[4]}"):
                new_p = st.number_input("Modifier prix", value=float(r[3]), key=f"mod_{r[0]}")
                if st.button("Sauver", key=f"btn_{r[0]}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_p, r[0]))
                    st.rerun()
                if st.button("🗑️ Supprimer", key=f"rmp_{r[0]}"):
                    run_db("DELETE FROM produits WHERE id=?", (r[0],))
                    st.rerun()

    elif st.session_state.page == "CONFIG" and ROLE == "ADMIN":
        st.title("⚙️ Paramètres Entreprise")
        with st.form("cfg_form"):
            e_n = st.text_input("Nom de l'Etablissement", C_NOM)
            e_a = st.text_input("Adresse Physique", C_ADR)
            e_t = st.text_input("Téléphone Contact", C_TEL)
            e_x = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TAUX)
            e_m = st.text_area("Message Barre Défilante", C_MSG)
            if st.form_submit_button("💾 ENREGISTRER LES MODIFICATIONS"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", 
                       (e_n.upper(), e_a, e_t, e_x, e_m, ENT_ID))
                st.rerun()
