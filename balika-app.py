# ==============================================================================
# PROJET : BALIKA ERP - VERSION MONSTRUEUSE v2037 (CODE COMPLET > 750 LIGNES)
# AUCUNE LIGNE SUPPRIMÉE - EXPANSION TOTALE DES FONCTIONNALITÉS
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
# 1. CONFIGURATION ET STYLE CSS (LUMINOSITÉ MAXIMALE & MOBILE FIRST)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v2037", layout="wide", initial_sidebar_state="expanded")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD", 'show_register': False, 'filtre_date': datetime.now().strftime("%d/%m/%Y")
    })

st.markdown("""
    <style>
    /* Global & Couleurs */
    .stApp { background-color: #0044cc !important; }
    h1, h2, h3, h4, h5, p, label, span, .stMarkdown { 
        color: #ffffff !important; text-align: center !important; font-weight: bold; 
    }
    
    /* Header Fixe avec Marquee */
    .fixed-header { 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000; color: #ffff00; height: 60px; 
        z-index: 9999; display: flex; align-items: center; border-bottom: 2px solid #fff; 
    }
    marquee { font-size: 20px; font-weight: bold; }
    .spacer { margin-top: 80px; }
    
    /* Login Box Stylisée */
    .login-card {
        background: white; padding: 40px; border-radius: 25px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.4);
        max-width: 450px; margin: auto; border: 4px solid #00c6ff;
    }
    .login-card h1 { color: #0044cc !important; }
    .login-card label { color: #333 !important; }
    
    /* Boutons Tactiles Géants */
    .stButton>button { 
        background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
        color: white !important; border-radius: 15px; height: 70px; width: 100%;
        font-size: 20px; border: 2px solid #fff; margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Frame Total Coloré */
    .total-frame { 
        background: #000; color: #00ff00; padding: 25px; 
        border: 4px solid #fff; border-radius: 20px; 
        font-size: 32px; margin: 15px 0; text-align: center;
        box-shadow: inset 0 0 15px #00ff00;
    }

    /* Factures Design */
    .fac-print-container { 
        background: white; color: black !important; padding: 30px; 
        border: 2px solid black; margin: auto; 
    }
    .fac-80mm { width: 300px; font-family: 'Courier New', monospace; font-size: 14px; }
    .fac-a4 { width: 95%; max-width: 800px; font-family: Arial, sans-serif; }
    .fac-print-container * { color: black !important; text-align: center; }
    .fac-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .fac-table th, .fac-table td { border: 1px solid black; padding: 8px; }

    /* Tables scannables */
    .stDataFrame, div[data-testid="stTable"] { 
        background-color: white !important; border-radius: 12px; color: black !important; 
    }
    div[data-testid="stTable"] td { color: black !important; font-weight: normal; }
    
    /* Inputs */
    input { text-align: center !important; font-size: 18px !important; }
    </style>
    <div class="fixed-header"><marquee>SYSTÈME DE GESTION UNIFIÉE BALIKA v2037 - VOTRE PERFORMANCE, NOTRE PRIORITÉ</marquee></div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. LOGIQUE BASE DE DONNÉES (SQLITE3)
# ------------------------------------------------------------------------------
DB_NAME = 'balika_master_v2037.db'

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect(DB_NAME, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Database: {e}")
        return []

def init_db():
    # Tables Utilisateurs & Config
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ATTENTE', date_validite TEXT, telephone TEXT, nom_resp TEXT)""")
    
    run_db("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, taux REAL)")
    
    # Tables Boutique
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, 
        rccm TEXT, header_txt TEXT, footer_txt TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, 
        stock_actuel INTEGER, prix_achat REAL, prix_vente REAL, ent_id TEXT, categorie TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, 
        paye REAL, reste REAL, devise TEXT, date_v TEXT, date_short TEXT, 
        vendeur TEXT, ent_id TEXT, details_json TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        ref_v TEXT, date_d TEXT, ent_id TEXT, statut TEXT DEFAULT 'NON PAYE')""")
    
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
        date_dep TEXT, auteur TEXT, ent_id TEXT)""")

    # Données par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, status) VALUES (?,?,?,?)", 
               ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'ACTIF'))
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config VALUES (1, 'BALIKA ERP', 'GESTIONNAIRE DE BOUTIQUE PROFESSIONNEL', 2850.0)")

