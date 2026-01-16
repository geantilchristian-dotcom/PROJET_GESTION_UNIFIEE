# ==============================================================================
# BALIKA ERP v2000 - L'ÉDITION MONOLITHIQUE (700+ LIGNES DE CODE)
# SYSTÈME DE GESTION INTÉGRÉ POUR COMMERCE ET SERVICES
# PROJET : BALIKA - DERNIÈRE MISE À JOUR : 16 JANVIER 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import hashlib
import json
import io
import time
import base64
import streamlit.components.v1 as components

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE L'ENVIRONNEMENT MOBILE & LUMINOSITÉ
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2000",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏢"
)

# ------------------------------------------------------------------------------
# 2. INITIALISATION DU SESSION STATE (MÉMOIRE GLOBALE)
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = ""
    st.session_state.role = ""
    st.session_state.ent_id = "SYSTEM"
    st.session_state.page = "ACCUEIL"
    st.session_state.panier = {}
    st.session_state.last_fac = None
    st.session_state.format_fac = "80mm"
    st.session_state.notifs = []
    st.session_state.edit_prod_id = None

# ------------------------------------------------------------------------------
# 3. MOTEUR DE BASE DE DONNÉES (SQLITE PERSISTANT AVEC LOGS)
# ------------------------------------------------------------------------------
DB_NAME = 'balika_master_v2000.db'

def run_db(query, params=(), fetch=False):
    """Exécute des requêtes SQL avec gestion des erreurs et reconnexion."""
    try:
        with sqlite3.connect(DB_NAME, timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")  # Mode haute performance
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"⚠️ Erreur Critique Base de données : {e}")
        return []

def make_hashes(password):
    """Hachage sécurisé des mots de passe."""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 4. ARCHITECTURE DES TABLES (SCHÉMA COMPLET)
