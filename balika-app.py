# ==============================================================================
# PROJET : BALIKA ERP - VERSION INTEGRALE & EXPANSÉE v2033
# AUCUNE LIGNE SUPPRIMÉE - SYSTÈME DE GESTION PROFESSIONNEL COMPLET
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import hashlib
import json
import time
import io

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & DESIGN (OPTIMISATION MOBILE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2033",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des états de session (Session State)
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False,
        'user': "",
        'role': "",
        'ent_id': "SYSTEM",
        'page': "ACCUEIL",
        'panier': {},
        'last_fac': None,
        'format_fac': "80mm",
        'show_register': False,
        'devise_vente': "USD",
        'temp_client': "COMPTANT"
    })

# CSS PERSONNALISÉ : CONTRASTE ÉLEVÉ ET CENTRAGE
st.markdown("""
    <style>
    /* Fond de l'application */
    .stApp { background-color: #002266 !important; }
    
    /* Textes et Titres */
    h1, h2, h3, h4, h5, p, label, span, div.stText { 
        color: #FFFFFF !important; 
        text-align: center !important; 
        font-weight: bold;
    }
    
    /* En-tête fixe avec texte défilant (Marquee) */
    .fixed-header { 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #FFFF00; height: 60px; 
        z-index: 999999; display: flex; align-items: center; 
        border-bottom: 3px solid #FFFFFF; 
    }
    marquee { font-size: 20px; font-weight: bold; }
    .spacer { margin-top: 80px; }
    
    /* Boutons larges pour usage sur téléphone */
    .stButton>button { 
        background: linear-gradient(135deg, #007bff, #0056b3) !important;
        color: white !important; border-radius: 15px; 
        height: 60px; width: 100%; border: 2px solid #FFFFFF;
        font-size: 18px; font-weight: bold;
        margin-bottom: 10px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Cadre de Total (Frame Coloré) */
    .total-frame { 
        background: #000000; color: #00FF00; 
        padding: 25px; border: 4px solid #FFFFFF; 
        border-radius: 20px; text-align: center; 
        margin: 20px 0; font-size: 32px; 
    }

    /* Tableaux : Fond blanc, texte noir pour lisibilité maximale */
    .stDataFrame, [data-testid="stTable"] { 
        background-color: #FFFFFF !important; 
        border-radius: 12px; padding: 10px;
        color: #000000 !important;
    }
    
    /* Champs de saisie */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] { 
        background-color: #FFFFFF !important; 
        border-radius: 10px !important; 
    }
    input { color: #000000 !important; font-weight: bold !important; text-align: center !important; }

    /* FACTURE ADMINISTRATIVE A4 & 80mm */
    .facture-container {
        background: #FFFFFF; color: #000000 !important;
        padding: 40px; border-radius: 2px; width: 95%; max-width: 850px;
        margin: auto; border: 2px solid #000000;
    }
    .facture-container * { color: #000000 !important; text-align: center; }
    .facture-container table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .facture-container th, .facture-container td { border: 1px solid #000000; padding: 12px; font-size: 16px; }
    .signature-box { margin-top: 50px; text-align: right; padding-right: 50px; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (SQLITE3)
# ------------------------------------------------------------------------------
def run_db(query, params=(), fetch=False):
    """Exécute les requêtes SQL de manière sécurisée."""
    try:
        with sqlite3.connect('balika_v2033_master.db', timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch: return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur Base de Données : {e}")
        return []

def hash_pw(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    """Initialisation complète de toutes les tables nécessaires."""
    # Table Utilisateurs (Incluant Essai et Validation)
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ATTENTE', date_fin_essai TEXT, 
        nom TEXT, prenom TEXT, telephone TEXT, date_creation TEXT)""")
    
    # Table Configuration Globale (Admin)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)""")
    
    # Table Infos Entreprise
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT, header_custom TEXT)""")

    # Table Produits (Stock Initial vs Actuel)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_initial INTEGER, stock_actuel INTEGER, 
        prix_achat REAL, prix_vente REAL, devise TEXT, ent_id TEXT)""")

    # Table Ventes (Avec Vendeur pour traçabilité)
    run_db("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, devise TEXT, 
        date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)""")

    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, 
        montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT)""")

    # Table Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, 
        montant REAL, devise TEXT, date_d TEXT, ent_id TEXT)""")

    # --- DONNÉES DE BASE ---
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("""INSERT INTO users (username, password, role, status, date_creation) 
               VALUES (?,?,?,?,?)""", 
               ('admin', hash_pw("admin123"), 'SUPER_ADMIN', 'ACTIF', datetime.now().strftime("%d/%m/%Y")))
    
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("""INSERT INTO system_config (id, app_name, marquee_text, taux_global) 
               VALUES (1, 'BALIKA ERP', 'BIENVENUE DANS VOTRE SYSTÈME DE GESTION v2033', 2850.0)""")

init_db()

# Chargement des constantes globales
cfg_data = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_GLOBAL = cfg_data[0] if cfg_data else ("BALIKA ERP", "Bienvenue", 2850.0)

# Affichage du Header défilant
st.markdown(f'<div class="fixed-header"><marquee>{MARQUEE}</marquee></div><div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. INTERFACE D'ACCÈS (CONNEXION & INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f"<h1>🏢 {APP_NAME}</h1>", unsafe_allow_html=True)
    
    tab_log, tab_reg = st.tabs(["🔐 SE CONNECTER", "📝 CRÉER MA BOUTIQUE"])
    
    with tab_log:
        u_log = st.text_input("Identifiant (Username)").lower().strip()
        p_log = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU TABLEAU DE BORD"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u_log,), fetch=True)
            if res and hash_pw(p_log) == res[0][0]:
                if res[0][3] == "ATTENTE":
                    st.warning("⏳ Votre compte est en attente de validation par l'administrateur.")
                elif res[0][3] == "PAUSE":
                    st.error("❌ Votre accès a été suspendu.")
                else:
                    st.session_state.update({'auth':True, 'user':u_log, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
            else:
                st.error("🚫 Identifiants incorrects.")

    with tab_reg:
        with st.form("inscription_form"):
            st.write("### Formulaire d'Ouverture de Boutique")
            r_ent = st.text_input("Nom de votre Boutique (ex: BALIKA SHOP)")
            col1, col2 = st.columns(2)
            r_nom = col1.text_input("Votre Nom")
            r_pre = col2.text_input("Votre Prénom")
            r_tel = st.text_input("Numéro de Téléphone")
            r_pw1 = st.text_input("Définir un mot de passe", type="password")
            
            if st.form_submit_button("ENVOYER MA DEMANDE D'ADHÉSION"):
                if len(r_pw1) < 4 or not r_ent:
                    st.error("Veuillez remplir tous les champs correctement.")
                else:
                    clean_id = r_ent.lower().replace(" ", "")
                    check = run_db("SELECT username FROM users WHERE username=?", (clean_id,), fetch=True)
                    if check:
                        st.error("Ce nom de boutique est déjà pris.")
                    else:
                        run_db("""INSERT INTO users (username, password, role, ent_id, status, nom, prenom, telephone, date_creation) 
                               VALUES (?,?,?,?,?,?,?,?,?)""", 
                               (clean_id, hash_pw(r_pw1), 'USER', clean_id, 'ATTENTE', r_nom, r_pre, r_tel, datetime.now().strftime("%d/%m/%Y")))
                        run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (clean_id, r_ent.upper(), r_tel))
                        st.success("✅ Demande enregistrée ! L'administrateur va valider votre compte sous peu.")
    st.stop()

# ------------------------------------------------------------------------------
# 4. LOGIQUE DE NAVIGATION (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    st.write(f"Rôle : {st.session_state.role}")
    st.divider()
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = {"🏠 ACCUEIL": "ACCUEIL", "👥 GÉRER ABONNÉS": "ABONNES", "⚙️ CONFIG SYSTÈME": "CONFIG"}
    else:
        menu = {
            "🏠 ACCUEIL": "ACCUEIL", 
            "📦 GESTION STOCK": "STOCK", 
            "🛒 CAISSE": "CAISSE", 
            "📊 RAPPORTS VENTRE": "RAPPORTS", 
            "📉 DETTES": "DETTES", 
            "💸 DÉPENSES": "DEPENSES",
            "👥 MES VENDEURS": "VENDEURS",
            "⚙️ PARAMÈTRES": "REGLAGES"
        }
    
    for label, target in menu.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = target
            st.rerun()
            
    st.divider()
    if st.button("🚪 DÉCONNEXION", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 5. MODULE SUPER ADMIN (admin / admin123)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ACCUEIL":
        st.markdown("<h1>🌟 DASHBOARD SUPER ADMIN</h1>", unsafe_allow_html=True)
        total_u = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)[0][0]
        st.markdown(f"<div class='total-frame'>TOTAL BOUTIQUES : {total_u}</div>", unsafe_allow_html=True)

    elif st.session_state.page == "ABONNES":
        st.markdown("<h1>👥 VALIDATION & ESSAIS</h1>", unsafe_allow_html=True)
        clients = run_db("SELECT username, status, telephone, date_fin_essai, nom, prenom FROM users WHERE role='USER'", fetch=True)
        
        for u_id, u_st, u_tel, u_fin, u_n, u_p in clients:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**Boutique: {u_id.upper()}** ({u_n} {u_p})")
                c1.write(f"📞 {u_tel} | 🏁 Fin : {u_fin if u_fin else 'Non défini'}")
                
                # Gestion de la validation et du temps d'essai
                duree = c2.number_input("Jours d'essai", 1, 365, 30, key=f"d_{u_id}")
                if c2.button(f"✅ VALIDER / ACTIVER", key=f"v_{u_id}"):
                    date_limite = (datetime.now() + timedelta(days=duree)).strftime("%d/%m/%Y")
                    run_db("UPDATE users SET status='ACTIF', date_fin_essai=? WHERE username=?", (date_limite, u_id))
                    st.success(f"Compte {u_id} activé jusqu'au {date_limite}")
                    time.sleep(1); st.rerun()
                
                if c3.button("🔴 SUSPENDRE", key=f"s_{u_id}"):
                    run_db("UPDATE users SET status='PAUSE' WHERE username=?", (u_id,))
                    st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"del_{u_id}"):
                    run_db("DELETE FROM users WHERE username=?", (u_id,))
                    run_db("DELETE FROM ent_infos WHERE ent_id=?", (u_id,))
                    st.rerun()

    elif st.session_state.page == "CONFIG":
        st.markdown("<h1>⚙️ CONFIGURATION GLOBALE</h1>", unsafe_allow_html=True)
        with st.form("sys_form"):
            new_app = st.text_input("Nom de l'Application", APP_NAME)
            new_mar = st.text_area("Texte de défilement", MARQUEE)
            new_tx = st.number_input("Taux d'échange (1$ = ? CDF)", value=TX_GLOBAL)
            if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (new_app, new_mar, new_tx))
                st.success("Configuration mise à jour sur tout le système !")
                st.rerun()

# ------------------------------------------------------------------------------
# 6. MODULE BOUTIQUE (USER & VENDEUR)
# ------------------------------------------------------------------------------
else:
    # --- PAGE ACCUEIL ---
    if st.session_state.page == "ACCUEIL":
        st.markdown(f"<h1>🏠 BIENVENUE CHEZ {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>CHIFFRE D'AFFAIRES DU JOUR :<br>{v_jr:,.2f} $</div>", unsafe_allow_html=True)
        
        info_essai = run_db("SELECT date_fin_essai FROM users WHERE username=?", (st.session_state.user,), fetch=True)
        st.write(f"📅 Votre abonnement expire le : **{info_essai[0][0]}**")

    # --- PAGE GESTION STOCK ---
    elif st.session_state.page == "STOCK":
        st.markdown("<h1>📦 INVENTAIRE DES PRODUITS</h1>", unsafe_allow_html=True)
        
        with st.expander("➕ AJOUTER UN NOUVEL ARTICLE"):
            with st.form("add_p"):
                f_des = st.text_input("Désignation du produit")
                col_a, col_b = st.columns(2)
                f_qte = col_a.number_input("Quantité en stock (Initial)", 1)
                f_pa = col_b.number_input("Prix d'Achat Unitaire ($)", 0.0)
                f_pv = st.number_input("Prix de Vente Unitaire ($)", 0.0)
                if st.form_submit_button("ENREGISTRER DANS LE STOCK"):
                    run_db("""INSERT INTO produits (designation, stock_initial, stock_actuel, prix_achat, prix_vente, devise, ent_id) 
                           VALUES (?,?,?,?,?,?,?)""", 
                           (f_des.upper(), f_qte, f_qte, f_pa, f_pv, "USD", st.session_state.ent_id))
                    st.success("Article ajouté avec succès !")
                    st.rerun()

        # Affichage du Tableau de Stock
        prods = run_db("SELECT id, designation, stock_initial, stock_actuel, prix_achat, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if prods:
            df_stock = pd.DataFrame(prods, columns=["ID", "Désignation", "Initial", "Actuel", "P. Achat ($)", "P. Vente ($)"])
            st.table(df_stock)
            
            # Option de modification
            st.write("### ✏️ Mise à jour rapide")
            sel_mod = st.selectbox("Choisir un article à modifier", [p[1] for p in prods])
            p_data = [p for p in prods if p[1] == sel_mod][0]
            with st.form("edit_stock"):
                up_q = st.number_input("Nouveau Stock Actuel", value=p_data[3])
                up_v = st.number_input("Nouveau Prix de Vente", value=p_data[5])
                if st.form_submit_button("MODIFIER"):
                    run_db("UPDATE produits SET stock_actuel=?, prix_vente=? WHERE id=?", (up_q, up_v, p_data[0]))
                    st.rerun()

    # --- PAGE CAISSE ET VENTE ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.markdown("<h1>🛒 COMPTOIR DE VENTE</h1>", unsafe_allow_html=True)
            
            c_dev = st.selectbox("Devise de paiement", ["USD", "CDF"])
            c_fmt = st.selectbox("Format de Facture", ["80mm", "A4 Administrative"])
            
            p_caisse = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in p_caisse}
            
            col_sel, col_add = st.columns([3, 1])
            sel_p = col_sel.selectbox("Sélectionner un produit", ["---"] + list(p_map.keys()))
            if col_add.button("➕ AJOUTER") and sel_p != "---":
                if p_map[sel_p][1] > 0:
                    st.session_state.panier[sel_p] = st.session_state.panier.get(sel_p, 0) + 1
                    st.rerun()
                else: st.error("Stock épuisé !")
            
            if st.session_state.panier:
                st.write("### Panier Actuel")
                tot_facture = 0.0
                save_items = []
                for art, qte in list(st.session_state.panier.items()):
                    pu_base = p_map[art][0]
                    pu_final = pu_base if c_dev == "USD" else pu_base * TX_GLOBAL
                    st.write(f"**{art}** : {qte} x {pu_final:,.0f} {c_dev} = {qte*pu_final:,.0f} {c_dev}")
                    tot_facture += qte * pu_final
                    save_items.append({"art": art, "qty": qte, "pu": pu_final})
                    if st.button(f"❌ Retirer {art}", key=f"rem_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL : {tot_facture:,.2f} {c_dev}</div>", unsafe_allow_html=True)
                
                c_nom = st.text_input("Nom du Client", st.session_state.temp_client)
                c_pay = st.number_input("Montant Versé", value=float(tot_facture))
                
                if st.button("✅ VALIDER ET ÉMETTRE LA FACTURE"):
                    ref_v = f"FAC-{random.randint(10000, 99999)}"
                    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    # Enregistrement Vente
                    run_db("""INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) 
                           VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                           (ref_v, c_nom.upper(), tot_facture, c_pay, tot_facture - c_pay, c_dev, date_now, st.session_state.user, st.session_state.ent_id, json.dumps(save_items)))
                    # Gestion Dette
                    if tot_facture - c_pay > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", 
                               (c_nom.upper(), tot_facture - c_pay, c_dev, ref_v, st.session_state.ent_id))
                    # Mise à jour Stock
                    for it in save_items:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (it['qty'], it['art'], st.session_state.ent_id))
                    
                    st.session_state.last_fac = {
                        'ref': ref_v, 'cli': c_nom.upper(), 'total': tot_facture, 
                        'paye': c_pay, 'reste': tot_facture - c_pay, 'dev': c_dev, 
                        'items': save_items, 'date': date_now
                    }
                    st.session_state.panier = {}
                    st.session_state.format_fac = c_fmt
                    st.rerun()
        else:
            # --- AFFICHAGE DE LA FACTURE ADMINISTRATIVE ---
            f = st.session_state.last_fac
            info = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            st.markdown(f"""
                <div class="facture-container">
                    <h1 style="color:black;">{info[4] if info[4] else info[0]}</h1>
                    <p style="color:black;">{info[1]} | Tél: {info[2]}<br>RCCM: {info[3] if info[3] else 'En cours'}</p>
                    <hr style="border: 1px solid black;">
                    <h2 style="color:black;">FACTURE N° {f['ref']}</h2>
                    <p style="color:black; text-align:left;"><b>CLIENT :</b> {f['cli']}<br><b>DATE :</b> {f['date']}</p>
                    <table>
                        <thead>
                            <tr><th>DÉSIGNATION</th><th>QTÉ</th><th>P.U</th><th>TOTAL</th></tr>
                        </thead>
                        <tbody>
                            {" ".join([f"<tr><td>{i['art']}</td><td>{i['qty']}</td><td>{i['pu']:,.0f}</td><td>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <div style="text-align:right; margin-top:20px;">
                        <h3 style="color:black;">NET À PAYER : {f['total']:,.2f} {f['dev']}</h3>
                        <p style="color:black;">PAYÉ : {f['paye']:,.2f} | RESTE : {f['reste']:,.2f}</p>
                    </div>
                    <div class="signature-box">
                        <p>Signature de l'Établissement</p>
                        <br>
                        <p>_________________________</p>
                        <p style="font-size:12px;">Vendeur: {st.session_state.user}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            if c1.button("🖨️ IMPRIMER FACTURE"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if c2.button("📲 PARTAGER"):
                st.info("Prenez une capture d'écran pour partager sur WhatsApp.")
            if c3.button("⬅️ RETOUR CAISSE"):
                st.session_state.last_fac = None
                st.rerun()

    # --- PAGE RAPPORTS POUR LE BOSS ---
    elif st.session_state.page == "RAPPORTS":
        st.markdown("<h1>📊 RAPPORTS & ANALYSES</h1>", unsafe_allow_html=True)
        
        vts = run_db("SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if vts:
            df_v = pd.DataFrame(vts, columns=["Date", "Référence", "Client", "Montant", "Vendu par"])
            st.write("### Historique des Ventes (Traçabilité)")
            st.table(df_v) # Pour que le Boss sache quel admin/vendeur a fait la vente
            
            tot_v = df_v["Montant"].sum()
            st.markdown(f"<div class='total-frame'>TOTAL CUMULÉ : {tot_v:,.2f} $</div>", unsafe_allow_html=True)
        else:
            st.warning("Aucune vente enregistrée pour le moment.")

    # --- PAGE GESTION DES DETTES ---
    elif st.session_state.page == "DETTES":
        st.markdown("<h1>📉 SUIVI DES CRÉANCES</h1>", unsafe_allow_html=True)
        dettes_list = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        
        for d_id, d_cli, d_mt, d_dev, d_ref in dettes_list:
            with st.container(border=True):
                st.write(f"👤 **CLIENT : {d_cli}** | Facture : {d_ref}")
                st.write(f"💰 Reste à payer : **{d_mt:,.2f} {d_dev}**")
                p_pay = st.number_input(f"Montant versé", 0.0, float(d_mt), key=f"pay_{d_id}")
                if st.button(f"ENCAISSER TRANCHE", key=f"btn_{d_id}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (p_pay, d_id))
                    st.success("Paiement enregistré !")
                    st.rerun()

    # --- PAGE GESTION DES VENDEURS ---
    elif st.session_state.page == "VENDEURS":
        st.markdown("<h1>👥 GESTION DES COMPTES VENDEURS</h1>", unsafe_allow_html=True)
        with st.form("add_vendeur"):
            v_user = st.text_input("Identifiant Vendeur (Username)").lower()
            v_pass = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)",
                       (v_user, hash_pw(v_pass), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.success("Vendeur ajouté !")
                st.rerun()
        
        st.write("### Liste de vos Vendeurs")
        vendeurs = run_db("SELECT username, status FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True)
        for v_u, v_s in vendeurs:
            st.write(f"🔹 {v_u} | Statut : {v_s}")

    # --- PAGE PARAMÈTRES BOUTIQUE ---
    elif st.session_state.page == "REGLAGES":
        st.markdown("<h1>⚙️ RÉGLAGES DE LA BOUTIQUE</h1>", unsafe_allow_html=True)
        info = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        with st.form("edit_ent_form"):
            st.write("### Modifier les informations de la Facture")
            n_nom = st.text_input("Nom de l'Enseigne", info[0])
            n_head = st.text_input("En-tête Personnalisé (Slogan/Titre)", info[4])
            n_adr = st.text_input("Adresse Physique", info[1])
            n_tel = st.text_input("Téléphone", info[2])
            n_rccm = st.text_input("RCCM / ID Nat", info[3])
            
            st.divider()
            st.write("### Sécurité du compte Boss")
            n_pass = st.text_input("Nouveau Mot de passe (Laisser vide pour ne pas changer)", type="password")
            
            if st.form_submit_button("SAUVEGARDER LES MODIFICATIONS"):
                run_db("""UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=?, header_custom=? 
                       WHERE ent_id=?", (n_nom.upper(), n_adr, n_tel, n_rccm, n_head, st.session_state.ent_id))
                if n_pass:
                    run_db("UPDATE users SET password=? WHERE username=?", (hash_pw(n_pass), st.session_state.user))
                st.success("✅ Paramètres mis à jour !")
                st.rerun()
        
        st.divider()
        if st.button("🔴 RÉINITIALISER TOUTES LES DONNÉES (ATTENTION)"):
            run_db("DELETE FROM ventes WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM dettes WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM produits WHERE ent_id=?", (st.session_state.ent_id,))
            st.error("Toutes les données de votre boutique ont été effacées.")
            time.sleep(2); st.rerun()

# Fin du code v2033
