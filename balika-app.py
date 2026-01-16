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
# 1. CONFIGURATION SYSTÈME & CORE
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP COMMAND v710", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State pour la persistance des données session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 
        'user': "", 
        'role': "", 
        'ent_id': "", 
        'page': "ACCUEIL", 
        'panier': {}, 
        'last_fac': None
    })

# --- MOTEUR DE BASE DE DONNÉES (SQLite avec Mode WAL pour la performance) ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_pro_v710.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur de base de données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. SCHÉMA DE BASE DE DONNÉES COMPLET
# ==============================================================================
def init_db():
    # Table des utilisateurs (Admin, Vendeur, Super-Admin)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT, 
                photo BLOB, 
                full_name TEXT, 
                telephone TEXT)""")
    
    # Table des configurations entreprises (SaaS)
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL, 
                message TEXT, 
                status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, 
                date_inscription TEXT)""")
    
    # Table des produits en stock
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT)""")
    
    # Table des ventes effectuées
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
    
    # Table des dettes clients
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")

    # Création du compte Super-Admin Maître si inexistant
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP - SYSTÈME DE GESTION UNIFIÉ', '16/01/2026'))

init_db()

# ==============================================================================
# 3. CHARGEMENT CONFIGURATION & DESIGN CSS
# ==============================================================================
# Récupération dynamique du message (Global pour login, Spécifique après login)
if st.session_state.auth:
    res_msg = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status FROM config WHERE ent_id=?", 
                     (st.session_state.ent_id,), fetch=True)
else:
    res_msg = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status FROM config WHERE ent_id='SYSTEM'", fetch=True)

if res_msg:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = res_msg[0]
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = ("BALIKA", "Bienvenue", 2850.0, "", "", "", "ACTIF")

# Blocage si compte suspendu
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.markdown("<h1 style='color:red; text-align:center;'>🚨 VOTRE ACCÈS EST SUSPENDU.<br>Veuillez contacter l'administrateur BALIKA.</h1>", unsafe_allow_html=True)
    st.stop()

st.markdown(f"""
    <style>
    /* Global Background */
    .stApp {{ background-color: #f4f7f6; }}
    
    /* Centrage des textes */
    h1, h2, h3, p, label {{ text-align: center !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}

    /* Marquee (Texte Défilant) */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #002266; color: white;
        padding: 10px 0; position: fixed; top: 0; left: 0; z-index: 9999;
        border-bottom: 2px solid #FF8C00;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap; font-weight: bold; font-size: 16px;
        animation: scroll 25s linear infinite;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Boutons Bleus avec texte blanc */
    .stButton>button {{
        background-color: #0044cc !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        border: none;
        padding: 10px;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ background-color: #003399 !important; border: 1px solid #FF8C00; }}

    /* Cadre Total Caisse */
    .total-frame {{
        border: 4px solid #FF8C00; background: #000; padding: 20px;
        border-radius: 15px; color: #00FF00; font-size: 30px; font-weight: bold;
        margin: 15px 0; text-align: center;
    }}

    /* Montre Digitale Accueil */
    .watch-box {{
        background: #1a1a1a; color: #FF8C00; padding: 20px 50px; border-radius: 15px;
        font-size: 32px; font-weight: bold; border: 3px solid #FF8C00;
        display: inline-block; box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }}

    /* Facture Stylisée */
    .invoice-box {{
        background: white; color: black; padding: 30px; border: 1px solid #ddd;
        max-width: 800px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    .sig-area {{ margin-top: 50px; text-align: right; font-style: italic; border-top: 1px solid #000; display: inline-block; width: 200px; float: right; }}

    /* Mobile First */
    @media (max-width: 768px) {{
        .total-frame {{ font-size: 22px; }}
        .watch-box {{ font-size: 20px; padding: 10px 20px; }}
        .marquee-text {{ font-size: 14px; }}
    }}
    </style>
    
    <div class="marquee-container">
        <div class="marquee-text">📢 {C_MSG} | 🏢 {C_NOM} | 💹 TAUX DU JOUR: {C_TX} CDF/USD | DATE: {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    <div style="margin-top: 70px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SYSTÈME D'AUTHENTIFICATION & INSCRIPTION
# ==============================================================================
if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.title("CONNEXION BALIKA")
        
        tab_log, tab_reg = st.tabs(["🔑 SE CONNECTER", "📝 CRÉER UN COMPTE"])
        
        with tab_log:
            u_in = st.text_input("Identifiant Utilisateur").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER L'ACCÈS"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if res and make_hashes(p_in) == res[0][0]:
                    st.session_state.update({
                        'auth': True, 'user': u_in, 'role': res[0][1], 'ent_id': res[0][2]
                    })
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

        with tab_reg:
            with st.form("form_reg"):
                st.subheader("Nouvel Abonnement")
                r_ent = st.text_input("Nom de votre Entreprise (Boutique, Agence...)")
                r_tel = st.text_input("Téléphone Professionnel (WhatsApp)")
                r_adr = st.text_input("Adresse Physique")
                r_user = st.text_input("Identifiant de Connexion").lower().strip()
                r_pass = st.text_input("Mot de passe sécurisé", type="password")
                
                if st.form_submit_button("ACTIVER MON ERP MAINTENANT"):
                    if r_ent and r_user and r_pass:
                        # Vérifier si l'user existe
                        check = run_db("SELECT * FROM users WHERE username=?", (r_user,), fetch=True)
                        if not check:
                            new_eid = f"E-{random.randint(10000, 99999)}"
                            # Créer l'utilisateur
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                                   (r_user, make_hashes(r_pass), "ADMIN", new_eid, r_tel))
                            # Créer la config
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, adresse, taux, message, date_inscription) VALUES (?,?,?,?,?,?,?)", 
                                   (new_eid, r_ent.upper(), r_tel, r_adr, 2850.0, "Bienvenue dans votre nouvel espace", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Compte activé ! Connectez-vous dans l'onglet voisin.")
                        else:
                            st.warning("Cet identifiant est déjà pris.")
                    else:
                        st.error("Veuillez remplir tous les champs.")
    st.stop()

# --- VARIABLES DE SESSION RAPIDES ---
ENT_ID = st.session_state.ent_id
ROLE = st.session_state.role
USER = st.session_state.user

# ==============================================================================
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:
    # Photo de profil
    u_pic = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if u_pic and u_pic[0][0]:
        st.image(u_pic[0][0], width=120)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.info(f"Rôle: {ROLE}")
    st.write("---")
    
    # Menus selon les rôles
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 GESTION ABONNÉS", "📊 RAPPORTS HQ", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # VENDEUR
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. PAGE D'ACCUEIL (DASHBOARD)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"🏢 {C_NOM}")
    
    # Watch and Date
    st.markdown(f"""
        <center>
            <div class="watch-box">
                {datetime.now().strftime('%H:%M:%S')}<br>
                <span style="font-size:18px;">{datetime.now().strftime('%d %B %Y')}</span>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    
    v_total = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    col1.metric("CHIFFRE D'AFFAIRES", f"{v_total:,.2f} $")
    
    d_total = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    col2.metric("DETTES À RECOUVRER", f"{d_total:,.2f} $", delta_color="inverse")
    
    s_count = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    col3.metric("ARTICLES EN STOCK", s_count)

# ==============================================================================
# 7. SUPER-ADMIN : GESTION DES ABONNÉS
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 ADMINISTRATION GÉNÉRALE (SaaS)")
    
    # Contrôle du message défilant global
    with st.expander("📢 ÉDITER LE MESSAGE DÉFILANT"):
        new_msg = st.text_area("Message à diffuser sur tous les écrans", value=C_MSG)
        if st.button("DIFFUSER LE MESSAGE"):
            run_db("UPDATE config SET message=?", (new_msg,))
            st.success("Message mis à jour avec succès.")
            st.rerun()

    st.write("---")
    st.subheader("Liste des Entreprises Clientes")
    
    clients = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, adresse FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    if not clients:
        st.info("Aucun client enregistré pour le moment.")
    else:
        for eid, ename, etel, estat, edate, eadr in clients:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.write(f"🏢 **{ename}**")
                    st.write(f"📞 {etel} | 📍 {eadr}")
                    st.write(f"📅 Inscription : {edate} | ID: `{eid}`")
                
                with c2:
                    st.write(f"Statut : **{estat}**")
                    if st.button("⏸️ PAUSE / ▶️ PLAY", key=f"ps_{eid}"):
                        new_s = "PAUSE" if estat == "ACTIF" else "ACTIF"
                        run_db("UPDATE config SET status=? WHERE ent_id=?", (new_s, eid))
                        st.rerun()
                
                with c3:
                    if st.button("🗑️ SUPPRIMER", key=f"del_{eid}"):
                        # Suppression sécurisée de tout le compte
                        run_db("DELETE FROM config WHERE ent_id=?", (eid,))
                        run_db("DELETE FROM users WHERE ent_id=?", (eid,))
                        run_db("DELETE FROM produits WHERE ent_id=?", (eid,))
                        st.warning(f"Compte {ename} supprimé.")
                        st.rerun()

# ==============================================================================
# 8. GESTION DU STOCK (PRODUITS)
# ==============================================================================
elif st.session_state.page == "STOCK" and ROLE != "VENDEUR":
    st.header("📦 GESTION DU STOCK")
    
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("add_product"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            name = c1.text_input("Désignation du produit")
            qty = c2.number_input("Quantité Initiale", min_value=1, value=10)
            price = c3.number_input("Prix de Vente", min_value=0.0)
            curr = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                if name:
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                           (name.upper(), qty, price, curr, ENT_ID))
                    st.success("Produit ajouté !")
                    st.rerun()

    st.write("---")
    # Liste des produits
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    
    if prods:
        df_p = pd.DataFrame(prods, columns=["ID", "Désignation", "Stock", "Prix", "Devise"])
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        
        st.subheader("Modifier ou Supprimer")
        for pid, p_nom, p_stk, p_px, p_dv in prods:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])
                col1.write(f"**{p_nom}**")
                col2.write(f"En stock: {p_stk}")
                new_px = col3.number_input("Prix", value=float(p_px), key=f"px_{pid}")
                
                if col4.button("💾 SAUVER", key=f"sv_{pid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, pid))
                    st.rerun()
                
                if col5.button("🗑️", key=f"rm_{pid}"):
                    run_db("DELETE FROM produits WHERE id=?", (pid,))
                    st.rerun()

# ==============================================================================
# 9. TERMINAL DE VENTE (CAISSE)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        
        c1, c2 = st.columns(2)
        v_devise = c1.selectbox("Devise de facturation", ["USD", "CDF"])
        v_format = c2.selectbox("Format d'impression", ["80mm (Ticket)", "A4 (Facture)"])
        
        # Sélection des produits
        prods_list = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_data = {r[0]: {"prix": r[1], "stk": r[2], "dv": r[3]} for r in prods_list}
        
        col_sel, col_btn = st.columns([3, 1])
        choix = col_sel.selectbox("Chercher un article", ["---"] + list(p_data.keys()))
        
        if col_btn.button("➕ AJOUTER AU PANIER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            st.subheader("Détails du Panier")
            total_panier = 0.0
            liste_ventes = []

            for art, qte in list(st.session_state.panier.items()):
                # Conversion devise si nécessaire
                px_orig = p_data[art]["prix"]
                dv_orig = p_data[art]["dv"]
                
                if dv_orig == "USD" and v_devise == "CDF": px_calc = px_orig * C_TX
                elif dv_orig == "CDF" and v_devise == "USD": px_calc = px_orig / C_TX
                else: px_calc = px_orig
                
                sous_total = px_calc * qte
                total_panier += sous_total
                liste_ventes.append({"art": art, "qte": qte, "pu": px_calc, "st": sous_total})
                
                ca, cb, cc = st.columns([3, 1, 0.5])
                ca.write(f"**{art}**")
                st.session_state.panier[art] = cb.number_input("Qté", 1, p_data[art]["stk"], value=qte, key=f"qte_{art}")
                if cc.button("❌", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            # CADRE TOTAL
            st.markdown(f'<div class="total-frame">MONTANT NET À PAYER : {total_panier:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_paye = st.number_input(f"MONTANT REÇU ({v_devise})", min_value=0.0, value=float(total_panier))
            
            if st.button("💾 FINALISER LA VENTE & IMPRIMER"):
                ref = f"FAC-{random.randint(1000, 9999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = total_panier - c_paye
                
                # Enregistrer Vente
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                       (ref, c_nom, total_panier, c_paye, reste, v_devise, dt, USER, ENT_ID, json.dumps(liste_ventes)))
                
                # Gérer Dette
                if reste > 0.1:
                    hist = [{"date": dt, "paye": c_paye}]
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                           (c_nom, reste, v_devise, ref, ENT_ID, json.dumps(hist)))
                
                # Décrémenter Stock
                for item in liste_ventes:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                           (item['qte'], item['art'], ENT_ID))
                
                # Préparer Facture
                st.session_state.last_fac = {
                    "ref": ref, "client": c_nom, "total": total_panier, "paye": c_paye, 
                    "reste": reste, "devise": v_devise, "items": liste_ventes, "date": dt, "format": v_format
                }
                st.session_state.panier = {}
                st.rerun()
    else:
        # AFFICHAGE DE LA FACTURE POUR IMPRESSION
        f = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        style_fac = "width:350px; font-size:13px;" if f['format'] == "80mm (Ticket)" else "width:100%; font-size:16px;"
        
        html_fac = f"""
        <div class="invoice-box" style="{style_fac}">
            <center>
                <h2 style="margin:0;">{C_NOM}</h2>
                <p>{C_ADR}<br>Tél: {C_TEL}</p>
                <hr>
                <p><b>FACTURE N° {f['ref']}</b><br>
                Date: {f['date']}<br>
                Client: {f['client']}</p>
            </center>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="border-bottom: 2px solid #000;">
                    <th align="left">Article</th>
                    <th align="center">Qté</th>
                    <th align="right">Total</th>
                </tr>
                {" ".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">TOTAL : {f['total']:,.2f} {f['devise']}</h3>
            <p align="right">Payé : {f['paye']:,.2f}<br>Reste à payer : {f['reste']:,.2f}</p>
            <div style="margin-top:30px;">
                <p style="font-size:10px;">Vendeur: {USER.upper()}<br>Merci de votre confiance !</p>
                <div class="sig-area">Signature et Cachet</div>
            </div>
        </div>
        """
        st.markdown(html_fac, unsafe_allow_html=True)
        
        # Boutons d'actions
        c_p1, c_p2, c_p3 = st.columns(3)
        c_p1.button("🖨️ IMPRIMER / PDF", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        
        # Partage WhatsApp
        txt_share = f"Facture {f['ref']} de {C_NOM}. Montant: {f['total']} {f['devise']}. Merci !"
        c_p2.markdown(f'<a href="https://wa.me/?text={txt_share}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:8px; font-weight:bold;">📲 PARTAGER WHATSAPP</button></a>', unsafe_allow_html=True)
        c_p3.info("Pour sauvegarder en PDF, choisissez 'Imprimer' puis 'Enregistrer au format PDF'.")

# ==============================================================================
# 10. GESTION DES DETTES (PAIEMENTS PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 RECOUVREMENT DES DETTES")
    
    dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.01", (ENT_ID,), fetch=True)
    
    if not dettes:
        st.success("Félicitations ! Aucune dette en cours.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in dettes:
            with st.expander(f"🔴 {dcl} - {dmt:,.2f} {ddv} (Ref: {drf})"):
                # Affichage historique
                h_list = json.loads(dhi)
                st.write("**Historique des paiements :**")
                st.table(pd.DataFrame(h_list))
                
                # Nouveau versement
                nv_paye = st.number_input(f"Montant à verser ({ddv})", min_value=0.0, max_value=float(dmt), key=f"pay_{did}")
                
                if st.button("ENREGISTRER LE VERSEMENT", key=f"btn_{did}"):
                    nouveau_reste = dmt - nv_paye
                    h_list.append({"date": datetime.now().strftime("%d/%m/%Y"), "paye": nv_paye})
                    
                    if nouveau_reste <= 0.01:
                        # Dette terminée
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                        st.success(f"Dette de {dcl} totalement soldée !")
                    else:
                        run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nouveau_reste, json.dumps(h_list), did))
                    
                    # Mise à jour de la vente originale
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (nv_paye, nv_paye, drf, ENT_ID))
                    st.rerun()

# ==============================================================================
# 11. MON PROFIL (MODIFICATIONS)
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE")
    
    # Charger infos
    u_info = run_db("SELECT full_name, telephone, photo FROM users WHERE username=?", (USER,), fetch=True)[0]
    
    with st.container(border=True):
        st.subheader("Informations Personnelles")
        new_fn = st.text_input("Nom Complet", value=u_info[0] if u_info[0] else "")
        new_tel = st.text_input("Téléphone Personnel", value=u_info[1] if u_info[1] else "")
        new_img = st.file_uploader("Changer ma photo de profil", type=["jpg", "png", "jpeg"])
        
        st.write("---")
        st.subheader("Sécurité du Compte")
        new_username = st.text_input("Nouvel Identifiant", value=USER)
        p1, p2 = st.columns(2)
        new_pass = p1.text_input("Nouveau mot de passe", type="password")
        conf_pass = p2.text_input("Confirmer le mot de passe", type="password")
        
        if st.button("METTRE À JOUR MON PROFIL"):
            # Update photo si présente
            if new_img:
                run_db("UPDATE users SET photo=? WHERE username=?", (new_img.getvalue(), USER))
            
            # Update mot de passe si rempli
            if new_pass:
                if new_pass == conf_pass:
                    run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_pass), USER))
                else:
                    st.error("Les mots de passe ne correspondent pas.")
            
            # Update infos
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (new_fn, new_tel, USER))
            
            # Update Identifiant
            if new_username != USER:
                try:
                    run_db("UPDATE users SET username=? WHERE username=?", (new_username, USER))
                    st.session_state.user = new_username
                except:
                    st.error("Cet identifiant est déjà utilisé.")
            
            st.success("Profil mis à jour !")
            st.rerun()

# ==============================================================================
# 12. RÉGLAGES ENTREPRISE & VENDEURS
# ==============================================================================
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ PARAMÈTRES DE L'ENTREPRISE")
    
    tab_inf, tab_vend = st.tabs(["🏢 INFOS BOUTIQUE", "👥 GESTION DES VENDEURS"])
    
    with tab_inf:
        with st.form("set_config"):
            c_n = st.text_input("Nom de l'Entreprise", value=C_NOM)
            c_a = st.text_input("Adresse Physique", value=C_ADR)
            c_t = st.text_input("Téléphone", value=C_TEL)
            c_x = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TX)
            c_m = st.text_area("Message de bienvenue (Marquee)", value=C_MSG)
            c_e = st.text_area("En-tête de Facture", value=C_ENTETE)
            
            if st.form_submit_button("SAUVEGARDER LES RÉGLAGES"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, entete_fac=? WHERE ent_id=?", 
                       (c_n.upper(), c_a, c_t, c_x, c_m, c_e, ENT_ID))
                st.success("Configuration enregistrée !")
                st.rerun()

    with tab_vend:
        st.subheader("Ajouter un Vendeur")
        with st.form("add_v"):
            v_u = st.text_input("Identifiant du vendeur").lower().strip()
            v_p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                if v_u and v_p:
                    run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'VENDEUR', ?)", 
                           (v_u, make_hashes(v_p), ENT_ID))
                    st.success(f"Vendeur {v_u} ajouté !")
                st.rerun()
        
        st.write("---")
        st.subheader("Vendeurs Actuels")
        vendeurs = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
        for v in vendeurs:
            col_v1, col_v2 = st.columns([3, 1])
            col_v1.write(f"👤 {v[0].upper()}")
            if col_v2.button("🗑️", key=f"del_v_{v[0]}"):
                run_db("DELETE FROM users WHERE username=?", (v[0],))
                st.rerun()

# ==============================================================================
# 13. RAPPORTS DE VENTES
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.header("📊 JOURNAL DES VENTES")
    
    ventes_data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    
    if ventes_data:
        df_v = pd.DataFrame(ventes_data, columns=["Date", "Référence", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
        st.dataframe(df_v, use_container_width=True, hide_index=True)
        
        st.write("---")
        c_r1, c_r2 = st.columns(2)
        if c_r1.button("🖨️ IMPRIMER LE JOURNAL"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        
        # Export CSV
        csv = df_v.to_csv(index=False).encode('utf-8')
        c_r2.download_button("📥 TÉLÉCHARGER CSV", data=csv, file_name=f"rapport_ventes_{ENT_ID}.csv", mime='text/csv')
    else:
        st.warning("Aucune vente enregistrée.")
