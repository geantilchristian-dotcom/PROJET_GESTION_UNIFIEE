import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & STYLE (v950 - INTÉGRALE)
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP ULTIMATE", layout="wide", initial_sidebar_state="collapsed")

# Initialisation exhaustive du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm", 'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_final_v950.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES (AUCUNE LIGNE SUPPRIMÉE)
# ==============================================================================
def init_db():
    # Utilisateurs & Profils
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, status TEXT DEFAULT 'ACTIF', photo BLOB)")
    # Config Système
    run_db("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)")
    # En-tête Boutique
    run_db("CREATE TABLE IF NOT EXISTS ent_infos (ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, rccm TEXT)")
    # Produits & Stock
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    # Ventes & Historique
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)")
    # Dettes Clients (Paiement échelonné)
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT)")
    # Dépenses
    run_db("CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, devise TEXT, date_d TEXT, ent_id TEXT)")
    # Dettes Fournisseurs
    run_db("CREATE TABLE IF NOT EXISTS dettes_fournisseurs (id INTEGER PRIMARY KEY AUTOINCREMENT, fournisseur TEXT, montant REAL, devise TEXT, motif TEXT, date_f TEXT, ent_id TEXT, status TEXT DEFAULT 'NON PAYÉ')")

    # Admin par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
    # Config par défaut
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global) VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR BALIKA ERP v950 - TOUTES FONCTIONS ACTIVES', 2850.0)")

init_db()

