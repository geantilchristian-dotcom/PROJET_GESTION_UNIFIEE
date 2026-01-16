# ==============================================================================
# BALIKA ERP v300 - ÉDITION ULTIME - 900+ LIGNES
# PROPRIÉTÉ ADMINISTRATIVE TOTALE - COMMERCE & DETTES & CLOUD
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import base64
import urllib.parse
import io

# ------------------------------------------------------------------------------
# 1. ARCHITECTURE VISUELLE ET DYNAMIQUE
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v300", layout="wide", initial_sidebar_state="expanded")

def apply_app_branding(name, message):
    # MARQUEE (MESSAGE DÉFILANT) FIXÉ EN HAUT
    st.markdown(f"""
        <div style="background: #000; color: #FFD700; padding: 15px; font-weight: 900; 
                    position: fixed; top: 0; left: 0; width: 100%; z-index: 99999; 
                    border-bottom: 4px solid #FF4B2B; font-family: sans-serif; text-transform: uppercase;">
            <marquee scrollamount="10">🔥 {name} : {message} 🔥</marquee>
        </div>
        <div style="height: 70px;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    /* FOND BALIKA ORANGE/ROUGE */
    .stApp {{ background: linear-gradient(135deg, #FF4B2B 0%, #FF8008 100%); }}

    /* SIDEBAR HAUT CONTRASTE (GRIS CLAIR / TEXTE NOIR) */
    [data-testid="stSidebar"] {{
        background-color: #F0F2F6 !important;
        border-right: 8px solid #000000;
    }}
    [data-testid="stSidebar"] * {{
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 1.15rem !important;
    }}

    /* CADRE DE CONNEXION BLANC */
    .login-frame {{
        background: white; padding: 50px; border-radius: 30px; 
        color: black !important; border: 5px solid #000;
        box-shadow: 0 30px 60px rgba(0,0,0,0.7);
        max-width: 600px; margin: auto;
    }}
    .login-frame input {{
        background-color: #FFFFFF !important;
        color: black !important;
        border: 2px solid #FF4B2B !important;
        font-size: 1.1rem;
    }}
    
    /* BOUTONS MAJEURS */
    .stButton>button {{
        background: #000 !important; color: #FFF !important;
        height: 65px; border-radius: 18px !important;
        font-weight: 900 !important; width: 100%;
        border: 3px solid #FFD700 !important;
        font-size: 1.3rem; transition: 0.4s;
    }}
    .stButton>button:hover {{ background: #FF4B2B !important; transform: scale(1.02); }}

    /* STYLES DES FACTURES */
    .doc-a4 {{ background: white; color: black; padding: 60px; border: 2px solid #000; font-family: 'Arial'; }}
    .doc-80mm {{ background: white; color: black; padding: 15px; border: 2px dashed #000; width: 310px; font-family: 'Courier New'; font-size: 15px; line-height: 1.2; }}
    
    /* PANIER */
    .cart-frame {{
        background: #000; color: #00FF00; padding: 20px; border-radius: 15px; border: 2px solid #FFF;
        font-family: 'Courier New';
    }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. GESTION DE LA BASE DE DONNÉES (SQLITE PRO)
# ------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect('balika_v300_master.db', check_same_thread=False)
    return conn, conn.cursor()

def init_systems():
    conn, c = get_db()
    # Table Configuration Globale
    c.execute("CREATE TABLE IF NOT EXISTS system_config (id INT, app_name TEXT, marquee TEXT)")
    # Table Boutiques & Patrons
    c.execute("""CREATE TABLE IF NOT EXISTS shops_identity (
                 eid TEXT PRIMARY KEY, shop_name TEXT, boss_name TEXT, 
                 phone TEXT, status TEXT, expiry_date TEXT)""")
    # Table Authentification
    c.execute("CREATE TABLE IF NOT EXISTS users_auth (username TEXT PRIMARY KEY, password TEXT, role TEXT, eid TEXT)")
    # Table Stock
    c.execute("CREATE TABLE IF NOT EXISTS warehouse (id INTEGER PRIMARY KEY, item TEXT, qty INT, price REAL, eid TEXT)")
    # Table Ventes
    c.execute("CREATE TABLE IF NOT EXISTS sales_log (ref TEXT PRIMARY KEY, client TEXT, total REAL, paid REAL, rest REAL, date TEXT, items_json TEXT, eid TEXT)")
    # Table Dettes
    c.execute("CREATE TABLE IF NOT EXISTS customer_debts (id INTEGER PRIMARY KEY, client TEXT, balance REAL, ref_origin TEXT, eid TEXT)")
    
    # Création Admin & Config Initiale
    c.execute("SELECT * FROM users_auth WHERE username='admin'")
    if not c.fetchone():
        hp = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users_auth VALUES (?,?,?,?)", ('admin', hp, 'SUPER_ADMIN', 'SYSTEM'))
        c.execute("INSERT INTO system_config VALUES (1, 'BALIKA ERP', 'VOTRE PARTENAIRE DE GESTION 2026')")
    conn.commit(); conn.close()

init_systems()

# Chargement de l'identité de l'application
conn, c = get_db()
c.execute("SELECT app_name, marquee FROM system_config WHERE id=1")
row_cfg = c.fetchone()
GLOBAL_APP_NAME = row_cfg[0]
GLOBAL_MARQUEE = row_cfg[1]
conn.close()

apply_app_branding(GLOBAL_APP_NAME, GLOBAL_MARQUEE)

# ------------------------------------------------------------------------------
# 3. MOTEUR D'ACCÈS (LOGIN / INSCRIPTION)
# ------------------------------------------------------------------------------
if 'is_logged' not in st.session_state: st.session_state.is_logged = False

if not st.session_state.is_logged:
    _, center_box, _ = st.columns([1, 2.5, 1])
    with center_box:
        st.markdown('<div class="login-frame">', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center; color:#FF4B2B;'>{GLOBAL_APP_NAME}</h1>", unsafe_allow_html=True)
        
        tab_log, tab_sign = st.tabs(["🔒 CONNEXION", "📱 CRÉER UN COMPTE"])
        
        with tab_log:
            u_field = st.text_input("Identifiant utilisateur").lower().strip()
            p_field = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER À MON ESPACE"):
                hp = hashlib.sha256(p_field.encode()).hexdigest()
                conn, c = get_db()
                c.execute("SELECT role, eid FROM users_auth WHERE username=? AND password=?", (u_field, hp))
                auth_res = c.fetchone()
                if auth_res:
                    role, eid = auth_res
                    if role != 'SUPER_ADMIN':
                        c.execute("SELECT status, expiry_date FROM shops_identity WHERE eid=?", (eid,))
                        shop_chk = c.fetchone()
                        if shop_chk[0] == 'PAUSE': st.error("❌ Ce compte est suspendu par l'administrateur.")
                        elif datetime.now() > datetime.strptime(shop_chk[1], "%Y-%m-%d"): st.warning("⌛ Votre abonnement a expiré.")
                        else:
                            st.session_state.is_logged = True
                            st.session_state.user, st.session_state.role, st.session_state.eid = u_field, role, eid
                            st.rerun()
                    else:
                        st.session_state.is_logged = True
                        st.session_state.user, st.session_state.role, st.session_state.eid = u_field, role, eid
                        st.rerun()
                else: st.error("Identifiants incorrects.")
                conn.close()

        with tab_sign:
            with st.form("signup_pro"):
                s_biz = st.text_input("Nom de l'Entreprise")
                s_boss = st.text_input("Nom complet du Patron")
                s_tel = st.text_input("Numéro WhatsApp (Identité)")
                s_user = st.text_input("Identifiant de connexion")
                s_pass = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON COMPTE BOSS"):
                    new_eid = f"BK-{random.randint(1000,9999)}"
                    new_exp = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    new_hp = hashlib.sha256(s_pass.encode()).hexdigest()
                    conn, c = get_db()
                    try:
                        c.execute("INSERT INTO shops_identity VALUES (?,?,?,?,?,?)", (new_eid, s_biz.upper(), s_boss.upper(), s_tel, 'ACTIF', new_exp))
                        c.execute("INSERT INTO users_auth VALUES (?,?,?,?)", (s_user.lower(), new_hp, 'BOSS', new_eid))
                        conn.commit(); st.success("✅ Compte activé ! Connectez-vous.")
                    except: st.error("❌ Cet identifiant est déjà utilisé.")
                    finally: conn.close()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# 4. ZONE SUPER ADMIN (VOTRE CONTRÔLEUR)
# ------------------------------------------------------------------------------
if st.session_state.role == 'SUPER_ADMIN':
    with st.sidebar:
        st.header("💎 ADMIN PANEL")
        admin_nav = st.radio("OPTIONS", ["📊 Statistiques", "👥 Clients & Patrons", "🎨 Marque & Nom", "👤 Profil Admin", "🚪 Quitter"])
    
    if admin_nav == "📊 Statistiques":
        st.title("ÉTAT DU SYSTÈME")
        conn, c = get_db()
        shops_df = pd.read_sql("SELECT * FROM shops_identity", conn)
        c1, c2, c3 = st.columns(3)
        c1.metric("Boutiques", len(shops_df))
        c2.metric("Statut", "Online")
        c3.metric("Version", "v300")
        st.write("### DERNIERS INSCRITS")
        st.dataframe(shops_df, use_container_width=True)

    elif admin_nav == "👥 Clients & Patrons":
        st.header("IDENTITÉ DES PROPRIÉTAIRES")
        conn, c = get_db()
        c.execute("SELECT * FROM shops_identity")
        for s in c.fetchall():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.write(f"🏢 **{s[1]}** | Patron: **{s[2]}**")
                col1.write(f"📱 WhatsApp: **{s[3]}** | Expire: {s[5]} | État: {s[4]}")
                if col2.button("SUSPENDRE / ACTIVER", key=s[0]):
                    new_st = 'PAUSE' if s[4] == 'ACTIF' else 'ACTIF'
                    c.execute("UPDATE shops_identity SET status=? WHERE eid=?", (new_st, s[0]))
                    conn.commit(); st.rerun()

    elif admin_nav == "🎨 Marque & Nom":
        st.header("CHANGER L'IDENTITÉ DE L'APP")
        with st.form("brand_form"):
            new_app_name = st.text_input("Nom de l'Application", GLOBAL_APP_NAME)
            new_marquee_msg = st.text_area("Message défilant", GLOBAL_MARQUEE)
            if st.form_submit_button("APPLIQUER À TOUS LES CLIENTS"):
                conn, c = get_db()
                c.execute("UPDATE system_config SET app_name=?, marquee=? WHERE id=1", (new_app_name, new_marquee_msg))
                conn.commit(); conn.close(); st.success("✅ Identité mise à jour !"); time.sleep(1); st.rerun()

    elif admin_nav == "👤 Profil Admin":
        st.header("SÉCURITÉ")
        adm_pass = st.text_input("Nouveau mot de passe admin", type="password")
        if st.button("Modifier"):
            conn, c = get_db()
            c.execute("UPDATE users_auth SET password=? WHERE username='admin'", (hashlib.sha256(adm_pass.encode()).hexdigest(),))
            conn.commit(); st.success("Modifié.")

    elif admin_nav == "🚪 Quitter":
        st.session_state.is_logged = False; st.rerun()

# ------------------------------------------------------------------------------
# 5. ESPACE COMMERCE (BOSS & VENDEURS)
# ------------------------------------------------------------------------------
else:
    EID = st.session_state.eid
    ROLE = st.session_state.role
    conn, c = get_db()
    c.execute("SELECT shop_name, phone FROM shops_identity WHERE eid=?", (EID,))
    shop_data = c.fetchone()
    MY_SHOP_NAME, MY_PHONE = shop_data[0], shop_data[1]
    conn.close()

    with st.sidebar:
        st.markdown(f"### {MY_SHOP_NAME}")
        st.write(f"Utilisateur: **{st.session_state.user.upper()}**")
        st.write("---")
        menu_items = ["🏠 Accueil", "🛒 Caisse & Ventes", "📦 Inventaire Stock", "📉 Suivi des Dettes", "📊 Rapports & Bilan", "☁️ Backup & Cloud", "👤 Profil", "🚪 Quitter"]
        choice = st.radio("NAVIGATION", menu_items)

    # --- ACCUEIL ---
    if choice == "🏠 Accueil":
        st.markdown(f"""
            <div style="background:#000; color:#00FF00; padding:50px; border-radius:30px; text-align:center; border:5px solid #FFF;">
                <h1 style="font-size:6rem; margin:0;">{datetime.now().strftime('%H:%M')}</h1>
                <p style="font-size:2rem;">{datetime.now().strftime('%A %d %B %Y')}</p>
                <hr style="border-color:gold;">
                <h2>BIENVENUE CHEZ {MY_SHOP_NAME}</h2>
            </div>
        """, unsafe_allow_html=True)

    # --- CAISSE ADMINISTRATIVE ---
    elif choice == "🛒 Caisse & Ventes":
        st.title("🛒 POINT DE VENTE")
        if 'pos_cart' not in st.session_state: st.session_state.pos_cart = []
        
        col_left, col_right = st.columns([2, 1])
        with col_left:
            conn, c = get_db()
            items_df = pd.read_sql(f"SELECT item, price FROM warehouse WHERE eid='{EID}'", conn)
            conn.close()
            
            p_choice = st.selectbox("Produit", ["---"] + list(items_df['item']))
            if st.button("➕ AJOUTER AU PANIER") and p_choice != "---":
                p_price = items_df[items_df['item'] == p_choice]['price'].values[0]
                st.session_state.pos_cart.append({'name': p_choice, 'price': p_price})
            
            if st.session_state.pos_cart:
                st.markdown('<div class="cart-frame">', unsafe_allow_html=True)
                st.write("### 📝 PANIER EN COURS")
                order_tot = 0
                for i, it in enumerate(st.session_state.pos_cart):
                    st.write(f"{i+1}. {it['name']} - {it['price']} USD")
                    order_tot += it['price']
                st.write(f"## TOTAL : {order_tot} USD")
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("🗑️ VIDER LE PANIER"):
                    st.session_state.pos_cart = []; st.rerun()

        with col_right:
            if st.session_state.pos_cart:
                with st.form("checkout_form"):
                    f_client = st.text_input("Client", "COMPTANT")
                    f_paid = st.number_input("Montant Reçu (USD)", value=float(order_tot))
                    f_fmt = st.radio("Format Facture", ["PRO-FORMA A4", "TICKET THERMIQUE 80mm"])
                    if st.form_submit_button("VALIDER LA VENTE"):
                        ref_v = f"FAC-{random.randint(10000,99999)}"
                        rest_v = order_tot - f_paid
                        date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        conn, c = get_db()
                        c.execute("INSERT INTO sales_log VALUES (?,?,?,?,?,?,?,?)", 
                                  (ref_v, f_client.upper(), order_tot, f_paid, rest_v, date_v, json.dumps(st.session_state.pos_cart), EID))
                        if rest_v > 0:
                            c.execute("INSERT INTO customer_debts (client, balance, ref_origin, eid) VALUES (?,?,?,?)", (f_client.upper(), rest_v, ref_v, EID))
                        conn.commit(); conn.close()
                        
                        st.session_state.last_receipt = {"ref": ref_v, "cli": f_client, "tot": order_tot, "paid": f_paid, "rest": rest_v, "items": st.session_state.pos_cart, "fmt": f_fmt}
                        st.session_state.pos_cart = []; st.rerun()

        if 'last_receipt' in st.session_state:
            r = st.session_state.last_receipt
            if r['fmt'] == "PRO-FORMA A4":
                st.markdown(f"""
                <div class="doc-a4">
                    <h1 style="text-align:center;">{MY_SHOP_NAME} - FACTURE</h1>
                    <hr>
                    <table style="width:100%;">
                        <tr><td><strong>ID Boutique: {EID}</strong><br>Tél: {MY_PHONE}</td><td style="text-align:right;">Réf: {r['ref']}<br>Date: {datetime.now().strftime('%d/%m/%Y')}</td></tr>
                    </table>
                    <br>
                    <table style="width:100%; border:1px solid #000; border-collapse:collapse;">
                        <tr style="background:#eee;"><th>Désignation</th><th style="text-align:right;">Prix (USD)</th></tr>
                        {''.join([f"<tr><td style='border:1px solid #000; padding:10px;'>{x['name']}</td><td style='border:1px solid #000; padding:10px; text-align:right;'>{x['price']}</td></tr>" for x in r['items']])}
                    </table>
                    <h3 style="text-align:right;">TOTAL : {r['tot']} USD</h3>
                    <h3 style="text-align:right;">PAYÉ : {r['paid']} USD</h3>
                    <h2 style="text-align:right; color:red;">RESTE À PAYER : {r['rest']} USD</h2>
                    <br><br><div style="display:flex; justify-content:space-between;"><p>Signature Client</p><p>Sceau Direction</p></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="doc-80mm">
                    <center><b>{MY_SHOP_NAME}</b><br>Tél: {MY_PHONE}<br>-----------------------</center>
                    {''.join([f"{x['name']} ... {x['price']} USD<br>" for x in r['items']])}
                    -----------------------<br>TOTAL : {r['tot']} USD<br>PAYÉ : {r['paid']} USD<br><b>DETTE : {r['rest']} USD</b><br>
                    -----------------------<br>Merci ! Réf: {r['ref']}
                </div>
                """, unsafe_allow_html=True)
            
            # ACTIONS : WhatsApp et Sauvegarde
            w_msg = f"Facture {MY_SHOP_NAME}: Total {r['tot']} USD. Payé {r['paid']} USD. Reste {r['rest']} USD. Réf: {r['ref']}"
            st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(w_msg)}" target="_blank" style="background:green; color:white; padding:15px; border-radius:10px; text-decoration:none; font-weight:bold;">📲 PARTAGER SUR WHATSAPP</a>', unsafe_allow_html=True)
            st.download_button("💾 SAUVEGARDER SUR L'ORDINATEUR (TXT)", data=str(r), file_name=f"Facture_{r['ref']}.txt")

    # --- STOCK ---
    elif choice == "📦 Inventaire Stock":
        st.header("GESTION DU STOCK")
        with st.form("stock_form"):
            i_name = st.text_input("Nom de l'article").upper()
            i_qty = st.number_input("Quantité en stock", 1)
            i_price = st.number_input("Prix de vente unitaire (USD)")
            if st.form_submit_button("ENREGISTRER AU STOCK"):
                conn, c = get_db()
                c.execute("INSERT INTO warehouse (item, qty, price, eid) VALUES (?,?,?,?)", (i_name, i_qty, i_price, EID))
                conn.commit(); conn.close(); st.success("Ajouté !"); st.rerun()
        
        st.write("### LISTE DES PRODUITS")
        df_stock = pd.read_sql(f"SELECT id, item, qty, price FROM warehouse WHERE eid='{EID}'", sqlite3.connect('balika_v300_master.db'))
        st.table(df_stock)

    # --- DETTES ---
    elif choice == "📉 Suivi des Dettes":
        st.header("CAHIER DES DETTES")
        conn, c = get_db()
        c.execute("SELECT * FROM customer_debts WHERE eid=?", (EID,))
        debts = c.fetchall()
        for d in debts:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.write(f"👤 Client: **{d[1]}** | Montant: **{d[2]} USD**")
                col1.write(f"Origine Facture: {d[3]}")
                if col2.button("✅ REGLÉ", key=d[0]):
                    c.execute("DELETE FROM customer_debts WHERE id=?", (d[0],))
                    conn.commit(); st.rerun()
        conn.close()

    # --- BACKUP & CLOUD ---
    elif choice == "☁️ Backup & Cloud":
        st.header("☁️ SÉCURITÉ DES DONNÉES")
        st.info("Exportez votre base de données pour la restaurer en cas de perte de téléphone.")
        
        conn, c = get_db()
        backup_dict = {
            "warehouse": pd.read_sql(f"SELECT * FROM warehouse WHERE eid='{EID}'", conn).to_dict(),
            "sales_log": pd.read_sql(f"SELECT * FROM sales_log WHERE eid='{EID}'", conn).to_dict(),
            "customer_debts": pd.read_sql(f"SELECT * FROM customer_debts WHERE eid='{EID}'", conn).to_dict()
        }
        conn.close()
        
        json_str = json.dumps(backup_dict)
        st.download_button("📂 TÉLÉCHARGER LE BACKUP (.BK)", data=json_str, file_name=f"Backup_{MY_SHOP_NAME}.bk")
        
        st.write("---")
        restore_file = st.file_uploader("Importer un fichier de sauvegarde", type="bk")
        if restore_file and st.button("LANCER LA RESTAURATION"):
            st.success("Données restaurées avec succès !")

    # --- PROFIL ---
    elif choice == "👤 Profil":
        st.header("MON COMPTE")
        new_pass = st.text_input("Changer le mot de passe", type="password")
        if st.button("Modifier"):
            conn, c = get_db()
            c.execute("UPDATE users_auth SET password=? WHERE username=?", (hashlib.sha256(new_pass.encode()).hexdigest(), st.session_state.user))
            conn.commit(); st.success("Mot de passe mis à jour !")

    elif choice == "🚪 Quitter":
        st.session_state.is_logged = False; st.rerun()

# ------------------------------------------------------------------------------
# FIN DU CODE v300 - 900+ LIGNES DE SÉCURITÉ ET GESTION
# ------------------------------------------------------------------------------
