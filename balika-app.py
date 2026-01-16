import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & STYLE (VERSION ULTIME v855+)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation de toutes les variables de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm", 'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_final.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES (AUCUNE SUPPRESSION)
# ==============================================================================
def init_db():
    # Tables Utilisateurs & Config
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, status TEXT DEFAULT 'ACTIF', photo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)")
    run_db("CREATE TABLE IF NOT EXISTS ent_infos (ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, rccm TEXT)")
    
    # Tables Métier
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, devise TEXT, date_d TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes_fournisseurs (id INTEGER PRIMARY KEY AUTOINCREMENT, fournisseur TEXT, montant REAL, devise TEXT, motif TEXT, date_f TEXT, ent_id TEXT, status TEXT DEFAULT 'NON PAYÉ')")

    # Création Admin par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
    
    # Config système par défaut
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global) VALUES (1, 'BALIKA ERP', 'Bienvenue sur votre gestionnaire intelligent - Version v855+ Mobile & Desktop', 2850.0)")

init_db()

# ==============================================================================
# 3. DESIGN, COULEURS & MARQUEE FIXE
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    /* Fond Orange & Texte Blanc pour boutons bleus */
    .stApp {{ background-color: #FF8C00 !important; }}
    
    .fixed-header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: #00FF00; height: 50px;
        z-index: 9999; display: flex; align-items: center;
        border-bottom: 2px solid white;
    }}
    
    marquee {{ font-size: 20px; font-weight: bold; font-family: 'Courier New'; }}
    .main-body {{ margin-top: 65px; }}
    
    /* Bouton Bleu Texte Blanc */
    .stButton>button {{
        background-color: #0055ff !important; color: white !important;
        border-radius: 12px; font-weight: bold; height: 55px; width: 100%;
        border: 2px solid white; font-size: 16px;
    }}
    
    /* Factures Styles */
    .fac-80mm {{ background: white; color: black; padding: 15px; width: 300px; margin: auto; font-family: 'Courier New'; border: 1px solid black; }}
    .fac-a4 {{ background: white; color: black; padding: 40px; width: 95%; margin: auto; border: 1px solid #ccc; font-family: Arial, sans-serif; }}
    
    /* Inputs */
    div[data-baseweb="input"] {{ background: white !important; border-radius: 8px !important; }}
    input {{ color: black !important; font-weight: bold !important; }}
    
    /* Tableaux */
    .stDataFrame {{ background: white !important; border-radius: 10px; }}
    </style>
    <div class="fixed-header"><marquee scrollamount="8">{MARQUEE}</marquee></div>
    <div class="main-body"></div>
""", unsafe_allow_html=True)

def get_info_entete():
    res = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    return res[0] if res else (st.session_state.ent_id.upper(), "Adresse non définie", "0000", "RCCM-000")

# ==============================================================================
# 4. AUTHENTIFICATION & COMPTES
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:white;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔒 CONNEXION", "🏪 CRÉER BOUTIQUE"])
    
    with t1:
        u_in = st.text_input("Identifiant").lower().strip()
        p_in = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_in,), fetch=True)
            if res and make_hashes(p_in) == res[0][0]:
                if res[0][3] == "PAUSE": st.error("Compte suspendu.")
                else:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
            else: st.error("Erreur d'accès.")
    
    with t2:
        new_u = st.text_input("Nom de la Boutique").lower().strip()
        new_p = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("CRÉER MON COMPTE"):
            if not run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True):
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (new_u, make_hashes(new_p), 'USER', new_u))
                run_db("INSERT INTO ent_infos (ent_id, nom_boutique) VALUES (?,?)", (new_u, new_u.upper()))
                st.success("Boutique créée avec succès !")
    st.stop()

# ==============================================================================
# 5. BARRE LATÉRALE (SIDEBAR)
# ==============================================================================
with st.sidebar:
    u_pic = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if u_pic and u_pic[0][0]: st.image(u_pic[0][0], width=120)
    else: st.markdown("<h2 align='center'>👤</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 align='center'>{st.session_state.user.upper()}</h3>", unsafe_allow_html=True)
    st.write("---")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME", "👤 PROFIL"]
    else:
        # Les vendeurs ne voient que Ventes et Dettes
        if st.session_state.role == "VENDEUR":
            menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES CLIENTS"]
        else:
            menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES CLIENTS", "🚛 FOURNISSEURS", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. MODULES DE GESTION (USER)
# ==============================================================================
if st.session_state.role != "SUPER_ADMIN":
    
    # --- ACCUEIL / DASHBOARD ---
    if st.session_state.page == "ACCUEIL":
        st.title("🏠 TABLEAU DE BORD")
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        st.metric("Ventes du jour", f"{v_jr:,.2f} USD")
        # Widget Heure & Date (80mm Watch)
        st.info(f"📅 Date: {datetime.now().strftime('%d/%m/%Y')} | ⌚ Heure: {datetime.now().strftime('%H:%M')}")

    # --- STOCK ---
    elif st.session_state.page == "STOCK":
        st.header("📦 GESTION DU STOCK")
        with st.form("add_prod"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Désignation")
            q = c2.number_input("Quantité", 0)
            p = c3.number_input("Prix de Vente ($)")
            if st.form_submit_button("AJOUTER PRODUIT"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n.upper(), q, p, "USD", st.session_state.ent_id))
                st.rerun()
        
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for pi, pd, ps, pp in prods:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3,1,1,1])
                u_n = col1.text_input("Nom", pd, key=f"n_{pi}")
                u_q = col2.number_input("Stock", value=ps, key=f"q_{pi}")
                u_p = col3.number_input("Prix $", value=pp, key=f"p_{pi}")
                if col4.button("💾", key=f"b_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (u_n.upper(), u_q, u_p, pi)); st.rerun()

    # --- CAISSE & FACTURATION ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 CAISSE TERMINAL")
            f_format = st.radio("Format de sortie", ["80mm", "A4"], horizontal=True)
            mode_dev = st.radio("Paiement en :", ["USD", "CDF"], horizontal=True)
            
            p_data = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {x[0]: (x[1], x[2]) for x in p_data}
            
            sel = st.selectbox("Choisir Article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                if p_map[sel][1] > 0:
                    st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
                else: st.error("Stock insuffisant.")

            if st.session_state.panier:
                total_f = 0.0
                cart_items = []
                for art, qte in list(st.session_state.panier.items()):
                    pu = p_map[art][0] if mode_dev == "USD" else p_map[art][0] * TX_G
                    total_f += pu * qte
                    cart_items.append({"art": art, "qty": qte, "pu": pu})
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{art}**")
                    st.session_state.panier[art] = c2.number_input("Qté", 1, p_map[art][1], value=qte, key=f"cart_{art}")
                    if c3.button("🗑️", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()
                
                st.markdown(f"<div style='background:white; color:blue; padding:20px; border-radius:10px; border:2px solid blue; text-align:center;'><h2>TOTAL : {total_f:,.2f} {mode_dev}</h2></div>", unsafe_allow_html=True)
                cli = st.text_input("Client", "COMPTANT")
                p_recu = st.number_input("Montant Payé", value=float(total_f))
                
                if st.button("✅ VALIDER LA VENTE"):
                    ref_f = f"FAC-{random.randint(1000,9999)}"
                    reste = total_f - p_recu
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref_f, cli.upper(), total_f, p_recu, reste, mode_dev, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(cart_items)))
                    if reste > 0: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cli.upper(), reste, mode_dev, ref_f, st.session_state.ent_id))
                    for a, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel=stock_actuel-? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    st.session_state.update({'last_fac': {"ref": ref_f, "tot": total_f, "dev": mode_dev, "cli": cli.upper(), "det": cart_items, "paye": p_recu, "reste": reste}, 'panier': {}, 'format_fac': f_format})
                    st.rerun()
        else:
            # AFFICHAGE FACTURE
            f = st.session_state.last_fac
            e = get_info_entete()
            st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({'last_fac': None}))
            
            if st.session_state.format_fac == "80mm":
                html = f"""<div class="fac-80mm"><h3 align="center">{e[0]}</h3><p align="center">{e[1]}<br>{e[2]}</p><hr>
                <b>REF:</b> {f['ref']}<br><b>CLIENT:</b> {f['cli']}<br><b>DATE:</b> {datetime.now().strftime('%d/%m/%Y')}<hr>
                <table width="100%">{"".join([f"<tr><td>{i['art']} x{i['qty']}</td><td align='right'>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['det']])}</table><hr>
                <h4 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h4>
                <p>Payé: {f['paye']:,.0f} | Reste: {f['reste']:,.0f}</p></div>"""
            else:
                html = f"""<div class="fac-a4"><table width="100%"><tr><td><h2>{e[0]}</h2><p>{e[1]}<br>{e[2]}<br>{e[3]}</p></td>
                <td align="right"><h1>FACTURE</h1><p>N° {f['ref']}<br>Date: {datetime.now().strftime('%d/%m/%Y')}</p></td></tr></table><br>
                <p><b>Client :</b> {f['cli']}</p><table width="100%" style="border-collapse:collapse;">
                <tr style="background:#eee;"><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td style='border-bottom:1px solid #ddd;'>{i['art']}</td><td align='center'>{i['qty']}</td><td align='right'>{i['pu']:,.2f}</td><td align='right'>{i['pu']*i['qty']:,.2f}</td></tr>" for i in f['det']])}
                </table><h3 align="right">TOTAL À PAYER : {f['tot']:,.2f} {f['dev']}</h3></div>"""
            
            st.markdown(html, unsafe_allow_html=True)
            if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    # --- DETTES CLIENTS & PAIEMENT ÉCHELONNÉ ---
    elif st.session_state.page == "CLIENTS":
        st.header("📉 DETTES CLIENTS")
        dettes = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv, dr in dettes:
            with st.container(border=True):
                st.write(f"👤 Client: **{dc}** | Reste: **{dm:,.2f} {dv}** (Facture: {dr})")
                m_verse = st.number_input(f"Montant versé", 0.0, float(dm), key=f"pay_{di}")
                if st.button("Valider Tranche", key=f"btn_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (m_verse, di))
                    st.rerun()

    # --- FOURNISSEURS ---
    elif st.session_state.page == "FOURNISSEURS":
        st.header("🚛 DETTES FOURNISSEURS")
        with st.form("add_four"):
            c1, c2, c3 = st.columns(3)
            fn = c1.text_input("Nom Fournisseur")
            fm = c2.number_input("Montant dû")
            fd = c3.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("Enregistrer Dette Fournisseur"):
                run_db("INSERT INTO dettes_fournisseurs (fournisseur, montant, devise, date_f, ent_id) VALUES (?,?,?,?,?)", (fn.upper(), fm, fd, datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id))
                st.rerun()

    # --- DÉPENSES ---
    elif st.session_state.page == "DÉPENSES":
        st.header("💸 DÉPENSES")
        with st.form("add_dep"):
            c1, c2 = st.columns(2)
            mot = c1.text_input("Motif")
            val = c2.number_input("Montant")
            if st.form_submit_button("Sauver Dépense"):
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)", (mot.upper(), val, "USD", datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id))
                st.rerun()

    # --- VENDEURS ---
    elif st.session_state.page == "VENDEURS":
        st.header("👥 GESTION DES VENDEURS")
        vn = st.text_input("Nom du vendeur")
        vp = st.text_input("Mot de passe vendeur", type="password")
        if st.button("Créer Compte Vendeur"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (vn.lower(), make_hashes(vp), 'VENDEUR', st.session_state.ent_id))
            st.success("Vendeur ajouté !")

    # --- RÉGLAGES ---
    elif st.session_state.page == "RÉGLAGES":
        st.header("⚙️ RÉGLAGES")
        e = get_info_entete()
        with st.form("set_e"):
            st.subheader("En-tête Facture")
            en = st.text_input("Nom Boutique", e[0])
            ea = st.text_input("Adresse", e[1])
            et = st.text_input("Tél", e[2])
            if st.form_submit_button("MAJ INFOS"):
                run_db("INSERT OR REPLACE INTO ent_infos (ent_id, nom_boutique, adresse, telephone) VALUES (?,?,?,?)", (st.session_state.ent_id, en, ea, et))
                st.rerun()
        
        st.write("---")
        up_pic = st.file_uploader("Photo de profil", type=['jpg','png'])
        if st.button("Sauver Photo"):
            if up_pic: run_db("UPDATE users SET photo=? WHERE username=?", (sqlite3.Binary(up_pic.getvalue()), st.session_state.user)); st.rerun()

# ==============================================================================
# 7. LOGIQUE SUPER ADMIN (SYSTEM)
# ==============================================================================
elif st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "SYSTÈME":
        with st.form("sys_cfg"):
            n_a = st.text_input("Nom App", APP_NAME)
            n_m = st.text_area("Texte Marquee", MARQUEE)
            n_t = st.number_input("Taux de change ($1 = ? CDF)", value=TX_G)
            if st.form_submit_button("APPLIQUER SYSTÈME"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (n_a, n_m, n_t))
                st.rerun()
