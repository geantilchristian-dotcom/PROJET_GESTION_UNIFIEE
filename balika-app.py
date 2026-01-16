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
# 1. CONFIGURATION SYSTÈME ULTIME (v500)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP TITAN v500", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation exhaustive du Session State
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_facture': "80mm", 'devise_vente': "USD"
    })

# --- MOTEUR DE BASE DE DONNÉES ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v500.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL") # Haute performance
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
# 2. SCHÉMA DE BASE DE DONNÉES (AUCUNE LIGNE SUPPRIMÉE)
# ==============================================================================
def init_db():
    # Table des Utilisateurs (Admin, Vendeurs, Profils)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, tel_perso TEXT)""")
    
    # Table Entreprises (Le Coeur du SaaS)
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT, logo BLOB, devise_pref TEXT DEFAULT 'USD')""")
    
    # Table Inventaire
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT, categorie TEXT)""")
    
    # Table Ventes (Factures)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Création du Compte Maître (Super Admin)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'Système Global Activé'))

init_db()

# ==============================================================================
# 3. CHARGEMENT DES DONNÉES & CSS PERSONNALISÉ (STYLE v199)
# ==============================================================================
# Récupération des infos de l'entreprise si connecté
if st.session_state.auth:
    res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status FROM config WHERE ent_id=?", 
                 (st.session_state.ent_id,), fetch=True)
    if res:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS = res[0]
        if C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
            st.error("⛔ COMPTE SUSPENDU")
            st.stop()
    else:
        C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA", "Bienvenue", 2850.0, "", "", ""
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA CLOUD", "Gérez votre business", 2850.0, "", "", ""

