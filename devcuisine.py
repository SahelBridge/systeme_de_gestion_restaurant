import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Cuisine - SmartResto",
    page_icon="🍽️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: #f3eee4;
        color: #2f241c;
    }

    .main-title {
        background: #173f35;
        padding: 28px 35px;
        border-radius: 18px;
        margin-bottom: 25px;
        border: 1px solid #b99a5b;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }

    .main-title h1 {
        color: #f5efe3;
        margin: 0;
        font-size: 32px;
        letter-spacing: 1px;
    }

    .main-title p {
        color: #d8c9aa;
        margin: 7px 0 0 0;
        font-size: 15px;
    }

    .stat-card {
        background: #fffaf1;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #d5c5a5;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }

    .stat-number {
        color: #173f35;
        font-size: 30px;
        font-weight: bold;
    }

    .stat-label {
        color: #806f5b;
        font-size: 14px;
    }

    .order-card {
        background: #fffdf8;
        border-radius: 18px;
        padding: 24px;
        margin: 15px 0;
        border: 1px solid #d8c8a9;
        box-shadow: 0 7px 20px rgba(45,35,25,0.08);
    }

    .order-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }

    .order-title {
        color: #173f35;
        font-size: 21px;
        font-weight: bold;
    }

    .table-number {
        color: #806f5b;
        font-size: 15px;
    }

    .wait-normal {
        display: inline-block;
        background: #dce9df;
        color: #285b45;
        padding: 7px 13px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
    }

    .wait-warning {
        display: inline-block;
        background: #f1dfb5;
        color: #805f20;
        padding: 7px 13px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
    }

    .wait-danger {
        display: inline-block;
        background: #efd0c8;
        color: #873d31;
        padding: 7px 13px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
    }

    .plats-title {
        color: #173f35;
        font-size: 16px;
        font-weight: bold;
        margin-top: 18px;
        margin-bottom: 8px;
    }

    .plat {
        background: #f5efe3;
        padding: 11px 15px;
        border-radius: 10px;
        margin: 7px 0;
        border-left: 4px solid #b99a5b;
        color: #3d3025;
    }

    .separator {
        height: 1px;
        background: #d8c8a9;
        margin: 22px 0;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #b99a5b;
        background: #173f35;
        color: #fffaf1;
        font-weight: bold;
        padding: 10px 20px;
    }

    div.stButton > button:hover {
        background: #235748;
        border-color: #c5a765;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


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
                date_commande = datetime.strptime(
                    date_commande,
                    "%Y-%m-%d %H:%M:%S"
                )
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
        badge = f'<span class="wait-normal">● {minutes} min</span>'
    elif couleur == "orange":
        badge = f'<span class="wait-warning">● {minutes} min</span>'
    else:
        badge = f'<span class="wait-danger">● {minutes} min</span>'

    st.markdown(f"""
    <div class="order-card">
        <div class="order-header">
            <div>
                <div class="order-title">COMMANDE {commande['id']}</div>
                <div class="table-number">Table {commande['table_id']}</div>
            </div>
            <div>{badge}</div>
        </div>

        <div class="plats-title">PLATS À PRÉPARER</div>
    """, unsafe_allow_html=True)

    for item in commande["items"]:
        nom = item["nom"]
        quantite = item["quantite"]

        st.markdown(
            f"""
            <div class="plat">
                <strong>{quantite} ×</strong> {nom}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "✓  Commande terminée",
            key=f"terminee_{commande['id']}"
        ):
            st.success("Commande terminée.")

    with col2:
        if st.button(
            "⚠  Rupture de stock",
            key=f"rupture_{commande['id']}"
        ):
            st.warning("Le plat doit maintenant être désactivé.")

    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)


st.markdown("""
<div class="main-title">
    <h1>SMARTRESTO — CUISINE</h1>
    <p>Tableau de gestion des commandes en cours</p>
</div>
""", unsafe_allow_html=True)


commandes = obtenir_commandes()

total_commandes = len(commandes)
commandes_urgentes = 0
total_attente = 0

for commande in commandes:
    minutes = calculer_minutes_attente(commande["date_commande"])
    total_attente += minutes

    if minutes >= 20:
        commandes_urgentes += 1

if total_commandes > 0:
    moyenne_attente = round(total_attente / total_commandes)
else:
    moyenne_attente = 0


col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_commandes}</div>
        <div class="stat-label">COMMANDES EN COURS</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{commandes_urgentes}</div>
        <div class="stat-label">COMMANDES URGENTES</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{moyenne_attente} min</div>
        <div class="stat-label">ATTENTE MOYENNE</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("###")


if st.button("⟳  Actualiser les commandes"):
    st.rerun()


if len(commandes) == 0:
    st.info("Aucune commande en cours.")
else:
    st.markdown(
        f"**{len(commandes)} commande(s) en cours**"
    )

    for commande in commandes:
        afficher_commande(commande)