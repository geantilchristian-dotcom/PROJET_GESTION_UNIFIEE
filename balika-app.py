# ==============================================================================
# PROJET : BALIKA ERP - VERSION MASTER v2055
# MAINTENANCE : OPTIMISÉ POUR SMARTPHONE (CARD DESIGN)
# FONCTIONNALITÉS : STOCK, VENTES, DETTES, DÉPENSES, ADMIN, MULTI-BOUTIQUE
# ==============================================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import time
import base64

# ------------------------------------------------------------------------------
# 1. CONFIGURATION VISUELLE & CSS MOBILE-FIRST
# ------------------------------------------------------------------------------
st.set_page_config(page_title="BALIKA ERP v2055", layout="wide", initial_sidebar_state="expanded")

if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'panier': {}, 'last_fac': None, 'devise': "USD", 'show_reg': False
    })

st.markdown("""
    <style>
    /* Fond Bleu Cobalt et Texte Blanc pour un contraste maximal */
    .stApp { background-color: #0033aa !important; }
    h1, h2, h3, h4, h5, p, label, span, .stMarkdown, [data-testid="stMetricValue"] { 
        color: #ffffff !important; text-align: center !important; font-weight: bold !important; 
    }
    
    /* Message Défilant (Marquee) - Fixe en haut */
    .marquee-header { 
        position: fixed; top: 0; left: 0; width: 100%; background: #000; 
        color: #00ff00; z-index: 9999; border-bottom: 2px solid #fff; height: 50px;
        display: flex; align-items: center; font-size: 18px;
    }
    .spacer { margin-top: 65px; }
    
    /* Design des Cartes Mobile (Évite le chevauchement des tableaux) */
    .card {
        background: #ffffff; border-radius: 15px; padding: 18px;
        margin-bottom: 15px; border-left: 10px solid #00ccff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    .card p, .card h3, .card h4 { color: #111111 !important; margin: 3px 0; text-align: left !important; }
    .card b { color: #0033aa; }

    /* Boutons tactiles géants */
    .stButton>button { 
        background: linear-gradient(135deg, #00ccff, #0055ff) !important;
        color: white !important; border-radius: 15px; height: 65px; width: 100%;
        font-size: 20px; border: 2px solid #fff; margin-top: 10px; font-weight: bold;
    }
    
    /* Frame de Résultat (Bénéfice/Total) */
    .total-frame { 
        background: #000; color: #00ff00; padding: 25px; border: 4px solid #fff;
        border-radius: 20px; font-size: 32px; text-align: center; margin: 15px 0;
        box-shadow: 0px 0px 20px rgba(0,255,0,0.6);
    }

    /* Inputs lisibles */
    input, select, textarea { 
        background-color: #ffffff !important; color: #000000 !important; 
        border-radius: 10px !important; font-size: 18px !important;
    }
    div[data-baseweb="select"] > div { background-color: white !important; color: black !important; }
    
    /* Forcer l'empilement sur Mobile */
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. LOGIQUE BASE DE DONNÉES (SQLITE)
# ------------------------------------------------------------------------------
DB_FILE = "balika_master_v2055.db"

def run_db(q, p=(), fetch=False):
    with sqlite3.connect(DB_FILE, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(q, p)
        conn.commit()
        return cursor.fetchall() if fetch else None

def init_system():
    # Tables de base
    run_db("CREATE TABLE IF NOT EXISTS users (uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, ent TEXT, status TEXT DEFAULT 'ACTIF', boss TEXT, tel TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, app_name TEXT, marquee TEXT, rate REAL)")
    run_db("CREATE TABLE IF NOT EXISTS stores (ent_id TEXT PRIMARY KEY, name TEXT, addr TEXT, tel TEXT, head TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, buy REAL, sell REAL, ent TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, tot REAL, pay REAL, rest REAL, dev TEXT, dt TEXT, day TEXT, seller TEXT, ent TEXT, items TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, amt REAL, ref TEXT, day TEXT, ent TEXT, status TEXT DEFAULT 'NON PAYE')")
    run_db("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, mot TEXT, amt REAL, day TEXT, cat TEXT, ent TEXT)")

    # Seed Admin & Config
    if not run_db("SELECT * FROM users WHERE uid='admin'", fetch=True):
        run_db("INSERT INTO users VALUES (?,?,?,?,?,?,?)", ('admin', hashlib.sha256(b"admin123").hexdigest(), 'SUPER_ADMIN', 'SYSTEM', 'ACTIF', 'ADMIN', '000'))
    if not run_db("SELECT * FROM settings", fetch=True):
        run_db("INSERT INTO settings VALUES (1, 'BALIKA ERP', 'BIENVENUE DANS VOTRE ESPACE DE GESTION PROFESSIONNEL', 2850.0)")

init_system()
sys_cfg = run_db("SELECT app_name, marquee, rate FROM settings WHERE id=1", fetch=True)[0]

# Affichage du Marquee
st.markdown(f'<div class="marquee-header"><marquee scrollamount="8">{sys_cfg[1]}</marquee></div><div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. AUTHENTIFICATION & INSCRIPTION
# ------------------------------------------------------------------------------
if not st.session_state.auth:
    if not st.session_state.show_reg:
        st.markdown(f"<h1>🔐 {sys_cfg[0]}</h1>", unsafe_allow_html=True)
        with st.container():
            u_log = st.text_input("Identifiant (ID)").lower().strip()
            p_log = st.text_input("Mot de passe", type="password")
            if st.button("SE CONNECTER"):
                res = run_db("SELECT pwd, role, ent, status FROM users WHERE uid=?", (u_log,), fetch=True)
                if res and hashlib.sha256(p_log.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "PAUSE": st.error("⚠️ Compte suspendu. Contactez l'admin.")
                    else:
                        st.session_state.update({'auth':True, 'user':u_log, 'role':res[0][1], 'ent_id':res[0][2]})
                        st.rerun()
                else: st.error("❌ Identifiants invalides.")
            st.divider()
            if st.button("📩 CRÉER UNE NOUVELLE BOUTIQUE"):
                st.session_state.show_reg = True; st.rerun()
    else:
        st.markdown("<h1>📝 INSCRIPTION</h1>", unsafe_allow_html=True)
        with st.form("reg_form"):
            r_name = st.text_input("Nom de la Boutique (ex: BALIKA SHOP)").upper()
            r_boss = st.text_input("Nom du Propriétaire")
            r_tel = st.text_input("N° de Téléphone")
            r_pwd = st.text_input("Définir Mot de passe", type="password")
            if st.form_submit_button("CRÉER MON COMPTE"):
                u_id = r_name.lower().replace(" ","")
                run_db("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u_id, hashlib.sha256(r_pwd.encode()).hexdigest(), 'USER', u_id, 'ACTIF', r_boss, r_tel))
                run_db("INSERT INTO stores (ent_id, name, tel) VALUES (?,?,?)", (u_id, r_name, r_tel))
                st.success("✅ Compte créé avec succès !"); time.sleep(1); st.session_state.show_reg = False; st.rerun()
        if st.button("⬅️ RETOUR"): st.session_state.show_reg = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. ESPACE SUPER ADMIN (CONTROLE GLOBAL)
# ------------------------------------------------------------------------------
if st.session_state.role == "SUPER_ADMIN":
    st.sidebar.title("🛠️ SUPER ADMIN")
    adm_nav = st.sidebar.radio("MENU", ["BOUTIQUES", "RÉGLAGES SYSTÈME", "DÉCONNEXION"])
    
    if adm_nav == "BOUTIQUES":
        st.header("🏢 GESTION DES CLIENTS")
        clients = run_db("SELECT uid, boss, status, ent FROM users WHERE role='USER'", fetch=True)
        for u, b, s, e in clients:
            with st.container():
                st.markdown(f"<div class='card'><h3>Boutique: {e.upper()}</h3><p>Propriétaire: {b}</p><pp>Statut actuel: <b>{s}</b></p></div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ ACTIVER", key=f"act_{u}"): run_db("UPDATE users SET status='ACTIF' WHERE uid=?", (u,)); st.rerun()
                if c2.button("⏸️ PAUSE", key=f"pau_{u}"): run_db("UPDATE users SET status='PAUSE' WHERE uid=?", (u,)); st.rerun()
                if c3.button("🗑️ SUPPRIMER", key=f"del_{u}"): run_db("DELETE FROM users WHERE uid=?", (u,)); st.rerun()

    elif adm_nav == "RÉGLAGES SYSTÈME":
        st.header("⚙️ CONFIGURATION")
        with st.form("cfg"):
            new_app = st.text_input("Nom de l'Application", sys_cfg[0])
            new_mar = st.text_area("Message Défilant", sys_cfg[1])
            new_tax = st.number_input("Taux de Change (1$ en CDF)", value=sys_cfg[2])
            if st.form_submit_button("SAUVEGARDER"):
                run_db("UPDATE settings SET app_name=?, marquee=?, rate=? WHERE id=1", (new_app, new_mar, new_tax))
                st.success("Système mis à jour !"); st.rerun()

    elif adm_nav == "DÉCONNEXION": st.session_state.auth = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE UTILISATEUR (BOUTIQUE)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🏪 {st.session_state.ent_id.upper()}")
    st.markdown(f"👤 {st.session_state.user.upper()}")
    st.divider()
    if st.session_state.role == "VENDEUR":
        nav = st.radio("MENU", ["🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"])
    else:
        nav = st.radio("MENU", ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "💸 DÉPENSES", "📉 DETTES", "📊 RAPPORTS", "⚙️ RÉGLAGES", "🚪 QUITTER"])

# --- 5.1 ACCUEIL (DASHBOARD v192+) ---
if nav == "🏠 ACCUEIL":
    st.header("📊 TABLEAU DE BORD")
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Calculs Financiers
    rec_j = run_db("SELECT SUM(tot) FROM sales WHERE ent=? AND day=?", (st.session_state.ent_id, today), fetch=True)[0][0] or 0
    dep_j = run_db("SELECT SUM(amt) FROM expenses WHERE ent=? AND day=?", (st.session_state.ent_id, today), fetch=True)[0][0] or 0
    benef = rec_j - dep_j
    
    color = "#00FF00" if benef >= 0 else "#FF0000"
    st.markdown(f"<div class='total-frame' style='color:{color}; border-color:{color};'>BÉNÉFICE NET DU JOUR<br>{benef:,.2f} $</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Recettes", f"{rec_j:,.2f} $")
        low_stock = run_db("SELECT COUNT(*) FROM products WHERE ent=? AND qty < 5", (st.session_state.ent_id,), fetch=True)[0][0]
        st.metric("Alertes Stock", low_stock)
    with col2:
        st.metric("Dépenses", f"{dep_j:,.2f} $")
        dettes_total = run_db("SELECT SUM(amt) FROM debts WHERE ent=? AND status='NON PAYE'", (st.session_state.ent_id,), fetch=True)[0][0] or 0
        st.metric("Dettes Clients", f"{dettes_total:,.2f} $")

# --- 5.2 CAISSE (TERMINAL DE VENTE) ---
elif nav == "🛒 CAISSE":
    if not st.session_state.last_fac:
        st.header("🛒 VENTE RAPIDE")
        c_dev = st.selectbox("Devise de paiement", ["USD", "CDF"])
        
        # Liste produits
        stk_data = run_db("SELECT item, sell, qty FROM products WHERE ent=?", (st.session_state.ent_id,), fetch=True)
        p_map = {p[0]: (p[1], p[2]) for p in stk_data}
        
        pick = st.selectbox("🔍 Ajouter un article", ["--- Choisir ---"] + list(p_map.keys()))
        if pick != "--- Choisir ---":
            if p_map[pick][1] > 0:
                st.session_state.panier[pick] = st.session_state.panier.get(pick, 0) + 1
                st.toast(f"✅ {pick} ajouté")
            else: st.error("❌ Stock épuisé !")

        if st.session_state.panier:
            st.divider()
            t_ven = 0.0; cart_items = []
            for a, q in list(st.session_state.panier.items()):
                pu = p_map[a][0] if c_dev == "USD" else p_map[a][0] * sys_cfg[2]
                stot = pu * q
                t_ven += stot
                cart_items.append({"art": a, "qte": q, "pu": pu, "st": stot})
                
                with st.container():
                    st.markdown(f"<div class='card'><h4>{a}</h4><p>Qté: <b>{q}</b> | Sous-total: <b>{stot:,.0f} {c_dev}</b></p></div>", unsafe_allow_html=True)
                    if st.button(f"Enlever {a}", key=f"rm_{a}"):
                        del st.session_state.panier[a]; st.rerun()

            st.markdown(f"<div class='total-frame'>TOTAL : {t_ven:,.2f} {c_dev}</div>", unsafe_allow_html=True)
            
            with st.container(border=True):
                cli_n = st.text_input("Nom du Client", "COMPTANT")
                pay_n = st.number_input(f"Montant Reçu ({c_dev})", value=float(t_ven))
                rest_n = t_ven - pay_n
                
                if st.button("🏁 FINALISER LA VENTE"):
                    ref_f = f"FAC-{random.randint(1000,9999)}"
                    h_v = datetime.now().strftime("%H:%M")
                    d_v = datetime.now().strftime("%d/%m/%Y")
                    
                    # Log Vente
                    run_db("INSERT INTO sales (ref, cli, tot, pay, rest, dev, dt, day, seller, ent, items) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (ref_f, cli_n.upper(), t_ven, pay_n, rest_n, c_dev, h_v, d_v, st.session_state.user, st.session_state.ent_id, json.dumps(cart_items)))
                    
                    # Update Stock
                    for it in cart_items:
                        run_db("UPDATE products SET qty = qty - ? WHERE item=? AND ent=?", (it['qte'], it['art'], st.session_state.ent_id))
                    
                    # Dette
                    if rest_n > 0:
                        run_db("INSERT INTO debts (cli, amt, ref, day, ent) VALUES (?,?,?,?,?)", (cli_n.upper(), rest_n, ref_f, d_v, st.session_state.ent_id))
                    
                    st.session_state.last_fac = {"ref": ref_f, "cli": cli_n, "tot": t_ven, "pay": pay_n, "res": rest_n, "dev": c_dev, "its": cart_items, "h": h_v}
                    st.session_state.panier = {}; st.rerun()
    else:
        # FACTURE
        f = st.session_state.last_fac
        pr = run_db("SELECT name, addr, tel, head FROM stores WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
        html_f = f"""<div style="background:#fff; color:#000; padding:20px; border:2px solid #000; font-family:monospace;">
            <h2 style='text-align:center;'>{pr[3] if pr[3] else pr[0]}</h2>
            <p style='text-align:center;'>{pr[1]} | Tél: {pr[2]}</p><hr>
            <p><b>FAC: {f['ref']}</b> | Client: {f['cli']}</p>
            <p>Heure: {f['h']}</p><hr>
            {"".join([f"<p>{i['art']} x{i['qte']} : {i['st']:,.0f} {f['dev']}</p>" for i in f['its']])}
            <hr><h3>TOTAL: {f['tot']:,.2f} {f['dev']}</h3>
            <p>Payé: {f['pay']} | Reste: {f['res']}</p>
        </div>"""
        st.markdown(html_f, unsafe_allow_html=True)
        
        # Download
        b64 = base64.b64encode(html_f.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Facture_{f["ref"]}.html" style="background:#00ff00; color:black; padding:15px; display:block; text-align:center; border-radius:10px; font-weight:bold; text-decoration:none;">📥 ENREGISTRER SUR LE TÉLÉPHONE</a>', unsafe_allow_html=True)
        
        if st.button("🔄 NOUVELLE VENTE"): st.session_state.last_fac = None; st.rerun()

# --- 5.3 STOCK (GESTION COMPLETE) ---
elif nav == "📦 STOCK":
    st.header("📦 INVENTAIRE & PRODUITS")
    
    # Affichage en Cartes
    items = run_db("SELECT id, item, qty, sell FROM products WHERE ent=?", (st.session_state.ent_id,), fetch=True)
    if items:
        for sid, sit, sq, sp in items:
            with st.container():
                st.markdown(f"<div class='card'><h3>ID: {sid} | {sit}</h3><p>Stock: <b>{sq}</b> | Prix: <b>{sp} $</b></p></div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🛠️ ACTIONS SUR LE STOCK")
    with st.form("stk_form"):
        act = st.radio("Action", ["Nouveau Produit", "Modifier par ID"])
        f_id = st.number_input("ID (si modification)", 0)
        f_nom = st.text_input("Désignation")
        f_qty = st.number_input("Quantité", 1)
        f_buy = st.number_input("Prix Achat ($)")
        f_sel = st.number_input("Prix Vente ($)")
        if st.form_submit_button("VALIDER"):
            if act == "Nouveau Produit":
                run_db("INSERT INTO products (item, qty, buy, sell, ent) VALUES (?,?,?,?,?)", (f_nom.upper(), f_qty, f_buy, f_sel, st.session_state.ent_id))
            else:
                run_db("UPDATE products SET item=?, qty=?, buy=?, sell=? WHERE id=? AND ent=?", (f_nom.upper(), f_qty, f_buy, f_sel, f_id, st.session_state.ent_id))
            st.success("Opération réussie !"); st.rerun()
    
    if st.button("🗑️ SUPPRIMER UN PRODUIT (Saisir ID)"):
        run_db("DELETE FROM products WHERE id=? AND ent=?", (f_id, st.session_state.ent_id)); st.rerun()

# --- 5.4 DÉPENSES ---
elif nav == "💸 DÉPENSES":
    st.header("💸 GESTION DES DÉPENSES")
    with st.form("exp_f"):
        e_mot = st.text_input("Motif de la dépense")
        e_amt = st.number_input("Montant ($)")
        e_cat = st.selectbox("Catégorie", ["LOYER", "SALAIRE", "TRANSPORT", "TAXE", "UNITES", "AUTRE"])
        if st.form_submit_button("ENREGISTRER"):
            run_db("INSERT INTO expenses (mot, amt, day, cat, ent) VALUES (?,?,?,?,?)", (e_mot.upper(), e_amt, datetime.now().strftime("%d/%m/%Y"), e_cat, st.session_state.ent_id))
            st.success("Dépense enregistrée !"); st.rerun()
    
    st.subheader("📋 LISTE DES CHARGES")
    exps = run_db("SELECT mot, amt, day, cat FROM expenses WHERE ent=? ORDER BY id DESC", (st.session_state.ent_id,), fetch=True)
    for mo, am, da, ca in exps:
        st.markdown(f"<div class='card'><p><b>{da}</b> | {ca}</p><h4>{mo} : {am} $</h4></div>", unsafe_allow_html=True)

# --- 5.5 DETTES ---
elif nav == "📉 DETTES":
    st.header("📉 CRÉANCES CLIENTS")
    d_list = run_db("SELECT id, cli, amt, ref FROM debts WHERE ent=? AND status='NON PAYE'", (st.session_state.ent_id,), fetch=True)
    if d_list:
        for di, dc, da, dr in d_list:
            with st.container():
                st.markdown(f"<div class='card'><h3>{dc}</h3><p>REF: {dr}</p><h4>Reste: {da:,.2f} $</h4></div>", unsafe_allow_html=True)
                tr_pay = st.number_input(f"Verser pour {dc}", 0.0, float(da), key=f"pay_{di}")
                if st.button("VALIDER PAIEMENT", key=f"btn_{di}"):
                    new_a = da - tr_pay
                    if new_a <= 0: run_db("UPDATE debts SET amt=0, status='PAYE' WHERE id=?", (di,))
                    else: run_db("UPDATE debts SET amt=? WHERE id=?", (new_a, di))
                    st.success("Paiement enregistré !"); st.rerun()
    else: st.success("🎉 Aucune dette en cours !")

# --- 5.6 RÉGLAGES & RESET ---
elif nav == "⚙️ RÉGLAGES":
    st.header("⚙️ MA BOUTIQUE")
    p_info = run_db("SELECT name, addr, tel, head FROM stores WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)[0]
    with st.form("st_set"):
        sn = st.text_input("Nom Entreprise", p_info[0])
        sa = st.text_input("Adresse", p_info[1])
        st_ = st.text_input("Téléphone", p_info[2])
        sh = st.text_input("En-tête Facture", p_info[3])
        if st.form_submit_button("MODIFIER PROFIL"):
            run_db("UPDATE stores SET name=?, addr=?, tel=?, head=? WHERE ent_id=?", (sn.upper(), sa, st_, sh, st.session_state.ent_id))
            st.success("Profil mis à jour !"); st.rerun()
    
    st.divider()
    if st.button("🔴 RESET : EFFACER TOUTES MES DONNÉES"):
        for t in ["products", "sales", "debts", "expenses"]:
            run_db(f"DELETE FROM {t} WHERE ent=?", (st.session_state.ent_id,))
        st.error("Données réinitialisées !"); st.rerun()

elif nav == "🚪 QUITTER": st.session_state.auth = False; st.rerun()

# --- 5.7 RAPPORTS (SUCCINCT) ---
if nav == "📊 RAPPORTS":
    st.header("📊 HISTORIQUE DES VENTES")
    f_day = st.date_input("Choisir une date", datetime.now()).strftime("%d/%m/%Y")
    h_data = run_db("SELECT dt, ref, cli, tot, seller FROM sales WHERE ent=? AND day=?", (st.session_state.ent_id, f_day), fetch=True)
    if h_data:
        for dt, rf, cl, to, se in h_data:
            st.markdown(f"<div class='card'><p>{dt} | REF: {rf}</p><p>Client: {cl}</p><h4>Total: {to:,.2f} $</h4></div>", unsafe_allow_html=True)
    else: st.info("Aucune vente trouvée.")
