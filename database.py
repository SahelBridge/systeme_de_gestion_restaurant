"""Module de gestion de la base de données du restaurant.

Ce module gère la persistance des commandes à l'aide d'une base SQLite.
Il fournit les fonctions nécessaires à l'API Backend (api_backend.py),
à l'application client (app_client.py) et à l'écran cuisine (devcuisine.py).
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
    """Initialise le schéma de la base de données si la table n'existe pas."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
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
        conn.commit()
    finally:
        conn.close()


def save_order(
    table_id: int,
    items: list[dict[str, Any]],
    total: float,
    db_path: str | Path | None = None,
) -> bool:
    """Enregistre une nouvelle commande en base de données.

    Retourne True strictly en cas de succès pour satisfaire le contrat d'api_backend.py.
    """
    try:
        init_db(db_path)
        now = datetime.now()
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
    except Exception as error:
        # En cas d'erreur de persistance, on signale l'échec en renvoyant False
        return False


def get_active_orders(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Récupère la liste des commandes actives (statut != 'terminee')."""
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, table_id, items_json, total, status, date_commande
                FROM orders
                WHERE status != 'terminee' AND status != 'annulee'
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
