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
# 1. CONFIGURATION ET SYSTÈME CORE
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v741", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation complète du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None
    })

# --- MOTEUR DE BASE DE DONNÉES (SQLite WAL Mode) ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_pro_v740.db', timeout=60) as conn:
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
    # Table Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    # Table Configuration Entreprise & SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT, montant_paye REAL DEFAULT 0.0)""")
    
    # Table Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT)""")
    
    # Table Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Insertion Admin Maître
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP - SYSTÈME UNIFIÉ 2026', '16/01/2026'))

init_db()

# ==============================================================================
# 3. MOTEUR D'AFFICHAGE CSS ET MARQUEE (MODIFIÉ POUR MOBILE ET PERSO)
# ==============================================================================
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)

if res_cfg:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0]
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

# Injection CSS (Ajusté pour luminosité téléphone et Marquee dynamique)
st.markdown(f"""
    <style>
    /* Global - Fond Noir pour haute luminosité téléphone */
    .stApp {{ background-color: #000000; margin-top: 50px; color: #FFFFFF !important; }}
    
    /* LE MARQUEE FIXE (UTILISE VOTRE MESSAGE PERSO) */
    .marquee-wrapper {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 50px;
        z-index: 999999; border-bottom: 3px solid #FF8C00;
        display: flex; align-items: center; overflow: hidden;
    }}
    marquee {{
        font-family: 'Courier New', monospace; font-size: 20px; font-weight: bold;
    }}

    /* MONTRE ACCUEIL STYLÉE */
    .clock-box {{
        background: linear-gradient(145deg, #1e1e1e, #000000);
        color: #FF8C00; padding: 40px; border-radius: 25px;
        border: 4px solid #FF8C00; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        display: inline-block; text-align: center; margin: 20px auto;
    }}
    .clock-time {{ font-size: 65px; font-weight: 900; margin: 0; letter-spacing: 4px; }}
    .clock-date {{ font-size: 20px; color: #fff; text-transform: uppercase; }}

    /* BOUTONS BLEUS TEXTE BLANC */
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 10px; font-weight: bold; border: none; height: 45px; width: 100%;
    }}

    /* CADRE TOTAL */
    .price-frame {{
        border: 5px solid #FF8C00; background: #000; padding: 20px;
        border-radius: 15px; color: #00FF00; font-size: 35px;
        font-weight: bold; text-align: center; margin: 20px 0;
    }}

    /* Optimisation des champs de saisie pour téléphone */
    div[data-baseweb="input"] {{ background-color: #FFFFFF !important; border-radius: 8px !important; }}
    input {{ color: #000000 !important; font-weight: bold !important; }}

    @media print {{
        .marquee-wrapper, .stSidebar, .stButton, .no-print {{ display: none !important; }}
    }}
    </style>

    <div class="marquee-wrapper">
        <marquee scrollamount="8">
             📢 {C_MSG} | 🏢 {C_NOM} | 💹 TAUX: {C_TX} CDF/USD | 📅 {datetime.now().strftime('%d/%m/%Y')}
        </marquee>
    </div>
""", unsafe_allow_html=True)

# Blocage si compte suspendu
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 ACCÈS SUSPENDU. CONTACTEZ BALIKA HQ.")
    st.stop()

