import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & CORE SaaS (v350)
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP v350", layout="wide", initial_sidebar_state="collapsed")

# États de session
for key, val in {
    'auth': False, 'user': "", 'role': "", 'ent_id': "", 
    'page': "ACCUEIL", 'panier': {}, 'last_fac': None
}.items():
    if key not in st.session_state: st.session_state[key] = val

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_v350_cloud.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. SCHÉMA DE BASE DE DONNÉES ÉTENDU
# ==============================================================================
def init_db():
    # Table utilisateurs avec info identité vendeur
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        role TEXT, 
        ent_id TEXT,
        nom_complet TEXT,
        telephone TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        designation TEXT, stock_actuel INTEGER, 
        prix_vente REAL, devise TEXT, ent_id TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, 
        devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        client TEXT, montant REAL, devise TEXT, ref_v TEXT, 
        ent_id TEXT, historique TEXT)""")
    
    # Ajout du champ app_name modifiable par le Super Admin
    run_db("""CREATE TABLE IF NOT EXISTS config (
        ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
        tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
        app_name TEXT DEFAULT 'BALIKA CLOUD')""")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM', 'ADMINISTRATEUR', '000')", (make_hashes("admin123"),))
        run_db("INSERT INTO config (ent_id, nom_ent, app_name) VALUES ('SYSTEM', 'BALIKA HQ', 'BALIKA CLOUD ERP')")

init_db()

# ==============================================================================
# 3. DESIGN CENTRALISÉ & OPTIMISATION MOBILE
# ==============================================================================
# Récupération du nom global de l'app (défini par le Super Admin)
sys_cfg = run_db("SELECT app_name FROM config WHERE ent_id='SYSTEM'", fetch=True)
GLOBAL_APP_NAME = sys_cfg[0][0] if sys_cfg else "BALIKA CLOUD"

if st.session_state.auth:
    c_res = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL = c_res[0] if c_res else ("Boutique", "Bienvenue", 2850.0, "", "")
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL = GLOBAL_APP_NAME, "Connexion", 2850.0, "", ""

st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    body, [data-testid="stAppViewContainer"] {{ 
        background-color: #FFFFFF !important; color: #000000 !important; 
        text-align: center !important; 
    }}
    
    /* Centrage de tous les éléments Streamlit */
    .block-container {{ padding-top: 5rem !important; text-align: center !important; }}
    [data-testid="stForm"] {{ margin: 0 auto !important; max-width: 500px !important; }}
    .stDataFrame, .stTable {{ margin: 0 auto !important; }}
    
    /* Design Mobile Luminosité & Contraste */
    @media (max-width: 768px) {{
        input, button {{ font-size: 18px !important; }}
        .marquee-text {{ font-size: 14px !important; }}
    }}

    .login-box {{
        max-width: 420px; margin: 0 auto; padding: 25px;
        border: 2px solid #FF8C00; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }}

    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 15px; height: 55px;
        font-weight: bold; width: 100% !important; border: none;
    }}

    .total-frame {{
        border: 4px solid #FF8C00; background: #FFF; padding: 20px;
        border-radius: 20px; font-size: 32px; color: #FF4500;
        font-weight: 900; margin: 20px auto; max-width: 500px;
    }}

    .marquee-container {{
        width: 100%; overflow: hidden; background: #000; color: #FF8C00;
        padding: 15px 0; position: fixed; top: 0; left: 0; z-index: 9999;
    }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 20s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    
    /* Facture Centrée */
    .bill-card {{
        background: #FFF; color: #000; padding: 30px; border: 1px solid #CCC;
        width: 380px; margin: 20px auto; font-family: 'monospace';
        text-align: center !important; box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🚀 {GLOBAL_APP_NAME} | {C_NOM} : {C_MSG}</div></div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 4. PORTAIL D'ACCÈS (LOGIN CENTRÉ)
# ==============================================================================
if not st.session_state.auth:
    st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
    st.markdown(f"# {GLOBAL_APP_NAME}")
    
    col_l, col_c, col_r = st.columns([0.1, 1, 0.1])
    with col_c:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 CONNEXION", "📝 NOUVEAU COMPTE"])
        
        with tab_log:
            with st.form("f_login"):
                u = st.text_input("Identifiant").lower().strip()
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("SE CONNECTER"):
                    res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
                    if res and make_hashes(p) == res[0][0]:
                        status = run_db("SELECT status FROM config WHERE ent_id=?", (res[0][2],), fetch=True)
                        if res[0][1] == 'SUPER_ADMIN' or (status and status[0][0] == 'ACTIF'):
                            st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                            st.rerun()
                        else: st.error("Compte suspendu.")
                    else: st.error("Erreur d'accès.")
        
        with tab_reg:
            with st.form("f_reg"):
                ent_n = st.text_input("Nom de l'Etablissement").upper()
                adm_u = st.text_input("Identifiant Admin souhaité").lower()
                adm_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON ESPACE"):
                    if ent_n and adm_u and adm_p:
                        if not run_db("SELECT * FROM users WHERE username=?", (adm_u,), fetch=True):
                            new_eid = f"ID-{random.randint(100,999)}"
                            run_db("INSERT INTO users VALUES (?,?,'ADMIN',?,'Propriétaire','000')", (adm_u, make_hashes(adm_p), new_eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, status) VALUES (?,?,'ACTIF')", (new_eid, ent_n))
                            st.success("Compte créé avec succès !")
                        else: st.error("Identifiant déjà pris.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 5. NAVIGATION SIDEBAR
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
# 6. ESPACE SUPER-ADMIN (GESTION DU NOM DE L'APP)
# ==============================================================================
if ROLE == "SUPER_ADMIN":
    if st.session_state.page == "PROFIL":
        st.header("👤 Mon Compte Super-Admin")
        with st.form("f_sys_adm"):
            new_sys_u = st.text_input("Nouvel Identifiant Master", USER)
            new_sys_p = st.text_input("Nouveau Mot de passe Master", type="password")
            new_app_name = st.text_input("Nom Global de l'Application", GLOBAL_APP_NAME)
            if st.form_submit_button("METTRE À JOUR LE SYSTÈME"):
                if new_sys_p:
                    run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_sys_u, make_hashes(new_sys_p), USER))
                run_db("UPDATE config SET app_name=? WHERE ent_id='SYSTEM'", (new_app_name,))
                st.session_state.user = new_sys_u
                st.success("Système mis à jour !"); st.rerun()

    elif st.session_state.page == "ABONNÉS":
        st.header("🌍 Gestion des Clients SaaS")
        for eid, nom, stat in run_db("SELECT ent_id, nom_ent, status FROM config WHERE ent_id!='SYSTEM'", fetch=True):
            with st.expander(f"{nom} ({stat})"):
                if stat == 'ACTIF':
                    if st.button(f"⏸️ BLOQUER {nom}", key=f"b_{eid}"):
                        run_db("UPDATE config SET status='PAUSE' WHERE ent_id=?", (eid,)); st.rerun()
                else:
                    if st.button(f"▶️ RÉACTIVER {nom}", key=f"a_{eid}"):
                        run_db("UPDATE config SET status='ACTIF' WHERE ent_id=?", (eid,)); st.rerun()
    st.stop()

# ==============================================================================
# 7. PAGES CLIENT : CAISSE & FACTURE (IMP/PARTAGER/ENREG)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 Terminal de Vente")
        devise = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
        
        choix = st.selectbox("Choisir Article", ["---"] + list(p_map.keys()))
        if st.button("📥 AJOUTER"):
            if choix != "---": st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1; st.rerun()
            
        if st.session_state.panier:
            total = 0.0; details = []
            for art, qte in list(st.session_state.panier.items()):
                p_b = p_map[art]['p']
                p_u = p_b * C_TX if p_map[art]['d']=="USD" and devise=="CDF" else (p_b / C_TX if p_map[art]['d']=="CDF" and devise=="USD" else p_b)
                stot = p_u * qte; total += stot
                details.append({'art': art, 'qte': qte, 'pu': p_u, 'st': stot})
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_map[art]['s'], value=qte, key=f"q_{art}")
                if c3.button("❌", key=f"r_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-frame">À PAYER : {total:,.2f} {devise}</div>', unsafe_allow_html=True)
            cl_n = st.text_input("NOM CLIENT", "CLIENT COMPTANT").upper()
            paye = st.number_input("REÇU", 0.0, value=float(total))
            
            if st.button("💳 VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(1000, 9999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", (ref, cl_n, total, paye, total-paye, devise, dt, USER, ENT_ID, json.dumps(details)))
                if total-paye > 0: run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", (cl_n, total-paye, devise, ref, ENT_ID, json.dumps([{"date":dt, "p":paye}])))
                for d in details: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (d['qte'], d['art'], ENT_ID))
                st.session_state.last_fac = {"ref": ref, "cl": cl_n, "tot": total, "pay": paye, "dev": devise, "items": details, "date": dt}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.header("📄 Facture Prête")
        
        # HTML de la facture (Centré)
        html_bill = f"""
        <div id="bill" class="bill-card">
            <h2 style="margin:0;">{C_NOM}</h2>
            <p>{C_ADR}<br>Tél: {C_TEL}</p>
            <hr>
            <p align="left">REF: {f['ref']}<br>Client: {f['cl']}<br>Date: {f['date']}</p>
            <table style="width:100%; text-align:left;">
                <tr style="border-bottom:1px solid #000"><th>Désignation</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">NET À PAYER : {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Versé: {f['pay']} | Reste: {f['tot']-f['pay']}</p>
        </div>
        """
        st.markdown(html_bill, unsafe_allow_html=True)
        
        # Boutons d'action : Partager, Imprimer, Enregistrer
        c1, c2, c3, c4 = st.columns(4)
        c1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        
        # Partager (Lien WhatsApp Web)
        whatsapp_link = f"https://wa.me/?text=Facture%20{C_NOM}%20Ref%20{f['ref']}%20Total%20{f['tot']}%20{f['dev']}"
        c2.markdown(f'<a href="{whatsapp_link}" target="_blank"><button style="width:100%; height:50px; background:#25D366; color:white; border-radius:12px; border:none; font-weight:bold;">📲 PARTAGER</button></a>', unsafe_allow_html=True)
        
        # Enregistrer (Téléchargement HTML)
        b64 = base64.b64encode(html_bill.encode()).decode()
        c3.markdown(f'<a href="data:text/html;base64,{b64}" download="Facture_{f["ref"]}.html"><button style="width:100%; height:50px; background:#444; color:white; border-radius:12px; border:none; font-weight:bold;">💾 ENREGISTRER</button></a>', unsafe_allow_html=True)
        
        if c4.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()

# ==============================================================================
# 8. GESTION DES VENDEURS PAR LE PATRON (ACCÈS TOTAL)
# ==============================================================================
elif st.session_state.page == "VENDEURS":
    st.header("👥 Gestion du Personnel")
    
    # Création vendeur
    with st.expander("➕ AJOUTER UN NOUVEAU VENDEUR"):
        with st.form("new_v"):
            v_nom_c = st.text_input("Nom Complet de l'agent").upper()
            v_tel = st.text_input("Numéro de Téléphone")
            v_user = st.text_input("Identifiant de connexion").lower().strip()
            v_pass = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("VALIDER L'IDENTITÉ ET CRÉER LE COMPTE"):
                if v_nom_c and v_tel and v_user and v_pass:
                    if not run_db("SELECT * FROM users WHERE username=?", (v_user,), fetch=True):
                        run_db("INSERT INTO users VALUES (?,?,'VENDEUR',?,?,?)", (v_user, make_hashes(v_pass), ENT_ID, v_nom_c, v_tel))
                        st.success("Vendeur créé."); st.rerun()
                    else: st.error("Identifiant déjà utilisé.")
    
    st.write("---")
    # Liste et Modification des vendeurs
    staff = run_db("SELECT username, nom_complet, telephone FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s_u, s_n, s_t in staff:
        with st.expander(f"👤 {s_n} ({s_u})"):
            with st.form(f"mod_{s_u}"):
                mod_nom = st.text_input("Modifier Nom Complet", s_n)
                mod_tel = st.text_input("Modifier Téléphone", s_t)
                mod_pass = st.text_input("Nouveau Mot de passe (Laisser vide si inchangé)", type="password")
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 SAUVEGARDER"):
                    if mod_pass:
                        run_db("UPDATE users SET nom_complet=?, telephone=?, password=? WHERE username=?", (mod_nom, mod_tel, make_hashes(mod_pass), s_u))
                    else:
                        run_db("UPDATE users SET nom_complet=?, telephone=? WHERE username=?", (mod_nom, mod_tel, s_u))
                    st.success("Modifié !"); st.rerun()
                if c2.form_submit_button("🗑️ SUPPRIMER COMPTE"):
                    run_db("DELETE FROM users WHERE username=?", (s_u,)); st.rerun()

# ==============================================================================
# 9. CONFIGURATION PROFIL (ADMIN & VENDEUR)
# ==============================================================================
elif st.session_state.page == "CONFIG" or st.session_state.page == "PROFIL":
    st.header("⚙️ Paramètres & Profil")
    
    # Bloc 1 : Changer Identifiants
    with st.form("f_my_profil"):
        st.subheader("🔑 Sécurité du compte")
        new_my_u = st.text_input("Mon Identifiant", USER).lower().strip()
        new_my_p = st.text_input("Nouveau Mot de passe", type="password")
        if st.form_submit_button("METTRE À JOUR MES ACCÈS"):
            if new_my_p:
                run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_my_u, make_hashes(new_my_p), USER))
            else:
                run_db("UPDATE users SET username=? WHERE username=?", (new_my_u, USER))
            st.session_state.user = new_my_u
            st.success("Compte mis à jour !"); st.rerun()
            
    # Bloc 2 : Infos Entreprise (Admin uniquement)
    if ROLE == "ADMIN":
        with st.form("f_ent_cfg"):
            st.subheader("🏢 Infos Boutique")
            en = st.text_input("Nom de l'Etablissement", C_NOM)
            ea = st.text_input("Adresse", C_ADR); et = st.text_input("Tél", C_TEL)
            tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TX)
            ms = st.text_area("Message défilant", C_MSG)
            if st.form_submit_button("ENREGISTRER INFOS BOUTIQUE"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", (en.upper(), ea, et, tx, ms, ENT_ID))
                st.rerun()

# ==============================================================================
# 10. STOCK & RAPPORTS & DETTES (CENTRALISÉS)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 Inventaire")
    with st.form("f_add_p"):
        c1, c2, c3, c4 = st.columns([2,1,1,1])
        n = c1.text_input("Article")
        q = c2.number_input("Qté", 1)
        p = c3.number_input("Prix")
        d = c4.selectbox("Dev", ["USD", "CDF"])
        if st.form_submit_button("AJOUTER AU STOCK"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n.upper(), q, p, d, ENT_ID)); st.rerun()
    
    st.write("---")
    for r in run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        col1.write(f"**{r[1]}**")
        col2.write(f"Stock: {r[2]}")
        col3.write(f"{r[3]} {r[4]}")
        if col4.button("🗑️", key=f"del_{r[0]}"): run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

elif st.session_state.page == "DETTES":
    st.header("📉 Suivi des Dettes")
    dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    if not dettes: st.info("Aucune dette en cours.")
    for d_id, cl, mt, dv, rf, hi in dettes:
        with st.expander(f"🔴 {cl} : {mt:,.2f} {dv} (Réf: {rf})"):
            pay_tranche = st.number_input(f"Verser", 0.0, max_value=float(mt), key=f"t_{d_id}")
            if st.button("Valider Tranche", key=f"bt_{d_id}"):
                new_mt = mt - pay_tranche
                h = json.loads(hi); h.append({"date":datetime.now().strftime("%d/%m"), "p":pay_tranche})
                if new_mt <= 0: run_db("DELETE FROM dettes WHERE id=?", (d_id,))
                else: run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (new_mt, json.dumps(h), d_id))
                st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 Journal des Ventes")
    df = pd.DataFrame(run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True), 
                      columns=["Date", "Ref", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
    st.dataframe(df, use_container_width=True)
    if st.button("🖨️ IMPRIMER RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

elif st.session_state.page == "ACCUEIL":
    st.header(f"Bienvenue sur {GLOBAL_APP_NAME}")
    st.write(f"Compte : **{C_NOM}**")
    st.markdown(f"### Utilisateur : {USER.upper()}")
