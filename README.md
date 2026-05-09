# MTC Ads Engine v0

AI-driven ad operations system for MTC (Muttaheda Training Center, Cairo). Runs entirely inside Claude Code — no cloud infrastructure, no external APIs.

**Target:** ≤17 EGP cost per WhatsApp conversation (current blended: ~18.59 EGP, best ad: 6.59 EGP).

---

## What it does

Takes a course brief as input and produces:

1. **Strategy** — audience, angles, channel split, budget recommendation
2. **Creative pack** — hooks, body copy, image briefs, video scripts, landing page copy
3. **Launch CSV** — ready to bulk-paste into Meta Ads Manager

Plus an ongoing **status report** that reads your ad library and tells you exactly which ads to pause, scale, or refresh.

---

## Quick start

```bash
# One-time setup: seed the ad library from historical data
python3 scripts/seed_library.py

# Launch a new course
/new_brief 3dsmax
# Fill in data/briefs/3dsmax.yaml, then:
/strategy data/briefs/3dsmax.yaml
/creative <strategy_id>
/launch <creative_id>

# Daily: after dropping a fresh Meta CSV export into data/incoming/
/ingest perf data/incoming/<export_file.csv>
/status
```

---

## Six slash commands

| Command | Input | Output |
|---------|-------|--------|
| `/new_brief <course>` | course name | `data/briefs/<course>.yaml` to fill in |
| `/strategy <brief>` | brief YAML path | strategy + critic review in `data/strategies/` |
| `/creative <id>` | strategy ID | creative pack + critic review in `data/creative/` |
| `/launch <id>` | creative ID | validated launch CSV in `data/launches/` |
| `/ingest perf <file>` | Meta export CSV | updated `data/library/` |
| `/status` | _(none)_ | opinionated triage report in terminal |

Every `/strategy`, `/creative`, and `/launch` run includes an automatic critic review — same session, second prompt — that checks the output against the playbook before saving.

---

## Data flow

```
data/seed/              ← historical CSVs (one-time reference)
    ↓ seed_library.py
data/library/           ← live canonical state
  master.csv            ← 70+ ads with tags + performance
  performance_log.csv   ← append-only monthly snapshots
  conversations.csv     ← WhatsApp outcomes (manual)
    ↑ /ingest perf
data/incoming/          ← operator drops Meta exports here
```

---

## Playbook source

All strategy intelligence comes from `data/seed/MTC_Ad_Diagnostic_v1.md`. Key findings:

- **Job-ad mimicry** is the best-performing angle (13.6 EGP CPR, 217 conversations)
- **Specific-course ads** beat all-courses ads 2:1
- **Holiday-greeting hooks** cost 2–3× normal ads — retire them
- **First 6 words** must name the audience segment

See `CLAUDE.md` for full project memory loaded on every session.

---

## Setup

**Prerequisites:** Python 3.x, Claude Code (Max plan)

```bash
# Install dependencies
pip install pyyaml

# Clone and seed
git clone https://github.com/AhmedBassiouny/mtc-ads-engine
cd mtc-ads-engine
python3 scripts/seed_library.py

# Verify: data/library/master.csv should have 70 rows
```

See `WALKTHROUGH.md` for the full operator guide.
