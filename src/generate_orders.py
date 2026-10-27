
import random
import sqlite3

from .init_db import DATABASE_FILE
from datetime import datetime, timedelta
from .id_generator import generate_order_id
SEED = 20261022
SAMPLE_ORDER_COUNT = 5
FULL_DATASET_ORDER_COUNT = 50_000

CITIES = [
    ("Hyderabad", "SOUTH"),
    ("Bengaluru", "SOUTH"),
    ("Chennai", "SOUTH"),
]


def generate_orders(count=SAMPLE_ORDER_COUNT, start_sequence=1):
    random_generator = random.Random(SEED)
    orders = []

    start_time = datetime(2026, 10, 1, 8, 0, 0)

    for number in range(1, count + 1):
        order_time = start_time + timedelta(
            minutes=random_generator.randint(0, 60 * 24 * 30)
        )

        city, zone = random_generator.choice(CITIES)

        order = {
            "order_id": generate_order_id(start_sequence + number - 1),
            "order_timestamp": order_time.isoformat(),
            "destination_city": city,
            "destination_zone": zone,
            "order_status": "CREATED",
            "created_at": order_time.isoformat(),
        }

        orders.append(order)

    return orders

def save_orders_to_database(orders):
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executemany(
            """
            INSERT INTO orders (
                order_id,
                order_timestamp,
                destination_city,
                destination_zone,
                order_status,
                created_at
            )
            VALUES (
                :order_id,
                :order_timestamp,
                :destination_city,
                :destination_zone,
                :order_status,
                :created_at
            )
            """,
            orders,
        )

    return len(orders)

def get_order_count():
    with sqlite3.connect(DATABASE_FILE) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()

    return row[0]

def get_next_order_number():
    with sqlite3.connect(DATABASE_FILE) as connection:
        row = connection.execute(
            """
            SELECT MAX(CAST(SUBSTR(order_id, 10) AS INTEGER))
            FROM orders
            WHERE order_id LIKE 'ORD-2026-%'
            """
        ).fetchone()

    return (row[0] or 0) + 1



if __name__ == "__main__":
    existing_count = get_order_count()

    remaining_count = FULL_DATASET_ORDER_COUNT - existing_count

    if remaining_count <= 0:
        print(
            f"Target already reached: {existing_count} orders."
        )
    else:
        start_sequence = get_next_order_number()

        generated_orders = generate_orders(
            count=remaining_count,
            start_sequence=start_sequence,
        )

        saved_count = save_orders_to_database(generated_orders)

        print(f"Orders before generation: {existing_count}")
        print(f"Orders added: {saved_count}")
        print(
            f"Target order count: "
            f"{existing_count + saved_count}"
        )
