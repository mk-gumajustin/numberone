import csv
from collections import defaultdict
from pathlib import Path

# Resolve paths relative to this script's location
FOLDER = Path(__file__).parent
INPUT_FILE = FOLDER / "devices.csv"
OUTPUT_FILE = FOLDER / "devices_summary.csv"

# Each key is (Manufacturer, Model); value tracks count and unique group tags
summary = defaultdict(lambda: {
    "count": 0,
    "group_tags": set(),
    "profile_statuses": set(),
})

# Read and aggregate the source data
with open(INPUT_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        manufacturer = row["Manufacturer"].strip()
        model = row["Model"].strip()
        key = (manufacturer, model)

        entry = summary[key]
        entry["count"] += 1

        # Collect distinct group tags and profile statuses across the group
        group_tag = row.get("Group tag", "").strip()
        if group_tag:
            entry["group_tags"].add(group_tag)

        status = row.get("Profile Status", "").strip()
        if status:
            entry["profile_statuses"].add(status)

# Write the aggregated results, sorted by Manufacturer then Model
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Manufacturer",
        "Model",
        "Device Count",
        "Group Tags",
        "Profile Statuses",
    ])

    for (manufacturer, model), data in sorted(summary.items()):
        writer.writerow([
            manufacturer,
            model,
            data["count"],
            # Join sets into a readable semicolon-separated string
            "; ".join(sorted(data["group_tags"])),
            "; ".join(sorted(data["profile_statuses"])),
        ])

print(f"Summary written to: {OUTPUT_FILE}")
print(f"Total groups: {len(summary)}")
print(f"Total devices: {sum(v['count'] for v in summary.values())}")
