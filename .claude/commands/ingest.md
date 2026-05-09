Ingest a data file into the MTC ad library.

Usage: /ingest perf <file_path>
       /ingest whatsapp <file_path>

Arguments received: $ARGUMENTS

Steps:

**1. Parse the arguments**
Split `$ARGUMENTS` into: [type] [file_path]
- type: "perf" or "whatsapp"
- file_path: path to the file to ingest

If arguments are missing or type is not "perf" or "whatsapp", print usage and stop:
```
Usage:
  /ingest perf data/incoming/<meta_export.csv>
  /ingest whatsapp data/incoming/<whatsapp_export.txt>
```

**2. Check the file exists**
Verify the file at [file_path] exists. If not, list the contents of `data/incoming/` and stop.

**3. Run the appropriate ingest script**

For `perf`:
  Run: `python3 scripts/ingest_perf.py [file_path]`

  This script:
  - Auto-detects encoding (UTF-16 LE or UTF-8) and delimiter (tab or comma)
  - Validates row counts and spend totals
  - Appends new rows to data/library/performance_log.csv
  - Adds any new ad IDs to data/library/master.csv
  - Moves the processed file to data/archive/

For `whatsapp`:
  Run: `python3 scripts/ingest_whatsapp.py [file_path]`

  This script:
  - Parses WhatsApp text export format
  - Appends conversation records to data/library/conversations.csv
  - Moves the processed file to data/archive/

**4. Report results**
After the script runs, print what was output by the script (row counts, spend totals, any anomalies flagged).

Then print:
```
✅ Ingest complete. Run /status to see the updated report.
```

If the script exits with an error, print the error and suggest:
- For encoding errors: "The file may be UTF-16 LE with tabs — check scripts/ingest_perf.py detects this correctly"
- For row count mismatches: "Compare the row count and spend total against Meta Ads Manager and investigate the delta"