# ==============================================================================
# 3. DESIGN & MARQUEE FIXE (CSS PRIORITAIRE)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .fixed-header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 55px;
        z-index: 999999; display: flex; align-items: center;
        border-bottom: 2px solid white;
    }}
    marquee {{ font-size: 22px; font-weight: bold; font-family: 'Courier New'; padding-top: 10px; }}
    .spacer {{ margin-top: 70px; }}
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 50px; width: 100%;
        border: 2px solid white;
    }}
    .fac-80mm {{ background: white; color: black; padding: 10px; width: 300px; margin: auto; font-family: 'Courier New'; border: 1px solid black; }}
    .fac-a4 {{ background: white; color: black; padding: 40px; width: 90%; margin: auto; border: 1px solid #ccc; font-family: Arial; }}
    div[data-baseweb="input"] {{ background: white !important; border-radius: 8px !important; }}
    input {{ color: black !important; font-weight: bold !important; }}
    </style>
    <div class="fixed-header"><marquee scrollamount="10">{MARQUEE}</marquee></div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

def get_entete():
    res = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    return res[0] if res else (st.session_state.ent_id.upper(), "Adresse non définie", "0000", "RCCM-000")

# ==============================================================================
# 4. AUTHENTIFICATION
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 CONNEXION", "🚀 CRÉER BOUTIQUE"])
    with t1:
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU SYSTÈME"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                if res[0][3] == "PAUSE": st.error("Compte suspendu.")
                else:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
    with t2:
        nu = st.text_input("Nom de la Boutique").lower().strip()
        np = st.text_input("Nouveau Pass", type="password")
        if st.button("LANCER MA BOUTIQUE"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (nu, make_hashes(np), 'USER', nu))
            run_db("INSERT INTO ent_infos (ent_id, nom_boutique) VALUES (?,?)", (nu, nu.upper()))
            st.success("Compte créé !")
    st.stop()

# ==============================================================================
# 5. SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    u_pic = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if u_pic and u_pic[0][0]: st.image(u_pic[0][0], width=110)
    else: st.markdown("<h1 align='center'>👤</h1>", unsafe_allow_html=True)
    st.write(f"**Session: {st.session_state.user.upper()}**")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME"]
    elif st.session_state.role == "VENDEUR":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES CLIENTS"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES CLIENTS", "🚛 FOURNISSEURS", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    if st.button("🚪 DÉCONNEXION"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. LOGIQUE BOUTIQUE (COMPLÈTE)
# ==============================================================================
if st.session_state.role != "SUPER_ADMIN":
    
    # --- DASHBOARD ---
    if st.session_state.page == "ACCUEIL":
        st.header("🏠 TABLEAU DE BORD")
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        st.metric("Ventes du jour (USD)", f"{v_jr:,.2f} $")
        st.info(f"📅 {datetime.now().strftime('%d/%m/%Y')} | ⌚ {datetime.now().strftime('%H:%M')} | Version v950")

    # --- STOCK ---
    elif st.session_state.page == "STOCK":
        st.header("📦 STOCK")
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            dn = c1.text_input("Article")
            sq = c2.number_input("Quantité", 1)
            pv = c3.number_input("Prix Vente ($)")
            if st.form_submit_button("AJOUTER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (dn.upper(), sq, pv, "USD", st.session_state.ent_id)); st.rerun()
        
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for pi, pd, ps, pp in prods:
            with st.container(border=True):
                l1, l2, l3, l4 = st.columns([3,1,1,1])
                u_d = l1.text_input("Nom", pd, key=f"d_{pi}")
                u_q = l2.number_input("Stock", value=ps, key=f"q_{pi}")
                u_p = l3.number_input("Prix $", value=pp, key=f"p_{pi}")
                if l4.button("💾", key=f"b_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_d.upper(), u_q, u_p, pi)); st.rerun()

    # --- CAISSE (A4 & 80mm) ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 CAISSE")
            c_f = st.radio("Format Facture", ["80mm", "A4"], horizontal=True)
            c_d = st.radio("Devise", ["USD", "CDF"], horizontal=True)
            
            p_map = {p[0]: (p[1], p[2]) for p in run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)}
            sel = st.selectbox("Article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()

            if st.session_state.panier:
                tot = 0.0
                items = []
                for a, q in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if c_d == "USD" else p_map[a][0] * TX_G
                    tot += pu * q
                    items.append({"art": a, "qty": q, "pu": pu})
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{a}**")
                    st.session_state.panier[a] = c2.number_input("Qté", 1, p_map[a][1], value=q, key=f"cart_{a}")
                    if c3.button("🗑️", key=f"rm_{a}"): del st.session_state.panier[a]; st.rerun()
                
                st.markdown(f"### TOTAL : {tot:,.2f} {c_d}")
                cl = st.text_input("Client", "COMPTANT")
                p_r = st.number_input("Payé", value=float(tot))
                if st.button("✅ VALIDER"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref, cl.upper(), tot, p_r, tot-p_r, c_d, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(items)))
                    if tot-p_r > 0: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cl.upper(), tot-p_r, c_d, ref, st.session_state.ent_id))
                    for a, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel=stock_actuel-? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    st.session_state.update({'last_fac': {"ref":ref, "tot":tot, "dev":c_d, "cli":cl.upper(), "det":items, "paye":p_r, "reste":tot-p_r}, 'panier': {}, 'format_fac': c_f})
                    st.rerun()
        else:
            f = st.session_state.last_fac
            e = get_entete()
            st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac': None}))
            if st.session_state.format_fac == "80mm":
                html = f"""<div class="fac-80mm"><h3 align="center">{e[0]}</h3><p align="center">{e[1]}<br>{e[2]}</p><hr>
                <b>REF:</b> {f['ref']}<br><b>CLIENT:</b> {f['cli']}<hr>
                <table width="100%">{"".join([f"<tr><td>{i['art']} x{i['qty']}</td><td align='right'>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['det']])}</table><hr>
                <h4 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h4></div>"""
            else:
                html = f"""<div class="fac-a4"><table width="100%"><tr><td><h2>{e[0]}</h2><p>{e[1]}<br>{e[2]}</p></td><td align="right"><h1>FACTURE</h1><p>{f['ref']}<br>{datetime.now().strftime('%d/%m/%Y')}</p></td></tr></table><br>
                <p><b>Client:</b> {f['cli']}</p><table width="100%" style="border-collapse:collapse; border:1px solid black;">
                <tr style="background:#eee;"><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td style='border:1px solid black;'>{i['art']}</td><td align='center' style='border:1px solid black;'>{i['qty']}</td><td align='right' style='border:1px solid black;'>{i['pu']:,.2f}</td><td align='right' style='border:1px solid black;'>{i['pu']*i['qty']:,.2f}</td></tr>" for i in f['det']])}
                </table><h2 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h2></div>"""
            st.markdown(html, unsafe_allow_html=True)
            if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    # --- RAPPORTS ---
    elif st.session_state.page == "RAPPORTS":
        st.header("📊 HISTORIQUE VENTES")
        vs = run_db("SELECT date_v, ref, client, total, devise FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if vs: st.dataframe(pd.DataFrame(vs, columns=["Date", "Réf", "Client", "Total", "Devise"]), use_container_width=True)

    # --- DETTES CLIENTS ---
    elif st.session_state.page == "CLIENTS":
        st.header("📉 DETTES CLIENTS")
        ds = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv, dr in ds:
            with st.container(border=True):
                st.write(f"👤 **{dc}** | **{dm:,.2f} {dv}** (Facture: {dr})")
                m_v = st.number_input("Paiement tranche", 0.0, float(dm), key=f"py_{di}")
                if st.button("VALIDER TRANCHE", key=f"bk_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (m_v, di)); st.rerun()

    # --- FOURNISSEURS ---
    elif st.session_state.page == "FOURNISSEURS":
        st.header("🚛 DETTES FOURNISSEURS")
        with st.form("four"):
            fn = st.text_input("Fournisseur")
            fm = st.number_input("Montant")
            if st.form_submit_button("SAUVER DETTE"):
                run_db("INSERT INTO dettes_fournisseurs (fournisseur, montant, devise, date_f, ent_id) VALUES (?,?,?,?,?)", (fn.upper(), fm, "USD", datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id)); st.rerun()

    # --- DÉPENSES ---
    elif st.session_state.page == "DÉPENSES":
        st.header("💸 DÉPENSES")
        with st.form("dep"):
            mot = st.text_input("Motif")
            val = st.number_input("Montant")
            if st.form_submit_button("SAUVER"):
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)", (mot.upper(), val, "USD", datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id)); st.rerun()

    # --- VENDEURS ---
    elif st.session_state.page == "VENDEURS":
        st.header("👥 VENDEURS")
        vn = st.text_input("Nom Vendeur")
        vp = st.text_input("Pass", type="password")
        if st.button("CRÉER COMPTE"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (vn.lower(), make_hashes(vp), 'VENDEUR', st.session_state.ent_id)); st.success("Vendeur ajouté !")

    # --- RÉGLAGES ---
    elif st.session_state.page == "RÉGLAGES":
        st.header("⚙️ RÉGLAGES")
        e = get_entete()
        with st.form("settings"):
            en = st.text_input("Nom Boutique", e[0])
            ea = st.text_input("Adresse", e[1])
            et = st.text_input("Tél", e[2])
            if st.form_submit_button("SAUVEGARDER"):
                run_db("INSERT OR REPLACE INTO ent_infos (ent_id, nom_boutique, adresse, telephone) VALUES (?,?,?,?)", (st.session_state.ent_id, en, ea, et)); st.rerun()
        up_img = st.file_uploader("Photo Profil", type=['png','jpg'])
        if st.button("METTRE À JOUR PHOTO"):
            if up_img: run_db("UPDATE users SET photo=? WHERE username=?", (sqlite3.Binary(up_img.getvalue()), st.session_state.user)); st.rerun()

# --- ADMIN SYSTEM ---
elif st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "SYSTÈME":
        with st.form("sys"):
            n_m = st.text_area("Message Marquee", MARQUEE)
            n_t = st.number_input("Taux Global", value=TX_G)
            if st.form_submit_button("APPLIQUER"):
                run_db("UPDATE system_config SET marquee_text=?, taux_global=? WHERE id=1", (n_m, n_t)); st.rerun()
