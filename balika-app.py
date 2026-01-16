import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io
from PIL import Image

# ==============================================================================
# 1. CONFIGURATION CORE & STYLE
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP ULTIMATE v380", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation du State (Mémoire de session)
states = {
    'auth': False, 'user': "", 'role': "", 'ent_id': "", 
    'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
    'msg_success': ""
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

# Fonction de communication Base de données
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_cloud_v380.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur Système : {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES & MIGRATIONS
# ==============================================================================
def init_db():
    # Table Utilisateurs (Ajout Profil Image)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
                photo BLOB DEFAULT NULL)""")
    
    # Table Configuration Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, 
                taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', 
                entete_fac TEXT DEFAULT '', logo BLOB DEFAULT NULL)""")
    
    # Table Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, 
                prix_vente REAL, devise TEXT, ent_id TEXT)""")
    
    # Table Ventes & Dettes
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, 
                paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, 
                ent_id TEXT, details TEXT)""")
    
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, 
                devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)""")

    # Création du compte Maître si inexistant
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'SUPER_ADMIN', 'SYSTEM')", 
               (make_hashes("admin123"),))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES ('SYSTEM', 'BALIKA ERP', 'ACTIF', 2850, 'Bienvenue')")

init_db()

# ==============================================================================
# 3. MOTEUR DE DESIGN (CENTRE & MOBILE FRIENDLY)
# ==============================================================================
# Récupération des réglages en temps réel
if st.session_state.auth:
    res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, logo FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_LOGO = res[0] if res else ("BALIKA", "Prêt", 2850, "", "", "", None)
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_LOGO = "BALIKA CLOUD", "Gérez votre business", 2850, "", "", "", None

st.markdown(f"""
    <style>
    /* Centrage de tout le contenu */
    .stApp {{ text-align: center !important; }}
    .stMarkdown, p, h1, h2, h3, label, div[data-testid="stBlock"] {{ text-align: center !important; }}
    
    /* Style Bouton Harmonisé */
    .stButton>button {{
        background: linear-gradient(135deg, #0047AB, #00BFFF) !important;
        color: white !important; border-radius: 15px; height: 55px;
        font-weight: bold; width: 100%; border: none; margin: 10px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}

    /* Cadre Prix Panier */
    .total-frame {{
        border: 4px solid #0047AB; background: #E3F2FD; padding: 20px;
        border-radius: 20px; font-size: 32px; color: #0047AB;
        font-weight: 900; margin: 20px auto; width: 85%;
    }}

    /* Barre défilante top */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #0047AB; color: white;
        padding: 12px 0; position: fixed; top: 0; left: 0; z-index: 1000;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: marquee 25s linear infinite; font-size: 18px; font-weight: bold;
    }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Facture pro */
    .table-fac {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    .table-fac th, .table-fac td {{ border: 1px solid #000; padding: 10px; text-align: center; }}
    
    /* Responsive phone */
    @media (max-width: 640px) {{
        .total-frame {{ font-size: 22px; width: 95%; }}
        h1 {{ font-size: 24px !important; }}
    }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🏢 {C_NOM} | 💹 TAUX DU JOUR : 1 USD = {C_TX} CDF | {C_MSG}</div></div>
    <div style="margin-top: 100px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. MODULE AUTHENTIFICATION (PROFIL PHOTO)
# ==============================================================================
if not st.session_state.auth:
    _, center, _ = st.columns([0.1, 0.8, 0.1])
    with center:
        st.markdown('<div style="padding:30px; border:2px solid #0047AB; border-radius:30px; background:white;">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/9131/9131529.png", width=100)
        st.title("CONNEXION CLOUD")
        
        tab_in, tab_up = st.tabs(["🔐 SE CONNECTER", "🏢 CRÉER BUSINESS"])
        
        with tab_in:
            with st.form("login"):
                u = st.text_input("Identifiant").lower().strip()
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACCÉDER AU TABLEAU DE BORD"):
                    res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
                    if res and make_hashes(p) == res[0][0]:
                        st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                        st.rerun()
                    else: st.error("Accès refusé.")
        
        with tab_up:
            with st.form("register"):
                new_ent = st.text_input("Nom de votre Entreprise").upper().strip()
                new_u = st.text_input("Identifiant Administrateur").lower().strip()
                new_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON COMPTE CLOUD"):
                    if new_ent and new_u and new_p:
                        exist = run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True)
                        if not exist:
                            eid = f"B-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'ADMIN', ?)", (new_u, make_hashes(new_p), eid))
                            run_db("INSERT INTO config (ent_id, nom_ent, status, taux) VALUES (?, ?, 'ACTIF', 2850)", (eid, new_ent))
                            st.success("Compte créé avec succès ! Connectez-vous.")
                        else: st.error("Cet identifiant existe déjà.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. BARRE DE NAVIGATION (MOBILE READY)
# ==============================================================================
with st.sidebar:
    # Photo de profil
    u_data = run_db("SELECT photo FROM users WHERE username=?", (USER,), fetch=True)
    if u_data and u_data[0][0]:
        st.image(u_data[0][0], width=100)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    
    st.markdown(f"### {USER.upper()}")
    st.markdown(f"**Rôle:** {ROLE}")
    st.write("---")
    
    if ROLE == "SUPER_ADMIN":
        menu = ["🌍 ABONNÉS", "📊 SYSTÈME", "⚙️ MON COMPTE"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: # Vendeur
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]; st.rerun()
    
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. LOGIQUE : CAISSE & VENTES (MULTIDEVISE)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 TERMINAL DE VENTE")
        
        # Choix monnaie vente
        cur = st.radio("Vendre en :", ["USD", "CDF"], horizontal=True)
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        col_a, col_b = st.columns([3, 1])
        choix = col_a.selectbox("Sélectionner l'article", ["---"] + list(p_dict.keys()))
        if col_b.button("➕ AJOUTER"):
            if choix != "---":
                st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1; st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_net = 0.0; items_list = []
            
            for art, qte in list(st.session_state.panier.items()):
                # Conversion dynamique basée sur le taux
                p_u_orig = p_dict[art]['px']
                d_orig = p_dict[art]['dv']
                
                # Conversion vers la devise de vente choisie
                if d_orig == "USD" and cur == "CDF": p_u_conv = p_u_orig * C_TX
                elif d_orig == "CDF" and cur == "USD": p_u_conv = p_u_orig / C_TX
                else: p_u_conv = p_u_orig
                
                stot = p_u_conv * qte
                total_net += stot
                items_list.append({"art": art, "qte": qte, "pu": p_u_conv, "st": stot})
                
                c1, c2, c3, c4 = st.columns([3, 1, 1, 0.5])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_dict[art]['stk'], value=qte, key=f"q_{art}")
                c3.write(f"{stot:,.0f} {cur}")
                if c4.button("❌", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-frame">NET À PAYER : {total_net:,.2f} {cur}</div>', unsafe_allow_html=True)
            
            with st.container(border=True):
                c_nom = st.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
                c_paye = st.number_input(f"MONTANT REÇU ({cur})", value=float(total_net))
                reste = total_net - c_paye
                
                if reste > 0:
                    st.warning(f"Dette générée : {reste:,.2f} {cur}")
                
                if st.button("✅ CONFIRMER ET IMPRIMER"):
                    v_ref = f"FAC-{random.randint(1000, 9999)}"
                    v_dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    # Sauvegarde vente
                    run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                           (v_ref, c_nom, total_net, c_paye, reste, cur, v_dt, USER, ENT_ID, json.dumps(items_list)))
                    # Gestion Dette
                    if reste > 0:
                        run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", 
                               (c_nom, reste, cur, v_ref, ENT_ID, json.dumps([{"date": v_dt, "paye": c_paye}])))
                    # Mise à jour Stock
                    for i in items_list:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                    
                    st.session_state.last_fac = {"ref": v_ref, "cl": c_nom, "tot": total_net, "pay": c_paye, "dev": cur, "items": items_list, "date": v_dt}
                    st.session_state.panier = {}; st.rerun()
    else:
        # FACTURE (MODE IMPRESSION)
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        fmt = st.radio("Format :", ["Format 80mm", "Format A4"], horizontal=True)
        w = "320px" if "80mm" in fmt else "100%"
        
        html_fac = f"""
        <div style="background:white; color:black; padding:20px; border:1px solid #000; width:{w}; margin:auto; font-family: 'Courier New', Courier, monospace;">
            <h1 style="margin:0;">{C_NOM}</h1>
            <p>{C_ENTETE}</p>
            <p>{C_ADR}<br>Tel: {C_TEL}</p>
            <hr>
            <table style="width:100%; font-size:14px;">
                <tr><td>RECU N°: {f['ref']}</td><td align="right">{f['date']}</td></tr>
                <tr><td>CLIENT: {f['cl']}</td><td align="right">VDR: {USER}</td></tr>
            </table>
            <table class="table-fac">
                <tr style="background:#eee;"><th>Designation</th><th>Qty</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <h2 align="right">TOTAL : {f['tot']:,.2f} {f['dev']}</h2>
            <p align="right">Payé: {f['pay']} | Reste: {f['tot']-f['pay']}</p>
            <hr>
            <div style="margin-top:20px; display:flex; justify-content: space-around;">
                <div style="font-size:10px;">Signature Client</div>
                <div style="border:1px solid black; padding:10px; font-weight:bold;">SCEAU & CACHET</div>
            </div>
            <p style="font-size:10px; margin-top:10px;">Logiciel BALIKA ERP - Cloud v380</p>
        </div>
        """
        st.markdown(html_fac, unsafe_allow_html=True)
        st.button("🖨️ LANCER L'IMPRESSION", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# ==============================================================================
# 7. LOGIQUE : DETTES (PAIEMENT PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 SUIVI DES DETTES CLIENTS")
    dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    
    if not dettes:
        st.success("Félicitations ! Aucune dette en cours.")
    
    for did, dcl, dmt, ddv, drf, dhi in dettes:
        with st.expander(f"🔴 CLIENT: {dcl} | RESTE: {dmt:,.2f} {ddv}"):
            st.write(f"Référence Vente : {drf}")
            h_list = json.loads(dhi)
            st.write("**Historique des paiements :**")
            for h in h_list: st.write(f"- {h['date']} : {h['paye']:,.2f} {ddv}")
            
            v_verse = st.number_input(f"Nouveau Versement ({ddv})", 0.0, float(dmt), key=f"tranche_{did}")
            if st.button("ENREGISTRER LE VERSEMENT", key=f"btn_{did}"):
                new_reste = dmt - v_verse
                h_list.append({"date": datetime.now().strftime("%d/%m/%Y"), "paye": v_verse})
                
                if new_reste <= 0.01: # Si dette finie
                    run_db("DELETE FROM dettes WHERE id=?", (did,))
                    st.toast(f"Dette de {dcl} soldée !")
                else:
                    run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (new_reste, json.dumps(h_list), did))
                st.rerun()

# ==============================================================================
# 8. LOGIQUE : STOCK (MODIFIER PRIX / SUPPRIMER)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 GESTION DES STOCKS")
    
    with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
        with st.form("new_p"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            n_a = c1.text_input("Désignation")
            n_q = c2.number_input("Quantité Initiale", 1)
            n_p = c3.number_input("Prix de Vente")
            n_d = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER L'ARTICLE"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (n_a.upper(), n_q, n_p, n_d, ENT_ID)); st.rerun()

    st.write("---")
    # Liste avec modification et suppression
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    
    for pid, pnom, pstk, ppx, pdv in items:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"**{pnom}**")
            col2.write(f"Stock: {pstk}")
            
            # Modification de prix directe
            n_px = col3.number_input("Prix", value=float(ppx), key=f"px_{pid}")
            if n_px != ppx:
                if col3.button("💾", key=f"save_{pid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, pid)); st.rerun()
            
            # Suppression
            if col4.button("🗑️", key=f"del_{pid}"):
                run_db("DELETE FROM produits WHERE id=?", (pid,)); st.rerun()

# ==============================================================================
# 9. LOGIQUE : VENDEURS & COMPTES
# ==============================================================================
elif st.session_state.page == "VENDEURS":
    st.header("👥 COMPTES VENDEURS")
    with st.form("v_add"):
        v_u = st.text_input("Identifiant Vendeur").lower().strip()
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,'VENDEUR',?)", 
                   (v_u, make_hashes(v_p), ENT_ID)); st.rerun()
    
    st.write("---")
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        c1, c2 = st.columns([4, 1])
        c1.write(f"👤 **{s[0]}**")
        if c2.button("Supprimer", key=f"ds_{s[0]}"):
            run_db("DELETE FROM users WHERE username=?", (s[0],)); st.rerun()

# ==============================================================================
# 10. LOGIQUE : CONFIGURATION & PROFIL (PHOTO, PASSWORD)
# ==============================================================================
elif st.session_state.page == "CONFIG" or st.session_state.page == "COMPTE":
    st.header("⚙️ RÉGLAGES & PROFIL")
    
    tab_p, tab_e = st.tabs(["👤 MON PROFIL", "🏢 ENTREPRISE"])
    
    with tab_p:
        st.subheader("Modifier mes accès")
        with st.form("prof"):
            new_uid = st.text_input("Nouvel Identifiant", USER)
            new_pass = st.text_input("Nouveau Mot de passe (Laissez vide pour garder)", type="password")
            up_photo = st.file_uploader("Photo de profil", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("METTRE À JOUR MON PROFIL"):
                photo_bytes = up_photo.read() if up_photo else None
                if new_pass:
                    run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_uid, make_hashes(new_pass), USER))
                if photo_bytes:
                    run_db("UPDATE users SET photo=? WHERE username=?", (photo_bytes, USER))
                
                run_db("UPDATE users SET username=? WHERE username=?", (new_uid, USER))
                st.session_state.user = new_uid
                st.success("Profil mis à jour !"); st.rerun()

    with tab_e:
        if ROLE == "ADMIN":
            with st.form("ent_cfg"):
                c_n = st.text_input("Nom Business", C_NOM)
                c_a = st.text_input("Adresse", C_ADR)
                c_t = st.text_input("Téléphone", C_TEL)
                c_tx = st.number_input("Taux de change (1 USD en CDF)", value=float(C_TX))
                c_et = st.text_area("En-tête de Facture (RCCM, Id Nat, etc.)", C_ENTETE)
                c_ms = st.text_input("Message Défilant", C_MSG)
                if st.form_submit_button("SAUVEGARDER LES INFOS BUSINESS"):
                    run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=?, entete_fac=? WHERE ent_id=?", 
                           (c_n.upper(), c_a, c_t, c_tx, c_ms, c_et, ENT_ID)); st.rerun()

# ==============================================================================
# 11. RAPPORTS & ACCUEIL
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.header("📊 JOURNAL DES ACTIVITÉS")
    vnts = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if vnts:
        df = pd.DataFrame(vnts, columns=["Date", "Référence", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
        st.dataframe(df, use_container_width=True)
        
        # Statistiques rapides
        tot_usd = df[df['Devise']=='USD']['Total'].sum()
        tot_cdf = df[df['Devise']=='CDF']['Total'].sum()
        st.info(f"CA Total : **{tot_usd:,.2f} USD** et **{tot_cdf:,.0f} CDF**")
        
        if st.button("🖨️ IMPRIMER LE RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

elif st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1>{C_NOM}</h1>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/2855/2855160.png", width=150)
    st.subheader(f"Bienvenue, {USER.upper()}")
    st.write(f"Nous sommes le {datetime.now().strftime('%d/%m/%Y')}")
    st.write(f"Taux actuel : **1 USD = {C_TX} CDF**")