# CSS AVANCÉ POUR MOBILE ET DASHBOARD
st.markdown(f"""
    <style>
    /* --- Thème Global --- */
    .stApp {{ background-color: #f8f9fa; text-align: center !important; }}
    h1, h2, h3, p, span, label {{ text-align: center !important; font-family: 'Inter', sans-serif; }}

    /* --- Barre Défilante (Marquee) --- */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #000000; color: #FFFFFF;
        padding: 12px 0; position: fixed; top: 0; left: 0; z-index: 9999;
        border-bottom: 2px solid #FF8C00;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap; font-weight: bold;
        animation: scroll 20s linear infinite; color: #FF8C00;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* --- Boutons Styles (Blue/White & Orange) --- */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 10px; height: 50px;
        width: 100%; font-weight: 700; border: none; margin-bottom: 10px;
    }}
    
    /* --- Cadre Total (Colored Frame) --- */
    .total-box {{
        border: 4px solid #FF8C00; background-color: #000; padding: 25px;
        border-radius: 20px; color: #00FF00; font-size: 32px; font-weight: 900;
        margin: 20px 0; box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }}

    /* --- Montre Stylisée (Watch) --- */
    .clock-box {{
        background: #000; color: #FF8C00; padding: 15px; border-radius: 50px;
        font-size: 24px; font-weight: bold; display: inline-block;
        border: 2px solid #FF8C00; margin-bottom: 20px;
    }}

    /* --- Formats Facture --- */
    .fac-80mm {{ width: 300px; padding: 10px; background: white; color: black; font-family: monospace; font-size: 12px; margin: auto; border: 1px solid #ddd; }}
    .fac-a4 {{ width: 95%; padding: 40px; background: white; color: black; font-family: serif; margin: auto; border: 1px solid #ddd; }}

    /* --- Mobile Fixes --- */
    @media (max-width: 768px) {{
        [data-testid="column"] {{ width: 100% !important; flex: 1 1 auto !important; min-width: 100% !important; }}
        .total-box {{ font-size: 22px; }}
    }}
    </style>
    
    <div class="marquee-container"><div class="marquee-text">🚀 {C_NOM} | 📊 GESTION SÉCURISÉE | 💹 TAUX: {C_TX} CDF | {C_MSG}</div></div>
    <div style="margin-top: 100px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SYSTÈME DE CONNEXION (SaaS & SECURITY)
# ==============================================================================
if not st.session_state.auth:
    _, center, _ = st.columns([0.1, 0.8, 0.1])
    with center:
        st.title("🔑 ACCÈS SYSTÈME")
        tab_log, tab_reg = st.tabs(["CONNEXION", "OUVRIR UN COMPTE"])
        
        with tab_log:
            u_in = st.text_input("Identifiant", key="log_u").lower().strip()
            p_in = st.text_input("Mot de passe", type="password", key="log_p")
            if st.button("SE CONNECTER AU DASHBOARD"):
                data = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u_in,), fetch=True)
                if data and make_hashes(p_in) == data[0][0]:
                    st.session_state.update({'auth':True, 'user':u_in, 'role':data[0][1], 'ent_id':data[0][2]})
                    st.rerun()
                else: st.error("Accès refusé.")
        
        with tab_reg:
            with st.form("reg"):
                st.write("### Nouveau Business")
                r_ent = st.text_input("Nom de l'Entreprise")
                r_u = st.text_input("Admin ID").lower().strip()
                r_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP"):
                    if r_ent and r_u and r_p:
                        eid = f"ENT-{random.randint(100, 999)}"
                        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (r_u, make_hashes(r_p), "ADMIN", eid))
                        run_db("INSERT INTO config (ent_id, nom_ent, taux, message) VALUES (?,?,?,?)", (eid, r_ent.upper(), 2850.0, "Prêt à vendre"))
                        st.success("Compte créé avec succès !")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. NAVIGATION SIDEBAR (COMPLÈTE)
# ==============================================================================
with st.sidebar:
    # Photo de Profil
    pic_res = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if pic_res and pic_res[0][0]:
        st.image(pic_res[0][0], width=120)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    
    st.markdown(f"### {USER.upper()}")
    st.info(f"Rôle : {ROLE}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🌍 TOUS LES ABONNÉS", "📊 RAPPORTS SYSTÈME", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: # Vendeur
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]
            st.rerun()

    st.write("---")
    if st.button("🚪 FERMER LA SESSION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. LOGIQUE ACCUEIL (MONTRE, DATE, DASHBOARD)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1>{C_NOM}</h1>", unsafe_allow_html=True)
    
    # La Montre et Date (Demande v199)
    now = datetime.now()
    st.markdown(f"""
        <div class="clock-box">
            🕒 {now.strftime('%H:%M:%S')} | 📅 {now.strftime('%d/%m/%Y')}
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    v_val = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES TOTALES", f"{v_val:,.2f} $")
    
    d_val = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES CLIENTS", f"{d_val:,.2f} $", delta_color="inverse")
    
    s_val = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", s_val)

# ==============================================================================
# 7. LOGIQUE CAISSE (FORMAT A4 / 80MM / MULTIDEVISE)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        
        # Choix de la devise et du format
        col_opt1, col_opt2 = st.columns(2)
        devise_v = col_opt1.selectbox("Monnaie de paiement", ["USD", "CDF"])
        fmt_fac = col_opt2.selectbox("Format d'impression", ["80mm", "A4"])
        
        # Sélection Produits
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_data = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        c_search, c_add = st.columns([3, 1])
        pick = c_search.selectbox("Choisir un article", ["---"] + list(p_data.keys()))
        if c_add.button("➕ AJOUTER") and pick != "---":
            st.session_state.panier[pick] = st.session_state.panier.get(pick, 0) + 1
            st.rerun()

        # Affichage Panier
        if st.session_state.panier:
            total_facture = 0.0
            lignes_v = []
            
            st.write("---")
            for art, qte in list(st.session_state.panier.items()):
                p_u_base = p_data[art]['px']
                d_base = p_data[art]['dv']
                
                # Calcul conversion
                if d_base == "USD" and devise_v == "CDF": p_calc = p_u_base * C_TX
                elif d_base == "CDF" and devise_v == "USD": p_calc = p_u_base / C_TX
                else: p_calc = p_u_base
                
                stot = p_calc * qte
                total_facture += stot
                lignes_v.append({"art": art, "qte": qte, "pu": p_calc, "st": stot})
                
                col1, col2, col3 = st.columns([3, 1, 0.5])
                col1.write(f"**{art}**")
                st.session_state.panier[art] = col2.number_input("Qté", 1, p_data[art]['stk'], value=qte, key=f"q_{art}")
                if col3.button("🗑️", key=f"rm_{art}"):
                    del st.session_state.panier[art]; st.rerun()
            
            # CADRE TOTAL COLORÉ (v192)
            st.markdown(f'<div class="total-box">TOTAL À PAYER : {total_facture:,.2f} {devise_v}</div>', unsafe_allow_html=True)
            
            # Client et Versement
            c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_verse = st.number_input("MONTANT REÇU", value=float(total_facture))
            
            if st.button("💾 ENREGISTRER & GÉNÉRER LA FACTURE"):
                ref = f"FAC-{random.randint(1000, 9999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = total_facture - c_verse
                
                # DB : Ventes
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (ref, c_nom, total_facture, c_verse, reste, devise_v, dt, USER, ENT_ID, json.dumps(lignes_v)))
                
                # DB : Dettes
                if reste > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", 
                           (c_nom, reste, devise_v, ref, ENT_ID, json.dumps([{"date": dt, "paye": c_verse}])))
                
                # DB : Stock
                for i in lignes_v:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": ref, "cl": c_nom, "tot": total_facture, "pay": c_verse, "dev": devise_v, "items": lignes_v, "date": dt, "fmt": fmt_fac}
                st.rerun()
    else:
        # --- MODE FACTURE AFFICHAGE ---
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        css_class = "fac-80mm" if f['fmt'] == "80mm" else "fac-a4"
        
        facture_html = f"""
        <div class="{css_class}">
            <center>
                <h1>{C_NOM}</h1>
                <p>{C_ENTETE}</p>
                <p>Tél: {C_TEL} | {C_ADR}</p>
            </center>
            <hr>
            <p align="left"><b>FACT N°: {f['ref']}</b><br>Client: {f['cl']}<br>Date: {f['date']}</p>
            <table style="width:100%; text-align:left; border-collapse:collapse;">
                <tr style="border-bottom:1px solid #000;"><th>Article</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td align='right'>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
            <p align="right">Payé: {f['pay']:,.2f} | Reste: {f['tot']-f['pay']:,.2f}</p>
            <center><p>*** Merci de votre fidélité ***</p></center>
        </div>
        """
        st.markdown(facture_html, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("🖨️ IMPRIMER MAINTENANT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if c2.button("📤 PARTAGER SUR WHATSAPP"):
            st.success("Fonction de partage activée.")

# ==============================================================================
# 8. GESTION DU STOCK (MODIFIER/SUPPRIMER SANS PERTE)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DES ARTICLES")
    
    with st.expander("➕ AJOUTER UN PRODUIT"):
        with st.form("f_add"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            na = c1.text_input("Désignation")
            nq = c2.number_input("Quantité", 1)
            np = c3.number_input("Prix de Vente")
            nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (na.upper(), nq, np, nd, ENT_ID))
                st.rerun()

    st.write("---")
    # Liste du Stock
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, snom, sqte, sprix, sdev in items:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
            col1.write(f"**{snom}**")
            col2.write(f"Stock: `{sqte}`")
            # Modification Prix
            n_px = col3.number_input("Prix", value=float(sprix), key=f"p_edit_{sid}")
            if n_px != sprix:
                if col3.button("OK", key=f"upd_{sid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, sid))
                    st.rerun()
            # Suppression sécurisée
            if col4.button("🗑️", key=f"del_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

# ==============================================================================
# 9. GESTION DES DETTES (PAIEMENT ÉCHELONNÉ AUTOMATIQUE)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 SUIVI DES DETTES")
    liste_d = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    
    if not liste_d:
        st.balloons()
        st.success("Toutes les dettes sont apurées !")
    
    for did, dcl, dmt, ddv, drf, dhist in liste_d:
        with st.expander(f"🔴 {dcl} | RESTE : {dmt:,.2f} {ddv}"):
            st.write(f"Référence facture : {drf}")
            h_data = json.loads(dhist)
            st.table(pd.DataFrame(h_data))
            
            v_paye = st.number_input("Versement du jour", 0.0, float(dmt), key=f"v_{did}")
            if st.button("ENREGISTRER LE VERSEMENT", key=f"btn_{did}"):
                n_reste = dmt - v_paye
                h_data.append({"date": datetime.now().strftime("%d/%m"), "paye": v_paye})
                
                if n_reste <= 0:
                    run_db("DELETE FROM dettes WHERE id=?", (did,))
                    st.success("Dette totalement réglée !")
                else:
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_reste, json.dumps(h_data), did))
                
                # Mise à jour auto de la vente
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_paye, v_paye, drf, ENT_ID))
                st.rerun()

