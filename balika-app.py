# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTIME v2029 (CORRECTIONS & EXPANSION)
# AUCUNE LIGNE SUPPRIMÉE - RÉPARATION DE LA BASE DE DONNÉES ET DE L'INSCRIPTION
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

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & THÈME VISUEL (DESIGN CENTRÉ)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2029 - SYSTÈME UNIFIÉ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation exhaustive des états de session
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
        'devise_vente': "USD"
    })

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES (RÉSILIENCE ET SÉCURITÉ)
# ------------------------------------------------------------------------------
def run_db(query, params=(), fetch=False):
    """Exécute les requêtes avec gestion de timeout pour éviter les blocages SQLite."""
    try:
        with sqlite3.connect('balika_master_final.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        # On ne redige pas l'erreur pour que vous puissiez voir si une colonne manque encore
        st.error(f"Erreur Base de données : {e}")
        return []

def make_hashes(password):
    """Hachage SHA-256 pour la sécurité des mots de passe."""
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------------------------------------------------------------------
# 3. INITIALISATION ET RÉPARATION AUTOMATIQUE DES COLONNES (MIGRATION)
# ------------------------------------------------------------------------------
def init_db():
    # Table Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        role TEXT, 
        ent_id TEXT, 
        status TEXT DEFAULT 'ACTIF', 
        telephone TEXT, 
        date_creation TEXT,
        nom TEXT, 
        prenom TEXT, 
        adresse_physique TEXT, 
        photo BLOB)""")
    
    # --- RÉPARATION FORCÉE DES COLONNES MANQUANTES ---
    with sqlite3.connect('balika_master_final.db') as conn:
        cursor = conn.cursor()
        # On récupère la liste des colonnes actuelles de la table users
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = [info[1] for info in cursor.fetchall()]
        
        # Si les colonnes n'existent pas, on les ajoute une par une
        if 'nom' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN nom TEXT DEFAULT ''")
        if 'prenom' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN prenom TEXT DEFAULT ''")
        if 'adresse_physique' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN adresse_physique TEXT DEFAULT ''")
        conn.commit()

    # Table Configuration Système (Admin Global)
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, 
        app_name TEXT, 
        marquee_text TEXT, 
        taux_global REAL)""")
    
    # Table Entreprises
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, 
        nom_boutique TEXT, 
        adresse TEXT, 
        telephone TEXT, 
        rccm TEXT,
        custom_app_name TEXT)""")

    # Table Produits
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        designation TEXT, 
        stock_actuel INTEGER, 
        prix_vente REAL, 
        devise TEXT, 
        ent_id TEXT)""")

    # Table Ventes
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
        details_json TEXT)""")

    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS dettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        client TEXT, 
        montant REAL, 
        devise TEXT, 
        ref_v TEXT, 
        ent_id TEXT)""")

    # Table Dépenses
    run_db("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        motif TEXT, 
        montant REAL, 
        devise TEXT, 
        date_d TEXT, 
        ent_id TEXT)""")

    # Compte SUPER ADMIN
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("""INSERT INTO users (username, password, role, ent_id, date_creation, nom, prenom) 
               VALUES (?,?,?,?,?,?,?)""", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', datetime.now().strftime("%d/%m/%Y"), "ADMIN", "SYSTEM"))
    
    # Config par défaut
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("""INSERT INTO system_config (id, app_name, marquee_text, taux_global) 
               VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR VOTRE SYSTÈME DE GESTION v2029', 2850.0)""")

init_db()

# ------------------------------------------------------------------------------
# 4. RÉCUPÉRATION DES PARAMÈTRES DYNAMIQUES
# ------------------------------------------------------------------------------
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME_GLOBAL, MARQUEE_TEXT_GLOBAL, TX_G = cfg[0] if cfg else ("BALIKA ERP", "Bienvenue", 2850.0)

