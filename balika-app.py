import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v253 - INTÉGRAL)
# ==========================================
st.set_page_config(page_title="BALIKA ERP ULTIME", layout="wide", initial_sidebar_state="collapsed")

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
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, email TEXT, rccm TEXT, idnat TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    
    # Création Admin par défaut (admin / admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'ADMIN')", (make_hashes("admin123"),))
    # Config par défaut
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'VOTRE ADRESSE', '000', 'contact@mail.com', 'RCCM-000', 'IDNAT-000', 2850.0, 'Bienvenue chez BALIKA')")

init_db()

# Chargement Config Globale
cfg_data = run_db("SELECT entreprise, message, taux, adresse, telephone, email, rccm, idnat FROM config WHERE id=1", fetch=True)[0]
C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL, C_MAIL, C_RCCM, C_IDN = cfg_data

# ==========================================
# 3. CSS SPÉCIAL MOBILE & ANTI-MODE SOMBRE
# ==========================================
st.markdown(f"""
    <style>
    /* Force le fond blanc et texte noir pour iPhone */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}
    
    /* Correction visibilité Selectbox (Produits) */
    div[data-baseweb="select"] > div, .stSelectbox div {{
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        opacity: 1 !important;
    }}

    /* Titres et Textes */
    h1, h2, h3, h4, label, p, span, div {{ color: #000000 !important; font-weight: 600; }}

    /* Boutons Orange Stylisés */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 55px; width: 100%; border: none; font-weight: bold;
    }}

    /* Cadre Total Panier */
    .total-box {{
        border: 4px solid #FF8C00; background: #FFF3E0; padding: 20px; border-radius: 15px;
        text-align: center; font-size: 26px; font-weight: bold; color: #E65100 !important;
    }}

    /* Marquee Défilant */
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 12px 0; font-weight: bold; position: fixed; top: 0; z-index: 1000; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Facture 80mm et A4 */
    .fac-a4 {{ width: 100%; padding: 25px; border: 2px solid #000; background: white; color: black; }}
    .fac-80 {{ width: 80mm; margin: auto; padding: 10px; border: 1px dashed #000; font-family: 'Courier New', monospace; text-align: center; background: white; color: black; }}
    
    @media print {{
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }}
    }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    <div style="margin-top: 60px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. SYSTÈME DE CONNEXION
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown(f'<div style="background:#FF8C00; padding:30px; border-radius:20px; text-align:center; color:white !important;"><h1>{C_ENT}</h1><p>ACCÈS SÉCURISÉ</p></div>', unsafe_allow_html=True)
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, res[0][1]
                st.rerun()
            else: st.error("Erreur d'identification.")
    st.stop()

# ==========================================
# 5. MENU DE NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.write(f"Rôle : {st.session_state.role}")
    st.write("---")
    
    pages = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        pages.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 VENDEURS": "USERS", "⚙️ CONFIG": "CONFIG"})
    
    for n, p in pages.items():
        if st.button(n, use_container_width=True):
            st.session_state.page = p
            st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 6. CONTENU DES PAGES
# ==========================================

# --- PAGE ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div style="border:5px solid #FF8C00; border-radius:50%; width:200px; height:200px; display:flex; flex-direction:column; justify-content:center; background:#FFF3E0;"><h1>{datetime.now().strftime("%H:%M")}</h1><p>{datetime.now().strftime("%d/%m/%Y")}</p></div></center>', unsafe_allow_html=True)
    st.title("📊 Performance du jour")
    v = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if v:
        df = pd.DataFrame(v, columns=["T", "D"])
        c1, c2 = st.columns(2)
        c1.metric("Recette USD", f"{df[df['D']=='USD']['T'].sum():,.2f} $")
        c2.metric("Recette CDF", f"{df[df['D']=='CDF']['T'].sum():,.0f} FC")
    else: st.info("Aucune vente aujourd'hui.")

# --- PAGE CAISSE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse Mobile")
        dev_v = st.radio("Devise de vente", ["USD", "CDF"], horizontal=True)
        items = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in items}
        
        choix = st.selectbox("RECHERCHER ARTICLE", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            total_gnl = 0.0; details_v = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_map[art]['p']
                pf = pb * C_TAUX if p_map[art]['d'] == "USD" and dev_v == "CDF" else (pb / C_TAUX if p_map[art]['d'] == "CDF" and dev_v == "USD" else pb)
                total_gnl += (pf * qte)
                details_v.append({'art': art, 'qte': qte, 'pu': pf, 'st': pf*qte})
                
                c1, c2 = st.columns([3, 1])
                new_q = c1.number_input(f"{art} ({pf:,.0f} {dev_v})", 1, p_map[art]['s'], value=qte, key=f"q_{art}")
                st.session_state.panier[art] = new_q
                if c2.button("🗑️", key=f"d_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-box">À PAYER : {total_gnl:,.2f} {dev_v}</div>', unsafe_allow_html=True)
            cl_nom = st.text_input("NOM DU CLIENT").upper()
            paye = st.number_input("ACOMPTE", 0.0)
            fmt_fac = st.selectbox("FORMAT FACTURE", ["80mm (Ticket)", "A4 (Administratif)"])
            
            if st.button("✅ FINALISER LA VENTE") and cl_nom:
                ref_f = f"FAC-{random.randint(1000,9999)}"; now_f = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste_f = total_gnl - paye
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", (ref_f, cl_nom, total_gnl, paye, reste_f, str(details_v), dev_v, now_f))
                if reste_f > 0: run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)", (cl_nom, reste_f, dev_v, f"{len(details_v)} articles", ref_f, now_f))
                for d in details_v: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (d['qte'], d['art']))
                st.session_state.last_fac = {"ref": ref_f, "cl": cl_nom, "tot": total_gnl, "ac": paye, "re": reste_f, "dev": dev_v, "lines": details_v, "date": now_f, "fmt": fmt_fac}
                st.session_state.panier = {}; st.rerun()
    else:
        # Affichage de la Facture
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        if f['fmt'] == "80mm (Ticket)":
            st.markdown(f'<div class="fac-80"><h2>{C_ENT}</h2><p>{C_ADR}<br>{C_TEL}</p><hr><p align="left">N°: {f["ref"]}<br>Client: {f["cl"]}<br>Date: {f["date"]}</p><hr><table style="width:100%">{"".join([f"<tr><td align=\'left\'>{l[\'art\']}</td><td>x{l[\'qte\']}</td><td align=\'right\'>{l[\'st\']:,.0f}</td></tr>" for l in f["lines"]])}</table><hr><h3>TOTAL: {f["tot"]:,.0f} {f["dev"]}</h3><p>Payé: {f["ac"]} | Reste: {f["re"]}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="fac-a4"><div style="display:flex; justify-content:space-between"><div><h1>{C_ENT}</h1><p>{C_ADR}<br>Tél: {C_TEL}<br>Email: {C_MAIL}<br>RCCM: {C_RCCM} | IDNAT: {C_IDN}</p></div><div style="text-align:right"><h2>FACTURE</h2><p>N° {f["ref"]}<br>Date: {f["date"]}</p></div></div><hr><b>CLIENT : {f["cl"]}</b><table style="width:100%; border-collapse:collapse; margin-top:15px"><tr style="background:#EEE"><th style="border:1px solid #000; padding:10px">Article</th><th style="border:1px solid #000; padding:10px">Qté</th><th style="border:1px solid #000; padding:10px">P.U</th><th style="border:1px solid #000; padding:10px">Total</th></tr>{"".join([f"<tr><td style=\'border:1px solid #000; padding:10px\'>{l[\'art\']}</td><td style=\'border:1px solid #000; text-align:center\'>{l[\'qte\']}</td><td style=\'border:1px solid #000; text-align:right\'>{l[\'pu\']:,.0f}</td><td style=\'border:1px solid #000; text-align:right\'>{l[\'st\']:,.0f}</td></tr>" for l in f["lines"]])}</table><h3 style="text-align:right; margin-top:20px">NET À PAYER : {f["tot"]:,.2f} {f["dev"]}</h3><p>Payé: {f["ac"]} | Reste: {f["re"]}</p><div style="display:flex; justify-content:space-between; margin-top:40px"><b>Le Client</b><b>Pour l\'Entreprise</b></div></div>', unsafe_allow_html=True)
        
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# --- PAGE STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion des Articles")
    with st.form("add_p"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Désignation")
        p = c2.number_input("Prix de vente", 0.0)
        d = st.selectbox("Devise", ["USD", "CDF"])
        q = st.number_input("Quantité initiale", 1)
        if st.form_submit_button("ENREGISTRER PRODUIT"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (n.upper(), q, q, p, d))
            st.rerun()
    
    st.write("---")
    for r in run_db("SELECT * FROM produits", fetch=True):
        with st.expander(f"📦 {r[1]} - {r[3]} en stock"):
            new_pr = st.number_input("Modifier Prix", value=float(r[4]), key=f"p_{r[0]}")
            col1, col2 = st.columns(2)
            if col1.button("Sauver Prix", key=f"s_{r[0]}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_pr, r[0])); st.rerun()
            if col2.button("Supprimer", key=f"del_{r[0]}"):
                run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

# --- PAGE DETTES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Dettes Clients")
    dts = run_db("SELECT * FROM dettes", fetch=True)
    if not dts: st.success("Aucune dette en cours.")
    for d in dts:
        st.info(f"Client: {d[1]} | Reste à payer: {d[2]:,.2f} {d[3]}")
        v_paye = st.number_input("Montant versé", 0.0, float(d[2]), key=f"v_{d[0]}")
        if st.button(f"Valider paiement {d[1]}", key=f"b_{d[0]}"):
            reste_n = d[2] - v_paye
            if reste_n <= 0.05: run_db("DELETE FROM dettes WHERE id=?", (d[0],))
            else: run_db("UPDATE dettes SET montant_du=? WHERE id=?", (reste_n, d[0]))
            run_db("UPDATE ventes SET reste = reste - ? WHERE ref=?", (v_paye, d[5])); st.rerun()

# --- PAGE RAPPORT ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Journal des Ventes")
    data = run_db("SELECT date_v, ref, client_nom, total_val, devise, reste FROM ventes ORDER BY id DESC", fetch=True)
    if data:
        df = pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Devise", "Reste"])
        st.dataframe(df, use_container_width=True)
        st.button("🖨️ IMPRIMER LE RAPPORT", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
    else: st.warning("Le journal est vide.")

# --- PAGE USERS ---
elif st.session_state.page == "USERS":
    st.title("👥 Personnel")
    with st.form("nu"):
        nu = st.text_input("Identifiant"); np = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            run_db("INSERT INTO users VALUES (?,?,'VENDEUR')", (nu.lower(), make_hashes(np))); st.rerun()
    for u in run_db("SELECT username FROM users WHERE username!='admin'", fetch=True):
        st.write(f"👤 {u[0].upper()}")
        if st.button(f"Supprimer {u[0]}", key=u[0]): run_db("DELETE FROM users WHERE username=?", (u[0],)); st.rerun()

# --- PAGE CONFIG ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Configuration")
    with st.form("cfg"):
        en = st.text_input("Nom de l'Entreprise", C_ENT)
        ad = st.text_input("Adresse Physique", C_ADR); tl = st.text_input("Téléphone", C_TEL)
        ml = st.text_input("Email Professionnel", C_MAIL)
        rc = st.text_input("RCCM", C_RCCM); idn = st.text_input("ID NATIONAL", C_IDN)
        tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TAUX)
        ms = st.text_area("Message Défilant", C_MSG)
        if st.form_submit_button("SAUVEGARDER LES PARAMÈTRES"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, email=?, rccm=?, idnat=?, taux=?, message=? WHERE id=1", (en.upper(), ad, tl, ml, rc, idn, tx, ms))
            st.rerun()
    if os.path.exists("anash_data.db"):
        with open("anash_data.db", "rb") as f: st.download_button("📥 SAUVEGARDER LA BASE DE DONNÉES", f, file_name="backup_erp.db")
