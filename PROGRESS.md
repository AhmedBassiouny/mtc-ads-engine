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

## Phase 2 — Configuration YAMLs ⬜
- [ ] config/courses.yaml
- [ ] config/kill_scale_rules.yaml
- [ ] config/audience_definitions.yaml
- [ ] config/seasonal_calendar.yaml
- [ ] data/briefs/_template.yaml

## Phase 3 — Prompt Templates ⬜
- [ ] prompts/_shared_context.md
- [ ] prompts/strategy.md
- [ ] prompts/copywriter.md
- [ ] prompts/media_buyer.md
- [ ] prompts/critic.md
- [ ] prompts/triage.md

## Phase 4 — Hooks ⬜
- [ ] .claude/settings.json
- [ ] .claude/hooks/pre_csv_write.py

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
