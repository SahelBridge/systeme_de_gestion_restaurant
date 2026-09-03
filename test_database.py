"""Tests unitaires pour database.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import database


class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        # Création d'un fichier temporaire pour la base de données de test
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_resto.db"
        # Orientations vers la DB temporaire
        self.original_db_path = database.DEFAULT_DB_PATH
        database.DEFAULT_DB_PATH = self.db_path
        database.init_db(self.db_path)

    def tearDown(self) -> None:
        database.DEFAULT_DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_save_and_get_active_orders(self) -> None:
        items = [{"id": "plat_01", "nom": "Steak Frites", "quantite": 2, "sous_total": 31.0}]
        success = database.save_order(table_id=5, items=items, total=31.0, db_path=self.db_path)
        self.assertTrue(success)

        active = database.get_active_orders(self.db_path)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["table_id"], 5)
        self.assertEqual(active[0]["total"], 31.0)
        self.assertEqual(active[0]["items"][0]["nom"], "Steak Frites")

    def test_complete_order(self) -> None:
        items = [{"id": "plat_02", "nom": "Thiéboudienne", "quantite": 1, "sous_total": 14.0}]
        database.save_order(table_id=2, items=items, total=14.0, db_path=self.db_path)

        active_before = database.get_active_orders(self.db_path)
        self.assertEqual(len(active_before), 1)
        order_id = active_before[0]["id"]

        comp_success = database.complete_order(order_id, db_path=self.db_path)
        self.assertTrue(comp_success)

        active_after = database.get_active_orders(self.db_path)
        self.assertEqual(len(active_after), 0)

        all_orders = database.get_all_orders(self.db_path)
        self.assertEqual(len(all_orders), 1)
        self.assertEqual(all_orders[0]["status"], "terminee")


if __name__ == "__main__":
    unittest.main()

