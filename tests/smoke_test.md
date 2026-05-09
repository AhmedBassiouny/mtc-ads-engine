# Smoke Test Runbook — MTC Ads Engine v0

Run this end-to-end after setting up the repo for the first time, or after any significant change.
Expected total time: under 20 minutes.

---

## Prerequisites

- [ ] Repo cloned and in the project directory
- [ ] Python venv created: `python3 -m venv .venv && .venv/bin/pip install pyyaml`
- [ ] Library seeded: `python3 scripts/seed_library.py` (answer `y` to both prompts)
- [ ] Library tagged: `python3 scripts/tag_ads.py`
- [ ] Claude Code open in this project directory

---

## Step 1 — Validate the test brief

```bash
python3 scripts/validate_brief.py tests/fixtures/test_brief_3dsmax.yaml
```

**Expected:** `✅ Brief valid: tests/fixtures/test_brief_3dsmax.yaml`

If it fails, fix the error before continuing.

---

## Step 2 — Scaffold a brief with /new_brief

In Claude Code, run:
```
/new_brief 3dsmax_smoke
```

**Expected:**
- File created at `data/briefs/3dsmax_smoke.yaml`
- Pre-filled with `track: interior_design` and `objective: Messages`
- Claude prints a list of required fields to fill in

You don't need to fill it in — for the rest of the test, use the pre-filled test brief instead.

---

## Step 3 — Run /strategy

In Claude Code, run:
```
/strategy tests/fixtures/test_brief_3dsmax.yaml
```

**Expected:**
1. Brief validates without errors
2. Strategy block generated with:
   - 2 angles from the angle bank (at least one from the top-6 proven angles)
   - No retire-list angles
   - Reels-first placement, Marketplace = 0
   - Budget recommendation citing `config/kill_scale_rules.yaml`
   - Week-1 schedule
   - Pre-flight QA checklist
3. Critic review (Branch A) appended — should show ✅ Passing for all checks if strategy is correct
4. File saved to `data/strategies/strategy_YYYYMMDD_interior_design.md`
5. Confirmation message with ID printed

**Check:**
```bash
ls data/strategies/
cat data/strategies/strategy_*.md | head -40
```

---

## Step 4 — Run /creative

Copy the strategy ID from Step 3 output (e.g. `strategy_20260601_interior_design`), then run:
```
/creative strategy_20260601_interior_design
```

**Expected:**
1. Strategy file found and loaded
2. Creative pack generated with:
   - 12 hooks total (6 per angle), each with template label (A/B/C/D/E)
   - Every hook's first 6 words naming the audience segment
   - No retire-list patterns (no greeting openers, no philosophical openers)
   - Body copy with offer before character 125
   - 12 image briefs specifying 9:16 mobile-vertical
   - 4 video scripts with hook landing in 0–3 seconds
   - Bilingual landing page (Arabic + English)
3. Critic review (Branch B) appended
4. File saved to `data/creative/creative_YYYYMMDD_interior_design.md`

**Check:**
```bash
ls data/creative/
# Scan for retire-list patterns:
grep -i "رمضان كريم\|مش نقص شغل\|حققنا المعادلة" data/creative/*.md && echo "RETIRE LIST VIOLATION" || echo "✅ No retire list patterns"
```

---

## Step 5 — Add image links and run /launch

Open the creative file and add a placeholder image URL to each image brief:
```bash
# Quick way for smoke test — sed won't work on real URLs but confirms the flow
# Manually edit data/creative/<id>.md and add:
# - Image URL: https://example.com/image1.jpg
# (repeat for each image brief)
```

Then run:
```
/launch creative_20260601_interior_design
```

**Expected:**
1. Claude checks for image links — if any are PENDING or missing, it stops with a clear error
2. Media buyer generates launch CSV
3. Pre-write hook (`pre_csv_write.py`) fires and validates:
   - objective = Messages ✅
   - No Marketplace placement ✅
   - hook_ar ≤ 125 chars ✅
   - image_url not PENDING ✅
   - destination_url valid https:// ✅
   - ad_name follows naming convention ✅
4. CSV saved to `data/launches/launch_YYYYMMDD_interior_design.csv`
5. Critic review (Branch C) saved to `data/launches/launch_YYYYMMDD_interior_design.review.md`

**Check hook fires on a bad CSV:**
```bash
python3 -c "
import json, subprocess
bad = '''campaign_name,ad_set_name,ad_name,objective,placement,daily_budget_egp,schedule_start,schedule_end,hook_ar,body_ar,image_url,cta_type,destination_url,angle,hook_template
test,test,bad name,Post Engagement,Feed+Marketplace,30,2026-06-01,2026-05-31,hook,body,PENDING,SEND_MESSAGE,not-a-url,a,A'''
payload = json.dumps({'tool_name': 'Write', 'tool_input': {'file_path': 'data/launches/test.csv', 'content': bad}})
r = subprocess.run(['python3', '.claude/hooks/pre_csv_write.py'], input=payload, capture_output=True, text=True)
print(r.stdout)
print('Exit code:', r.returncode, '(expected: 1)')
"
```

---

## Step 6 — Ingest a performance export

```bash
cp data/seed/Orca-Palace-Ads-6-Apr-2023-6-May-2026.csv data/incoming/test_perf.csv
python3 scripts/ingest_perf.py data/incoming/test_perf.csv
```

**Expected:**
```
Detected: encoding=utf-8, delimiter=COMMA
Source rows: 109 (columns: 29)
Source totals: spend=59637.66 EGP, conversations=3178
✓ Added 109 rows to data/library/performance_log.csv
New data: 109 rows | 59637.66 EGP spend | 3178 conversations
Blended CPR (this import): 18.77 EGP/conversation
✓ Archived source file to data/archive/...
```

Spend and conversation counts must match this. If they don't, there's a parsing issue.

---

## Step 7 — Run /status

In Claude Code:
```
/status
```

**Expected report structure:**
- Portfolio summary with active ad count, total spend, blended CPR
- At least one PAUSE / WATCH / SCALE recommendation with specific reasoning
- Each recommendation cites a metric and a diagnostic rule
- Patterns section with ≥1 observation traceable to data
- Suggested next tests section

**Failure modes to catch:**
- "Generic data dump" — every ad just says "performance is mixed" → fail
- Missing active ads despite just ingesting data → check `performance_log.csv` row count
- No citations to diagnostic rules → the triage prompt needs tuning (Phase 7)

---

## Step 8 — Verify library state

```bash
python3 scripts/library_query.py --days 7 | python3 -m json.tool | head -20
```

**Expected:** JSON with `active_ad_count > 0`, `total_spend_egp > 0`, `blended_cpr_egp` in a reasonable range.

---

## Pass criteria

| Check | Pass condition |
|-------|---------------|
| validate_brief | Exits 0 on valid brief, exits 1 on empty template |
| /strategy | Strategy + critic saved; no retire-list angles |
| /creative | 12 hooks, all following Templates A–E; no retire-list patterns |
| /launch | Hook blocks bad CSV; clean CSV passes; CSV + review saved |
| /ingest perf | Rows added = source rows; spend total matches |
| /status | Opinionated PAUSE/WATCH/SCALE per active ad; diagnostic citations |

---

## Restore clean state after smoke test

```bash
python3 scripts/seed_library.py  # answer y to both
python3 scripts/tag_ads.py
rm -f data/archive/*.csv
rm -f data/strategies/*.md data/creative/*.md data/launches/*.csv data/launches/*.md
rm -f data/briefs/3dsmax_smoke.yaml
```
