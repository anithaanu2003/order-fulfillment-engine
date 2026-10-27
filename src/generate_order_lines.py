import random
import sqlite3

from .id_generator import generate_order_id
from .init_db import DATABASE_FILE

SEED = 20261022

PRODUCTS = [
    ("SKU-000001", 55000.00),
    ("SKU-000002", 750.00),
    ("SKU-000003", 1500.00),
    ("SKU-000004", 12000.00),
    ("SKU-000005", 2500.00),
]


def generate_order_lines(order_count=5, start_sequence=1):
    rng = random.Random(SEED)
    order_lines = []
    line_number = 1

    for order_number in range(1, order_count + 1):
        order_id = generate_order_id(start_sequence + order_number - 1)

        # Each order contains between 1 and 3 different products.
        product_count = rng.randint(1, 3)
        selected_products = rng.sample(PRODUCTS, product_count)

        for sku_id, unit_price in selected_products:
            order_lines.append({
                "order_line_id": f"LINE-{line_number:06d}",
                "order_id": order_id,
                "sku_id": sku_id,
                "quantity": rng.randint(1, 3),
                "unit_price": unit_price,
            })
            line_number += 1

    return order_lines

def save_order_lines_to_database(order_lines):
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executemany(
            """
            INSERT INTO order_lines (
                order_line_id,
                order_id,
                sku_id,
                quantity,
                unit_price
            )
            VALUES (
                :order_line_id,
                :order_id,
                :sku_id,
                :quantity,
                :unit_price
            )
            """,
            order_lines,
        )

    return len(order_lines)

def get_orders_without_lines():
    with sqlite3.connect(DATABASE_FILE) as connection:
        rows = connection.execute(
            """
            SELECT o.order_id
            FROM orders o
            LEFT JOIN order_lines ol
                ON o.order_id = ol.order_id
            WHERE ol.order_id IS NULL
            ORDER BY o.order_id
            """
        ).fetchall()

    return [row[0] for row in rows]

def generate_lines_for_orders(order_ids):
    rng = random.Random(SEED)
    order_lines = []
    with sqlite3.connect(DATABASE_FILE) as connection:
        row = connection.execute(
        """
        SELECT MAX(CAST(SUBSTR(order_line_id, 6) AS INTEGER))
        FROM order_lines
        WHERE order_line_id LIKE 'LINE-%'
        """
    ).fetchone()

    line_number = (row[0] or 0) + 1

    for order_id in order_ids:
        product_count = rng.randint(1, 3)
        selected_products = rng.sample(PRODUCTS, product_count)

        for sku_id, unit_price in selected_products:
            order_lines.append({
                "order_line_id": f"LINE-{line_number:06d}",
                "order_id": order_id,
                "sku_id": sku_id,
                "quantity": rng.randint(1, 3),
                "unit_price": unit_price,
            })
            line_number += 1

    return order_lines


if __name__ == "__main__":
    order_ids = get_orders_without_lines()

    if not order_ids:
        print("All existing orders already have order lines.")
    else:
        lines = generate_lines_for_orders(order_ids)
        saved_count = save_order_lines_to_database(lines)

        print(f"Orders processed: {len(order_ids)}")
        print(f"Order lines saved: {saved_count}")

        for line in lines:
            print(line)
