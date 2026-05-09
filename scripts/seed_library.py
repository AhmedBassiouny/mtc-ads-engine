#!/usr/bin/env python3
"""
One-time script: copies seed CSVs into data/library/ as canonical working files.
Run once from the repo root: python3 scripts/seed_library.py
"""

import csv
import pathlib
import sys

SEED_DIR = pathlib.Path("data/seed")
LIB_DIR = pathlib.Path("data/library")


def seed_master():
    src = SEED_DIR / "MTC_master_ad_library_v2.csv"
    dst = LIB_DIR / "master.csv"

    if dst.exists():
        answer = input(f"{dst} already exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Skipping master.csv")
            return 0

    with open(src, newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        base_fields = reader.fieldnames

    tag_fields = ["angle", "hook_template", "course_track"]
    out_fields = base_fields + tag_fields

    rows_written = 0
    with open(src, newline="", encoding="utf-8") as f_in, \
         open(dst, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()
        for row in reader:
            row["angle"] = ""
            row["hook_template"] = ""
            row["course_track"] = ""
            writer.writerow(row)
            rows_written += 1

    print(f"✓ master.csv: {rows_written} rows written to {dst}")
    return rows_written


def seed_performance_log():
    src = SEED_DIR / "MTC_performance_-y_month_2017_to_now.csv"
    dst = LIB_DIR / "performance_log.csv"

    if dst.exists():
        answer = input(f"{dst} already exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Skipping performance_log.csv")
            return 0

    rows_written = 0
    with open(src, newline="", encoding="utf-8") as f_in, \
         open(dst, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            writer.writerow(row)
            rows_written += 1

    print(f"✓ performance_log.csv: {rows_written} rows written to {dst}")
    return rows_written


def seed_conversations():
    dst = LIB_DIR / "conversations.csv"

    if dst.exists():
        print(f"  conversations.csv already exists — skipping")
        return

    fields = [
        "date", "ad_id", "ad_name", "angle", "course_track",
        "outcome",       # enrolled / quoted / ghosted / unknown
        "notes",
    ]
    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

    print(f"✓ conversations.csv: empty schema created at {dst}")


def main():
    if not SEED_DIR.exists():
        print(f"ERROR: seed directory not found at {SEED_DIR}")
        sys.exit(1)

    LIB_DIR.mkdir(parents=True, exist_ok=True)

    print("Seeding data/library/ from data/seed/ ...\n")

    master_rows = seed_master()
    perf_rows = seed_performance_log()
    seed_conversations()

    print(f"\nDone. Run 'python3 scripts/tag_ads.py' next to tag the master library.")
    print(f"Then verify: master.csv should have {master_rows} rows with angle/hook_template/course_track columns.")


if __name__ == "__main__":
    main()
