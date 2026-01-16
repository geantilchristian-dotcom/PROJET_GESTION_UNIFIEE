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
# 1. CONFIGURATION SYSTÈME & ENGINE (BALIKA CLOUD v420)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v420", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation complète de l'état de la session (Session State)
# On ne supprime rien, on initialise tout pour éviter les erreurs "KeyError"
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'ent_id' not in st.session_state: st.session_state.ent_id = ""
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'panier' not in st.session_state: st.session_state.panier = {}
if 'last_fac' not in st.session_state: st.session_state.last_fac = None
if 'devise_vente' not in st.session_state: st.session_state.devise_vente = "USD"

# Moteur de Base de Données SaaS (Multi-entreprises)
def run_db(query, params=(), fetch=False):
    try:
        # Utilisation d'une base robuste avec mode WAL pour les accès simultanés
        with sqlite3.connect('balika_cloud_v420.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Base de Données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. ARCHITECTURE DES TABLES (SCHÉMA COMPLET SANS SUPPRESSION)
# ==============================================================================
def init_db():
    # Table Utilisateurs : Inclut les vendeurs, admin et profil
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT, 
                photo BLOB)""")
    
    # Table Configuration : Coeur du SaaS et infos entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL, 
                message TEXT, 
                status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, 
                logo BLOB)""")
    
    # Table Produits : Stock cloisonné (Pas de prix d'achat visible en vente)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT)""")
    
    # Table Ventes : Archives complètes pour rapports
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
    
    # Table Dettes : Gestion des paiements échelonnés
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")

    # Injection du compte Maître si inexistant
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD HQ', 'ACTIF', 2850.0, 'Bienvenue dans votre ERP Cloud'))

init_db()

# ==============================================================================
# 3. CHARGEMENT DES PARAMÈTRES ET DESIGN CSS (RESPONSIVE)
# ==============================================================================
if st.session_state.auth:
    # Récupération des données de l'entreprise connectée
    c_res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if c_res:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = c_res[0]
        # Sécurité : Si le compte est mis en pause par le Super-Admin
        if C_STATUS == 'PAUSE' and st.session_state.role != "SUPER_ADMIN":
            st.session_state.auth = False
            st.warning("⚠️ ACCÈS SUSPENDU. Veuillez contacter le support BALIKA.")
            st.stop()
    else:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA", "Prêt", 2850.0, "", "", ""
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA CLOUD", "Gérez votre business", 2850.0, "", "", ""

