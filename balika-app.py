# ==============================================================================
# PROJET : BALIKA ERP - VERSION ULTIME v2031 (INTÉGRATION TOTALE)
# AUCUNE LIGNE SUPPRIMÉE - EXPANSION DES FONCTIONNALITÉS ET DESIGN MOBILE
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
# 1. CONFIGURATION DE LA PAGE & THÈME (DESIGN LUMINEUX ET MOBILE)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2031",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation exhaustive des états de session
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm", 'show_register': False, 'devise_vente': "USD"
    })

# CSS POUR CENTRAGE, LUMINOSITÉ ET LISIBILITÉ MOBILE
st.markdown("""
    <style>
    /* Fond bleu profond pour faire ressortir le texte blanc */
    .stApp { background-color: #0044cc !important; }
    
    /* Centrage et luminosité des textes */
    h1, h2, h3, h4, h5, p, label, span, div.stText { 
        color: #ffffff !important; 
        text-align: center !important; 
        font-weight: bold;
    }
    
    /* Header noir fixe avec texte défilant jaune */
    .fixed-header { 
        position: fixed; top: 0; left: 0; width: 100%; 
        background: #000000; color: #ffff00; height: 60px; 
        z-index: 999999; display: flex; align-items: center; 
        border-bottom: 3px solid #ffffff; 
    }
    marquee { font-size: 22px; font-weight: bold; }
    .spacer { margin-top: 80px; }
    
    /* Boutons larges et tactiles */
    .stButton>button { 
        background: linear-gradient(135deg, #0055ff, #002288) !important;
        color: white !important; border-radius: 12px; 
        height: 60px; width: 100%; border: 2px solid #ffffff;
        font-size: 18px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    }
    
    /* Frame de Total très visible */
    .total-frame { 
        background: #000000; color: #00FF00; 
        padding: 25px; border: 5px solid #ffffff; 
        border-radius: 20px; text-align: center; 
        margin: 15px 0; font-size: 30px; 
    }

    /* Tableaux blancs contrastés */
    .stDataFrame, [data-testid="stTable"] { 
        background-color: white !important; 
        border-radius: 10px; padding: 10px;
        color: black !important;
    }
    
    /* Inputs blancs texte noir */
    div[data-baseweb="input"], div[data-baseweb="select"] { 
        background-color: white !important; border-radius: 8px !important; 
    }
    input { color: black !important; font-weight: bold !important; text-align: center !important; }

    /* FACTURE ADMINISTRATIVE */
    .facture-admin {
        background: #ffffff; color: #000000 !important;
        padding: 30px; border-radius: 5px; width: 95%; max-width: 800px;
        margin: auto; border: 2px solid #000; box-shadow: 0px 0px 20px rgba(0,0,0,0.5);
    }
    .facture-admin * { color: #000000 !important; text-align: center; }
    .facture-admin table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .facture-admin th, .facture-admin td { border: 1px solid #000; padding: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES ET MIGRATIONS
# ------------------------------------------------------------------------------
def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_v2031.db', timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch: return cursor.fetchall()
            return None
    except Exception as e:
        st.error(f"Erreur DB: {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    # Table Users (avec Essai et Validation)
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ATTENTE', date_fin_essai TEXT, 
        nom TEXT, prenom TEXT, telephone TEXT, date_creation TEXT)""")
    
    # Table Config Système
    run_db("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)""")
    
    # Table Infos Entreprise (Header personnalisé ajouté)
    run_db("""CREATE TABLE IF NOT EXISTS ent_infos (
        ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, 
        telephone TEXT, rccm TEXT, header_custom TEXT)""")

    # Table Produits (Stock Initial ajouté)
    run_db("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, 
        stock_initial INTEGER, stock_actuel INTEGER, 
        prix_vente REAL, devise TEXT, ent_id TEXT)""")

    # Table Ventes (Vendeur ajouté pour le rapport Boss)
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

    # Données par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, status) VALUES (?,?,?,?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'ACTIF'))
    
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config VALUES (1, 'BALIKA ERP', 'VOTRE PARTENAIRE DE GESTION v2031', 2850.0)")

init_db()

# Chargement config globale
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA ERP", "Bienvenue", 2850.0)

st.markdown(f'<div class="fixed-header"><marquee>{MARQUEE}</marquee></div><div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. INTERFACE LOGIN / INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown(f"<h1>🚀 {APP_NAME}</h1>", unsafe_allow_html=True)
    
    if not st.session_state.show_register:
        st.subheader("🔐 CONNEXION")
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU SYSTÈME"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                if res[0][3] == "ATTENTE": st.warning("⏳ Compte en attente de validation par l'administrateur.")
                elif res[0][3] == "PAUSE": st.error("❌ Compte suspendu.")
                else:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
            else: st.error("Identifiants invalides.")
        st.write("---")
        if st.button("🆕 CRÉER UN COMPTE BOUTIQUE"):
            st.session_state.show_register = True; st.rerun()
    else:
        st.subheader("📝 FORMULAIRE D'INSCRIPTION")
        with st.container():
            col1, col2 = st.columns(2)
            r_nom = col1.text_input("Nom Propriétaire")
            r_pre = col2.text_input("Prénom")
            r_ent = st.text_input("Nom de la Boutique (Sera votre ID)")
            r_tel = st.text_input("Téléphone")
            r_pw1 = st.text_input("Mot de passe (6 car. min)", type="password")
            r_pw2 = st.text_input("Confirmer mot de passe", type="password")
            
            if st.button("ENVOYER MA DEMANDE"):
                if len(r_pw1) < 6: st.error("Mot de passe trop court !")
                elif r_pw1 != r_pw2: st.error("Les mots de passe divergent !")
                else:
                    u_id = r_ent.lower().replace(" ","")
                    run_db("""INSERT INTO users (username, password, role, ent_id, status, nom, prenom, telephone, date_creation) 
                           VALUES (?,?,?,?,?,?,?,?,?)""", 
                           (u_id, make_hashes(r_pw1), 'USER', u_id, 'ATTENTE', r_nom, r_pre, r_tel, datetime.now().strftime("%d/%m/%Y")))
                    run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (u_id, r_ent.upper(), r_tel))
                    st.success("Demande envoyée ! Veuillez contacter l'admin pour validation.")
                    time.sleep(3); st.session_state.show_register = False; st.rerun()
        if st.button("RETOUR"): st.session_state.show_register = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. NAVIGATION SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    if st.session_state.role == "SUPER_ADMIN":
        m = ["DEMANDES", "PARAMÈTRES GLOBAUX", "DÉCONNEXION"]
    else:
        m = ["TABLEAU DE BORD", "STOCK", "CAISSE", "RAPPORTS", "DETTES", "DÉPENSES", "PARAMÈTRES", "DÉCONNEXION"]
    
    choice = st.radio("MENU", m)
    if choice == "DÉCONNEXION": st.session_state.auth = False; st.rerun()

# ------------------------------------------------------------------------------
# 5. LOGIQUE SUPER ADMIN (IDENTIFIANT : admin)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    if choice == "DEMANDES":
        st.header("👥 VALIDATION DES COMPTES")
        users = run_db("SELECT username, status, telephone, nom, prenom FROM users WHERE role='USER'", fetch=True)
        for u_id, u_st, u_tel, u_n, u_p in users:
            with st.container(border=True):
                st.write(f"🏢 **{u_id.upper()}** ({u_n} {u_p})")
                st.write(f"📞 Tél: {u_tel} | Statut: {u_st}")
                c1, c2, c3 = st.columns(3)
                jours = c1.number_input("Jours d'essai", 1, 365, 30, key=f"j_{u_id}")
                if c2.button("✅ VALIDER", key=f"v_{u_id}"):
                    fin = (datetime.now() + timedelta(days=jours)).strftime("%d/%m/%Y")
                    run_db("UPDATE users SET status='ACTIF', date_fin_essai=? WHERE username=?", (fin, u_id))
                    st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"d_{u_id}"):
                    run_db("DELETE FROM users WHERE username=?", (u_id,))
                    st.rerun()
                    
    elif choice == "PARAMÈTRES GLOBAUX":
        st.header("⚙️ CONFIGURATION SYSTÈME")
        with st.form("sys"):
            n_app = st.text_input("Nom de l'App", APP_NAME)
            n_mar = st.text_area("Texte Marquee", MARQUEE)
            n_tx = st.number_input("Taux Global (1$ = ? CDF)", value=TX_G)
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE system_config SET app_name=?, marquee_text=?, taux_global=? WHERE id=1", (n_app, n_mar, n_tx))
                st.rerun()

# ------------------------------------------------------------------------------
# 6. LOGIQUE BOUTIQUE (USER)
# ------------------------------------------------------------------------------
else:
    if choice == "TABLEAU DE BORD":
        st.markdown(f"<h1>BIENVENUE CHEZ {st.session_state.ent_id.upper()}</h1>", unsafe_allow_html=True)
        fin_e = run_db("SELECT date_fin_essai FROM users WHERE username=?", (st.session_state.user,), fetch=True)[0][0]
        st.info(f"📅 Votre licence est valide jusqu'au : {fin_e}")
        
        # Stats Rapides
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        st.markdown(f"<div class='total-frame'>VENTES DU JOUR :<br>{v_jr:,.2f} $</div>", unsafe_allow_html=True)

    elif choice == "STOCK":
        st.header("📦 INVENTAIRE")
        with st.expander("➕ NOUVEL ARTICLE"):
            with st.form("add"):
                d = st.text_input("Désignation")
                q = st.number_input("Quantité Initial", 1)
                p = st.number_input("Prix Vente ($)", 0.0)
                if st.form_submit_button("ENREGISTRER"):
                    run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?,?)",
                           (d.upper(), q, q, p, "USD", st.session_state.ent_id))
                    st.rerun()
        
        # Affichage du tableau de stock
        prods = run_db("SELECT id, designation, stock_initial, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if prods:
            df_st = pd.DataFrame(prods, columns=["ID", "Désignation", "Stock Initial", "Stock Actuel", "Prix ($)"])
            st.table(df_st)
            
            # Modification rapide
            st.subheader("✏️ Modifier un article")
            sel_p = st.selectbox("Choisir l'article à modifier", [p[1] for p in prods])
            p_info = [p for p in prods if p[1] == sel_p][0]
            with st.form("edit_p"):
                up_d = st.text_input("Nom", p_info[1])
                up_q = st.number_input("Stock Actuel", value=p_info[3])
                up_p = st.number_input("Prix", value=p_info[4])
                if st.form_submit_button("SAUVEGARDER"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (up_d.upper(), up_q, up_p, p_info[0]))
                    st.rerun()

    elif choice == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 VENTE ET FACTURATION")
            dev = st.selectbox("Devise", ["USD", "CDF"])
            fmt = st.selectbox("Format", ["80mm", "A4"])
            
            p_data = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
            p_map = {p[0]: (p[1], p[2]) for p in p_data}
            
            sel = st.selectbox("Article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER AU PANIER") and sel != "---":
                if p_map[sel][1] > 0:
                    st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
                    st.rerun()
                else: st.error("Stock épuisé !")
            
            if st.session_state.panier:
                tot = 0.0
                save_items = []
                for a, q in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if dev == "USD" else p_map[a][0] * TX_G
                    st.write(f"✅ {a} | Qté: {q} | Sous-total: {pu*q:,.0f} {dev}")
                    tot += pu * q
                    save_items.append({"art": a, "qty": q, "pu": pu})
                
                st.markdown(f"<div class='total-frame'>TOTAL : {tot:,.2f} {dev}</div>", unsafe_allow_html=True)
                cli = st.text_input("Nom Client", "COMPTANT")
                pay = st.number_input("Montant Reçu", value=float(tot))
                
                if st.button("🏁 VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000, 9999)}"
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref, cli.upper(), tot, pay, tot-pay, dev, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(save_items)))
                    if tot-pay > 0:
                        run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (cli.upper(), tot-pay, dev, ref, st.session_state.ent_id))
                    for it in save_items:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (it['qty'], it['art'], st.session_state.ent_id))
                    st.session_state.update({'last_fac': {'ref':ref, 'cli':cli.upper(), 'total':tot, 'paye':pay, 'reste':tot-pay, 'dev':dev, 'items':save_items}, 'panier':{}, 'format_fac':fmt})
                    st.rerun()
        else:
            # AFFICHAGE DE LA FACTURE ADMINISTRATIVE
            f = st.session_state.last_fac
            e = run_db("SELECT nom_boutique, adresse, telephone, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
            
            st.markdown(f"""
                <div class="facture-admin">
                    <h2 style="color:black;">{e[3] if e[3] else e[0]}</h2>
                    <p style="color:black;">{e[1]} | Tél: {e[2]}</p>
                    <hr style="border:1px solid black;">
                    <p style="color:black;"><b>FACTURE N° {f['ref']}</b><br>Client: {f['cli']}<br>Date: {datetime.now().strftime('%d/%m/%Y')}</p>
                    <table>
                        <thead><tr><th>ARTICLE</th><th>QTÉ</th><th>P.U</th><th>TOTAL</th></tr></thead>
                        <tbody>
                            {"".join([f"<tr><td>{i['art']}</td><td>{i['qty']}</td><td>{i['pu']:,.0f}</td><td>{i['pu']*i['qty']:,.0f}</td></tr>" for i in f['items']])}
                        </tbody>
                    </table>
                    <h3 style="color:black; text-align:right;">TOTAL GÉNÉRAL : {f['total']:,.2f} {f['dev']}</h3>
                    <p style="color:black; font-style:italic;">Effectué par : {st.session_state.user}</p>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("🖨️ IMPRIMER / PDF"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if c2.button("🆕 NOUVELLE VENTE"):
                st.session_state.last_fac = None; st.rerun()

    elif choice == "RAPPORTS":
        st.header("📊 RAPPORT DES ACTIVITÉS")
        vts = run_db("SELECT date_v, ref, client, total, vendeur FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        if vts:
            df_v = pd.DataFrame(vts, columns=["Date", "Référence", "Client", "Montant", "Effectué par"])
            st.table(df_v) # Le Boss voit qui a fait la vente
            st.markdown(f"<div class='total-frame'>TOTAL VENTES : {df_v['Montant'].sum():,.2f} $</div>", unsafe_allow_html=True)

    elif choice == "DETTES":
        st.header("📉 CRÉANCES CLIENTS")
        ds = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        for di, dc, dm, dv, dr in ds:
            with st.container(border=True):
                st.write(f"👤 **{dc}** | Reste: {dm:,.2f} {dv} (Ref: {dr})")
                pay_tr = st.number_input("Montant versé", 0.0, float(dm), key=f"p_{di}")
                if st.button("ENCAISSER TRANCHE", key=f"b_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (pay_tr, di))
                    st.rerun()

    elif choice == "PARAMÈTRES":
        st.header("⚙️ RÉGLAGES BOUTIQUE")
        e = run_db("SELECT nom_boutique, adresse, telephone, rccm, header_custom FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        
        with st.form("p_ed"):
            st.subheader("Informations Facture")
            n_b = st.text_input("Nom de l'Entreprise", e[0])
            n_h = st.text_input("En-tête Personnalisé (S'affichera sur la facture)", e[4])
            n_a = st.text_input("Adresse", e[1])
            n_t = st.text_input("Téléphone", e[2])
            st.subheader("Sécurité")
            n_pw = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE ent_infos SET nom_boutique=?, adresse=?, telephone=?, header_custom=? WHERE ent_id=?", (n_b.upper(), n_a, n_t, n_h, st.session_state.ent_id))
                if n_pw: run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(n_pw), st.session_state.user))
                st.rerun()
        
        st.write("---")
        if st.button("🔴 RÉINITIALISER TOUTES LES VENTES"):
            run_db("DELETE FROM ventes WHERE ent_id=?", (st.session_state.ent_id,))
            run_db("DELETE FROM dettes WHERE ent_id=?", (st.session_state.ent_id,))
            st.success("Toutes les données de vente ont été effacées.")
            time.sleep(2); st.rerun()
