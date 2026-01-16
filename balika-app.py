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
# 1. CONFIGURATION SYSTÈME & CORE (BALIKA ERP v750)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v750", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation persistante du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None
    })

# --- MOTEUR DE BASE DE DONNÉES (SQLite WAL Mode pour la rapidité) ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v750.db', timeout=60) as conn:
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
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET SANS SUPPRESSION)
# ==============================================================================
def init_db():
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, color_m TEXT DEFAULT '#00FF00', 
                status TEXT DEFAULT 'ACTIF', entete_fac TEXT, 
                date_inscription TEXT, montant_paye REAL DEFAULT 0.0)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, color_m, date_inscription) VALUES (?, ?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP', '#00FF00', '16/01/2026'))

init_db()

# ==============================================================================
# 3. INTERFACE VISUELLE : CSS & MARQUEE PERSISTANT
# ==============================================================================
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)

if res_cfg:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", "#00FF00", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #f4f7f6; }}
    
    /* MARQUEE FIXE - AUCUN TEXTE AJOUTÉ, COULEUR PERSONNALISABLE */
    .marquee-fixed {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: {C_COLOR}; height: 55px;
        z-index: 999999; border-bottom: 3px solid #FF8C00;
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-content {{
        display: inline-block; white-space: nowrap;
        animation: scroll-text 20s linear infinite;
        font-family: 'Arial Black', sans-serif; font-size: 22px;
    }}
    @keyframes scroll-text {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}

    /* MONTRE ACCUEIL LUXE */
    .watch-container {{
        background: radial-gradient(circle, #222 0%, #000 100%);
        color: #FF8C00; padding: 45px; border-radius: 35px;
        border: 6px solid #FF8C00; box-shadow: 0 15px 40px rgba(0,0,0,0.7);
        display: inline-block; text-align: center; margin: 30px auto;
    }}
    .watch-time {{ font-size: 70px; font-weight: 900; margin: 0; letter-spacing: 3px; font-family: 'Courier New', monospace; }}
    .watch-date {{ font-size: 22px; color: #ffffff; text-transform: uppercase; letter-spacing: 2px; }}

    /* BOUTONS PROFESSIONNELS */
    .stButton>button {{
        background: linear-gradient(135deg, #0044cc, #001f66) !important;
        color: white !important; border-radius: 12px; font-weight: bold;
        border: none; height: 50px; width: 100%; font-size: 16px;
    }}

    /* CADRE PRIX CAISSE */
    .total-box {{
        border: 4px solid #FF8C00; background: #000; padding: 25px;
        border-radius: 20px; color: #00FF00; font-size: 40px;
        font-weight: 900; text-align: center; margin: 25px 0;
    }}

    /* TABLEAUX ADMIN */
    .styled-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 10px; overflow: hidden; }}
    .styled-table th {{ background: #0044cc; color: white; padding: 15px; text-align: center; }}
    .styled-table td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: center; }}

    /* FACTURE & SIGNATURES */
    .facture-ui {{
        background: #fff; color: #000; padding: 50px; border: 1px solid #ddd;
        max-width: 800px; margin: auto; font-family: 'Courier New', monospace;
    }}
    .signature-grid {{ display: flex; justify-content: space-between; margin-top: 80px; }}
    .signature-area {{ border-top: 2px solid #000; width: 220px; text-align: center; padding-top: 10px; font-weight: bold; }}

    @media print {{
        .marquee-fixed, .stSidebar, .stButton, .no-print {{ display: none !important; }}
        .facture-ui {{ border: none !important; width: 100% !important; }}
    }}
    </style>

    <div class="marquee-fixed">
        <div class="marquee-content">{C_MSG}</div>
    </div>
    <div style="margin-top: 85px;"></div>
""", unsafe_allow_html=True)

# Suspension de compte
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 VOTRE ACCÈS EST SUSPENDU. CONTACTEZ L'ADMINISTRATION.")
    st.stop()

# ==============================================================================
# 4. PAGE DE CONNEXION (LOGIN)
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.title("BALIKA ERP - LOGIN")
        t1, t2 = st.tabs(["🔐 IDENTIFICATION", "🚀 CRÉER UN COMPTE"])
        with t1:
            u = st.text_input("Username").lower().strip()
            p = st.text_input("Password", type="password")
            if st.button("SE CONNECTER"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
                if res and make_hashes(p) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Accès refusé.")
        with t2:
            with st.form("new_acc"):
                ne = st.text_input("Nom Entreprise"); nt = st.text_input("WhatsApp")
                nu = st.text_input("ID Admin").lower().strip(); np = st.text_input("Pass", type="password")
                if st.form_submit_button("CRÉER MON INSTANCE"):
                    if ne and nu and np:
                        if not run_db("SELECT * FROM users WHERE username=?", (nu,), fetch=True):
                            eid = f"B-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", (nu, make_hashes(np), "ADMIN", eid, nt))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, taux, message, color_m, date_inscription) VALUES (?,?,?,?,?,?,?)", (eid, ne.upper(), nt, 2850.0, "BIENVENUE", "#00FF00", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Succès !")
                        else: st.warning("ID déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. SIDEBAR (NAVIGATION COMPLÈTE)
# ==============================================================================
with st.sidebar:
    u_info = run_db("SELECT photo, full_name FROM users WHERE username=?", (USER,), fetch=True)[0]
    if u_info[0]: st.image(u_info[0], width=130)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=130)
    st.markdown(f"### 🛡️ {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 MES ABONNÉS", "📊 RAPPORTS HQ", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]; st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER", type="primary"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. ACCUEIL (MONTRE & DATE STYLE 80mm)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"BIENVENUE CHEZ {C_NOM}")
    st.markdown(f"""
        <center>
            <div class="watch-container">
                <p class="watch-time">{datetime.now().strftime('%H:%M:%S')}</p>
                <p class="watch-date">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    s_v = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES", f"{s_v:,.2f} $")
    d_v = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES", f"{d_v:,.2f} $")
    p_v = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("STOCK", p_v)

# ==============================================================================
# 7. SUPER-ADMIN : GESTION ABONNÉS (SaaS)
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES ABONNÉS")
    clients = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, montant_paye FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    # Tableau Stylé
    st.markdown("""<table class="styled-table">
        <tr><th>ID</th><th>Entreprise</th><th>WhatsApp</th><th>Date</th><th>Montant Reçu</th><th>Statut</th></tr>""", unsafe_allow_html=True)
    for eid, en, et, es, ed, em in clients:
        st.markdown(f"<tr><td>{eid}</td><td><b>{en}</b></td><td>{et}</td><td>{ed}</td><td style='color:green;font-weight:bold;'>{em} $</td><td>{es}</td></tr>", unsafe_allow_html=True)
    st.markdown("</table>", unsafe_allow_html=True)

    st.write("---")
    for eid, en, et, es, ed, em in clients:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2,1,1])
            cl1.write(f"🏢 **{en}**")
            new_val = cl2.number_input(f"Paiement ($)", value=float(em), key=f"pay_{eid}")
            if cl2.button("Mettre à jour", key=f"up_{eid}"):
                run_db("UPDATE config SET montant_paye=? WHERE ent_id=?", (new_val, eid)); st.rerun()
            if cl3.button("PAUSE/ACTIF", key=f"tgl_{eid}"):
                ns = "PAUSE" if es == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid)); st.rerun()

# ==============================================================================
# 8. CAISSE (SIGNATURES & PARTAGE)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 VENTE")
        c_o1, c_o2 = st.columns(2)
        v_dev = c_o1.selectbox("Devise", ["USD", "CDF"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in prods}
        
        cs, cb = st.columns([3, 1])
        pk = cs.selectbox("Article", ["---"] + list(p_map.keys()))
        if cb.button("➕ AJOUTER") and pk != "---":
            st.session_state.panier[pk] = st.session_state.panier.get(pk, 0) + 1; st.rerun()

        if st.session_state.panier:
            st.write("---")
            total = 0.0; lines = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_map[art]['px']; db = p_map[art]['dv']
                pxf = pb * C_TX if db=="USD" and v_dev=="CDF" else pb / C_TX if db=="CDF" and v_dev=="USD" else pb
                stot = pxf * qte; total += stot
                lines.append({'art':art, 'qte':qte, 'pu':pxf, 'st':stot})
                c_a, c_b, c_c = st.columns([3, 1, 0.5])
                c_a.write(art)
                st.session_state.panier[art] = c_b.number_input("Q", 1, p_map[art]['st'], value=qte, key=f"q_{art}")
                if c_c.button("❌", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()

            st.markdown(f'<div class="total-box">TOTAL : {total:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            cl_n = st.text_input("CLIENT", "COMPTANT").upper()
            cl_p = st.number_input("VERSÉ", value=float(total))
            
            if st.button("VALIDER"):
                ref = f"REF-{random.randint(100, 999)}"; dt = datetime.now().strftime("%d/%m/%Y %H:%M"); reste = total - cl_p
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", (ref, cl_n, total, cl_p, reste, v_dev, dt, USER, ENT_ID, json.dumps(lines)))
                if reste > 0.1: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", (cl_n, reste, v_dev, ref, ENT_ID, json.dumps([{'d':dt, 'p':cl_p}])))
                for l in lines: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (l['qte'], l['art'], ENT_ID))
                st.session_state.last_fac = {'ref':ref, 'cl':cl_n, 'tot':total, 'pay':cl_p, 'dev':v_dev, 'items':lines, 'date':dt}; st.rerun()
    else:
        f = st.session_state.last_fac; st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac':None}))
        html_f = f"""
        <div class="facture-ui">
            <center><h2>{C_NOM}</h2><p>{C_ADR}<br>WhatsApp: {C_TEL}</p><hr>
            <p><b>FACTURE {f['ref']}</b><br>Client: {f['cl']} | Date: {f['date']}</p></center>
            <table style="width:100%;"><tr><th>Désignation</th><th>Qté</th><th>Total</th></tr>
            {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}</table>
            <hr><h3 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h3>
            <div class="signature-grid"><div class="signature-area">Signature Entreprise</div><div class="signature-area">Signature Client</div></div>
        </div>"""
        st.markdown(html_f, unsafe_allow_html=True)
        c_a1, c_a2, c_a3 = st.columns(3)
        c_a1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        c_a2.info("📂 SAUVEGARDE : 'Imprimer' -> 'PDF'")
        wa_m = f"Facture {f['ref']} - {C_NOM}. Total: {f['tot']} {f['dev']}"
        c_a3.markdown(f'<a href="https://wa.me/?text={wa_m}" target="_blank"><button style="width:100%;background:#25D366;color:white;border:none;height:50px;border-radius:12px;">📲 PARTAGER</button></a>', unsafe_allow_html=True)

# ==============================================================================
# 9. PROFIL (USER, PASS, PHOTO)
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL")
    with st.form("prof_f"):
        c_u = run_db("SELECT full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
        n_n = st.text_input("Nom", c_u[0]); n_t = st.text_input("Tél", c_u[1])
        n_u = st.text_input("Identifiant", USER); n_p = st.text_input("Nouveau Pass", type="password")
        n_ph = st.file_uploader("Photo", type=["jpg", "png"])
        if st.form_submit_button("SAUVEGARDER"):
            if n_p: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_p), USER))
            if n_ph: run_db("UPDATE users SET photo=? WHERE username=?", (n_ph.getvalue(), USER))
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (n_n, n_t, USER))
            if n_u != USER:
                run_db("UPDATE users SET username=? WHERE username=?", (n_u, USER)); st.session_state.user = n_u
            st.success("Mis à jour !"); st.rerun()

