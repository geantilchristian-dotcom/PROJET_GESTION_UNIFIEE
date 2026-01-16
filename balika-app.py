import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v258)
# ==========================================
st.set_page_config(page_title="BALIKA ERP v258", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'panier' not in st.session_state: st.session_state.panier = {} 
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'last_fac' not in st.session_state: st.session_state.last_fac = None
if 'role' not in st.session_state: st.session_state.role = "VENDEUR"
if 'user' not in st.session_state: st.session_state.user = ""

def run_db(query, params=(), fetch=False):
    # Optimisation pour éviter les erreurs OperationalError (Database locked)
    try:
        with sqlite3.connect('anash_data.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL") # Mode haute performance
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 2. INITIALISATION ET STRUCTURE DB
# ==========================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL, devise_origine TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, total_val REAL, acompte REAL, reste REAL, details TEXT, devise TEXT, date_v TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, montant_du REAL, devise TEXT, articles TEXT, sale_ref TEXT, date_d TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, email TEXT, rccm TEXT, idnat TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    
    # Correction automatique des colonnes
    cols = [c[1] for c in run_db("PRAGMA table_info(config)", fetch=True)]
    for col in ['email', 'rccm', 'idnat']:
        if col not in cols: run_db(f"ALTER TABLE config ADD COLUMN {col} TEXT DEFAULT '---'")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'ADMIN')", (make_hashes("admin123"),))
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'ADRESSE', '000', 'info@mail.com', '000', '000', 2850.0, 'Bienvenue')")

init_db()
cfg_data = run_db("SELECT entreprise, message, taux, adresse, telephone, email, rccm, idnat FROM config WHERE id=1", fetch=True)
C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL, C_MAIL, C_RCCM, C_IDN = cfg_data[0]

