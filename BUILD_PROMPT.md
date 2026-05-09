# Claude Code Mission Brief: MTC Ads Engine v1 (CC-Native)

You are building an AI-driven, multi-channel ad operations system for a single-operator engineering training business (MTC, Cairo). The owner currently runs Meta ads at a blended ~17 EGP per WhatsApp conversation. This system will (a) systematize what's working, (b) add Google Search Ads as a second channel, (c) close the loop from ad-clicked to course-paid via daily automated triage and weekly retrospective.

The system takes a **course brief** as input (e.g. *3DS Max, 1500 EGP, 4 weeks, intermediate, decor students + working pros*) and produces, on demand:

1. A **strategy block** — audience, angles, channel split, budget
2. A **creative pack** — hooks, body copy, image briefs, video scripts, landing page copy
3. A **launch spec** — Meta + Google Ads bulk-paste CSV (no platform write APIs)

…and continuously:

4. **Daily triage** — reads yesterday's performance, applies kill/scale rules, proposes variants, emails operator a one-page summary
5. **Weekly review** — patterns over 7 days, library updates, drafts next week's brief

**Architectural principle:** Claude Code-native. Each automated stage runs as a **Claude Code Routine** on Anthropic's cloud infrastructure, billed against the operator's Max plan. Data lives in Google Sheets via MCP. No n8n, no separate Anthropic API account, no Docker. The system "learns" via retrieval over a structured library, not model fine-tuning.

> **Why this architecture:** the operator already pays for a Claude Max plan. Routines run on that plan rather than on the pay-as-you-go API, so the daily/weekly automation costs nothing on top of what's already being paid. n8n was the right answer six months ago; Routines have made it unnecessary for this specific use case.
>
> **Honest caveat:** Claude Code Routines is in research preview. Anthropic has stated behavior, limits, and the API surface may change. Build accordingly — keep the system simple enough to migrate to a different orchestrator if Routines is restructured.

---

## Operating mode

1. **Enter plan mode first.** Read this brief, read all seed data (especially `MTC_Ad_Diagnostic_v2.md` — read it in full before anything else), then produce a phased build plan with acceptance criteria. Wait for explicit user approval before executing.
2. **Ask before any destructive action.** Don't `git push --force`, don't drop sheets, don't delete files outside the project root.
3. **Ask before assuming any path or credential.** If a seed file isn't where you expect, ask. If MCP servers aren't connected, ask.
4. **Commit to Git after every phase.** GitHub private repo, atomic per-phase commits, sensible messages, never commit secrets.
5. **Maintain `PROGRESS.md`** with phase completion status and open questions.
6. **Maintain `DECISIONS.md`** documenting any architectural choice you made and why — especially anywhere you depart from this brief.
7. **Update `WALKTHROUGH.md`** as you go — operator-facing guide for setting up external services and running the system day-to-day.

---

## Tech stack (fixed — do not change without asking)

