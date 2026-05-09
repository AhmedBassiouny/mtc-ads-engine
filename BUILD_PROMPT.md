# Claude Code Mission Brief: MTC Ads Engine v0 (Manual / Command-Driven)

You are building the **manual, command-driven version** of an AI-driven multi-channel ad operations system for a single-operator engineering training business (MTC, Cairo). This is **v0** — the prove-it-works-first release. v1 (cloud Routines, automated triage, scheduled email reports) exists as a separate brief and will come later. v0's purpose: validate every prompt and every script in real use, with the operator manually triggering each step, before adding orchestration.

The system takes a **course brief** as input (e.g. *3DS Max, 1500 EGP, 4 weeks, intermediate, decor students + working pros*) and produces, on demand:

1. A **strategy block** — audience, angles, channel split, budget
2. A **creative pack** — hooks, body copy, image briefs, video scripts, landing page copy
3. A **launch spec** — Meta + Google Ads bulk-paste CSV (no platform write APIs)
4. A **status report** — current state of all running ads + AI-recommended next action per ad, on demand

**Architectural principle for v0:** Claude Code slash commands. Each operator action — generate strategy, ingest a CSV, request the status report — is a slash command (`/strategy`, `/ingest`, `/status`) whose body is a markdown prompt in `.claude/commands/`. No cloud orchestration, no email, no Sheets, no MCP. Operator runs `claude` in the project folder and types commands. All data lives in local CSVs in the repo. When v0 graduates to v1, each slash command becomes the body of a Routine — the migration is mostly mechanical because the prompts, scripts, and data model carry over unchanged.

> **Why v0 first:** the system has six prompts, multiple stages, manual CSV ingest, WhatsApp logging, the critic, hooks. Building all of that AND wrapping it in cloud Routines simultaneously is too many points of failure across too many layers. v0 forces the operator to see every output, catch every weird edge case, refine every prompt, before automating the wrongness.

---

## Operating mode

1. **Enter plan mode first.** Read this brief, read all seed data (especially `MTC_Ad_Diagnostic_v2.md` — read it in full before anything else), then produce a phased build plan with acceptance criteria. Wait for explicit user approval before executing.
2. **Ask before any destructive action.** Don't `git push --force`, don't delete files outside the project root.
3. **Ask before assuming any path.** If a seed file isn't where you expect, ask.
4. **Commit to Git after every phase.** GitHub private repo, atomic per-phase commits, sensible messages, never commit secrets.
5. **Maintain `PROGRESS.md`** with phase completion status and open questions.
6. **Maintain `DECISIONS.md`** documenting any architectural choice you made and why — especially anywhere you depart from this brief.
7. **Update `WALKTHROUGH.md`** as you go — operator-facing guide.

---

## Tech stack (fixed — do not change without asking)

| Layer | Choice |
|---|---|
| Orchestration | **Claude Code slash commands** (`.claude/commands/*.md`) — operator invokes everything manually |
| Project memory | `CLAUDE.md` at repo root, loaded on every session |
| Data store | **Local CSVs** in `data/library/` + YAML briefs in `data/briefs/` + generated artifacts in `data/strategies/`, `data/creative/`, `data/launches/` |
| Validation | Claude Code hooks (`PreToolUse` for Arabic char counts and URL format checks before writing launch CSVs; `PostToolUse` for git commits when artifacts are produced) |
| Ad performance ingest | Manual CSV export from Ads Manager dropped into `data/incoming/`, processed by `/ingest perf <file>` |
| Launch output | CSV ready to bulk-paste into Meta Ads Manager + Google Ads Editor |
| WhatsApp logging | `data/library/conversations.csv` — operator (or staff) appends one row per conversation manually. No Form, no Sheets in v0 |
| Languages | Python for orchestration scripts; markdown for prompts and slash commands |
| Models | Whatever Claude Code uses on the operator's Max plan (currently Opus 4.7) |
| Version control | GitHub private repo, first commit on initial scaffold |

