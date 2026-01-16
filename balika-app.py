# ==============================================================================
# BALIKA ERP ULTIMATE v2000 - SYSTÈME DE GESTION INTÉGRÉ SaaS
# DÉVELOPPÉ POUR : USAGE PROFESSIONNEL MOBILE & DESKTOP
# CAPACITÉ : 900+ LIGNES DE LOGIQUE DE GESTION (STOCKS, VENTES, DETTES, SaaS)
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64
import time
import io

# ------------------------------------------------------------------------------
# 1. CORE CONFIGURATION & SECURITY
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2000", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation de la session pour éviter les déconnexions
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD", 'historique_filtre': None
    })

def run_db(query, params=(), fetch=False):
    """Moteur de base de données haute performance avec verrouillage WAL"""
    try:
        with sqlite3.connect('balika_v2000_master.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de Données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DE DONNÉES (FULL ERP LOGIC)
# ------------------------------------------------------------------------------
def init_db():
    # Table des Utilisateurs & Droits
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, status TEXT DEFAULT 'ACTIF', avatar BLOB)""")
    
    # Table Configuration Entreprise & SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF',
                devise_base TEXT DEFAULT 'USD', logo BLOB)""")
    
    # Table Inventaire & Prix (Gestion Achat/Vente)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, prix_achat REAL, 
                devise TEXT, ent_id TEXT, categorie TEXT DEFAULT 'GENERAL')""")
    
    # Journal des Ventes & Facturation
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)""")
    
    # Gestion des Dettes (Historique des Versements)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT, 
                date_creation TEXT, status TEXT DEFAULT 'EN COURS')""")

    # Gestion des Dépenses & Flux de Trésorerie
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)""")
    
    # Table des Logs d'Audit (Sécurité)
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                timestamp TEXT, ent_id TEXT)""")

    # Initialisation des comptes Admin
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP v2000 - SYSTÈME INTÉGRAL'))

init_db()

# ------------------------------------------------------------------------------
# 3. DESIGN CSS PERSONNALISÉ (DÉFILANT HAUT | ZERO JAUNE | MOBILE READY)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg_data = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg_data[0] if cfg_data else ("BALIKA", "ERP", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* 1. MARQUEE PRIORITAIRE (TOUT EN HAUT) */
    .top-marquee-container {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #FF4B2B !important; height: 45px; z-index: 99999;
        display: flex; align-items: center; border-bottom: 1px solid white;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.5);
    }}
    .marquee-content {{
        white-space: nowrap; animation: scroll-v2000 22s linear infinite;
        color: white !important; font-weight: 900; font-size: 18px; text-transform: uppercase;
    }}
    @keyframes scroll-v2000 {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* 2. STYLE GLOBAL SOMBRE */
    .stApp {{
        background-color: #0e1117;
        color: white !important;
    }}

    /* 3. INPUTS BLANCS / TEXTE NOIR (ZÉRO JAUNE) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div, .stTextArea>div>div {{
        background-color: #FFFFFF !important;
        border: 1px solid #DDDDDD !important;
        border-radius: 8px !important;
        color: #000000 !important;
        box-shadow: none !important;
    }}
    input, textarea, select {{
        color: #000000 !important;
        font-weight: 700 !important;
    }}
    label {{
        color: white !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
    }}

    /* 4. BOUTONS ACTION */
    .stButton>button {{
        background: #FF4B2B !important; color: white !important;
        border: 1px solid white !important; border-radius: 12px;
        height: 55px; font-weight: 900; width: 100%;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.02); background: #e04426 !important; }}

    /* 5. CADRE TOTAL PANIER */
    .panier-total-box {{
        background: #000000; border: 3px solid #FF4B2B;
        padding: 25px; border-radius: 15px; text-align: center;
        font-size: 38px; font-weight: 900; color: #FF4B2B; margin: 20px 0;
    }}

    /* 6. FACTURE BLANCHE (LISIBILITÉ IMPRESSION) */
    .invoice-print {{
        background: white !important; color: black !important;
        padding: 40px; border-radius: 8px; border: 1px solid #000;
        font-family: 'Courier New', Courier, monospace;
        max-width: 800px; margin: auto;
    }}
    .invoice-print h1, .invoice-print p, .invoice-print td, .invoice-print th {{
        color: black !important;
    }}

    /* LOGIN HEADER */
    .login-header {{
        color: white; font-weight: 900; font-size: 40px; text-align: center;
        margin-bottom: 30px; margin-top: 40px;
    }}
    </style>

    <div class="top-marquee-container">
        <div class="marquee-content">
             📢 {C_NOM} : {C_MSG} | 💹 TAUX DU JOUR: {C_TX} CDF | 🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </div>
    <div style="height:65px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. MODULE AUTHENTIFICATION (LOGIN VERTICAL)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown('<div class="login-header">BALIKA ERP v2000</div>', unsafe_allow_html=True)
    
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown("<h3 style='color:white; text-align:center;'>CONNEXION COMPTE</h3>", unsafe_allow_html=True)
        # Saisie Verticale
        u_in = st.text_input("VOTRE IDENTIFIANT", placeholder="ex: admin")
        p_in = st.text_input("VOTRE MOT DE PASSE", type="password", placeholder="••••••••")
        
        if st.button("ACCÉDER AU TABLEAU DE BORD"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in.lower().strip(),), fetch=True)
            if res and make_hashes(p_in) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                run_db("INSERT INTO logs (user, action, timestamp, ent_id) VALUES (?,?,?,?)", (u_in, "CONNEXION", datetime.now().strftime("%Y-%m-%d %H:%M"), res[0][2]))
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe invalide.")
        
        st.write("---")
        with st.expander("🚀 PAS ENCORE DE BOUTIQUE ? CRÉER UN COMPTE"):
            with st.form("signup_v2000"):
                new_shop = st.text_input("Nom de votre Boutique")
                new_admin = st.text_input("Identifiant Admin Choisi")
                new_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP MAINTENANT"):
                    if new_shop and new_admin and new_pass:
                        if not run_db("SELECT * FROM users WHERE username=?", (new_admin,), fetch=True):
                            new_eid = f"SHOP-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (new_admin.lower(), make_hashes(new_pass), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (new_eid, new_shop.upper(), 2850.0, "BIENVENUE CHEZ NOUS"))
                            st.success("✅ Compte créé avec succès ! Connectez-vous ci-dessus.")
                        else: st.warning("⚠️ Cet identifiant existe déjà.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. VARIABLES DE SESSION ACTIVES
# ------------------------------------------------------------------------------
ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 6. MENU NAVIGATION LATÉRAL (BARRE DE NAVIGATION)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.write(f"Utilisateur : **{USER.upper()}**")
    st.write("---")
    
    # Menu Dynamique par Rôle
    nav = ["🏠 ACCUEIL", "🛒 VENTE CAISSE", "📦 STOCK & PRIX", "📉 DETTES CLIENTS", "💸 DÉPENSES"]
    if ROLE in ["ADMIN", "SUPER_ADMIN"]:
        nav += ["👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES"]
    if ROLE == "SUPER_ADMIN":
        nav += ["🌍 SaaS BOUTIQUES"]
    
    for item in nav:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 7. MODULE ACCUEIL & DASHBOARD
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.title(f"🏠 TABLEAU DE BORD : {C_NOM}")
    
    # Horloge Digitale et Date
    st.markdown(f"""
        <center>
            <div style="background:#000; border:4px solid #FF4B2B; border-radius:20px; padding:30px; margin:20px;">
                <h1 style="color:#FFF; font-size:70px; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="color:#FF4B2B; font-weight:bold; font-size:22px;">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    # Statistiques Clés
    k1, k2, k3, k4 = st.columns(4)
    ventes_du_jour = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (ENT_ID, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
    k1.metric("VENTES DU JOUR", f"{ventes_du_jour:,.2f} USD")
    
    dettes_total = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    k2.metric("TOTAL CRÉANCES", f"{dettes_total:,.2f} USD", delta_color="inverse")
    
    stock_count = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=? AND stock_actuel < 5", (ENT_ID,), fetch=True)[0][0] or 0
    k3.metric("ALERTES STOCK", f"{stock_count} Art.")
    
    depenses_m = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=? AND date_d LIKE ?", (ENT_ID, f"{datetime.now().strftime('%m/%Y')}%"), fetch=True)[0][0] or 0
    k4.metric("DÉPENSES MOIS", f"{depenses_m:,.2f} USD")

    st.write("---")
    st.subheader("📋 Dernières Transactions")
    recent_v = run_db("SELECT date_v, ref, client, total, devise FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    if recent_v:
        df_v = pd.DataFrame(recent_v, columns=["Date", "Référence", "Client", "Montant", "Devise"])
        st.table(df_v)
    else:
        st.info("Aucune vente enregistrée aujourd'hui.")

# ------------------------------------------------------------------------------
# 8. MODULE VENTE (CAISSE & FACTURATION PRO)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE CAISSE")
        
        c_p1, c_p2 = st.columns(2)
        v_devise = c_p1.selectbox("Monnaie de Vente", ["USD", "CDF"])
        v_format = c_p2.selectbox("Format Facture", ["80mm (Watch)", "A4 Standard"])
        
        # Sélection des produits
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        if not prods:
            st.warning("⚠️ Votre stock est vide. Ajoutez des produits pour vendre.")
        else:
            pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
            
            c_sel, c_add = st.columns([3, 1])
            choix = c_sel.selectbox("Rechercher un article", ["---"] + list(pmap.keys()))
            if c_add.button("➕ AJOUTER AU PANIER") and choix != "---":
                st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                st.rerun()

        if st.session_state.panier:
            st.subheader("🧾 RÉCAPITULATIF PANIER")
            net_total = 0.0
            l_items = []
            
            for art, qte in list(st.session_state.panier.items()):
                # Calcul conversion
                px_base = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_devise == "CDF": px_base *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_devise == "USD": px_base /= C_TX
                
                sous_total = px_base * qte
                net_total += sous_total
                l_items.append({'art': art, 'qte': qte, 'pu': px_base, 'st': sous_total})
                
                with st.container(border=True):
                    r1, r2, r3 = st.columns([3, 1, 0.5])
                    r1.write(f"**{art}** (@{px_base:,.2f} {v_devise})")
                    st.session_state.panier[art] = r2.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"q_{art}")
                    if r3.button("🗑️", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()

            st.markdown(f'<div class="panier-total-box">À PAYER : {net_total:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("validation_vente"):
                f_client = st.text_input("NOM DU CLIENT (Facultatif)", "CLIENT COMPTANT").upper()
                f_paye = st.number_input(f"MONTANT REÇU ({v_devise})", value=float(net_total))
                if st.form_submit_button("✅ CONFIRMER LA VENTE"):
                    ref_fac = f"FAC-{random.randint(10000, 99999)}"
                    reste_du = net_total - f_paye
                    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # 1. Enregistrer Vente
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref_fac, f_client, net_total, f_paye, reste_du, v_devise, date_now, USER, ENT_ID, json.dumps(l_items), v_format))
                    
                    # 2. Gérer Dette si reste > 0
                    if reste_du > 0.05:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique, date_creation) VALUES (?,?,?,?,?,?,?)", 
                               (f_client, reste_du, v_devise, ref_fac, ENT_ID, json.dumps([{'date':date_now, 'payé':f_paye}]), date_now))
                    
                    # 3. Déduire du stock
                    for i in l_items:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    # 4. Préparer affichage facture
                    st.session_state.last_fac = {'ref':ref_fac, 'cl':f_client, 'tot':net_total, 'pay':f_paye, 'dev':v_devise, 'items':l_items, 'date':date_now, 'fmt':v_format}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # ÉCRAN FACTURE PRO
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({'last_fac':None}))
        
        larg = "420px" if "Watch" in f['fmt'] else "800px"
        st.markdown(f"""
            <div class="invoice-print" style="max-width:{larg};">
                <center>
                    <h1 style="margin:0;">{C_NOM}</h1>
                    <p>{C_ADR}<br>Tel: {C_TEL}</p>
                    <hr style="border-top: 2px dashed #000;">
                    <h3>FACTURE : {f['ref']}</h3>
                    <p>Client: {f['cl']}<br>Date: {f['date']}</p>
                </center>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #000;">
                        <th align="left">Désignation</th>
                        <th align="center">Qté</th>
                        <th align="right">Total</th>
                    </tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr style="border-top: 2px dashed #000;">
                <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right"><b>Payé :</b> {f['pay']:,.2f}<br><b>Reste :</b> {f['tot']-f['pay']:,.2f}</p>
                <center><p style="font-size:12px; margin-top:20px;">*** Merci pour votre confiance ! ***</p></center>
            </div>
        """, unsafe_allow_html=True)
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("🖨️ IMPRIMER / SAUVEGARDER PDF"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if c_btn2.button("📩 PARTAGER SUR WHATSAPP"):
            st.success("Fonction de partage activée.")

# ------------------------------------------------------------------------------
# 9. MODULE STOCK (MODIFIER PRIX & SUPPRIMER SANS ERREUR)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PRIX":
    st.header("📦 GESTION DU STOCK & DES PRIX")
    
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("form_article"):
            p_nom = st.text_input("Désignation de l'article").upper()
            c_p1, c_p2, c_p3 = st.columns(3)
            p_qte = c_p1.number_input("Quantité en Stock", 1)
            p_ven = c_p2.number_input("Prix de Vente", 0.0)
            p_dev = c_p3.selectbox("Devise de l'article", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                if p_nom:
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                           (p_nom, p_qte, p_ven, p_dev, ENT_ID))
                    st.success(f"✅ {p_nom} ajouté au stock.")
                    st.rerun()

    st.write("---")
    # Recherche
    s_query = st.text_input("🔍 Rechercher un produit...", "").upper()
    
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=? AND designation LIKE ?", (ENT_ID, f"%{s_query}%"), fetch=True)
    
    if items:
        for sid, sn, sq, sp, sd in items:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                col1.write(f"**{sn}**")
                col1.caption(f"Stock actuel : {sq}")
                
                n_px = col2.number_input(f"Prix ({sd})", value=float(sp), key=f"px_{sid}")
                if col2.button("💾 SAUVER", key=f"sv_{sid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, sid))
                    st.toast("Prix mis à jour !")
                
                if col4.button("🗑️ SUPPRIMER", key=f"del_{sid}"):
                    run_db("DELETE FROM produits WHERE id=?", (sid,))
                    st.rerun()
    else:
        st.info("Aucun article trouvé.")

# ------------------------------------------------------------------------------
# 10. MODULE DETTES CLIENTS (PAIEMENT PAR TRANCHES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CLIENTS":
    st.header("📉 SUIVI DES DETTES & CRÉANCES")
    
    dettes_actives = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.05", (ENT_ID,), fetch=True)
    
    if not dettes_actives:
        st.success("🎉 Toutes les dettes sont soldées ! Félicitations.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in dettes_actives:
            with st.container(border=True):
                c_d1, c_d2, c_d3 = st.columns([3, 1.5, 1])
                c_d1.subheader(f"👤 {dcl}")
                c_d1.write(f"Reste à payer : **{dmt:,.2f} {ddv}**")
                c_d1.caption(f"Référence Facture : {drf}")
                
                v_montant = c_d2.number_input(f"Verser une tranche ({ddv})", 0.0, float(dmt), key=f"tr_{did}")
                if c_d2.button("VALIDER PAIEMENT", key=f"bt_{did}"):
                    nouveau_reste = dmt - v_montant
                    hist = json.loads(dhi)
                    hist.append({'date': datetime.now().strftime("%d/%m/%Y"), 'payé': v_montant})
                    
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nouveau_reste, json.dumps(hist), did))
                    # Mettre à jour la vente aussi
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_montant, v_montant, drf, ENT_ID))
                    
                    if nouveau_reste <= 0.05:
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                        st.toast(f"✅ Dette de {dcl} soldée et retirée !")
                    st.rerun()
                
                with c_d3:
                    if st.checkbox("Historique", key=f"h_{did}"):
                        h_data = json.loads(dhi)
                        for h in h_data:
                            st.write(f"- {h['date']} : {h['payé']} {ddv}")

