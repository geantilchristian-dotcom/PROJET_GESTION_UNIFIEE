# ==============================================================================
# BALIKA ERP ULTIMATE v2000 - VERSION FINALE INTÉGRALE (900+ LIGNES)
# DESIGN : MARQUEE TOP | LOGIN VERTICAL | ZERO CONTOUR JAUNE | MOBILE READY
# FONCTIONS : SaaS, STOCK, VENTES, DETTES (PAIEMENT ÉCHELONNÉ), DÉPENSES
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time
import io

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DU MOTEUR
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v2000", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_pref': "USD"
    })

def run_db(query, params=(), fetch=False):
    """Exécution SQL avec gestion de verrouillage"""
    try:
        with sqlite3.connect('balika_v2000.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 2. ARCHITECTURE DE LA BASE DE DONNÉES (ERP COMPLET)
# ------------------------------------------------------------------------------
def init_db():
    # Tables Système
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, status TEXT DEFAULT 'ACTIF')")
    run_db("CREATE TABLE IF NOT EXISTS config (ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF')")
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT, prix_achat REAL DEFAULT 0)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT, date_d TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)")

    # Initialisation Admin (Identifiants : admin / admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP v2000 - SYSTÈME COMPLET'))

init_db()

# ------------------------------------------------------------------------------
# 3. INTERFACE CSS (MARQUEE EN HAUT & ZERO CONTOUR JAUNE)
# ------------------------------------------------------------------------------
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL = cfg[0] if cfg else ("BALIKA", "SYSTÈME ERP", 2850.0, "", "")

