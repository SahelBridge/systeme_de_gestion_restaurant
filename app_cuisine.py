"""Écran Cuisine (KDS - Kitchen Display System) - SmartResto.

Branche : dev-cuisine (app_cuisine.py)
Responsabilités :
- Affichage en temps réel des commandes actives
- Code couleur d'urgence : vert (<10 min), orange (10-20 min), rouge (>=20 min)
- Validation et clôture des commandes en cuisine
- Déclaration des ruptures de stock express
- Réception et traitement des appels serveur des tables
"""

from __future__ import annotations

from datetime import datetime, timedelta
import streamlit as st

import api_backend
import database

try:
    st.set_page_config(
        page_title="Cuisine KDS - SmartResto",
        page_icon="🧑‍🍳",
        layout="wide"
    )
except Exception:
    pass

# Injection CSS personnalisée
st.markdown("""
<style>
    .stApp {
        background: #f3eee4;
        color: #2f241c;
    }

    .main-title {
        background: #173f35;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid #b99a5b;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }

    .main-title h1 {
        color: #f5efe3;
        margin: 0;
        font-size: 30px;
        letter-spacing: 1px;
    }

    .main-title p {
        color: #d8c9aa;
        margin: 6px 0 0 0;
        font-size: 14px;
    }

    .stat-card {
        background: #fffaf1;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #d5c5a5;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }

    .stat-number {
        color: #173f35;
        font-size: 28px;
        font-weight: bold;
    }

    .stat-label {
        color: #806f5b;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .order-card {
        background: #fffdf8;
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid #d8c8a9;
        box-shadow: 0 7px 20px rgba(45,35,25,0.08);
    }

    .order-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .order-title {
        color: #173f35;
        font-size: 20px;
        font-weight: bold;
    }

    .table-number {
        color: #806f5b;
        font-size: 14px;
    }

    .wait-normal {
        display: inline-block;
        background: #dce9df;
        color: #285b45;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
    }

    .wait-warning {
        display: inline-block;
        background: #f1dfb5;
        color: #805f20;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
    }

    .wait-danger {
        display: inline-block;
        background: #efd0c8;
        color: #873d31;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
    }

    .plats-title {
        color: #173f35;
        font-size: 15px;
        font-weight: bold;
        margin-top: 14px;
        margin-bottom: 8px;
    }

    .plat {
        background: #f5efe3;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 6px 0;
        border-left: 4px solid #b99a5b;
        color: #3d3025;
    }

    .plat-custom {
        font-size: 0.82rem;
        color: #806f5b;
        margin-top: 3px;
    }

    .call-card {
        background: #fff8e6;
        border: 1px solid #f6d365;
        border-left: 5px solid #d97706;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)


def calculer_minutes_attente(date_commande: Any) -> int:
    """Calcule le nombre de minutes écoulées depuis la création de la commande."""
    if isinstance(date_commande, str):
        try:
            date_commande = datetime.fromisoformat(date_commande)
        except ValueError:
            try:
                date_commande = datetime.strptime(date_commande, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return 0

    if not isinstance(date_commande, datetime):
        return 0

    maintenant = datetime.now()
    difference = maintenant - date_commande
    minutes = int(difference.total_seconds() / 60)
    return max(0, minutes)


def obtenir_couleur_urgence(minutes: int) -> str:
    """Règle du Cahier des Charges : vert (<10 min), orange (10-20 min), rouge (>=20 min)."""
    if minutes < 10:
        return "green"
    elif minutes < 20:
        return "orange"
    else:
        return "red"


# =============================================================================
# BARRE LATÉRALE : GESTION EXPRESS DES STOCKS (RUPTURES)
# =============================================================================
with st.sidebar:
    st.markdown("### 🥫 Rupture de Stock Express")
    st.caption("Désactivez instantanément un plat sur les tablettes s'il manque un ingrédient.")

    menu_complet = api_backend.load_menu(apply_overrides=False)
    overrides = database.get_dish_overrides()

    for plat in menu_complet:
        dish_id = plat["id"]
        dish_nom = plat["nom"]
        
        # Statut effectif (surcharge DB prioritaire sur menu.json)
        est_dispo = overrides.get(dish_id, plat.get("disponible", True))
        
        col_s1, col_s2 = st.columns([2.5, 1])
        with col_s1:
            statut_txt = "🟢 En stock" if est_dispo else "🔴 En rupture"
            st.write(f"**{dish_nom}**\n*{statut_txt}*")
        with col_s2:
            action_txt = "Désactiver" if est_dispo else "Réactiver"
            btn_type = "secondary" if est_dispo else "primary"
            if st.button(action_txt, key=f"side_stk_{dish_id}", type=btn_type):
                database.set_dish_availability(dish_id, not est_dispo)
                st.toast(f"{dish_nom} marqué comme {'disponible' if not est_dispo else 'en rupture'} !")
                st.rerun()
        st.divider()


# =============================================================================
# EN-TÊTE PRINCIPAL
# =============================================================================
st.markdown("""
<div class="main-title">
    <h1>🧑‍🍳 SMARTRESTO — ÉCRAN CUISINE (KDS)</h1>
    <p>Système de gestion et ordonnancement des tickets de préparation en temps réel</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# SECTION 1 : NOTIFICATIONS EN DIRECT DES APPELS SERVEUR
# =============================================================================
appels_actifs = database.get_active_server_calls()
if appels_actifs:
    st.markdown("### 🛎️ Demandes des Tables en Attente")
    for appel in appels_actifs:
        c_info, c_btn = st.columns([4, 1])
        with c_info:
            st.markdown(f"""
            <div class="call-card">
                <div>
                    <strong>Table {appel['table_id']}</strong> : Demande <b>{appel['call_type']}</b>
                    <div style="font-size:0.8rem; color:#854d0e;">Reçu à {appel['created_at']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_btn:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("✓ Traité", key=f"call_res_{appel['id']}", type="primary"):
                database.resolve_server_call(appel["id"])
                st.toast(f"Appel Table {appel['table_id']} marqué comme traité !")
                st.rerun()
    st.markdown("---")


# =============================================================================
# SECTION 2 : STATISTIQUES EN DIRECT
# =============================================================================
commandes = database.get_active_orders()

total_commandes = len(commandes)
commandes_urgentes = 0
total_attente = 0

for commande in commandes:
    minutes = calculer_minutes_attente(commande["date_commande"])
    total_attente += minutes
    if minutes >= 20:
        commandes_urgentes += 1

moyenne_attente = round(total_attente / total_commandes) if total_commandes > 0 else 0

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns([1, 1, 1, 1])

with col_stat1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_commandes}</div>
        <div class="stat-label">Commandes en cours</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="color:#b91c1c;">{commandes_urgentes}</div>
        <div class="stat-label">Urgences (&gt;20 min)</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{moyenne_attente} min</div>
        <div class="stat-label">Attente Moyenne</div>
    </div>
    """, unsafe_allow_html=True)

with col_stat4:
    top_ventes = database.get_top_sales(limit=1)
    top_plat_nom = top_ventes[0]["nom"] if top_ventes else "—"
    top_plat_qty = f"({top_ventes[0]['total_vendu']} vendus)" if top_ventes else ""
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="font-size:18px; line-height:36px;">{top_plat_nom}</div>
        <div class="stat-label">Top Plat {top_plat_qty}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_ctrl1, col_ctrl2 = st.columns([1, 3])
with col_ctrl1:
    if st.button("⟳  Actualiser les commandes", use_container_width=True):
        st.rerun()


# =============================================================================
# SECTION 3 : AFFICHAGE DES TICKETS DE COMMANDE
# =============================================================================
if not commandes:
    st.info("🎉 Aucune commande en attente de préparation en cuisine.")
else:
    st.markdown(f"### 📋 Tickets Actifs ({len(commandes)})")

    # Affichage en grille de 2 colonnes de tickets
    for i in range(0, len(commandes), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(commandes):
                cmd = commandes[i + j]
                minutes = calculer_minutes_attente(cmd["date_commande"])
                couleur = obtenir_couleur_urgence(minutes)

                if couleur == "green":
                    badge = f'<span class="wait-normal">● {minutes} min (Normal)</span>'
                elif couleur == "orange":
                    badge = f'<span class="wait-warning">● {minutes} min (Attention)</span>'
                else:
                    badge = f'<span class="wait-danger">● {minutes} min (URGENT)</span>'

                with cols[j]:
                    st.markdown(f"""
                    <div class="order-card">
                        <div class="order-header">
                            <div>
                                <div class="order-title">TICKET {cmd['id']}</div>
                                <div class="table-number">📍 Table {cmd['table_id']} | Reçu à {cmd.get('date_commande', 'N/A')}</div>
                            </div>
                            <div>{badge}</div>
                        </div>
                        <div class="plats-title">🍽️ PLATS À PRÉPARER :</div>
                    """, unsafe_allow_html=True)

                    for item in cmd["items"]:
                        nom = item.get("nom", item.get("id"))
                        quantite = item.get("quantite", 1)

                        details = []
                        if item.get("cuisson"):
                            details.append(f"Cuisson : <b>{item['cuisson']}</b>")
                        if item.get("options"):
                            details.extend([f"<b>{opt}</b>" for opt in item["options"]])
                        if item.get("instructions"):
                            details.append(f"Note client : <i>{item['instructions']}</i>")

                        custom_html = f"<div class='plat-custom'>{' • '.join(details)}</div>" if details else ""

                        st.markdown(
                            f"""
                            <div class="plat">
                                <strong>{quantite} ×</strong> {nom}
                                {custom_html}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown("</div>", unsafe_allow_html=True)

                    c_done, c_rupture = st.columns([1.5, 1.5])
                    with c_done:
                        if st.button(
                            "✓ Commande terminée",
                            key=f"kds_done_{cmd['id']}",
                            type="primary",
                            use_container_width=True
                        ):
                            database.complete_order(cmd["id"])
                            st.toast(f"✅ Commande {cmd['id']} clôturée !")
                            st.rerun()

                    with c_rupture:
                        with st.popover("⚠ Rupture express", use_container_width=True):
                            st.caption("Désactiver un plat de ce ticket :")
                            for item in cmd["items"]:
                                p_id = item.get("id")
                                p_nom = item.get("nom", p_id)
                                if st.button(f"Rupture : {p_nom}", key=f"rup_{cmd['id']}_{p_id}"):
                                    database.set_dish_availability(p_id, False)
                                    st.toast(f"Plat '{p_nom}' mis en rupture de stock !")
                                    st.rerun()
