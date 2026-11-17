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

    def test_top_sales(self) -> None:
        items1 = [
            {"id": "plat_01", "nom": "Steak Frites", "quantite": 3, "prix_unitaire": 15.0},
            {"id": "dessert_01", "nom": "Tiramisu", "quantite": 1, "prix_unitaire": 6.0},
        ]
        items2 = [
            {"id": "plat_01", "nom": "Steak Frites", "quantite": 2, "prix_unitaire": 15.0},
            {"id": "plat_02", "nom": "Thiéboudienne", "quantite": 4, "prix_unitaire": 14.0},
        ]
        database.save_order(table_id=1, items=items1, total=51.0, db_path=self.db_path)
        database.save_order(table_id=2, items=items2, total=86.0, db_path=self.db_path)

        top = database.get_top_sales(limit=2, db_path=self.db_path)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["id"], "plat_01")
        self.assertEqual(top[0]["total_vendu"], 5)
        self.assertEqual(top[1]["id"], "plat_02")
        self.assertEqual(top[1]["total_vendu"], 4)

    def test_fidelity_and_reviews(self) -> None:
        phone = "+33612345678"
        self.assertTrue(database.save_fidelity_profile(phone, 25, db_path=self.db_path))
        self.assertEqual(database.get_fidelity_points(phone, db_path=self.db_path), 25)
        
        # Crédit additionnel
        self.assertTrue(database.save_fidelity_profile(phone, 15, db_path=self.db_path))
        self.assertEqual(database.get_fidelity_points(phone, db_path=self.db_path), 40)

        # Avis
        self.assertTrue(database.save_review(table_id=3, stars=5, phone=phone, comment="Excellent!", db_path=self.db_path))
        reviews = database.get_all_reviews(db_path=self.db_path)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["stars"], 5)
        self.assertEqual(reviews[0]["comment"], "Excellent!")

    def test_server_calls(self) -> None:
        self.assertTrue(database.save_server_call(table_id=4, call_type="Eau", db_path=self.db_path))
        calls = database.get_active_server_calls(db_path=self.db_path)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["table_id"], 4)
        self.assertEqual(calls[0]["call_type"], "Eau")

        call_id = calls[0]["id"]
        self.assertTrue(database.resolve_server_call(call_id, db_path=self.db_path))
        self.assertEqual(len(database.get_active_server_calls(db_path=self.db_path)), 0)

    def test_dish_availability(self) -> None:
        self.assertTrue(database.set_dish_availability("plat_01", False, db_path=self.db_path))
        overrides = database.get_dish_overrides(db_path=self.db_path)
        self.assertIn("plat_01", overrides)
        self.assertFalse(overrides["plat_01"])

        self.assertTrue(database.set_dish_availability("plat_01", True, db_path=self.db_path))
        overrides2 = database.get_dish_overrides(db_path=self.db_path)
        self.assertTrue(overrides2["plat_01"])


if __name__ == "__main__":
    unittest.main()


