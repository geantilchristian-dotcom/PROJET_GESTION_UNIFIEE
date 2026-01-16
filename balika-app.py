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
# 1. CONFIGURATION SYSTÈME & STYLE (v826 - MARQUEE FIX)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation des états
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v826.db', timeout=60) as conn:
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
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        ent_id TEXT, status TEXT DEFAULT 'ACTIF', photo BLOB)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, 
        taux_global REAL, version TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
        ent_id TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
        devise TEXT, ref_v TEXT, ent_id TEXT)""")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)",
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global, version) VALUES (1, 'BALIKA ERP', 'Bienvenue sur votre espace de gestion intelligente BALIKA ERP 2026', 2850.0, 'v826')")

init_db()

# ==============================================================================
# 3. DESIGN & RÉTABLISSEMENT DU MESSAGE DÉFILANT (MARQUEE)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

# Injection CSS pour le bandeau fixe et les couleurs Orange/Bleu
st.markdown(f"""
    <style>
    /* Fond Orange de l'application */
    .stApp {{ background-color: #FF8C00 !important; }}

    /* BANDEAU NOIR FIXE EN HAUT */
    .fixed-marquee {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #000000;
        color: #00FF00; /* Texte vert fluo */
        height: 50px;
        z-index: 999999;
        display: flex;
        align-items: center;
        border-bottom: 2px solid #FFFFFF;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }}

    marquee {{
        font-size: 20px;
        font-weight: bold;
        font-family: 'Courier New', Courier, monospace;
    }}

    /* Ajustement du contenu pour ne pas être caché par le bandeau */
    .main-content-area {{
        margin-top: 70px;
    }}

    /* Boutons Bleus avec texte Blanc */
    .stButton>button {{
        background-color: #0055ff !important;
        color: white !important;
        border-radius: 12px;
        font-weight: bold;
        height: 55px;
        width: 100%;
        border: 2px solid white;
        font-size: 16px;
    }}

    /* Champs de saisie blancs pour visibilité */
    div[data-baseweb="input"], div[data-baseweb="select"] {{
        background-color: white !important;
        border-radius: 8px !important;
    }}
    
    input {{
        color: black !important;
        font-weight: bold !important;
    }}

    /* Design Facture Administrative */
    .invoice-card {{
        background: white;
        color: black;
        padding: 25px;
        border: 2px solid black;
        border-radius: 15px;
        font-family: 'Courier New', monospace;
    }}
    </style>

    <div class="fixed-marquee">
        <marquee scrollamount="8">{MARQUEE}</marquee>
    </div>
    <div class="main-content-area"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIQUE D'ACCÈS
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 CONNEXION", "🏪 CRÉER MA BOUTIQUE"])
    
    with tab1:
        user_in = st.text_input("Identifiant").lower().strip()
        pass_in = st.text_input("Mot de passe", type="password")
        if st.button("ENTRER DANS L'ESPACE"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (user_in,), fetch=True)
            if res:
                if res[0][3] == "PAUSE" and res[0][1] != "SUPER_ADMIN":
                    st.error("⛔ Accès suspendu par l'administration.")
                elif make_hashes(pass_in) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':user_in, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
                else: st.error("❌ Mot de passe incorrect.")
            else: st.error("❌ Utilisateur introuvable.")

    with tab2:
        new_u = st.text_input("Choisir Identifiant").lower().strip()
        new_p = st.text_input("Choisir Mot de passe ", type="password")
        if st.button("CRÉER MON COMPTE MAINTENANT"):
            if run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True):
                st.warning("⚠️ Cet identifiant est déjà utilisé.")
            else:
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                       (new_u, make_hashes(new_p), 'USER', new_u))
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique) VALUES (?,?)", 
                       (new_u, new_u.upper()))
                st.success("✅ Compte créé avec succès ! Connectez-vous à gauche.")
    st.stop()

# ==============================================================================
# 5. MENU LATÉRAL
# ==============================================================================
with st.sidebar:
    # Affichage de la photo de profil si elle existe
    pic = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if pic and pic[0][0]:
        st.image(pic[0][0], width=120)
    else:
        st.markdown("<h1 style='text-align:center;'>👤</h1>", unsafe_allow_html=True)
    
    st.markdown(f"<h3 style='text-align:center;'>{st.session_state.user.upper()}</h3>", unsafe_allow_html=True)
    st.write("---")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. LOGIQUE SUPER ADMIN (admin / admin123)
