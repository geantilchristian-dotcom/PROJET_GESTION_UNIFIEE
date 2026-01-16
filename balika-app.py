import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v254 - FIX SYNTAXE)
# ==========================================
st.set_page_config(page_title="BALIKA ERP v254", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'panier' not in st.session_state: st.session_state.panier = {} 
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'last_fac' not in st.session_state: st.session_state.last_fac = None
if 'role' not in st.session_state: st.session_state.role = "VENDEUR"
if 'user' not in st.session_state: st.session_state.user = ""

def run_db(query, params=(), fetch=False):
    with sqlite3.connect('anash_data.db', timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 2. INITIALISATION BASE DE DONNÉES
# ==========================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL, devise_origine TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, total_val REAL, acompte REAL, reste REAL, details TEXT, devise TEXT, date_v TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, montant_du REAL, devise TEXT, articles TEXT, sale_ref TEXT, date_d TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, email TEXT, rccm TEXT, idnat TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'ADMIN')", (make_hashes("admin123"),))
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'ADRESSE', '000', 'info@mail.com', 'RCCM-000', 'IDNAT-000', 2850.0, 'Bienvenue')")

init_db()
cfg = run_db("SELECT entreprise, message, taux, adresse, telephone, email, rccm, idnat FROM config WHERE id=1", fetch=True)[0]
C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL, C_MAIL, C_RCCM, C_IDN = cfg

# ==========================================
# 3. CSS ANTI-MODE SOMBRE & MOBILE
# ==========================================
st.markdown(f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}
    div[data-baseweb="select"] > div, .stSelectbox div {{
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        opacity: 1 !important;
    }}
    h1, h2, h3, label, p, span, div {{ color: #000000 !important; font-weight: bold; }}
    .stButton>button {{
        background: linear-gradient(to right, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 50px; border: none; font-weight: bold;
    }}
    .total-box {{
        border: 4px solid #FF8C00; background: #FFF3E0; padding: 15px; border-radius: 12px;
        text-align: center; font-size: 24px; color: #E65100 !important;
    }}
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 10px 0; position: fixed; top: 0; z-index: 1000; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .fac-a4 {{ width: 100%; padding: 20px; border: 2px solid #000; background: white; color: black; }}
    .fac-80 {{ width: 80mm; margin: auto; padding: 10px; border: 1px dashed #000; font-family: 'Courier New', monospace; text-align: center; background: white; color: black; }}
    @media print {{ .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }} }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    <div style="margin-top: 50px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. CONNEXION
# ==========================================
if not st.session_state.auth:
    st.markdown('<div style="background:#FF8C00; padding:30px; border-radius:15px; text-align:center; color:white !important;"><h1>LOGIN</h1></div>', unsafe_allow_html=True)
    u = st.text_input("Identifiant").lower().strip()
    p = st.text_input("Mot de passe", type="password").strip()
    if st.button("ACCÉDER"):
        res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
        if res and make_hashes(p) == res[0][0]:
            st.session_state.auth, st.session_state.user, st.session_state.role = True, u, res[0][1]
            st.rerun()
    st.stop()

# ==========================================
# 5. NAVIGATION
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state.user.upper()}")
    pages = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        pages.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 VENDEURS": "USERS", "⚙️ CONFIG": "CONFIG"})
    for n, p_id in pages.items():
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
        devise = st.radio("Monnaie", ["USD", "CDF"], horizontal=True)
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
        
        sel = st.selectbox("Choisir Article", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            total = 0.0; rows = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_map[art]['p']
                pf = pb * C_TAUX if p_map[art]['d'] == "USD" and devise == "CDF" else (pb / C_TAUX if p_map[art]['d'] == "CDF" and devise == "USD" else pb)
                total += (pf * qte)
                rows.append({'art': art, 'qte': qte, 'pu': pf, 'st': pf*qte})
                c1, c2 = st.columns([3, 1])
                new_q = c1.number_input(f"{art}", 1, p_map[art]['s'], value=qte, key=f"q_{art}")
                st.session_state.panier[art] = new_q
                if c2.button("🗑️", key=f"d_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-box">TOTAL : {total:,.2f} {devise}</div>', unsafe_allow_html=True)
            nom = st.text_input("CLIENT").upper()
            paye = st.number_input("PAYÉ", 0.0)
            fmt = st.selectbox("FORMAT", ["80mm", "A4"])
            
            if st.button("✅ VALIDER") and nom:
                ref = f"FAC-{random.randint(1000,9999)}"; now = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", (ref, nom, total, paye, total-paye, str(rows), devise, now))
                if total-paye > 0: run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)", (nom, total-paye, devise, f"{len(rows)} arts", ref, now))
                for r in rows: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (r['qte'], r['art']))
                st.session_state.last_fac = {"ref": ref, "cl": nom, "tot": total, "ac": paye, "re": total-paye, "dev": devise, "lines": rows, "date": now, "fmt": fmt}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        # --- FIX TECHNIQUE POUR LES LIGNES HTML ---
        html_lines = ""
        for l in f['lines']:
            html_lines += f"<tr><td>{l['art']}</td><td align='center'>x{l['qte']}</td><td align='right'>{l['st']:,.0f}</td></tr>"

        if f['fmt'] == "80mm":
            st.markdown(f"""
            <div class="fac-80">
                <h3>{C_ENT}</h3><p>{C_ADR}<br>{C_TEL}</p><hr>
                <p align="left">N°: {f['ref']}<br>Client: {f['cl']}<br>{f['date']}</p><hr>
                <table style="width:100%">{html_lines}</table><hr>
                <h4>TOTAL: {f['tot']:,.0f} {f['dev']}</h4>
                <p>Payé: {f['ac']} | Reste: {f['re']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="fac-a4">
                <div style="display:flex; justify-content:space-between">
                    <div><h1>{C_ENT}</h1><p>{C_ADR}<br>Tél: {C_TEL}<br>RCCM: {C_RCCM}</p></div>
                    <div style="text-align:right"><h2>FACTURE</h2><p>N° {f['ref']}<br>{f['date']}</p></div>
                </div><hr>
                <b>CLIENT : {f['cl']}</b>
                <table style="width:100%; border-collapse:collapse; margin-top:20px">
                    <tr style="background:#EEE"><th style="border:1px solid #000">Désignation</th><th style="border:1px solid #000">Qté</th><th style="border:1px solid #000">Total</th></tr>
                    {html_lines.replace('td>', 'td style="border:1px solid #000; padding:8px">')}
                </table>
                <h3 style="text-align:right">NET À PAYER : {f['tot']:,.2f} {f['dev']}</h3>
            </div>
            """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

elif st.session_state.page == "STOCK":
    st.title("📦 Stock")
    with st.form("p"):
        n = st.text_input("Nom"); p = st.number_input("Prix"); d = st.selectbox("Devise", ["USD", "CDF"]); q = st.number_input("Qté", 1)
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (n.upper(), q, q, p, d)); st.rerun()
    for r in run_db("SELECT * FROM produits", fetch=True):
        with st.expander(f"{r[1]} ({r[3]} en stock)"):
            np = st.number_input("Nouveau Prix", value=float(r[4]), key=f"p_{r[0]}")
            if st.button("Modifier", key=f"s_{r[0]}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (np, r[0])); st.rerun()
            if st.button("Supprimer", key=f"del_{r[0]}"): run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

elif st.session_state.page == "DETTES":
    st.title("📉 Dettes")
    for d in run_db("SELECT * FROM dettes", fetch=True):
        st.write(f"**{d[1]}** : {d[2]:,.2f} {d[3]}")
        v = st.number_input("Versement", 0.0, float(d[2]), key=f"v_{d[0]}")
        if st.button("Encaisser", key=f"b_{d[0]}"):
            if d[2]-v <= 0.05: run_db("DELETE FROM dettes WHERE id=?", (d[0],))
            else: run_db("UPDATE dettes SET montant_du=montant_du-? WHERE id=?", (v, d[0]))
            run_db("UPDATE ventes SET reste=reste-? WHERE ref=?", (v, d[5])); st.rerun()

elif st.session_state.page == "RAPPORT":
    st.title("📊 Rapport")
    data = run_db("SELECT date_v, ref, client_nom, total_val, devise, reste FROM ventes ORDER BY id DESC", fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Devise", "Dette"]), use_container_width=True)
        st.button("🖨️ IMPRIMER RAPPORT", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres")
    with st.form("cfg"):
        en = st.text_input("Entreprise", C_ENT); ad = st.text_input("Adresse", C_ADR); tl = st.text_input("Tél", C_TEL)
        ml = st.text_input("Email", C_MAIL); rc = st.text_input("RCCM", C_RCCM); idn = st.text_input("ID NAT", C_IDN)
        tx = st.number_input("Taux", value=C_TAUX); ms = st.text_area("Message", C_MSG)
        if st.form_submit_button("SAUVER"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, email=?, rccm=?, idnat=?, taux=?, message=? WHERE id=1", (en.upper(), ad, tl, ml, rc, idn, tx, ms)); st.rerun()
    if os.path.exists("anash_data.db"):
        with open("anash_data.db", "rb") as f: st.download_button("📥 Backup", f, file_name="backup.db")

elif st.session_state.page == "USERS":
    st.title("👥 Personnel")
    nu = st.text_input("Nom"); np = st.text_input("Pass", type="password")
    if st.button("Créer"): run_db("INSERT INTO users VALUES (?,?,?)", (nu.lower(), make_hashes(np), "VENDEUR")); st.rerun()
    for u in run_db("SELECT username FROM users WHERE username!='admin'", fetch=True):
        st.write(f"👤 {u[0]}")
        if st.button(f"Effacer {u[0]}"): run_db("DELETE FROM users WHERE username=?", (u[0],)); st.rerun()