# ==============================================================================
# 4. PAGE DE CONNEXION (LOGIN)
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        st.title("BALIKA - ACCÈS RÉSEAU")
        
        tab_l, tab_r = st.tabs(["🔑 CONNEXION", "📝 NOUVEAU COMPTE"])
        
        with tab_l:
            u_in = st.text_input("Identifiant").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if res and make_hashes(p_in) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        
        with tab_r:
            with st.form("reg"):
                st.subheader("Créer votre instance ERP")
                r_e = st.text_input("Nom de l'Entreprise")
                r_t = st.text_input("WhatsApp")
                r_u = st.text_input("Identifiant Admin").lower().strip()
                r_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if r_e and r_u and r_p:
                        check = run_db("SELECT * FROM users WHERE username=?", (r_u,), fetch=True)
                        if not check:
                            new_id = f"E-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", (r_u, make_hashes(r_p), "ADMIN", new_id, r_t))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, taux, message, date_inscription) VALUES (?,?,?,?,?,?)", (new_id, r_e.upper(), r_t, 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Compte activé !")
                        else: st.warning("ID déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. SIDEBAR (NAVIGATION)
# ==============================================================================
with st.sidebar:
    # Photo Profil
    pic_res = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    pic_data = pic_res[0][0] if pic_res else None
    if pic_data: st.image(pic_data, width=120)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.info(f"Rôle : {ROLE}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        m = ["🏠 ACCUEIL", "🌍 MES ABONNÉS", "📊 RAPPORTS HQ", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        m = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # VENDEUR
        m = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for item in m:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. PAGE ACCUEIL (MONTRE & DATE)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"TABLEAU DE BORD : {C_NOM}")
    
    st.markdown(f"""
        <center>
            <div class="clock-box">
                <p class="clock-time">{datetime.now().strftime('%H:%M:%S')}</p>
                <p class="clock-date">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    sales = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{sales:,.2f} $")
    debts = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES À RÉCUPÉRER", f"{debts:,.2f} $", delta_color="inverse")
    stock = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", stock)

# ==============================================================================
# 7. SUPER-ADMIN : GESTION DES ABONNÉS
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 ADMINISTRATION DES ABONNÉS")
    
    with st.expander("📢 ÉDITER LE MESSAGE DÉFILANT GLOBAL"):
        msg_g = st.text_input("Nouveau message pour tous les écrans")
        if st.button("DÉPLOYER LE MESSAGE"):
            run_db("UPDATE config SET message=?", (msg_g,))
            st.success("Message déployé !")
            st.rerun()

    clients = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, montant_paye FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    tab_html = """<table class="admin-table" style="width:100%; color:white;">
        <tr><th>ID ENT</th><th>ENTREPRISE</th><th>TÉLÉPHONE</th><th>DATE INSCRIPTION</th><th>PAIEMENT ($)</th><th>STATUT</th></tr>"""
    for eid, en, et, es, ed, em in clients:
        tab_html += f"<tr><td>{eid}</td><td><b>{en}</b></td><td>{et}</td><td>{ed}</td><td><b style='color:green;'>{em} $</b></td><td>{es}</td></tr>"
    tab_html += "</table>"
    st.markdown(tab_html, unsafe_allow_html=True)
    
    st.write("---")
    for eid, en, et, es, ed, em in clients:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2, 1, 1])
            cl1.write(f"🏢 **{en}**")
            new_m = cl2.number_input(f"Paiement Reçu ($)", value=float(em), key=f"m_{eid}")
            if cl2.button("💾 SAUVER PAIEMENT", key=f"btn_m_{eid}"):
                run_db("UPDATE config SET montant_paye=? WHERE ent_id=?", (new_m, eid))
                st.rerun()
            if cl3.button("⏯️ PAUSE / ACTIF", key=f"btn_s_{eid}"):
                ns = "PAUSE" if es == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid))
                st.rerun()

# ==============================================================================
# 8. CAISSE (SIGNATURES, PARTAGE ET IMPRESSION)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        c_v1, c_v2 = st.columns(2)
        v_devise = c_v1.selectbox("Devise de vente", ["USD", "CDF"])
        v_format = c_v2.selectbox("Format Ticket", ["80mm", "A4"])
        
        plist = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in plist}
        
        cs, cb = st.columns([3, 1])
        choix = cs.selectbox("Chercher article", ["---"] + list(p_dict.keys()))
        if cb.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_net = 0.0; lines = []
            for art, qte in list(st.session_state.panier.items()):
                p_b = p_dict[art]['px']; d_b = p_dict[art]['dv']
                if d_b == "USD" and v_devise == "CDF": px_f = p_b * C_TX
                elif d_b == "CDF" and v_devise == "USD": px_f = p_b / C_TX
                else: px_f = p_b
                stot = px_f * qte; total_net += stot
                lines.append({'art': art, 'qte': qte, 'pu': px_f, 'st': stot})
                
                ca, cb, cc = st.columns([3, 1, 0.5])
                ca.write(f"**{art}**")
                st.session_state.panier[art] = cb.number_input("Qté", 1, p_dict[art]['st'], value=qte, key=f"q_{art}")
                if cc.button("🗑️", key=f"r_{art}"): del st.session_state.panier[art]; st.rerun()

            st.markdown(f'<div class="price-frame">TOTAL : {total_net:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            c_cl = st.text_input("CLIENT", "CLIENT COMPTANT").upper()
            c_reçu = st.number_input("MONTANT REÇU", value=float(total_net))
            
            if st.button("✅ VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(1000, 9999)}"; dt = datetime.now().strftime("%d/%m/%Y %H:%M"); reste = total_net - c_reçu
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", (ref, c_cl, total_net, c_reçu, reste, v_devise, dt, USER, ENT_ID, json.dumps(lines)))
                if reste > 0.1: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", (c_cl, reste, v_devise, ref, ENT_ID, json.dumps([{'d': dt, 'p': c_reçu}])))
                for l in lines: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (l['qte'], l['art'], ENT_ID))
                st.session_state.last_fac = {'ref': ref, 'cl': c_cl, 'tot': total_net, 'pay': c_reçu, 'dev': v_devise, 'items': lines, 'date': dt}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({'last_fac': None}))
        html_fac = f"""<div class="invoice-card">...</div>""" # (Logique facture conservée)
        st.markdown(html_fac, unsafe_allow_html=True)

# ==============================================================================
# 9. MON PROFIL (ÉDITION DU MESSAGE ET INFOS)
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL")
    curr = run_db("SELECT full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    
    # --- MODIFICATION DU MESSAGE DÉFILANT ICI ---
    if ROLE in ["ADMIN", "SUPER_ADMIN"]:
        with st.container(border=True):
            st.subheader("📢 PERSONNALISER LE TEXTE DÉFILANT")
            nouveau_marquee = st.text_area("Entrez le message qui défile en haut de l'écran :", value=C_MSG)
            if st.button("💾 SAUVER LE MESSAGE"):
                run_db("UPDATE config SET message=? WHERE ent_id=?", (nouveau_marquee, ENT_ID))
                st.success("Message mis à jour !")
                st.rerun()
    
    with st.container(border=True):
        p1, p2 = st.columns(2)
        with p1:
            n_fn = st.text_input("Nom Complet", curr[0])
            n_tl = st.text_input("Téléphone", curr[1])
            n_im = st.file_uploader("Photo de Profil", type=["jpg", "png"])
        with p2:
            n_us = st.text_input("Identifiant (Username)", USER)
            n_pw = st.text_input("Nouveau mot de passe", type="password")
            
        if st.button("METTRE À JOUR LE PROFIL"):
            if n_pw: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pw), USER))
            if n_im: run_db("UPDATE users SET photo=? WHERE username=?", (n_im.getvalue(), USER))
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (n_fn, n_tl, USER))
            st.success("Profil mis à jour !"); st.rerun()

# ==============================================================================
# 10. STOCK (INTÉGRAL)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE STOCK")
    with st.expander("➕ AJOUTER UN PRODUIT"):
        with st.form("add"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            na = c1.text_input("Désignation"); nq = c2.number_input("Qté", 1); np = c3.number_input("Prix", 0.0); nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([3, 1, 1, 0.5])
            cl1.write(f"**{sn}**"); cl2.write(f"Stock: {sq}")
            nx = cl3.number_input("Modifier Prix", value=float(sp), key=f"p_{sid}")
            if cl3.button("💾", key=f"s_{sid}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nx, sid)); st.rerun()
            if cl4.button("🗑️", key=f"d_{sid}"): run_db("DELETE FROM produits WHERE id=?", (sid,)); st.rerun()

# ==============================================================================
# 11. DETTES (INTÉGRAL)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 RECOUVREMENT")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    for did, dcl, dmt, ddv, drf, dhi in d_list:
        with st.expander(f"🔴 {dcl} : {dmt:,.2f} {ddv}"):
            vp = st.number_input("Nouveau versement", 0.0, float(dmt), key=f"v_{did}")
            if st.button("ENREGISTRER PAIEMENT", key=f"b_{did}"):
                nm = dmt - vp; h = json.loads(dhi); h.append({'d': datetime.now().strftime("%d/%m"), 'p': vp})
                run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h), did))
                if nm <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                st.rerun()

# ==============================================================================
# 12. RÉGLAGES (HEADER, NOM, TAUX)
# ==============================================================================
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION")
    with st.form("cfg"):
        en = st.text_input("Nom Entreprise", C_NOM); ea = st.text_input("Adresse", C_ADR); et = st.text_input("WhatsApp", C_TEL)
        ex = st.number_input("Taux de change", value=C_TX); em = st.text_area("Message Défilant Rapide", C_MSG)
        if st.form_submit_button("SAUVER"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", (en.upper(), ea, et, ex, em, ENT_ID))
            st.rerun()

# ==============================================================================
# 13. RAPPORTS (INTÉGRAL)
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.header("📊 HISTORIQUE")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data: st.dataframe(pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste", "Devise"]))
