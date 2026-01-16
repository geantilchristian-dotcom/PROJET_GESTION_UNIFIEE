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
# 1. CONFIGURATION SYSTÈME & CORE (STRICTEMENT CENTRÉ)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v800", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None
    })

# --- MOTEUR DE BASE DE DONNÉES ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_pro_v800.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur DB Critique : {e}")
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

    # Admin Maître (Codes: admin / admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, color_m, date_inscription) VALUES (?, ?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP', '#00FF00', '16/01/2026'))

init_db()

# ==============================================================================
# 3. DESIGN CSS GLOBAL (TEXTES CENTRÉS & MARQUEE FIXE)
# ==============================================================================
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)

if res_cfg:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", "#00FF00", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    /* TOUT LE TEXTE EST CENTRÉ PAR DÉFAUT */
    .stApp {{ background-color: #f1f3f6; text-align: center !important; }}
    h1, h2, h3, h4, h5, p, span, label, div {{ text-align: center !important; }}
    
    /* MARQUEE FIXE */
    .marquee-fixed {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: {C_COLOR}; height: 50px;
        z-index: 999999; border-bottom: 3px solid #FF8C00;
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: scroll-v800 20s linear infinite;
        font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 20px; font-weight: bold;
    }}
    @keyframes scroll-v800 {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* MONTRE STYLÉE */
    .watch-box {{
        background: radial-gradient(circle, #333 0%, #000 100%);
        color: #FF8C00; padding: 40px; border-radius: 30px;
        border: 5px solid #FF8C00; box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        display: inline-block; min-width: 320px; margin: 20px auto;
    }}
    .watch-h {{ font-size: 60px; font-weight: 900; margin: 0; letter-spacing: 5px; }}
    .watch-d {{ font-size: 20px; color: white; text-transform: uppercase; }}

    /* BOUTONS BLEU / TEXTE BLANC */
    .stButton>button {{
        background: linear-gradient(135deg, #0055ff, #0022aa) !important;
        color: white !important; border-radius: 15px; height: 50px;
        width: 100%; font-weight: bold; border: none; font-size: 16px; margin: 5px 0;
    }}

    /* CADRE PRIX */
    .price-tag {{
        border: 5px solid #FF8C00; background: #111; padding: 25px;
        border-radius: 20px; color: #00FF00; font-size: 38px;
        font-weight: 900; margin: 20px auto; display: inline-block; width: 80%;
    }}

    /* TABLEAUX STYLÉS */
    .hq-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; border-radius: 15px; overflow: hidden; }}
    .hq-table th {{ background: #0022aa; color: white; padding: 15px; text-align: center; }}
    .hq-table td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: center; font-size: 14px; }}

    /* FACTURE PRO */
    .facture-container {{
        background: #fff; color: #000; padding: 40px; border: 1px solid #ccc;
        max-width: 750px; margin: 20px auto; font-family: 'Courier New', monospace; text-align: left !important;
    }}
    .facture-container h2, .facture-container p {{ text-align: center !important; }}
    .sig-row {{ display: flex; justify-content: space-between; margin-top: 60px; }}
    .sig-line {{ border-top: 2px solid #000; width: 220px; text-align: center; font-weight: bold; }}

    @media print {{
        .marquee-fixed, .stSidebar, .stButton, .no-print {{ display: none !important; }}
        .facture-container {{ border: none !important; width: 100% !important; }}
    }}
    </style>

    <div class="marquee-fixed">
        <div class="marquee-text">{C_MSG}</div>
    </div>
    <div style="margin-top: 80px;"></div>
""", unsafe_allow_html=True)

# Blocage compte
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 ACCÈS SUSPENDU. CONTACTEZ BALIKA.")
    st.stop()

# ==============================================================================
# 4. LOGIN & INSCRIPTION
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.2, 0.6, 0.2])
    with col_log:
        st.title("BALIKA CLOUD ERP")
        t_in, t_up = st.tabs(["🔑 CONNEXION", "📝 NOUVEAU ERP"])
        with t_in:
            u_in = st.text_input("Identifiant").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER"):
                r = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if r and make_hashes(p_in) == r[0][0]:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':r[0][1], 'ent_id':r[0][2]})
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        with t_up:
            with st.form("crea"):
                st.subheader("Créer mon instance")
                r_ent = st.text_input("Nom de l'Entreprise")
                r_tel = st.text_input("WhatsApp")
                r_u = st.text_input("ID Admin").lower().strip()
                r_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("LANCER MON ERP"):
                    if r_ent and r_u and r_p:
                        if not run_db("SELECT * FROM users WHERE username=?", (r_u,), fetch=True):
                            eid = f"ERP-{random.randint(100, 999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", (r_u, make_hashes(r_p), "ADMIN", eid, r_tel))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, taux, message, color_m, date_inscription) VALUES (?,?,?,?,?,?,?)", (eid, r_ent.upper(), r_tel, 2850.0, "BIENVENUE", "#00FF00", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Création réussie !")
                        else: st.warning("ID déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:
    u_d = run_db("SELECT photo, full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    if u_d[0]: st.image(u_d[0], width=130)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=130)
    st.markdown(f"### 👑 {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 MES ABONNÉS", "📊 RAPPORTS HQ", "⚙️ RÉGLAGES ADMIN", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. ACCUEIL (AVEC MONTRE ET DATE)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"TABLEAU DE BORD : {C_NOM}")
    
    st.markdown(f"""
        <center>
            <div class="watch-box">
                <p class="watch-h">{datetime.now().strftime('%H:%M:%S')}</p>
                <p class="watch-d">📅 {datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    v_t = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{v_t:,.2f} $")
    d_t = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("RECOUVREMENT", f"{d_t:,.2f} $")
    s_t = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES STOCK", s_t)

# ==============================================================================
# 7. SUPER-ADMIN : GESTION DES ABONNÉS
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES CLIENTS BALIKA ERP")
    
    clients = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, montant_paye FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    # Tableau HTML Stylé
    st.markdown("""<table class="hq-table">
        <tr><th>ID ENT</th><th>NOM ENTREPRISE</th><th>CONTACT</th><th>INSCRIPTION</th><th>PAIEMENT ($)</th><th>STATUS</th></tr>""", unsafe_allow_html=True)
    for eid, en, et, es, ed, em in clients:
        st.markdown(f"<tr><td><code>{eid}</code></td><td><b>{en}</b></td><td>{et}</td><td>{ed}</td><td style='color:green; font-weight:bold;'>{em:,.2f} $</td><td>{es}</td></tr>", unsafe_allow_html=True)
    st.markdown("</table>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("🔧 ACTIONS SUR LES COMPTES")
    for eid, en, et, es, ed, em in clients:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2, 1, 1])
            cl1.write(f"🏢 **{en}**")
            new_p = cl2.number_input(f"Montant Versé ($)", value=float(em), key=f"p_{eid}")
            if cl2.button("💾 SAUVER PAIEMENT", key=f"s_{eid}"):
                run_db("UPDATE config SET montant_paye=? WHERE ent_id=?", (new_p, eid))
                st.rerun()
            if cl3.button("⏯️ PAUSE/ACTIF", key=f"t_{eid}"):
                ns = "PAUSE" if es == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid))
                st.rerun()
            if cl3.button("🗑️ SUPPRIMER", key=f"del_{eid}"):
                run_db("DELETE FROM config WHERE ent_id=?", (eid,))
                run_db("DELETE FROM users WHERE ent_id=?", (eid,))
                st.rerun()

# ==============================================================================
# 8. SUPER-ADMIN : RÉGLAGES ADMIN (MESSAGE ET COULEURS)
# ==============================================================================
elif st.session_state.page == "ADMIN" and ROLE == "SUPER_ADMIN":
    st.header("⚙️ RÉGLAGES SYSTÈME BALIKA")
    
    with st.form("hq_cfg"):
        st.subheader("Personnalisation du Marquee")
        new_msg = st.text_area("Votre Message Défilant", C_MSG)
        new_color = st.color_picker("Couleur du Message", C_COLOR)
        st.write("---")
        st.subheader("Informations HQ")
        new_nom = st.text_input("Nom de la Maison Mère", C_NOM)
        new_tx = st.number_input("Taux de base", value=C_TX)
        
        if st.form_submit_button("APPLIQUER LES MODIFICATIONS"):
            run_db("UPDATE config SET message=?, color_m=?, nom_ent=?, taux=? WHERE ent_id='SYSTEM'", (new_msg, new_color, new_nom, new_tx))
            st.rerun()

# ==============================================================================
# 9. CAISSE (SIGNATURES & PARTAGE)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
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
                c_a.write(f"**{art}**")
                st.session_state.panier[art] = c_b.number_input("Qté", 1, p_map[art]['st'], value=qte, key=f"q_{art}")
                if c_c.button("❌", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()

            st.markdown(f'<center><div class="price-tag">NET À PAYER : {total:,.2f} {v_dev}</div></center>', unsafe_allow_html=True)
            cl_n = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            cl_p = st.number_input("MONTANT REÇU", value=float(total))
            
            if st.button("💾 FINALISER LA VENTE"):
                ref = f"FAC-{random.randint(100, 999)}"; dt = datetime.now().strftime("%d/%m/%Y %H:%M"); reste = total - cl_p
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", (ref, cl_n, total, cl_p, reste, v_dev, dt, USER, ENT_ID, json.dumps(lines)))
                if reste > 0.1: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", (cl_n, reste, v_dev, ref, ENT_ID, json.dumps([{'d':dt, 'p':cl_p}])))
                for l in lines: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (l['qte'], l['art'], ENT_ID))
                st.session_state.last_fac = {'ref':ref, 'cl':cl_n, 'tot':total, 'pay':cl_p, 'dev':v_dev, 'items':lines, 'date':dt}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({'last_fac':None}))
        
        html_f = f"""
        <div class="facture-container">
            <h2>{C_NOM}</h2><p>{C_ADR}<br>WhatsApp: {C_TEL}</p><hr>
            <p><b>FACTURE {f['ref']}</b><br>Client: {f['cl']} | Date: {f['date']}</p>
            <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                <tr style="border-bottom: 2px solid #000;"><th>Article</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td style='padding:8px;'>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
            </table>
            <hr><h3 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Payé: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
            <div class="sig-row">
                <div class="sig-line">Signature Entreprise</div>
                <div class="sig-line">Signature Client</div>
            </div>
        </div>
        """
        st.markdown(html_f, unsafe_allow_html=True)
        
        st.write("---")
        a1, a2, a3 = st.columns(3)
        a1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        a2.info("📂 SAUVER : Imprimer > PDF")
        wa_msg = f"Facture {f['ref']} de {C_NOM}. Total: {f['tot']} {f['dev']}."
        a3.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="width:100%; height:50px; background:#25D366; color:white; border-radius:12px; border:none; font-weight:bold;">📲 PARTAGER WHATSAPP</button></a>', unsafe_allow_html=True)

# ==============================================================================
# 10. PROFIL (USER, PASS, PHOTO)
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE UTILISATEUR")
    with st.container(border=True):
        p1, p2 = st.columns(2)
        with p1:
            n_fn = st.text_input("Nom Complet", u_d[1])
            n_tel = st.text_input("Téléphone", u_d[2])
            n_img = st.file_uploader("Photo de profil", type=["jpg", "png"])
        with p2:
            n_usr = st.text_input("Identifiant (Username)", USER)
            n_pwd = st.text_input("Nouveau Mot de Passe", type="password")
            n_cf = st.text_input("Confirmer Mot de Passe", type="password")
            
        if st.button("METTRE À JOUR MON PROFIL"):
            if n_pwd:
                if n_pwd == n_cf: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pwd), USER))
                else: st.error("Mots de passe différents")
            
            if n_img: run_db("UPDATE users SET photo=? WHERE username=?", (n_img.getvalue(), USER))
            
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (n_fn, n_tel, USER))
            
            if n_usr != USER:
                try:
                    run_db("UPDATE users SET username=? WHERE username=?", (n_usr, USER))
                    st.session_state.user = n_usr
                except: st.error("Identifiant déjà pris")
            st.success("Profil actualisé !"); st.rerun()

