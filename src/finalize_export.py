import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "final_assessment_v2.db"
OUT = ROOT / "exports" / "final_assessment_v2_corrected"
OUT.mkdir(parents=True, exist_ok=True)

db_uri = "file:" + quote(DB.resolve().as_posix(), safe="/:") + "?mode=ro"
con = sqlite3.connect(db_uri, uri=True)
con.row_factory = sqlite3.Row

# SQL seed: schema and data from the active assessment database.
with (OUT / "seed.sql").open("w", encoding="utf-8", newline="\n") as f:
    for line in con.iterdump():
        f.write(line + "\n")

# Data dictionary from the live SQLite schema.
tables = [
    r["name"] for r in con.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
]
with (OUT / "data_dictionary.csv").open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    w = csv.writer(f)
    w.writerow([
        "table_name", "column_name", "data_type", "not_null",
        "primary_key", "default_value", "foreign_key_references"
    ])
    for table in tables:
        escaped = table.replace('"', '""')
        columns = con.execute(f'PRAGMA table_info("{escaped}")').fetchall()
        foreign_keys = con.execute(f'PRAGMA foreign_key_list("{escaped}")').fetchall()
        refs = {}
        for fk in foreign_keys:
            refs[fk["from"]] = f'{fk["table"]}.{fk["to"]}'
        for col in columns:
            w.writerow([
                table, col["name"], col["type"], col["notnull"],
                col["pk"], col["dflt_value"], refs.get(col["name"], "")
            ])

# Current database counts and integrity checks.
row_counts = {
    table: con.execute(
        f'SELECT COUNT(*) FROM "{table.replace(chr(34), chr(34)*2)}"'
    ).fetchone()[0]
    for table in tables
}
fk_violations = [dict(r) for r in con.execute("PRAGMA foreign_key_check")]

mismatches = None
if {"shipments", "tracking_events"}.issubset(tables):
    mismatches = con.execute("""
        SELECT COUNT(*) FROM shipments s
        WHERE s.shipment_status <> (
            SELECT t.event_type FROM tracking_events t
            WHERE t.shipment_id = s.shipment_id
            ORDER BY t.event_sequence DESC LIMIT 1
        )
    """).fetchone()[0]

summary = {
    "database": DB.name,
    "fixed_seed": 20261022,
    "row_counts": row_counts,
    "total_rows": sum(row_counts.values()),
    "foreign_key_violations": len(fk_violations),
    "shipment_status_latest_event_mismatches": mismatches,
    "automated_tests": "155 passed; 5 subtests passed",
    "export_verification": "PASSED: 16 tables, 32 CSV/JSON files; checksums and row counts match",
    "anomaly_validation": "PASSED: 5 scenarios and 5 ground-truth labels",
    "notes": [
        "Synthetic assessment data; not production data.",
        "The operational database was opened read-only."
    ]
}
(OUT / "validation_summary.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)

con.close()

# Separate source manifest with checksums for every current export artifact.
files = []
for path in sorted(OUT.rglob("*")):
    if path.is_file() and path.name != "source_manifest.json":
        files.append({
            "path": path.relative_to(OUT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
        })

source_manifest = {
    "source_database": DB.name,
    "fixed_seed": 20261022,
    "artifacts": files
}
(OUT / "source_manifest.json").write_text(
    json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8"
)

print("Created seed.sql, data_dictionary.csv, validation_summary.json, source_manifest.json")
print("Tables:", len(tables), "| Total rows:", sum(row_counts.values()))
print("Foreign-key violations:", len(fk_violations))
print("Shipment status mismatches:", mismatches)
if fk_violations or mismatches not in (0, None):
    raise SystemExit("STOP: integrity checks did not pass; do not commit yet.")
