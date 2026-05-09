# MTC Ads Engine — Operator Walkthrough

This guide takes you from zero to a running system. Estimated time: 1–2 hours on first setup, 5–10 minutes per daily use.

---

## Part 1 — First-time setup

### 1.1 Prerequisites

- **Claude Code** installed and logged in to a Max plan account
- **Python 3.9+** (`python3 --version`)
- **Git** (`git --version`)
- **GitHub account** (AhmedBassiouny) with access to this repo

### 1.2 Clone and enter the repo

```bash
git clone https://github.com/AhmedBassiouny/mtc-ads-engine
cd mtc-ads-engine
```

### 1.3 Create the Python virtual environment

```bash
python3 -m venv .venv
.venv/bin/pip install pyyaml
```

> You only need to do this once. The `.venv/` folder is gitignored.

### 1.4 Seed the ad library

This copies the historical seed data into `data/library/` where the system reads from during normal use.

```bash
python3 scripts/seed_library.py
# Answer 'y' to both prompts
```

Expected output:
```
✓ master.csv: 113 rows written to data/library/master.csv
✓ performance_log.csv: 4294 rows written to data/library/performance_log.csv
✓ conversations.csv: empty schema created at data/library/conversations.csv
```

### 1.5 Tag the historical ads

This infers angle, hook template, and course track from each ad's name and body copy.

```bash
python3 scripts/tag_ads.py
```

Expected output:
```
✓ Tagged 43 ads with angle + course_track
⚠  64 ads flagged in data/library/untagged_review.csv
```

The 64 untagged ads are historical campaigns with vague names (test runs, single-word names). They won't affect the system's ability to generate new campaigns — they just won't appear in angle-level breakdowns in `/status`. You can tag them manually or leave them.

### 1.6 Verify setup

```bash
python3 scripts/library_query.py --days 30
```

You should see JSON with `active_ad_count > 0` and `total_spend_egp > 0`.

### 1.7 Open Claude Code in this directory

```bash
claude
```

The `CLAUDE.md` file at the repo root loads automatically on every session — it gives Claude the full project context without you having to re-explain it.

---

## Part 2 — Launching a new course

This is the main workflow. Repeat for every course intake.

### 2.1 Create a brief

```
/new_brief <course_name>
```

Example: `/new_brief decor_june`

This creates `data/briefs/decor_june.yaml` pre-filled with the course track defaults. Open the file and fill in:

| Field | What to enter |
|-------|--------------|
| `course.price_egp` | Full price before discount |
| `course.discount_pct` | Discount % to advertise (e.g. 50) |
| `course.discounted_price_egp` | Calculated price after discount |
| `launch.start_date` | Course start date (YYYY-MM-DD) |
| `launch.enrollment_deadline` | Last day to register (YYYY-MM-DD) |
| `launch.daily_budget_egp` | Per-variant daily budget (minimum 100 EGP recommended) |
| `creative.urgency_reason` | Why act now — e.g. "قبل ما تقفل المجموعة" |
| `creative.destination_url` | Your WhatsApp link or landing page |
| `notes` | Anything special about this intake |

### 2.2 Generate strategy

```
/strategy data/briefs/decor_june.yaml
```

Claude reads the brief, the playbook, and the seasonal calendar, then outputs:
- 2 recommended angles (from the angle bank)
- Channel split and placement rules
- Daily budget per variant
- Week-1 schedule
- Pre-flight QA checklist
- Critic review (automatically run — no extra command needed)

**Read the output file** (`data/strategies/strategy_<id>.md`) before proceeding. Check the critic's 🛑 Blockers — if any exist, fix them before continuing.

### 2.3 Generate creative pack

```
/creative strategy_<id>
```

Replace `<id>` with the strategy ID shown in the previous step.

Claude outputs:
- 12 hooks (6 per angle), labelled with template A–E
- Full Arabic body copy for each hook
- 12 image briefs (9:16 mobile-vertical, Arabic on-image text)
- 4 video scripts (15s + 30s per angle)
- Bilingual landing page copy (Arabic + English)
- Critic review

**Read the output** at `data/creative/creative_<id>.md`. Then add image URLs:
- Brief a designer using the image briefs
- Once images are ready and hosted, add their URLs to the creative file next to each image brief

### 2.4 Generate launch CSV

```
/launch creative_<id>
```

Claude generates a bulk-paste Meta Ads Manager CSV. Before saving, the pre-write hook automatically validates:
- Objective is Messages or Conversions
- No Marketplace/Notifications/Profile feeds placements
- Arabic text within character limits
- Valid URLs, no PENDING image links
- Naming convention followed

If the hook blocks the write, Claude will show you exactly what to fix.

The launch CSV is saved to `data/launches/launch_<id>.csv`.

### 2.5 Upload to Meta Ads Manager

1. Go to **Meta Ads Manager → Ads → Import**
2. Upload `data/launches/launch_<id>.csv`
3. Review the import preview — check campaign/ad set/ad names
4. Confirm and publish

**Set a kill-check reminder:** 2 days after launch, check CPR per ad:
- CPR > 30 EGP with ≥80 EGP spend → pause it
- CPR ≤ 17 EGP with ≥80 EGP spend → scale it (duplicate ad set at 2× budget)
- See `config/kill_scale_rules.yaml` for the full rules

---

## Part 3 — Daily operations

### 3.1 Ingest a Meta performance export

After running ads, export performance data from Meta Ads Manager:
1. **Ads Manager → Reports → Export**
2. Select date range (last 7 days recommended)
3. Save the file

