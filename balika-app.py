import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json

# ==============================================================================
# 1. CONFIGURATION & STYLE (v855)
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP ULTIMATE", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_v855_master.db', timeout=60) as conn:
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
# 2. INITIALISATION DES TABLES
# ==============================================================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, status TEXT DEFAULT 'ACTIF', photo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)")
    run_db("CREATE TABLE IF NOT EXISTS ent_infos (ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, rccm TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, devise TEXT, date_d TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes_fournisseurs (id INTEGER PRIMARY KEY AUTOINCREMENT, fournisseur TEXT, montant REAL, devise TEXT, motif TEXT, date_f TEXT, ent_id TEXT, status TEXT DEFAULT 'NON PAYÉ')")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global) VALUES (1, 'BALIKA ERP', 'Bienvenue sur BALIKA ERP v855 - Version A4 & 80mm Active', 2850.0)")

init_db()

# ==============================================================================
# 3. DESIGN & MARQUEE
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .fixed-header {{ position: fixed; top: 0; left: 0; width: 100%; background: #000; color: #00FF00; height: 50px; z-index: 9999; display: flex; align-items: center; border-bottom: 2px solid white; }}
    marquee {{ font-size: 18px; font-weight: bold; }}
    .main-content {{ margin-top: 60px; }}
    .stButton>button {{ background-color: #0055ff !important; color: white !important; border-radius: 10px; font-weight: bold; height: 50px; border: 2px solid white; width: 100%; }}
    .fac-80mm {{ background: white; color: black; padding: 10px; width: 300px; margin: auto; font-family: 'Courier New'; border: 1px solid #000; }}
    .fac-a4 {{ background: white; color: black; padding: 40px; width: 90%; margin: auto; font-family: Arial; border: 1px solid #ddd; min-height: 500px; }}
    div[data-baseweb="input"] {{ background: white !important; border-radius: 8px !important; }}
    input {{ color: black !important; font-weight: bold !important; }}
    </style>
    <div class="fixed-header"><marquee>{MARQUEE}</marquee></div><div class="main-content"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. FONCTION SECURITE INFOS BOUTIQUE
# ==============================================================================
def get_shop_info():
    info = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if not info:
        return (st.session_state.ent_id.upper(), "Adresse non définie", "000000000", "RCCM-000-000")
    return info[0]

# ==============================================================================
# 5. AUTHENTIFICATION
# ==============================================================================
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:white;'>BALIKA ERP LOGIN</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Password", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
            else: st.error("Identifiants incorrects.")
    st.stop()

# ==============================================================================
# 6. NAVIGATION
# ==============================================================================
with st.sidebar:
    st.title(f"⭐ {st.session_state.user.upper()}")
    st.write("---")
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "💸 DÉPENSES", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    if st.button("🚪 QUITTER"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 7. LOGIQUE CAISSE & FACTURATION (A4 / 80mm)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        mode = st.radio("Format Facture", ["80mm", "A4"], horizontal=True)
        devise = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        p_map = {x[0]: (x[1], x[2]) for x in prods}
        
        sel = st.selectbox("Choisir Produit", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER AU PANIER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
        
        if st.session_state.panier:
            total = 0.0
            l_items = []
            for art, qte in list(st.session_state.panier.items()):
                pu = p_map[art][0] if devise == "USD" else p_map[art][0] * TX_G
                sub = pu * qte
                total += sub
                l_items.append({"art": art, "qty": qte, "pu": pu})
                c1, c2, c3 = st.columns([3,1,1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_map[art][1], value=qte, key=f"q_{art}")
                if c3.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f"<div style='background:white; color:red; padding:10px; border:2px solid black;'><h3>TOTAL : {total:,.2f} {devise}</h3></div>", unsafe_allow_html=True)
            nom_c = st.text_input("Nom Client", "COMPTANT")
            if st.button("✅ VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(1000,9999)}"
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (ref, nom_c.upper(), total, total, 0, devise, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(l_items)))
                for a, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel=stock_actuel-? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                st.session_state.update({'last_fac': {"ref": ref, "tot": total, "dev": devise, "cli": nom_c.upper(), "det": l_items}, 'panier': {}, 'format_fac': mode})
                st.rerun()
    else:
        f = st.session_state.last_fac
        e = get_shop_info()
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({'last_fac': None}))
        
        if st.session_state.format_fac == "80mm":
            html = f"""<div class="fac-80mm"><h2 align="center">{e[0]}</h2><p align="center">{e[1]}<br>Tél: {e[2]}</p><hr>
            <b>REF:</b> {f['ref']}<br><b>CLIENT:</b> {f['cli']}<br><b>DATE:</b> {datetime.now().strftime('%d/%m/%Y')}<hr>
            <table width="100%">{"".join([f"<tr><td>{i['art']} x{i['qty']}</td><td align='right'>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['det']])}</table><hr>
            <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3><p align="center">Merci de votre visite !</p></div>"""
        else:
            html = f"""<div class="fac-a4"><table width="100%"><tr><td><h1>{e[0]}</h1><p>{e[1]}<br>{e[2]}<br>{e[3]}</p></td>
            <td align="right"><h2>FACTURE</h2><p>N°: {f['ref']}<br>Date: {datetime.now().strftime('%d/%m/%Y')}</p></td></tr></table><br>
            <p><b>Facturé à :</b> {f['cli']}</p><table width="100%" style="border-collapse: collapse; border: 1px solid black;">
            <tr style="background: #eee;"><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
            {"".join([f"<tr><td style='border:1px solid #000; padding:5px;'>{i['art']}</td><td align='center' style='border:1px solid #000;'>{i['qty']}</td><td align='right' style='border:1px solid #000;'>{i['pu']:,.2f}</td><td align='right' style='border:1px solid #000;'>{i['pu']*i['qty']:,.2f}</td></tr>" for i in f['det']])}
            </table><h2 align="right">TOTAL À PAYER : {f['tot']:,.2f} {f['dev']}</h2></div>"""
        
        st.markdown(html, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER LA FACTURE"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ==============================================================================
# 8. AUTRES MODULES (STOCK, RAPPORTS, RÉGLAGES)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DU STOCK")
    with st.form("add"):
        c1, c2, c3 = st.columns(3)
        dn = c1.text_input("Article")
        sq = c2.number_input("Qté initiale", 1)
        pv = c3.number_input("Prix Vente $")
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (dn.upper(), sq, pv, "USD", st.session_state.ent_id))
            st.rerun()
    
    items = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    for i_id, i_des, i_st, i_pr in items:
        with st.container(border=True):
            l1, l2, l3, l4 = st.columns([3,1,1,1])
            u_d = l1.text_input("Nom", i_des, key=f"d_{i_id}")
            u_q = l2.number_input("Qté", value=i_st, key=f"q_{i_id}")
            u_p = l3.number_input("Prix $", value=i_pr, key=f"p_{i_id}")
            if l4.button("💾", key=f"b_{i_id}"):
                run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_d.upper(), u_q, u_p, i_id)); st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 HISTORIQUE & PERFORMANCE")
    ventes = run_db("SELECT date_v, ref, client, total, devise FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if ventes:
        df = pd.DataFrame(ventes, columns=["Date", "Réf", "Client", "Total", "Devise"])
        st.dataframe(df, use_container_width=True)

elif st.session_state.page == "RÉGLAGES":
    st.header("⚙️ RÉGLAGES")
    e = get_shop_info()
    with st.form("settings"):
        en = st.text_input("Nom de la Boutique", e[0])
        ea = st.text_input("Adresse Physique", e[1])
        et = st.text_input("Téléphone", e[2])
        er = st.text_input("RCCM / ID National", e[3])
        if st.form_submit_button("SAUVEGARDER LES INFOS"):
            run_db("INSERT OR REPLACE INTO ent_infos (ent_id, nom_boutique, adresse, telephone, rccm) VALUES (?,?,?,?,?)", (st.session_state.ent_id, en, ea, et, er))
            st.rerun()
