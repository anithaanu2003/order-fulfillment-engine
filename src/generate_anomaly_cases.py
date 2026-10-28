
import argparse
import csv
import json
from pathlib import Path

SEED = 20261022

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "anomaly_cases"

# Synthetic input scenarios.
# These are examples, not records inserted into the operational database.
SCENARIOS = [
    {
        "case_id": "ANOM-001",
        "anomaly_type": "PROMISE_BEFORE_ORDER",
        "order_timestamp": "2026-10-22T10:00:00",
        "promise_created_at": "2026-10-22T10:05:00",
        "promised_delivery_start": "2026-10-21T00:00:00",
        "promised_delivery_end": "2026-10-23T23:59:59",
        "allocated_quantity": "",
        "available_quantity": "",
        "carrier_id": "",
        "service_level_id": "",
        "destination_zone": "",
        "supported_zone": "",
        "created_at": "",
        "dispatched_at": "",
        "delivered_at": "",
        "ordered_quantity": "",
        "shipment_1_quantity": "",
        "shipment_2_quantity": "",
        "shipped_quantity": "",
        "reported_rollup_quantity": "",
    },
    {
        "case_id": "ANOM-002",
        "anomaly_type": "ALLOCATION_EXCEEDS_INVENTORY",
        "order_timestamp": "2026-10-22T10:00:00",
        "promise_created_at": "",
        "promised_delivery_start": "",
        "promised_delivery_end": "",
        "allocated_quantity": 8,
        "available_quantity": 5,
        "carrier_id": "",
        "service_level_id": "",
        "destination_zone": "",
        "supported_zone": "",
        "created_at": "",
        "dispatched_at": "",
        "delivered_at": "",
        "ordered_quantity": 8,
        "shipment_1_quantity": "",
        "shipment_2_quantity": "",
        "shipped_quantity": 8,
        "reported_rollup_quantity": "",
    },
    {
        "case_id": "ANOM-003",
        "anomaly_type": "CARRIER_UNSUPPORTED_FOR_ZONE",
        "order_timestamp": "2026-10-22T10:00:00",
        "promise_created_at": "",
        "promised_delivery_start": "",
        "promised_delivery_end": "",
        "allocated_quantity": "",
        "available_quantity": "",
        "carrier_id": "CAR-000001",
        "service_level_id": "SVC-000001",
        "destination_zone": "CENTRAL",
        "supported_zone": "NORTH",
        "created_at": "",
        "dispatched_at": "",
        "delivered_at": "",
        "ordered_quantity": "",
        "shipment_1_quantity": "",
        "shipment_2_quantity": "",
        "shipped_quantity": "",
        "reported_rollup_quantity": "",
    },
    {
        "case_id": "ANOM-004",
        "anomaly_type": "DELIVERED_BEFORE_DISPATCH",
        "order_timestamp": "2026-10-22T10:00:00",
        "promise_created_at": "",
        "promised_delivery_start": "",
        "promised_delivery_end": "",
        "allocated_quantity": "",
        "available_quantity": "",
        "carrier_id": "",
        "service_level_id": "",
        "destination_zone": "",
        "supported_zone": "",
        "created_at": "2026-10-22T11:00:00",
        "dispatched_at": "2026-10-23T09:00:00",
        "delivered_at": "2026-10-22T18:00:00",
        "ordered_quantity": "",
        "shipment_1_quantity": "",
        "shipment_2_quantity": "",
        "shipped_quantity": "",
        "reported_rollup_quantity": "",
    },
    {
        "case_id": "ANOM-005",
        "anomaly_type": "SPLIT_SHIPMENT_ROLLUP_INCORRECT",
        "order_timestamp": "2026-10-22T10:00:00",
        "promise_created_at": "",
        "promised_delivery_start": "",
        "promised_delivery_end": "",
        "allocated_quantity": "",
        "available_quantity": "",
        "carrier_id": "",
        "service_level_id": "",
        "destination_zone": "",
        "supported_zone": "",
        "created_at": "",
        "dispatched_at": "",
        "delivered_at": "",
        "ordered_quantity": 10,
        "shipment_1_quantity": 6,
        "shipment_2_quantity": 4,
        "shipped_quantity": 10,
        "reported_rollup_quantity": 12,
    },
]

# Ground-truth labels are kept separate from scenario input features.
GROUND_TRUTH = [
    {
        "case_id": "ANOM-001",
        "expected_anomaly": True,
        "expected_decision": "REJECT_PROMISE",
        "reason": "Promised delivery starts before the order was placed.",
    },
    {
        "case_id": "ANOM-002",
        "expected_anomaly": True,
        "expected_decision": "REJECT_ALLOCATION",
        "reason": "Allocated quantity exceeds available inventory.",
    },
    {
        "case_id": "ANOM-003",
        "expected_anomaly": True,
        "expected_decision": "REJECT_CARRIER",
        "reason": (
            "The selected carrier and service level do not support "
            "the destination zone."
        ),
    },
    {
        "case_id": "ANOM-004",
        "expected_anomaly": True,
        "expected_decision": "FLAG_INVALID_LIFECYCLE",
        "reason": "The delivery timestamp occurs before dispatch.",
    },
    {
        "case_id": "ANOM-005",
        "expected_anomaly": True,
        "expected_decision": "FLAG_ROLLUP_MISMATCH",
        "ordered_quantity": 10,
        "shipments": [
            {
                "shipment_id": "SHP-ANOM-005-01",
                "shipped_quantity": 6,
            },
            {
                "shipment_id": "SHP-ANOM-005-02",
                "shipped_quantity": 4,
            },
        ],
        "actual_shipped_total": 10,
        "reported_shipped_rollup": 12,
        "reason": (
            "The reported shipment rollup is 12, but the sum of "
            "the two shipment quantities is 10."
        ),
    },
]


def write_csv(path, rows):
    """Write rows to CSV using the union of their field names."""
    if not rows:
        return

    fieldnames = list(
        dict.fromkeys(
            field
            for row in rows
            for field in row.keys()
        )
    )

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Generate isolated synthetic anomaly scenarios."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing generated files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Output directory. Defaults to data/anomaly_cases. "
            "Use a temporary directory for isolated tests."
        ),
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = output_dir / "scenario_inputs.csv"
    truth_path = output_dir / "ground_truth.csv"
    json_path = output_dir / "anomaly_cases.json"

    output_files = (input_path, truth_path, json_path)
    existing_files = [path for path in output_files if path.exists()]

    if existing_files and not args.overwrite:
        names = ", ".join(path.name for path in existing_files)
        raise FileExistsError(
            f"Output files already exist: {names}. "
            "Choose a different --output-dir or use --overwrite "
            "if replacing those files is intentional."
        )

    write_csv(input_path, SCENARIOS)
    write_csv(truth_path, GROUND_TRUTH)

    payload = {
        "seed": SEED,
        "database_modified": False,
        "description": (
            "Isolated synthetic anomaly examples. "
            "These scenarios are not inserted into the operational database."
        ),
        "scenario_inputs": SCENARIOS,
        "ground_truth": GROUND_TRUTH,
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")

    print(f"Seed: {SEED}")
    print(f"Scenario inputs: {len(SCENARIOS)}")
    print(f"Ground-truth labels: {len(GROUND_TRUTH)}")
    print(f"Output directory: {output_dir}")
    print("Operational database modified: No")
    print("Created:")
    for path in output_files:
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