**v0 explicitly excludes:** cloud Routines, email notifications, Google Sheets, MCP servers, Whisper / voice transcription, image generation API, Agent Teams, scheduled execution, languages beyond Arabic + English.

**v0 explicitly INCLUDES the Critic.** Each generation command (`/strategy`, `/creative`, `/launch`) runs the generator prompt, then runs `prompts/critic.md` on the output as a sequential second pass — same Claude session, different persona — and returns both side-by-side. Critic flags issues but does not auto-block or auto-regenerate; operator decides whether to approve, regenerate, or fix manually. This is "personas as prompts" — not Agent Teams.

---

## Existing data the operator provides

Expect these files in `./data/seed/` at the start of the build. **If any are missing, stop and ask the operator** — do not proceed without them.

**Required:**
- `MTC_Ad_Diagnostic_v2.md` — canonical playbook. Source of truth for angle bank, hook templates, retire list, seasonal calendar, audience strategy, channel strategy, placement strategy.
- `MTC_master_ad_library_v2.csv` — 70 historical ads with creative + performance joined. The `Body` column contains Egyptian Arabic body copy for the 51 ads where it could be recovered; the other 19 are 2025–2026 ads where Meta gates body text behind the Marketing API. Filter by `Body IS NOT NULL` whenever you need the creative-text-bearing subset.
- `MTC_performance_-y_month_2017_to_now.csv` — 38 monthly time-slices, ad-level granularity.
- `MTC_-y_placement.csv`, `MTC_-y_age_gender.csv`, `MTC_-y_country.csv` — three breakdowns.

**Optional (raw exports, useful for ingest format reference):**
- `export_20260506_2324.csv` — original creative export. **UTF-16 LE encoded, tab-separated despite `.csv` extension.** Your CSV ingest must detect this; silent corruption otherwise.
- `Orca-Palace-Ads-6-Apr-2023-6-May-2026.csv` — original performance export (UTF-8, comma-separated).

---

## Target repository structure

```
mtc-ads-engine/
├── README.md
├── WALKTHROUGH.md
├── PROGRESS.md
├── DECISIONS.md
├── CLAUDE.md                       # loaded on every Claude Code session
├── .gitignore                      # ignores data/incoming/, data/archive/, .DS_Store
├── .claude/
│   ├── settings.json               # hooks config
│   ├── commands/                   # SLASH COMMANDS — operator-facing
│   │   ├── new_brief.md            # /new_brief <course_name> — scaffolds a brief YAML
│   │   ├── strategy.md             # /strategy <brief_path>
│   │   ├── creative.md             # /creative <strategy_id>
│   │   ├── launch.md               # /launch <creative_id>
│   │   ├── ingest.md               # /ingest perf|whatsapp <file>
│   │   └── status.md               # /status — the single report
│   └── hooks/
│       └── pre_csv_write.py
├── data/
│   ├── seed/                       # historical CSVs + v2 diagnostic
│   ├── library/                    # canonical state (the system reads from here)
│   │   ├── master.csv              # all ads ever, with creative + tags + lifetime perf
│   │   ├── performance_log.csv     # daily perf snapshots, append-only
│   │   └── conversations.csv       # WhatsApp conversation logs, manually maintained
│   ├── incoming/                   # operator drops files here, /ingest processes them
│   │   └── .gitkeep
│   ├── archive/                    # processed inputs (gitignored)
│   ├── briefs/                     # course briefs (YAML), one per launch
│   │   └── _template.yaml
│   ├── strategies/                 # generated strategy outputs (markdown)
│   ├── creative/                   # generated creative packs (markdown)
│   └── launches/                   # generated launch CSVs
├── prompts/
│   ├── _shared_context.md          # condensed v2 playbook prepended to every command
│   ├── strategy.md
│   ├── copywriter.md
│   ├── media_buyer.md
│   ├── critic.md                   # branches by input type (strategy/creative/launch)
│   └── triage.md                   # used by /status
├── config/
│   ├── courses.yaml                # MTC course catalog (extract from v2)
│   ├── kill_scale_rules.yaml
│   ├── audience_definitions.yaml
│   └── seasonal_calendar.yaml
├── scripts/
│   ├── seed_library.py             # one-time bulk load seed CSVs into data/library/
│   ├── ingest_perf.py              # parse manual perf exports (UTF-16 LE!)
│   ├── ingest_whatsapp.py          # parse WhatsApp text exports if operator drops one
│   ├── tag_ads.py                  # tag historical ads
│   ├── validate_brief.py           # YAML schema check
│   └── library_query.py            # helper that loads + joins library/perf/conversations for /status
└── tests/
    ├── fixtures/                   # sample brief, sample CSV
    └── smoke_test.md               # end-to-end test plan
```