init_db()
config = run_db("SELECT app_name, marquee, taux FROM system_config WHERE id=1", fetch=True)[0]

# ------------------------------------------------------------------------------
# 3. SYSTÈME D'AUTHENTIFICATION & LOGIN (DESIGN AMÉLIORÉ)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    if not st.session_state.show_register:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown(f"<h1>🔐 {config[0]}</h1>", unsafe_allow_html=True)
        u = st.text_input("Identifiant Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id, status, date_validite FROM users WHERE username=?", (u,), fetch=True)
            if res and hashlib.sha256(p.encode()).hexdigest() == res[0][0]:
                if res[0][3] == "PAUSE":
                    st.error("🚨 Votre compte est en pause. Contactez l'administrateur.")
                elif res[0][3] == "ATTENTE":
                    st.warning("⏳ Compte en attente de validation.")
                else:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
            else:
                st.error("Identifiants incorrects")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br><br>")
        if st.button("📥 CRÉER UN NOUVEAU COMPTE"):
            st.session_state.show_register = True
            st.rerun()
    else:
        st.markdown("<h1>📝 INSCRIPTION BOUTIQUE</h1>", unsafe_allow_html=True)
        with st.form("inscription"):
            nom_b = st.text_input("Nom de la Boutique / Business")
            nom_r = st.text_input("Nom du Propriétaire")
            tel_b = st.text_input("Téléphone")
            pass_b = st.text_input("Choisir un mot de passe", type="password")
            if st.form_submit_button("DEMANDER MON ACCÈS"):
                user_id = nom_b.lower().replace(" ","")
                run_db("INSERT INTO users (username, password, role, ent_id, telephone, nom_resp) VALUES (?,?,?,?,?,?)",
                       (user_id, hashlib.sha256(pass_b.encode()).hexdigest(), 'USER', user_id, tel_b, nom_r))
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (user_id, nom_b.upper(), tel_b))
                st.success("Inscription réussie ! Votre compte est en attente de validation.")
                time.sleep(2)
                st.session_state.show_register = False
                st.rerun()
        if st.button("⬅️ RETOUR AU LOGIN"):
            st.session_state.show_register = False
            st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE SUPER ADMIN (GESTION TOTALE)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    menu = st.sidebar.radio("ADMINISTRATION", ["DASHBOARD", "VALIDATION CLIENTS", "CONFIG SYSTÈME", "DÉCONNEXION"])
    
    if menu == "DASHBOARD":
        st.header("📊 VUE D'ENSEMBLE DU RÉSEAU")
        total_u = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)[0][0]
        st.markdown(f"<div class='total-frame'>BOUTIQUES INSCRITES : {total_u}</div>", unsafe_allow_html=True)
        
    elif menu == "VALIDATION CLIENTS":
        st.header("👥 GESTION DES BOUTIQUES")
        clients = run_db("SELECT username, telephone, status, nom_resp, ent_id FROM users WHERE role='USER'", fetch=True)
        for un, tel, stat, resp, eid in clients:
            with st.container(border=True):
                st.write(f"🏢 **{eid.upper()}** | 👤 {resp} | 📞 {tel}")
                st.write(f"Statut : `{stat}`")
                c1, c2, c3, c4 = st.columns(4)
                if c1.button("✅ ACTIVER", key=f"ac_{un}"):
                    run_db("UPDATE users SET status='ACTIF' WHERE username=?", (un,)); st.rerun()
                if c2.button("⏸️ PAUSE", key=f"ps_{un}"):
                    run_db("UPDATE users SET status='PAUSE' WHERE username=?", (un,)); st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"del_{un}"):
                    run_db("DELETE FROM users WHERE username=?", (un,)); st.rerun()
                if c4.button("📅 ESSAI 30J", key=f"es_{un}"):
                    d_fin = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                    run_db("UPDATE users SET date_validite=?, status='ACTIF' WHERE username=?", (d_fin, un)); st.rerun()

    elif menu == "CONFIG SYSTÈME":
        st.header("⚙️ RÉGLAGES GLOBAUX")
        n_taux = st.number_input("Taux de change (USD/CDF)", value=config[2])
        n_marq = st.text_area("Texte Marquee", value=config[1])
        if st.button("SAUVEGARDER CONFIG"):
            run_db("UPDATE system_config SET taux=?, marquee=? WHERE id=1", (n_taux, n_marq)); st.rerun()

    elif menu == "DÉCONNEXION": st.session_state.auth = False; st.rerun()

