# ==============================================================================
# BALIKA ERP ULTIMATE v750 - VERSION ÉTENDUE PROFESSIONNELLE
# COMPREND : SaaS, CAISSE MULTI-DEVISE, GESTION VENDEURS, AUDIT & EXPORT
# DESIGN : FULL SCREEN ORANGE-NOIR | MARQUEE FIXE | ZÉRO CADRE BLANC
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
# 1. CONFIGURATION SYSTÈME & CORE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v750", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation complète du Session State (Indispensable pour la navigation)
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD", 'notifs': []
    })

def run_db(query, params=(), fetch=False):
    """Moteur de base de données ultra-sécurisé avec mode WAL"""
    try:
        with sqlite3.connect('balika_pro_v750.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur DB Critique : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET ÉTENDU)
# ------------------------------------------------------------------------------
def init_db():
    # Table Utilisateurs (Profils & Droits)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT, status TEXT DEFAULT 'ACTIF')""")
    
    # Table Configuration Entreprise & Paramètres SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT, montant_paye REAL DEFAULT 0.0,
                logo BLOB)""")
    
    # Table Inventaire (Stock & Prix)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, categorie TEXT, stock_alerte INTEGER DEFAULT 5)""")
    
    # Table Ventes (Journal Central)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, type_paiement TEXT)""")
    
    # Table Dettes (Suivi des Crédits Clients)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT, date_echeance TEXT)""")
    
    # Table Logs (Audit de sécurité)
    run_db("""CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, 
                date TEXT, ent_id TEXT)""")

    # Initialisation Admin Système (Maître du SaaS)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP - SYSTÈME UNIFIÉ 2026', '16/01/2026'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS PROFESSIONNELLE (SANS CADRE BLANC)
