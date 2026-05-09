Run the launch workflow for the creative pack: $ARGUMENTS

Steps:

**1. Load the creative pack**
Find and read the creative file. Try these paths in order:
- `data/creative/$ARGUMENTS.md`
- `data/creative/$ARGUMENTS` (if operator omitted .md)
- Search `data/creative/` for any file containing `$ARGUMENTS` in the filename

If not found, list available files in `data/creative/` and stop.

**2. Check image links**
Scan the creative file for image briefs. Check whether image URLs have been added next to each brief (operator fills these in after the /creative step).

If any image URLs are missing:
```
🛑 Missing image links. Before running /launch:

  Open data/creative/$ARGUMENTS.md and add the hosted image URL
  next to each Image Brief. Look for lines like:
    **Image [#] — ...**
    - Image URL: [ADD URL HERE]

  Then run /launch $ARGUMENTS again.
```
Stop — do not proceed with missing images.

**3. Load the strategy brief context**
Read the strategy file linked in the creative pack's front-matter (strategy_id).
Load the brief path from the strategy front-matter.
Read the brief YAML for: destination_url, daily_budget_egp, start_date, enrollment_deadline, objective.

**4. Generate the launch CSV**
Read @prompts/media_buyer.md and execute it against the creative pack and brief. Also read:
- @prompts/_shared_context.md
- @config/kill_scale_rules.yaml
- @config/audience_definitions.yaml

Produce the launch CSV as defined in prompts/media_buyer.md.

**5. Generate ID and paths**
Derive from the creative ID: replace `creative_` with `launch_`
Example: `creative_20260515_decor` → `launch_20260515_decor`

CSV path: `data/launches/<id>.csv`
Review path: `data/launches/<id>.review.md`

**6. Write the launch CSV**
Write the CSV to `data/launches/<id>.csv`.

The pre-write hook (.claude/hooks/pre_csv_write.py) will automatically validate the CSV before it is saved. If the hook blocks the write, fix the flagged issues and try again — do not bypass the hook.

**7. Run the critic**
Read @prompts/critic.md and execute the launch branch (Branch C) against the CSV content.

**8. Save the critic review**
Write the critic review to `data/launches/<id>.review.md`.

**9. Confirm to the operator**
Print:
```
✅ Launch CSV saved to data/launches/<id>.csv
✅ Critic review saved to data/launches/<id>.review.md

To launch:
1. Read the critic review — fix any 🛑 Blockers before uploading
2. Open Meta Ads Manager → Ads → Import → upload data/launches/<id>.csv
3. Set kill-check reminder: check CPR on [start_date + 2 days]
   Kill rule: ≥80 EGP spend AND CPR >30 EGP → pause (see config/kill_scale_rules.yaml)

After the campaign runs, drop the Meta performance export into data/incoming/
and run: /ingest perf data/incoming/<export_file.csv>
```
