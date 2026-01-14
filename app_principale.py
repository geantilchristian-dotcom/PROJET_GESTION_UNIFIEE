import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import io

# ==========================================
# 1. DESIGN & STYLE (STRICTE CONFORMITÉ)
# ==========================================
st.set_page_config(page_title="ANASH WEB 2026", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Fond global blanc */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Sidebar Bleu Foncé avec texte blanc */
    [data-testid="stSidebar"] { background-color: #002D62 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; font-weight: 800 !important; }

    /* CADRE DU TOTAL (COLORED FRAME) */
    .total-container {
        background: linear-gradient(135deg, #0047AB, #002D62);
        color: white !important;
        border-radius: 15px; 
        padding: 20px; 
        text-align: center; 
        margin-bottom: 25px;
        border: 4px solid #001A3A;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .total-label { font-size: 1.1rem; font-weight: bold; opacity: 0.9; }
    .total-montant { font-size: 3.2rem !important; font-weight: 900 !important; color: white !important; margin: 5px 0; line-height: 1; }
    .total-devise { font-size: 1.4rem; font-weight: bold; color: #FFD700 !important; }

    /* CODE : FOND BLEU / TEXTE BLANC */
    code, pre { 
        background-color: #0047AB !important; 
        color: white !important; 
        font-weight: bold; 
        padding: 15px; 
        border-radius: 8px; 
    }

    /* ZONE D'IMPRESSION PRO */
    #printable-area {
        background-color: white !important; 
        padding: 35px; 
        border: 2px solid #000;
        max-width: 700px; 
        margin: auto; 
        color: black !important; 
        font-family: 'Arial', sans-serif;
    }
    .print-header { border-bottom: 3px solid #002D62; text-align: center; margin-bottom: 20px; color: black !important; }
    
    @media print {
        body * { visibility: hidden; }
        #printable-area, #printable-area * { visibility: visible; }
        #printable-area { position: absolute; left: 0; top: 0; width: 100%; border: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. GESTION BASE DE DONNÉES
# ==========================================
DB_NAME = "anash_v41_final.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY, entreprise TEXT, entete_manuel TEXT, 
            taux REAL, pwd_admin TEXT, pwd_vendeur TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT, qte_actuel INTEGER, prix_v REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, date TEXT, client_info TEXT, 
            total_facture REAL, deja_paye REAL, devise TEXT, vendeur TEXT, items_json TEXT)""")
        if conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0] == 0:
            conn.execute("INSERT INTO settings VALUES (1, 'ANASH BUSINESS', 'Kinshasa, RDC\\nRCCM: 00-000-00', 2850.0, 'ADMIN', '1234')")
        conn.commit()

init_db()

def db_query(sql, params=(), select=True):
    with sqlite3.connect(DB_NAME) as conn:
        if select: return pd.read_sql_query(sql, conn, params=params)
        conn.execute(sql, params); conn.commit(); return True

# ==========================================
# 3. ÉTATS DE SESSION
# ==========================================
if "auth" not in st.session_state: st.session_state.auth = False
if "panier" not in st.session_state: st.session_state.panier = {}
if "etape" not in st.session_state: st.session_state.etape = "caisse"
if "temp_facture" not in st.session_state: st.session_state.temp_facture = None

CONFIG = db_query("SELECT * FROM settings WHERE id=1").iloc[0]

# --- LOGIN ---
if not st.session_state.auth:
    st.title("🔐 ACCÈS SYSTÈME")
    role_log = st.selectbox("Position", ["VENDEUR", "ADMIN"])
    pwd_log = st.text_input("Mot de passe", type="password")
    if st.button("🚀 SE CONNECTER", use_container_width=True):
        check = CONFIG['pwd_admin'] if role_log == "ADMIN" else CONFIG['pwd_vendeur']
        if pwd_log == str(check):
            st.session_state.auth, st.session_state.role = True, role_log
            st.rerun()
        else: st.error("Code erroné.")
    st.stop()

# ==========================================
# 4. NAVIGATION
# ==========================================
menu_list = ["🛒 CAISSE", "📉 DETTES", "📦 STOCK", "📊 RAPPORTS", "💰 CLÔTURE", "⚙️ CONFIG"]
if st.session_state.role == "VENDEUR":
    menu_list = ["🛒 CAISSE", "📉 DETTES", "📦 STOCK"]

menu = st.sidebar.radio("NAVIGATION", menu_list)
st.sidebar.divider()
if st.sidebar.button("🚪 Déconnexion"):
    st.session_state.clear(); st.rerun()

# --- 🛒 CAISSE ---
if menu == "🛒 CAISSE":
    devise = st.sidebar.selectbox("Devise d'encaissement", ["USD", "CDF"])
    total_usd = sum(v['pu'] * v['qty'] for v in st.session_state.panier.values())
    total_final = total_usd if devise == "USD" else total_usd * CONFIG['taux']

    if st.session_state.etape == "facture" and st.session_state.temp_facture:
        f = st.session_state.temp_facture
        reste = f['total'] - f['paye']
        
        st.markdown(f"""
            <div id="printable-area">
                <div class="print-header"><h1>{CONFIG['entreprise']}</h1>{CONFIG['entete_manuel']}</div>
                <div style="display:flex; justify-content:space-between; color:black;">
                    <p><b>CLIENT :</b> {f['client']}</p>
                    <p><b>RÉF :</b> {f['ref']}<br><b>DATE :</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                </div>
                <table style="width:100%; color:black; border-collapse:collapse; margin-top:10px;">
                    <tr style="border-bottom:2px solid black; background:#f2f2f2;">
                        <th style="padding:8px; text-align:left;">Désignation</th>
                        <th style="padding:8px;">Qté</th>
                        <th style="padding:8px; text-align:right;">Total</th>
                    </tr>
                    {"".join([f"<tr><td style='padding:8px; border-bottom:1px solid #ddd;'>{v['nom']}</td><td align='center'>{v['qty']}</td><td align='right'>{int(v['qty']*v['pu']):,} {f['devise']}</td></tr>" for v in f['items']])}
                </table>
                <div style="text-align:right; margin-top:20px; color:black; font-weight:bold; font-size:1.2rem; border-top:2px solid black; padding-top:10px;">
                    TOTAL : {int(f['total']):,} {f['devise']}<br>
                    PAYÉ : {int(f['paye']):,} {f['devise']}<br>
                    <span style="color:red;">RESTE : {int(reste):,} {f['devise']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        if c1.button("💾 ENREGISTRER LA VENTE", use_container_width=True):
            items_txt = ", ".join([f"{v['nom']} (x{v['qty']})" for v in f['items']])
            db_query("INSERT INTO ventes (ref, date, client_info, total_facture, deja_paye, devise, vendeur, items_json) VALUES (?,?,?,?,?,?,?,?)",
                     (f['ref'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f['client'], f['total'], f['paye'], f['devise'], st.session_state.role, items_txt), False)
            st.session_state.panier, st.session_state.etape, st.session_state.temp_facture = {}, "caisse", None
            st.rerun()
        if c2.button("🖨️ IMPRIMER", use_container_width=True):
            components.html("<script>window.print();</script>", height=0)
        if c3.button("🔙 RETOUR PANIER", use_container_width=True):
            st.session_state.etape = "caisse"; st.rerun()

    else:
        # CADRE TOTAL COLORÉ
        m_alt = int(total_usd * CONFIG['taux']) if devise == "USD" else int(total_usd / CONFIG['taux'])
        d_alt = "CDF" if devise == "USD" else "USD"
        st.markdown(f"<div class='total-container'><div class='total-label'>MONTANT À PAYER</div><div class='total-montant'>{int(total_final):,}</div><div class='total-devise'>{devise} | {m_alt:,} {d_alt}</div></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1.3])
        with col1:
            st.write("### ➕ Articles")
            df_s = db_query("SELECT * FROM stock")
            art = st.selectbox("Sélectionner l'article", ["---"] + df_s['designation'].tolist())
            if st.button("➕ Ajouter au Panier", use_container_width=True) and art != "---":
                row = df_s[df_s['designation'] == art].iloc[0]
                pu_it = row['prix_v'] if devise == "USD" else row['prix_v'] * CONFIG['taux']
                st.session_state.panier[str(row['id'])] = {'nom': art, 'pu': pu_it, 'qty': 1}
                st.rerun()
        with col2:
            st.write("### 🛒 Mon Panier")
            cli = st.text_input("Nom du Client")
            p_recu = st.number_input(f"Acompte Versé ({devise})", 0.0)
            for k, v in list(st.session_state.panier.items()):
                ca, cb = st.columns([4, 1])
                v['qty'] = ca.number_input(f"{v['nom']}", 1, 1000, v['qty'], key=f"q_{k}")
                if cb.button("🗑️", key=f"d_{k}"): del st.session_state.panier[k]; st.rerun()
            if st.button("🏁 PRÉPARER FACTURE", use_container_width=True) and cli and st.session_state.panier:
                st.session_state.temp_facture = {"ref": f"FAC-{datetime.now().strftime('%H%M%S')}", "client": cli, "items": list(st.session_state.panier.values()), "total": total_final, "devise": devise, "paye": p_recu}
                st.session_state.etape = "facture"; st.rerun()

# --- 💰 CLÔTURE (ADMIN) ---
elif menu == "💰 CLÔTURE":
    st.title("💰 CLÔTURE JOURNALIÈRE")
    dt = st.date_input("Date du rapport", datetime.now()).strftime('%Y-%m-%d')
    df_j = db_query(f"SELECT * FROM ventes WHERE date LIKE '{dt}%'")
    
    if not df_j.empty:
        c_usd = df_j[df_j['devise'] == 'USD']['deja_paye'].sum()
        c_cdf = df_j[df_j['devise'] == 'CDF']['deja_paye'].sum()
        
        st.markdown(f"""
            <div id="printable-area">
                <div class="print-header"><h1>RAPPORT DE CAISSE - {dt}</h1><b>{CONFIG['entreprise']}</b></div>
                <h3 style="color:black;">RÉSUMÉ CASH</h3>
                <p style="font-size:1.5rem; color:black;"><b>TOTAL USD : {int(c_usd):,} $</b></p>
                <p style="font-size:1.5rem; color:black;"><b>TOTAL CDF : {int(c_cdf):,} FC</b></p>
                <hr>
                <h3 style="color:black;">DÉTAIL DES ARTICLES SORTIS</h3>
                <table style="width:100%; color:black; border-collapse:collapse;">
                    <tr style="background:#eee;"><th>Réf</th><th>Client</th><th>Articles</th><th align="right">Montant</th></tr>
                    {"".join([f"<tr><td>{r['ref']}</td><td>{r['client_info']}</td><td>{r['items_json']}</td><td align='right'>{int(r['total_facture'])} {r['devise']}</td></tr>" for _, r in df_j.iterrows()])}
                </table>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER LE RAPPORT"):
            components.html("<script>window.print();</script>", height=0)
    else: st.warning("Aucune transaction pour cette date.")

# --- 📊 RAPPORTS (SUPPRESSION) ---
elif menu == "📊 RAPPORTS":
    st.title("📊 HISTORIQUE DES VENTES")
    df_v = db_query("SELECT * FROM ventes ORDER BY id DESC")
    st.dataframe(df_v, use_container_width=True)
    
    if st.session_state.role == "ADMIN":
        st.divider()
        st.subheader("⚠️ SUPPRIMER UNE ERREUR")
        ref_sel = st.selectbox("Référence Facture", ["---"] + df_v['ref'].tolist())
        if st.button("🔥 SUPPRIMER DÉFINITIVEMENT") and ref_sel != "---":
            db_query("DELETE FROM ventes WHERE ref = ?", (ref_sel,), False)
            st.success("Vente effacée !"); st.rerun()

# --- 📦 STOCK ---
elif menu == "📦 STOCK":
    st.title("📦 GESTION DU STOCK")
    if st.session_state.role == "ADMIN":
        with st.form("stock"):
            d, q, p = st.text_input("Désignation"), st.number_input("Qté initiale", 0), st.number_input("Prix Vente ($)", 0.0)
            if st.form_submit_button("💾 Enregistrer"):
                db_query("INSERT INTO stock (designation, qte_actuel, prix_v) VALUES (?,?,?)", (d, q, p), False); st.rerun()
    st.dataframe(db_query("SELECT * FROM stock"), use_container_width=True)

# --- 📉 DETTES ---
elif menu == "📉 DETTES":
    st.title("📉 LISTE DES CRÉDITS")
    df_d = db_query("SELECT ref, date, client_info, (total_facture - deja_paye) as Reste, devise FROM ventes WHERE Reste > 0.1")
    st.dataframe(df_d, use_container_width=True)

# --- ⚙️ CONFIG ---
elif menu == "⚙️ CONFIG":
    st.title("⚙️ PARAMÈTRES")
    with st.form("config"):
        n = st.text_input("Entreprise", CONFIG['entreprise'])
        e = st.text_area("Entête", CONFIG['entete_manuel'])
        t = st.number_input("Taux", value=float(CONFIG['taux']))
        if st.form_submit_button("Mettre à jour"):
            db_query("UPDATE settings SET entreprise=?, entete_manuel=?, taux=? WHERE id=1", (n, e, t), False); st.rerun()
    with open(DB_NAME, "rb") as f:
        st.download_button("📥 BACKUP (.db)", f, file_name="anash_db.db")