"""Logique metier du systeme Resto.

Ce module ne depend pas de Streamlit : il peut donc etre utilise aussi bien par
l'interface tablette que par l'ecran cuisine et teste independamment.
"""

# Rend les annotations de type plus souples à l'exécution.
from __future__ import annotations

# Lit le catalogue de plats au format JSON.
import json
# Sert à comparer les tags indépendamment des accents.
import unicodedata
# Construit le chemin vers le fichier du menu.
from pathlib import Path
# Indique qu'une valeur peut avoir différents types.
from typing import Any


# Chemin absolu du catalogue JSON, basé sur le dossier de ce fichier.
MENU_PATH = Path(__file__).resolve().parent / "data" / "menu.json"
# Durée ajoutée à l'estimation pour chaque ticket actif.
MINUTES_PER_ACTIVE_TICKET = 10


class OrderValidationError(ValueError):
    """Erreur levee lorsqu'une commande recue n'est pas exploitable."""


class OrderPersistenceError(RuntimeError):
    """Erreur levee lorsque la commande validee ne peut pas etre enregistree."""


def _normalise(value: str) -> str:
    """Normalise un tag pour accepter, par exemple, ``vegetarien`` et ``végétarien``."""
    # Retire les espaces, met en minuscules et sépare les accents des lettres.
    decomposed = unicodedata.normalize("NFD", value.strip().lower())
    # Reconstruit le texte sans les marques d'accent (catégorie Unicode Mn).
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def load_menu(menu_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Charge et controle sommairement le catalogue JSON.

    ``menu_path`` est optionnel afin de simplifier les tests sans modifier le
    catalogue partage par l'equipe.
    """
    # Prend le chemin fourni pour les tests, ou le menu principal par défaut.
    path = Path(menu_path) if menu_path is not None else MENU_PATH
    try:
        # Ouvre le fichier dans l'encodage standard UTF-8 (avec support BOM transparent).
        with path.open("r", encoding="utf-8-sig") as menu_file:
            # Convertit le contenu JSON en liste/dictionnaires Python.
            menu = json.load(menu_file)
    except FileNotFoundError as error:
        # Ajoute un message métier tout en gardant la cause originale.
        raise FileNotFoundError(f"Catalogue introuvable : {path}") from error
    except json.JSONDecodeError as error:
        # Signale un fichier existant dont la syntaxe JSON est invalide.
        raise ValueError(f"Catalogue JSON invalide : {path}") from error

    # Le contrat de données exige une liste de plats.
    if not isinstance(menu, list):
        raise ValueError("Le catalogue doit etre une liste de plats.")
    # Remet le catalogue validé à l'appelant.
    return menu


def filter_menu(
    dietary_tag: str | None = None,
    *,
    available_only: bool = True,
    menu_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Retourne les plats correspondant a un regime alimentaire.

    Exemple : ``filter_menu('Vegetarien')`` ou ``filter_menu('halal')``.
    Sans tag, la fonction retourne tous les plats (disponibles par defaut).
    """
    # Rejette un tag qui n'est pas du texte ou qui est vide.
    if dietary_tag is not None and (not isinstance(dietary_tag, str) or not dietary_tag.strip()):
        raise ValueError("Le tag alimentaire doit etre une chaine non vide.")

    # Normalise le tag recherché ; None signifie « pas de filtre alimentaire ».
    expected_tag = _normalise(dietary_tag) if dietary_tag else None
    # Stocke progressivement les plats retenus.
    filtered_menu: list[dict[str, Any]] = []
    # Examine chaque entrée chargée depuis le catalogue.
    for dish in load_menu(menu_path):
        # Ignore une entrée qui n'est pas un dictionnaire de plat.
        if not isinstance(dish, dict):
            continue
        # Écarte les plats non disponibles si le filtre est actif.
        if available_only and not dish.get("disponible", False):
            continue
        # Récupère les tags, ou une liste vide s'ils sont absents.
        tags = dish.get("tags", [])
        # Écarte le plat lorsqu'il ne correspond pas au régime demandé.
        if expected_tag and expected_tag not in {_normalise(str(tag)) for tag in tags}:
            continue
        # Copie le plat pour ne pas exposer l'objet original du menu.
        filtered_menu.append(dish.copy())
    # Retourne le menu filtré.
    return filtered_menu


# Alias explicite, pratique pour les interfaces qui preferent un nom descriptif.
# Crée un alias au nom plus descriptif pour les interfaces.
filter_menu_by_diet = filter_menu


def estimate_wait_time(active_orders: list[dict[str, Any]] | None = None) -> int:
    """Estime l'attente en minutes : 10 minutes par ticket deja en cuisine."""
    # Charge les commandes en base seulement si elles ne sont pas déjà fournies.
    if active_orders is None:
        try:
            # L'import local maintient ce module testable sans la base de données.
            from database import get_active_orders

            # Demande la liste des tickets toujours en cours à la cuisine.
            active_orders = get_active_orders()
        except (ImportError, ModuleNotFoundError) as error:
            # Transforme le problème technique en erreur métier claire.
            raise OrderPersistenceError("Le module database.py est indisponible.") from error

    # Le calcul ne peut être effectué qu'à partir d'une liste.
    if not isinstance(active_orders, list):
        raise ValueError("Les commandes actives doivent etre fournies sous forme de liste.")
    # Multiplie les tickets actifs par le délai moyen défini comme constante.
    return len(active_orders) * MINUTES_PER_ACTIVE_TICKET


def _validate_table_id(table_id: int) -> int:
    # Rejette les booléens, les non-entiers et les numéros inférieurs à 1.
    if isinstance(table_id, bool) or not isinstance(table_id, int) or table_id <= 0:
        raise OrderValidationError("Le numero de table doit etre un entier positif.")
    # Renvoie l'identifiant après validation.
    return table_id


def _parse_item(raw_item: Any) -> tuple[str, int, dict[str, Any]]:
    """Accepte un id simple ou un objet ``{id, quantite, ...}`` provenant de l'UI."""
    # Un identifiant seul désigne une unité du plat, sans personnalisation.
    if isinstance(raw_item, str):
        return raw_item, 1, {}
    # Tout autre format valide doit être un dictionnaire.
    if not isinstance(raw_item, dict):
        raise OrderValidationError("Chaque article doit etre un id de plat ou un dictionnaire.")

    # Accepte les deux appellations prévues pour l'identifiant du plat.
    dish_id = raw_item.get("id", raw_item.get("plat_id"))
    # Accepte les noms français et anglais pour la quantité.
    quantity = raw_item.get("quantite", raw_item.get("quantity", 1))
    # Vérifie que l'identifiant est une chaîne non vide.
    if not isinstance(dish_id, str) or not dish_id.strip():
        raise OrderValidationError("Chaque article doit contenir un id de plat.")
    # Vérifie que la quantité est un entier positif et non un booléen.
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise OrderValidationError("La quantite de chaque article doit etre un entier positif.")

    # Conserve uniquement les informations de personnalisation de l'interface.
    details = {
        key: value
        for key, value in raw_item.items()
        if key not in {"id", "plat_id", "quantite", "quantity"}
    }
    # Retourne les informations normalisées de l'article.
    return dish_id, quantity, details


def process_order(table_id: int, order_items: list) -> dict:
    """Valide une commande, calcule son total, l'enregistre et renvoie son detail.

    ``order_items`` accepte ``['plat_01']`` ou
    ``[{'id': 'plat_01', 'quantite': 2, 'personnalisation': ['Sans sel']}]``.
    """
    # Vérifie le numéro de table avant de traiter la commande.
    _validate_table_id(table_id)
    # Une commande valide doit contenir au moins un article dans une liste.
    if not isinstance(order_items, list) or not order_items:
        raise OrderValidationError("La commande doit contenir au moins un article.")

    # Indexe les plats par id afin de les trouver rapidement pendant la validation.
    menu_by_id = {
        dish.get("id"): dish
        for dish in load_menu()
        if isinstance(dish, dict) and isinstance(dish.get("id"), str)
    }
    # Prépare la liste des articles qui seront effectivement enregistrés.
    validated_items: list[dict[str, Any]] = []
    # Initialise le total avant de cumuler les sous-totaux.
    total = 0.0

    # Traite chaque article reçu depuis l'interface cliente.
    for raw_item in order_items:
        # Extrait un format d'article uniforme et ses personnalisations.
        dish_id, quantity, extra_details = _parse_item(raw_item)
        # Cherche le plat dans le catalogue indexé.
        dish = menu_by_id.get(dish_id)
        # Refuse un identifiant qui ne figure pas dans le menu.
        if dish is None:
            raise OrderValidationError(f"Plat inconnu : {dish_id}")
        # Refuse un plat actuellement indisponible.
        if not dish.get("disponible", False):
            raise OrderValidationError(f"Plat indisponible : {dish.get('nom', dish_id)}")
        try:
            # Convertit le prix du menu en nombre pour le calculer.
            unit_price = float(dish["prix"])
        except (KeyError, TypeError, ValueError) as error:
            # Signale un prix absent ou inutilisable.
            raise OrderValidationError(f"Prix invalide pour le plat : {dish_id}") from error
        # Interdit un prix négatif, même s'il est convertible en float.
        if unit_price < 0:
            raise OrderValidationError(f"Prix invalide pour le plat : {dish_id}")

        # Calcule et arrondit le montant de cet article.
        subtotal = round(unit_price * quantity, 2)
        # Construit l'objet article final avec ses informations calculées.
        item = {
            "id": dish_id,
            "nom": dish.get("nom", dish_id),
            "prix_unitaire": unit_price,
            "quantite": quantity,
            "sous_total": subtotal,
        }
        # Ajoute les personnalisations, comme « Sans sel », si elles existent.
        item.update(extra_details)
        # Ajoute l'article validé à la commande finale.
        validated_items.append(item)
        # Cumule le sous-total dans le montant global.
        total += subtotal

    # Arrondit le total à deux décimales pour une valeur monétaire propre.
    total = round(total, 2)
    # Évalue le délai en fonction des tickets actifs avant la nouvelle commande.
    estimated_wait_time = estimate_wait_time()

    try:
        # Importe la fonction de sauvegarde seulement au moment de l'utiliser.
        from database import save_order

        # Enregistre la commande validée et récupère la confirmation de la base.
        saved = save_order(table_id, validated_items, total)
    except (ImportError, ModuleNotFoundError) as error:
        # Explique l'absence du module chargé de la persistance.
        raise OrderPersistenceError("Le module database.py est indisponible.") from error
    except Exception as error:
        # Uniformise les erreurs de sauvegarde sous une erreur métier.
        raise OrderPersistenceError("Impossible d'enregistrer la commande.") from error

    # Exige une confirmation explicite de réussite.
    if saved is not True:
        raise OrderPersistenceError("La base de donnees a refuse l'enregistrement de la commande.")

    # Renvoie à l'interface toutes les informations utiles de la commande créée.
    return {
        "table_id": table_id,
        "items": validated_items,
        "total": total,
        "estimated_wait_time": estimated_wait_time,
        "estimated_wait_time_minutes": estimated_wait_time,
        "status": "en_attente",
    }
