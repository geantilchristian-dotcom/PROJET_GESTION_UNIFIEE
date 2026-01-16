import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import base64
from PIL import Image

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & STYLE (v825 - FULL PRO)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation des états
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v825.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES (AUCUNE SUPPRESSION, QUE DES AJOUTS)
# ==============================================================================
def init_db():
    # Table Utilisateurs & Vendeurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        ent_id TEXT, status TEXT DEFAULT 'ACTIF', photo BLOB)""")
    
    # Config Globale
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
        taux_global REAL, version TEXT)""")
    
    # Infos Boutique (En-tête)
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT)""")
    
    # Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
        ent_id TEXT)""")
    
    # Ventes & Dettes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        devise TEXT, ref_v TEXT, ent_id TEXT)""")

    # Données initiales
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        
    if not run_db("SELECT * FROM system_config", fetch=True):
        # CORRECTION SYNTAXE ICI : Tout sur une seule ligne
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global, version) VALUES (1, 'BALIKA APP', 'Bienvenue sur votre espace de gestion intelligente', 2850.0, 'v825')")

init_db()

# ==============================================================================
# 3. DESIGN & MARQUEE (FIXED)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 50px;
        z-index: 9999; border-bottom: 2px solid white;
        display: flex; align-items: center; overflow: hidden;
    }}
    marquee {{ font-size: 22px; font-weight: bold; }}
    .main-content {{ margin-top: 60px; }}
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 50px; width: 100%;
        border: 2px solid white;
    }}
    .invoice-card {{
        background: white; color: black; padding: 20px; 
        border: 2px solid black; border-radius: 10px; font-family: 'Courier New';
    }}
    div[data-baseweb="input"] {{ background-color: white !important; }}
    input {{ color: black !important; font-weight: bold !important; }}
    </style>
    <div class="marquee-wrapper"><marquee scrollamount="7">{MARQUEE}</marquee></div>
    <div class="main-content"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. AUTHENTIFICATION
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["CONNEXION", "CRÉER BOUTIQUE"])
    
    with t1:
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res:
                if res[0][3] == "PAUSE" and res[0][1] != "SUPER_ADMIN": st.error("Compte suspendu.")
                elif make_hashes(p) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Mot de passe incorrect.")
            else: st.error("Compte inexistant.")
    with t2:
        nu = st.text_input("Nom d'utilisateur").lower().strip()
        np = st.text_input("Mot de passe ", type="password")
        if st.button("CRÉER MON COMPTE"):
            if run_db("SELECT * FROM users WHERE username=?", (nu,), fetch=True): st.warning("Déjà pris.")
            else:
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (nu, make_hashes(np), 'USER', nu))
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique) VALUES (?,?)", (nu, nu.upper()))
                st.success("Compte créé ! Connectez-vous.")
    st.stop()

# ==============================================================================
# 5. NAVIGATION
# ==============================================================================
with st.sidebar:
    # Photo de profil
    photo_data = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if photo_data and photo_data[0][0]:
        st.image(photo_data[0][0], width=100)
    else:
        st.markdown("👤")
    
    st.markdown(f"**{st.session_state.user.upper()}**")
    st.write("---")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    if st.button("🚪 QUITTER"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. LOGIQUE SUPER ADMIN
# ==============================================================================
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("👥 GESTION DES BOUTIQUES")
        for u, s in run_db("SELECT username, status FROM users WHERE role='USER'", fetch=True):
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"Boutique : **{u.upper()}**")
                if c2.button("ACTIVER/PAUSE", key=u):
                    ns = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (ns, u)); st.rerun()
                if c3.button("SUPPRIMER", key=f"del_{u}"):
                    run_db("DELETE FROM users WHERE username=?", (u)); st.rerun()

    elif st.session_state.page == "SYSTÈME":
        st.header("🛠️ RÉGLAGES GLOBAUX")
        new_app = st.text_input("Nom de l'App", APP_NAME)
        new_marq = st.text_area("Texte défilant", MARQUEE)
        new_tx = st.number_input("Taux de change (1$ = ? CDF)", value=TX_G)
        if st.button("SAUVEGARDER"):
            run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (new_app, new_marq, new_tx))
            st.rerun()

