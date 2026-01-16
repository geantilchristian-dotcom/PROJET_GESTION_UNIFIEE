import streamlit as st
import pandas as pd
from datetime import datetime
import random
import hashlib
import httpx

# ==========================================
# 1. CONFIGURATION & SÉCURITÉ (v230)
# ==========================================
st.set_page_config(page_title="BALIKA ERP PRO", layout="wide", initial_sidebar_state="collapsed")

SUPABASE_URL = "https://ngrjinsorpxqkeajfufd.supabase.co"
SUPABASE_KEY = "sb_publishable__9hjGqGla0UU-Y9L-zOBRA_zG0rrbWJ"

@st.cache_data(ttl=2)
def query_cloud(table, params_str=None):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = dict(item.split('=') for item in params_str.split('&')) if params_str else {}
    try:
        with httpx.Client(timeout=20.0) as client:
            res = client.get(url, headers=headers, params=params)
            return res.json() if res.status_code == 200 else []
    except: return []

def run_action(table, method, data=None, params=None):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        with httpx.Client(timeout=20.0) as client:
            if method == "POST": return client.post(url, headers=headers, json=data)
            if method == "PATCH": return client.patch(url, headers=headers, json=data, params=params)
            if method == "DELETE": return client.delete(url, headers=headers, params=params)
    except: return None

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# Initialisation complète des états
for k, v in {'auth': False, 'panier': {}, 'page': "ACCUEIL", 'role': "VENDEUR", 'user': "", 'last_fac': None}.items():
    if k not in st.session_state: st.session_state[k] = v

# Chargement Config Dynamique
cfg = query_cloud("config", "id=eq.1")
C_ENT = cfg[0]['entreprise'] if cfg else "BALIKA ERP"
C_TAUX = cfg[0]['taux'] if cfg else 2850.0
C_ADR = cfg[0]['adresse'] if cfg else "ADRESSE"
C_TEL = cfg[0]['telephone'] if cfg else "000"
C_MSG = cfg[0]['message'] if cfg else "BIENVENUE CHEZ BALIKA"

