# ==============================================================================
# ANASH ERP v3100 - SOLUTION FINALE ANTI-BUG
# CORRECTIF : INDEXERROR & SUBMIT BUTTON & DESIGN COBALT
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
# 1. DESIGN & CSS (FORCE LE TEXTE BLANC & ANIMATION DÉFILANTE)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ANASH ERP v3100", layout="wide", initial_sidebar_state="expanded")

def apply_v3100_ui():
    st.markdown("""
    <style>
    /* Fond Global Bleu Cobalt */
    .stApp {
        background: radial-gradient(circle at center, #0044ff 0%, #001133 100%) !important;
        color: white !important;
    }

    /* MESSAGE DÉFILANT CSS (Fluide et visible) */
    .marquee-container {
        width: 100%; overflow: hidden; background: #000; color: #00ff00;
        border-bottom: 2px solid #fff; position: fixed; top: 0; left: 0; z-index: 9999;
        height: 40px; display: flex; align-items: center;
    }
    .marquee-text {
        white-space: nowrap; display: inline-block;
        animation: scroll-left 25s linear infinite;
        font-weight: bold; font-size: 18px;
    }
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* HORLOGE GÉANTE 80mm */
    .clock-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px); border-radius: 35px; padding: 50px;
        text-align: center; border: 2px solid white; margin: 60px auto;
        max-width: 800px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .clock-h1 { font-family: 'Monospace'; font-size: 100px; color: #ffffff !important; margin: 0; }
    .date-p { font-size: 24px; color: #00ffff !important; text-transform: uppercase; }

    /* TEXTE BLANC SUR FOND BLEU (IMPORTANT) */
    .blue-section {
        background-color: #0044ff !important;
        color: white !important;
        padding: 25px; border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.4);
        margin-bottom: 15px;
    }
    .blue-section h1, .blue-section h2, .blue-section h3, .blue-section p, .blue-section b {
        color: white !important;
    }

    /* CADRE TOTAL PANIER COLORÉ */
    .total-frame-neon {
        background: #000 !important;
        color: #0ff !important;
        border: 5px solid #0ff !important;
        padding: 25px; border-radius: 20px;
        text-align: center; font-size: 45px !important;
        font-weight: 900; margin: 25px 0;
        box-shadow: 0 0 20px rgba(0,255,255,0.4);
    }

    /* BOUTONS XXL SMARTPHONE */
    .stButton>button {
        background: linear-gradient(135deg, #0088ff, #0044cc) !important;
        color: white !important; height: 75px !important;
        font-size: 22px !important; border-radius: 20px !important;
        border: 2px solid #fff !important; width: 100% !important;
        font-weight: bold;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #ffffff !important; }
    [data-testid="stSidebar"] * { color: #000 !important; font-weight: 600; }

    /* Fix pour inputs sur mobile */
    input, select { background-color: white !important; color: black !important; height: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOTEUR DE DONNÉES SQLITE
# ------------------------------------------------------------------------------
DB_PATH = "anash_master_v3100.db"

def sql_query(sql, params=(), fetch=True):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def boot_v3100():
    sql_query("CREATE TABLE IF NOT EXISTS users (uid TEXT PRIMARY KEY, pwd TEXT, role TEXT, s_ref TEXT, status TEXT, name TEXT, tel TEXT)", fetch=False)
    sql_query("CREATE TABLE IF NOT EXISTS shops (sid TEXT PRIMARY KEY, name TEXT, owner TEXT, rate REAL, head TEXT, addr TEXT, tel TEXT)", fetch=False)
    sql_query("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER, buy REAL, sell REAL, sid TEXT)", fetch=False)
    sql_query("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, cli TEXT, tot REAL, pay REAL, res REAL, date TEXT, time TEXT, seller TEXT, sid TEXT, data TEXT)", fetch=False)
    sql_query("CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, cli TEXT, bal REAL, ref TEXT, sid TEXT, status TEXT)", fetch=False)
    sql_query("CREATE TABLE IF NOT EXISTS system_cfg (id INTEGER PRIMARY KEY, marquee TEXT)", fetch=False)

    # Admin par défaut
    if not sql_query("SELECT uid FROM users WHERE uid='admin'"):
        sql_query("INSERT INTO users VALUES ('admin', ?, 'ADMIN', 'SYSTEM', 'ACTIF', 'ADMINISTRATEUR', '000')", (hashlib.sha256(b"admin123").hexdigest(),), fetch=False)
    
    if not sql_query("SELECT id FROM system_cfg"):
        sql_query("INSERT INTO system_cfg VALUES (1, 'ANASH ERP v3100 - BIENVENUE DANS VOTRE ESPACE DE GESTION PROFESSIONNEL')", fetch=False)

boot_v3100()
current_marquee = sql_query("SELECT marquee FROM system_cfg WHERE id=1")[0][0]

# ------------------------------------------------------------------------------
# 3. INITIALISATION SESSION
# ------------------------------------------------------------------------------
if 'state' not in st.session_state:
    st.session_state.state = {'auth': False, 'u': None, 'r': None, 's': None, 'cart': {}, 'ticket': None}

apply_v3100_ui()

# Affichage du message défilant CSS
st.markdown(f'<div class="marquee-container"><div class="marquee-text">{current_marquee}</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. AUTHENTIFICATION (FIXÉE)
# ------------------------------------------------------------------------------
if not st.session_state.state['auth']:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, lbox, _ = st.columns([1, 1.8, 1])
    with lbox:
        st.markdown("<div class='clock-container'><h1 style='color:white;'>ANASH ERP</h1></div>", unsafe_allow_html=True)
        t_login, t_signup = st.tabs(["🔐 CONNEXION", "📝 INSCRIPTION"])
        
        with t_login:
            u_id = st.text_input("Identifiant").lower().strip()
            u_pw = st.text_input("Mot de passe", type="password")
            if st.button("ACCÉDER AU SYSTÈME"):
                res = sql_query("SELECT pwd, role, s_ref, status FROM users WHERE uid=?", (u_id,))
                if res and hashlib.sha256(u_pw.encode()).hexdigest() == res[0][0]:
                    if res[0][3] == "EN_ATTENTE":
                        st.warning("Compte en attente de validation par l'Admin.")
                    else:
                        st.session_state.state.update({'auth': True, 'u': u_id, 'r': res[0][1], 's': res[0][2]})
                        st.rerun()
                else: st.error("Identifiants incorrects.")

        with t_signup:
            with st.form("signup"):
                su_id = st.text_input("ID Utilisateur").lower()
                su_nm = st.text_input("Nom Complet")
                su_tl = st.text_input("Numéro Téléphone")
                su_pw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("S'INSCRIRE"):
                    if sql_query("SELECT uid FROM users WHERE uid=?", (su_id,)): st.error("Déjà pris.")
                    else:
                        sql_query("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (su_id, hashlib.sha256(su_pw.encode()).hexdigest(), 'GERANT', 'EN_ATTENTE', 'EN_ATTENTE', su_nm, su_tl), fetch=False)
                        st.success("Inscrit ! Attendez la validation Admin.")
    st.stop()

# ------------------------------------------------------------------------------
# 5. ESPACE ADMIN (FIXÉ POUR admin / admin123)
# ------------------------------------------------------------------------------
if st.session_state.state['r'] == "ADMIN":
    st.sidebar.title("ADMINISTRATEUR")
    a_nav = st.sidebar.radio("Menu", ["Validation Comptes", "Message Défilant", "Déconnexion"])
    
    if a_nav == "Validation Comptes":
        st.header("👥 ACTIVATION DES GÉRANTS")
        pendings = sql_query("SELECT uid, name, tel, status FROM users WHERE role='GERANT'")
        for u, n, t, s in pendings:
            with st.container():
                st.markdown(f"<div class='blue-section'><h3>{n} (@{u})</h3><p>Tel: {t} | Statut: {s}</p></div>", unsafe_allow_html=True)
                ca, cb = st.columns(2)
                if ca.button("✅ ACTIVER", key=f"ok_{u}"):
                    sql_query("UPDATE users SET status='ACTIF', s_ref=? WHERE uid=?", (u, u), fetch=False)
                    st.rerun()
                if cb.button("🗑️ SUPPRIMER", key=f"rm_{u}"):
                    sql_query("DELETE FROM users WHERE uid=?", (u,), fetch=False)
                    st.rerun()

    elif a_nav == "Message Défilant":
        st.header("📢 ÉDITER LE MESSAGE")
        new_m = st.text_area("Texte du message", current_marquee)
        if st.button("ENREGISTRER"):
            sql_query("UPDATE system_cfg SET marquee=? WHERE id=1", (new_m,), fetch=False)
            st.rerun()

    if a_nav == "Déconnexion": st.session_state.state['auth'] = False; st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 6. PANEL UTILISATEUR (GERANT / VENDEUR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.state['u'].upper()}**")
    if st.session_state.state['r'] == "GERANT":
        u_menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "📊 RAPPORTS", "👥 ÉQUIPE", "⚙️ RÉGLAGES", "🚪 QUITTER"]
    else:
        u_menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES", "📊 RAPPORTS", "🚪 QUITTER"]
    choice = st.radio("NAVIGATION", u_menu)

# RECUPERATION DES INFOS BOUTIQUE (AVEC SECURITE ANTI-BUG)
shop_data = sql_query("SELECT name, rate, head, addr, tel FROM shops WHERE sid=?", (st.session_state.state['s'],))
if not shop_data:
    if st.session_state.state['r'] == "GERANT":
        st.warning("⚠️ Aucune boutique trouvée. Veuillez en créer une dans RÉGLAGES.")
        shop_info = ("", 2800.0, "", "", "") # Valeurs par défaut pour éviter l'IndexError
        choice = "⚙️ RÉGLAGES"
    else: st.error("Accès boutique restreint."); st.stop()
else:
    shop_info = shop_data[0]

# --- ACCUEIL ---
if choice == "🏠 ACCUEIL":
    st.markdown(f"""
    <div class='clock-container'>
        <p class='clock-h1'>{datetime.now().strftime('%H:%M')}</p>
        <p class='date-p'>{datetime.now().strftime('%d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    recette_j = sql_query("SELECT SUM(tot) FROM sales WHERE sid=? AND date=?", (st.session_state.state['s'], datetime.now().strftime("%d/%m/%Y")))[0][0] or 0
    st.markdown(f"<div class='blue-section'><h2 style='text-align:center; color:white;'>RECETTE DU JOUR : {recette_j:,.2f} $</h2></div>", unsafe_allow_html=True)

# --- CAISSE ---
elif choice == "🛒 CAISSE":
    if not st.session_state.state['ticket']:
        st.header("🛒 CAISSE")
        devise = st.radio("Devise", ["USD", "CDF"], horizontal=True)
        taux = shop_info[1]
        
        prods = sql_query("SELECT item, sell, qty FROM stock WHERE sid=?", (st.session_state.state['s'],))
        p_map = {p[0]: (p[1], p[2]) for p in prods}
        
        sel_p = st.selectbox("Choisir Produit", ["---"] + list(p_map.keys()))
        if sel_p != "---":
            if p_map[sel_p][1] > 0:
                st.session_state.state['cart'][sel_p] = st.session_state.state['cart'].get(sel_p, 0) + 1
                st.toast(f"Ajouté : {sel_p}")
            else: st.error("Stock épuisé !")

        if st.session_state.state['cart']:
            st.divider()
            total_v = 0.0; list_v = []
            for n, q in list(st.session_state.state['cart'].items()):
                p_u = p_map[n][0] if devise == "USD" else p_map[n][0] * taux
                stot = p_u * q
                total_v += stot
                list_v.append({"n": n, "q": q, "p": p_u, "s": stot})
                st.markdown(f"<div style='background:white;color:black;padding:10px;border-radius:10px;margin-bottom:5px;'><b>{n}</b> | {q} x {p_u:,.0f} {devise}</div>", unsafe_allow_html=True)
                if st.button(f"Retirer {n}"): del st.session_state.state['cart'][n]; st.rerun()

            st.markdown(f"<div class='total-frame-neon'>TOTAL : {total_v:,.2f} {devise}</div>", unsafe_allow_html=True)
            
            c_nom = st.text_input("Client", "COMPTANT").upper()
            c_pay = st.number_input(f"Payé ({devise})", value=float(total_v))
            c_res = total_v - c_pay
            
            if st.button("🚀 FINALISER LA VENTE"):
                v_ref = f"FAC-{random.randint(1000,9999)}"
                d, h = datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
                
                # Sauvegarde base USD
                t_u = total_v if devise == "USD" else total_v / taux
                p_u = c_pay if devise == "USD" else c_pay / taux
                r_u = c_res if devise == "USD" else c_res / taux
                
                sql_query("INSERT INTO sales (ref, cli, tot, pay, res, date, time, seller, sid, data) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (v_ref, c_nom, t_u, p_u, r_u, d, h, st.session_state.state['u'], st.session_state.state['s'], json.dumps(list_v)), fetch=False)
                
                for it in list_v:
                    sql_query("UPDATE stock SET qty = qty - ? WHERE item=? AND sid=?", (it['q'], it['n'], st.session_state.state['s']), fetch=False)
                
                if r_u > 0:
                    sql_query("INSERT INTO debts (cli, bal, ref, sid, status) VALUES (?,?,?,?,?)", (c_nom, r_u, v_ref, st.session_state.state['s'], 'OUVERT'), fetch=False)
                
                st.session_state.state['ticket'] = {"ref": v_ref, "cli": c_nom, "tot": total_v, "pay": c_pay, "res": c_res, "dev": devise, "items": list_v, "d": d, "h": h}
                st.session_state.state['cart'] = {}; st.rerun()
    else:
        # TICKET
        tk = st.session_state.state['ticket']
        st.markdown(f"<div style='background:white; color:black; padding:20px; border-radius:10px; font-family:monospace;'><h3>{shop_info[0]}</h3><p>REF: {tk['ref']}</p><hr>{"".join([f"<p>{x['n']} x{x['q']} : {x['s']:,.0f} {tk['dev']}</p>" for x in tk['items']])}<hr><h4>TOTAL: {tk['tot']:,.2f} {tk['dev']}</h4></div>", unsafe_allow_html=True)
        if st.button("NOUVELLE VENTE"): st.session_state.state['ticket'] = None; st.rerun()

# --- RÉGLAGES (FIXÉ) ---
elif choice == "⚙️ RÉGLAGES":
    st.header("⚙️ CONFIGURATION BOUTIQUE")
    
    # Formulaire de mise à jour avec vérification d'existence
    with st.form("shop_update"):
        st.subheader("Informations de la boutique")
        # Ici, on utilise shop_info qui a des valeurs par défaut si shop_data était vide
        e_n = st.text_input("Nom Enseigne", shop_info[0])
        e_t = st.number_input("Taux de change (CDF/USD)", shop_info[1])
        e_h = st.text_input("En-tête Facture", shop_info[2])
        e_a = st.text_input("Adresse", shop_info[3])
        e_p = st.text_input("Téléphone", shop_info[4])
        
        # BOUTON DE SOUMISSION OBLIGATOIRE DANS UN FORMULAIRE
        submit = st.form_submit_button("SAUVEGARDER LES MODIFICATIONS")
        
        if submit:
            if not shop_data:
                sql_query("INSERT INTO shops VALUES (?,?,?,?,?,?,?)", (st.session_state.state['s'], e_n, st.session_state.state['u'], e_t, e_h, e_a, e_p), fetch=False)
            else:
                sql_query("UPDATE shops SET name=?, rate=?, head=?, addr=?, tel=? WHERE sid=?", (e_n, e_t, e_h, e_a, e_p, st.session_state.state['s']), fetch=False)
            st.success("✅ Boutique mise à jour !")
            st.rerun()

# --- STOCK ---
elif choice == "📦 STOCK":
    st.header("📦 STOCK")
    with st.form("add_stock"):
        f_n = st.text_input("Désignation")
        f_q = st.number_input("Quantité", 0)
        f_a = st.number_input("Prix Achat ($)")
        f_v = st.number_input("Prix Vente ($)")
        if st.form_submit_button("AJOUTER"):
            sql_query("INSERT INTO stock (item, qty, buy, sell, sid) VALUES (?,?,?,?,?)", (f_n.upper(), f_q, f_a, f_v, st.session_state.state['s']), fetch=False)
            st.rerun()
    
    st.divider()
    inv = sql_query("SELECT id, item, qty, sell FROM stock WHERE sid=?", (st.session_state.state['s'],))
    for i, n, q, p in inv:
        st.markdown(f"<div class='blue-section'>ID: {i} | <b>{n}</b> | Qte: {q} | Prix: {p} $</div>", unsafe_allow_html=True)

elif choice == "📉 DETTES":
    st.header("📉 DETTES")
    dts = sql_query("SELECT id, cli, bal, ref FROM debts WHERE sid=? AND status='OUVERT'", (st.session_state.state['s'],))
    for di, dc, db, dr in dts:
        with st.container():
            st.markdown(f"<div class='blue-section'><h3>{dc}</h3><p>Solde: {db:,.2f} $</p></div>", unsafe_allow_html=True)
            if st.button(f"Solder {dc}", key=f"s_{di}"):
                sql_query("UPDATE debts SET bal=0, status='PAYE' WHERE id=?", (di,), fetch=False)
                st.rerun()

elif choice == "🚪 QUITTER":
    st.session_state.state['auth'] = False; st.rerun()
