import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import os

# ==========================================
# 1. CONFIGURATION SYSTÈME & SESSION
# ==========================================
st.set_page_config(page_title="BALIKA ERP PRO v247", layout="wide", initial_sidebar_state="collapsed")

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
# 2. INITIALISATION COMPLÈTE BASE DE DONNÉES
# ==========================================
def init_db():
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL, devise_origine TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, total_val REAL, acompte REAL, reste REAL, details TEXT, devise TEXT, date_v TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, montant_du REAL, devise TEXT, articles TEXT, sale_ref TEXT, date_d TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, avatar BLOB)")
    
    # Vérification et création des accès admin par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users VALUES (?,?,?,?)", ("admin", make_hashes("admin123"), "ADMIN", None))
    
    # Initialisation de la configuration par défaut
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config VALUES (1, 'BALIKA ERP', 'ADRESSE DE L''ENTREPRISE', '000000000', 2850.0, 'Bienvenue chez BALIKA ERP PRO - Gagnez en efficacité !')")

init_db()

# Chargement des variables de configuration
config_data = run_db("SELECT entreprise, message, taux, adresse, telephone FROM config WHERE id=1", fetch=True)
if config_data:
    C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = config_data[0]
else:
    C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = "BALIKA ERP", "Bienvenue", 2850.0, "ADRESSE", "000"

