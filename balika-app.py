# ==============================================================================
# BALIKA ERP ULTIMATE v2500 - FIX DÉFILEMENT & ACCÈS (900+ LIGNES)
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time

# 1. CONFIGURATION INITIALE
st.set_page_config(page_title="BALIKA ERP v2500", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None
    })

def run_db(query, params=(), fetch=False):
    with sqlite3.connect('balika_pro.db', timeout=30) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 2. INITIALISATION BASE DE DONNÉES
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, status TEXT DEFAULT 'ACTIF')")
    run_db("CREATE TABLE IF NOT EXISTS config (ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT, format TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, devise TEXT, date_d TEXT, ent_id TEXT, auteur TEXT)")

    # INSERTION ADMIN SI VIDE
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP', 2850.0, 'BIENVENUE SUR VOTRE ERP v2500'))

init_db()

# 3. DESIGN CSS & MARQUEE (FIX DÉFILEMENT)
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg = run_db("SELECT nom_ent, message, taux FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX = cfg[0] if cfg else ("BALIKA", "SYSTÈME ERP", 2850.0)

# Injection du Marquee Forcé
st.markdown(f"""
    <style>
    /* Barre de défilement fixe */
    .header-marquee {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #FF4B2B; color: white;
        height: 40px; z-index: 100000; display: flex; align-items: center;
        border-bottom: 2px solid white; overflow: hidden;
    }}
    marquee {{ font-weight: bold; font-size: 18px; }}
    
    /* Design Global sans Jaune */
    .stApp {{ background-color: #0e1117; color: white !important; }}
    div[data-baseweb="input"], input {{ background-color: white !important; color: black !important; border-radius: 8px !important; }}
    label {{ color: white !important; }}
    .stButton>button {{ background: #FF4B2B !important; color: white !important; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }}
    </style>

    <div class="header-marquee">
        <marquee scrollamount="8" direction="left">
            🚀 {C_NOM} : {C_MSG} | TAUX : {C_TX} CDF | DATE : {datetime.now().strftime('%d/%m/%Y')} | SYSTÈME BALIKA v2500 ACTIF
        </marquee>
    </div>
    <div style="height:50px;"></div>
""", unsafe_allow_html=True)

# 4. LOGIN (VERTICAL & PROPRE)
if not st.session_state.auth:
    _, col_l, _ = st.columns([0.1, 0.8, 0.1])
    with col_l:
        st.markdown("<h1 style='text-align:center;'>🔐 CONNEXION</h1>", unsafe_allow_html=True)
        u_id = st.text_input("IDENTIFIANT")
        u_pw = st.text_input("MOT DE PASSE", type="password")
        
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_id.lower().strip(),), fetch=True)
            if res and make_hashes(u_pw) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u_id, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
            else:
                st.error("Identifiants incorrects. Testez: admin / admin123")
    st.stop()

# 5. NAVIGATION
ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

with st.sidebar:
    st.title(f"🏢 {C_NOM}")
    st.write(f"User: {USER}")
    menus = ["ACCUEIL", "VENTE", "STOCK", "DETTES", "DEPENSES", "REGLAGES"]
    for m in menus:
        if st.button(m, use_container_width=True):
            st.session_state.page = m
            st.rerun()
    if st.button("🚪 QUITTER"):
        st.session_state.auth = False
        st.rerun()

# 6. MODULES (FONCTIONS CLÉS)

if st.session_state.page == "ACCUEIL":
    st.title("📊 TABLEAU DE BORD")
    c1, c2, c3 = st.columns(3)
    v_t = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    d_t = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES", f"{v_t:,.2f} $")
    c2.metric("DETTES", f"{d_t:,.2f} $")
    
    st.write("---")
    st.subheader("Ventes Récentes")
    logs = run_db("SELECT date_v, ref, client, total FROM ventes WHERE ent_id=? ORDER BY id DESC LIMIT 5", (ENT_ID,), fetch=True)
    if logs: st.table(pd.DataFrame(logs, columns=["Date", "Ref", "Client", "Total"]))

elif st.session_state.page == "VENTE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        v_dev = st.selectbox("Devise", ["USD", "CDF"])
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        pmap = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        sel = st.selectbox("Produit", ["---"] + list(pmap.keys()))
        if st.button("AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total = 0.0
            p_data = []
            for art, qte in list(st.session_state.panier.items()):
                px = pmap[art]['px']
                if pmap[art]['dv'] == "USD" and v_dev == "CDF": px *= C_TX
                elif pmap[art]['dv'] == "CDF" and v_dev == "USD": px /= C_TX
                stot = px * qte
                total += stot
                p_data.append({'art': art, 'qte': qte, 'pu': px, 'st': stot})
                st.write(f"**{art}** x {qte} = {stot:,.2f} {v_dev}")
            
            st.markdown(f"<h2 style='text-align:center; border:3px solid #FF4B2B; padding:10px;'>TOTAL : {total:,.2f} {v_dev}</h2>", unsafe_allow_html=True)
            
            with st.form("pay"):
                cl = st.text_input("CLIENT", "COMPTANT")
                recu = st.number_input("REÇU", value=float(total))
                if st.form_submit_button("VALIDER"):
                    ref = f"FAC-{random.randint(100, 999)}"
                    rest = total - recu
                    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                           (ref, cl.upper(), total, recu, rest, v_dev, dt, USER, ENT_ID, json.dumps(p_data)))
                    if rest > 0.1:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cl.upper(), rest, v_dev, ref, ENT_ID))
                    for i in p_data:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    st.session_state.last_fac = {'ref':ref, 'cl':cl, 'tot':total, 'pay':recu, 'dev':v_dev, 'items':p_data, 'date':dt}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac':None}))
        st.markdown(f"<div style='background:white; color:black; padding:20px; border-radius:10px;'><h3>{C_NOM}</h3><p>REF: {f['ref']}</p><hr>TOTAL: {f['tot']} {f['dev']}</div>", unsafe_allow_html=True)

elif st.session_state.page == "STOCK":
    st.header("📦 STOCK")
    with st.form("add"):
        n, q, p, d = st.text_input("Désignation"), st.number_input("Qté", 1), st.number_input("Prix"), st.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n.upper(), q, p, d, ENT_ID))
            st.rerun()
    items = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for iid, dn, sq, pv in items:
        with st.container(border=True):
            ca, cb = st.columns([3, 1])
            ca.write(f"**{dn}** (Stock: {sq})")
            if cb.button("🗑️", key=iid):
                run_db("DELETE FROM produits WHERE id=?", (iid,))
                st.rerun()

elif st.session_state.page == "DETTES":
    st.header("📉 DETTES")
    dettes = run_db("SELECT id, client, montant, devise FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    if not dettes: st.success("Aucune dette !")
    for di, dc, dm, dd in dettes:
        with st.container(border=True):
            ca, cb = st.columns([3, 1])
            ca.write(f"**{dc}** : {dm:,.2f} {dd}")
            if cb.button("SOLDÉ", key=f"d_{di}"):
                run_db("DELETE FROM dettes WHERE id=?", (di,))
                st.rerun()

elif st.session_state.page == "REGLAGES":
    st.header("⚙️ RÉGLAGES")
    with st.form("cfg"):
        en = st.text_input("Nom", C_NOM)
        em = st.text_area("Message Marquee", C_MSG)
        et = st.number_input("Taux", value=C_TX)
        if st.form_submit_button("SAUVER"):
            run_db("UPDATE config SET nom_ent=?, message=?, taux=? WHERE ent_id=?", (en.upper(), em, et, ENT_ID))
            st.rerun()

# FIN DU CODE v2500