Drop the file in `data/incoming/` and run:

```
/ingest perf data/incoming/<filename.csv>
```

The script auto-detects encoding (UTF-16 LE or UTF-8) and delimiter (tab or comma) — you don't need to configure anything. It will:
- Print the row count and total spend (verify these match Ads Manager)
- Add new rows to `data/library/performance_log.csv`
- Archive the source file to `data/archive/`

### 3.2 Run the status report

```
/status
```

This reads the current library and produces an opinionated report:

```
# MTC Ads Status — 2026-06-03

## Portfolio summary (last 7 days)
- Active ads: 8
- Spend: 3,200 EGP
- Conversations: 187
- Blended CPR: 17.1 EGP (target: ≤17 EGP)

## Action required

🛑 PAUSE — 2026-06-01_decor_holiday_v1
   CPR: 38 EGP after 95 EGP spend — above kill threshold
   Action: Pause. Holiday framing on retire list (§4).

✅ SCALE — 2026-06-01_decor_jobad_v2
   CPR: 12 EGP after 110 EGP spend — below 17 EGP target
   Action: Duplicate ad set at 200 EGP/day.
...
```

Run `/status` any time — not just after ingesting. It works on whatever data is in the library.

### 3.3 Log WhatsApp outcomes (important!)

After each Messenger conversation, log the outcome in `data/library/conversations.csv`:

| Field | Value |
|-------|-------|
| `date` | DD/MM/YYYY |
| `ad_id` | Ad ID from Meta (visible in Ads Manager) |
| `ad_name` | Ad name |
| `angle` | Angle used (from the angle bank) |
| `course_track` | Course track |
| `outcome` | `enrolled` / `quoted` / `ghosted` / `unknown` |
| `notes` | Optional: main objection raised |

After 30+ rows, `/status` will show which angles produce cheap conversations AND cheap enrollments — the missing link in the loop (§7 of the diagnostic).

You can also bulk-import from a WhatsApp chat export:
```
/ingest whatsapp data/incoming/<export.txt>
```
Then fill in the `ad_id` and `outcome` columns manually.

---

## Part 4 — Troubleshooting

### "No recent performance data" in /status

You haven't ingested a performance export yet. Drop a Meta CSV export into `data/incoming/` and run `/ingest perf <file>`.

### Hook blocks the launch CSV

Read the error message — it will name the exact column and row with the problem. Common fixes:
- **Wrong objective:** change `Post Engagement` to `Messages`
- **Marketplace in placement:** remove it from the placement column
- **PENDING image:** add the actual image URL before running `/launch` again
- **Bad ad_name:** must be `YYYY-MM-DD_course_angle_v1` format

### UTF-16 LE encoding error

If `ingest_perf.py` crashes on a Meta export, check:
```bash
python3 -c "
f = open('data/incoming/<yourfile.csv>', 'rb')
print(f.read(4).hex())
"
```
If it starts with `fffe`, it's UTF-16 LE — the script should detect this automatically. If it doesn't, open an issue.

### Untagged ads in /status

Run `python3 scripts/tag_ads.py` to re-run auto-tagging after new ads are ingested. For ads that still don't get tagged (vague names), open `data/library/untagged_review.csv` and fill in `angle`, `hook_template`, `course_track` manually.

### Brief validation fails

Run `python3 scripts/validate_brief.py data/briefs/<your_brief>.yaml` to see exactly which fields are missing or invalid.

---

## Part 5 — File reference

| Location | What it is |
|----------|-----------|
| `data/library/master.csv` | All historical ads with tags + lifetime metrics |
| `data/library/performance_log.csv` | Monthly performance snapshots (append-only) |
| `data/library/conversations.csv` | WhatsApp outcomes (fill manually) |
| `data/incoming/` | Drop new Meta exports here |
| `data/archive/` | Processed exports (gitignored) |
| `data/briefs/` | Course brief YAMLs |
| `data/strategies/` | Generated strategy outputs |
| `data/creative/` | Generated creative packs |
| `data/launches/` | Generated launch CSVs |
| `config/courses.yaml` | Course catalog with lead angles |
| `config/kill_scale_rules.yaml` | Kill/scale thresholds |
| `config/seasonal_calendar.yaml` | Ramadan/Eid/Summer budget multipliers |
| `prompts/` | AI persona prompts (read-only during normal use) |
| `data/seed/` | Original historical data (read-only) |

---

## Part 6 — Updating the system

### Updating prompt templates

Edit the relevant file in `prompts/`. Changes take effect on the next slash command run — no restart needed.

After editing a prompt, note the change in `DECISIONS.md` with the reason.

### Adding a new course track

1. Add an entry to `config/courses.yaml`
2. Add the relevant audience segment to `config/audience_definitions.yaml` if needed
3. Commit with a message referencing the diagnostic section that supports the new angle

### Updating kill/scale rules

Edit `config/kill_scale_rules.yaml`. The new thresholds apply on the next `/status` run.

---

## Quick reference card

```
First time:
  git clone / cd mtc-ads-engine
  python3 -m venv .venv && .venv/bin/pip install pyyaml
  python3 scripts/seed_library.py   # answer y twice
  python3 scripts/tag_ads.py
  claude

Launch a course:
  /new_brief <name>           → fill in data/briefs/<name>.yaml
  /strategy data/briefs/<name>.yaml
  /creative <strategy_id>     → add image URLs to output file
  /launch <creative_id>       → upload data/launches/<id>.csv to Meta

Daily:
  drop export → data/incoming/
  /ingest perf data/incoming/<file.csv>
  /status
```
