
import csv
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPORT = PROJECT_ROOT / "exports" / "current_snapshot"


def calculate_sha256(file_path):
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def count_csv_rows(file_path):
    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return sum(1 for _ in csv.DictReader(file))


def count_json_rows(file_path):
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON list in {file_path.name}"
        )

    return len(data)


def verify_export(export_directory):
    export_directory = Path(export_directory).resolve()
    manifest_path = export_directory / "manifest.json"

    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Manifest not found: {manifest_path}"
        )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    checked_files = 0
    failed_checks = []
    total_rows = 0

    for table_name, details in manifest["tables"].items():
        expected_rows = details["rows"]
        total_rows += expected_rows

        for format_name in ("csv", "json"):
            file_info = details[format_name]
            file_path = export_directory / file_info["file"]

            if not file_path.is_file():
                failed_checks.append(
                    f"Missing file: {file_info['file']}"
                )
                continue

            checked_files += 1

            actual_hash = calculate_sha256(file_path)
            if actual_hash != file_info["sha256"]:
                failed_checks.append(
                    f"Checksum mismatch: {file_info['file']}"
                )
                continue

            try:
                actual_rows = (
                    count_csv_rows(file_path)
                    if format_name == "csv"
                    else count_json_rows(file_path)
                )
            except (OSError, ValueError, json.JSONDecodeError) as error:
                failed_checks.append(
                    f"Cannot count rows in {file_info['file']}: {error}"
                )
                continue

            if actual_rows != expected_rows:
                failed_checks.append(
                    f"Row count mismatch in {file_info['file']}: "
                    f"expected {expected_rows}, got {actual_rows}"
                )

    print(f"Export directory: {export_directory}")
    print(f"Tables checked: {len(manifest['tables'])}")
    print(f"Files checked: {checked_files}")
    print(f"Rows recorded in manifest: {total_rows}")

    if failed_checks:
        print("\nVerification FAILED:")
        for failure in failed_checks:
            print(f"- {failure}")
        return False

    print(
        "\nVerification PASSED: all file checksums "
        "and row counts match."
    )
    return True


if __name__ == "__main__":
    export_directory = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else DEFAULT_EXPORT
    )

    try:
        success = verify_export(export_directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Verification error: {error}")
        sys.exit(1)

    sys.exit(0 if success else 1)