---

## The six slash commands

Each command lives at `.claude/commands/<name>.md`. The body is a markdown prompt that Claude Code runs in the operator's session when they type `/<name> <args>`. Each command @-references the relevant prompt and data files so all context loads automatically.

| Command | Purpose | Output |
|---|---|---|
| `/new_brief <course_name>` | Scaffold `data/briefs/<course_name>.yaml` from `_template.yaml` | New YAML file the operator fills in |
| `/strategy <brief_path>` | Run `prompts/strategy.md` on the brief, then `prompts/critic.md` on the output | Markdown file in `data/strategies/<id>.md` containing strategy + critic review side-by-side; operator reads it in the terminal |
| `/creative <strategy_id>` | Run `prompts/copywriter.md` on the approved strategy, then `prompts/critic.md` on the output | Markdown file in `data/creative/<id>.md` with creative pack + critic review |
| `/launch <creative_id>` | Run `prompts/media_buyer.md` on the approved creative + image links. PreToolUse hook validates the CSV. Then run `prompts/critic.md` (launch branch) on the CSV | CSV file in `data/launches/<id>.csv` ready to bulk-paste, plus a sibling `<id>.review.md` with critic notes |
| `/ingest perf <file>` | Run `scripts/ingest_perf.py` on the file → append to `data/library/performance_log.csv`. Update `data/library/master.csv` with any new ad rows | Confirmation message: rows added, total spend processed, anomalies flagged |
| `/status` | Run the single status report — see next section | Markdown report streamed to the terminal |

---

## The single `/status` report

This is v0's main analytical surface. The operator types `/status` after dropping a fresh perf CSV (or any time) and gets back the canonical "where do my ads stand and what should I do?" view.

The slash command body @-references `data/library/master.csv`, `data/library/performance_log.csv`, `data/library/conversations.csv`, `prompts/_shared_context.md`, `prompts/triage.md`, and `config/kill_scale_rules.yaml`. Then runs the triage prompt against current state.

Report structure (markdown, in the terminal):

```
# MTC Ads Status — <date>

## Portfolio summary (last 7 days)
- Active ads: X
- Spend: X EGP (vs target)
- Conversations: X
- Blended CPR: X EGP (vs target)
- Conversation → deposit rate: X% (if data available)

## Action required (ordered by urgency)

🛑 PAUSE — <ad_name>
   Reasoning: <why> (cite specific metric movements + v2 section)
   Action: <what to do>

⚠️ WATCH — <ad_name>
   Reasoning: <why>
   Action: <what to monitor, when to reassess>

✅ SCALE — <ad_name>
   Reasoning: <why>
   Action: <how to scale, by how much>

[... per active ad ...]

## Patterns this week
- <one-line observation 1, traceable to data>
- <one-line observation 2>
- <one-line observation 3>

## Conversion insights (if conversations.csv has recent data)
- Top objection: X (count)
- Highest-converting angle this week: X (Y% deposit rate)
- Lowest-converting: X
- Notable signal: X

## Suggested next tests (2–3, not more)
1. <hypothesis + which angle/audience to test>
2. <hypothesis>
```

