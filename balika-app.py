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
# 1. CONFIGURATION SYSTÈME & STYLE (v850 - ULTIMATE EDITION)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation exhaustive du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_v850_pro.db', timeout=60) as conn:
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
# 2. INITIALISATION DES TABLES (ARCHITECTURE COMPLÈTE)
# ==============================================================================
def init_db():
    # Utilisateurs & Vendeurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        ent_id TEXT, status TEXT DEFAULT 'ACTIF', photo BLOB)""")
    
    # Configuration Application
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
        taux_global REAL, version TEXT)""")
    
    # En-tête Boutique
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT)""")
    
    # Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
        ent_id TEXT)""")
    
    # Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)""")
    
    # Dettes Clients
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        devise TEXT, ref_v TEXT, ent_id TEXT)""")

    # Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
        devise TEXT, date_d TEXT, ent_id TEXT)""")

    # NOUVEAU : Dettes Fournisseurs
    run_db("""CREATE TABLE IF NOT EXISTS dettes_fournisseurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fournisseur TEXT, montant REAL, 
        devise TEXT, motif TEXT, date_f TEXT, ent_id TEXT, status TEXT DEFAULT 'NON PAYÉ')""")

    # Données par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global, version) VALUES (1, 'BALIKA ERP', 'Bienvenue sur BALIKA ERP v850 - La gestion simplifiée pour votre succès', 2850.0, 'v850')")

init_db()

# ==============================================================================
# 3. DESIGN & MARQUEE FIXE (ORANGE & BLEU)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .fixed-marquee {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #000; color: #00FF00; height: 50px;
        z-index: 999999; display: flex; align-items: center;
        border-bottom: 2px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    marquee {{ font-size: 20px; font-weight: bold; font-family: 'Courier New'; }}
    .spacer {{ margin-top: 65px; }}
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 55px; width: 100%;
        border: 2px solid white; font-size: 16px; transition: 0.3s;
    }}
    .white-card {{
        background: white; color: black; padding: 20px; 
        border: 2px solid black; border-radius: 12px; margin-bottom: 10px;
    }}
    .invoice-box {{
        background: white; color: black; padding: 30px; 
        border: 1px dashed black; border-radius: 5px; font-family: 'Courier New', monospace;
    }}
    div[data-baseweb="input"], div[data-baseweb="select"] {{ background-color: white !important; border-radius: 10px !important; }}
    input {{ color: black !important; font-weight: bold !important; }}
    </style>
    <div class="fixed-marquee"><marquee scrollamount="8">{MARQUEE}</marquee></div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. AUTHENTIFICATION
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 CONNEXION", "🚀 CRÉER BOUTIQUE"])
    with t1:
        u_log = st.text_input("Identifiant").lower().strip()
        p_log = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU TABLEAU DE BORD"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_log,), fetch=True)
            if res:
                if res[0][3] == "PAUSE" and res[0][1] != "SUPER_ADMIN": st.error("Accès suspendu.")
                elif make_hashes(p_log) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_log, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Mot de passe incorrect.")
            else: st.error("Utilisateur inconnu.")
    with t2:
        nu = st.text_input("Nom de la Boutique").lower().strip()
        np = st.text_input("Mot de passe souhaité", type="password")
        if st.button("LANCER MA BOUTIQUE"):
            if not run_db("SELECT * FROM users WHERE username=?", (nu,), fetch=True):
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (nu, make_hashes(np), 'USER', nu))
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique) VALUES (?,?)", (nu, nu.upper()))
                st.success("Compte créé ! Connectez-vous.")
            else: st.warning("Nom déjà utilisé.")
    st.stop()

# ==============================================================================
# 5. NAVIGATION SIDEBAR
# ==============================================================================
with st.sidebar:
    u_pic = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if u_pic and u_pic[0][0]: st.image(u_pic[0][0], width=110)
    else: st.markdown("<h2 align='center'>👤</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 align='center'>{st.session_state.user.upper()}</h3>", unsafe_allow_html=True)
    st.write("---")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES CLIENTS", "🚛 DETTES FOURNISSEURS", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION"): st.session_state.auth = False; st.rerun()

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
                c2.write(f"État : {s}")
                if c3.button("ACTIVER/PAUSE", key=u):
                    ns = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (ns, u)); st.rerun()
    
    elif st.session_state.page == "SYSTÈME":
        st.header("🛠️ CONFIGURATION GLOBALE")
        with st.form("sys"):
            n_app = st.text_input("Nom App", APP_NAME)
            n_mar = st.text_area("Marquee", MARQUEE)
            n_tau = st.number_input("Taux Global", value=TX_G)
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (n_app, n_mar, n_tau))
                st.rerun()

