Generate the MTC ads status report.

Steps:

**1. Load the library data**
Read these files:
- @data/library/master.csv — ad library with tags and lifetime performance
- @data/library/performance_log.csv — monthly performance snapshots
- @data/library/conversations.csv — WhatsApp conversation outcomes

Also read:
- @config/kill_scale_rules.yaml — kill/scale thresholds
- @prompts/_shared_context.md — diagnostic playbook (for angle citations)
- @prompts/triage.md — the triage analyst instructions

**2. Check data freshness**
Scan performance_log.csv for the most recent `Reporting ends` date.

If no data in the last 14 days, print:
```
⚠️  No recent performance data (last entry: [date]).

Drop a Meta CSV export into data/incoming/ and run:
  /ingest perf data/incoming/<filename.csv>

Then run /status again.
```
Still produce the report using whatever data is available.

**3. Identify active ads**
An ad is "active" if it has spend > 0 in performance_log.csv within the last 7 days.

If no active ads found, print:
```
No active ads in the last 7 days. The report below covers all historical data.
```

**4. Produce the status report**
Execute the triage analyst role defined in @prompts/triage.md.

Produce the full report as specified in triage.md:
- Portfolio summary (last 7 days)
- Action required section (PAUSE / WATCH / SCALE per active ad)
- Patterns this week
- Conversion insights (if conversations.csv has data)
- Suggested next tests (2–3 max)

**Rules (from triage.md):**
- Every active ad gets exactly one of PAUSE, WATCH, or SCALE — never skip an ad
- Ads with <80 EGP spend get WATCH (insufficient data to kill/scale)
- Every recommendation cites a specific metric and the diagnostic section behind it
- No data dumps — every sentence is a conclusion or action
- If master.csv has untagged ads, note: "X ads untagged — run python3 scripts/tag_ads.py to improve future reports"

**5. Save the report (optional)**
If the report is longer than 50 lines, also save a copy to `data/library/status_[YYYYMMDD].md` so the operator can reference it later.

Stream the full report to the terminal.
