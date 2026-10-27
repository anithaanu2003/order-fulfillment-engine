
import unittest

from src.id_generator import generate_order_id
from src.id_generator import generate_shipment_id
from src.id_generator import generate_tracking_event_id
from src.id_generator import generate_promise_id
class TestOrderIdGenerator(unittest.TestCase):

    def test_generates_first_order_id(self):
        self.assertEqual(
            generate_order_id(1),
            "ORD-2026-000001",
        )

    def test_generates_large_sequence(self):
        self.assertEqual(
            generate_order_id(50000),
            "ORD-2026-050000",
        )

    def test_supports_different_year(self):
        self.assertEqual(
            generate_order_id(12, 2027),
            "ORD-2027-000012",
        )

    def test_rejects_zero_sequence(self):
        with self.assertRaises(ValueError):
            generate_order_id(0)

    def test_rejects_negative_sequence(self):
        with self.assertRaises(ValueError):
            generate_order_id(-1)

    def test_rejects_unsupported_year(self):
        with self.assertRaises(ValueError):
            generate_order_id(1, 1999)
    
    
    def test_generates_first_shipment_id(self):
        self.assertEqual(
            generate_shipment_id(1),
            "SHP-2026-000001",
        )

    def test_generates_large_shipment_id(self):
        self.assertEqual(
            generate_shipment_id(50000),
            "SHP-2026-050000",
        )

    def test_rejects_zero_shipment_sequence(self):
        with self.assertRaises(ValueError):
            generate_shipment_id(0)
            
    
    def test_generates_tracking_event_id(self):
        self.assertEqual(
            generate_tracking_event_id("SHP-2026-000001", 1),
            "TRK-SHP-2026-000001-001",
        )

    def test_generates_next_tracking_event_id(self):
        self.assertEqual(
            generate_tracking_event_id("SHP-2026-000001", 2),
            "TRK-SHP-2026-000001-002",
        )

    def test_rejects_zero_tracking_sequence(self):
        with self.assertRaises(ValueError):
            generate_tracking_event_id("SHP-2026-000001", 0)
            
    
    def test_generates_promise_id(self):
        self.assertEqual(
            generate_promise_id("ORD-2026-000001", 1),
            "PROM-ORD-2026-000001-01",
        )

    def test_generates_second_promise_version(self):
        self.assertEqual(
            generate_promise_id("ORD-2026-000001", 2),
            "PROM-ORD-2026-000001-02",
        )

    def test_rejects_zero_promise_version(self):
        with self.assertRaises(ValueError):
            generate_promise_id("ORD-2026-000001", 0)





if __name__ == "__main__":
    unittest.main()
