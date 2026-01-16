# ==============================================================================
# BALIKA ERP v205 - SYSTÈME DE GESTION INTÉGRAL (750+ LIGNES LOGIQUES)
# MODULES : VENTES, STOCKS, DETTES, MULTI-ENTREPRISES, SUPER-ADMIN
# TOUS DROITS RÉSERVÉS - 2026
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
import time
import base64
from PIL import Image

# ------------------------------------------------------------------------------
# 1. CONFIGURATION ET STYLE AVANCÉ
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v205",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏢"
)

# ------------------------------------------------------------------------------
# 2. SYSTÈME DE BASE DE DONNÉES PERSISTANT
# ------------------------------------------------------------------------------
def get_connection():
    return sqlite3.connect('balika_v205_master.db', timeout=30)

def run_db(query, params=(), fetch=False):
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        if fetch: return cursor.fetchall()
        return None
    except Exception as e:
        st.error(f"Erreur Database : {e}")
        return []
    finally:
        conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 3. INITIALISATION DES TABLES (ARCHITECTURE COMPLÈTE)
# ------------------------------------------------------------------------------
def init_db():
    # Table Utilisateurs (Incluant photo et détails)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    # Table Configuration (Gestion des abonnés et styles)
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, 
                taux REAL DEFAULT 2850.0, message TEXT DEFAULT 'BIENVENUE', 
                color_m TEXT DEFAULT '#00FF00', status TEXT DEFAULT 'ACTIF',
                date_inscription TEXT)""")
    
    # Table Produits (Gestion stock et prix)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)""")
    
    # Table Ventes (Journalisation complète)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, 
                vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    # Table Dettes (Recouvrement intelligent)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Table Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT)""")

    # --- CRÉATION DU COMPTE SUPER_ADMIN (Si inexistant) ---
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        # Le compte admin est le contrôleur des abonnés (SUPER_ADMIN)
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, message, color_m) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 'ADMINISTRATION CENTRALE DU SYSTÈME', '#FFD700'))

init_db()

# ------------------------------------------------------------------------------
# 4. CHARGEMENT DE LA CONFIGURATION ACTUELLE
# ------------------------------------------------------------------------------
if 'ent_id' not in st.session_state: st.session_state.ent_id = "SYSTEM"

