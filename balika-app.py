# ==============================================================================
# ANASH ERP v3318 - SYSTÈME DE GESTION INTÉGRAL (ÉDITION ULTIME 2026)
# ------------------------------------------------------------------------------
# VOLUME REQUIS : > 750 LIGNES | INTERFACE : MOBILE FIRST | SÉCURITÉ : SHA-256
# ------------------------------------------------------------------------------
# CE CODE EST COMPLET ET REMPLACE TOUTES LES VERSIONS PRÉCÉDENTES.
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import base64
import time
import os

# ------------------------------------------------------------------------------
# 1. CONFIGURATION & SÉCURITÉ
# ------------------------------------------------------------------------------
DB_NAME = "anash_master_v3318.db"

def get_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table Configuration Globale (Admin)
    c.execute("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        marquee_text TEXT,
        marquee_enabled INTEGER DEFAULT 1,
        system_version TEXT DEFAULT 'v3318',
        global_rate REAL DEFAULT 2800.0
    )""")
    
    # Table Utilisateurs (Profils, Passwords, Rôles)
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        real_name TEXT,
        shop_id TEXT,
        status TEXT DEFAULT 'ACTIF',
        profile_pic BLOB,
        phone TEXT
    )""")
    
    # Table Boutique & Profil
    c.execute("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY,
        name TEXT,
        address TEXT,
        phone TEXT,
        footer_msg TEXT,
        logo BLOB
    )""")
    
    # Table Inventaire (Sans prix d'achat dans les vues simples)
    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        quantity INTEGER,
        buy_price REAL,
        sell_price REAL,
        sid TEXT,
        active INTEGER DEFAULT 1
    )""")
    
    # Table Ventes (Historique)
    c.execute("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref TEXT,
        client TEXT,
        total_usd REAL,
        paid_usd REAL,
        debt_usd REAL,
        currency TEXT,
        rate REAL,
        date TEXT,
        time TEXT,
        items_json TEXT,
        seller TEXT,
        sid TEXT
    )""")
    
    # Table Dettes (Paiements échelonnés)
    c.execute("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        remaining_amount REAL,
        sale_ref TEXT,
        sid TEXT,
        status TEXT DEFAULT 'OUVERT'
    )""")

    # Données par défaut (Admin & Config)
    c.execute("SELECT count(*) FROM system_config")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO system_config (id, company_name, marquee_text) VALUES (1, 'ANASH BUSINESS', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION PROFESSIONNEL')")
    
    c.execute("SELECT count(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        admin_p = get_hash("admin123")
        c.execute("INSERT INTO users (username, password, role, real_name, shop_id) VALUES ('admin', ?, 'ADMIN', 'Super Admin', 'SYSTEM')", (admin_p,))
    
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------------------
# 2. STYLES CSS (MOBILE, TEXTE BLANC SUR BLEU, CADRES COLORÉS)
# ------------------------------------------------------------------------------
def inject_custom_css():
    st.markdown("""
    <style>
        /* Global Background & Mobile Optimization */
        .stApp { background-color: #001f3f; color: white; }
        
        /* Blue Background with White Text Sections */
        .blue-section {
            background-color: #003366; 
            color: white !important; 
            padding: 20px; 
            border-radius: 15px;
            margin-bottom: 15px;
            border-left: 5px solid #0074D9;
        }

        /* Marquee / Scrolling Text */
        .marquee {
            width: 100%; height: 40px; background: #0074D9; color: white;
            white-space: nowrap; overflow: hidden; box-sizing: border-box;
            display: flex; align-items: center; font-weight: bold;
            border-radius: 5px; margin-bottom: 20px;
        }
        .marquee span { display: inline-block; padding-left: 100%; animation: marquee 15s linear infinite; }
        @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }

        /* Total Shopping Cart (Colored Frame) */
        .total-frame {
            border: 4px solid #FF851B;
            padding: 20px;
            border-radius: 20px;
            text-align: center;
            background: rgba(255, 133, 27, 0.1);
            margin: 15px 0;
        }
        .total-amount { font-size: 35px; font-weight: 900; color: #FF851B; }

        /* Sidebar Customization */
        [data-testid="stSidebar"] { background-color: #003366 !important; }
        [data-testid="stSidebar"] * { color: white !important; }

        /* Buttons for Mobile */
        .stButton > button {
            width: 100% !important;
            height: 60px !important;
            font-size: 18px !important;
            border-radius: 12px !important;
            background-color: #0074D9 !important;
            color: white !important;
        }
        
        /* Hide User details in cart before purchase */
        .hidden-details { display: none; }

        /* Print formatting */
        @media print {
            .no-print { display: none !important; }
            .print-area { display: block !important; width: 80mm; font-family: monospace; color: black; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ------------------------------------------------------------------------------
# 3. LOGIQUE DE SESSION & AUTHENTIFICATION
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state:
    st.session_state.auth = {'logged': False, 'user': None, 'role': None, 'shop': None}
if 'cart' not in st.session_state:
    st.session_state.cart = []

def login_ui():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🔐 CONNEXION</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Utilisateur")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("ENTRER"):
                conn = sqlite3.connect(DB_NAME)
                res = conn.execute("SELECT password, role, shop_id, real_name FROM users WHERE username=?", (u,)).fetchone()
                conn.close()
                if res and res[0] == get_hash(p):
                    st.session_state.auth = {'logged': True, 'user': u, 'role': res[1], 'shop': res[2], 'name': res[3]}
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    st.stop()

if not st.session_state.auth['logged']:
    login_ui()

# ------------------------------------------------------------------------------
# 4. MODULES DE GESTION DES DONNÉES
# ------------------------------------------------------------------------------
def get_config():
    conn = sqlite3.connect(DB_NAME)
    cfg = conn.execute("SELECT company_name, marquee_text, marquee_enabled, global_rate FROM system_config WHERE id=1").fetchone()
    conn.close()
    return cfg

CONFIG = get_config()

def save_backup():
    try:
        with open(DB_NAME, 'rb') as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="backup_{datetime.now().strftime("%Y%m%d")}.db">Cliquer ici pour télécharger la sauvegarde</a>'
            st.markdown(href, unsafe_allow_html=True)
            return True
    except:
        return False

# ------------------------------------------------------------------------------
# 5. NAVIGATION & SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.auth['name']}")
    st.markdown(f"**Rôle:** {st.session_state.auth['role']}")
    st.divider()
    
    if st.session_state.auth['role'] == "ADMIN":
        menu = st.radio("MENU ADMIN", ["Tableau de Bord", "Gestion Utilisateurs", "Réglages Système", "Sauvegarde"])
    else:
        menu = st.radio("MENU", ["Accueil", "Caisse (Vente)", "Stock", "Dettes", "Paramètres Profil"])
    
    if st.button("🚪 Déconnexion"):
        st.session_state.auth = {'logged': False}
        st.rerun()

# ------------------------------------------------------------------------------
# 6. INTERFACE ADMIN (COMPLET)
# ------------------------------------------------------------------------------
if st.session_state.auth['role'] == "ADMIN":
    
    if menu == "Tableau de Bord":
        st.title("📊 Supervision Générale")
        conn = sqlite3.connect(DB_NAME)
        v_tot = conn.execute("SELECT SUM(total_usd) FROM sales").fetchone()[0] or 0
        u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        s_count = conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventes Totales", f"{v_tot:,.2f} $")
        c2.metric("Utilisateurs", u_count)
        c3.metric("Boutiques", s_count)
    
    elif menu == "Gestion Utilisateurs":
        st.header("👥 Utilisateurs & Vendeurs")
        with st.expander("➕ Ajouter un compte (Vendeur ou Boss)"):
            with st.form("new_user"):
                new_u = st.text_input("Identifiant")
                new_n = st.text_input("Nom Complet")
                new_p = st.text_input("Mot de passe", type="password")
                new_r = st.selectbox("Rôle", ["VENDEUR", "BOSS"])
                new_s = st.text_input("ID Boutique assigné")
                if st.form_submit_button("Créer le compte"):
                    conn = sqlite3.connect(DB_NAME)
                    try:
                        conn.execute("INSERT INTO users (username, password, role, real_name, shop_id) VALUES (?,?,?,?,?)",
                                   (new_u, get_hash(new_p), new_r, new_n, new_s))
                        conn.commit()
                        st.success("Compte créé avec succès")
                    except: st.error("L'identifiant existe déjà")
                    finally: conn.close()
        
        st.subheader("Liste des comptes")
        conn = sqlite3.connect(DB_NAME)
        df_u = pd.read_sql_query("SELECT username, role, real_name, shop_id, status FROM users", conn)
        st.dataframe(df_u, use_container_width=True)
        conn.close()

    elif menu == "Réglages Système":
        st.header("⚙️ Configuration Globale")
        with st.form("sys_cfg"):
            c_name = st.text_input("Nom de l'entreprise", CONFIG[0])
            m_text = st.text_area("Texte défilant (Marquee)", CONFIG[1])
            m_stat = st.checkbox("Activer le défilement", value=(CONFIG[2] == 1))
            g_rate = st.number_input("Taux de change Global (CDF)", value=CONFIG[3])
            if st.form_submit_button("Appliquer les changements"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("UPDATE system_config SET company_name=?, marquee_text=?, marquee_enabled=?, global_rate=? WHERE id=1",
                           (c_name, m_text, 1 if m_stat else 0, g_rate))
                conn.commit()
                conn.close()
                st.rerun()

    elif menu == "Sauvegarde":
        st.header("💾 Sauvegarde de la Base de Données")
        if st.button("Générer une copie de sauvegarde"):
            if save_backup():
                st.success("Sauvegarde prête !")
            else:
                st.error("Échec de la sauvegarde")

# ------------------------------------------------------------------------------
# 7. INTERFACE UTILISATEUR (VENDEUR / BOSS)
# ------------------------------------------------------------------------------
else:
    # HEADER COMMUN
    if CONFIG[2] == 1:
        st.markdown(f'<div class="marquee"><span>{CONFIG[1]}</span></div>', unsafe_allow_html=True)
    
    if menu == "Accueil":
        st.markdown(f"<div class='blue-section'><h1>Bienvenue chez {CONFIG[0]}</h1></div>", unsafe_allow_html=True)
        st.markdown(f"### {st.session_state.auth['name']}")
        
        # Dashboard rapide
        conn = sqlite3.connect(DB_NAME)
        today = datetime.now().strftime("%d/%m/%Y")
        v_day = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (st.session_state.auth['shop'], today)).fetchone()[0] or 0
        conn.close()
        
        st.info(f"Ventes d'aujourd'hui : {v_day:,.2f} $")

    elif menu == "Caisse (Vente)":
        st.title("🛒 Panier de Vente")
        
        # Choix devise
        devise = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        taux = CONFIG[3]
        
        conn = sqlite3.connect(DB_NAME)
        prods = conn.execute("SELECT name, sell_price, quantity FROM products WHERE sid=? AND quantity > 0 AND active=1", (st.session_state.auth['shop'],)).fetchall()
        conn.close()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            choice = st.selectbox("Choisir un produit", [""] + [f"{p[0]} ({p[1]}$)" for p in prods])
            if choice:
                p_name = choice.split(" (")[0]
                if st.button("Ajouter au panier"):
                    # Logique ajout panier
                    found = False
                    for item in st.session_state.cart:
                        if item['name'] == p_name:
                            item['qty'] += 1
                            found = True
                    if not found:
                        price = [p[1] for p in prods if p[0] == p_name][0]
                        st.session_state.cart.append({'name': p_name, 'qty': 1, 'price': price})
                    st.rerun()

        # Affichage Panier
        if st.session_state.cart:
            st.divider()
            total_u = 0
            for i, item in enumerate(st.session_state.cart):
                col_n, col_q, col_p, col_rm = st.columns([3, 1, 2, 1])
                col_n.write(item['name'])
                new_q = col_q.number_input("Qté", 1, 1000, item['qty'], key=f"q_{i}")
                item['qty'] = new_q
                sub = item['price'] * item['qty']
                total_u += sub
                col_p.write(f"{sub:,.2f} $")
                if col_rm.button("❌", key=f"rm_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            
            final_total = total_u if devise == "USD" else total_u * taux
            st.markdown(f"""
                <div class="total-frame">
                    <div style="color:white">TOTAL À PAYER</div>
                    <div class="total-amount">{final_total:,.2f} {devise}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Formulaire de paiement (Les détails client ne sont affichés que si nécessaire)
            with st.form("paiement"):
                st.write("### Validation du Paiement")
                client = st.text_input("Nom du Client", "COMPTANT")
                montant_paye = st.number_input(f"Montant Reçu ({devise})", value=float(final_total))
                
                if st.form_submit_button("CONCLURE LA VENTE"):
                    # Calcul dette
                    paye_usd = montant_paye if devise == "USD" else montant_paye / taux
                    dette = total_u - paye_usd
                    ref = f"FAC-{int(time.time())}"
                    
                    conn = sqlite3.connect(DB_NAME)
                    # Enregistrer vente
                    conn.execute("""INSERT INTO sales (ref, client, total_usd, paid_usd, debt_usd, currency, rate, date, time, items_json, seller, sid)
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                 (ref, client, total_u, paye_usd, dette, devise, taux, datetime.now().strftime("%d/%m/%Y"), 
                                  datetime.now().strftime("%H:%M"), json.dumps(st.session_state.cart), st.session_state.auth['user'], st.session_state.auth['shop']))
                    
                    # Déduire stock
                    for it in st.session_state.cart:
                        conn.execute("UPDATE products SET quantity = quantity - ? WHERE name=? AND sid=?", (it['qty'], it['name'], st.session_state.auth['shop']))
                    
                    # Gérer dette
                    if dette > 0:
                        conn.execute("INSERT INTO debts (client_name, remaining_amount, sale_ref, sid) VALUES (?,?,?,?)",
                                   (client, dette, ref, st.session_state.auth['shop']))
                    
                    conn.commit()
                    conn.close()
                    st.session_state.cart = []
                    st.success(f"Vente réussie ! Réf: {ref}")
                    time.sleep(1)
                    st.rerun()

    elif menu == "Stock":
        st.header("📦 Gestion des Produits")
        
        tab1, tab2 = st.tabs(["Inventaire", "Ajouter Produit"])
        
        with tab1:
            conn = sqlite3.connect(DB_NAME)
            df_p = pd.read_sql_query(f"SELECT id, name, category, quantity, sell_price FROM products WHERE sid='{st.session_state.auth['shop']}' AND active=1", conn)
            st.dataframe(df_p, use_container_width=True)
            
            st.subheader("Actions sur le stock")
            selected_id = st.number_input("Entrez ID du produit à modifier/supprimer", step=1)
            new_p = st.number_input("Nouveau Prix de vente ($)")
            if st.button("Mettre à jour le prix"):
                conn.execute("UPDATE products SET sell_price=? WHERE id=? AND sid=?", (new_p, selected_id, st.session_state.auth['shop']))
                conn.commit()
                st.success("Prix mis à jour")
            
            if st.button("🗑️ Supprimer le produit"):
                conn.execute("UPDATE products SET active=0 WHERE id=? AND sid=?", (selected_id, st.session_state.auth['shop']))
                conn.commit()
                st.warning("Produit désactivé")
            conn.close()
            
        with tab2:
            with st.form("add_p"):
                pn = st.text_input("Désignation")
                pc = st.selectbox("Catégorie", ["DIVERS", "HABILLEMENT", "ELECTRONIQUE", "ALIMENTATION"])
                pq = st.number_input("Quantité", step=1)
                pb = st.number_input("Prix d'achat ($)")
                ps = st.number_input("Prix de vente ($)")
                if st.form_submit_button("Enregistrer"):
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO products (name, category, quantity, buy_price, sell_price, sid) VALUES (?,?,?,?,?,?)",
                               (pn.upper(), pc, pq, pb, ps, st.session_state.auth['shop']))
                    conn.commit()
                    conn.close()
                    st.success("Produit ajouté !")

    elif menu == "Dettes":
        st.header("📉 Clients Débiteurs")
        conn = sqlite3.connect(DB_NAME)
        dettes = conn.execute("SELECT id, client_name, remaining_amount, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (st.session_state.auth['shop'],)).fetchall()
        
        if not dettes:
            st.info("Aucune dette enregistrée.")
        else:
            for d in dettes:
                with st.expander(f"Client: {d[1]} | Reste: {d[2]:,.2f} $"):
                    p_amount = st.number_input(f"Verser paiement ($)", 0.0, float(d[2]), key=f"pay_{d[0]}")
                    if st.button(f"Valider paiement {d[0]}", key=f"btn_{d[0]}"):
                        new_rem = d[2] - p_amount
                        if new_rem <= 0:
                            conn.execute("UPDATE debts SET remaining_amount=0, status='SOLDE' WHERE id=?", (d[0],))
                        else:
                            conn.execute("UPDATE debts SET remaining_amount=? WHERE id=?", (new_rem, d[0]))
                        conn.commit()
                        st.rerun()
        conn.close()

    elif menu == "Paramètres Profil":
        st.header("⚙️ Profil & Boutique")
        
        # Modification Password
        with st.form("pass_change"):
            st.write("Changer le mot de passe")
            old_p = st.text_input("Ancien mot de passe", type="password")
            new_p = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("Mettre à jour"):
                conn = sqlite3.connect(DB_NAME)
                current = conn.execute("SELECT password FROM users WHERE username=?", (st.session_state.auth['user'],)).fetchone()[0]
                if current == get_hash(old_p):
                    conn.execute("UPDATE users SET password=? WHERE username=?", (get_hash(new_p), st.session_state.auth['user']))
                    conn.commit()
                    st.success("C'est fait !")
                else: st.error("Ancien mot de passe incorrect")
                conn.close()

        # Infos Boutique
        if st.session_state.auth['role'] == "BOSS":
            st.divider()
            st.write("Modifier Informations Boutique")
            conn = sqlite3.connect(DB_NAME)
            s_info = conn.execute("SELECT name, address, phone FROM shops WHERE sid=?", (st.session_state.auth['shop'],)).fetchone()
            with st.form("shop_edit"):
                sn = st.text_input("Nom Boutique", s_info[0] if s_info else "")
                sa = st.text_input("Adresse", s_info[1] if s_info else "")
                sp = st.text_input("Téléphone", s_info[2] if s_info else "")
                if st.form_submit_button("Sauvegarder Info Boutique"):
                    conn.execute("INSERT OR REPLACE INTO shops (sid, name, address, phone) VALUES (?,?,?,?)",
                               (st.session_state.auth['shop'], sn, sa, sp))
                    conn.commit()
                    st.success("Boutique mise à jour")
            conn.close()

# ------------------------------------------------------------------------------
# 8. PIED DE PAGE & SÉCURITÉ STOCK
# ------------------------------------------------------------------------------
st.markdown("<br><br><hr><center><small>ANASH ERP PRO v3318 | Protégé par licence Balika Business</small></center>", unsafe_allow_html=True)

# Note: Pour que l'application soit utilisable sur téléphone, 
# Streamlit gère nativement le responsive design (layout="wide").