# ==============================================================================
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("👥 GESTION DES BOUTIQUES INSCRITES")
        shops = run_db("SELECT username, status FROM users WHERE role='USER'", fetch=True)
        for u, s in shops:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"Boutique : **{u.upper()}**")
                c2.write(f"État : {s}")
                if c3.button("ACTIVER/PAUSE", key=f"btn_{u}"):
                    ns = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (ns, u))
                    st.rerun()

    elif st.session_state.page == "SYSTÈME":
        st.header("🛠️ RÉGLAGES GLOBAUX DU SYSTÈME")
        with st.form("sys"):
            n_app = st.text_input("Nom de l'Application", APP_NAME)
            n_marq = st.text_area("Message défilant (Marquee)", MARQUEE)
            n_tx = st.number_input("Taux de change (1$ = ? CDF)", value=TX_G)
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (n_app, n_marq, n_tx))
                st.success("Modifications enregistrées !")
                st.rerun()

# ==============================================================================
# 7. LOGIQUE BOUTIQUE (USER/VENDEUR)
# ==============================================================================
else:
    # --- MODULE STOCK ---
    if st.session_state.page == "STOCK":
        st.header("📦 GESTION DU STOCK")
        with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
            with st.form("add_item"):
                f1, f2, f3 = st.columns(3)
                nom_p = f1.text_input("Désignation")
                qty_p = f2.number_input("Quantité en stock", 1)
                pri_p = f3.number_input("Prix de vente ($)")
                if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                           (nom_p.upper(), qty_p, pri_p, "USD", st.session_state.ent_id))
                    st.rerun()

        st.subheader("📋 LISTE DES ARTICLES DISPONIBLES")
        items = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for i_id, i_des, i_st, i_pr in items:
            with st.container(border=True):
                cl1, cl2, cl3, cl4 = st.columns([3,1,1,1])
                u_des = cl1.text_input("Nom", i_des, key=f"edit_d_{i_id}")
                u_qty = cl2.number_input("Qté", value=i_st, key=f"edit_q_{i_id}")
                u_pri = cl3.number_input("Prix $", value=i_pr, key=f"edit_p_{i_id}")
                if cl4.button("💾 MAJ", key=f"btn_u_{i_id}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_des.upper(), u_qty, u_pri, i_id))
                    st.rerun()

    # --- MODULE CAISSE ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 TERMINAL DE VENTE")
            mode_dev = st.radio("Devise de paiement :", ["USD", "CDF"], horizontal=True)
            
            p_data = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in p_data}
            
            choix = st.selectbox("Sélectionner un article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER AU PANIER") and choix != "---":
                if p_map[choix][1] > 0:
                    st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                    st.rerun()
                else: st.error("Stock épuisé !")

            if st.session_state.panier:
                total_global = 0.0
                cart_final = []
                st.write("---")
                for art, qte in list(st.session_state.panier.items()):
                    pu = p_map[art][0] if mode_dev == "USD" else p_map[art][0] * TX_G
                    sub = pu * qte
                    total_global += sub
                    cart_final.append({"art": art, "qty": qte, "pu": pu})
                    
                    l1, l2, l3 = st.columns([3,1,1])
                    l1.write(f"**{art}**")
                    st.session_state.panier[art] = l2.number_input("Qté", 1, p_map[art][1], value=qte, key=f"cart_qty_{art}")
                    if l3.button("🗑️", key=f"del_cart_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                
                st.markdown(f"## TOTAL : {total_global:,.2f} {mode_dev}")
                nom_c = st.text_input("Nom du Client", "COMPTANT")
                montant_recu = st.number_input("Montant Reçu", value=float(total_global))
                
                if st.button("✅ VALIDER ET GÉNÉRER FACTURE"):
                    ref_f = f"FAC-{random.randint(10000, 99999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref_f, nom_c.upper(), total_global, montant_recu, total_global-montant_recu, mode_dev, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(cart_final)))
                    
                    if total_global-montant_recu > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (nom_c.upper(), total_global-montant_recu, mode_dev, ref_f, st.session_state.ent_id))
                    
                    for a, q in st.session_state.panier.items():
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    
                    st.session_state.last_fac = {"ref": ref_f, "tot": total_global, "dev": mode_dev, "cli": nom_c.upper(), "det": cart_final}
                    st.session_state.panier = {}
                    st.rerun()
        else:
            # AFFICHAGE DE LA FACTURE ADMINISTRATIVE
            f = st.session_state.last_fac
            info_ent = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            c_ret, c_pri, c_sha = st.columns(3)
            if c_ret.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()
            
            st.markdown(f"""
            <div class="invoice-card">
                <h2 align="center">{info_ent[0]}</h2>
                <p align="center">{info_ent[1]}<br>Tél: {info_ent[2]} | RCCM: {info_ent[3]}</p><hr>
                <p><b>FACTURE N°:</b> {f['ref']}<br><b>CLIENT:</b> {f['cli']}<br><b>DATE:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                <table width="100%" border="0">
                    <tr style="background:#eee;"><th>Art.</th><th>Qté</th><th>Total</th></tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qty']}</td><td align='right'>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['det']])}
                </table><hr>
                <h3 align="right">TOTAL À PAYER: {f['tot']:,.2f} {f['dev']}</h3>
                <p align="center" style="font-size:12px;">Merci de votre confiance !</p>
            </div>
            """, unsafe_allow_html=True)
            
            if c_pri.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if c_sha.button("📤 PARTAGER"):
                txt_sha = f"Facture {f['ref']} - {info_ent[0]} - Client: {f['cli']} - Total: {f['tot']} {f['dev']}"
                st.components.v1.html(f"<script>navigator.share({{title:'Facture', text:'{txt_sha}', url:window.location.href}})</script>")

    # --- MODULE RAPPORTS ---
    elif st.session_state.page == "RAPPORTS":
        st.header("📊 HISTORIQUE DES VENTES")
        v_list = run_db("SELECT date_v, ref, client, total, devise, details_json FROM ventes WHERE ent_id=? ORDER BY id DESC", (st.session_state.ent_id,), fetch=True)
        if v_list:
            df_v = pd.DataFrame(v_list, columns=["Date/Heure", "Référence", "Client", "Montant", "Devise", "Details"])
            st.dataframe(df_v.drop("Details", axis=1), use_container_width=True)
            
            st.subheader("🔎 RÉIMPRIMER UNE ANCIENNE FACTURE")
            ref_sel = st.selectbox("Choisir la référence :", df_v["Référence"].unique())
            if st.button("GÉNÉRER LE REÇU"):
                v_sel = [v for v in v_list if v[1] == ref_sel][0]
                st.session_state.last_fac = {"ref": v_sel[1], "tot": v_sel[3], "dev": v_sel[4], "cli": v_sel[2], "det": json.loads(v_sel[5])}
                st.session_state.page = "CAISSE"; st.rerun()

    # --- MODULE RÉGLAGES ---
    elif st.session_state.page == "RÉGLAGES":
        st.header("⚙️ RÉGLAGES DE LA BOUTIQUE")
        cur_e = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        with st.form("set_e"):
            st.subheader("En-tête des Factures")
            en = st.text_input("Nom de l'Etablissement", cur_e[0])
            ea = st.text_input("Adresse Physique", cur_e[1])
            et = st.text_input("Téléphone", cur_e[2])
            er = st.text_input("RCCM / ID National", cur_e[3])
            if st.form_submit_button("SAUVEGARDER L'EN-TÊTE"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=? WHERE ent_id=?", (en, ea, et, er, st.session_state.ent_id))
                st.success("En-tête mis à jour !")
        
        st.write("---")
        st.subheader("Profil et Sécurité")
        up_img = st.file_uploader("Modifier Photo de Profil", type=['jpg', 'png'])
        new_pw = st.text_input("Nouveau mot de passe", type="password")
        if st.button("METTRE À JOUR LE PROFIL"):
            if up_img:
                run_db("UPDATE users SET photo=? WHERE username=?", (sqlite3.Binary(up_img.getvalue()), st.session_state.user))
            if new_pw:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_pw), st.session_state.user))
            st.success("Profil actualisé !")
