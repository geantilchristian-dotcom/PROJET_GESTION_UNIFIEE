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
# 1. CONFIGURATION SYSTÈME & CORE SECURITY (v600)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP INFINITY v600", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State (Mémoire de l'application)
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 
        'user': "", 
        'role': "", 
        'ent_id': "", 
        'page': "ACCUEIL", 
        'panier': {}, 
        'last_fac': None,
        'temp_user_change': False
    })

# --- MOTEUR DE BASE DE DONNÉES ROBUSTE ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v600.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Fatale Base de Données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. SCHÉMA DE BASE DE DONNÉES COMPLET (SaaS READY)
# ==============================================================================
def init_db():
    # Table des Utilisateurs : Inclut Profil, Photo et Lien Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT, 
                photo BLOB, 
                full_name TEXT)""")
    
    # Table Configuration Entreprise : Paramètres SaaS
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL, 
                message TEXT, 
                status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, 
                logo BLOB, 
                devise_defaut TEXT DEFAULT 'USD')""")
    
    # Table Produits : Inventaire complet
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT, 
                categorie TEXT)""")
    
    # Table Ventes : Archives facturation
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
    
    # Table Dettes : Suivi des crédits clients
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")

    # Insertion des comptes par défaut (Admin & Admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD MASTER', 'ACTIF', 2850.0, 'Système Global v600 Activé'))

init_db()

# ==============================================================================
# 3. INTERFACE GRAPHIQUE (CSS & MARQUEE)
# ==============================================================================
# Chargement des variables globales d'entreprise
if st.session_state.auth:
    conf = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status FROM config WHERE ent_id=?", 
                  (st.session_state.ent_id,), fetch=True)
    if conf:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = conf[0]
        # Blocage si compte suspendu
        if C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
            st.error("🚨 VOTRE COMPTE EST SUSPENDU. CONTACTEZ BALIKA.")
            st.stop()
    else:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA", "Prêt", 2850.0, "", "", ""
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA CLOUD", "Gérez votre business", 2850.0, "", "", ""

st.markdown(f"""
    <style>
    /* Global & Typography */
    .stApp {{ background-color: #f4f7f6; }}
    h1, h2, h3, p, label {{ text-align: center !important; font-family: 'Segoe UI', sans-serif; }}

    /* Marquee v192 Style (Orange on Black) */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #000000; color: #FF8C00;
        padding: 15px 0; position: fixed; top: 0; left: 0; z-index: 9999;
        border-bottom: 3px solid #FF8C00; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap; font-weight: 900; font-size: 20px;
        animation: scroll-text 25s linear infinite;
    }}
    @keyframes scroll-text {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Buttons Style (White text on Blue/Orange Gradient) */
    .stButton>button {{
        background: linear-gradient(135deg, #1E3A8A, #2563EB) !important;
        color: white !important; border-radius: 15px; height: 55px;
        width: 100%; font-weight: bold; border: none; font-size: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.2); }}

    /* Total Frame (Colored Box) */
    .total-frame {{
        border: 5px solid #FF8C00; background: #000; padding: 30px;
        border-radius: 25px; color: #00FF00; font-size: 35px; font-weight: 900;
        margin: 25px 0; text-shadow: 2px 2px #000;
    }}

    /* Watch Style (v199) */
    .watch-box {{
        background: #111; color: #FF8C00; padding: 20px; border-radius: 60px;
        font-size: 28px; font-weight: bold; display: inline-block;
        border: 3px solid #FF8C00; margin-bottom: 25px; min-width: 250px;
    }}

    /* Mobile Responsive Fixes */
    @media (max-width: 600px) {{
        .total-frame {{ font-size: 22px; padding: 15px; }}
        .watch-box {{ font-size: 18px; }}
        [data-testid="column"] {{ width: 100% !important; min-width: 100% !important; }}
    }}
    
    /* Invoice Layouts */
    .ticket-80 {{ width: 300px; background: white; color: black; padding: 10px; margin: auto; border: 1px solid #000; font-family: monospace; font-size: 12px; }}
    .ticket-a4 {{ width: 800px; background: white; color: black; padding: 40px; margin: auto; border: 1px solid #ccc; }}
    </style>

    <div class="marquee-container">
        <div class="marquee-text">🏢 {C_NOM} | 💹 TAUX DU JOUR : 1$ = {C_TX} CDF | 📢 {C_MSG} | STATUS : {C_STATUS}</div>
    </div>
    <div style="margin-top: 110px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. ÉCRAN DE CONNEXION (SaaS LOGIN)
# ==============================================================================
if not st.session_state.auth:
    _, center_col, _ = st.columns([0.1, 0.8, 0.1])
    with center_col:
        st.image("https://cdn-icons-png.flaticon.com/512/6073/6073873.png", width=120)
        st.title("ACCÈS SÉCURISÉ")
        
        tab_login, tab_signup = st.tabs(["SE CONNECTER", "CRÉER UN COMPTE"])
        
        with tab_login:
            u_login = st.text_input("Identifiant (Username)").lower().strip()
            p_login = st.text_input("Mot de passe", type="password")
            if st.button("ENTRER DANS L'APPLICATION"):
                res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_login,), fetch=True)
                if res and make_hashes(p_login) == res[0][0]:
                    st.session_state.update({'auth':True, 'user':u_login, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")
        
        with tab_signup:
            with st.form("signup"):
                st.write("### Nouveau Business")
                s_ent = st.text_input("Nom de l'Entreprise")
                s_user = st.text_input("Nom d'utilisateur Admin").lower().strip()
                s_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if s_ent and s_user and s_pass:
                        eid = f"BAL-{random.randint(1000, 9999)}"
                        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                               (s_user, make_hashes(s_pass), "ADMIN", eid))
                        run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", 
                               (eid, s_ent.upper(), 2850.0, "Prêt pour les ventes"))
                        st.success("Compte créé ! Veuillez vous connecter.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ==============================================================================
with st.sidebar:
    # Photo de Profil (Prise de la DB)
    u_photo = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if u_photo and u_photo[0][0]:
        st.image(u_photo[0][0], width=120)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    
    st.markdown(f"### 👤 {USER.upper()}")
    st.markdown(f"**🏢 {C_NOM}**")
    st.write("---")
    
    # Menus selon les rôles
    if ROLE == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "🌍 ABONNÉS", "📊 RAPPORTS GÉNÉRAUX", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIGURATION", "👤 MON PROFIL"]
    else:
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 QUITTER SESSION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. PAGE ACCUEIL (MONTRE 80MM STYLE & DATE)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1 style='color:#1E3A8A;'>{C_NOM}</h1>", unsafe_allow_html=True)
    
    # La Montre Stylisée (v199)
    now = datetime.now()
    st.markdown(f"""
        <div class="watch-box">
            ⌚ {now.strftime('%H:%M:%S')}<br>
            📅 {now.strftime('%d / %m / %Y')}
        </div>
    """, unsafe_allow_html=True)
    
    st.write(f"Heureux de vous revoir, **{USER.upper()}**")
    
    # Statistiques Visuelles
    c1, c2, c3 = st.columns(3)
    v_tot = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES TOTALES", f"{v_tot:,.2f} $")
    
    d_tot = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES EN COURS", f"{d_tot:,.2f} $", delta_color="inverse")
    
    s_tot = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", s_tot)

# ==============================================================================
# 7. PAGE MON PROFIL (MODIFIER USER, PASSWORD, PHOTO) - DÉTAILLÉE
# ==============================================================================
elif st.session_state.page == "PROFIL":
    st.header("👤 GESTION DE MON COMPTE")
    
    with st.container(border=True):
        st.write("### 🔑 Sécurité & Identité")
        
        curr_u = st.text_input("Identifiant Actuel", value=USER, disabled=True)
        new_u = st.text_input("Nouvel Identifiant (Username)", value=USER)
        
        c_p1, c_p2 = st.columns(2)
        new_p = c_p1.text_input("Nouveau Mot de Passe", type="password", placeholder="Laisser vide pour garder l'ancien")
        conf_p = c_p2.text_input("Confirmer Mot de Passe", type="password")
        
        st.write("### 🖼️ Photo de Profil")
        new_img = st.file_uploader("Choisir une image", type=['png', 'jpg', 'jpeg'])
        
        if st.button("💾 ENREGISTRER TOUTES LES MODIFICATIONS"):
            # 1. Mise à jour Password si rempli
            if new_p:
                if new_p == conf_p:
                    run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
                    st.success("Mot de passe modifié !")
                else:
                    st.error("Les mots de passe ne correspondent pas.")
            
            # 2. Mise à jour Photo
            if new_img:
                img_bytes = new_img.getvalue()
                run_db("UPDATE users SET photo=? WHERE username=?", (img_bytes, USER))
                st.success("Photo de profil mise à jour !")
            
            # 3. Mise à jour Username (Attention : doit rester unique)
            if new_u != USER:
                try:
                    # On crée d'abord un nouveau record ou on update (dépend de la contrainte PK)
                    # Pour simplifier dans SQLite sans trigger complexe, on update le PK
                    run_db("UPDATE users SET username=? WHERE username=?", (new_u, USER))
                    st.session_state.user = new_u
                    st.success("Identifiant mis à jour !")
                except:
                    st.error("Cet identifiant est déjà utilisé.")
            
            st.rerun()

# ==============================================================================
# 8. PAGE CAISSE (FORMAT A4 / 80MM / MULTIDEVISE)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        
        # Options de Vente
        col_opt1, col_opt2 = st.columns(2)
        v_devise = col_opt1.selectbox("Devise de paiement", ["USD", "CDF"])
        v_format = col_opt2.selectbox("Format Facture", ["80mm (Ticket)", "A4 (Standard)"])
        
        # Sélection Articles
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_map = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        c_search, c_btn = st.columns([3, 1])
        choix = c_search.selectbox("Chercher un produit", ["---"] + list(p_map.keys()))
        if c_btn.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()
            
        # Affichage Panier
        if st.session_state.panier:
            st.write("---")
            total_v = 0.0
            items_v = []
            
            for art, qte in list(st.session_state.panier.items()):
                # Conversion auto
                px_base = p_map[art]['px']
                dv_base = p_map[art]['dv']
                
                if dv_base == "USD" and v_devise == "CDF": px_conv = px_base * C_TX
                elif dv_base == "CDF" and v_devise == "USD": px_conv = px_base / C_TX
                else: px_conv = px_base
                
                stot = px_conv * qte
                total_v += stot
                items_v.append({"art": art, "qte": qte, "pu": px_conv, "st": stot})
                
                c1, c2, c3 = st.columns([3, 1, 0.5])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_map[art]['stk'], value=qte, key=f"pan_{art}")
                if c3.button("❌", key=f"rm_{art}"):
                    del st.session_state.panier[art]; st.rerun()
            
            # FRAME TOTAL (Noir & Orange)
            st.markdown(f'<div class="total-frame">TOTAL À PAYER : {total_v:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            c_client = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_paye = st.number_input("MONTANT REÇU", value=float(total_v))
            
            if st.button("💾 ENREGISTRER LA VENTE"):
                v_ref = f"FAC-{random.randint(10000, 99999)}"
                v_dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                v_reste = total_v - c_paye
                
                # Sauvegarde Vente
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (v_ref, c_client, total_v, c_paye, v_reste, v_devise, v_dt, USER, ENT_ID, json.dumps(items_v)))
                
                # Gestion Dette Automatique
                if v_reste > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", 
                           (c_client, v_reste, v_devise, v_ref, ENT_ID, json.dumps([{"date": v_dt, "paye": c_paye}])))
                
                # Mise à jour Stock
                for i in items_v:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": v_ref, "cl": c_client, "tot": total_v, "pay": c_paye, "dev": v_devise, "items": items_v, "date": v_dt, "fmt": v_format}
                st.session_state.panier = {}
                st.rerun()
    else:
        # --- AFFICHAGE FACTURE (80mm ou A4) ---
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        if f['fmt'] == "80mm (Ticket)":
            html = f"""
            <div class="ticket-80">
                <center><h3>{C_NOM}</h3><p>{C_ENTETE}<br>Tél: {C_TEL}</p></center>
                <hr>
                <p>N°: {f['ref']}<br>Client: {f['cl']}<br>Date: {f['date']}</p>
                <table style="width:100%">
                    <tr style="border-bottom:1px solid #000"><th>Art</th><th>Q</th><th>T</th></tr>
                    {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
                </table>
                <hr><h2 align="right">{f['tot']:,.0f} {f['dev']}</h2>
                <p align="right">Payé: {f['pay']:,.0f}<br>Reste: {f['tot']-f['pay']:,.0f}</p>
            </div>
            """
        else:
            html = f"""
            <div class="ticket-a4">
                <table style="width:100%">
                    <tr>
                        <td><h1>{C_NOM}</h1><p>{C_ENTETE}<br>{C_ADR}</p></td>
                        <td align="right"><h2>FACTURE</h2><p>Réf: {f['ref']}<br>Date: {f['date']}</p></td>
                    </tr>
                </table>
                <hr>
                <p><b>Client:</b> {f['cl']}</p>
                <table style="width:100%; border-collapse:collapse;" border="1">
                    <tr style="background:#eee"><th>Désignation</th><th>Quantité</th><th>Prix Unitaire</th><th>Sous-Total</th></tr>
                    {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['pu']:,.2f}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
                </table>
                <h2 align="right">TOTAL À PAYER : {f['tot']:,.2f} {f['dev']}</h2>
                <p align="right">Montant Versé : {f['pay']:,.2f} | Reste : {f['tot']-f['pay']:,.2f}</p>
            </div>
            """
        
        st.markdown(html, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER FACTURE"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ==============================================================================
# 9. PAGE STOCK (MODIFIER PRIX / SUPPRIMER)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DES PRODUITS")
    
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("add_p"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            na = c1.text_input("Désignation")
            nq = c2.number_input("Quantité", 1)
            np = c3.number_input("Prix de Vente")
            nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER L'AJOUT"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    st.write("---")
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, snom, sqte, sprix, sdev in items:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
            col1.write(f"**{snom}**")
            col2.write(f"Stock: `{sqte}`")
            # Modification de prix en direct
            n_px = col3.number_input("Prix", value=float(sprix), key=f"px_{sid}")
            if n_px != sprix:
                if col3.button("💾", key=f"up_{sid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, sid))
                    st.rerun()
            # Suppression sans perte de ligne
            if col4.button("🗑️", key=f"del_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ==============================================================================
# 10. PAGE DETTES (PAIEMENT PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 SUIVI DES DETTES CLIENTS")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    
    if not d_list:
        st.success("Toutes les dettes sont payées ! 🎉")
    
    for did, dcl, dmt, ddv, drf, dhist in d_list:
        with st.expander(f"🔴 {dcl} | RESTE : {dmt:,.2f} {ddv}"):
            st.write(f"Facture associée : {drf}")
            history = json.loads(dhist)
            st.dataframe(pd.DataFrame(history), use_container_width=True)
            
            pay_val = st.number_input("Encaisser une tranche", 0.0, float(dmt), key=f"pay_{did}")
            if st.button("VALIDER LE PAIEMENT", key=f"btn_{did}"):
                new_reste = dmt - pay_val
                history.append({"date": datetime.now().strftime("%d/%m"), "paye": pay_val})
                
                if new_reste <= 0:
                    run_db("DELETE FROM dettes WHERE id=?", (did,))
                    st.balloons()
                else:
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (new_reste, json.dumps(history), did))
                
                # Mise à jour du rapport de vente
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (pay_val, pay_val, drf, ENT_ID))
                st.rerun()

# ==============================================================================
# 11. CONFIGURATION (ENTREPRISE & VENDEURS)
# ==============================================================================
elif st.session_state.page == "CONFIGURATION":
    st.header("⚙️ PARAMÈTRES GÉNÉRAUX")
    
    with st.expander("🏢 INFOS ENTREPRISE"):
        with st.form("cfg"):
            e_nom = st.text_input("Nom Société", C_NOM)
            e_adr = st.text_input("Adresse", C_ADR)
            e_tel = st.text_input("Téléphone", C_TEL)
            e_tx = st.number_input("Taux de Change (USD -> CDF)", value=C_TX)
            e_msg = st.text_input("Message Défilant", C_MSG)
            e_hdr = st.text_area("En-tête Facture", C_ENTETE)
            if st.form_submit_button("SAUVEGARDER CONFIG"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, entete_fac=? WHERE ent_id=?", 
                       (e_nom.upper(), e_adr, e_tel, e_tx, e_msg, e_hdr, ENT_ID))
                st.rerun()

elif st.session_state.page == "VENDEURS":
    st.header("👥 COMPTES VENDEURS")
    with st.form("v_add"):
        v_u = st.text_input("Identifiant Vendeur").lower()
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'VENDEUR', ?)", 
                   (v_u, make_hashes(v_p), ENT_ID))
            st.rerun()
    
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        st.write(f"👤 {s[0].upper()}")

# ==============================================================================
# 12. SUPER-ADMIN (GESTION SaaS ABONNÉS)
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES ENTREPRISES ABONNÉES")
    clients = run_db("SELECT ent_id, nom_ent, status, tel FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    for cid, cnom, cstat, ctel in clients:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"🏢 **{cnom}** (ID: {cid})")
            c2.write(f"Statut : `{cstat}`")
            
            btn_txt = "ACTIVER" if cstat == "PAUSE" else "SUSPENDRE"
            if c3.button(btn_txt, key=f"sw_{cid}"):
                new_stat = "ACTIF" if cstat == "PAUSE" else "PAUSE"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (new_stat, cid))
                st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 JOURNAL DES VENTES")
    v_data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if v_data:
        df = pd.DataFrame(v_data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
        st.dataframe(df, use_container_width=True)
        if st.button("🖨️ IMPRIMER LE RAPPORT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
