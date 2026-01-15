import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import hashlib

# ==========================================
# 1. CONFIGURATION VISUELLE (STYLE V192+)
# ==========================================
st.set_page_config(page_title="BALIKA ERP v197", layout="wide", initial_sidebar_state="expanded")

def get_marquee():
    try:
        with sqlite3.connect('anash_data.db') as conn:
            res = conn.execute("SELECT message FROM config WHERE id=1").fetchone()
            return res[0] if res else "Bienvenue chez BALIKA ERP"
    except: return "Bienvenue chez BALIKA ERP"

m_text = get_marquee()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #F4F7F9 !important; }}
    code {{ color: white !important; background-color: #0047AB !important; padding: 3px 8px; border-radius: 6px; font-weight: bold; }}
    
    /* Marquee v192 */
    .marquee-container {{ width: 100%; overflow: hidden; background: #0047AB; color: white; padding: 12px 0; font-weight: bold; border-radius: 8px; margin-bottom: 20px; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 25s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

    /* Facture Administrative Pro */
    .invoice-box {{ padding: 30px; border: 2px solid #333; background: white; color: black; font-family: 'Arial', sans-serif; margin: auto; max-width: 800px; }}
    .invoice-header {{ border-bottom: 3px solid #000; margin-bottom: 20px; padding-bottom: 10px; text-align: center; }}
    
    /* Tableaux Tracés */
    .pro-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; border: 1px solid #333; }}
    .pro-table th {{ background-color: #0047AB; color: white; padding: 10px; border: 1px solid #333; text-align: left; }}
    .pro-table td {{ padding: 8px; border: 1px solid #333; }}

    /* Case Dette Individuelle */
    .debt-card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 10px solid #FF4B4B; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}

    /* Total Frame v192 */
    .total-frame {{ background-color: #0047AB; color: white !important; padding: 25px; border-radius: 15px; border: 5px solid #FF4B4B; text-align: center; font-size: 30px; font-weight: bold; margin: 20px 0; }}

    @media print {{ .no-print {{ display: none !important; }} .print-area {{ display: block !important; width: 100% !important; }} }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{m_text}</div></div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MOTEUR DE DONNÉES & RÉPARATION (MIGRATION)
# ==========================================
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

def run_db(query, params=(), fetch=False):
    with sqlite3.connect('anash_data.db', timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall() if fetch else None

def init_db():
    # Création des tables
    run_db("CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, stock_initial INTEGER, stock_actuel INTEGER, prix_vente REAL, devise_origine TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, client_nom TEXT, client_tel TEXT, total_val REAL, acompte REAL, reste REAL, details TEXT, statut TEXT, devise TEXT, date_v TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, client_tel TEXT, montant_du REAL, devise TEXT, articles TEXT, sale_ref TEXT, date_d TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, entreprise TEXT, adresse TEXT, telephone TEXT, rccm TEXT, nif TEXT, id_nat TEXT, taux REAL, message TEXT)")
    run_db("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, avatar BLOB)")
    
    # --- RÉPARATION DE LA TABLE DETTES (AJOUT DES COLONNES MANQUANTES) ---
    infos = run_db("PRAGMA table_info(dettes)", fetch=True)
    cols = [i[1] for i in infos]
    if 'articles' not in cols:
        try: run_db("ALTER TABLE dettes ADD COLUMN articles TEXT")
        except: pass
    if 'client_tel' not in cols:
        try: run_db("ALTER TABLE dettes ADD COLUMN client_tel TEXT")
        except: pass

    # Admin par défaut
    if not run_db("SELECT * FROM users WHERE username='admin'", fetch=True):
        run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", ("admin", make_hashes("admin123"), "ADMIN"))
    
    if not run_db("SELECT * FROM config WHERE id=1", fetch=True):
        run_db("INSERT INTO config (id, entreprise, adresse, telephone, rccm, nif, id_nat, taux, message) VALUES (1, 'BALIKA ERP', 'VOTRE ADRESSE', '000', '0', '0', '0', 2850.0, 'Bienvenue')")

init_db()

# Chargement Config
cfg = run_db("SELECT * FROM config WHERE id=1", fetch=True)[0]
C_ENT, C_ADR, C_TEL, C_RCCM, C_NIF, C_IDNAT, C_TAUX, C_MSG = cfg[1], cfg[2], cfg[3], cfg[4], cfg[5], cfg[6], cfg[7], cfg[8]

if 'auth' not in st.session_state: st.session_state.auth = False
if 'panier' not in st.session_state: st.session_state.panier = {}
if 'page' not in st.session_state: st.session_state.page = "ACCUEIL"
if 'last_fac' not in st.session_state: st.session_state.last_fac = None

# ==========================================
# 3. ÉCRAN DE CONNEXION
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>🔐 {C_ENT}</h1>", unsafe_allow_html=True)
        u_in = st.text_input("Identifiant").lower().strip()
        p_in = st.text_input("Mot de passe", type="password").strip()
        if st.button("SE CONNECTER", use_container_width=True):
            res = run_db("SELECT password, role, avatar FROM users WHERE username=?", (u_in,), fetch=True)
            if res and make_hashes(p_in) == res[0][0]:
                st.session_state.auth, st.session_state.role, st.session_state.user, st.session_state.avatar = True, res[0][1], u_in, res[0][2]
                st.rerun()
            else: st.error("Accès refusé.")
    st.stop()

# ==========================================
# 4. MENU LATÉRAL
# ==========================================
with st.sidebar:
    if st.session_state.avatar: st.image(st.session_state.avatar, width=100)
    st.title(st.session_state.user.upper())
    st.write("---")
    btns = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📦 STOCK": "STOCK", "📉 DETTES": "DETTES", "📊 RAPPORTS": "RAPPORT", "⚙️ PARAMÈTRES": "CONFIG"}
    for label, pg in btns.items():
        if st.session_state.role != "ADMIN" and pg in ["RAPPORT", "CONFIG"]: continue
        if st.button(label, use_container_width=True): st.session_state.page = pg; st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION"): st.session_state.auth = False; st.rerun()

# ==========================================
# 5. LOGIQUE DES PAGES
# ==========================================

# --- DASHBOARD ---
if st.session_state.page == "ACCUEIL":
    st.title(f"📊 Dashboard - {C_ENT}")
    v_rows = run_db("SELECT total_val, devise, reste, date_v FROM ventes", fetch=True)
    df = pd.DataFrame(v_rows, columns=["total", "devise", "reste", "date"])
    c1, c2, c3 = st.columns(3)
    if not df.empty:
        c1.metric("Ventes USD", f"{df[df['devise']=='USD']['total'].sum():,.2f} $")
        c2.metric("Ventes CDF", f"{df[df['devise']=='CDF']['total'].sum():,.0f} FC")
        c3.metric("Dettes Clients", f"{df['reste'].sum():,.2f}")
        st.subheader("Graphique des ventes")
        st.line_chart(df.groupby('date')['total'].sum())

# --- CAISSE & FACTURE ADMINISTRATIVE ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse")
        col_g, col_d = st.columns([1, 1.5])
        with col_g:
            m_v = st.radio("MONNAIE", ["USD", "CDF"], horizontal=True)
            prods = run_db("SELECT designation, prix_vente, stock_actuel, devise_origine FROM produits WHERE stock_actuel > 0", fetch=True)
            imap = {r[0]: {'p': r[1], 's': r[2], 'd': r[3]} for r in prods}
            sel = st.selectbox("Article", ["---"] + list(imap.keys()))
            if st.button("AJOUTER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1; st.rerun()
        with col_d:
            total = 0.0; details = []; art_names = []
            for art, qte in list(st.session_state.panier.items()):
                p_b, d_b = imap[art]['p'], imap[art]['d']
                p_f = p_b * C_TAUX if (d_b == "USD" and m_v == "CDF") else p_b / C_TAUX if (d_b == "CDF" and m_v == "USD") else p_b
                total += (p_f * qte); details.append({'art': art, 'qte': qte, 'pu': p_f, 'st': p_f*qte}); art_names.append(f"{art}(x{qte})")
                r = st.columns([3, 1, 1, 1])
                r[0].write(f"**{art}**")
                if r[1].button("➖", key=f"m_{art}"):
                    if qte > 1: st.session_state.panier[art] -= 1
                    else: del st.session_state.panier[art]
                    st.rerun()
                r[2].write(f"{qte}")
                if r[3].button("➕", key=f"p_{art}"):
                    if qte < imap[art]['s']: st.session_state.panier[art] += 1; st.rerun()
            if st.session_state.panier:
                st.markdown(f'<div class="total-frame">NET À PAYER : {total:,.2f} {m_v}</div>', unsafe_allow_html=True)
                cl_n = st.text_input("Nom Client").upper(); cl_t = st.text_input("Tél Client")
                paye = st.number_input("Montant Reçu", 0.0)
                if st.button("VALIDER VENTE") and cl_n:
                    ref = f"FAC-{random.randint(1000,9999)}"; d_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_db("INSERT INTO ventes (ref, client_nom, client_tel, total_val, acompte, reste, details, statut, devise, date_v) VALUES (?,?,?,?,?,?,?,?,?,?)", (ref, cl_n, cl_t, total, paye, total-paye, str(details), "SOLDE", m_v, d_now))
                    if total-paye > 0:
                        run_db("INSERT INTO dettes (client_nom, client_tel, montant_du, devise, articles, sale_ref, date_d) VALUES (?,?,?,?,?,?,?)", (cl_n, cl_t, total-paye, m_v, ", ".join(art_names), ref, d_now))
                    for d in details: run_db("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE designation = ?", (d['qte'], d['art']))
                    st.session_state.last_fac = {"ref": ref, "cl": cl_n, "tel": cl_t, "tot": total, "ac": paye, "re": total-paye, "dev": m_v, "lines": details, "date": d_now}
                    st.session_state.panier = {}; st.rerun()
    else:
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        f = st.session_state.last_fac
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="print-area invoice-box">
            <div class="invoice-header">
                <h2>{C_ENT}</h2><p>{C_ADR} | Tél: {C_TEL}<br>RCCM: {C_RCCM} | NIF: {C_NIF} | IDNAT: {C_IDNAT}</p>
            </div>
            <p><b>REF:</b> {f["ref"]} | <b>Date:</b> {f["date"]}</p>
            <p><b>Client:</b> {f["cl"]} | <b>Tél:</b> {f["tel"]}</p>
            <table class="pro-table">
                <tr><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                {"".join([f"<tr><td>{l['art']}</td><td>{l['qte']}</td><td>{l['pu']:,.2f}</td><td>{l['st']:,.2f}</td></tr>" for l in f['lines']])}
            </table>
            <div style="text-align:right; margin-top:15px;">
                <h3>NET À PAYER : {f["tot"]:,.2f} {f["dev"]}</h3>
                <p>Acompte: {f["ac"]:,.2f} | Reste: {f["re"]:,.2f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- DETTES (PAR CASE CLIENT) ---
elif st.session_state.page == "DETTES":
    st.title("📉 Dettes Clients")
    dettes = run_db("SELECT id, client_nom, client_tel, montant_du, devise, articles, date_d, sale_ref FROM dettes", fetch=True)
    if not dettes: st.info("Aucune dette.")
    for d in dettes:
        with st.container():
            st.markdown(f"""
            <div class="debt-card">
                <h3>👤 {d[1]} | 📞 {d[2]}</h3>
                <p><b>Articles:</b> {d[5]}</p>
                <p><b>Facture:</b> {d[7]} | <b>Date:</b> {d[6]}</p>
                <h2 style="color:#FF4B4B;">RESTE À PAYER : {d[3]:,.2f} {d[4]}</h2>
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns([2, 1])
            p_val = c1.number_input(f"Montant versé par {d[1]}", 0.0, float(d[3]), key=f"p_{d[0]}")
            if c2.button("ENCAISSER", key=f"b_{d[0]}", use_container_width=True):
                if d[3] - p_val <= 0.1: run_db("DELETE FROM dettes WHERE id=?", (d[0],))
                else: run_db("UPDATE dettes SET montant_du = montant_du - ? WHERE id=?", (p_val, d[0]))
                run_db("UPDATE ventes SET reste = reste - ? WHERE ref=?", (p_val, d[7]))
                st.success("Paiement validé !"); st.rerun()

# --- STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Stock")
    with st.form("add_p"):
        c1, c2, c3, c4 = st.columns(4)
        n, p, d, q = c1.text_input("Nom"), c2.number_input("Prix"), c3.selectbox("Devise", ["USD", "CDF"]), c4.number_input("Qté", 1)
        if st.form_submit_button("AJOUTER"):
            run_db("INSERT INTO produits (designation, stock_initial, stock_actuel, prix_vente, devise_origine) VALUES (?,?,?,?,?)", (n.upper(), q, q, p, d)); st.rerun()
    prods = run_db("SELECT id, designation, stock_actuel, prix_vente, devise_origine FROM produits", fetch=True)
    for p in prods:
        st.write(f"**{p[1]}** | En Stock: {p[2]} | Prix: {p[3]} {p[4]}")
        if st.button(f"🗑️ Supprimer {p[1]}", key=f"del_{p[0]}"): run_db("DELETE FROM produits WHERE id=?", (p[0],)); st.rerun()

# --- RAPPORTS ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Rapports des Ventes")
    data = run_db("SELECT ref, client_nom, total_val, date_v, reste FROM ventes", fetch=True)
    if data:
        df_r = pd.DataFrame(data, columns=["Réf", "Client", "Total", "Date", "Reste"])
        st.dataframe(df_r, use_container_width=True)
        st.download_button("Télécharger CSV", df_r.to_csv(index=False).encode('utf-8'), "rapport.csv")

# --- CONFIG ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres")
    e1 = st.text_input("Société", C_ENT); e2 = st.text_input("Adresse", C_ADR); e3 = st.text_input("Tél", C_TEL)
    r, n, i = st.columns(3); rccm = r.text_input("RCCM", C_RCCM); nif = n.text_input("NIF", C_NIF); idnat = i.text_input("ID NAT", C_IDNAT)
    tx = st.number_input("Taux de change (1$ = X FC)", value=C_TAUX); m = st.text_area("Message Marquee", C_MSG)
    if st.button("SAUVEGARDER CONFIG"):
        run_db("UPDATE config SET entreprise=?, adresse=?, telephone=?, rccm=?, nif=?, id_nat=?, taux=?, message=? WHERE id=1", (e1.upper(), e2, e3, rccm, nif, idnat, tx, m)); st.rerun()
    st.write("---")
    v_u = st.text_input("Nom Vendeur"); v_p = st.text_input("Code", type="password")
    if st.button("CRÉER COMPTE VENDEUR"):
        run_db("INSERT INTO users (username, password, role) VALUES (?,?,?)", (v_u.lower(), make_hashes(v_p), "USER")); st.success("Compte créé.")