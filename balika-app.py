# ==============================================================================
# BALIKA ERP v210 - SYSTÈME DE GESTION MULTI-ABONNÉS (VERSION MAÎTRE)
# ARCHITECTURE : SUPER_ADMIN | BOSS_CLIENT | VENDEUR
# DÉVELOPPÉ POUR MOBILES ET ORDINATEURS - 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64
from PIL import Image
import io

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & STYLE CSS (MOBILE OPTIMIZED)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v210", layout="wide", initial_sidebar_state="collapsed")

def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&family=Roboto:wght@400;700&display=swap');
    
    /* Fond dégradé dynamique pour lisibilité */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        font-family: 'Roboto', sans-serif;
    }

    /* Message défilant persistant (Marquee) */
    .marquee-fixed {
        position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;
        padding: 10px 0; font-weight: bold; font-size: 1.1rem;
        box-shadow: 0 2px 15px rgba(0,0,0,0.5);
    }
    .marquee-content {
        display: inline-block; white-space: nowrap;
        animation: marquee 25s linear infinite;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* Montre LCD Centrée */
    .watch-container {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; margin: 40px 0; padding: 20px;
        background: rgba(0,0,0,0.4); border-radius: 30px;
        border: 2px solid rgba(255,255,255,0.1);
    }
    .watch-time {
        font-family: 'Orbitron', sans-serif; font-size: 4rem;
        color: #00d4ff; text-shadow: 0 0 20px #00d4ff; margin: 0;
    }
    .watch-date { font-size: 1.2rem; color: #ffffff; letter-spacing: 3px; }

    /* Login Box */
    .login-card {
        background: rgba(255, 255, 255, 0.95); padding: 40px;
        border-radius: 25px; color: #1e3c72; text-align: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4); margin-top: 50px;
    }

    /* Cadre Total Caisse */
    .total-frame {
        background: #ffffff; border: 5px solid #ff9800; border-radius: 15px;
        padding: 20px; color: #1e3c72; font-size: 2.5rem;
        font-weight: 900; text-align: center; margin: 15px 0;
    }

    /* Boutons */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5rem;
        font-weight: bold; font-size: 1.1rem; text-transform: uppercase;
    }
    
    /* Facture Format A4 et 80mm */
    .invoice-box {
        background: white; color: black; padding: 20px;
        border-radius: 5px; font-family: 'Courier New', Courier, monospace;
        line-height: 1.2;
    }
    .centered-text { text-align: center; }
    
    /* Responsive adjustment */
    @media (max-width: 768px) {
        .watch-time { font-size: 2.5rem; }
        .total-frame { font-size: 1.8rem; }
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES
# ------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect('balika_master_v210.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Table Système (Pour vous, Super Admin)
    c.execute("""CREATE TABLE IF NOT EXISTS system_config (
                 id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
                 marquee_color TEXT, global_status TEXT)""")
    
    # Table Abonnés (Les Boutiques)
    c.execute("""CREATE TABLE IF NOT EXISTS subscribers (
                 ent_id TEXT PRIMARY KEY, ent_name TEXT, boss_user TEXT, 
                 boss_pass TEXT, status TEXT, date_joined TEXT, 
                 header_info TEXT, seal BLOB, signature BLOB)""")
    
    # Table Utilisateurs (Boss et Vendeurs)
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                 ent_id TEXT, photo BLOB)""")
    
    # Table Produits
    c.execute("""CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                 stock_initial INTEGER, stock_actuel INTEGER, 
                 prix_vente REAL, devise TEXT, ent_id TEXT)""")
    
    # Table Ventes
    c.execute("""CREATE TABLE IF NOT EXISTS sales (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                 total REAL, paye REAL, reste REAL, devise TEXT, 
                 date_s TEXT, items TEXT, seller TEXT, ent_id TEXT)""")
    
    # Table Dettes
    c.execute("""CREATE TABLE IF NOT EXISTS debts (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, 
                 montant REAL, devise TEXT, ref_s TEXT, ent_id TEXT)""")

    # Insertion Initiale Super Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)", 
                  ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'SUPER_ADMIN', 'SYSTEM', None))
        c.execute("INSERT INTO system_config VALUES (?,?,?,?,?)", 
                  (1, 'BALIKA ERP PREMIMUM', 'BIENVENUE SUR VOTRE ERP GESTION PRO', '#FFD700', 'ACTIVE'))
    
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------------------
# 3. FONCTIONS UTILES
# ------------------------------------------------------------------------------
def run_query(q, p=(), fetch=True):
    conn = get_db()
    c = conn.cursor()
    c.execute(q, p)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

def img_to_bytes(img_file):
    return img_file.read() if img_file else None

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION STYLISÉ
# ------------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# Récupération config système pour le Marquee
sys_conf = run_query("SELECT app_name, marquee_text, marquee_color FROM system_config WHERE id=1")[0]

# Affichage Marquee
st.markdown(f"""
    <div class="marquee-fixed" style="background: {sys_conf[2]}; color: #000;">
        <div class="marquee-content">{sys_conf[1]} | {sys_conf[0]}</div>
    </div>
    <div style="height: 50px;"></div>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(f'<div class="login-card"><h1>{sys_conf[0]}</h1><p>Veuillez vous identifier</p>', unsafe_allow_html=True)
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            pw = hashlib.sha256(p.encode()).hexdigest()
            user_data = run_query("SELECT role, ent_id FROM users WHERE username=? AND password=?", (u, pw))
            if user_data:
                # Vérifier si l'abonné est actif
                role, eid = user_data[0]
                if role != 'SUPER_ADMIN':
                    sub_stat = run_query("SELECT status FROM subscribers WHERE ent_id=?", (eid,))
                    if sub_stat and sub_stat[0][0] != 'ACTIF':
                        st.error("Votre compte est suspendu. Contactez l'administrateur.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user, st.session_state.role, st.session_state.ent_id = u, role, eid
                        st.rerun()
                else:
                    st.session_state.logged_in = True
                    st.session_state.user, st.session_state.role, st.session_state.ent_id = u, role, eid
                    st.rerun()
            else:
                st.error("Identifiants incorrects")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN (GESTION SYSTÈME ET ABONNÉS)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    st.sidebar.title("💎 SUPER ADMIN")
    menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Gérer Abonnés", "Réglages Système", "Mon Profil"])

    if menu == "Tableau de Bord":
        st.title("Contrôle Central")
        total_subs = run_query("SELECT COUNT(*) FROM subscribers")[0][0]
        st.metric("Nombre d'abonnés", total_subs)
        
    elif menu == "Gérer Abonnés":
        st.subheader("Liste des boutiques abonnées")
        with st.expander("➕ Créer un nouvel abonné"):
            with st.form("new_sub"):
                n_ent = st.text_input("Nom de l'entreprise")
                n_boss = st.text_input("Utilisateur Boss")
                n_pass = st.text_input("Mot de passe Boss", type="password")
                if st.form_submit_button("Enregistrer l'abonné"):
                    eid = f"ENT-{random.randint(1000,9999)}"
                    hp = hashlib.sha256(n_pass.encode()).hexdigest()
                    run_query("INSERT INTO subscribers (ent_id, ent_name, boss_user, boss_pass, status, date_joined) VALUES (?,?,?,?,?,?)",
                              (eid, n_ent.upper(), n_boss, hp, 'ACTIF', datetime.now().strftime("%d/%m/%Y")), fetch=False)
                    run_query("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
                              (n_boss, hp, 'BOSS', eid), fetch=False)
                    st.success(f"Abonné {n_ent} créé avec ID: {eid}")
                    st.rerun()

        subs = run_query("SELECT ent_id, ent_name, status, date_joined FROM subscribers")
        for s_id, s_name, s_stat, s_date in subs:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2,1,1,1])
                c1.write(f"**{s_name}** ({s_id})")
                c2.write(f"Statut: {s_stat}")
                if c3.button("Pause/Activer", key=f"p_{s_id}"):
                    new_s = 'SUSPENDU' if s_stat == 'ACTIF' else 'ACTIF'
                    run_query("UPDATE subscribers SET status=? WHERE ent_id=?", (new_s, s_id), fetch=False)
                    st.rerun()
                if c4.button("Supprimer", key=f"d_{s_id}"):
                    run_query("DELETE FROM subscribers WHERE ent_id=?", (s_id,), fetch=False)
                    run_query("DELETE FROM users WHERE ent_id=?", (s_id,), fetch=False)
                    st.rerun()

    elif menu == "Réglages Système":
        st.subheader("Configuration Global de l'App")
        with st.form("sys_form"):
            new_app = st.text_input("Nom de l'App", sys_conf[0])
            new_txt = st.text_area("Message défilant", sys_conf[1])
            new_col = st.color_picker("Couleur Marquee", sys_conf[2])
            if st.form_submit_button("Sauvegarder Global"):
                run_query("UPDATE system_config SET app_name=?, marquee_text=?, marquee_color=? WHERE id=1",
                          (new_app, new_txt, new_col), fetch=False)
                st.rerun()