# ==========================================
# 3. DESIGN CSS & INTERFACE MOBILE
# ==========================================
st.markdown(f"""
    <style>
    /* Fond blanc et texte noir pour tout le système */
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"], header {{ background-color: #FFFFFF !important; }}
    [data-testid="stHeader"] *, [data-testid="stSidebar"] *, h1, h2, h3, h4, label, span, p, div {{ color: #000000 !important; }}
    
    /* Boutons de connexion et actions */
    .stButton>button {{ 
        background: linear-gradient(to right, #FF8C00, #FF4500) !important; 
        color: white !important; 
        border-radius: 12px; 
        height: 55px; 
        font-weight: bold; 
        border: none; 
        width: 100%; 
    }}
    
    /* Login Box */
    .login-box {{ 
        background: linear-gradient(135deg, #FF8C00, #FF4500); 
        padding: 40px; 
        border-radius: 20px; 
        color: white !important; 
        text-align: center; 
        margin-bottom: 20px;
    }}
    .login-box h1, .login-box p {{ color: white !important; }}

    /* Marquee (Texte défilant) */
    .marquee-container {{ width: 100%; overflow: hidden; background: #333; color: #FF8C00; padding: 12px 0; font-weight: bold; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 20s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    
    /* Cadre du Total Panier */
    .total-frame {{ 
        border: 4px solid #FF8C00; 
        background: #FFF3E0; 
        color: #E65100 !important; 
        padding: 20px; 
        border-radius: 15px; 
        font-size: 26px; 
        font-weight: bold; 
        text-align: center; 
        margin: 15px 0; 
    }}
    
    /* FACTURE ADMINISTRATIVE CENTRÉE */
    .invoice-container {{
        background: white; 
        color: black !important; 
        padding: 40px; 
        border: 2px solid #000; 
        max-width: 700px; 
        margin: auto; 
        text-align: center; 
        font-family: 'Times New Roman', serif;
    }}
    .invoice-header {{ border-bottom: 3px double #000; margin-bottom: 20px; padding-bottom: 10px; }}
    .invoice-header h1 {{ font-size: 28px; text-transform: uppercase; margin: 0; }}
    .invoice-info {{ display: flex; justify-content: space-between; text-align: left; margin-top: 15px; }}
    .invoice-table {{ width: 100%; border-collapse: collapse; margin: 25px 0; }}
    .invoice-table th, .invoice-table td {{ border: 1px solid #000; padding: 12px; text-align: left; }}
    .invoice-table th {{ background-color: #f2f2f2; }}
    .invoice-total-section {{ margin-top: 20px; border: 2px solid #000; padding: 15px; font-size: 1.5rem; font-weight: bold; }}
    .signature-section {{ margin-top: 60px; display: flex; justify-content: space-between; font-weight: bold; }}

    /* Mode Impression */
    @media print {{ 
        .no-print, [data-testid="stSidebar"] {{ display: none !important; }} 
        .invoice-container {{ border: none; width: 100%; max-width: 100%; padding: 0; }}
        .stApp {{ background: white !important; }}
    }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. ÉCRAN DE CONNEXION AVEC SECOURS
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown(f'<div class="login-box"><h1>{C_ENT}</h1><p>ACCÈS SÉCURISÉ</p></div>', unsafe_allow_html=True)
        u = st.text_input("Identifiant", placeholder="Entrez votre nom d'utilisateur").lower().strip()
        p = st.text_input("Mot de passe", type="password", placeholder="******").strip()
        
        if st.button("SE CONNECTER"):
            res = run_db("SELECT password, role FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                st.session_state.auth = True
                st.session_state.user = u
                st.session_state.role = res[0][1]
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
        
        st.write("---")
        if st.button("🆘 RÉINITIALISER ADMIN (admin / admin123)"):
            run_db("DELETE FROM users WHERE username='admin'")
            run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", ("admin", make_hashes("admin123"), "ADMIN"))
            st.success("Accès restauré : admin / admin123")
    st.stop()

# ==========================================
# 5. BARRE DE NAVIGATION (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown(f"<div style='text-align:center;'><h2>👤 {st.session_state.user.upper()}</h2><p>Rôle: {st.session_state.role}</p></div>", unsafe_allow_html=True)
    st.write("---")
    
    pages = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        pages.update({
            "📦 STOCK": "STOCK",
            "📊 RAPPORT": "RAPPORT",
            "👥 VENDEURS": "USERS",
            "⚙️ CONFIGURATION": "CONFIG"
        })
    
    for label, target in pages.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = target
            st.rerun()
            
    st.write("---")
    if st.button("🚪 DÉCONNEXION", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 6. CONTENU DES PAGES (LOGIQUE COMPLÈTE)
# ==========================================

# --- PAGE ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div style="border:3px solid #FF8C00; border-radius:20px; padding:20px; background:#FFF3E0; display:inline-block;"><h1>⌚ {datetime.now().strftime("%H:%M")}</h1><h3>📅 {datetime.now().strftime("%d/%m/%Y")}</h3></div></center>', unsafe_allow_html=True)
    st.title("Tableau de bord")
    
    v = run_db("SELECT total_val, devise FROM ventes", fetch=True)
    if v:
        df = pd.DataFrame(v, columns=["Total", "Devise"])
        c1, c2 = st.columns(2)
        c1.metric("Ventes en USD", f"{df[df['Devise']=='USD']['Total'].sum():,.2f} $")
        c2.metric("Ventes en CDF", f"{df[df['Devise']=='CDF']['Total'].sum():,.0f} FC")
    else:
        st.info("Aucune vente enregistrée aujourd'hui.")

# --- PAGE CAISSE & FACTURATION ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Terminal de Vente")
        monnaie_vente = st.radio("Monnaie de paiement", ["USD", "CDF"], horizontal=True)
        
        # Récupération des produits
        produits_db = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
        if not produits_db:
            st.warning("Le stock est vide. Veuillez ajouter des produits.")
        else:
            p_map = {r[0]: {'prix': r[1], 'stock': r[2], 'dev': r[3]} for r in produits_db}
            selection = st.selectbox("Choisir un article", ["---"] + list(p_map.keys()))
            
            if st.button("➕ AJOUTER AU PANIER") and selection != "---":
                st.session_state.panier[selection] = st.session_state.panier.get(selection, 0) + 1
                st.rerun()
            
            if st.session_state.panier:
                total_global = 0.0
                liste_details = []
                st.write("### Articles dans le panier")
                
                for art, qte in list(st.session_state.panier.items()):
                    p_base = p_map[art]['prix']
                    # Conversion dynamique selon le taux configuré
                    if p_map[art]['dev'] == "USD" and monnaie_vente == "CDF": p_final = p_base * C_TAUX
                    elif p_map[art]['dev'] == "CDF" and monnaie_vente == "USD": p_final = p_base / C_TAUX
                    else: p_final = p_base
                    
                    col_a, col_q, col_x = st.columns([3, 1, 1])
                    col_a.write(f"**{art}** ({p_final:,.2f} {monnaie_vente})")
                    new_qte = col_q.number_input("Qté", 1, p_map[art]['stock'], value=qte, key=f"q_{art}")
                    st.session_state.panier[art] = new_qte
                    if col_x.button("🗑️", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                    
                    sous_total = p_final * new_qte
                    total_global += sous_total
                    liste_details.append({'article': art, 'qte': new_qte, 'pu': p_final, 'st': sous_total})
                
                st.markdown(f'<div class="total-frame">NET À PAYER : {total_global:,.2f} {monnaie_vente}</div>', unsafe_allow_html=True)
                
                client_nom = st.text_input("NOM DU CLIENT").upper()
                montant_recu = st.number_input("MONTANT REÇU (ACOMPTE)", 0.0)
                
                if st.button("✅ VALIDER ET IMPRIMER") and client_nom:
                    ref_fac = f"FAC-{random.randint(10000, 99999)}"
                    date_actuelle = datetime.now().strftime("%d/%m/%Y %H:%M")
                    reste_a_payer = total_global - montant_recu
                    
                    # Enregistrement Vente
                    run_db("INSERT INTO ventes (ref, client_nom, total_val, acompte, reste, details, devise, date_v) VALUES (?,?,?,?,?,?,?,?)", 
                          (ref_fac, client_nom, total_global, montant_recu, reste_a_payer, str(liste_details), monnaie_vente, date_actuelle))
                    
                    # Gestion Dette si reste > 0
                    if reste_a_payer > 0:
                        run_db("INSERT INTO dettes (client_nom, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?)",
                              (client_nom, reste_a_payer, monnaie_vente, ", ".join([f"{x['article']}(x{x['qte']})" for x in liste_details]), ref_fac, date_actuelle))
                    
                    # Mise à jour Stock
                    for item in liste_details:
                        run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (item['qte'], item['article']))
                    
                    st.session_state.last_fac = {"ref": ref_fac, "cl": client_nom, "tot": total_global, "ac": montant_recu, "re": reste_a_payer, "dev": monnaie_vente, "lines": liste_details, "date": date_actuelle}
                    st.session_state.panier = {}
                    st.rerun()
    else:
        # --- AFFICHAGE DE LA FACTURE ADMINISTRATIVE CENTRÉE ---
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR À LA CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        
        st.markdown(f"""
        <div class="invoice-container">
            <div class="invoice-header">
                <h1>{C_ENT}</h1>
                <p>{C_ADR}<br>TÉLÉPHONE : {C_TEL}</p>
            </div>
            <h2>FACTURE N° {f['ref']}</h2>
            <div class="invoice-info">
                <div><b>CLIENT :</b> {f['cl']}</div>
                <div><b>DATE :</b> {f['date']}</div>
            </div>
            <table class="invoice-table">
                <thead>
                    <tr><th>DESCRIPTION</th><th>QTÉ</th><th>P.U</th><th>TOTAL</th></tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td>{l['article']}</td><td>{l['qte']}</td><td>{l['pu']:,.2f}</td><td>{l['st']:,.2f}</td></tr>" for l in f['lines']])}
                </tbody>
            </table>
            <div class="invoice-total-section">
                TOTAL GÉNÉRAL : {f['tot']:,.2f} {f['dev']}
            </div>
            <div style="text-align: left; margin-top: 10px;">
                <p><b>Payé :</b> {f['ac']:,.2f} {f['dev']} | <b>Reste à payer :</b> {f['re']:,.2f} {f['dev']}</p>
            </div>
            <div class="signature-section">
                <div>Signature du Client</div>
                <div>La Direction</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        c1, c2 = st.columns(2)
        c1.button("🖨️ SAUVEGARDER EN PDF / IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        
        whatsapp_link = f"https://wa.me/?text=Facture {f['ref']} - {C_ENT}%0AClient: {f['cl']}%0ATotal: {f['tot']} {f['dev']}%0AMerci de votre confiance."
        c2.markdown(f'<a href="{whatsapp_link}" target="_blank"><button style="width:100%; height:55px; background:#25D366; color:white; border:none; border-radius:12px; font-weight:bold;">📲 PARTAGER SUR WHATSAPP</button></a>', unsafe_allow_html=True)

# --- PAGE GESTION DU STOCK (COMPLÈTE) ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion des Produits")
    with st.form("ajout_produit"):
        c1, c2 = st.columns(2)
        nom_p = c1.text_input("Désignation du produit")
        prix_p = c2.number_input("Prix de vente", min_value=0.0)
        c3, c4 = st.columns(2)
        devise_p = c3.selectbox("Devise d'origine", ["USD", "CDF"])
        qte_p = c4.number_input("Stock initial", min_value=1)
        if st.form_submit_button("AJOUTER AU STOCK"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)",
                  (nom_p.upper(), qte_p, qte_p, prix_p, devise_p))
            st.success(f"{nom_p} ajouté !")
            st.rerun()

    st.write("### Inventaire")
    stock_data = run_db("SELECT * FROM produits", fetch=True)
    if stock_data:
        df_stock = pd.DataFrame(stock_data, columns=["ID", "Désignation", "Initial", "Actuel", "Prix", "Devise"])
        st.dataframe(df_stock, use_container_width=True)
        
        # Options de modification/suppression
        for row in stock_data:
            with st.expander(f"Modifier {row[1]}"):
                new_price = st.number_input(f"Nouveau prix ({row[1]})", value=float(row[4]), key=f"p_edit_{row[0]}")
                if st.button(f"Mettre à jour le prix de {row[1]}", key=f"btn_edit_{row[0]}"):
                    run_db("UPDATE produits SET prix_vente = ? WHERE id = ?", (new_price, row[0]))
                    st.rerun()
                if st.button(f"❌ Supprimer {row[1]}", key=f"btn_del_{row[0]}"):
                    run_db("DELETE FROM produits WHERE id = ?", (row[0],))
                    st.rerun()

# --- PAGE GESTION DES DETTES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Suivi des Dettes Clients")
    dettes_db = run_db("SELECT * FROM dettes", fetch=True)
    
    if not dettes_db:
        st.success("Toutes les dettes ont été réglées !")
    else:
        for d in dettes_db:
            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px;">
                    <h4>Client : {d[1]}</h4>
                    <p><b>Montant dû :</b> {d[2]:,.2f} {d[3]} | <b>Articles :</b> {d[4]}</p>
                    <p><b>Date :</b> {d[6]} | <b>Ref Vente :</b> {d[5]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                v_paie = st.number_input(f"Encaisser un montant pour {d[1]}", 0.0, float(d[2]), key=f"v_{d[0]}")
                if st.button(f"Valider le versement de {d[1]}", key=f"btn_v_{d[0]}"):
                    nouveau_reste = d[2] - v_paie
                    if nouveau_reste <= 0.05: # Si presque fini, on supprime
                        run_db("DELETE FROM dettes WHERE id = ?", (d[0],))
                        st.success(f"Dette de {d[1]} totalement réglée !")
                    else:
                        run_db("UPDATE dettes SET montant_du = ? WHERE id = ?", (nouveau_reste, d[0]))
                        st.info(f"Nouveau solde pour {d[1]} : {nouveau_reste:,.2f} {d[3]}")
                    
                    # Mise à jour dans l'historique des ventes
                    run_db("UPDATE ventes SET reste = reste - ? WHERE ref = ?", (v_paie, d[5]))
                    st.rerun()

# --- PAGE GESTION DES VENDEURS ---
elif st.session_state.page == "USERS":
    st.title("👥 Gestion du Personnel")
    with st.form("ajout_vendeur"):
        new_u = st.text_input("Identifiant du vendeur")
        new_p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE"):
            run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", (new_u.lower(), make_hashes(new_p), "VENDEUR"))
            st.success("Compte vendeur créé.")
            st.rerun()
            
    st.write("### Liste des comptes")
    users_list = run_db("SELECT username, role FROM users", fetch=True)
    for user in users_list:
        col_u1, col_u2 = st.columns([3, 1])
        col_u1.write(f"👤 **{user[0].upper()}** ({user[1]})")
        if user[0] != 'admin':
            if col_u2.button("Supprimer", key=f"del_u_{user[0]}"):
                run_db("DELETE FROM users WHERE username = ?", (user[0],))
                st.rerun()

# --- PAGE CONFIGURATION ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres du Système")
    with st.form("config_form"):
        new_ent = st.text_input("Nom de l'entreprise", C_ENT)
        new_adr = st.text_input("Adresse physique", C_ADR)
        new_tel = st.text_input("Téléphone de contact", C_TEL)
        new_taux = st.number_input("Taux de change (1 USD en CDF)", value=C_TAUX)
        new_msg = st.text_area("Message défilant (Accueil)", C_MSG)
        if st.form_submit_button("ENREGISTRER LES MODIFICATIONS"):
            run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, taux=?, message=? WHERE id=1",
                  (new_ent.upper(), new_adr, new_tel, new_taux, new_msg))
            st.success("Configuration mise à jour !")
            st.rerun()
            
    st.write("---")
    st.write("### Sauvegarde des données")
    if os.path.exists("anash_data.db"):
        with open("anash_data.db", "rb") as f:
            st.download_button("📥 TÉLÉCHARGER LA BASE DE DONNÉES (BACKUP)", f, file_name=f"backup_erp_{datetime.now().strftime('%d_%m')}.db")

# --- PAGE RAPPORT DE VENTES ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Historique Global des Ventes")
    ventes_data = run_db("SELECT date_v, ref, client_nom, total_val, devise, acompte, reste FROM ventes ORDER BY id DESC", fetch=True)
    if ventes_data:
        df_ventes = pd.DataFrame(ventes_data, columns=["Date", "Référence", "Client", "Total", "Devise", "Payé", "Dette"])
        st.dataframe(df_ventes, use_container_width=True)
        
        # Sommaire rapide
        total_usd = df_ventes[df_ventes['Devise']=='USD']['Total'].sum()
        total_cdf = df_ventes[df_ventes['Devise']=='CDF']['Total'].sum()
        st.success(f"TOTAL GÉNÉRAL : {total_usd:,.2f} USD et {total_cdf:,.0f} CDF")
    else:
        st.info("Aucune transaction enregistrée.")
