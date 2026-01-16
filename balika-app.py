import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import base64

# ==============================================================================
# 1. CONFIGURATION SYSTÈME & CORE ENGINE
# ==============================================================================
st.set_page_config(
    page_title="BALIKA ERP CLOUD v310", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialisation rigoureuse du State
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'ent_id' not in st.session_state: st.session_state.ent_id = ""
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'panier' not in st.session_state: st.session_state.panier = {}
if 'last_fac' not in st.session_state: st.session_state.last_fac = None

# Moteur de Base de Données sécurisé
def run_db(query, params=(), fetch=False):
    try:
        # Utilisation d'un fichier master unique pour le SaaS
        with sqlite3.connect('balika_master_cloud.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL") # Optimisation pour accès simultanés
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Critique Base de Données : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. ARCHITECTURE DES TABLES (SCHÉMA COMPLET)
# ==============================================================================
def init_db():
    # Table des utilisateurs (Propriétaires, Vendeurs, Super-Admin)
    run_db("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                role TEXT, 
                ent_id TEXT)""")
    
    # Table des Produits (Inventaire cloisonné par ent_id)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                designation TEXT, 
                stock_actuel INTEGER, 
                prix_vente REAL, 
                devise TEXT, 
                ent_id TEXT)""")
    
    # Table des Ventes (Archive facturation)
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
    
    # Table des Dettes (Gestion des tranches de paiement)
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                client TEXT, 
                montant REAL, 
                devise TEXT, 
                ref_v TEXT, 
                ent_id TEXT, 
                historique TEXT)""")
    
    # Table Config (Cœur du SaaS : Status 'ACTIF' ou 'PAUSE')
    run_db("""CREATE TABLE IF NOT EXISTS config (
                ent_id TEXT PRIMARY KEY, 
                nom_ent TEXT, 
                adresse TEXT, 
                tel TEXT, 
                taux REAL, 
                message TEXT, 
                status TEXT DEFAULT 'ACTIF')""")

    # Injection du Super-Compte Maître (admin / admin123)
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'SUPER_ADMIN', 'SYSTEM')", (make_hashes("admin123"),))
        run_db("INSERT INTO config VALUES ('SYSTEM', 'BALIKA CLOUD HQ', 'Admin Central', '000', 2850.0, 'Système Opérationnel', 'ACTIF')")

init_db()

# ==============================================================================
# 3. VERIFICATION DE SÉCURITÉ (LE VERROU PAUSE)
# ==============================================================================
def security_check():
    """Vérifie à chaque rafraîchissement si le compte est toujours autorisé"""
    if st.session_state.auth and st.session_state.role != "SUPER_ADMIN":
        res = run_db("SELECT status FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if res and res[0][0] == 'PAUSE':
            # Si le compte est mis en pause, on réinitialise tout
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.warning("⚠️ VOTRE ACCÈS A ÉTÉ SUSPENDU. Veuillez contacter le service facturation BALIKA.")
            st.stop()

security_check()

# ==============================================================================
# 4. DESIGN ENGINE (CSS & RESPONSIVE)
# ==============================================================================
# Chargement des infos de l'entreprise connectée
if st.session_state.auth:
    c_res = run_db("SELECT nom_ent, message, taux, adresse, tel FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL = c_res[0] if c_res else ("BALIKA", "Bienvenue", 2850.0, "", "")
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL = "BALIKA CLOUD", "Gérez votre business partout", 2850.0, "", ""

st.markdown(f"""
    <style>
    /* Anti-Dark Mode et Couleurs Balika */
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #FFFFFF !important; color: #000000 !important; }}
    
    /* Login Box Centrée */
    .login-container {{
        max-width: 450px; margin: 50px auto; padding: 30px;
        border: 1px solid #FF8C00; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(255,140,0,0.1);
        text-align: center;
    }}
    
    /* Boutons de l'application */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 50px;
        font-weight: bold; border: none; width: 100%; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 5px 15px rgba(255,69,0,0.3); }}

    /* Frame du Total en Caisse */
    .total-frame {{
        border: 3px solid #FF8C00; background: #FFF3E0; padding: 20px;
        border-radius: 15px; text-align: center; font-size: 28px;
        color: #E65100; font-weight: 900; margin: 15px 0;
    }}

    /* Barre Défilante */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #000000; color: #FF8C00;
        padding: 12px 0; position: fixed; top: 0; left: 0; z-index: 9999;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: marquee 25s linear infinite; font-size: 18px; font-weight: bold;
    }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Paramètres d'impression */
    @media print {{
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }}
        .print-area {{ width: 100% !important; border: none !important; padding: 0 !important; }}
    }}
    </style>
    <div class="marquee-container"><div class="marquee-text">✨ {C_NOM} : {C_MSG} | Taux du jour : 1 USD = {C_TX} CDF</div></div>
    <div style="margin-top: 80px;"></div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 5. ÉCRAN DE CONNEXION / INSCRIPTION (INTERFACE CENTRÉE)
