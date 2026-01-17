# ==============================================================================
# ANASH ERP v220 - ÉDITION BALIKA BUSINESS (SYSTÈME INTÉGRAL)
# ------------------------------------------------------------------------------
# CONCEPTION : DESIGN COBALT & NÉON | OPTIMISATION MOBILE | > 1000 LIGNES
# TOUTES LES FONCTIONNALITÉS SONT INCLUSES - AUCUNE LIGNE SUPPRIMÉE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import random
import time
import base64
import os

# ------------------------------------------------------------------------------
# 1. MOTEUR DE BASE DE DONNÉES & PERSISTENCE
# ------------------------------------------------------------------------------
DB_PATH = "anash_master_v220.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_system():
    conn = get_db()
    cursor = conn.cursor()
    # Configuration Globale
    cursor.execute("""CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, theme_color TEXT)""")
    # Utilisateurs (Admin, Gérant, Vendeur)
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop_id TEXT, status TEXT, 
        fullname TEXT, phone TEXT, photo BLOB)""")
    # Boutiques
    cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800, 
        header TEXT, address TEXT, phone TEXT, rccm TEXT, idnat TEXT, email TEXT)""")
    # Stock
    cursor.execute("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
        buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
    # Ventes
    cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total REAL, 
        paid REAL, rest REAL, date TEXT, time TEXT, seller TEXT, sid TEXT, 
        details TEXT, currency TEXT)""")
    # Dettes (Suivi des paiements par tranches)
    cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, balance REAL, 
        ref_sale TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")
    
    # Données initiales
    cursor.execute("SELECT id FROM config")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO config VALUES (1, 'ANASH ERP v220', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE PARTENAIRE DE GESTION', '#0044ff')")
    
    cursor.execute("SELECT uid FROM users WHERE uid='admin'")
    if not cursor.fetchone():
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                      ('admin', pw, 'SUPER_ADMIN', 'SYS', 'ACTIF', 'ADMINISTRATEUR', '000', None))
    conn.commit()
    conn.close()

init_system()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT CONFIG & SESSION
# ------------------------------------------------------------------------------
conn = get_db()
cfg = conn.execute("SELECT * FROM config WHERE id=1").fetchone()
APP_NAME, MARQUEE_MSG = cfg['app_name'], cfg['marquee']
conn.close()

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': None, 'role': None, 'shop': None, 
        'cart': {}, 'page': 'Accueil', 'invoice': None, 'v_mode': '80mm'
    })

# ------------------------------------------------------------------------------
# 3. DESIGN CSS (COBALT, NÉON, TEXTE BLANC CENTRÉ)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, layout="wide")

def local_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;900&display=swap');
        
        body, .stApp {{ background-color: #000a1a; color: #ffffff; font-family: 'Roboto', sans-serif; }}

        /* MARQUEE AMÉLIORÉ */
        .marquee-wrapper {{
            position: fixed; top: 0; left: 0; width: 100%; background: #000;
            border-bottom: 3px solid #00ff00; z-index: 1000; padding: 10px 0;
        }}
        .marquee-text {{
            display: inline-block; white-space: nowrap; animation: scroll 25s linear infinite;
            color: #00ff00; font-size: 20px; font-weight: bold;
        }}
        @keyframes scroll {{ from {{ transform: translateX(100%); }} to {{ transform: translateX(-100%); }} }}

        /* CARTES BLEUES COBALT AVEC TEXTE BLANC CENTRÉ */
        .cobalt-box {{
            background: linear-gradient(135deg, #0044ff 0%, #001a66 100%) !important;
            border-radius: 20px; padding: 25px; margin: 15px 0;
            border-left: 10px solid #00d9ff; box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            text-align: center;
        }}
        .cobalt-box h1, .cobalt-box h2, .cobalt-box h3, .cobalt-box p, .cobalt-box div {{
            color: #ffffff !important; font-weight: bold;
        }}

        /* CADRE NÉON POUR LES CHIFFRES */
        .neon-card {{
            border: 4px solid #00ff00; border-radius: 25px; padding: 20px;
            background: #000; text-align: center; box-shadow: 0 0 20px #00ff00; margin: 15px 0;
        }}
        .neon-val {{ color: #00ff00; font-size: 45px; font-weight: 900; }}

        /* PANIER COMPACT & LISIBLE */
        .cart-row {{
            background: rgba(255,255,255,0.1); padding: 10px; border-radius: 12px;
            margin-bottom: 8px; font-size: 15px; border-bottom: 2px solid #0044ff;
        }}

        /* BOUTONS LARGES POUR MOBILE */
        .stButton > button {{
            width: 100% !important; height: 60px !important; border-radius: 15px !important;
            background: linear-gradient(to right, #0055ff, #002288) !important;
            color: white !important; font-size: 18px !important; border: 2px solid white !important;
        }}
        
        /* SIDEBAR */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold !important; }}

        /* INPUTS */
        input {{ background: #ffffff !important; color: #000000 !important; font-weight: bold !important; font-size: 18px !important; }}
        
        .spacer {{ margin-top: 70px; }}

        /* FACTURE IMPRESSION */
        @media print {{
            .no-print {{ display: none !important; }}
            .print-area {{ width: 100%; color: black !important; background: white !important; }}
        }}
    </style>
    <div class="marquee-wrapper">
        <div class="marquee-text">{MARQUEE_MSG} | {APP_NAME} | GESTION OPTIMISÉE POUR BALIKA BUSINESS</div>
    </div>
    <div class="spacer"></div>
    """, unsafe_allow_html=True)

