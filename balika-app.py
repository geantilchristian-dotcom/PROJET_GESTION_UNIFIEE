import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import base64

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & STYLE AVANCÉ (v820)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP PRO CLOUD", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation exhaustive du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD", 'history_view': None
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_v820_master.db', timeout=60) as conn:
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
# 2. INITIALISATION DES TABLES (STRUCTURE PROFESSIONNELLE)
# ==============================================================================
def init_db():
    # Table des Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        ent_id TEXT, status TEXT DEFAULT 'ACTIF', date_creation TEXT)""")
    
    # Configuration Globale (Super Admin)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
        taux_global REAL, version TEXT)""")
    
    # Infos Boutique (En-tête de facture par utilisateur)
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT, email TEXT)""")
    
    # Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
        ent_id TEXT, categorie TEXT DEFAULT 'Général')""")
    
    # Ventes (Stockage JSON pour les articles)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, heure_v TEXT, vendeur TEXT, ent_id TEXT, 
        details_json TEXT)""")
    
    # Dettes et Historique de paiement
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        devise TEXT, ref_v TEXT, ent_id TEXT, status TEXT DEFAULT 'OUVERT')""")

    # Logs système
    run_db("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, date_log TEXT)""")

    # Données par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF'))
        
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global, version) 
               VALUES (1, 'BALIKA ERP', 'Bienvenue sur la version Pro v820', 2850.0, 'v820')")

init_db()

# ==============================================================================
# 3. CSS & INTERFACE (ORANGE & BLEU)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    .marquee-container {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #000; color: #00FF00; padding: 10px 0;
        z-index: 999999; border-bottom: 2px solid white;
        height: 45px; display: flex; align-items: center;
    }}
    .main-content {{ margin-top: 55px; }}
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 10px; font-weight: bold; height: 50px; width: 100%;
        border: 2px solid white; font-size: 16px;
    }}
    .white-card {{
        background: white; color: black; padding: 20px; 
        border-radius: 12px; border: 3px solid black; margin-bottom: 15px;
    }}
    .invoice-print {{
        background: white; color: black; padding: 30px; 
        border: 1px dashed black; font-family: 'Courier New';
    }}
    div[data-baseweb="input"] {{ background-color: #FFFFFF !important; }}
    input {{ color: #000 !important; font-weight: bold !important; }}
    </style>
    <div class="marquee-container"><marquee scrollamount="6">{MARQUEE}</marquee></div>
    <div class="main-content"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. FONCTIONNALITÉS TRANSVERSALES
# ==============================================================================
def add_log(user, action):
    run_db("INSERT INTO logs (user, action, date_log) VALUES (?,?,?)", 
           (user, action, datetime.now().strftime("%d/%m/%Y %H:%M")))

def get_ent_info(eid):
    res = run_db("SELECT * FROM ent_infos WHERE ent_id=?", (eid,), fetch=True)
    if res: return res[0]
    return (eid, "MA BOUTIQUE", "ADRESSE NON DÉFINIE", "000000000", "RCCM-X-000", "email@mail.com")

def share_ui(text, title):
    st.components.v1.html(f"""<script>
        async function share() {{
            const data = {{ title: '{title}', text: `{text}`, url: window.location.href }};
            try {{ await navigator.share(data); }} catch(e) {{ console.log(e); }}
        }}
        share();
    </script>""", height=0)

# ==============================================================================
# 5. AUTHENTIFICATION (SÉCURISÉE)
# ==============================================================================
if not st.session_state.auth:
    _, col_login, _ = st.columns([0.2, 0.6, 0.2])
    with col_login:
        st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["CONNEXION", "INSCRIPTION"])
        
        with tab_in:
            u = st.text_input("Identifiant").lower().strip()
            p = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
                if res:
                    if res[0][3] == "PAUSE" and res[0][1] != "SUPER_ADMIN":
                        st.error("❌ Accès suspendu.")
                    elif make_hashes(p) == res[0][0]:
                        st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                        add_log(u, "Connexion réussie")
                        st.rerun()
                    else: st.error("❌ Mot de passe erroné.")
                else: st.error("❌ Utilisateur inexistant.")
        
        with tab_up:
            nu = st.text_input("Choisir Identifiant").lower().strip()
            np = st.text_input("Choisir Mot de passe", type="password")
            if st.button("CRÉER MON COMPTE"):
                if not run_db("SELECT * FROM users WHERE username=?", (nu,), fetch=True):
                    d_c = datetime.now().strftime("%d/%m/%Y")
                    run_db("INSERT INTO users (username, password, role, ent_id, date_creation) VALUES (?,?,?,?,?)",
                           (nu, make_hashes(np), 'USER', nu, d_c))
                    run_db("INSERT INTO ent_infos (ent_id, nom_boutique) VALUES (?,?)", (nu, nu.upper()))
                    st.success("✅ Compte créé ! Connectez-vous.")
                else: st.warning("⚠️ Identifiant déjà pris.")
    st.stop()

# ==============================================================================
# 6. MENU LATÉRAL (DYNAMIQUE)
# ==============================================================================
with st.sidebar:
    st.markdown(f"### 🛡️ {st.session_state.user.upper()}")
    st.write(f"Rôle : `{st.session_state.role}`")
    st.write("---")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "📊 AUDIT LOGS", "🛠️ SYSTÈME", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "👥 VENDEURS", "⚙️ CONFIG"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        add_log(st.session_state.user, "Déconnexion")
        st.session_state.auth = False; st.rerun()

# ==============================================================================
# 7. LOGIQUE SUPER ADMIN (admin)
# ==============================================================================
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("👥 GESTION DES ABONNÉS")
        abos = run_db("SELECT username, status, date_creation, ent_id FROM users WHERE role='USER'", fetch=True)
        for u, s, d, e in abos:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2,1,1,1])
                c1.write(f"**{u.upper()}** (Inscrit le {d})")
                c2.write(f"Statut : `{s}`")
                if c3.button("🔄 ÉTAT", key=f"st_{u}"):
                    ns = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (ns, u)); st.rerun()
                if c4.button("🗑️ SUPPRIMER", key=f"del_{u}"):
                    run_db("DELETE FROM users WHERE username=?", (u)); st.rerun()

    elif st.session_state.page == "LOGS":
        st.header("📊 AUDIT DES ACTIONS")
        logs = run_db("SELECT * FROM logs ORDER BY id DESC LIMIT 100", fetch=True)
        st.table(pd.DataFrame(logs, columns=["ID", "User", "Action", "Horodatage"]))

    elif st.session_state.page == "SYSTÈME":
        st.header("🛠️ PARAMÈTRES GLOBAUX")
        with st.form("sys_form"):
            new_n = st.text_input("Nom de l'App", value=APP_NAME)
            new_m = st.text_area("Message Défilant", value=MARQUEE)
            new_t = st.number_input("Taux de change ($1 = ?)", value=TX_G)
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (new_n, new_m, new_t))
                st.rerun()

