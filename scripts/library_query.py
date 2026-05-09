#!/usr/bin/env python3
"""
Library query helper — joins master.csv + performance_log.csv + conversations.csv.

Used by /status to build a unified view of ad performance for the triage analyst.

Usage (as a module):
    from scripts.library_query import load_library
    data = load_library(days=7)

Usage (CLI — prints JSON summary to stdout):
    python3 scripts/library_query.py [--days 7]
"""

import argparse
import csv
import json
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timedelta

LIB = pathlib.Path("data/library")


def read_csv_safe(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_date(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def load_library(days: int = 7) -> dict:
    """
    Returns a dict with:
      - master: list of all ad rows from master.csv
      - recent_perf: list of performance rows within the last `days` days
      - active_ads: dict of ad_id → aggregated metrics for the last `days` days
      - conversations: list of conversation rows
      - summary: high-level numbers for the status report header
      - untagged_count: number of master rows missing angle or course_track
    """
    master_rows = read_csv_safe(LIB / "master.csv")
    perf_rows   = read_csv_safe(LIB / "performance_log.csv")
    conv_rows   = read_csv_safe(LIB / "conversations.csv")

    cutoff = datetime.now() - timedelta(days=days)

    # Filter performance rows to the window
    recent_perf = []
    for row in perf_rows:
        end_date = parse_date(row.get("Reporting ends", ""))
        if end_date and end_date >= cutoff:
            recent_perf.append(row)

    # Aggregate metrics per ad_id over the window
    active_ads: dict[str, dict] = defaultdict(lambda: {
        "ad_id": "",
        "ad_name": "",
        "angle": "",
        "course_track": "",
        "hook_template": "",
        "total_spend_egp": 0.0,
        "total_convos": 0.0,
        "total_impressions": 0.0,
        "cpr_egp": 0.0,
        "ctr": 0.0,
        "days_in_window": 0,
        "first_seen": None,
        "last_seen": None,
    })

    for row in recent_perf:
        ad_id = row.get("Ad ID", "")
        if not ad_id:
            continue

        spend  = float(row.get("Amount spent (EGP)") or 0)
        convos = float(row.get("Messaging conversations started") or 0)
        imps   = float(row.get("Impressions") or 0)

        agg = active_ads[ad_id]
        agg["ad_id"]            = ad_id
        agg["ad_name"]          = row.get("Ad name", agg["ad_name"])
        agg["total_spend_egp"]  += spend
        agg["total_convos"]     += convos
        agg["total_impressions"]+= imps
        agg["days_in_window"]   += 1

        end_date = parse_date(row.get("Reporting ends", ""))
        if end_date:
            if agg["last_seen"] is None or end_date > agg["last_seen"]:
                agg["last_seen"] = end_date
            if agg["first_seen"] is None or end_date < agg["first_seen"]:
                agg["first_seen"] = end_date

    # Enrich with master.csv data (tags)
    master_by_id = {r.get("Ad ID", ""): r for r in master_rows}
    for ad_id, agg in active_ads.items():
        master_row = master_by_id.get(ad_id, {})
        agg["angle"]        = master_row.get("angle", "")
        agg["course_track"] = master_row.get("course_track", "")
        agg["hook_template"]= master_row.get("hook_template", "")

        # Compute CPR
        if agg["total_convos"] > 0:
            agg["cpr_egp"] = round(agg["total_spend_egp"] / agg["total_convos"], 2)

        # Compute CTR
        if agg["total_impressions"] > 0:
            agg["ctr"] = round(agg["total_convos"] / agg["total_impressions"] * 100, 4)

        # Days live (approximate from first→last seen)
        if agg["first_seen"] and agg["last_seen"]:
            agg["days_live"] = (agg["last_seen"] - agg["first_seen"]).days + 1
        else:
            agg["days_live"] = agg["days_in_window"]

        # Serialise dates
        agg["first_seen"] = agg["first_seen"].strftime("%Y-%m-%d") if agg["first_seen"] else ""
        agg["last_seen"]  = agg["last_seen"].strftime("%Y-%m-%d")  if agg["last_seen"]  else ""

    # Portfolio summary
    total_spend  = sum(a["total_spend_egp"] for a in active_ads.values())
    total_convos = sum(a["total_convos"]     for a in active_ads.values())
    blended_cpr  = round(total_spend / total_convos, 2) if total_convos > 0 else 0

    # Untagged count
    untagged = sum(
        1 for r in master_rows
        if (not r.get("angle") or not r.get("course_track"))
        and float(r.get("spend") or 0) > 0
    )

    # Recent conversations (last 14 days)
    conv_cutoff = datetime.now() - timedelta(days=14)
    recent_convs = []
    for row in conv_rows:
        d = parse_date(row.get("date", ""))
        if d and d >= conv_cutoff:
            recent_convs.append(row)

    return {
        "master": master_rows,
        "recent_perf": recent_perf,
        "active_ads": dict(active_ads),
        "conversations": conv_rows,
        "recent_conversations": recent_convs,
        "summary": {
            "days": days,
            "active_ad_count": len(active_ads),
            "total_spend_egp": round(total_spend, 2),
            "total_convos": int(total_convos),
            "blended_cpr_egp": blended_cpr,
            "target_cpr_egp": 17,
        },
        "untagged_count": untagged,
        "data_as_of": datetime.now().strftime("%Y-%m-%d"),
    }


def main():
    parser = argparse.ArgumentParser(description="Query the MTC ad library")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    args = parser.parse_args()

    data = load_library(days=args.days)

    # Print summary to stdout as JSON (for /status to consume)
    output = {
        "summary": data["summary"],
        "untagged_count": data["untagged_count"],
        "data_as_of": data["data_as_of"],
        "active_ads": list(data["active_ads"].values()),
        "recent_conversations_count": len(data["recent_conversations"]),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
