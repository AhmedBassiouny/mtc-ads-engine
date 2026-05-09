#!/usr/bin/env python3
"""
Ingest a WhatsApp chat export into data/library/conversations.csv.

Usage: python3 scripts/ingest_whatsapp.py <file_path>

WhatsApp exports a .txt file (from "Export Chat" in the app).
Format varies by locale, but common patterns:

  [DD/MM/YYYY, HH:MM:SS] Sender: Message
  DD/MM/YYYY, HH:MM - Sender: Message

This script:
  1. Parses the text file into (date, sender, message) tuples
  2. Groups messages by conversation (date proximity)
  3. Appends a row to data/library/conversations.csv for operator review
  4. The operator fills in: ad_id, outcome (enrolled/quoted/ghosted)

Note: WhatsApp exports don't contain ad attribution — the operator manually
links a conversation to an ad by date-matching with the active campaign.
The conversations.csv schema has an ad_id column for this.
"""

import csv
import pathlib
import re
import shutil
import sys
from datetime import datetime

LIB = pathlib.Path("data/library")
ARCHIVE = pathlib.Path("data/archive")
CONV_FILE = LIB / "conversations.csv"

CONV_FIELDS = ["date", "ad_id", "ad_name", "angle", "course_track", "outcome", "notes"]

# WhatsApp message line patterns
# Pattern 1: [DD/MM/YYYY, HH:MM:SS] Sender: Message
# Pattern 2: DD/MM/YYYY, HH:MM - Sender: Message
WA_PATTERNS = [
    re.compile(r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.+)$"),
    re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.+)$"),
]


def parse_whatsapp_export(path: pathlib.Path) -> list[dict]:
    """Parse WhatsApp .txt export into list of message dicts."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-16")

    messages = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pattern in WA_PATTERNS:
            m = pattern.match(line)
            if m:
                date_str, time_str, sender, message = m.groups()
                messages.append({
                    "date_str": date_str,
                    "time_str": time_str,
                    "sender": sender.strip(),
                    "message": message.strip(),
                })
                break

    return messages


def group_into_conversations(messages: list[dict]) -> list[dict]:
    """
    Group messages into conversation sessions.
    A new conversation starts when the first message from a new sender
    (non-MTC side) appears. Returns one row per conversation session.
    """
    if not messages:
        return []

    conversations = []
    current_date = messages[0]["date_str"] if messages else ""
    first_message = messages[0]["message"][:100] if messages else ""

    # Simple grouping: one row per unique date (each day = potential conversation)
    by_date: dict[str, list] = {}
    for msg in messages:
        by_date.setdefault(msg["date_str"], []).append(msg)

    for date_str, msgs in sorted(by_date.items()):
        # Get a preview of the conversation
        preview = " | ".join(m["message"][:40] for m in msgs[:2])
        conversations.append({
            "date": date_str,
            "ad_id": "",          # operator fills this in
            "ad_name": "",        # operator fills this in
            "angle": "",          # operator fills this in after tagging
            "course_track": "",
            "outcome": "",        # enrolled / quoted / ghosted / unknown
            "notes": preview[:120],
        })

    return conversations


def load_existing_conv_dates(path: pathlib.Path) -> set[str]:
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {r.get("date", "") for r in reader}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/ingest_whatsapp.py <file_path>")
        sys.exit(1)

    src = pathlib.Path(sys.argv[1])
    if not src.exists():
        print(f"ERROR: file not found: {src}")
        sys.exit(1)

    print(f"Parsing WhatsApp export: {src}")
    messages = parse_whatsapp_export(src)
    print(f"Parsed {len(messages)} messages")

    if not messages:
        print("No messages found — check the file format")
        sys.exit(1)

    conversations = group_into_conversations(messages)
    print(f"Grouped into {len(conversations)} conversation sessions")

    # Skip dates already in the file
    existing_dates = load_existing_conv_dates(CONV_FILE)
    new_convs = [c for c in conversations if c["date"] not in existing_dates]
    print(f"New sessions to add: {len(new_convs)} (skipping {len(conversations) - len(new_convs)} duplicates)")

    if not new_convs:
        print("No new conversations to add")
        sys.exit(0)

    # Append to conversations.csv
    write_header = not CONV_FILE.exists()
    with open(CONV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(new_convs)

    print(f"✓ Added {len(new_convs)} rows to data/library/conversations.csv")
    print(f"\nNext step: open data/library/conversations.csv and fill in:")
    print(f"  - ad_id: which ad was running that day (check Meta Ads Manager)")
    print(f"  - outcome: enrolled / quoted / ghosted / unknown")
    print(f"  - angle / course_track: from the ad that drove the conversation")
    print(f"\nAfter 30+ rows with outcomes, /status will show enrollment rates per angle.")

    # Archive
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE / f"{timestamp}_{src.name}"
    shutil.move(str(src), str(archive_path))
    print(f"✓ Archived to {archive_path}")


if __name__ == "__main__":
    main()
