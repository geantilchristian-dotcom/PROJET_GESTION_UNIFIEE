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
# 1. CONFIGURATION SYSTÈME & CORE ENGINE
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP v410", layout="wide", initial_sidebar_state="collapsed")

# Initialisation du State
for key, val in {
    'auth': False, 'user': "", 'role': "", 'ent_id': "", 
    'page': "ACCUEIL", 'panier': {}, 'last_fac': None
}.items():
    if key not in st.session_state: st.session_state[key] = val

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_cloud_master.db', timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        if "already exists" not in str(e): st.error(f"DB Error: {e}")
        return []

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. INITIALISATION DES TABLES (SCHÉMA COMPLET v410)
# ==============================================================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, photo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS config (ent_id TEXT PRIMARY KEY, nom_ent TEXT, adresse TEXT, tel TEXT, taux REAL, message TEXT, status TEXT DEFAULT 'ACTIF', entete_fac TEXT, logo BLOB)")
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT, historique TEXT)")

    # Admin Central par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, ?, ?)", 
               ("admin", make_hashes("admin123"), "SUPER_ADMIN", "SYSTEM"))
        run_db("INSERT INTO config (ent_id, nom_ent, status, taux, message) VALUES (?, ?, ?, ?, ?)", 
               ('SYSTEM', 'BALIKA CLOUD', 'ACTIF', 2850.0, 'Bienvenue sur Balika Cloud v410'))

init_db()

# ==============================================================================
# 3. DESIGN RESPONSIVE & COULEURS
# ==============================================================================
# Récupération des données de l'entité
if st.session_state.auth:
    res = run_db("SELECT nom_ent, message, taux, adresse, tel, entete_fac, status, photo FROM config JOIN users ON config.ent_id = users.ent_id WHERE users.username=?", (st.session_state.user,), fetch=True)
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS, U_PHOTO = res[0] if res else ("BALIKA", "Prêt", 2850.0, "", "", "", "ACTIF", None)
else:
    C_NOM, C_MSG, C_TX, C_ADR, C_TEL, C_ENTETE, C_STATUS, U_PHOTO = "BALIKA CLOUD", "Gérez votre business", 2850.0, "", "", "", "ACTIF", None

