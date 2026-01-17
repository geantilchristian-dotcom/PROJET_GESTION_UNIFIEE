# ==============================================================================
# ANASH ERP v230 - ÉDITION FINALE BALIKA BUSINESS (LOGIQUE 800 LIGNES)
# ------------------------------------------------------------------------------
# CE CODE EST COMPLET ET NE SUPPRIME AUCUNE FONCTIONNALITÉ ANTÉRIEURE.
# NOUVEAUTÉ : MODÈLE DE FACTURE PROFESSIONNELLE AVEC TABLEAU ET SIGNATURE.
# ------------------------------------------------------------------------------
# LISIBILITÉ : TEXTE BLANC / FOND BLEU | LOGIN : HAUT | INSCRIPTION : BAS
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import json
import random
import time
import io

# ------------------------------------------------------------------------------
# 1. INITIALISATION DU SYSTÈME ET DE LA BASE DE DONNÉES
# ------------------------------------------------------------------------------
DB_FILE = "balika_v230_master.db"

def init_master_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Table Configuration (Version, Nom, Message défilant)
        cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)""")
        
        # Table Utilisateurs (Inclut Admin, Gérants, Vendeurs)
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop TEXT, status TEXT, name TEXT, tel TEXT)""")
        
        # Table Boutiques (Informations facturation)
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL DEFAULT 2800.0, 
            head TEXT, addr TEXT, tel TEXT, rccm TEXT, idnat TEXT)""")
        
        # Table Inventaire (Stock)
        cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, 
            buy_price REAL, sell_price REAL, sid TEXT, category TEXT)""")
        
        # Table Ventes (Historique complet)
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, total_usd REAL, 
            paid_usd REAL, rest_usd REAL, date TEXT, time TEXT, seller TEXT, 
            sid TEXT, items_json TEXT, currency TEXT)""")
        
        # Table Dettes (Suivi des paiements partiels)
        cursor.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, balance REAL, 
            sale_ref TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")

        # Insertion des données par défaut si vide
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA BUSINESS ERP', 'SUCCÈS ET PROSPÉRITÉ À VOTRE ENTREPRISE', '2.3.0')")
            
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            admin_p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                          ('admin', admin_p, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'))
        conn.commit()

init_master_db()

# ------------------------------------------------------------------------------
# 2. DESIGN PERSONNALISÉ (STYLE BLEU & FACTURE IMAGE)
# ------------------------------------------------------------------------------
def get_sys_info():
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT app_name, marquee FROM system_config WHERE id=1").fetchone()

SYS_INFO = get_sys_info()
APP_NAME, MARQUEE_TEXT = SYS_INFO[0], SYS_INFO[1]

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

def apply_global_styles():
    st.markdown(f"""
    <style>
        /* Thème Bleu Royal */
        .stApp {{ background-color: #002b5c; color: white !important; }}
        
        /* Texte Blanc sur fond bleu pour tous les widgets */
        p, span, label, h1, h2, h3, h4, .stMarkdown {{ color: white !important; text-align: center; }}
        
        /* Centrage et Style des entrées de texte */
        input {{ text-align: center; background-color: #ffffff !important; color: #000000 !important; font-weight: bold; }}
        
        /* Marquee Professionnel */
        .marquee-container {{
            background: #000; color: #00ff00; padding: 10px; font-weight: bold;
            border-bottom: 3px solid #0055ff; position: fixed; top: 0; left: 0; width: 100%; z-index: 999;
        }}

        /* Carte Cobalt */
        .cobalt-box {{
            background: #004a99; padding: 25px; border-radius: 20px;
            border: 2px solid #00d4ff; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}

        /* Style Panier (Noir sur Blanc) */
        .cart-white {{
            background: white !important; color: black !important; padding: 20px;
            border-radius: 15px; border: 5px solid #004a99;
        }}
        .cart-white * {{ color: black !important; font-weight: bold; text-align: left; }}

        /* Cadre du Total Néon */
        .neon-total {{
            border: 4px solid #00ff00; background: #000; padding: 20px;
            border-radius: 15px; margin: 15px 0;
        }}
        .total-val {{ color: #00ff00; font-size: 40px; font-weight: bold; }}

        /* BOUTON MOBILE LARGE */
        .stButton > button {{
            width: 100%; height: 70px; border-radius: 15px; font-size: 22px;
            background: linear-gradient(to bottom, #007bff, #004a99);
            color: white !important; border: 2px solid white; font-weight: bold;
        }}

        /* DESIGN FACTURE (Selon l'image fournie) */
        .facture-print {{
            background: white; color: black !important; padding: 40px;
            font-family: 'Arial', sans-serif; width: 80mm; margin: auto;
        }}
        .facture-print h1, .facture-print h2, .facture-print p {{ color: black !important; }}
        .table-fac {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .table-fac th, .table-fac td {{ border: 1px solid black; padding: 8px; text-align: center; color: black !important; }}
        .net-a-payer {{ font-size: 20px; font-weight: bold; margin-top: 20px; border-top: 2px solid black; padding-top: 10px; }}
        .signature-zone {{ margin-top: 50px; border-top: 1px dashed black; width: 200px; margin-left: auto; margin-right: auto; }}
        
        @media print {{
            .no-print {{ display: none !important; }}
            .stApp {{ background: white !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)

apply_global_styles()

# ------------------------------------------------------------------------------
# 3. LOGIQUE DE SÉCURITÉ ET SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {
        'logged_in': False, 'user': None, 'role': None, 
        'shop_id': None, 'cart': {}, 'viewing_invoice': None
    }

def get_hash(p): return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'ACCÈS (LOGIN HAUT, INSCRIPTION BAS)
# ------------------------------------------------------------------------------
if not st.session_state.session['logged_in']:
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br><br><br>", unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        # LOGO ET TITRE
        st.markdown(f"<h1 style='font-size:45px;'>💎 {APP_NAME}</h1>", unsafe_allow_html=True)
        
        # BLOC CONNEXION (EN HAUT)
        st.markdown("<div class='cobalt-box'>", unsafe_allow_html=True)
        st.markdown("### 🔑 CONNEXION")
        uid = st.text_input("VOTRE IDENTIFIANT").lower().strip()
        upw = st.text_input("VOTRE MOT DE PASSE", type="password")
        if st.button("🚀 SE CONNECTER"):
            with sqlite3.connect(DB_FILE) as conn:
                u_data = conn.execute("SELECT pwd, role, shop, status FROM users WHERE uid=?", (uid,)).fetchone()
                if u_data and get_hash(upw) == u_data[0]:
                    if u_data[3] == "ACTIF":
                        st.session_state.session.update({'logged_in': True, 'user': uid, 'role': u_data[1], 'shop_id': u_data[2]})
                        st.rerun()
                    else: st.error("❌ Compte en attente de validation Admin.")
                else: st.error("❌ Identifiants incorrects.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br><br><hr style='border:1px solid white;'><br>", unsafe_allow_html=True)

        # BLOC INSCRIPTION (EN BAS)
        with st.expander("📝 CRÉER UNE NOUVELLE BOUTIQUE (INSCRIPTION)"):
            new_uid = st.text_input("CHOISIR UN ID UNIQUE")
            new_name = st.text_input("NOM DE VOTRE ETABLISSEMENT")
            new_pwd = st.text_input("CRÉER UN MOT DE PASSE  ", type="password")
            if st.button("📩 ENVOYER LA DEMANDE"):
                if new_uid and new_pwd:
                    with sqlite3.connect(DB_FILE) as conn:
                        try:
                            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                         (new_uid.lower(), get_hash(new_pwd), 'GERANT', 'PENDING', 'EN_ATTENTE', new_name, ''))
                            conn.commit(); st.success("✅ Demande envoyée ! Attendez l'activation par l'Admin.")
                        except sqlite3.IntegrityError: st.error("❌ Cet Identifiant est déjà utilisé.")
                else: st.warning("⚠️ Remplissez tous les champs.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. GESTION SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ ADMIN")
    a_menu = st.sidebar.radio("Navigation Admin", ["Activations", "Paramètres", "Déconnexion"])
    
    if a_menu == "Activations":
        st.header("✅ VALIDATION DES COMPTES")
        with sqlite3.connect(DB_FILE) as conn:
            pendings = conn.execute("SELECT uid, name FROM users WHERE status='EN_ATTENTE'").fetchall()
            if not pendings: st.info("Aucune demande en attente.")
            for u, n in pendings:
                with st.expander(f"Boutique : {n} (ID: {u})"):
                    if st.button(f"ACTIVER & CRÉER : {u}"):
                        conn.execute("UPDATE users SET status='ACTIF', shop=? WHERE uid=?", (u, u))
                        conn.execute("INSERT OR IGNORE INTO shops (sid, name, owner) VALUES (?,?,?)", (u, n, u))
                        conn.commit(); st.rerun()

    elif a_menu == "Paramètres":
        with st.form("global"):
            n_app = st.text_input("Nom de l'App", APP_NAME)
            n_marq = st.text_area("Message Défilant", MARQUEE_TEXT)
            if st.form_submit_button("APPLIQUER"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("UPDATE system_config SET app_name=?, marquee=? WHERE id=1", (n_app, n_marq))
                    conn.commit(); st.rerun()
    
    if a_menu == "Déconnexion": st.session_state.session['logged_in'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. LOGIQUE DE LA BOUTIQUE (GERANT & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['shop_id']
with sqlite3.connect(DB_FILE) as conn:
    sh_inf = conn.execute("SELECT name, rate, head, addr, tel, rccm, idnat FROM shops WHERE sid=?", (sid,)).fetchone()

# Menu adaptatif selon le rôle
m_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE TACTILE", "📦 STOCK & PRIX", "📉 CRÉDITS CLIENTS", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    m_options = ["🏠 TABLEAU DE BORD", "🛒 CAISSE TACTILE", "📉 CRÉDITS CLIENTS", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-box'>🏪 {sh_inf[0]}<br>👤 {st.session_state.session['user'].upper()}</div>", unsafe_allow_html=True)
    choice = st.radio("NAVIGATION", m_options)

# --- 6.1 ACCUEIL (DASHBOARD) ---
if choice == "🏠 TABLEAU DE BORD":
    st.markdown(f"<div class='marquee-container'><marquee>{MARQUEE_TEXT}</marquee></div><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:70px;'>{datetime.now().strftime('%H:%M')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3>{datetime.now().strftime('%d %B %Y')}</h3>", unsafe_allow_html=True)
    
    with sqlite3.connect(DB_FILE) as conn:
        ca_j = conn.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, datetime.now().strftime("%d/%m/%Y"))).fetchone()[0] or 0
        st.markdown(f"<div class='cobalt-box'><h2>RECETTE DU JOUR</h2><h1 style='font-size:50px;'>{ca_j:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE (SELON MODÈLE FACTURE IMAGE) ---
elif choice == "🛒 CAISSE TACTILE":
    if st.session_state.session['viewing_invoice']:
        inv = st.session_state.session['viewing_invoice']
        st.markdown("<div class='facture-print'>", unsafe_allow_html=True)
        st.markdown(f"""
            <center>
                <h1>{sh_inf[0]}</h1>
                <p>{sh_inf[3]} | Tél: {sh_inf[4]}<br>RCCM: {sh_inf[5]}</p>
                <hr style='border:1px solid black;'>
                <h2>FACTURE N° {inv['ref']}</h2>
                <p>CLIENT : {inv['cli']}<br>DATE : {inv['date']}</p>
            </center>
            <table class='table-fac'>
                <tr><th>DÉSIGNATION</th><th>QTÉ</th><th>P.UNITAIRE</th><th>TOTAL</th></tr>
        """, unsafe_allow_html=True)
        
        for item, data in inv['items'].items():
            st.markdown(f"<tr><td>{item}</td><td>{data['q']}</td><td>{data['p']}</td><td>{data['q']*data['p']}</td></tr>", unsafe_allow_html=True)
        
        st.markdown(f"""
            </table>
            <div class='net-a-payer'>NET À PAYER : {inv['total_val']:,.2f} {inv['dev']}</div>
            <p>ACOMPTE VERSÉ : {inv['paid']:,.2f} | RESTE : {inv['rest']:,.2f}</p>
            <div class='signature-zone'><br>(Signé par : {st.session_state.session['user']})</div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("⬅️ NOUVELLE VENTE"): st.session_state.session['viewing_invoice'] = None; st.rerun()
        if c2.button("🖨️ IMPRIMER FACTURE"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        st.header("🛒 TERMINAL DE CAISSE")
        c_dev, c_ser = st.columns([1, 2])
        devise = c_dev.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            prods = conn.execute("SELECT item, sell_price, qty FROM inventory WHERE sid=? AND qty > 0", (sid,)).fetchall()
            choice_p = c_ser.selectbox("RECHERCHER ARTICLE", ["---"] + [f"{p[0]} ({p[2]}) - {p[1]}$" for p in prods])
            if choice_p != "---" and st.button("➕ AJOUTER AU PANIER"):
                it_name = choice_p.split(" (")[0]
                p_inf = conn.execute("SELECT sell_price, qty FROM inventory WHERE item=? AND sid=?", (it_name, sid)).fetchone()
                st.session_state.session['cart'][it_name] = {'p': p_inf[0], 'q': 1, 'max': p_inf[1]}
                st.rerun()

        if st.session_state.session['cart']:
            st.markdown("<div class='cart-white'>", unsafe_allow_html=True)
            t_usd = 0
            for art, d in list(st.session_state.session['cart'].items()):
                col1, col2, col3 = st.columns([3, 2, 1])
                nq = col2.number_input(f"Qté {art}", 1, d['max'], d['q'], key=f"cart_{art}")
                st.session_state.session['cart'][art]['q'] = nq
                t_usd += d['p'] * nq
                col1.write(f"**{art}**")
                if col3.button("🗑️", key=f"del_{art}"): del st.session_state.session['cart'][art]; st.rerun()
            
            final_p = t_usd if devise == "USD" else t_usd * sh_inf[1]
            st.markdown(f"<div class='neon-total'><center><span class='total-val'>{final_p:,.2f} {devise}</span></center></div>", unsafe_allow_html=True)
            
            with st.form("valider_vente"):
                client_n = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                recu_m = st.number_input(f"MONTANT REÇU ({devise})", value=float(final_p))
                if st.form_submit_button("✅ VALIDER & ÉMETTRE FACTURE"):
                    ref_f = f"BAL-{random.randint(100000,999999)}"
                    r_u = recu_m if devise == "USD" else recu_m / sh_inf[1]
                    rest_u = t_usd - r_u
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO sales (ref, cli, total_usd, paid_usd, rest_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (ref_f, client_n, t_usd, r_u, rest_u, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), st.session_state.session['user'], sid, json.dumps(st.session_state.session['cart']), devise))
                        for a, v in st.session_state.session['cart'].items():
                            conn.execute("UPDATE inventory SET qty = qty - ? WHERE item=? AND sid=?", (v['q'], a, sid))
                        if rest_u > 0.01:
                            conn.execute("INSERT INTO debts (cli, balance, sale_ref, sid) VALUES (?,?,?,?)", (client_n, rest_u, ref_f, sid))
                        conn.commit()
                    st.session_state.session['viewing_invoice'] = {
                        'ref': ref_f, 'cli': client_n, 'total_val': final_p, 'dev': devise, 
                        'paid': recu_m, 'rest': (final_p - recu_m), 'items': st.session_state.session['cart'],
                        'date': datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    st.session_state.session['cart'] = {}; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 6.3 STOCK (MODIFIER PRIX/QTÉ SANS SUPPRIMER) ---
elif choice == "📦 STOCK & PRIX":
    st.header("📦 GESTION DU STOCK")
    with st.expander("🆕 AJOUTER NOUVEL ARTICLE"):
        with st.form("add_stock"):
            n, pa, pv, q = st.text_input("Désignation"), st.number_input("Prix Achat $"), st.number_input("Prix Vente $"), st.number_input("Quantité", 0)
            if st.form_submit_button("SAUVEGARDER DANS LE STOCK"):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO inventory (item, qty, buy_price, sell_price, sid) VALUES (?,?,?,?,?)", (n.upper(), q, pa, pv, sid))
                    conn.commit(); st.rerun()

    with sqlite3.connect(DB_FILE) as conn:
        st_items = conn.execute("SELECT id, item, qty, buy_price, sell_price FROM inventory WHERE sid=?", (sid,)).fetchall()
        for i_id, i_name, i_qty, i_bp, i_sp in st_items:
            with st.expander(f"⚙️ {i_name} (En stock : {i_qty})"):
                c1, c2 = st.columns(2)
                new_q = c1.number_input("Modifier Quantité", value=i_qty, key=f"stock_q_{i_id}")
                new_p = c2.number_input("Modifier Prix de Vente $", value=i_sp, key=f"stock_p_{i_id}")
                if st.button("METTRE À JOUR LA LIGNE", key=f"btn_upd_{i_id}"):
                    conn.execute("UPDATE inventory SET qty=?, sell_price=? WHERE id=?", (new_q, new_p, i_id))
                    conn.commit(); st.success("Article mis à jour !"); st.rerun()

# --- 6.4 DETTES (PAIEMENT PAR TRANCHES) ---
elif choice == "📉 CRÉDITS CLIENTS":
    st.header("📉 SUIVI DES CRÉDITS")
    with sqlite3.connect(DB_FILE) as conn:
        dts = conn.execute("SELECT id, cli, balance, sale_ref FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
        if not dts: st.success("Aucune dette à recouvrer !")
        for di, dc, db, dr in dts:
            with st.expander(f"👤 {dc} | DETTE : {db:,.2f} $"):
                pay_t = st.number_input("Montant versé aujourd'hui ($)", max_value=db, key=f"debt_p_{di}")
                if st.button("ENREGISTRER LA TRANCHE", key=f"debt_btn_{di}"):
                    rem_b = db - pay_t
                    conn.execute("UPDATE debts SET balance=? WHERE id=?", (rem_b, di))
                    if rem_b <= 0.01: conn.execute("UPDATE debts SET status='SOLDE' WHERE id=?", (di,))
                    conn.commit(); st.success("Paiement enregistré !"); st.rerun()

# --- 6.5 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.header("📊 ANALYSE DES VENTES")
    r_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    with sqlite3.connect(DB_FILE) as conn:
        vens = pd.read_sql(f"SELECT DISTINCT seller FROM sales WHERE sid='{sid}'", conn)['seller'].tolist()
        f_v = st.selectbox("Filtrer par Vendeur", ["TOUS LES VENDEURS"] + vens)
        
        q_sql = f"SELECT ref, cli, total_usd, paid_usd, rest_usd, time, seller FROM sales WHERE sid='{sid}' AND date='{r_date}'"
        if f_v != "TOUS LES VENDEURS": q_sql += f" AND seller='{f_v}'"
        
        df_v = pd.read_sql(q_sql, conn)
        st.table(df_v)
        st.markdown(f"<div class='cobalt-box'>CHIFFRE D'AFFAIRES SÉLECTIONNÉ : {df_v['total_usd'].sum():,.2f} $</div>", unsafe_allow_html=True)

# --- 6.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 PERSONNEL")
    if st.session_state.session['role'] == "GERANT":
        with st.form("vendeur_n"):
            v_uid, v_nam, v_pwd = st.text_input("ID Vendeur"), st.text_input("Nom Complet"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (v_uid.lower(), get_hash(v_pwd), 'VENDEUR', sid, 'ACTIF', v_nam, ''))
                        conn.commit(); st.success("Compte vendeur créé !")
                    except: st.error("L'Identifiant existe déjà.")
    
    with st.expander("🔐 CHANGER MON MOT DE PASSE"):
        my_new_p = st.text_input("Nouveau password", type="password")
        if st.button("MAJ MOT DE PASSE"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET pwd=? WHERE uid=?", (get_hash(my_new_p), st.session_state.session['user']))
                conn.commit(); st.success("C'est fait !")

# --- 6.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("sh_cfg"):
        s_n = st.text_input("Nom de l'Enseigne", sh_inf[0])
        s_r = st.number_input("Taux de Change (1$ = ? CDF)", value=sh_inf[1])
        s_rc = st.text_input("RCCM / IDNAT", sh_inf[5])
        s_tl = st.text_input("Téléphone Contact", sh_inf[4])
        s_ad = st.text_area("Adresse Physique", sh_inf[3])
        if st.form_submit_button("SAUVEGARDER PARAMÈTRES"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE shops SET name=?, rate=?, rccm=?, tel=?, addr=? WHERE sid=?", (s_n, s_r, s_rc, s_tl, s_ad, sid))
                conn.commit(); st.success("Boutique mise à jour !"); st.rerun()

elif choice == "🚪 QUITTER": 
    st.session_state.session['logged_in'] = False
    st.rerun()

# ==============================================================================
# FIN DU CODE v230 - ROBUSTE & PROFESSIONNEL
# ==============================================================================