# ------------------------------------------------------------------------------
# 6. ESPACE BOSS CLIENT & VENDEUR
# ------------------------------------------------------------------------------
else:
    ENT_ID = st.session_state.ent_id
    ROLE = st.session_state.role
    
    # Infos Boutique
    b_info = run_query("SELECT ent_name, header_info, seal, signature FROM subscribers WHERE ent_id=?", (ENT_ID,))[0]
    
    # Sidebar Navigation
    st.sidebar.markdown(f"<h2 style='text-align:center;'>{b_info[0]}</h2>", unsafe_allow_html=True)
    if ROLE == 'BOSS':
        nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES"]
    else:
        nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    choice = st.sidebar.radio("Menu", nav)

    # --- ACCUEIL (MONTRE STYLÉE) ---
    if choice == "🏠 ACCUEIL":
        st.markdown(f"""
            <div class="watch-container">
                <div class="watch-time">{datetime.now().strftime('%H:%M')}</div>
                <div class="watch-date">{datetime.now().strftime('%A, %d %B %Y')}</div>
            </div>
            <h2 style='text-align:center;'>Bienvenue, {st.session_state.user.upper()}</h2>
        """, unsafe_allow_html=True)

    # --- CAISSE (FORMATS D'IMPRESSION) ---
    elif choice == "🛒 CAISSE":
        st.title("🛒 Terminal de Vente")
        if 'cart' not in st.session_state: st.session_state.cart = {}
        
        c_devise = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        
        # Sélection article
        prods = run_query("SELECT designation, prix_vente, stock_actuel, devise FROM products WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,))
        p_list = {p[0]: (p[1], p[2], p[3]) for p in prods}
        
        col_s1, col_s2 = st.columns([3, 1])
        item_sel = col_s1.selectbox("Article", [""] + list(p_list.keys()))
        if col_s2.button("➕ AJOUTER") and item_sel:
            st.session_state.cart[item_sel] = st.session_state.cart.get(item_sel, 0) + 1
        
        if st.session_state.cart:
            total = 0
            details = []
            st.write("---")
            for it, qte in list(st.session_state.cart.items()):
                px, stock, dev_orig = p_list[it]
                # Logique prix ici simplifiée
                st.write(f"**{it}** - {qte} x {px} {dev_orig}")
                total += (px * qte)
                details.append({"art": it, "qte": qte, "px": px})
                if st.button("Supprimer", key=f"del_{it}"):
                    del st.session_state.cart[it]
                    st.rerun()
            
            st.markdown(f'<div class="total-frame">TOTAL : {total:,.2f} {c_devise}</div>', unsafe_allow_html=True)
            
            with st.form("valider"):
                cli = st.text_input("Nom du Client", "COMPTANT")
                paye = st.number_input("Montant Reçu", value=float(total))
                fmt = st.selectbox("Format d'impression", ["80mm", "A4 Administrative"])
                if st.form_submit_button("🔥 VALIDER ET IMPRIMER"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    reste = total - paye
                    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    # Enregistrement
                    run_query("INSERT INTO sales (ref, client, total, paye, reste, devise, date_s, items, seller, ent_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (ref, cli.upper(), total, paye, reste, c_devise, date_now, json.dumps(details), st.session_state.user, ENT_ID), fetch=False)
                    # Update stock
                    for d in details:
                        run_query("UPDATE products SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (d['qte'], d['art'], ENT_ID), fetch=False)
                    # Si dette
                    if reste > 0:
                        run_query("INSERT INTO debts (client, montant, devise, ref_s, ent_id) VALUES (?,?,?,?,?)",
                                  (cli.upper(), reste, c_devise, ref, ENT_ID), fetch=False)
                    
                    st.session_state.last_sale = (ref, cli, total, paye, reste, c_devise, details, fmt)
                    st.session_state.cart = {}
                    st.success("Vente réussie !")

        if 'last_sale' in st.session_state:
            ls = st.session_state.last_sale
            st.markdown(f"<div class='invoice-box {'centered-text' if ls[7]=='80mm' else ''}'>", unsafe_allow_html=True)
            st.write(f"### {b_info[0]}")
            st.write(f"{b_info[1]}")
            st.write(f"**FACTURE : {ls[0]}** | Date : {datetime.now().strftime('%d/%m/%Y')}")
            st.write(f"Client : {ls[1]}")
            st.write("---")
            for i in ls[6]: st.write(f"{i['art']} x {i['qte']} : {i['px']*i['qte']:,.1f}")
            st.write("---")
            st.write(f"**TOTAL : {ls[2]:,.1f} {ls[5]}**")
            st.write(f"Payé : {ls[3]:,.1f} | Reste : {ls[4]:,.1f}")
            
            if ls[7] == "A4 Administrative":
                col_f1, col_f2 = st.columns(2)
                if b_info[2]: col_f1.image(b_info[2], caption="Sceau", width=100)
                if b_info[3]: col_f2.image(b_info[3], caption="Signature", width=100)
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.button("🖨️ Imprimer / Partager")

    # --- STOCK (MODIFICATION ET INITIAL) ---
    elif choice == "📦 STOCK" and ROLE == "BOSS":
        st.title("Gestion des Stocks")
        with st.expander("➕ Nouveau Produit"):
            with st.form("p_add"):
                d = st.text_input("Désignation")
                q = st.number_input("Stock Initial", min_value=1)
                p = st.number_input("Prix de Vente")
                dv = st.selectbox("Devise", ["USD", "CDF"])
                if st.form_submit_button("Ajouter"):
                    run_query("INSERT INTO products (designation, stock_initial, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?,?)",
                              (d.upper(), q, q, p, dv, ENT_ID), fetch=False)
                    st.rerun()
        
        prods = run_query("SELECT id, designation, stock_initial, stock_actuel, prix_vente, devise FROM products WHERE ent_id=?", (ENT_ID,))
        df = pd.DataFrame(prods, columns=["ID", "Désignation", "Initial", "Actuel", "Prix", "Devise"])
        st.dataframe(df, use_container_width=True)
        
        st.subheader("Modifier Prix / Supprimer")
        sel_id = st.selectbox("Choisir produit par ID", df["ID"])
        new_px = st.number_input("Nouveau Prix")
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("Mettre à jour le prix"):
            run_query("UPDATE products SET prix_vente=? WHERE id=?", (new_px, sel_id), fetch=False)
            st.rerun()
        if col_b2.button("🗑️ Supprimer le produit", type="primary"):
            run_query("DELETE FROM products WHERE id=?", (sel_id,), fetch=False)
            st.rerun()

    # --- VENDEURS (BOSS SEULEMENT) ---
    elif choice == "👥 VENDEURS" and ROLE == "BOSS":
        st.title("Gestion du Personnel")
        with st.form("v_add"):
            vn = st.text_input("Nom du Vendeur")
            vp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Créer compte Vendeur"):
                hp = hashlib.sha256(vp.encode()).hexdigest()
                run_query("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (vn.lower(), hp, 'VENDEUR', ENT_ID), fetch=False)
                st.success("Vendeur ajouté")
        
        vendeurs = run_query("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,))
        for v in vendeurs:
            col_v1, col_v2 = st.columns([3,1])
            col_v1.write(f"👤 {v[0].upper()}")
            if col_v2.button("Supprimer", key=f"del_{v[0]}"):
                run_query("DELETE FROM users WHERE username=?", (v[0],), fetch=False)
                st.rerun()

    # --- RÉGLAGES (SCEAU ET SIGNATURE) ---
    elif choice == "⚙️ RÉGLAGES" and ROLE == "BOSS":
        st.title("Paramètres Boutique")
        with st.form("cfg_boss"):
            new_h = st.text_area("Entête de Facture (Adresse, Tel, etc.)", b_info[1])
            sc = st.file_uploader("Importer Sceau (PNG)", type=['png'])
            sg = st.file_uploader("Importer Signature (PNG)", type=['png'])
            if st.form_submit_button("Sauvegarder Réglages"):
                run_query("UPDATE subscribers SET header_info=? WHERE ent_id=?", (new_h, ENT_ID), fetch=False)
                if sc: run_query("UPDATE subscribers SET seal=? WHERE ent_id=?", (img_to_bytes(sc), ENT_ID), fetch=False)
                if sg: run_query("UPDATE subscribers SET signature=? WHERE ent_id=?", (img_to_bytes(sg), ENT_ID), fetch=False)
                st.rerun()

    # --- DÉCONNEXION ---
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.logged_in = False
        st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v210
# ------------------------------------------------------------------------------