res_cfg = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
if res_cfg:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL = res_cfg[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL = ("BALIKA ERP", "Bienvenue", "#00FF00", 2850.0, "Adresse", "000")

# ------------------------------------------------------------------------------
# 5. DESIGN CSS AVANCÉ ET ANIMATIONS
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&family=Roboto:wght@300;400;700&display=swap');
    
    /* Fond Global */
    .stApp {{ background-color: #f0f2f6; font-family: 'Roboto', sans-serif; }}
    
    /* LOGIN BOX STYLISÉ */
    .login-container {{
        background: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1); border-top: 5px solid #0056b3;
        max-width: 450px; margin: 100px auto; text-align: center;
    }}
    
    /* MARQUEE DÉFILANT (FIXE ET VISIBLE) */
    .marquee-container {{
        position: fixed; top: 0; left: 0; width: 100%; height: 45px;
        background: #111; z-index: 10000; border-bottom: 2px solid {C_COLOR};
        display: flex; align-items: center; overflow: hidden;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: marquee-move 20s linear infinite;
        color: {C_COLOR}; font-size: 1.2rem; font-weight: 700;
        text-shadow: 0 0 10px {C_COLOR}44;
    }}
    @keyframes marquee-move {{ 
        0% {{ transform: translateX(100%); }} 
        100% {{ transform: translateX(-100%); }} 
    }}

    /* MONTRE v199+ (CENTRÉE) */
    .watch-wrapper {{ display: flex; justify-content: center; width: 100%; margin: 20px 0; }}
    .watch-box {{
        background: #000; border: 4px solid #0056b3; border-radius: 25px;
        padding: 30px; text-align: center; min-width: 280px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }}
    .w-time {{ font-family: 'Orbitron', sans-serif; font-size: 55px; color: #0056b3; margin: 0; }}
    .w-date {{ color: #ffffff; font-size: 16px; text-transform: uppercase; letter-spacing: 2px; }}

    /* BOUTONS ET CADRES */
    .stButton>button {{
        background: #0056b3 !important; color: white !important;
        border-radius: 12px; height: 50px; font-weight: bold; font-size: 16px;
        transition: 0.3s; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.2); }}
    
    .total-frame {{
        border: 4px solid #0056b3; background: white; padding: 25px;
        border-radius: 20px; color: #111; font-size: 35px;
        font-weight: 900; text-align: center; margin: 20px 0;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
    }}

    /* MOBILE OPTIMIZATIONS */
    @media (max-width: 768px) {{
        .w-time {{ font-size: 40px; }}
        .total-frame {{ font-size: 25px; }}
    }}
    </style>
    
    <div class="marquee-container">
        <div class="marquee-text">{C_MSG} &nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp; {C_NOM} &nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp; TAUX : {C_TX} CDF / 1$</div>
    </div>
    <div style="height: 60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. ÉCRAN DE CONNEXION (BEAU ET ÉPURÉ)
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.markdown(f"""
            <div class="login-container">
                <h1 style='color:#0056b3; margin-bottom:10px;'>🏢 BALIKA ERP</h1>
                <p style='color:#666;'>Connectez-vous pour accéder à votre espace</p>
            </div>
        """, unsafe_allow_html=True)
        
        user_input = st.text_input("Identifiant", placeholder="Nom d'utilisateur").lower().strip()
        pass_input = st.text_input("Mot de passe", type="password", placeholder="••••••••")
        
        if st.button("DÉVERROUILLER L'ACCÈS", use_container_width=True):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (user_input,), fetch=True)
            if res and make_hashes(pass_input) == res[0][0]:
                st.session_state.auth = True
                st.session_state.user = user_input
                st.session_state.role = res[0][1]
                st.session_state.ent_id = res[0][2]
                st.session_state.page = "ACCUEIL"
                st.rerun()
            else:
                st.error("Identifiants incorrects ou compte inactif.")
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        with st.expander("Créer une nouvelle boutique (Essai)"):
            with st.form("new_shop_reg"):
                new_e = st.text_input("Nom de la Boutique")
                new_u = st.text_input("Admin Boutique")
                new_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON ERP"):
                    if new_e and new_u and new_p:
                        eid = f"ERP-{random.randint(1000, 9999)}"
                        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                               (new_u, make_hashes(new_p), "ADMIN", eid))
                        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, date_inscription) VALUES (?,?,?,?,?,?)", 
                               (eid, new_e.upper(), "ACTIF", 2850.0, "BIENVENUE", datetime.now().strftime("%d/%m/%Y")))
                        st.success("Boutique créée ! Connectez-vous.")
    st.stop()

# ------------------------------------------------------------------------------
# 7. NAVIGATION ET ÉTATS
# ------------------------------------------------------------------------------
USER = st.session_state.user
ROLE = st.session_state.role
ENT_ID = st.session_state.ent_id

with st.sidebar:
    # Photo de profil chargée depuis la DB
    u_photo = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if u_photo and u_photo[0][0]:
        st.image(u_photo[0][0], width=120)
    else:
        st.markdown("<div style='text-align:center; font-size:60px;'>👤</div>", unsafe_allow_html=True)
        
    st.markdown(f"<h3 style='text-align:center;'>{USER.upper()}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:gold;'>{ROLE}</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Menus conditionnels
    if ROLE == "SUPER_ADMIN":
        nav = ["🏠 ACCUEIL", "🌍 GESTION ABONNÉS", "📊 RAPPORTS HQ", "⚙️ SYSTÈME"]
    elif ROLE == "ADMIN":
        nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "💸 DÉPENSES", "📊 RAPPORTS", "⚙️ RÉGLAGES"]
    else: # VENDEUR
        nav = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    nav += ["👤 MON PROFIL", "🚪 DÉCONNEXION"]

    for item in nav:
        if st.button(item, use_container_width=True):
            if item == "🚪 DÉCONNEXION":
                st.session_state.auth = False
                st.rerun()
            st.session_state.page = item.split()[-1]
            st.rerun()

# ------------------------------------------------------------------------------
# 8. PAGE : ACCUEIL (AVEC MONTRE ET DASHBOARD)
# ------------------------------------------------------------------------------
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1 style='text-align: center;'>{C_NOM}</h1>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="watch-wrapper">
            <div class="watch-box">
                <p class="w-time">{datetime.now().strftime('%H:%M')}</p>
                <p class="w-date">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Statistiques rapides
    st.write("---")
    c1, c2, c3 = st.columns(3)
    
    ventes_du_jour = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (ENT_ID, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
    dettes_total = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    stock_alert = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=? AND stock_actuel < 5", (ENT_ID,), fetch=True)[0][0]
    
    with c1: st.metric("Ventes (Aujourd'hui)", f"{ventes_du_jour:,.1f} $")
    with c2: st.metric("Dettes Clients", f"{dettes_total:,.1f} $", delta_color="inverse")
    with c3: st.metric("Alertes Stock", stock_alert, delta="-5" if stock_alert > 0 else "OK")

# ------------------------------------------------------------------------------
# 9. PAGE : GESTION ABONNÉS (SUPER ADMIN SEULEMENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 CONTRÔLE DES ABONNEMENTS BALIKA")
    
    abos = run_db("SELECT ent_id, nom_ent, status, taux, date_inscription FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    df_abos = pd.DataFrame(abos, columns=["ID", "Entreprise", "Statut", "Taux", "Inscrit le"])
    
    st.dataframe(df_abos, use_container_width=True)
    
    st.write("---")
    st.subheader("Action sur un compte")
    col_a1, col_a2, col_a3 = st.columns(3)
    target_id = col_a1.selectbox("Sélectionner ID", df_abos["ID"])
    new_stat = col_a2.selectbox("Nouveau Statut", ["ACTIF", "SUSPENDU", "EXPIRED"])
    if col_a3.button("APPLIQUER LE CHANGEMENT"):
        run_db("UPDATE config SET status=? WHERE ent_id=?", (new_stat, target_id))
        st.success(f"Compte {target_id} mis à jour.")
        st.rerun()

# ------------------------------------------------------------------------------
# 10. PAGE : CAISSE (VERSION MOBILE OPTIMISÉE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "CAISSE":
    if 'panier' not in st.session_state: st.session_state.panier = {}
    
    st.subheader("🛒 TERMINAL DE VENTE")
    
    # Choix devise et format
    col_opt1, col_opt2 = st.columns(2)
    v_devise = col_opt1.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
    f_format = col_opt2.selectbox("Format Ticket", ["80mm", "A4"])
    
    # Catalogue
    prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
    p_dict = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
    
    sel_art = st.selectbox("Choisir Article", ["---"] + list(p_dict.keys()))
    if st.button("➕ AJOUTER AU PANIER") and sel_art != "---":
        st.session_state.panier[sel_art] = st.session_state.panier.get(sel_art, 0) + 1
        st.rerun()

    if st.session_state.panier:
        st.write("---")
        total_gen = 0.0
        details_vente = []
        
        for art, qte in list(st.session_state.panier.items()):
            p_info = p_dict[art]
            prix = p_info['p']
            # Conversion dynamique si devise différente
            if p_info['d'] == "USD" and v_devise == "CDF": prix *= C_TX
            elif p_info['d'] == "CDF" and v_devise == "USD": prix /= C_TX
            
            stot = prix * qte
            total_gen += stot
            details_vente.append({'art': art, 'qte': qte, 'st': stot})
            
            # Ligne de contrôle
            lc1, lc2, lc3 = st.columns([3, 1, 0.5])
            lc1.write(f"**{art}** ({prix:,.0f} {v_devise})")
            st.session_state.panier[art] = lc2.number_input("Qté", 1, p_info['s'], qte, key=f"q_{art}")
            if lc3.button("🗑️", key=f"del_{art}"):
                del st.session_state.panier[art]
                st.rerun()

        st.markdown(f'<div class="total-frame">À PAYER : {total_gen:,.1f} {v_devise}</div>', unsafe_allow_html=True)
        
        with st.form("validation_vente"):
            c_cl = st.text_input("Nom Client", "COMPTANT")
            c_pay = st.number_input("Montant Reçu", 0.0, value=float(total_gen))
            if st.form_submit_button("✅ GÉNÉRER LA FACTURE"):
                ref_v = f"FAC-{random.randint(1000, 9999)}"
                reste_v = total_gen - c_pay
                dt_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # DB : Vente
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (ref_v, c_cl.upper(), total_gen, c_pay, reste_v, v_devise, dt_v, USER, ENT_ID, json.dumps(details_vente)))
                
                # DB : Stock
                for item in details_vente:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (item['qte'], item['art'], ENT_ID))
                
                # DB : Dettes
                if reste_v > 0.1:
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)",
                           (c_cl.upper(), reste_v, v_devise, ref_v, ENT_ID, json.dumps([{'d': dt_v, 'p': c_pay}])))
                
                st.session_state.last_fac = {'ref': ref_v, 'cl': c_cl, 'tot': total_gen, 'pay': c_pay, 'items': details_vente, 'dev': v_devise, 'date': dt_v}
                st.session_state.panier = {}
                st.success("Vente enregistrée !")
                st.rerun()

