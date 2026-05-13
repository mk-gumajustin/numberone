"""
json_device_summary.py

Reads a JSON file of device records, normalises manufacturer names,
and produces three summaries:
  1. By Manufacturer (count + Profile Status breakdown)
  2. By Profile Status (count + Manufacturer breakdown)
  3. By Userless Enrollment Status (count + Manufacturer breakdown)

Outputs:
  - json_devices_summary.json  (machine-readable)
  - json_devices_summary.txt   (human-readable)
  - Brief table printed to the terminal
"""

import json
from collections import defaultdict
from pathlib import Path

# --- File locations -------------------------------------------------------
# Input + output all live in the user's Downloads folder for convenience.
DOWNLOADS = Path(r"C:\Users\JustinGuma\Downloads")
INPUT_FILE = DOWNLOADS / "json_devices.json"
OUTPUT_JSON = DOWNLOADS / "json_devices_summary.json"
OUTPUT_TXT = DOWNLOADS / "json_devices_summary.txt"


# --- Manufacturer normalisation ------------------------------------------
# Map source manufacturer strings to their canonical form. Anything not in
# this map is kept as-is (after stripping whitespace).
MANUFACTURER_ALIASES = {
    "HP": "HP",
    "Hewlett-Packard": "HP",
    "LENOVO": "Lenovo",
    "Lenovo": "Lenovo",
}


def normalise_manufacturer(raw: str) -> str:
    """Return the canonical manufacturer name for a raw input string."""
    # Defensive: handle None and stray whitespace.
    if not raw:
        return "Unknown"
    name = raw.strip()
    return MANUFACTURER_ALIASES.get(name, name)


# --- Loading --------------------------------------------------------------
def load_devices(path: Path) -> list[dict]:
    """Load the device list from the JSON file."""
    # utf-8-sig transparently strips a UTF-8 BOM if present (PowerShell
    # exports often include one).
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


# --- Summary builders -----------------------------------------------------
def summarise_by_manufacturer(devices: list[dict]) -> dict:
    """
    Group devices by (normalised) manufacturer.
    For each manufacturer, return total count and a Profile Status breakdown.
    """
    # defaultdict-of-defaultdicts keeps the counting code short.
    by_mfr = defaultdict(lambda: {"total": 0, "profile_status": defaultdict(int)})

    for device in devices:
        mfr = normalise_manufacturer(device.get("Manufacturer", ""))
        status = device.get("Profile status", "Unknown") or "Unknown"

        by_mfr[mfr]["total"] += 1
        by_mfr[mfr]["profile_status"][status] += 1

    # Convert inner defaultdicts to plain dicts so JSON serialisation works,
    # and sort manufacturers by descending count for readability.
    result = {}
    for mfr, data in sorted(by_mfr.items(), key=lambda kv: -kv[1]["total"]):
        result[mfr] = {
            "total": data["total"],
            "profile_status": dict(sorted(data["profile_status"].items())),
        }
    return result


def summarise_by_profile_status(devices: list[dict]) -> dict:
    """
    Group devices by Profile Status.
    For each status, return total count and which manufacturers contribute.
    """
    by_status = defaultdict(lambda: {"total": 0, "manufacturers": defaultdict(int)})

    for device in devices:
        status = device.get("Profile status", "Unknown") or "Unknown"
        mfr = normalise_manufacturer(device.get("Manufacturer", ""))

        by_status[status]["total"] += 1
        by_status[status]["manufacturers"][mfr] += 1

    result = {}
    for status, data in sorted(by_status.items(), key=lambda kv: -kv[1]["total"]):
        result[status] = {
            "total": data["total"],
            # Sort manufacturer breakdown by count descending.
            "manufacturers": dict(
                sorted(data["manufacturers"].items(), key=lambda kv: -kv[1])
            ),
        }
    return result


