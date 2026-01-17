# ==============================================================================
# ANASH ERP v210 - SYSTÈME DE GESTION INTÉGRAL (ÉDITION BALIKA BUSINESS)
# ------------------------------------------------------------------------------
# DÉVELOPPÉ POUR UNE FIABILITÉ MAXIMALE SUR MOBILE ET ORDINATEUR.
# CE CODE INCLUT : ADMIN, GÉRANT, VENDEUR, DETTES ÉCHELONNÉES, MULTI-MONNAIE.
# ------------------------------------------------------------------------------
# LIGNES : > 700 | DESIGN : COBALT NÉON COMPACT | SESSION PERSISTANTE
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

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DU MOTEUR DE BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_NAME = "anash_v210_enterprise.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def core_init():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Table Config Globale
    cursor.execute("""CREATE TABLE IF NOT EXISTS system_cfg (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_msg TEXT, last_update TEXT)""")
    # Table Utilisateurs
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
    # Table Boutiques (Détails complets)
    cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
        sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
        head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT, email TEXT)""")
    # Table Stock (Inventaire complet)
    cursor.execute("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
        buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
    # Table Ventes (Transactions)
    cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, tot REAL, 
        pay REAL, res REAL, date TEXT, time TEXT, seller TEXT, sid TEXT, 
        items_data TEXT, currency TEXT)""")
    # Table Dettes (Suivi par tranches)
    cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
        original_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")
    
    # Données par défaut
    cursor.execute("SELECT id FROM system_cfg WHERE id=1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO system_cfg VALUES (1, 'ANASH ERP v210', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION BALIKA BUSINESS', ?)", (datetime.now().isoformat(),))
    
    cursor.execute("SELECT uid FROM users WHERE uid='admin'")
    if not cursor.fetchone():
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                      ('admin', pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMIN MASTER', '000'))
    
    conn.commit()
    conn.close()

core_init()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT DE LA CONFIGURATION
# ------------------------------------------------------------------------------
conn = get_db_connection()
sys_cfg = conn.execute("SELECT app_name, marquee_msg FROM system_cfg WHERE id=1").fetchone()
APP_NAME = sys_cfg['app_name']
MARQUEE_MSG = sys_cfg['marquee_msg']
conn.close()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS (COBALT, NÉON & MOBILE OPTIMISATION)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def inject_styles():
    st.markdown(f"""
    <style>
        /* BASE & TYPOGRAPHIE */
        .stApp {{ background-color: #000a1a; color: white; }}
        
        /* MARQUEE CSS (FIXÉ ET FLUIDE) */
        .marquee-container {{
            width: 100%; overflow: hidden; background: #000; border-bottom: 2px solid #00ff00;
            position: fixed; top: 0; left: 0; z-index: 1000; padding: 10px 0;
        }}
        .marquee-content {{
            display: inline-block; white-space: nowrap; animation: scroll-text 30s linear infinite;
            color: #00ff00; font-family: 'Courier New', Courier, monospace; font-size: 20px; font-weight: bold;
        }}
        @keyframes scroll-text {{ from {{ transform: translateX(100%); }} to {{ transform: translateX(-100%); }} }}

        /* PANNEAUX BLEU COBALT (TEXTE BLANC OBLIGATOIRE) */
        .cobalt-card {{
            background: linear-gradient(135deg, #0044ff 0%, #001a66 100%);
            color: white !important; border-radius: 15px; padding: 18px;
            margin-bottom: 15px; border-left: 8px solid #00d9ff;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        .cobalt-card h1, .cobalt-card h2, .cobalt-card h3, .cobalt-card p, .cobalt-card span {{
            color: white !important;
        }}

        /* CADRE NÉON POUR LES TOTAUX */
        .neon-frame {{
            border: 4px solid #00ff00; padding: 20px; border-radius: 20px;
            background: #000; text-align: center; box-shadow: 0 0 15px #00ff00; margin: 15px 0;
        }}
        .neon-text {{ color: #00ff00; font-size: 35px; font-weight: bold; }}

        /* PANIER COMPACT (PETIT TEXTE POUR MOBILE) */
        .cart-item {{
            background: rgba(255,255,255,0.05); padding: 5px 10px; border-radius: 8px;
            margin-bottom: 5px; font-size: 13px; border: 1px solid #0044ff;
        }}
        .cart-name {{ color: #00d9ff; font-weight: bold; }}

        /* BOUTONS D'ACTION MOBILES */
        .stButton > button {{
            width: 100%; height: 60px; border-radius: 12px; font-weight: bold;
            background: linear-gradient(to right, #0055ff, #002288);
            color: white; border: 1px solid white; text-transform: uppercase;
        }}
        
        /* SIDEBAR PERSONNALISÉE */
        [data-testid="stSidebar"] {{ background: #ffffff !important; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold; }}

        /* CHAMPS DE SAISIE */
        input {{ background: white !important; color: black !important; font-weight: bold !important; }}
        
        .spacer {{ margin-top: 60px; }}
        
        @media print {{ .no-print {{ display: none !important; }} }}
    </style>
    <div class="marquee-container">
        <div class="marquee-content">{MARQUEE_MSG} | {APP_NAME} | {datetime.now().strftime('%H:%M')}</div>
    </div>
    <div class="spacer"></div>
    """, unsafe_allow_html=True)

inject_styles()

# ------------------------------------------------------------------------------
# 4. GESTION DES ÉTATS DE SESSION (POUR ÉVITER LA FERMETURE)
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': None, 'role': None, 'shop': None, 
        'cart': {}, 'view': 'dashboard', 'invoice': None
    })

