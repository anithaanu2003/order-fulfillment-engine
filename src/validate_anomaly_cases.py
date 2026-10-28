
import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "anomaly_cases"
DATABASE_PATH = PROJECT_ROOT / "data" / "fulfillment.db"

EXPECTED_DECISIONS = {
    "PROMISE_BEFORE_ORDER": "REJECT_PROMISE",
    "ALLOCATION_EXCEEDS_INVENTORY": "REJECT_ALLOCATION",
    "CARRIER_UNSUPPORTED_FOR_ZONE": "REJECT_CARRIER",
    "DELIVERED_BEFORE_DISPATCH": "FLAG_INVALID_LIFECYCLE",
    "SPLIT_SHIPMENT_ROLLUP_INCORRECT": "FLAG_ROLLUP_MISMATCH",
}


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def validate():
    input_path = DATA_DIR / "scenario_inputs.csv"
    truth_path = DATA_DIR / "ground_truth.csv"

    if not input_path.exists() or not truth_path.exists():
        raise FileNotFoundError(
            "Scenario input or ground-truth CSV is missing."
        )

    scenarios = read_csv(input_path)
    labels = read_csv(truth_path)
    errors = []

    scenario_ids = [row["case_id"] for row in scenarios]
    label_ids = [row["case_id"] for row in labels]

    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("Duplicate case IDs found in scenario inputs.")

    if len(label_ids) != len(set(label_ids)):
        errors.append("Duplicate case IDs found in ground truth.")

    if set(scenario_ids) != set(label_ids):
        errors.append("Scenario IDs and ground-truth IDs do not match.")

    labels_by_id = {row["case_id"]: row for row in labels}

    if len(scenarios) != 5:
        errors.append(f"Expected 5 scenarios; found {len(scenarios)}.")

    if len(labels) != 5:
        errors.append(f"Expected 5 labels; found {len(labels)}.")

    connection = sqlite3.connect(
        DATABASE_PATH.as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        for row in scenarios:
            case_id = row["case_id"]
            anomaly_type = row["anomaly_type"]
            label = labels_by_id.get(case_id)

            if label is None:
                continue

            if label["expected_anomaly"].lower() != "true":
                errors.append(
                    f"{case_id}: expected_anomaly should be true."
                )

            expected_decision = EXPECTED_DECISIONS.get(anomaly_type)

            if label["expected_decision"] != expected_decision:
                errors.append(
                    f"{case_id}: expected decision does not match "
                    f"anomaly type {anomaly_type}."
                )

            try:
                if anomaly_type == "PROMISE_BEFORE_ORDER":
                    order_time = row["order_timestamp"]
                    promise_start = row["promised_delivery_start"]

                    if not promise_start or promise_start >= order_time:
                        errors.append(
                            f"{case_id}: promise does not start "
                            "before the order."
                        )

                elif anomaly_type == "ALLOCATION_EXCEEDS_INVENTORY":
                    allocated = int(row["allocated_quantity"])
                    available = int(row["available_quantity"])

                    if allocated <= available:
                        errors.append(
                            f"{case_id}: allocation does not "
                            "exceed inventory."
                        )

                elif anomaly_type == "CARRIER_UNSUPPORTED_FOR_ZONE":
                    carrier_id = row["carrier_id"]
                    service_id = row["service_level_id"]
                    destination_zone = row["destination_zone"]
                    supported_zone = row["supported_zone"]

                    actual_support = connection.execute(
                        """
                        SELECT 1
                        FROM carrier_service_zones
                        WHERE carrier_id = ?
                          AND service_level_id = ?
                          AND service_zone = ?
                          AND is_active = 1
                        """,
                        (carrier_id, service_id, destination_zone),
                    ).fetchone()

                    declared_support = connection.execute(
                        """
                        SELECT 1
                        FROM carrier_service_zones
                        WHERE carrier_id = ?
                          AND service_level_id = ?
                          AND service_zone = ?
                          AND is_active = 1
                        """,
                        (carrier_id, service_id, supported_zone),
                    ).fetchone()

                    if actual_support:
                        errors.append(
                            f"{case_id}: destination zone is "
                            "actually supported."
                        )

                    if not declared_support:
                        errors.append(
                            f"{case_id}: reference supported zone "
                            "is not supported."
                        )

                elif anomaly_type == "DELIVERED_BEFORE_DISPATCH":
                    dispatch_time = row["dispatched_at"]
                    delivered_time = row["delivered_at"]

                    if not dispatch_time or not delivered_time:
                        errors.append(
                            f"{case_id}: dispatch or delivery "
                            "timestamp is missing."
                        )
                    elif delivered_time >= dispatch_time:
                        errors.append(
                            f"{case_id}: delivery is not before dispatch."
                        )

                elif anomaly_type == "SPLIT_SHIPMENT_ROLLUP_INCORRECT":
                    ordered = int(row["ordered_quantity"])
                    shipment_1 = int(row["shipment_1_quantity"])
                    shipment_2 = int(row["shipment_2_quantity"])
                    shipped = int(row["shipped_quantity"])
                    reported = int(row["reported_rollup_quantity"])

                    calculated_total = shipment_1 + shipment_2

                    if shipment_1 <= 0 or shipment_2 <= 0:
                        errors.append(
                            f"{case_id}: each shipment must have "
                            "a positive quantity."
                        )

                    if calculated_total != shipped:
                        errors.append(
                            f"{case_id}: shipped quantity does not "
                            "match the sum of individual shipments."
                        )

                    if calculated_total > ordered:
                        errors.append(
                            f"{case_id}: total shipped quantity "
                            "exceeds ordered quantity."
                        )

                    if reported == calculated_total:
                        errors.append(
                            f"{case_id}: reported rollup matches "
                            "the calculated shipment total."
                        )

                else:
                    errors.append(
                        f"{case_id}: unknown anomaly type {anomaly_type}."
                    )

            except (ValueError, TypeError, KeyError) as error:
                errors.append(
                    f"{case_id}: invalid or missing field value: {error}"
                )

    finally:
        connection.close()

    print("Anomaly scenario validation")
    print("-" * 40)
    print(f"Input scenarios: {len(scenarios)}")
    print(f"Ground-truth labels: {len(labels)}")
    print("Operational database opened read-only.")

    if errors:
        print(f"\nValidation FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Validation PASSED: all five anomaly scenarios are valid.")
    print("Scenario IDs and ground-truth labels match.")


if __name__ == "__main__":
    validate()
