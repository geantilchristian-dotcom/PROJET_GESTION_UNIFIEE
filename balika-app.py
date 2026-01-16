import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & CORE ENGINE
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP CLOUD v360", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation rigoureuse du State
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'ent_id' not in st.session_state: st.session_state.ent_id = ""
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'panier' not in st.session_state: st.session_state.panier = {}
if 'last_fac' not in st.session_state: st.session_state.last_fac = None

# Moteur de Base de Données sécurisé
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_cloud.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL") 
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Critique Base de Données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. ARCHITECTURE DES TABLES (SCHÉMA COMPLET)
# ==============================================================================
def init_db():
    # Table des utilisateurs avec identité complète pour les vendeurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT,
                nom_complet TEXT DEFAULT '',
                telephone TEXT DEFAULT '')""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT)""")
    
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
                ent_id TEXT, 
                details TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")
    
    # Table Config étendue : app_name, entete_fac
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL, 
                message TEXT, 
                status TEXT DEFAULT 'ACTIF',
                app_name TEXT DEFAULT 'BALIKA CLOUD',
                entete_fac TEXT DEFAULT '')""")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM', 'MAITRE', '000')", (make_hashes("admin123"),))
        run_db("INSERT INTO config VALUES ('SYSTEM', 'BALIKA CLOUD HQ', 'Admin Central', '000', 2850.0, 'Système Opérationnel', 'ACTIF', 'BALIKA ERP CLOUD', 'ADMINISTRATION CENTRALE')")

init_db()