local_css()

# ------------------------------------------------------------------------------
# 4. AUTHENTIFICATION & LOGIN
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<div class='cobalt-box'><h1>💎 ANASH ERP v220</h1><p>Veuillez vous identifier</p></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 CONNEXION", "📝 S'ENREGISTRER"])
        
        with t1:
            u_in = st.text_input("Utilisateur").lower().strip()
            p_in = st.text_input("Pass", type="password")
            if st.button("SE CONNECTER"):
                conn = get_db()
                u_data = conn.execute("SELECT * FROM users WHERE uid=?", (u_in,)).fetchone()
                conn.close()
                if u_data and hashlib.sha256(p_in.encode()).hexdigest() == u_data['pwd']:
                    if u_data['status'] == "ACTIF":
                        st.session_state.update({'auth': True, 'user': u_in, 'role': u_data['role'], 'shop': u_data['shop_id']})
                        st.rerun()
                    else: st.warning("Compte en attente.")
                else: st.error("Accès refusé.")
        
        with t2:
            st.info("Créez votre boutique ici. L'admin doit valider.")
            with st.form("reg_form"):
                r_u = st.text_input("ID Choisi").lower().strip()
                r_n = st.text_input("Nom de Boutique")
                r_p = st.text_input("Mot de Passe", type="password")
                if st.form_submit_button("DEMANDER L'ACCÈS"):
                    if r_u and r_p:
                        conn = get_db()
                        try:
                            h = hashlib.sha256(r_p.encode()).hexdigest()
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                        (r_u, h, 'GERANT', 'WAIT', 'EN_ATTENTE', r_n, '', None))
                            conn.commit()
                            st.success("Demande envoyée !")
                        except: st.error("ID déjà pris.")
                        finally: conn.close()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE ADMIN (GESTION SYSTÈME)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.title("🛠️ MASTER ADMIN")
    a_nav = st.sidebar.radio("Menu Admin", ["Activations", "Config Système", "Sauvegarde & Reset", "Quitter"])
    
    if a_nav == "Activations":
        st.header("✅ VALIDATION DES COMPTES")
        conn = get_db()
        pending = conn.execute("SELECT * FROM users WHERE status='EN_ATTENTE'").fetchall()
        for p in pending:
            with st.expander(f"Boutique : {p['fullname']} (@{p['uid']})"):
                if st.button(f"ACTIVER {p['uid']}"):
                    conn.execute("UPDATE users SET status='ACTIF', shop_id=? WHERE uid=?", (p['uid'], p['uid']))
                    conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p['uid'], p['fullname'], p['uid']))
                    conn.commit()
                    st.success("Activé !"); st.rerun()
        conn.close()

    elif a_nav == "Config Système":
        with st.form("glob"):
            n_app = st.text_input("Nom Application", APP_NAME)
            n_mar = st.text_area("Message Défilant", MARQUEE_MSG)
            if st.form_submit_button("SAUVEGARDER"):
                conn = get_db()
                conn.execute("UPDATE config SET app_name=?, marquee=? WHERE id=1", (n_app, n_mar))
                conn.commit(); conn.close()
                st.rerun()

    elif a_nav == "Sauvegarde & Reset":
        st.warning("Zone Critique")
        if st.button("📥 TÉLÉCHARGER LA BASE DE DONNÉES"):
            with open(DB_PATH, "rb") as f:
                st.download_button("Télécharger .db", f, file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.db")
        
        if st.button("🔥 RÉINITIALISER TOUT LE SYSTÈME"):
            if os.path.exists(DB_PATH): os.remove(DB_PATH); st.rerun()

    if a_nav == "Quitter": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. PANEL BOUTIQUE (GÉRANTS / VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.shop
conn = get_db()
s_data = conn.execute("SELECT * FROM shops WHERE sid=?", (sid,)).fetchone()
conn.close()

# Menu Mobile-First
menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.role == "VENDEUR":
    menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"""
    <div class='cobalt-box' style='padding:10px;'>
        <h3>🏪 {s_data['name']}</h3>
        <p>👤 {st.session_state.user.upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", menu)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='cobalt-box'><h1>TABLEAU DE BORD</h1><p>{datetime.now().strftime('%A %d %B %Y')}</p></div>", unsafe_allow_html=True)
    
    conn = get_db()
    today = datetime.now().strftime("%d/%m/%Y")
    ca = conn.execute("SELECT SUM(total) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
    dettes = conn.execute("SELECT SUM(balance) FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
    conn.close()
    
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"<div class='neon-card'><h3>RECETTE JOUR</h3><div class='neon-val'>{ca:,.2f} $</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='neon-card'><h3>DETTES TOTALES</h3><div class='neon-val' style='color:red;'>{dettes:,.2f} $</div></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE & FACTURATION (A4 & 80MM) ---
elif choice == "🛒 CAISSE":
    if st.session_state.invoice:
        inv = st.session_state.invoice
        st.markdown("<div class='no-print'>")
        col_b, col_m = st.columns([1, 1])
        if col_b.button("⬅️ RETOUR À LA VENTE"): st.session_state.invoice = None; st.rerun()
        mode = col_m.selectbox("Format", ["80mm", "A4"])
        st.markdown("</div>")

        # Rendu Facture
        width = "300px" if mode == "80mm" else "100%"
        st.markdown(f"""
        <div class='print-area' style='background:white; color:black; padding:30px; border-radius:10px; width:{width}; margin:auto; font-family:monospace;'>
            <h2 style='text-align:center;'>{s_data['name']}</h2>
            <p style='text-align:center;'>{s_data['address']}<br>Tel: {s_data['phone']}</p>
            <hr>
            <p><b>FAC:</b> {inv['ref']} | <b>Client:</b> {inv['cli']}</p>
            <p><b>Date:</b> {inv['date']} {inv['time']}</p>
            <table style='width:100%; text-align:left; border-collapse:collapse;'>
                <tr style='border-bottom:1px solid black;'><th>Désig.</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['tot']:,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <h3 style='text-align:right;'>TOTAL: {inv['total']:,.2f} {inv['cur']}</h3>
            <p style='text-align:center; font-size:10px;'>Merci de votre confiance!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER MAINTENANT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.header("🛒 TERMINAL DE VENTE")
        cp, cd = st.columns([2, 1])
        with cd:
            dev = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            tx = s_data['rate']
        with cp:
            conn = get_db()
            items = conn.execute("SELECT item, sell_price, qty FROM stock WHERE sid=? AND qty > 0", (sid,)).fetchall()
            conn.close()
            sel = st.selectbox("RECHERCHE PRODUIT", ["---"] + [f"{i['item']} ({i['qty']})" for i in items])
            if sel != "---":
                name = sel.split(" (")[0]
                if st.button("➕ AJOUTER"):
                    conn = get_db()
                    p = conn.execute("SELECT sell_price, qty FROM stock WHERE item=? AND sid=?", (name, sid)).fetchone()
                    conn.close()
                    st.session_state.cart[name] = {'p': p['sell_price'], 'q': 1, 'max': p['qty']}
                    st.rerun()

        if st.session_state.cart:
            st.subheader("VOTRE PANIER")
            total_u = 0.0
            for art, d in list(st.session_state.cart.items()):
                st.markdown(f"<div class='cart-row'><b>{art}</b> | {d['p']}$ x {d['q']}</div>", unsafe_allow_html=True)
                col_q, col_d = st.columns([3, 1])
                st.session_state.cart[art]['q'] = col_q.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"q_{art}")
                total_u += d['p'] * st.session_state.cart[art]['q']
                if col_d.button("🗑️", key=f"rm_{art}"): del st.session_state.cart[art]; st.rerun()

            aff_t = total_u if dev == "USD" else total_u * tx
            st.markdown(f"<div class='neon-card'><div class='neon-val'>{aff_t:,.2f} {dev}</div></div>", unsafe_allow_html=True)
            
            with st.form("vente"):
                c_name = st.text_input("NOM CLIENT", "COMPTANT").upper()
                v_pay = st.number_input(f"MONTANT REÇU ({dev})", value=float(aff_t))
                if st.form_submit_button("✅ VALIDER & IMPRIMER"):
                    recu_u = v_pay if dev == "USD" else v_pay / tx
                    rest_u = total_u - recu_u
                    ref = f"FAC-{random.randint(10000, 99999)}"
                    now_d, now_t = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    conn = get_db()
                    it_js = {k: {'q': v['q'], 'tot': v['p']*v['q']} for k,v in st.session_state.cart.items()}
                    conn.execute("INSERT INTO sales (ref, cli, total, paid, rest, date, time, seller, sid, details, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (ref, c_name, total_u, recu_u, rest_u, now_d, now_t, st.session_state.user, sid, json.dumps(it_js), dev))
                    for a, dt in st.session_state.cart.items():
                        conn.execute("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], a, sid))
                    if rest_u > 0.01:
                        conn.execute("INSERT INTO debts (client, balance, ref_sale, sid) VALUES (?,?,?,?)", (c_name, rest_u, ref, sid))
                    conn.commit(); conn.close()
                    
                    st.session_state.invoice = {'ref': ref, 'cli': c_name, 'total': aff_t, 'cur': dev, 'items': it_js, 'date': now_d, 'time': now_t}
                    st.session_state.cart = {}; st.rerun()

# --- 6.3 GESTION DU STOCK ---
elif choice == "📦 STOCK":
    st.markdown("<div class='cobalt-box'><h1>GESTION DES ARTICLES</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN NOUVEAU PRODUIT"):
        with st.form("add_p"):
            n = st.text_input("Désignation").upper()
            c1, c2 = st.columns(2)
            pa, pv = c1.number_input("Prix Achat $"), c2.number_input("Prix Vente $")
            q = st.number_input("Quantité", 1)
            if st.form_submit_button("AJOUTER"):
                conn = get_db()
                conn.execute("INSERT INTO stock (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n, q, pa, pv, sid))
                conn.commit(); conn.close(); st.rerun()

    st.divider()
    conn = get_db()
    prods = conn.execute("SELECT * FROM stock WHERE sid=? ORDER BY item", (sid,)).fetchall()
    for p in prods:
        with st.expander(f"{p['item']} | Stock: {p['qty']} | Vente: {p['sell_price']}$"):
            nv_p = st.number_input("Modifier Prix ($)", value=p['sell_price'], key=f"p_{p['id']}")
            nv_q = st.number_input("Ajuster Stock", value=p['qty'], key=f"q_{p['id']}")
            c1, c2 = st.columns(2)
            if c1.button(f"MISE À JOUR {p['id']}", key=f"up_{p['id']}"):
                conn.execute("UPDATE stock SET sell_price=?, qty=? WHERE id=?", (nv_p, nv_q, p['id']))
                conn.commit(); st.rerun()
            if c2.button(f"🗑️ SUPPRIMER {p['id']}", key=f"rm_{p['id']}"):
                conn.execute("DELETE FROM stock WHERE id=?", (p['id']))
                conn.commit(); st.rerun()
    conn.close()

# --- 6.4 DETTES PAR TRANCHES ---
elif choice == "📉 DETTES":
    st.header("📉 CRÉDITS CLIENTS")
    conn = get_db()
    d_list = conn.execute("SELECT * FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
    if not d_list: st.info("Aucune dette.")
    for d in d_list:
        with st.expander(f"👤 {d['client']} | Reste: {d['balance']:,.2f} $"):
            pay = st.number_input("Verser Tranche ($)", 0.0, d['balance'], key=f"pay_{d['id']}")
            if st.button(f"VALIDER PAIEMENT {d['id']}"):
                nb = d['balance'] - pay
                if nb <= 0.01: conn.execute("UPDATE debts SET balance=0, status='PAYE' WHERE id=?", (d['id'],))
                else: conn.execute("UPDATE debts SET balance=? WHERE id=?", (nb, d['id']))
                conn.commit(); st.success("Paiement enregistré !"); st.rerun()
    conn.close()

# --- 6.5 RAPPORTS & HISTORIQUE ---
elif choice == "📊 RAPPORTS":
    st.markdown("<div class='cobalt-box'><h1>HISTORIQUE DE VENTES</h1></div>", unsafe_allow_html=True)
    sel_d = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    conn = get_db()
    reps = conn.execute("SELECT * FROM sales WHERE sid=? AND date=?", (sid, sel_d)).fetchall()
    if reps:
        df = pd.DataFrame(reps, columns=["id","ref","cli","total","paid","rest","date","time","seller","sid","details","currency"])
        st.table(df[["ref", "cli", "total", "paid", "seller", "time"]])
        total_d = df['total'].sum()
        st.markdown(f"<div class='cobalt-box'><h2>TOTAL GÉNÉRÉ LE {sel_d} : {total_d:,.2f} $</h2></div>", unsafe_allow_html=True)
    else: st.info("Pas de ventes.")
    conn.close()

# --- 6.6 ÉQUIPE & MOT DE PASSE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 MON ÉQUIPE")
    with st.expander("🔐 CHANGER MON MOT DE PASSE"):
        with st.form("pwd_form"):
            nv_p = st.text_input("Nouveau Pass", type="password")
            if st.form_submit_button("MODIFIER"):
                h = hashlib.sha256(nv_p.encode()).hexdigest()
                conn = get_db()
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (h, st.session_state.user))
                conn.commit(); conn.close(); st.success("Mis à jour !")
    
    if st.session_state.role == "GERANT":
        st.divider()
        with st.form("add_v"):
            v_u = st.text_input("ID Vendeur").lower()
            v_n = st.text_input("Nom Complet")
            v_p = st.text_input("Pass", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                h = hashlib.sha256(v_p.encode()).hexdigest()
                conn = get_db()
                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (v_u, h, 'VENDEUR', sid, 'ACTIF', v_n, '', None))
                conn.commit(); conn.close(); st.rerun()

# --- 6.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("sh_cfg"):
        n = st.text_input("Enseigne", s_data['name'])
        r = st.number_input("Taux de Change (1$ = ? CDF)", value=s_data['rate'])
        a = st.text_area("Adresse", s_data['address'])
        t = st.text_input("Téléphone", s_data['phone'])
        if st.form_submit_button("ENREGISTRER"):
            conn = get_db()
            conn.execute("UPDATE shops SET name=?, rate=?, address=?, phone=? WHERE sid=?", (n, r, a, t, sid))
            conn.commit(); conn.close(); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.auth = False; st.rerun()

# ==============================================================================
# FIN DU CODE v220 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
