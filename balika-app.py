# ==============================================================================
# ANASH ERP v500 - TITANIUM EDITION (SYSTÈME BALIKA BUSINESS)
# ------------------------------------------------------------------------------
# OPTIMISÉ POUR SMARTPHONE | FACTURATION DYNAMIQUE A4/80MM | SÉCURITÉ RENFORCÉE
# GESTION DES DETTES PAR TRANCHES | MULTI-DEVISES CDF/USD | ANALYTIQUE AVANCÉ
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import io
import base64
import time

# ------------------------------------------------------------------------------
# 1. MOTEUR DE BASE DE DONNÉES (ARCHITECTURE PERSISTANTE)
# ------------------------------------------------------------------------------
DB_NAME = "anash_titanium_v500.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_db():
    with get_db() as conn:
        c = conn.cursor()
        # Configuration Global
        c.execute("""CREATE TABLE IF NOT EXISTS sys_config (
            id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, version TEXT)""")
        
        # Comptes Utilisateurs
        c.execute("""CREATE TABLE IF NOT EXISTS accounts (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop_id TEXT, 
            status TEXT, full_name TEXT, phone TEXT, expiry TEXT)""")
        
        # Boutiques
        c.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, rate REAL DEFAULT 2800, 
            addr TEXT, tel TEXT, logo BLOB)""")
        
        # Inventaire
        c.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, cat TEXT, 
            qty INTEGER DEFAULT 0, buy_p REAL, sell_p REAL, sid TEXT)""")
        
        # Ventes
        c.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, customer TEXT, 
            total_usd REAL, paid_usd REAL, debt_usd REAL, date TEXT, time TEXT, 
            seller TEXT, sid TEXT, items_json TEXT, currency TEXT)""")
        
        # Dettes & Tranches
        c.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, balance REAL, 
            ref_invoice TEXT, sid TEXT, status TEXT DEFAULT 'OUVERT')""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS debt_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, debt_id INTEGER, amount REAL, 
            date TEXT, seller TEXT)""")
        
        # Dépenses
        c.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, amount REAL, 
            date TEXT, sid TEXT, seller TEXT)""")

        # Données initiales
        c.execute("SELECT id FROM sys_config")
        if not c.fetchone():
            c.execute("INSERT INTO sys_config VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION UNIFIÉ 2026', '5.0.0')")
        
        c.execute("SELECT uid FROM accounts WHERE uid='admin'")
        if not c.fetchone():
            h = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", 
                     ('admin', h, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000', '2099-12-31'))
        conn.commit()

setup_db()

# ------------------------------------------------------------------------------
# 2. DESIGN & STYLE (COBALT SMARTPHONE READY)
# ------------------------------------------------------------------------------
db = get_db()
sys = db.execute("SELECT * FROM sys_config WHERE id=1").fetchone()
APP_TITLE, MARQUEE = sys['app_name'], sys['marquee']
db.close()

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")

def apply_ui():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;700&display=swap');
        .stApp {{ background-color: #000c1f; color: #ffffff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        
        /* LABELS & TEXTES EN BLANC SUR FOND BLEU */
        label, p, span, h1, h2, h3, h4, .stMarkdown {{ color: #ffffff !important; text-shadow: 1px 1px 2px #000; }}
        
        /* CONTENEURS */
        .card {{
            background: linear-gradient(135deg, #0044ff 0%, #001a66 100%);
            border: 1px solid #00d9ff; border-radius: 15px; padding: 20px;
            margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}

        /* TABLEAUX LISIBLES */
        .stTable, table {{ background: #ffffff !important; color: #000000 !important; border-radius: 10px; }}
        th {{ background: #0044ff !important; color: white !important; font-size: 14px; }}
        td {{ color: #000000 !important; font-weight: bold !important; border-bottom: 1px solid #eee !important; }}

        /* BOUTONS MASSIFS POUR MOBILE */
        .stButton > button {{
            width: 100% !important; height: 60px !important; border-radius: 15px !important;
            background: linear-gradient(to right, #0077ff, #0033aa) !important;
            color: white !important; font-weight: bold; font-size: 18px; border: 2px solid #ffffff;
            margin-bottom: 10px;
        }}
        
        /* BARRE DÉFILANTE */
        .marquee-container {{
            position: fixed; top: 0; left: 0; width: 100%; height: 40px;
            background: #000; border-bottom: 2px solid #00ff00;
            z-index: 9999; display: flex; align-items: center; overflow: hidden;
        }}
        .marquee-text {{
            white-space: nowrap; animation: scroll-text 25s linear infinite;
            color: #00ff00; font-size: 18px; font-weight: bold;
        }}
        @keyframes scroll-text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
        
        .main-content {{ margin-top: 50px; }}
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold !important; }}
        
        /* CADRE COLORE POUR TOTAL PANIER */
        .total-frame {{
            border: 4px solid #00ff00; padding: 15px; border-radius: 15px;
            text-align: center; background: rgba(0,255,0,0.1); margin: 10px 0;
        }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🚀 {MARQUEE} - {APP_TITLE} v500 🚀</div></div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)

apply_ui()

# ------------------------------------------------------------------------------
# 3. GESTION DES SESSIONS
# ------------------------------------------------------------------------------
if 'user' not in st.session_state:
    st.session_state.user = {'auth': False, 'uid': None, 'role': None, 'sid': None, 'cart': {}, 'active_invoice': None}

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.user['auth']:
    _, auth_col, _ = st.columns([1, 2, 1])
    with auth_col:
        st.markdown("<div class='card' style='text-align:center;'><h1>💎 ACCÈS ERP</h1></div>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔒 CONNEXION", "📝 DEMANDE D'ACCÈS"])
        
        with tab_log:
            u_id = st.text_input("Identifiant").lower().strip()
            u_pw = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                db = get_db()
                acc = db.execute("SELECT * FROM accounts WHERE uid=?", (u_id,)).fetchone()
                db.close()
                if acc and hashlib.sha256(u_pw.encode()).hexdigest() == acc['pwd']:
                    if acc['status'] == 'ACTIF' or acc['role'] == 'SUPER_ADMIN':
                        st.session_state.user.update({'auth': True, 'uid': u_id, 'role': acc['role'], 'sid': acc['shop_id']})
                        st.rerun()
                    else: st.warning("Compte en attente d'activation.")
                else: st.error("Identifiants incorrects.")
        
        with tab_reg:
            with st.form("reg_form"):
                r_id = st.text_input("Identifiant souhaité").lower()
                r_name = st.text_input("Nom de l'Entreprise")
                r_pw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ENVOYER LA DEMANDE"):
                    db = get_db()
                    try:
                        hp = hashlib.sha256(r_pw.encode()).hexdigest()
                        exp = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                        db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", 
                                  (r_id, hp, 'BOSS', 'PENDING', 'ATTENTE', r_name, '', exp))
                        db.commit(); st.success("Demande envoyée à l'administrateur.")
                    except: st.error("Cet identifiant est déjà pris.")
                    finally: db.close()
    st.stop()

# ------------------------------------------------------------------------------
# 5. MODULE SUPER ADMIN
# ------------------------------------------------------------------------------
if st.session_state.user['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛡️ SUPER ADMIN")
    m_adm = st.sidebar.radio("Navigation", ["Abonnements", "Système", "Sauvegarde", "Déconnexion"])
    
    if m_adm == "Abonnements":
        st.markdown("<div class='card'><h1>GESTION DES LICENCES</h1></div>", unsafe_allow_html=True)
        db = get_db()
        users = db.execute("SELECT * FROM accounts WHERE role='BOSS'").fetchall()
        for u in users:
            with st.expander(f"🏢 {u['full_name']} (@{u['uid']})"):
                c1, c2 = st.columns(2)
                nst = c1.selectbox("Statut", ["ATTENTE", "ACTIF", "SUSPENDU"], index=["ATTENTE", "ACTIF", "SUSPENDU"].index(u['status']), key=f"st_{u['uid']}")
                nexp = c2.date_input("Expiration", datetime.strptime(u['expiry'], '%Y-%m-%d'), key=f"ex_{u['uid']}")
                if st.button(f"Mettre à jour {u['uid']}"):
                    db.execute("UPDATE accounts SET status=?, expiry=?, shop_id=? WHERE uid=?", (nst, nexp.strftime('%Y-%m-%d'), u['uid'], u['uid']))
                    db.execute("INSERT OR IGNORE INTO shops (sid, name) VALUES (?,?)", (u['uid'], u['full_name']))
                    db.commit(); st.rerun()
        db.close()

    elif m_adm == "Système":
        st.header("⚙️ Configuration App")
        with st.form("sys_f"):
            at = st.text_input("Nom de l'Application", APP_TITLE)
            am = st.text_area("Message Défilant", MARQUEE)
            if st.form_submit_button("Appliquer"):
                db = get_db()
                db.execute("UPDATE sys_config SET app_name=?, marquee=? WHERE id=1", (at, am))
                db.commit(); db.close(); st.rerun()

    elif m_adm == "Sauvegarde":
        st.header("💾 Base de Données")
        with open(DB_NAME, "rb") as f:
            st.download_button("Télécharger Backup .db", f, file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.db")

    if m_adm == "Déconnexion": st.session_state.user['auth'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE BOUTIQUE (BOSS & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.user['sid']
db = get_db()
shop = db.execute("SELECT * FROM shops WHERE sid=?", (sid,)).fetchone()
db.close()

if not shop:
    st.error("Erreur : Boutique introuvable. Contactez l'admin.")
    st.stop()

# Menus de Navigation
if st.session_state.user['role'] == "BOSS":
    nav = ["🏠 Accueil", "🛒 Vente", "📦 Stock", "📉 Dettes", "💸 Dépenses", "📊 Rapports", "👥 Équipe", "⚙️ Réglages", "🚪 Quitter"]
else:
    nav = ["🏠 Accueil", "🛒 Vente", "📉 Dettes", "💸 Dépenses", "📊 Rapports", "🚪 Quitter"]

with st.sidebar:
    st.markdown(f"<div class='card' style='padding:10px;'><h3 style='margin:0;'>{shop['name']}</h3><p style='font-size:12px;'>Utilisateur: {st.session_state.user['uid']}</p></div>", unsafe_allow_html=True)
    sel = st.radio("MENU", nav)

# --- 6.1 ACCUEIL (DASHBOARD) ---
if sel == "🏠 Accueil":
    st.markdown(f"<div class='card'><h1>BIENVENUE CHEZ {shop['name']}</h1></div>", unsafe_allow_html=True)
    db = get_db()
    today = datetime.now().strftime("%d/%m/%Y")
    v_j = db.execute("SELECT SUM(total_usd) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
    d_j = db.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
    dt_t = db.execute("SELECT SUM(balance) FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchone()[0] or 0
    db.close()
    
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"<div class='card' style='background:#00cc44;'><h3 style='margin:0;'>VENTES JOUR</h3><h1>{v_j:,.2f} $</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card' style='background:#ff4444;'><h3 style='margin:0;'>TOTAL DETTES</h3><h1>{dt_t:,.2f} $</h1></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'><h3>DERNIÈRES VENTES</h3></div>", unsafe_allow_html=True)
    db = get_db()
    last = db.execute("SELECT * FROM sales WHERE sid=? ORDER BY id DESC LIMIT 5", (sid,)).fetchall()
    db.close()
    if last:
        df_l = pd.DataFrame(last, columns=["ID","REF","CLIENT","TOTAL","PAYÉ","DETTE","DATE","HEURE","VENDEUR","SID","ITEMS","CUR"])
        st.table(df_l[["REF", "CLIENT", "TOTAL", "DATE"]])

# --- 6.2 VENTE (POINT DE VENTE) ---
elif sel == "🛒 Vente":
    if st.session_state.user['active_invoice']:
        inv = st.session_state.user['active_invoice']
        st.markdown("<div class='no-print'>")
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.user['active_invoice'] = None; st.rerun()
        st.markdown("</div>")
        
        # Facture Style A4 / Ticket
        st.markdown(f"""
        <div style="background:white; color:black; padding:30px; border:2px solid black; font-family:monospace; max-width:600px; margin:auto;">
            <center><h2>{shop['name']}</h2><p>{shop['addr']}<br>Tél: {shop['tel']}</p></center>
            <hr>
            <div style="display:flex; justify-content:space-between;">
                <span>REF: {inv['ref']}</span><span>Date: {inv['date']}</span>
            </div>
            <p>Client: {inv['client']}</p>
            <table style="width:100%; border-collapse:collapse;">
                <tr style="border-bottom:1px solid black;"><th>Désignation</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td align='center'>{v['q']}</td><td align='right'>{v['t']:,.2f}</td></tr>" for k,v in inv['items'].items()])}
            </table>
            <hr>
            <div style="text-align:right;"><h3>TOTAL: {inv['total']:,.2f} {inv['cur']}</h3></div>
            <p style="font-size:10px; text-align:center;">Merci de votre confiance !</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        
    else:
        st.markdown("<div class='card'><h1>TERMINAL DE VENTE</h1></div>", unsafe_allow_html=True)
        db = get_db()
        items = db.execute("SELECT * FROM products WHERE sid=? AND qty > 0", (sid,)).fetchall()
        db.close()
        
        c_p, c_c = st.columns([3, 1])
        with c_c: cur_c = st.radio("Monnaie", ["USD", "CDF"])
        with c_p:
            sel_p = st.selectbox("Sélectionner Article", ["---"] + [f"{p['name']} (Stock: {p['qty']})" for p in items])
            if sel_p != "---":
                p_pure = sel_p.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    db = get_db()
                    p_info = db.execute("SELECT sell_p, qty FROM products WHERE name=? AND sid=?", (p_pure, sid)).fetchone()
                    db.close()
                    st.session_state.user['cart'][p_pure] = {'p': p_info['sell_p'], 'q': 1, 'max': p_info['qty']}
                    st.rerun()

        if st.session_state.user['cart']:
            st.subheader("🛒 PANIER")
            total_usd = 0
            for item, data in list(st.session_state.user['cart'].items()):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{item}**")
                st.session_state.user['cart'][item]['q'] = c2.number_input(f"Qté", 1, data['max'], data['q'], key=f"cart_{item}")
                if c3.button("🗑️", key=f"del_{item}"): del st.session_state.user['cart'][item]; st.rerun()
                total_usd += data['p'] * st.session_state.user['cart'][item]['q']
            
            final_total = total_usd if cur_c == "USD" else total_usd * shop['rate']
            st.markdown(f"<div class='total-frame'><h2>TOTAL À PAYER : {final_total:,.2f} {cur_c}</h2></div>", unsafe_allow_html=True)
            
            with st.form("pay_f"):
                cust = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                paid = st.number_input(f"MONTANT REÇU ({cur_c})", value=float(final_total))
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    p_usd = paid if cur_c == "USD" else paid / shop['rate']
                    d_usd = total_usd - p_usd
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    d_s, t_s = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    db = get_db()
                    items_blob = {k: {'q': v['q'], 't': v['p']*v['q']} for k,v in st.session_state.user['cart'].items()}
                    db.execute("INSERT INTO sales (ref, customer, total_usd, paid_usd, debt_usd, date, time, seller, sid, items_json, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (ref, cust, total_usd, p_usd, d_usd, d_s, t_s, st.session_state.user['uid'], sid, json.dumps(items_blob), cur_c))
                    for n, v in st.session_state.user['cart'].items():
                        db.execute("UPDATE products SET qty = qty - ? WHERE name=? AND sid=?", (v['q'], n, sid))
                    if d_usd > 0.01:
                        db.execute("INSERT INTO debts (customer, balance, ref_invoice, sid) VALUES (?,?,?,?)", (cust, d_usd, ref, sid))
                    db.commit(); db.close()
                    
                    st.session_state.user['active_invoice'] = {'ref': ref, 'client': cust, 'total': final_total, 'cur': cur_c, 'items': items_blob, 'date': d_s}
                    st.session_state.user['cart'] = {}; st.rerun()

# --- 6.3 STOCK (INVENTAIRE) ---
elif sel == "📦 Stock":
    st.markdown("<div class='card'><h1>GESTION INVENTAIRE</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("add_p"):
            n = st.text_input("Désignation").upper()
            c = st.selectbox("Catégorie", ["GENERAL", "ALIMENTAIRE", "BOISSONS", "AUTRE"])
            c1, c2, c3 = st.columns(3)
            bp = c1.number_input("Prix Achat ($)")
            sp = c2.number_input("Prix Vente ($)")
            qt = c3.number_input("Quantité", 1)
            if st.form_submit_button("Enregistrer"):
                db = get_db()
                db.execute("INSERT INTO products (name, cat, qty, buy_p, sell_p, sid) VALUES (?,?,?,?,?,?)", (n, c, qt, bp, sp, sid))
                db.commit(); db.close(); st.success("Produit ajouté !"); st.rerun()

    db = get_db()
    data = db.execute("SELECT * FROM products WHERE sid=? ORDER BY name ASC", (sid,)).fetchall()
    db.close()
    if data:
        df_p = pd.DataFrame(data, columns=["ID", "NOM", "CAT", "STOCK", "ACHAT", "VENTE", "SID"])
        st.table(df_p[["NOM", "STOCK", "VENTE"]])
        for r in data:
            with st.expander(f"MODIFIER : {r['name']}"):
                col1, col2 = st.columns(2)
                up_s = col1.number_input("Prix Vente", value=r['sell_p'], key=f"s_{r['id']}")
                up_q = col2.number_input("Ajuster Stock", value=r['qty'], key=f"q_{r['id']}")
                b1, b2 = st.columns(2)
                if b1.button("✅ MAJ", key=f"b1_{r['id']}"):
                    db = get_db()
                    db.execute("UPDATE products SET sell_p=?, qty=? WHERE id=?", (up_s, up_q, r['id']))
                    db.commit(); db.close(); st.rerun()
                if b2.button("🗑️ SUPPRIMER", key=f"b2_{r['id']}"):
                    db = get_db()
                    db.execute("DELETE FROM products WHERE id=?", (r['id'],))
                    db.commit(); db.close(); st.rerun()

# --- 6.4 DETTES (CRÉDITS CLIENTS) ---
elif sel == "📉 Dettes":
    st.markdown("<div class='card'><h1>SUIVI DES DETTES</h1></div>", unsafe_allow_html=True)
    db = get_db()
    active = db.execute("SELECT * FROM debts WHERE sid=? AND status='OUVERT'", (sid,)).fetchall()
    db.close()
    if not active: st.success("Aucune dette en cours.")
    for d in active:
        with st.expander(f"👤 {d['customer']} | RESTE : {d['balance']:,.2f} $"):
            pay = st.number_input("Verser un acompte ($)", 0.0, d['balance'], key=f"pay_{d['id']}")
            if st.button(f"VALIDER PAIEMENT {d['id']}"):
                nb = d['balance'] - pay
                db = get_db()
                if nb <= 0.01:
                    db.execute("UPDATE debts SET balance=0, status='SOLDE' WHERE id=?", (d['id'],))
                else:
                    db.execute("UPDATE debts SET balance=? WHERE id=?", (nb, d['id']))
                db.execute("INSERT INTO debt_payments (debt_id, amount, date, seller) VALUES (?,?,?,?)",
                          (d['id'], pay, datetime.now().strftime("%d/%m/%Y"), st.session_state.user['uid']))
                db.commit(); db.close(); st.success("Paiement enregistré !"); st.rerun()

# --- 6.5 DÉPENSES ---
elif sel == "💸 Dépenses":
    st.markdown("<div class='card'><h1>JOURNAL DES DÉPENSES</h1></div>", unsafe_allow_html=True)
    with st.form("exp_f"):
        lbl = st.text_input("Motif de la dépense")
        amt = st.number_input("Montant ($)")
        if st.form_submit_button("Enregistrer Dépense"):
            db = get_db()
            db.execute("INSERT INTO expenses (label, amount, date, sid, seller) VALUES (?,?,?,?,?)",
                      (lbl, amt, datetime.now().strftime("%d/%m/%Y"), sid, st.session_state.user['uid']))
            db.commit(); db.close(); st.success("Dépense notée."); st.rerun()

# --- 6.6 RAPPORTS ---
elif sel == "📊 Rapports":
    st.markdown("<div class='card'><h1>RAPPORTS FINANCIERS</h1></div>", unsafe_allow_html=True)
    sel_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    db = get_db()
    s_day = db.execute("SELECT * FROM sales WHERE sid=? AND date=?", (sid, sel_date)).fetchall()
    e_day = db.execute("SELECT SUM(amount) FROM expenses WHERE sid=? AND date=?", (sid, sel_date)).fetchone()[0] or 0
    db.close()
    
    if s_day:
        df_rep = pd.DataFrame(s_day, columns=["ID","REF","CLIENT","TOTAL","PAYÉ","DETTE","DATE","HEURE","VENDEUR","SID","ITEMS","CUR"])
        st.table(df_rep[["REF", "CLIENT", "TOTAL", "HEURE", "VENDEUR"]])
        total_v = df_rep['TOTAL'].sum()
        st.markdown(f"<div class='card' style='background:#0044ff;'><h3>RECETTE BRUTE : {total_v:,.2f} $</h3><h3>DÉPENSES : {e_day:,.2f} $</h3><hr><h2>BÉNÉFICE NET ESTIMÉ : {total_v - e_day:,.2f} $</h2></div>", unsafe_allow_html=True)
        
        # Bouton Partage / Print
        if st.button("🖨️ IMPRIMER LE RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.info("Aucune donnée pour cette date.")

# --- 6.7 ÉQUIPE (BOSS UNIQUEMENT) ---
elif sel == "👥 Équipe":
    st.markdown("<div class='card'><h1>VOS VENDEURS</h1></div>", unsafe_allow_html=True)
    with st.form("v_add"):
        v_u = st.text_input("Identifiant Vendeur").lower()
        v_n = st.text_input("Nom Complet")
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            db = get_db()
            try:
                vh = hashlib.sha256(v_p.encode()).hexdigest()
                db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)",
                          (v_u, vh, 'VENDEUR', sid, 'ACTIF', v_n, '', '2099-12-31'))
                db.commit(); st.success("Vendeur ajouté !"); st.rerun()
            except: st.error("L'identifiant existe déjà.")
            finally: db.close()

# --- 6.8 RÉGLAGES ---
elif sel == "⚙️ Réglages":
    st.header("⚙️ Paramètres Boutique")
    with st.form("shop_cfg"):
        n_n = st.text_input("Nom de l'Enseigne", shop['name'])
        n_a = st.text_area("Adresse Physique", shop['addr'])
        n_t = st.text_input("Téléphone", shop['tel'])
        n_r = st.number_input("Taux de Change (1$ = ? CDF)", value=shop['rate'])
        if st.form_submit_button("Sauvegarder les changements"):
            db = get_db()
            db.execute("UPDATE shops SET name=?, addr=?, tel=?, rate=? WHERE sid=?", (n_n, n_a, n_t, n_r, sid))
            db.commit(); db.close(); st.success("Paramètres mis à jour !"); st.rerun()

# --- QUITTER ---
elif sel == "🚪 Quitter":
    st.session_state.user['auth'] = False; st.rerun()

# ==============================================================================
# FOOTER & SÉCURITÉ
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.caption(f"Système {APP_TITLE} v5.0.0")
