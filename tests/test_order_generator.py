
import unittest
from datetime import datetime

from src.generate_orders import (
    generate_orders,
    START_TIME,
    END_TIME,
)


class TestOrderGenerator(unittest.TestCase):

    def test_generates_five_orders(self):
        self.assertEqual(len(generate_orders(5)), 5)

    def test_order_ids_are_sequential(self):
        orders = generate_orders(5)
        expected_ids = [
            f"ORD-2026-{number:06d}"
            for number in range(1, 6)
        ]
        self.assertEqual(
            [order["order_id"] for order in orders],
            expected_ids,
        )

    def test_generation_is_reproducible(self):
        self.assertEqual(generate_orders(5), generate_orders(5))

    def test_every_order_has_required_fields(self):
        required_fields = {
            "order_id",
            "order_timestamp",
            "destination_city",
            "destination_zone",
            "order_status",
            "created_at",
        }

        for order in generate_orders(5):
            self.assertTrue(required_fields.issubset(order))
            self.assertEqual(order["order_status"], "CREATED")

    def test_generated_orders_have_valid_destinations(self):
        valid_destinations = {
            ("Hyderabad", "SOUTH"),
            ("Bengaluru", "SOUTH"),
            ("Chennai", "SOUTH"),
            ("Mumbai", "WEST"),
            ("Pune", "WEST"),
            ("Delhi", "NORTH"),
            ("Chandigarh", "NORTH"),
            ("Kolkata", "EAST"),
            ("Bhubaneswar", "EAST"),
            ("Bhopal", "CENTRAL"),
            ("Nagpur", "CENTRAL"),
            ("Guwahati", "NORTHEAST"),
            ("Shillong", "NORTHEAST"),
        }

        for order in generate_orders(1000):
            destination = (
                order["destination_city"],
                order["destination_zone"],
            )
            self.assertIn(destination, valid_destinations)

    def test_order_timestamps_are_valid_and_within_calendar(self):
        for order in generate_orders(1000):
            parsed = datetime.fromisoformat(
                order["order_timestamp"]
            )
            self.assertGreaterEqual(parsed, START_TIME)
            self.assertLessEqual(parsed, END_TIME)

    def test_created_at_matches_order_timestamp(self):
        for order in generate_orders(5):
            self.assertEqual(
                order["created_at"],
                order["order_timestamp"],
            )

    def test_generates_50000_orders(self):
        orders = generate_orders(50_000)
        self.assertEqual(len(orders), 50_000)
        self.assertEqual(orders[0]["order_id"], "ORD-2026-000001")
        self.assertEqual(orders[-1]["order_id"], "ORD-2026-050000")

    def test_all_50000_order_ids_are_unique(self):
        orders = generate_orders(50_000)
        order_ids = [order["order_id"] for order in orders]
        self.assertEqual(len(order_ids), len(set(order_ids)))

    def test_full_dataset_covers_all_six_zones(self):
        orders = generate_orders(50_000)
        zones = {order["destination_zone"] for order in orders}
        self.assertEqual(
            zones,
            {
                "SOUTH",
                "WEST",
                "NORTH",
                "EAST",
                "CENTRAL",
                "NORTHEAST",
            },
        )

    def test_supports_custom_start_sequence(self):
        orders = generate_orders(3, start_sequence=101)
        self.assertEqual(
            [order["order_id"] for order in orders],
            [
                "ORD-2026-000101",
                "ORD-2026-000102",
                "ORD-2026-000103",
            ],
        )

    def test_rejects_invalid_arguments(self):
        for count in (-1, 1.5, True):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    generate_orders(count)

        with self.assertRaises(ValueError):
            generate_orders(1, start_sequence=0)


if __name__ == "__main__":
    unittest.main()