# ------------------------------------------------------------------------------
# 5. STYLE CSS AVANCÉ (CENTRAGE TOTAL ET COULEURS)
# ------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FF8C00 !important; }}
    
    /* Centrage et Blanchiment du texte */
    h1, h2, h3, h4, h5, p, label, span, div.stText {{ 
        color: white !important; 
        text-align: center !important; 
        font-weight: bold;
    }}
    
    .fixed-header {{ 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #00FF00; height: 60px; 
        z-index: 999999; display: flex; align-items: center; 
        border-bottom: 3px solid #ffffff; 
    }}
    marquee {{ font-size: 24px; font-weight: bold; }}
    
    .spacer {{ margin-top: 100px; }}
    
    .stButton>button {{ 
        background-color: #0055ff !important; 
        color: white !important; 
        border-radius: 12px; 
        font-weight: bold; 
        height: 55px; 
        width: 100%; 
        border: 2px solid #ffffff;
        font-size: 18px;
    }}
    
    .total-frame {{ 
        background: #000000; color: #00FF00; 
        padding: 30px; border: 5px solid #ffffff; 
        border-radius: 25px; text-align: center; 
        margin: 20px 0; font-size: 35px; 
    }}

    /* Styles Factures */
    .fac-80mm {{ background: #ffffff; color: #000000 !important; padding: 15px; width: 300px; margin: auto; border: 1px dashed black; }}
    .fac-80mm * {{ color: #000000 !important; text-align: left !important; }}
    
    .fac-a4 {{ background: #ffffff; color: #000000 !important; padding: 40px; width: 90%; max-width: 850px; margin: auto; border: 1px solid #000; min-height: 800px; }}
    .fac-a4 * {{ color: #000000 !important; }}

    /* Inputs et Tableaux */
    div[data-baseweb="input"], div[data-baseweb="select"] {{ background-color: white !important; border-radius: 10px !important; }}
    input {{ color: black !important; font-weight: bold !important; text-align: center !important; font-size: 18px !important; }}
    
    .stDataFrame, [data-testid="stTable"] {{ 
        background-color: white !important; 
        border-radius: 10px; 
        padding: 10px;
    }}
    </style>
    
    <div class="fixed-header">
        <marquee scrollamount="12">{MARQUEE_TEXT_GLOBAL}</marquee>
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. INTERFACE DE CONNEXION / INSCRIPTION (FIX BUG INSCRIPTION)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f"<h1>🏢 {APP_NAME_GLOBAL}</h1>", unsafe_allow_html=True)
    
    if not st.session_state.show_register:
        st.markdown("### 🔐 ESPACE DE CONNEXION")
        c_u = st.text_input("Identifiant Utilisateur").lower().strip()
        c_p = st.text_input("Mot de passe", type="password")
        
        if st.button("SE CONNECTER AU TABLEAU DE BORD"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (c_u,), fetch=True)
            if res and make_hashes(c_p) == res[0][0]:
                if res[0][3] == "PAUSE":
                    st.error("❌ Compte suspendu par l'administrateur.")
                else:
                    st.session_state.update({'auth':True, 'user':c_u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
            else:
                st.error("🚫 Identifiant ou mot de passe invalide.")
        
        st.write("---")
        if st.button("✨ PAS ENCORE DE COMPTE ? CRÉER VOTRE BOUTIQUE"):
            st.session_state.show_register = True
            st.rerun()
    else:
        st.markdown("### 📝 CRÉATION DE VOTRE COMPTE")
        with st.container():
            col1, col2 = st.columns(2)
            r_nom = col1.text_input("Votre Nom de famille")
            r_pre = col2.text_input("Votre Prénom")
            r_ent = st.text_input("Nom de votre Entreprise (Sera votre ID)")
            r_tel = st.text_input("Numéro de téléphone portable")
            r_adr = st.text_input("Adresse Physique de la Boutique")
            
            p1, p2 = st.columns(2)
            r_pw1 = p1.text_input("Mot de passe (6 car. min)", type="password")
            r_pw2 = p2.text_input("Confirmation", type="password")
            
            if st.button("🚀 ENREGISTRER MON ENTREPRISE"):
                if len(r_pw1) < 6:
                    st.error("⚠️ Sécurité : Le mot de passe est trop court (min 6).")
                elif r_pw1 != r_pw2:
                    st.error("⚠️ Erreur : Les mots de passe ne sont pas identiques.")
                elif not (r_ent and r_nom and r_tel):
                    st.error("⚠️ Erreur : Veuillez remplir les informations obligatoires.")
                else:
                    # Nettoyage de l'ID entreprise
                    clean_id = r_ent.lower().replace(" ", "")
                    # Vérifier si l'ID existe déjà
                    check = run_db("SELECT username FROM users WHERE username=?", (clean_id,), fetch=True)
                    if check:
                        st.error("⚠️ Ce nom d'entreprise est déjà utilisé. Ajoutez un chiffre à la fin.")
                    else:
                        # Insertion sécurisée
                        run_db("""INSERT INTO users (username, password, role, ent_id, telephone, date_creation, nom, prenom, adresse_physique) 
                               VALUES (?,?,?,?,?,?,?,?,?)""", 
                               (clean_id, make_hashes(r_pw1), 'USER', clean_id, r_tel, datetime.now().strftime("%d/%m/%Y"), r_nom, r_pre, r_adr))
                        run_db("INSERT INTO ent_infos (ent_id, nom_boutique, adresse, telephone) VALUES (?,?,?,?)", 
                               (clean_id, r_ent.upper(), r_adr, r_tel))
                        
                        st.success(f"✅ Félicitations {r_pre} ! Connectez-vous avec l'identifiant : {clean_id}")
                        time.sleep(3)
                        st.session_state.show_register = False
                        st.rerun()
            
            if st.button("🔙 RETOUR"):
                st.session_state.show_register = False
                st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 7. NAVIGATION SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color: #00FF00;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = {"🏠 ACCUEIL": "ACCUEIL", "👥 ABONNÉS": "ABONNES", "👤 PROFIL": "PROFIL", "⚙️ PARAMÈTRES": "PARAMETRES"}
    else:
        menu = {"🏠 ACCUEIL": "ACCUEIL", "📦 STOCK": "STOCK", "🛒 CAISSE": "CAISSE", "📊 RAPPORTS": "RAPPORTS", "📉 DETTES": "DETTES", "💸 DÉPENSES": "DEPENSES", "👥 VENDEURS": "VENDEURS", "⚙️ RÉGLAGES": "REGLAGES"}
    
    for label, target in menu.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = target
            st.rerun()
            
    st.divider()
    if st.button("🚪 QUITTER", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ------------------------------------------------------------------------------
# 8. INTERFACE SUPER ADMIN (admin / admin123)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    
    if st.session_state.page == "ACCUEIL":
        st.markdown("<h1>🌟 TABLEAU DE BORD ADMINISTRATEUR</h1>", unsafe_allow_html=True)
        count = run_db("SELECT COUNT(*) FROM users WHERE role='USER'", fetch=True)[0][0]
        st.markdown(f"<div class='total-frame'>TOTAL ENTREPRISES : {count}</div>", unsafe_allow_html=True)

    elif st.session_state.page == "ABONNES":
        st.markdown("<h1>👥 GESTION DES COMPTES CLIENTS</h1>", unsafe_allow_html=True)
        # La requête inclut maintenant NOM et PRENOM sans erreur
        users = run_db("SELECT username, status, telephone, date_creation, nom, prenom FROM users WHERE role='USER'", fetch=True)
        
        for u_id, u_st, u_tel, u_dt, u_n, u_p in users:
            with st.container(border=True):
                cl1, cl2, cl3, cl4 = st.columns([2, 1, 1, 1])
                cl1.markdown(f"**{u_n} {u_p}**<br>ID: {u_id.upper()}<br>📅 {u_dt}", unsafe_allow_html=True)
                cl2.write(f"📞 {u_tel}")
                
                # PAUSE / ACTIF
                st_label = "🟢 ACTIF" if u_st == "ACTIF" else "🔴 PAUSE"
                if cl3.button(st_label, key=f"btn_st_{u_id}"):
                    run_db("UPDATE users SET status=? WHERE username=?", ("PAUSE" if u_st == "ACTIF" else "ACTIF", u_id))
                    st.rerun()
                
                # SUPPRESSION
                if cl4.button("🗑️ SUPPRIMER", key=f"btn_del_{u_id}"):
                    run_db("DELETE FROM users WHERE username=?", (u_id,))
                    run_db("DELETE FROM ent_infos WHERE ent_id=?", (u_id,))
                    st.rerun()

    elif st.session_state.page == "PROFIL":
        st.markdown("<h1>👤 MODIFIER MON ACCÈS ADMIN</h1>", unsafe_allow_html=True)
        with st.form("edit_admin"):
            new_u = st.text_input("Nouvel Identifiant", value=st.session_state.user)
            new_p = st.text_input("Nouveau Mot de passe", type="password")
            if st.form_submit_button("SAUVEGARDER"):
                if new_p:
                    run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_u.lower(), make_hashes(new_p), st.session_state.user))
                else:
                    run_db("UPDATE users SET username=? WHERE username=?", (new_u.lower(), st.session_state.user))
                st.session_state.user = new_u.lower()
                st.success("Admin mis à jour.")

    elif st.session_state.page == "PARAMETRES":
        st.markdown("<h1>⚙️ CONFIGURATION GLOBALE</h1>", unsafe_allow_html=True)
        with st.form("cfg_glob"):
            an = st.text_input("Nom de l'App", value=APP_NAME_GLOBAL)
            mt = st.text_area("Texte Marquee", value=MARQUEE_TEXT_GLOBAL)
            tx = st.number_input("Taux (1$ en CDF)", value=TX_G)
            if st.form_submit_button("APPLIQUER À TOUT LE SYSTÈME"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (an, mt, tx))
                st.success("Changements appliqués.")
                st.rerun()

# ------------------------------------------------------------------------------
# 9. INTERFACE BOUTIQUE (USER)
# ------------------------------------------------------------------------------
else:
    if st.session_state.page == "ACCUEIL":
        st.markdown(f"<h1>🏠 BIENVENUE : {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>CHIFFRE DU JOUR :<br>{v_jr:,.2f} $</div>", unsafe_allow_html=True)

    elif st.session_state.page == "STOCK":
        st.markdown("<h1>📦 MON STOCK ET PRIX</h1>", unsafe_allow_html=True)
        with st.expander("➕ AJOUTER UN ARTICLE"):
            with st.form("add_art"):
                d = st.text_input("Désignation")
                q = st.number_input("Quantité", min_value=0)
                p = st.number_input("Prix Vente ($)", min_value=0.0)
                if st.form_submit_button("VALIDER L'ARTICLE"):
                    run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (d.upper(), q, p, "USD", st.session_state.ent_id))
                    st.rerun()
        
        # Liste modifiable
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for pi, pd, ps, pp in prods:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
                n_n = c1.text_input("Nom", pd, key=f"e_n_{pi}")
                n_q = c2.number_input("Qté", value=ps, key=f"e_q_{pi}")
                n_p = c3.number_input("Prix", value=pp, key=f"e_p_{pi}")
                if c4.button("💾", key=f"upd_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (n_n.upper(), n_q, n_p, pi))
                    st.rerun()
                if c5.button("🗑️", key=f"rm_p_{pi}"):
                    run_db("DELETE FROM produits WHERE id=?", (pi,))
                    st.rerun()

    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.markdown("<h1>🛒 CAISSE EN DIRECT</h1>", unsafe_allow_html=True)
            dv = st.selectbox("Devise", ["USD", "CDF"])
            fmt = st.selectbox("Format Facture", ["80mm", "A4"])
            
            p_list = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {x[0]: (x[1], x[2]) for x in p_list}
            
            sel = st.selectbox("Sélectionner un article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                if p_map[sel][1] > 0:
                    st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
                    st.rerun()
            
            if st.session_state.panier:
                total = 0.0
                items = []
                for a, q in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if dv == "USD" else p_map[a][0] * TX_G
                    total += pu * q
                    items.append({"art": a, "qty": q, "pu": pu})
                    c1, c2, c3 = st.columns([4, 1, 1])
                    c1.write(f"**{a}** ({pu:,.0f} {dv})")
                    st.session_state.panier[a] = c2.number_input("Qté", 1, p_map[a][1], value=q, key=f"p_q_{a}")
                    if c3.button("❌", key=f"del_it_{a}"):
                        del st.session_state.panier[a]
                        st.rerun()
                
                st.markdown(f"<div class='total-frame'>TOTAL : {total:,.2f} {dv}</div>", unsafe_allow_html=True)
                cli = st.text_input("Nom Client", "COMPTANT")
                pay = st.number_input("Montant Reçu", value=float(total))
                
                if st.button("✅ CONFIRMER LA VENTE"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref, cli.upper(), total, pay, total-pay, dv, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(items)))
                    if total-pay > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cli.upper(), total-pay, dv, ref, st.session_state.ent_id))
                    for it in items:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (it['qty'], it['art'], st.session_state.ent_id))
                    st.session_state.update({'last_fac': {'ref':ref, 'cli':cli.upper(), 'total':total, 'paye':pay, 'reste':total-pay, 'dev':dv, 'items':items}, 'panier':{}, 'format_fac':fmt})
                    st.rerun()
        else:
            f = st.session_state.last_fac
            info = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            if st.session_state.format_fac == "80mm":
                st.markdown(f"<div class='fac-80mm'><h3>{info[0]}</h3><p>{info[1]}<br>Tél: {info[2]}</p><hr>REF: {f['ref']}<br>Client: {f['cli']}<hr>{''.join([f'<p>{i[ 'art']} x{i['qty']} : {i['pu']*i['qty']:,.0f}</p>' for i in f['items']])}<hr>TOTAL: {f['total']}<br>PAYÉ: {f['paye']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='fac-a4'><h1>FACTURE</h1><h3>{info[0]}</h3><p>{info[1]}<br>RCCM: {info[3]}</p><hr><p><b>CLIENT:</b> {f['cli']}<br><b>REF:</b> {f['ref']}</p><table><thead><tr><th>Article</th><th>Qté</th><th>P.U</th><th>Total</th></tr></thead><tbody>{''.join([f'<tr><td>{i['art']}</td><td>{i['qty']}</td><td>{i['pu']}</td><td>{i['pu']*i['qty']}</td></tr>' for i in f['items']])}</tbody></table><h3>TOTAL : {f['total']} {f['dev']}</h3></div>", unsafe_allow_html=True)
            if st.button("⬅️ RETOUR"): st.session_state.last_fac = None; st.rerun()

    elif st.session_state.page == "RAPPORTS":
        st.markdown("<h1>📊 ANALYSE DES CHIFFRES</h1>", unsafe_allow_html=True)
        # Calcul dynamique
        v_df = pd.DataFrame(run_db("SELECT date_v, total, paye, reste FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True), columns=['Date', 'Total', 'Payé', 'Reste'])
        d_df = pd.DataFrame(run_db("SELECT date_d, montant, motif FROM depenses WHERE ent_id=?", (st.session_state.ent_id,), fetch=True), columns=['Date', 'Montant', 'Motif'])
        
        c1, c2, c3 = st.columns(3)
        vt = v_df['Total'].sum() if not v_df.empty else 0
        dt = d_df['Montant'].sum() if not d_df.empty else 0
        c1.metric("Ventes Totales", f"{vt:,.0f} $")
        c2.metric("Dépenses Totales", f"{dt:,.0f} $")
        c3.metric("Bénéfice Brut", f"{(vt - dt):,.0f} $")
        
        st.subheader("Détails des Ventes")
        st.dataframe(v_df, use_container_width=True)

    elif st.session_state.page == "DEPENSES":
        st.markdown("<h1>💸 ENREGISTRER UNE DÉPENSE</h1>", unsafe_allow_html=True)
        with st.form("f_dep"):
            m_t = st.text_input("Motif / Raison")
            m_n = st.number_input("Montant ($)", min_value=0.0)
            if st.form_submit_button("SAUVEGARDER"):
                run_db("INSERT INTO depenses (motif, montant, devise, date_d, ent_id) VALUES (?,?,?,?,?)", (m_t, m_n, "USD", datetime.now().strftime("%d/%m/%Y"), st.session_state.ent_id))
                st.success("Dépense enregistrée !")
                st.rerun()

    elif st.session_state.page == "DETTES":
        st.markdown("<h1>📉 GESTION DES CRÉANCES</h1>", unsafe_allow_html=True)
        ds = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv, dr in ds:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                p_pay = col2.number_input("Payer", 0.0, float(dm), key=f"det_p_{di}")
                col1.markdown(f"**{dc}** | Dette: {dm:,.0f} {dv} (Ref: {dr})")
                if col2.button("ENCAISSER", key=f"det_b_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (p_pay, di))
                    st.rerun()

    elif st.session_state.page == "VENDEURS":
        st.markdown("<h1>👥 COMPTES VENDEURS</h1>", unsafe_allow_html=True)
        with st.form("add_v"):
            vu = st.text_input("Nom Vendeur").lower()
            vp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("CRÉER COMPTE VENDEUR"):
                run_db("INSERT INTO users (username, password, role, ent_id, status) VALUES (?,?,?,?,?)", (vu, make_hashes(vp), 'VENDEUR', st.session_state.ent_id, 'ACTIF'))
                st.rerun()

    elif st.session_state.page == "REGLAGES":
        st.markdown("<h1>⚙️ INFOS BOUTIQUE</h1>", unsafe_allow_html=True)
        e = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        with st.form("ed_ent"):
            en = st.text_input("Nom Enseigne", e[0]); ea = st.text_input("Adresse", e[1])
            et = st.text_input("Tél", e[2]); er = st.text_input("RCCM", e[3])
            if st.form_submit_button("METTRE À JOUR"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, rccm=? WHERE ent_id=?", (en, ea, et, er, st.session_state.ent_id))
                st.rerun()
