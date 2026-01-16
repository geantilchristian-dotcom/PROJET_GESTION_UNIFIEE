import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io

# ==============================================================================
# 1. CONFIGURATION ET DESIGN (CENTRAGE TOTAL & LISIBILITÉ)
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP v1000", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du Session State pour éviter les pertes de données
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM", 
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None, 'format_fac': "80mm"
    })

# --- MOTEUR DE BASE DE DONNÉES ---
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v1000.db', timeout=60) as conn:
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
# 2. SCHÉMA DE BASE DE DONNÉES (SANS SUPPRESSION DE LIGNES)
# ==============================================================================
def init_db():
    # Table des utilisateurs (Admin, Vendeurs)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                ent_id TEXT, photo BLOB, full_name TEXT, telephone TEXT)""")
    
    # Configuration de l'entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, 
                tel TEXT, taux REAL, message TEXT, color_m TEXT DEFAULT '#FFFF00', 
                status TEXT DEFAULT 'ACTIF', date_inscription TEXT, montant_paye REAL DEFAULT 0.0)""")
    
    # Gestion du Stock
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
                stock_actuel INTEGER, prix_vente REAL, devise TEXT, 
                ent_id TEXT)""")
    
    # Journal des Ventes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
                total REAL, paye REAL, reste REAL, devise TEXT, 
                date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)""")
    
    # Gestion des Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Journal des Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, 
                devise TEXT, date_d TEXT, ent_id TEXT)""")

    # Création du compte Maître si inexistant
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM'))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message, color_m, date_inscription) VALUES (?, ?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP HQ', 'ACTIF', 2850.0, 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION', '#FFFF00', '16/01/2026'))

init_db()

# ==============================================================================
# 3. CSS PERSONNALISÉ (DOUCEUR VISUELLE & CENTRAGE)
# ==============================================================================
curr_eid = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
res_cfg = run_db("SELECT nom_ent, message, color_m, taux, adresse, tel, status FROM config WHERE ent_id=?", (curr_eid,), fetch=True)

if res_cfg:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_STATUS = res_cfg[0]
else:
    C_NOM, C_MSG, C_COLOR, C_TX, C_ADR, C_TEL, C_STATUS = ("BALIKA", "Bienvenue", "#FFFF00", 2850.0, "", "", "ACTIF")