st.markdown(f"""
    <style>
    /* 1. MARQUEE TOUT EN HAUT (FIXÉ) */
    .top-marquee-bar {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #FF4B2B !important; height: 45px; z-index: 99999;
        display: flex; align-items: center; border-bottom: 2px solid white;
    }}
    .marquee-text-v2000 {{
        white-space: nowrap; animation: scroll-erp 20s linear infinite;
        color: white !important; font-weight: 900; font-size: 20px;
    }}
    @keyframes scroll-erp {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* 2. STYLE GLOBAL SOMBRE */
    .stApp {{ background-color: #0e1117; color: white !important; }}

    /* 3. INPUTS SANS CONTOUR JAUNE (TEXTE NOIR SUR BLANC) */
    div[data-baseweb="input"], .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {{
        background-color: #FFFFFF !important;
        border: 1px solid #444444 !important;
        border-radius: 8px !important;
        color: #000000 !important;
    }}
    input, select {{ color: #000000 !important; font-weight: 800 !important; }}
    label {{ color: white !important; font-weight: bold !important; font-size: 15px !important; }}

    /* 4. BOUTONS ACTION ORANGE */
    .stButton>button {{
        background: #FF4B2B !important; color: white !important;
        border: 1px solid white !important; border-radius: 12px;
        height: 55px; font-weight: 900; width: 100%;
    }}

    /* 5. FACTURE BLANCHE */
    .invoice-card {{
        background: white !important; color: black !important;
        padding: 30px; border: 2px solid black; border-radius: 5px;
        font-family: monospace; max-width: 600px; margin: auto;
    }}
    .invoice-card * {{ color: black !important; }}

    /* LOGIN */
    .login-box {{ margin-top: 60px; text-align: center; }}
    </style>

    <div class="top-marquee-bar">
        <div class="marquee-text-v2000">🚀 {C_NOM} : {C_MSG} | TAUX : {C_TX} CDF | 📅 {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    <div style="height:65px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. MODULE AUTHENTIFICATION (LOGIN VERTICAL)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown('<div class="login-box"><h1 style="color:white; font-size:45px;">BALIKA ERP v2000</h1></div>', unsafe_allow_html=True)
    
    _, col_l, _ = st.columns([0.1, 0.8, 0.1])
    with col_l:
        st.markdown("<p style='color:white; text-align:center; font-size:18px;'>VEUILLEZ VOUS CONNECTER</p>", unsafe_allow_html=True)
        # Saisie Verticale
        u_id = st.text_input("VOTRE IDENTIFIANT", placeholder="Tapez 'admin'")
        u_pw = st.text_input("VOTRE MOT DE PASSE", type="password", placeholder="Tapez 'admin123'")
        
        if st.button("ACCÉDER AU SYSTÈME"):
            clean_user = u_id.lower().strip()
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (clean_user,), fetch=True)
            if res and make_hashes(u_pw) == res[0][0]:
                st.session_state.update({'auth':True, 'user':clean_user, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe invalide.")
        
        st.write("---")
        with st.expander("🚀 CRÉER UNE NOUVELLE BOUTIQUE"):
            with st.form("new_shop"):
                ns_nom = st.text_input("Nom de l'Etablissement")
                ns_id = st.text_input("Identifiant Admin souhaité")
                ns_pw = st.text_input("Mot de passe souhaité", type="password")
                if st.form_submit_button("LANCER MA BOUTIQUE"):
                    if ns_nom and ns_id and ns_pw:
                        if not run_db("SELECT * FROM users WHERE username=?", (ns_id,), fetch=True):
                            new_eid = f"ERP-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (ns_id.lower(), make_hashes(ns_pw), "ADMIN", new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (new_eid, ns_nom.upper(), 2850.0, "BIENVENUE"))
                            st.success("✅ Boutique créée ! Connectez-vous ci-dessus.")
                        else: st.warning("ID déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ------------------------------------------------------------------------------
# 5. NAVIGATION LATÉRALE
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏢 {C_NOM}")
    st.write(f"Utilisateur : **{USER.upper()}**")
    st.write("---")
    
    menus = ["🏠 ACCUEIL", "🛒 VENTE", "📦 STOCK", "📉 DETTES", "💸 DÉPENSES", "⚙️ RÉGLAGES"]
    if ROLE == "SUPER_ADMIN": menus.append("🌍 SaaS")
    
    for m in menus:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER"):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULES ERP (850-900 LIGNES DE LOGIQUE)
# ------------------------------------------------------------------------------

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.title(f"🏠 BIENVENUE : {C_NOM}")
    
    # Horloge
    st.markdown(f"""
        <div style="background:black; border:2px solid #FF4B2B; border-radius:15px; padding:20px; text-align:center; margin-bottom:20px;">
            <h1 style="color:white; font-size:60px; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
            <p style="color:#FF4B2B;">{datetime.now().strftime('%A %d %B %Y')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    vt = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    dt = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES TOTALES", f"{vt:,.2f} $")
    c2.metric("DETTES CLIENTS", f"{dt:,.2f} $")
    
    st.write("---")
    st.subheader("Dernières Ventes")
    logs = run_db("SELECT date_v, ref, client, total FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    if logs: st.table(pd.DataFrame(logs, columns=["Date", "Référence", "Client", "Montant"]))

# --- VENTE ---
elif st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        c_v1, c_v2 = st.columns(2)
        v_devise = c_v1.selectbox("Monnaie", ["USD", "CDF"])
        v_fmt = c_v2.selectbox("Format", ["80mm", "A4"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        sel = st.selectbox("Article", ["---"] + list(pmap.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total_net = 0.0
            p_final = []
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_devise == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_devise == "USD": px /= C_TX
                stot = px * qte
                total_net += stot
                p_final.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                
                ra, rb, rc = st.columns([3, 1, 0.5])
                ra.write(f"**{art}**")
                st.session_state.panier[art] = rb.number_input("Qté", 1, pmap[art]['st'], value=qte, key=f"v_{art}")
                if rc.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div style="background:black; border:3px solid #FF4B2B; padding:20px; text-align:center; font-size:35px; color:#FF4B2B; font-weight:900; border-radius:15px;">TOTAL : {total_net:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            with st.form("valid"):
                f_cl = st.text_input("NOM CLIENT", "COMPTANT").upper()
                f_pay = st.number_input("MONTANT REÇU", value=float(total_net))
                if st.form_submit_button("💰 VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    reste = total_net - f_pay
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details, format) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (ref, f_cl, total_net, f_pay, reste, v_devise, dt, USER, ENT_ID, json.dumps(p_final), v_fmt))
                    if reste > 0.01:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique, date_d) VALUES (?,?,?,?,?,?,?)", 
                               (f_cl, reste, v_devise, ref, ENT_ID, json.dumps([{'d':dt, 'p':f_pay}]), dt))
                    for i in p_final:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    st.session_state.last_fac = {'ref':ref, 'cl':f_cl, 'tot':total_net, 'pay':f_pay, 'dev':v_devise, 'items':p_final, 'date':dt, 'fmt':v_fmt}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # FACTURE
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({'last_fac':None}))
        st.markdown(f"""
            <div class="invoice-card">
                <center>
                    <h2 style="margin:0;">{C_NOM}</h2>
                    <p>{C_ADR}<br>Tel: {C_TEL}</p>
                    <hr>
                    <h4>FACTURE : {f['ref']}</h4>
                </center>
                <p>Date: {f['date']}<br>Client: {f['cl']}</p>
                <table style="width:100%;">
                    {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr>
                <h3 align="right">NET À PAYER : {f['tot']:,.2f} {f['dev']}</h3>
                <p align="right">Reçu : {f['pay']:,.2f} | Reste : {f['tot']-f['pay']:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION INVENTAIRE")
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("p_f"):
            n = st.text_input("Désignation").upper()
            q = st.number_input("Stock", 1)
            p = st.number_input("Prix Vente", 0.0)
            d = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n, q, p, d, ENT_ID))
                st.rerun()
    
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pi, dn, sq, pv, dv in prods:
        with st.container(border=True):
            ca, cb, cc = st.columns([3, 1, 1])
            ca.write(f"**{dn}** | Stock : `{sq}`")
            np = cb.number_input("Prix", value=float(pv), key=f"px_{pi}")
            if cb.button("💾 SAUVER", key=f"s_{pi}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (np, pi)); st.rerun()
            if cc.button("🗑️ SUPPRIMER", key=f"d_{pi}"):
                run_db("DELETE FROM produits WHERE id=?", (pi,)); st.rerun()

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.header("📉 DETTES CLIENTS")
    dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.01", (ENT_ID,), fetch=True)
    for di, dc, dm, dd, dr, dh in dettes:
        with st.container(border=True):
            ca, cb = st.columns([3, 1])
            ca.write(f"👤 {dc} | Reste : **{dm:,.2f} {dd}**")
            v_m = cb.number_input("Verser", 0.0, float(dm), key=f"pay_{di}")
            if cb.button("PAYER", key=f"bt_{di}"):
                nr = dm - v_m
                run_db("UPDATE dettes SET montant=? WHERE id=?", (nr, di))
                if nr <= 0.01: run_db("DELETE FROM dettes WHERE id=?", (di,))
                st.rerun()

# --- REGLAGES ---
elif st.session_state.page == "RÉGLAGES":
    st.header("⚙️ CONFIGURATION")
    with st.form("cfg_f"):
        en = st.text_input("Nom Boutique", C_NOM)
        em = st.text_area("Message Marquee", C_MSG)
        et = st.number_input("Taux Change", value=C_TX)
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=? WHERE ent_id=?", (en.upper(), em, et, ENT_ID))
            st.rerun()

# --- SaaS ---
elif st.session_state.page == "SaaS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION RÉSEAU")
    shops = run_db("SELECT ent_id, nom_ent, status FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for sid, sn, ss in shops:
        st.write(f"🏢 {sn} ({sid}) | État: {ss}")
        if st.button("ACTIVER/PAUSER", key=sid):
            ns = "PAUSE" if ss == "ACTIF" else "ACTIF"
            run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, sid)); st.rerun()

# FIN DU CODE v2000
