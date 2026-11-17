"""Module de gestion de la base de données du restaurant (SmartResto).

Ce module gère la persistance de toutes les données du restaurant à l'aide de SQLite :
- Commandes (actives, terminées, annulées)
- Programme de fidélité (points par numéro de téléphone)
- Avis clients et notations (1 à 5 étoiles)
- Appels serveur en direct (eau, pain, addition, requêtes personnalisées)
- Suivi dynamique de la disponibilité des plats (rupture de stock express)
- Statistiques de vente (Top 3 des ventes)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# Chemin par défaut de la base de données SQLite
DEFAULT_DB_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "restaurant.db"


def get_db_path(db_path: str | Path | None = None) -> Path:
    """Retourne le chemin effectif du fichier de base de données SQLite."""
    if db_path is not None:
        path = Path(db_path)
    else:
        path = DEFAULT_DB_PATH

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Ouvre une connexion à la base de données SQLite."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    """Initialise le schéma complet de la base de données si les tables n'existent pas."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # 1. Table des commandes
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                table_id INTEGER NOT NULL,
                items_json TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'en_attente',
                date_commande TEXT NOT NULL
            );
            """
        )
        
        # 2. Table du programme de fidélité (Cahier des charges - Personne 4)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fidelity (
                phone TEXT PRIMARY KEY,
                points INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            """
        )
        
        # 3. Table des avis clients
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                stars INTEGER NOT NULL,
                phone TEXT,
                comment TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        
        # 4. Table des appels serveur (Cahier des charges - Personne 1)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS server_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                call_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'en_attente',
                created_at TEXT NOT NULL
            );
            """
        )
        
        # 5. Table des ruptures de stock dynamiques (Cahier des charges - Personne 2)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dish_overrides (
                dish_id TEXT PRIMARY KEY,
                disponible INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );
            """
        )
        
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# GESTION DES COMMANDES
# =============================================================================

