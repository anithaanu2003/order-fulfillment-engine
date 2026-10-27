
from pathlib import Path
import sqlite3
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


class TestForeignKeys(unittest.TestCase):

    def test_inventory_rejects_unknown_warehouse(self):
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
                        "INV-TEST-UNKNOWN-NODE",
                        "FUL-DOES-NOT-EXIST",
                        "SKU-000001",
                        5,
                        0,
                        "2026-10-26T12:00:00",
                    ),
                )

    def test_inventory_rejects_unknown_sku(self):
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
                        "INV-TEST-UNKNOWN-SKU",
                        "FUL-2026-000001",
                        "SKU-DOES-NOT-EXIST",
                        5,
                        0,
                        "2026-10-26T12:00:00",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
