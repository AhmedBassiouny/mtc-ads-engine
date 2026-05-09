#!/usr/bin/env python3
"""
Tags master.csv with angle, hook_template, and course_track.

Uses pattern matching based on MTC_Ad_Diagnostic_v1.md §2-5.
Run after seed_library.py: python3 scripts/tag_ads.py

For ads that don't match any pattern, outputs a review file at
data/library/untagged_review.csv so you can tag them manually
or run this script in a Claude Code session for AI-assisted tagging.
"""

import csv
import pathlib
import re
import sys

LIB = pathlib.Path("data/library")
MASTER = LIB / "master.csv"
REVIEW = LIB / "untagged_review.csv"


# ── Course track patterns ──────────────────────────────────────────────────
# Source: §5 Course track playbook
COURSE_PATTERNS = [
    ("interior_design", re.compile(r"ديكور|تصميم داخلي|interior|decor", re.I)),
    ("civil_3d",        re.compile(r"سيفيل ثري دي|civil 3d|civil3d|surveying|مساحة", re.I)),
    ("civil",           re.compile(r"مدني|إنشاء|إنشاءات|طرق|civil(?! 3)", re.I)),
    ("architecture",    re.compile(r"عمار|architect|revit|bim", re.I)),
    ("mechanical",      re.compile(r"ميكانيكا|mechanical|hvac|fire fighting|ميكانيك", re.I)),
    ("technical_office",re.compile(r"مكتب فني|technical office|shop drawing", re.I)),
    ("electrical",      re.compile(r"كهرب|electrical|elec", re.I)),
    ("3dsmax",          re.compile(r"3ds|ثري دي اس|3d max|ماكس|3dsmax", re.I)),
    ("autocad",         re.compile(r"اوتوكاد|autocad", re.I)),
]

# ── Angle patterns ─────────────────────────────────────────────────────────
# Source: §2 Angle bank
ANGLE_PATTERNS = [
    ("job_ad_mimicry",       re.compile(r"مطلوب", re.I)),
    ("future_vision_ai",     re.compile(r"ذكاء|ai|مستقبل.*mtc|ابدأ مستقبل", re.I)),
    ("group_social",         re.compile(r"جمع اصاحب|جمع أصحاب|صاحبك", re.I)),
    ("first_time_egypt",     re.compile(r"لاول مرة|لأول مرة|first time", re.I)),
    ("dream_to_career",      re.compile(r"نفسك تكون|نفسك تحترف|حلمك|dream|تكون محترف", re.I)),
    ("student_inertia",      re.compile(r"زهقت|مللت|عندك عقدة", re.I)),
    ("ambitious_students",   re.compile(r"طموح|طالب في هندسة|مهندس أو طالب", re.I)),
    ("curriculum_dump",      re.compile(r"المعادلة الصعبة|هتتعلم|هيتعلم", re.I)),
    ("holiday_eid",          re.compile(r"عيد|eid", re.I)),
    ("holiday_ramadan",      re.compile(r"رمضان|ramadan", re.I)),
    ("generic_discount",     re.compile(r"خصم|discount", re.I)),
    ("specific_course_offer",re.compile(r"لمهندسي|لطلاب|يركزو", re.I)),
    ("philosophical",        re.compile(r"نقص مهار|مش نقص", re.I)),
    ("scarcity_only",        re.compile(r"مش هتلاقي خصوم|آخر فرصة|last chance", re.I)),
    ("price_anchor",         re.compile(r"\d+.*vs.*\d+|\d+ بدل \d+", re.I)),
    ("english_brand",        re.compile(r"^[a-z\s]+$", re.I)),
]

# ── Hook template patterns ─────────────────────────────────────────────────
# Source: §3 Hook templates A–E
HOOK_PATTERNS = [
    # A: [لـ + segment], offer + reality-check
    ("A", re.compile(r"^لـ?[مط].{3,20}[،,].{5,}", re.I)),
    # B: مطلوب ...
    ("B", re.compile(r"^مطلوب", re.I)),
    # C: [audience plural] يركزو
    ("C", re.compile(r"يركزو|يركّزو", re.I)),
    # D: ابدأ مستقبلك
    ("D", re.compile(r"^ابدأ مستقبل", re.I)),
    # E: جمع اصاحبك
    ("E", re.compile(r"^جمع", re.I)),
]


def detect_course(text: str) -> str:
    for track, pattern in COURSE_PATTERNS:
        if pattern.search(text):
            return track
    if re.search(r"هندس|engineer|كل الكورسات|all courses", text, re.I):
        return "cross_track"
    return ""


def detect_angle(text: str) -> str:
    for angle, pattern in ANGLE_PATTERNS:
        if pattern.search(text):
            return angle
    return ""


def strip_meta_wrapper(text: str) -> str:
    """Remove 'Post: "..."', 'المنشور: "..."' wrappers and Unicode bidi chars."""
    # Strip Unicode directional marks
    text = re.sub(r"[‎‏‪-‮]", "", text)
    # Extract content from 'Post: "..."' or 'المنشور: "..."'
    m = re.match(r'^(?:Post|المنشور|الفيديو)\s*:\s*["“”]?(.+)', text, re.S)
    if m:
        text = m.group(1).rstrip('""”').strip()
    return text


def detect_hook(text: str) -> str:
    first_line = strip_meta_wrapper(text).split("\n")[0][:200]
    for label, pattern in HOOK_PATTERNS:
        if pattern.search(first_line):
            return label
    return ""


def tag_row(row: dict) -> dict:
    name = strip_meta_wrapper(row.get("ad_name", ""))
    body = row.get("Body", "")
    combined = " ".join(filter(None, [name, body]))
    row["course_track"] = detect_course(combined)
    row["angle"] = detect_angle(combined)
    hook_source = body or name
    row["hook_template"] = detect_hook(hook_source)
    return row


def main():
    if not MASTER.exists():
        print(f"ERROR: {MASTER} not found. Run seed_library.py first.")
        sys.exit(1)

    with open(MASTER, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    tagged = 0
    untagged = []

    for row in rows:
        row = tag_row(row)
        has_spend = float(row.get("spend") or 0) > 0
        fully_tagged = row["angle"] and row["course_track"]
        if has_spend and not fully_tagged:
            untagged.append(row)
        elif fully_tagged:
            tagged += 1

    with open(MASTER, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ Tagged {tagged} ads with angle + course_track")

    if untagged:
        with open(REVIEW, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(untagged)
        print(f"⚠  {len(untagged)} ads with spend but missing tags → {REVIEW}")
        print("   Review that file and fill in angle/hook_template/course_track manually,")
        print("   or open a Claude Code session and ask Claude to tag them from the ad name.")
    else:
        print("✓ All ads with spend are fully tagged")

    # Summary
    from collections import Counter
    angle_counts = Counter(r["angle"] for r in rows if r["angle"])
    course_counts = Counter(r["course_track"] for r in rows if r["course_track"])
    print(f"\nAngle distribution: {dict(angle_counts.most_common())}")
    print(f"Course distribution: {dict(course_counts.most_common())}")


if __name__ == "__main__":
    main()
