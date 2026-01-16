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
# 1. CONFIGURATION SYSTÈME & CORE (v700)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP COMMAND v700", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None
    })

# --- MOTEUR DE BASE DE DONNÉES ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v700.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Système : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. SCHÉMA DE BASE DE DONNÉES (EXTENSIONS DEMANDÉES)
# ==============================================================================
def init_db():
    # Table Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    # Table Configuration Entreprise (Ajout date_creation)
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT)""")
    
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

    # Admin Maître par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'Bienvenue sur BALIKA ERP v700', '15/01/2026'))

init_db()

# ==============================================================================
# 3. CHARGEMENT DES DONNÉES & CSS
# ==============================================================================
C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = "BALIKA", "Bienvenue", 2850.0, "", "", "", "ACTIF"

if st.session_state.auth:
    res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status FROM config WHERE ent_id=?", 
                 (st.session_state.ent_id,), fetch=True)
    if res:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = res[0]
        if C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
            st.error("🚨 VOTRE COMPTE EST SUSPENDU. VEUILLEZ CONTACTER L'ADMINISTRATEUR.")
            st.stop()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; }}
    h1, h2, h3, p, label {{ text-align: center !important; font-family: 'Inter', sans-serif; }}

    /* Marquee Styles */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #000; color: #FF8C00;
        padding: 12px 0; position: fixed; top: 0; left: 0; z-index: 9999;
        border-bottom: 3px solid #FF8C00;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap; font-weight: bold; font-size: 18px;
        animation: scroll 20s linear infinite;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Blue Buttons */
    .stButton>button {{
        background: linear-gradient(135deg, #0044ff, #0088ff) !important;
        color: white !important; border-radius: 12px; height: 50px;
        width: 100%; font-weight: bold; border: none; margin-bottom: 10px;
    }}

    /* Total Colored Frame */
    .total-frame {{
        border: 5px solid #FF8C00; background: #000; padding: 25px;
        border-radius: 20px; color: #00FF00; font-size: 35px; font-weight: 900;
        margin: 20px 0; text-shadow: 2px 2px #000;
    }}

    /* Watch Style */
    .watch-box {{
        background: #000; color: #FF8C00; padding: 15px 40px; border-radius: 50px;
        font-size: 26px; font-weight: bold; display: inline-block;
        border: 2px solid #FF8C00; margin-top: 10px;
    }}

    /* Mobile Adjustment */
    @media (max-width: 768px) {{
        .total-frame {{ font-size: 24px; }}
        [data-testid="column"] {{ width: 100% !important; min-width: 100% !important; }}
    }}
    </style>
    
    <div class="marquee-container">
        <div class="marquee-text">🚀 {C_NOM} | 💹 TAUX: {C_TX} CDF | 📢 {C_MSG}</div>
    </div>
    <div style="margin-top: 100px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. INSCRIPTION AVEC DÉTAILS COMPLETS
# ==============================================================================
if not st.session_state.auth:
    _, center_col, _ = st.columns([0.1, 0.8, 0.1])
    with center_col:
        st.title("BALIKA ERP - ACCÈS")
        tab_log, tab_reg = st.tabs(["SE CONNECTER", "CRÉER UN COMPTE"])
        
        with tab_log:
            u_in = st.text_input("Identifiant").lower().strip()
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU DASHBOARD"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if res and make_hashes(p_in) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("Accès refusé.")
        
        with tab_reg:
            with st.form("inscription"):
                st.subheader("Formulaire d'Abonnement")
                r_nom_ent = st.text_input("Nom de l'Entreprise / Boutique")
                r_tel = st.text_input("Numéro de Téléphone (WhatsApp)")
                r_adr = st.text_input("Adresse Physique")
                r_user = st.text_input("Identifiant Admin (ex: boss)").lower().strip()
                r_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON COMPTE MAINTENANT"):
                    if r_nom_ent and r_user and r_pass and r_tel:
                        eid = f"ENT-{random.randint(1000, 9999)}"
                        date_c = datetime.now().strftime("%d/%m/%Y")
                        run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                               (r_user, make_hashes(r_pass), "ADMIN", eid, r_tel))
                        run_db("INSERT INTO config (ent_id, nom_ent, tel, adresse, taux, message, date_inscription) VALUES (?,?,?,?,?,?,?)", 
                               (eid, r_nom_ent.upper(), r_tel, r_adr, 2850.0, "Bienvenue", date_c))
                        st.success("✅ Compte créé avec succès ! Connectez-vous.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. SIDEBAR (NAVIGATION)
# ==============================================================================
with st.sidebar:
    u_pic = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if u_pic and u_pic[0][0]: st.image(u_pic[0][0], width=120)
    else: st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 GESTION ABONNÉS", "📊 RAPPORTS HQ", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 QUITTER", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. ACCUEIL (MONTRE & DATE)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"ERP {C_NOM}")
    now = datetime.now()
    st.markdown(f"""
        <center>
            <div class="watch-box">
                ⌚ {now.strftime('%H:%M:%S')} | 📅 {now.strftime('%d/%m/%Y')}
            </div>
        </center>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    v_val = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES TOTALES", f"{v_val:,.2f} $")
    d_val = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES CLIENTS", f"{d_val:,.2f} $", delta_color="inverse")
    s_val = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES STOCK", s_val)