# ------------------------------------------------------------------------------
# 5. SYSTÈME D'AUTHENTIFICATION & INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.markdown(f"<h1 style='text-align:center;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 SE CONNECTER", "📝 CRÉER COMPTE"])
        
        with tab_log:
            u_id = st.text_input("Identifiant").lower().strip()
            u_pw = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU TABLEAU DE BORD"):
                conn = get_db_connection()
                res = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (u_id,)).fetchone()
                conn.close()
                if res and hashlib.sha256(u_pw.encode()).hexdigest() == res['pwd']:
                    if res['status'] == "ACTIF":
                        st.session_state.update({'auth': True, 'user': u_id, 'role': res['role'], 'shop': res['shop']})
                        st.rerun()
                    else: st.warning("Compte en attente d'activation par l'Admin.")
                else: st.error("Identifiants incorrects.")
        
        with tab_reg:
            with st.form("form_reg"):
                reg_u = st.text_input("Identifiant souhaité").lower().strip()
                reg_n = st.text_input("Nom de la Boutique")
                reg_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("DEMANDER MON ACCÈS"):
                    if reg_u and reg_p:
                        conn = get_db_connection()
                        try:
                            h = hashlib.sha256(reg_p.encode()).hexdigest()
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                        (reg_u, h, 'GERANT', 'PENDING', 'EN_ATTENTE', reg_n, ''))
                            conn.commit()
                            st.success("Demande envoyée ! Veuillez contacter l'administrateur.")
                        except sqlite3.IntegrityError: st.error("Cet identifiant est déjà pris.")
                        finally: conn.close()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.title("🛠️ MASTER ADMIN")
    adm_menu = st.sidebar.radio("Navigation", ["Validations Clients", "Réglages App", "Déconnexion"])
    
    if adm_menu == "Validations Clients":
        st.header("✅ GESTION DES NOUVEAUX CLIENTS")
        conn = get_db_connection()
        pending = conn.execute("SELECT uid, name FROM users WHERE status='EN_ATTENTE'").fetchall()
        if not pending: st.info("Aucune demande en attente.")
        for p in pending:
            with st.expander(f"Demande de : {p['name']} (@{p['uid']})"):
                if st.button(f"ACTIVER & CRÉER BOUTIQUE : {p['uid']}"):
                    conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (p['uid'], p['uid']))
                    conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (p['uid'], p['name'], p['uid']))
                    conn.commit()
                    st.success(f"Compte {p['uid']} activé !"); st.rerun()
        conn.close()

    elif adm_menu == "Réglages App":
        st.header("⚙️ CONFIGURATION SYSTÈME")
        with st.form("sys_cfg"):
            new_title = st.text_input("Nom de l'Application", APP_NAME)
            new_msg = st.text_area("Message défilant", MARQUEE_MSG)
            if st.form_submit_button("APPLIQUER LES MODIFICATIONS"):
                conn = get_db_connection()
                conn.execute("UPDATE system_cfg SET app_name=?, marquee_msg=? WHERE id=1", (new_title, new_msg))
                conn.commit()
                conn.close()
                st.rerun()
    
    if adm_menu == "Déconnexion": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (GÉRANTS & VENDEURS)
