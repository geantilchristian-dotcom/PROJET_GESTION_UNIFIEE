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
# 1. CONFIGURATION SYSTÈME & CORE
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v730", 
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
        with sqlite3.connect('balika_master_v730.db', timeout=60) as conn:
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
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET AVEC PAIEMENTS ABONNÉS)
# ==============================================================================
def init_db():
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT, montant_paye REAL DEFAULT 0.0)""")
    
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

    # Admin par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP - SYSTÈME DE GESTION UNIFIÉ', '16/01/2026'))

init_db()

# ==============================================================================
# 3. DESIGN CSS & MARQUEE PERSISTANT (LOGIN + APP)
# ==============================================================================
# Récupération dynamique pour le marquee
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)
C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0] if res_cfg else ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #f0f2f6; }}
    h1, h2, h3, p, label {{ text-align: center !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}

    /* MARQUEE TOP LEVEL */
    .marquee-fixed {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; padding: 12px 0; z-index: 99999;
        border-bottom: 2px solid #FF8C00; font-family: 'Courier New', Courier, monospace;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap; font-weight: bold; font-size: 18px;
        animation: scroll 30s linear infinite;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* MONTRE STYLÉE */
    .clock-container {{
        background: radial-gradient(circle, #2c3e50 0%, #000000 100%);
        color: #FF8C00; padding: 40px; border-radius: 30px;
        border: 5px solid #FF8C00; box-shadow: 0 15px 40px rgba(0,0,0,0.6);
        display: inline-block; margin: 20px auto; min-width: 320px;
    }}
    .time-txt {{ font-size: 60px; font-weight: 900; letter-spacing: 5px; margin: 0; }}
    .date-txt {{ font-size: 22px; color: #fff; text-transform: uppercase; letter-spacing: 2px; }}

    /* BOUTONS BLEUS TEXTE BLANC */
    .stButton>button {{
        background: linear-gradient(135deg, #0044ff, #002288) !important;
        color: white !important; border-radius: 12px; height: 50px;
        width: 100%; font-weight: bold; border: none; font-size: 16px;
    }}

    /* CADRE TOTAL CAISSE */
    .total-box {{
        border: 4px solid #FF8C00; background: #111; padding: 25px;
        border-radius: 20px; color: #00FF00; font-size: 38px; font-weight: 900;
        margin: 20px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }}

    /* TABLEAU ABONNÉS STYLE HQ */
    .hq-table {{
        width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden;
    }}
    .hq-table th {{ background: #002288; color: white; padding: 15px; }}
    .hq-table td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: center; }}

    /* FACTURE PROFESSIONNELLE */
    .fac-container {{
        background: #fff; color: #000; padding: 40px; border: 1px solid #eee;
        width: 100%; max-width: 800px; margin: auto; font-family: 'Courier New', monospace;
    }}
    .fac-grid {{ display: flex; justify-content: space-between; margin-top: 50px; }}
    .sig-box {{ border-top: 2px solid #000; width: 200px; padding-top: 10px; font-size: 14px; text-align: center; }}

    @media print {{
        .marquee-fixed, .stSidebar, .stButton, .no-print {{ display: none !important; }}
        .fac-container {{ border: none !important; width: 100% !important; }}
    }}
    </style>
    
    <div class="marquee-fixed">
        <div class="marquee-text">🛡️ HQ BALIKA : {C_MSG} | 🌐 ENTREPRISE : {C_NOM} | 💹 TAUX DU JOUR : {C_TX} CDF | 🕒 {datetime.now().strftime('%H:%M')}</div>
    </div>
    <div style="margin-top: 80px;"></div>
""", unsafe_allow_html=True)

# Blocage compte suspendu
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 VOTRE ACCÈS EST SUSPENDU. VEUILLEZ CONTACTER L'ADMINISTRATEUR BALIKA.")
    st.stop()

