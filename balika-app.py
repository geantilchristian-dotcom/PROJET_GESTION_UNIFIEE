import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME ULTIME
# ==========================================
st.set_page_config(page_title="BALIKA ERP PRO v251", layout="wide", initial_sidebar_state="collapsed")

# Initialisation de la session
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
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, taux REAL, message TEXT, logo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, avatar BLOB)")
    
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role) VALUES ('admin', ?, 'ADMIN')", (make_hashes("admin123"),))
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config (id, entreprise, adresse, telephone, taux, message) VALUES (1, 'BALIKA ERP', 'VOTRE ADRESSE', '000', 2850.0, 'Bienvenue')")

init_db()

# Chargement config
cfg_res = run_db("SELECT entreprise, message, taux, adresse, telephone FROM config WHERE id=1", fetch=True)[0]
C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = cfg_res

# ==========================================
# 3. DESIGN CSS MOBILE-FIRST (ANTI MODE SOMBRE)
# ==========================================
st.markdown(f"""
    <style>
    /* Force le blanc et le noir partout */
    html, body, .stApp, [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}
    
    /* Correction visibilité des listes déroulantes sur téléphone */
    div[data-baseweb="select"] > div, .stSelectbox div {{
        background-color: #F0F2F6 !important;
        color: #000000 !important;
    }}
    
    /* Textes et Labels */
    h1, h2, h3, h4, h5, h6, p, span, label, div, li, td, th {{
        color: #000000 !important;
    }}

    /* Boutons de commande */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important;
        border-radius: 12px; height: 55px; width: 100%; border: none; font-weight: bold;
    }}

    /* Marquee défilant */
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 12px 0; font-weight: bold; position: fixed; top: 0; z-index: 1000; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Cadre du Total Panier */
    .total-box {{
        border: 4px solid #FF8C00; background: #FFF3E0; padding: 20px; border-radius: 15px;
        text-align: center; font-size: 26px; font-weight: bold; color: #E65100 !important; margin: 15px 0;
    }}

    /* FORMATS DE FACTURES */
    .fac-a4 {{ width: 95%; margin: auto; padding: 30px; border: 2px solid #000; background: white; }}
    .fac-80 {{ width: 80mm; margin: auto; padding: 10px; border: 1px dashed #000; font-family: 'Courier New', monospace; text-align: center; background: white; }}
    
    @media print {{
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }}
        .fac-a4, .fac-80 {{ border: none; width: 100%; padding: 0; }}
    }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    <div style="margin-top: 60px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. ÉCRAN DE CONNEXION
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown(f'<div style="background:#FF8C00; padding:30px; border-radius:20px; text-align:center; color:white !important;"><h1>{C_ENT}</h1><p>GESTION COMMERCIALE</p></div>', unsafe_allow_html=True)
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("ACCÉDER AU SYSTÈME"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, res[0][1]
                st.rerun()
            else: st.error("Identifiants incorrects.")
    st.stop()

# ==========================================
# 5. MENU LATÉRAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.write(f"Accès : {st.session_state.role}")
    st.write("---")
    
    nav = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        nav.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 VENDEURS": "USERS", "⚙️ CONFIG": "CONFIG"})
    
    for label, page in nav.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = page
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 6. LOGIQUE DES PAGES
# ==========================================

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div style="border:5px solid #FF8C00; border-radius:50%; width:220px; height:220px; display:flex; flex-direction:column; justify-content:center; background:#FFF3E0;"><h1>{datetime.now().strftime("%H:%M")}</h1><h3>{datetime.now().strftime("%d/%m/%Y")}</h3></div></center>', unsafe_allow_html=True)
    st.title("📊 Résumé du jour")
    v = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if v:
        df = pd.DataFrame(v, columns=["T", "D"])
        c1, c2 = st.columns(2)
        c1.metric("Ventes USD", f"{df[df['D']=='USD']['T'].sum():,.2f} $")
        c2.metric("Ventes CDF", f"{df[df['D']=='CDF']['T'].sum():,.0f} FC")
    else: st.info("Aucune transaction enregistrée aujourd'hui.")

# --- CAISSE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Terminal de Vente")
        devise_v = st.radio("Monnaie de paiement", ["USD", "CDF"], horizontal=True)
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
        
        sel = st.selectbox("CHOISIR L'ARTICLE", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            total_gnl = 0.0; details = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_map[art]['p']
                # Taux conversion
                if p_map[art]['d'] == "USD" and devise_v == "CDF": pf = pb * C_TAUX
                elif p_map[art]['d'] == "CDF" and devise_v == "USD": pf = pb / C_TAUX
                else: pf = pb
                
                st.write(f"**{art}** | {pf:,.2f} {devise_v}")
                c1, c2 = st.columns([3, 1])
                new_q = c1.number_input("Quantité", 1, p_map[art]['s'], value=qte, key=f"q_{art}")
                st.session_state.panier[art] = new_q
                if c2.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
                
                st_val = pf * new_q
                total_gnl += st_val
                details.append({'art': art, 'qte': new_q, 'pu': pf, 'st': st_val})
            
            st.markdown(f'<div class="total-box">À PAYER : {total_gnl:,.2f} {devise_v}</div>', unsafe_allow_html=True)
            cl = st.text_input("NOM DU CLIENT").upper()
            ac = st.number_input("MONTANT REÇU", 0.0)
            fmt = st.selectbox("FORMAT D'IMPRESSION", ["80mm (Ticket)", "A4 (Facture)"])
            
            if st.button("✅ VALIDER LA VENTE") and cl:
                ref = f"FAC-{random.randint(1000,9999)}"; now = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = total_gnl - ac
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", (ref, cl, total_gnl, ac, reste, str(details), devise_v, now))
                if reste > 0: run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)", (cl, reste, devise_v, f"{len(details)} articles", ref, now))
                for it in details: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (it['qte'], it['art']))
                st.session_state.last_fac = {"ref": ref, "cl": cl, "tot": total_gnl, "ac": ac, "re": reste, "dev": devise_v, "lines": details, "date": now, "fmt": fmt}
                st.session_state.panier = {}; st.rerun()
    else:
        # --- AFFICHAGE FACTURES ---
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        if f['fmt'] == "80mm (Ticket)":
            st.markdown(f"""
            <div class="fac-80">
                <h2>{C_ENT}</h2><p>{C_ADR}<br>Tél: {C_TEL}</p><hr>
                <p align="left">N°: {f['ref']}<br>Client: {f['cl']}<br>Date: {f['date']}</p><hr>
                <table style="width:100%; font-size:12px;">
                    {"".join([f"<tr><td>{l['art']}</td><td>x{l['qte']}</td><td align='right'>{l['st']:,.0f}</td></tr>" for l in f['lines']])}
                </table><hr>
                <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
                <p align="left" style="font-size:11px;">Payé: {f['ac']}<br>Reste: {f['re']}</p>
                <p>Merci de votre confiance !</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="fac-a4">
                <div style="display:flex; justify-content:space-between; border-bottom:3px solid #000;">
                    <div><h1>{C_ENT}</h1><p>{C_ADR}<br>Tél: {C_TEL}</p></div>
                    <div style="text-align:right;"><h2>FACTURE N° {f['ref']}</h2><p>Date: {f['date']}</p></div>
                </div>
                <div style="margin:20px 0;"><b>CLIENT :</b> {f['cl']}</div>
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="background:#EEE;">
                        <th style="border:1px solid #000; padding:10px;">Désignation</th>
                        <th style="border:1px solid #000; padding:10px;">Qté</th>
                        <th style="border:1px solid #000; padding:10px;">P.U</th>
                        <th style="border:1px solid #000; padding:10px;">Total</th>
                    </tr>
                    {"".join([f"<tr><td style='border:1px solid #000; padding:10px;'>{l['art']}</td><td style='border:1px solid #000; padding:10px; text-align:center;'>{l['qte']}</td><td style='border:1px solid #000; padding:10px; text-align:right;'>{l['pu']:,.2f}</td><td style='border:1px solid #000; padding:10px; text-align:right;'>{l['st']:,.2f}</td></tr>" for l in f['lines']])}
                </table>
                <div style="text-align:right; font-size:22px; font-weight:bold; margin-top:20px;">NET À PAYER : {f['tot']:,.2f} {f['dev']}</div>
                <p>Payé : {f['ac']} | Reste à payer : {f['re']}</p>
                <div style="display:flex; justify-content:space-between; margin-top:50px; font-weight:bold;">
                    <span>Signature Client</span><span>Pour l'Entreprise</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Inventaire")
    with st.form("add_p"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Désignation")
        p = c2.number_input("Prix")
        d = st.selectbox("Devise", ["USD", "CDF"])
        q = st.number_input("Stock", 1)
        if st.form_submit_button("ENREGISTRER"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (n.upper(), q, q, p, d))
            st.rerun()
    
    st.write("### Liste des articles")
    stk = run_db("SELECT * FROM produits", fetch=True)
    for r in stk:
        with st.expander(f"📦 {r[1]} ({r[3]} restants)"):
            new_pr = st.number_input("Changer Prix", value=float(r[4]), key=f"e_{r[0]}")
            if st.button("Modifier", key=f"s_{r[0]}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_pr, r[0])); st.rerun()
            if st.button("Supprimer", key=f"d_{r[0]}"): run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Suivi des Dettes")
    dts = run_db("SELECT * FROM dettes", fetch=True)
    for d in dts:
        st.info(f"Client: {d[1]} | Reste: {d[2]:,.2f} {d[3]}")
        v = st.number_input("Montant versé", 0.0, float(d[2]), key=f"p_{d[0]}")
        if st.button("Encaisser", key=f"b_{d[0]}"):
            if d[2]-v <= 0.05: run_db("DELETE FROM dettes WHERE id=?", (d[0],))
            else: run_db("UPDATE dettes SET montant_du=montant_du-? WHERE id=?", (v, d[0]))
            run_db("UPDATE ventes SET reste=reste-? WHERE ref=?", (v, d[5])); st.rerun()

# --- USERS ---
elif st.session_state.page == "USERS":
    st.title("👥 Personnel")
    with st.form("usr"):
        nu = st.text_input("Nom"); np = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER VENDEUR"):
            run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", (nu.lower(), make_hashes(np), "VENDEUR"))
            st.rerun()
    for u in run_db("SELECT username FROM users WHERE username!='admin'", fetch=True):
        st.write(f"👤 {u[0].upper()}")
        if st.button(f"X {u[0]}"): run_db("DELETE FROM users WHERE username=?", (u[0],)); st.rerun()

# --- CONFIG ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres")
    with st.form("c"):
        en = st.text_input("Entreprise", C_ENT); ad = st.text_input("Adresse", C_ADR)
        tl = st.text_input("Tél", C_TEL); tx = st.number_input("Taux (1 USD en CDF)", value=C_TAUX)
        ms = st.text_area("Message Accueil", C_MSG)
        if st.form_submit_button("APPLIQUER"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, taux=?, message=? WHERE id=1", (en.upper(), ad, tl, tx, ms)); st.rerun()
    if st.download_button("📥 BACKUP (Sauvegarde)", open("anash_data.db","rb"), file_name="backup.db"): st.success("Fichier prêt !")

# --- RAPPORT ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Historique")
    data = run_db("SELECT date_v, ref, client_nom, total_val, devise, reste FROM ventes ORDER BY id DESC", fetch=True)
    if data: st.dataframe(pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Devise", "Dette"]), use_container_width=True)