def summarise_by_userless_status(devices: list[dict]) -> dict:
    """
    Group devices by Userless Enrollment Status.
    For each status, break the count down by manufacturer.
    """
    by_userless = defaultdict(lambda: {"total": 0, "manufacturers": defaultdict(int)})

    for device in devices:
        ustatus = device.get("Userless Enrollment Status", "Unknown") or "Unknown"
        mfr = normalise_manufacturer(device.get("Manufacturer", ""))

        by_userless[ustatus]["total"] += 1
        by_userless[ustatus]["manufacturers"][mfr] += 1

    result = {}
    for ustatus, data in sorted(by_userless.items(), key=lambda kv: -kv[1]["total"]):
        result[ustatus] = {
            "total": data["total"],
            "manufacturers": dict(
                sorted(data["manufacturers"].items(), key=lambda kv: -kv[1])
            ),
        }
    return result


# --- Output formatters ----------------------------------------------------
def render_text_report(summary: dict, total_devices: int) -> str:
    """Build a human-readable text report from the summary dictionaries."""
    lines = []
    lines.append("=" * 72)
    lines.append("DEVICE SUMMARY REPORT")
    lines.append("=" * 72)
    lines.append(f"Total devices: {total_devices}")
    lines.append("")

    # --- Section 1: by manufacturer ---
    lines.append("-" * 72)
    lines.append("1. BY MANUFACTURER (with Profile Status breakdown)")
    lines.append("-" * 72)
    for mfr, data in summary["by_manufacturer"].items():
        lines.append(f"{mfr}: {data['total']}")
        for status, count in data["profile_status"].items():
            lines.append(f"    - {status}: {count}")
        lines.append("")

    # --- Section 2: by profile status ---
    lines.append("-" * 72)
    lines.append("2. BY PROFILE STATUS (with Manufacturer breakdown)")
    lines.append("-" * 72)
    for status, data in summary["by_profile_status"].items():
        lines.append(f"{status}: {data['total']}")
        for mfr, count in data["manufacturers"].items():
            lines.append(f"    - {mfr}: {count}")
        lines.append("")

    # --- Section 3: by userless enrollment status ---
    lines.append("-" * 72)
    lines.append("3. BY USERLESS ENROLLMENT STATUS (with Manufacturer breakdown)")
    lines.append("-" * 72)
    for ustatus, data in summary["by_userless_enrollment_status"].items():
        lines.append(f"{ustatus}: {data['total']}")
        for mfr, count in data["manufacturers"].items():
            lines.append(f"    - {mfr}: {count}")
        lines.append("")

    return "\n".join(lines)


def print_terminal_summary(summary: dict, total_devices: int) -> None:
    """Print a brief, easy-to-scan summary table to stdout."""
    print()
    print("=" * 60)
    print(f"  DEVICE SUMMARY  -  {total_devices} total devices")
    print("=" * 60)

    # Manufacturer totals
    print("\nManufacturer                          Count")
    print("-" * 60)
    for mfr, data in summary["by_manufacturer"].items():
        print(f"  {mfr:<36} {data['total']:>6}")

    # Profile status totals
    print("\nProfile Status                        Count")
    print("-" * 60)
    for status, data in summary["by_profile_status"].items():
        print(f"  {status:<36} {data['total']:>6}")

    # Userless enrollment totals
    print("\nUserless Enrollment Status            Count")
    print("-" * 60)
    for ustatus, data in summary["by_userless_enrollment_status"].items():
        print(f"  {ustatus:<36} {data['total']:>6}")

    print()


# --- Main -----------------------------------------------------------------
def main() -> None:
    # 1. Read input.
    devices = load_devices(INPUT_FILE)
    total = len(devices)

    # 2. Build the three summaries.
    summary = {
        "total_devices": total,
        "by_manufacturer": summarise_by_manufacturer(devices),
        "by_profile_status": summarise_by_profile_status(devices),
        "by_userless_enrollment_status": summarise_by_userless_status(devices),
    }

    # 3. Write machine-readable JSON output.
    with OUTPUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    # 4. Write human-readable text output.
    with OUTPUT_TXT.open("w", encoding="utf-8") as fh:
        fh.write(render_text_report(summary, total))

    # 5. Print a brief table to the terminal.
    print_terminal_summary(summary, total)
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_TXT}")


if __name__ == "__main__":
    main()