# CSS Personnalisé (Marquee, Boutons, Responsive Mobile)
st.markdown(f"""
    <style>
    /* Mode Clair Forcé */
    :root {{ color-scheme: light; }}
    .stApp {{ background-color: #FFFFFF; color: #000000; text-align: center !important; }}
    
    /* Barre Défilante (Marquee) v192 */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #000000; color: #FF8C00;
        padding: 12px 0; position: fixed; top: 0; left: 0; z-index: 9999;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: marquee 25s linear infinite; font-size: 18px; font-weight: bold;
    }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Boutons Gradient Balika */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 50px;
        font-weight: bold; border: none; width: 100%; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.02); }}

    /* Cadre Total Coloré (Demande utilisateur) */
    .total-frame {{
        border: 3px solid #FF8C00; background: #FFF3E0; padding: 20px;
        border-radius: 15px; text-align: center; font-size: 28px;
        color: #E65100; font-weight: 900; margin: 15px 0;
    }}

    /* Optimisation Impression */
    @media print {{
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }}
        .print-area {{ width: 100% !important; border: none !important; }}
    }}
    
    /* Correction Mobile */
    [data-testid="column"] {{ width: 100% !important; flex: 1 1 auto !important; min-width: 100% !important; }}
    @media (min-width: 768px) {{
        [data-testid="column"] {{ min-width: 0 !important; }}
    }}
    </style>
    <div class="marquee-container"><div class="marquee-text">✨ {C_NOM} : {C_MSG} | 💹 TAUX : 1 USD = {C_TX} CDF</div></div>
    <div style="margin-top: 80px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. ÉCRAN DE CONNEXION ET CRÉATION DE COMPTE
# ==============================================================================
if not st.session_state.auth:
    _, center_col, _ = st.columns([0.1, 0.8, 0.1])
    with center_col:
        st.image("https://cdn-icons-png.flaticon.com/512/2622/2622143.png", width=100)
        st.title(C_NOM)
        tab_log, tab_reg = st.tabs(["🔒 SE CONNECTER", "🚀 CRÉER UN COMPTE"])
        
        with tab_log:
            u = st.text_input("Identifiant", key="login_u").lower().strip()
            p = st.text_input("Mot de passe", type="password", key="login_p")
            if st.button("ACCÉDER À L'ERP"):
                user_data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
                if user_data and make_hashes(p) == user_data[0][0]:
                    st.session_state.auth = True
                    st.session_state.user = u
                    st.session_state.role = user_data[0][1]
                    st.session_state.ent_id = user_data[0][2]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")
        
        with tab_reg:
            with st.form("signup_form"):
                new_ent = st.text_input("Nom de votre Business").upper().strip()
                new_u = st.text_input("Identifiant Admin (ex: boss1)").lower().strip()
                new_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON COMPTE"):
                    if new_ent and new_u and new_p:
                        check = run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True)
                        if not check:
                            eid = f"E-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'ADMIN', ?)", (new_u, make_hashes(new_p), eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, 'ACTIF', 2850.0, 'Bienvenue')", (eid, new_ent))
                            st.success("✅ Compte créé ! Connectez-vous.")
                        else: st.error("L'identifiant existe déjà.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. SIDEBAR & NAVIGATION (MENU SELON RÔLE)
# ==============================================================================
with st.sidebar:
    # Affichage Photo Profil (Si dispo)
    profile_data = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if profile_data and profile_data[0][0]:
        st.image(profile_data[0][0], width=100)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🌍 ABONNÉS", "📊 SYSTÈME", "⚙️ MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
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
# 6. LOGIQUE CAISSE (PANIER, MULTIDEVISE, FACTURE 80MM)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 Terminal de Vente")
        v_devise = st.radio("Devise de paiement :", ["USD", "CDF"], horizontal=True)
        
        # Chargement Stock
        produits = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'prix': r[1], 'stock': r[2], 'dev': r[3]} for r in produits}
        
        col_sel, col_add = st.columns([3, 1])
        choix = col_sel.selectbox("Sélectionner article", ["---"] + list(p_dict.keys()))
        if col_add.button("➕ AJOUTER"):
            if choix != "---":
                st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
                st.rerun()
        
        if st.session_state.panier:
            st.write("### 📝 Votre Panier")
            net_a_payer = 0.0
            list_details = []
            
            for art, qte in list(st.session_state.panier.items()):
                # Conversion auto selon taux config
                p_u_base = p_dict[art]['prix']
                d_base = p_dict[art]['dev']
                
                if d_base == "USD" and v_devise == "CDF": p_u = p_u_base * C_TX
                elif d_base == "CDF" and v_devise == "USD": p_u = p_u_base / C_TX
                else: p_u = p_u_base
                
                stot = p_u * qte
                net_a_payer += stot
                list_details.append({"art": art, "qte": qte, "pu": p_u, "st": stot})
                
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_dict[art]['stock'], value=qte, key=f"pan_{art}")
                if c3.button("❌", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()
            
            st.markdown(f'<div class="total-frame">NET À PAYER : {net_a_payer:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_paye = st.number_input("MONTANT REÇU", min_value=0.0, value=float(net_a_payer))
            
            if st.button("✅ VALIDER ET IMPRIMER"):
                v_ref = f"FAC-{random.randint(10000, 99999)}"
                v_dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = net_a_payer - c_paye
                
                # Enregistrement Vente
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (v_ref, c_nom, net_a_payer, c_paye, reste, v_devise, v_dt, USER, ENT_ID, json.dumps(list_details)))
                
                # Gestion Dette Automatique (Si reste > 0)
                if reste > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", 
                           (c_nom, reste, v_devise, v_ref, ENT_ID, json.dumps([{"date": v_dt, "paye": c_paye}])))
                
                # Décrémentation Stock
                for i in list_details:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": v_ref, "cl": c_nom, "tot": net_a_payer, "pay": c_paye, "dev": v_devise, "items": list_details, "date": v_dt}
                st.session_state.panier = {}
                st.rerun()
    else:
        # MODE FACTURE (v192 - 80mm)
        f = st.session_state.last_fac
        st.header("📄 Facture Prête")
        
        fac_html = f"""
        <div class="print-area" style="width: 300px; background:white; color:black; padding:10px; border:1px solid #000; margin:auto; font-family: monospace; font-size:12px;">
            <center>
                <h2 style="margin:0;">{C_NOM}</h2>
                <p style="margin:0;">{C_ENTETE}</p>
                <p style="margin:0;">{C_ADR}<br>Tél: {C_TEL}</p>
            </center>
            <hr>
            <p>REF: {f['ref']}<br>Client: {f['cl']}<br>Date: {f['date']}<br>Vendeur: {USER}</p>
            <table style="width:100%; border-collapse:collapse;">
                <tr style="border-bottom:1px dashed #000;"><th>Art</th><th>Q</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Payé: {f['pay']:,.2f}<br>Reste: {f['tot']-f['pay']:,.2f}</p>
            <center><p>Merci de votre confiance !</p></center>
        </div>
        """
        st.markdown(fac_html, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        if c1.button("🖨️ IMPRIMER"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if c2.button("📲 PARTAGER"):
            st.info("Lien de partage généré.")
        if c3.button("🔄 NOUVELLE VENTE"):
            st.session_state.last_fac = None
            st.rerun()

# ==============================================================================
# 7. LOGIQUE STOCK (MODIFICATION ET SUPPRESSION)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 Gestion du Stock")
    
    with st.expander("➕ Ajouter un Article"):
        with st.form("new_art"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            na = c1.text_input("Désignation")
            nq = c2.number_input("Stock Initial", 1)
            np = c3.number_input("Prix de Vente")
            nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    st.write("---")
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pid, pnom, pstk, ppx, pdv in items:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
            col1.write(f"**{pnom}**")
            col2.write(f"En stock: `{pstk}`")
            # Modification du prix sans supprimer la ligne
            n_px = col3.number_input("Prix", value=float(ppx), key=f"px_{pid}")
            if n_px != ppx:
                if col3.button("💾", key=f"up_{pid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, pid))
                    st.toast("Prix mis à jour !")
            # Suppression article
            if col4.button("🗑️", key=f"del_{pid}"):
                run_db("DELETE FROM produits WHERE id=?", (pid,))
                st.rerun()

# ==============================================================================
# 8. LOGIQUE DETTES (PAIEMENT ÉCHELONNÉ)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 Clients Débiteurs")
    dts = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    if not dts:
        st.success("Aucune dette enregistrée ! ✨")
    for did, dcl, dmt, ddv, drf, dhi in dts:
        with st.expander(f"🔴 {dcl} - Reste : {dmt:,.2f} {ddv} (Ref: {drf})"):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Historique :**")
                for h in json.loads(dhi):
                    st.write(f"- {h['date']} : {h['paye']:,.2f}")
            with c2:
                v_pay = st.number_input("Montant Versé", 0.0, float(dmt), key=f"pay_{did}")
                if st.button("Valider le paiement", key=f"btn_{did}"):
                    nm = dmt - v_pay
                    h_list = json.loads(dhi)
                    h_list.append({"date": datetime.now().strftime("%d/%m"), "paye": v_pay})
                    if nm <= 0.01:
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                    else:
                        run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(h_list), did))
                    # Sync avec les ventes
                    run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_pay, v_pay, drf, ENT_ID))
                    st.rerun()

# ==============================================================================
# 9. CONFIGURATION ET PROFIL (MODIFICATIONS DEMANDÉES)
# ==============================================================================
elif st.session_state.page == "CONFIG":
    st.header("⚙️ Paramètres")
    with st.expander("🏢 Informations de l'Entreprise"):
        with st.form("cfg_form"):
            f_nom = st.text_input("Nom Société", C_NOM)
            f_adr = st.text_input("Adresse", C_ADR)
            f_tel = st.text_input("Téléphone", C_TEL)
            f_tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TX)
            f_hdr = st.text_area("En-tête / Pied de facture", C_ENTETE)
            f_msg = st.text_input("Message Défilant", C_MSG)
            if st.form_submit_button("SAUVEGARDER LES MODIFS"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, entete_fac=?, message=? WHERE ent_id=?",
                       (f_nom.upper(), f_adr, f_tel, f_tx, f_hdr, f_msg, ENT_ID))
                st.rerun()

    with st.expander("👤 Mon Profil & Sécurité"):
        up_pass = st.text_input("Nouveau mot de passe", type="password")
        up_img = st.file_uploader("Changer photo de profil", type=['jpg', 'png'])
        if st.button("METTRE À JOUR LE PROFIL"):
            if up_pass:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(up_pass), USER))
            if up_img:
                img_bytes = up_img.getvalue()
                run_db("UPDATE users SET photo=? WHERE username=?", (img_bytes, USER))
            st.success("Profil mis à jour !")

elif st.session_state.page == "ACCUEIL":
    st.title(f"Bienvenue, {USER.upper()}")
    st.write(f"Aujourd'hui : {datetime.now().strftime('%d/%m/%Y')}")
    st.metric("Taux de change", f"1 USD = {C_TX} CDF")
    
    # Dashboard rapide
    v_data = run_db("SELECT SUM(paye) FROM ventes WHERE ent_id=? AND devise='USD'", (ENT_ID,), fetch=True)
    st.metric("Ventes du jour (USD)", f"{v_data[0][0] if v_data[0][0] else 0:,.2f} $")

elif st.session_state.page == "VENDEURS":
    st.header("👥 Gestion du Personnel")
    with st.form("new_v"):
        v_u = st.text_input("Nom d'utilisateur").lower()
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE VENDEUR"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'VENDEUR', ?)", 
                   (v_u, make_hashes(v_p), ENT_ID))
            st.rerun()
    
    st.write("---")
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        c1, c2 = st.columns([3, 1])
        c1.write(f"👤 **{s[0].upper()}**")
        if c2.button("Supprimer", key=f"s_{s[0]}"):
            run_db("DELETE FROM users WHERE username=?", (s[0],))
            st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 Rapports de Vente")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        df = pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
        st.dataframe(df, use_container_width=True)
        if st.button("🖨️ IMPRIMER LE JOURNAL"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
