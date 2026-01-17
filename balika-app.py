# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTIME v2100
# CLIENT : BALIKA BUSINESS
# OPTIMISATION : SMARTPHONE & TABLETTE (ZÉRO CHEVAUCHEMENT)
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time
import base64

# ------------------------------------------------------------------------------
# 1. MOTEUR DE STYLE : CSS "BLOCK-FLOW" (ADAPTÉ AUX ÉCRANS ÉTROITS)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v2100", layout="wide", initial_sidebar_state="collapsed")

# Initialisation des variables de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'panier': {}, 'last_fac': None, 'devise': "USD", 'show_reg': False
    })

st.markdown("""
    <style>
    /* Thème Visuel : Bleu Cobalt & Blanc Pur */
    .stApp { background-color: #0033cc !important; }
    
    /* Textes et Labels */
    h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stMetricValue"] { 
        color: #FFFFFF !important; text-align: center !important; font-weight: bold !important; 
    }

    /* Message Défilant Admin (Marquee) */
    .marquee-box {
        position: fixed; top: 0; left: 0; width: 100%; background: #000000;
        color: #00FF00; z-index: 9999; height: 45px; line-height: 45px;
        border-bottom: 2px solid white; font-size: 16px; font-weight: bold;
    }
    .main-spacer { margin-top: 60px; }

    /* Forcer l'affichage vertical sur mobile (Anti-chevauchement) */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        display: block !important;
        padding: 5px !important;
    }

    /* Cartes Design (Cards) pour les Articles, Ventes et Dettes */
    .erp-card {
        background: #FFFFFF; border-radius: 15px; padding: 20px;
        margin-bottom: 15px; border-left: 10px solid #00ccff;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    .erp-card p, .erp-card h3, .erp-card h4 { 
        color: #222222 !important; text-align: left !important; margin: 4px 0; 
    }
    .erp-card b { color: #0033cc; }

    /* Boutons Tactiles XXL */
    .stButton>button {
        width: 100% !important; height: 65px !important;
        border-radius: 15px !important; font-size: 20px !important;
        background: linear-gradient(145deg, #00ccff, #0055ff) !important;
        color: white !important; border: 2px solid #fff !important;
        margin: 10px 0px !important; font-weight: bold; text-transform: uppercase;
    }

    /* Cadre de Résultat Financier */
    .financial-frame {
        background: #000; color: #00FF00; padding: 25px;
        border-radius: 20px; border: 3px solid #00FF00;
        font-size: 28px; text-align: center; margin: 20px 0;
        box-shadow: 0px 0px 15px rgba(0,255,0,0.5);
    }

    /* Inputs (Blancs pour être visibles) */
    input, select, textarea { 
        background-color: #ffffff !important; color: #000000 !important; 
        border-radius: 12px !important; height: 50px !important; font-size: 18px !important;
    }

    /* Style Facture imprimable */
    .bill-box { background: #fff; color: #000 !important; padding: 25px; border: 1px solid #000; font-family: 'Courier New', Courier, monospace; }
    .bill-box * { color: #000 !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DE LA BASE DE DONNÉES (SQLITE AVANCÉ)
# ------------------------------------------------------------------------------
DB_NAME = "balika_pro_v2100.db"

def execute_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def init_all_systems():
    # Table Utilisateurs & Boutiques
    execute_query("""CREATE TABLE IF NOT EXISTS accounts (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ACTIF', boss_name TEXT, phone TEXT)""")
    
    # Table Configuration Globale
    execute_query("CREATE TABLE IF NOT EXISTS sys_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee_msg TEXT, usd_rate REAL)")
    
    # Table Profil Boutique
    execute_query("CREATE TABLE IF NOT EXISTS store_profiles (ent_id TEXT PRIMARY KEY, s_name TEXT, s_addr TEXT, s_tel TEXT, s_head TEXT)")
    
    # Table Stock (Articles)
    execute_query("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock_qty INTEGER, 
        buy_price REAL, sell_price REAL, ent_id TEXT)""")
    
    # Table Ventes
    execute_query("""CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, bill_ref TEXT, client_name TEXT, 
        total_amt REAL, paid_amt REAL, debt_amt REAL, currency TEXT, 
        time_v TEXT, date_v TEXT, seller_id TEXT, ent_id TEXT, json_items TEXT)""")
    
    # Table Dettes
    execute_query("""CREATE TABLE IF NOT EXISTS debt_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT, balance REAL, 
        bill_ref TEXT, date_start TEXT, ent_id TEXT, status TEXT DEFAULT 'NON_PAYE')""")
    
    # Table Dépenses (Charges)
    execute_query("""CREATE TABLE IF NOT EXISTS company_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motive TEXT, amount REAL, 
        date_exp TEXT, category TEXT, ent_id TEXT)""")

    # Seed initial
    if not execute_query("SELECT * FROM accounts WHERE uid='admin'", fetch=True):
        execute_query("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", 
                     ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'CHEF', '000'))
    if not execute_query("SELECT * FROM sys_config", fetch=True):
        execute_query("INSERT INTO sys_config VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION V2100', 2850.0)")

init_all_systems()
core_cfg = execute_query("SELECT app_name, marquee_msg, usd_rate FROM sys_config WHERE id=1", fetch=True)[0]

# Barre de défilement fixe
st.markdown(f'<div class="marquee-box"><marquee scrollamount="8">{core_cfg[1]}</marquee></div><div class="main-spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. INTERFACE DE CONNEXION / INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    if not st.session_state.show_reg:
        st.markdown(f"<h1>🔐 ACCÈS {core_cfg[0]}</h1>", unsafe_allow_html=True)
        with st.container():
            u_in = st.text_input("Identifiant Utilisateur").lower().strip()
            p_in = st.text_input("Mot de Passe", type="password")
            if st.button("SE CONNECTER AU SYSTÈME"):
                res = execute_query("SELECT pwd, role, ent_id, status FROM accounts WHERE uid=?", (u_in,), fetch=True)
                if res and hashlib.sha256(p_in.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "PAUSE": st.error("❌ Accès suspendu par l'administrateur.")
                    else:
                        st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                        st.rerun()
                else: st.error("❌ Identifiants incorrects.")
            st.divider()
            if st.button("🚀 CRÉER UN COMPTE BOUTIQUE"):
                st.session_state.show_reg = True; st.rerun()
    else:
        st.markdown("<h1>📝 NOUVELLE BOUTIQUE</h1>", unsafe_allow_html=True)
        with st.form("reg_form"):
            r_btq = st.text_input("Nom de votre Boutique (ex: BALIKA LUXE)").upper()
            r_boss = st.text_input("Nom du Gérant")
            r_tel = st.text_input("N° Téléphone")
            r_pwd = st.text_input("Définir un mot de passe", type="password")
            if st.form_submit_button("VALIDER L'INSCRIPTION"):
                u_id = r_btq.lower().replace(" ","_")
                execute_query("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", 
                             (u_id, hashlib.sha256(r_pwd.encode()).hexdigest(), 'USER', u_id, 'ACTIF', r_boss, r_tel))
                execute_query("INSERT INTO store_profiles (ent_id, s_name, s_tel) VALUES (?,?,?)", (u_id, r_btq, r_tel))
                st.success("✅ Boutique créée ! Connectez-vous."); st.session_state.show_reg = False; st.rerun()
        if st.button("⬅️ RETOUR"): st.session_state.show_reg = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. MODULE SUPER ADMIN (CONTRÔLEUR CENTRAL)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.title("💎 PANEL ADMIN")
    a_nav = st.sidebar.radio("NAVIGATION", ["BOUTIQUES CLIENTS", "CONFIG SYSTÈME", "QUITTER"])
    
    if a_nav == "BOUTIQUES CLIENTS":
        st.header("👥 GESTION DES ABONNÉS")
        clients = execute_query("SELECT uid, boss_name, status, ent_id FROM accounts WHERE role='USER'", fetch=True)
        for u, b, s, e in clients:
            with st.container():
                st.markdown(f"<div class='erp-card'><h3>🏢 Boutique: {e.upper()}</h3><p>Gérant: {b}</p><p>Statut: <b>{s}</b></p></div>", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3)
                if col_a.button("✅ ACTIVER", key=f"on_{u}"): execute_query("UPDATE accounts SET status='ACTIF' WHERE uid=?", (u,)); st.rerun()
                if col_b.button("⏸️ BLOQUER", key=f"off_{u}"): execute_query("UPDATE accounts SET status='PAUSE' WHERE uid=?", (u,)); st.rerun()
                if col_c.button("🗑️ SUPPRIMER", key=f"del_{u}"): execute_query("DELETE FROM accounts WHERE uid=?", (u,)); st.rerun()

    elif a_nav == "CONFIG SYSTÈME":
        st.header("⚙️ RÉGLAGES GLOBAUX")
        with st.form("sys_cfg_form"):
            f_app = st.text_input("Nom de l'App", core_cfg[0])
            f_msg = st.text_area("Message Défilant (Marquee)", core_cfg[1])
            f_tx = st.number_input("Taux de Change (1$ = ? CDF)", value=core_cfg[2])
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                execute_query("UPDATE sys_config SET app_name=?, marquee_msg=?, usd_rate=? WHERE id=1", (f_app, f_msg, f_tx))
                st.success("✅ Système mis à jour !"); st.rerun()

    elif a_nav == "QUITTER": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE BOUTIQUE (ADMIN BOUTIQUE & VENDEURS)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏪 {st.session_state.ent_id.upper()}")
    st.markdown(f"👤 {st.session_state.user.upper()}")
    st.divider()
    if st.session_state.role == "VENDEUR":
        nav = st.radio("MENU PRINCIPAL", ["🛒 CAISSE TACTILE", "📉 DETTES CLIENTS", "📊 RAPPORTS", "🚪 QUITTER"])
    else:
        nav = st.radio("MENU PRINCIPAL", ["🏠 ACCUEIL", "🛒 CAISSE TACTILE", "📦 STOCK / INVENTAIRE", "💸 DÉPENSES / CHARGES", "📉 DETTES CLIENTS", "📊 RAPPORTS VENTES", "👥 ÉQUIPE VENDEURS", "⚙️ RÉGLAGES PROFIL", "🚪 QUITTER"])

# --- 5.1 ACCUEIL (DASHBOARD v192 AVEC CALCUL BÉNÉFICE) ---
if nav == "🏠 ACCUEIL":
    st.header("📊 TABLEAU DE BORD")
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    # Récupération des données financières
    tot_recettes = execute_query("SELECT SUM(total_amt) FROM sales_history WHERE ent_id=? AND date_v=?", (st.session_state.ent_id, today_str), fetch=True)[0][0] or 0
    tot_depenses = execute_query("SELECT SUM(amount) FROM company_expenses WHERE ent_id=? AND date_exp=?", (st.session_state.ent_id, today_str), fetch=True)[0][0] or 0
    benefice_net = tot_recettes - tot_depenses
    
    # Affichage Dynamique du Bénéfice
    status_color = "#00FF00" if benefice_net >= 0 else "#FF0000"
    st.markdown(f"<div class='financial-frame' style='color:{status_color}; border-color:{status_color};'>BÉNÉFICE NET DU JOUR<br>{benefice_net:,.2f} $</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Recettes (Ventes)", f"{tot_recettes:,.2f} $")
        low_stk = execute_query("SELECT COUNT(*) FROM inventory WHERE ent_id=? AND stock_qty < 5", (st.session_state.ent_id,), fetch=True)[0][0]
        st.metric("Alertes Stock Bas", low_stk)
    with c2:
        st.metric("Charges (Dépenses)", f"{tot_depenses:,.2f} $")
        dettes_encours = execute_query("SELECT SUM(balance) FROM debt_records WHERE ent_id=? AND status='NON_PAYE'", (st.session_state.ent_id,), fetch=True)[0][0] or 0
        st.metric("Total Dettes Clients", f"{dettes_encours:,.2f} $")

# --- 5.2 CAISSE TACTILE (PROCESSUS DE VENTE COMPLET) ---
elif nav == "🛒 CAISSE TACTILE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        sel_devise = st.selectbox("Devise de la transaction", ["USD", "CDF"])
        
        # Moteur de recherche et sélection d'articles
        prods = execute_query("SELECT item_name, sell_price, stock_qty FROM inventory WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        stock_map = {p[0]: (p[1], p[2]) for p in prods}
        
        recherche = st.selectbox("🔍 Sélectionner un article...", ["---"] + list(stock_map.keys()))
        if recherche != "---":
            if stock_map[recherche][1] > 0:
                st.session_state.panier[recherche] = st.session_state.panier.get(recherche, 0) + 1
                st.toast(f"✅ {recherche} ajouté au panier")
            else: st.error("❌ Stock épuisé pour cet article !")

        # Affichage du Panier (Cartes Verticales)
        if st.session_state.panier:
            st.divider()
            st.markdown("### 🧺 PANIER ACTUEL")
            total_panier = 0.0; items_list = []
            
            for art, qty in list(st.session_state.panier.items()):
                prix_u = stock_map[art][0] if sel_devise == "USD" else stock_map[art][0] * core_cfg[2]
                stot = prix_u * qty
                total_panier += stot
                items_list.append({"nom": art, "qte": qty, "pu": prix_u, "st": stot})
                
                with st.container():
                    st.markdown(f"""<div class='erp-card'>
                        <h4>{art}</h4>
                        <p>Quantité: <b>{qty}</b> | Prix: <b>{prix_u:,.0f} {sel_devise}</b></p>
                        <p>Sous-total: <b>{stot:,.0f} {sel_devise}</b></p>
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"🗑️ Retirer {art}", key=f"rm_v_{art}"):
                        del st.session_state.panier[art]; st.rerun()

            st.markdown(f"<div class='financial-frame'>TOTAL À PAYER : {total_panier:,.2f} {sel_devise}</div>", unsafe_allow_html=True)
            
            with st.container():
                c_nom = st.text_input("Nom du Client", "CLIENT COMPTANT")
                m_recu = st.number_input(f"Montant Reçu ({sel_devise})", value=float(total_panier))
                m_reste = total_panier - m_recu
                
                if st.button("🏁 VALIDER LA VENTE & GÉNÉRER FACTURE"):
                    v_ref = f"FAC-{random.randint(10000,99999)}"
                    v_heure = datetime.now().strftime("%H:%M:%S")
                    v_date = datetime.now().strftime("%d/%m/%Y")
                    
                    # 1. Enregistrement de la vente
                    execute_query("""INSERT INTO sales_history 
                        (bill_ref, client_name, total_amt, paid_amt, debt_amt, currency, time_v, date_v, seller_id, ent_id, json_items) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (v_ref, c_nom.upper(), total_panier, m_recu, m_reste, sel_devise, v_heure, v_date, st.session_state.user, st.session_state.ent_id, json.dumps(items_list)))
                    
                    # 2. Mise à jour du stock
                    for it in items_list:
                        execute_query("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name=? AND ent_id=?", (it['qte'], it['nom'], st.session_state.ent_id))
                    
                    # 3. Création de la dette si nécessaire
                    if m_reste > 0:
                        execute_query("INSERT INTO debt_records (client_name, balance, bill_ref, date_start, ent_id) VALUES (?,?,?,?,?)",
                                     (c_nom.upper(), m_reste, v_ref, v_date, st.session_state.ent_id))
                    
                    st.session_state.last_fac = {"ref": v_ref, "cli": c_nom.upper(), "tot": total_panier, "pay": m_recu, "res": m_reste, "dev": sel_devise, "items": items_list, "date": v_date, "h": v_heure}
                    st.session_state.panier = {}; st.rerun()
    else:
        # --- AFFICHAGE DE LA FACTURE FINALE ---
        f = st.session_state.last_fac
        inf = execute_query("SELECT s_name, s_addr, s_tel, s_head FROM store_profiles WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        bill_html = f"""<div class='bill-box'>
            <h2>{inf[3] if inf[3] else inf[0]}</h2>
            <p>{inf[1]} | Tél: {inf[2]}</p><hr>
            <h3>FACTURE N° {f['ref']}</h3>
            <p>Client: {f['cli']}</p>
            <p>Date: {f['date']} à {f['h']}</p><hr>
            {"".join([f"<p>{i['nom']} x{i['qte']} : {i['st']:,.0f} {f['dev']}</p>" for i in f['items']])}<hr>
            <h3>TOTAL : {f['tot']:,.2f} {f['dev']}</h3>
            <p>PAYÉ : {f['pay']} | RESTE : {f['res']}</p>
        </div>"""
        st.markdown(bill_html, unsafe_allow_html=True)
        
        # Téléchargement Facture HTML
        b64_fac = base64.b64encode(bill_html.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64_fac}" download="Facture_{f["ref"]}.html" style="background:#00FF00; color:black; padding:15px; display:block; text-align:center; border-radius:12px; font-weight:bold; text-decoration:none; margin-top:10px;">💾 ENREGISTRER LA FACTURE SUR LE PC</a>', unsafe_allow_html=True)
        
        if st.button("⬅️ RETOUR À LA CAISSE"): st.session_state.last_fac = None; st.rerun()

# --- 5.3 STOCK / INVENTAIRE (MODIFICATION PAR ID SANS SUPPRESSION) ---
elif nav == "📦 STOCK / INVENTAIRE":
    st.header("📦 GESTION DU STOCK")
    t1, t2 = st.tabs(["📋 LISTE ARTICLES", "➕ AJOUTER / MODIFIER"])
    
    with t1:
        items_db = execute_query("SELECT id, item_name, stock_qty, sell_price FROM inventory WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if items_db:
            for sid, snam, sqty, spri in items_db:
                with st.container():
                    st.markdown(f"""<div class='erp-card'>
                        <h3>ID: {sid} | {snam}</h3>
                        <p>Stock disponible: <b>{sqty}</b></p>
                        <p>Prix de vente: <b>{spri:,.2f} $</b></p>
                    </div>""", unsafe_allow_html=True)
        else: st.info("Aucun article en stock.")

    with t2:
        st.subheader("🛠️ ACTIONS SUR ARTICLES")
        with st.form("inventory_form"):
            f_mode = st.radio("Type d'opération", ["Nouveau Produit", "Mettre à jour par ID"])
            f_id = st.number_input("ID de l'article (uniquement pour modification)", min_value=0)
            f_item = st.text_input("Désignation de l'article").upper()
            f_q = st.number_input("Quantité totale", min_value=0)
            f_pa = st.number_input("Prix d'Achat ($)")
            f_pv = st.number_input("Prix de Vente ($)")
            
            if st.form_submit_button("VALIDER L'ENREGISTREMENT"):
                if f_mode == "Nouveau Produit":
                    execute_query("INSERT INTO inventory (item_name, stock_qty, buy_price, sell_price, ent_id) VALUES (?,?,?,?,?)",
                                 (f_item, f_q, f_pa, f_pv, st.session_state.ent_id))
                    st.success("✅ Article ajouté !")
                else:
                    execute_query("UPDATE inventory SET item_name=?, stock_qty=?, buy_price=?, sell_price=? WHERE id=? AND ent_id=?",
                                 (f_item, f_q, f_pa, f_pv, f_id, st.session_state.ent_id))
                    st.success("✅ Article mis à jour !")
                st.rerun()
        
        st.divider()
        if st.button("🗑️ SUPPRIMER L'ARTICLE (Saisir ID ci-dessus)"):
            execute_query("DELETE FROM inventory WHERE id=? AND ent_id=?", (f_id, st.session_state.ent_id))
            st.warning("Article supprimé."); st.rerun()

# --- 5.4 DÉPENSES / CHARGES ---
elif nav == "💸 DÉPENSES / CHARGES":
    st.header("💸 GESTION DES CHARGES")
    with st.form("expense_form"):
        e_mot = st.text_input("Motif de la dépense (ex: Loyer, Transport, Unités)")
        e_amt = st.number_input("Montant dépensé ($)", min_value=0.1)
        e_cat = st.selectbox("Catégorie", ["LOYER", "SALAIRE", "TRANSPORT", "TAXES", "MARKETING", "AUTRE"])
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            e_date = datetime.now().strftime("%d/%m/%Y")
            execute_query("INSERT INTO company_expenses (motive, amount, date_exp, category, ent_id) VALUES (?,?,?,?,?)",
                         (e_mot.upper(), e_amt, e_date, e_cat, st.session_state.ent_id))
            st.success("✅ Dépense enregistrée !"); st.rerun()
    
    st.subheader("📋 HISTORIQUE DES FRAIS")
    charges = execute_query("SELECT motive, amount, date_exp, category FROM company_expenses WHERE ent_id=? ORDER BY id DESC", (st.session_state.ent_id,), fetch=True)
    if charges:
        for m, a, d, c in charges:
            st.markdown(f"<div class='erp-card'><p><b>{d}</b> | {c}</p><h4>{m} : {a:,.2f} $</h4></div>", unsafe_allow_html=True)

# --- 5.5 DETTES CLIENTS (PAIEMENT PAR TRANCHES) ---
elif nav == "📉 DETTES CLIENTS":
    st.header("📉 SUIVI DES CRÉANCES")
    dettes_db = execute_query("SELECT id, client_name, balance, bill_ref, date_start FROM debt_records WHERE ent_id=? AND status='NON_PAYE'", (st.session_state.ent_id,), fetch=True)
    
    if dettes_db:
        for di, dc, db, dr, ds in dettes_db:
            with st.container():
                st.markdown(f"""<div class='erp-card'>
                    <h3>Client: {dc}</h3>
                    <p>Facture Ref: <b>{dr}</b> | Date: {ds}</p>
                    <h4>RESTE À PAYER: <span style='color:red;'>{db:,.2f} $</span></h4>
                </div>""", unsafe_allow_html=True)
                
                tranche = st.number_input(f"Montant versé par {dc} ($)", 0.0, float(db), key=f"t_pay_{di}")
                if st.button("VALIDER LE PAIEMENT PARTIEL", key=f"b_pay_{di}"):
                    nouveau_solde = db - tranche
                    if nouveau_solde <= 0:
                        execute_query("UPDATE debt_records SET balance=0, status='PAYE' WHERE id=?", (di,))
                    else:
                        execute_query("UPDATE debt_records SET balance=? WHERE id=?", (nouveau_solde, di))
                    st.success("✅ Solde mis à jour !"); st.rerun()
    else:
        st.success("🎉 Félicitations ! Vous n'avez aucune dette client en cours.")

# --- 5.6 RÉGLAGES PROFIL & RESET ---
elif nav == "⚙️ RÉGLAGES PROFIL":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    p_data = execute_query("SELECT s_name, s_addr, s_tel, s_head FROM store_profiles WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
    
    with st.form("settings_form"):
        n_name = st.text_input("Nom de l'Entreprise", p_data[0])
        n_addr = st.text_input("Adresse Physique", p_data[1])
        n_tel = st.text_input("Téléphone Officiel", p_data[2])
        n_head = st.text_input("Slogan / En-tête Facture", p_data[3])
        st.divider()
        n_pwd = st.text_input("Changer le mot de passe (Laisser vide pour garder l'ancien)", type="password")
        
        if st.form_submit_button("METTRE À JOUR LE PROFIL"):
            execute_query("UPDATE store_profiles SET s_name=?, s_addr=?, s_tel=?, s_head=? WHERE ent_id=?", 
                         (n_name.upper(), n_addr, n_tel, n_head, st.session_state.ent_id))
            if n_pwd:
                execute_query("UPDATE accounts SET pwd=? WHERE uid=?", (hashlib.sha256(n_pwd.encode()).hexdigest(), st.session_state.user))
            st.success("✅ Profil mis à jour !"); st.rerun()
    
    st.divider()
    st.subheader("🔴 ZONE DE DANGER")
    if st.button("❗ RÉINITIALISER TOUTE MA BOUTIQUE (RESET)"):
        for table in ["inventory", "sales_history", "debt_records", "company_expenses"]:
            execute_query(f"DELETE FROM {table} WHERE ent_id=?", (st.session_state.ent_id,))
        st.error("💥 Toutes les données de la boutique ont été effacées !"); st.rerun()

# --- 5.7 RAPPORTS VENTES ---
elif nav == "📊 RAPPORTS VENTES":
    st.header("📊 ANALYSE DES VENTES")
    r_date = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    ventes = execute_query("SELECT time_v, bill_ref, client_name, total_amt, seller_id FROM sales_history WHERE ent_id=? AND date_v=?", (st.session_state.ent_id, r_date), fetch=True)
    
    if ventes:
        for t, r, c, am, s in ventes:
            st.markdown(f"<div class='erp-card'><p>{t} | REF: {r}</p><p>Client: {c}</p><h4>Total: {am:,.2f} $</h4><p>Vendeur: {s}</p></div>", unsafe_allow_html=True)
    else: st.info("Aucune vente enregistrée pour cette date.")

# --- 5.8 ÉQUIPE VENDEURS ---
elif nav == "👥 ÉQUIPE VENDEURS":
    st.header("👥 GESTION DES VENDEURS")
    with st.form("vendeur_form"):
        v_id = st.text_input("Identifiant Vendeur (ID)").lower()
        v_pw = st.text_input("Mot de Passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            execute_query("INSERT INTO accounts (uid, pwd, role, ent_id) VALUES (?,?,?,?)",
                         (v_id, hashlib.sha256(v_pw.encode()).hexdigest(), 'VENDEUR', st.session_state.ent_id))
            st.success("✅ Vendeur ajouté avec succès !"); st.rerun()

elif nav == "🚪 QUITTER":
    st.session_state.auth = False; st.rerun()

# FIN DU CODE v2100
