#!/usr/bin/env python3
"""
PreToolUse hook — validates launch CSVs before they are written.

Fires on every Write tool call. If the target path is data/launches/*.csv,
it parses the content and checks all technical constraints. If any blocker
is found, exits non-zero and prints a specific error — the write is blocked.

Validation rules (from MTC_Ad_Diagnostic_v1.md and media_buyer.md):
  - Required fields present in header
  - objective = Messages or Conversions (never Post Engagement, Traffic, etc.)
  - Forbidden placements: Marketplace, Notifications, Profile feeds
  - hook_ar visible length ≤ 125 chars (Unicode code points — Arabic counts as 1 each)
  - destination_url well-formed (starts with https:// or https://wa.me/)
  - image_url not PENDING
  - ad_name follows naming convention [YYYY-MM-DD]_[course]_[angle]_v[n]
  - daily_budget_egp ≥ 50
  - schedule_end > schedule_start
"""

import csv
import io
import json
import re
import sys
from datetime import datetime

REQUIRED_FIELDS = {
    "campaign_name", "ad_set_name", "ad_name", "objective",
    "placement", "daily_budget_egp", "schedule_start", "schedule_end",
    "hook_ar", "body_ar", "image_url", "cta_type", "destination_url",
}

VALID_OBJECTIVES = {"Messages", "Conversions"}
FORBIDDEN_PLACEMENTS = {"marketplace", "notifications", "profile feeds", "profile_feeds"}

HOOK_AR_VISIBLE_LIMIT = 125   # Meta truncation point (Unicode code points)
BODY_AR_OFFER_LIMIT   = 125   # offer must appear before this char in body_ar
MIN_BUDGET_EGP        = 50

# ad_name: YYYY-MM-DD_<course>_<angle>_v<n> or _<variant#>
AD_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_.+_.+_(v\d+|\d+)$")


def err(msg: str) -> None:
    print(f"🛑 HOOK BLOCKED: {msg}", flush=True)