# ==============================================================================
# 11. STOCK (PRIX & SUPPRESSION)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DU STOCK")
    with st.expander("➕ AJOUTER UN PRODUIT"):
        with st.form("add_p"):
            st1, st2, st3, st4 = st.columns([3, 1, 1, 1])
            na = st1.text_input("Désignation")
            nq = st2.number_input("Stock", 1)
            np = st3.number_input("Prix", 0.0)
            nd = st4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([3, 1, 1, 0.5])
            cl1.write(f"**{sn}**")
            cl2.write(f"Stock: {sq}")
            nx = cl3.number_input("Prix", value=float(sp), key=f"px_{sid}")
            if cl3.button("💾", key=f"s_{sid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nx, sid)); st.rerun()
            if cl4.button("🗑️", key=f"d_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,)); st.rerun()

# ==============================================================================
# 12. RÉGLAGES (HEADER CLIENT)
# ==============================================================================
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("set_cl"):
        en_c = st.text_input("Nom de l'Entreprise", C_NOM)
        ad_c = st.text_input("Adresse", C_ADR)
        tl_c = st.text_input("Téléphone", C_TEL)
        tx_c = st.number_input("Taux de change (1$ = ? CDF)", value=C_TX)
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=? WHERE ent_id=?", (en_c.upper(), ad_c, tl_c, tx_c, ENT_ID))
            st.rerun()

# ==============================================================================
# 13. DETTES & RAPPORTS
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 GESTION DES DETTES")
    dl = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    for did, dcl, dmt, ddv, drf, dhi in dl:
        with st.expander(f"🔴 {dcl} : {dmt:,.2f} {ddv}"):
            vp = st.number_input("Montant versé ce jour", 0.0, float(dmt), key=f"v_{did}")
            if st.button("VALIDER LE PAIEMENT", key=f"b_{did}"):
                nm = dmt - vp; h = json.loads(dhi); h.append({'d': datetime.now().strftime("%d/%m"), 'p': vp})
                run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (vp, vp, drf, ENT_ID))
                if nm <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste", "Devise"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER LE JOURNAL"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
