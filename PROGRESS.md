# Build Progress

## Phase 0 — Foundation ✅
- [x] Git initialized
- [x] .gitignore created
- [x] GitHub remote confirmed (https://github.com/AhmedBassiouny/mtc-ads-engine)
- [x] Initial commit pushed
- [x] CLAUDE.md skeleton
- [x] README.md

## Phase 1 — Data Seeding ✅
- [x] scripts/seed_library.py
- [x] scripts/tag_ads.py
- [x] data/library/ populated (master.csv 113 rows, performance_log.csv 4294 rows, conversations.csv schema)
- Note: 43 ads auto-tagged; 64 with spend flagged in data/library/untagged_review.csv for manual/AI review

## Phase 2 — Configuration YAMLs ✅
- [x] config/courses.yaml (8 course tracks with lead angles, hook templates, CPR targets)
- [x] config/kill_scale_rules.yaml (kill ≥80 EGP + CPR >30 OR 5 days live; scale at CPR ≤17)
- [x] config/audience_definitions.yaml (6 segments with hook handles and meta age ranges)
- [x] config/seasonal_calendar.yaml (Ramadan, Eid, Summer, with budget multipliers)
- [x] data/briefs/_template.yaml (operator fills and runs /strategy)
- [x] requirements.txt (pyyaml) + .venv created

## Phase 3 — Prompt Templates ✅
- [x] prompts/_shared_context.md (angle bank + Templates A–E verbatim + retire list + course playbook + kill/scale rules)
- [x] prompts/strategy.md (2 angles, channel split, budget, week-1 schedule, pre-flight checklist)
- [x] prompts/copywriter.md (12 hooks, paired body copy, 12 image briefs, 4 video scripts, bilingual landing page)
- [x] prompts/media_buyer.md (bulk-paste launch CSV with Reels-first, naming convention, Google Search section)
- [x] prompts/critic.md (branches A/B/C by input type; ✅/⚠️/🛑 output; does not auto-block)
- [x] prompts/triage.md (PAUSE/WATCH/SCALE per active ad; cite diagnostic; powers /status)

## Phase 4 — Hooks ✅
- [x] .claude/settings.json (PreToolUse on Write tool)
- [x] .claude/hooks/pre_csv_write.py (validates objective, placement, char limits, URL, naming convention, budget, schedule)
- Tested: catches 8 errors in bad CSV; passes clean CSV

## Phase 5 — Slash Commands ⬜
- [ ] .claude/commands/new_brief.md
- [ ] .claude/commands/strategy.md
- [ ] .claude/commands/creative.md
- [ ] .claude/commands/launch.md
- [ ] .claude/commands/ingest.md
- [ ] .claude/commands/status.md

## Phase 6 — Ingest Scripts ⬜
- [ ] scripts/ingest_perf.py
- [ ] scripts/ingest_whatsapp.py
- [ ] scripts/validate_brief.py
- [ ] scripts/library_query.py

## Phase 7 — Status Report Tuning ⬜
- [ ] /status produces opinionated, traceable output on real data

## Phase 8 — End-to-End Smoke Test ⬜
- [ ] tests/fixtures/test_brief_3dsmax.yaml
- [ ] tests/smoke_test.md
- [ ] Full pipeline runs clean

## Phase 9 — Walkthrough Finalization ⬜
- [ ] WALKTHROUGH.md complete
- [ ] Tagged v0.1.0

---

## Open questions

_(none)_
