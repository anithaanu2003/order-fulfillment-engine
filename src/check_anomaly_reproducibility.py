
import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = PROJECT_ROOT / "src" / "generate_anomaly_cases.py"
OUTPUT_DIR = PROJECT_ROOT / "data" / "anomaly_cases"

OUTPUT_FILES = [
    "scenario_inputs.csv",
    "ground_truth.csv",
    "anomaly_cases.json",
]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_generator():
    result = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--overwrite",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Anomaly generator failed.")

    print(result.stdout)


def snapshot_hashes():
    hashes = {}

    for filename in OUTPUT_FILES:
        path = OUTPUT_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing generated file: {path}")

        hashes[filename] = file_hash(path)

    return hashes


def main():
    print("Reproducibility check")
    print("-" * 40)

    print("\nRun 1:")
    run_generator()
    first_hashes = snapshot_hashes()

    print("\nRun 2:")
    run_generator()
    second_hashes = snapshot_hashes()

    print("\nComparing SHA-256 checksums:")

    all_match = True

    for filename in OUTPUT_FILES:
        matches = first_hashes[filename] == second_hashes[filename]
        print(f"{filename}: {'MATCH' if matches else 'MISMATCH'}")

        if not matches:
            all_match = False

    if not all_match:
        raise SystemExit("FAILED: generated files are not reproducible.")

    print("\nPASSED: both runs produced identical files.")
    print("Operational database modified: No")


if __name__ == "__main__":
    main()