# ==============================================================================
# 7. SUPER-ADMIN : GESTION DES ABONNÉS (DÉTAILLÉ)
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 TABLEAU DE COMMANDES SaaS")
    
    # Message Défilant Global (Seul l'admin maître contrôle cela ici)
    with st.expander("📢 MODIFIER LE MESSAGE DÉFILANT GLOBAL"):
        new_global_msg = st.text_input("Nouveau message pour toutes les entreprises")
        if st.button("DIFFUSER LE MESSAGE"):
            run_db("UPDATE config SET message=?", (new_global_msg,))
            st.success("Message mis à jour pour tous les abonnés !")
            st.rerun()

    st.write("---")
    st.subheader("Détails des Clients")
    # Récupération des détails demandés : Entreprise, Tel, Date Inscription, Status
    clients = run_db("SELECT ent_id, nom_ent, tel, status, date_inscription, adresse FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    for eid, ename, etel, estat, edate, eadr in clients:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.write(f"🏢 **{ename}**")
                st.write(f"📞 {etel} | 📍 {eadr}")
                st.write(f"🗓️ Inscrit le : `{edate}` | ID : `{eid}`")
            
            with c2:
                status_color = "green" if estat == "ACTIF" else "red"
                st.markdown(f"<h4 style='color:{status_color}'>{estat}</h4>", unsafe_allow_html=True)
                
            with c3:
                # PAUSE / PLAY
                label = "⏸️ METTRE EN PAUSE" if estat == "ACTIF" else "▶️ RÉACTIVER"
                if st.button(label, key=f"btn_{eid}"):
                    new_s = "PAUSE" if estat == "ACTIF" else "ACTIF"
                    run_db("UPDATE config SET status=? WHERE ent_id=?", (new_s, eid))
                    st.rerun()
                
                # SUPPRESSION
                if st.button("🗑️ SUPPRIMER COMPTE", key=f"del_{eid}"):
                    run_db("DELETE FROM config WHERE ent_id=?", (eid,))
                    run_db("DELETE FROM users WHERE ent_id=?", (eid,))
                    st.warning(f"Compte {ename} supprimé.")
                    st.rerun()

# ==============================================================================
# 8. CAISSE (A4 / 80MM / CADRE TOTAL)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        col_c1, col_c2 = st.columns(2)
        v_monnaie = col_c1.selectbox("Devise", ["USD", "CDF"])
        v_format = col_c2.selectbox("Format d'impression", ["80mm", "A4"])
        
        # Sélection Articles
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        cs, cb = st.columns([3, 1])
        choix = cs.selectbox("Chercher article", ["---"] + list(p_map.keys()))
        if cb.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()

        if st.session_state.panier:
            total_v = 0.0
            lignes = []
            st.write("---")
            for art, qte in list(st.session_state.panier.items()):
                px_b, dv_b = p_map[art]['px'], p_map[art]['dv']
                if dv_b == "USD" and v_monnaie == "CDF": px_c = px_b * C_TX
                elif dv_b == "CDF" and v_monnaie == "USD": px_c = px_b / C_TX
                else: px_c = px_b
                
                stot = px_c * qte
                total_v += stot
                lignes.append({"art": art, "qte": qte, "pu": px_c, "st": stot})
                
                c1, c2, c3 = st.columns([3, 1, 0.5])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_map[art]['stk'], value=qte, key=f"q_{art}")
                if c3.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
            
            # CADRE TOTAL COLORÉ (v192)
            st.markdown(f'<div class="total-frame">NET À PAYER : {total_v:,.2f} {v_monnaie}</div>', unsafe_allow_html=True)
            
            c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_paye = st.number_input("VERSEMENT CLIENT", value=float(total_v))
            
            if st.button("💾 ENREGISTRER & GÉNÉRER FACTURE"):
                ref = f"FAC-{random.randint(1000, 9999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = total_v - c_paye
                
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (ref, c_nom, total_v, c_paye, reste, v_monnaie, dt, USER, ENT_ID, json.dumps(lignes)))
                
                if reste > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", 
                           (c_nom, reste, v_monnaie, ref, ENT_ID, json.dumps([{"date": dt, "paye": c_paye}])))
                
                for i in lignes:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": ref, "cl": c_nom, "tot": total_v, "pay": c_paye, "dev": v_monnaie, "items": lignes, "date": dt, "fmt": v_format}
                st.session_state.panier = {}
                st.rerun()
    else:
        # AFFICHAGE DE LA FACTURE
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        style = "fac-80" if f['fmt'] == "80mm" else "fac-a4"
        html = f"""
        <div class="{style}">
            <center><h2>{C_NOM}</h2><p>{C_ADR}<br>{C_TEL}</p></center>
            <hr>
            <p><b>REF: {f['ref']}</b><br>Client: {f['cl']}<br>Date: {f['date']}</p>
            <table style="width:100%; text-align:left;">
                <tr style="border-bottom:1px solid #000"><th>Désignation</th><th>Q</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Versé: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER MAINTENANT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ==============================================================================
# 9. MON PROFIL (MODIFIER USER, PASSWORD, PHOTO)
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE PERSONNEL")
    info = run_db("SELECT full_name, telephone, photo FROM users WHERE username=?", (USER,), fetch=True)[0]
    
    with st.container(border=True):
        st.subheader("Sécurité")
        new_u = st.text_input("Nouvel Identifiant (Username)", value=USER)
        p1, p2 = st.columns(2)
        new_p = p1.text_input("Nouveau mot de passe", type="password")
        conf_p = p2.text_input("Confirmer mot de passe", type="password")
        
        st.write("---")
        st.subheader("Détails Personnels")
        f_name = st.text_input("Nom complet", value=info[0] if info[0] else "")
        f_tel = st.text_input("Téléphone perso", value=info[1] if info[1] else "")
        f_img = st.file_uploader("Modifier ma photo", type=['png', 'jpg', 'jpeg'])
        
        if st.button("💾 SAUVEGARDER LES MODIFICATIONS"):
            if new_p and new_p == conf_p:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
            if new_u != USER:
                try:
                    run_db("UPDATE users SET username=? WHERE username=?", (new_u, USER))
                    st.session_state.user = new_u
                except: st.error("ID déjà pris.")
            if f_img:
                run_db("UPDATE users SET photo=? WHERE username=?", (f_img.getvalue(), USER))
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (f_name, f_tel, USER))
            st.success("Profil mis à jour !")
            st.rerun()

# ==============================================================================
# 10. STOCK (AJOUTER / MODIFIER PRIX / SUPPRIMER)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DU STOCK")
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("add_s"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            na = c1.text_input("Désignation")
            nq = c2.number_input("Quantité", 1)
            np = c3.number_input("Prix")
            nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in items:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
            col1.write(f"**{sn}**")
            col2.write(f"Dispo: `{sq}`")
            nx = col3.number_input("Modifier Prix", value=float(sp), key=f"px_{sid}")
            if nx != sp:
                if col3.button("💾", key=f"s_{sid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (nx, sid))
                    st.rerun()
            if col4.button("🗑️", key=f"del_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ==============================================================================
# 11. DETTES (PAIEMENT PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 SUIVI DES DETTES")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    for did, dc, dm, dd, dr, dh in d_list:
        with st.expander(f"🔴 {dc} : {dm:,.2f} {dd}"):
            st.table(pd.DataFrame(json.loads(dh)))
            pv = st.number_input("Nouveau versement", 0.0, float(dm), key=f"v_{did}")
            if st.button("ENCAISSER", key=f"b_{did}"):
                nm = dm - pv
                h = json.loads(dh); h.append({"date": datetime.now().strftime("%d/%m"), "paye": pv})
                if nm <= 0.01: run_db("DELETE FROM dettes WHERE id=?", (did,))
                else: run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (pv, pv, dr, ENT_ID))
                st.rerun()

# ==============================================================================
# 12. CONFIGURATION (ENTREPRISE & VENDEURS)
# ==============================================================================
elif st.session_state.page == "CONFIG":
    st.header("⚙️ RÉGLAGES")
    with st.expander("🏢 INFOS DE LA BOUTIQUE"):
        with st.form("cfg"):
            en = st.text_input("Nom Société", C_NOM)
            ea = st.text_input("Adresse", C_ADR)
            et = st.text_input("Tél", C_TEL)
            ex = st.number_input("Taux de change", value=C_TX)
            eh = st.text_area("En-tête Facture", C_ENTETE)
            if st.form_submit_button("SAUVER"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, entete_fac=? WHERE ent_id=?", 
                       (en.upper(), ea, et, ex, eh, ENT_ID))
                st.rerun()

elif st.session_state.page == "VENDEURS":
    st.header("👥 MES VENDEURS")
    with st.form("v"):
        vu = st.text_input("Identifiant").lower(); vp = st.text_input("Pass", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'VENDEUR', ?)", (vu, make_hashes(vp), ENT_ID))
            st.rerun()
    
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff: st.write(f"👤 {s[0].upper()}")

elif st.session_state.page == "RAPPORTS":
    st.header("📊 JOURNAL DES VENTES")
    vd = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if vd:
        st.dataframe(pd.DataFrame(vd, columns=["Date", "Ref", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER LE JOURNAL"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
