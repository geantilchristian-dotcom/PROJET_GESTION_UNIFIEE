# ==============================================================================
# PROJET : ANASH ERP (BY BALIKA BUSINESS) - VERSION MASTER v2100
# DESIGN : GLASSMORPHISM & COBALT BLUE (BASÉ SUR VOS RÉFÉRENCES)
# LOGIQUE : MULTI-BOUTIQUE, TAUX INDIVIDUEL, GESTION STOCK ID, BÉNÉFICE NET
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import base64
import random

# ------------------------------------------------------------------------------
# 1. ARCHITECTURE VISUELLE : CSS AVANCÉ (MOBILE-FIRST & GLASSMORPHISM)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v2100", layout="wide", initial_sidebar_state="expanded")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'owner': "",
        'current_store': None, 'panier': {}, 'last_fac': None
    })

def local_css():
    st.markdown("""
    <style>
    /* Fond principal avec dégradé cobalt selon vos photos */
    .stApp {
        background: radial-gradient(circle at top right, #0044ff, #001133) !important;
        color: white !important;
    }
    
    /* Effet Glassmorphism pour les containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Message défilant Admin */
    .marquee-container {
        position: fixed; top: 0; left: 0; width: 100%; background: #000;
        color: #00ff00; z-index: 9999; height: 40px; line-height: 40px;
        font-family: 'Courier New', monospace; border-bottom: 2px solid #fff;
    }

    /* Horloge 80mm Stylée */
    .clock-80mm {
        font-size: 80px; font-weight: 900; text-align: center;
        color: #fff; text-shadow: 0 0 20px #00ccff, 0 0 40px #00ccff;
        margin-top: 20px; font-family: 'Orbitron', sans-serif;
    }
    .date-neon {
        font-size: 24px; text-align: center; color: #00ccff;
        text-transform: uppercase; letter-spacing: 5px; margin-bottom: 30px;
    }

    /* Dashboard Metrics */
    .metric-box {
        background: rgba(0, 204, 255, 0.1);
        border-radius: 15px; padding: 20px; text-align: center;
        border: 1px solid #00ccff;
    }

    /* Boutons Tactiles XXL */
    .stButton>button {
        width: 100% !important; height: 65px !important;
        border-radius: 15px !important; font-size: 18px !important;
        background: linear-gradient(135deg, #0077ff, #0033aa) !important;
        color: white !important; border: 1px solid rgba(255,255,255,0.3) !important;
        font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #0077ff; }

    /* Inputs Blancs comme sur les photos */
    input, select, textarea {
        background-color: white !important; color: black !important;
        border-radius: 10px !important; height: 45px !important;
    }

    /* Sidebar Personnalisée ANASH */
    [data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
    [data-testid="stSidebar"] * { color: #333 !important; }
    .status-online { color: #00ff00; font-size: 14px; }
    
    /* Tableaux adaptatifs mobile */
    .mobile-table-row {
        background: white; color: black; padding: 15px;
        border-radius: 10px; margin-bottom: 10px; border-left: 8px solid #0044ff;
    }
    
    /* Facture Stylée */
    .invoice-box {
        background: white; color: black; padding: 30px;
        border-radius: 5px; font-family: 'Courier New', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. LOGIQUE BASE DE DONNÉES (SQLITE MULTI-TENANT)
# ------------------------------------------------------------------------------
DB_FILE = "anash_master_v2100.db"

def db_query(q, p=(), fetch=False):
    with sqlite3.connect(DB_FILE, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(q, p)
        conn.commit()
        return cursor.fetchall() if fetch else None

def init_db():
    # Utilisateurs (SuperAdmin, Gérant, Vendeur)
    db_query("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, owner_id TEXT, 
        status TEXT DEFAULT 'ACTIF', full_name TEXT, tel TEXT)""")
    
    # Boutiques (Un Gérant peut en avoir plusieurs)
    db_query("""CREATE TABLE IF NOT EXISTS stores (
        store_id TEXT PRIMARY KEY, store_name TEXT, owner_id TEXT, 
        address TEXT, tel TEXT, header TEXT, rate REAL DEFAULT 2800.0)""")
    
    # Stock (Produits)
    db_query("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, qty INTEGER, 
        buy_price REAL, sell_price REAL, store_id TEXT)""")
    
    # Ventes
    db_query("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paid REAL, rest REAL, currency TEXT, 
        day TEXT, hour TEXT, seller TEXT, store_id TEXT, items_json TEXT)""")
    
    # Dettes (Paiement par tranches)
    db_query("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, balance REAL, 
        ref_sale TEXT, store_id TEXT, status TEXT DEFAULT 'NON_PAYE')""")
    
    # Dépenses
    db_query("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motive TEXT, amount REAL, 
        day TEXT, store_id TEXT)""")
    
    # Système
    db_query("CREATE TABLE IF NOT EXISTS system_cfg (id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT)")
    
    # Seed Initial
    if not db_query("SELECT * FROM users WHERE uid='admin'", fetch=True):
        db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)", ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMIN', '000'))
    if not db_query("SELECT * FROM system_cfg", fetch=True):
        db_query("INSERT INTO system_cfg VALUES (1, 'ANASH ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION PROFESSIONNEL')")