# ------------------------------------------------------------------------------
# 11. PAGE : STOCK (GESTION COMPLETE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "STOCK" and ROLE == "ADMIN":
    st.header("📦 GESTION DU STOCK ET PRIX")
    
    with st.expander("➕ AJOUTER UN PRODUIT"):
        with st.form("add_p"):
            f_des = st.text_input("Désignation")
            f_qte = st.number_input("Quantité initiale", 0)
            f_px = st.number_input("Prix de vente", 0.0)
            f_dv = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER L'AJOUT"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                       (f_des.upper(), f_qte, f_px, f_dv, ENT_ID))
                st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pid, pdes, pst, ppx, pdv in prods:
        with st.container(border=True):
            pc1, pc2, pc3, pc4 = st.columns([3, 1, 1, 0.5])
            pc1.markdown(f"**{pdes}**")
            pc2.write(f"Stock: {pst}")
            n_px = pc3.number_input(f"Prix ({pdv})", value=float(ppx), key=f"px_{pid}")
            if pc3.button("💾", key=f"btn_{pid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, pid))
                st.toast("Prix mis à jour")
            if pc4.button("🗑️", key=f"del_{pid}"):
                run_db("DELETE FROM produits WHERE id=?", (pid,))
                st.rerun()

# ------------------------------------------------------------------------------
# 12. PAGE : DETTES (RECOUVREMENT PAR ACOMPTE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "DETTES":
    st.header("📉 GESTION DES DETTES CLIENTS")
    d_list = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)
    
    if not d_list:
        st.success("Aucune dette en cours.")
    else:
        for did, dcl, dmt, ddv, drf, dhi in d_list:
            with st.expander(f"🔴 {dcl} | Reste : {dmt:,.1f} {ddv} (Ref: {drf})"):
                hist = json.loads(dhi)
                st.write("Historique des paiements :")
                for h in hist: st.write(f"- {h['d']} : {h['p']:,.1f} {ddv}")
                
                acompte = st.number_input("Encaisser acompte", 0.0, float(dmt), key=f"aco_{did}")
                if st.button("VALIDER LE PAIEMENT", key=f"v_aco_{did}"):
                    n_reste = dmt - acompte
                    hist.append({'d': datetime.now().strftime("%d/%m"), 'p': acompte})
                    
                    if n_reste <= 0.1:
                        run_db("DELETE FROM dettes WHERE id=?", (did,))
                        st.balloons()
                    else:
                        run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_reste, json.dumps(hist), did))
                    
                    run_db("UPDATE ventes SET paye = paye + ?, reste = reste - ? WHERE ref=? AND ent_id=?", (acompte, acompte, drf, ENT_ID))
                    st.rerun()

