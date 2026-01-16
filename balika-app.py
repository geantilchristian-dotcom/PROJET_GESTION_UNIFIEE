import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os
import json

# ==========================================
# 1. SYSTÈME & SESSION (v249 - FULL VERSION)
# ==========================================
st.set_page_config(page_title="BALIKA ERP v249", layout="wide", initial_sidebar_state="collapsed")

# Initialisation des variables de session
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
# 2. INITIALISATION BASE DE DONNÉES
# ==========================================
def init_db():
    # Table Produits
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL, devise_origine TEXT)")
    # Table Ventes
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, total_val REAL, acompte REAL, reste REAL, details TEXT, devise TEXT, date_v TEXT)")
    # Table Dettes
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, montant_du REAL, devise TEXT, articles TEXT, sale_ref TEXT, date_d TEXT)")
    # Table Configuration
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, taux REAL, message TEXT)")
    # Table Utilisateurs
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, avatar BLOB)")
    
    # Données par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES (?,?,?,?)", ("admin", make_hashes("admin123"), "ADMIN", None))
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'VOTRE ADRESSE ICI', '+243 000 000', 2850.0, 'Bienvenue chez BALIKA ERP')")

init_db()

# Chargement de la config globale
config_data = run_db("SELECT entreprise, message, taux, adresse, telephone FROM config WHERE id=1", fetch=True)
C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = config_data[0] if config_data else ("BALIKA ERP", "Bienvenue", 2850.0, "ADRESSE", "000")

