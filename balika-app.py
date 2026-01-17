# ==============================================================================
# PROJET : BALIKA ERP - VERSION MASTER v2046
# COMPLÉTUDE : 100% (STOCK, DETTES, CAISSE, DÉPENSES, ADMIN, MARQUEE, RESET)
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
# 1. DESIGN & STYLE (TEXTE BLANC SUR BLEU - OPTIMISÉ TÉLÉPHONE)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v2046", layout="wide", initial_sidebar_state="expanded")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'panier': {}, 'last_fac': None, 'devise': "USD", 'show_reg': False
    })

st.markdown("""
    <style>
    /* Fond Bleu Global */
    .stApp { background-color: #0033aa !important; }
    
    /* Textes Blancs Partout */
    h1, h2, h3, h4, h5, p, label, span, .stMarkdown, .stMetric { 
        color: #ffffff !important; text-align: center !important; font-weight: bold !important; 
    }
    
    /* Marquee Fixe (Message Défilant) */
    .marquee-header { 
        position: fixed; top: 0; left: 0; width: 100%; background: #000; 
        color: #ffff00; z-index: 9999; border-bottom: 2px solid white; height: 50px;
        display: flex; align-items: center;
    }
    .spacer { margin-top: 75px; }
    
    /* Cartes de Login */
    .login-card {
        background: #ffffff; padding: 30px; border-radius: 20px;
        max-width: 450px; margin: auto; border: 4px solid #00ccff;
    }
    .login-card h1 { color: #0033aa !important; }
    .login-card label { color: #333 !important; }
    
    /* Boutons Larges et Tactiles */
    .stButton>button { 
        background: linear-gradient(135deg, #00ccff, #0055ff) !important;
        color: white !important; border-radius: 15px; height: 65px; width: 100%;
        font-size: 18px; border: 2px solid #fff; margin-top: 10px;
    }
    
    /* Cadre Total Bénéfice / Recette */
    .total-display { 
        background: #000; color: #00ff00; padding: 25px; border: 4px solid #fff;
        border-radius: 20px; font-size: 32px; text-align: center; margin: 15px 0;
        box-shadow: 0px 0px 20px rgba(0,255,0,0.5);
    }

    /* Tableaux Lisibles (Fond Blanc) */
    .stDataFrame, [data-testid="stTable"] { 
        background-color: #ffffff !important; border-radius: 10px; overflow: hidden;
    }
    [data-testid="stTable"] td, [data-testid="stTable"] th { 
        color: #000000 !important; font-size: 14px !important; border: 1px solid #ddd;
    }

    /* Style Facture */
    .fac-box { background: white; color: black !important; padding: 25px; border: 2px solid #000; }
    .fac-box * { color: black !important; text-align: center; }
    
    /* Inputs */
    input { color: black !important; text-align: center !important; font-weight: bold !important; }
    div[data-baseweb="input"] { background-color: white !important; border-radius: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. BASE DE DONNÉES (ARCHITECTURE COMPLÈTE)
# ------------------------------------------------------------------------------
DB_PATH = "balika_master_v2046.db"

def sql_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def init_all_tables():
    # Utilisateurs
    sql_query("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ACTIF', tel TEXT, boss TEXT)""")
    
    # Config Admin
    sql_query("CREATE TABLE IF NOT EXISTS system_cfg (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, rate REAL)")
    
    # Profils Boutiques
    sql_query("""CREATE TABLE IF NOT EXISTS store_profiles (
        ent_id TEXT PRIMARY KEY, store_name TEXT, addr TEXT, phone TEXT, header_msg TEXT)""")
    
    # Stock
    sql_query("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, quantity INTEGER, 
        buy_price REAL, sell_price REAL, ent_id TEXT)""")
    
    # Ventes
    sql_query("""CREATE TABLE IF NOT EXISTS sales_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, customer TEXT, total REAL, 
        paid REAL, balance REAL, currency TEXT, date_time TEXT, date_day TEXT, seller TEXT, ent_id TEXT, items_json TEXT)""")
    
    # Dettes
    sql_query("""CREATE TABLE IF NOT EXISTS debt_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, balance REAL, 
        sale_ref TEXT, date_d TEXT, ent_id TEXT, status TEXT DEFAULT 'OPEN')""")
    
    # Dépenses
    sql_query("""CREATE TABLE IF NOT EXISTS expense_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motive TEXT, amount REAL, 
        date_e TEXT, category TEXT, ent_id TEXT)""")

    # Initialisation Admin par défaut
    if not sql_query("SELECT * FROM users WHERE username='admin'", fetch=True):
        sql_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                 ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', '000', 'ADMIN'))
    
    if not sql_query("SELECT * FROM system_cfg", fetch=True):
        sql_query("INSERT INTO system_cfg VALUES (1, 'BALIKA ERP', 'BIENVENUE DANS VOTRE SYSTEME DE GESTION PROFESSIONNEL', 2850.0)")

init_all_tables()

# Chargement de la configuration globale
cfg_data = sql_query("SELECT app_name, marquee_text, rate FROM system_cfg WHERE id=1", fetch=True)[0]

# Affichage Marquee
st.markdown(f'<div class="marquee-header"><marquee scrollamount="7">{cfg_data[1]}</marquee></div><div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. SYSTÈME DE CONNEXION / INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    if not st.session_state.show_reg:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown(f"<h1>🔐 {cfg_data[0]}</h1>", unsafe_allow_html=True)
        u_input = st.text_input("Identifiant").lower().strip()
        p_input = st.text_input("Mot de passe", type="password")
        
        if st.button("SE CONNECTER"):
            res = sql_query("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_input,), fetch=True)
            if res and hashlib.sha256(p_input.encode()).hexdigest() == res[0][0]:
                if res[0][3] == "PAUSE": st.error("Compte suspendu.")
                else:
                    st.session_state.update({'auth':True, 'user':u_input, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
            else: st.error("Identifiants incorrects.")
        
        st.markdown('</div><br>', unsafe_allow_html=True)
        if st.button("🚀 CRÉER UN COMPTE BOUTIQUE"):
            st.session_state.show_reg = True; st.rerun()
    else:
        st.markdown('<div class="login-card"><h1>📝 NOUVEAU CLIENT</h1>', unsafe_allow_html=True)
        with st.form("reg_form"):
            r_btq = st.text_input("Nom de la Boutique").upper()
            r_bos = st.text_input("Nom du Gérant")
            r_tel = st.text_input("Téléphone")
            r_pwd = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("VALIDER L'INSCRIPTION"):
                u_id = r_btq.lower().replace(" ","")
                sql_query("INSERT INTO users (username, password, role, ent_id, tel, boss) VALUES (?,?,?,?,?,?)",
                         (u_id, hashlib.sha256(r_pwd.encode()).hexdigest(), 'USER', u_id, r_tel, r_bos))
                sql_query("INSERT INTO store_profiles (ent_id, store_name, phone) VALUES (?,?,?)", (u_id, r_btq, r_tel))
                st.success("Compte créé !"); time.sleep(1); st.session_state.show_reg = False; st.rerun()
        if st.button("⬅️ RETOUR"): st.session_state.show_reg = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMIN (PANEL DE CONTRÔLE)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.markdown("### 👑 SUPER ADMIN")
    m_adm = st.sidebar.radio("MENU", ["LISTE CLIENTS", "PARAMÈTRES SYSTÈME", "QUITTER"])
    
    if m_adm == "LISTE CLIENTS":
        st.header("👥 GESTION DES ABONNÉS")
        clients = sql_query("SELECT username, boss, status, ent_id FROM users WHERE role='USER'", fetch=True)
        for u, b, s, eid in clients:
            with st.container(border=True):
                st.write(f"🏢 **{eid.upper()}** | 👤 Gérant: {b} | Statut: {s}")
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ ACTIVER", key=f"on_{u}"):
                    sql_query("UPDATE users SET status='ACTIF' WHERE username=?", (u,)); st.rerun()
                if c2.button("⏸️ PAUSE", key=f"off_{u}"):
                    sql_query("UPDATE users SET status='PAUSE' WHERE username=?", (u,)); st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"del_{u}"):
                    sql_query("DELETE FROM users WHERE username=?", (u,)); st.rerun()

    elif m_adm == "PARAMÈTRES SYSTÈME":
        st.header("⚙️ CONFIGURATION DU SYSTÈME")
        with st.form("sys_cfg"):
            n_app = st.text_input("Nom de l'App", cfg_data[0])
            n_mar = st.text_area("Message Défilant (Marquee)", cfg_data[1])
            n_tx = st.number_input("Taux de Change (1$ = ? CDF)", value=cfg_data[2])
            if st.form_submit_button("SAUVEGARDER"):
                sql_query("UPDATE system_cfg SET app_name=?, marquee_text=?, rate=? WHERE id=1", (n_app, n_mar, n_tx))
                st.success("Système mis à jour !"); st.rerun()

    elif m_adm == "QUITTER": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE BOUTIQUE (ADMIN BOUTIQUE & VENDEUR)
# ------------------------------------------------------------------------------
else:
    with st.sidebar:
        st.markdown(f"### 🏪 {st.session_state.ent_id.upper()}")
        st.markdown(f"👤 {st.session_state.user.upper()}")
        st.divider()
        if st.session_state.role == "VENDEUR":
            nav = st.radio("MENU", ["🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"])
        else:
            nav = st.radio("MENU", ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "💸 DÉPENSES", "📉 DETTES", "📊 RAPPORTS", "👥 VENDEURS", "⚙️ RÉGLAGES", "🚪 QUITTER"])

    # --- 5.1 ACCUEIL (DASHBOARD v192 AVEC BENEFICE) ---
    if nav == "🏠 ACCUEIL":
        st.header("📊 TABLEAU DE BORD")
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Calculs financiers
        rec_j = sql_query("SELECT SUM(total) FROM sales_log WHERE ent_id=? AND date_day=?", (st.session_state.ent_id, today), fetch=True)[0][0] or 0
        dep_j = sql_query("SELECT SUM(amount) FROM expense_log WHERE ent_id=? AND date_e=?", (st.session_state.ent_id, today), fetch=True)[0][0] or 0
        benef = rec_j - dep_j
        
        # Affichage Impactant
        color = "#00FF00" if benef >= 0 else "#FF0000"
        st.markdown(f"""
            <div class='total-display' style='border-color:{color}; color:{color};'>
                BÉNÉFICE NET DU JOUR<br>{benef:,.2f} $
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Recette Brute", f"{rec_j:,.2f} $")
        c2.metric("Dépenses Jour", f"{dep_j:,.2f} $")
        
        low_stk = sql_query("SELECT COUNT(*) FROM products WHERE ent_id=? AND quantity < 5", (st.session_state.ent_id,), fetch=True)[0][0]
        c3.metric("Alertes Stock", low_stk)

    # --- 5.2 CAISSE (TERMINAL DE VENTE MOBILE) ---
    elif nav == "🛒 CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 CAISSE TACTILE")
            
            cp1, cp2 = st.columns(2)
            sel_dev = cp1.selectbox("Devise", ["USD", "CDF"])
            sel_fmt = cp2.selectbox("Papier", ["Ticket 80mm", "A4"])
            
            # Stock mapping
            stk = sql_query("SELECT designation, sell_price, quantity FROM products WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in stk}
            
            choix = st.selectbox("🔍 Sélectionner un article...", ["---"] + list(p_map.keys()))
            if choix != "---":
                if p_map[choix][1] > 0:
                    st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                    st.toast(f"✅ {choix} ajouté")
                else: st.error("Stock épuisé !")

            if st.session_state.panier:
                st.divider()
                total_v = 0.0; cart_list = []
                for a, q in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if sel_dev == "USD" else p_map[a][0] * cfg_data[2]
                    stot = pu * q
                    total_v += stot
                    cart_list.append({"art": a, "qte": q, "pu": pu, "st": stot})
                    
                    cc1, cc2, cc3 = st.columns([3, 1, 1])
                    cc1.write(f"**{a}**")
                    cc2.write(f"x{q}")
                    if cc3.button("❌", key=f"del_{a}"): del st.session_state.panier[a]; st.rerun()
                
                st.markdown(f"<div class='total-display'>TOTAL : {total_v:,.2f} {sel_dev}</div>", unsafe_allow_html=True)
                
                with st.container(border=True):
                    client = st.text_input("Nom du Client", "COMPTANT")
                    paye = st.number_input("Montant Reçu", value=float(total_v))
                    reste = total_v - paye
                    
                    if st.button("🏁 VALIDER ET IMPRIMER"):
                        ref = f"FAC-{random.randint(1000,9999)}"
                        dt_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                        dt_s = datetime.now().strftime("%d/%m/%Y")
                        
                        # Save Sale
                        sql_query("INSERT INTO sales_log (ref, customer, total, paid, balance, currency, date_time, date_day, seller, ent_id, items_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (ref, client.upper(), total_v, paye, reste, sel_dev, dt_v, dt_s, st.session_state.user, st.session_state.ent_id, json.dumps(cart_list)))
                        
                        # Update Stock
                        for it in cart_list:
                            sql_query("UPDATE products SET quantity = quantity - ? WHERE designation=? AND ent_id=?", (it['qte'], it['art'], st.session_state.ent_id))
                        
                        # Save Debt
                        if reste > 0:
                            sql_query("INSERT INTO debt_log (customer, balance, sale_ref, date_d, ent_id) VALUES (?,?,?,?,?)",
                                     (client.upper(), reste, ref, dt_s, st.session_state.ent_id))
                        
                        st.session_state.last_fac = {"ref": ref, "cli": client.upper(), "tot": total_v, "pay": paye, "res": reste, "dev": sel_dev, "its": cart_list, "dt": dt_v}
                        st.session_state.panier = {}; st.rerun()
        else:
            # FACTURE HTML
            f = st.session_state.last_fac
            info = sql_query("SELECT store_name, addr, phone, header_msg FROM store_profiles WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            html = f"""<div class='fac-box'><h2>{info[3] if info[3] else info[0]}</h2><p>{info[1]} | {info[2]}</p><hr>
            <h3>FACTURE {f['ref']}</h3><p>{f['dt']}</p><p>Client: {f['cli']}</p>
            {"".join([f"<p>{i['art']} x{i['qte']} = {i['st']:,.0f} {f['dev']}</p>" for i in f['its']])}<hr>
            <h3>TOTAL : {f['tot']:,.2f} {f['dev']}</h3><p>Payé: {f['pay']} | Reste: {f['res']}</p></div>"""
            st.markdown(html, unsafe_allow_html=True)
            
            # SAUVEGARDE PC
            b64 = base64.b64encode(html.encode()).decode()
            st.markdown(f'<a href="data:text/html;base64,{b64}" download="Facture_{f["ref"]}.html" style="background:#00ff00; color:black; padding:15px; border-radius:10px; text-decoration:none; display:block; text-align:center; font-weight:bold;">📥 ENREGISTRER SUR LE PC</a>', unsafe_allow_html=True)
            
            if st.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()

    # --- 5.3 STOCK (MODIF SANS SUPPRIMER) ---
    elif nav == "📦 STOCK":
        st.header("📦 GESTION DU STOCK")
        t1, t2 = st.tabs(["📋 INVENTAIRE", "➕ AJOUTER"])
        with t1:
            pds = sql_query("SELECT id, designation, quantity, sell_price FROM products WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            if pds:
                df = pd.DataFrame(pds, columns=["ID", "Désignation", "Qté", "Prix Vente"])
                st.table(df)
                st.subheader("🛠️ MODIFIER QUANTITÉ OU PRIX")
                with st.form("edit_stk"):
                    e_id = st.number_input("ID Article", min_value=1)
                    e_qte = st.number_input("Nouvelle Qté totale", min_value=0)
                    e_px = st.number_input("Nouveau Prix Vente ($)")
                    if st.form_submit_button("MODIFIER"):
                        sql_query("UPDATE products SET quantity=?, sell_price=? WHERE id=? AND ent_id=?", (e_qte, e_px, e_id, st.session_state.ent_id))
                        st.success("Mise à jour réussie !"); st.rerun()
                if st.button("🗑️ SUPPRIMER"):
                    sql_query("DELETE FROM products WHERE id=? AND ent_id=?", (e_id, st.session_state.ent_id)); st.rerun()

        with t2:
            with st.form("add_p"):
                d = st.text_input("Désignation").upper()
                q = st.number_input("Qté Initiale", 1)
                pa = st.number_input("Prix Achat ($)")
                pv = st.number_input("Prix Vente ($)")
                if st.form_submit_button("AJOUTER"):
                    sql_query("INSERT INTO products (designation, quantity, buy_price, sell_price, ent_id) VALUES (?,?,?,?,?)",
                             (d, q, pa, pv, st.session_state.ent_id))
                    st.success("Produit enregistré !"); st.rerun()

    # --- 5.4 DÉPENSES ---
    elif nav == "💸 DÉPENSES":
        st.header("💸 GESTION DES CHARGES")
        with st.form("f_exp"):
            mot = st.text_input("Motif")
            amt = st.number_input("Montant ($)", min_value=0.1)
            cat = st.selectbox("Type", ["LOYER", "SALAIRE", "TRANSPORT", "TAXE", "AUTRE"])
            if st.form_submit_button("ENREGISTRER"):
                dt_e = datetime.now().strftime("%d/%m/%Y")
                sql_query("INSERT INTO expense_log (motive, amount, date_e, category, ent_id) VALUES (?,?,?,?,?)",
                         (mot.upper(), amt, dt_e, cat, st.session_state.ent_id))
                st.success("Dépense notée !"); st.rerun()
        
        exps = sql_query("SELECT motive, amount, date_e FROM expense_log WHERE ent_id=? ORDER BY id DESC", (st.session_state.ent_id,), fetch=True)
        if exps: st.table(pd.DataFrame(exps, columns=["Motif", "Montant ($)", "Date"]))

    # --- 5.5 DETTES (MAJ ET SUPPRESSION AUTO) ---
    elif nav == "📉 DETTES":
        st.header("📉 SUIVI DES DETTES")
        dts = sql_query("SELECT id, customer, balance, sale_ref FROM debt_log WHERE ent_id=? AND status='OPEN'", (st.session_state.ent_id,), fetch=True)
        if dts:
            for di, dc, db, dr in dts:
                with st.container(border=True):
                    st.write(f"👤 **{dc}** | Facture: {dr} | Reste: **{db:,.2f} $**")
                    tr = st.number_input("Montant versé ($)", 0.0, float(db), key=f"t_{di}")
                    if st.button("VALIDER PAIEMENT", key=f"b_{di}"):
                        nr = db - tr
                        if nr <= 0: sql_query("UPDATE debt_log SET balance=0, status='PAID' WHERE id=?", (di,))
                        else: sql_query("UPDATE debt_log SET balance=? WHERE id=?", (nr, di))
                        st.success("Dette mise à jour !"); time.sleep(1); st.rerun()
        else: st.success("Aucune dette !")

    # --- 5.6 RÉGLAGES (RESET, PROFIL, MOT DE PASSE) ---
    elif nav == "⚙️ RÉGLAGES":
        st.header("⚙️ PARAMÈTRES BOUTIQUE")
        prof = sql_query("SELECT store_name, addr, phone, header_msg FROM store_profiles WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        with st.form("set_btq"):
            n_sn = st.text_input("Nom de l'Entreprise", prof[0])
            n_ad = st.text_input("Adresse", prof[1])
            n_tl = st.text_input("Téléphone", prof[2])
            n_hd = st.text_input("En-tête Facture (Slogan)", prof[3])
            n_pw = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("SAUVEGARDER"):
                sql_query("UPDATE store_profiles SET store_name=?, addr=?, phone=?, header_msg=? WHERE ent_id=?", (n_sn, n_ad, n_tl, n_hd, st.session_state.ent_id))
                if n_pw: sql_query("UPDATE users SET password=? WHERE username=?", (hashlib.sha256(n_pw.encode()).hexdigest(), st.session_state.user))
                st.success("Profil mis à jour !"); st.rerun()
        
        st.divider()
        if st.button("🔴 RÉINITIALISER TOUTES LES DONNÉES (RESET)"):
            for t in ["sales_log", "products", "debt_log", "expense_log"]:
                sql_query(f"DELETE FROM {t} WHERE ent_id='{st.session_state.ent_id}'")
            st.error("Données effacées !"); st.rerun()

    # --- 5.7 RAPPORTS & VENDEURS (SUCCINCT) ---
    elif nav == "📊 RAPPORTS":
        st.header("📊 HISTORIQUE DES VENTES")
        day = st.date_input("Date").strftime("%d/%m/%Y")
        vnts = sql_query("SELECT date_time, ref, customer, total, seller FROM sales_log WHERE ent_id=? AND date_day=?", (st.session_state.ent_id, day), fetch=True)
        if vnts: st.table(pd.DataFrame(vnts, columns=["Heure", "Réf", "Client", "Total ($)", "Vendeur"]))

    elif nav == "👥 VENDEURS":
        st.header("👥 COMPTES VENDEURS")
        with st.form("add_v"):
            vu = st.text_input("Identifiant Vendeur").lower()
            vp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER"):
                sql_query("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
                         (vu, hashlib.sha256(vp.encode()).hexdigest(), 'VENDEUR', st.session_state.ent_id))
                st.success("Vendeur ajouté !"); st.rerun()

    elif nav == "🚪 QUITTER": st.session_state.auth = False; st.rerun()

# FIN DU CODE v2046