# ------------------------------------------------------------------------------
sid = st.session_state.shop
conn = get_db_connection()
shop_data = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat, email FROM shops WHERE sid=?", (sid,)).fetchone()
conn.close()

if not shop_data:
    st.error("Erreur d'initialisation de la boutique. Contactez l'admin.")
    st.stop()

# Menu Dynamique
nav_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.role == "VENDEUR":
    nav_options = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'>🏪 {shop_data['name']}<br>👤 {st.session_state.user.upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("MENU PRINCIPAL", nav_options)

# --- 7.1 ACCUEIL (DASHBOARD) ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
        <div style='text-align:center; padding: 40px; border: 3px solid white; border-radius: 30px; background: rgba(0, 68, 255, 0.1);'>
            <h1 style='font-size: 80px; margin:0;'>{datetime.now().strftime('%H:%M')}</h1>
            <h3 style='color: #00d9ff;'>{datetime.now().strftime('%d %B %Y')}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Statistiques Rapides
    conn = get_db_connection()
    today_str = datetime.now().strftime("%d/%m/%Y")
    ca_jour = conn.execute("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (sid, today_str)).fetchone()[0] or 0
    nb_ventes = conn.execute("SELECT COUNT(*) FROM sales WHERE sid=? AND date=?", (sid, today_str)).fetchone()[0]
    conn.close()
    
    st.markdown(f"<div class='neon-frame'><div class='neon-text'>RECETTE : {ca_jour:,.2f} $</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='cobalt-card' style='text-align:center;'>NOMBRE DE VENTES : {nb_ventes}</div>", unsafe_allow_html=True)

# --- 7.2 CAISSE TACTILE (MULTI-DEVISE) ---
elif choice == "🛒 CAISSE":
    if st.session_state.invoice:
        # ÉCRAN DE FACTURE (PRÊT À IMPRIMER)
        inv = st.session_state.invoice
        st.markdown("### 📄 FACTURE DE VENTE")
        st.markdown(f"""
        <div style='background: white; color: black; padding: 20px; border-radius: 10px; font-family: sans-serif;'>
            <div style='text-align:center;'>
                <h2>{shop_data['name']}</h2>
                <p>{shop_data['addr']}<br>Tél: {shop_data['tel']}</p>
                <hr>
                <h4>FACTURE N° {inv['ref']}</h4>
            </div>
            <p><b>Client:</b> {inv['cli']} | <b>Date:</b> {inv['date']}</p>
            <table style='width:100%; border-collapse: collapse; color: black;'>
                <tr style='border-bottom: 2px solid #000;'><th>Désignation</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['tot']:,.2f}</td></tr>" for k, v in inv['data'].items()])}
            </table>
            <hr>
            <h3 style='text-align:right;'>NET À PAYER : {inv['total']:,.2f} {inv['cur']}</h3>
            <p style='text-align:center; font-size:12px;'>{shop_data['head']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("⬅️ RETOUR À LA CAISSE"):
            st.session_state.invoice = None; st.rerun()
        if c2.button("🖨️ IMPRIMER / PARTAGER"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        c_p, c_d = st.columns([2, 1])
        with c_d:
            monnaie = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            taux = shop_data['rate']
            st.info(f"Taux du jour: 1$ = {taux} CDF")
        
        with c_p:
            conn = get_db_connection()
            items = conn.execute("SELECT item, sell_price, qty FROM stock WHERE sid=? AND qty > 0", (sid,)).fetchall()
            conn.close()
            sel = st.selectbox("RECHERCHER ARTICLE", ["---"] + [f"{i['item']} ({i['qty']}) - {i['sell_price']}$" for i in items])
            
            if sel != "---":
                name = sel.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    conn = get_db_connection()
                    inf = conn.execute("SELECT sell_price, qty FROM stock WHERE item=? AND sid=?", (name, sid)).fetchone()
                    conn.close()
                    st.session_state.cart[name] = {'p': inf['sell_price'], 'q': 1, 'max': inf['qty']}
                    st.rerun()

        if st.session_state.cart:
            st.subheader("📋 PANIER EN COURS")
            total_usd = 0.0
            for art, d in list(st.session_state.cart.items()):
                # Panier compact
                st.markdown(f"<div class='cart-item'><span class='cart-name'>{art}</span> | {d['p']}$ x {d['q']}</div>", unsafe_allow_html=True)
                col_q, col_del = st.columns([3, 1])
                new_q = col_q.number_input(f"Quantité {art}", 1, d['max'], d['q'], key=f"q_{art}")
                st.session_state.cart[art]['q'] = new_q
                total_usd += d['p'] * new_q
                if col_del.button("🗑️", key=f"del_{art}"):
                    del st.session_state.cart[art]; st.rerun()
            
            # Affichage Total Néon
            aff_total = total_usd if monnaie == "USD" else total_usd * taux
            st.markdown(f"<div class='neon-frame'><div class='neon-text'>{aff_total:,.2f} {monnaie}</div></div>", unsafe_allow_html=True)
            
            with st.form("valid_v"):
                cli_name = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                paye = st.number_input(f"MONTANT REÇU ({monnaie})", value=float(aff_total))
                if st.form_submit_button("✅ FINALISER LA VENTE"):
                    recu_usd = paye if monnaie == "USD" else paye / taux
                    reste_usd = total_usd - recu_usd
                    ref_v = f"FAC-{random.randint(10000, 99999)}"
                    d_v, t_v = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    # Enregistrement Base
                    conn = get_db_connection()
                    items_js = {k: {'q': v['q'], 'tot': v['p']*v['q']} for k,v in st.session_state.cart.items()}
                    conn.execute("""INSERT INTO sales (ref, cli, tot, pay, res, date, time, seller, sid, items_data, currency) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                (ref_v, cli_name, total_usd, recu_usd, reste_usd, d_v, t_v, st.session_state.user, sid, json.dumps(items_js), monnaie))
                    
                    for a, dt in st.session_state.cart.items():
                        conn.execute("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (dt['q'], a, sid))
                    
                    if reste_usd > 0.01:
                        conn.execute("INSERT INTO debts (cli, balance, original_ref, sid) VALUES (?,?,?,?)", (cli_name, reste_usd, ref_v, sid))
                    
                    conn.commit()
                    conn.close()
                    
                    st.session_state.invoice = {'ref': ref_v, 'cli': cli_name, 'total': aff_total, 'cur': monnaie, 'date': d_v, 'data': items_js}
                    st.session_state.cart = {}; st.rerun()

# --- 7.3 STOCK (MODIFIER & SUPPRIMER) ---
elif choice == "📦 STOCK":
    st.header("📦 GESTION DES ARTICLES")
    with st.expander("➕ AJOUTER UN NOUVEAU PRODUIT"):
        with st.form("add_p"):
            nom = st.text_input("Désignation").upper()
            cat = st.selectbox("Catégorie", ["BOISSON", "NOURRITURE", "DIVERS"])
            col1, col2 = st.columns(2)
            p_a = col1.number_input("Prix Achat ($)")
            p_v = col2.number_input("Prix Vente ($)")
            q_i = st.number_input("Quantité initiale", min_value=1)
            if st.form_submit_button("SAUVEGARDER LE PRODUIT"):
                conn = get_db_connection()
                conn.execute("INSERT INTO stock (item, qty, buy_price, sell_price, sid, category) VALUES (?,?,?,?,?,?)",
                            (nom, q_i, p_a, p_v, sid, cat))
                conn.commit(); conn.close()
                st.success("Produit ajouté !"); st.rerun()
    
    st.divider()
    conn = get_db_connection()
    stock_list = conn.execute("SELECT * FROM stock WHERE sid=? ORDER BY item", (sid,)).fetchall()
    for s in stock_list:
        with st.expander(f"{s['item']} | Stock: {s['qty']} | Vente: {s['sell_price']}$"):
            nv_p = st.number_input("Modifier Prix ($)", value=s['sell_price'], key=f"pv_{s['id']}")
            nv_q = st.number_input("Ajuster Stock", value=s['qty'], key=f"qv_{s['id']}")
            c1, c2 = st.columns(2)
            if c1.button(f"Mise à jour {s['id']}", key=f"up_{s['id']}"):
                conn.execute("UPDATE stock SET sell_price=?, qty=? WHERE id=?", (nv_p, nv_q, s['id']))
                conn.commit(); st.rerun()
            if c2.button(f"🗑️ SUPPRIMER {s['id']}", key=f"del_{s['id']}"):
                conn.execute("DELETE FROM stock WHERE id=?", (s['id']))
                conn.commit(); st.rerun()
    conn.close()

# --- 7.4 DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 DETTES":
    st.header("📉 SUIVI DES CRÉDITS CLIENTS")
    conn = get_db_connection()
    credits = conn.execute("SELECT * FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
    if not credits: st.info("Aucune dette enregistrée.")
    for d in credits:
        with st.expander(f"👤 {d['cli']} | Restant: {d['balance']:,.2f} $"):
            tranche = st.number_input("Verser une tranche ($)", min_value=0.0, max_value=d['balance'], key=f"pay_{d['id']}")
            if st.button(f"VALIDER PAIEMENT TRANCHE {d['id']}"):
                nouveau_bal = d['balance'] - tranche
                if nouveau_bal <= 0.01:
                    conn.execute("UPDATE debts SET balance=0, status='PAYE' WHERE id=?", (d['id'],))
                else:
                    conn.execute("UPDATE debts SET balance=? WHERE id=?", (nouveau_bal, d['id']))
                conn.commit(); st.rerun()
    conn.close()

# --- 7.5 RAPPORTS & ANALYSE ---
elif choice == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DE VENTES")
    date_sel = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    conn = get_db_connection()
    sales_rep = conn.execute("SELECT ref, cli, tot, pay, seller, time FROM sales WHERE sid=? AND date=?", (sid, date_sel)).fetchall()
    conn.close()
    if sales_rep:
        df = pd.DataFrame(sales_rep, columns=["REF", "CLIENT", "TOTAL", "PAYE", "VENDEUR", "HEURE"])
        st.table(df)
        st.markdown(f"<div class='cobalt-card'><h3>TOTAL GÉNÉRÉ LE {date_sel} : {df['TOTAL'].sum():,.2f} $</h3></div>", unsafe_allow_html=True)
    else: st.info("Aucune vente pour cette date.")

# --- 7.6 ÉQUIPE (GÉRER VENDEURS) ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 GESTION DES UTILISATEURS")
    with st.expander("🔐 MODIFIER MON MOT DE PASSE"):
        with st.form("pwd_form"):
            new_p = st.text_input("Nouveau Mot de passe", type="password")
            if st.form_submit_button("MODIFIER"):
                h_p = hashlib.sha256(new_p.encode()).hexdigest()
                conn = get_db_connection()
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (h_p, st.session_state.user))
                conn.commit(); conn.close()
                st.success("Mot de passe mis à jour !")
    
    if st.session_state.role == "GERANT":
        st.divider()
        with st.form("add_vend"):
            v_id = st.text_input("ID Vendeur").lower().strip()
            v_name = st.text_input("Nom Complet")
            v_pass = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                h_v = hashlib.sha256(v_pass.encode()).hexdigest()
                conn = get_db_connection()
                conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                            (v_id, h_v, 'VENDEUR', sid, 'ACTIF', v_name, ''))
                conn.commit(); conn.close()
                st.success("Vendeur ajouté !"); st.rerun()

# --- 7.7 RÉGLAGES BOUTIQUE ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ PARAMÈTRES DE LA BOUTIQUE")
    with st.form("shop_cfg"):
        s_n = st.text_input("Nom de l'Enseigne", shop_data['name'])
        s_r = st.number_input("Taux de change (1$ = ? CDF)", value=shop_data['rate'])
        s_a = st.text_area("Adresse Physique", shop_data['addr'])
        s_t = st.text_input("N° Téléphone", shop_data['tel'])
        s_h = st.text_area("Pied de Facture (Message)", shop_data['head'])
        if st.form_submit_button("💾 SAUVEGARDER LES RÉGLAGES"):
            conn = get_db_connection()
            conn.execute("UPDATE shops SET name=?, rate=?, addr=?, tel=?, head=? WHERE sid=?", (s_n, s_r, s_a, s_t, s_h, sid))
            conn.commit(); conn.close()
            st.success("Informations boutique mises à jour !"); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.auth = False
    st.rerun()

# ==============================================================================
# FIN DU CODE v210 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
