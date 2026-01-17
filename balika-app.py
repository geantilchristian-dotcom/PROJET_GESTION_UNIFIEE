# ==============================================================================
# ANASH ERP v260 - SYSTÈME DE GESTION INTÉGRAL (ÉDITION FINALE BALIKA)
# ------------------------------------------------------------------------------
# FIX CONTRASTE TOTAL | MESSAGE DÉFILANT PERSISTANT | OPTIMISATION SMARTPHONE
# TOUTES LES LIGNES SONT PRÉSENTES - AUCUNE SUPPRESSION
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import os
import base64

# ------------------------------------------------------------------------------
# 1. BASE DE DONNÉES ET PERSISTANCE
# ------------------------------------------------------------------------------
DB_FILE = "anash_v260_enterprise.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_master_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # Système
        cursor.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT)")
        # Comptes (Admin, Boss, Vendeur)
        cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop_id TEXT, status TEXT, 
            name TEXT, expiry TEXT)""")
        # Boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, name TEXT, rate REAL DEFAULT 2800, addr TEXT, tel TEXT)""")
        # Stock & Ventes
        cursor.execute("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, buy REAL, sell REAL, sid TEXT)")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, tot REAL, 
            paid REAL, rest REAL, date TEXT, time TEXT, seller TEXT, sid TEXT, items TEXT, cur TEXT)""")
        cursor.execute("CREATE TABLE IF NOT EXISTS credit (id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, bal REAL, ref TEXT, sid TEXT, state TEXT DEFAULT 'OUVERT')")

        # Initialisation
        cursor.execute("SELECT id FROM config")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO config VALUES (1, 'ANASH BUSINESS v260', 'BIENVENUE CHEZ BALIKA BUSINESS - GESTION PROFESSIONNELLE EN TEMPS RÉEL')")
        
        cursor.execute("SELECT uid FROM accounts WHERE uid='admin'")
        if not cursor.fetchone():
            p = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", ('admin', p, 'SUPER_ADMIN', 'SYS', 'ACTIF', 'ADMIN', '2099-12-31'))
        conn.commit()

setup_master_db()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT CONFIGURATION
# ------------------------------------------------------------------------------
db = get_db()
conf = db.execute("SELECT * FROM config WHERE id=1").fetchone()
APP_NAME, MARQUEE_MSG = conf['app_name'], conf['marquee']
db.close()

# ------------------------------------------------------------------------------
# 3. DESIGN CSS ULTIME (CORRECTION CONTRASTE & LABELS)
# ------------------------------------------------------------------------------
st.set_page_config(page_title=APP_NAME, layout="wide")

def apply_ui_theme():
    st.markdown(f"""
    <style>
        /* FOND ET TEXTE DE BASE */
        .stApp {{ background-color: #000a1a; color: #ffffff !important; }}
        
        /* CORRECTION CRITIQUE : LABELS ET TEXTES DES INPUTS */
        label, .stMarkdown, p, span, h1, h2, h3 {{ color: #ffffff !important; font-weight: bold !important; }}
        
        /* MESSAGE DÉFILANT (MARQUEE) */
        .marquee-container {{
            position: fixed; top: 0; left: 0; width: 100%; height: 45px;
            background: #000000; border-bottom: 3px solid #00ff00;
            z-index: 10000; display: flex; align-items: center; overflow: hidden;
        }}
        .marquee-text {{
            white-space: nowrap; display: inline-block;
            animation: scroll-left 25s linear infinite;
            color: #00ff00; font-size: 20px; font-weight: 900; font-family: sans-serif;
        }}
        @keyframes scroll-left {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        /* BOITES BLEUES COBALT */
        .cobalt-card {{
            background: linear-gradient(135deg, #0044ff 0%, #001a66 100%);
            border-radius: 15px; padding: 25px; margin: 15px 0;
            border: 1px solid #00d9ff; text-align: center;
        }}

        /* TABLEAUX BLANCS LISIBLES */
        .stTable, table {{ background-color: white !important; color: black !important; border-radius: 10px; }}
        th {{ background-color: #0044ff !important; color: white !important; text-align: center !important; }}
        td {{ color: black !important; text-align: center !important; font-weight: bold !important; border-bottom: 1px solid #ddd !important; }}

        /* BOUTONS MOBILE TACTILE */
        .stButton > button {{
            width: 100% !important; height: 50px !important; border-radius: 12px !important;
            background: linear-gradient(to bottom, #0055ff, #002288) !important;
            color: white !important; border: 2px solid white !important; font-size: 16px;
        }}

        /* SIDEBAR BLANCHE */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold !important; }}

        .spacer {{ margin-top: 60px; }}
    </style>
    <div class="marquee-container">
        <div class="marquee-text">🚀 {MARQUEE_MSG} | {APP_NAME} | BALIKA BUSINESS SOLUTIONS 🚀</div>
    </div>
    <div class="spacer"></div>
    """, unsafe_allow_html=True)

apply_ui_theme()

# ------------------------------------------------------------------------------
# 4. GESTION SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {'auth': False, 'uid': None, 'role': None, 'sid': None, 'cart': {}, 'receipt': None}

# ------------------------------------------------------------------------------
# 5. ÉCRAN DE CONNEXION (CORRIGÉ)
# ------------------------------------------------------------------------------
if not st.session_state.session['auth']:
    _, login_area, _ = st.columns([1, 2, 1])
    with login_area:
        st.markdown("<div class='cobalt-card'><h1>💎 ACCÈS SYSTÈME</h1><p>Connectez-vous pour gérer votre business</p></div>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔒 CONNEXION", "📝 CRÉER COMPTE"])
        
        with t_log:
            u = st.text_input("Utilisateur (ID)").lower().strip()
            p = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                db = get_db()
                row = db.execute("SELECT * FROM accounts WHERE uid=?", (u,)).fetchone()
                db.close()
                if row and hashlib.sha256(p.encode()).hexdigest() == row['pwd']:
                    if row['status'] == 'ACTIF' or row['role'] == 'SUPER_ADMIN':
                        exp = datetime.strptime(row['expiry'], '%Y-%m-%d')
                        if datetime.now() > exp and row['role'] != 'SUPER_ADMIN':
                            st.error("Abonnement expiré. Contactez l'admin.")
                        else:
                            st.session_state.session.update({'auth': True, 'uid': u, 'role': row['role'], 'sid': row['shop_id']})
                            st.rerun()
                    else: st.warning("Compte en attente d'activation.")
                else: st.error("Accès refusé.")
        
        with t_reg:
            with st.form("signup"):
                new_u = st.text_input("ID souhaité").lower()
                new_n = st.text_input("Nom de la Boutique")
                new_p = st.text_input("Nouveau Mot de passe", type="password")
                if st.form_submit_button("S'INSCRIRE"):
                    db = get_db()
                    try:
                        h = hashlib.sha256(new_p.encode()).hexdigest()
                        trial = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                        db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", (new_u, h, 'BOSS', 'PENDING', 'ATTENTE', new_n, trial))
                        db.commit(); st.success("Demande envoyée !")
                    except: st.error("Cet ID existe déjà.")
                    finally: db.close()
    st.stop()

# ------------------------------------------------------------------------------
# 6. PANEL SUPER ADMIN (CORRIGÉ)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛠️ MASTER ADMIN")
    a_menu = st.sidebar.radio("Navigation", ["Abonnés", "Système Global", "Mon Profil Admin", "Sauvegarde", "Quitter"])
    
    if a_menu == "Abonnés":
        st.header("👥 VALIDATION DES CLIENTS")
        db = get_db()
        users = db.execute("SELECT * FROM accounts WHERE role='BOSS'").fetchall()
        for u in users:
            with st.expander(f"{u['name']} (@{u['uid']}) - {u['status']}"):
                col_st, col_dt = st.columns(2)
                s_new = col_st.selectbox("Statut", ["ATTENTE", "ACTIF", "OFF"], index=["ATTENTE", "ACTIF", "OFF"].index(u['status']), key=f"s_{u['uid']}")
                d_new = col_dt.date_input("Expiration", datetime.strptime(u['expiry'], '%Y-%m-%d'), key=f"d_{u['uid']}")
                if st.button("Appliquer", key=f"btn_{u['uid']}"):
                    db.execute("UPDATE accounts SET status=?, expiry=?, shop_id=? WHERE uid=?", (s_new, d_new.strftime('%Y-%m-%d'), u['uid'], u['uid']))
                    db.execute("INSERT OR IGNORE INTO shops (sid, name) VALUES (?,?)", (u['uid'], u['name']))
                    db.commit(); st.rerun()
        db.close()

    elif a_menu == "Système Global":
        st.header("⚙️ CONFIGURATION APP")
        with st.form("sys"):
            new_title = st.text_input("Nom de l'App", APP_NAME)
            new_marq = st.text_area("Texte défilant", MARQUEE_MSG)
            if st.form_submit_button("Sauvegarder Global"):
                db = get_db()
                db.execute("UPDATE config SET app_name=?, marquee=? WHERE id=1", (new_title, new_marq))
                db.commit(); db.close(); st.rerun()

    elif a_menu == "Mon Profil Admin":
        st.header("👤 MON PROFIL")
        with st.form("prof_a"):
            a_id = st.text_input("Mon Login", st.session_state.session['uid'])
            a_pw = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("Changer mes accès"):
                db = get_db()
                if a_pw:
                    hp = hashlib.sha256(a_pw.encode()).hexdigest()
                    db.execute("UPDATE accounts SET uid=?, pwd=? WHERE uid=?", (a_id, hp, st.session_state.session['uid']))
                else:
                    db.execute("UPDATE accounts SET uid=? WHERE uid=?", (a_id, st.session_state.session['uid']))
                db.commit(); db.close(); st.session_state.session['auth'] = False; st.rerun()

    elif a_menu == "Sauvegarde":
        with open(DB_FILE, "rb") as f:
            st.download_button("📥 Télécharger Base de Données", f, file_name=f"backup_anash_{datetime.now().strftime('%Y%m%d')}.db")

    if a_menu == "Quitter": st.session_state.session['auth'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. LOGIQUE BOUTIQUE (BOSS / VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['sid']
db = get_db()
sh = db.execute("SELECT * FROM shops WHERE sid=?", (sid,)).fetchone()
acc = db.execute("SELECT expiry FROM accounts WHERE uid=?", (st.session_state.session['uid'],)).fetchone()
db.close()

if not sh:
    st.error("Erreur d'initialisation de la boutique. Contactez l'Admin.")
    st.stop()

# Navigation
main_nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    main_nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='cobalt-card'><h3>{sh['name']}</h3><p>Expire : {acc['expiry']}</p></div>", unsafe_allow_html=True)
    sel = st.radio("MENU", main_nav)

# --- 7.1 ACCUEIL ---
if sel == "🏠 ACCUEIL":
    st.markdown("<div class='cobalt-card'><h1>TABLEAU DE BORD</h1></div>", unsafe_allow_html=True)
    db = get_db()
    today = datetime.now().strftime("%d/%m/%Y")
    ventes = db.execute("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
    dettes = db.execute("SELECT SUM(bal) FROM credit WHERE sid=? AND state='OUVERT'", (sid,)).fetchone()[0] or 0
    db.close()
    
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"<div style='border:3px solid #00ff00; border-radius:15px; text-align:center; padding:20px;'><h3 style='color:#00ff00;'>RECETTE JOUR</h3><h1 style='color:#00ff00;'>{ventes:,.2f} $</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div style='border:3px solid #ff4444; border-radius:15px; text-align:center; padding:20px;'><h3 style='color:#ff4444;'>DETTES TOTALES</h3><h1 style='color:#ff4444;'>{dettes:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 7.2 CAISSE & FACTURE ADMINISTRATIVE ---
elif sel == "🛒 CAISSE":
    if st.session_state.session['receipt']:
        r = st.session_state.session['receipt']
        st.markdown("<div class='no-print'>")
        if st.button("⬅️ RETOUR"): st.session_state.session['receipt'] = None; st.rerun()
        f_type = st.radio("Format", ["80mm", "A4 Administrative"], horizontal=True)
        st.markdown("</div>")

        width = "320px" if f_type == "80mm" else "100%"
        st.markdown(f"""
        <div style="background:white; color:black; padding:30px; border-radius:10px; width:{width}; margin:auto; font-family:monospace;">
            <h2 style="text-align:center; margin:0;">{sh['name']}</h2>
            <p style="text-align:center;">{sh['addr']}<br>Tel: {sh['tel']}</p>
            <hr style="border:1px dashed black;">
            <p style="text-align:center; font-weight:bold;">FACTURE {r['ref']}</p>
            <table style="width:100%; text-align:left;">
                <tr style="border-bottom:1px solid black;"><th>Article</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td>{v['tot']:,.2f}</td></tr>" for k,v in r['items'].items()])}
            </table>
            <hr style="border:1px dashed black;">
            <h3 style="text-align:right;">TOTAL: {r['tot']:,.2f} {r['cur']}</h3>
            <p style="text-align:center; font-size:11px; margin-top:20px;">Vendeur: {st.session_state.session['uid'].upper()}<br>Merci pour votre visite !</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        db = get_db()
        items = db.execute("SELECT * FROM stock WHERE sid=? AND qty > 0", (sid,)).fetchall()
        db.close()
        
        l_col, r_col = st.columns([2, 1])
        with r_col:
            monnaie = st.selectbox("Monnaie", ["USD", "CDF"])
            taux = sh['rate']
        with l_col:
            choice = st.selectbox("Sélectionner un produit", ["---"] + [f"{i['item']} (Dispo: {i['qty']})" for i in items])
            if choice != "---":
                name = choice.split(" (")[0]
                if st.button("➕ AJOUTER AU PANIER"):
                    db = get_db()
                    it_d = db.execute("SELECT sell, qty FROM stock WHERE item=? AND sid=?", (name, sid)).fetchone()
                    db.close()
                    st.session_state.session['cart'][name] = {'p': it_d['sell'], 'q': 1, 'max': it_d['qty']}
                    st.rerun()

        if st.session_state.session['cart']:
            st.subheader("📋 PANIER")
            total_usd = 0.0
            for k, v in list(st.session_state.session['cart'].items()):
                st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:10px; border-radius:10px; margin-bottom:5px;'><b>{k}</b> | {v['p']}$</div>", unsafe_allow_html=True)
                cq, cd = st.columns([3, 1])
                st.session_state.session['cart'][k]['q'] = cq.number_input("Qté", 1, v['max'], v['q'], key=f"q_{k}")
                total_usd += v['p'] * st.session_state.session['cart'][k]['q']
                if cd.button("🗑️", key=f"del_{k}"): del st.session_state.session['cart'][k]; st.rerun()

            display_tot = total_usd if monnaie == "USD" else total_usd * taux
            st.markdown(f"<div class='cobalt-card'><h2>TOTAL : {display_tot:,.2f} {monnaie}</h2></div>", unsafe_allow_html=True)
            
            with st.form("valider"):
                client = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                recu = st.number_input(f"MONTANT REÇU ({monnaie})", value=float(display_tot))
                if st.form_submit_button("✅ CONFIRMER LA VENTE"):
                    p_usd = recu if monnaie == "USD" else recu / taux
                    rest_usd = total_usd - p_usd
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    d_n, t_n = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    db = get_db()
                    js = {k: {'q': v['q'], 'tot': v['p']*v['q']} for k,v in st.session_state.session['cart'].items()}
                    db.execute("INSERT INTO sales (ref, cli, tot, paid, rest, date, time, seller, sid, items, cur) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (ref, client, total_usd, p_usd, rest_usd, d_n, t_n, st.session_state.session['uid'], sid, json.dumps(js), monnaie))
                    for n, d in st.session_state.session['cart'].items():
                        db.execute("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], n, sid))
                    if rest_usd > 0.01:
                        db.execute("INSERT INTO credit (cli, bal, ref, sid) VALUES (?,?,?,?)", (client, rest_usd, ref, sid))
                    db.commit(); db.close()
                    
                    st.session_state.session['receipt'] = {'ref': ref, 'cli': client, 'tot': display_tot, 'cur': monnaie, 'items': js, 'date': d_n, 'time': t_n}
                    st.session_state.session['cart'] = {}; st.rerun()

# --- 7.3 STOCK (TABLEAUX CENTRÉS) ---
elif sel == "📦 STOCK":
    st.header("📦 GESTION DES ARTICLES")
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("add_s"):
            nom = st.text_input("Désignation").upper()
            pa, pv = st.number_input("Prix Achat $"), st.number_input("Prix Vente $")
            qt = st.number_input("Quantité", 1)
            if st.form_submit_button("Sauvegarder Article"):
                db = get_connection()
                db.execute("INSERT INTO stock (item, qty, buy, sell, sid) VALUES (?,?,?,?,?)", (nom, qt, pa, pv, sid))
                db.commit(); db.close(); st.rerun()
    
    db = get_db()
    stk = db.execute("SELECT * FROM stock WHERE sid=? ORDER BY item", (sid,)).fetchall()
    db.close()
    if stk:
        df = pd.DataFrame(stk, columns=["ID", "ARTICLE", "QTÉ", "ACHAT", "VENTE", "SID"])
        st.table(df[["ARTICLE", "QTÉ", "VENTE"]])
        for s in stk:
            with st.expander(f"MODIFIER: {s['item']}"):
                col_p, col_q = st.columns(2)
                nv_p = col_p.number_input("Prix $", value=s['sell'], key=f"p_{s['id']}")
                nv_q = col_q.number_input("Stock", value=s['qty'], key=f"q_{s['id']}")
                if st.button(f"MAJ {s['id']}", key=f"up_{s['id']}"):
                    db = get_db()
                    db.execute("UPDATE stock SET sell=?, qty=? WHERE id=?", (nv_p, nv_q, s['id']))
                    db.commit(); db.close(); st.rerun()

# --- 7.4 DETTES ---
elif sel == "📉 DETTES":
    st.header("📉 CRÉDITS CLIENTS")
    db = get_db()
    dettes = db.execute("SELECT * FROM credit WHERE sid=? AND state='OUVERT'", (sid,)).fetchall()
    if not dettes: st.info("Aucune dette en cours.")
    for d in dettes:
        with st.expander(f"👤 {d['cli']} | {d['bal']:,.2f} $"):
            pay = st.number_input("Payer tranche ($)", 0.0, d['bal'], key=f"t_{d['id']}")
            if st.button(f"Valider paiement {d['id']}"):
                rem = d['bal'] - pay
                if rem <= 0.01: db.execute("UPDATE credit SET bal=0, state='SOLDE' WHERE id=?", (d['id'],))
                else: db.execute("UPDATE credit SET bal=? WHERE id=?", (rem, d['id']))
                db.commit(); st.rerun()
    db.close()

# --- 7.5 RAPPORTS ---
elif sel == "📊 RAPPORTS":
    st.markdown("<div class='cobalt-card'><h1>HISTORIQUE DE VENTES</h1></div>", unsafe_allow_html=True)
    f_date = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    db = get_db()
    reps = db.execute("SELECT * FROM sales WHERE sid=? AND date=?", (sid, f_date)).fetchall()
    db.close()
    if reps:
        df_r = pd.DataFrame(reps, columns=["ID","REF","CLIENT","TOTAL","PAYÉ","RESTE","DATE","HEURE","VENDEUR","SID","JS","CUR"])
        st.table(df_r[["REF", "CLIENT", "TOTAL", "HEURE", "VENDEUR"]])
        st.markdown(f"<div class='cobalt-card'><h2>TOTAL GÉNÉRÉ LE {f_date} : {df_r['TOTAL'].sum():,.2f} $</h2></div>", unsafe_allow_html=True)
    else: st.info("Aucune vente enregistrée.")

# --- 7.6 ÉQUIPE & MON PROFIL ---
elif sel == "👥 ÉQUIPE":
    st.header("👥 MON COMPTE & ÉQUIPE")
    with st.expander("👤 CHANGER MES ACCÈS PERSONNELS"):
        with st.form("prof_b"):
            m_id = st.text_input("Mon Login", st.session_state.session['uid'])
            m_p = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("Mettre à jour mon profil"):
                db = get_db()
                if m_p:
                    hp = hashlib.sha256(m_p.encode()).hexdigest()
                    db.execute("UPDATE accounts SET uid=?, pwd=? WHERE uid=?", (m_id, hp, st.session_state.session['uid']))
                else:
                    db.execute("UPDATE accounts SET uid=? WHERE uid=?", (m_id, st.session_state.session['uid']))
                db.commit(); db.close(); st.session_state.session['auth'] = False; st.rerun()

    if st.session_state.session['role'] == "BOSS":
        st.divider()
        with st.form("add_v"):
            v_id = st.text_input("ID Vendeur").lower()
            v_pw = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Ajouter Vendeur"):
                db = get_db()
                hp = hashlib.sha256(v_pw.encode()).hexdigest()
                db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", (v_id, hp, 'VENDEUR', sid, 'ACTIF', 'VENDEUR', acc['expiry']))
                db.commit(); db.close(); st.success("Vendeur ajouté !")

# --- 7.7 RÉGLAGES ---
elif sel == "⚙️ RÉGLAGES":
    st.header("⚙️ RÉGLAGES BOUTIQUE")
    with st.form("sett"):
        n = st.text_input("Nom de l'Enseigne", sh['name'])
        r = st.number_input("Taux CDF", value=sh['rate'])
        a = st.text_area("Adresse", sh['addr'])
        t = st.text_input("Téléphone", sh['tel'])
        if st.form_submit_button("Enregistrer Réglages"):
            db = get_db()
            db.execute("UPDATE shops SET name=?, rate=?, addr=?, tel=? WHERE sid=?", (n, r, a, t, sid))
            db.commit(); db.close(); st.success("Réglages mis à jour !"); st.rerun()

elif sel == "🚪 QUITTER":
    st.session_state.session['auth'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v260 - ANASH ERP BALIKA BUSINESS
# ==============================================================================
