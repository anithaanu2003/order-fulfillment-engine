
from pathlib import Path
import sqlite3
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


class TestInventoryConstraints(unittest.TestCase):

    def test_negative_available_quantity_is_rejected(self):
        with sqlite3.connect(DATABASE_FILE) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO inventory (
                        inventory_id,
                        node_id,
                        sku_id,
                        available_quantity,
                        reserved_quantity,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "INV-TEST-NEGATIVE",
                        "FUL-2026-000001",
                        "SKU-000001",
                        -1,
                        0,
                        "2026-10-26T12:00:00",
                    ),
                )

    def test_reserved_quantity_cannot_exceed_available(self):
        with sqlite3.connect(DATABASE_FILE) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO inventory (
                        inventory_id,
                        node_id,
                        sku_id,
                        available_quantity,
                        reserved_quantity,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "INV-TEST-RESERVED",
                        "FUL-2026-000001",
                        "SKU-000001",
                        5,
                        6,
                        "2026-10-26T12:00:00",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
