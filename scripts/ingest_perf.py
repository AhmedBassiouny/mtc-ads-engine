#!/usr/bin/env python3
"""
Ingest a Meta Ads performance export CSV into data/library/.

Usage: python3 scripts/ingest_perf.py <file_path>

Handles:
  - UTF-16 LE with BOM (tab-separated) — recent Meta exports
  - UTF-8 (comma-separated) — older Meta exports and Ads Manager downloads
  Detects encoding and delimiter automatically. Silent corruption otherwise.

On success:
  - Appends new rows to data/library/performance_log.csv
  - Adds any new Ad IDs to data/library/master.csv (with empty tag columns)
  - Moves the source file to data/archive/
  - Prints: rows added, total spend processed, anomalies flagged
"""

import csv
import io
import pathlib
import shutil
import sys
from datetime import datetime

LIB = pathlib.Path("data/library")
ARCHIVE = pathlib.Path("data/archive")

PERF_LOG = LIB / "performance_log.csv"
MASTER   = LIB / "master.csv"

# Columns the performance log uses — subset of what Meta exports
PERF_COLUMNS = [
    "Ad name", "Ad ID", "Ad set name", "Ad set ID",
    "Campaign name", "Campaign ID",
    "Reporting starts", "Reporting ends",
    "Objective", "Ad delivery",
    "Amount spent (EGP)",
    "Impressions", "Reach", "Frequency",
    "Link clicks", "CTR (link click-through rate)",
    "CPM (cost per 1,000 impressions) (EGP)",
    "Messaging conversations started",
    "Cost per messaging conversation started (EGP)",
    "Quality ranking", "Engagement rate ranking", "Conversion rate ranking",
]

MASTER_TAG_COLUMNS = ["angle", "hook_template", "course_track"]


def detect_encoding_and_delimiter(path: pathlib.Path) -> tuple[str, str]:
    """Returns (encoding, delimiter). Never silently falls back."""
    raw = path.read_bytes()

    if raw[:2] == b"\xff\xfe":
        encoding = "utf-16-le"
        # Strip BOM and decode to find delimiter
        sample = raw[2:4096].decode("utf-16-le", errors="replace")
    elif raw[:2] == b"\xfe\xff":
        encoding = "utf-16-be"
        sample = raw[2:4096].decode("utf-16-be", errors="replace")
    elif raw[:3] == b"\xef\xbb\xbf":
        encoding = "utf-8-sig"
        sample = raw[3:4096].decode("utf-8", errors="replace")
    else:
        encoding = "utf-8"
        sample = raw[:4096].decode("utf-8", errors="replace")

    first_line = sample.split("\n")[0]
    delimiter = "\t" if "\t" in first_line else ","
    return encoding, delimiter


def read_csv(path: pathlib.Path, encoding: str, delimiter: str) -> tuple[list[str], list[dict]]:
    """Read CSV; return (fieldnames, rows)."""
    raw = path.read_bytes()

    # Decode properly
    if encoding in ("utf-16-le", "utf-16-be"):
        # Strip BOM if present
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
            raw = raw[2:]
        text = raw.decode(encoding, errors="replace")
    else:
        text = raw.decode(encoding.replace("-sig", ""), errors="replace")
        if text.startswith("﻿"):
            text = text[1:]

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    fieldnames = [f.strip().strip('"') for f in (reader.fieldnames or [])]

    rows = []
    for row in reader:
        cleaned = {k.strip().strip('"'): v.strip().strip('"') for k, v in row.items() if k}
        rows.append(cleaned)

    return fieldnames, rows


def normalise_row(row: dict, src_fields: list[str]) -> dict:
    """Map source field names to canonical PERF_COLUMNS, best-effort."""
    # Build a case-insensitive lookup
    lower_row = {k.lower(): v for k, v in row.items()}

    def get(*candidates):
        for c in candidates:
            v = lower_row.get(c.lower())
            if v is not None:
                return v
        return ""

    return {
        "Ad name":       get("Ad name", "ad name"),
        "Ad ID":         get("Ad ID", "ad id"),
        "Ad set name":   get("Ad set name"),
        "Ad set ID":     get("Ad set ID"),
        "Campaign name": get("Campaign name"),
        "Campaign ID":   get("Campaign ID"),
        "Reporting starts": get("Reporting starts"),
        "Reporting ends":   get("Reporting ends"),
        "Objective":     get("Objective"),
        "Ad delivery":   get("Ad delivery"),
        "Amount spent (EGP)": get("Amount spent (EGP)", "Amount spent (EGP) (EGP)", "Amount spent"),
        "Impressions":   get("Impressions"),
        "Reach":         get("Reach"),
        "Frequency":     get("Frequency"),
        "Link clicks":   get("Link clicks"),
        "CTR (link click-through rate)": get("CTR (link click-through rate)", "CTR"),
        "CPM (cost per 1,000 impressions) (EGP)": get(
            "CPM (cost per 1,000 impressions) (EGP)", "CPM (cost per 1,000 impressions)", "CPM"
        ),
        "Messaging conversations started": get("Messaging conversations started"),
        "Cost per messaging conversation started (EGP)": get(
            "Cost per messaging conversation started (EGP)",
            "Cost per messaging conversation started",
            "Cost per results",
        ),
        "Quality ranking":      get("Quality ranking"),
        "Engagement rate ranking": get("Engagement rate ranking"),
        "Conversion rate ranking": get("Conversion rate ranking"),
    }


