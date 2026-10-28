
import random
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from .init_db import DATABASE_FILE
from .id_generator import generate_order_id

SEED = 20261022
SAMPLE_ORDER_COUNT = 5
FULL_DATASET_ORDER_COUNT = 50_000

PROJECT_ROOT = Path(__file__).resolve().parent.parent

START_TIME = datetime(2026, 10, 1, 8, 0, 0)
END_TIME = datetime(2026, 12, 31, 23, 59, 0)

# Synthetic destination data covering all six supported service zones.
CITIES = [
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
]


def resolve_database_path(database_file=None):
    """Use the supplied database, or the original default if omitted."""
    target = (
        Path(database_file)
        if database_file is not None
        else DATABASE_FILE
    )

    if not target.is_absolute():
        target = PROJECT_ROOT / target

    if not target.exists():
        raise FileNotFoundError(f"Database does not exist: {target}")

    return target


def generate_orders(count=SAMPLE_ORDER_COUNT, start_sequence=1):
    """Generate reproducible synthetic orders across all supported zones."""
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
    ):
        raise ValueError("count must be a non-negative integer.")

    if (
        not isinstance(start_sequence, int)
        or isinstance(start_sequence, bool)
        or start_sequence < 1
    ):
        raise ValueError("start_sequence must be a positive integer.")

    random_generator = random.Random(SEED)
    orders = []

    total_minutes = int(
        (END_TIME - START_TIME).total_seconds() // 60
    )

    for number in range(1, count + 1):
        order_time = START_TIME + timedelta(
            minutes=random_generator.randint(0, total_minutes)
        )

        city, zone = random_generator.choice(CITIES)

        orders.append({
            "order_id": generate_order_id(
                start_sequence + number - 1
            ),
            "order_timestamp": order_time.isoformat(),
            "destination_city": city,
            "destination_zone": zone,
            "order_status": "CREATED",
            "created_at": order_time.isoformat(),
        })

    return orders


def save_orders_to_database(orders, database_file=None):
    """Save orders only to the explicitly selected database."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
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


def get_order_count(database_file=None):
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()

    return row[0]


def get_next_order_number(database_file=None):
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        row = connection.execute(
            """
            SELECT MAX(CAST(SUBSTR(order_id, 10) AS INTEGER))
            FROM orders
            WHERE order_id LIKE 'ORD-2026-%'
            """
        ).fetchone()

    return (row[0] or 0) + 1


if __name__ == "__main__":
    # The standalone entry point retains its original default database.
    # Do not run it for the assessment dataset.
    existing_count = get_order_count()
    remaining_count = FULL_DATASET_ORDER_COUNT - existing_count

    if remaining_count <= 0:
        print(f"Target already reached: {existing_count} orders.")
    else:
        start_sequence = get_next_order_number()
        generated_orders = generate_orders(
            count=remaining_count,
            start_sequence=start_sequence,
        )
        saved_count = save_orders_to_database(generated_orders)

        print(f"Orders before generation: {existing_count}")
        print(f"Orders added: {saved_count}")
        print(f"Target order count: {existing_count + saved_count}")
