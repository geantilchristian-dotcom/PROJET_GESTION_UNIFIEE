import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v265 - ARCHITECTURE MULTI-ENTREPRISE)
# ==========================================
st.set_page_config(page_title="BALIKA ERP CLOUD", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'panier' not in st.session_state: st.session_state.panier = {} 
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'last_fac' not in st.session_state: st.session_state.last_fac = None
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'ent_id' not in st.session_state: st.session_state.ent_id = "" # L'ID de l'entreprise (Propriétaire)

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Système : {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 2. INITIALISATION BASE DE DONNÉES
# ==========================================
def init_db():
    # Table des utilisateurs (Lien vers une entreprise via ent_id)
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        role TEXT, 
        ent_id TEXT)""")
    
    # Table des produits (Isolés par ent_id)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        designation TEXT, 
        stock_actuel INTEGER, 
        prix_vente REAL, 
        devise TEXT, 
        ent_id TEXT)""")
    
    # Table des ventes (Isolés par ent_id)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        ref TEXT, 
        client TEXT, 
        total REAL, 
        paye REAL, 
        reste REAL, 
        devise TEXT, 
        date_v TEXT, 
        vendeur TEXT, 
        ent_id TEXT)""")
    
    # Table des dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        client TEXT, 
        montant REAL, 
        devise TEXT, 
        ref_v TEXT, 
        ent_id TEXT)""")
    
    # Table de configuration par Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
        ent_id TEXT PRIMARY KEY, 
        nom_ent TEXT, 
        adresse TEXT, 
        tel TEXT, 
        taux REAL, 
        message TEXT)""")

    # Création du Super Admin si inexistant
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM')", (make_hashes("admin123"),))

init_db()

# ==========================================
# 3. CHARGEMENT CONFIGURATION DYNAMIQUE
# ==========================================
if st.session_state.auth:
    res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if res_cfg:
        C_NOM, C_MSG, C_TAUX, C_ADR, C_TEL = res_cfg[0]
    else:
        C_NOM, C_MSG, C_TAUX, C_ADR, C_TEL = "BALIKA ERP", "Bienvenue", 2850.0, "Adresse", "000"
else:
    C_NOM, C_MSG = "BALIKA CLOUD", "Gérez votre business comme un pro"

# ==========================================
# 4. DESIGN & STYLE (ANTI-DARK MODE IPHONE)
# ==========================================
st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #FFFFFF !important; color: #000000 !important; }}
    .stButton>button {{ background: linear-gradient(135deg, #FF8C00, #FF4500) !important; color: white !important; border-radius: 12px; height: 55px; font-weight: bold; border: none; }}
    input, select, textarea {{ background-color: #F0F2F6 !important; color: #000 !important; border: 2px solid #FF8C00 !important; border-radius: 8px !important; }}
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 12px 0; position: fixed; top: 0; z-index: 9999; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; font-size: 18px; font-weight: bold; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .total-frame {{ border: 4px solid #FF8C00; background: #FFF3E0; padding: 20px; border-radius: 15px; text-align: center; font-size: 28px; color: #E65100; font-weight: bold; }}
    h1, h2, h3, p, span, label, b {{ color: #000000 !important; }}
    @media print {{ .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }} }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🚀 {C_NOM} : {C_MSG}</div></div>
    <div style="margin-top: 70px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. ÉCRAN DE LOGIN & INSCRIPTION ENTREPRISE
# ==========================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:#FF8C00;'>{C_NOM}</h1>", unsafe_allow_html=True)
    tab_log, tab_reg = st.tabs(["🔐 CONNEXION", "🏢 CRÉER MON ESPACE ENTREPRISE"])
    
    with tab_log:
        u_log = st.text_input("Utilisateur").lower().strip()
        p_log = st.text_input("Mot de passe", type="password").strip()
        if st.button("SE CONNECTER AU SYSTÈME"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_log,), fetch=True)
            if res and make_hashes(p_log) == res[0][0]:
                st.session_state.auth = True
                st.session_state.user = u_log
                st.session_state.role = res[0][1]
                st.session_state.ent_id = res[0][2]
                st.rerun()
            else: st.error("Identifiants incorrects.")

    with tab_reg:
        st.subheader("Ouvrez votre propre instance ERP")
        new_ent = st.text_input("Nom de votre Entreprise").upper().strip()
        new_adm = st.text_input("Nom d'utilisateur Admin").lower().strip()
        new_pwd = st.text_input("Mot de passe Admin", type="password").strip()
        if st.button("LANCER MON ENTREPRISE"):
            if new_ent and new_adm and new_pwd:
                if not run_db("SELECT * FROM users WHERE username=?", (new_adm,), fetch=True):
                    ent_token = f"ENT-{random.randint(10000, 99999)}"
                    run_db("INSERT INTO users VALUES (?,?, 'ADMIN', ?)", (new_adm, make_hashes(new_pwd), ent_token))
                    run_db("INSERT INTO config VALUES (?,?, 'Adresse', '000', 2850.0, 'Bienvenue')", (ent_token, new_ent))
                    st.success(f"Félicitations ! Connectez-vous avec {new_adm}")
                else: st.warning("Cet utilisateur existe déjà.")
    st.stop()

# ==========================================
# 6. NAVIGATION ET LOGIQUE DES RÔLES
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}\n**Rôle : {st.session_state.role}**")
    st.write("---")
    
    nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    if st.session_state.role == "ADMIN":
        nav += ["📦 STOCK", "👥 MES VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    
    for item in nav:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION"):
        st.session_state.auth = False
        st.rerun()

# Variables de session simplifiées
USER = st.session_state.user
ENT_ID = st.session_state.ent_id
ROLE = st.session_state.role

# ==========================================
# 7. PAGES
# ==========================================

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.title(f"Tableau de bord - {C_NOM}")
    v_data = run_db("SELECT total, devise FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    if v_data:
        df = pd.DataFrame(v_data, columns=["T", "D"])
        c1, c2 = st.columns(2)
        c1.metric("Ventes en USD", f"{df[df['D']=='USD']['T'].sum():,.2f} $")
        c2.metric("Ventes en CDF", f"{df[df['D']=='CDF']['T'].sum():,.0f} FC")

# --- CAISSE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Terminal de Vente")
        devise_v = st.radio("Vendre en :", ["USD", "CDF"], horizontal=True)
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
        
        sel = st.selectbox("Rechercher un article", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            st.write("---")
            total_v = 0.0; rows = []
            for art, qte in list(st.session_state.panier.items()):
                p_orig = p_map[art]['p']
                # Conversion dynamique basée sur le taux de l'entreprise
                if p_map[art]['d'] == "USD" and devise_v == "CDF": p_final = p_orig * C_TAUX
                elif p_map[art]['d'] == "CDF" and devise_v == "USD": p_final = p_orig / C_TAUX
                else: p_final = p_orig
                
                st_val = p_final * qte
                total_v += st_val
                rows.append({'art': art, 'qte': qte, 'st': st_val})
                
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_map[art]['s'], value=qte, key=f"q_{art}")
                if c3.button("🗑️", key=f"rm_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()
            
            st.markdown(f'<div class="total-frame">NET À PAYER : {total_v:,.2f} {devise_v}</div>', unsafe_allow_html=True)
            
            client = st.text_input("NOM DU CLIENT").upper()
            acompte = st.number_input("VERSEMENT", 0.0)
            
            if st.button("✅ FINALISER LA VENTE") and client:
                ref_f = f"FAC-{random.randint(1000,9999)}"
                now = datetime.now().strftime("%d/%m/%Y %H:%M")
                # Enregistrement
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?)", 
                       (ref_f, client, total_v, acompte, total_v-acompte, devise_v, now, USER, ENT_ID))
                if total_v - acompte > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?)", (client, total_v-acompte, devise_v, ref_f, ENT_ID))
                for r in rows:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (r['qte'], r['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": ref_f, "cl": client, "tot": total_v, "pay": acompte, "rest": total_v-acompte, "dev": devise_v, "items": rows, "date": now}
                st.session_state.panier = {}
                st.rerun()
    else:
        f = st.session_state.last_fac
        st.markdown(f"""
        <div style="background:white; padding:20px; border:1px solid #000; color:black; font-family:monospace; width:350px; margin:auto;">
            <h2 align="center">{C_NOM}</h2>
            <p align="center">{C_ADR}<br>Tél: {C_TEL}</p>
            <hr>
            <p>Date: {f['date']}<br>Facture: {f['ref']}<br>Client: {f['cl']}<br>Vendeur: {USER.upper()}</p>
            <hr>
            <table style="width:100%">
                {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Payé: {f['pay']}<br>Reste: {f['rest']}</p>
            <hr>
            <p align="center">Merci de votre confiance !</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ NOUVELLE VENTE"):
            st.session_state.last_fac = None
            st.rerun()

# --- STOCK (ADMIN ONLY) ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion des Produits")
    with st.form("add_p"):
        c1, c2, c3 = st.columns([3, 1, 1])
        n_p = c1.text_input("Désignation")
        q_p = c2.number_input("Quantité", 1)
        p_p = c3.number_input("Prix de Vente")
        d_p = st.selectbox("Devise de l'article", ["USD", "CDF"])
        if st.form_submit_button("📥 AJOUTER AU STOCK"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                   (n_p.upper(), q_p, p_p, d_p, ENT_ID))
            st.rerun()
            
    st.write("---")
    prods_list = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for p_id, p_nom, p_stock, p_prix, p_dev in prods_list:
        with st.expander(f"{p_nom} - Stock: {p_stock}"):
            new_px = st.number_input("Modifier Prix", value=float(p_prix), key=f"px_{p_id}")
            if st.button("Mettre à jour", key=f"up_{p_id}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, p_id))
                st.rerun()
            if st.button("🗑️ Supprimer l'article", key=f"del_{p_id}"):
                run_db("DELETE FROM produits WHERE id=?", (p_id,))
                st.rerun()

# --- MES VENDEURS (L'ESPACE POUR CRÉER LES COMPTES VENDEURS) ---
elif st.session_state.page == "VENDEURS":
    st.title("👥 Gestion de mon Personnel")
    st.info("Ici, vous créez les comptes pour vos employés. Ils ne pourront que vendre.")
    
    with st.form("v_add"):
        v_u = st.text_input("Identifiant Vendeur").lower().strip()
        v_p = st.text_input("Mot de passe", type="password").strip()
        if st.form_submit_button("✅ CRÉER LE COMPTE VENDEUR"):
            if not run_db("SELECT * FROM users WHERE username=?", (v_u,), fetch=True):
                run_db("INSERT INTO users VALUES (?,?, 'VENDEUR', ?)", (v_u, make_hashes(v_p), ENT_ID))
                st.success("Compte vendeur actif !")
            else: st.error("Ce nom est déjà pris.")
            
    st.write("---")
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        c1, c2 = st.columns([4, 1])
        c1.write(f"👤 Vendeur : **{s[0].upper()}**")
        if c2.button("Supprimer", key=s[0]):
            run_db("DELETE FROM users WHERE username=?", (s[0],))
            st.rerun()

# --- CONFIG ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres de l'Entreprise")
    with st.form("cfg_f"):
        en = st.text_input("Nom de l'Etablissement", C_NOM)
        ad = st.text_input("Adresse Physique", C_ADR)
        tl = st.text_input("Téléphone", C_TEL)
        tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TAUX)
        ms = st.text_area("Message de la barre défilante", C_MSG)
        if st.form_submit_button("💾 SAUVER LES MODIFICATIONS"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", 
                   (en.upper(), ad, tl, tx, ms, ENT_ID))
            st.rerun()