# ==============================================================================
# 7. LOGIQUE BOUTIQUE (PRO)
# ==============================================================================
else:
    # --- MODULE STOCK ---
    if st.session_state.page == "STOCK":
        st.header("📦 MON STOCK")
        with st.form("add_p"):
            f1, f2, f3 = st.columns(3)
            dn = f1.text_input("Nom de l'article")
            sq = f2.number_input("Quantité reçue", 1)
            pv = f3.number_input("Prix de vente $")
            if st.form_submit_button("AJOUTER AU STOCK"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                       (dn.upper(), sq, pv, "USD", st.session_state.ent_id)); st.rerun()
        
        st.subheader("Modifier les produits existants")
        for pi, pd, ps, pp in run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True):
            with st.container(border=True):
                l1, l2, l3, l4 = st.columns([3,1,1,1])
                u_d = l1.text_input("Nom", pd, key=f"d_{pi}")
                u_q = l2.number_input("Qté", value=ps, key=f"q_{pi}")
                u_p = l3.number_input("Prix $", value=pp, key=f"p_{pi}")
                if l4.button("💾", key=f"b_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_d.upper(), u_q, u_p, pi)); st.rerun()

    # --- MODULE CAISSE ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 VENTE EN DIRECT")
            dev_v = st.radio("Devise :", ["USD", "CDF"], horizontal=True)
            p_map = {p[0]: (p[1], p[2]) for p in run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)}
            
            sel = st.selectbox("Sélectionner article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                if p_map[sel][1] > 0:
                    st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
                else: st.error("Stock épuisé !")

            if st.session_state.panier:
                total_c = 0.0
                det_c = []
                for a, q in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if dev_v == "USD" else p_map[a][0] * TX_G
                    total_c += pu * q
                    det_c.append({"art": a, "qty": q, "pu": pu})
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{a}**")
                    st.session_state.panier[a] = c2.number_input("Qté", 1, p_map[a][1], value=q, key=f"ca_{a}")
                    if c3.button("🗑️", key=f"rm_{a}"): del st.session_state.panier[a]; st.rerun()
                
                st.markdown(f"<div style='background:white; color:blue; padding:15px; border-radius:10px; border:2px solid blue;'><h2>TOTAL : {total_c:,.2f} {dev_v}</h2></div>", unsafe_allow_html=True)
                cl_n = st.text_input("Nom Client", "COMPTANT")
                m_rec = st.number_input("Montant Reçu", value=float(total_c))
                if st.button("✅ CONFIRMER LA VENTE"):
                    ref_v = f"FAC-{random.randint(1000,9999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref_v, cl_n.upper(), total_c, m_rec, total_c-m_rec, dev_v, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(det_c)))
                    if total_c-m_rec > 0: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cl_n.upper(), total_c-m_rec, dev_v, ref_v, st.session_state.ent_id))
                    for a, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel=stock_actuel-? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    st.session_state.last_fac = {"ref": ref_v, "tot": total_c, "dev": dev_v, "cli": cl_n.upper(), "det": det_c}; st.session_state.panier = {}; st.rerun()
        else:
            f = st.session_state.last_fac
            e = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            if st.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()
            st.markdown(f"""<div class="invoice-box"><h2 align="center">{e[0]}</h2><p align="center">{e[1]}<br>Tél: {e[2]} | RCCM: {e[3]}</p><hr><p><b>FACTURE:</b> {f['ref']}<br><b>CLIENT:</b> {f['cli']}</p><table width="100%"><tr><th>Art</th><th>Qté</th><th>Total</th></tr>{"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qty']}</td><td align='right'>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['det']])}</table><hr><h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3></div>""", unsafe_allow_html=True)
            if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    # --- MODULE DETTES CLIENTS ---
    elif st.session_state.page == "CLIENTS":
        st.header("📉 CRÉANCES CLIENTS")
        cl_d = run_db("SELECT id, client, montant, devise FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv in cl_d:
            with st.container(border=True):
                st.write(f"👤 Client : **{dc}** | Reste à payer : **{dm:,.2f} {dv}**")
                p_pay = st.number_input("Encaisser", 0.0, float(dm), key=f"p_{di}")
                if st.button("VALIDER LE PAIEMENT", key=f"b_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (p_pay, di)); st.rerun()

    # --- MODULE DETTES FOURNISSEURS ---
    elif st.session_state.page == "FOURNISSEURS":
        st.header("🚛 DETTES FOURNISSEURS")
        with st.form("add_df"):
            c1, c2, c3 = st.columns(3)
            f_nom = c1.text_input("Nom Fournisseur")
            f_mon = c2.number_input("Montant dû")
            f_dev = c3.selectbox("Devise", ["USD", "CDF"])
            f_mot = st.text_input("Motif (Ex: Achat marchandises)")
            if st.form_submit_button("ENREGISTRER LA DETTE"):
                run_db("INSERT INTO dettes_fournisseurs (fournisseur, montant, devise, motif, date_f, ent_id) VALUES (?,?,?,?,?,?)",
                       (f_nom.upper(), f_mon, f_dev, f_mot, datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id)); st.rerun()
        
        st.subheader("Mes dettes envers les fournisseurs")
        for fi, fn, fm, fd, fmo, fst in run_db("SELECT id, fournisseur, montant, devise, motif, status FROM dettes_fournisseurs WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True):
            with st.container(border=True):
                st.write(f"🏢 **{fn}** | Dette : **{fm:,.2f} {fd}** | Motif : {fmo}")
                if st.button("MARQUER COMME PAYÉ", key=f"df_{fi}"):
                    run_db("UPDATE dettes_fournisseurs SET montant = 0, status='PAYÉ' WHERE id=?", (fi,)); st.rerun()

    # --- MODULE DÉPENSES ---
    elif st.session_state.page == "DÉPENSES":
        st.header("💸 MES DÉPENSES")
        with st.form("add_dep"):
            c1, c2, c3 = st.columns(3)
            m_dep = c1.text_input("Motif dépense")
            v_dep = c2.number_input("Montant")
            d_dep = c3.selectbox("Devise ", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)",
                       (m_dep.upper(), v_dep, d_dep, datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id)); st.rerun()

    # --- MODULE RAPPORTS ---
    elif st.session_state.page == "RAPPORTS":
        st.header("📊 PERFORMANCE FINANCIÈRE")
        v_data = run_db("SELECT total, devise FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        d_data = run_db("SELECT montant, devise FROM depenses WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        t_v = sum([v[0] if v[1]=="USD" else v[0]/TX_G for v in v_data])
        t_d = sum([d[0] if d[1]=="USD" else d[0]/TX_G for d in d_data])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("RECETTES (USD)", f"{t_v:,.2f} $")
        c2.metric("DÉPENSES (USD)", f"{t_d:,.2f} $")
        c3.metric("BÉNÉFICE NET", f"{t_v - t_d:,.2f} $")

    # --- MODULE RÉGLAGES ---
    elif st.session_state.page == "RÉGLAGES":
        st.header("⚙️ PARAMÈTRES BOUTIQUE")
        e_inf = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        with st.form("up_e"):
            en = st.text_input("Nom de l'Etablissement", e_inf[0])
            ea = st.text_input("Adresse", e_inf[1])
            et = st.text_input("Téléphone", e_inf[2])
            er = st.text_input("RCCM / ID", e_inf[3])
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=? WHERE ent_id=?", (en, ea, et, er, st.session_state.ent_id)); st.rerun()
        
        up_img = st.file_uploader("Photo de profil", type=['jpg', 'png'])
        if st.button("METTRE À JOUR PHOTO"):
            if up_img: run_db("UPDATE users SET photo=? WHERE username=?", (sqlite3.Binary(up_img.getvalue()), st.session_state.user)); st.rerun()
