from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a privacy-safe structural summary of a CSV log.")
    parser.add_argument("csv_file")
    args = parser.parse_args()
    path = Path(args.csv_file)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    print(f"Rows: {len(rows)}")
    print("Columns:", ", ".join(reader.fieldnames or []))
    if rows:
        for field in reader.fieldnames or []:
            values = [row[field] for row in rows if row.get(field, "") != ""]
            print(f"{field}: {len(values)} populated values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
