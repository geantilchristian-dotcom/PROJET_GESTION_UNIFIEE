import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib

# ==========================================
# 1. STYLE CSS : CONTRASTE BLANC SUR COULEUR
# ==========================================
st.set_page_config(page_title="ANASH ERP v137", layout="wide")

st.markdown("""
    <style>
    /* 1. Texte en NOIR par défaut sur fond blanc (Écran de connexion) */
    h1, h2, h3, p, label, .stMarkdown, div[data-testid="stWidgetLabel"] p {
        color: #000000 !important;
    }
    
    /* 2. Texte en BLANC pour les éléments sur fond BLEU ou NOIR */
    /* Blocs de code (consigne : fond bleu, texte blanc) */
    code { 
        color: #FFFFFF !important; 
        background-color: #0047AB !important; 
        padding: 2px 5px; 
        border-radius: 4px; 
    }

    /* Cadre du Total Panier (fond dégradé bleu, texte blanc) */
    .total-frame {
        background: linear-gradient(135deg, #0047AB 0%, #002D6B 100%);
        color: #FFFFFF !important; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center;
        border: 4px solid #FFD700; 
        font-size: 28px; 
        font-weight: bold; 
        margin: 10px 0;
    }
    
    /* Forcer le texte en blanc à l'intérieur du cadre total */
    .total-frame div, .total-frame span {
        color: #FFFFFF !important;
    }

    /* Boutons (fond bleu, texte blanc) */
    .stButton>button { 
        width: 100% !important; 
        height: 55px !important; 
        background-color: #0047AB !important; 
        color: #FFFFFF !important; 
        border-radius: 10px !important; 
        font-weight: bold;
        border: none;
    }

    /* Champs de saisie (si fond noir automatique sur mobile) */
    input {
        color: #000000 !important;
    }

    @media print {
        header, footer, .stSidebar, .stButton, .no-print, [data-testid="stHeader"], .stRadio, .stSelectbox {
            display: none !important;
        }
        .stApp { background-color: white !important; }
        .print-area { display: block !important; width: 100% !important; color: black !important; }
    }

    .stApp { background-color: #FFFFFF !important; }
    
    .facture-box { background: white; border: 1px solid #000; padding: 20px; color: black !important; font-family: 'Arial'; }
    .ticket-thermique {
        background: white; border: 1px dashed #000; padding: 10px; color: black !important;
        width: 280px; margin: auto; font-family: 'Courier New'; font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGIQUE BASE DE DONNÉES
# ==========================================
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

def run_db(query, params=(), fetch=False):
    with sqlite3.connect('anash_data.db', timeout=30) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            if fetch: return cursor.fetchall()
        except Exception as e: return str(e)
    return None

def init_db():
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, total_usd REAL, acompte REAL, reste REAL, details TEXT, statut TEXT, devise TEXT, date_v DATE DEFAULT (date('now')))")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, montant_du REAL, details TEXT, date_d DATE DEFAULT (date('now')))")
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, rccm TEXT, nif TEXT, id_nat TEXT, telephone TEXT, taux REAL)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES (?,?,?)", ("admin", make_hashes("admin123"), "ADMIN"))
init_db()

c_data = run_db("SELECT * FROM config WHERE id=1", fetch=True)
if not c_data:
    run_db("INSERT INTO config VALUES (1, 'VOTRE BOUTIQUE', 'ADRESSE', 'RCCM', 'NIF', 'IDNAT', '+243', 2850.0)")
    c_data = run_db("SELECT * FROM config WHERE id=1", fetch=True)
_, C_ENT, C_ADR, C_RCCM, C_NIF, C_IDNAT, C_TEL, C_TAUX = c_data[0]

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'panier' not in st.session_state: st.session_state.panier = {}
if 'ref_fac' not in st.session_state: st.session_state.ref_fac = f"FAC-{datetime.now().strftime('%y%m%d')}-{random.randint(100, 999)}"

# ==========================================
# 3. ÉCRAN DE CONNEXION (VISIBILITÉ MAX)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 CONNEXION ANASH ERP</h2>", unsafe_allow_html=True)
    _, cent, _ = st.columns([0.05, 1, 0.05])
    with cent:
        u = st.text_input("Nom d'utilisateur")
        p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER AU SYSTÈME"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if res and check_hashes(p, res[0][0]):
                st.session_state.logged_in, st.session_state.user_role, st.session_state.username = True, res[0][1], u
                st.rerun()
            else: st.error("Identifiants incorrects")
    st.stop()

# ==========================================
# 4. MODULES
# ==========================================
st.sidebar.title(f"👤 {st.session_state.username}")
menu_opt = ["🏠 ACCUEIL", "🛒 CAISSE", "📦 STOCK", "📉 DETTES", "👥 USERS", "⚙️ CONFIG"] if st.session_state.user_role == "ADMIN" else ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
menu = st.sidebar.radio("SÉLECTIONNER UN MODULE", menu_opt)

# --- MODULE CAISSE ---
if menu == "🛒 CAISSE":
    col_v, col_f = st.columns([1, 1.3])
    with col_v:
        devise = st.radio("DEVISE :", ["USD", "CDF"], horizontal=True)
        items = run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE stock_actuel > 0", fetch=True)
        art_map = {r[0]: {'p': r[1], 's': r[2]} for r in items} if items else {}
        sel = st.selectbox("Article", ["---"] + list(art_map.keys()))
        if st.button("➕ AJOUTER") and sel != "---":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
        
        total_usd = 0.0
        rows_html = ""
        for art, qte in list(st.session_state.panier.items()):
            nq = st.number_input(f"Qté {art}", 1, art_map[art]['s'], qte, key=f"q_{art}")
            st.session_state.panier[art] = nq
            stut = nq * art_map[art]['p']
            total_usd += stut
            rows_html += f"<tr><td>{art}</td><td align='center'>{nq}</td><td align='right'>{stut:,.2f}$</td></tr>"
            if st.button(f"🗑️ Retirer {art}"): del st.session_state.panier[art]; st.rerun()

    with col_f:
        c_nom = st.text_input("NOM DU CLIENT", "PASSAGER")
        tx_m = C_TAUX if devise == "CDF" else 1.0
        tot_p = total_usd * tx_m
        # CADRE TOTAL : FOND BLEU, TEXTE BLANC
        st.markdown(f'<div class="total-frame">NET À PAYER : {tot_p:,.2f} {devise}</div>', unsafe_allow_html=True)
        
        acompte = st.number_input(f"MONTANT REÇU ({devise})", 0.0)
        reste = max(0.0, tot_p - acompte)
        fmt = st.radio("FORMAT", ["THERMIQUE", "A4"], horizontal=True)

        if total_usd > 0:
            st.markdown(f"""
            <div class="print-area">
                <div class="{"ticket-thermique" if fmt == "THERMIQUE" else "facture-box"}">
                    <center><b>{C_ENT}</b><br>{C_ADR}<br>Tél: {C_TEL}</center><hr>
                    <table width="100%"><tr><td>REF: {st.session_state.ref_fac}</td><td align="right">{datetime.now().strftime('%d/%m/%Y')}</td></tr></table>
                    <p>Client: {c_nom.upper()}</p><hr>
                    <table width="100%" border="1" style="border-collapse:collapse;">
                        <tr><th>Article</th><th>Qté</th><th>Total</th></tr>{rows_html}
                    </table><hr>
                    <h3 align="right">TOTAL : {tot_p:,.2f} {devise}</h3>
                    <p align="right">Payé: {acompte:,.2f} | Reste: {reste:,.2f}</p>
                </div>
            </div>""", unsafe_allow_html=True)
            
            if st.button("🖨️ IMPRIMER MAINTENANT"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

        if st.button("🚀 VALIDER & DÉBITER STOCK"):
            if st.session_state.panier:
                ac_usd = acompte / tx_m
                re_usd = total_usd - ac_usd
                det = ", ".join([f"{n}(x{q})" for n, q in st.session_state.panier.items()])
                run_db("INSERT INTO ventes (ref, client_nom, total_usd, acompte, reste, details, statut, devise) VALUES (?,?,?,?,?,?,?,?)", (st.session_state.ref_fac, c_nom.upper(), total_usd, ac_usd, re_usd, det, "SOLDE" if re_usd <= 0.01 else "DETTE", devise))
                if re_usd > 0.01: run_db("INSERT INTO dettes (client_nom, montant_du, details) VALUES (?,?,?)", (c_nom.upper(), re_usd, det))
                for n, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (q, n))
                st.session_state.panier = {}; st.session_state.ref_fac = f"FAC-{datetime.now().strftime('%y%m%d')}-{random.randint(100, 999)}"; st.rerun()

# --- MODULE STOCK ---
elif menu == "📦 STOCK" and st.session_state.user_role == "ADMIN":
    st.subheader("📦 Stock")
    with st.form("st_f"):
        c1, c2, c3 = st.columns(3); dn = c1.text_input("Désignation"); pr = c2.number_input("Prix $"); qt = c3.number_input("Stock", step=1)
        if st.form_submit_button("AJOUTER PRODUIT"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente) VALUES (?,?,?,?)", (dn.upper(), qt, qt, pr)); st.rerun()
    for pid, d, p, s in run_db("SELECT id, designation, prix_vente, stock_actuel FROM produits", fetch=True):
        with st.expander(f"{d} ({s} restants)"):
            np = st.number_input("Modifier Prix ($)", value=float(p), key=f"p_{pid}")
            if st.button("Sauvegarder", key=f"s_{pid}"): run_db("UPDATE produits SET prix_vente=? WHERE id=?", (np, pid)); st.rerun()
            if st.button("🗑️ Supprimer", key=f"d_{pid}"): run_db("DELETE FROM produits WHERE id=?", (pid,)); st.rerun()

# --- MODULE DETTES ---
elif menu == "📉 DETTES":
    st.subheader("📉 Dettes")
    for did, cl, mt in run_db("SELECT id, client_nom, montant_du FROM dettes", fetch=True):
        with st.expander(f"{cl} - Dû: {mt:,.2f} $"):
            tr = st.number_input("Payer Tranche ($)", 0.0, float(mt), key=f"t_{did}")
            if st.button(f"Confirmer {cl}", key=f"b_{did}"):
                nr = mt - tr
                if nr <= 0.01: run_db("DELETE FROM dettes WHERE id=?", (did,))
                else: run_db("UPDATE dettes SET montant_du=? WHERE id=?", (nr, did))
                st.rerun()

# --- MODULE CONFIG ---
elif menu == "⚙️ CONFIG" and st.session_state.user_role == "ADMIN":
    with st.form("cfg"):
        st.subheader("⚙️ Config")
        e = st.text_input("Boutique", value=C_ENT); a = st.text_input("Adresse", value=C_ADR); t = st.text_input("Tél", value=C_TEL)
        c1, c2, c3 = st.columns(3); r = c1.text_input("RCCM", value=C_RCCM); n = c2.text_input("NIF", value=C_NIF); i = c3.text_input("IDNAT", value=C_IDNAT)
        tx = st.number_input("Taux (1$=?)", value=C_TAUX)
        if st.form_submit_button("SAUVEGARDER"):
            run_db("UPDATE config SET entreprise=?, adresse=?, rccm=?, nif=?, id_nat=?, telephone=?, taux=? WHERE id=1", (e.upper(), a, r, n, i, t, tx)); st.rerun()

# --- MODULE USERS ---
elif menu == "👥 USERS" and st.session_state.user_role == "ADMIN":
    st.subheader("👥 Users")
    with st.form("u"):
        nu = st.text_input("Nom"); np = st.text_input("Pass", type="password"); nr = st.selectbox("Rôle", ["ADMIN", "VENDEUR"])
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO users VALUES (?,?,?)", (nu, make_hashes(np), nr)); st.rerun()
    for un, ur in run_db("SELECT username, role FROM users", fetch=True):
        if un != "admin" and st.button(f"Supprimer {un}"): run_db("DELETE FROM users WHERE username=?", (un,)); st.rerun()

# --- ACCUEIL ---
elif menu == "🏠 ACCUEIL":
    v = run_db("SELECT SUM(total_usd) FROM ventes", fetch=True)[0][0] or 0
    d = run_db("SELECT SUM(montant_du) FROM dettes", fetch=True)[0][0] or 0
    st.metric("VENTES ($)", f"{v:,.2f} $")
    st.metric("DETTES ($)", f"{d:,.2f} $")