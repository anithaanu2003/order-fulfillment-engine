
import csv
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUTS_PATH = PROJECT_ROOT / "data" / "anomaly_cases" / "scenario_inputs.csv"
GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "anomaly_cases" / "ground_truth.csv"


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


class TestAnomalyScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.scenarios = read_csv(INPUTS_PATH)
        cls.labels = read_csv(GROUND_TRUTH_PATH)

        cls.scenarios_by_id = {
            row["case_id"]: row for row in cls.scenarios
        }
        cls.labels_by_id = {
            row["case_id"]: row for row in cls.labels
        }

    def test_scenario_and_ground_truth_ids_match(self):
        self.assertEqual(
            set(self.scenarios_by_id),
            set(self.labels_by_id),
        )

    def test_all_five_scenarios_exist(self):
        self.assertEqual(len(self.scenarios), 5)
        self.assertEqual(len(self.labels), 5)

    def test_split_shipment_quantities_sum_correctly(self):
        scenario = self.scenarios_by_id["ANOM-005"]

        shipment_1 = int(scenario["shipment_1_quantity"])
        shipment_2 = int(scenario["shipment_2_quantity"])
        shipped_total = int(scenario["shipped_quantity"])
        ordered_quantity = int(scenario["ordered_quantity"])

        self.assertEqual(shipment_1 + shipment_2, shipped_total)
        self.assertLessEqual(shipped_total, ordered_quantity)

    def test_split_shipment_rollup_is_incorrect(self):
        scenario = self.scenarios_by_id["ANOM-005"]
        label = self.labels_by_id["ANOM-005"]

        actual_total = (
            int(scenario["shipment_1_quantity"])
            + int(scenario["shipment_2_quantity"])
        )
        reported_total = int(scenario["reported_rollup_quantity"])

        self.assertNotEqual(actual_total, reported_total)
        self.assertEqual(label["expected_anomaly"].lower(), "true")
        self.assertEqual(
            label["expected_decision"],
            "FLAG_ROLLUP_MISMATCH",
        )


if __name__ == "__main__":
    unittest.main()
