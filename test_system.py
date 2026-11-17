"""Test d integration complet du systeme SmartResto."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import api_backend
import database


class TestSmartRestoIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_system.db"
        self.original_db_path = database.DEFAULT_DB_PATH
        database.DEFAULT_DB_PATH = self.db_path
        database.init_db(self.db_path)

    def tearDown(self) -> None:
        database.DEFAULT_DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_menu_loading_and_filtering(self) -> None:
        menu = api_backend.load_menu()
        self.assertIsInstance(menu, list)
        self.assertGreater(len(menu), 0)

        # Filtre vegetarien avec et sans accent
        vege1 = api_backend.filter_menu("Vegetarien")
        vege2 = api_backend.filter_menu("végétarien")
        self.assertEqual(len(vege1), len(vege2))
        self.assertGreater(len(vege1), 0)

        # Filtre halal
        halal = api_backend.filter_menu("halal")
        self.assertGreater(len(halal), 0)

    def test_full_order_lifecycle(self) -> None:
        # 1. Estimation initiale (0 tickets -> 0 min)
        attente_init = api_backend.estimate_wait_time()
        self.assertEqual(attente_init, 0)

        # 2. Prise de commande par la tablette client
        items = [
            {
                "id": "plat_01",
                "quantite": 2,
                "cuisson": "A point",
                "options": ["Sans sel"]
            },
            {
                "id": "boisson_01",
                "quantite": 1
            }
        ]
        cmd = api_backend.process_order(table_id=4, order_items=items)
        self.assertIn("id", cmd)
        self.assertEqual(cmd["table_id"], 4)
        self.assertEqual(cmd["status"], "en_attente")
        # Steak (15.50 * 2 = 31) + Bissap (3.50 * 1) = 34.50
        self.assertEqual(cmd["total"], 34.50)

        # 3. Réception par la cuisine (KDS)
        actives = database.get_active_orders()
        self.assertEqual(len(actives), 1)
        self.assertEqual(actives[0]["id"], cmd["id"])
        self.assertEqual(len(actives[0]["items"]), 2)

        # 4. Nouvelle estimation d'attente (1 ticket actif -> 10 min)
        attente_apres = api_backend.estimate_wait_time()
        self.assertEqual(attente_apres, 10)

        # 5. Clôture de la commande par la cuisine
        comp_ok = database.complete_order(cmd["id"])
        self.assertTrue(comp_ok)
        self.assertEqual(len(database.get_active_orders()), 0)

        # 6. Vérification du Top des Ventes
        top = database.get_top_sales(limit=2)
        self.assertGreaterEqual(len(top), 1)
        self.assertEqual(top[0]["id"], "plat_01")
        self.assertEqual(top[0]["total_vendu"], 2)

    def test_server_call_lifecycle(self) -> None:
        # Envoi de la demande d'eau par la table 7
        self.assertTrue(database.save_server_call(table_id=7, call_type="Eau"))
        appels = database.get_active_server_calls()
        self.assertEqual(len(appels), 1)
        self.assertEqual(appels[0]["table_id"], 7)
        self.assertEqual(appels[0]["call_type"], "Eau")

        # Résolution par le serveur
        self.assertTrue(database.resolve_server_call(appels[0]["id"]))
        self.assertEqual(len(database.get_active_server_calls()), 0)

    def test_fidelity_and_review_lifecycle(self) -> None:
        phone = "+221770000000"
        # Dépôt d'un avis 5 étoiles et crédit de points
        self.assertTrue(database.save_review(table_id=4, stars=5, phone=phone, comment="Superbe service !"))
        self.assertTrue(database.save_fidelity_profile(phone, 35))

        solde = database.get_fidelity_points(phone)
        self.assertEqual(solde, 35)

        reviews = database.get_all_reviews()
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["stars"], 5)
        self.assertEqual(reviews[0]["comment"], "Superbe service !")

    def test_express_stock_rupture(self) -> None:
        # Désactivation du plat_01 par la cuisine
        self.assertTrue(database.set_dish_availability("plat_01", False))
        menu_avec_rupture = api_backend.load_menu(apply_overrides=True)
        plat1 = next(p for p in menu_avec_rupture if p["id"] == "plat_01")
        self.assertFalse(plat1["disponible"])

        # Réactivation
        self.assertTrue(database.set_dish_availability("plat_01", True))
        menu_reactif = api_backend.load_menu(apply_overrides=True)
        plat1_bis = next(p for p in menu_reactif if p["id"] == "plat_01")
        self.assertTrue(plat1_bis["disponible"])


if __name__ == "__main__":
    unittest.main()