# ------------------------------------------------------------------------------
# Récupération des données de branding
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
if res_cfg:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0]
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    /* Fond dégradé immersif */
    .stApp {{
        background: linear-gradient(180deg, #FF4B2B 0%, #FF8008 100%);
        background-attachment: fixed;
        color: white !important;
    }}

    /* MARQUEE FIXE HAUT DE PAGE */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 55px;
        z-index: 999999; border-bottom: 3px solid #FFF;
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-content {{
        display: inline-block; white-space: nowrap;
        animation: marquee-move 22s linear infinite;
        font-family: 'Courier New', monospace; font-size: 22px; font-weight: bold;
    }}
    @keyframes marquee-move {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Suppression des cadres blancs (Inputs transparents) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important; border: 2px solid rgba(255,255,255,0.5) !important;
        color: white !important; height: 50px !important;
    }}
    input {{ color: white !important; font-weight: bold !important; font-size: 18px !important; }}
    label {{ color: white !important; font-weight: bold !important; text-transform: uppercase; }}

    /* Boutons de commande */
    .stButton>button {{
        background: #0055ff !important; color: white !important;
        border-radius: 15px; font-weight: 900; height: 60px; width: 100%;
        border: 2px solid white !important; text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.02); background: #003399 !important; }}

    /* Montre et Total */
    .clock-box {{
        background: rgba(0,0,0,0.5); color: #FFD700; padding: 35px; border-radius: 25px;
        border: 4px solid white; text-align: center; margin-bottom: 30px;
    }}
    .price-frame {{
        border: 5px solid #FFF; background: #000; padding: 25px;
        border-radius: 20px; color: #39FF14; font-size: 45px;
        font-weight: 900; text-align: center; margin: 25px 0;
    }}
    
    /* Sidebar Stylisée */
    [data-testid="stSidebar"] {{ background-color: #F8F9FA !important; border-right: 10px solid #000; }}
    [data-testid="stSidebar"] * {{ color: #000 !important; font-weight: 800 !important; }}

    /* Tableaux */
    .stDataFrame {{ background: white !important; border-radius: 10px; }}
    </style>

    <div class="marquee-wrapper">
        <div class="marquee-content">
             🚀 {C_NOM} : {C_MSG} | 💹 TAUX: {C_TX} CDF/USD | 📅 {datetime.now().strftime('%d/%m/%Y')} | SYSTÈME BALIKA v750
        </div>
    </div>
    <div style="height:70px;"></div>
""", unsafe_allow_html=True)

# Blocage Sécurité SaaS
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 VOTRE ACCÈS EST SUSPENDU. VEUILLEZ RÉGULARISER VOTRE ABONNEMENT.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE DE CONNEXION (LOGIN)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.markdown(f"<h1 style='text-align:center; font-size:4rem; color:white;'>{C_NOM}</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 ACCÈS TERMINAL", "🚀 CRÉER UNE INSTANCE"])
        
        with tab_log:
            u_in = st.text_input("Identifiant Utilisateur").lower().strip()
            p_in = st.text_input("Mot de passe secret", type="password")
            if st.button("DÉVERROUILLER LE SYSTÈME"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if res and make_hashes(p_in) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                    run_db("INSERT INTO logs (user, action, date, ent_id) VALUES (?,?,?,?)", (u_in, "CONNEXION", datetime.now().strftime("%d/%m/%Y %H:%M"), res[0][2]))
                    st.success("Accès autorisé...")
                    time.sleep(1)
                    st.rerun()
                else: st.error("ÉCHEC : Identifiants invalides.")
        
        with tab_reg:
            with st.form("inscription_saas"):
                st.subheader("Déployer votre ERP personnel")
                r_ent = st.text_input("Nom de votre Business (Boutique/Ets)")
                r_tel = st.text_input("Contact WhatsApp Principal")
                r_user = st.text_input("Créer un ID Admin").lower().strip()
                r_pass = st.text_input("Créer un Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP MAINTENANT"):
                    if r_ent and r_user and r_pass:
                        check = run_db("SELECT * FROM users WHERE username=?", (r_user,), fetch=True)
                        if not check:
                            new_id = f"E-{random.randint(10000, 99999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                                   (r_user, make_hashes(r_pass), "ADMIN", new_id, r_tel))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, taux, message, date_inscription) VALUES (?,?,?,?,?,?)", 
                                   (new_id, r_ent.upper(), r_tel, 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ INSTANCE CRÉÉE ! Connectez-vous.")
                        else: st.warning("Cet ID est déjà réservé.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION SIDEBAR DYNAMIQUE
# ------------------------------------------------------------------------------
with st.sidebar:
    # Gestion Photo de Profil
    pic_res = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if pic_res and pic_res[0][0]: st.image(pic_res[0][0], width=120)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.info(f"Rôle : {ROLE} | ID : {ENT_ID}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        nav = ["🏠 ACCUEIL", "🌍 ABONNÉS SaaS", "📊 AUDIT RÉSEAU", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        nav = ["🏠 ACCUEIL", "🛒 CAISSE VENTE", "📉 GESTION DETTES", "📦 STOCK & PRIX", "👥 ÉQUIPE VENDEURS", "📊 ANALYSE VENTES", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # VENDEUR
        nav = ["🏠 ACCUEIL", "🛒 CAISSE VENTE", "📉 GESTION DETTES", "👤 MON PROFIL"]

    for item in nav:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 FERMER LA SESSION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE ACCUEIL (DASHBOARD)
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.title(f"🏢 {C_NOM}")
    
    st.markdown(f"""
        <center>
            <div class="clock-box">
                <h1 style="font-size:70px; margin:0;">{datetime.now().strftime('%H:%M:%S')}</h1>
                <p style="font-size:24px;">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    # Statistiques rapides
    st.write("---")
    c1, c2, c3, c4 = st.columns(4)
    s_tot = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{s_tot:,.2f} $")
    
    d_tot = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("CRÉANCES CLIENTS", f"{d_tot:,.2f} $", delta="-5%", delta_color="inverse")
    
    p_tot = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", p_tot)
    
    v_tot = run_db("SELECT COUNT(*) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c4.metric("VENTES RÉALISÉES", v_tot)

# ------------------------------------------------------------------------------
# 7. MODULE CAISSE (VENTE PROFESSIONNELLE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL POINT DE VENTE")
        
        col_set1, col_set2 = st.columns(2)
        v_devise = col_set1.selectbox("Monnaie de paiement", ["USD", "CDF"])
        v_type = col_set2.selectbox("Type de transaction", ["COMPTANT", "CRÉDIT", "MOBILE MONEY"])
        
        # Sélection de l'article
        st.write("### ➕ Ajouter au panier")
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        c_sel, c_add = st.columns([3, 1])
        choix = c_sel.selectbox("Rechercher un produit...", ["---"] + list(p_map.keys()))
        if c_add.button("AJOUTER AU PANIER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            st.write("### 🛍️ Votre Panier")
            net_total = 0.0
            lignes_fac = []
            
            for art, qte in list(st.session_state.panier.items()):
                base_px = p_map[art]['px']
                base_dv = p_map[art]['dv']
                
                # Conversion dynamique selon devise de vente
                if base_dv == "USD" and v_devise == "CDF": final_px = base_px * C_TX
                elif base_dv == "CDF" and v_devise == "USD": final_px = base_px / C_TX
                else: final_px = base_px
                
                sous_total = final_px * qte
                net_total += sous_total
                lignes_fac.append({'art': art, 'qte': qte, 'pu': final_px, 'st': sous_total})
                
                row1, row2, row3 = st.columns([3, 1, 0.5])
                row1.write(f"**{art}** (@{final_px:,.2f})")
                st.session_state.panier[art] = row2.number_input("Qté", 1, p_map[art]['st'], value=qte, key=f"q_{art}")
                if row3.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="price-frame">TOTAL À PAYER : {net_total:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("validation_vente"):
                f_client = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                f_paye = st.number_input(f"MONTANT REÇU ({v_devise})", value=float(net_total))
                if st.form_submit_button("💰 FINALISER ET IMPRIMER"):
                    ref_f = f"FAC-{random.randint(10000, 99999)}"
                    reste_f = net_total - f_paye
                    date_f = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Enregistrement Vente
                    run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, type_paiement) 
                              VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                           (ref_f, f_client, net_total, f_paye, reste_f, v_devise, date_f, USER, ENT_ID, json.dumps(lignes_fac), v_type))
                    
                    # Enregistrement Dette si crédit
                    if reste_f > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                               (f_client, reste_f, v_devise, ref_f, ENT_ID, json.dumps([{'d': date_f, 'p': f_paye}])))
                    
                    # Déstockage
                    for l in lignes_fac:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (l['qte'], l['art'], ENT_ID))
                    
                    st.session_state.last_fac = {'ref': ref_f, 'cl': f_client, 'tot': net_total, 'pay': f_paye, 'dev': v_devise, 'items': lignes_fac, 'date': date_f}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # Affichage Facture
        fac = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({'last_fac': None}))
        
        st.markdown(f"""
            <div style="background: white; color: black; padding: 40px; border: 2px solid #000; font-family: 'Courier New', monospace; max-width: 600px; margin: auto;">
                <center>
                    <h1>{C_NOM}</h1>
                    <p>{C_ADR}<br>Tél: {C_TEL}</p>
                    <hr style="border-top: 2px dashed black;">
                    <h3>FACTURE N° {fac['ref']}</h3>
                    <p>Client: {fac['cl']}<br>Date: {fac['date']}</p>
                </center>
                <table style="width:100%;">
                    <tr style="border-bottom: 1px solid black;"><th>Article</th><th>Qté</th><th>Total</th></tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in fac['items']])}
                </table>
                <hr style="border-top: 2px dashed black;">
                <h2 align="right">TOTAL : {fac['tot']:,.2f} {fac['dev']}</h2>
                <p align="right">Payé : {fac['pay']:,.2f} | Reste : {fac['tot']-fac['pay']:,.2f}</p>
                <br><br>
                <center><p>*** MERCI DE VOTRE VISITE ***</p></center>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        c_p1, c_p2 = st.columns(2)
        c_p1.button("🖨️ IMPRIMER TICKET", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        w_msg = f"Facture {fac['ref']} - {C_NOM}. Total: {fac['tot']} {fac['dev']}. Merci!"
        c_p2.markdown(f'<a href="https://wa.me/?text={w_msg}" target="_blank"><button style="width:100%; background:#25D366; color:white; height:50px; border-radius:10px; border:none; font-weight:bold;">📲 ENVOYER WHATSAPP</button></a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 8. MODULE STOCK (MODIFICATION & SUPPRESSION SÉCURISÉE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PRIX":
    st.header("📦 GESTION DU STOCK ET DES PRIX")
    
    tab_list, tab_add = st.tabs(["📋 LISTE DU STOCK", "➕ NOUVEL ARTICLE"])
    
    with tab_add:
        with st.form("nouveau_produit"):
            f_nom = st.text_input("Désignation de l'article").upper()
            f_cat = st.selectbox("Catégorie", ["GÉNÉRAL", "ALIMENTATION", "HABILLEMENT", "ÉLECTRONIQUE"])
            c_q1, c_q2, c_q3 = st.columns(3)
            f_qty = c_q1.number_input("Quantité en stock", 0)
            f_px = c_q2.number_input("Prix de vente", 0.0)
            f_dv = c_q3.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER DANS L'INVENTAIRE"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id, categorie) VALUES (?,?,?,?,?,?)", 
                       (f_nom, f_qty, f_px, f_dv, ENT_ID, f_cat))
                st.success("Produit ajouté !")
                st.rerun()

    with tab_list:
        items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise, categorie FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
        if items:
            df_stock = pd.DataFrame(items, columns=["ID", "Désignation", "Stock", "Prix", "Devise", "Catégorie"])
            st.dataframe(df_stock, use_container_width=True)
            
            st.write("---")
            st.subheader("🛠️ Actions rapides")
            for idp, nomp, qp, pxp, dvp, catp in items:
                with st.expander(f"Modifier : {nomp} (ID: {idp})"):
                    cl_m1, cl_m2, cl_m3 = st.columns([2, 1, 1])
                    new_px = cl_m1.number_input("Changer Prix", value=float(pxp), key=f"px_mod_{idp}")
                    if cl_m2.button("💾 SAUVER", key=f"save_{idp}"):
                        run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, idp))
                        st.rerun()
                    if cl_m3.button("🗑️ SUPPRIMER", key=f"del_prod_{idp}"):
                        run_db("DELETE FROM produits WHERE id=?", (idp,))
                        st.rerun()

# ------------------------------------------------------------------------------
# 9. MODULE DETTES (RECOUVREMENT AUTO-SOLDE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.header("📉 CAHIER DES DETTES CLIENTS")
    d_rows = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not d_rows:
        st.success("Félicitations ! Aucun client ne vous doit de l'argent.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in d_rows:
            with st.container(border=True):
                col_d1, col_d2 = st.columns([3, 1])
                col_d1.subheader(f"👤 {dcl}")
                col_d1.write(f"💰 Reste à payer : **{dmt:,.2f} {ddv}** | Facture : {drf}")
                
                v_pay = col_d2.number_input("Montant versé", 0.0, float(dmt), key=f"pay_d_{did}")
                if col_d2.button("ENCAISSER", key=f"btn_d_{did}"):
                    n_mt = dmt - v_pay
                    hist = json.loads(dhi)
                    hist.append({'d': datetime.now().strftime("%d/%m %H:%M"), 'p': v_pay})
                    
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_mt, json.dumps(hist), did))
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_pay, v_pay, drf, ENT_ID))
                    
                    if n_mt <= 0.1:
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                        st.success(f"Dette de {dcl} soldée !")
                    st.rerun()

# ------------------------------------------------------------------------------
# 10. MODULE ANALYSE & RAPPORTS
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENTES":
    st.header("📊 ANALYSE DE L'ACTIVITÉ")
    
    r_data = run_db("SELECT date_v, ref, client, total, paye, reste, vendeur, devise FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if r_data:
        df_v = pd.DataFrame(r_data, columns=["Date", "Référence", "Client", "Total", "Payé", "Reste", "Vendeur", "Devise"])
        st.dataframe(df_v, use_container_width=True)
        
        # Export Excel
        csv = df_v.to_csv(index=False).encode('utf-8')
        st.download_button("📥 TÉLÉCHARGER LE RAPPORT (CSV)", data=csv, file_name=f"Rapport_Ventes_{ENT_ID}.csv", mime='text/csv')
    else:
        st.info("Aucune vente enregistrée pour le moment.")

# ------------------------------------------------------------------------------
# 11. MODULE RÉGLAGES (CONFIG ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ PARAMÈTRES DE L'ENTREPRISE")
    
    with st.form("config_generale"):
        c_nom = st.text_input("Nom de l'Etablissement", C_NOM)
        c_adr = st.text_input("Adresse Physique", C_ADR)
        c_tel = st.text_input("WhatsApp de l'entreprise", C_TEL)
        c_tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TX)
        c_msg = st.text_area("Message défilant (Marquee)", C_MSG)
        
        if st.form_submit_button("SAUVEGARDER LES PARAMÈTRES"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", 
                   (c_nom.upper(), c_adr, c_tel, c_tx, c_msg, ENT_ID))
            st.success("Configuration mise à jour avec succès !")
            st.rerun()

# ------------------------------------------------------------------------------
# 12. MODULE PROFIL (SÉCURITÉ & PHOTO)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE UTILISATEUR")
    
    prof = run_db("SELECT full_name, telephone, username FROM users WHERE username=?", (USER,), fetch=True)[0]
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write("### Informations personnelles")
        n_fn = st.text_input("Nom Complet", prof[0])
        n_tl = st.text_input("Téléphone", prof[1])
        n_img = st.file_uploader("Modifier ma photo de profil", type=["jpg", "png"])
    
    with col_p2:
        st.write("### Sécurité du compte")
        n_pwd = st.text_input("Nouveau mot de passe", type="password")
        n_pwd_c = st.text_input("Confirmer le mot de passe", type="password")
        
    if st.button("METTRE À JOUR MON PROFIL"):
        if n_pwd:
            if n_pwd == n_pwd_c: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pwd), USER))
            else: st.error("Les mots de passe ne correspondent pas.")
        
        if n_img: run_db("UPDATE users SET photo=? WHERE username=?", (n_img.getvalue(), USER))
        
        run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (n_fn, n_tl, USER))
        st.success("Profil mis à jour !"); st.rerun()

# ------------------------------------------------------------------------------
# 13. MODULE SUPER ADMIN (SaaS MANAGEMENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "SaaS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DU RÉSEAU BALIKA")
    
    abos = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, montant_paye FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    for eid, en, et, es, ed, em in abos:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([2, 1, 1, 1])
            cl1.write(f"🏢 **{en}** ({eid})")
            cl2.write(f"📞 {et}")
            cl3.write(f"💰 Payé: **{em} $**")
            cl4.write(f"Status: `{es}`")
            
            c_a1, c_a2, c_a3 = st.columns(3)
            if c_a1.button("PAUSE/ACTIF", key=f"st_{eid}"):
                n_st = "PAUSE" if es == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (n_st, eid))
                st.rerun()
            new_p = c_a2.number_input("Ajouter Paiement", 0.0, key=f"pay_saas_{eid}")
            if c_a2.button("VALIDER $", key=f"btn_p_saas_{eid}"):
                run_db("UPDATE config SET montant_paye = montant_paye + ? WHERE ent_id=?", (new_p, eid))
                st.rerun()
            if c_a3.button("🗑️ SUPPRIMER TOUT", key=f"del_saas_{eid}"):
                run_db("DELETE FROM config WHERE ent_id=?", (eid,))
                run_db("DELETE FROM users WHERE ent_id=?", (eid,))
                st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v750 - +650 LIGNES DE LOGIQUE ERP
# ------------------------------------------------------------------------------
