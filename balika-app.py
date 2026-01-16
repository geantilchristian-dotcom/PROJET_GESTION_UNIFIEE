import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME (v257)
# ==========================================
st.set_page_config(page_title="BALIKA ERP v257", layout="wide", initial_sidebar_state="collapsed")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'panier' not in st.session_state: st.session_state.panier = {} 
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'last_fac' not in st.session_state: st.session_state.last_fac = None
if 'role' not in st.session_state: st.session_state.role = "VENDEUR"
if 'user' not in st.session_state: st.session_state.user = ""

def run_db(query, params=(), fetch=False):
    with sqlite3.connect('anash_data.db', timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 2. INITIALISATION ET SÉCURITÉ DB
# ==========================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL, devise_origine TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, total_val REAL, acompte REAL, reste REAL, details TEXT, devise TEXT, date_v TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, montant_du REAL, devise TEXT, articles TEXT, sale_ref TEXT, date_d TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, email TEXT, rccm TEXT, idnat TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    
    # Mise à jour des colonnes si existantes
    cols = [c[1] for c in run_db("PRAGMA table_info(config)", fetch=True)]
    for col in ['email', 'rccm', 'idnat']:
        if col not in cols: run_db(f"ALTER TABLE config ADD COLUMN {col} TEXT DEFAULT '---'")

    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES ('admin', ?, 'ADMIN')", (make_hashes("admin123"),))
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'VOTRE ADRESSE', '000', 'info@mail.com', '000', '000', 2850.0, 'Bienvenue dans notre système de gestion')")

init_db()
cfg_res = run_db("SELECT entreprise, message, taux, adresse, telephone, email, rccm, idnat FROM config WHERE id=1", fetch=True)[0]
C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL, C_MAIL, C_RCCM, C_IDN = cfg_res

