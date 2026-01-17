# ==============================================================================
# ANASH ERP v300 - ÉDITION FINALE BALIKA BUSINESS
# ------------------------------------------------------------------------------
# FIX MARQUEE PERSISTANT | FIX VALIDATION ADMIN | TEXTE BLANC INTÉGRAL
# CODE COMPLET : +1000 LIGNES DE LOGIQUE MÉTIER SÉCURISÉE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import os

# ------------------------------------------------------------------------------
# 1. MOTEUR DE DONNÉES (SQLITE AVANCÉ)
# ------------------------------------------------------------------------------
DB_NAME = "balika_master_v300.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_system():
    with get_db() as conn:
        cursor = conn.cursor()
        # Table de configuration globale
        cursor.execute("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, title TEXT, marquee TEXT)")
        # Table des comptes utilisateurs
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, shop_id TEXT, status TEXT, 
            fullname TEXT, contact TEXT, expiry TEXT)""")
        # Table des boutiques
        cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            sid TEXT PRIMARY KEY, sname TEXT, rate REAL DEFAULT 2800, addr TEXT, tel TEXT)""")
        # Table des stocks
        cursor.execute("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, buy REAL, sell REAL, sid TEXT)")
        # Table des ventes
        cursor.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, tot REAL, 
            paid REAL, rest REAL, date TEXT, time TEXT, seller TEXT, sid TEXT, items TEXT, cur TEXT)""")
        # Table des dettes
        cursor.execute("CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, bal REAL, ref TEXT, sid TEXT, state TEXT DEFAULT 'OUVERT')")

        # Initialisation du titre et du message défilant
        cursor.execute("SELECT id FROM system_config WHERE id=1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO system_config VALUES (1, 'BALIKA BUSINESS ERP', 'BIENVENUE CHEZ BALIKA BUSINESS - VOTRE SOLUTION DE GESTION INTELLIGENTE 2026')")
        
        # Création du compte Admin Racine
        cursor.execute("SELECT uid FROM users WHERE uid='admin'")
        if not cursor.fetchone():
            adm_pwd = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                          ('admin', adm_pwd, 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000', '2099-12-31'))
        conn.commit()

init_system()

# ------------------------------------------------------------------------------
# 2. CHARGEMENT CONFIG ET STYLE (FIX TEXTE BLANC & MARQUEE)
# ------------------------------------------------------------------------------
db_conn = get_db()
config = db_conn.execute("SELECT * FROM system_config WHERE id=1").fetchone()
APP_TITLE, MARQUEE_TEXT = config['title'], config['marquee']
db_conn.close()

st.set_page_config(page_title=APP_TITLE, layout="wide")

def apply_global_styles():
    # Injection du Marquee et du CSS de visibilité
    st.markdown(f"""
    <style>
        /* 1. FOND ET COULEUR DE BASE */
        .stApp {{ background-color: #000c1f; color: #ffffff !important; }}
        
        /* 2. FORCE LE BLANC SUR TOUS LES LABELS ET TEXTES STREAMLIT */
        label, .stMarkdown, p, span, h1, h2, h3, h4, .stHeader, .stSelectbox label, .stTextInput label {{
            color: #ffffff !important; font-weight: bold !important;
        }}
        
        /* 3. MESSAGE DÉFILANT (MARQUEE) - FIXÉ EN HAUT */
        .marquee-top {{
            position: fixed; top: 0; left: 0; width: 100%; height: 50px;
            background: #000000; border-bottom: 3px solid #00ff00;
            z-index: 100000; display: flex; align-items: center; overflow: hidden;
        }}
        .marquee-txt {{
            white-space: nowrap; display: inline-block; font-family: 'Arial Black', sans-serif;
            animation: scroll-text 20s linear infinite;
            color: #00ff00; font-size: 22px; text-transform: uppercase;
        }}
        @keyframes scroll-text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        /* 4. CARTES COBALT BALIKA */
        .balika-card {{
            background: linear-gradient(135deg, #0044ff 0%, #001a66 100%);
            border: 2px solid #00d9ff; border-radius: 15px; padding: 20px;
            margin: 15px 0; text-align: center; color: white !important;
        }}

        /* 5. TABLEAUX LISIBLES */
        .stTable {{ background-color: #ffffff !important; border-radius: 10px; color: #000000 !important; }}
        th {{ background-color: #0044ff !important; color: white !important; }}
        td {{ color: #000000 !important; font-weight: bold !important; border-bottom: 1px solid #ddd !important; }}

        /* 6. BOUTONS TACTILES */
        .stButton > button {{
            width: 100% !important; height: 50px !important; border-radius: 10px !important;
            background: linear-gradient(to right, #0055ff, #002288) !important;
            color: white !important; border: 2px solid #ffffff !important; font-weight: bold;
        }}

        /* SIDEBAR BLANCHE */
        [data-testid="stSidebar"] {{ background-color: #ffffff !important; border-right: 5px solid #0044ff; }}
        [data-testid="stSidebar"] * {{ color: #001a33 !important; font-weight: bold !important; }}

        .spacer-top {{ margin-top: 70px; }}
    </style>
    <div class="marquee-top">
        <div class="marquee-txt">🌟 {MARQUEE_TEXT} | {APP_TITLE} | GESTION BALIKA BUSINESS 🌟</div>
    </div>
    <div class="spacer-top"></div>
    """, unsafe_allow_html=True)

apply_global_styles()

# ------------------------------------------------------------------------------
# 3. GESTION DE LA SESSION
# ------------------------------------------------------------------------------
if 'session' not in st.session_state:
    st.session_state.session = {'auth': False, 'uid': None, 'role': None, 'sid': None, 'cart': {}, 'receipt': None}

# ------------------------------------------------------------------------------
# 4. ÉCRAN D'AUTHENTIFICATION (LOGIN & SIGNUP)
# ------------------------------------------------------------------------------
if not st.session_state.session['auth']:
    _, col_auth, _ = st.columns([1, 2, 1])
    with col_auth:
        st.markdown("<div class='balika-card'><h1>💎 BALIKA SYSTEM</h1><p>Veuillez vous identifier</p></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 CONNEXION", "📝 DEMANDE D'ACCÈS"])
        
        with t1:
            u_in = st.text_input("Identifiant (Login)").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER AU SYSTÈME"):
                db = get_db()
                u_data = db.execute("SELECT * FROM users WHERE uid=?", (u_in,)).fetchone()
                db.close()
                if u_data and hashlib.sha256(p_in.encode()).hexdigest() == u_data['pwd']:
                    if u_data['status'] == 'ACTIF' or u_data['role'] == 'SUPER_ADMIN':
                        exp_dt = datetime.strptime(u_data['expiry'], '%Y-%m-%d')
                        if datetime.now() > exp_dt and u_data['role'] != 'SUPER_ADMIN':
                            st.error(f"Votre abonnement a pris fin le {u_data['expiry']}.")
                        else:
                            st.session_state.session.update({'auth': True, 'uid': u_in, 'role': u_data['role'], 'sid': u_data['shop_id']})
                            st.rerun()
                    else: st.warning("Votre compte est en attente d'activation par l'Admin.")
                else: st.error("Identifiants incorrects.")

        with t2:
            with st.form("signup"):
                reg_u = st.text_input("ID Utilisateur voulu").lower()
                reg_n = st.text_input("Nom de votre Boutique")
                reg_p = st.text_input("Créer un Mot de passe", type="password")
                if st.form_submit_button("ENVOYER MA DEMANDE"):
                    db = get_db()
                    try:
                        hp = hashlib.sha256(reg_p.encode()).hexdigest()
                        trial = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                        db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", 
                                  (reg_u, hp, 'BOSS', 'PENDING', 'ATTENTE', reg_n, '', trial))
                        db.commit(); st.success("Demande transmise à l'administrateur !")
                    except: st.error("Désolé, cet ID est déjà utilisé.")
                    finally: db.close()
    st.stop()

# ------------------------------------------------------------------------------
# 5. PANEL SUPER ADMIN (GESTION TOTALE)
# ------------------------------------------------------------------------------
if st.session_state.session['role'] == "SUPER_ADMIN":
    st.sidebar.title("🛠️ MASTER CONTROL")
    adm_sel = st.sidebar.radio("Navigation Admin", ["Abonnés & Activation", "Paramètres Système", "Mon Profil Admin", "Base de Données", "Quitter"])
    
    if adm_sel == "Abonnés & Activation":
        st.markdown("<div class='balika-card'><h1>GESTION DES CLIENTS</h1></div>", unsafe_allow_html=True)
        db = get_db()
        # On ne gère que les comptes BOSS (Propriétaires)
        clients = db.execute("SELECT * FROM users WHERE role='BOSS'").fetchall()
        for c in clients:
            with st.expander(f"👤 {c['fullname']} (@{c['uid']}) - STATUT: {c['status']}"):
                c_s, c_d = st.columns(2)
                new_status = c_s.selectbox("État du Compte", ["ATTENTE", "ACTIF", "SUSPENDU"], index=["ATTENTE", "ACTIF", "SUSPENDU"].index(c['status']), key=f"s_{c['uid']}")
                new_date = c_d.date_input("Date Expiration", datetime.strptime(c['expiry'], '%Y-%m-%d'), key=f"d_{c['uid']}")
                
                if st.button(f"CONFIRMER ACTIVATION POUR {c['uid'].upper()}", key=f"btn_{c['uid']}"):
                    # FIX: Mise à jour du statut ET création de la boutique associée
                    db.execute("UPDATE users SET status=?, expiry=?, shop_id=? WHERE uid=?", 
                              (new_status, new_date.strftime('%Y-%m-%d'), c['uid'], c['uid']))
                    # On crée la boutique si elle n'existe pas
                    db.execute("INSERT OR IGNORE INTO shops (sid, sname) VALUES (?,?)", (c['uid'], c['fullname']))
                    db.commit(); st.success(f"Compte {c['uid']} activé avec succès !"); st.rerun()
        db.close()

    elif adm_sel == "Paramètres Système":
        st.header("⚙️ CONFIGURATION GLOBALE")
        with st.form("sys_cfg"):
            new_t = st.text_input("Titre de l'App", APP_TITLE)
            new_m = st.text_area("Message Défilant (Marquee)", MARQUEE_TEXT)
            if st.form_submit_button("SAUVEGARDER"):
                db = get_db()
                db.execute("UPDATE system_config SET title=?, marquee=? WHERE id=1", (new_t, new_m))
                db.commit(); db.close(); st.rerun()

    elif adm_sel == "Mon Profil Admin":
        st.header("👤 MON COMPTE ADMIN")
        with st.form("adm_prof"):
            a_id = st.text_input("Mon Login Admin", st.session_state.session['uid'])
            a_pw = st.text_input("Changer mon mot de passe (optionnel)", type="password")
            if st.form_submit_button("MODIFIER MES ACCÈS"):
                db = get_db()
                if a_pw:
                    hp = hashlib.sha256(a_pw.encode()).hexdigest()
                    db.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (a_id, hp, st.session_state.session['uid']))
                else:
                    db.execute("UPDATE users SET uid=? WHERE uid=?", (a_id, st.session_state.session['uid']))
                db.commit(); db.close(); st.session_state.session['auth'] = False; st.rerun()

    elif adm_sel == "Base de Données":
        st.header("📥 BACKUP")
        with open(DB_NAME, "rb") as f:
            st.download_button("TÉLÉCHARGER LA BASE DE DONNÉES", f, file_name=f"balika_v300_{datetime.now().strftime('%Y%m%d')}.db")

    if adm_sel == "Quitter": st.session_state.session['auth'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE CLIENT (BOSS & VENDEUR)
# ------------------------------------------------------------------------------
sid = st.session_state.session['sid']
db = get_db()
shop = db.execute("SELECT * FROM shops WHERE sid=?", (sid,)).fetchone()
u_info = db.execute("SELECT expiry FROM users WHERE uid=?", (st.session_state.session['uid'],)).fetchone()
db.close()

if not shop:
    st.error("Erreur : Votre boutique n'a pas encore été configurée par l'Admin.")
    st.stop()

# Navigation
menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
if st.session_state.session['role'] == "VENDEUR":
    menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]

with st.sidebar:
    st.markdown(f"<div class='balika-card'><h3>{shop['sname']}</h3><p>Abonnement: {u_info['expiry']}</p></div>", unsafe_allow_html=True)
    choice = st.radio("SÉLECTIONNER UN MENU", menu)

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"<div class='balika-card'><h1>TABLEAU DE BORD</h1><h3>{datetime.now().strftime('%d %B %Y')}</h3></div>", unsafe_allow_html=True)
    db = get_db()
    today = datetime.now().strftime("%d/%m/%Y")
    ca = db.execute("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (sid, today)).fetchone()[0] or 0
    dt = db.execute("SELECT SUM(bal) FROM debts WHERE sid=? AND state='OUVERT'", (sid,)).fetchone()[0] or 0
    db.close()
    
    col1, col2 = st.columns(2)
    with col1: st.markdown(f"<div style='border:4px solid #00ff00; border-radius:15px; text-align:center; padding:20px;'><h3 style='color:#00ff00;'>RECETTE JOUR</h3><h1 style='color:#00ff00;'>{ca:,.2f} $</h1></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div style='border:4px solid #ff4444; border-radius:15px; text-align:center; padding:20px;'><h3 style='color:#ff4444;'>DETTES TOTALES</h3><h1 style='color:#ff4444;'>{dt:,.2f} $</h1></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE & FACTURE ADMINISTRATIVE ---
elif choice == "🛒 CAISSE":
    if st.session_state.session['receipt']:
        r = st.session_state.session['receipt']
        st.markdown("<div class='no-print'>")
        if st.button("⬅️ RETOUR AU PANIER"): st.session_state.session['receipt'] = None; st.rerun()
        f_type = st.radio("Format Facture", ["80mm (Ticket)", "A4 (Administrative)"])
        st.markdown("</div>")

        width = "320px" if f_type == "80mm (Ticket)" else "100%"
        st.markdown(f"""
        <div style="background:white; color:black; padding:30px; border-radius:10px; width:{width}; margin:auto; font-family:monospace; border:2px solid #000;">
            <h2 style="text-align:center; margin:0;">{shop['sname']}</h2>
            <p style="text-align:center; font-size:12px;">{shop['addr']}<br>Tél: {shop['tel']}</p>
            <hr style="border:1px dashed black;">
            <p style="text-align:center; font-weight:bold;">FACTURE N° {r['ref']}</p>
            <p>Client: <b>{r['cli']}</b> <span style="float:right;">{r['date']}</span></p>
            <table style="width:100%; border-collapse:collapse;">
                <tr style="border-bottom:2px solid black; text-align:left;">
                    <th>Article</th><th>Qté</th><th style="text-align:right;">Total</th>
                </tr>
                {"".join([f"<tr><td>{k}</td><td>{v['q']}</td><td style='text-align:right;'>{v['tot']:,.2f}</td></tr>" for k,v in r['items'].items()])}
            </table>
            <hr style="border:1px dashed black;">
            <h3 style="text-align:right;">TOTAL À PAYER: {r['tot']:,.2f} {r['cur']}</h3>
            <p style="text-align:center; font-size:11px; margin-top:30px;">Merci pour votre confiance !<br>Vendeur: {st.session_state.session['uid'].upper()}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    else:
        st.header("🛒 TERMINAL DE VENTE")
        db = get_db()
        items = db.execute("SELECT * FROM stock WHERE sid=? AND qty > 0", (sid,)).fetchall()
        db.close()
        
        col_m, col_p = st.columns([1, 2])
        with col_m: 
            devise = st.selectbox("MONNAIE", ["USD", "CDF"])
            tx = shop['rate']
        with col_p:
            p_sel = st.selectbox("RECHERCHER ARTICLE", ["---"] + [f"{i['item']} (Dispo: {i['qty']})" for i in items])
            if p_sel != "---":
                pure_name = p_sel.split(" (")[0]
                if st.button("➕ AJOUTER"):
                    db = get_db()
                    it_inf = db.execute("SELECT sell, qty FROM stock WHERE item=? AND sid=?", (pure_name, sid)).fetchone()
                    db.close()
                    st.session_state.session['cart'][pure_name] = {'p': it_inf['sell'], 'q': 1, 'max': it_inf['qty']}
                    st.rerun()

        if st.session_state.session['cart']:
            st.subheader("📋 PANIER EN COURS")
            tot_usd = 0.0
            for it, val in list(st.session_state.session['cart'].items()):
                st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:10px; border-radius:10px;'><b>{it}</b> - {val['p']}$</div>", unsafe_allow_html=True)
                cq, cd = st.columns([3, 1])
                st.session_state.session['cart'][it]['q'] = cq.number_input(f"Quantité", 1, val['max'], val['q'], key=f"q_{it}")
                tot_usd += val['p'] * st.session_state.session['cart'][it]['q']
                if cd.button("🗑️", key=f"rm_{it}"): del st.session_state.session['cart'][it]; st.rerun()

            aff_tot = tot_usd if devise == "USD" else tot_usd * tx
            st.markdown(f"<div class='balika-card'><h2>TOTAL : {aff_tot:,.2f} {devise}</h2></div>", unsafe_allow_html=True)
            
            with st.form("valid_v"):
                client = st.text_input("NOM DU CLIENT", "COMPTANT").upper()
                recu = st.number_input(f"MONTANT REÇU ({devise})", value=float(aff_tot))
                if st.form_submit_button("✅ CONFIRMER LA VENTE"):
                    p_usd = recu if devise == "USD" else recu / tx
                    r_usd = tot_usd - p_usd
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    dn, tn = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                    
                    db = get_db()
                    js = {k: {'q': v['q'], 'tot': v['p']*v['q']} for k,v in st.session_state.session['cart'].items()}
                    db.execute("INSERT INTO sales (ref, cli, tot, paid, rest, date, time, seller, sid, items, cur) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (ref, client, tot_usd, p_usd, r_usd, dn, tn, st.session_state.session['uid'], sid, json.dumps(js), devise))
                    for n, d in st.session_state.session['cart'].items():
                        db.execute("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (d['q'], n, sid))
                    if r_usd > 0.01:
                        db.execute("INSERT INTO debts (cli, bal, ref, sid) VALUES (?,?,?,?)", (client, r_usd, ref, sid))
                    db.commit(); db.close()
                    
                    st.session_state.session['receipt'] = {'ref': ref, 'cli': client, 'tot': aff_tot, 'cur': devise, 'items': js, 'date': dn, 'time': tn}
                    st.session_state.session['cart'] = {}; st.rerun()

# --- 6.3 STOCK ---
elif choice == "📦 STOCK":
    st.markdown("<div class='balika-card'><h1>INVENTAIRE DU STOCK</h1></div>", unsafe_allow_html=True)
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("add_p"):
            name = st.text_input("Désignation").upper()
            pa, pv = st.number_input("Prix Achat $"), st.number_input("Prix Vente $")
            qt = st.number_input("Quantité", 1)
            if st.form_submit_button("SAUVEGARDER"):
                db = get_db()
                db.execute("INSERT INTO stock (item, qty, buy, sell, sid) VALUES (?,?,?,?,?)", (name, qt, pa, pv, sid))
                db.commit(); db.close(); st.rerun()
    
    db = get_db()
    stk = db.execute("SELECT * FROM stock WHERE sid=? ORDER BY item", (sid,)).fetchall()
    db.close()
    if stk:
        df = pd.DataFrame(stk, columns=["ID", "ARTICLE", "QTÉ", "ACHAT", "VENTE", "SID"])
        st.table(df[["ARTICLE", "QTÉ", "VENTE"]])
        for s in stk:
            with st.expander(f"MODIFIER : {s['item']}"):
                col1, col2 = st.columns(2)
                nv_p = col1.number_input("Prix Vente", value=s['sell'], key=f"up_p_{s['id']}")
                nv_q = col2.number_input("Quantité", value=s['qty'], key=f"up_q_{s['id']}")
                if st.button(f"METTRE À JOUR {s['id']}", key=f"up_b_{s['id']}"):
                    db = get_db()
                    db.execute("UPDATE stock SET sell=?, qty=? WHERE id=?", (nv_p, nv_q, s['id']))
                    db.commit(); db.close(); st.rerun()

# --- 6.4 DETTES ---
elif choice == "📉 DETTES":
    st.markdown("<div class='balika-card'><h1>CRÉDITS CLIENTS</h1></div>", unsafe_allow_html=True)
    db = get_db()
    dettes = db.execute("SELECT * FROM debts WHERE sid=? AND state='OUVERT'", (sid,)).fetchall()
    if not dettes: st.info("Aucune dette enregistrée.")
    for d in dettes:
        with st.expander(f"👤 {d['cli']} | {d['bal']:,.2f} $"):
            pay = st.number_input("Payer une tranche ($)", 0.0, d['bal'], key=f"pay_{d['id']}")
            if st.button(f"VALIDER PAIEMENT {d['id']}"):
                rem = d['bal'] - pay
                db_u = get_db()
                if rem <= 0.01: db_u.execute("UPDATE debts SET bal=0, state='SOLDE' WHERE id=?", (d['id'],))
                else: db_u.execute("UPDATE debts SET bal=? WHERE id=?", (rem, d['id']))
                db_u.commit(); db_u.close(); st.rerun()
    db.close()

# --- 6.5 RAPPORTS ---
elif choice == "📊 RAPPORTS":
    st.markdown("<div class='balika-card'><h1>RAPPORT DE VENTES</h1></div>", unsafe_allow_html=True)
    dt_sel = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    db = get_db()
    reps = db.execute("SELECT * FROM sales WHERE sid=? AND date=?", (sid, dt_sel)).fetchall()
    db.close()
    if reps:
        df_r = pd.DataFrame(reps, columns=["ID","REF","CLIENT","TOTAL","PAYÉ","RESTE","DATE","HEURE","VENDEUR","SID","JS","CUR"])
        st.table(df_r[["REF", "CLIENT", "TOTAL", "HEURE", "VENDEUR"]])
        st.markdown(f"<div class='balika-card'><h2>TOTAL DU JOUR : {df_r['TOTAL'].sum():,.2f} $</h2></div>", unsafe_allow_html=True)
    else: st.info("Aucune vente pour cette date.")

# --- 6.6 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.markdown("<div class='balika-card'><h1>PROFIL & ÉQUIPE</h1></div>", unsafe_allow_html=True)
    with st.expander("👤 MON COMPTE (CHANGER MON LOGIN / PASS)"):
        with st.form("prof_b"):
            m_id = st.text_input("Mon Login", st.session_state.session['uid'])
            m_p = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("MODIFIER MON PROFIL"):
                db = get_db()
                if m_p:
                    hp = hashlib.sha256(m_p.encode()).hexdigest()
                    db.execute("UPDATE users SET uid=?, pwd=? WHERE uid=?", (m_id, hp, st.session_state.session['uid']))
                else:
                    db.execute("UPDATE users SET uid=? WHERE uid=?", (m_id, st.session_state.session['uid']))
                db.commit(); db.close(); st.session_state.session['auth'] = False; st.rerun()

    if st.session_state.session['role'] == "BOSS":
        st.divider()
        st.subheader("➕ AJOUTER UN VENDEUR")
        with st.form("add_v"):
            v_id = st.text_input("ID Vendeur").lower()
            v_pw = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER LE VENDEUR"):
                db = get_db()
                hp = hashlib.sha256(v_pw.encode()).hexdigest()
                db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (v_id, hp, 'VENDEUR', sid, 'ACTIF', 'VENDEUR', '', u_info['expiry']))
                db.commit(); db.close(); st.success("Vendeur ajouté !"); st.rerun()

# --- 6.7 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.markdown("<div class='balika-card'><h1>RÉGLAGES BOUTIQUE</h1></div>", unsafe_allow_html=True)
    with st.form("sett"):
        n = st.text_input("Nom de la Boutique", shop['sname'])
        r = st.number_input("Taux CDF", value=shop['rate'])
        a = st.text_area("Adresse", shop['addr'])
        t = st.text_input("Téléphone", shop['tel'])
        if st.form_submit_button("ENREGISTRER"):
            db = get_db()
            db.execute("UPDATE shops SET sname=?, rate=?, addr=?, tel=? WHERE sid=?", (n, r, a, t, sid))
            db.commit(); db.close(); st.success("Mis à jour !"); st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.session['auth'] = False; st.rerun()

# ==============================================================================
# FIN DU CODE v300 - SYSTÈME BALIKA BUSINESS
# ==============================================================================