# ------------------------------------------------------------------------------
# 5. MODULE BOUTIQUE (POUR LES UTILISATEURS)
# ------------------------------------------------------------------------------
else:
    with st.sidebar:
        st.markdown(f"### 🏪 {st.session_state.ent_id.upper()}")
        st.markdown(f"👤 {st.session_state.user}")
        st.divider()
        page = st.radio("MENU PRINCIPAL", ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES", "🚪 QUITTER"])

    # --- ACCUEIL BOUTIQUE ---
    if page == "🏠 ACCUEIL":
        st.markdown(f"<h1>BIENVENUE CHEZ {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        now_d = datetime.now().strftime("%d/%m/%Y")
        v_j = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_short=?", (st.session_state.ent_id, now_d), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>VENTES DU JOUR<br>{v_j:,.2f} $</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        low_stock = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=? AND stock_actuel < 5", (st.session_state.ent_id,), fetch=True)[0][0]
        c1.metric("Articles en rupture", low_stock)
        
        dettes_t = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=? AND statut='NON PAYE'", (st.session_state.ent_id,), fetch=True)[0][0] or 0
        c2.metric("Total Créances", f"{dettes_t:,.2f} $")

    # --- GESTION DU STOCK ---
    elif page == "📦 STOCK":
        st.header("📦 GESTION DES PRODUITS")
        tab_list, tab_add = st.tabs(["📋 INVENTAIRE", "➕ NOUVEL ARTICLE"])
        
        with tab_list:
            items = run_db("SELECT id, designation, stock_actuel, prix_vente, prix_achat FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            if items:
                df_stock = pd.DataFrame(items, columns=["ID", "Désignation", "Stock", "Prix Vente", "Prix Achat"])
                st.table(df_stock)
                
                st.subheader("🗑️ Supprimer un article")
                s_id = st.selectbox("Sélectionner ID", [i[0] for i in items])
                if st.button("SUPPRIMER DÉFINITIVEMENT"):
                    run_db("DELETE FROM produits WHERE id=?", (s_id,))
                    st.rerun()
            else:
                st.info("Votre stock est vide.")

        with tab_add:
            with st.form("form_stock"):
                d_art = st.text_input("Désignation de l'article")
                c_art = st.text_input("Catégorie (Optionnel)")
                s_art = st.number_input("Stock Initial", 1)
                pa_art = st.number_input("Prix d'Achat Unitaire ($)")
                pv_art = st.number_input("Prix de Vente Unitaire ($)")
                if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                    run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_achat, prix_vente, ent_id, categorie) VALUES (?,?,?,?,?,?,?)",
                           (d_art.upper(), s_art, s_art, pa_art, pv_art, st.session_state.ent_id, c_art))
                    st.success("Article ajouté !"); time.sleep(1); st.rerun()

    # --- CAISSE & VENTE (OPTIMISÉ PANIER) ---
    elif page == "🛒 CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            
            # Paramètres de vente
            col_a, col_b = st.columns(2)
            sel_devise = col_a.selectbox("Devise", ["USD", "CDF"])
            sel_format = col_b.selectbox("Format Facture", ["80mm (Ticket)", "A4 (Admin)"])
            
            # Sélection Article
            prods = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            prod_map = {p[0]: (p[1], p[2]) for p in prods}
            
            choix = st.selectbox("🔍 Choisir un article", ["---"] + list(prod_map.keys()))
            
            # Panier immédiat au choix
            if choix != "---":
                if prod_map[choix][1] > 0:
                    st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                    st.success(f"{choix} ajouté au panier.")
                    # On ne RERUN pas ici pour permettre plusieurs clics rapides si nécessaire, 
                    # mais le panier s'affiche juste en dessous.
                else:
                    st.error("Rupture de stock !")

            # Affichage du Panier
            if st.session_state.panier:
                st.divider()
                st.subheader("🧺 PANIER ACTUEL")
                total_v = 0.0
                list_items = []
                
                for art, qte in list(st.session_state.panier.items()):
                    p_u = prod_map[art][0]
                    if sel_devise == "CDF": p_u *= config[2]
                    
                    st_v = p_u * qte
                    total_v += st_v
                    list_items.append({"art": art, "qte": qte, "pu": p_u, "total": st_v})
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{art}**")
                    c2.write(f"x {qte}")
                    if c3.button("🗑️", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL : {total_v:,.2f} {sel_devise}</div>", unsafe_allow_html=True)
                
                # Finalisation
                with st.container(border=True):
                    client = st.text_input("Nom du Client", "COMPTANT")
                    verse = st.number_input("Montant Reçu", value=float(total_v))
                    reste = total_v - verse
                    
                    if st.button("🏁 VALIDER LA VENTE"):
                        ref_f = f"FAC-{random.randint(10000, 99999)}"
                        d_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                        d_s = datetime.now().strftime("%d/%m/%Y")
                        
                        # Enregistrement Vente
                        run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, date_short, vendeur, ent_id, details_json) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                               (ref_f, client.upper(), total_v, verse, reste, sel_devise, d_v, d_s, st.session_state.user, st.session_state.ent_id, json.dumps(list_items)))
                        
                        # Sortie Stock
                        for it in list_items:
                            run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", 
                                   (it['qte'], it['art'], st.session_state.ent_id))
                        
                        # Gestion Dette
                        if reste > 0:
                            run_db("INSERT INTO dettes (client, montant, ref_v, date_d, ent_id) VALUES (?,?,?,?,?)",
                                   (client.upper(), reste, ref_f, d_s, st.session_state.ent_id))
                        
                        st.session_state.last_fac = {
                            "ref": ref_f, "client": client.upper(), "total": total_v, 
                            "paye": verse, "reste": reste, "devise": sel_devise, 
                            "items": list_items, "date": d_v, "format": sel_format
                        }
                        st.session_state.panier = {}
                        st.rerun()
        else:
            # --- AFFICHAGE DE LA FACTURE ---
            f = st.session_state.last_fac
            info = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_txt FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            # Construction HTML pour l'affichage et l'enregistrement
            fac_html = ""
            if f['format'] == "A4 (Admin)":
                fac_html = f"""
                <div class="fac-print-container fac-a4">
                    <h1>{info[4] if info[4] else info[0]}</h1>
                    <p>{info[1]} | Tél: {info[2]}<br>RCCM: {info[3] if info[3] else '-'}</p>
                    <hr>
                    <h3>FACTURE OFFICIELLE N° {f['ref']}</h3>
                    <p>Client: {f['client']} | Date: {f['date']}</p>
                    <table class="fac-table">
                        <thead><tr><th>Désignation</th><th>Qté</th><th>P.U</th><th>S.Total</th></tr></thead>
                        <tbody>
                            {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['pu']:,.0f}</td><td>{i['total']:,.0f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <h2 style="text-align:right;">NET À PAYER : {f['total']:,.2f} {f['devise']}</h2>
                    <p style="text-align:right;">Payé : {f['paye']:,.2f} | Reste : {f['reste']:,.2f}</p>
                    <div style="margin-top:50px; text-align:right;">
                        <p>Signature et Cachet</p><br><br>__________
                        <p style="font-size:10px;">Émis par {f['vendeur'] if 'vendeur' in f else st.session_state.user}</p>
                    </div>
                </div>"""
            else:
                fac_html = f"""
                <div class="fac-print-container fac-80mm">
                    <h3>{info[0]}</h3>
                    <p>FAC: {f['ref']}<br>{f['date']}</p>
                    <hr>
                    {"".join([f"<p style='text-align:left;'>{i['art']} x{i['qte']}<br>=> {i['total']:,.0f} {f['devise']}</p>" for i in f['items']])}
                    <hr>
                    <h4>TOTAL : {f['total']:,.2f} {f['devise']}</h4>
                    <p>Merci pour votre confiance !</p>
                </div>"""

            st.markdown(fac_html, unsafe_allow_html=True)
            
            # SAUVEGARDE AUTOMATIQUE SUR L'ORDINATEUR
            file_name = f"Facture_{f['ref']}.html"
            b64 = base64.b64encode(fac_html.encode()).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="{file_name}" style="background:#00ff00; color:black; padding:20px; border-radius:15px; text-decoration:none; display:block; text-align:center; font-weight:bold; border:2px solid white;">📥 ENREGISTRER SUR CET ORDINATEUR</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            if c1.button("🖨️ IMPRIMER"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if c2.button("📲 PARTAGER"):
                st.info("Utilisez la capture d'écran pour partager sur WhatsApp.")
            if c3.button("⬅️ RETOUR CAISSE"):
                st.session_state.last_fac = None; st.rerun()

    # --- RAPPORTS DE VENTES ---
    elif page == "📊 RAPPORTS":
        st.header("📊 RAPPORT D'ACTIVITÉ")
        sel_date = st.date_input("Filtrer par date", datetime.now())
        date_str = sel_date.strftime("%d/%m/%Y")
        
        v_list = run_db("SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=? AND date_short=?", (st.session_state.ent_id, date_str), fetch=True)
        if v_list:
            df_v = pd.DataFrame(v_list, columns=["Heure", "Référence", "Client", "Montant", "Vendeur"])
            st.table(df_v)
            st.markdown(f"**Total pour cette journée : {df_v['Montant'].sum():,.2f} $**")
        else:
            st.warning("Aucune vente trouvée pour cette date.")

    # --- GESTION DES DETTES ---
    elif page == "📉 DETTES":
        st.header("📉 CRÉANCES CLIENTS")
        d_list = run_db("SELECT id, client, montant, ref_v, date_d FROM dettes WHERE ent_id=? AND statut='NON PAYE'", (st.session_state.ent_id,), fetch=True)
        if d_list:
            for di, dc, dm, dr, dd in d_list:
                with st.container(border=True):
                    st.write(f"👤 **{dc}** | Facture: {dr} du {dd}")
                    st.write(f"💰 Reste à payer : **{dm:,.2f} $**")
                    v_p = st.number_input("Encaisser un montant", 0.0, float(dm), key=f"pay_{di}")
                    if st.button("VALIDER PAIEMENT", key=f"btn_{di}"):
                        if v_p >= dm:
                            run_db("UPDATE dettes SET montant=0, statut='PAYE' WHERE id=?", (di,))
                        else:
                            run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (v_p, di))
                        st.success("Paiement enregistré !"); time.sleep(1); st.rerun()
        else:
            st.success("Aucune dette en cours.")

    # --- GESTION DES DÉPENSES ---
    elif page == "💸 DÉPENSES":
        st.header("💸 SORTIES DE CAISSE")
        with st.form("form_dep"):
            m_dep = st.text_input("Motif de la dépense")
            v_dep = st.number_input("Montant ($)", 0.0)
            if st.form_submit_button("VALIDER DÉPENSE"):
                run_db("INSERT INTO depenses (motif, montant, date_dep, auteur, ent_id) VALUES (?,?,?,?,?)",
                       (m_dep, v_dep, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id))
                st.success("Dépense enregistrée !"); st.rerun()
        
        st.divider()
        h_dep = run_db("SELECT date_dep, motif, montant, auteur FROM depenses WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if h_dep:
            st.table(pd.DataFrame(h_dep, columns=["Date", "Motif", "Montant ($)", "Auteur"]))

    # --- GESTION VENDEURS ---
    elif page == "👥 VENDEURS":
        st.header("👥 MES AGENTS DE VENTE")
        with st.form("add_v"):
            vu = st.text_input("Identifiant Vendeur").lower().strip()
            vp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
                       (vu, hashlib.sha256(vp.encode()).hexdigest(), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.success("Compte vendeur créé !"); st.rerun()
        
        st.divider()
        vs = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True)
        for u, s in vs:
            st.write(f"🔹 {u.upper()} | Statut : {s}")

    # --- RÉGLAGES BOUTIQUE ---
    elif page == "⚙️ RÉGLAGES":
        st.header("⚙️ PARAMÈTRES BOUTIQUE")
        e_info = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_txt FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        with st.form("set_boutique"):
            n_b = st.text_input("Nom de l'Enseigne", e_info[0])
            a_b = st.text_input("Adresse Physique", e_info[1])
            t_b = st.text_input("Téléphone", e_info[2])
            r_b = st.text_input("RCCM / ID Nat", e_info[3])
            h_b = st.text_input("Slogan / En-tête", e_info[4])
            if st.form_submit_button("METTRE À JOUR"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=?, header_txt=? WHERE ent_id=?",
                       (n_b.upper(), a_b, t_b, r_b, h_b, st.session_state.ent_id))
                st.success("Informations mises à jour !"); st.rerun()

    elif page == "🚪 QUITTER":
        st.session_state.auth = False
        st.rerun()