init_db()
sys_cfg = db_query("SELECT app_name, marquee FROM system_cfg WHERE id=1", fetch=True)[0]

# ------------------------------------------------------------------------------
# 3. AUTHENTIFICATION & INSCRIPTION
# ------------------------------------------------------------------------------
local_css()

if not st.session_state.auth:
    st.markdown(f"<div class='marquee-container'><marquee>{sys_cfg[1]}</marquee></div>", unsafe_allow_html=True)
    
    # Interface Login stylée Glassmorphism
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown(f"""
            <div class='glass-card' style='text-align:center;'>
                <h1 style='color:white;'>{sys_cfg[0]}</h1>
                <p>Identifiez-vous pour accéder à votre espace</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            u_login = st.text_input("Identifiant").lower().strip()
            p_login = st.text_input("Mot de passe", type="password")
            
            col_l1, col_l2 = st.columns(2)
            if col_l1.button("CONNEXION"):
                res = db_query("SELECT pwd, role, owner_id, status FROM users WHERE uid=?", (u_login,), fetch=True)
                if res and hashlib.sha256(p_login.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "PAUSE": st.error("Compte suspendu")
                    else:
                        st.session_state.update({'auth':True, 'user':u_login, 'role':res[0][1], 'owner':res[0][2]})
                        # Si Gérant, charger la première boutique
                        if res[0][1] == "GERANT":
                            st.session_state.current_store = db_query("SELECT store_id FROM stores WHERE owner_id=?", (u_login,), fetch=True)[0][0]
                        elif res[0][1] == "VENDEUR":
                            # Le vendeur est rattaché à une boutique spécifique (owner_id ici stocke le store_id)
                            st.session_state.current_store = res[0][2]
                        st.rerun()
                else: st.error("Identifiants incorrects")
                
            if col_l2.button("CRÉER MON COMPTE"):
                st.info("Contactez l'administrateur ou remplissez le formulaire d'inscription.")

    st.stop()

# ------------------------------------------------------------------------------
# 4. DASHBOARD SUPER ADMIN (GESTION ABONNEMENTS)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.title("🛠️ ADMIN SYSTEM")
    adm_nav = st.sidebar.radio("Navigation", ["Dashboard Global", "Validation Clients", "Réglages Système", "Déconnexion"])
    
    if adm_nav == "Dashboard Global":
        st.header("🌍 État du Système")
        nb_u = db_query("SELECT COUNT(*) FROM users WHERE role='GERANT'", fetch=True)[0][0]
        st.metric("Nombre de Gérants", nb_u)
        
    elif adm_nav == "Validation Clients":
        st.header("👥 Gestion des Comptes Gérants")
        clients = db_query("SELECT uid, full_name, status FROM users WHERE role='GERANT'", fetch=True)
        for u, n, s in clients:
            with st.expander(f"{n} ({u}) - Statut: {s}"):
                c1, c2 = st.columns(2)
                if c1.button("✅ Activer", key=f"ac_{u}"): db_query("UPDATE users SET status='ACTIF' WHERE uid=?", (u,)); st.rerun()
                if c2.button("⏸️ Suspendre", key=f"su_{u}"): db_query("UPDATE users SET status='PAUSE' WHERE uid=?", (u,)); st.rerun()

    elif adm_nav == "Réglages Système":
        with st.form("sys"):
            n_app = st.text_input("Nom App", sys_cfg[0])
            n_mar = st.text_area("Message Marquee", sys_cfg[1])
            if st.form_submit_button("Sauvegarder"):
                db_query("UPDATE system_cfg SET app_name=?, marquee=? WHERE id=1", (n_app, n_mar))
                st.rerun()
    
    if adm_nav == "Déconnexion": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. INTERFACE GÉRANT & VENDEUR (COEUR DE L'APP)
# ------------------------------------------------------------------------------

# -- SIDEBAR PERSONNALISÉE (Comme sur votre photo) --
with st.sidebar:
    st.markdown(f"### 🏪 {st.session_state.user.upper()}")
    st.markdown(f"<span class='status-online'>●</span> Utilisateur : {st.session_state.user.upper()}", unsafe_allow_html=True)
    st.divider()
    
    # Switcher de Boutique pour le Gérant
    if st.session_state.role == "GERANT":
        mes_boutiques = db_query("SELECT store_id, store_name FROM stores WHERE owner_id=?", (st.session_state.user,), fetch=True)
        if mes_boutiques:
            b_list = {b[1]: b[0] for b in mes_boutiques}
            choix_b = st.selectbox("Ma Boutique Active", list(b_list.keys()))
            st.session_state.current_store = b_list[choix_b]
        
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📊 RAPPORTS", "📉 DETTES", "💸 DEPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES", "🚪 QUITTER"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]
    
    choice = st.radio("MENU PRINCIPAL", menu)

# Récupération des infos de la boutique actuelle
s_info = db_query("SELECT store_name, rate, header, address, tel FROM stores WHERE store_id=?", (st.session_state.current_store,), fetch=True)
if not s_info:
    if st.session_state.role == "GERANT":
        st.warning("Veuillez créer votre première boutique dans RÉGLAGES.")
        choice = "⚙️ RÉGLAGES"
    else:
        st.error("Boutique introuvable.")
        st.stop()
else:
    s_info = s_info[0]

# --- 5.1 ACCUEIL (HORLOGE 80MM & DASHBOARD) ---
if choice == "🏠 ACCUEIL":
    # Horloge Digitale et Date
    st.markdown(f"<div class='clock-80mm' id='clock'>{datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='date-neon'>{datetime.now().strftime('%A, %d %B %Y')}</div>", unsafe_allow_html=True)
    
    # Chiffres du jour
    today = datetime.now().strftime("%d/%m/%Y")
    recette = db_query("SELECT SUM(total) FROM sales WHERE store_id=? AND day=?", (st.session_state.current_store, today), fetch=True)[0][0] or 0
    depense = db_query("SELECT SUM(amount) FROM expenses WHERE store_id=? AND day=?", (st.session_state.current_store, today), fetch=True)[0][0] or 0
    benefice = recette - depense
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("RECETTE JOUR", f"{recette:,.2f} $")
    c2.metric("DÉPENSES JOUR", f"{depense:,.2f} $")
    b_color = "normal" if benefice >= 0 else "inverse"
    c3.metric("BÉNÉFICE NET", f"{benefice:,.2f} $", delta=benefice)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Alerte Stock
    alertes = db_query("SELECT item_name, qty FROM stock WHERE store_id=? AND qty < 5", (st.session_state.current_store,), fetch=True)
    if alertes:
        with st.container(border=True):
            st.error("⚠️ ALERTES STOCK BAS")
            for a in alertes:
                st.write(f"❌ {a[0]} (Reste: {a[1]})")

# --- 5.2 CAISSE (MULTI-DEVISE & FACTURE) ---
elif choice == "🛒 CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        devise = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        taux = s_info[1]
        
        # Liste articles
        articles = db_query("SELECT item_name, sell_price, qty FROM stock WHERE store_id=?", (st.session_state.current_store,), fetch=True)
        art_map = {a[0]: (a[1], a[2]) for a in articles}
        
        selected = st.selectbox("🔍 Rechercher un produit...", ["---"] + list(art_map.keys()))
        if selected != "---":
            if art_map[selected][1] > 0:
                st.session_state.panier[selected] = st.session_state.panier.get(selected, 0) + 1
                st.toast(f"Ajouté : {selected}")
            else: st.error("Stock épuisé !")

        if st.session_state.panier:
            st.divider()
            total_v = 0.0; cart_data = []
            for art, qte in list(st.session_state.panier.items()):
                pu_usd = art_map[art][0]
                pu_final = pu_usd if devise == "USD" else pu_usd * taux
                stot = pu_final * qte
                total_v += stot
                cart_data.append({"n": art, "q": qte, "p": pu_final, "s": stot})
                
                with st.container():
                    st.markdown(f"""
                    <div class='mobile-table-row'>
                        <b>{art}</b><br>
                        Qté: {qte} | Sous-total: {stot:,.0f} {devise}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Enlever {art}", key=f"del_{art}"):
                        del st.session_state.panier[art]; st.rerun()

            st.markdown(f"<div class='glass-card' style='font-size:30px; text-align:center;'>TOTAL : {total_v:,.2f} {devise}</div>", unsafe_allow_html=True)
            
            client = st.text_input("Nom du Client", "COMPTANT")
            paye = st.number_input(f"Montant Reçu ({devise})", value=float(total_v))
            reste = total_v - paye
            
            if st.button("🏁 VALIDER ET IMPRIMER"):
                ref = f"AN-{random.randint(1000,9999)}"
                jour = datetime.now().strftime("%d/%m/%Y")
                heure = datetime.now().strftime("%H:%M")
                
                # Enregistrer Vente (On stocke tout en USD dans la DB pour la cohérence des rapports)
                t_usd = total_v if devise == "USD" else total_v / taux
                p_usd = paye if devise == "USD" else paye / taux
                r_usd = reste if devise == "USD" else reste / taux
                
                db_query("""INSERT INTO sales (ref, client, total, paid, rest, currency, day, hour, seller, store_id, items_json) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                         (ref, client.upper(), t_usd, p_usd, r_usd, devise, jour, heure, st.session_state.user, st.session_state.current_store, json.dumps(cart_data)))
                
                # Maj Stock
                for c in cart_data:
                    db_query("UPDATE stock SET qty = qty - ? WHERE item_name=? AND store_id=?", (c['qte'], c['n'], st.session_state.current_store))
                
                # Si dette
                if r_usd > 0:
                    db_query("INSERT INTO debts (client, balance, ref_sale, store_id) VALUES (?,?,?,?)", (client.upper(), r_usd, ref, st.session_state.current_store))
                
                st.session_state.last_fac = {"ref": ref, "cli": client, "tot": total_v, "pay": paye, "res": reste, "dev": devise, "items": cart_data, "h": heure, "d": jour}
                st.session_state.panier = {}; st.rerun()
    else:
        # Affichage Facture
        f = st.session_state.last_fac
        fac_html = f"""
        <div class='invoice-box'>
            <h2 style='text-align:center;'>{s_info[2] if s_info[2] else s_info[0]}</h2>
            <p style='text-align:center;'>{s_info[3]} | Tel: {s_info[4]}</p>
            <hr>
            <p><b>REF: {f['ref']}</b> | Date: {f['d']} {f['h']}</p>
            <p>Client: {f['cli'].upper()}</p>
            <hr>
            {"".join([f"<p>{i['n']} x{i['q']} ... {i['s']:,.0f} {f['dev']}</p>" for i in f['items']])}
            <hr>
            <h3>TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            <p>PAYÉ: {f['pay']:,.2f} | RESTE: {f['res']:,.2f}</p>
            <p style='text-align:center; font-size:10px;'>Merci de votre confiance !</p>
        </div>
        """
        st.markdown(fac_html, unsafe_allow_html=True)
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.last_fac = None; st.rerun()

# --- 5.3 STOCK (GESTION PAR ID & INVENTAIRE) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DU STOCK")
    t1, t2 = st.tabs(["📋 INVENTAIRE", "➕ AJOUTER / MODIFIER"])
    
    with t1:
        st.subheader("Liste des produits")
        items = db_query("SELECT id, item_name, qty, buy_price, sell_price FROM stock WHERE store_id=?", (st.session_state.current_store,), fetch=True)
        for i_id, i_nom, i_q, i_p, i_s in items:
            with st.container():
                st.markdown(f"""
                <div class='mobile-table-row'>
                    <b>ID: {i_id} | {i_nom}</b><br>
                    En stock: {i_q} | Prix Vente: {i_s} $
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🗑️ Supprimer un article")
        del_id = st.number_input("Entrez l'ID de l'article à supprimer", min_value=0)
        if st.button("SUPPRIMER DÉFINITIVEMENT"):
            db_query("DELETE FROM stock WHERE id=? AND store_id=?", (del_id, st.session_state.current_store))
            st.success("Article supprimé"); st.rerun()

    with t2:
        with st.form("stk"):
            mode = st.radio("Action", ["Nouveau", "Modifier via ID"])
            f_id = st.number_input("ID (si modification)", 0)
            f_nom = st.text_input("Désignation")
            f_q = st.number_input("Quantité", 0)
            f_pa = st.number_input("Prix Achat ($)")
            f_pv = st.number_input("Prix Vente ($)")
            if st.form_submit_button("VALIDER"):
                if mode == "Nouveau":
                    db_query("INSERT INTO stock (item_name, qty, buy_price, sell_price, store_id) VALUES (?,?,?,?,?)",
                             (f_nom.upper(), f_q, f_pa, f_pv, st.session_state.current_store))
                else:
                    db_query("UPDATE stock SET item_name=?, qty=?, buy_price=?, sell_price=? WHERE id=? AND store_id=?",
                             (f_nom.upper(), f_q, f_pa, f_pv, f_id, st.session_state.current_store))
                st.rerun()

# --- 5.4 RAPPORTS & HISTORIQUE ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DES ACTIVITÉS")
    f_date = st.date_input("Filtrer par date", datetime.now()).strftime("%d/%m/%Y")
    histo = db_query("SELECT ref, client, total, hour, seller FROM sales WHERE store_id=? AND day=?", (st.session_state.current_store, f_date), fetch=True)
    
    for r, c, t, h, s in histo:
        with st.container():
            st.markdown(f"""
            <div class='mobile-table-row'>
                <b>{h} | REF: {r}</b><br>
                Client: {c} | Total: {t:,.2f} $<br>
                Vendeur: {s}
            </div>
            """, unsafe_allow_html=True)
    
    total_j = sum([x[2] for x in histo])
    st.markdown(f"### Total Journée : {total_j:,.2f} $")

# --- 5.5 DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉANCES CLIENTS")
    dettes = db_query("SELECT id, client, balance, ref_sale FROM debts WHERE store_id=? AND status='NON_PAYE'", (st.session_state.current_store,), fetch=True)
    
    if not dettes: st.success("Aucune dette !")
    for d_id, d_cli, d_bal, d_ref in dettes:
        with st.container():
            st.markdown(f"<div class='mobile-table-row'><b>{d_cli}</b> (Réf: {d_ref})<br>Reste : {d_bal:,.2f} $</div>", unsafe_allow_html=True)
            v_pay = st.number_input(f"Verser pour {d_cli} ($)", 0.0, float(d_bal), key=f"p_{d_id}")
            if st.button("VALIDER TRANCHE", key=f"b_{d_id}"):
                nouveau = d_bal - v_pay
                if nouveau <= 0:
                    db_query("UPDATE debts SET balance=0, status='PAYE' WHERE id=?", (d_id,))
                else:
                    db_query("UPDATE debts SET balance=? WHERE id=?", (nouveau, d_id))
                st.rerun()

# --- 5.6 DEPENSES ---
elif choice == "💸 DEPENSES":
    st.header("💸 SORTIES DE CAISSE")
    with st.form("exp"):
        mot = st.text_input("Motif")
        amt = st.number_input("Montant ($)")
        if st.form_submit_button("ENREGISTRER"):
            db_query("INSERT INTO expenses (motive, amount, day, store_id) VALUES (?,?,?,?)", 
                     (mot.upper(), amt, datetime.now().strftime("%d/%m/%Y"), st.session_state.current_store))
            st.rerun()

# --- 5.7 GESTION DES VENDEURS ---
elif choice == "👥 VENDEURS":
    st.header("👥 MES EMPLOYÉS")
    with st.form("vend"):
        v_id = st.text_input("ID Vendeur").lower()
        v_nm = st.text_input("Nom Complet")
        v_pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            db_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                     (v_id, hashlib.sha256(v_pw.encode()).hexdigest(), 'VENDEUR', st.session_state.current_store, 'ACTIF', v_nm, ""))
            st.success("Vendeur ajouté !")
            
    st.subheader("Liste des vendeurs")
    vendeurs = db_query("SELECT uid, full_name FROM users WHERE owner_id=? AND role='VENDEUR'", (st.session_state.current_store,), fetch=True)
    for vi, vn in vendeurs:
        st.write(f"👤 {vn} (ID: {vi})")
        if st.button(f"Supprimer {vi}"):
            db_query("DELETE FROM users WHERE uid=?", (vi,))
            st.rerun()

# --- 5.8 RÉGLAGES & MULTI-BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION & BOUTIQUES")
    
    # Ajouter une boutique
    with st.expander("➕ CRÉER UNE NOUVELLE BOUTIQUE"):
        with st.form("new_st"):
            ns_id = st.text_input("ID Unique Boutique (ex: depot1)").lower()
            ns_nm = st.text_input("Nom de l'Enseigne")
            ns_rt = st.number_input("Taux de change (1$ = ? CDF)", 2800.0)
            if st.form_submit_button("CRÉER"):
                db_query("INSERT INTO stores (store_id, store_name, owner_id, rate) VALUES (?,?,?,?)", (ns_id, ns_nm, st.session_state.user, ns_rt))
                st.session_state.current_store = ns_id
                st.rerun()

    # Modifier boutique actuelle
    st.subheader(f"Paramètres de : {s_info[0]}")
    with st.form("edit_st"):
        e_nm = st.text_input("Nom Enseigne", s_info[0])
        e_rt = st.number_input("Taux de change", s_info[1])
        e_hd = st.text_input("En-tête Facture", s_info[2])
        e_ad = st.text_input("Adresse", s_info[3])
        e_tl = st.text_input("Téléphone", s_info[4])
        if st.form_submit_button("METTRE À JOUR"):
            db_query("UPDATE stores SET store_name=?, rate=?, header=?, address=?, tel=? WHERE store_id=?", (e_nm, e_rt, e_hd, e_ad, e_tl, st.session_state.current_store))
            st.rerun()

    st.divider()
    st.subheader("🔴 ZONE DANGER")
    if st.button("RÉINITIALISER TOUTES LES DONNÉES DE CETTE BOUTIQUE"):
        for t in ["stock", "sales", "debts", "expenses"]:
            db_query(f"DELETE FROM {t} WHERE store_id=?", (st.session_state.current_store,))
        st.error("Données effacées !"); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.auth = False; st.rerun()