# ==============================================================================
# 4. SYSTÈME DE CONNEXION (LOGIN)
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.1, 0.8, 0.1])
    with col_log:
        st.title("BALIKA CLOUD - CONNEXION")
        tab_in, tab_up = st.tabs(["🔑 IDENTIFICATION", "📝 CRÉER MON COMPTE ERP"])
        
        with tab_in:
            u_in = st.text_input("Identifiant Utilisateur").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER L'ESPACE"):
                r = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if r and make_hashes(p_in) == r[0][0]:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':r[0][1], 'ent_id':r[0][2]})
                    st.rerun()
                else: st.error("Accès refusé.")
        
        with tab_up:
            with st.form("inscription"):
                r_ent = st.text_input("Nom de l'Entreprise")
                r_tel = st.text_input("Téléphone WhatsApp")
                r_adr = st.text_input("Adresse")
                r_user = st.text_input("ID Admin (ex: jules12)").lower().strip()
                r_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP MAINTENANT"):
                    if r_ent and r_user and r_pass:
                        chk = run_db("SELECT * FROM users WHERE username=?", (r_user,), fetch=True)
                        if not chk:
                            eid = f"ENT-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                                   (r_user, make_hashes(r_pass), "ADMIN", eid, r_tel))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, adresse, taux, message, date_inscription) VALUES (?,?,?,?,?,?,?)", 
                                   (eid, r_ent.upper(), r_tel, r_adr, 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Compte créé ! Connectez-vous.")
                        else: st.warning("ID déjà pris.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:
    u_data = run_db("SELECT photo, full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    if u_data[0]: st.image(u_data[0], width=120)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    st.markdown(f"### 👑 {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL ADMIN", "🌍 MES ABONNÉS", "📊 RAPPORTS HQ", "👤 MON PROFIL ADMIN"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # VENDEUR
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
    st.title(f"INTERFACE : {C_NOM}")
    
    st.markdown(f"""
        <center>
            <div class="clock-container">
                <p class="time-txt">{datetime.now().strftime('%H:%M')}</p>
                <p class="date-txt">📅 {datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    
    v_val = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("CHIFFRE D'AFFAIRES", f"{v_val:,.2f} $")
    
    d_val = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("RECOUVREMENT DETTES", f"{d_val:,.2f} $", delta_color="inverse")
    
    s_val = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", s_val)

# ==============================================================================
# 7. ESPACE SUPER-ADMIN (MES ABONNÉS)
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES ABONNÉS BALIKA")
    
    with st.expander("📢 DIFFUSER UN MESSAGE DÉFILANT GLOBAL"):
        new_g_msg = st.text_input("Message pour tous les clients")
        if st.button("DIFFUSER"):
            run_db("UPDATE config SET message=?", (new_g_msg,))
            st.success("Message global mis à jour !")
            st.rerun()

    clients = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, montant_paye, adresse FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    # Tableau Stylisé
    st.subheader("📋 LISTE DÉTAILLÉE DES ENTREPRISES")
    html_tab = """<table class="hq-table"><tr><th>ID</th><th>Entreprise</th><th>Téléphone</th><th>Inscription</th><th>Paiement Reçu</th><th>Statut</th><th>Action</th></tr>"""
    for eid, ename, etel, estat, edate, epay, eadr in clients:
        color = "green" if estat == "ACTIF" else "red"
        html_tab += f"""
        <tr>
            <td><code>{eid}</code></td>
            <td><b>{ename}</b><br><small>{eadr}</small></td>
            <td>{etel}</td>
            <td>{edate}</td>
            <td style='color:green; font-weight:bold;'>{epay} $</td>
            <td style='color:{color}'>{estat}</td>
            <td>Action via bouton ci-dessous</td>
        </tr>
        """
    html_tab += "</table>"
    st.markdown(html_tab, unsafe_allow_html=True)

    st.write("---")
    st.subheader("🛠️ GESTION DES COMPTES ET PAIEMENTS")
    for eid, ename, etel, estat, edate, epay, eadr in clients:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2, 1, 1])
            cl1.write(f"🏢 **{ename}**")
            new_val = cl2.number_input(f"Verser Paiement ($)", 0.0, 1000.0, value=float(epay), key=f"pay_{eid}")
            if cl2.button("💾 SAUVER PRIX", key=f"sav_{eid}"):
                run_db("UPDATE config SET montant_paye=? WHERE ent_id=?", (new_val, eid))
                st.rerun()
            
            if cl3.button("⏯️ PAUSE/ACTIF", key=f"tgl_{eid}"):
                ns = "PAUSE" if estat == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid))
                st.rerun()
            if cl3.button("🗑️ SUPPRIMER", key=f"del_{eid}"):
                run_db("DELETE FROM config WHERE ent_id=?", (eid,))
                run_db("DELETE FROM users WHERE ent_id=?", (eid,))
                st.rerun()

# ==============================================================================
# 8. CAISSE (SIGNATURES DOUBLES & ACTIONS SÉPARÉES)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        c_o1, c_o2 = st.columns(2)
        v_dev = c_o1.selectbox("Devise", ["USD", "CDF"])
        v_fmt = c_o2.selectbox("Format", ["80mm Ticket", "A4 Facture"])
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        cs, cb = st.columns([3, 1])
        pick = cs.selectbox("Article", ["---"] + list(p_map.keys()))
        if cb.button("➕ AJOUTER") and pick != "---":
            st.session_state.panier[pick] = st.session_state.panier.get(pick, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_v = 0.0; lines = []
            for art, qte in list(st.session_state.panier.items()):
                px_b = p_map[art]['px']
                dv_b = p_map[art]['dv']
                if dv_b == "USD" and v_dev == "CDF": px_f = px_b * C_TX
                elif dv_b == "CDF" and v_dev == "USD": px_f = px_b / C_TX
                else: px_f = px_b
                
                stot = px_f * qte; total_v += stot
                lines.append({"art": art, "qte": qte, "pu": px_f, "st": stot})
                
                ca, cb, cc = st.columns([3, 1, 0.5])
                ca.write(f"**{art}**")
                st.session_state.panier[art] = cb.number_input("Q", 1, p_map[art]['stk'], value=qte, key=f"q_{art}")
                if cc.button("❌", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()

            st.markdown(f'<div class="total-box">NET À PAYER : {total_v:,.2f} {v_dev}</div>', unsafe_allow_html=True)
            c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_paye = st.number_input("MONTANT REÇU", value=float(total_v))
            
            if st.button("💾 FINALISER ET GÉNÉRER FACTURE"):
                ref = f"FAC-{random.randint(1000, 9999)}"; dt = datetime.now().strftime("%d/%m/%Y %H:%M"); reste = total_v - c_paye
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", (ref, c_nom, total_v, c_paye, reste, v_dev, dt, USER, ENT_ID, json.dumps(lines)))
                if reste > 0.1: run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", (c_nom, reste, v_dev, ref, ENT_ID, json.dumps([{"date": dt, "paye": c_paye}])))
                for i in lines: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                st.session_state.last_fac = {"ref": ref, "cl": c_nom, "tot": total_v, "pay": c_paye, "dev": v_dev, "items": lines, "date": dt, "fmt": v_fmt}
                st.rerun()
    else:
        # --- MODE FACTURE ---
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        html_f = f"""
        <div class="fac-container" id="print_area">
            <center>
                <h1>{C_NOM}</h1>
                <p>{C_ADR}<br>WhatsApp: {C_TEL}</p>
                <hr>
                <p><b>REF: {f['ref']}</b> | Client: {f['cl']} | Date: {f['date']}</p>
            </center>
            <table style="width:100%; border-collapse: collapse; margin-top:20px;">
                <tr style="border-bottom: 2px solid #000;"><th>Désignation</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td style='padding:10px;'>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
            <p align="right">Payé: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
            
            <div class="fac-grid">
                <div class="sig-box">Signature de l'Entreprise</div>
                <div class="sig-box">Signature du Client</div>
            </div>
        </div>
        """
        st.markdown(html_f, unsafe_allow_html=True)
        
        st.write("---")
        # ACTIONS SÉPARÉES
        a1, a2, a3 = st.columns(3)
        a1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        a2.info("📂 SAUVEGARDER : Utilisez 'Imprimer' -> 'Sauvegarder en PDF'")
        
        wa_msg = f"Facture {f['ref']} de {C_NOM}. Total: {f['tot']} {f['dev']}. Merci !"
        a3.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="width:100%; height:50px; background:#25D366; color:white; border-radius:12px; border:none; font-weight:bold;">📲 PARTAGER WHATSAPP</button></a>', unsafe_allow_html=True)

# ==============================================================================
# 9. MON PROFIL (ADMIN & CLIENT)
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE")
    curr_u = run_db("SELECT full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    
    with st.container(border=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.subheader("Informations")
            new_fn = st.text_input("Nom Complet", curr_u[0])
            new_tel = st.text_input("Téléphone", curr_u[1])
            new_img = st.file_uploader("Changer Photo de Profil", type=["jpg", "png", "jpeg"])
        
        with col_p2:
            st.subheader("Sécurité")
            new_uid = st.text_input("Nouvel Identifiant", USER)
            new_pwd = st.text_input("Nouveau Mot de passe", type="password")
            confirm = st.text_input("Confirmer Mot de passe", type="password")
            
        if st.button("Mettre à jour mon profil"):
            if new_pwd:
                if new_pwd == confirm:
                    run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_pwd), USER))
                else: st.error("Mots de passe différents")
            
            if new_img: run_db("UPDATE users SET photo=? WHERE username=?", (new_img.getvalue(), USER))
            
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (new_fn, new_tel, USER))
            
            if new_uid != USER:
                try:
                    run_db("UPDATE users SET username=? WHERE username=?", (new_uid, USER))
                    st.session_state.user = new_uid
                except: st.error("Identifiant déjà pris")
            
            st.success("Profil actualisé !")
            st.rerun()

# ==============================================================================
# 10. STOCK (PRIX & SUPPRESSION)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 INVENTAIRE")
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("add_s"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            na = c1.text_input("Désignation")
            nq = c2.number_input("Q", 1)
            np = c3.number_input("Prix", 0.0)
            nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (na.upper(), nq, np, nd, ENT_ID)); st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([3, 1, 1, 0.5])
            cl1.write(f"**{sn}**")
            cl2.write(f"Stock: {sq}")
            nx = cl3.number_input("Prix", value=float(sp), key=f"px_{sid}")
            if nx != sp:
                if cl3.button("💾", key=f"s_{sid}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nx, sid)); st.rerun()
            if cl4.button("🗑️", key=f"d_{sid}"): run_db("DELETE FROM produits WHERE id=?", (sid,)); st.rerun()

# ==============================================================================
# 11. DETTES (AUTO-DELETE)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 GESTION DES DETTES")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    if not d_list: st.success("Aucune dette !")
    for did, dcl, dmt, ddv, drf, dhi in d_list:
        with st.expander(f"🔴 {dcl} : {dmt:,.2f} {ddv}"):
            st.table(pd.DataFrame(json.loads(dhi)))
            vp = st.number_input("Versement", 0.0, float(dmt), key=f"v_{did}")
            if st.button("ENCAISSER", key=f"b_{did}"):
                nm = dmt - vp; h = json.loads(dhi); h.append({"date": datetime.now().strftime("%d/%m"), "paye": vp})
                run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (vp, vp, drf, ENT_ID))
                if nm <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                st.rerun()

# ==============================================================================
# 12. RÉGLAGES (ADMIN CLIENT)
# ==============================================================================
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    with st.form("set_cfg"):
        en = st.text_input("Nom", C_NOM); ea = st.text_input("Adresse", C_ADR); et = st.text_input("Tél", C_TEL)
        ex = st.number_input("Taux (1$ = ? CDF)", value=C_TX); em = st.text_area("Message Défilant", C_MSG)
        if st.form_submit_button("SAUVER"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", (en.upper(), ea, et, ex, em, ENT_ID))
            st.rerun()

# ==============================================================================
# 13. RAPPORTS
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.header("📊 JOURNAL DES VENTES")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste", "Devise"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