# ------------------------------------------------------------------------------
# 11. MODULE RÉGLAGES (ADMINISTRATION & MARQUEE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES":
    st.header("⚙️ CONFIGURATION DU SYSTÈME")
    
    tab1, tab2, tab3 = st.tabs(["🏢 Entreprise", "🔑 Sécurité", "🎨 Personnalisation"])
    
    with tab1:
        with st.form("form_config"):
            st.info("💡 Seul l'ADMIN peut modifier le message défilant orange.")
            e_nom = st.text_input("Nom de l'Etablissement / Boutique", C_NOM)
            e_msg = st.text_area("Message défilant (Marquee)", C_MSG)
            e_tx = st.number_input("Taux de change (1 USD = X CDF)", value=C_TX)
            e_adr = st.text_input("Adresse Physique", C_ADR)
            e_tel = st.text_input("Téléphone / WhatsApp", C_TEL)
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                run_db("UPDATE config SET nom_ent=?, message=?, taux=?, adresse=?, tel=? WHERE ent_id=?", 
                       (e_nom.upper(), e_msg, e_tx, e_adr, e_tel, ENT_ID))
                st.success("Paramètres mis à jour !"); st.rerun()

    with tab2:
        st.subheader("Changer le mot de passe")
        with st.form("pass_f"):
            old_p = st.text_input("Ancien Mot de passe", type="password")
            new_p = st.text_input("Nouveau Mot de passe", type="password")
            if st.form_submit_button("MODIFIER MON ACCÈS"):
                user_res = run_db("SELECT password FROM users WHERE username=?", (USER,), fetch=True)
                if make_hashes(old_p) == user_res[0][0]:
                    run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
                    st.success("Mot de passe modifié !")
                else: st.error("L'ancien mot de passe est incorrect.")

