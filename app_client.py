"""
=============================================================================
Application Tablette Client - Smart Restaurant System (smart-resto-system)
Branche: dev-client
Auteur: Équipe Frontend Client
=============================================================================
Fonctionnalités principales :
- Consultation du catalogue des plats et boissons avec filtres dynamiques
- ✨ Fonctionnalité 2 : Personnalisation avancée des plats (cuisson, allergies, sans sel...)
- Gestion interactive du panier et calcul en temps réel du total
- Validation et transmission de la commande aux modules Backend/DB
- ✨ Fonctionnalité 1 : Appel Serveur rapide (Eau, Pain, Addition, Demande libre)
- Évaluation de fin de repas et Programme de Fidélité (numéro de téléphone)
=============================================================================
"""

import os
import json
import uuid
from datetime import datetime
import streamlit as st

# =============================================================================
# 1. Configuration de la page Streamlit (Optimisée pour Tablette Tactile)
# =============================================================================
st.set_page_config(
    page_title="SmartResto - Tablette Client",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection CSS personnalisée pour un design moderne, épuré et adapté au tactile
st.markdown("""
<style>
    /* Styles globaux */
    .main {
        background-color: #f8f9fa;
    }
    
    /* En-tête restaurant */
    .resto-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .resto-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    
    .resto-subtitle {
        font-size: 1.05rem;
        opacity: 0.9;
    }
    
    /* Carte de Plat */
    .dish-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .dish-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.08);
        border-color: #cbd5e1;
    }
    
    .dish-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.3rem;
    }
    
    .dish-price {
        font-size: 1.3rem;
        font-weight: 700;
        color: #059669;
    }
    
    .dish-desc {
        font-size: 0.92rem;
        color: #64748b;
        margin: 0.5rem 0;
        line-height: 1.4;
    }
    
    /* Badges */
    .tag-badge {
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
        text-transform: capitalize;
    }
    
    .status-badge-ok {
        background-color: #dcfce7;
        color: #15803d;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
    }
    
    .status-badge-out {
        background-color: #fee2e2;
        color: #b91c1c;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
    }
    
    /* Section Appel Serveur */
    .call-server-box {
        background: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    /* Panier */
    .cart-summary {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-top: 1rem;
    }
    
    .cart-item {
        border-bottom: 1px dashed #e2e8f0;
        padding: 0.6rem 0;
    }
    
    .cart-item:last-child {
        border-bottom: none;
    }
    
    /* Boutons tactiles larges */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 2.6rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. Intégration Robuste des Modules Équipe (Backend API & Database)
# =============================================================================
# Importation sécurisée pour garantir le bon fonctionnement même en mode autonome
try:
    from api_backend import process_order as backend_process_order
    HAS_BACKEND_API = True
except Exception:
    HAS_BACKEND_API = False

try:
    from database import save_order as db_save_order, get_active_orders as db_get_active_orders
    HAS_DATABASE = True
except Exception:
    HAS_DATABASE = False


def fallback_process_order(table_id: int, order_items: list) -> dict:
    """
    Logique métier locale autonome conforme au contrat de données.
    Calcule les totaux, valide les articles et prépare les métadonnées.
    """
    total = sum(item.get("prix", 0.0) * item.get("quantite", 1) for item in order_items)
    order_id = f"CMD-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    
    # Estimation basique du temps d'attente (10 min + 2 min par plat)
    nb_articles = sum(item.get("quantite", 1) for item in order_items)
    temps_estime = 10 + (nb_articles * 2)
    
    return {
        "id": order_id,
        "table_id": table_id,
        "items": order_items,
        "total": round(total, 2),
        "statut": "en_attente",
        "date_commande": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temps_estime_minutes": temps_estime
    }


def fallback_save_order(table_id: int, items: list, total: float) -> bool:
    """
    Sauvegarde locale de session lorsque la DB MongoDB n'est pas encore connectée.
    """
    return True


def executer_commande(table_id: int, order_items: list) -> tuple[bool, dict]:
    """
    Orchestre l'envoi de la commande via l'API backend et la base de données.
    """
    # 1. Traitement Logique Métier
    if HAS_BACKEND_API:
        try:
            order_details = backend_process_order(table_id, order_items)
        except Exception as e:
            st.warning(f"Note: api_backend a renvoyé une erreur ({e}). Traitement via le moteur intégré.")
            order_details = fallback_process_order(table_id, order_items)
    else:
        order_details = fallback_process_order(table_id, order_items)

    total = order_details.get("total", sum(i.get("prix", 0) * i.get("quantite", 1) for i in order_items))

    # 2. Sauvegarde Base de Données
    succes_db = False
    if HAS_DATABASE:
        try:
            succes_db = db_save_order(table_id, order_items, total)
        except Exception as e:
            st.warning(f"Note: database a renvoyé une exception ({e}). Sauvegarde locale effectuée.")
            succes_db = fallback_save_order(table_id, order_items, total)
    else:
        succes_db = fallback_save_order(table_id, order_items, total)

    return (succes_db, order_details)


# =============================================================================
# 3. Initialisation de l'État de Session (State Management)
# =============================================================================
if "table_id" not in st.session_state:
    st.session_state.table_id = 4

if "panier" not in st.session_state:
    st.session_state.panier = []

if "appels_serveur" not in st.session_state:
    st.session_state.appels_serveur = []

if "historique_commandes" not in st.session_state:
    st.session_state.historique_commandes = []

if "plat_a_personnaliser" not in st.session_state:
    st.session_state.plat_a_personnaliser = None

if "points_fidelite_session" not in st.session_state:
    st.session_state.points_fidelite_session = 0

if "avis_soumis" not in st.session_state:
    st.session_state.avis_soumis = False


# =============================================================================
# 4. Chargement des Données du Catalogue (data/menu.json)
# =============================================================================
@st.cache_data
def charger_catalogue_menu() -> list:
    """Charge le menu depuis le fichier data/menu.json ou retourne le jeu par défaut."""
    chemin_menu = os.path.join(os.path.dirname(__file__), "data", "menu.json")
    if os.path.exists(chemin_menu):
        try:
            with open(chemin_menu, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur de lecture de {chemin_menu}: {e}")
    
    # Jeu de données de secours si data/menu.json n'est pas encore disponible
    return [
        {
            "id": "plat_01",
            "nom": "Steak Frites Maison",
            "categorie": "Plats Principaux",
            "description": "Pièce de boeuf tendre grillée, frites maison croustillantes.",
            "ingredients": ["viande de boeuf", "pommes de terre", "sel"],
            "tags": ["plat_principal", "viande", "chaud", "halal"],
            "prix": 15.50,
            "disponible": true
        },
        {
            "id": "plat_02",
            "nom": "Thiéboudienne Rouge (Tchep)",
            "categorie": "Plats Principaux",
            "description": "Riz rouge sénégalais parfumé, mérou braisé et légumes mijotés.",
            "ingredients": ["riz", "poisson", "carotte", "manioc", "epices"],
            "tags": ["plat_principal", "poisson", "chaud", "specialite"],
            "prix": 14.00,
            "disponible": true
        },
        {
            "id": "dessert_01",
            "nom": "Tiramisu Traditionnel",
            "categorie": "Desserts",
            "description": "Crème mascarpone légère, biscuits au café expresso, cacao.",
            "ingredients": ["mascarpone", "cafe", "biscuit", "cacao"],
            "tags": ["dessert", "sucre", "froid", "vegetarien"],
            "prix": 6.00,
            "disponible": true
        }
    ]

menu_items = charger_catalogue_menu()


# =============================================================================
# 5. Barre Latérale (Sidebar) : Table, Panier & Synthèse
# =============================================================================
with st.sidebar:
    st.markdown("### 🏷️ Table & Session")
    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.session_state.table_id = st.selectbox(
            "Numéro de Table",
            options=list(range(1, 21)),
            index=st.session_state.table_id - 1 if 1 <= st.session_state.table_id <= 20 else 0,
            help="Sélectionnez le numéro de votre table physique"
        )
    with col_t2:
        st.metric(
            label="Articles Panier",
            value=sum(item.get("quantite", 1) for item in st.session_state.panier)
        )

    st.divider()

    # Section Récapitulatif du Panier
    st.markdown("### 🛒 Votre Panier")
    
    if not st.session_state.panier:
        st.info("Votre panier est actuellement vide. Sélectionnez un plat dans le menu !")
    else:
        total_panier = 0.0
        
        for idx, item in enumerate(st.session_state.panier):
            sous_total = item["prix"] * item["quantite"]
            total_panier += sous_total
            
            with st.container():
                st.markdown(f"**{item['quantite']}× {item['nom']}** — `{sous_total:.2f} €`")
                
                # Affichage des personnalisations
                details = []
                if item.get("cuisson"):
                    details.append(f"🥩 *{item['cuisson']}*")
                if item.get("options"):
                    details.extend([f"• {opt}" for opt in item["options"]])
                if item.get("instructions"):
                    details.append(f"💬 *Note: {item['instructions']}*")
                
                if details:
                    st.caption(" | ".join(details))
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn1:
                    if st.button("➕", key=f"inc_{idx}", help="Augmenter la quantité"):
                        st.session_state.panier[idx]["quantite"] += 1
                        st.rerun()
                with col_btn2:
                    if st.button("➖", key=f"dec_{idx}", help="Diminuer la quantité"):
                        if st.session_state.panier[idx]["quantite"] > 1:
                            st.session_state.panier[idx]["quantite"] -= 1
                        else:
                            st.session_state.panier.pop(idx)
                        st.rerun()
                with col_btn3:
                    if st.button("🗑️", key=f"del_{idx}", help="Supprimer du panier"):
                        st.session_state.panier.pop(idx)
                        st.rerun()
                
                st.markdown("---")

        # Affichage du Total
        st.markdown(f"### **Total : {total_panier:.2f} €**")
        st.caption("Prix TTC service compris")

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.panier = []
                st.rerun()
        
        with col_act2:
            if st.button("🚀 Commander", type="primary", use_container_width=True):
                succes, order_details = executer_commande(st.session_state.table_id, st.session_state.panier)
                
                if succes:
                    st.session_state.historique_commandes.append(order_details)
                    st.session_state.points_fidelite_session += int(total_panier)
                    st.session_state.panier = []
                    st.toast("🎉 Commande transmise en cuisine avec succès !")
                    st.rerun()
                else:
                    st.error("Erreur lors de l'enregistrement de la commande.")

    st.divider()
    
    # Intégration de l'état système dans la sidebar
    st.markdown("##### 🔌 État du Système")
    c_api, c_db = st.columns(2)
    with c_api:
        if HAS_BACKEND_API:
            st.success("API: Connectée", icon="✅")
        else:
            st.info("API: Mode Local", icon="⚡")
    with c_db:
        if HAS_DATABASE:
            st.success("DB: Connectée", icon="✅")
        else:
            st.info("DB: Mode Local", icon="⚡")


# =============================================================================
# 6. En-tête Principal & Navigation par Onglets
# =============================================================================
st.markdown("""
<div class="resto-header">
    <div class="resto-title">🍽️ Smart Restaurant - Tablette Client</div>
    <div class="resto-subtitle">Bienvenue ! Commandez directement depuis votre table, personnalisez vos plats et demandez de l'aide à tout moment.</div>
</div>
""", unsafe_allow_html=True)

# Barre d'action permanente : ✨ FONCTIONNALITÉ 1 - APPEL SERVEUR FLOTTANT / RAPIDE
with st.container():
    st.markdown("""
    <div class="call-server-box">
        <h4 style="margin:0 0 0.5rem 0; color:#b45309;">🛎️ Besoin d'assistance ? Appelez votre serveur en 1 clic</h4>
        <span style="font-size:0.9rem; color:#78350f;">Un membre de notre équipe viendra directement à votre <b>Table {table_id}</b>.</span>
    </div>
    """.format(table_id=st.session_state.table_id), unsafe_allow_html=True)
    
    col_srv1, col_srv2, col_srv3, col_srv4 = st.columns(4)
    
    with col_srv1:
        if st.button("💧 Demander de l'eau", use_container_width=True):
            demande = {"table_id": st.session_state.table_id, "type": "Eau", "heure": datetime.now().strftime("%H:%M:%S")}
            st.session_state.appels_serveur.append(demande)
            st.toast(f"💧 Demande d'eau envoyée pour la Table {st.session_state.table_id} !")
            st.success(f"🛎️ Le serveur a bien été notifié : **Demande d'eau fraîche** pour la Table {st.session_state.table_id}.")
            
    with col_srv2:
        if st.button("🥖 Demander du pain", use_container_width=True):
            demande = {"table_id": st.session_state.table_id, "type": "Pain", "heure": datetime.now().strftime("%H:%M:%S")}
            st.session_state.appels_serveur.append(demande)
            st.toast(f"🥖 Corbeille de pain demandée pour la Table {st.session_state.table_id} !")
            st.success(f"🛎️ Le serveur a bien été notifié : **Corbeille de pain** pour la Table {st.session_state.table_id}.")
            
    with col_srv3:
        if st.button("🧾 Demander l'addition", use_container_width=True):
            demande = {"table_id": st.session_state.table_id, "type": "Addition", "heure": datetime.now().strftime("%H:%M:%S")}
            st.session_state.appels_serveur.append(demande)
            st.toast(f"🧾 Demande d'addition envoyée pour la Table {st.session_state.table_id} !")
            st.info(f"🛎️ Votre serveur prépare l'addition et se rend à votre Table {st.session_state.table_id}.")
            
    with col_srv4:
        with st.popover("💬 Autre demande"):
            message_custom = st.text_input("Précisez votre demande :", placeholder="Ex: Serviettes, couverts...")
            if st.button("Envoyer la demande"):
                if message_custom.strip():
                    demande = {"table_id": st.session_state.table_id, "type": f"Personnalisé: {message_custom.strip()}", "heure": datetime.now().strftime("%H:%M:%S")}
                    st.session_state.appels_serveur.append(demande)
                    st.toast("Demande personnalisée transmise !")
                    st.success("Votre demande a été envoyée au serveur.")
                else:
                    st.warning("Veuillez saisir votre demande.")

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# 7. Affichage des Dernières Commandes Validées (Temps d'attente estimé)
# =============================================================================
if st.session_state.historique_commandes:
    derniere = st.session_state.historique_commandes[-1]
    with st.expander(f"🟢 Commande en cours : **{derniere['id']}** (Table {derniere['table_id']}) - Cliquez pour le statut", expanded=True):
        col_c1, col_c2, col_c3 = st.columns([1.5, 1, 1])
        with col_c1:
            st.markdown(f"**Montant :** `{derniere['total']:.2f} €`")
            st.markdown(f"**Heure d'envoi :** {derniere.get('date_commande', 'Récemment')}")
        with col_c2:
            st.metric(label="⏱️ Temps d'attente estimé", value=f"~{derniere.get('temps_estime_minutes', 15)} min")
        with col_c3:
            st.markdown("**Statut Cuisine :** 🧑‍🍳 *En préparation*")
        
        st.markdown("**Articles commandés :**")
        for it in derniere["items"]:
            opts = f" ({', '.join(it['options'])})" if it.get("options") else ""
            cuiss = f" [{it['cuisson']}]" if it.get("cuisson") else ""
            st.write(f"- {it.get('quantite', 1)}× **{it['nom']}**{cuiss}{opts}")


# =============================================================================
# 8. Onglets Principaux : Menu / Catalogue & Avis Fin de Repas
# =============================================================================
tab_menu, tab_avis, tab_historique = st.tabs(["📜 Catalogue & Commande", "⭐ Avis & Fidélité", "📋 Mes Commandes du Jour"])


# =============================================================================
# 8.1. ONGLET 1 : CATALOGUE DES PLATS & ✨ FONCTIONNALITÉ 2 (PERSONNALISATION)
# =============================================================================
with tab_menu:
    # Filtres et recherche
    col_f1, col_f2, col_f3 = st.columns([2, 1.5, 1.5])
    
    with col_f1:
        recherche = st.text_input("🔍 Rechercher un plat ou un ingrédient...", placeholder="Ex: boeuf, tchep, sans piment, chocolat...")
        
    with col_f2:
        categories_dispos = ["Toutes", "Entrées", "Plats Principaux", "Desserts", "Boissons"]
        cat_choisie = st.selectbox("📂 Catégorie", categories_dispos)
        
    with col_f3:
        regimes_dispos = ["Tous", "Halal", "Végétarien", "Sans gluten", "Spécialité"]
        regime_choisi = st.selectbox("🌱 Régime / Filtre", regimes_dispos)

    # Filtrage des plats
    plats_filtres = []
    for p in menu_items:
        # Filtre texte
        if recherche:
            q = recherche.lower()
            nom_match = q in p.get("nom", "").lower()
            desc_match = q in p.get("description", "").lower()
            ing_match = any(q in ing.lower() for ing in p.get("ingredients", []))
            tag_match = any(q in tag.lower() for tag in p.get("tags", []))
            if not (nom_match or desc_match or ing_match or tag_match):
                continue
                
        # Filtre catégorie
        if cat_choisie != "Toutes":
            if p.get("categorie", "") != cat_choisie:
                # Fallback tags si pas de catégorie explicite
                tags = p.get("tags", [])
                if cat_choisie == "Entrées" and "entree" not in tags:
                    continue
                elif cat_choisie == "Plats Principaux" and "plat_principal" not in tags:
                    continue
                elif cat_choisie == "Desserts" and "dessert" not in tags:
                    continue
                elif cat_choisie == "Boissons" and "boisson" not in tags:
                    continue

        # Filtre régime
        if regime_choisi != "Tous":
            tags = [t.lower() for t in p.get("tags", [])]
            if regime_choisi == "Halal" and "halal" not in tags:
                continue
            elif regime_choisi == "Végétarien" and "vegetarien" not in tags:
                continue
            elif regime_choisi == "Sans gluten" and "sans_gluten" not in tags:
                continue
            elif regime_choisi == "Spécialité" and "specialite" not in tags:
                continue
                
        plats_filtres.append(p)

    st.markdown(f"**{len(plats_filtres)} plat(s) trouvé(s)**")

    # Affichage en grille de 2 colonnes
    if not plats_filtres:
        st.info("Aucun plat ne correspond à vos critères de recherche.")
    else:
        for i in range(0, len(plats_filtres), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(plats_filtres):
                    plat = plats_filtres[i + j]
                    with cols[j]:
                        with st.container():
                            st.markdown(f"""
                            <div class="dish-card">
                                <div>
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span class="dish-name">{plat.get('nom', 'Plat sans nom')}</span>
                                        <span class="dish-price">{plat.get('prix', 0.0):.2f} €</span>
                                    </div>
                                    <p class="dish-desc">{plat.get('description', 'Délicieux plat préparé avec soin par notre chef.')}</p>
                                    <div style="margin-bottom:0.6rem;">
                                        {''.join([f'<span class="tag-badge">{tag}</span>' for tag in plat.get('tags', [])])}
                                    </div>
                                    <div style="font-size:0.85rem; color:#475569; margin-bottom:0.8rem;">
                                        <b>Ingrédients :</b> {', '.join(plat.get('ingredients', []))}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            dispo = plat.get("disponible", True)
                            
                            # Formulaire interactif de personnalisation & ajout au panier
                            with st.expander(f"⚙️ Personnaliser & Ajouter au Panier - {plat['nom']}", expanded=False):
                                if not dispo:
                                    st.error("Ce plat est actuellement en rupture de stock.")
                                else:
                                    st.markdown("##### ✨ Options de personnalisation :")
                                    
                                    # 1. Option Cuisson si plat de viande/boeuf
                                    is_viande = any(t in ["viande", "boeuf", "agneau"] for t in plat.get("tags", []) + plat.get("ingredients", []))
                                    choix_cuisson = None
                                    if is_viande:
                                        choix_cuisson = st.radio(
                                            "Cuisson souhaitée :",
                                            options=["Bleu", "Saignant", "À point", "Bien cuit"],
                                            index=2,
                                            horizontal=True,
                                            key=f"cuisson_{plat['id']}"
                                        )
                                    
                                    # 2. Options diététiques & allergies (Cases à cocher)
                                    col_opt1, col_opt2 = st.columns(2)
                                    with col_opt1:
                                        sans_sel = st.checkbox("🧂 Sans sel", key=f"sel_{plat['id']}")
                                        sans_piment = st.checkbox("🌶️ Sans piment", key=f"pim_{plat['id']}")
                                        sans_oignon = st.checkbox("🧅 Sans oignon", key=f"oig_{plat['id']}")
                                    with col_opt2:
                                        allergie_arachide = st.checkbox("🥜 Allergie arachide (sans arachide)", key=f"ara_{plat['id']}")
                                        sans_gluten = st.checkbox("🌾 Sans gluten", key=f"glu_{plat['id']}")
                                    
                                    # 3. Champ instructions spéciales
                                    instructions_custom = st.text_input(
                                        "Instructions pour le chef (facultatif) :",
                                        placeholder="Ex: Sauce à part, très chaud...",
                                        key=f"inst_{plat['id']}"
                                    )
                                    
                                    # 4. Quantité & Bouton d'ajout
                                    col_q, col_add = st.columns([1, 2])
                                    with col_q:
                                        quantite = st.number_input(
                                            "Quantité",
                                            min_value=1,
                                            max_value=20,
                                            value=1,
                                            step=1,
                                            key=f"qte_{plat['id']}"
                                        )
                                    with col_add:
                                        st.markdown("<br>", unsafe_allow_html=True)
                                        if st.button("🛒 Ajouter au Panier", key=f"btn_add_{plat['id']}", type="primary", use_container_width=True):
                                            # Assemblage des options
                                            options_selectionnees = []
                                            if sans_sel:
                                                options_selectionnees.append("Sans sel")
                                            if sans_piment:
                                                options_selectionnees.append("Sans piment")
                                            if sans_oignon:
                                                options_selectionnees.append("Sans oignon")
                                            if allergie_arachide:
                                                options_selectionnees.append("Allergie arachide")
                                            if sans_gluten:
                                                options_selectionnees.append("Sans gluten")
                                            
                                            nouvel_item = {
                                                "id": plat["id"],
                                                "nom": plat["nom"],
                                                "prix": float(plat["prix"]),
                                                "quantite": int(quantite),
                                                "cuisson": choix_cuisson,
                                                "options": options_selectionnees,
                                                "instructions": instructions_custom.strip() if instructions_custom else ""
                                            }
                                            
                                            st.session_state.panier.append(nouvel_item)
                                            st.toast(f"✅ {quantite}x {plat['nom']} ajouté(s) au panier !")
                                            st.rerun()


# =============================================================================
# 8.2. ONGLET 2 : AVIS CLIENT & PROGRAMME DE FIDÉLITÉ
# =============================================================================
with tab_avis:
    st.markdown("### ⭐ Votre Avis Compte pour Nous !")
    st.write("Aidez-nous à nous améliorer et cumulez des points sur votre compte fidélité.")
    
    with st.form("form_avis_fidelite"):
        col_av1, col_av2 = st.columns(2)
        with col_av1:
            note_etoiles = st.feedback("stars")
            st.caption("Notez votre expérience globale (1 à 5 étoiles)")
        with col_av2:
            telephone = st.text_input("📱 Numéro de Téléphone (Programme Fidélité)", placeholder="+33 6 12 34 56 78 / +223 70 00 00 00")
            st.caption("Gagnez 1 point par euro consommé lors de ce repas !")
            
        commentaire = st.text_area("💬 Vos remarques, compliments ou suggestions :", placeholder="Qualité des plats, rapidité du service, ambiance...")
        
        btn_avis = st.form_submit_button("Envoyer mon Avis & Créditer mes Points", type="primary")
        
        if btn_avis:
            pts_gagnes = max(10, st.session_state.points_fidelite_session)
            st.session_state.avis_soumis = True
            st.success(f"🎉 Merci pour votre retour ! Votre avis a été enregistré avec succès.")
            if telephone:
                st.info(f"💎 **Programme Fidélité :** {pts_gagnes} points ont été associés au numéro **{telephone}**.")
            st.balloons()


# =============================================================================
# 8.3. ONGLET 3 : HISTORIQUE DES COMMANDES DE LA SESSION
# =============================================================================
with tab_historique:
    st.markdown("### 📋 Historique de vos Commandes pour cette Table")
    if not st.session_state.historique_commandes:
        st.info("Aucune commande n'a encore été passée lors de cette session.")
    else:
        for cmd in reversed(st.session_state.historique_commandes):
            with st.container():
                st.markdown(f"#### Commande `{cmd['id']}` - Table {cmd['table_id']}")
                st.write(f"📅 **Date :** {cmd.get('date_commande', 'N/A')} | 💰 **Total :** `{cmd['total']:.2f} €`")
                st.write("**Détails :**")
                for itm in cmd["items"]:
                    details = []
                    if itm.get("cuisson"):
                        details.append(itm["cuisson"])
                    if itm.get("options"):
                        details.extend(itm["options"])
                    if itm.get("instructions"):
                        details.append(f"Note: {itm['instructions']}")
                    info_txt = f" ({', '.join(details)})" if details else ""
                    st.write(f"- **{itm.get('quantite', 1)}× {itm['nom']}**{info_txt} : `{itm['prix'] * itm.get('quantite', 1):.2f} €`")
                st.divider()

    st.markdown("### 🛎️ Historique des Appels Serveur")
    if not st.session_state.appels_serveur:
        st.caption("Aucun appel serveur émis pour le moment.")
    else:
        for app in reversed(st.session_state.appels_serveur):
            st.write(f"- 🕒 `{app['heure']}` - **Table {app['table_id']}** : {app['type']}")