# ------------------------------------------------------------------------------
def init_db_schema():
    # Table des Utilisateurs (Admin & Vendeurs)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT, 
                full_name TEXT, 
                telephone TEXT,
                date_crea TEXT)""")
    
    # Table de Configuration Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL DEFAULT 2850.0, 
                message TEXT, 
                color_m TEXT DEFAULT '#FFFF00', 
                status TEXT DEFAULT 'ACTIF', 
                date_insc TEXT,
                logo_b64 TEXT)""")
    
    # Table du Stock
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT,
                alerte_stock INTEGER DEFAULT 5)""")
    
    # Table des Ventes (Archives)
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
    
    # Table des Dettes (Suivi des paiements échelonnés)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT,
                statut TEXT DEFAULT 'NON_PAYE')""")

    # Table des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                motif TEXT, 
                montant REAL, 
                devise TEXT, 
                date_d TEXT, 
                vendeur TEXT,
                ent_id TEXT)""")

    # --- DONNÉES DE BASE SI VIDE ---
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM', 'ADMINISTRATEUR MAITRE', '000', '16/01/2026')", 
               (make_hashes("admin123"),))
        run_db("INSERT INTO config VALUES ('SYSTEM', 'BALIKA ERP HQ', 'RUE DE LA PAIX', '000', 2850.0, 'BIENVENUE SUR BALIKA ERP - LE SYSTÈME DE GESTION LE PLUS COMPLET', '#FFFF00', 'ACTIF', '16/01/2026', '')")

init_db_schema()

# ------------------------------------------------------------------------------
# 5. CHARGEMENT DES PARAMÈTRES ET STYLES CSS (HAUTE LUMINOSITÉ)
# ------------------------------------------------------------------------------
current_eid = st.session_state.ent_id
conf_res = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel FROM config WHERE ent_id=?", (current_eid,), fetch=True)

if conf_res:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL = conf_res[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL = ("BALIKA", "Bienvenue", "#FFFF00", 2850.0, "", "")

# --- STYLES CSS POUR TÉLÉPHONE (LUMINOSITÉ ET BOUTONS) ---
st.markdown(f"""
    <style>
    /* RESET GLOBAL */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
    }}

    /* AJUSTEMENT LUMINOSITÉ TÉLÉPHONE (CONTRASTE ÉLEVÉ) */
    .stApp {{
        filter: contrast(1.1) brightness(1.05);
    }}

    /* HEADER FIXE POUR MESSAGE DÉFILANT */
    .header-container {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        background: #000000; z-index: 999999; border-bottom: 2px solid #FF8C00;
        display: flex; align-items: center;
    }}

    /* BOUTONS STYLE MOBILE (GROS ET VISIBLES) */
    .stButton>button {{
        background: #0047AB !important; color: #ffffff !important;
        border-radius: 15px !important; height: 55px !important;
        font-size: 18px !important; font-weight: bold !important;
        border: none !important; box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        margin-bottom: 10px !important; width: 100% !important;
    }}

    /* MONTRE NUMÉRIQUE */
    .watch-card {{
        background: radial-gradient(circle, #222 0%, #000 100%);
        border: 4px solid #FF8C00; border-radius: 25px;
        padding: 40px; text-align: center; margin: 20px auto;
        max-width: 400px; box-shadow: 0 15px 35px rgba(0,0,0,0.5);
    }}
    .time-text {{ font-family: 'Courier New', monospace; font-size: 55px; color: #FF8C00; font-weight: bold; margin: 0; }}
    .date-text {{ color: #ffffff; font-size: 18px; text-transform: uppercase; letter-spacing: 2px; }}

    /* CADRE PRIX TOTAL (TRÈS VISIBLE) */
    .price-tag {{
        border: 6px solid #FF8C00; background: #ffffff; padding: 30px;
        border-radius: 20px; color: #000000; font-size: 45px;
        font-weight: 900; text-align: center; margin: 25px auto;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }}

    /* FACTURE */
    .invoice-container {{
        background: #ffffff; color: #000000; padding: 20px;
        border: 1px solid #000000; font-family: 'Courier New', monospace;
    }}

    /* SCROLLBARS */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: #f1f1f1; }}
    ::-webkit-scrollbar-thumb {{ background: #0047AB; border-radius: 10px; }}
    
    /* MASQUAGE À L'IMPRESSION */
    @media print {{
        .no-print, .stSidebar, .stButton, .header-container {{ display: none !important; }}
        .invoice-container {{ border: none; width: 100%; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- COMPOSANT MESSAGE DÉFILANT (FORCÉ) ---
def render_marquee():
    html_content = f"""
    <div style="background:#000; overflow:hidden; white-space:nowrap; width:100%; height:45px; display:flex; align-items:center; border-bottom:2px solid #FF8C00;">
        <p style="display:inline-block; padding-left:100%; font-family:Arial, sans-serif; font-weight:bold; font-size:22px; color:{C_COLOR}; animation:scroll-text 25s linear infinite; margin:0;">
            {C_MSG} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {C_NOM} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {C_MSG}
        </p>
    </div>
    <style>
        @keyframes scroll-text {{
            0% {{ transform: translate(0, 0); }}
            100% {{ transform: translate(-100%, 0); }}
        }}
    </style>
    """
    components.html(html_content, height=50)

render_marquee()

# ------------------------------------------------------------------------------
# 6. SYSTÈME D'AUTHENTIFICATION & SÉCURITÉ
# ------------------------------------------------------------------------------
def login_screen():
    _, center_col, _ = st.columns([0.1, 0.8, 0.1])
    with center_col:
        st.markdown("<h1 style='text-align: center; color:#0047AB;'>🏢 BALIKA ERP v2000</h1>", unsafe_allow_html=True)
        st.write("---")
        with st.form("login_form"):
            u = st.text_input("👤 Identifiant Utilisateur").lower().strip()
            p = st.text_input("🔑 Mot de passe", type="password")
            if st.form_submit_button("🔓 SE CONNECTER"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
                if res and make_hashes(p) == res[0][0]:
                    st.session_state.auth = True
                    st.session_state.user = u
                    st.session_state.role = res[0][1]
                    st.session_state.ent_id = res[0][2]
                    st.success("Connexion réussie !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Accès refusé. Vérifiez vos identifiants.")
        
        st.info("💡 Les codes par défaut sont admin / admin123")

if not st.session_state.auth:
    login_screen()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE DE NAVIGATION (MENU MOBILE)
# ------------------------------------------------------------------------------
ROLE = st.session_state.role
USER = st.session_state.user
ENT_ID = st.session_state.ent_id

with st.sidebar:
    st.markdown(f"<h2 style='text-align: center;'>👤 {USER.upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{ROLE} | {C_NOM}</p>", unsafe_allow_html=True)
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 ABONNÉS", "📊 RAPPORTS HQ", "⚙️ RÉGLAGES SYSTÈME", "👤 PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "💸 DÉPENSES", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 PROFIL"]
    else: # Vendeur
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.replace("🏠 ", "").replace("🛒 ", "").replace("📉 ", "").replace("📦 ", "").replace("👥 ", "").replace("💸 ", "").replace("📊 ", "").replace("⚙️ ", "").replace("👤 ", "").replace("🌍 ", "")
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 8. PAGE D'ACCUEIL (MONTRE & STATS)
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1 style='text-align: center; color: #0047AB;'>BIENVENUE CHEZ {C_NOM}</h1>", unsafe_allow_html=True)
    
    # Montre Digitale
    st.markdown(f"""
        <center>
            <div class="watch-card">
                <p class="time-text">{datetime.now().strftime('%H:%M:%S')}</p>
                <p class="date-text">📅 {datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)

    st.write("---")
    
    # Indicateurs de performance
    c1, c2, c3 = st.columns(3)
    
    total_v = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    total_d = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=? AND statut='NON_PAYE'", (ENT_ID,), fetch=True)[0][0] or 0
    total_s = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0]
    
    c1.metric("💰 CHIFFRE D'AFFAIRES", f"{total_v:,.2f} $")
    c2.metric("📉 CRÉANCES CLIENTS", f"{total_d:,.2f} $")
    c3.metric("📦 ARTICLES EN STOCK", total_s)

    # Petit Graphique pour le Dashboard
    st.write("---")
    st.subheader("📈 Aperçu des dernières ventes")
    v_data = run_db("SELECT date_v, total FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 10", (ENT_ID,), fetch=True)
    if v_data:
        df_v = pd.DataFrame(v_data, columns=["Date", "Montant"])
        fig = px.line(df_v, x="Date", y="Montant", title="Tendance des ventes", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------------------
# 9. TERMINAL DE VENTE (CAISSE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.markdown("<h2 style='text-align: center;'>🛒 TERMINAL DE VENTE</h2>", unsafe_allow_html=True)
        
        # Sélection Devise et Format
        col_set1, col_set2 = st.columns(2)
        devise_v = col_set1.selectbox("Monnaie de paiement", ["USD", "CDF"])
        st.session_state.format_fac = col_set2.selectbox("Format Facture", ["80mm", "A4"])
        
        # Liste des produits
        prods = run_db("SELECT id, designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        if not prods:
            st.warning("⚠️ Le stock est vide. Veuillez ajouter des produits.")
        else:
            p_map = {r[1]: {'id':r[0], 'px':r[2], 'st':r[3], 'dv':r[4]} for r in prods}
            
            c_a, c_b = st.columns([3, 1])
            article_sel = c_a.selectbox("Rechercher un produit", ["---"] + list(p_map.keys()))
            if c_b.button("➕ AJOUTER") and article_sel != "---":
                st.session_state.panier[article_sel] = st.session_state.panier.get(article_sel, 0) + 1
                st.rerun()

        # Affichage du Panier
        if st.session_state.panier:
            st.write("---")
            total_net = 0.0
            details_facture = []
            
            for art, qte in list(st.session_state.panier.items()):
                p_info = p_map[art]
                p_base = p_info['px']
                d_base = p_info['dv']
                
                # Conversion en temps réel
                if d_base == "USD" and devise_v == "CDF": px_final = p_base * C_TX
                elif d_base == "CDF" and devise_v == "USD": px_final = p_base / C_TX
                else: px_final = p_base
                
                stot = px_final * qte
                total_net += stot
                details_facture.append({'art': art, 'qte': qte, 'pu': px_final, 'st': stot})
                
                with st.container():
                    l1, l2, l3 = st.columns([3, 1, 0.5])
                    l1.markdown(f"**{art}**")
                    st.session_state.panier[art] = l2.number_input(f"Qté (Dispo: {p_info['st']})", 1, p_info['st'], value=qte, key=f"qte_{art}")
                    if l3.button("❌", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()

            st.markdown(f'<div class="price-tag">TOTAL : {total_net:,.2f} {devise_v}</div>', unsafe_allow_html=True)
            
            # Finalisation
            c_cl1, c_cl2 = st.columns(2)
            nom_client = c_cl1.text_input("NOM DU CLIENT", value="CLIENT COMPTANT").upper()
            montant_paye = c_cl2.number_input(f"MONTANT REÇU ({devise_v})", value=float(total_net))
            
            if st.button("💾 VALIDER LA VENTE ET IMPRIMER"):
                ref_fac = f"B-{random.randint(10000, 99999)}"
                date_fac = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste_fac = total_net - montant_paye
                
                # Enregistrement Vente
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (ref_fac, nom_client, total_net, montant_paye, reste_fac, devise_v, date_fac, USER, ENT_ID, json.dumps(details_facture)))
                
                # Enregistrement Dette si nécessaire
                if reste_fac > 0.1:
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)",
                           (nom_client, reste_fac, devise_v, ref_fac, ENT_ID, json.dumps([{'date': date_fac, 'paye': montant_paye}])))
                
                # Décrémenter Stock
                for item in details_facture:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (item['qte'], item['art'], ENT_ID))
                
                st.session_state.last_fac = {
                    'ref': ref_fac, 'cl': nom_client, 'tot': total_net, 
                    'pay': montant_paye, 'dev': devise_v, 'items': details_facture, 'date': date_fac
                }
                st.session_state.panier = {}
                st.rerun()
    else:
        # Affichage Facture
        fac = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({'last_fac': None}))
        
        f_style = "width:300px; font-size:12px;" if st.session_state.format_fac == "80mm" else "width:100%; font-size:16px;"
        
        html_facture = f"""
        <div class="invoice-container" style="{f_style}">
            <center>
                <h2 style="margin:0;">{C_NOM}</h2>
                <p>{C_ADR}<br>Tel: {C_TEL}</p>
                <hr>
                <b>FACTURE N° {fac['ref']}</b><br>
                Date: {fac['date']}<br>
                Client: {fac['cl']}
                <hr>
            </center>
            <table style="width:100%;">
                <tr><td><b>ART</b></td><td align="center"><b>Q</b></td><td align="right"><b>TOTAL</b></td></tr>
                {" ".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in fac['items']])}
            </table>
            <hr>
            <h3 align="right">NET À PAYER : {fac['tot']:,.2f} {fac['dev']}</h3>
            <p align="right">Payé : {fac['pay']:,.2f}<br>Reste : {fac['tot']-fac['pay']:,.2f}</p>
            <center><p>MERCI DE VOTRE VISITE</p></center>
        </div>
        """
        st.markdown(html_facture, unsafe_allow_html=True)
        
        c_p1, c_p2 = st.columns(2)
        c_p1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        
        share_msg = f"Facture {fac['ref']} de {C_NOM}. Montant: {fac['tot']} {fac['dev']}. Merci."
        c_p2.markdown(f'<a href="https://wa.me/?text={share_msg}" target="_blank"><button style="width:100%; background:#25D366; color:white; border-radius:10px; height:50px; border:none; font-weight:bold;">📲 PARTAGER WHATSAPP</button></a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 10. GESTION DU STOCK (MODIFICATION ET SUPPRESSION)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK":
    st.markdown("<h2 style='text-align: center;'>📦 GESTION DU STOCK</h2>", unsafe_allow_html=True)
    
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("form_add_p"):
            f_na = st.text_input("Nom de l'article")
            f_st = st.number_input("Quantité en stock", min_value=1)
            f_px = st.number_input("Prix de vente", min_value=0.0)
            f_dv = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                if f_na:
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                           (f_na.upper(), f_st, f_px, f_dv, ENT_ID))
                    st.success("Produit ajouté !")
                    st.rerun()

    st.write("---")
    # Liste avec modification
    prods_list = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    if prods_list:
        for p_id, p_na, p_sq, p_px, p_dv in prods_list:
            with st.container():
                cl1, cl2, cl3, cl4 = st.columns([3, 1, 1, 0.5])
                cl1.markdown(f"**{p_na}**")
                cl2.write(f"Stock: {p_sq}")
                
                new_px = cl3.number_input(f"Prix ({p_dv})", value=float(p_px), key=f"px_{p_id}")
                if cl3.button("💾", key=f"save_{p_id}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, p_id))
                    st.success("Prix mis à jour !")
                    st.rerun()
                
                if cl4.button("🗑️", key=f"del_{p_id}"):
                    run_db("DELETE FROM produits WHERE id=?", (p_id,))
                    st.rerun()

# ------------------------------------------------------------------------------
# 11. GESTION DES DETTES (ÉCHELONNEMENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.markdown("<h2 style='text-align: center;'>📉 SUIVI DES CRÉANCES</h2>", unsafe_allow_html=True)
    dettes_data = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not dettes_data:
        st.success("🎉 Toutes les dettes sont apurées !")
    else:
        for d_id, d_cl, d_mt, d_dv, d_rf, d_hi in dettes_data:
            with st.expander(f"🔴 {d_cl} | RESTE : {d_mt:,.2f} {d_dv}"):
                st.write(f"Facture d'origine : {d_rf}")
                acompte = st.number_input(f"Verser un acompte ({d_dv})", 0.0, float(d_mt), key=f"ac_{d_id}")
                if st.button("ENREGISTRER PAIEMENT", key=f"btn_d_{d_id}"):
                    nouveau_reste = d_mt - acompte
                    historique = json.loads(d_hi)
                    historique.append({'date': datetime.now().strftime("%d/%m/%Y"), 'paye': acompte})
                    
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nouveau_reste, json.dumps(historique), d_id))
                    run_db("UPDATE ventes SET paye = paye + ?, reste = reste - ? WHERE ref=? AND ent_id=?", (acompte, acompte, d_rf, ENT_ID))
                    
                    if nouveau_reste <= 0.1:
                        run_db("UPDATE dettes SET statut='PAYE' WHERE id=?", (d_id,))
                        st.balloons()
                    st.rerun()

# ------------------------------------------------------------------------------
# 12. GESTION DES VENDEURS
# ------------------------------------------------------------------------------
elif st.session_state.page == "VENDEURS" and ROLE == "ADMIN":
    st.header("👥 COMPTES DU PERSONNEL")
    
    with st.expander("➕ CRÉER UN COMPTE VENDEUR"):
        with st.form("form_new_v"):
            v_u = st.text_input("Identifiant (Username)").lower().strip()
            v_p = st.text_input("Mot de passe", type="password")
            v_t = st.text_input("Téléphone")
            if st.form_submit_button("CRÉER LE COMPTE"):
                if not run_db("SELECT * FROM users WHERE username=?", (v_u,), fetch=True):
                    run_db("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (v_u, make_hashes(v_p), "VENDEUR", ENT_ID, v_u.upper(), v_t, datetime.now().strftime("%d/%m/%Y")))
                    st.success(f"Compte {v_u} créé !")
                    st.rerun()
                else:
                    st.error("Cet identifiant est déjà utilisé.")

    st.write("---")
    vendeurs = run_db("SELECT username, telephone, date_crea FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for v_un, v_tel, v_dt in vendeurs:
        with st.container():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"👤 **{v_un.upper()}**")
            c2.write(f"📞 {v_tel}")
            if c3.button("🗑️ SUPPRIMER", key=f"del_v_{v_un}"):
                run_db("DELETE FROM users WHERE username=?", (v_un,))
                st.rerun()

# ------------------------------------------------------------------------------
# 13. RAPPORTS FINANCIERS
# ------------------------------------------------------------------------------
elif st.session_state.page == "RAPPORTS" and ROLE == "ADMIN":
    st.header("📊 ANALYSE FINANCIÈRE")
    
    cash_net = run_db("SELECT SUM(paye) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    dep_tot = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    encaisse = cash_net - dep_tot
    
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("RECETTES BRUTES", f"{cash_net:,.2f} $")
    col_r2.metric("DÉPENSES TOTALES", f"{dep_tot:,.2f} $")
    col_r3.metric("EN CAISSE (NET)", f"{encaisse:,.2f} $", delta=f"-{dep_tot:,.2f}")
    
    st.write("---")
    tab1, tab2 = st.tabs(["Journal des Ventes", "Journal des Dépenses"])
    
    with tab1:
        v_journal = run_db("SELECT date_v, ref, client, total, paye, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
        if v_journal:
            st.dataframe(pd.DataFrame(v_journal, columns=["Date", "REF", "Client", "Total", "Payé", "Vendeur"]), use_container_width=True)
    
    with tab2:
        d_journal = run_db("SELECT date_d, motif, montant, vendeur FROM depenses WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
        if d_journal:
            st.table(pd.DataFrame(d_journal, columns=["Date", "Motif", "Montant", "Auteur"]))

# ------------------------------------------------------------------------------
# 14. DÉPENSES
# ------------------------------------------------------------------------------
elif st.session_state.page == "DÉPENSES":
    st.header("💸 ENREGISTRER UNE DÉPENSE")
    with st.form("form_dep"):
        d_mot = st.text_input("Motif de la dépense")
        d_mon = st.number_input("Montant ($)", min_value=0.0)
        if st.form_submit_button("ENREGISTRER"):
            run_db("INSERT INTO depenses (motif, montant, devise, date_d, vendeur, ent_id) VALUES (?,?,?,?,?,?)",
                   (d_mot, d_mon, "USD", datetime.now().strftime("%d/%m/%Y"), USER, ENT_ID))
            st.success("Dépense enregistrée.")
            st.rerun()

# ------------------------------------------------------------------------------
# 15. RÉGLAGES BOUTIQUE
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION DE LA BOUTIQUE")
    with st.form("form_shop"):
        s_nom = st.text_input("Nom de l'Entreprise", C_NOM)
        s_adr = st.text_input("Adresse", C_ADR)
        s_tel = st.text_input("Téléphone / WhatsApp", C_TEL)
        s_tx = st.number_input("Taux de change (CDF pour 1$)", value=C_TX)
        s_msg = st.text_area("Message défilant", C_MSG)
        s_col = st.color_picker("Couleur du texte défilant", C_COLOR)
        
        if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, color_m=? WHERE ent_id=?",
                   (s_nom.upper(), s_adr, s_tel, s_tx, s_msg, s_col, ENT_ID))
            st.success("Paramètres mis à jour !")
            st.rerun()

# ------------------------------------------------------------------------------
# 16. PROFIL SÉCURITÉ
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header("👤 SÉCURITÉ DU COMPTE")
    with st.form("form_p"):
        st.write(f"Utilisateur : **{USER}**")
        new_p = st.text_input("Nouveau mot de passe", type="password")
        if st.form_submit_button("CHANGER LE MOT DE PASSE"):
            if new_p:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
                st.success("Mot de passe modifié avec succès !")
            else:
                st.warning("Veuillez saisir un mot de passe.")

# ------------------------------------------------------------------------------
# 17. MODULE SYSTÈME (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES INSTANCES ERP")
    all_shops = run_db("SELECT ent_id, nom_ent, status, date_insc FROM config", fetch=True)
    st.table(pd.DataFrame(all_shops, columns=["ID", "Entreprise", "Statut", "Date"]))

# FIN DU CODE v2000
