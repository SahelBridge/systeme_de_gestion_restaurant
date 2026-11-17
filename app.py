"""Plateforme Unifiee de Test SmartResto (app.py).

Ce fichier unifie l ensemble des modules du projet dans une seule application Streamlit :
- Tablette Client (dev-client / app_client.py)
- Ecran Cuisine KDS (dev-cuisine / app_cuisine.py)
- Espace Serveur & Appels de Table (Gestion en direct des demandes)
- Tableau de Bord & Statistiques (Top 3 des ventes, CA, notes & avis, points fidelite)
- Gestion Express des Stocks (Disponibilite On/Off)
"""

from __future__ import annotations

import os
from pathlib import Path
import runpy
from datetime import datetime
import streamlit as st

import api_backend
import database

# 1. Configuration de la page principale
st.set_page_config(
    page_title="SmartResto - Hub de Test Unifié",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de la base SQLite
database.init_db()

# 2. Navigation dans la barre latérale
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #173f35 0%, #235748 100%); padding: 16px; border-radius: 12px; color: white; margin-bottom: 15px;">
    <h2 style="margin:0; font-size:20px; color:#f5efe3;">🍽️ SmartResto</h2>
    <p style="margin:4px 0 0 0; font-size:12px; color:#d8c9aa;">Hub de Test Unifié de l'Équipe</p>
</div>
""", unsafe_allow_html=True)

menu_views = [
    "📱 Tablette Client",
    "🧑‍🍳 Écran Cuisine (KDS)",
    "🛎️ Espace Serveur & Salle",
    "📊 Statistiques & Top Ventes",
    "🥫 Gestion du Menu & Stocks"
]

if "current_view" not in st.session_state:
    st.session_state.current_view = menu_views[0]

current_view = st.sidebar.radio(
    "🎯 Module à tester :",
    options=menu_views,
    index=menu_views.index(st.session_state.current_view) if st.session_state.current_view in menu_views else 0,
    key="nav_radio"
)
st.session_state.current_view = current_view

# Badges d'état système en temps réel dans la sidebar
st.sidebar.divider()
nb_commandes_actives = len(database.get_active_orders())
nb_appels_en_attente = len(database.get_active_server_calls())

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    st.metric("Commandes", nb_commandes_actives, help="Tickets en attente en cuisine")
with col_sb2:
    st.metric("Appels Table", nb_appels_en_attente, help="Demandes clients non traitées")

st.sidebar.divider()


# =============================================================================
# VUES DÉDIÉES
# =============================================================================

def render_serveur_view():
    st.markdown("""
    <div style="background:#1e3c72; padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
        <h1 style="margin:0; font-size:26px;">🛎️ Espace Serveur & Salle</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">Suivi et réponse aux demandes d'assistance des tables en temps réel</p>
    </div>
    """, unsafe_allow_html=True)

    appels = database.get_active_server_calls()
    
    col_act1, col_act2 = st.columns([2, 1])
    with col_act1:
        st.subheader(f"Demandes actives ({len(appels)})")
    with col_act2:
        if st.button("🔄 Actualiser les appels", use_container_width=True):
            st.rerun()

    if not appels:
        st.success("✨ Aucune demande en attente. Toutes les tables sont servies !")
    else:
        for appel in appels:
            with st.container():
                c_card, c_act = st.columns([4, 1])
                with c_card:
                    icon = "💧" if "eau" in appel["call_type"].lower() else ("🥖" if "pain" in appel["call_type"].lower() else ("🧾" if "addition" in appel["call_type"].lower() else "💬"))
                    st.info(f"{icon} **Table {appel['table_id']}** : Demande **{appel['call_type']}** (reçue à `{appel['created_at']}`)")
                with c_act:
                    if st.button("✓ Marquer servi", key=f"srv_done_{appel['id']}", type="primary", use_container_width=True):
                        database.resolve_server_call(appel["id"])
                        st.toast(f"Appel Table {appel['table_id']} traité !")
                        st.rerun()


def render_stats_view():
    st.markdown("""
    <div style="background:#2c3e50; padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
        <h1 style="margin:0; font-size:26px;">📊 Tableau de Bord & Statistiques</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">Top 3 des Ventes, indicateurs financiers, avis clients et programme de fidélité</p>
    </div>
    """, unsafe_allow_html=True)

    all_orders = database.get_all_orders()
    total_ca = sum(o.get("total", 0.0) for o in all_orders if o.get("status") != "annulee")
    nb_total_cmd = len(all_orders)
    reviews = database.get_all_reviews()
    moyenne_etoiles = (sum(r["stars"] for r in reviews) / len(reviews)) if reviews else 5.0

    # Cartes d'indicateurs clés
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Chiffre d'Affaires Total", f"{total_ca:.2f} €")
    with kpi2:
        st.metric("Commandes Totales", nb_total_cmd)
    with kpi3:
        st.metric("Note Moyenne Clients", f"⭐ {moyenne_etoiles:.1f} / 5")
    with kpi4:
        st.metric("Avis Déposés", len(reviews))

    st.divider()

    # ✨ Fonctionnalité 1 (Cahier des charges - Personne 4) : TOP 3 DES VENTES
    st.subheader("🏆 Top 3 des Plats les Plus Vendus")
    top3 = database.get_top_sales(limit=3)
    if not top3:
        st.info("Aucune vente enregistrée pour le moment. Passez des commandes sur la tablette client !")
    else:
        cols_top = st.columns(len(top3))
        medailles = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
        for idx, plat in enumerate(top3):
            with cols_top[idx]:
                st.markdown(f"""
                <div style="background:white; border-radius:12px; padding:18px; border:2px solid #e2e8f0; box-shadow:0 4px 10px rgba(0,0,0,0.05); text-align:center;">
                    <div style="font-size:22px; font-weight:bold; color:#d97706;">{medailles[idx]}</div>
                    <div style="font-size:18px; font-weight:600; color:#1e293b; margin:8px 0;">{plat['nom']}</div>
                    <div style="font-size:24px; font-weight:bold; color:#059669;">{plat['total_vendu']} <span style="font-size:14px; color:#64748b;">portions vendues</span></div>
                    <div style="font-size:13px; color:#64748b; margin-top:4px;">Revenu : {plat['revenu_total']:.2f} €</div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Section Avis clients & Fidélité
    col_av, col_hist = st.columns(2)
    with col_av:
        st.subheader("💬 Derniers Avis & Retours d'Expérience")
        if not reviews:
            st.caption("Aucun avis déposé pour le moment.")
        else:
            for r in reviews[:5]:
                stars_display = "⭐" * r["stars"]
                phone_display = f" | 📱 `{r['phone']}`" if r.get("phone") else ""
                st.markdown(f"**Table {r['table_id']}** — {stars_display}{phone_display}")
                if r.get("comment"):
                    st.write(f"> *« {r['comment']} »*")
                st.caption(f"Déposé le {r['created_at']}")
                st.divider()

    with col_hist:
        st.subheader("📜 Historique Récent des Commandes")
        if not all_orders:
            st.caption("Aucune commande dans l'historique.")
        else:
            for o in all_orders[:5]:
                badge_color = "#15803d" if o["status"] == "terminee" else "#d97706"
                st.markdown(f"**Ticket `{o['id']}`** — Table {o['table_id']} — `{o['total']:.2f} €`")
                st.markdown(f"Statut : <span style='background-color:#f1f5f9; color:{badge_color}; padding:2px 8px; border-radius:4px; font-weight:bold;'>{o['status']}</span> | *{o['date_commande']}*", unsafe_allow_html=True)
                st.divider()


def render_stocks_view():
    st.markdown("""
    <div style="background:#854d0e; padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
        <h1 style="margin:0; font-size:26px;">🥫 Gestion Centralisée des Stocks & Disponibilités</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">Activez ou désactivez un plat en temps réel (mise à jour instantanée pour le client et la cuisine)</p>
    </div>
    """, unsafe_allow_html=True)

    menu_complet = api_backend.load_menu(apply_overrides=False)
    overrides = database.get_dish_overrides()

    for item in menu_complet:
        dish_id = item["id"]
        dish_nom = item["nom"]
        dish_cat = item.get("categorie", "Autre")
        dish_prix = item.get("prix", 0.0)
        
        est_dispo = overrides.get(dish_id, item.get("disponible", True))

        c_info, c_prix, c_stat, c_btn = st.columns([3, 1.5, 2, 2])
        with c_info:
            st.write(f"**{dish_nom}** (`{dish_id}`)\n*{dish_cat}*")
        with c_prix:
            st.write(f"`{dish_prix:.2f} €`")
        with c_stat:
            if est_dispo:
                st.markdown("🟢 **Disponible en salle**")
            else:
                st.markdown("🔴 **RUPTURE DE STOCK**")
        with c_btn:
            btn_label = "Mettre en rupture" if est_dispo else "Remettre en stock"
            btn_t = "secondary" if est_dispo else "primary"
            if st.button(btn_label, key=f"stk_page_{dish_id}", type=btn_t, use_container_width=True):
                database.set_dish_availability(dish_id, not est_dispo)
                st.toast(f"{dish_nom} mis à jour !")
                st.rerun()
        st.divider()


# =============================================================================
# ROUTAGE PRINCIPAL DE L'APPLICATION
# =============================================================================
root_dir = Path(__file__).resolve().parent

if current_view == "📱 Tablette Client":
    client_path = root_dir / "app_client.py"
    runpy.run_path(str(client_path), run_name="__main__")

elif current_view == "🧑‍🍳 Écran Cuisine (KDS)":
    cuisine_path = root_dir / "app_cuisine.py"
    runpy.run_path(str(cuisine_path), run_name="__main__")

elif current_view == "🛎️ Espace Serveur & Salle":
    render_serveur_view()

elif current_view == "📊 Statistiques & Top Ventes":
    render_stats_view()

elif current_view == "🥫 Gestion du Menu & Stocks":
    render_stocks_view()