# ==============================================================================
# 8. LOGIQUE UTILISATEUR (LA BOUTIQUE)
# ==============================================================================
else:
    # --- MODULE STOCK ---
    if st.session_state.page == "STOCK":
        st.header("📦 GESTION DU STOCK")
        with st.expander("➕ AJOUTER UN NOUVEAU PRODUIT"):
            with st.form("new_p"):
                f1, f2, f3 = st.columns(3)
                d_in = f1.text_input("Désignation")
                q_in = f2.number_input("Stock Initial", 1)
                p_in = f3.number_input("Prix Vente ($)")
                if st.form_submit_button("ENREGISTRER"):
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                           (d_in.upper(), q_in, p_in, "USD", st.session_state.ent_id))
                    add_log(st.session_state.user, f"Ajout produit: {d_in}")
                    st.rerun()
        
        st.subheader("📋 LISTE DES ARTICLES")
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for pi, p_des, p_st, p_pr in prods:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3,1,1,1])
                u_des = col1.text_input("Nom", p_des, key=f"des_{pi}")
                u_st = col2.number_input("Stock", value=p_st, key=f"st_{pi}")
                u_pr = col3.number_input("Prix $", value=p_pr, key=f"pr_{pi}")
                if col4.button("MAJ", key=f"upd_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_des.upper(), u_st, u_pr, pi))
                    st.success("Produit modifié")

    # --- MODULE CAISSE ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            devise = st.radio("Mode de paiement :", ["USD", "CDF"], horizontal=True)
            
            # Recherche & Ajout
            items = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {r[0]: (r[1], r[2]) for r in items}
            
            sel = st.selectbox("Choisir l'article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                if p_map[sel][1] > 0:
                    st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
                    st.rerun()
                else: st.error("Stock épuisé !")

            if st.session_state.panier:
                st.write("---")
                total_f = 0.0
                cart_details = []
                for art, qte in list(st.session_state.panier.items()):
                    pu = p_map[art][0] if devise == "USD" else p_map[art][0] * TX_G
                    st_max = p_map[art][1]
                    total_item = pu * qte
                    total_f += total_item
                    cart_details.append({"art": art, "qte": qte, "pu": pu, "tot": total_item})
                    
                    l1, l2, l3 = st.columns([3,1,1])
                    l1.write(f"**{art}**")
                    st.session_state.panier[art] = l2.number_input("Qté", 1, st_max, value=qte, key=f"cart_{art}")
                    if l3.button("🗑️", key=f"rm_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                
                st.markdown(f"### TOTAL À PAYER : {total_f:,.2f} {devise}")
                c_nom = st.text_input("Nom du Client", "CLIENT COMPTANT")
                c_pay = st.number_input("Montant Reçu", value=float(total_f))
                
                if st.button("✅ FINALISER LA VENTE"):
                    ref = f"FAC-{random.randint(10000, 99999)}"
                    now = datetime.now()
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, heure_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           (ref, c_nom.upper(), total_f, c_pay, total_f-c_pay, devise, now.strftime("%d/%m/%Y"), now.strftime("%H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(cart_details)))
                    
                    if total_f-c_pay > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (c_nom.upper(), total_f-c_pay, devise, ref, st.session_state.ent_id))
                    
                    for a, q in st.session_state.panier.items():
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    
                    st.session_state.last_fac = {"ref": ref, "tot": total_f, "dev": devise, "cli": c_nom.upper(), "det": cart_details}
                    st.session_state.panier = {}
                    add_log(st.session_state.user, f"Vente réalisée: {ref}")
                    st.rerun()
        else:
            # AFFICHAGE REÇU PROFESSIONNEL
            f = st.session_state.last_fac
            e = get_ent_info(st.session_state.ent_id)
            
            c_ret, c_pri, c_sha = st.columns(3)
            if c_ret.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()
            
            receipt = f"""
            <div class="invoice-print">
                <h2 style='text-align:center;'>{e[1]}</h2>
                <p style='text-align:center;'>{e[2]}<br>Tel: {e[3]} | RCCM: {e[4]}</p>
                <hr>
                <p><b>REF:</b> {f['ref']} | <b>DATE:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                <p><b>CLIENT:</b> {f['cli']}</p>
                <hr>
                <table style='width:100%;'>
                    <tr><th align="left">Art.</th><th align="center">Qté</th><th align="right">Total</th></tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['tot']:,.0f}</td></tr>" for i in f['det']])}
                </table>
                <hr>
                <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
                <p style='text-align:center; font-size:10px;'>Merci de votre confiance !</p>
            </div>
            """
            st.markdown(receipt, unsafe_allow_html=True)
            if c_pri.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if c_sha.button("📤 PARTAGER"): share_ui(f"Facture {f['ref']} - {e[1]}", "Votre Facture")

    # --- MODULE RAPPORTS ---
    elif st.session_state.page == "RAPPORTS":
        st.header("📊 HISTORIQUE ET RAPPORTS")
        vts = run_db("SELECT date_v, ref, client, total, devise, details_json FROM ventes WHERE ent_id=? ORDER BY id DESC", (st.session_state.ent_id,), fetch=True)
        if vts:
            df_vts = pd.DataFrame(vts, columns=["Date", "Réf", "Client", "Montant", "Devise", "Details"])
            st.dataframe(df_vts.drop(columns=["Details"]), use_container_width=True)
            
            sel_ref = st.selectbox("Réimprimer une facture :", df_vts["Réf"].unique())
            if st.button("GÉNÉRER À NOUVEAU"):
                match = [v for v in vts if v[1] == sel_ref][0]
                st.session_state.last_fac = {"ref": match[1], "tot": match[3], "dev": match[4], "cli": match[2], "det": json.loads(match[5])}
                st.session_state.page = "CAISSE"; st.rerun()

    # --- MODULE DETTES ---
    elif st.session_state.page == "DETTES":
        st.header("📉 SUIVI DES CRÉANCES")
        dts = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv, dr in dts:
            with st.container(border=True):
                st.write(f"👤 **{dc}** | Dette : **{dm:,.2f} {dv}** | Réf : {dr}")
                v_pay = st.number_input("Montant à verser", 0.0, float(dm), key=f"det_pay_{di}")
                if st.button("ENCAISSER PAIEMENT", key=f"btn_det_{di}"):
                    new_m = dm - v_pay
                    run_db("UPDATE dettes SET montant=? WHERE id=?", (new_m, di))
                    add_log(st.session_state.user, f"Paiement dette client: {dc} ({v_pay})")
                    st.rerun()

    # --- MODULE CONFIGURATION ---
    elif st.session_state.page == "CONFIG":
        st.header("⚙️ INFOS DE LA BOUTIQUE")
        e_info = get_ent_info(st.session_state.ent_id)
        with st.form("ent_f"):
            e_nom = st.text_input("Nom de l'Etablissement", e_info[1])
            e_adr = st.text_input("Adresse Physique", e_info[2])
            e_tel = st.text_input("Téléphone Contact", e_info[3])
            e_rcm = st.text_input("Numéro RCCM / ID Nat", e_info[4])
            if st.form_submit_button("SAUVEGARDER LES INFOS"):
                run_db("REPLACE INTO ent_infos (ent_id, nom_boutique, adresse, telephone, rccm) VALUES (?,?,?,?,?)",
                       (st.session_state.ent_id, e_nom, e_adr, e_tel, e_rcm))
                st.success("Informations de facture mises à jour !")