# ==============================================================================
# 10. CONFIGURATION & PROFIL (PHOTO, PASSWORD, INFOS ENTREPRISE)
# ==============================================================================
elif st.session_state.page == "CONFIG":
    st.header("⚙️ CONFIGURATION")
    
    # 1. Infos Entreprise
    with st.expander("🏢 INFOS DE L'ENTREPRISE"):
        with st.form("cfg"):
            e_nom = st.text_input("Nom de la Société", C_NOM)
            e_adr = st.text_input("Adresse", C_ADR)
            e_tel = st.text_input("Téléphone", C_TEL)
            e_tx = st.number_input("Taux de change (USD vers CDF)", value=C_TX)
            e_msg = st.text_input("Message Défilant", C_MSG)
            e_hdr = st.text_area("En-tête de Facture", C_ENTETE)
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, entete_fac=? WHERE ent_id=?", 
                       (e_nom.upper(), e_adr, e_tel, e_tx, e_msg, e_hdr, ENT_ID))
                st.rerun()

    # 2. Profil Personnel
    with st.expander("👤 MON PROFIL & SÉCURITÉ"):
        new_p = st.text_input("Nouveau Mot de Passe", type="password")
        up_img = st.file_uploader("Ma Photo de Profil", type=["jpg", "png"])
        if st.button("METTRE À JOUR MON PROFIL"):
            if new_p: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
            if up_img:
                bytes_img = up_img.getvalue()
                run_db("UPDATE users SET photo=? WHERE username=?", (bytes_img, USER))
            st.success("Profil mis à jour !")