# ==========================================
# 3. DESIGN CSS (TEXTE NOIR, FOND BLANC, MOBILE & 80MM)
# ==========================================
st.markdown(f"""
    <style>
    /* Global White Background & Black Text */
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"], header {{ background-color: #FFFFFF !important; }}
    * {{ color: #000000 !important; font-family: 'Arial', sans-serif; }}
    
    /* Marquee */
    .marquee-container {{ width: 100%; overflow: hidden; background: #000; color: #FF8C00 !important; padding: 10px 0; font-weight: bold; position: fixed; top: 0; z-index: 999; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 20s linear infinite; color: #FF8C00 !important; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    
    /* Buttons */
    .stButton>button {{ 
        background: linear-gradient(to right, #FF8C00, #FF4500) !important; 
        color: white !important; 
        border-radius: 10px; height: 50px; border: none; font-weight: bold; width: 100%;
    }}
    
    /* Login Box */
    .login-box {{ background: #FF8C00; padding: 30px; border-radius: 20px; text-align: center; margin-top: 50px; }}
    .login-box h1, .login-box p {{ color: white !important; }}

    /* Total Frame */
    .total-frame {{ border: 3px solid #FF8C00; background: #FFF3E0; color: #E65100 !important; padding: 15px; border-radius: 12px; font-size: 22px; font-weight: bold; text-align: center; margin: 10px 0; }}

    /* FORMAT TICKET 80MM */
    .ticket-80mm {{
        width: 80mm;
        margin: auto;
        padding: 5mm;
        border: 1px dashed #000;
        background: white;
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
    }}
    .ticket-header {{ border-bottom: 1px solid #000; margin-bottom: 5px; padding-bottom: 5px; }}
    .ticket-table {{ width: 100%; font-size: 12px; border-collapse: collapse; }}
    .ticket-table th {{ border-bottom: 1px solid #000; }}
    .ticket-total {{ font-size: 16px; font-weight: bold; margin-top: 10px; border-top: 1px double #000; padding-top: 5px; }}
    
    /* Input adjustments */
    input {{ background-color: #F8F9FA !important; border: 1px solid #CCC !important; color: black !important; }}
    
    @media print {{
        .no-print {{ display: none !important; }}
        .ticket-80mm {{ border: none; width: 100%; }}
    }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    <div style="margin-top: 50px;"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. ÉCRAN DE CONNEXION
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown(f'<div class="login-box"><h1>{C_ENT}</h1><p>IDENTIFICATION</p></div>', unsafe_allow_html=True)
        u = st.text_input("Utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("ACCÉDER"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, res[0][1]
                st.rerun()
            else: st.error("Identifiants incorrects.")
        st.write("---")
        if st.button("🆘 RESTAURER ADMIN"):
            run_db("DELETE FROM users WHERE username='admin'")
            run_db("INSERT INTO users VALUES (?,?,?,?)", ("admin", make_hashes("admin123"), "ADMIN", None))
            st.success("Admin : admin / admin123")
    st.stop()

# ==========================================
# 5. NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    st.write(f"Rôle : {st.session_state.role}")
    st.write("---")
    menu = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        menu.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 VENDEURS": "USERS", "⚙️ CONFIG": "CONFIG"})
    
    for lab, pg in menu.items():
        if st.button(lab, use_container_width=True):
            st.session_state.page = pg
            st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary"):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 6. LOGIQUE DES PAGES (VERSION LONGUE)
# ==========================================

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f"""
        <center>
            <div style="border:4px solid #FF8C00; padding:30px; border-radius:100px; width:250px; height:250px; background:#FFF3E0; display:flex; flex-direction:column; justify-content:center;">
                <h1 style="font-size:50px; margin:0;">{datetime.now().strftime("%H:%M")}</h1>
                <h3 style="margin:0;">{datetime.now().strftime("%d/%m/%Y")}</h3>
            </div>
        </center>
    """, unsafe_allow_html=True)
    
    st.title("📊 Aperçu des ventes")
    ventes = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if ventes:
        df_v = pd.DataFrame(ventes, columns=["Total", "Devise"])
        col1, col2 = st.columns(2)
        col1.metric("Recette USD", f"{df_v[df_v['Devise']=='USD']['Total'].sum():,.2f} $")
        col2.metric("Recette CDF", f"{df_v[df_v['Devise']=='CDF']['Total'].sum():,.0f} FC")
    else:
        st.info("Aucune vente pour le moment.")

# --- CAISSE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse")
        devise_vente = st.radio("Devise de paiement", ["USD", "CDF"], horizontal=True)
        
        prods = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        p_map = {r[0]: {'prix': r[1], 'stock': r[2], 'dev': r[3]} for r in prods}
        
        choix = st.selectbox("Choisir un produit", ["---"] + list(p_map.keys()))
        if st.button("➕ AJOUTER") and choix != "---":
            st.session_state.panier[choix] = st.session_state.panier.get(choix, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            st.write("---")
            total_panier = 0.0
            details_vente = []
            
            for art, qte in list(st.session_state.panier.items()):
                p_base = p_map[art]['prix']
                # Conversion
                if p_map[art]['dev'] == "USD" and devise_vente == "CDF": p_f = p_base * C_TAUX
                elif p_map[art]['dev'] == "CDF" and devise_vente == "USD": p_f = p_base / C_TAUX
                else: p_f = p_base
                
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{art}**\n({p_f:,.2f} {devise_vente})")
                new_q = c2.number_input("Qté", 1, p_map[art]['stock'], value=qte, key=f"q_{art}")
                st.session_state.panier[art] = new_q
                if c3.button("🗑️", key=f"del_{art}"):
                    del st.session_state.panier[art]
                    st.rerun()
                
                sous_total = p_f * new_q
                total_panier += sous_total
                details_vente.append({'art': art, 'qte': new_q, 'pu': p_f, 'st': sous_total})
            
            st.markdown(f'<div class="total-frame">TOTAL : {total_panier:,.2f} {devise_vente}</div>', unsafe_allow_html=True)
            
            nom_cl = st.text_input("Nom du client").upper()
            paye = st.number_input("Acompte", 0.0)
            
            if st.button("✅ VALIDER LA VENTE") and nom_cl:
                ref = f"FAC-{random.randint(1000,9999)}"
                now = datetime.now().strftime("%d/%m/%Y %H:%M")
                reste = total_panier - paye
                
                # Insert Vente
                run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", 
                      (ref, nom_cl, total_panier, paye, reste, str(details_vente), devise_vente, now))
                
                # Insert Dette si reste
                if reste > 0:
                    arts_txt = ", ".join([f"{x['art']} (x{x['qte']})" for x in details_vente])
                    run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)",
                          (nom_cl, reste, devise_vente, arts_txt, ref, now))
                
                # Update Stock
                for item in details_vente:
                    run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (item['qte'], item['art']))
                
                st.session_state.last_fac = {"ref": ref, "cl": nom_cl, "tot": total_panier, "ac": paye, "re": reste, "dev": devise_vente, "lines": details_vente, "date": now}
                st.session_state.panier = {}
                st.rerun()
    else:
        # --- AFFICHAGE TICKET 80MM ---
        f = st.session_state.last_fac
        st.button("⬅️ NOUVELLE VENTE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        st.markdown(f"""
        <div class="ticket-80mm">
            <div class="ticket-header">
                <h2 style="margin:0;">{C_ENT}</h2>
                <p style="font-size:10px; margin:0;">{C_ADR}<br>Tél: {C_TEL}</p>
            </div>
            <p style="font-size:12px;"><b>TICKET N° {f['ref']}</b><br>Client: {f['cl']}<br>Date: {f['date']}</p>
            <table class="ticket-table">
                <thead><tr><th align="left">Art</th><th align="center">Q</th><th align="right">S.T</th></tr></thead>
                <tbody>
                    {"".join([f"<tr><td>{l['art']}</td><td align='center'>{l['qte']}</td><td align='right'>{l['st']:,.2f}</td></tr>" for l in f['lines']])}
                </tbody>
            </table>
            <div class="ticket-total">TOTAL: {f['tot']:,.2f} {f['dev']}</div>
            <p style="font-size:11px; margin-top:5px;">Payé: {f['ac']:,.2f}<br>Reste: {f['re']:,.2f}</p>
            <p style="font-size:10px; margin-top:10px;">Merci de votre visite !</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        msg = f"Facture {f['ref']} - {C_ENT}\nClient: {f['cl']}\nTotal: {f['tot']} {f['dev']}"
        c2.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="width:100%; height:50px; background:#25D366; color:white; border:none; border-radius:10px; font-weight:bold;">📲 PARTAGER</button></a>', unsafe_allow_html=True)

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion du Stock")
    with st.form("add_prod"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Désignation")
        prix = c2.number_input("Prix de vente", 0.0)
        c3, c4 = st.columns(2)
        dev = c3.selectbox("Devise", ["USD", "CDF"])
        qte = c4.number_input("Quantité", 1)
        if st.form_submit_button("➕ ENREGISTRER PRODUIT"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (nom.upper(), qte, qte, prix, dev))
            st.rerun()
            
    st.write("### Liste des produits")
    stk = run_db("SELECT * FROM produits", fetch=True)
    if stk:
        for r in stk:
            with st.expander(f"📦 {r[1]} - Stock : {r[3]}"):
                new_p = st.number_input("Modifier prix", value=float(r[4]), key=f"edit_{r[0]}")
                col1, col2 = st.columns(2)
                if col1.button("💾 SAUVER PRIX", key=f"sv_{r[0]}"):
                    run_db("UPDATE produits SET prix_vente = ? WHERE id = ?", (new_p, r[0]))
                    st.rerun()
                if col2.button("🗑️ SUPPRIMER", key=f"del_{r[0]}"):
                    run_db("DELETE FROM produits WHERE id = ?", (r[0],))
                    st.rerun()

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Dettes Clients")
    dts = run_db("SELECT * FROM dettes", fetch=True)
    if not dts:
        st.success("Aucune dette en cours.")
    else:
        for d in dts:
            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #CCC; padding:15px; border-radius:10px; margin-bottom:10px;">
                    <b>CLIENT : {d[1]}</b><br>Montant : {d[2]:,.2f} {d[3]}<br>Articles : {d[4]}
                </div>
                """, unsafe_allow_html=True)
                v_paie = st.number_input(f"Montant versé par {d[1]}", 0.0, float(d[2]), key=f"p_{d[0]}")
                if st.button(f"Valider paiement {d[1]}", key=f"btn_{d[0]}"):
                    nouveau = d[2] - v_paie
                    if nouveau <= 0.05:
                        run_db("DELETE FROM dettes WHERE id = ?", (d[0],))
                        st.success("Dette réglée !")
                    else:
                        run_db("UPDATE dettes SET montant_du = ? WHERE id = ?", (nouveau, d[0]))
                    run_db("UPDATE ventes SET reste = reste - ? WHERE ref = ?", (v_paie, d[5]))
                    st.rerun()

# --- CONFIG ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Configuration")
    with st.form("cfg"):
        en = st.text_input("Nom Entreprise", C_ENT)
        ad = st.text_input("Adresse", C_ADR)
        tl = st.text_input("Téléphone", C_TEL)
        tx = st.number_input("Taux de change (1 USD = ? CDF)", value=C_TAUX)
        ms = st.text_area("Message Défilant", C_MSG)
        if st.form_submit_button("ENREGISTRER"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, taux=?, message=? WHERE id=1", (en.upper(), ad, tl, tx, ms))
            st.rerun()
    
    st.write("---")
    if os.path.exists("anash_data.db"):
        with open("anash_data.db", "rb") as f:
            st.download_button("📥 SAUVEGARDER LA BASE DE DONNÉES", f, file_name="backup_erp.db")

# --- RAPPORT ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Rapport des ventes")
    data = run_db("SELECT date_v, ref, client_nom, total_val, devise, reste FROM ventes ORDER BY id DESC", fetch=True)
    if data:
        df = pd.DataFrame(data, columns=["Date", "Réf", "Client", "Total", "Devise", "Dette"])
        st.dataframe(df, use_container_width=True)

# --- VENDEURS ---
elif st.session_state.page == "USERS":
    st.title("👥 Gestion des Vendeurs")
    with st.form("u"):
        nu = st.text_input("Identifiant")
        np = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER COMPTE"):
            run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", (nu.lower(), make_hashes(np), "VENDEUR"))
            st.rerun()
    for u in run_db("SELECT username FROM users WHERE username!='admin'", fetch=True):
        st.write(f"👤 {u[0].upper()}")
        if st.button(f"Supprimer {u[0]}", key=u[0]):
            run_db("DELETE FROM users WHERE username=?", (u[0],))
            st.rerun()
