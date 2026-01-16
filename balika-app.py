# ==============================================================================
# BALIKA ERP v200 - VERSION COMPLÈTE OPTIMISÉE MOBILE
# TOUS DROITS RÉSERVÉS - 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import time
import base64
from PIL import Image

# ------------------------------------------------------------------------------
# 1. INITIALISATION DE LA CONFIGURATION DE PAGE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v200",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏢"
)

# ------------------------------------------------------------------------------
# 2. GESTION DU SESSION STATE
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'ent_id' not in st.session_state:
    st.session_state.ent_id = "SYSTEM"
if 'page' not in st.session_state:
    st.session_state.page = "ACCUEIL"
if 'panier' not in st.session_state:
    st.session_state.panier = {}
if 'last_fac' not in st.session_state:
    st.session_state.last_fac = None
if 'format_fac' not in st.session_state:
    st.session_state.format_fac = "80mm"

# ------------------------------------------------------------------------------
# 3. MOTEUR DE BASE DE DONNÉES
# ------------------------------------------------------------------------------
def get_connection():
    return sqlite3.connect('balika_v200_master.db', timeout=30)

def run_db(query, params=(), fetch=False):
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        if fetch:
            return cursor.fetchall()
        return None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []
    finally:
        conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 4. CRÉATION DES TABLES
