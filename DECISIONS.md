# Architectural Decisions

## v0 scope: local slash commands only, no cloud

**Decision:** Build v0 as a pure Claude Code slash-command system. No cloud Routines, no Google Sheets MCP, no email automation.

**Why:** The operator needs a working system now. Cloud Routines add setup complexity (MCP auth, Routines config at claude.ai/code, bearer tokens) that delays value delivery. The slash-command architecture delivers identical intelligence in the terminal with zero external dependencies. Cloud automation is v1.

---

## Data lives in local CSV files

**Decision:** Canonical state is `data/library/*.csv`, not Google Sheets.

**Why:** Consistent with v0 scope. CSVs are readable in any editor, versionable in git, and require no auth setup. The operator can inspect and manually edit them if needed. Migration to Sheets in v1 is a matter of swapping the read/write layer in `scripts/library_query.py`.

---

## MTC_Ad_Diagnostic_v1.md treated as v2

**Decision:** `data/seed/MTC_Ad_Diagnostic_v1.md` is the source of truth. All prompt templates reference it. The BUILD_PROMPT calls it v2 — same content, different filename.

**Why:** The operator confirmed seed files are unchanged. v1.md contains the complete angle bank, hook templates, retire list, and course playbook needed for the system.

---

## Critic runs sequentially in the same session, not as a separate agent

**Decision:** After every generator prompt (strategy / copywriter / media_buyer), the same Claude Code session immediately runs the critic prompt on the output.

**Why:** The BUILD_PROMPT is explicit: "this is personas as prompts, not Agent Teams." A second prompt in the same session costs no additional routine run on the Max plan. The critic does not auto-block or auto-regenerate — it produces a review the operator reads alongside the generated artifact.

---

## Prompt file summaries (Phase 3)

| File | One-line summary |
|------|-----------------|
| `_shared_context.md` | Condensed diagnostic: angle bank, Templates A–E verbatim, retire list, course playbook, kill/scale rules — prepended to every command |
| `strategy.md` | Strategist who picks 2 angles from the bank, sizes budget against seasonal calendar, and outputs a pre-flight QA checklist |
| `copywriter.md` | Egyptian 3amiya copywriter who writes 12 hooks (6/angle), paired body copy, 12 image briefs, 4 video scripts, and bilingual landing page |
| `media_buyer.md` | Meta buyer who outputs a bulk-paste launch CSV with Reels-first placement, correct objective, and naming convention; includes Google Search section if brief requests it |
| `critic.md` | Skeptical reviewer who branches on input type (A=strategy, B=creative, C=launch CSV) and outputs ✅/⚠️/🛑 blocks — does not auto-block, operator decides |
| `triage.md` | Daily analyst who reads master.csv + performance_log.csv + conversations.csv and outputs one opinionated PAUSE/WATCH/SCALE recommendation per active ad |

---

## Pre-write hook validates launch CSVs, not strategy/creative

**Decision:** The `pre_csv_write.py` hook fires only on `data/launches/*.csv` writes, not on strategy or creative markdown files.

**Why:** Technical constraints (character limits, objective type, placement allocation) are deterministic and machine-checkable. Strategic quality (angle choice, hook register, audience fit) requires human judgment — that's the critic's job, not the hook's.