st.markdown(f"""
    <style>
    /* Global Styles */
    .stApp {{ background-color: #fdfdfd; text-align: center !important; }}
    h1, h2, h3, h4, p, span, label, div {{ text-align: center !important; font-family: 'Helvetica Neue', sans-serif; }}
    
    /* Marquee (Message Défilant) */
    .marquee-container {{
        position: fixed; top: 0; left: 0; width: 100%;
        background: #000; color: {C_COLOR}; height: 40px;
        z-index: 1000; display: flex; align-items: center; 
        border-bottom: 2px solid #FF8C00; overflow: hidden;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: scroll-fast 20s linear infinite;
        font-weight: bold; font-size: 18px;
    }}
    @keyframes scroll-fast {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Montre 80mm Centrée */
    .watch-v1000 {{
        background: radial-gradient(circle, #222 0%, #000 100%);
        color: #FF8C00; padding: 35px; border-radius: 25px;
        border: 4px solid #FF8C00; display: inline-block; margin: 30px auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}
    .w-time {{ font-size: 60px; font-weight: 900; margin: 0; letter-spacing: 2px; }}
    .w-date {{ font-size: 20px; color: #fff; text-transform: uppercase; }}

    /* Boutons Bleus Texte Blanc */
    .stButton>button {{
        background: linear-gradient(to bottom, #007bff, #0056b3) !important;
        color: white !important; border-radius: 10px; height: 50px;
        font-weight: bold; border: none; width: 100%; font-size: 16px;
    }}

    /* Cadre de Prix */
    .price-frame {{
        border: 4px solid #FF8C00; background: #fff; padding: 20px;
        border-radius: 20px; color: #000; font-size: 35px;
        font-weight: 900; margin: 20px auto; width: 80%;
    }}

    /* Factures A4 / 80mm */
    .f-80 {{ width: 300px; margin: auto; padding: 10px; border: 1px dashed #000; background: #fff; text-align: left !important; font-family: monospace; }}
    .f-a4 {{ width: 90%; max-width: 800px; margin: auto; padding: 40px; border: 1px solid #ddd; background: #fff; text-align: left !important; }}
    .f-header {{ text-align: center !important; }}
    .sig-box {{ display: flex; justify-content: space-between; margin-top: 50px; border-top: 1px solid #000; padding-top: 10px; }}

    /* Tableaux */
    .table-clean {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }}
    .table-clean th {{ background: #007bff; color: white; padding: 12px; }}
    .table-clean td {{ padding: 10px; border-bottom: 1px solid #eee; }}

    @media print {{ .marquee-container, .stSidebar, .stButton, .no-print {{ display: none !important; }} }}
    </style>

    <div class="marquee-container"><div class="marquee-text">{C_MSG}</div></div>
    <div style="margin-top: 60px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIQUE D'AUTHENTIFICATION
# ==============================================================================
if not st.session_state.auth:
    _, col_log, _ = st.columns([0.2, 0.6, 0.2])
    with col_log:
        st.title("🛡️ BALIKA ERP LOGIN")
        l_u = st.text_input("Identifiant").lower().strip()
        l_p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU SYSTÈME"):
            u_info = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (l_u,), fetch=True)
            if u_info and make_hashes(l_p) == u_info[0][0]:
                st.session_state.update({'auth':True, 'user':l_u, 'role':u_info[0][1], 'ent_id':u_info[0][2]})
                st.rerun()
            else: st.error("Identifiants incorrects.")
        
        st.write("---")
        with st.expander("📝 CRÉER UN NOUVEL ERP"):
            with st.form("reg_erp"):
                r_en = st.text_input("Nom de l'Entreprise")
                r_un = st.text_input("Admin Username")
                r_pw = st.text_input("Admin Password", type="password")
                if st.form_submit_button("LANCER MON ERP"):
                    if r_en and r_un and r_pw:
                        eid = f"ERP-{random.randint(100, 999)}"
                        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (r_un, make_hashes(r_pw), 'ADMIN', eid))
                        run_db("INSERT INTO config (ent_id, nom_ent, message, date_inscription) VALUES (?,?,?,?)", (eid, r_en.upper(), 'BIENVENUE', datetime.now().strftime("%d/%m/%Y")))
                        st.success("✅ Compte créé !")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. MENU LATÉRAL (DYNAMIQUE PAR RÔLE)
# ==============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {USER.upper()}")
    st.write(f"Rôle : {ROLE}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        pages = ["🏠 ACCUEIL", "🌍 ABONNÉS", "📊 RAPPORTS HQ", "⚙️ RÉGLAGES ADMIN", "👤 MON PROFIL"]
    elif ROLE == "ADMIN":
        pages = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "💸 DÉPENSES", "📊 RAPPORTS", "⚙️ RÉGLAGES", "👤 MON PROFIL"]
    else: # Vendeur
        pages = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]

    for p in pages:
        if st.button(p, use_container_width=True):
            st.session_state.page = p.split()[-1]
            st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 6. ACCUEIL (MONTRE & RÉSUMÉ)
# ==============================================================================
if st.session_state.page == "ACCUEIL":
    st.title(f"BIENVENUE CHEZ {C_NOM}")
    st.markdown(f"""
        <center>
            <div class="watch-v1000">
                <p class="w-time">{datetime.now().strftime('%H:%M:%S')}</p>
                <p class="w-date">{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    v_total = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c1.metric("VENTES TOTALES", f"{v_total:,.2f} $")
    d_total = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c2.metric("DETTES CLIENTS", f"{d_total:,.2f} $")
    s_total = run_db("SELECT COUNT(*) FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    c3.metric("ARTICLES EN STOCK", s_total)

# ==============================================================================
# 7. CAISSE (FORMATS D'IMPRESSION A4/80MM)
# ==============================================================================
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        col_dev, col_fmt = st.columns(2)
        v_devise = col_dev.selectbox("Devise de paiement", ["USD", "CDF"])
        st.session_state.format_fac = col_fmt.selectbox("Format d'impression", ["80mm", "A4"])
        
        # Liste produits
        plist = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_data = {r[0]: {'px': r[1], 'st': r[2], 'dv': r[3]} for r in plist}
        
        ca, cb = st.columns([3, 1])
        art_sel = ca.selectbox("Choisir un article", ["---"] + list(p_data.keys()))
        if cb.button("➕ AJOUTER") and art_sel != "---":
            st.session_state.panier[art_sel] = st.session_state.panier.get(art_sel, 0) + 1
            st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_v = 0.0; lines = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_data[art]['px']; db = p_data[art]['dv']
                # Conversion dynamique
                px_final = pb * C_TX if db=="USD" and v_devise=="CDF" else pb / C_TX if db=="CDF" and v_devise=="USD" else pb
                stot = px_final * qte
                total_v += stot
                lines.append({'art':art, 'qte':qte, 'pu':px_final, 'st':stot})
                
                c_1, c_2, c_3 = st.columns([3, 1, 0.5])
                c_1.write(f"**{art}**")
                st.session_state.panier[art] = c_2.number_input("Qté", 1, p_data[art]['st'], value=qte, key=f"q_{art}")
                if c_3.button("🗑️", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()

            st.markdown(f'<center><div class="price-frame">À PAYER : {total_v:,.2f} {v_devise}</div></center>', unsafe_allow_html=True)
            cl_n = st.text_input("CLIENT", "COMPTANT").upper()
            cl_v = st.number_input("MONTANT REÇU", value=float(total_v))
            
            if st.button("💾 VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(10000, 99999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = total_v - cl_v
                run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details) VALUES (?,?,?,?,?,?,?,?,?,?)", (ref, cl_n, total_v, cl_v, reste, v_devise, dt, USER, ENT_ID, json.dumps(lines)))
                if reste > 0.1:
                    run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id, historique) VALUES (?,?,?,?,?,?)", (cl_n, reste, v_devise, ref, ENT_ID, json.dumps([{'d':dt, 'p':cl_v}])))
                for l in lines:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (l['qte'], l['art'], ENT_ID))
                st.session_state.last_fac = {'ref':ref, 'cl':cl_n, 'tot':total_v, 'pay':cl_v, 'dev':v_devise, 'items':lines, 'date':dt}
                st.rerun()
    else:
        # Affichage Facture
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({'last_fac':None}))
        cl_facture = "f-80" if st.session_state.format_fac == "80mm" else "f-a4"
        
        html = f"""
        <div class="{cl_facture}">
            <div class="f-header">
                <h2>{C_NOM}</h2>
                <p>{C_ADR}<br>Tél: {C_TEL}</p>
                <hr>
                <p><b>FACTURE : {f['ref']}</b><br>Date: {f['date']}<br>Client: {f['cl']}</p>
            </div>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #000;"><th>Art</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Payé : {f['pay']:,.2f}<br>Reste : {f['tot']-f['pay']:,.2f}</p>
            <div class="sig-box">
                <div>Signature Maison</div>
                <div>Signature Client</div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        c_p1, c_p2 = st.columns(2)
        c_p1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        wa_m = f"Facture {f['ref']} chez {C_NOM}. Total: {f['tot']} {f['dev']}."
        c_p2.markdown(f'<a href="https://wa.me/?text={wa_m}" target="_blank"><button style="width:100%; background:#25D366; color:white; height:48px; border-radius:10px; border:none; font-weight:bold;">📲 PARTAGER WHATSAPP</button></a>', unsafe_allow_html=True)

# ==============================================================================
# 8. GESTION DES VENDEURS (CRÉATION ET MODIFICATION)
# ==============================================================================
elif st.session_state.page == "VENDEURS":
    st.header("👥 GESTION DU PERSONNEL")
    
    with st.expander("➕ CRÉER UN COMPTE VENDEUR"):
        with st.form("new_vendeur"):
            v_u = st.text_input("Identifiant Vendeur (Username)").lower().strip()
            v_p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("VALIDER"):
                if not run_db("SELECT * FROM users WHERE username=?", (v_u,), fetch=True):
                    run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (v_u, make_hashes(v_p), "VENDEUR", ENT_ID))
                    st.success("✅ Vendeur ajouté !")
                    st.rerun()
                else: st.error("❌ Ce nom d'utilisateur est déjà utilisé.")

    st.write("---")
    st.subheader("LISTE DES VENDEURS ACTIFS")
    v_list = run_db("SELECT username, full_name, telephone FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    
    if not v_list:
        st.info("Aucun vendeur pour le moment.")
    else:
        for v_name, v_full, v_tel in v_list:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"Vendeur : **{v_name.upper()}**")
                v_new_pw = col2.text_input("Changer Pass", type="password", key=f"pw_{v_name}")
                if col2.button("💾 SAUVER", key=f"btn_{v_name}"):
                    if v_new_pw:
                        run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(v_new_pw), v_name))
                        st.success("Mot de passe mis à jour !")
                    else: st.warning("Entrez un mot de passe.")
                if col3.button("🗑️ SUPPRIMER", key=f"del_{v_name}"):
                    run_db("DELETE FROM users WHERE username=?", (v_name,))
                    st.rerun()

# ==============================================================================
# 9. RAPPORTS (CASH, DETTES, DÉPENSES)
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.header("📊 ANALYSE FINANCIÈRE")
    
    cash = run_db("SELECT SUM(paye) FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    dette_cl = run_db("SELECT SUM(montant) FROM dettes WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    depense = run_db("SELECT SUM(montant) FROM depenses WHERE ent_id=?", (ENT_ID,), fetch=True)[0][0] or 0
    net = cash - depense
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("CASH TOTAL", f"{cash:,.2f} $")
    r2.metric("DETTES CLIENTS", f"{dette_cl:,.2f} $")
    r3.metric("DÉPENSES", f"{depense:,.2f} $")
    r4.metric("FONDS DISPOS (Net)", f"{net:,.2f} $")
    
    st.write("---")
    st.subheader("Historique des Ventes")
    data = run_db("SELECT date_v, ref, client, total, paye, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Référence", "Client", "Total", "Payé", "Vendeur"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER LE JOURNAL"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ==============================================================================
# 10. DÉPENSES
# ==============================================================================
elif st.session_state.page == "DÉPENSES":
    st.header("💸 SORTIES DE CAISSE")
    with st.form("f_dep"):
        motif = st.text_input("Motif de la dépense")
        montant = st.number_input("Montant ($)", 0.0)
        if st.form_submit_button("ENREGISTRER"):
            if motif and montant > 0:
                dt = datetime.now().strftime("%d/%m/%Y")
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)", (motif, montant, "USD", dt, ENT_ID))
                st.success("Dépense enregistrée !")
                st.rerun()

    d_list = run_db("SELECT date_d, motif, montant FROM depenses WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if d_list:
        st.table(pd.DataFrame(d_list, columns=["Date", "Motif", "Montant ($)"]))

# ==============================================================================
# 11. RÉGLAGES ADMIN (MARQUEE & COULEUR)
# ==============================================================================
elif st.session_state.page == "ADMIN" and ROLE == "SUPER_ADMIN":
    st.header("⚙️ RÉGLAGES MAÎTRE BALIKA")
    with st.form("set_hq"):
        msg_h = st.text_area("Message Défilant Global", C_MSG)
        clr_h = st.color_picker("Couleur du Message", C_COLOR)
        if st.form_submit_button("METTRE À JOUR"):
            run_db("UPDATE config SET message=?, color_m=? WHERE ent_id='SYSTEM'", (msg_h, clr_h))
            st.rerun()

elif st.session_state.page == "RÉGLAGES" and ROLE == "ADMIN":
    st.header("⚙️ RÉGLAGES DE LA BOUTIQUE")
    with st.form("set_cl"):
        c_n = st.text_input("Nom Entreprise", C_NOM)
        c_a = st.text_input("Adresse", C_ADR)
        c_t = st.text_input("WhatsApp", C_TEL)
        c_x = st.number_input("Taux de change (CDF pour 1$)", value=C_TX)
        if st.form_submit_button("SAUVEGARDER LES INFOS"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=? WHERE ent_id=?", (c_n.upper(), c_a, c_t, c_x, ENT_ID))
            st.rerun()

# ==============================================================================
# 12. STOCK, DETTES & PROFIL (COMPLETS)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DES ARTICLES")
    with st.expander("➕ AJOUTER UN PRODUIT"):
        with st.form("add_p"):
            n_p = st.text_input("Désignation")
            n_q = st.number_input("Quantité", 1)
            n_v = st.number_input("Prix de Vente", 0.0)
            n_d = st.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("VALIDER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (n_p.upper(), n_q, n_v, n_d, ENT_ID))
                st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for sid, sn, sq, sp, sd in prods:
        with st.container(border=True):
            cl1, cl2, cl3, cl4 = st.columns([3, 1, 1, 0.5])
            cl1.write(f"**{sn}**")
            cl2.write(f"Stock : {sq}")
            px_mod = cl3.number_input("Prix", value=float(sp), key=f"px_{sid}")
            if cl3.button("💾", key=f"s_{sid}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (px_mod, sid))
                st.rerun()
            if cl4.button("🗑️", key=f"d_{sid}"):
                run_db("DELETE FROM produits WHERE id=?", (sid,))
                st.rerun()

elif st.session_state.page == "DETTES":
    st.header("📉 GESTION DES DETTES")
    d_rows = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0.1", (ENT_ID,), fetch=True)
    for did, dcl, dmt, ddv, drf, dhi in d_rows:
        with st.expander(f"🔴 {dcl} | {dmt:,.2f} {ddv}"):
            v_pay = st.number_input("Acompte versé", 0.0, float(dmt), key=f"pay_{did}")
            if st.button("ENREGISTRER LE PAIEMENT", key=f"btn_p_{did}"):
                new_mt = dmt - v_pay
                hist = json.loads(dhi)
                hist.append({'d': datetime.now().strftime("%d/%m"), 'p': v_pay})
                run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (new_mt, json.dumps(hist), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (v_pay, v_pay, drf, ENT_ID))
                if new_mt <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (did,))
                st.rerun()

elif st.session_state.page == "PROFIL":
    st.header("👤 MON PROFIL")
    with st.form("f_prof"):
        new_u = st.text_input("Identifiant", USER)
        new_p = st.text_input("Changer Mot de passe", type="password")
        up_img = st.file_uploader("Photo de profil", type=["jpg", "png"])
        if st.form_submit_button("SAUVEGARDER"):
            if new_p: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), USER))
            if up_img: run_db("UPDATE users SET photo=? WHERE username=?", (up_img.getvalue(), USER))
            if new_u != USER:
                run_db("UPDATE users SET username=? WHERE username=?", (new_u, USER))
                st.session_state.user = new_u
            st.success("Profil mis à jour !"); st.rerun()
