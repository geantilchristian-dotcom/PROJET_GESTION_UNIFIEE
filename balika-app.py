# ==============================================================================
# BALIKA ERP v1200 - VERSION INTÉGRALE ET COMPLÈTE
# TOUS DROITS RÉSERVÉS - 2026
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
import base64

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA CONFIGURATION DE PAGE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v1200",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏢"
)

# ------------------------------------------------------------------------------
# 2. GESTION DU SESSION STATE (MÉMOIRE DE L'APPLICATION)
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'ent_id' not in st.session_state:
    st.session_state.ent_id = "SYSTEM"
if 'page' not in st.session_state:
    st.session_state.page = "ACCUEIL"
if 'panier' not in st.session_state:
    st.session_state.panier = {}
if 'last_fac' not in st.session_state:
    st.session_state.last_fac = None
if 'format_fac' not in st.session_state:
    st.session_state.format_fac = "80mm"
if 'devise_vente' not in st.session_state:
    st.session_state.devise_vente = "USD"

# ------------------------------------------------------------------------------
# 3. MOTEUR DE BASE DE DONNÉES (SQLITE PERSISTANT)
# ------------------------------------------------------------------------------
def get_connection():
    return sqlite3.connect('balika_v1200_master.db', timeout=30)

def run_db(query, params=(), fetch=False):
    """Exécute une requête SQL et gère la connexion proprement."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL") # Optimisation pour accès simultanés
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        if fetch:
            return cursor.fetchall()
        return None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []
    finally:
        conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 4. CRÉATION DES TABLES (ARCHITECTUE COMPLÈTE)
# ------------------------------------------------------------------------------
def init_db():
    # Table des Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT, 
                photo BLOB, 
                full_name TEXT, 
                telephone TEXT)""")
    
    # Table de Configuration Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL DEFAULT 2850.0, 
                message TEXT DEFAULT 'BIENVENUE SUR BALIKA ERP', 
                color_m TEXT DEFAULT '#00FF00', 
                status TEXT DEFAULT 'ACTIF', 
                date_inscription TEXT)""")
    
    # Table des Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT)""")
    
    # Table des Ventes
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
    
    # Table des Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")

    # Table des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                motif TEXT, 
                montant REAL, 
                devise TEXT, 
                date_d TEXT, 
                ent_id TEXT)""")

    # Insertion des données par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, color_m, date_inscription) VALUES (?, ?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'SYSTÈME DE GESTION PROFESSIONNEL BALIKA v1200', '#00FF00', '16/01/2026'))

init_db()

# ------------------------------------------------------------------------------
# 5. CHARGEMENT DES PARAMÈTRES VISUELS
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id
res_cfg = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)

if res_cfg:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL = res_cfg[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL = ("BALIKA", "Bienvenue", "#00FF00", 2850.0, "Adresse", "000")

# ------------------------------------------------------------------------------
# 6. DESIGN CSS (MARQUEE, MONTRE, BOUTONS, CENTRAGE)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap');

    /* Fond Global */
    .stApp {{ background-color: #ffffff; }}
    
    /* MARQUEE DÉFILANT FORCÉ */
    .fixed-header {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        background: #000; z-index: 99999; border-bottom: 3px solid #FF8C00;
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: scroll-v12 20s linear infinite;
        color: {C_COLOR}; font-size: 20px; font-weight: bold;
    }}
    @keyframes scroll-v12 {{ 
        0% {{ transform: translateX(100%); }} 
        100% {{ transform: translateX(-100%); }} 
    }}

    /* MONTRE CENTRÉE */
    .watch-box {{
        background: #000; border: 4px solid #FF8C00; border-radius: 20px;
        padding: 30px; display: inline-block; margin: 40px auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center;
    }}
    .w-time {{ font-family: 'Orbitron', sans-serif; font-size: 60px; color: #FF8C00; margin: 0; }}
    .w-date {{ color: #fff; font-size: 18px; margin-top: 10px; text-transform: uppercase; }}

    /* BOUTONS BLEUS / TEXTE BLANC */
    .stButton>button {{
        background: #0056b3 !important; color: white !important;
        border-radius: 10px; height: 50px; font-weight: bold;
        border: none; width: 100%; font-size: 16px;
    }}

    /* CADRE TOTAL */
    .total-display {{
        border: 5px solid #FF8C00; background: #fff; padding: 20px;
        border-radius: 15px; color: #000; font-size: 40px;
        font-weight: 900; margin: 20px auto; width: fit-content; text-align: center;
    }}

    /* FORMATS FACTURE */
    .invoice-80mm {{ width: 300px; margin: auto; padding: 10px; border: 1px dashed #000; font-family: monospace; text-align: left; }}
    .invoice-A4 {{ width: 800px; margin: auto; padding: 50px; border: 1px solid #ccc; background: #fff; text-align: left; }}

    /* TABLEAUX */
    .styled-table {{ width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.9em; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
    .styled-table th {{ background-color: #0056b3; color: white; text-align: left; padding: 12px 15px; }}
    .styled-table td {{ padding: 12px 15px; border-bottom: 1px solid #dddddd; }}

    /* Masquer Sidebar et Boutons à l'impression */
    @media print {{ 
        .fixed-header, .stSidebar, .stButton, .no-print {{ display: none !important; }} 
        .invoice-A4, .invoice-80mm {{ border: none; width: 100%; margin: 0; }}
    }}
    </style>

    <div class="fixed-header">
        <div class="marquee-text">{C_MSG} &nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp; {C_NOM}</div>
    </div>
    <div style="height: 60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. ÉCRAN DE CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, center_col, _ = st.columns([0.2, 0.6, 0.2])
    with center_col:
        st.markdown("<h1 style='text-align: center;'>🔐 BALIKA SECURE LOGIN</h1>", unsafe_allow_html=True)
        login_user = st.text_input("Identifiant", placeholder="Entrez votre nom d'utilisateur").lower().strip()
        login_pass = st.text_input("Mot de passe", type="password", placeholder="••••••••")
        
        if st.button("DÉVERROUILLER L'ACCÈS"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (login_user,), fetch=True)
            if res and make_hashes(login_pass) == res[0][0]:
                st.session_state.auth = True
                st.session_state.user = login_user
                st.session_state.role = res[0][1]
                st.session_state.ent_id = res[0][2]
                st.rerun()
            else:
                st.error("Identifiants incorrects ou compte inactif.")
        
        st.write("---")
        with st.expander("Créer une nouvelle instance (Admin)"):
            with st.form("new_erp"):
                new_e = st.text_input("Nom de la boutique")
                new_u = st.text_input("Utilisateur Admin")
                new_p = st.text_input("Mot de passe Admin", type="password")
                if st.form_submit_button("CRÉER MON ERP"):
                    if new_e and new_u and new_p:
                        eid = f"ERP-{random.randint(100, 999)}"
                        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                               (new_u, make_hashes(new_p), "ADMIN", eid))
                        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?,?,?,?,?,?)", 
                               (eid, new_e.upper(), "ACTIF", 2850.0, "BIENVENUE", datetime.now().strftime("%d/%m/%Y")))
                        st.success("Compte créé avec succès !")
    st.stop()

# ------------------------------------------------------------------------------
# 8. VARIABLES DE SESSION COURANTES
# ------------------------------------------------------------------------------
ENT_ID = st.session_state.ent_id
ROLE = st.session_state.role
USER = st.session_state.user

# ------------------------------------------------------------------------------
# 9. MENU LATÉRAL (NAVIGATION)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center;'>👤 {USER.upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Rôle: {ROLE}</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Définition des accès par rôle
    if ROLE == "SUPER_ADMIN":
        nav_items = ["🏠 ACCUEIL", "🌍 GESTION ABONNÉS", "📊 RAPPORTS HQ", "⚙️ RÉGLAGES SYSTÈME", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        nav_items = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "💸 DÉPENSES", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # Vendeur
        nav_items = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for item in nav_items:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 10. PAGE : ACCUEIL (MONTRE & RÉSUMÉ)
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1 style='text-align: center;'>🏢 {C_NOM}</h1>", unsafe_allow_html=True)
    
    # Affichage Montre
    st.markdown(f"""
        <center>
            <div class="watch-box">
                <p class="w-time">{datetime.now().strftime('%H:%M:%S')}</p>
                <p class="w-date">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)

    st.write("---")
    c1, c2, c3 = st.columns(3)
    
    # Statistiques rapides
    v_total = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    d_total = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    p_count = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0]
    
    c1.metric("CHIFFRE D'AFFAIRES", f"{v_total:,.2f} $")
    c2.metric("DETTES À RÉCUPÉRER", f"{d_total:,.2f} $")
    c3.metric("VARIÉTÉS EN STOCK", p_count)