# ==========================================
# 2. DESIGN MOBILE & ANTI-BLANC CSS
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF !important; color: #000000 !important; }}
    h1, h2, h3, h4, p, span, label, div {{ color: #000000 !important; }}
    .stButton>button {{ 
        background: orange !important; color: white !important; border-radius: 12px !important; 
        height: 60px !important; font-weight: bold !important; width: 100%; border: none !important;
    }}
    .total-box {{ border: 3px solid orange; background: #FFF3E0; padding: 20px; border-radius: 15px; text-align: center; font-size: 26px; font-weight: bold; color: #E65100 !important; }}
    .marquee-container {{ background: #333; color: orange; padding: 12px; font-weight: bold; overflow: hidden; }}
    .print-area {{ background: white; color: black; padding: 15px; border: 1px solid #ddd; font-family: monospace; }}
    input {{ background-color: white !important; color: black !important; border: 2px solid orange !important; border-radius: 10px !important; }}
    </style>
    <div class="marquee-container"><center>{C_MSG}</center></div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTIFICATION
# ==========================================
if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>🔐 CONNEXION</h2>", unsafe_allow_html=True)
    u = st.text_input("Identifiant").lower().strip()
    p = st.text_input("Mot de passe", type="password").strip()
    if st.button("SE CONNECTER"):
        run_action("users", "POST", {"username": "admin", "password": make_hashes("admin123"), "role": "ADMIN"})
        res = query_cloud("users", f"username=eq.{u}")
        if res and make_hashes(p) == res[0]['password']:
            st.session_state.update({"auth": True, "user": u, "role": res[0]['role']})
            st.rerun()
        else: st.error("Accès refusé.")
    st.stop()

# ==========================================
# 4. NAVIGATION MOBILE
# ==========================================
with st.sidebar:
    st.write(f"👤 {st.session_state.user.upper()} ({st.session_state.role})")
    menu = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        menu.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 USERS": "USERS", "⚙️ CONFIG": "CONFIG"})
    for l, p in menu.items():
        if st.button(l, use_container_width=True): st.session_state.page = p; st.rerun()
    if st.button("🚪 QUITTER"): st.session_state.auth = False; st.rerun()

# ==========================================
# 5. LOGIQUE DES MODULES
# ==========================================

# --- DASHBOARD ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f"<center><h1 style='font-size:60px;'>⌚ {datetime.now().strftime('%H:%M')}</h1><h3>{C_ENT}</h3></center>", unsafe_allow_html=True)
    v = query_cloud("ventes")
    if v:
        df = pd.DataFrame(v)
        st.metric("Ventes USD", f"{df[df['devise']=='USD']['total_val'].sum():,.2f}")
        st.metric("Ventes CDF", f"{df[df['devise']=='CDF']['total_val'].sum():,.0f}")

# --- CAISSE & FACTURE (Version 80mm Incluse) ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse Mobile")
        devise_v = st.radio("Devise", ["USD", "CDF"], horizontal=True)
        prods = query_cloud("produits", "stock_actuel=gt.0")
        if prods:
            imap = {r['designation']: r for r in prods}
            sel = st.selectbox("Article", ["---"] + list(imap.keys()))
            if st.button("➕ AJOUTER") and sel != "---":
                st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
                st.rerun()
            
            if st.session_state.panier:
                total = 0.0; details = []; items_txt = []
                for art, qte in list(st.session_state.panier.items()):
                    p_orig = imap[art]['prix_vente']
                    p_f = p_orig * C_TAUX if imap[art]['devise_origine']=="USD" and devise_v=="CDF" else (p_orig / C_TAUX if imap[art]['devise_origine']=="CDF" and devise_v=="USD" else p_orig)
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{art}**\n{p_f:,.2f} {devise_v}")
                    nq = c2.number_input("Qté", 1, value=qte, key=f"q_{art}")
                    st.session_state.panier[art] = nq
                    if c3.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
                    
                    total += (p_f * nq)
                    details.append({'art': art, 'qte': nq, 'pu': p_f, 'st': p_f * nq})
                    items_txt.append(f"{art}(x{nq})")
                
                st.markdown(f"<div class='total-box'>TOTAL : {total:,.2f} {devise_v}</div>", unsafe_allow_html=True)
                nom_c = st.text_input("NOM CLIENT").upper()
                paye = st.number_input("PAYÉ (ACOMPTE)", 0.0)
                
                if st.button("✅ VALIDER LA VENTE") and nom_c:
                    ref = f"FAC-{random.randint(1000,9999)}"
                    now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    run_action("ventes", "POST", {"ref": ref, "client_nom": nom_c, "total_val": total, "acompte": paye, "reste": total-paye, "details": str(details), "devise": devise_v, "date_v": now})
                    if (total-paye) > 0.1:
                        run_action("dettes", "POST", {"client_nom": nom_c, "montant_du": total-paye, "devise": devise_v, "articles": ", ".join(items_txt), "sale_ref": ref, "date_d": now})
                    for d in details:
                        run_action("produits", "PATCH", {"stock_actuel": imap[d['art']]['stock_actuel']-d['qte']}, f"id=eq.{imap[d['art']]['id']}")
                    st.session_state.last_fac = {"ref": ref, "cl": nom_c, "tot": total, "ac": paye, "re": total-paye, "dev": devise_v, "lines": details, "date": now}
                    st.session_state.panier = {}; st.rerun()
    else:
        f = st.session_state.last_fac
        st.button("⬅️ RETOUR", on_click=lambda: st.session_state.update({"last_fac": None}))
        st.markdown(f"""<div class="print-area"><center><h2>{C_ENT}</h2><p>{C_ADR}<br>{C_TEL}</p></center><hr>
            <b>REF: {f['ref']}</b><br>Client: {f['cl']}<br>Date: {f['date']}<hr>
            <table style="width:100%;">{"".join([f"<tr><td>{l['art']} x{l['qte']}</td><td style='text-align:right;'>{l['st']:,.2f}</td></tr>" for l in f['lines']])}</table><hr>
            <h4 style="text-align:right;">TOTAL: {f['tot']:,.2f} {f['dev']}</h4>
            <p style="text-align:right;">Reste: {f['re']:,.2f}</p></div>""", unsafe_allow_html=True)
        if st.button("🖨️ IMPRIMER"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# --- DETTES PAR TRANCHES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Suivi des Dettes")
    for d in query_cloud("dettes"):
        with st.expander(f"👤 {d['client_nom']} | Reste: {d['montant_du']:,.2f} {d['devise']}"):
            v = st.number_input("Versement", 0.0, float(d['montant_du']), key=f"v_{d['id']}")
            if st.button("Valider Paiement", key=f"b_{d['id']}"):
                r = d['montant_du'] - v
                if r <= 0.1: run_action("dettes", "DELETE", params=f"id=eq.{d['id']}")
                else: run_action("dettes", "PATCH", {"montant_du": r}, f"id=eq.{d['id']}")
                st.success("Payé !"); st.rerun()

# --- STOCK AVEC SUPPRESSION ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion Stock")
    with st.form("s"):
        n = st.text_input("Nom"); p = st.number_input("Prix"); d = st.selectbox("Devise", ["USD", "CDF"]); q = st.number_input("Qté", 1)
        if st.form_submit_button("AJOUTER"):
            run_action("produits", "POST", {"designation": n.upper(), "stock_actuel": q, "prix_vente": p, "devise_origine": d})
            st.rerun()
    for r in query_cloud("produits"):
        c1, c2 = st.columns([4,1])
        c1.write(f"**{r['designation']}** | Stock: {r['stock_actuel']}")
        if c2.button("🗑️", key=f"p_{r['id']}"): run_action("produits", "DELETE", f"id=eq.{r['id']}"); st.rerun()

# --- CONFIG & SÉCURITÉ ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Configuration")
    with st.form("cfg"):
        en = st.text_input("Entreprise", C_ENT); ad = st.text_input("Adresse", C_ADR); tl = st.text_input("Tél", C_TEL); tx = st.number_input("Taux", value=C_TAUX)
        if st.form_submit_button("SAUVEGARDER"):
            run_action("config", "PATCH", {"entreprise": en.upper(), "adresse": ad, "telephone": tl, "taux": tx}, "id=eq.1")
            st.rerun()
    st.write("---")
    new_p = st.text_input("Nouveau Pass Admin", type="password")
    if st.button("CHANGER MOT DE PASSE"):
        run_action("users", "PATCH", {"password": make_hashes(new_p)}, "username=eq.admin")
        st.success("Modifié !")
