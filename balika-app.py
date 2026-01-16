import streamlit as st
import pandas as pd
from datetime import datetime
import random
import hashlib
import httpx

# ==========================================
# 1. CŒUR DU SYSTÈME & CONNEXIONS (v235 - Ajusté)
# ==========================================
st.set_page_config(page_title="BALIKA ERP PRO", layout="wide", initial_sidebar_state="collapsed")

SUPABASE_URL = "https://ngrjinsorpxqkeajfufd.supabase.co"
SUPABASE_KEY = "sb_publishable__9hjGqGla0UU-Y9L-zOBRA_zG0rrbWJ"

@st.cache_data(ttl=1)
def query_cloud(table, params_str=None):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = dict(item.split('=') for item in params_str.split('&')) if params_str else {}
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers, params=params)
            return res.json() if res.status_code == 200 else []
    except: return []

def run_action(table, method, data=None, params=None):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        with httpx.Client(timeout=10.0) as client:
            if method == "POST": return client.post(url, headers=headers, json=data)
            if method == "PATCH": return client.patch(url, headers=headers, json=data, params=params)
            if method == "DELETE": return client.delete(url, headers=headers, params=params)
    except: return None

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- INITIALISATION DES ÉTATS ---
for key, val in {'auth': False, 'panier': {}, 'page': "ACCUEIL", 'last_fac': None, 'role': "VENDEUR", 'user': ""}.items():
    if key not in st.session_state: st.session_state[key] = val

# Chargement Config
cfg_res = query_cloud("config", "id=eq.1")
if cfg_res:
    C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = cfg_res[0]['entreprise'], cfg_res[0]['message'], cfg_res[0]['taux'], cfg_res[0]['adresse'], cfg_res[0]['telephone']
else:
    C_ENT, C_MSG, C_TAUX, C_ADR, C_TEL = "BALIKA ERP", "Bienvenue", 2850.0, "ADRESSE", "000"

