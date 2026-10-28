
import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "fulfillment.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "exports" / "current_snapshot"


def sha256_file(file_path):
    """Return the SHA-256 checksum of a file."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def quote_identifier(identifier):
    """Safely quote a SQLite table or column identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def get_table_names(connection):
    """Return user-created tables in a stable order."""
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    return [row[0] for row in rows]


def get_columns_and_order(connection, table_name):
    """Return column names and a deterministic row ordering."""
    table = quote_identifier(table_name)

    info = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    columns = [row[1] for row in info]

    primary_key_columns = sorted(
        (row[5], row[1])
        for row in info
        if row[5] > 0
    )

    if primary_key_columns:
        order_columns = [column for _, column in primary_key_columns]
    else:
        order_columns = columns

    return columns, order_columns


def export_table(connection, table_name, output_directory):
    """Export one SQLite table to CSV and JSON."""
    table = quote_identifier(table_name)
    columns, order_columns = get_columns_and_order(
        connection,
        table_name,
    )

    selected_columns = ", ".join(
        quote_identifier(column) for column in columns
    )
    ordering = ", ".join(
        quote_identifier(column) for column in order_columns
    )

    query = f"SELECT {selected_columns} FROM {table}"

    if ordering:
        query += f" ORDER BY {ordering}"

    cursor = connection.execute(query)
    csv_path = output_directory / f"{table_name}.csv"
    json_path = output_directory / f"{table_name}.json"

    count = 0

    with (
        csv_path.open("w", encoding="utf-8", newline="") as csv_file,
        json_path.open("w", encoding="utf-8", newline="") as json_file,
    ):
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(columns)

        json_file.write("[\n")
        first_record = True

        for row in cursor:
            values = list(row)
            csv_writer.writerow(values)

            if not first_record:
                json_file.write(",\n")

            record = dict(zip(columns, values))
            json_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )

            first_record = False
            count += 1

        json_file.write("\n]\n")

    return {
        "rows": count,
        "csv": {
            "file": csv_path.name,
            "sha256": sha256_file(csv_path),
        },
        "json": {
            "file": json_path.name,
            "sha256": sha256_file(json_path),
        },
    }


def export_dataset(database_file, output_directory):
    """Export every user-created table without modifying the database."""
    database_file = Path(database_file).resolve()
    output_directory = Path(output_directory).resolve()

    if not database_file.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_file}"
        )

    # Refuse to overwrite an existing export directory.
    # This protects previous exports from accidental replacement.
    if output_directory.exists() and any(output_directory.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty: {output_directory}\n"
            "Choose a new output directory to preserve existing exports."
        )

    output_directory.mkdir(parents=True, exist_ok=True)

    database_uri = database_file.as_uri() + "?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)

    try:
        table_names = get_table_names(connection)

        if not table_names:
            raise RuntimeError("No user-created tables were found.")

        manifest = {
            "format_version": 1,
            "tables": {},
        }

        for table_name in table_names:
            result = export_table(
                connection,
                table_name,
                output_directory,
            )
            manifest["tables"][table_name] = result

            print(
                f"{table_name}: {result['rows']:,} rows exported"
            )

        manifest_path = output_directory / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        print("\nExport completed.")
        print(f"Output directory: {output_directory}")
        print(f"Manifest: {manifest_path}")

    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export SQLite tables to deterministic CSV and JSON."
    )
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DATABASE),
        help="Source SQLite database path.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="New or empty export directory.",
    )

    arguments = parser.parse_args()

    export_dataset(
        database_file=arguments.database,
        output_directory=arguments.output,
    )
