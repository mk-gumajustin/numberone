"""
Summarize devices.csv from the Downloads folder.

Reads the device inventory, drops the always-empty 'Purchase Order' and
'Group tag' columns, and produces two summaries:
  1. Devices grouped by Manufacturer, with a breakdown of Profile Status.
  2. Devices grouped by Profile Status, with a breakdown by Manufacturer.

Both summaries are written to a single output file (devices_grouped.csv)
and a brief overview is printed to the terminal.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path


# --- Configuration ---------------------------------------------------------
# Source CSV lives in the user's Downloads folder. Using Path.home() keeps
# the script portable across machines/users.
INPUT_PATH = Path.home() / "Downloads" / "devices.csv"

# Output is written next to this script for easy retrieval.
OUTPUT_PATH = Path(__file__).resolve().parent / "devices_grouped.csv"

# Columns that the source CSV always leaves blank — exclude from all output.
# Matched case-insensitively because the file headers vary in casing
# (e.g. "Profile status" vs "Profile Status", "Purchase order" vs "Purchase Order").
COLUMNS_TO_EXCLUDE = {"purchase order", "group tag"}

# Canonical names we expect for the two columns we group on. Looked up
# case-insensitively against the actual headers in the CSV.
MANUFACTURER_COL = "manufacturer"
PROFILE_STATUS_COL = "profile status"


def load_devices(path: Path) -> list[dict]:
    """Read the CSV into a list of dict rows, skipping excluded columns."""
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Strip whitespace from values and drop the excluded columns.
            # Keys are lowercased so downstream lookups don't depend on the
            # exact header casing used in the file.
            cleaned = {
                key.strip().lower(): (value or "").strip()
                for key, value in row.items()
                if key and key.strip().lower() not in COLUMNS_TO_EXCLUDE
            }
            rows.append(cleaned)
    return rows


def summarize_by_manufacturer(rows: list[dict]) -> dict:
    """
    Group rows by Manufacturer.

    Returns a mapping of:
        manufacturer -> {
            "total": int,
            "by_status": { profile_status: count, ... }
        }
    """
    summary: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "by_status": defaultdict(int)}
    )
    for row in rows:
        manufacturer = row.get(MANUFACTURER_COL, "") or "(Unknown)"
        status = row.get(PROFILE_STATUS_COL, "") or "(Unknown)"
        summary[manufacturer]["total"] += 1
        summary[manufacturer]["by_status"][status] += 1
    return summary


def summarize_by_status(rows: list[dict]) -> dict:
    """
    Group rows by Profile Status.

    Returns a mapping of:
        profile_status -> {
            "total": int,
            "by_manufacturer": { manufacturer: count, ... }
        }
    """
    summary: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "by_manufacturer": defaultdict(int)}
    )
    for row in rows:
        manufacturer = row.get(MANUFACTURER_COL, "") or "(Unknown)"
        status = row.get(PROFILE_STATUS_COL, "") or "(Unknown)"
        summary[status]["total"] += 1
        summary[status]["by_manufacturer"][manufacturer] += 1
    return summary


def write_combined_csv(
    output_path: Path,
    by_manufacturer: dict,
    by_status: dict,
) -> None:
    """
    Write both summaries to a single CSV file.

    The file contains two sections separated by a blank line; each section
    has its own header so it can be read in a spreadsheet without confusion.
    """
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)

        # --- Section 1: grouped by Manufacturer --------------------------
        writer.writerow(["Summary by Manufacturer"])
        writer.writerow(["Manufacturer", "Profile Status", "Count", "Manufacturer Total"])
        # Sort manufacturers by total count (descending) for readability.
        for manufacturer, data in sorted(
            by_manufacturer.items(), key=lambda kv: kv[1]["total"], reverse=True
        ):
            # Sort status rows by count within each manufacturer.
            for status, count in sorted(
                data["by_status"].items(), key=lambda kv: kv[1], reverse=True
            ):
                writer.writerow([manufacturer, status, count, data["total"]])

        # Blank line separates the two sections visually.
        writer.writerow([])

        # --- Section 2: grouped by Profile Status ------------------------
        writer.writerow(["Summary by Profile Status"])
        writer.writerow(["Profile Status", "Manufacturer", "Count", "Status Total"])
        for status, data in sorted(
            by_status.items(), key=lambda kv: kv[1]["total"], reverse=True
        ):
            for manufacturer, count in sorted(
                data["by_manufacturer"].items(), key=lambda kv: kv[1], reverse=True
            ):
                writer.writerow([status, manufacturer, count, data["total"]])


def print_terminal_summary(
    total_devices: int,
    by_manufacturer: dict,
    by_status: dict,
    output_path: Path,
) -> None:
    """Print a short human-readable overview to the terminal."""
    print(f"Loaded {total_devices} devices from {INPUT_PATH}")
    print()

    print("Devices per Manufacturer:")
    for manufacturer, data in sorted(
        by_manufacturer.items(), key=lambda kv: kv[1]["total"], reverse=True
    ):
        print(f"  {manufacturer:<25} {data['total']}")
    print()

    print("Devices per Profile Status:")
    for status, data in sorted(
        by_status.items(), key=lambda kv: kv[1]["total"], reverse=True
    ):
        affected = len(data["by_manufacturer"])
        print(f"  {status:<25} {data['total']} (across {affected} manufacturer/s)")
    print()

    print(f"Full breakdown written to: {output_path}")


def main() -> None:
    # 1. Read the CSV (dropping the two excluded columns as we go).
    if not INPUT_PATH.exists():
        raise SystemExit(f"Input file not found: {INPUT_PATH}")
    rows = load_devices(INPUT_PATH)

    # 2. Build the two summaries.
    by_manufacturer = summarize_by_manufacturer(rows)
    by_status = summarize_by_status(rows)

    # 3. Persist the combined output and 4. print a quick recap.
    write_combined_csv(OUTPUT_PATH, by_manufacturer, by_status)
    print_terminal_summary(len(rows), by_manufacturer, by_status, OUTPUT_PATH)


if __name__ == "__main__":
    main()