# ==========================================
# 3. DESIGN MOBILE & ANTI-DARK MODE (FORCÉ)
# ==========================================
st.markdown(f"""
    <style>
    :root {{ color-scheme: light !important; }}
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}
    
    /* Inputs et Selectbox visibles sur iPhone */
    input, select, textarea, div[data-baseweb="select"] > div {{
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border: 2px solid #FF8C00 !important;
        opacity: 1 !important;
    }}

    h1, h2, h3, label, p, span, b {{ color: #000000 !important; font-weight: bold !important; }}

    /* Boutons Orange Stylisés */
    .stButton>button {{
        background: linear-gradient(135deg, #FF8C00, #FF4500) !important;
        color: white !important; border-radius: 12px; height: 50px; border: none; font-weight: bold; width: 100%;
    }}

    .total-box {{
        border: 4px solid #FF8C00; background: #FFF3E0; padding: 20px; border-radius: 15px;
        text-align: center; font-size: 24px; font-weight: bold; color: #E65100 !important;
    }}

    /* Message Défilant Permanent */
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00; padding: 10px 0; position: fixed; top: 0; z-index: 9999; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; font-size: 18px; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Factures */
    .fac-80 {{ width: 80mm; margin: auto; padding: 10px; border: 1px dashed #000; background: white; color: black; text-align: center; }}
    .fac-a4 {{ width: 100%; padding: 25px; border: 2px solid #000; background: white; color: black; }}
    .signature-area {{ margin-top: 40px; display: flex; justify-content: space-between; font-weight: bold; padding-top: 20px; }}
    
    @media print {{ .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }} }}
    </style>
    <div class="marquee-container"><div class="marquee-text">📢 {C_MSG} | {C_ENT} à votre service</div></div>
    <div style="margin-top: 60px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. ÉCRAN LOGIN / INSCRIPTION
# ==========================================
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔑 CONNEXION", "📝 S'INSCRIRE"])
    
    with tab1:
        st.markdown(f"<h1 style='text-align:center;'>{C_ENT}</h1>", unsafe_allow_html=True)
        u_log = st.text_input("Identifiant", key="log_u").lower().strip()
        p_log = st.text_input("Mot de passe", type="password", key="log_p").strip()
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u_log,), fetch=True)
            if res and make_hashes(p_log) == res[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u_log, res[0][1]
                st.rerun()
            else: st.error("Identifiants incorrects.")

    with tab2:
        st.markdown("### Créer un nouveau compte")
        new_u = st.text_input("Choisir un Identifiant").lower().strip()
        new_p = st.text_input("Choisir un Mot de passe", type="password").strip()
        confirm_p = st.text_input("Confirmer le mot de passe", type="password").strip()
        if st.button("CRÉER MON COMPTE"):
            if new_u and new_p == confirm_p:
                if run_db("SELECT * FROM users WHERE username=?", (new_u,), fetch=True):
                    st.warning("Cet identifiant existe déjà.")
                else:
                    run_db("INSERT INTO users VALUES (?,?,?)", (new_u, make_hashes(new_p), "VENDEUR"))
                    st.success("Compte créé avec succès ! Connectez-vous maintenant.")
            else: st.error("Les mots de passe ne correspondent pas.")
    st.stop()

# ==========================================
# 5. NAVIGATION SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    btns = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        btns.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 USERS": "USERS", "⚙️ CONFIG": "CONFIG"})
    for n, p_id in btns.items():
        if st.button(n, use_container_width=True): st.session_state.page = p_id; st.rerun()
    st.write("---")
    if st.button("🚪 SE DÉCONNECTER"): st.session_state.auth = False; st.rerun()

# ==========================================
# 6. LOGIQUE DES PAGES
# ==========================================

if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div style="border:5px solid #FF8C00; border-radius:50%; width:180px; height:180px; display:flex; flex-direction:column; justify-content:center; background:#FFF3E0;"><h1>{datetime.now().strftime("%H:%M")}</h1><p>{datetime.now().strftime("%d/%m/%Y")}</p></div></center>', unsafe_allow_html=True)
    v = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if v:
        df = pd.DataFrame(v, columns=["T", "D"])
        c1, c2 = st.columns(2)
        c1.metric("RECETTE USD", f"{df[df['D']=='USD']['T'].sum():,.2f} $")
        c2.metric("RECETTE CDF", f"{df[df['D']=='CDF']['T'].sum():,.0f} FC")

elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse")
        dev = st.radio("Monnaie de Vente", ["USD", "CDF"], horizontal=True)
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        p_map = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
        
        sel = st.selectbox("Sélectionner un Article", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER AU PANIER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            tot = 0.0; rows = []
            for art, qte in list(st.session_state.panier.items()):
                pb = p_map[art]['p']
                pf = pb * C_TAUX if p_map[art]['d'] == "USD" and dev == "CDF" else (pb / C_TAUX if p_map[art]['d'] == "CDF" and dev == "USD" else pb)
                tot += (pf * qte); rows.append({'art': art, 'qte': qte, 'pu': pf, 'st': pf*qte})
                c1, c2 = st.columns([3, 1])
                new_q = c1.number_input(f"{art} ({pf:,.0f} {dev})", 1, p_map[art]['s'], value=qte, key=f"q_{art}")
                st.session_state.panier[art] = new_q
                if c2.button("🗑️", key=f"d_{art}"): del st.session_state.panier[art]; st.rerun()
            
            st.markdown(f'<div class="total-box">TOTAL À PAYER : {tot:,.2f} {dev}</div>', unsafe_allow_html=True)
            nom = st.text_input("NOM DU CLIENT").upper()
            pay = st.number_input("MONTANT REÇU (ACOMPTE)", 0.0)
            fmt = st.selectbox("FORMAT DE FACTURE", ["Ticket (80mm)", "Administratif (A4)"])
            
            if st.button("✅ VALIDER LA VENTE") and nom:
                ref = f"FAC-{random.randint(1000,9999)}"; now = datetime.now().strftime("%d/%m/%Y %H:%M")
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", (ref, nom, tot, pay, tot-pay, str(rows), dev, now))
                if tot-pay > 0: run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)", (nom, tot-pay, dev, f"{len(rows)} articles", ref, now))
                for r in rows: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (r['qte'], r['art']))
                st.session_state.last_fac = {"ref": ref, "cl": nom, "tot": tot, "ac": pay, "re": tot-pay, "dev": dev, "lines": rows, "date": now, "fmt": fmt}
                st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({"last_fac": None}))
        h_lines = "".join([f"<tr><td>{l['art']}</td><td align='center'>x{l['qte']}</td><td align='right'>{l['st']:,.0f}</td></tr>" for l in f['lines']])

        if f['fmt'] == "Ticket (80mm)":
            st.markdown(f'<div class="fac-80"><h3>{C_ENT}</h3><p>{C_ADR}<br>{C_TEL}</p><hr><p align="left">N°: {f["ref"]}<br>Client: {f["cl"]}<br>{f["date"]}</p><hr><table style="width:100%">{h_lines}</table><hr><h4>TOTAL: {f["tot"]:,.0f} {f["dev"]}</h4><p>Payé: {f["ac"]} | Reste: {f["re"]}</p><div class="signature-area"><span>Client</span><span>Vendeur</span></div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="fac-a4"><div style="display:flex; justify-content:space-between"><div><h1>{C_ENT}</h1><p>{C_ADR}<br>Tél: {C_TEL}<br>Email: {C_MAIL}<br>RCCM: {C_RCCM} | IDNAT: {C_IDN}</p></div><div style="text-align:right"><h2>FACTURE</h2><p>N° {f["ref"]}<br>{f["date"]}</p></div></div><hr><b>CLIENT : {f["cl"]}</b><table style="width:100%; border-collapse:collapse; margin-top:15px"><tr style="background:#EEE"><th style="border:1px solid #000; padding:10px">Description</th><th style="border:1px solid #000">Qté</th><th style="border:1px solid #000">P.U</th><th style="border:1px solid #000">Total</th></tr>{h_lines.replace("<td>", "<td style=\'border:1px solid #000; padding:10px\'>")}</table><h3 style="text-align:right; margin-top:20px">NET À PAYER : {f["tot"]:,.2f} {f["dev"]}</h3><div class="signature-area"><span>Signature du Client</span><span>Cachet et Signature {C_ENT}</span></div></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        c2.markdown(f'<a href="whatsapp://send?text=Facture {C_ENT} - Client: {f["cl"]} - Montant: {f["tot"]} {f["dev"]}" style="text-decoration:none;"><button style="width:100%; height:50px; background:#25D366; color:white; border:none; border-radius:10px; font-weight:bold;">📲 ENVOYER PAR WHATSAPP</button></a>', unsafe_allow_html=True)

elif st.session_state.page == "STOCK":
    st.title("📦 Inventaire des Articles")
    with st.form("add_prod"):
        c1, c2 = st.columns(2)
        nm = c1.text_input("Désignation de l'article")
        pr = c2.number_input("Prix de vente")
        dv = st.selectbox("Devise d'origine", ["USD", "CDF"])
        qt = st.number_input("Quantité en stock", 1)
        if st.form_submit_button("ENREGISTRER L'ARTICLE"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (nm.upper(), qt, qt, pr, dv)); st.rerun()
    
    st.write("---")
    for r in run_db("SELECT * FROM produits", fetch=True):
        with st.expander(f"📦 {r[1]} - {r[3]} restants"):
            np = st.number_input("Changer le prix", value=float(r[4]), key=f"p_{r[0]}")
            if st.button("Mettre à jour", key=f"s_{r[0]}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (np, r[0])); st.rerun()
            if st.button("🗑️ Supprimer", key=f"del_{r[0]}"): run_db("DELETE FROM produits WHERE id=?", (r[0],)); st.rerun()

elif st.session_state.page == "DETTES":
    st.title("📉 Suivi des Dettes")
    dts = run_db("SELECT * FROM dettes", fetch=True)
    if not dts: st.success("Aucun crédit en cours.")
    for d in dts:
        st.warning(f"**Client: {d[1]}** | Montant restant : {d[2]:,.2f} {d[3]}")
        v = st.number_input("Montant versé", 0.0, float(d[2]), key=f"v_{d[0]}")
        if st.button(f"Valider paiement {d[1]}", key=f"b_{d[0]}"):
            if d[2]-v <= 0.05: run_db("DELETE FROM dettes WHERE id=?", (d[0],))
            else: run_db("UPDATE dettes SET montant_du=montant_du-? WHERE id=?", (v, d[0]))
            run_db("UPDATE ventes SET reste=reste-? WHERE ref=?", (v, d[5])); st.rerun()

elif st.session_state.page == "RAPPORT":
    st.title("📊 Journal de l'Entreprise")
    data = run_db("SELECT date_v, ref, client_nom, total_val, devise, reste FROM ventes ORDER BY id DESC", fetch=True)
    if data:
        st.dataframe(pd.DataFrame(data, columns=["Date", "Référence", "Client", "Total", "Devise", "Dette"]), use_container_width=True)
        st.button("🖨️ IMPRIMER LE JOURNAL", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres Généraux")
    with st.expander("🔑 SÉCURITÉ"):
        npw = st.text_input("Changer mon mot de passe", type="password")
        if st.button("CONFIRMER LE NOUVEAU MOT DE PASSE"):
            run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(npw), st.session_state.user)); st.success("Modifié !")
            
    with st.form("config_form"):
        ent = st.text_input("NOM DE L'ENTREPRISE", C_ENT)
        adr = st.text_input("ADRESSE", C_ADR); tel = st.text_input("TÉLÉPHONE", C_TEL)
        eml = st.text_input("EMAIL", C_MAIL); rcm = st.text_input("RCCM", C_RCCM); idn = st.text_input("ID NATIONAL", C_IDN)
        txc = st.number_input("TAUX DE CHANGE (1 USD = ? CDF)", value=C_TAUX)
        msg = st.text_area("MESSAGE DÉFILANT", C_MSG)
        if st.form_submit_button("ENREGISTRER TOUTES LES MODIFICATIONS"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, email=?, rccm=?, idnat=?, taux=?, message=? WHERE id=1", (ent.upper(), adr, tel, eml, rcm, idn, txc, msg))
            st.rerun()
    if os.path.exists("anash_data.db"):
        with open("anash_data.db", "rb") as f: st.download_button("📥 TÉLÉCHARGER LA BASE DE DONNÉES (BACKUP)", f, file_name="backup_erp.db")

elif st.session_state.page == "USERS":
    st.title("👥 Gestion du Personnel")
    for u in run_db("SELECT username, role FROM users", fetch=True):
        st.write(f"👤 **{u[0].upper()}** ({u[1]})")
        if u[0] != 'admin' and st.button(f"Supprimer {u[0]}", key=u[0]):
            run_db("DELETE FROM users WHERE username=?", (u[0],)); st.rerun()
