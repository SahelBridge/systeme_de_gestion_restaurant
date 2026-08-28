import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Cuisine - SmartResto",
    page_icon="🍽️",
    layout="wide"
)

def obtenir_commandes_test():
    maintenant = datetime.now()
    return [
        {
            "id": "CMD001",
            "table_id": 4,
            "items": [
                {"nom": "Tchep poisson", "quantite": 2},
                {"nom": "Alloco", "quantite": 1}
            ],
            "date_commande": maintenant - timedelta(minutes=5)
        },
        {
            "id": "CMD002",
            "table_id": 7,
            "items": [
                {"nom": "Yassa poulet", "quantite": 1},
                {"nom": "Jus de bissap", "quantite": 2}
            ],
            "date_commande": maintenant - timedelta(minutes=15)
        },
        {
            "id": "CMD003",
            "table_id": 2,
            "items": [
                {"nom": "Choukouya d'agneau", "quantite": 1}
            ],
            "date_commande": maintenant - timedelta(minutes=25)
        }
    ]

def obtenir_commandes():
    try:
        from database import get_active_orders
        return get_active_orders()
    except Exception:
        return obtenir_commandes_test()

def calculer_minutes_attente(date_commande):
    if isinstance(date_commande, str):
        try:
            date_commande = datetime.fromisoformat(date_commande)
        except ValueError:
            try:
                date_commande = datetime.strptime(date_commande, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return 0
    maintenant = datetime.now()
    difference = maintenant - date_commande
    minutes = int(difference.total_seconds() / 60)
    return max(0, minutes)

def obtenir_couleur(minutes):
    if minutes < 10:
        return "green"
    elif minutes < 20:
        return "orange"
    else:
        return "red"

def afficher_commande(commande):
    date_commande = commande["date_commande"]
    minutes = calculer_minutes_attente(date_commande)
    couleur = obtenir_couleur(minutes)

    if couleur == "green":
        st.success(
            f"COMMANDE {commande['id']} - Table {commande['table_id']}"
        )
    elif couleur == "orange":
        st.warning(
            f"COMMANDE {commande['id']} - Table {commande['table_id']}"
        )
    else:
        st.error(
            f"COMMANDE {commande['id']} - Table {commande['table_id']}"
        )

    st.write(f"Temps d'attente : **{minutes} minutes**")

    st.write("### Plats")

    for item in commande["items"]:
        nom = item["nom"]
        quantite = item["quantite"]
        st.write(f"- **{quantite} × {nom}**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Commande terminée",
            key=f"terminee_{commande['id']}"
        ):
            st.success("Commande terminée.")

    with col2:
        if st.button(
            "Rupture de stock",
            key=f"rupture_{commande['id']}"
        ):
            st.warning("Le plat doit maintenant être désactivé.")

    st.divider()

st.title("Écran Cuisine")
st.write("Gestion des commandes en cours")

if st.button("Actualiser les commandes"):
    st.rerun()

commandes = obtenir_commandes()

if len(commandes) == 0:
    st.info("Aucune commande en cours.")
else:
    st.write(f"**{len(commandes)} commande(s) en cours**")

    for commande in commandes:
        afficher_commande(commande)