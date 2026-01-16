import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io

# ==============================================================================
# 1. CONFIGURATION CORE & DESIGN
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP v390", layout="wide", initial_sidebar_state="collapsed")

# Initialisation de la session
for key, val in {
    'auth': False, 'user': "", 'role': "", 'ent_id': "", 
    'page': "ACCUEIL", 'panier': {}, 'last_fac': None
}.items():
    if key not in st.session_state: st.session_state[key] = val

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_cloud_v390.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        # On ne bloque pas l'app pour une erreur de colonne déjà existante
        if "already exists" not in str(e):
            st.error(f"Erreur Système : {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION & REPARATION AUTO (CORRIGE LES ERREURS BINDINGS)
# ==============================================================================
def init_db():
    # Tables de base
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, photo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS config (ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', entete_fac TEXT, logo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)")

    # Correction UNIQUE constraint : INSERT OR IGNORE
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT OR IGNORE INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ("admin", make_hashes("admin123"), "SUPER_ADMIN", "SYSTEM"))
    
    if not run_db("SELECT * FROM config WHERE ent_id='SYSTEM'", fetch=True):
        run_db("INSERT OR IGNORE INTO config (ent_id, nom_ent, status, taux, message, adresse, tel, entete_fac) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA ERP', 'ACTIF', 2850.0, 'Bienvenue', 'Direction', '000', 'ADMINISTRATION'))

init_db()

# ==============================================================================
# 3. INTERFACE VISUELLE (CENTRAGE STRICT)
# ==============================================================================
if st.session_state.auth:
    res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac FROM config WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = res[0] if res else ("BALIKA", "Prêt", 2850.0, "", "", "")
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE = "BALIKA CLOUD", "Gérez votre business", 2850.0, "", "", ""

st.markdown(f"""
    <style>
    .stApp {{ text-align: center !important; background-color: #f9f9f9; }}
    .stMarkdown, p, h1, h2, h3, label, .stButton {{ text-align: center !important; }}
    
    .marquee-container {{
        width: 100%; overflow: hidden; background: #0047AB; color: white;
        padding: 12px 0; position: fixed; top: 0; left: 0; z-index: 1000;
    }}
    .marquee-text {{
        display: inline-block; white-space: nowrap;
        animation: marquee 20s linear infinite; font-size: 18px; font-weight: bold;
    }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    .stButton>button {{
        background: linear-gradient(135deg, #0047AB, #007FFF) !important;
        color: white !important; border-radius: 12px; height: 50px; width: 100%; font-weight: bold; border:none;
    }}
    
    .card {{
        background: white; padding: 20px; border-radius: 15px; border: 1px solid #ddd; margin-bottom: 10px;
    }}

    .total-box {{
        border: 3px solid #0047AB; background: #e7efff; padding: 15px;
        border-radius: 15px; font-size: 28px; font-weight: bold; color: #0047AB; margin: 15px 0;
    }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🏢 {C_NOM} | 💹 TAUX : 1 USD = {C_TX} CDF | {C_MSG}</div></div>
    <div style="margin-top: 80px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. AUTHENTIFICATION
# ==============================================================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.title("CONNEXION")
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU SYSTÈME"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
            else: st.error("Identifiants incorrects")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. NAVIGATION SIDEBAR
# ==============================================================================
with st.sidebar:
    st.title(f"👤 {USER.upper()}")
    if ROLE == "SUPER_ADMIN": menu = ["🌍 ABONNÉS", "⚙️ MON COMPTE"]
    elif ROLE == "ADMIN": menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]; st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. LOGIQUE : CAISSE (MULTI-CURRENCY & MOBILE)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        devise_v = st.radio("Vendre en :", ["USD", "CDF"], horizontal=True)
        
        # Liste produits
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        choix = st.selectbox("Article", ["---"] + list(p_dict.keys()))
        if st.button("➕ AJOUTER AU PANIER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1; st.rerun()

        if st.session_state.panier:
            st.write("---")
            total_vente = 0.0; items_fac = []
            for art, qte in list(st.session_state.panier.items()):
                p_orig = p_dict[art]['px']
                d_orig = p_dict[art]['dv']
                
                # Conversion prix
                if d_orig == "USD" and devise_v == "CDF": p_u = p_orig * C_TX
                elif d_orig == "CDF" and devise_v == "USD": p_u = p_orig / C_TX
                else: p_u = p_orig
                
                stot = p_u * qte
                total_vente += stot
                items_fac.append({"art": art, "qte": qte, "pu": p_u, "st": stot})
                
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_dict[art]['stk'], value=qte, key=f"q_{art}")
                if c3.button("❌", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-box">TOTAL : {total_vente:,.2f} {devise_v}</div>', unsafe_allow_html=True)
            
            cl_nom = st.text_input("NOM CLIENT", "COMPTANT").upper()
            paye = st.number_input("MONTANT REÇU", value=float(total_vente))
            reste = total_vente - paye

            if st.button("💾 VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(1000, 9999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", 
                       (ref, cl_nom, total_vente, paye, reste, devise_v, dt, USER, ENT_ID, json.dumps(items_fac)))
                
                if reste > 0:
                    run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", 
                           (cl_nom, reste, devise_v, ref, ENT_ID, json.dumps([{"date": dt, "paye": paye}])))
                
                for i in items_fac:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                
                st.session_state.last_fac = {"ref": ref, "cl": cl_nom, "tot": total_vente, "pay": paye, "dev": devise_v, "items": items_fac, "date": dt}
                st.session_state.panier = {}; st.rerun()
    else:
        # FACTURE
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        html = f"""
        <div style="background:white; color:black; padding:20px; border:1px solid #000; width:100%; max-width:400px; margin:auto; font-family: monospace;">
            <h2 style="margin:0;">{C_NOM}</h2>
            <p style="font-size:11px;">{C_ENTETE}</p>
            <hr>
            <p align="left">N°: {f['ref']}<br>Client: {f['cl']}<br>Date: {f['date']}</p>
            <table style="width:100%; border-collapse:collapse; font-size:12px;">
                <tr style="border-bottom:1px solid #000;"><th>Art</th><th>Qté</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['st']:,.0f}</td></tr>" for i in f['items']])}
            </table>
            <hr>
            <h3 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            <p align="right">Payé: {f['pay']} | Reste: {f['tot']-f['pay']}</p>
            <div style="margin-top:20px; text-align:center; border:1px solid #000; padding:10px;">SCEAU & CACHET</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ==============================================================================
# 7. LOGIQUE : DETTES (PAIEMENT PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 DETTES")
    dts = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    if not dts: st.success("Aucune dette")
    for did, dcl, dmt, ddv, drf, dhi in dts:
        with st.expander(f"Dette {dcl} : {dmt:,.2f} {ddv}"):
            v_tranche = st.number_input("Verser une tranche", 0.0, float(dmt), key=f"t_{did}")
            if st.button("Valider Paiement", key=f"b_{did}"):
                n_mt = dmt - v_tranche
                h = json.loads(dhi); h.append({"date": datetime.now().strftime("%d/%m"), "paye": v_tranche})
                if n_mt <= 0: run_db("DELETE FROM dettes WHERE id=?", (did,))
                else: run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (n_mt, json.dumps(h), did))
                st.rerun()

# ==============================================================================
# 8. LOGIQUE : STOCK (MODIFIER/SUPPRIMER SANS LIGNES VIDES)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 STOCK")
    with st.expander("➕ NOUVEL ARTICLE"):
        with st.form("add_p"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            n_a = c1.text_input("Désignation")
            n_q = c2.number_input("Quantité", 1)
            n_p = c3.number_input("Prix")
            n_d = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("ENREGISTRER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", 
                       (n_a.upper(), n_q, n_p, n_d, ENT_ID)); st.rerun()
    
    items = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pid, pnom, pstk, ppx, pdv in items:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"**{pnom}**")
            col2.write(f"Stock: {pstk}")
            n_px = col3.number_input("Prix", value=float(ppx), key=f"px_{pid}")
            if n_px != ppx:
                if col3.button("MAJ", key=f"s_{pid}"):
                    run_db("UPDATE produits SET prix_vente=? WHERE id=?", (n_px, pid)); st.rerun()
            if col4.button("🗑️", key=f"d_{pid}"):
                run_db("DELETE FROM produits WHERE id=?", (pid,)); st.rerun()

# ==============================================================================
# 9. LOGIQUE : CONFIG & PROFIL (PHOTO & PASS)
# ==============================================================================
elif st.session_state.page == "CONFIG" or st.session_state.page == "COMPTE":
    st.header("⚙️ PARAMÈTRES")
    
    # Section Profil
    with st.container(border=True):
        st.subheader("👤 MON PROFIL")
        new_u = st.text_input("Nouvel Identifiant", USER)
        new_p = st.text_input("Nouveau Mot de passe (Laisser vide pour garder)", type="password")
        if st.button("SAUVEGARDER PROFIL"):
            if new_p: run_db("UPDATE users SET username=?, password=? WHERE username=?", (new_u, make_hashes(new_p), USER))
            else: run_db("UPDATE users SET username=? WHERE username=?", (new_u, USER))
            st.session_state.user = new_u
            st.success("Profil mis à jour !"); st.rerun()

    # Section Entreprise (Admin seul)
    if ROLE == "ADMIN":
        with st.container(border=True):
            st.subheader("🏢 BUSINESS")
            with st.form("cfg_ent"):
                c_n = st.text_input("Nom Entreprise", C_NOM)
                c_a = st.text_input("Adresse", C_ADR)
                c_t = st.text_input("Téléphone", C_TEL)
                c_tx = st.number_input("Taux de change", value=float(C_TX))
                c_et = st.text_area("En-tête (RCCM...)", C_ENTETE)
                c_msg = st.text_input("Message Défilant", C_MSG)
                if st.form_submit_button("APPLIQUER LES CHANGEMENTS"):
                    run_db("UPDATE config SET nom_ent=?, adresse=?, tel=?, taux=?, entete_fac=?, message=? WHERE ent_id=?", 
                           (c_n.upper(), c_a, c_t, c_tx, c_et, c_msg, ENT_ID)); st.rerun()

elif st.session_state.page == "VENDEURS":
    st.header("👥 VENDEURS")
    with st.form("nv"):
        v_u = st.text_input("Identifiant Vendeur").lower().strip()
        v_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER VENDEUR"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,'VENDEUR',?)", 
                   (v_u, make_hashes(v_p), ENT_ID)); st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 RAPPORTS")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=? ORDER BY id DESC", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Ref", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER RAPPORT"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

elif st.session_state.page == "ACCUEIL":
    st.markdown(f"<h1>{C_NOM}</h1>", unsafe_allow_html=True)
    st.write(f"Utilisateur : {USER.upper()}")
    st.write(f"Taux : 1 USD = {C_TX} CDF")
    st.write(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
