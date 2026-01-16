# ==============================================================================
# BALIKA ERP v2000 SaaS PRO
# MODE : MULTI-BOUTIQUES | SUPER ADMIN + ADMINS CLIENTS
# ==============================================================================

import streamlit as st
import sqlite3
import hashlib
import random
import json
from datetime import datetime
import pandas as pd

# ------------------------------------------------------------------------------
# CONFIG STREAMLIT
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="BALIKA ERP v2000 SaaS",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# SESSION INIT
# ------------------------------------------------------------------------------
if "auth" not in st.session_state:
    st.session_state.update({
        "auth": False,
        "user": "",
        "role": "",
        "ent_id": "",
        "page": "LOGIN"
    })

# ------------------------------------------------------------------------------
# DB HELPERS
# ------------------------------------------------------------------------------
def run_db(q, p=(), fetch=False):
    with sqlite3.connect("balika_v2000_master.db", timeout=60) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        cur.execute(q, p)
        conn.commit()
        return cur.fetchall() if fetch else None

def make_hash(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ------------------------------------------------------------------------------
# INIT DB
# ------------------------------------------------------------------------------
def init_db():
    run_db("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        ent_id TEXT,
        status TEXT DEFAULT 'ACTIF'
    )""")

    run_db("""
    CREATE TABLE IF NOT EXISTS config (
        ent_id TEXT PRIMARY KEY,
        nom_ent TEXT,
        message TEXT,
        taux REAL,
        status TEXT DEFAULT 'ACTIF'
    )""")

    # SUPER ADMIN
    if not run_db("SELECT * FROM users WHERE username='superadmin'", fetch=True):
        run_db("INSERT INTO users VALUES (?,?,?,?,?)",
               ("superadmin", make_hash("admin123"), "SUPER_ADMIN", "SYSTEM", "ACTIF"))
        run_db("INSERT INTO config VALUES (?,?,?,?,?)",
               ("SYSTEM", "BALIKA ERP HQ", "MESSAGE GLOBAL SaaS - BIENVENUE", 2850, "ACTIF"))

init_db()

# ------------------------------------------------------------------------------
# LOAD CONFIG
# ------------------------------------------------------------------------------
ENT_ID = st.session_state.ent_id if st.session_state.auth else "SYSTEM"
cfg = run_db("SELECT nom_ent, message, taux, status FROM config WHERE ent_id=?", (ENT_ID,), fetch=True)
C_NOM, C_MSG, C_TAUX, C_STATUS = cfg[0] if cfg else ("BALIKA", "", 2850, "ACTIF")

# ------------------------------------------------------------------------------
# CSS (LOGIN ORANGE + MARQUEE)
# ------------------------------------------------------------------------------
st.markdown(f"""
<style>
.stApp {{
    background:#0e1117;
    color:white;
}}

.login-bg {{
    background: linear-gradient(135deg,#FF4B2B,#FF8C42);
    min-height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}}

.login-card {{
    background:#0e1117;
    padding:40px;
    border-radius:20px;
    width:420px;
}}

.top-marquee-container {{
    position:fixed;
    top:0;
    width:100%;
    background:#FF4B2B;
    color:white;
    font-weight:900;
    z-index:9999;
}}

.marquee-content {{
    white-space:nowrap;
    animation:scroll 18s linear infinite;
}}

@keyframes scroll {{
    0% {{transform:translateX(100%);}}
    100% {{transform:translateX(-100%);}}
}}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# LOGIN SCREEN
# ------------------------------------------------------------------------------
if not st.session_state.auth:

    st.markdown(f"""
    <div class="top-marquee-container">
        <div class="marquee-content">📢 {C_MSG}</div>
    </div>
    <div style="height:60px;"></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-bg"><div class="login-card">', unsafe_allow_html=True)

    st.markdown("## 🔐 CONNEXION BALIKA ERP")

    u = st.text_input("Identifiant")
    p = st.text_input("Mot de passe", type="password")

    if st.button("SE CONNECTER"):
        res = run_db("SELECT password, role, ent_id, status FROM users WHERE username=?",
                     (u.lower(),), fetch=True)
        if res and make_hash(p) == res[0][0]:
            if res[0][3] == "PAUSE":
                st.error("⛔ Compte suspendu par l'administrateur SaaS.")
            else:
                st.session_state.update({
                    "auth": True,
                    "user": u.lower(),
                    "role": res[0][1],
                    "ent_id": res[0][2],
                    "page": "DASHBOARD"
                })
                st.rerun()
        else:
            st.error("Identifiants invalides")

    st.write("---")
    st.subheader("Créer une boutique")

    shop = st.text_input("Nom boutique")
    admin = st.text_input("Admin boutique")
    pwd = st.text_input("Mot de passe", type="password")

    if st.button("CRÉER MON ERP"):
        eid = f"SHOP-{random.randint(1000,9999)}"
        run_db("INSERT INTO users VALUES (?,?,?,?,?)",
               (admin.lower(), make_hash(pwd), "ADMIN", eid, "ACTIF"))
        run_db("INSERT INTO config VALUES (?,?,?,?,?)",
               (eid, shop.upper(), "BIENVENUE CHEZ NOUS", 2850, "ACTIF"))
        st.success("Compte créé. Connectez-vous.")

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()
# ------------------------------------------------------------------------------
# SIDEBAR + NAVIGATION
# ------------------------------------------------------------------------------
if st.session_state.auth:

    with st.sidebar:
        st.markdown(f"## 🏢 {C_NOM}")
        st.write(f"👤 {st.session_state.user.upper()}")
        st.write(f"🔑 Rôle : {st.session_state.role}")
        st.write("---")

        if st.session_state.role == "ADMIN":
            menu = [
                "🏠 DASHBOARD",
                "⚙️ PARAMÈTRES",
                "🔐 SÉCURITÉ"
            ]
        else:  # SUPER ADMIN
            menu = [
                "🏠 DASHBOARD",
                "🌍 BOUTIQUES",
                "📢 MESSAGE GLOBAL",
                "🔐 MON COMPTE"
            ]

        for m in menu:
            if st.button(m, use_container_width=True):
                st.session_state.page = m
                st.rerun()

        st.write("---")
        if st.button("🚪 DÉCONNEXION"):
            st.session_state.clear()
            st.rerun()

# ------------------------------------------------------------------------------
# MARQUEE GLOBAL (TOUTES INTERFACES)
# ------------------------------------------------------------------------------
st.markdown(f"""
<div class="top-marquee-container">
    <div class="marquee-content">
        📢 {C_MSG} | 🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
</div>
<div style="height:60px;"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# DASHBOARD ADMIN BOUTIQUE
# ------------------------------------------------------------------------------
if st.session_state.page == "🏠 DASHBOARD" and st.session_state.role == "ADMIN":

    st.title("🏠 Tableau de bord Boutique")
    st.success("Bienvenue dans votre ERP")

    st.metric("Boutique", C_NOM)
    st.metric("Statut", C_STATUS)

# ------------------------------------------------------------------------------
# PARAMÈTRES BOUTIQUE (ADMIN CLIENT)
# ------------------------------------------------------------------------------
elif st.session_state.page == "⚙️ PARAMÈTRES" and st.session_state.role == "ADMIN":

    st.header("⚙️ Paramètres de la boutique")

    with st.form("cfg_shop"):
        n_nom = st.text_input("Nom boutique", C_NOM)
        n_msg = st.text_area("Message local boutique", C_MSG)
        n_tx = st.number_input("Taux USD → CDF", value=C_TAUX)

        if st.form_submit_button("SAUVEGARDER"):
            run_db("""
                UPDATE config
                SET nom_ent=?, message=?, taux=?
                WHERE ent_id=?
            """, (n_nom.upper(), n_msg, n_tx, ENT_ID))
            st.success("Paramètres mis à jour")
            st.rerun()

# ------------------------------------------------------------------------------
# SÉCURITÉ ADMIN BOUTIQUE
# ------------------------------------------------------------------------------
elif st.session_state.page == "🔐 SÉCURITÉ" and st.session_state.role == "ADMIN":

    st.header("🔐 Sécurité du compte")

    with st.form("sec_admin"):
        old = st.text_input("Ancien mot de passe", type="password")
        new = st.text_input("Nouveau mot de passe", type="password")

        if st.form_submit_button("CHANGER"):
            res = run_db("SELECT password FROM users WHERE username=?",
                         (st.session_state.user,), fetch=True)
            if make_hash(old) == res[0][0]:
                run_db("UPDATE users SET password=? WHERE username=?",
                       (make_hash(new), st.session_state.user))
                st.success("Mot de passe modifié")
            else:
                st.error("Ancien mot de passe incorrect")

# ------------------------------------------------------------------------------
# DASHBOARD SUPER ADMIN
# ------------------------------------------------------------------------------
elif st.session_state.page == "🏠 DASHBOARD" and st.session_state.role == "SUPER_ADMIN":

    st.title("🧑‍💼 SUPER ADMIN SaaS")
    st.success("Contrôle global des boutiques")

    shops = run_db("SELECT COUNT(*) FROM config WHERE ent_id!='SYSTEM'", fetch=True)[0][0]
    st.metric("Boutiques actives", shops)

# ------------------------------------------------------------------------------
# GESTION DES BOUTIQUES (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "🌍 BOUTIQUES" and st.session_state.role == "SUPER_ADMIN":

    st.header("🌍 Boutiques clientes")

    shops = run_db("""
        SELECT c.ent_id, c.nom_ent, c.status, u.username
        FROM config c
        JOIN users u ON u.ent_id = c.ent_id
        WHERE c.ent_id!='SYSTEM'
    """, fetch=True)

    for eid, nom, stat, admin in shops:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3,1,1])
            c1.write(f"🏢 **{nom}** (`{eid}`)")
            c1.caption(f"Admin : {admin} | Statut : {stat}")

            if c2.button("⏸️ / ▶️", key=f"tg_{eid}"):
                new = "PAUSE" if stat == "ACTIF" else "ACTIF"
                run_db("UPDATE config SET status=? WHERE ent_id=?", (new, eid))
                run_db("UPDATE users SET status=? WHERE ent_id=?", (new, eid))
                st.rerun()

            if c3.button("🗑️ SUPPRIMER", key=f"dl_{eid}"):
                run_db("DELETE FROM users WHERE ent_id=?", (eid,))
                run_db("DELETE FROM config WHERE ent_id=?", (eid,))
                st.warning("Boutique supprimée")
                st.rerun()

# ------------------------------------------------------------------------------
# MESSAGE GLOBAL SaaS (SUPER ADMIN)
# ------------------------------------------------------------------------------
elif st.session_state.page == "📢 MESSAGE GLOBAL" and st.session_state.role == "SUPER_ADMIN":

    st.header("📢 Message global SaaS")

    with st.form("msg_global"):
        msg = st.text_area("Message défilant global", C_MSG)
        if st.form_submit_button("METTRE À JOUR"):
            run_db("UPDATE config SET message=? WHERE ent_id='SYSTEM'", (msg,))
            st.success("Message global mis à jour")
            st.rerun()

# ------------------------------------------------------------------------------
# COMPTE SUPER ADMIN
# ------------------------------------------------------------------------------
elif st.session_state.page == "🔐 MON COMPTE" and st.session_state.role == "SUPER_ADMIN":

    st.header("🔐 Mon compte Super Admin")

    with st.form("super_sec"):
        old = st.text_input("Ancien mot de passe", type="password")
        new = st.text_input("Nouveau mot de passe", type="password")

        if st.form_submit_button("CHANGER"):
            res = run_db("SELECT password FROM users WHERE username='superadmin'", fetch=True)
            if make_hash(old) == res[0][0]:
                run_db("UPDATE users SET password=? WHERE username='superadmin'",
                       (make_hash(new),))
                st.success("Mot de passe modifié")
            else:
                st.error("Mot de passe incorrect")