st.markdown(f"""
    <style>
    /* Global Centering & Mobile Optimisation */
    .stApp {{ text-align: center !important; }}
    .stMarkdown, p, h1, h2, h3, label {{ text-align: center !important; font-family: 'Segoe UI', sans-serif; }}
    
    /* Barre Défilante Noire Texte Orange */
    .marquee-container {{
        width: 100%; overflow: hidden; background: #000; color: #FF8C00;
        padding: 10px 0; position: fixed; top: 0; left: 0; z-index: 9999;
    }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marq 20s linear infinite; font-weight: bold; }}
    @keyframes marq {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Boutons Balika Gradient */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 50px; width: 100%; font-weight: bold; border:none;
    }}
    
    /* Panier & Cadre Total */
    .total-frame {{
        border: 3px solid #FF8C00; background: #FFF3E0; padding: 20px;
        border-radius: 15px; font-size: 26px; color: #E65100; font-weight: 900; margin: 20px 0;
    }}
    
    /* Style Facture 80mm */
    .ticket {{ width: 300px; background: white; color: black; padding: 10px; margin: auto; border: 1px solid #000; font-family: monospace; font-size: 12px; }}
    </style>
    <div class="marquee-container"><div class="marquee-text">🏢 {C_NOM} | 💹 TAUX : 1 USD = {C_TX} CDF | {C_MSG}</div></div>
    <div style="margin-top: 80px;"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. SYSTÈME DE CONNEXION (CENTRÉ)
# ==============================================================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.title("CONNEXION")
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role, ent_id FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                st.rerun()
            else: st.error("Échec de connexion")
    st.stop()

# Sécurité SaaS (Pause)
if C_STATUS == "PAUSE" and st.session_state.role != "SUPER_ADMIN":
    st.warning("⚠️ Compte suspendu. Contactez l'administrateur.")
    st.stop()

ENT_ID, ROLE, USER = st.session_state.ent_id, st.session_state.role, st.session_state.user

# ==============================================================================
# 5. NAVIGATION SIDEBAR
# ==============================================================================
with st.sidebar:
    if U_PHOTO: st.image(U_PHOTO, width=100)
    st.markdown(f"### {USER.upper()}")
    st.write(f"🏢 {C_NOM}")
    st.write("---")
    if ROLE == "SUPER_ADMIN": menu = ["🌍 ABONNÉS", "⚙️ MON PROFIL"]
    elif ROLE == "ADMIN": menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📦 STOCK", "👥 VENDEURS", "📊 RAPPORTS", "⚙️ CONFIG"]
    else: menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    
    for m in menu:
        if st.button(m, use_container_width=True):
            st.session_state.page = m.split()[-1]; st.rerun()
    st.write("---")
    if st.button("🚪 QUITTER", type="primary"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. LOGIQUE CAISSE (MULTIDEVISE + MOBILE)
# ==============================================================================
if st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 CAISSE")
        devise_v = st.radio("Vendre en :", ["USD", "CDF"], horizontal=True)
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise FROM produits WHERE ent_id=? AND stock_actuel > 0", (ENT_ID,), fetch=True)
        p_dict = {r[0]: {'px': r[1], 'stk': r[2], 'dv': r[3]} for r in prods}
        
        choix = st.selectbox("Article", ["---"] + list(p_dict.keys()))
        if st.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1; st.rerun()

        if st.session_state.panier:
            total_v = 0.0; items_f = []
            for art, qte in list(st.session_state.panier.items()):
                p_base = p_dict[art]['px']
                d_base = p_dict[art]['dv']
                
                # Conversion auto
                if d_base == "USD" and devise_v == "CDF": p_conv = p_base * C_TX
                elif d_base == "CDF" and devise_v == "USD": p_conv = p_base / C_TX
                else: p_conv = p_base
                
                stot = p_conv * qte
                total_v += stot
                items_f.append({"art": art, "qte": qte, "pu": p_conv, "st": stot})
                
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{art}**")
                st.session_state.panier[art] = c2.number_input("Qté", 1, p_dict[art]['stk'], value=qte, key=f"v_{art}")
                if c3.button("❌", key=f"rm_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-frame">TOTAL : {total_v:,.2f} {devise_v}</div>', unsafe_allow_html=True)
            
            cl = st.text_input("CLIENT", "COMPTANT").upper()
            paye = st.number_input("VERSÉ", value=float(total_v))
            reste = total_v - paye

            if st.button("💾 VALIDER LA VENTE"):
                ref = f"FAC-{random.randint(100, 999)}"
                dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", (ref, cl, total_v, paye, reste, devise_v, dt, USER, ENT_ID, json.dumps(items_f)))
                if reste > 0: run_db("INSERT INTO dettes VALUES (NULL,?,?,?,?,?,?)", (cl, reste, devise_v, ref, ENT_ID, json.dumps([{"date": dt, "paye": paye}])))
                for i in items_f: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation=? AND ent_id=?", (i['qte'], i['art'], ENT_ID))
                st.session_state.last_fac = {"ref": ref, "cl": cl, "tot": total_v, "pay": paye, "dev": devise_v, "items": items_f, "date": dt}
                st.session_state.panier = {}; st.rerun()
    else:
        # Facture 80mm
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        st.markdown(f"""<div class="ticket"><h3>{C_NOM}</h3><p>{C_ENTETE}<br>Tél: {C_TEL}</p><hr><p align="left">REF: {f['ref']}<br>Client: {f['cl']}<br>Date: {f['date']}</p><table style="width:100%"><tr><th>Art</th><th>Q</th><th>T</th></tr>{"".join([f"<tr><td>{i['art']}</td><td>{i['qte']}</td><td>{i['st']:,.0f}</td></tr>" for i in f['items']])}</table><hr><h3 align="right">TOTAL: {f['tot']:,.0f} {f['dev']}</h3><p align="right">Payé: {f['pay']} | Reste: {f['tot']-f['pay']}</p></div>""", unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ==============================================================================
# 7. LOGIQUE STOCK (MODIFIER PRIX / SUPPRIMER)
# ==============================================================================
elif st.session_state.page == "STOCK":
    st.header("📦 STOCK")
    with st.expander("➕ NOUVEAU PRODUIT"):
        with st.form("np"):
            c1, c2, c3, c4 = st.columns([3,1,1,1])
            na = c1.text_input("Article")
            nq = c2.number_input("Qte", 1)
            np = c3.number_input("Prix")
            nd = c4.selectbox("Devise", ["USD", "CDF"])
            if st.form_submit_button("AJOUTER"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (na.upper(), nq, np, nd, ENT_ID)); st.rerun()

    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise FROM produits WHERE ent_id=?", (ENT_ID,), fetch=True)
    for pid, pnom, pstk, ppx, pdv in prods:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"**{pnom}**")
            col2.write(f"Stock: {pstk}")
            npx = col3.number_input("Prix", value=float(ppx), key=f"px_{pid}")
            if npx != ppx:
                if col3.button("MAJ", key=f"up_{pid}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (npx, pid)); st.rerun()
            if col4.button("🗑️", key=f"del_{pid}"): run_db("DELETE FROM produits WHERE id=?", (pid,)); st.rerun()

# ==============================================================================
# 8. CONFIGURATION & PROFIL (PHOTO, PASSWORD, INFOS)
# ==============================================================================
elif st.session_state.page == "CONFIG" or st.session_state.page == "PROFIL":
    st.header("⚙️ PARAMÈTRES")
    
    with st.expander("👤 MON COMPTE (Photo & Sécurité)"):
        up_img = st.file_uploader("Photo de profil", type=['png', 'jpg'])
        up_pass = st.text_input("Nouveau mot de passe", type="password")
        if st.button("METTRE À JOUR MON PROFIL"):
            if up_img: 
                img_byte = up_img.getvalue()
                run_db("UPDATE users SET photo=? WHERE username=?", (img_byte, USER))
            if up_pass:
                run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(up_pass), USER))
            st.success("Profil actualisé !"); st.rerun()

    if ROLE == "ADMIN":
        with st.expander("🏢 ENTREPRISE (Nom, Taux, En-tête)"):
            with st.form("f_ent"):
                e_nom = st.text_input("Nom Business", C_NOM)
                e_msg = st.text_input("Message Défilant", C_MSG)
                e_tx = st.number_input("Taux de change", value=float(C_TX))
                e_tel = st.text_input("Téléphone", C_TEL)
                e_adr = st.text_input("Adresse", C_ADR)
                e_hdr = st.text_area("En-tête Facture (RCCM...)", C_ENTETE)
                if st.form_submit_button("SAUVEGARDER CONFIG"):
                    run_db("UPDATE config SET nom_ent=?, message=?, taux=?, tel=?, adresse=?, entete_fac=? WHERE ent_id=?", 
                           (e_nom.upper(), e_msg, e_tx, e_tel, e_adr, e_hdr, ENT_ID)); st.rerun()

# ==============================================================================
# 9. DETTES (PAIEMENT PAR TRANCHES)
# ==============================================================================
elif st.session_state.page == "DETTES":
    st.header("📉 DETTES")
    dts = run_db("SELECT id, client, montant, devise, ref_v, historique FROM dettes WHERE ent_id=? AND montant > 0", (ENT_ID,), fetch=True)
    if not dts: st.success("Aucune dette")
    for did, dcl, dmt, ddv, drf, dhi in dts:
        with st.expander(f"Dette {dcl} : {dmt:,.2f} {ddv}"):
            pay = st.number_input("Montant à payer", 0.0, float(dmt), key=f"p_{did}")
            if st.button("Valider Tranche", key=f"b_{did}"):
                nm = dmt - pay
                hist = json.loads(dhi); hist.append({"date": datetime.now().strftime("%d/%m"), "paye": pay})
                if nm <= 0: run_db("DELETE FROM dettes WHERE id=?", (did,))
                else: run_db("UPDATE dettes SET montant=?, historique=? WHERE id=?", (nm, json.dumps(hist), did))
                run_db("UPDATE ventes SET paye=paye+?, reste=reste-? WHERE ref=? AND ent_id=?", (pay, pay, drf, ENT_ID))
                st.rerun()

elif st.session_state.page == "ACCUEIL":
    st.title(C_NOM)
    st.write(f"Bonjour **{USER.upper()}**")
    st.metric("Taux du Jour", f"1 USD = {C_TX} CDF")
    st.write(f"Nous sommes le {datetime.now().strftime('%d/%m/%Y')}")

elif st.session_state.page == "VENDEURS":
    st.header("👥 VENDEURS")
    with st.form("sv"):
        vu = st.text_input("Identifiant Vendeur").lower()
        vp = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?, ?, 'VENDEUR', ?)", (vu, make_hashes(vp), ENT_ID)); st.rerun()

elif st.session_state.page == "RAPPORTS":
    st.header("📊 RAPPORTS")
    data = run_db("SELECT date_v, ref, client, total, paye, reste, devise, vendeur FROM ventes WHERE ent_id=?", (ENT_ID,), fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Payé", "Reste", "Devise", "Vendeur"]), use_container_width=True)
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