def save_order(
    table_id: int,
    items: list[dict[str, Any]],
    total: float,
    db_path: str | Path | None = None,
    order_id: str | None = None,
) -> bool:
    """Enregistre une nouvelle commande en base de données.

    Retourne True strictement en cas de succès pour satisfaire le contrat d'api_backend.py.
    """
    try:
        init_db(db_path)
        now = datetime.now()
        if not order_id:
            timestamp_str = now.strftime("%Y%m%d%H%M%S%f")[:17]
            order_id = f"CMD-{timestamp_str}"
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        items_json = json.dumps(items, ensure_ascii=False)

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO orders (id, table_id, items_json, total, status, date_commande)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (order_id, table_id, items_json, float(total), "en_attente", date_str),
            )
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def get_active_orders(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Récupère la liste des commandes actives (statut != 'terminee' et != 'annulee')."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, table_id, items_json, total, status, date_commande
                FROM orders
                WHERE status NOT IN ('terminee', 'annulee')
                ORDER BY date_commande ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        orders = []
        for row in rows:
            orders.append(
                {
                    "id": row["id"],
                    "table_id": row["table_id"],
                    "items": json.loads(row["items_json"]),
                    "total": row["total"],
                    "status": row["status"],
                    "date_commande": row["date_commande"],
                }
            )
        return orders
    except Exception:
        return []


def update_order_status(
    order_id: str,
    status: str,
    db_path: str | Path | None = None,
) -> bool:
    """Met à jour le statut d'une commande (ex: 'en_cours', 'terminee', 'annulee')."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE orders
                SET status = ?
                WHERE id = ?
                """,
                (status, order_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    except Exception:
        return False


def complete_order(order_id: str, db_path: str | Path | None = None) -> bool:
    """Marque une commande comme terminée."""
    return update_order_status(order_id, "terminee", db_path)


def get_all_orders(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Récupère la totalité de l'historique des commandes."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, table_id, items_json, total, status, date_commande
                FROM orders
                ORDER BY date_commande DESC
                """
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        orders = []
        for row in rows:
            orders.append(
                {
                    "id": row["id"],
                    "table_id": row["table_id"],
                    "items": json.loads(row["items_json"]),
                    "total": row["total"],
                    "status": row["status"],
                    "date_commande": row["date_commande"],
                }
            )
        return orders
    except Exception:
        return []


# =============================================================================
# STATISTIQUES & TOP VENTES (Cahier des charges - Personne 4)
# =============================================================================

def get_top_sales(limit: int = 3, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Calcule le classement des plats les plus vendus (Top ventes)."""
    try:
        init_db(db_path)
        orders = get_all_orders(db_path)
        
        ventes: dict[str, dict[str, Any]] = {}
        for order in orders:
            if order.get("status") == "annulee":
                continue
            for item in order.get("items", []):
                dish_id = item.get("id", item.get("nom", "inconnu"))
                nom = item.get("nom", dish_id)
                quantite = int(item.get("quantite", item.get("quantity", 1)))
                prix = float(item.get("prix_unitaire", item.get("prix", 0.0)))
                
                if dish_id not in ventes:
                    ventes[dish_id] = {
                        "id": dish_id,
                        "nom": nom,
                        "total_vendu": 0,
                        "revenu_total": 0.0
                    }
                ventes[dish_id]["total_vendu"] += quantite
                ventes[dish_id]["revenu_total"] += quantite * prix
        
        classement = sorted(ventes.values(), key=lambda x: x["total_vendu"], reverse=True)
        return classement[:limit]
    except Exception:
        return []


# =============================================================================
# PROGRAMME DE FIDÉLITÉ (Cahier des charges - Personne 4)
# =============================================================================

def save_fidelity_profile(phone: str, points: int, db_path: str | Path | None = None) -> bool:
    """Crédite ou met à jour des points de fidélité pour un numéro de téléphone."""
    phone_clean = phone.strip()
    if not phone_clean:
        return False
    try:
        init_db(db_path)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fidelity (phone, points, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(phone) DO UPDATE SET
                    points = points + excluded.points,
                    updated_at = excluded.updated_at
                """,
                (phone_clean, max(0, points), now_str)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def get_fidelity_points(phone: str, db_path: str | Path | None = None) -> int:
    """Récupère le solde de points d'un client par son numéro de téléphone."""
    phone_clean = phone.strip()
    if not phone_clean:
        return 0
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM fidelity WHERE phone = ?", (phone_clean,))
            row = cursor.fetchone()
            return row["points"] if row else 0
        finally:
            conn.close()
    except Exception:
        return 0


# =============================================================================
# AVIS ET NOTATIONS CLIENTS
# =============================================================================

def save_review(
    table_id: int,
    stars: int,
    phone: str = "",
    comment: str = "",
    db_path: str | Path | None = None,
) -> bool:
    """Enregistre l'évaluation d'un client."""
    try:
        init_db(db_path)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reviews (table_id, stars, phone, comment, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (table_id, stars, phone.strip(), comment.strip(), now_str)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def get_all_reviews(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Récupère tous les avis laissés par les clients."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, table_id, stars, phone, comment, created_at
                FROM reviews
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    except Exception:
        return []


# =============================================================================
# APPELS SERVEUR (Cahier des charges - Personne 1)
# =============================================================================

def save_server_call(table_id: int, call_type: str, db_path: str | Path | None = None) -> bool:
    """Enregistre un appel serveur (ex: 'Eau', 'Pain', 'Addition', 'Demande personnalisée')."""
    try:
        init_db(db_path)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO server_calls (table_id, call_type, status, created_at)
                VALUES (?, ?, 'en_attente', ?)
                """,
                (table_id, call_type, now_str)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def get_active_server_calls(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Récupère les appels serveur non encore traités."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, table_id, call_type, status, created_at
                FROM server_calls
                WHERE status = 'en_attente'
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    except Exception:
        return []


def resolve_server_call(call_id: int, db_path: str | Path | None = None) -> bool:
    """Marque un appel serveur comme traité."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE server_calls
                SET status = 'traite'
                WHERE id = ?
                """,
                (call_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    except Exception:
        return False


# =============================================================================
# RUPTURE DE STOCK EXPRESS (Cahier des charges - Personne 2)
# =============================================================================

def set_dish_availability(dish_id: str, disponible: bool, db_path: str | Path | None = None) -> bool:
    """Active ou désactive la disponibilité d'un plat (Rupture de stock)."""
    try:
        init_db(db_path)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dish_overrides (dish_id, disponible, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(dish_id) DO UPDATE SET
                    disponible = excluded.disponible,
                    updated_at = excluded.updated_at
                """,
                (dish_id, 1 if disponible else 0, now_str)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def get_dish_overrides(db_path: str | Path | None = None) -> dict[str, bool]:
    """Récupère la table des surcharges de disponibilité des plats."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT dish_id, disponible FROM dish_overrides")
            rows = cursor.fetchall()
            return {row["dish_id"]: bool(row["disponible"]) for row in rows}
        finally:
            conn.close()
    except Exception:
        return {}
