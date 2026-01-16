import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. SYSTÈME & SESSION (v244 COMPLET)
# ==========================================
st.set_page_config(page_title="BALIKA ERP v244", layout="wide", initial_sidebar_state="collapsed")

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
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, avatar BLOB)")
    
    # Création forcée de l'admin par défaut si la table est vide
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES (?,?,?,?)", ("admin", make_hashes("admin123"), "ADMIN", None))
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'ADRESSE', '000', 2850.0, 'Bienvenue')")

init_db()

# Récupération de la configuration
config_data = run_db("SELECT entreprise, message, taux, adresse, telephone FROM config WHERE id=1", fetch=True)
if config_data:
    C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = config_data[0]
else:
    C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = "BALIKA ERP", "Bienvenue", 2850.0, "ADRESSE", "000"

# ==========================================
# 3. DESIGN CSS (TEXTE NOIR & MOBILE)
# ==========================================
st.markdown(f"""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"], header {{ background-color: #FFFFFF !important; }}
    [data-testid="stHeader"] *, [data-testid="stSidebar"] *, h1, h2, h3, h4, label, span, p {{ color: #000000 !important; }}
    
    .login-box {{ background: linear-gradient(135deg, #FF8C00, #FF4500); padding: 40px; border-radius: 20px; color: white !important; text-align: center; }}
    .login-box h1, .login-box p {{ color: white !important; }}
    
    .stButton>button {{ background: linear-gradient(to right, #FF8C00, #FF4500) !important; color: white !important; border-radius: 12px; height: 55px; font-weight: bold; border: none; width: 100%; }}
    
    .marquee-container {{ width: 100%; overflow: hidden; background: #333; color: #FF8C00; padding: 12px 0; font-weight: bold; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 20s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    
    .clock-box {{ border: 3px solid #FF8C00; border-radius: 20px; padding: 20px; background: #FFF3E0; display: inline-block; text-align: center; }}
    .total-frame {{ border: 4px solid #FF8C00; background: #FFF3E0; color: #E65100 !important; padding: 20px; border-radius: 15px; font-size: 26px; font-weight: bold; text-align: center; margin: 15px 0; }}
    
    .print-area {{ background: white; color: black !important; padding: 15px; border: 1px solid #eee; }}
    .sig-row {{ margin-top: 40px; display: flex; justify-content: space-between; font-weight: bold; font-size: 14px; border-top: 1px dashed #ccc; padding-top: 10px; }}
    @media print {{ .no-print {{ display: none !important; }} .stApp {{ background: white !important; }} }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. ÉCRAN DE CONNEXION (AVEC RÉPARATION)
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown(f'<div class="login-box"><h1>{C_ENT}</h1><p>Veuillez vous identifier</p></div>', unsafe_allow_html=True)
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password").strip()
        
        if st.button("ACCÉDER AU SYSTÈME"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, res[0][1]
                st.rerun()
            else: st.error("Identifiants incorrects.")
        
        st.write("---")
        if st.button("🆘 RÉTABLIR ADMIN (admin / admin123)"):
            run_db("DELETE FROM users WHERE username='admin'")
            run_db("INSERT INTO users VALUES (?,?,?,?)", ("admin", make_hashes("admin123"), "ADMIN", None))
            st.success("Compte admin réinitialisé !")

    st.stop()

# ==========================================
# 5. BARRE LATÉRALE (NAVIGATION)
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.write("---")
    
    m = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        m.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 VENDEURS": "USERS", "⚙️ CONFIG": "CONFIG"})
    
    for label, pg in m.items():
        if st.button(label, use_container_width=True): 
            st.session_state.page = pg
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
    st.markdown(f'<center><div class="clock-box"><h1>⌚ {datetime.now().strftime("%H:%M")}</h1><h3>📅 {datetime.now().strftime("%d/%m/%Y")}</h3></div></center>', unsafe_allow_html=True)
    st.title("Statistiques du jour")
    v = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if v:
        df = pd.DataFrame(v, columns=["T", "D"])
        c1, c2 = st.columns(2)
        c1.metric("Total USD", f"{df[df['D']=='USD']['T'].sum():,.2f} $")
        c2.metric("Total CDF", f"{df[df['D']=='CDF']['T'].sum():,.0f} FC")

# --- CAISSE & FACTURE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Terminal de Vente")
        mv = st.radio("Devise de vente", ["USD", "CDF"], horizontal=True)
        items = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        imap = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in items}
        
        sel = st.selectbox("Sélectionner Article", ["---"] + list(imap.keys()))
        if st.button("➕ AJOUTER AU PANIER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
            
        total = 0.0; details = []; arts_txt = []
        if st.session_state.panier:
            st.write("### Panier en cours")
            for art, qte in list(st.session_state.panier.items()):
                pb = imap[art]['p']
                if imap[art]['d'] == "USD" and mv == "CDF": pf = pb * C_TAUX
                elif imap[art]['d'] == "CDF" and mv == "USD": pf = pb / C_TAUX
                else: pf = pb
                
                c_a, c_q, c_d = st.columns([3, 2, 1])
                c_a.write(f"**{art}**\n({pf:,.2f} {mv})")
                nq = c_q.number_input("Qté", 1, imap[art]['s'], value=qte, key=f"q_{art}")
                st.session_state.panier[art] = nq
                if c_d.button("🗑️", key=f"del_{art}"): 
                    del st.session_state.panier[art]
                    st.rerun()
                total += (pf * nq)
                details.append({'art': art, 'qte': nq, 'pu': pf, 'st': pf*nq})
                arts_txt.append(f"{art}(x{nq})")
            
            st.markdown(f'<div class="total-frame">À PAYER : {total:,.2f} {mv}</div>', unsafe_allow_html=True)
            cl = st.text_input("NOM DU CLIENT").upper()
            pay = st.number_input("MONTANT REÇU", 0.0)
            
            if st.button("✅ FINALISER LA VENTE") and cl:
                ref = f"FAC-{random.randint(1000,9999)}"
                now = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", (ref, cl, total, pay, total-pay, str(details), mv, now))
                if total-pay > 0:
                    run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)", (cl, total-pay, mv, ", ".join(arts_txt), ref, now))
                for d in details:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (d['qte'], d['art']))
                st.session_state.last_fac = {"ref": ref, "cl": cl, "tot": total, "ac": pay, "re": total-pay, "dev": mv, "lines": details, "date": now}
                st.session_state.panier = {}
                st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        fmt = st.radio("Format", ["80mm", "A4"], horizontal=True)
        
        fac_html = f"""<div class="print-area">
        <center><h2>{C_ENT}</h2><p>{C_ADR}<br>{C_TEL}</p></center><hr>
        <p><b>REF: {f['ref']}</b> | Client: {f['cl']}<br>Date: {f['date']}</p><hr>
        <table style="width:100%;">{"".join([f"<tr><td>{l['art']} x{l['qte']}</td><td style='text-align:right;'>{l['st']:,.2f}</td></tr>" for l in f['lines']])}</table><hr>
        <h3 style="text-align:right;">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
        <p style="text-align:right;">Payé: {f['ac']:,.2f} | Reste: {f['re']:,.2f}</p>
        <div class="sig-row"><div>Signature Client</div><div>Signature Vendeur</div></div></div>"""
        
        st.markdown(fac_html, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        msg_share = f"Facture {f['ref']} - {C_ENT}\nClient: {f['cl']}\nTotal: {f['tot']} {f['dev']}\nMerci de votre confiance."
        c2.markdown(f'<a href="https://wa.me/?text={msg_share}" target="_blank"><button style="width:100%; height:55px; background:#25D366; color:white; border:none; border-radius:12px; font-weight:bold;">📲 WHATSAPP</button></a>', unsafe_allow_html=True)

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion des Articles")
    with st.form("f_stk"):
        c1, c2, c3, c4 = st.columns(4)
        n = c1.text_input("Désignation")
        p = c2.number_input("Prix")
        d = c3.selectbox("Devise", ["USD", "CDF"])
        q = c4.number_input("Quantité", value=1)
        if st.form_submit_button("AJOUTER AU STOCK"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (n.upper(), q, q, p, d))
            st.rerun()
    
    stk_data = run_db("SELECT id, designation, stock_initial, stock_actuel, prix_vente, devise_origine FROM produits", fetch=True)
    if stk_data:
        df_stk = pd.DataFrame(stk_data, columns=["ID", "Désignation", "Initial", "Actuel", "Prix", "Devise"])
        st.dataframe(df_stk, use_container_width=True)
        for r in stk_data:
            with st.expander(f"Gérer {r[1]}"):
                if st.button(f"🗑️ Supprimer définitivement {r[1]}", key=f"del_p_{r[0]}"):
                    run_db("DELETE FROM produits WHERE id=?", (r[0],))
                    st.rerun()

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Suivi des Dettes")
    dettes = run_db("SELECT id, client_nom, montant_du, devise, articles, sale_ref FROM dettes", fetch=True)
    if not dettes: st.info("Aucune dette enregistrée.")
    for d in dettes:
        with st.container():
            st.warning(f"**Client: {d[1]}** | Reste : {d[2]:,.2f} {d[3]} (Ref: {d[5]})")
            ac = st.number_input(f"Paiement pour {d[1]}", 0.0, float(d[2]), key=f"p_{d[0]}")
            if st.button(f"Enregistrer le versement", key=f"b_{d[0]}"):
                if d[2]-ac <= 0.05: run_db("DELETE FROM dettes WHERE id=?", (d[0],))
                else: run_db("UPDATE dettes SET montant_du = montant_du - ? WHERE id = ?", (ac, d[0]))
                run_db("UPDATE ventes SET reste = reste - ? WHERE ref = ?", (ac, d[5]))
                st.rerun()

# --- USERS ---
elif st.session_state.page == "USERS":
    st.title("👥 Gestion des Vendeurs")
    with st.form("f_u"):
        nu = st.text_input("Identifiant")
        np = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", (nu.lower(), make_hashes(np), "VENDEUR"))
            st.rerun()
    
    users = run_db("SELECT username FROM users WHERE username!='admin'", fetch=True)
    for u in users:
        c1, c2 = st.columns([4,1])
        c1.write(f"Vendeur : **{u[0].upper()}**")
        if c2.button("🗑️", key=f"del_u_{u[0]}"):
            run_db("DELETE FROM users WHERE username=?", (u[0],))
            st.rerun()

# --- CONFIGURATION ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres")
    with st.form("f_cfg"):
        en = st.text_input("Entreprise", C_ENT)
        ad = st.text_input("Adresse", C_ADR)
        tl = st.text_input("Téléphone", C_TEL)
        tx = st.number_input("Taux (1 USD = ? CDF)", value=C_TAUX)
        ms = st.text_area("Message défilant", C_MSG)
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, taux=?, message=? WHERE id=1", (en.upper(), ad, tl, tx, ms))
            st.rerun()
    
    st.write("---")
    if os.path.exists("anash_data.db"):
        with open("anash_data.db", "rb") as file:
            st.download_button("📥 TÉLÉCHARGER LE BACKUP (.db)", file, file_name=f"erp_backup_{datetime.now().strftime('%d_%m')}.db")

# --- RAPPORT ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Historique des Ventes")
    data = run_db("SELECT date_v, ref, client_nom, total_val, devise, reste FROM ventes ORDER BY id DESC", fetch=True)
    if data:
        df = pd.DataFrame(data, columns=["Date", "Référence", "Client", "Total", "Devise", "Dette"])
        st.dataframe(df, use_container_width=True)
