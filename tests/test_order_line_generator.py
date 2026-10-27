
import unittest

from src.generate_order_lines import generate_order_lines
from src.generate_orders import generate_orders


class TestOrderLineGenerator(unittest.TestCase):

    def test_generates_order_lines(self):
        lines = generate_order_lines(5)
        self.assertGreater(len(lines), 0)

    def test_every_line_has_required_fields(self):
        lines = generate_order_lines(5)

        required_fields = {
            "order_line_id",
            "order_id",
            "sku_id",
            "quantity",
            "unit_price",
        }

        for line in lines:
            self.assertTrue(required_fields.issubset(line.keys()))

    def test_quantities_are_positive(self):
        lines = generate_order_lines(5)

        for line in lines:
            self.assertGreater(line["quantity"], 0)

    def test_prices_are_non_negative(self):
        lines = generate_order_lines(5)

        for line in lines:
            self.assertGreaterEqual(line["unit_price"], 0)

    def test_lines_reference_generated_orders(self):
        orders = generate_orders(5)
        lines = generate_order_lines(5)

        order_ids = {order["order_id"] for order in orders}

        for line in lines:
            self.assertIn(line["order_id"], order_ids)

    def test_generation_is_reproducible(self):
        first_run = generate_order_lines(5)
        second_run = generate_order_lines(5)

        self.assertEqual(first_run, second_run)
        
    
    def test_order_line_ids_are_unique(self):
        lines = generate_order_lines(5)

        line_ids = [line["order_line_id"] for line in lines]

        self.assertEqual(len(line_ids), len(set(line_ids)))
        
    
    def test_no_duplicate_skus_within_an_order(self):
        lines = generate_order_lines(20)

        order_sku_pairs = [
            (line["order_id"], line["sku_id"])
            for line in lines
        ]

        self.assertEqual(
            len(order_sku_pairs),
            len(set(order_sku_pairs)),
        )
    
    
    def test_line_ids_are_unique_for_larger_dataset(self):
        lines = generate_order_lines(1000)

        line_ids = [
            line["order_line_id"]
            for line in lines
        ]

        self.assertEqual(len(line_ids), len(set(line_ids)))
        
    
    def test_generates_order_lines_for_50000_orders(self):
        lines = generate_order_lines(50000)

        self.assertGreater(len(lines), 50000)

        line_ids = [line["order_line_id"] for line in lines]
        self.assertEqual(len(line_ids), len(set(line_ids)))
        
    
    def test_every_order_has_at_least_one_line(self):
        orders = generate_orders(1000)
        lines = generate_order_lines(1000)

        order_ids = {order["order_id"] for order in orders}
        line_order_ids = {line["order_id"] for line in lines}

        self.assertEqual(order_ids, line_order_ids)
        
    
    def test_quantities_are_within_expected_range(self):
        lines = generate_order_lines(1000)

        for line in lines:
            self.assertIn(line["quantity"], [1, 2, 3])
            
    
    def test_unit_prices_match_product_catalog(self):
        expected_prices = {
            "SKU-000001": 55000.00,
            "SKU-000002": 750.00,
            "SKU-000003": 1500.00,
            "SKU-000004": 12000.00,
            "SKU-000005": 2500.00,
        }

        lines = generate_order_lines(1000)

        for line in lines:
            self.assertEqual(
                line["unit_price"],
                expected_prices[line["sku_id"]]
            )
    
    def test_order_lines_reference_valid_skus(self):
        valid_skus = {
            "SKU-000001",
            "SKU-000002",
            "SKU-000003",
            "SKU-000004",
            "SKU-000005",
        }

        lines = generate_order_lines(1000)

        for line in lines:
            self.assertIn(line["sku_id"], valid_skus)
            
    
    def test_every_order_line_references_an_existing_order(self):
        orders = generate_orders(1000)
        lines = generate_order_lines(1000)

        valid_order_ids = {
            order["order_id"] for order in orders
        }

        for line in lines:
            self.assertIn(line["order_id"], valid_order_ids)







if __name__ == "__main__":
    unittest.main()