# ==============================================================================
# 7. LOGIQUE UTILISATEUR / VENDEUR
# ==============================================================================
else:
    # --- STOCK ---
    if st.session_state.page == "STOCK":
        st.header("📦 MON STOCK")
        with st.form("add_p"):
            c1, c2, c3 = st.columns(3)
            d = c1.text_input("Article")
            q = c2.number_input("Quantité", 1)
            p = c3.number_input("Prix Vente $")
            if st.form_submit_button("AJOUTER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                       (d.upper(), q, p, "USD", st.session_state.ent_id)); st.rerun()
        
        for pi, pd, ps, pp in run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True):
            with st.container(border=True):
                l1, l2, l3, l4 = st.columns([3,1,1,1])
                u_d = l1.text_input("Désignation", pd, key=f"d_{pi}")
                u_s = l2.number_input("Qté", value=ps, key=f"q_{pi}")
                u_p = l3.number_input("Prix $", value=pp, key=f"p_{pi}")
                if l4.button("MAJ", key=f"b_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_d.upper(), u_s, u_p, pi))
                    st.rerun()

    # --- CAISSE ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 CAISSE")
            dev = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
            prods = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {x[0]: (x[1], x[2]) for x in prods}
            sel = st.selectbox("Choisir l'article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
            
            if st.session_state.panier:
                tot = 0.0
                det_list = []
                for a, qte in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if dev == "USD" else p_map[a][0] * TX_G
                    sub = pu * qte
                    tot += sub
                    det_list.append({"art": a, "qty": qte, "pu": pu})
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{a}**")
                    st.session_state.panier[a] = c2.number_input("Qté", 1, p_map[a][1], value=qte, key=f"ca_{a}")
                    if c3.button("🗑️", key=f"rm_{a}"): del st.session_state.panier[a]; st.rerun()
                
                st.markdown(f"### TOTAL : {tot:,.2f} {dev}")
                cli = st.text_input("Client", "COMPTANT")
                pay = st.number_input("Payé", value=float(tot))
                if st.button("VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref, cli.upper(), tot, pay, tot-pay, dev, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(det_list)))
                    if tot-pay > 0: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cli.upper(), tot-pay, dev, ref, st.session_state.ent_id))
                    for a, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel=stock_actuel-? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    st.session_state.last_fac = {"ref": ref, "tot": tot, "dev": dev, "cli": cli.upper(), "det": det_list}; st.session_state.panier = {}; st.rerun()
        else:
            # Facture Administrative
            f = st.session_state.last_fac
            e = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            col1, col2, col3 = st.columns(3)
            if col1.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()
            
            st.markdown(f"""
            <div class="invoice-card">
                <h2 align="center">{e[0]}</h2>
                <p align="center">{e[1]}<br>Tél: {e[2]} | RCCM: {e[3]}</p><hr>
                <p><b>REF:</b> {f['ref']} | <b>CLIENT:</b> {f['cli']}</p>
                <table width="100%">
                    <tr><th>Art</th><th>Qté</th><th>Total</th></tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qty']}</td><td align='right'>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['det']])}
                </table><hr>
                <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            </div>
            """, unsafe_allow_html=True)
            if col2.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if col3.button("📤 PARTAGER"):
                msg = f"Facture {f['ref']} - {e[0]} - Total: {f['tot']} {f['dev']}"
                st.components.v1.html(f"<script>navigator.share({{title:'Facture', text:'{msg}', url:window.location.href}})</script>")

    # --- RAPPORTS ---
    elif st.session_state.page == "RAPPORTS":
        st.header("📊 HISTORIQUE")
        data = run_db("SELECT date_v, ref, client, total, devise, details_json FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if data:
            df = pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Devise", "JSON"])
            st.dataframe(df.drop("JSON", axis=1), use_container_width=True)
            sel_r = st.selectbox("Réimprimer :", df["Réf"].unique())
            if st.button("GÉNÉRER FACTURE"):
                row = [x for x in data if x[1] == sel_r][0]
                st.session_state.last_fac = {"ref": row[1], "tot": row[3], "dev": row[4], "cli": row[2], "det": json.loads(row[5])}
                st.session_state.page = "CAISSE"; st.rerun()

    # --- VENDEURS ---
    elif st.session_state.page == "VENDEURS":
        st.header("👥 MES COMPTES VENDEURS")
        with st.form("v_add"):
            v_u = st.text_input("Identifiant Vendeur")
            v_p = st.text_input("Mot de passe Vendeur", type="password")
            if st.form_submit_button("CRÉER COMPTE"):
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
                       (v_u, make_hashes(v_p), 'VENDEUR', st.session_state.ent_id)); st.rerun()
        
        for vu, in run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True):
            st.write(f"Vendeur : **{vu}**")

    # --- RÉGLAGES ---
    elif st.session_state.page == "RÉGLAGES":
        st.header("⚙️ PARAMÈTRES BOUTIQUE")
        e = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        with st.form("e_up"):
            en = st.text_input("Nom de l'entreprise", e[0])
            ea = st.text_input("Adresse", e[1])
            et = st.text_input("Téléphone", e[2])
            er = st.text_input("RCCM / ID Nat", e[3])
            if st.form_submit_button("METTRE À JOUR EN-TÊTE"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=? WHERE ent_id=?", (en, ea, et, er, st.session_state.ent_id))
                st.rerun()
        
        st.write("---")
        # Photo et Password
        new_pass = st.text_input("Changer mon mot de passe", type="password")
        up_img = st.file_uploader("Photo de profil", type=['jpg', 'png'])
        if st.button("ENREGISTRER PROFIL"):
            if new_pass: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_pass), st.session_state.user))
            if up_img:
                img_byte = up_img.getvalue()
                run_db("UPDATE users SET photo=? WHERE username=?", (sqlite3.Binary(img_byte), st.session_state.user))
            st.success("Profil mis à jour !")
