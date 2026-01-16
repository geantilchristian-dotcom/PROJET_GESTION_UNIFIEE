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
    page_title="BALIKA ERP v720", 
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
        with sqlite3.connect('balika_master_v720.db', timeout=60) as conn:
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
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET)
# ==============================================================================
def init_db():
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, date_inscription TEXT)""")
    
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

    # Création Admin par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'BIENVENUE SUR BALIKA ERP - SYSTÈME DE GESTION UNIFIÉ', '16/01/2026'))

init_db()

# ==============================================================================
# 3. RÉCUPÉRATION DU MESSAGE DÉFILANT (AVANT TOUT AFFICHAGE)
# ==============================================================================
# On cherche d'abord si l'utilisateur est loggé pour prendre son message, sinon celui du système
current_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, taux, adresse, tel, status FROM config WHERE ent_id=?", (current_eid,), fetch=True)

if res_cfg:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0]
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", 2850.0, "", "", "ACTIF")

# --- INJECTION CSS & MARQUEE (S'AFFICHE PARTOUT) ---
st.markdown(f"""
    <style>
    /* Global Styles */
    .stApp {{ background-color: #f8f9fa; }}
    h1, h2, h3, p, label {{ text-align: center !important; }}

    /* LE MARQUEE : S'affiche en haut de l'écran, même au Login */
    .marquee-fixed {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: linear-gradient(90deg, #001f3f, #0044cc);
        color: #ffffff; padding: 12px 0; z-index: 999999;
        border-bottom: 3px solid #FF8C00; font-family: 'Arial Black', sans-serif;
    }}
    .marquee-content {{
        display: inline-block; white-space: nowrap;
        animation: scroll-text 20s linear infinite; font-size: 18px;
    }}
    @keyframes scroll-text {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}

    /* Boutons Bleus Texte Blanc */
    .stButton>button {{
        background: #0044cc !important; color: white !important;
        border-radius: 10px; font-weight: bold; width: 100%; border: none;
        padding: 12px; margin-bottom: 5px;
    }}
    
    /* Cadre Total en couleur */
    .total-display {{
        border: 6px double #FF8C00; background: #000; padding: 20px;
        border-radius: 15px; color: #00FF00; font-size: 32px;
        font-weight: 900; text-align: center; margin: 20px 0;
    }}

    /* Montre 80mm Accueil */
    .digital-watch {{
        background: #222; color: #FF8C00; padding: 15px 30px;
        border-radius: 10px; font-size: 28px; font-weight: bold;
        border: 2px solid #FF8C00; display: inline-block;
    }}

    /* Facture & Mobile Fix */
    .fac-box {{
        background: #fff; color: #000; padding: 20px; border: 1px solid #ccc;
        font-family: 'Courier New', monospace; width: 100%; max-width: 400px; margin: auto;
    }}
    .sig-line {{ margin-top: 40px; border-top: 1px solid #000; width: 120px; float: right; text-align: center; }}

    /* Cache les éléments inutiles à l'impression */
    @media print {{
        .marquee-fixed, .stSidebar, .stButton, .no-print {{ display: none !important; }}
        .fac-box {{ border: none !important; width: 100% !important; }}
    }}
    </style>

    <div class="marquee-fixed">
        <div class="marquee-content">
            🚀 {C_NOM} | 📢 {C_MSG} | 💹 TAUX: {C_TX} CDF | 📅 {datetime.now().strftime('%d/%m/%Y')}
        </div>
    </div>
    <div style="margin-top: 80px;"></div>
""", unsafe_allow_html=True)

# Vérification Suspension
if st.session_state.auth and C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.error("🚨 VOTRE COMPTE EST ACTUELLEMENT SUSPENDU. CONTACTEZ LE SUPPORT.")
    st.stop()

# ==============================================================================
# 4. ÉCRAN DE CONNEXION (LOGIN)
# ==============================================================================
if not st.session_state.auth:
    _, center, _ = st.columns([0.1, 0.8, 0.1])
    with center:
        st.title("ACCÈS SÉCURISÉ BALIKA")
        t1, t2 = st.tabs(["🔑 CONNEXION", "📝 INSCRIPTION NOUVEAU CLIENT"])
        
        with t1:
            u_name = st.text_input("Identifiant").lower().strip()
            u_pass = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER AU SYSTÈME"):
                user_data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_name,), fetch=True)
                if user_data and make_hashes(u_pass) == user_data[0][0]:
                    st.session_state.update({
                        'auth': True, 'user': u_name, 'role': user_data[0][1], 'ent_id': user_data[0][2]
                    })
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")

        with t2:
            with st.form("reg_form"):
                st.subheader("Ouvrir un compte ERP")
                new_ent_name = st.text_input("Nom de l'Entreprise")
                new_ent_tel = st.text_input("Téléphone WhatsApp")
                new_ent_adr = st.text_input("Adresse")
                new_ent_user = st.text_input("Créer un Identifiant Admin").lower().strip()
                new_ent_pass = st.text_input("Créer un Mot de Passe", type="password")
                
                if st.form_submit_button("ACTIVER MON ERP"):
                    if new_ent_name and new_ent_user and new_ent_pass:
                        exists = run_db("SELECT * FROM users WHERE username=?", (new_ent_user,), fetch=True)
                        if not exists:
                            eid = f"BAL-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id, telephone) VALUES (?,?,?,?,?)", 
                                   (new_ent_user, make_hashes(new_ent_pass), "ADMIN", eid, new_ent_tel))
                            run_db("INSERT INTO config (ent_id, nom_ent, tel, adresse, taux, message, date_inscription) VALUES (?,?,?,?,?,?,?)", 
                                   (eid, new_ent_name.upper(), new_ent_tel, new_ent_adr, 2850.0, "Bienvenue", datetime.now().strftime("%d/%m/%Y")))
                            st.success("✅ Compte créé avec succès ! Connectez-vous maintenant.")
                        else:
                            st.error("Cet identifiant existe déjà.")
    st.stop()

# --- RACCOURCIS ---
ENT_ID = st.session_state.ent_id
ROLE = st.session_state.role
USER = st.session_state.user

# ==============================================================================
# 5. MENU LATÉRAL (SIDEBAR)
# ==============================================================================
with st.sidebar:
    # Photo de profil
    upic = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if upic and upic[0][0]: st.image(upic[0][0], width=120)
    else: st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.caption(f"Entreprise: {C_NOM}")
    st.write("---")
    
    # Navigation
    if ROLE == "SUPER_ADMIN":
        m = ["🏠 ACCUEIL", "🌍 GESTION SaaS", "📊 RAPPORTS HQ", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        m = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # VENDEUR
        m = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for item in m:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 QUITTER", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.session_state.ent_id = "SYSTEM"
        st.rerun()

# ==============================================================================
# 6. PAGE ACCUEIL
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"BIENVENUE CHEZ {C_NOM}")
    
    # Montre Digitale
    st.markdown(f"""
        <center>
            <div class="digital-watch">
                ⌚ {datetime.now().strftime('%H:%M:%S')}<br>
                <span style="font-size:16px; color:white;">{datetime.now().strftime('%d %B %Y')}</span>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    
    sales_val = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES TOTALES", f"{sales_val:,.2f} $")
    
    debt_val = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES CLIENTS", f"{debt_val:,.2f} $", delta_color="inverse")
    
    stock_val = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", stock_val)

# ==============================================================================
# 7. CAISSE (TERMINAL DE VENTE AVEC SIGNATURE & PARTAGE)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 VENTE ET FACTURATION")
        
        col_opt1, col_opt2 = st.columns(2)
        v_devise = col_opt1.selectbox("Devise de Vente", ["USD", "CDF"])
        v_format = col_opt2.selectbox("Type d'impression", ["Ticket 80mm", "Facture A4"])
        
        # Liste produits
        plist = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {"px": r[1], "stk": r[2], "dv": r[3]} for r in plist}
        
        c_sel, c_add = st.columns([3, 1])
        pick = c_sel.selectbox("Choisir un article", ["---"] + list(p_dict.keys()))
        if c_add.button("➕ AJOUTER") and pick != "---":
            st.session_state.panier[pick] = st.session_state.panier.get(pick, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            net_total = 0.0
            lignes_v = []

            for art, qte in list(st.session_state.panier.items()):
                p_base = p_dict[art]["px"]
                d_base = p_dict[art]["dv"]
                
                # Conversion auto
                if d_base == "USD" and v_devise == "CDF": p_final = p_base * C_TX
                elif d_base == "CDF" and v_devise == "USD": p_final = p_base / C_TX
                else: p_final = p_base
                
                stot = p_final * qte
                net_total += stot
                lignes_v.append({"art": art, "qte": qte, "pu": p_final, "st": stot})
                
                cl1, cl2, cl3 = st.columns([3, 1, 0.5])
                cl1.write(f"**{art}**")
                st.session_state.panier[art] = cl2.number_input("Qté", 1, p_dict[art]["stk"], value=qte, key=f"v_q_{art}")
                if cl3.button("🗑️", key=f"v_rm_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()

            st.markdown(f'<div class="total-display">TOTAL À PAYER : {net_total:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            cl_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            cl_paye = st.number_input(f"MONTANT VERSÉ ({v_devise})", min_value=0.0, value=float(net_total))
            
            if st.button("✅ VALIDER LA VENTE"):
                ref = f"REF-{random.randint(10000, 99999)}"
                d_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = net_total - cl_paye
                
                # Enregistrement
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                       (ref, cl_nom, net_total, cl_paye, reste, v_devise, d_now, USER, ENT_ID, json.dumps(lignes_v)))
                
                # Gestion Dette
                if reste > 0.1:
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", 
                           (cl_nom, reste, v_devise, ref, ENT_ID, json.dumps([{"date": d_now, "paye": cl_paye}])))
                
                # Déstockage
                for l in lignes_v:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (l['qte'], l['art'], ENT_ID))
                
                st.session_state.last_fac = {
                    "ref": ref, "cl": cl_nom, "tot": net_total, "pay": cl_paye, 
                    "reste": reste, "dev": v_devise, "items": lignes_v, "date": d_now, "fmt": v_format
                }
                st.session_state.panier = {}
                st.rerun()
    else:
        # --- MODE FACTURE ---
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        html_facture = f"""
        <div class="fac-box">
            <center>
                <h3>{C_NOM}</h3>
                <p style="font-size:12px;">{C_ADR}<br>Tél: {C_TEL}</p>
                <hr>
                <p><b>REF: {f['ref']}</b><br>Client: {f['cl']}<br>Date: {f['date']}</p>
            </center>
            <table style="width:100%; font-size:12px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #000;">
                    <th align="left">Désignation</th>
                    <th align="center">Q</th>
                    <th align="right">Total</th>
                </tr>
                {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <p align="right"><b>TOTAL : {f['tot']:,.2f} {f['dev']}</b></p>
            <p align="right">Reçu : {f['pay']:,.2f}<br>Reste : {f['reste']:,.2f}</p>
            <br>
            <div class="sig-line">Signature</div>
            <div style="clear:both;"></div>
        </div>
        """
        st.markdown(html_facture, unsafe_allow_html=True)
        
        c_p1, c_p2, c_p3 = st.columns(3)
        c_p1.button("🖨️ IMPRIMER / PDF", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        
        # Bouton Partage WhatsApp
        wa_text = f"Facture {f['ref']} de {C_NOM}. Total: {f['tot']} {f['dev']}. Merci pour votre achat !"
        c_p2.markdown(f'<a href="https://wa.me/?text={wa_text}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold;">📲 PARTAGER</button></a>', unsafe_allow_html=True)
        c_p3.info("Info: Pour sauvegarder en PDF, sélectionnez 'Imprimer' puis destination 'Enregistrer en PDF'.")

# ==============================================================================
# 8. DETTES (PAIEMENT PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 GESTION DES DETTES")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    
    if not d_list:
        st.success("Aucune dette enregistrée.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in d_list:
            with st.expander(f"👤 CLIENT: {dcl} | RESTE: {dmt:,.2f} {ddv}"):
                hist = json.loads(dhi)
                st.write("**Historique des versements :**")
                st.table(pd.DataFrame(hist))
                
                v_montant = st.number_input("Nouveau Versement", 0.0, float(dmt), key=f"pay_in_{did}")
                if st.button("VALIDER LE PAIEMENT", key=f"btn_p_{did}"):
                    n_reste = dmt - v_montant
                    hist.append({"date": datetime.now().strftime("%d/%m/%Y"), "paye": v_montant})
                    
                    if n_reste <= 0.1:
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                        st.balloons()
                    else:
                        run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_reste, json.dumps(hist), did))
                    
                    # Update Vente
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_montant, v_montant, drf, ENT_ID))
                    st.rerun()

# ==============================================================================
# 9. STOCK (MODIFICATION PRIX & SUPPRESSION)
# ==============================================================================
elif st.session_state.page == "STOCK" and ROLE != "VENDEUR":
    st.header("📦 INVENTAIRE")
    with st.expander("➕ AJOUTER UN ARTICLE"):
        with st.form("f_add"):
            n1, n2, n3, n4 = st.columns([3, 1, 1, 1])
            na = n1.text_input("Désignation")
            nq = n2.number_input("Quantité", 1)
            np = n3.number_input("Prix Vente", 0.0)
            nd = n4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])
            col1.write(f"**{sn}**")
            col2.write(f"Stock: {sq}")
            new_px = col3.number_input("Prix", value=float(sp), key=f"px_ed_{sid}")
            if col4.button("💾", key=f"sv_p_{sid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_px, sid))
                st.rerun()
            if col5.button("🗑️", key=f"del_p_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ==============================================================================
# 10. CONFIGURATION & VENDEURS
# ==============================================================================
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ PARAMÈTRES")
    t_cfg, t_ven = st.tabs(["🏢 BOUTIQUE", "👥 COMPTES VENDEURS"])
    
    with t_cfg:
        with st.form("f_cfg"):
            e_n = st.text_input("Nom Entreprise", C_NOM)
            e_a = st.text_input("Adresse", C_ADR)
            e_t = st.text_input("WhatsApp", C_TEL)
            e_x = st.number_input("Taux (1 USD = ? CDF)", value=C_TX)
            e_m = st.text_area("Texte défilant", value=C_MSG)
            if st.form_submit_button("APPLIQUER"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?", 
                       (e_n.upper(), e_a, e_t, e_x, e_m, ENT_ID))
                st.rerun()

    with t_ven:
        st.subheader("Nouveau Vendeur")
        with st.form("f_v"):
            vu, vp = st.text_input("Identifiant"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER"):
                run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,'VENDEUR',?)", (vu.lower(), make_hashes(vp), ENT_ID))
                st.rerun()
        st.write("---")
        vs = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
        for v in vs:
            c_v1, c_v2 = st.columns([3, 1])
            c_v1.write(v[0])
            if c_v2.button("Supprimer", key=f"v_rm_{v[0]}"):
                run_db("DELETE FROM users WHERE username=?", (v[0],))
                st.rerun()

# ==============================================================================
# 11. MON PROFIL & PHOTO
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL")
    curr_data = run_db("SELECT full_name, telephone FROM users WHERE username=?", (USER,), fetch=True)[0]
    with st.form("f_prof"):
        f_n = st.text_input("Nom Complet", curr_data[0])
        f_t = st.text_input("Tél", curr_data[1])
        f_p = st.text_input("Changer Mot de passe (Laisser vide si inchangé)", type="password")
        f_img = st.file_uploader("Photo de profil", type=["png", "jpg", "jpeg"])
        if st.form_submit_button("SAUVEGARDER"):
            if f_p: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(f_p), USER))
            if f_img: run_db("UPDATE users SET photo=? WHERE username=?", (f_img.getvalue(), USER))
            run_db("UPDATE users SET full_name=?, telephone=? WHERE username=?", (f_n, f_t, USER))
            st.success("Profil mis à jour !")
            st.rerun()

# ==============================================================================
# 12. SUPER ADMIN (GESTION SaaS)
# ==============================================================================
elif st.session_state.page == "SaaS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 ADMINISTRATION GLOBALE")
    clients = run_db("SELECT ent_id, nom_ent, status FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    for eid, en, est in clients:
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2, 1, 1])
            cl1.write(f"🏢 {en} ({eid})")
            cl2.write(f"Statut: {est}")
            if cl3.button("PAUSE/ACTIF", key=f"btn_s_{eid}"):
                ns = "PAUSE" if est == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (ns, eid))
                st.rerun()

# ==============================================================================
# 13. RAPPORTS
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste", "Devise"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER RAPPORT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
