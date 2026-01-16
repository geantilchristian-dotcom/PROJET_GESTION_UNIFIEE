import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib
import json
import io

# ==============================================================================
# 1. CONFIGURATION SYSTÈME (v1500 - AUCUNE LIGNE SUPPRIMÉE)
# ==============================================================================
st.set_page_config(page_title="BALIKA ERP v1500", layout="wide", initial_sidebar_state="collapsed")

# Initialisation complète du Session State (Mémoire de l'application)
if 'auth' not in st.session_state:
    st.session_state.update({
        'auth': False, 'user': "", 'role': "", 'ent_id': "SYSTEM",
        'page': "ACCUEIL", 'panier': {}, 'last_fac': None,
        'format_fac': "80mm", 'devise_vente': "USD"
    })

def run_db(query, params=(), fetch=False):
    try:
        with sqlite3.connect('balika_master_final.db', timeout=60) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall() if fetch else None
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        return []

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==============================================================================
# 2. STRUCTURE DES TABLES (REPRISE TOTALE)
# ==============================================================================
def init_db():
    # Table Utilisateurs avec colonnes Admin, Vendeurs, Status, Date, Tel
    run_db("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, ent_id TEXT, 
        status TEXT DEFAULT 'ACTIF', photo BLOB, telephone TEXT, date_creation TEXT)""")
    
    # Configuration (Nom App, Marquee, Taux)
    run_db("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, app_name TEXT, marquee_text TEXT, taux_global REAL)")
    
    # En-têtes (Nom Entreprise, Adresse, Tel, RCCM)
    run_db("CREATE TABLE IF NOT EXISTS ent_infos (ent_id TEXT PRIMARY KEY, nom_boutique TEXT, adresse TEXT, telephone TEXT, rccm TEXT)")
    
    # Produits (Stock, Prix)
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_actuel INTEGER, prix_vente REAL, devise TEXT, ent_id TEXT)")
    
    # Ventes & Historique
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client TEXT, total REAL, paye REAL, reste REAL, devise TEXT, date_v TEXT, vendeur TEXT, ent_id TEXT, details_json TEXT)")
    
    # Dettes (Paiements échelonnés)
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, montant REAL, devise TEXT, ref_v TEXT, ent_id TEXT)")
    
    # Dépenses
    run_db("CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, devise TEXT, date_d TEXT, ent_id TEXT)")

    # Insertion Initiale Admin si vide
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role, ent_id, date_creation) VALUES (?,?,?,?,?)", 
               ('admin', make_hashes("admin123"), 'SUPER_ADMIN', 'SYSTEM', datetime.now().strftime("%d/%m/%Y")))
    
    if not run_db("SELECT * FROM system_config", fetch=True):
        run_db("INSERT INTO system_config (id, app_name, marquee_text, taux_global) VALUES (1, 'BALIKA ERP', 'BIENVENUE SUR BALIKA ERP v1500 - SOLUTION COMPLÈTE', 2850.0)")

init_db()

# ==============================================================================
# 3. INTERFACE VISUELLE & CSS (COULEURS & FORMAT MOBILE)
# ==============================================================================
cfg = run_db("SELECT app_name, marquee_text, taux_global FROM system_config WHERE id=1", fetch=True)
APP_NAME, MARQUEE, TX_G = cfg[0] if cfg else ("BALIKA", "Bienvenue", 2850.0)

st.markdown(f"""
    <style>
    /* Background Orange et Textes blancs demandés */
    .stApp {{ background-color: #FF8C00 !important; }}
    h1, h2, h3, p, label {{ color: white !important; }}
    
    /* Marquee Fixe en haut */
    .fixed-header {{ position: fixed; top: 0; left: 0; width: 100%; background: #000; color: #00FF00; height: 50px; z-index: 999999; display: flex; align-items: center; border-bottom: 2px solid white; }}
    marquee {{ font-size: 20px; font-weight: bold; font-family: 'Courier New'; padding-top: 5px; }}
    .spacer {{ margin-top: 60px; }}
    
    /* Boutons stylisés */
    .stButton>button {{ background-color: #0055ff !important; color: white !important; border-radius: 12px; font-weight: bold; height: 45px; width: 100%; border: 2px solid white; }}
    
    /* Cadre de couleur pour le total du panier */
    .total-frame {{ background: #000; color: #00FF00; padding: 20px; border: 4px solid #0055ff; border-radius: 15px; text-align: center; margin: 10px 0; }}
    
    /* Factures */
    .fac-80mm {{ background: white; color: black !important; padding: 10px; width: 300px; margin: auto; font-family: 'Courier New'; border: 1px solid black; font-size: 12px; }}
    .fac-80mm * {{ color: black !important; }}
    .fac-a4 {{ background: white; color: black !important; padding: 30px; width: 95%; margin: auto; border: 1px solid #ccc; font-family: Arial; }}
    .fac-a4 * {{ color: black !important; }}
    
    /* Inputs */
    div[data-baseweb="input"] {{ background: white !important; border-radius: 8px !important; }}
    input {{ color: black !important; font-weight: bold !important; }}
    </style>
    <div class="fixed-header"><marquee scrollamount="8">{MARQUEE}</marquee></div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

def get_entete():
    res = run_db("SELECT nom_boutique, adresse, telephone, rccm FROM ent_infos WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
    if res: return res[0]
    return (st.session_state.ent_id.upper(), "Adresse non définie", "0000", "RCCM-000")

# ==============================================================================
# 4. SYSTÈME D'AUTHENTIFICATION (MOBILE FRIENDLY)
# ==============================================================================
if not st.session_state.auth:
    st.markdown(f"<h1 align='center'>{APP_NAME}</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 CONNEXION", "🚀 CRÉER BOUTIQUE"])
    with t1:
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password")
        if st.button("ACCÉDER"):
            res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?", (u,), fetch=True)
            if res and make_hashes(p) == res[0][0]:
                if res[0][3] == "PAUSE": st.error("❌ Boutique Suspendue")
                else:
                    st.session_state.update({'auth':True, 'user':u, 'role':res[0][1], 'ent_id':res[0][2]})
                    st.rerun()
    with t2:
        nu = st.text_input("Nom de votre Boutique").lower().strip()
        nt = st.text_input("Téléphone Contact")
        np = st.text_input("Créer Mot de Passe", type="password")
        if st.button("LANCER MON ACTIVITÉ"):
            dc = datetime.now().strftime("%d/%m/%Y")
            run_db("INSERT INTO users (username, password, role, ent_id, telephone, date_creation) VALUES (?,?,?,?,?,?)", (nu, make_hashes(np), 'USER', nu, nt, dc))
            run_db("INSERT INTO ent_infos (ent_id, nom_boutique, telephone) VALUES (?,?,?)", (nu, nu.upper(), nt))
            st.success("Compte créé !")
    st.stop()

# ==============================================================================
# 5. MENU LATÉRAL
# ==============================================================================
with st.sidebar:
    u_pic = run_db("SELECT photo FROM users WHERE username=?", (st.session_state.user,), fetch=True)
    if u_pic and u_pic[0][0]: st.image(u_pic[0][0], width=100)
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    
    if st.session_state.role == "SUPER_ADMIN":
        menu = ["🏠 ACCUEIL", "👥 ABONNÉS", "🛠️ SYSTÈME"]
    elif st.session_state.role == "VENDEUR":
        menu = ["🏠 ACCUEIL", "🛒 CAISSE", "📉 DETTES"]
    else:
        menu = ["🏠 ACCUEIL", "📦 STOCK", "🛒 CAISSE", "📊 RAPPORTS", "📉 DETTES", "💸 DÉPENSES", "👥 VENDEURS", "⚙️ RÉGLAGES"]
    
    for item in menu:
        if st.button(item, use_container_width=True):
            st.session_state.page = item.split()[-1]
            st.rerun()
    
    if st.button("🚪 QUITTER"): st.session_state.auth = False; st.rerun()

# ==============================================================================
# 6. CŒUR DU SYSTÈME (FONCTIONS BOUTIQUE)
# ==============================================================================
if st.session_state.role != "SUPER_ADMIN":

    # --- ACCUEIL / DASHBOARD ---
    if st.session_state.page == "ACCUEIL":
        st.header("🏠 TABLEAU DE BORD")
        v_jr = run_db("SELECT SUM(total) FROM ventes WHERE ent_id=? AND date_v LIKE ?", (st.session_state.ent_id, f"{datetime.now().strftime('%d/%m/%Y')}%"), fetch=True)[0][0] or 0
        st.metric("Ventes du jour (USD)", f"{v_jr:,.2f} $")
        st.write(f"Vendeur actif : {st.session_state.user.upper()}")

    # --- STOCK (MODIFIER PRIX / SUPPRIMER SANS TOUCHER AUX LIGNES) ---
    elif st.session_state.page == "STOCK":
        st.header("📦 GESTION DU STOCK")
        with st.form("new_art"):
            c1, c2, c3 = st.columns(3)
            dn, sq, pv = c1.text_input("Désignation"), c2.number_input("Stock", 1), c3.number_input("Prix Vente $")
            if st.form_submit_button("AJOUTER AU STOCK"):
                run_db("INSERT INTO produits (designation, stock_actuel, prix_vente, devise, ent_id) VALUES (?,?,?,?,?)", (dn.upper(), sq, pv, "USD", st.session_state.ent_id)); st.rerun()
        
        prods = run_db("SELECT id, designation, stock_actuel, prix_vente FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
        for pi, pd, ps, pp in prods:
            with st.container(border=True):
                l1, l2, l3, l4, l5 = st.columns([3,1,1,1,1])
                un = l1.text_input("Nom", pd, key=f"n_{pi}")
                uq = l2.number_input("Qté", ps, key=f"q_{pi}")
                up = l3.number_input("Prix $", pp, key=f"p_{pi}")
                if l4.button("💾", key=f"s_{pi}"):
                    run_db("UPDATE produits SET designation=?, stock_actuel=?, prix_vente=? WHERE id=?", (un.upper(), uq, up, pi)); st.rerun()
                if l5.button("🗑️", key=f"d_{pi}"):
                    run_db("DELETE FROM produits WHERE id=?", (pi,)); st.rerun()

    # --- CAISSE (AUTOMATIQUE / CADRE TOTAL / PARTAGE / DEVISES) ---
    elif st.session_state.page == "CAISSE":
        if not st.session_state.last_fac:
            st.header("🛒 CAISSE")
            col_f, col_d = st.columns(2)
            fmt = col_f.radio("Format Facture", ["80mm", "A4"], horizontal=True)
            dev = col_d.radio("Monnaie", ["USD", "CDF"], horizontal=True)
            
            p_map = {p[0]: (p[1], p[2]) for p in run_db("SELECT designation, prix_vente, stock_actuel FROM produits WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)}
            sel = st.selectbox("Choisir Article", ["---"] + list(p_map.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                if p_map[sel][1] > 0: st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
                else: st.error("Stock épuisé !")

            if st.session_state.panier:
                tot = 0.0; items = []
                for a, q in list(st.session_state.panier.items()):
                    pu = p_map[a][0] if dev == "USD" else p_map[a][0] * TX_G
                    tot += pu * q
                    items.append({"art": a, "qty": q, "pu": pu})
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{a}** (Stock: {p_map[a][1]})")
                    st.session_state.panier[a] = c2.number_input("Qté", 1, p_map[a][1], value=q, key=f"ca_{a}")
                    if c3.button("❌", key=f"rm_{a}"): del st.session_state.panier[a]; st.rerun()
                
                # Cadre total coloré
                st.markdown(f'<div class="total-frame"><h2>TOTAL : {tot:,.2f} {dev}</h2></div>', unsafe_allow_html=True)
                
                client = st.text_input("Nom du Client", "COMPTANT")
                paye = st.number_input("Montant Reçu", value=float(tot))
                
                if st.button("✅ VALIDER LA VENTE"):
                    ref = f"FAC-{random.randint(1000,9999)}"
                    # Enregistrement Vente
                    run_db("INSERT INTO ventes (ref, client, total, paye, reste, devise, date_v, vendeur, ent_id, details_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ref, client.upper(), tot, paye, tot-paye, dev, datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.user, st.session_state.ent_id, json.dumps(items)))
                    # Si crédit, mise à jour auto dans DETTES
                    if tot-paye > 0: run_db("INSERT INTO dettes (client, montant, devise, ref_v, ent_id) VALUES (?,?,?,?,?)", (client.upper(), tot-paye, dev, ref, st.session_state.ent_id))
                    # Déduction Stock
                    for a, q in st.session_state.panier.items(): run_db("UPDATE produits SET stock_actuel=stock_actuel-? WHERE designation=? AND ent_id=?", (q, a, st.session_state.ent_id))
                    
                    st.session_state.update({'last_fac': {"ref":ref, "tot":tot, "dev":dev, "cli":client.upper(), "det":items, "paye":paye, "reste":tot-paye}, 'panier': {}, 'format_fac': fmt})
                    st.rerun()
        else:
            f = st.session_state.last_fac; e = get_entete()
            st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({'last_fac': None}))
            
            if st.session_state.format_fac == "80mm":
                html = f"""<div class="fac-80mm"><h3 align="center">{e[0]}</h3><p align="center">{e[1]}<br>{e[2]}</p><hr>
                <b>REF: {f['ref']}</b><br>Client: {f['cli']}<br>Vendeur: {st.session_state.user.upper()}<hr>
                {"".join([f"<p>{i['art']} x{i['qty']} : {i['pu']*i['qty']:,.0f} {f['dev']}</p>" for i in f['det']])}<hr>
                <h4 align="right">TOTAL: {f['tot']:,.2f} {f['dev']}</h4>
                <p>Payé: {f['paye']} | Reste: {f['reste']}</p></div>"""
            else:
                html = f"""<div class="fac-a4"><h2>{e[0]}</h2><p>{e[1]} | Tél: {e[2]} | RCCM: {e[3]}</p><hr>
                <h1>FACTURE {f['ref']}</h1><p>Client: {f['cli']} | Date: {datetime.now().strftime('%d/%m/%Y')}</p>
                <table width='100%' border='1' style='border-collapse:collapse;'><tr><th>Article</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td>{i['art']}</td><td align='center'>{i['qty']}</td><td>{i['pu']}</td><td>{i['pu']*i['qty']}</td></tr>" for i in f['det']])}</table>
                <h2 align='right'>TOTAL À PAYER : {f['tot']:,.2f} {f['dev']}</h2></div>"""
            
            st.markdown(html, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            if col1.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            col2.markdown(f'<a href="whatsapp://send?text=Facture {f["ref"]} de {e[0]} : {f["tot"]} {f["dev"]}" target="_blank"><button style="width:100%; height:45px; background:green; color:white; border-radius:10px; border:none; cursor:pointer;">📲 PARTAGER SUR WHATSAPP</button></a>', unsafe_allow_html=True)

    # --- DETTES (NOM RENOMMÉ + MAJ AUTO) ---
    elif st.session_state.page == "DETTES":
        st.header("📉 SUIVI DES DETTES CLIENTS")
        ds = run_db("SELECT id, client, montant, devise, ref_v FROM dettes WHERE ent_id=? AND montant > 0", (st.session_state.ent_id,), fetch=True)
        if not ds: st.info("Aucune dette en cours.")
        for di, dc, dm, dv, dr in ds:
            with st.container(border=True):
                st.write(f"👤 **{dc}** | **{dm:,.2f} {dv}** (Facture: {dr})")
                tranche = st.number_input("Montant à rembourser", 0.0, float(dm), key=f"pay_{di}")
                if st.button("ENREGISTRER PAIEMENT", key=f"btn_{di}"):
                    run_db("UPDATE dettes SET montant = montant - ? WHERE id=?", (tranche, di)); st.rerun()

    # --- VENDEURS (MODIFICATION) ---
    elif st.session_state.page == "VENDEURS":
        st.header("👥 GESTION DES VENDEURS")
        v_nom = st.text_input("Nom Vendeur")
        v_pass = st.text_input("Mot de Passe", type="password")
        if st.button("CRÉER COMPTE VENDEUR"):
            run_db("INSERT INTO users (username, password, role, ent_id) VALUES (?,?,?,?)", (v_nom.lower(), make_hashes(v_pass), 'VENDEUR', st.session_state.ent_id)); st.rerun()
        
        st.write("---")
        st.subheader("Liste des vendeurs")
        for u, r in run_db("SELECT username, role FROM users WHERE ent_id=? AND role='VENDEUR'", (st.session_state.ent_id,), fetch=True):
            with st.container(border=True):
                c1, c2 = st.columns([3,1])
                new_p = c1.text_input(f"Modifier mot de passe pour {u}", type="password", key=f"v_p_{u}")
                if c2.button("MAJ", key=f"v_b_{u}"):
                    run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(new_p), u)); st.success("Vendeur modifié")

    # --- RÉGLAGES (ENTREPRISE / PASS / RESET / SAVE) ---
    elif st.session_state.page == "RÉGLAGES":
        st.header("⚙️ PARAMÈTRES GÉNÉRAUX")
        e = get_entete()
        
        tab_ent, tab_sec, tab_data = st.tabs(["📝 EN-TÊTE", "🔒 SÉCURITÉ", "💾 DONNÉES"])
        
        with tab_ent:
            with st.form("set_ent"):
                n_nom = st.text_input("Nom de l'Entreprise", e[0])
                n_adr = st.text_input("Adresse Physique", e[1])
                n_tel = st.text_input("Téléphone", e[2])
                n_rcm = st.text_input("RCCM / ID Nat", e[3])
                if st.form_submit_button("SAUVEGARDER INFOS"):
                    run_db("INSERT OR REPLACE INTO ent_infos (ent_id, nom_boutique, adresse, telephone, rccm) VALUES (?,?,?,?,?)", (st.session_state.ent_id, n_nom, n_adr, n_tel, n_rcm)); st.rerun()
        
        with tab_sec:
            p_old = st.text_input("Mot de passe actuel", type="password")
            p_new = st.text_input("Nouveau mot de passe", type="password")
            if st.button("MODIFIER MON PASS"):
                curr = run_db("SELECT password FROM users WHERE username=?", (st.session_state.user,), fetch=True)
                if make_hashes(p_old) == curr[0][0]:
                    run_db("UPDATE users SET password=? WHERE username=?", (make_hashes(p_new), st.session_state.user)); st.success("Mot de passe changé")
        
        with tab_data:
            st.subheader("Sauvegarde")
            if st.button("EXPORTER VENTES CSV"):
                v_data = run_db("SELECT * FROM ventes WHERE ent_id=?", (st.session_state.ent_id,), fetch=True)
                st.download_button("Télécharger CSV", pd.DataFrame(v_data).to_csv(), "backup_ventes.csv")
            
            st.write("---")
            st.subheader("⚠️ ZONE DANGER")
            if st.button("💣 RÉINITIALISER COMPTE (EFFACER TOUT)"):
                run_db("DELETE FROM ventes WHERE ent_id=?", (st.session_state.ent_id,))
                run_db("DELETE FROM produits WHERE ent_id=?", (st.session_state.ent_id,))
                run_db("DELETE FROM dettes WHERE ent_id=?", (st.session_state.ent_id,))
                st.warning("Tout a été effacé."); st.rerun()

# ==============================================================================
# 7. INTERFACE SUPER ADMIN
# ==============================================================================
elif st.session_state.role == "SUPER_ADMIN":
    if st.session_state.page == "ABONNÉS":
        for u, s, t, d in run_db("SELECT username, status, telephone, date_creation FROM users WHERE role='USER'", fetch=True):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3,2,1])
                c1.write(f"🏢 **{u.upper()}** | 📞 {t}")
                c2.write(f"📅 {d} | Statut: {s}")
                if c3.button("PAUSE/PLAY", key=f"adm_{u}"):
                    ns = "PAUSE" if s == "ACTIF" else "ACTIF"
                    run_db("UPDATE users SET status=? WHERE username=?", (ns, u)); st.rerun()
    
    elif st.session_state.page == "SYSTÈME":
        with st.form("sys_adm"):
            nm = st.text_area("Message Marquee", MARQUEE)
            nt = st.number_input("Taux Change", value=TX_G)
            if st.form_submit_button("VALIDER"):
                run_db("UPDATE system_config SET marquee_text=?, taux_global=? WHERE id=1", (nm, nt)); st.rerun()
