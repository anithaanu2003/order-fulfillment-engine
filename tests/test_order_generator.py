
import unittest

from src.generate_orders import generate_orders


class TestOrderGenerator(unittest.TestCase):

    def test_generates_five_orders(self):
        orders = generate_orders(5)
        self.assertEqual(len(orders), 5)

    def test_order_ids_are_sequential(self):
        orders = generate_orders(5)

        expected_ids = [
            "ORD-2026-000001",
            "ORD-2026-000002",
            "ORD-2026-000003",
            "ORD-2026-000004",
            "ORD-2026-000005",
        ]

        actual_ids = [order["order_id"] for order in orders]
        self.assertEqual(actual_ids, expected_ids)

    def test_generation_is_reproducible(self):
        first_run = generate_orders(5)
        second_run = generate_orders(5)

        self.assertEqual(first_run, second_run)
        
    
    def test_every_order_has_required_fields(self):
        orders = generate_orders(5)

        required_fields = {
            "order_id",
            "order_timestamp",
            "destination_city",
            "destination_zone",
            "order_status",
            "created_at",
        }

        for order in orders:
            self.assertTrue(required_fields.issubset(order.keys()))

    def test_generated_orders_have_valid_destinations(self):
        orders = generate_orders(5)

        valid_cities = {"Hyderabad", "Bengaluru", "Chennai"}

        for order in orders:
            self.assertIn(order["destination_city"], valid_cities)
            self.assertEqual(order["destination_zone"], "SOUTH")
        
    
    def test_order_timestamps_are_valid(self):
        from datetime import datetime

        orders = generate_orders(5)

        for order in orders:
            parsed_time = datetime.fromisoformat(
                order["order_timestamp"]
            )
            self.assertIsInstance(parsed_time, datetime)

    def test_created_at_matches_order_timestamp(self):
        orders = generate_orders(5)

        for order in orders:
            self.assertEqual(
                order["created_at"],
                order["order_timestamp"],
            )
    
    
    def test_generates_50000_orders(self):
        orders = generate_orders(50000)

        self.assertEqual(len(orders), 50000)
        self.assertEqual(
            orders[0]["order_id"],
            "ORD-2026-000001",
        )
        self.assertEqual(
            orders[-1]["order_id"],
            "ORD-2026-050000",
        )
        
    
    def test_all_50000_order_ids_are_unique(self):
        orders = generate_orders(50000)

        order_ids = [
            order["order_id"]
            for order in orders
        ]

        self.assertEqual(len(order_ids), len(set(order_ids)))



if __name__ == "__main__":
    unittest.main()