# ==========================================
# 3. DESIGN ANTI-DARK MODE & MOBILE
# ==========================================
st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}
    h1, h2, h3, label, p, span, b, div {{ color: #000000 !important; font-weight: bold; }}
    input, select, textarea {{
        background-color: #F8F9FA !important;
        color: #000000 !important;
        border: 2px solid #FF8C00 !important;
    }}
    .stButton>button {{
        background: linear-gradient(to right, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 50px; border: none; font-weight: bold; width: 100%;
    }}
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 10px 0; position: fixed; top: 0; z-index: 9999; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; font-size: 18px; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .fac-80 {{ width: 80mm; margin: auto; padding: 10px; border: 1px dashed #000; text-align: center; }}
    .fac-a4 {{ width: 100%; padding: 20px; border: 2px solid #000; }}
    @media print {{ .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }} }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🔥 {C_ENT} : {C_MSG}</div></div>
    <div style="margin-top: 60px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. LOGIN ET INSCRIPTION
# ==========================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center;'>{C_ENT}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 CONNEXION", "📝 CRÉER COMPTE"])
    with t1:
        u = st.text_input("Utilisateur").lower()
        p = st.text_input("Mot de passe", type="password")
        if st.button("ENTRER"):
            r = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if r and make_hashes(p) == r[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, r[0][1]
                st.rerun()
            else: st.error("Échec de connexion")
    with t2:
        nu = st.text_input("Nouvel Utilisateur").lower().strip()
        np = st.text_input("Nouveau Mot de passe", type="password").strip()
        if st.button("S'INSCRIRE"):
            if nu and np:
                exist = run_db("SELECT * FROM users WHERE username=?", (nu,), fetch=True)
                if not exist:
                    run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", (nu, make_hashes(np), "VENDEUR"))
                    st.success("Compte créé ! Connectez-vous.")
                else: st.warning("Nom déjà pris.")
    st.stop()

# ==========================================
# 5. NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    pags = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        pags.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 COMPTES": "USERS", "⚙️ CONFIG": "CONFIG"})
    for n, p_id in pags.items():
        if st.button(n, use_container_width=True): st.session_state.page = p_id; st.rerun()
    if st.button("🚪 QUITTER"): st.session_state.auth = False; st.rerun()

# ==========================================
# 6. LOGIQUE DES PAGES
# ==========================================

if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div style="border:5px solid #FF8C00; border-radius:50%; width:180px; height:180px; display:flex; flex-direction:column; justify-content:center; background:#FFF3E0;"><h1>{datetime.now().strftime("%H:%M")}</h1><p>{datetime.now().strftime("%d/%m/%Y")}</p></div></center>', unsafe_allow_html=True)
    v = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if v:
        df = pd.DataFrame(v, columns=["T", "D"])
        st.metric("Total USD", f"{df[df['D']=='USD']['T'].sum():,.2f} $")
        st.metric("Total CDF", f"{df[df['D']=='CDF']['T'].sum():,.0f} FC")

elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse")
        dv = st.radio("Monnaie", ["USD", "CDF"], horizontal=True)
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
        sel = st.selectbox("Article", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
        if st.session_state.panier:
            tot = 0.0; rows = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_map[art]['p']
                pf = pb * C_TAUX if p_map[art]['d'] == "USD" and dv == "CDF" else (pb / C_TAUX if p_map[art]['d'] == "CDF" and dv == "USD" else pb)
                tot += (pf * qte); rows.append({'art': art, 'qte': qte, 'st': pf*qte})
                c1, c2 = st.columns([3, 1])
                st.session_state.panier[art] = c1.number_input(f"{art}", 1, p_map[art]['s'], value=qte)
                if c2.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
            st.markdown(f'<div style="border:4px solid #FF8C00; padding:15px; text-align:center; font-size:22px;">TOTAL : {tot:,.2f} {dv}</div>', unsafe_allow_html=True)
            nom = st.text_input("CLIENT").upper()
            pay = st.number_input("REÇU", 0.0)
            fmt = st.selectbox("FORMAT", ["80mm", "A4"])
            if st.button("✅ VALIDER") and nom:
                ref = f"FAC-{random.randint(1000,9999)}"; now = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", (ref, nom, tot, pay, tot-pay, str(rows), dv, now))
                if tot-pay > 0: run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)", (nom, tot-pay, dv, "Vente", ref, now))
                for r in rows: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (r['qte'], r['art']))
                st.session_state.last_fac = {"ref": ref, "cl": nom, "tot": tot, "ac": pay, "re": tot-pay, "dev": dv, "lines": rows, "date": now, "fmt": fmt}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        h_ls = "".join([f"<tr><td>{l['art']}</td><td align='center'>x{l['qte']}</td><td align='right'>{l['st']:,.0f}</td></tr>" for l in f['lines']])
        if f['fmt'] == "80mm":
            st.markdown(f'<div class="fac-80"><h3>{C_ENT}</h3><p>{C_ADR}</p><hr><p align="left">N°: {f["ref"]}<br>Client: {f["cl"]}</p><hr><table style="width:100%">{h_ls}</table><hr><h4>TOTAL: {f["tot"]:,.0f} {f["dev"]}</h4><div class="signature-area"><span>Client</span><span>Vendeur</span></div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="fac-a4"><h1>{C_ENT}</h1><p>{C_ADR} | {C_TEL}</p><hr><h3>FACTURE N° {f["ref"]}</h3><b>CLIENT : {f["cl"]}</b><table style="width:100%; border-collapse:collapse; margin-top:15px"><tr style="background:#EEE"><th>Article</th><th>Qté</th><th>Total</th></tr>{h_ls.replace("<td>", "<td style=\'border:1px solid #000; padding:8px\'>")}</table><h3 align="right">NET : {f["tot"]:,.2f} {f["dev"]}</h3></div>', unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

elif st.session_state.page == "STOCK":
    st.title("📦 Stock")
    with st.form("p"):
        n = st.text_input("Nom"); p = st.number_input("Prix"); d = st.selectbox("Devise", ["USD", "CDF"]); q = st.number_input("Qté", 1)
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (n.upper(), q, q, p, d)); st.rerun()
    for r in run_db("SELECT * FROM produits", fetch=True):
        with st.expander(f"{r[1]} ({r[3]})"):
            np = st.number_input("Prix", value=float(r[4]), key=f"p_{r[0]}")
            if st.button("Sauver", key=f"s_{r[0]}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (np, r[0])); st.rerun()
            if st.button("Supprimer", key=f"del_{r[0]}"): run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

elif st.session_state.page == "USERS":
    st.title("👥 Gestion des Comptes")
    # Liste de tous les comptes
    users = run_db("SELECT username, role FROM users", fetch=True)
    for u_name, u_role in users:
        c1, c2 = st.columns([3, 1])
        c1.write(f"👤 **{u_name.upper()}** - Rôle: {u_role}")
        if u_name != "admin": # Empêcher de supprimer l'admin principal
            if c2.button("🗑️", key=f"u_{u_name}"):
                run_db("DELETE FROM users WHERE username=?", (u_name,))
                st.rerun()

elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres")
    # Changer Nom d'utilisateur
    with st.expander("👤 MON COMPTE (CHANGER IDENTIFIANT/PASSWORD)"):
        new_username = st.text_input("Nouveau Nom d'utilisateur", value=st.session_state.user)
        new_password = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("METTRE À JOUR MON COMPTE"):
            if new_username:
                # Vérifier si le nom existe déjà
                check = run_db("SELECT * FROM users WHERE username=? AND username!=?", (new_username, st.session_state.user), fetch=True)
                if not check:
                    if new_password:
                        run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_username, make_hashes(new_password), st.session_state.user))
                    else:
                        run_db("UPDATE users SET username=? WHERE username=?", (new_username, st.session_state.user))
                    st.session_state.user = new_username
                    st.success("Compte mis à jour !")
                    st.rerun()
                else: st.error("Ce nom d'utilisateur est déjà pris.")

    with st.form("cfg"):
        ent = st.text_input("NOM ENTREPRISE", C_ENT)
        adr = st.text_input("ADRESSE", C_ADR); tel = st.text_input("TEL", C_TEL)
        tx = st.number_input("TAUX", value=C_TAUX); msg = st.text_area("MESSAGE DÉFILANT", C_MSG)
        if st.form_submit_button("SAUVER CONFIG"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, taux=?, message=? WHERE id=1", (ent.upper(), adr, tel, tx, msg))
            st.rerun()