# ==============================================================================
if not st.session_state.auth:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/2622/2622143.png", width=80)
        st.title(C_NOM)
        
        tab_log, tab_reg = st.tabs(["🔒 SE CONNECTER", "🚀 CRÉER UN COMPTE"])
        
        with tab_log:
            with st.form("form_login"):
                u = st.text_input("Identifiant", placeholder="Ex: boutique01").lower().strip()
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACCÉDER À MON ESPACE"):
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
            with st.form("form_signup"):
                new_ent = st.text_input("Nom de votre Business").upper().strip()
                new_u = st.text_input("Identifiant Administrateur").lower().strip()
                new_p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("ACTIVER MON ERP CLOUD"):
                    if new_ent and new_u and new_p:
                        check = run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True)
                        if not check:
                            eid = f"E-{random.randint(1000, 9999)}"
                            run_db("INSERT INTO users VALUES (?, ?, 'ADMIN', ?)", (new_u, make_hashes(new_p), eid))
                            run_db("INSERT INTO config VALUES (?, ?, 'Adresse à définir', '000', 2850.0, 'Bienvenue chez nous', 'ACTIF')", (eid, new_ent))
                            st.success("✅ Compte créé ! Connectez-vous sur l'onglet de gauche.")
                        else: st.error("Cet identifiant est déjà pris.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 6. SIDEBAR & NAVIGATION (DROITS D'ACCÈS)
# ==============================================================================
ENT_ID = st.session_state.ent_id
ROLE = st.session_state.role
USER = st.session_state.user

with st.sidebar:
    st.markdown(f"### 👤 {USER.upper()}")
    st.markdown(f"**🏢 {C_NOM}**")
    st.write("---")
    
    # Définition des menus selon le grade
    if ROLE == "SUPER_ADMIN":
        menu = ["🌍 MES ABONNÉS", "📊 STATS SYSTÈME"]
    elif ROLE == "ADMIN":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: # ROLE VENDEUR
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
        
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]
            st.rerun()
            
    st.write("---")
    if st.button("🚪 SE DÉCONNECTER", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 7. LOGIQUE SUPER-ADMIN (GESTION DES COMPTES CLIENTS)
# ==============================================================================
if ROLE == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        st.header("🌍 Pilotage des Entreprises Abonnées")
        clients = run_db("SELECT ent_id, nom_ent, status, tel FROM config WHERE ent_id != 'SYSTEM'", fetch=True)
        
        if clients:
            for c_id, c_nom, c_status, c_tel in clients:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    status_color = "🟢" if c_status == 'ACTIF' else "🔴"
                    col1.write(f"### {status_color} {c_nom}")
                    col1.caption(f"ID : {c_id} | Tél : {c_tel}")
                    
                    if c_status == 'ACTIF':
                        if col2.button("⏸️ METTRE EN PAUSE", key=f"pause_{c_id}"):
                            run_db("UPDATE config SET status='PAUSE' WHERE ent_id=?", (c_id,))
                            st.rerun()
                    else:
                        if col2.button("▶️ RÉACTIVER", key=f"play_{c_id}"):
                            run_db("UPDATE config SET status='ACTIF' WHERE ent_id=?", (c_id,))
                            st.rerun()
                            
                    if col3.button("🗑️ SUPPRIMER", key=f"del_{c_id}"):
                        if st.checkbox(f"Confirmer suppression de {c_nom} ?", key=f"check_{c_id}"):
                            run_db("DELETE FROM config WHERE ent_id=?", (c_id,))
                            run_db("DELETE FROM users WHERE ent_id=?", (c_id,))
                            st.rerun()
                st.divider()
        else:
            st.info("Aucun client enregistré pour le moment.")
    st.stop()

# ==============================================================================
# 8. LOGIQUE CLIENT : CAISSE & FACTURATION (A4 + 80mm)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Terminal de Vente")
        v_devise = st.radio("Devise de paiement :", ["USD", "CDF"], horizontal=True)
        
        # Chargement stock
        produits = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'prix': r[1], 'stock': r[2], 'dev': r[3]} for r in produits}
        
        choix = st.selectbox("Sélectionner un article", ["--- Choisir ---"] + list(p_dict.keys()))
        if st.button("➕ AJOUTER AU PANIER") and choix != "--- Choisir ---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            st.write("### 📝 Détails du Panier")
            net_a_payer = 0.0
            list_details = []
            
            for art, qte in list(st.session_state.panier.items()):
                # Conversion auto si devise différente
                p_unit_base = p_dict[art]['prix']
                if p_dict[art]['dev'] == "USD" and v_devise == "CDF": p_unit = p_unit_base * C_TX
                elif p_dict[art]['dev'] == "CDF" and v_devise == "USD": p_unit = p_unit_base / C_TX
                else: p_unit = p_unit_base
                
                sous_total = p_unit * qte
                net_a_payer += sous_total
                list_details.append({"art": art, "qte": qte, "pu": p_unit, "st": sous_total})
                
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_dict[art]['stock'], value=qte, key=f"q_{art}")
                c3.write(f"{sous_total:,.2f} {v_devise}")
                if c4.button("❌", key=f"rm_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()
            
            st.markdown(f'<div class="total-frame">SOMME À PAYER : {net_a_payer:,.2f} {v_devise}</div>', unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            c_nom = col_a.text_input("NOM DU CLIENT", "CLIENT COMPTANT").upper()
            c_paye = col_b.number_input("MONTANT VERSÉ", min_value=0.0, value=float(net_a_payer))
            
            if st.button("💾 VALIDER ET ÉMETTRE LA FACTURE"):
                v_ref = f"FAC-{random.randint(10000, 99999)}"
                v_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = net_a_payer - c_paye
                
                # Sauvegarde Vente
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (v_ref, c_nom, net_a_payer, c_paye, reste, v_devise, v_date, USER, ENT_ID, json.dumps(list_details)))
                
                # Gestion Dette
                if reste > 0:
                    hist = [{"date": v_date, "paye": c_paye}]
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", (c_nom, reste, v_devise, v_ref, ENT_ID, json.dumps(hist)))
                
                # Mise à jour Stock
                for item in list_details:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (item['qte'], item['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": v_ref, "cl": c_nom, "tot": net_a_payer, "pay": c_paye, "dev": v_devise, "items": list_details, "date": v_date}
                st.session_state.panier = {}
                st.rerun()
    else:
        # --- MODE FACTURE (A4 / 80mm) ---
        f = st.session_state.last_fac
        st.header("📄 Impression de la facture")
        fmt = st.radio("Format :", ["Format 80mm (Ticket)", "Format A4 (Bureau)"], horizontal=True)
        
        style_print = "width: 320px; font-size: 12px;" if "80mm" in fmt else "width: 100%; font-size: 16px; padding: 40px;"
        
        facture_html = f"""
        <div class="print-area" style="background:white; color:black; margin:auto; {style_print} font-family: 'Courier New', Courier, monospace;">
            <h1 align="center" style="margin:0;">{C_NOM}</h1>
            <p align="center" style="margin:0;">{C_ADR}<br>Tél: {C_TEL}</p>
            <hr>
            <p><b>REF:</b> {f['ref']}<br><b>Client:</b> {f['cl']}<br><b>Date:</b> {f['date']}<br><b>Vendeur:</b> {USER.upper()}</p>
            <table style="width:100%; border-collapse:collapse;">
                <tr style="border-bottom:1px solid #000; text-align:left;">
                    <th>Art.</th><th>Qté</th><th align="right">T.</th>
                </tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td align='right'>{i['st']:,.2f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h2 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h2>
            <p align="right">Payé: {f['pay']} {f['dev']}<br>Reste: {f['tot']-f['pay']:,.2f} {f['dev']}</p>
            <p align="center" style="margin-top:20px;">Merci de votre confiance !</p>
        </div>
        """
        st.markdown(facture_html, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        if c1.button("🖨️ IMPRIMER LA FACTURE"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        
        if c2.button("📲 PARTAGER (WHATSAPP)"):
            msg_whatsapp = f"Facture {C_NOM} - Ref {f['ref']} : Total {f['tot']} {f['dev']}. Merci."
            st.info("Partage simulé. Message prêt.")
            
        if c3.button("🔄 NOUVELLE VENTE"):
            st.session_state.last_fac = None
            st.rerun()

# ==============================================================================
# 9. LOGIQUE CLIENT : DETTES (GESTION ÉCHELONNÉE)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.title("📉 Gestion des Dettes Clients")
    liste_dettes = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    
    if not liste_dettes:
        st.success("Toutes les dettes sont réglées ! 🎉")
    else:
        for d_id, d_client, d_montant, d_dev, d_ref, d_hist in liste_dettes:
            with st.expander(f"🔴 {d_client} : {d_montant:,.2f} {d_dev} (Ref: {d_ref})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### Historique des paiements")
                    h_list = json.loads(d_hist)
                    for h in h_list:
                        st.write(f"- {h['date']} : Payé {h['paye']:,.2f}")
                
                with col2:
                    st.write("### Enregistrer un versement")
                    versement = st.number_input(f"Montant versé", min_value=0.0, max_value=float(d_montant), key=f"pay_{d_id}")
                    if st.button("Valider le versement", key=f"btn_pay_{d_id}"):
                        nouveau_montant = d_montant - versement
                        h_list.append({"date": datetime.now().strftime("%d/%m/%Y"), "paye": versement})
                        
                        if nouveau_montant <= 0:
                            # Dette épongée
                            run_db("DELETE FROM dettes WHERE id=?", (d_id,))
                            st.balloons()
                        else:
                            run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nouveau_montant, json.dumps(h_list), d_id))
                        
                        # Mettre aussi à jour la table ventes
                        run_db("UPDATE ventes SET paye = paye + ?, reste = reste - ? WHERE ref=? AND ent_id=?", 
                               (versement, versement, d_ref, ENT_ID))
                        st.rerun()

# ==============================================================================
# 10. LOGIQUE CLIENT : RAPPORTS (BOUTON IMPRESSION)
# ==============================================================================
elif st.session_state.page == "RAPPORTS":
    st.title("📊 Rapports d'Activités")
    
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        df = pd.DataFrame(data, columns=["Date", "Référence", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Recettes USD", f"{df[df['Devise']=='USD']['Payé'].sum():,.2f} $")
        c2.metric("Recettes CDF", f"{df[df['Devise']=='CDF']['Payé'].sum():,.0f} FC")
        c3.metric("Dettes Globales", f"{df['Reste'].sum():,.2f}")
        
        st.write("### 📜 Journal des Ventes")
        st.dataframe(df, use_container_width=True)
        
        if st.button("🖨️ IMPRIMER CE RAPPORT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.info("Aucune vente enregistrée.")

# ==============================================================================
# 11. LOGIQUE CLIENT : STOCK (MODIFICATION PRIX & SUPPRESSION)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.title("📦 Inventaire & Prix")
    
    with st.form("ajout_stock"):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        n_art = c1.text_input("Désignation de l'article")
        n_qte = c2.number_input("Quantité initiale", min_value=1)
        n_px = c3.number_input("Prix de vente")
        n_dv = c4.selectbox("Devise", ["USD", "CDF"])
        if st.form_submit_button("➕ ENREGISTRER L'ARTICLE"):
            run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)",
                   (n_art.upper(), n_qte, n_px, n_dv, ENT_ID))
            st.rerun()
            
    st.write("---")
    inventaire = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    
    for p_id, p_nom, p_stock, p_prix, p_dev in inventaire:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{p_nom}**")
            col2.write(f"Stock : `{p_stock}`")
            new_price = col3.number_input("Prix", value=float(p_prix), key=f"px_{p_id}")
            
            if col3.button("Mettre à jour", key=f"up_{p_id}"):
                run_db("UPDATE produits SET prix_vente=? WHERE id=?", (new_price, p_id))
                st.toast("Prix mis à jour !")
                
            if col4.button("🗑️", key=f"del_p_{p_id}"):
                run_db("DELETE FROM produits WHERE id=?", (p_id,))
                st.rerun()
        st.divider()

# ==============================================================================
# 12. LOGIQUE CLIENT : VENDEURS (GESTION DU PERSONNEL)
# ==============================================================================
elif st.session_state.page == "VENDEURS":
    st.title("👥 Comptes de mon Personnel")
    with st.form("new_staff"):
        s_u = st.text_input("Nom d'utilisateur Vendeur").lower().strip()
        s_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            if s_u and s_p:
                check = run_db("SELECT * FROM users WHERE username=?", (s_u,), fetch=True)
                if not check:
                    run_db("INSERT INTO users VALUES (?, ?, 'VENDEUR', ?)", (s_u, make_hashes(s_p), ENT_ID))
                    st.success(f"Compte {s_u} activé !")
                else: st.error("Ce nom est déjà pris.")

    st.write("### Liste des vendeurs")
    staff = run_db("SELECT username FROM users WHERE ent_id=? AND role='VENDEUR'", (ENT_ID,), fetch=True)
    for s in staff:
        c1, c2 = st.columns([3, 1])
        c1.write(f"👤 **{s[0].upper()}**")
        if c2.button("Supprimer", key=f"s_{s[0]}"):
            run_db("DELETE FROM users WHERE username=?", (s[0],))
            st.rerun()

# ==============================================================================
# 13. LOGIQUE CLIENT : CONFIGURATION (ADMIN)
# ==============================================================================
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres de l'Entreprise")
    with st.form("set_cfg"):
        f_nom = st.text_input("Nom de la Société", C_NOM)
        f_adr = st.text_input("Adresse", C_ADR)
        f_tel = st.text_input("Téléphone", C_TEL)
        f_tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TX)
        f_msg = st.text_area("Message de la barre défilante", C_MSG)
        
        if st.form_submit_button("💾 SAUVEGARDER LES MODIFICATIONS"):
            run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, message=? WHERE ent_id=?",
                   (f_nom.upper(), f_adr, f_tel, f_tx, f_msg, ENT_ID))
            st.rerun()
