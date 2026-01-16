import streamlit as st
import pandas as pd
from datetime import datetime
import random
import hashlib
import httpx

# ==========================================
# 1. OPTIMISATION TURBO & MOBILE (v220)
# ==========================================
st.set_page_config(
    page_title="BALIKA ERP", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = "https://ngrjinsorpxqkeajfufd.supabase.co"
SUPABASE_KEY = "sb_publishable__9hjGqGla0UU-Y9L-zOBRA_zG0rrbWJ"

# Cache haute performance pour supprimer la lenteur
@st.cache_data(ttl=10)
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

# Initialisation des états de session
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'panier': {}, 'page': "ACCUEIL", 'role': "VENDEUR", 'user': ""})

# Récupération de la configuration (Nom entreprise, Taux)
cfg = query_cloud("config", "id=eq.1")
C_ENT = cfg[0]['entreprise'] if cfg else "BALIKA ERP"
C_TAUX = cfg[0]['taux'] if cfg else 2850.0

# ==========================================
# 2. DESIGN MOBILE "ANTI-BUG" D'AFFICHAGE
# ==========================================
st.markdown(f"""
    <style>
    /* Forcer le fond blanc et texte noir pour éviter les bugs d'affichage */
    .stApp {{ background-color: #F8F9FA !important; color: #1E1E1E !important; }}
    
    /* Boutons larges et contrastés */
    .stButton>button {{ 
        background: #FF8C00 !important; 
        color: white !important; 
        border-radius: 12px !important; 
        height: 55px !important; 
        font-weight: bold !important;
        font-size: 18px !important;
        border: none !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* En-tête mobile compact */
    .mobile-header {{
        background: #333;
        color: #FF8C00;
        padding: 10px;
        text-align: center;
        font-weight: bold;
        border-radius: 0 0 15px 15px;
        margin-bottom: 20px;
    }}
    
    /* Input texte bien visible */
    input {{ border: 2px solid #FF8C00 !important; border-radius: 10px !important; padding: 10px !important; }}
    
    /* Masquer les menus Streamlit inutiles sur mobile */
    #MainMenu, footer {{visibility: hidden;}}
    </style>
    <div class="mobile-header">{C_ENT} PRO v220</div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. SYSTÈME DE CONNEXION
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown("<h3 style='text-align:center;'>Connexion</h3>", unsafe_allow_html=True)
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("SE CONNECTER"):
            # Création automatique de l'admin si absent
            run_action("users", "POST", {"username": "admin", "password": make_hashes("admin123"), "role": "ADMIN"})
            
            res = query_cloud("users", f"username=eq.{u}")
            if res and make_hashes(p) == res[0]['password']:
                st.session_state.update({"auth": True, "user": u, "role": res[0]['role']})
                st.rerun()
            else: st.error("Identifiants incorrects")
    st.stop()

# ==========================================
# 4. MENU DE NAVIGATION MOBILE
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.upper()}")
    nav = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES", "📦 STOCK": "STOCK", "⚙️ CONFIG": "CONFIG"}
    for label, page in nav.items():
        if st.button(label, use_container_width=True):
            st.session_state.page = page
            st.rerun()
    st.write("---")
    if st.button("🚪 Déconnexion"):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 5. LOGIQUE DES PAGES (Optimisée)
# ==========================================
if st.session_state.page == "ACCUEIL":
    st.subheader("Tableau de bord")
    v = query_cloud("ventes")
    if v:
        df = pd.DataFrame(v)
        c1, c2 = st.columns(2)
        c1.metric("Ventes USD", f"{df[df['devise']=='USD']['total_val'].sum():,.2f}")
        c2.metric("Ventes CDF", f"{df[df['devise']=='CDF']['total_val'].sum():,.0f}")

elif st.session_state.page == "CAISSE":
    st.subheader("🛒 Nouvelle Vente")
    devise = st.radio("Monnaie", ["USD", "CDF"], horizontal=True)
    
    prods = query_cloud("produits", "stock_actuel=gt.0")
    if prods:
        imap = {r['designation']: r for r in prods}
        sel = st.selectbox("Article", ["Choisir..."] + list(imap.keys()))
        
        if st.button("➕ AJOUTER") and sel != "Choisir...":
            st.session_state.panier[sel] = st.session_state.panier.get(sel, 0) + 1
            st.rerun()
            
        if st.session_state.panier:
            total = 0.0
            for art, qte in list(st.session_state.panier.items()):
                p_u = imap[art]['prix_vente']
                if imap[art]['devise_origine'] == "USD" and devise == "CDF": p_u *= C_TAUX
                
                with st.container():
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{art}**\n{p_u:,.2f} {devise}")
                    nq = c2.number_input("Qté", 1, value=qte, key=f"q_{art}")
                    st.session_state.panier[art] = nq
                    if c3.button("🗑️", key=f"del_{art}"):
                        del st.session_state.panier[art]
                        st.rerun()
                    total += (p_u * nq)
            
            st.markdown(f"<h2 style='text-align:center; color:orange;'>TOTAL : {total:,.2f} {devise}</h2>", unsafe_allow_html=True)
            nom_c = st.text_input("NOM CLIENT")
            paye = st.number_input("ACOMPTE", 0.0)
            
            if st.button("🚀 VALIDER LA VENTE") and nom_c:
                ref = f"FAC-{random.randint(1000,9999)}"
                run_action("ventes", "POST", {
                    "ref": ref, "client_nom": nom_c, "total_val": total, 
                    "acompte": paye, "reste": total-paye, "devise": devise, 
                    "date_v": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                if (total-paye) > 0:
                    run_action("dettes", "POST", {"client_nom": nom_c, "montant_du": total-paye, "devise": devise, "sale_ref": ref})
                
                # Mise à jour stock
                for art, qte in st.session_state.panier.items():
                    new_q = imap[art]['stock_actuel'] - qte
                    run_action("produits", "PATCH", {"stock_actuel": new_q}, f"id=eq.{imap[art]['id']}")
                
                st.session_state.panier = {}
                st.success("Vente réussie !")
                st.rerun()