The report must be opinionated. Generic data dumps like "here are all the metrics" are a failure mode — the operator can read a CSV. Triage value comes from a specific recommendation per ad with reasoning that ties to the playbook.

---

## The six persona prompts

Same as v1 — see `MTC_Ad_Diagnostic_v2.md` for source content.

| File | Persona | Used by |
|---|---|---|
| `_shared_context.md` | (Not a persona — condensed v2 playbook prepended to every prompt) | All commands |
| `strategy.md` | Senior performance marketing strategist who has internalized v2 | `/strategy` |
| `copywriter.md` | Egyptian Arabic direct-response copywriter, knows v2's hook templates and retire list | `/creative` |
| `media_buyer.md` | Meta + Google Ads media buyer aware of bulk-paste CSV constraints | `/launch` |
| `critic.md` | Skeptical reviewer; branches by input type (strategy/creative/launch) with stage-specific check lists, every check citing a v2 section | `/strategy`, `/creative`, `/launch` (after the generator) |
| `triage.md` | Daily paid-social analyst that produces the `/status` report | `/status` |

**Critical:** do not write playbook content from scratch. Lift the angle bank, hook templates, retire list, seasonal calendar, audience strategy, placement strategy, and verbatim Arabic examples directly from `MTC_Ad_Diagnostic_v2.md`. Your job is to reformat them into role-specific prompt structure, not to invent strategy.

---

## Critic checks per stage

The `critic.md` prompt branches on input type. Each branch has a specific check list, every item traceable to a section of `MTC_Ad_Diagnostic_v2.md`.

**Strategy critic:** angles in v2's angle bank? Any retire-list angles? Channel split aligned with v2 placement findings (Reels-first, Marketplace=0)? Budget consistent with `seasonal_calendar.yaml` for the launch month? Audience supported by v2's demographic findings?

**Creative critic:** every hook follows templates A–E from v2 §3 or explicitly justified? Any retire-list patterns (greeting-led, philosophical, English-only opener, wall-of-text)? First 6 words of each hook name the audience segment? Body copy under Meta's truncation point with offer in the visible portion? Image briefs specify mobile-vertical + Arabic on-image text? Video scripts deliver the hook in 0–3s? Egyptian dialect register matches proven examples?

**Launch CSV critic (light — pre-write hook covers technical):** campaign objective Messages or Conversions, not Post Engagement? Placement allocation Reels-first per v2 §3? Naming convention applied? Marketplace, Notifications, Profile feeds zeroed out per v2 §1.7?

Output: structured markdown with three sections: ✅ Passing, ⚠️ Warnings, 🛑 Blockers. Operator reads it alongside the generated artifact and decides.

---

## Phased build plan (propose in plan mode)

| Phase | Output | Acceptance criteria |
|---|---|---|
| 0 — Foundation | Repo, `.gitignore`, GitHub remote, `CLAUDE.md`, README | Repo initialized with first commit pushed; operator confirms remote |
| 1 — Data seeding | `scripts/seed_library.py` loads seed CSVs into `data/library/`; `scripts/tag_ads.py` tags historical ads via interactive Claude Code session | `data/library/master.csv` has 70 rows from v2, every row tagged with angle/hook/course; counts match v2 |
| 2 — Configuration | `courses.yaml`, `kill_scale_rules.yaml`, `audience_definitions.yaml`, `seasonal_calendar.yaml`, `briefs/_template.yaml` | Each YAML traceable back to v2 (cite section in comments) |
| 3 — Prompt templates | All six prompt files in `prompts/` | Operator reads each before approval; one-line summary in `DECISIONS.md` |
| 4 — Hooks | `.claude/settings.json` + `pre_csv_write.py` + post-write commit hook | Pre-write hook catches a deliberately-bad test launch CSV (over-length Arabic, malformed URL); operator confirms |
| 5 — Slash commands | All six commands in `.claude/commands/` | Each command runs end-to-end with a fixture input |
| 6 — Ingest scripts | `ingest_perf.py` (UTF-16 LE + UTF-8 + tab/comma), `ingest_whatsapp.py`, `validate_brief.py` | `/ingest perf` on the operator's actual recent export — row count + spend total match Ads Manager |
| 7 — Status report tuning | `/status` produces the report on real data | Operator reviews the output; we iterate the triage prompt until the recommendations are decisive and traceable to v2 |
| 8 — End-to-end smoke test | `tests/fixtures/test_brief_3dsmax.yaml` + `tests/smoke_test.md` runbook | Brief → strategy → creative → launch CSV completes; `/status` produces a coherent report |
| 9 — Walkthrough finalization | Complete `WALKTHROUGH.md` | A hypothetical fresh operator could clone the repo, follow the guide, and run all six commands in under 2 hours |