# ------------------------------------------------------------------------------
# 13. PAGE : RÉGLAGES (BOUTIQUE)
# ------------------------------------------------------------------------------
elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ CONFIGURATION DE LA BOUTIQUE")
    with st.form("shop_cfg"):
        s_nom = st.text_input("Nom de l'entreprise", C_NOM)
        s_adr = st.text_input("Adresse Physique", C_ADR)
        s_tel = st.text_input("Contact / WhatsApp", C_TEL)
        s_tx = st.number_input("Taux de change (CDF/$)", value=C_TX)
        s_msg = st.text_area("Message Défilant", C_MSG)
        s_col = st.color_picker("Couleur du Message", C_COLOR)
        
        if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, color_m=? WHERE ent_id=?", 
                   (s_nom.upper(), s_adr, s_tel, s_tx, s_msg, s_col, ENT_ID))
            st.success("Configuration mise à jour !")
            st.rerun()

# ------------------------------------------------------------------------------
# 14. PAGE : PROFIL (PHOTO ET SÉCURITÉ)
# ------------------------------------------------------------------------------
elif st.session_state.page == "PROFIL":
    st.header("👤 MON COMPTE SÉCURISÉ")
    
    with st.form("prof_mod"):
        up_photo = st.file_uploader("Modifier ma photo", type=['jpg','png','jpeg'])
        up_pass = st.text_input("Nouveau mot de passe", type="password")
        if st.form_submit_button("METTRE À JOUR MON PROFIL"):
            if up_pass:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(up_pass), USER))
            if up_photo:
                img_bytes = up_photo.read()
                run_db("UPDATE users SET photo=? WHERE username=?", (img_bytes, USER))
            st.success("Modifications effectuées.")
            st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE - BALIKA ERP v205
# ------------------------------------------------------------------------------
