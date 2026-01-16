import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v266 - SaaS EDITION)
# ==========================================
st.set_page_config(page_title="BALIKA ERP CLOUD v266", layout="wide", initial_sidebar_state="collapsed")

# Initialisation des variables de session
if 'auth' not in st.session_state: st.session_state.auth = False
if 'panier' not in st.session_state: st.session_state.panier = {} 
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'last_fac' not in st.session_state: st.session_state.last_fac = None
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'ent_id' not in st.session_state: st.session_state.ent_id = ""

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v2.db', timeout=60) as conn:
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
    run_db("""CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT)""")
    run_db("""CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)""")
    run_db("""CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    run_db("""CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT)""")
    run_db("""CREATE TABLE IF NOT EXISTS config (ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, taux REAL, message TEXT)""")

    # Admin global de secours (Toujours admin/admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM')", (make_hashes("admin123"),))
        run_db("INSERT INTO config VALUES ('SYSTEM', 'BALIKA SYSTEM', 'Cloud', '000', 2850.0, 'Bienvenue')", ())

init_db()

# ==========================================
# 3. CHARGEMENT CONFIGURATION
# ==========================================
if st.session_state.auth:
    res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if res_cfg: C_NOM, C_MSG, C_TAUX, C_ADR, C_TEL = res_cfg[0]
    else: C_NOM, C_MSG, C_TAUX, C_ADR, C_TEL = "BALIKA ERP", "Bienvenue", 2850.0, "Adresse", "000"
else:
    C_NOM, C_MSG = "BALIKA CLOUD", "Gérez votre business partout dans le monde"

# ==========================================
# 4. DESIGN MOBILE & ANTI-DARK MODE
# ==========================================
st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #FFFFFF !important; color: #000000 !important; }}
    .stButton>button {{ background: linear-gradient(135deg, #FF8C00, #FF4500) !important; color: white !important; border-radius: 12px; height: 50px; font-weight: bold; border: none; width: 100%; }}
    input, select, textarea {{ background-color: #F8F9FA !important; color: #000 !important; border: 2px solid #FF8C00 !important; }}
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 12px 0; position: fixed; top: 0; z-index: 9999; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 20s linear infinite; font-size: 18px; font-weight: bold; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .total-frame {{ border: 3px solid #FF8C00; background: #FFF3E0; padding: 15px; border-radius: 10px; text-align: center; font-size: 24px; color: #E65100; font-weight: bold; }}
    h1, h2, h3, label, p, span {{ color: #000 !important; }}
    @media print {{ .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }} }}
    </style>
    <div class="marquee-container"><div class="marquee-text">✨ {C_NOM} : {C_MSG}</div></div>
    <div style="margin-top: 70px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. LOGIN / INSCRIPTION D'ENTREPRISE
# ==========================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center;'>{C_NOM}</h1>", unsafe_allow_html=True)
    tab_l, tab_r = st.tabs(["🔑 CONNEXION", "🚀 CRÉER MON ENTREPRISE"])
    
    with tab_l:
        u_in = st.text_input("Identifiant").lower().strip()
        p_in = st.text_input("Mot de passe", type="password").strip()
        if st.button("ACCÉDER À MON ESPACE"):
            user_data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
            if user_data and make_hashes(p_in) == user_data[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role, st.session_state.ent_id = True, u_in, user_data[0][1], user_data[0][2]
                st.rerun()
            else: st.error("Identifiants incorrects.")

    with tab_r:
        st.subheader("Enregistrez votre société")
        r_ent = st.text_input("Nom de l'Etablissement (Ex: BOUTIQUE ANASH)").upper().strip()
        r_usr = st.text_input("Votre Identifiant Admin").lower().strip()
        r_pwd = st.text_input("Votre Mot de passe", type="password").strip()
        if st.button("ACTIVER MON COMPTE ERP"):
            if r_ent and r_usr and r_pwd:
                if not run_db("SELECT * FROM users WHERE username=?", (r_usr,), fetch=True):
                    new_id = f"ENT-{random.randint(1000, 9999)}"
                    run_db("INSERT INTO users VALUES (?,?, 'ADMIN', ?)", (r_usr, make_hashes(r_pwd), new_id))
                    run_db("INSERT INTO config VALUES (?,?, 'Mon Adresse', '000', 2850.0, 'Bienvenue chez nous')", (new_id, r_ent))
                    st.success("Succès ! Connectez-vous maintenant.")
                else: st.error("Cet utilisateur existe déjà.")
    st.stop()

# ==========================================
# 6. VARIABLES DE SESSION & NAVIGATION
# ==========================================
ENT_ID = st.session_state.ent_id
ROLE = st.session_state.role
USER = st.session_state.user

with st.sidebar:
    st.markdown(f"### 👤 {USER.upper()}\n**ENT: {C_NOM}**")
    st.write("---")
    menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    if ROLE == "ADMIN":
        menu += ["📦 STOCK", "👥 MES VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER"):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 7. LOGIQUE DES PAGES (FILTRÉ PAR ENT_ID)
# ==========================================

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.title(f"Tableau de bord - {C_NOM}")
    stats = run_db("SELECT total, devise FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    if stats:
        df = pd.DataFrame(stats, columns=["Total", "Devise"])
        st.metric("Ventes USD", f"{df[df['Devise']=='USD']['Total'].sum():,.2f} $")
        st.metric("Ventes CDF", f"{df[df['Devise']=='CDF']['Total'].sum():,.0f} FC")

# --- CAISSE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse")
        v_dev = st.radio("Devise de vente", ["USD", "CDF"], horizontal=True)
        
        # Charger uniquement les produits de CETTE entreprise
        items = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        i_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in items}
        
        choix = st.selectbox("Article", ["---"] + list(i_map.keys()))
        if st.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            v_total = 0.0; v_rows = []
            for art, qte in list(st.session_state.panier.items()):
                p_base = i_map[art]['p']
                if i_map[art]['d'] == "USD" and v_dev == "CDF": p_unit = p_base * C_TAUX
                elif i_map[art]['d'] == "CDF" and v_dev == "USD": p_unit = p_base / C_TAUX
                else: p_unit = p_base
                
                v_total += (p_unit * qte)
                v_rows.append({'art': art, 'qte': qte, 'st': p_unit*qte})
                
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, i_map[art]['s'], value=qte, key=f"v_{art}")
                if c3.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-frame">NET À PAYER : {v_total:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            cl_nom = st.text_input("NOM DU CLIENT").upper()
            cl_pay = st.number_input("ACOMPTE", 0.0)
            
            if st.button("✅ VALIDER LA VENTE") and cl_nom:
                v_ref = f"FAC-{random.randint(100,999)}"
                v_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (v_ref, cl_nom, v_total, cl_pay, v_total-cl_pay, v_dev, v_now, USER, ENT_ID, str(v_rows)))
                if v_total-cl_pay > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?)", (cl_nom, v_total-cl_pay, v_dev, v_ref, ENT_ID))
                for r in v_rows:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (r['qte'], r['art'], ENT_ID))
                st.session_state.last_fac = {"ref": v_ref, "cl": cl_nom, "tot": v_total, "pay": cl_pay, "dev": v_dev, "rows": v_rows, "date": v_now}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.markdown(f"""
        <div style="border:1px solid #000; padding:15px; background:white; color:black; font-family:monospace; width:300px; margin:auto;">
            <h3 align="center">{C_NOM}</h3>
            <p align="center">{C_ADR}<br>Vendeur: {USER.upper()}</p><hr>
            <p>Facture: {f['ref']}<br>Client: {f['cl']}</p><hr>
            <table style="width:100%">
                {"".join([f"<tr><td>{i['art']}</td><td>x{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['rows']])}
            </table><hr>
            <h4 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h4>
        </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        if st.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()

# --- MES VENDEURS (GESTION DU PERSONNEL PAR L'ADMIN) ---
elif st.session_state.page == "VENDEURS":
    st.title("👥 Mes Comptes Vendeurs")
    st.info("Créez ici des accès limités pour votre personnel.")
    with st.form("new_v"):
        v_user = st.text_input("Identifiant Vendeur").lower().strip()
        v_pass = st.text_input("Mot de passe", type="password").strip()
        if st.form_submit_button("ACTIVER LE COMPTE"):
            if not run_db("SELECT * FROM users WHERE username=?", (v_user,), fetch=True):
                run_db("INSERT INTO users VALUES (?,?, 'VENDEUR', ?)", (v_user, make_hashes(v_pass), ENT_ID))
                st.success(f"Compte {v_user} créé pour votre entreprise.")
            else: st.error("Ce nom est déjà utilisé.")
    
    st.write("---")
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        c1, c2 = st.columns([3, 1])
        c1.write(f"👤 **{s[0].upper()}** (Vendeur)")
        if c2.button("Supprimer", key=s[0]):
            run_db("DELETE FROM users WHERE username=?", (s[0],))
            st.rerun()

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Inventaire")
    with st.form("add"):
        n = st.text_input("Nom de l'article")
        q = st.number_input("Quantité", 1)
        p = st.number_input("Prix")
        d = st.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("ENREGISTRER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                   (n.upper(), q, p, d, ENT_ID)); st.rerun()
    for r in run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True):
        st.write(f"**{r[1]}** - Stock: {r[2]} - Prix: {r[3]} {r[4]}")
        if st.button(f"🗑️ Retirer {r[1]}", key=f"del_{r[0]}"):
            run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

# --- CONFIG ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres Société")
    with st.form("cfg"):
        nom = st.text_input("Nom Entreprise", C_NOM)
        adr = st.text_input("Adresse", C_ADR)
        tel = st.text_input("Téléphone", C_TEL)
        tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TAUX)
        msg = st.text_area("Message défilant", C_MSG)
        if st.form_submit_button("SAUVER"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", 
                   (nom.upper(), adr, tel, tx, msg, ENT_ID)); st.rerun()