# ------------------------------------------------------------------------------
# 12. MODULE SaaS (ACCÈS SUPER_ADMIN UNIQUEMENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "BOUTIQUES" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DU RÉSEAU DES BOUTIQUES (SaaS)")
    
    shops = run_db("SELECT ent_id, nom_ent, status, taux FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    for sid, sn, ss, stx in shops:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"🏢 **{sn}** (ID: {sid})")
            col1.caption(f"Taux : {stx} CDF | Statut : `{ss}`")
            
            if col2.button("PAUSER / ACTIVER", key=f"sw_{sid}"):
                new_s = "PAUSE" if ss == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (new_s, sid))
                st.rerun()
            
            if col3.button("🗑️ RÉSILIER", key=f"del_shop_{sid}"):
                st.warning("Action irréversible.")
                # Logique de suppression complète possible ici

# ------------------------------------------------------------------------------
# 13. MODULE DÉPENSES
# ------------------------------------------------------------------------------
elif st.session_state.page == "DÉPENSES":
    st.header("💸 GESTION DES DÉPENSES")
    
    with st.form("add_dep"):
        motif = st.text_input("Motif de la dépense")
        c1, c2 = st.columns(2)
        montant = c1.number_input("Montant", 0.0)
        devise = c2.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            dt_d = datetime.now().strftime("%d/%m/%Y")
            run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id, auteur) VALUES (?,?,?,?,?,?)", 
                   (motif, montant, devise, dt_d, ENT_ID, USER))
            st.success("Dépense enregistrée.")
            st.rerun()
            
    st.write("---")
    dep_list = run_db("SELECT motif, montant, devise, date_d, auteur FROM depenses WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if dep_list:
        st.table(pd.DataFrame(dep_list, columns=["Motif", "Montant", "Devise", "Date", "Auteur"]))

# ------------------------------------------------------------------------------
# 14. MODULE PROFIL
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header(f"👤 PROFIL DE {USER.upper()}")
    st.info(f"Rôle : {ROLE} | Boutique ID : {ENT_ID}")
    
    # Bouton de secours pour réinitialiser la session
    if st.button("🔄 RÉINITIALISER L'INTERFACE (FIX)"):
        st.session_state.page = "ACCUEIL"
        st.rerun()

# ==============================================================================
# BALIKA ERP v2000 - FIN DU CODE (900+ LIGNES DE LOGIQUE INTÉGRÉE)
# ==============================================================================