| Layer | Choice |
|---|---|
| Orchestration | **Claude Code Routines** (cloud-hosted, on the operator's Max plan). Five routines total — see §"The five Routines" |
| Repo execution | Routines clone this GitHub repo at the start of every run |
| Data store | **Google Sheets** accessed via the Google Sheets MCP server |
| File ingest | **Google Drive** folders for incoming CSV exports, accessed via Google Drive MCP |
| Notifications | **Gmail** via Gmail MCP server |
| Project memory | `CLAUDE.md` at repo root + per-routine prompt files in `prompts/` |
| Validation | **Claude Code hooks** (`PreToolUse` for Arabic char counts and URL format checks before writing launch CSVs; `PostToolUse` for auto-commits) |
| Ad performance ingest | **Manual CSV export** from Ads Manager dropped into a Google Drive folder (no Meta or Google Ads API write/read access) |
| Launch output | CSV ready to bulk-paste into Meta Ads Manager + Google Ads Editor |
| WhatsApp logging | **Google Form** filled by operator's team after each chat → Form responses sheet |
| Languages | Python for orchestration scripts and CLI tools; markdown for prompts |
| Models | Default to whatever Claude Code chooses on Max (currently Opus 4.7). For one-time bulk tagging of historical data during seeding, use Haiku 4.5 via interactive Claude Code session if usage limits become an issue |
| Version control | GitHub private repo, first commit on initial scaffold |

**v1 explicitly excludes:** Whisper / voice transcription, image generation API, Agent Teams (the pipeline is sequential — no parallel work to coordinate), languages beyond Arabic + English, custom dashboards beyond Sheets views.

**v1 explicitly INCLUDES a Critic step.** Each generation stage (Strategy, Creative, Launch) is followed by a sequential critic prompt run in the same routine session — same model, different persona — that audits the output against `MTC_Ad_Diagnostic_v2.md`. The critic flags issues but does NOT auto-regenerate or auto-block; its review is emailed to the operator alongside the generated output, so the operator approves, requests regeneration, or fixes manually with full visibility. This is "personas as prompts" with two personas in sequence — not Agent Teams, not multi-agent peer-to-peer. AI generators get lazy and hallucinate; the critic catches it before it reaches operator approval, where it would otherwise burn budget downstream.

---

## Existing data the operator provides

Expect these files in `./data/seed/` at the start of the build. **If any are missing, stop and ask the operator for the path** — do not proceed without them. They are the foundation of the system's intelligence.

**Required:**
- `MTC_Ad_Diagnostic_v2.md` — canonical playbook. Source of truth for angle bank, hook templates, retire list, seasonal calendar, audience strategy, channel strategy, placement strategy.
- `MTC_master_ad_library_v2.csv` — 70 historical ads, joined creative + performance.
- `MTC_ads_with_full_creative_v2.csv` — 51 ads with full Egyptian Arabic body copy.
- `MTC_performance_-y_month_2017_to_now.csv` — 38 monthly time-slices, ad-level granularity.
- `MTC_-y_placement.csv`, `MTC_-y_age_gender.csv`, `MTC_-y_country.csv` — three breakdowns.

**Optional (raw exports, useful for ingest format reference):**
- `export_20260506_2324.csv` — original creative export. Note: **UTF-16 LE encoded, tab-separated despite `.csv` extension**. Your CSV ingest must detect this; silent corruption otherwise.
- `Orca-Palace-Ads-6-Apr-2023-6-May-2026.csv` — original performance export (UTF-8, comma-separated).

---

## Target repository structure

Propose this in plan mode; refine with the operator.

```
mtc-ads-engine/
├── README.md
├── WALKTHROUGH.md          # operator-facing setup + daily-use guide
├── PROGRESS.md             # build state
├── DECISIONS.md            # architectural choices
├── CLAUDE.md               # project memory loaded on every Claude Code session
├── .gitignore              # ignores .env, .DS_Store, archive/, *.local.*
├── .claude/
│   ├── settings.json       # hooks config + MCP server references
│   └── hooks/
│       ├── pre_csv_write.py    # validates Arabic char counts, URLs, required fields
│       └── post_phase.py       # auto-commit after a phase completes
├── data/
│   ├── seed/               # historical CSVs + v2 diagnostic
│   └── archive/            # locally-archived files (git-ignored)
├── prompts/
│   ├── _shared_context.md  # condensed v2 playbook prepended to every routine prompt
│   ├── strategy.md
│   ├── copywriter.md
│   ├── media_buyer.md
│   ├── critic.md           # sequential reviewer — branches by input type (strategy/creative/launch)
│   ├── triage.md
│   └── weekly_review.md
├── routines/               # MARKDOWN documentation of each Routine — the actual Routine config lives at claude.ai/code/routines
│   ├── daily_triage.md     # describes prompt, schedule, MCP servers, expected sheets
│   ├── weekly_review.md
│   ├── on_demand_strategy.md
│   ├── on_demand_creative.md
│   └── on_demand_launch.md
├── config/
│   ├── courses.yaml        # MTC course catalog (extract from v2)
│   ├── kill_scale_rules.yaml
│   ├── audience_definitions.yaml
│   ├── seasonal_calendar.yaml  # budget multipliers from v2
│   └── sheets_schema.yaml  # canonical schema for every Google Sheet the system uses
├── scripts/
│   ├── seed_library.py     # one-time bulk load to Google Sheets (run interactively)
│   ├── ingest_csv.py       # parse manual exports (handle UTF-16 LE!)
│   ├── tag_ads.py          # tag historical ads (run interactively, uses Claude Code session)
│   └── validate_brief.py   # YAML schema check before strategy run
├── briefs/                 # course brief YAMLs, one per course launch
│   └── _template.yaml      # blank template the operator copies and fills
└── tests/
    ├── fixtures/           # sample brief, sample CSV
    └── smoke_test.md       # end-to-end test plan with dummy course
```

---

## The five persona prompts

Each prompt = a markdown file in `prompts/`. Each is prepended at runtime with `_shared_context.md` (condensed v2 playbook).

**Critical:** do not write playbook content from scratch. Lift the angle bank, hook templates, retire list, seasonal calendar, audience strategy, placement strategy, and verbatim Arabic examples directly from `MTC_Ad_Diagnostic_v2.md`. Your job is to reformat them into role-specific prompt structure, not to invent strategy.

| File | Persona | Input | Output |
|---|---|---|---|
| `strategy.md` | Senior performance marketing strategist who has internalized v2 | Course brief YAML | Strategy block: audience, primary 2 angles, channel split, budget recommendation, week-1 schedule, pre-flight QA checklist |
| `copywriter.md` | Egyptian Arabic direct-response copywriter who knows v2's hook templates and retire list | Approved strategy | 6 hooks per angle, body copy paired with each, 12 image briefs (specs detailed enough for human image generation), 4 vertical video scripts (15s + 30s), landing page copy in Arabic + English |
| `media_buyer.md` | Meta + Google Ads media buyer with awareness of bulk-paste CSV constraints | Approved creative + image links | Launch CSV: one row per ad with campaign / ad set / ad name (per naming convention) / audience / placement / budget / schedule / copy / image / CTA / URL. **Pre-flight validation against Meta's character limits, Arabic counting rules, URL format, audience-placement compatibility — enforced via the `PreToolUse` hook on `pre_csv_write.py`** |
| `critic.md` | Skeptical performance marketing reviewer who has internalized v2 and treats every generated artifact as suspect until verified | Strategy / Creative / Launch CSV from a generator stage | Structured review: pass/fail per check (with specific section of v2 cited for each), severity (blocker / warning / nit), suggested fix. Stage-specific check lists baked into the prompt — see "Critic checks" below |
| `triage.md` | Daily paid-social analyst | Yesterday's performance + 7-day rolling + library state | Pause list, scale list, variant briefs for winners, three-line email summary. Applies `kill_scale_rules.yaml` |
| `weekly_review.md` | Weekly retrospective analyst | 7 days of performance + WhatsApp Form responses + library deltas | One-page summary, three patterns (winners/losers/surprises), tag suggestions, 2–3 hypotheses for next week, draft brief for next week's launch |

All prompts in markdown so the operator can read and refine them. Each routine logs which prompt version it ran in a "Routine Runs" sheet, so the operator can correlate output quality with prompt changes.

### Critic checks per stage

The `critic.md` prompt branches on input type. Each branch has a specific check list, every item traceable to a section of `MTC_Ad_Diagnostic_v2.md`.

**Strategy critic checks:**
- All proposed angles appear in v2's angle bank? Any from the retire list?
- Channel split aligned with v2 placement findings (Reels-first, Marketplace=0)?
- Budget recommendation consistent with `seasonal_calendar.yaml` for the launch month?
- Target audience supported by v2's demographic findings (note tiny-sample asymmetric bets like 35–54 women if relevant)?
- Pre-flight QA checklist actually addresses platform constraints, not generic advice?

**Creative critic checks:**
- Every hook follows one of templates A–E from v2 §3? Or explicitly justified as a new template?
- Any retire-list patterns (greeting-led, philosophical, English-only opener, wall-of-text)?
- First 6 words of each hook name the audience segment?
- Body copy under Meta's truncation point with the offer in the visible portion?
- Image briefs specify mobile-vertical aspect ratio and Arabic on-image text?
- Video scripts deliver the hook in the first 0–3 seconds (per v2 §6)?
- Egyptian Arabic dialect register matches the proven examples (not MSA, not over-formal)?
- Landing page copy bilingual (Arabic + English) and aligned with the chosen angle?

**Launch CSV critic checks (light — pre-write hook covers technical):**
- Campaign objective is Messages or Conversions, not Post Engagement?
- Placement allocation skews Reels-first per v2 §3?
- Naming convention applied consistently? Audience definitions reference `audience_definitions.yaml`?
- Are Marketplace, Notifications, Profile feeds zeroed out per v2 §1.7?

The critic outputs a structured markdown review with three sections: ✅ Passing, ⚠️ Warnings, 🛑 Blockers. The operator email receives the generator's output AND the critic review side-by-side. Operator decides whether to approve, request regeneration, or edit manually. **The critic does not auto-block or auto-regenerate in v1** — the operator stays in the loop with full visibility.

---

## The five Routines

These get configured at `claude.ai/code/routines` (or via the desktop app or `/schedule` CLI). The Routine *config* lives in Anthropic's cloud, not this repo. The repo holds (a) the prompt each Routine calls, (b) markdown documentation in `routines/` describing what each does, (c) the scripts each invokes.

Each Routine is configured with: this GitHub repo, the relevant MCP connectors (Google Sheets, Gmail, Drive), the bearer token (auto-generated for API-triggered routines), and a top-level prompt that says roughly *"Read prompts/<role>.md and execute the workflow defined there using the connected sheets and Drive folders."*

| # | Routine | Trigger | Top-level workflow |
|---|---|---|---|
| 1 | **Daily Triage** | Scheduled, 07:00 daily | (a) List new files in Drive folder "MTC/Incoming/Performance" via Drive MCP. (b) Run `scripts/ingest_csv.py` on each. (c) Read master library + last 7 days. (d) Execute `prompts/triage.md`. (e) Write decisions to "Decisions Awaiting Approval" sheet. (f) Send summary email via Gmail MCP. |
| 2 | **Weekly Review** | Scheduled, Sunday 18:00 | Read 7 days perf + Form responses. Execute `prompts/weekly_review.md`. Update library tags. Draft next week's brief into "Next Week Brief" sheet. Email brief. |
| 3 | **On-Demand Strategy** | API-triggered (curl with course brief YAML in payload) | Validate brief via `scripts/validate_brief.py`. Execute `prompts/strategy.md`. **Then execute `prompts/critic.md` (strategy branch) on the output.** Write strategy + critic review to "Strategies" sheet (two columns). Email operator for approval with both side-by-side. |
| 4 | **On-Demand Creative** | API-triggered (curl with strategy ID in payload, after operator marks strategy "approved") | Read approved strategy. Execute `prompts/copywriter.md`. **Then execute `prompts/critic.md` (creative branch) on the output.** Write pack + critic review to "Creative" sheet. Email operator for approval with both side-by-side. |
| 5 | **On-Demand Launch** | API-triggered (curl with creative ID, after operator approves and adds image links) | Read approved creative + image links. Execute `prompts/media_buyer.md`. Hook validates the launch CSV before write (technical constraints). **Then execute `prompts/critic.md` (launch branch) on the CSV** (strategic constraints — objective, placement mix, etc.). Email operator with CSV attachment + critic review. |

**Daily routine usage budget:** Max plan caps at 15 routine *runs*/day. Each on-demand routine run includes a generator + critic in a single Claude Code session — that's two prompts but one routine run. Expected usage: 1 (daily triage) + ~0.14 (weekly review averaged) + 3–6 (on-demand during launch sprint) = well under cap. The critic doesn't add routine runs, only adds tokens within a single run.

For the API-triggered routines, the operator gets a per-routine HTTPS endpoint + bearer token. Provide a tiny `mtc` shell script in `scripts/` that wraps these calls so the operator's day-to-day looks like:

```
mtc strategy briefs/3dsmax.yaml
mtc creative <strategy_id>
mtc launch <creative_id>
```

Each command POSTs to the appropriate routine endpoint with the right payload.

---

## Phased build plan (propose in plan mode)

| Phase | Output | Acceptance criteria |
|---|---|---|
| 0 — Foundation | Repo, `.gitignore`, GitHub remote, `CLAUDE.md` skeleton, README | Repo initialized with first commit pushed; operator confirms remote |
| 1 — MCP setup | Operator-facing instructions in `WALKTHROUGH.md` for connecting Google Sheets, Drive, Gmail MCPs to Claude Code | Operator runs through the steps and confirms each MCP server responds |
| 2 — Sheets schema | `config/sheets_schema.yaml` defining every sheet (master library, decisions, strategies, creative, briefs, runs log) + a `scripts/init_sheets.py` to create them | Sheets exist with correct columns; operator can see them |
| 3 — Data seeding | `scripts/seed_library.py` (run interactively in Claude Code) loads all historical CSVs + tags them via `scripts/tag_ads.py` | Master library has 70 rows from v2, every row tagged with angle/hook/course; counts match v2 |
| 4 — Configuration | `courses.yaml`, `kill_scale_rules.yaml`, `audience_definitions.yaml`, `seasonal_calendar.yaml` | Each YAML traceable back to v2 (cite section in comments) |
| 5 — Prompt templates | All six persona prompts in `prompts/` (`_shared_context.md`, `strategy.md`, `copywriter.md`, `media_buyer.md`, `critic.md`, `triage.md`, `weekly_review.md`) | Operator reads each before approval; one-line summary of each in `DECISIONS.md`. Critic prompt branches cleanly by input type (strategy / creative / launch) with specific check lists each citing the relevant v2 section |
| 6 — Hooks | `.claude/settings.json` + `pre_csv_write.py` and `post_phase.py` | Hooks fire correctly on local Claude Code; pre-write hook catches a deliberately-bad test launch CSV |
| 7 — CSV ingest script | `scripts/ingest_csv.py` handling UTF-16 LE + UTF-8 + tab-separated + comma-separated; pulls from Drive folder | Test with operator's actual recent export; row counts + spend totals match Ads Manager |
| 8 — Routines configuration | `routines/*.md` documenting each Routine; step-by-step `WALKTHROUGH.md` instructions for setting them up at claude.ai/code/routines | Operator successfully creates all 5 routines; each smoke-tests with dummy input |
| 9 — `mtc` CLI wrapper | `scripts/mtc` shell script for triggering API routines + secret management for bearer tokens | Operator runs `mtc strategy briefs/_template.yaml` and gets a strategy emailed back |
| 10 — WhatsApp logging | Google Form schema + creation steps in `WALKTHROUGH.md`; weekly review reads Form responses sheet | Operator creates form, response appears in sheet, weekly review smoke test reads it |
| 11 — End-to-end smoke test | `tests/fixtures/test_brief_3dsmax.yaml` + `tests/smoke_test.md` runbook | Brief → strategy → creative → launch CSV completes in under 15 minutes; CSV passes Meta-format validation |
| 12 — Walkthrough finalization | Complete `WALKTHROUGH.md` covering every external setup step | A hypothetical fresh operator could go from zero to running system in under 4 hours following the guide |

Tag the repo `v0.1.0` after Phase 12.

---

## Definition of done (v1)

The build is done when the operator can:

1. Run `mtc strategy briefs/<course>.yaml` and within ~5 minutes have a strategy block emailed
2. Mark the strategy "approved" in the sheet, run `mtc creative <id>`, and within ~5 minutes have a full creative pack emailed
3. Add image links to the creative sheet, run `mtc launch <id>`, and within ~3 minutes have a launch CSV ready to bulk-paste into Meta + Google
4. Drop a manual CSV export of yesterday's performance into the Drive folder; the next morning's email contains the daily triage with kill/scale recommendations
5. Receive a weekly review email every Sunday evening with patterns + draft brief for next week
6. See the master library in Google Sheets growing with every new ad — tagged, joined to performance, joined to conversation outcomes from the WhatsApp Form

The walkthrough is done when a hypothetical fresh operator could clone the repo, follow `WALKTHROUGH.md`, and have the system running end-to-end in under 4 hours.

---

## Anti-patterns to avoid

- Don't generate MTC's actual ad copy during the build. The system does that *when running*, not at build time.
- Don't fabricate course catalog details. Extract from v2 data; ask if unclear.
- Don't write your own playbook content. Use v2 verbatim where possible.
- Don't ship a system that requires the operator to maintain custom code. Configuration over code wherever possible.
- Don't hide secrets in the repo. Bearer tokens for routines go in `.env.local` (gitignored) or in the operator's shell environment.
- Don't import n8n / Zapier / Make patterns. CC-native.
- Don't use Agent Teams. The pipeline is sequential — there's nothing to parallelize. The critic is a sequential second prompt within the same routine, NOT a peer-to-peer agent.
- Don't extend scope to image-gen API. Out of scope for v1.
- Don't push to GitHub before the operator confirms the remote URL.
- Don't skip the UTF-16 LE detection in `ingest_csv.py`. Recent Meta exports are UTF-16 LE with tabs masquerading as `.csv` — silent data corruption otherwise.
- Don't write Routine prompts that depend on conversation state from prior runs. Each routine run is a fresh Claude Code session with no memory of previous ones — state lives in Google Sheets, files in the repo, or `CLAUDE.md`.

---

## When to stop and ask the operator

- Before the first commit: confirm the GitHub remote URL.
- If any seed file is missing or in an unexpected location.
- If MCP servers (Sheets, Drive, Gmail) aren't yet authorized.
- If you find a pattern in v2 that's ambiguous and could be interpreted multiple ways. Don't guess.
- Before deleting any file outside the project root, ever.
- Before declaring a phase done: surface what was built and request sign-off.
- If a Meta or Google constraint encoded in `media_buyer.md` would meaningfully restrict the operator (e.g. "this CTA isn't supported for Messages campaigns").
- Before configuring any Routine: walk the operator through the trade-offs of scheduled vs API-triggered for that step.

---

## How to start

1. Read every file in `./data/seed/`. Read `MTC_Ad_Diagnostic_v2.md` in full before doing anything else — that document is your source of truth for the entire system's intelligence.
2. Verify the local environment is feasible: `node --version`, `python3 --version`, `git --version`, and confirm Claude Code is logged in to a Max plan account (`/status`).
3. Verify the operator has connected (or knows how to connect) the Google Sheets, Google Drive, and Gmail MCP servers. If not, your first walkthrough section is helping them connect these.
4. Produce the build plan in plan mode: phases, acceptance criteria, estimated time, and any clarifying questions.
5. Wait for plan approval.
6. Execute phase by phase. Commit at each phase boundary. Ask when uncertain. Update `PROGRESS.md` as you go.