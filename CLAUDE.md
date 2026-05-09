# MTC Ads Engine — Project Memory

## What this system is

An AI-driven ad operations system for MTC (Muttaheda Training Center, Cairo). Runs entirely inside Claude Code — no cloud, no external APIs, no separate infrastructure. The operator types slash commands in the terminal; Claude reads local CSV files and prompt templates and produces strategy, creative, and launch artifacts.

**Current version:** v0 (local, terminal-only). v1 (cloud Routines + Google Sheets) is future scope.

---

## Canonical data location

All live data lives in `data/library/`. Do not read from `data/seed/` during normal operation — seed files are for the one-time seeding step only.

| File | Purpose |
|------|---------|
| `data/library/master.csv` | All 70+ historical ads with creative + performance + tags |
| `data/library/performance_log.csv` | Append-only monthly performance snapshots |
| `data/library/conversations.csv` | WhatsApp conversation outcomes (manually maintained) |

New performance CSVs arrive in `data/incoming/` and are processed via `/ingest perf <file>`.

---

## The six slash commands

| Command | What it does |
|---------|-------------|
| `/new_brief <course_name>` | Scaffold `data/briefs/<course>.yaml` from the template |
| `/strategy <brief_path>` | Generate strategy block + critic review → `data/strategies/<id>.md` |
| `/creative <strategy_id>` | Generate creative pack + critic review → `data/creative/<id>.md` |
| `/launch <creative_id>` | Generate launch CSV (hook validates) + critic review → `data/launches/` |
| `/ingest perf <file>` | Parse Meta CSV export → update `data/library/` |
| `/status` | Opinionated triage report on current library state |

Every generator command (`/strategy`, `/creative`, `/launch`) runs the critic as a sequential second step in the same session. The critic output is saved alongside the generator output. The operator approves, requests regeneration, or edits manually.

---

## Playbook source of truth

`data/seed/MTC_Ad_Diagnostic_v1.md` is the canonical playbook. All prompt templates lift from it verbatim. Key sections:

- **§2 Angle bank** — 19 angles with CPR data, sorted by performance
- **§3 Hook templates A–E** — proven Arabic openers, variables to swap
- **§4 Retire list** — patterns that consistently underperform
- **§5 Course track playbook** — which angle to lead with per course
- **§6 AI-driven creative loop** — weekly + monthly cadence

**Blended target:** ≤17 EGP cost per WhatsApp conversation. Best ad on record: 6.59 EGP. Worst: 80.06 EGP.

---

## Kill / scale rules

- **Kill:** spent ≥80 EGP AND CPR > 30 EGP, OR live ≥5 days → pause
- **Scale:** CPR ≤17 EGP after ≥80 EGP spend → duplicate ad set at 2× budget (never edit the original — preserves algorithm learning)
- **Fatigue signal:** CPR rises 30% above 7-day rolling average → refresh creative

Rules live in `config/kill_scale_rules.yaml`.

---

## Ad naming convention

`[date]_[course]_[angle]_[variant#]`
Example: `2026-05-12_decor_jobad_v2`

This makes weekly performance analysis self-documenting.

---

## Config files

| File | Contents |
|------|---------|
| `config/courses.yaml` | MTC course catalog with lead angles |
| `config/kill_scale_rules.yaml` | Kill/scale thresholds |
| `config/audience_definitions.yaml` | Audience segment definitions |
| `config/seasonal_calendar.yaml` | Ramadan/Eid avoid windows, summer push periods |

---

## Hooks

`.claude/hooks/pre_csv_write.py` fires on every `Write` tool call targeting `data/launches/*.csv`. It validates:
- Arabic text ≤ Meta character limits
- URLs well-formed
- Required fields present
- Campaign objective = Messages or Conversions (never Post Engagement)
- Marketplace, Notifications, Profile feeds = 0

If validation fails, the write is blocked and the operator sees a specific error message.

---

## Anti-patterns (never do these)

- Don't generate actual MTC ad copy during build. The system does that at runtime.
- Don't fabricate course details — extract from `MTC_Ad_Diagnostic_v1.md`.
- Don't reach for MCP, Google Sheets, email, or cloud Routines — that's v1.
- Don't make `/status` a data dump. Every ad gets a specific recommended action with reasoning traced to the diagnostic.
- Don't skip UTF-16 LE detection in `ingest_perf.py` — Meta exports are UTF-16 LE tab-delimited despite the `.csv` extension.
- Don't edit winning ads in place — duplicate the ad set to scale.

---

## File structure

```
data/
  seed/          ← one-time reference only
  library/       ← canonical live state (read this)
  incoming/      ← operator drops files here
  briefs/        ← course brief YAMLs
  strategies/    ← generated strategy outputs
  creative/      ← generated creative packs
  launches/      ← generated launch CSVs
prompts/         ← persona prompt templates
config/          ← YAML playbook config
scripts/         ← Python data scripts
.claude/
  commands/      ← slash command definitions
  hooks/         ← pre-write validation
```