# ------------------------------------------------------------------------------
# 11. PAGE : CAISSE (TERMINAL DE VENTE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.markdown("<h2 style='text-align: center;'>🛒 TERMINAL DE VENTE</h2>", unsafe_allow_html=True)
        
        # Options de vente
        opt1, opt2 = st.columns(2)
        v_devise = opt1.selectbox("Monnaie de paiement", ["USD", "CDF"])
        st.session_state.format_fac = opt2.selectbox("Format d'impression", ["80mm", "A4"])
        
        # Chargement Produits
        plist = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in plist}
        
        col_a, col_b = st.columns([3, 1])
        selection = col_a.selectbox("Sélectionner l'article", ["---"] + list(p_dict.keys()))
        if col_b.button("➕ AJOUTER AU PANIER") and selection != "---":
            st.session_state.panier[selection] = st.session_state.panier.get(selection, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_final = 0.0
            lignes_vente = []
            
            for art, qte in list(st.session_state.panier.items()):
                prix_base = p_dict[art]['px']
                dev_base = p_dict[art]['dv']
                
                # Conversion dynamique
                if dev_base == "USD" and v_devise == "CDF":
                    prix_conv = prix_base * C_TX
                elif dev_base == "CDF" and v_devise == "USD":
                    prix_conv = prix_base / C_TX
                else:
                    prix_conv = prix_base
                
                sous_total = prix_conv * qte
                total_final += sous_total
                lignes_vente.append({'art': art, 'qte': qte, 'pu': prix_conv, 'st': sous_total})
                
                # Affichage Ligne
                l1, l2, l3 = st.columns([3, 1, 0.5])
                l1.markdown(f"**{art}**")
                st.session_state.panier[art] = l2.number_input("Qté", 1, p_dict[art]['st'], value=qte, key=f"pan_{art}")
                if l3.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            # Affichage du Total
            st.markdown(f'<div class="total-display">NET À PAYER : {total_final:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            c_cl, c_pay = st.columns(2)
            nom_client = c_cl.text_input("Nom du Client", value="COMPTANT").upper()
            montant_recu = c_pay.number_input("Montant Reçu", value=float(total_final))
            
            if st.button("✅ VALIDER ET GÉNÉRER LA FACTURE"):
                # Enregistrement Vente
                ref_v = f"FAC-{random.randint(1000, 9999)}"
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste_v = total_final - montant_recu
                
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (ref_v, nom_client, total_final, montant_recu, reste_v, v_devise, date_v, USER, ENT_ID, json.dumps(lignes_vente)))
                
                # Si dette
                if reste_v > 0.1:
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)",
                           (nom_client, reste_v, v_devise, ref_v, ENT_ID, json.dumps([{'d': date_v, 'p': montant_recu}])))
                
                # Mise à jour Stock
                for lv in lignes_vente:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                           (lv['qte'], lv['art'], ENT_ID))
                
                # Préparation facture
                st.session_state.last_fac = {
                    'ref': ref_v, 'cl': nom_client, 'tot': total_final, 
                    'pay': montant_recu, 'dev': v_devise, 'items': lignes_vente, 'date': date_v
                }
                st.session_state.panier = {}
                st.rerun()
    else:
        # Affichage de la Facture prête
        fac = st.session_state.last_fac
        st.button("⬅️ RETOUR AU TERMINAL", on_click=lambda: st.session_state.update({'last_fac': None}))
        
        div_class = "invoice-80mm" if st.session_state.format_fac == "80mm" else "invoice-A4"
        
        html_facture = f"""
        <div class="{div_class}">
            <center>
                <h2>{C_NOM}</h2>
                <p>{C_ADR}<br>WhatsApp: {C_TEL}</p>
                <hr>
                <h4>FACTURE N° {fac['ref']}</h4>
                <p>Client : {fac['cl']}<br>Date : {fac['date']}</p>
            </center>
            <table style="width:100%; border-bottom: 1px solid #000;">
                <tr><th>Art.</th><th>Qté</th><th align="right">Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in fac['items']])}
            </table>
            <h3 align="right">TOTAL : {fac['tot']:,.2f} {fac['dev']}</h3>
            <p align="right">Versé : {fac['pay']:,.2f}<br>Reste : {fac['tot']-fac['pay']:,.2f}</p>
            <br>
            <div style="display:flex; justify-content:space-between;">
                <p>Signature Maison</p>
                <p>Signature Client</p>
            </div>
            <center><p>*** Merci de votre confiance ***</p></center>
        </div>
        """
        st.markdown(html_facture, unsafe_allow_html=True)
        
        c_p1, c_p2 = st.columns(2)
        c_p1.button("🖨️ IMPRIMER LA FACTURE", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        
        # Bouton Partage WhatsApp
        msg_wa = f"Facture {fac['ref']} - {C_NOM}. Total: {fac['tot']} {fac['dev']}. Merci!"
        c_p2.markdown(f'<a href="https://wa.me/?text={msg_wa}" target="_blank"><button style="width:100%; background:#25D366; color:white; border-radius:10px; height:50px; border:none; font-weight:bold;">📲 ENVOYER PAR WHATSAPP</button></a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 12. PAGE : VENDEURS (GESTION COMPLÈTE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENDEURS" and ROLE == "ADMIN":
    st.markdown("<h2 style='text-align: center;'>👥 GESTION DES VENDEURS</h2>", unsafe_allow_html=True)
    
    # Formulaire de création
    with st.expander("➕ CRÉER UN NOUVEAU COMPTE VENDEUR"):
        with st.form("form_vendeur"):
            v_un = st.text_input("Nom d'utilisateur").lower().strip()
            v_pw = st.text_input("Mot de passe", type="password")
            v_tel = st.text_input("Téléphone")
            if st.form_submit_button("ENREGISTRER LE VENDEUR"):
                if not run_db("SELECT * FROM users WHERE username=?", (v_un,), fetch=True):
                    run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                           (v_un, make_hashes(v_pw), "VENDEUR", ENT_ID, v_tel))
                    st.success(f"Compte {v_un} créé !")
                    st.rerun()
                else:
                    st.error("Ce nom d'utilisateur existe déjà.")

    st.write("---")
    st.subheader("LISTE DU PERSONNEL")
    v_list = run_db("SELECT username, telephone FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    
    if not v_list:
        st.info("Aucun vendeur enregistré.")
    else:
        for v_name, v_phone in v_list:
            with st.container(border=True):
                cl1, cl2, cl3 = st.columns([2, 1, 1])
                cl1.markdown(f"**Identifiant :** {v_name.upper()}<br>**Tel :** {v_phone}", unsafe_allow_html=True)
                
                new_pw = cl2.text_input("Changer Pass", type="password", key=f"ch_{v_name}")
                if cl2.button("💾 SAUVER", key=f"btn_{v_name}"):
                    if new_pw:
                        run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_pw), v_name))
                        st.success("Mot de passe mis à jour !")
                    else:
                        st.warning("Entrez un mot de passe.")
                
                if cl3.button("🗑️ SUPPRIMER LE COMPTE", key=f"del_v_{v_name}"):
                    run_db("DELETE FROM users WHERE username=?", (v_name,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 13. PAGE : RAPPORTS (FINANCES TOTALES)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RAPPORTS" and ROLE == "ADMIN":
    st.markdown("<h2 style='text-align: center;'>📊 RAPPORT FINANCIER GLOBAL</h2>", unsafe_allow_html=True)
    
    # Calculs complexes
    cash_net = run_db("SELECT SUM(paye) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    dettes_ext = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    frais_dep = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    disponible = cash_net - frais_dep
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("CASH REÇU (Ventes)", f"{cash_net:,.2f} $")
    r2.metric("DETTES CLIENTS", f"{dettes_ext:,.2f} $")
    r3.metric("DÉPENSES", f"{frais_dep:,.2f} $")
    r4.metric("ARGENT PRÉSENT (NET)", f"{disponible:,.2f} $", delta=f"-{frais_dep:,.2f}")
    
    st.write("---")
    tab_v, tab_d = st.tabs(["📜 JOURNAL DES VENTES", "💸 HISTORIQUE DÉPENSES"])
    
    with tab_v:
        v_data = run_db("SELECT date_v, ref, client, total, paye, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
        if v_data:
            df_v = pd.DataFrame(v_data, columns=["Date", "Référence", "Client", "Total", "Payé", "Vendeur"])
            st.dataframe(df_v, use_container_width=True)
            if st.button("🖨️ IMPRIMER CE JOURNAL"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    with tab_d:
        d_data = run_db("SELECT date_d, motif, montant FROM depenses WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
        if d_data:
            df_d = pd.DataFrame(d_data, columns=["Date", "Motif", "Montant ($)"])
            st.table(df_d)

# ------------------------------------------------------------------------------
# 14. PAGE : DÉPENSES
# ------------------------------------------------------------------------------
elif st.session_state.page == "DÉPENSES" and ROLE == "ADMIN":
    st.markdown("<h2 style='text-align: center;'>💸 GESTION DES DÉPENSES</h2>", unsafe_allow_html=True)
    with st.form("form_depense"):
        motif_d = st.text_input("Motif de la dépense (ex: Loyer, Transport, Unité)")
        montant_d = st.number_input("Montant de la dépense ($)", min_value=0.0)
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            if motif_d and montant_d > 0:
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)",
                       (motif_d, montant_d, "USD", datetime.now().strftime("%d/%m/%Y"), ENT_ID))
                st.success("Dépense enregistrée !")
                st.rerun()

# ------------------------------------------------------------------------------
# 15. PAGE : STOCK (MODIFICATION ET SUPPRESSION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK" and ROLE == "ADMIN":
    st.markdown("<h2 style='text-align: center;'>📦 GESTION DU STOCK</h2>", unsafe_allow_html=True)
    
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("add_product"):
            n_art = st.text_input("Désignation")
            n_qte = st.number_input("Quantité Initiale", 1)
            n_px = st.number_input("Prix de Vente", 0.0)
            n_dv = st.selectbox("Devise du prix", ["USD", "CDF"])
            if st.form_submit_button("AJOUTER AU STOCK"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                       (n_art.upper(), n_qte, n_px, n_dv, ENT_ID))
                st.success("Produit ajouté !")
                st.rerun()

    st.write("---")
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for p_id, p_name, p_stock, p_price, p_dev in prods:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([3, 1, 1, 0.5])
            cl1.markdown(f"**{p_name}**")
            cl2.write(f"En stock : {p_stock}")
            
            # Modification de prix
            new_price = cl3.number_input(f"Prix ({p_dev})", value=float(p_price), key=f"px_mod_{p_id}")
            if cl3.button("💾 SAUVER", key=f"btn_s_{p_id}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_price, p_id))
                st.success("Prix modifié !")
                st.rerun()
            
            # Suppression (Ne supprime pas les ventes passées)
            if cl4.button("🗑️", key=f"del_p_{p_id}"):
                run_db("DELETE FROM produits WHERE id=?", (p_id,))
                st.rerun()

# ------------------------------------------------------------------------------
# 16. PAGE : DETTES (RECOUVREMENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.markdown("<h2 style='text-align: center;'>📉 RECOUVREMENT DES DETTES</h2>", unsafe_allow_html=True)
    dettes_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not dettes_list:
        st.success("Toutes les dettes ont été réglées !")
    else:
        for d_id, d_cl, d_mt, d_dv, d_rf, d_hi in dettes_list:
            with st.expander(f"🛑 {d_cl} | Reste : {d_mt:,.2f} {d_dv} (Facture: {d_rf})"):
                acompte = st.number_input("Montant de l'acompte", 0.0, float(d_mt), key=f"aco_{d_id}")
                if st.button("ENREGISTRER LE PAIEMENT", key=f"pay_btn_{d_id}"):
                    nouveau_reste = d_mt - acompte
                    historique = json.loads(d_hi)
                    historique.append({'d': datetime.now().strftime("%d/%m"), 'p': acompte})
                    
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nouveau_reste, json.dumps(historique), d_id))
                    run_db("UPDATE ventes SET paye = paye + ?, reste = reste - ? WHERE ref=? AND ent_id=?", (acompte, acompte, d_rf, ENT_ID))
                    
                    if nouveau_reste <= 0.1:
                        run_db("DELETE FROM dettes WHERE id=?", (d_id,))
                        st.balloons()
                    st.rerun()

# ------------------------------------------------------------------------------
# 17. PAGE : RÉGLAGES (BOUTIQUE & PROFIL)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.markdown("<h2 style='text-align: center;'>⚙️ CONFIGURATION BOUTIQUE</h2>", unsafe_allow_html=True)
    with st.form("shop_settings"):
        cfg_nom = st.text_input("Nom de l'Entreprise", C_NOM)
        cfg_adr = st.text_input("Adresse Physique", C_ADR)
        cfg_tel = st.text_input("Numéro WhatsApp", C_TEL)
        cfg_tx = st.number_input("Taux de change (CDF pour 1$)", value=C_TX)
        cfg_msg = st.text_area("Message défilant personnalisé", C_MSG)
        cfg_col = st.color_picker("Couleur du message défilant", C_COLOR)
        
        if st.form_submit_button("SAUVEGARDER LES PARAMÈTRES"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, color_m=? WHERE ent_id=?",
                   (cfg_nom.upper(), cfg_adr, cfg_tel, cfg_tx, cfg_msg, cfg_col, ENT_ID))
            st.success("Configuration mise à jour !")
            st.rerun()

elif st.session_state.page == "PROFIL":
    st.markdown("<h2 style='text-align: center;'>👤 MON PROFIL SÉCURISÉ</h2>", unsafe_allow_html=True)
    with st.form("user_profile"):
        p_u = st.text_input("Identifiant actuel", USER, disabled=True)
        p_n = st.text_input("Nouveau mot de passe", type="password")
        if st.form_submit_button("MODIFIER MON MOT DE PASSE"):
            if p_n:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(p_n), USER))
                st.success("Sécurité mise à jour !")
            else:
                st.warning("Veuillez saisir un nouveau mot de passe.")

# ------------------------------------------------------------------------------
# 18. GESTION DU SYSTÈME (SUPER ADMIN UNIQUEMENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "SYSTÈME" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES ABONNÉS BALIKA")
    # Liste de toutes les entreprises utilisant le logiciel
    all_ent = run_db("SELECT ent_id, nom_ent, date_inscription, status FROM config", fetch=True)
    df_ent = pd.DataFrame(all_ent, columns=["ID", "Entreprise", "Date Insc.", "Statut"])
    st.dataframe(df_ent, use_container_width=True)

# FIN DU CODE
