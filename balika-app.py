# ==============================================================================
# ANASH ERP - VERSION v2900 (INTÉGRALE & SÉCURISÉE)
# DÉVELOPPÉ POUR : BALIKA BUSINESS
# CONTRÔLE : ADMIN & GÉRANT & VENDEUR
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import random

# ------------------------------------------------------------------------------
# 1. DESIGN & INTERFACE (TEXTE BLANC SUR BLEU + MOBILE OPTIMIZED)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v2900", layout="wide", initial_sidebar_state="expanded")

def apply_styles_v2900():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Poppins:wght@400;600&display=swap');

    /* Fond Royal Cobalt */
    .stApp {
        background: radial-gradient(circle at center, #0033aa 0%, #001133 100%) !important;
        background-attachment: fixed !important;
        color: white !important;
        font-family: 'Poppins', sans-serif;
    }

    /* Message Défilant Fixe en Haut */
    .top-marquee {
        position: fixed; top: 0; left: 0; width: 100%; background: #000;
        color: #00ff00; z-index: 99999; height: 35px; line-height: 35px;
        font-weight: bold; border-bottom: 2px solid white; font-size: 15px;
    }

    /* Horloge 80mm style Smartphone */
    .hero-box {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px); border-radius: 40px; padding: 60px 20px;
        text-align: center; border: 2px solid rgba(255, 255, 255, 0.2);
        margin: 50px auto; max-width: 800px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.5);
    }
    .big-time {
        font-family: 'Orbitron', sans-serif; font-size: 100px; font-weight: 900;
        color: #ffffff !important; text-shadow: 0 0 20px #00ccff; line-height: 1;
    }
    .big-date { font-size: 24px; color: #00ccff; letter-spacing: 4px; margin-top: 10px; }

    /* TEXTE BLANC SUR FOND BLEU (Cards) */
    .info-card {
        background: #0044ff !important; 
        color: white !important;
        padding: 25px; border-radius: 20px; 
        border: 1px solid rgba(255,255,255,0.4);
        margin-bottom: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .info-card h1, .info-card h2, .info-card h3, .info-card p, .info-card b {
        color: white !important;
    }

    /* Cadre de Total Coloré (Panier) */
    .total-container {
        background: #000; 
        color: #00ff00 !important; 
        padding: 30px; border-radius: 20px;
        border: 6px solid #00ff00; 
        text-align: center; 
        font-size: 45px;
        font-weight: 900; 
        margin: 25px 0; 
        font-family: 'Orbitron', sans-serif;
        box-shadow: 0 0 20px rgba(0,255,0,0.3);
    }

    /* Boutons Tactiles XXL */
    .stButton>button {
        width: 100% !important; height: 75px !important; border-radius: 20px !important;
        background: linear-gradient(135deg, #0088ff, #0044bb) !important;
        color: white !important; font-size: 20px !important; font-weight: bold !important;
        border: 2px solid white !important;
        text-transform: uppercase;
    }

    /* Inputs pour Mobile */
    input, select, textarea {
        background-color: white !important; color: black !important;
        border-radius: 12px !important; height: 50px !important;
    }

    /* Sidebar Design */
    [data-testid="stSidebar"] { background-color: #ffffff !important; }
    [data-testid="stSidebar"] * { color: #000 !important; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE BASE DE DONNÉES SQLITE
# ------------------------------------------------------------------------------
DB_NAME = "anash_v2900_master.db"

def run_db(sql, params=(), fetch=True):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def setup_system():
    # Table des Utilisateurs
    run_db("""CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, owner TEXT, 
        status TEXT DEFAULT 'ACTIF', name TEXT, tel TEXT)""", fetch=False)
    
    # Table des Boutiques
    run_db("""CREATE TABLE IF NOT EXISTS shops (
        id TEXT PRIMARY KEY, name TEXT, owner TEXT, 
        rate REAL DEFAULT 2800.0, header TEXT, address TEXT, tel TEXT)""", fetch=False)
    
    # Table Stock
    run_db("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, 
        qte INTEGER, p_achat REAL, p_vente REAL, shop_id TEXT)""", fetch=False)
    
    # Table Ventes
    run_db("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, 
        total REAL, paye REAL, reste REAL, date TEXT, time TEXT, 
        seller TEXT, shop_id TEXT, details TEXT)""", fetch=False)
    
    # Table Dettes
    run_db("""CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, 
        balance REAL, ref TEXT, shop_id TEXT, status TEXT DEFAULT 'OUVERT')""", fetch=False)
    
    # Configuration (Marquee)
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, marquee TEXT)", fetch=False)

    # Initialisation Admin (admin / admin123)
    if not run_db("SELECT uid FROM users WHERE uid='admin'"):
        run_db("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
              ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000'), fetch=False)
    
    # Message défilant par défaut
    if not run_db("SELECT * FROM config"):
        run_db("INSERT INTO config VALUES (1, 'BIENVENUE SUR ANASH ERP v2900 - VOTRE SYSTÈME DE GESTION PROFESSIONNEL')", fetch=False)

setup_system()
marquee_text = run_db("SELECT marquee FROM config WHERE id=1")[0][0]

# ------------------------------------------------------------------------------
# 3. GESTION DES SESSIONS
# ------------------------------------------------------------------------------
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': None, 'role': None, 
        'active_shop': None, 'panier': {}, 'ticket': None
    })

apply_styles_v2900()
st.markdown(f'<div class="top-marquee"><marquee scrollamount="7">{marquee_text}</marquee></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION (ACCÈS RÉPARÉ)
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1.8, 1])
    
    with login_col:
        st.markdown("<div class='hero-box'><h1 style='color:white;'>ANASH ERP</h1></div>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 CONNEXION", "📝 S'INSCRIRE"])
        
        with tab_log:
            u_input = st.text_input("Identifiant").lower().strip()
            p_input = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU SYSTÈME"):
                user_res = run_db("SELECT pwd, role, owner, status FROM users WHERE uid=?", (u_input,))
                if user_res and hashlib.sha256(p_input.encode()).hexdigest() == user_res[0][0]:
                    if user_res[0][3] == "EN_ATTENTE":
                        st.warning("⏳ Compte en attente de validation.")
                    elif user_res[0][3] == "BLOQUE":
                        st.error("🚫 Accès suspendu.")
                    else:
                        st.session_state.auth = True
                        st.session_state.user = u_input
                        st.session_state.role = user_res[0][1]
                        # Charger la boutique par défaut
                        if user_res[0][1] == "GERANT":
                            btqs = run_db("SELECT id FROM shops WHERE owner=?", (u_input,))
                            if btqs: st.session_state.active_shop = btqs[0][0]
                        elif user_res[0][1] == "VENDEUR":
                            st.session_state.active_shop = user_res[0][2]
                        st.success("Connexion réussie !")
                        time.sleep(1)
                        st.rerun()
                else: st.error("❌ Identifiants invalides.")

        with tab_reg:
            with st.form("reg_form"):
                st.info("Tout compte gérant doit être validé par l'admin.")
                r_uid = st.text_input("Identifiant souhaité").lower()
                r_name = st.text_input("Nom Complet")
                r_tel = st.text_input("Téléphone")
                r_pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("CRÉER MON COMPTE GÉRANT"):
                    if run_db("SELECT uid FROM users WHERE uid=?", (r_uid,)):
                        st.error("Identifiant déjà utilisé.")
                    else:
                        run_db("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                              (r_uid, hashlib.sha256(r_pwd.encode()).hexdigest(), 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', r_name, r_tel), fetch=False)
                        st.success("✅ Inscription réussie ! Attendez l'activation.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE SUPER ADMIN (PANEL DE VALIDATION)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.title("💎 ADMIN PANEL")
    adm_choice = st.sidebar.radio("Navigation", ["Validation Comptes", "Message Défilant", "Déconnexion"])
    
    if adm_choice == "Validation Comptes":
        st.header("👥 GESTION DES UTILISATEURS")
        users = run_db("SELECT uid, name, tel, status FROM users WHERE role='GERANT'")
        for u, n, t, s in users:
            with st.container():
                st.markdown(f"""<div class='info-card'>
                    <h3>{n} (@{u})</h3>
                    <p>Téléphone: {t} | Statut: <b>{s}</b></p>
                </div>""", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ ACTIVER", key=f"ok_{u}"):
                    run_db("UPDATE users SET status='ACTIF', owner=? WHERE uid=?", (u, u), fetch=False)
                    st.rerun()
                if c2.button("⏸️ BLOQUER", key=f"bl_{u}"):
                    run_db("UPDATE users SET status='BLOQUE' WHERE uid=?", (u,), fetch=False)
                    st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"dl_{u}"):
                    run_db("DELETE FROM users WHERE uid=?", (u,), fetch=False)
                    st.rerun()

    elif adm_choice == "Message Défilant":
        st.header("📢 ÉDITER LE MESSAGE")
        new_marq = st.text_area("Texte du message", marquee_text)
        if st.button("ENREGISTRER LE MESSAGE"):
            run_db("UPDATE config SET marquee=? WHERE id=1", (new_marq,), fetch=False)
            st.rerun()

    if adm_choice == "Déconnexion": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. ESPACE GÉRANT & VENDEUR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div style='background:#0044ff; color:white; padding:15px; border-radius:15px;'>🏪 {st.session_state.active_shop if st.session_state.active_shop else 'ANASH'}<br>👤 {st.session_state.user.upper()}</div>", unsafe_allow_html=True)
    
    if st.session_state.role == "GERANT":
        my_shops = run_db("SELECT id, name FROM shops WHERE owner=?", (st.session_state.user,))
        if my_shops:
            shop_map = {s[1]: s[0] for s in my_shops}
            shop_sel = st.selectbox("Changer Boutique", list(shop_map.keys()))
            st.session_state.active_shop = shop_map[shop_sel]
        
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK PAR ID", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
    else:
        # Vendeurs ne voient que ça
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]
    
    choice = st.radio("MENU", menu)

# Charger infos boutique
info = run_db("SELECT name, rate, header, address, tel FROM shops WHERE id=?", (st.session_state.active_shop,))
if not info:
    if st.session_state.role == "GERANT":
        st.warning("Veuillez créer votre boutique dans RÉGLAGES.")
        choice = "⚙️ RÉGLAGES"
    else: st.error("Accès non configuré."); st.stop()
else: info = info[0]

# --- 6.1 ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='hero-box'>
        <div class='big-time'>{datetime.now().strftime('%H:%M')}</div>
        <div class='big-date'>{datetime.now().strftime('%A, %d %B %Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Résumé blanc sur bleu
    auj = datetime.now().strftime("%d/%m/%Y")
    recette = run_db("SELECT SUM(total) FROM sales WHERE shop_id=? AND date=?", (st.session_state.active_shop, auj))[0][0] or 0
    st.markdown(f"<div class='info-card'><h2 style='text-align:center;'>RECETTE DU JOUR : {recette:,.2f} $</h2></div>", unsafe_allow_html=True)

# --- 6.2 CAISSE TACTILE ---
elif choice == "🛒 CAISSE":
    if not st.session_state.ticket:
        st.header("🛒 VENTE")
        devise = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        taux = info[1]
        
        # Liste articles
        art_list = run_db("SELECT item, p_vente, qte FROM stock WHERE shop_id=?", (st.session_state.active_shop,))
        art_map = {a[0]: (a[1], a[2]) for a in art_list}
        
        sel_art = st.selectbox("🔎 Chercher Article", ["---"] + list(art_map.keys()))
        if sel_art != "---":
            if art_map[sel_art][1] > 0:
                st.session_state.panier[sel_art] = st.session_state.panier.get(sel_art, 0) + 1
                st.toast(f"Ajouté : {sel_art}")
            else: st.error("Stock épuisé !")

        if st.session_state.panier:
            st.divider()
            total_v = 0.0; details_v = []
            for n, q in list(st.session_state.panier.items()):
                p_unit = art_map[n][0] if devise == "USD" else art_map[n][0] * taux
                sous_t = p_unit * q
                total_v += sous_t
                details_v.append({"nom": n, "qte": q, "prix": p_unit, "st": sous_t})
                
                st.markdown(f"<div style='background:white; color:black; padding:10px; border-radius:10px; margin-bottom:5px;'><b>{n}</b> | {q} x {p_unit:,.0f} = {sous_t:,.0f} {devise}</div>", unsafe_allow_html=True)
                if st.button(f"Supprimer {n}"): del st.session_state.panier[n]; st.rerun()

            # CADRE TOTAL COLORÉ
            st.markdown(f"<div class='total-container'>TOTAL : {total_v:,.2f} {devise}</div>", unsafe_allow_html=True)
            
            client = st.text_input("Client", "COMPTANT").upper()
            verse = st.number_input(f"Montant Reçu ({devise})", value=float(total_v))
            reste = total_v - verse
            
            if st.button("🚀 VALIDER LA VENTE"):
                ref_v = f"FAC-{random.randint(1000,9999)}"
                dv, hv = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                
                # Conversion USD pour BD
                t_usd = total_v if devise == "USD" else total_v / taux
                p_usd = verse if devise == "USD" else verse / taux
                r_usd = reste if devise == "USD" else reste / taux
                
                run_db("""INSERT INTO sales (ref, client, total, paye, reste, date, time, seller, shop_id, details) 
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (ref_v, client, t_usd, p_usd, r_usd, dv, hv, st.session_state.user, st.session_state.active_shop, json.dumps(details_v)), fetch=False)
                
                for i in details_v:
                    run_db("UPDATE stock SET qte = qte - ? WHERE item=? AND shop_id=?", (i['qte'], i['nom'], st.session_state.active_shop), fetch=False)
                
                if r_usd > 0:
                    run_db("INSERT INTO debts (client, balance, ref, shop_id) VALUES (?,?,?,?)", (client, r_usd, ref_v, st.session_state.active_shop), fetch=False)
                
                st.session_state.ticket = {"ref": ref_v, "cli": client, "tot": total_v, "pay": verse, "res": reste, "dev": devise, "items": details_v, "d": dv, "h": hv}
                st.session_state.panier = {}; st.rerun()
    else:
        # TICKET DE CAISSE
        tk = st.session_state.ticket
        st.markdown(f"""
        <div style='background:white; color:black; padding:25px; border-radius:10px; font-family:monospace;'>
            <h2 style='text-align:center;'>{info[2] if info[2] else info[0]}</h2>
            <p style='text-align:center;'>{info[3]}<br>{info[4]}</p>
            <hr>
            <p>REF: {tk['ref']} | {tk['d']} {tk['h']}</p>
            {"".join([f"<p>{x['nom']} x{x['qte']} : {x['st']:,.0f} {tk['dev']}</p>" for x in tk['items']])}
            <hr>
            <h3>TOTAL: {tk['tot']:,.2f} {tk['dev']}</h3>
            <p>REÇU: {tk['pay']:,.2f} | RESTE: {tk['res']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ NOUVELLE VENTE"): st.session_state.ticket = None; st.rerun()

# --- 6.3 STOCK PAR ID ---
elif choice == "📦 STOCK PAR ID":
    st.header("📦 INVENTAIRE")
    t_inv, t_maj = st.tabs(["LISTE ARTICLES", "AJOUTER / MODIFIER"])
    with t_inv:
        stk = run_db("SELECT id, item, qte, p_vente FROM stock WHERE shop_id=?", (st.session_state.active_shop,))
        for i, a, q, p in stk:
            st.markdown(f"<div class='info-card'>ID: {i} | <b>{a}</b> | Qte: {q} | Prix: {p} $</div>", unsafe_allow_html=True)
        
        st.divider()
        del_id = st.number_input("ID à supprimer", 0)
        if st.button("SUPPRIMER L'ARTICLE"):
            run_db("DELETE FROM stock WHERE id=? AND shop_id=?", (del_id, st.session_state.active_shop), fetch=False)
            st.rerun()
            
    with t_maj:
        with st.form("form_stk"):
            mode = st.radio("Action", ["Nouveau", "Modifier via ID"])
            f_id = st.number_input("ID (si modification)", 0)
            f_art = st.text_input("Désignation")
            f_qte = st.number_input("Quantité en stock", 0)
            f_pa = st.number_input("Prix d'Achat ($)")
            f_pv = st.number_input("Prix de Vente ($)")
            if st.form_submit_button("VALIDER L'ARTICLE"):
                if mode == "Nouveau":
                    run_db("INSERT INTO stock (item, qte, p_achat, p_vente, shop_id) VALUES (?,?,?,?,?)", (f_art.upper(), f_qte, f_pa, f_pv, st.session_state.active_shop), fetch=False)
                else:
                    run_db("UPDATE stock SET item=?, qte=?, p_achat=?, p_vente=? WHERE id=? AND shop_id=?", (f_art.upper(), f_qte, f_pa, f_pv, f_id, st.session_state.active_shop), fetch=False)
                st.rerun()

# --- 6.4 DETTES ---
elif choice == "📉 DETTES":
    st.header("📉 CLIENTS DÉBITEURS")
    dettes = run_db("SELECT id, client, balance, ref FROM debts WHERE shop_id=? AND status='OUVERT'", (st.session_state.active_shop,))
    if not dettes: st.success("Aucune dette !")
    for d_id, d_cli, d_bal, d_ref in dettes:
        with st.container():
            st.markdown(f"<div class='info-card'><h3>{d_cli}</h3><p>Reste: {d_bal:,.2f} $ (Ref: {d_ref})</p></div>", unsafe_allow_html=True)
            v_pay = st.number_input(f"Verser pour {d_cli}", 0.0, float(d_bal), key=f"v_{d_id}")
            if st.button(f"ENCAISSER", key=f"b_{d_id}"):
                new_bal = d_bal - v_pay
                if new_bal <= 0:
                    run_db("UPDATE debts SET balance=0, status='PAYE' WHERE id=?", (d_id,), fetch=False)
                else:
                    run_db("UPDATE debts SET balance=? WHERE id=?", (new_bal, d_id), fetch=False)
                st.rerun()

# --- 6.5 ÉQUIPE ---
elif choice == "👥 ÉQUIPE":
    st.header("👥 MES VENDEURS")
    with st.form("v_form"):
        v_u = st.text_input("Identifiant Vendeur").lower()
        v_p = st.text_input("Mot de passe", type="password")
        v_n = st.text_input("Nom Complet")
        if st.form_submit_button("CRÉER LE COMPTE"):
            run_db("INSERT INTO users (uid, pwd, role, owner, status, name) VALUES (?,?,?,?,?,?)",
                  (v_u, hashlib.sha256(v_p.encode()).hexdigest(), 'VENDEUR', st.session_state.active_shop, 'ACTIF', v_n), fetch=False)
            st.rerun()
    
    st.subheader("Liste de l'Équipe")
    team = run_db("SELECT uid, name FROM users WHERE owner=? AND role='VENDEUR'", (st.session_state.active_shop,))
    for tu, tn in team:
        st.write(f"👤 {tn} (@{tu})")
        if st.button(f"Supprimer {tu}"):
            run_db("DELETE FROM users WHERE uid=?", (tu,), fetch=False); st.rerun()

# --- 6.6 RÉGLAGES ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ MA BOUTIQUE")
    with st.expander("➕ CRÉER UNE NOUVELLE BOUTIQUE"):
        with st.form("new_sh"):
            ns_id = st.text_input("ID Boutique (ex: boutique1)").lower()
            ns_nm = st.text_input("Nom Enseigne")
            if st.form_submit_button("LANCER LA BOUTIQUE"):
                run_db("INSERT INTO shops (id, name, owner) VALUES (?,?,?)", (ns_id, ns_nm, st.session_state.user), fetch=False)
                st.session_state.active_shop = ns_id; st.rerun()
    
    st.divider()
    with st.form("edit_sh"):
        st.subheader("Configuration Boutique")
        e_n = st.text_input("Nom Enseigne", info[0])
        e_t = st.number_input("Taux de change (CDF/USD)", info[1])
        e_h = st.text_input("En-tête Facture", info[2])
        e_a = st.text_input("Adresse", info[3])
        e_l = st.text_input("Téléphone", info[4])
        if st.form_submit_button("METTRE À JOUR"):
            run_db("UPDATE shops SET name=?, rate=?, header=?, address=?, tel=? WHERE id=?", (e_n, e_t, e_h, e_a, e_l, st.session_state.active_shop), fetch=False)
            st.rerun()

elif choice == "📊 RAPPORTS":
    st.header("📊 VENTES RÉCENTES")
    filt_d = st.date_input("Date", datetime.now()).strftime("%d/%m/%Y")
    logs = run_db("SELECT time, ref, client, total, seller FROM sales WHERE shop_id=? AND date=? ORDER BY id DESC", (st.session_state.active_shop, filt_d))
    for t, r, c, tot, sel in logs:
        st.markdown(f"<div class='info-card'>{t} | {r} | <b>{tot:,.2f} $</b> | Cli: {c} | Par: {sel}</div>", unsafe_allow_html=True)

elif choice == "🚪 QUITTER":
    st.session_state.auth = False; st.rerun()