def load_existing_perf_keys(path: pathlib.Path) -> set[tuple]:
    """Return set of (Ad ID, Reporting starts, Reporting ends) already in the log."""
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {
            (r.get("Ad ID", ""), r.get("Reporting starts", ""), r.get("Reporting ends", ""))
            for r in reader
        }


def load_existing_master_ids(path: pathlib.Path) -> set[str]:
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {r.get("Ad ID", "") for r in reader}


def append_to_perf_log(new_rows: list[dict], path: pathlib.Path) -> int:
    write_header = not path.exists()
    added = 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PERF_COLUMNS)
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)
            added += 1
    return added


def add_new_ads_to_master(new_ad_rows: list[dict], path: pathlib.Path) -> int:
    """Append ads with new IDs to master.csv with empty tag columns."""
    if not new_ad_rows:
        return 0

    # Read existing fieldnames
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

    added = 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for perf_row in new_ad_rows:
            master_row = {col: "" for col in fieldnames}
            master_row["Ad ID"] = perf_row.get("Ad ID", "")
            master_row["ad_name"] = perf_row.get("Ad name", "")
            master_row["objective"] = perf_row.get("Objective", "")
            master_row["campaign_name"] = perf_row.get("Campaign name", "")
            writer.writerow(master_row)
            added += 1

    return added


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/ingest_perf.py <file_path>")
        sys.exit(1)

    src = pathlib.Path(sys.argv[1])
    if not src.exists():
        print(f"ERROR: file not found: {src}")
        sys.exit(1)

    # Detect encoding
    encoding, delimiter = detect_encoding_and_delimiter(src)
    print(f"Detected: encoding={encoding}, delimiter={'TAB' if delimiter == chr(9) else 'COMMA'}")

    # Read source file
    src_fields, src_rows = read_csv(src, encoding, delimiter)
    print(f"Source rows: {len(src_rows)} (columns: {len(src_fields)})")

    if not src_rows:
        print("ERROR: no data rows found")
        sys.exit(1)

    # Normalise rows to canonical columns
    norm_rows = [normalise_row(r, src_fields) for r in src_rows]

    # Compute source totals for validation
    src_spend = sum(float(r.get("Amount spent (EGP)") or 0) for r in norm_rows)
    src_convos = sum(float(r.get("Messaging conversations started") or 0) for r in norm_rows)
    print(f"Source totals: spend={src_spend:.2f} EGP, conversations={src_convos:.0f}")

    # Check for duplicates
    existing_keys = load_existing_perf_keys(PERF_LOG)
    new_rows = []
    for row in norm_rows:
        key = (row.get("Ad ID", ""), row.get("Reporting starts", ""), row.get("Reporting ends", ""))
        if key not in existing_keys:
            new_rows.append(row)

    duplicate_count = len(norm_rows) - len(new_rows)
    if duplicate_count:
        print(f"Skipping {duplicate_count} duplicate rows (already in performance_log.csv)")

    if not new_rows:
        print("No new rows to add — all data already in performance_log.csv")
        sys.exit(0)

    # Append to performance log
    LIB.mkdir(parents=True, exist_ok=True)
    rows_added = append_to_perf_log(new_rows, PERF_LOG)
    print(f"✓ Added {rows_added} rows to data/library/performance_log.csv")

    # Add new Ad IDs to master.csv
    existing_master_ids = load_existing_master_ids(MASTER)
    novel_ads = [r for r in new_rows if r.get("Ad ID") and r["Ad ID"] not in existing_master_ids]
    # Deduplicate by Ad ID
    seen_ids: set[str] = set()
    unique_novel = []
    for r in novel_ads:
        if r["Ad ID"] not in seen_ids:
            unique_novel.append(r)
            seen_ids.add(r["Ad ID"])

    if unique_novel and MASTER.exists():
        new_master_count = add_new_ads_to_master(unique_novel, MASTER)
        print(f"✓ Added {new_master_count} new ad IDs to data/library/master.csv (untagged — run tag_ads.py)")
    elif unique_novel:
        print(f"⚠  master.csv not found — run seed_library.py first. {len(unique_novel)} new ads not added.")

    # Anomaly checks
    new_spend = sum(float(r.get("Amount spent (EGP)") or 0) for r in new_rows)
    new_convos = sum(float(r.get("Messaging conversations started") or 0) for r in new_rows)
    print(f"\nNew data: {rows_added} rows | {new_spend:.2f} EGP spend | {new_convos:.0f} conversations")

    if new_convos > 0:
        cpr = new_spend / new_convos
        print(f"Blended CPR (this import): {cpr:.2f} EGP/conversation")
        if cpr > 30:
            print(f"⚠  Blended CPR {cpr:.2f} EGP exceeds kill threshold of 30 EGP — run /status")

    # Archive the source file
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE / f"{timestamp}_{src.name}"
    shutil.move(str(src), str(archive_path))
    print(f"✓ Archived source file to {archive_path}")
    print(f"\nRun /status to see updated recommendations.")


if __name__ == "__main__":
    main()