def validate_csv(content: str, path: str) -> list[str]:
    """Returns list of error messages. Empty = valid."""
    errors = []
    try:
        reader = csv.DictReader(io.StringIO(content))
        if reader.fieldnames is None:
            return ["CSV has no header row"]

        # Check required fields
        missing = REQUIRED_FIELDS - set(f.strip() for f in reader.fieldnames)
        if missing:
            errors.append(f"Missing required columns: {sorted(missing)}")
            return errors  # can't validate rows without the columns

        rows = list(reader)
        if not rows:
            errors.append("CSV has no data rows")
            return errors

        for i, row in enumerate(rows, start=2):  # row 1 is header
            row_id = row.get("ad_name") or f"row {i}"

            # Objective
            obj = row.get("objective", "").strip()
            if obj not in VALID_OBJECTIVES:
                errors.append(
                    f"[{row_id}] objective='{obj}' — must be Messages or Conversions, "
                    f"never Post Engagement or Traffic"
                )

            # Placement
            placement = row.get("placement", "").lower()
            for forbidden in FORBIDDEN_PLACEMENTS:
                if forbidden in placement:
                    errors.append(
                        f"[{row_id}] placement includes '{forbidden}' — "
                        "Marketplace, Notifications, and Profile feeds must be excluded (§2 diagnostic)"
                    )

            # hook_ar length (Unicode code points — Arabic chars count as 1 each)
            hook = row.get("hook_ar", "")
            hook_len = len(hook)
            if hook_len > HOOK_AR_VISIBLE_LIMIT:
                errors.append(
                    f"[{row_id}] hook_ar is {hook_len} chars — exceeds Meta visible limit of "
                    f"{HOOK_AR_VISIBLE_LIMIT}. Offer must appear before truncation."
                )

            # body_ar: offer should appear before char 125
            body = row.get("body_ar", "")
            if body and "%" not in body[:BODY_AR_OFFER_LIMIT] and "EGP" not in body[:BODY_AR_OFFER_LIMIT]:
                # Check for common Arabic discount indicators
                visible = body[:BODY_AR_OFFER_LIMIT]
                has_offer_signal = any(w in visible for w in ["خصم", "عرض", "جنيه", "سعر", "%", "ج.م"])
                if not has_offer_signal:
                    errors.append(
                        f"[{row_id}] body_ar: no offer signal (discount %, price) in first "
                        f"{BODY_AR_OFFER_LIMIT} chars — Meta truncates here and offer must be visible"
                    )

            # image_url: no PENDING
            image_url = row.get("image_url", "").strip()
            if not image_url or image_url.upper() == "PENDING":
                errors.append(
                    f"[{row_id}] image_url is missing or PENDING — "
                    "do not launch without images"
                )

            # destination_url: must be a valid URL
            dest_url = row.get("destination_url", "").strip()
            if not dest_url:
                errors.append(f"[{row_id}] destination_url is empty")
            elif not (dest_url.startswith("https://") or dest_url.startswith("http://")):
                errors.append(
                    f"[{row_id}] destination_url '{dest_url[:50]}' is not a valid URL "
                    "(must start with https://)"
                )

            # ad_name: naming convention
            ad_name = row.get("ad_name", "").strip()
            if ad_name and not AD_NAME_RE.match(ad_name):
                errors.append(
                    f"[{row_id}] ad_name '{ad_name}' does not follow naming convention "
                    "[YYYY-MM-DD]_[course]_[angle]_v[n] — e.g. 2026-05-15_decor_jobad_v2"
                )

            # daily_budget_egp: minimum 50
            try:
                budget = float(row.get("daily_budget_egp", 0) or 0)
                if budget < MIN_BUDGET_EGP:
                    errors.append(
                        f"[{row_id}] daily_budget_egp={budget} — minimum is {MIN_BUDGET_EGP} EGP "
                        "(below this there is not enough data to kill/scale per kill_scale_rules.yaml)"
                    )
            except ValueError:
                errors.append(f"[{row_id}] daily_budget_egp is not a number: {row.get('daily_budget_egp')}")

            # schedule: end > start
            start_str = row.get("schedule_start", "").strip()
            end_str   = row.get("schedule_end", "").strip()
            if start_str and end_str:
                try:
                    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                    end_dt   = datetime.strptime(end_str,   "%Y-%m-%d")
                    if end_dt <= start_dt:
                        errors.append(
                            f"[{row_id}] schedule_end ({end_str}) must be after schedule_start ({start_str})"
                        )
                    delta_days = (end_dt - start_dt).days
                    if delta_days > 7:
                        errors.append(
                            f"[{row_id}] schedule spans {delta_days} days — "
                            "kill rules require checking at day 5; runs longer than 7 days risk fatigue"
                        )
                except ValueError as e:
                    errors.append(f"[{row_id}] invalid date format: {e}")

    except Exception as e:
        errors.append(f"Failed to parse CSV: {e}")

    return errors


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON — let the tool call through (not our concern)
        sys.exit(0)

    tool_name  = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Write tool calls
    if tool_name != "Write":
        sys.exit(0)

    file_path = tool_input.get("file_path", "")

    # Only intercept writes to data/launches/*.csv
    if not (file_path.endswith(".csv") and "data/launches" in file_path):
        sys.exit(0)

    content = tool_input.get("content", "")
    errors = validate_csv(content, file_path)

    if errors:
        print(f"\n{'='*60}")
        print(f"🛑 LAUNCH CSV VALIDATION FAILED — write blocked")
        print(f"   File: {file_path}")
        print(f"   {len(errors)} error(s) found:\n")
        for e in errors:
            print(f"   • {e}")
        print(f"\n   Fix these issues in the CSV and try again.")
        print(f"{'='*60}\n")
        sys.exit(1)

    # Valid — print a brief confirmation and allow
    print(f"✅ CSV validation passed ({file_path}) — {len(content.splitlines())-1} ad rows")
    sys.exit(0)


if __name__ == "__main__":
    main()