Tag the repo `v0.1.0` after Phase 9.

---

## Definition of done (v0)

The build is done when the operator can:

1. Run `/new_brief 3dsmax` to scaffold a brief, fill it in
2. Run `/strategy data/briefs/3dsmax.yaml` and within ~3 minutes see the strategy + critic review streamed to the terminal and saved to `data/strategies/`
3. Approve the strategy (just by referencing its ID), run `/creative <id>`, and within ~5 minutes see the creative pack + critic review
4. Add image links to the creative file, run `/launch <id>`, and within ~2 minutes get a launch CSV in `data/launches/` ready to bulk-paste — pre-write hook having validated character counts, URLs, and required fields
5. Drop a manual CSV export of yesterday's performance into `data/incoming/`, run `/ingest perf <file>`, and see the master library updated
6. Run `/status` at any time and get a coherent, opinionated report with per-ad recommendations and 2–3 next-test suggestions

---

## Anti-patterns to avoid

- Don't generate MTC's actual ad copy during the build. The system does that when running, not at build time.
- Don't fabricate course catalog details. Extract from v2 data; ask if unclear.
- Don't write playbook content from scratch. Use v2 verbatim where possible.
- Don't ship a system that requires the operator to maintain custom code. Configuration over code wherever possible.
- Don't hide secrets in the repo.
- Don't reach for cloud Routines, email, MCP, or Sheets — those are v1, not v0.
- Don't use Agent Teams. The pipeline is sequential. The critic is a sequential second prompt within the same command, NOT peer-to-peer.
- Don't push to GitHub before the operator confirms the remote URL.
- Don't skip UTF-16 LE detection in `ingest_perf.py`. Recent Meta exports are UTF-16 LE with tabs masquerading as `.csv` — silent data corruption otherwise.
- Don't make `/status` a generic data dump. It must be opinionated, with a specific action per ad and reasoning that traces to v2.

---

## When to stop and ask the operator

- Before the first commit: confirm the GitHub remote URL.
- If any seed file is missing or in an unexpected location.
- If you find a pattern in v2 that's ambiguous and could be interpreted multiple ways. Don't guess.
- Before deleting any file outside the project root, ever.
- Before declaring a phase done: surface what was built and request sign-off.
- If a Meta or Google constraint encoded in `media_buyer.md` would meaningfully restrict the operator (e.g. "this CTA isn't supported for Messages campaigns").
- If the `/status` report comes out generic or ungrounded on first run — iterate the triage prompt with the operator before tagging Phase 7 done.

---

## How to start

1. Read every file in `./data/seed/`. Read `MTC_Ad_Diagnostic_v2.md` in full before doing anything else — that document is your source of truth for the entire system's intelligence.
2. Verify the local environment: `node --version`, `python3 --version`, `git --version`, and confirm Claude Code is logged in to a Max plan account (`/status` in Claude Code, not the project's `/status`).
3. Produce the build plan in plan mode: phases, acceptance criteria, estimated time, and any clarifying questions.
4. Wait for plan approval.
5. Execute phase by phase. Commit at each phase boundary. Ask when uncertain. Update `PROGRESS.md` as you go.