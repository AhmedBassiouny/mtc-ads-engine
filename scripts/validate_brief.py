#!/usr/bin/env python3
"""
Validate a course brief YAML before running /strategy.

Usage: python3 scripts/validate_brief.py <brief_path>

Checks:
  - File exists and is valid YAML
  - All required fields are present and non-empty
  - course.track exists in config/courses.yaml
  - launch.objective is Messages or Conversions
  - launch.start_date and enrollment_deadline are valid dates
  - creative.destination_url starts with https://
  - discount_pct is 0-100

Exits 0 if valid, 1 if errors found.
"""

import pathlib
import sys
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: python3 -m venv .venv && .venv/bin/pip install pyyaml")
    sys.exit(1)

REQUIRED_FIELDS = {
    "course.track",
    "course.name_ar",
    "course.price_egp",
    "course.discount_pct",
    "launch.start_date",
    "launch.enrollment_deadline",
    "launch.daily_budget_egp",
    "launch.objective",
    "creative.destination_url",
}

VALID_OBJECTIVES = {"Messages", "Conversions"}


def get_nested(data: dict, dotted_key: str):
    """Get value from nested dict using dot notation."""
    keys = dotted_key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
    return val


def load_course_tracks() -> set[str]:
    courses_path = pathlib.Path("config/courses.yaml")
    if not courses_path.exists():
        return set()
    with open(courses_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return set(data.get("courses", {}).keys())


def validate(brief_path: pathlib.Path) -> list[str]:
    errors = []

    if not brief_path.exists():
        return [f"File not found: {brief_path}"]

    try:
        with open(brief_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return ["Brief is not a valid YAML mapping"]

    # Required fields
    for field in sorted(REQUIRED_FIELDS):
        val = get_nested(data, field)
        if val is None or val == "" or val == 0:
            errors.append(f"Missing or empty: {field}")

    if errors:
        return errors  # don't run further checks on incomplete brief

    # course.track must exist in courses.yaml
    track = get_nested(data, "course.track")
    valid_tracks = load_course_tracks()
    if valid_tracks and track not in valid_tracks:
        errors.append(
            f"course.track='{track}' not in config/courses.yaml. "
            f"Valid tracks: {sorted(valid_tracks)}"
        )

    # objective
    objective = get_nested(data, "launch.objective")
    if objective not in VALID_OBJECTIVES:
        errors.append(
            f"launch.objective='{objective}' must be one of {VALID_OBJECTIVES}"
        )

    # dates
    for date_field in ("launch.start_date", "launch.enrollment_deadline"):
        val = get_nested(data, date_field)
        if val:
            try:
                if isinstance(val, str):
                    datetime.strptime(val, "%Y-%m-%d")
                # datetime.date objects from YAML are fine
            except ValueError:
                errors.append(f"{date_field}='{val}' must be YYYY-MM-DD format")

    start = get_nested(data, "launch.start_date")
    deadline = get_nested(data, "launch.enrollment_deadline")
    if start and deadline:
        try:
            start_dt = datetime.strptime(str(start), "%Y-%m-%d")
            deadline_dt = datetime.strptime(str(deadline), "%Y-%m-%d")
            if deadline_dt < start_dt:
                errors.append("launch.enrollment_deadline must be on or after launch.start_date")
        except ValueError:
            pass  # already caught above

    # destination_url
    url = get_nested(data, "creative.destination_url")
    if url and not (str(url).startswith("https://") or str(url).startswith("http://")):
        errors.append(
            f"creative.destination_url='{url}' must start with https://"
        )

    # discount_pct
    discount = get_nested(data, "course.discount_pct")
    if discount is not None:
        try:
            d = float(discount)
            if not (0 <= d <= 100):
                errors.append(f"course.discount_pct={d} must be between 0 and 100")
        except (TypeError, ValueError):
            errors.append(f"course.discount_pct='{discount}' must be a number")

    # daily_budget_egp
    budget = get_nested(data, "launch.daily_budget_egp")
    if budget is not None:
        try:
            b = float(budget)
            if b < 50:
                errors.append(
                    f"launch.daily_budget_egp={b} — minimum is 50 EGP per variant "
                    "(below this there's insufficient data to kill/scale)"
                )
        except (TypeError, ValueError):
            errors.append(f"launch.daily_budget_egp='{budget}' must be a number")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_brief.py <brief_path>")
        sys.exit(1)

    brief_path = pathlib.Path(sys.argv[1])
    errors = validate(brief_path)

    if errors:
        print(f"🛑 Brief validation failed: {brief_path}")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print(f"✅ Brief valid: {brief_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