# ------------------------------------------------------------------------------
def init_db():
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
                photo BLOB, full_name TEXT, telephone TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, 
                taux REAL DEFAULT 2850.0, message TEXT DEFAULT 'BIENVENUE', 
                color_m TEXT DEFAULT '#00FF00', logo BLOB)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, 
                vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT)""")

    # Admin par défaut (v199+ requirements)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP', 2850.0, 'BIENVENUE SUR BALIKA ERP'))

init_db()

# ------------------------------------------------------------------------------
# 5. CHARGEMENT CONFIGURATION
# ------------------------------------------------------------------------------
ENT_ID = st.session_state.ent_id
res_cfg = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel, logo FROM config WHERE ent_id=?", (ENT_ID,), fetch=True)
if res_cfg:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_LOGO = res_cfg[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_LOGO = ("BOUTIQUE", "Bienvenue", "#00FF00", 2850.0, "Adresse", "000", None)

# ------------------------------------------------------------------------------
# 6. CSS & DESIGN (MOBILE FIRST)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap');
    
    /* Optimisation Mobile */
    [data-testid="stSidebar"] {{ width: 250px !important; }}
    .stApp {{ background-color: #f8f9fa; }}
    
    /* Marquee */
    .fixed-header {{
        position: fixed; top: 0; left: 0; width: 100%; height: 40px;
        background: #000; z-index: 9999; border-bottom: 2px solid {C_COLOR};
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: scroll 15s linear infinite;
        color: {C_COLOR}; font-size: 18px; font-weight: bold;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Montre v199+ */
    .watch-box {{
        background: #000; border: 3px solid #0056b3; border-radius: 15px;
        padding: 20px; text-align: center; margin: 10px auto; max-width: 300px;
    }}
    .w-time {{ font-family: 'Orbitron', sans-serif; font-size: 45px; color: #0056b3; margin: 0; }}
    .w-date {{ color: #fff; font-size: 14px; text-transform: uppercase; }}

    /* Boutique Boutons */
    .stButton>button {{
        background: #0056b3 !important; color: white !important;
        border-radius: 8px; font-weight: bold; width: 100%; border: none;
    }}
    
    /* Cadre Total Panier */
    .total-frame {{
        border: 3px solid #0056b3; background: #e7f1ff; padding: 15px;
        border-radius: 10px; color: #000; font-size: 28px;
        font-weight: bold; text-align: center; margin: 15px 0;
    }}

    /* Facture 80mm */
    .invoice-80mm {{ 
        width: 100%; max-width: 300px; margin: auto; padding: 10px; 
        background: white; font-family: monospace; font-size: 12px;
    }}
    
    @media print {{ .no-print, [data-testid="stSidebar"] {{ display: none !important; }} }}
    </style>
    
    <div class="fixed-header">
        <div class="marquee-text">{C_MSG} ● {C_NOM} ● Taux: 1$ = {C_TX} CDF</div>
    </div>
    <div style="height: 50px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. ÉCRAN DE CONNEXION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center;'>🔐 CONNEXION</h2>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.auth = True
                st.session_state.user = u
                st.session_state.role = res[0][1]
                st.session_state.ent_id = res[0][2]
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop()

# ------------------------------------------------------------------------------
# 8. NAVIGATION
# ------------------------------------------------------------------------------
with st.sidebar:
    # Photo de profil
    u_data = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if u_data and u_data[0][0]:
        st.image(u_data[0][0], width=100)
    else:
        st.markdown("👤")
        
    st.write(f"**{st.session_state.user.upper()}** ({st.session_state.role})")
    st.write("---")
    
    menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    if st.session_state.role == "ADMIN":
        menu += ["📦 STOCK", "👥 VENDEURS", "💸 DÉPENSES", "📊 RAPPORTS", "⚙️ RÉGLAGES"]
    menu += ["👤 PROFIL", "🚪 QUITTER"]

    for item in menu:
        if st.button(item, use_container_width=True):
            if item == "🚪 QUITTER":
                st.session_state.auth = False
                st.rerun()
            st.session_state.page = item.split()[-1]
            st.rerun()

# ------------------------------------------------------------------------------
# 9. PAGES
# ------------------------------------------------------------------------------

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<h3 style='text-align: center;'>{C_NOM}</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="watch-box">
            <p class="w-time">{datetime.now().strftime('%H:%M')}</p>
            <p class="w-date">{datetime.now().strftime('%d %B %Y')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.role == "ADMIN":
        c1, c2 = st.columns(2)
        v_tot = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
        d_tot = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
        c1.metric("Ventes", f"{v_tot:,.1f}$")
        c2.metric("Dettes", f"{d_tot:,.1f}$")

# --- CAISSE ---
elif st.session_state.page == "CAISSE":
    if st.session_state.last_fac:
        # Affichage Facture
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac': None}))
        f = st.session_state.last_fac
        html = f"""<div class="invoice-80mm">
            <center><b>{C_NOM}</b><br>{C_ADR}<br>{C_TEL}<hr>
            FACTURE: {f['ref']}<br>{f['date']}<hr></center>
            {"".join([f"{i['art']} x{i['qte']} : {i['st']:,.0f}<br>" for i in f['items']])}
            <hr><b>TOTAL: {f['tot']:,.1f} {f['dev']}</b><br>
            Payé: {f['pay']:,.1f}<br>Reste: {f['tot']-f['pay']:,.1f}
        </div>"""
        st.markdown(html, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.subheader("🛒 CAISSE")
        devise_v = st.radio("Devise", ["USD", "CDF"], horizontal=True)
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
        p_list = {r[0]: r for r in prods}
        
        sel = st.selectbox("Article", ["---"] + list(p_list.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            
        total = 0.0
        items_v = []
        for art, qte in list(st.session_state.panier.items()):
            p_data = p_list[art]
            # Conversion prix
            px = p_data[1]
            if p_data[3] == "USD" and devise_v == "CDF": px *= C_TX
            if p_data[3] == "CDF" and devise_v == "USD": px /= C_TX
            
            stot = px * qte
            total += stot
            items_v.append({'art': art, 'qte': qte, 'st': stot})
            
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(art)
            st.session_state.panier[art] = c2.number_input("Qté", 1, p_data[2], qte, key=f"q_{art}")
            if c3.button("🗑️", key=f"d_{art}"):
                del st.session_state.panier[art]
                st.rerun()

        st.markdown(f'<div class="total-frame">{total:,.1f} {devise_v}</div>', unsafe_allow_html=True)
        cl_nom = st.text_input("Client", "COMPTANT")
        cl_pay = st.number_input("Montant Reçu", 0.0, value=float(total))
        
        if st.button("VALIDER LA VENTE"):
            ref = f"V{random.randint(100,999)}"
            dt = datetime.now().strftime("%d/%m/%Y %H:%M")
            reste = total - cl_pay
            
            # Save Vente
            run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (ref, cl_nom, total, cl_pay, reste, devise_v, dt, st.session_state.user, ENT_ID, json.dumps(items_v)))
            
            # Save Dette
            if reste > 0.1:
                run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)",
                       (cl_nom, reste, devise_v, ref, ENT_ID, json.dumps([{'d':dt, 'p':cl_pay}])))
            
            # Update Stock
            for i in items_v:
                run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
            
            st.session_state.last_fac = {'ref':ref, 'date':dt, 'items':items_v, 'tot':total, 'pay':cl_pay, 'dev':devise_v}
            st.session_state.panier = {}
            st.rerun()

# --- VENDEURS ---
elif st.session_state.page == "VENDEURS":
    st.subheader("👥 GESTION VENDEURS")
    with st.expander("Ajouter un vendeur"):
        nv_u = st.text_input("Nom d'utilisateur").lower()
        nv_p = st.text_input("Mot de passe", type="password")
        if st.button("Créer"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
                   (nv_u, make_hashes(nv_p), "VENDEUR", ENT_ID))
            st.success("Vendeur ajouté")
    
    vendeurs = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for v in vendeurs:
        c1, c2 = st.columns([3, 1])
        c1.write(v[0])
        if c2.button("Supprimer", key=f"del_{v[0]}"):
            run_db("DELETE FROM users WHERE username=?", (v[0],))
            st.rerun()

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.subheader("📦 STOCK")
    with st.expander("Ajouter Produit"):
        n_d = st.text_input("Désignation")
        n_p = st.number_input("Prix", 0.0)
        n_v = st.selectbox("Devise", ["USD", "CDF"])
        n_q = st.number_input("Qté Initiale", 0)
        if st.button("Enregistrer"):
            run_db("INSERT INTO produits (designation, prix_vente, devise, stock_actuel, ent_id) VALUES (?,?,?,?,?)",
                   (n_d.upper(), n_p, n_v, n_q, ENT_ID))
            st.rerun()
            
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for p_id, p_des, p_st, p_px, p_dv in prods:
        with st.container(border=True):
            st.write(f"**{p_des}** | Stock: {p_st}")
            new_px = st.number_input("Nouveau Prix", value=float(p_px), key=f"p_{p_id}")
            c1, c2 = st.columns(2)
            if c1.button("Sauver", key=f"s_{p_id}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, p_id))
            if c2.button("Supprimer", key=f"d_{p_id}"):
                run_db("DELETE FROM produits WHERE id=?", (p_id,))
                st.rerun()

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.subheader("📉 RECOUVREMENT")
    dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)
    for d_id, d_cl, d_mt, d_dv, d_rf, d_hi in dettes:
        with st.expander(f"{d_cl} : {d_mt:,.1f} {d_dv}"):
            p_aco = st.number_input("Acompte", 0.0, float(d_mt), key=f"aco_{d_id}")
            if st.button("Payer Acompte", key=f"btn_aco_{d_id}"):
                n_mt = d_mt - p_aco
                hist = json.loads(d_hi)
                hist.append({'d': datetime.now().strftime("%d/%m"), 'p': p_aco})
                
                if n_mt <= 0.1:
                    run_db("DELETE FROM dettes WHERE id=?", (d_id,))
                else:
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_mt, json.dumps(hist), d_id))
                
                run_db("UPDATE ventes SET paye = paye + ?, reste = reste - ? WHERE ref=? AND ent_id=?", (p_aco, p_aco, d_rf, ENT_ID))
                st.rerun()

# --- RÉGLAGES ---
elif st.session_state.page == "RÉGLAGES":
    st.subheader("⚙️ PARAMÈTRES")
    with st.form("cfg"):
        n_nom = st.text_input("Nom Entreprise", C_NOM)
        n_adr = st.text_input("Adresse", C_ADR)
        n_tel = st.text_input("Téléphone", C_TEL)
        n_tx = st.number_input("Taux (CDF/$)", value=C_TX)
        n_msg = st.text_area("Message Défilant", C_MSG)
        n_col = st.color_picker("Couleur", C_COLOR)
        if st.form_submit_button("SAUVER"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, color_m=? WHERE ent_id=?",
                   (n_nom.upper(), n_adr, n_tel, n_tx, n_msg, n_col, ENT_ID))
            st.rerun()

# --- PROFIL ---
elif st.session_state.page == "PROFIL":
    st.subheader("👤 MON PROFIL")
    with st.form("prof"):
        pic = st.file_uploader("Photo de profil", type=['jpg', 'png'])
        n_pass = st.text_input("Nouveau mot de passe", type="password")
        if st.form_submit_button("MODIFIER"):
            if n_pass:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pass), st.session_state.user))
            if pic:
                img_byte = pic.read()
                run_db("UPDATE users SET photo=? WHERE username=?", (img_byte, st.session_state.user))
            st.success("Profil mis à jour")
            st.rerun()

# --- RAPPORTS ---
elif st.session_state.page == "RAPPORTS":
    st.subheader("📊 RAPPORT")
    v_data = run_db("SELECT date_v, ref, client, total, paye, vendeur FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    df = pd.DataFrame(v_data, columns=["Date", "Ref", "Client", "Total", "Payé", "Vendeur"])
    st.dataframe(df, use_container_width=True)
    if st.button("🖨️ IMPRIMER RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FIN DU CODE
# ------------------------------------------------------------------------------