# ==========================================
# 2. STYLE CSS MOBILE & IMPRESSION (AJUSTEMENT ANTI-BLANC)
# ==========================================
st.markdown(f"""
    <style>
    /* Forçage du mode clair pour éviter le texte blanc sur fond blanc sur mobile */
    .stApp {{ background-color: #FFFFFF !important; color: #000000 !important; }}
    [data-testid="stHeader"] {{ background: #FFFFFF !important; }}
    h1, h2, h3, p, span, label, .stMarkdown, div {{ color: black !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    
    /* Inputs visibles */
    input {{ background-color: #F0F2F6 !important; color: black !important; border: 1px solid orange !important; }}
    
    .stButton>button {{ 
        background: linear-gradient(to right, #FF8C00, #FF4500) !important; 
        color: white !important; border-radius: 12px !important; height: 55px !important; font-weight: bold; border: none; width: 100%;
    }}
    .marquee-container {{ width: 100%; overflow: hidden; background: #333; color: #FF8C00; padding: 12px 0; font-weight: bold; }}
    .marquee-text {{ display: inline-block; white-space: nowrap; animation: marquee 15s linear infinite; }}
    @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .total-frame {{ border: 3px solid #FF8C00; background: #FFF3E0; color: #E65100 !important; padding: 20px; border-radius: 15px; font-size: 26px; font-weight: bold; text-align: center; margin: 15px 0; }}
    
    /* Zones d'impression */
    .print-area {{ background: white; color: black; padding: 10px; border: 1px solid #eee; margin: auto; }}
    .f-80mm {{ width: 100%; max-width: 310px; font-size: 12px; font-family: monospace; }}
    .f-A4 {{ width: 100%; font-size: 16px; padding: 40px; }}
    
    @media print {{ .no-print {{ display: none !important; }} }}
    </style>
    <div class="marquee-container no-print"><div class="marquee-text">{C_MSG}</div></div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTIFICATION
# ==========================================
if not st.session_state.auth:
    _, col, _ = st.columns([0.1, 0.8, 0.1])
    with col:
        st.markdown(f'<div style="background:orange; padding:40px; border-radius:25px; color:white; text-align:center; margin-top:20px;"><h1>{C_ENT}</h1><p>SYSTÈME DE GESTION CLOUD</p></div>', unsafe_allow_html=True)
        u = st.text_input("Identifiant").lower().strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("SE CONNECTER"):
            # Auto-création admin si base vide
            run_action("users", "POST", {"username": "admin", "password": make_hashes("admin123"), "role": "ADMIN"})
            res = query_cloud("users", f"username=eq.{u}")
            if res and make_hashes(p) == res[0]['password']:
                st.session_state.update({"auth": True, "user": u, "role": res[0]['role']})
                st.rerun()
            else: st.error("Accès refusé.")
    st.stop()

# ==========================================
# 4. NAVIGATION
# ==========================================
with st.sidebar:
    st.header(f"👤 {st.session_state.user.upper()}")
    st.write("---")
    m = {"🏠 ACCUEIL": "ACCUEIL", "🛒 CAISSE": "CAISSE", "📉 DETTES": "DETTES"}
    if st.session_state.role == "ADMIN":
        m.update({"📦 STOCK": "STOCK", "📊 RAPPORT": "RAPPORT", "👥 VENDEURS": "USERS", "⚙️ CONFIG": "CONFIG"})
    
    for label, pg in m.items():
        if st.button(label, use_container_width=True): 
            st.session_state.page = pg
            st.rerun()
    st.write("---")
    if st.button("🚪 DÉCONNEXION"):
        st.session_state.auth = False
        st.rerun()

# ==========================================
# 5. PAGES
# ==========================================

# --- ACCUEIL ---
if st.session_state.page == "ACCUEIL":
    st.markdown(f'<center><div style="border:4px solid orange; padding:30px; border-radius:25px; background:#FFF3E0; margin-top:20px;"><h1>⌚ {datetime.now().strftime("%H:%M")}</h1><h3>{datetime.now().strftime("%d/%m/%Y")}</h3></div></center>', unsafe_allow_html=True)
    v = query_cloud("ventes")
    if v:
        df = pd.DataFrame(v)
        c1, c2 = st.columns(2)
        c1.metric("Ventes USD", f"{df[df['devise']=='USD']['total_val'].sum():,.2f} $")
        c2.metric("Ventes CDF", f"{df[df['devise']=='CDF']['total_val'].sum():,.0f} FC")

# --- CAISSE & FACTURATION ---
elif st.session_state.page == "CAISSE":
    if not st.session_state.last_fac:
        st.title("🛒 Caisse Mobile")
        devise_v = st.radio("Monnaie de vente", ["USD", "CDF"], horizontal=True)
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
                    if imap[art]['devise_origine']=="USD" and devise_v=="CDF": p_f = p_orig * C_TAUX
                    elif imap[art]['devise_origine']=="CDF" and devise_v=="USD": p_f = p_orig / C_TAUX
                    else: p_f = p_orig
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{art}**\n{p_f:,.2f} {devise_v}")
                    nq = c2.number_input("Qté", 1, int(imap[art]['stock_actuel']), value=qte, key=f"q_{art}")
                    st.session_state.panier[art] = nq
                    if c3.button("🗑️", key=f"del_{art}"): del st.session_state.panier[art]; st.rerun()
                    
                    sub = p_f * nq
                    total += sub
                    details.append({'art': art, 'qte': nq, 'pu': p_f, 'st': sub})
                    items_txt.append(f"{art}(x{nq})")
                
                st.markdown(f'<div class="total-frame">TOTAL : {total:,.2f} {devise_v}</div>', unsafe_allow_html=True)
                nom_c = st.text_input("NOM DU CLIENT").upper()
                paye = st.number_input("MONTANT PAYÉ (Acompte)", 0.0)
                
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
        st.button("⬅️ RETOUR CAISSE", on_click=lambda: st.session_state.update({"last_fac": None}))
        fmt = st.radio("Format Facture", ["80mm", "A4"], horizontal=True)
        cls = "f-80mm" if fmt == "80mm" else "f-A4"
        lignes = "".join([f"<tr><td>{l['art']} x{l['qte']}</td><td style='text-align:right;'>{l['st']:,.2f}</td></tr>" for l in f['lines']])
        st.markdown(f"""<div class="print-area {cls}"><center><h2>{C_ENT}</h2><p>{C_ADR}<br>{C_TEL}</p></center><hr>
            <b>REF: {f['ref']}</b> | Client: {f['cl']}<br>Date: {f['date']}<hr>
            <table style="width:100%;">{lignes}</table><hr>
            <h4 style="text-align:right;">TOTAL: {f['tot']:,.2f} {f['dev']}</h4><p style="text-align:right;">Acompte: {f['ac']:,.2f} | Reste: {f['re']:,.2f}</p>
            <div style="display:flex; justify-content:space-between; margin-top:30px;"><span>Signature Client</span><span>Signature Vendeur</span></div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.button("🖨️ IMPRIMER", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        txt = f"*{C_ENT}*\nFacture: {f['ref']}\nTotal: {f['tot']} {f['dev']}"
        c2.markdown(f'<a href="https://wa.me/?text={txt}" target="_blank"><button style="width:100%; height:55px; background:#25D366; color:white; border-radius:12px; border:none; font-weight:bold;">📲 WHATSAPP</button></a>', unsafe_allow_html=True)

# --- DETTES ---
elif st.session_state.page == "DETTES":
    st.title("📉 Suivi des Dettes")
    dts = query_cloud("dettes")
    if not dts: st.info("Aucune dette enregistrée.")
    for d in dts:
        with st.expander(f"👤 {d['client_nom']} | Reste: {d['montant_du']:,.2f} {d['devise']}"):
            st.write(f"Articles: {d['articles']}")
            v = st.number_input("Versement (Paiement partiel)", 0.0, float(d['montant_du']), key=f"v_{d['id']}")
            if st.button("Enregistrer Paiement", key=f"b_{d['id']}"):
                r = d['montant_du'] - v
                if r <= 0.1: run_action("dettes", "DELETE", params=f"id=eq.{d['id']}")
                else: run_action("dettes", "PATCH", {"montant_du": r}, f"id=eq.{d['id']}")
                run_action("ventes", "PATCH", {"reste": r}, f"ref=eq.{d['sale_ref']}")
                st.success("Paiement validé !"); st.rerun()

# --- CONFIGURATION (PARAMÈTRES) ---
elif st.session_state.page == "CONFIG":
    st.title("⚙️ Paramètres du Système")
    with st.form("conf_form"):
        st.subheader("En-tête de Facture")
        en = st.text_input("Nom de l'Entreprise", C_ENT)
        ad = st.text_input("Adresse Physique", C_ADR)
        tl = st.text_input("Téléphone de contact", C_TEL)
        st.subheader("Réglages Généraux")
        tx = st.number_input("Taux de Change (1 USD en CDF)", value=C_TAUX)
        ms = st.text_area("Message défilant (Accueil)", C_MSG)
        if st.form_submit_button("SAUVEGARDER LES RÉGLAGES"):
            run_action("config", "PATCH", {"entreprise": en.upper(), "adresse": ad, "telephone": tl, "taux": tx, "message": ms}, "id=eq.1")
            st.success("Paramètres mis à jour !"); st.rerun()
    st.write("---")
    st.subheader("🔑 Sécurité")
    with st.form("p_admin"):
        np = st.text_input("Nouveau mot de passe Admin", type="password")
        if st.form_submit_button("MODIFIER MON MOT DE PASSE"):
            run_action("users", "PATCH", {"password": make_hashes(np)}, "username=eq.admin")
            st.success("Mot de passe admin changé !")

# --- GESTION STOCK ---
elif st.session_state.page == "STOCK":
    st.title("📦 Gestion du Stock")
    with st.form("s_add"):
        c1, c2 = st.columns(2); n = c1.text_input("Désignation de l'article"); p = c2.number_input("Prix de Vente")
        c3, c4 = st.columns(2); d = c3.selectbox("Devise d'origine", ["USD", "CDF"]); q = c4.number_input("Quantité initiale", 1)
        if st.form_submit_button("AJOUTER AU STOCK"):
            run_action("produits", "POST", {"designation": n.upper(), "stock_initial": q, "stock_actuel": q, "prix_vente": p, "devise_origine": d})
            st.rerun()
    st.write("---")
    st.subheader("État actuel")
    stk = query_cloud("produits")
    if stk:
        for r in stk:
            c1, c2 = st.columns([4,1])
            c1.write(f"**{r['designation']}** | Stock: {r['stock_actuel']} | Prix: {r['prix_vente']} {r['devise_origine']}")
            if c2.button("🗑️", key=f"p_{r['id']}"):
                run_action("produits", "DELETE", f"id=eq.{r['id']}"); st.rerun()

# --- RAPPORT ---
elif st.session_state.page == "RAPPORT":
    st.title("📊 Rapport des Ventes")
    vr = query_cloud("ventes")
    if vr:
        st.dataframe(pd.DataFrame(vr)[['date_v', 'ref', 'client_nom', 'total_val', 'devise', 'reste']], use_container_width=True)
        st.button("🖨️ IMPRIMER LE RAPPORT", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))

# --- VENDEURS ---
elif st.session_state.page == "USERS":
    st.title("👥 Gestion des Vendeurs")
    with st.form("u_add"):
        un = st.text_input("Identifiant"); ps = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("CRÉER LE COMPTE VENDEUR"):
            run_action("users", "POST", {"username": un.lower(), "password": make_hashes(ps), "role": "VENDEUR"})
            st.rerun()
    st.write("### Liste des accès")
    for u in query_cloud("users", "role=eq.VENDEUR"):
        c1, c2 = st.columns([4,1])
        c1.write(f"👤 **{u['username'].upper()}**")
        if c2.button("Supprimer", key=u['username']): run_action("users", "DELETE", f"username=eq.{u['username']}"); st.rerun()