# ==============================================================================
# 3. VERIFICATION DE SÉCURITÉ (LE VERROU PAUSE)
# ==============================================================================
def security_check():
    if st.session_state.auth and st.session_state.role != "SUPER_ADMIN":
        res = run_db("SELECT status FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if res and res[0][0] == 'PAUSE':
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.warning("⚠️ VOTRE ACCÈS A ÉTÉ SUSPENDU. Veuillez contacter le service facturation BALIKA.")
            st.stop()

security_check()

# ==============================================================================
# 4. DESIGN ENGINE (CSS & RESPONSIVE)
# ==============================================================================
# Récupération du nom global défini par le Super Admin
sys_cfg = run_db("SELECT app_name FROM config WHERE ent_id='SYSTEM'", fetch=True)
GLOBAL_APP_NAME = sys_cfg[0][0] if sys_cfg else "BALIKA CLOUD"

if st.session_state.auth:
    c_res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = c_res[0] if c_res else ("BALIKA", "Bienvenue", 2850.0, "", "", "")
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = GLOBAL_APP_NAME, "Gérez votre business partout", 2850.0, "", "", ""

st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        text-align: center !important;
    }}
    
    .login-container {{
        max-width: 450px; margin: 30px auto; padding: 40px;
        border: 2px solid #FF8C00; border-radius: 30px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        background: #FFFFFF;
    }}
    
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 15px; height: 55px;
        font-weight: bold; border: none; width: 100%; font-size: 18px;
    }}

    .total-frame {{
        border: 4px solid #FF8C00; background: #FFF; padding: 25px;
        border-radius: 20px; font-size: 35px; color: #FF4500;
        font-weight: 900; margin: 20px auto; max-width: 500px;
        box-shadow: 0 5px 15px rgba(255,140,0,0.2);
    }}

    .marquee-container {{
        width: 100%; overflow: hidden; background: #000000; color: #FFB300;
        padding: 15px 0; position: fixed; top: 0; left: 0; z-index: 9999;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: marquee 25s linear infinite; font-size: 18px; font-weight: bold;
    }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Tableaux Administratifs */
    .admin-table {{
        width: 100%; border-collapse: collapse; margin-top: 20px;
        border: 1px solid #333;
    }}
    .admin-table th {{ background: #f2f2f2; border: 1px solid #333; padding: 8px; }}
    .admin-table td {{ border: 1px solid #333; padding: 8px; text-align: left; }}

    @media print {{
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], .stButton {{ display: none !important; }}
        .print-area {{ width: 100% !important; border: none !important; color: black !important; }}
    }}
    </style>
    <div class="marquee-container"><div class="marquee-text">✨ {GLOBAL_APP_NAME} | {C_NOM} : {C_MSG} | Taux : {C_TX}</div></div>
    <div style="margin-top: 100px;"></div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 5. ÉCRAN DE CONNEXION / INSCRIPTION
# ==============================================================================
if not st.session_state.auth:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown(f"<h1 style='color:#FF8C00'>{GLOBAL_APP_NAME}</h1>", unsafe_allow_html=True)
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/1160/1160119.png", width=100)
        
        tab_log, tab_reg = st.tabs(["🔑 CONNEXION", "🚀 NOUVEAU COMPTE"])
        
        with tab_log:
            with st.form("form_login"):
                u = st.text_input("Identifiant").lower().strip()
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ENTRER DANS LE CLOUD"):
                    user_data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
                    if user_data and make_hashes(p) == user_data[0][0]:
                        st.session_state.update({'auth':True, 'user':u, 'role':user_data[0][1], 'ent_id':user_data[0][2]})
                        st.rerun()
                    else: st.error("Accès refusé.")
        
        with tab_reg:
            with st.form("form_signup"):
                new_ent = st.text_input("Nom de l'Etablissement").upper().strip()
                new_u = st.text_input("Identifiant Admin").lower().strip()
                new_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON ESPACE"):
                    if new_ent and new_u and new_p:
                        if not run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True):
                            eid = f"E-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users VALUES (?, ?, 'ADMIN', ?, 'PROPRIO', '000')", (new_u, make_hashes(new_p), eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, status) VALUES (?, ?, 'ACTIF')", (eid, new_ent))
                            st.success("Compte créé ! Connectez-vous.")
                        else: st.error("Identifiant indisponible.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 6. SIDEBAR & NAVIGATION
# ==============================================================================
ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

with st.sidebar:
    st.markdown(f"### 🛡️ {USER.upper()}\n**{ROLE}**")
    st.write("---")
    if ROLE == "SUPER_ADMIN": menu = ["🌍 ABONNÉS", "📊 SYSTÈME", "⚙️ MON PROFIL"]
    elif ROLE == "ADMIN": menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "⚙️ MON PROFIL"]
    
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]; st.rerun()
    st.write("---")
    if st.button("🚪 QUITTER"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 7. LOGIQUE SUPER-ADMIN (GESTION DES COMPTES)
# ==============================================================================
if ROLE == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("🌍 Contrôle des Abonnés")
        clients = run_db("SELECT ent_id, nom_ent, status FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
        for c_id, c_nom, c_status in clients:
            with st.expander(f"{'🟢' if c_status=='ACTIF' else '🔴'} {c_nom}"):
                c1, c2 = st.columns(2)
                if c_status == 'ACTIF':
                    if c1.button("⏸️ PAUSE", key=f"p_{c_id}"):
                        run_db("UPDATE config SET status='PAUSE' WHERE ent_id=?", (c_id,)); st.rerun()
                else:
                    if c1.button("▶️ ACTIVER", key=f"a_{c_id}"):
                        run_db("UPDATE config SET status='ACTIF' WHERE ent_id=?", (c_id,)); st.rerun()
                if c2.button("🗑️ SUPPRIMER", key=f"d_{c_id}"):
                    run_db("DELETE FROM config WHERE ent_id=?", (c_id,))
                    run_db("DELETE FROM users WHERE ent_id=?", (c_id,))
                    st.rerun()

    elif st.session_state.page == "PROFIL":
        st.header("⚙️ Mon Accès Super-Admin")
        with st.form("f_sa"):
            new_u = st.text_input("Nouvel Identifiant Master", USER)
            new_p = st.text_input("Nouveau Mot de passe Master", type="password")
            new_app = st.text_input("Nom de l'Application", GLOBAL_APP_NAME)
            if st.form_submit_button("SAUVEGARDER"):
                if new_p: run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_u, make_hashes(new_p), USER))
                else: run_db("UPDATE users SET username=? WHERE username=?", (new_u, USER))
                run_db("UPDATE config SET app_name=? WHERE ent_id='SYSTEM'", (new_app,))
                st.session_state.user = new_u
                st.success("Système mis à jour"); st.rerun()
    st.stop()

# ==============================================================================
# 8. LOGIQUE CLIENT : CAISSE & FACTURES PRO
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 Terminal de Vente")
        v_devise = st.radio("Devise :", ["USD", "CDF"], horizontal=True)
        produits = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'prix': r[1], 'stock': r[2], 'dev': r[3]} for r in produits}
        
        choix = st.selectbox("Article", ["---"] + list(p_dict.keys()))
        if st.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1; st.rerun()
            
        if st.session_state.panier:
            net_a_payer = 0.0; list_details = []
            for art, qte in list(st.session_state.panier.items()):
                p_u_b = p_dict[art]['prix']
                p_u = p_u_b * C_TX if p_dict[art]['dev']=="USD" and v_devise=="CDF" else (p_u_b / C_TX if p_dict[art]['dev']=="CDF" and v_devise=="USD" else p_u_b)
                stot = p_u * qte; net_a_payer += stot
                list_details.append({"art": art, "qte": qte, "pu": p_u, "st": stot})
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_dict[art]['stock'], value=qte, key=f"q_{art}")
                if c3.button("❌", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-frame">TOTAL : {net_a_payer:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            c_nom = st.text_input("CLIENT", "COMPTANT").upper()
            c_paye = st.number_input("VERSEMENT", value=float(net_a_payer))
            
            if st.button("💾 FINALISER LA VENTE"):
                v_ref = f"FAC-{random.randint(1000, 9999)}"
                v_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", (v_ref, c_nom, net_a_payer, c_paye, net_a_payer-c_paye, v_devise, v_date, USER, ENT_ID, json.dumps(list_details)))
                if net_a_payer-c_paye > 0: run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", (c_nom, net_a_payer-c_paye, v_devise, v_ref, ENT_ID, json.dumps([{"date":v_date, "paye":c_paye}])))
                for i in list_details: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                st.session_state.last_fac = {"ref": v_ref, "cl": c_nom, "tot": net_a_payer, "pay": c_paye, "dev": v_devise, "items": list_details, "date": v_date}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        fmt = st.radio("Format :", ["80mm", "A4"], horizontal=True)
        
        # Facture Administrative avec Tableaux et Sceau
        style = "width:350px; font-size:12px;" if fmt=="80mm" else "width:100%; max-width:800px; padding:40px; border:1px solid #eee;"
        html = f"""
        <div class="print-area" style="background:white; color:black; margin:auto; {style} font-family: sans-serif;">
            <div style="border:2px solid black; padding:10px; margin-bottom:10px;">
                <h2 align="center" style="margin:0;">{C_NOM}</h2>
                <p align="center"><b>{C_ENTETE}</b><br>{C_ADR} | {C_TEL}</p>
            </div>
            <table style="width:100%;">
                <tr><td><b>Réf:</b> {f['ref']}</td><td align="right"><b>Date:</b> {f['date']}</td></tr>
                <tr><td><b>Client:</b> {f['cl']}</td><td align="right"><b>Vendeur:</b> {USER}</td></tr>
            </table>
            <table class="admin-table">
                <tr><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['pu']:,.0f}</td><td>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <h3 align="right" style="margin-top:20px;">NET À PAYER : {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Payé : {f['pay']} | Reste : {f['tot']-f['pay']}</p>
            <div style="margin-top:50px;">
                <table style="width:100%;">
                    <tr>
                        <td align="center">Signature Client<br><br>..........</td>
                        <td align="center">Sceau et Signature<br><br><b>{C_NOM}</b></td>
                    </tr>
                </table>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER MAINTENANT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if st.button("🔄 RETOUR"): st.session_state.last_fac = None; st.rerun()

# ==============================================================================
# 9. GESTION VENDEURS (IDENTITÉ COMPLÈTE)
# ==============================================================================
elif st.session_state.page == "VENDEURS":
    st.header("👥 Personnel & Accès")
    with st.expander("➕ CRÉER UN COMPTE VENDEUR"):
        with st.form("nv"):
            v_nom_c = st.text_input("Nom Complet de l'Agent").upper()
            v_tel = st.text_input("Téléphone Agent")
            v_u = st.text_input("Identifiant Connexion").lower().strip()
            v_p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("VALIDER"):
                if v_nom_c and v_u and v_p:
                    run_db("INSERT INTO users VALUES (?,?,'VENDEUR',?,?,?)", (v_u, make_hashes(v_p), ENT_ID, v_nom_c, v_tel))
                    st.success("Vendeur ajouté"); st.rerun()

    staff = run_db("SELECT username, nom_complet, telephone FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for su, sn, stel in staff:
        with st.expander(f"👤 {sn} ({su})"):
            with st.form(f"mod_{su}"):
                m_nom = st.text_input("Nom", sn)
                m_tel = st.text_input("Tél", stel)
                m_pass = st.text_input("Nouveau mot de passe (si changement)", type="password")
                if st.form_submit_button("MODIFIER"):
                    if m_pass: run_db("UPDATE users SET nom_complet=?, telephone=?, password=? WHERE username=?", (m_nom, m_tel, make_hashes(m_pass), su))
                    else: run_db("UPDATE users SET nom_complet=?, telephone=? WHERE username=?", (m_nom, m_tel, su))
                    st.rerun()
                if st.form_submit_button("SUPPRIMER"): run_db("DELETE FROM users WHERE username=?", (su,)); st.rerun()

# ==============================================================================
# 10. CONFIGURATION & PROFIL (IDENTIFIANTS + EN-TETE)
# ==============================================================================
elif st.session_state.page == "CONFIG" or st.session_state.page == "PROFIL":
    st.header("⚙️ Paramètres")
    with st.form("my_acc"):
        st.subheader("🔑 Mes Accès")
        new_my_u = st.text_input("Mon Identifiant", USER)
        new_my_p = st.text_input("Nouveau Mot de passe", type="password")
        if st.form_submit_button("CHANGER MES ACCÈS"):
            if new_my_p: run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_my_u, make_hashes(new_my_p), USER))
            else: run_db("UPDATE users SET username=? WHERE username=?", (new_my_u, USER))
            st.session_state.user = new_my_u; st.rerun()

    if ROLE == "ADMIN":
        with st.form("ent_acc"):
            st.subheader("🏢 Infos de l'Entreprise")
            en = st.text_input("Nom", C_NOM); ea = st.text_input("Adresse", C_ADR)
            et = st.text_input("Tél", C_TEL); etx = st.number_input("Taux", value=C_TX)
            eh = st.text_area("En-tête de Facture (Administratif)", C_ENTETE)
            emsg = st.text_area("Message défilant", C_MSG)
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, entete_fac=? WHERE ent_id=?", (en, ea, et, etx, emsg, eh, ENT_ID))
                st.rerun()

# [Les sections STOCK, DETTES et RAPPORTS restent identiques à votre code v310 fourni, intégrées ici]
elif st.session_state.page == "STOCK":
    st.title("📦 Inventaire & Prix")
    with st.form("ajout_stock"):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        n_art = c1.text_input("Désignation")
        n_qte = c2.number_input("Qté", 1)
        n_px = c3.number_input("Prix")
        n_dv = c4.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("➕ ENREGISTRER"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n_art.upper(), n_qte, n_px, n_dv, ENT_ID)); st.rerun()
    inventaire = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for p_id, p_nom, p_stock, p_prix, p_dev in inventaire:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        col1.write(f"**{p_nom}**"); col2.write(f"Stock: `{p_stock}`")
        new_p = col3.number_input("Prix", value=float(p_prix), key=f"p_{p_id}")
        if col3.button("MAJ", key=f"u_{p_id}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_p, p_id)); st.rerun()
        if col4.button("🗑️", key=f"d_{p_id}"): run_db("DELETE FROM produits WHERE id=?", (p_id,)); st.rerun()

elif st.session_state.page == "DETTES":
    st.title("📉 Dettes")
    liste = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    for d_id, d_cl, d_mt, d_dv, d_rf, d_hi in liste:
        with st.expander(f"🔴 {d_cl} : {d_mt} {d_dv}"):
            v = st.number_input("Verser", 0.0, float(d_mt), key=f"v_{d_id}")
            if st.button("Valider", key=f"b_{d_id}"):
                nm = d_mt - v; h = json.loads(d_hi); h.append({"date":datetime.now().strftime("%d/%m"), "paye":v})
                if nm <= 0: run_db("DELETE FROM dettes WHERE id=?", (d_id,))
                else: run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h), d_id))
                st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.title("📊 Rapports")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Payé", "Reste", "Dev", "Vendeur"]))
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

elif st.session_state.page == "ACCUEIL":
    st.header(f"Bienvenue sur {GLOBAL_APP_NAME}")
    st.write(f"Session : {USER.upper()} | Boutique : {C_NOM}")