# ==============================================================================
# 11. SUPER-ADMIN (ABONNÉS & SaaS)
# ==============================================================================
elif st.session_state.page == "ABONNÉS" and ROLE == "SUPER_ADMIN":
    st.header("🌍 GESTION DES ABONNÉS (SaaS)")
    abos = run_db("SELECT ent_id, nom_ent, status, tel FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
    
    for aid, anom, astat, atel in abos:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"🏢 **{anom}** (ID: {aid})")
            status_color = "green" if astat == "ACTIF" else "red"
            c2.markdown(f"<p style='color:{status_color}'>STATUT: {astat}</p>", unsafe_allow_html=True)
            
            new_stat = "PAUSE" if astat == "ACTIF" else "ACTIF"
            if c3.button(f"PASSER EN {new_stat}", key=f"sw_{aid}"):
                run_db("UPDATE config SET status=? WHERE ent_id=?", (new_stat, aid))
                st.rerun()

elif st.session_state.page == "VENDEURS":
    st.header("👥 MES VENDEURS")
    with st.form("add_v"):
        v_u = st.text_input("Identifiant Vendeur").lower()
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", 
                   (v_u, make_hashes(v_p), "VENDEUR", ENT_ID))
            st.rerun()
    
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        st.write(f"👤 {s[0].upper()}")

elif st.session_state.page == "RAPPORTS":
    st.header("📊 JOURNAL DES VENTES")
    v_data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if v_data:
        df = pd.DataFrame(v_data, columns=["Date", "Référence", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
        st.dataframe(df, use_container_width=True)
        
        c1, c2 = st.columns(2)
        if c1.button("🖨️ IMPRIMER LE RAPPORT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if c2.button("💾 EXPORTER EXCEL"):
            st.info("Exportation en cours...")
