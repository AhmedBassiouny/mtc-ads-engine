Create a new course brief for the course named: $ARGUMENTS

Steps:
1. Read @data/briefs/_template.yaml
2. Read @config/courses.yaml to find the matching course track (match by name_en, name_ar, or track key — be flexible)
3. Create the file `data/briefs/$ARGUMENTS.yaml` by copying the template
4. Pre-fill what you can from config/courses.yaml:
   - `course.track` — the matching key
   - `course.name_ar` and `course.name_en` — from the catalog
   - `creative.lead_angle` — the lead_angle for that track
   - `launch.objective` — always "Messages"
   - `launch.channels` — always includes "meta"
5. Leave all other fields blank or at their default — the operator fills them in
6. Print a confirmation: "✅ Brief created at data/briefs/$ARGUMENTS.yaml — open it and fill in: price_egp, discount_pct, start_date, enrollment_deadline, daily_budget_egp, destination_url, notes"
7. List the required fields the operator must fill before running /strategy

Do not invent any values. Only pre-fill what comes directly from config/courses.yaml.