# ==============================================================================
# 10. STOCK (PRIX & SUPPRESSION)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 STOCK")
    with st.expander("AJOUTER"):
        with st.form("a_s"):
            na = st.text_input("Désignation"); nq = st.number_input("Qté", 1); np = st.number_input("Prix", 0.0); nd = st.selectbox("D", ["USD", "CDF"])
            if st.form_submit_button("OK"): run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (na.upper(), nq, np, nd, ENT_ID)); st.rerun()
    p_s = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp in p_s:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([3,1,1,0.5])
            cl1.write(sn); cl2.write(f"Stock: {sq}")
            nx = cl3.number_input("Prix", value=float(sp), key=f"px_{sid}")
            if cl3.button("💾", key=f"s_{sid}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nx, sid)); st.rerun()
            if cl4.button("🗑️", key=f"d_{sid}"): run_db("DELETE FROM produits WHERE id=?", (sid,)); st.rerun()

# ==============================================================================
# 11. RÉGLAGES (COULEUR DÉFILANTE, TAUX, NOM)
# ==============================================================================
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ RÉGLAGES")
    with st.form("set_f"):
        en = st.text_input("Nom Boutique", C_NOM); ex = st.number_input("Taux", value=C_TX)
        em = st.text_area("Message Défilant", C_MSG)
        ec = st.color_picker("Couleur du Message Défilant", C_COLOR)
        if st.form_submit_button("APPLIQUER"):
            run_db("UPDATE config SET nom_ent=?, taux=?, message=?, color_m=? WHERE ent_id=?", (en.upper(), ex, em, ec, ENT_ID))
            st.rerun()

# ==============================================================================
# 12. DETTES & RAPPORTS
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 DETTES")
    dl = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    for did, dcl, dmt, ddv, drf, dhi in dl:
        with st.expander(f"{dcl} | {dmt:,.2f} {ddv}"):
            vp = st.number_input("Verser", 0.0, float(dmt), key=f"v_{did}")
            if st.button("OK", key=f"b_{did}"):
                nm = dmt - vp; h = json.loads(dhi); h.append({'d': datetime.now().strftime("%d/%m"), 'p': vp})
                run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (vp, vp, drf, ENT_ID))
                if nm <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 VENTES")
    data = run_db("SELECT date_v, ref, client, total, devise FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Devise"]), use_container_width=True)
        if st.button("🖨️ RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
