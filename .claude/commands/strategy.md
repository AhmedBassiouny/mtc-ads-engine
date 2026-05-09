Run the strategy workflow for the brief at: $ARGUMENTS

Steps:

**1. Validate the brief**
Read the brief YAML at `$ARGUMENTS`. Check that these required fields are filled:
- course.track, course.price_egp, course.discount_pct, course.name_ar
- launch.start_date, launch.enrollment_deadline, launch.daily_budget_egp
- creative.destination_url

If any are missing or empty, stop and list the missing fields. Do not proceed until they are filled.

**2. Generate the strategy**
Read @prompts/strategy.md and execute it against the brief. Also read:
- @prompts/_shared_context.md
- @config/courses.yaml
- @config/audience_definitions.yaml
- @config/seasonal_calendar.yaml
- @config/kill_scale_rules.yaml

Produce the full strategy block as defined in prompts/strategy.md.

**3. Generate a unique ID**
Create an ID from the date and course: `strategy_[YYYYMMDD]_[course_track]`
Example: `strategy_20260515_decor`

**4. Save the strategy**
Write the strategy output to `data/strategies/<id>.md`. Include at the top:
```
---
id: <id>
brief: $ARGUMENTS
date: <today>
status: awaiting_critic
---
```

**5. Run the critic**
Read @prompts/critic.md and execute the strategy branch (Branch A) against the strategy you just wrote.

**6. Append critic review**
Append the critic review to the same file `data/strategies/<id>.md` under a `---` divider with the heading `## Critic Review`.

Update the front-matter status from `awaiting_critic` to `awaiting_approval`.

**7. Confirm to the operator**
Print:
```
✅ Strategy + critic review saved to data/strategies/<id>.md

Review it, then run:
  /creative <id>

If you want changes, edit the brief and run /strategy again.
```

Reminder: the operator approves by reading the file and deciding — there is no approval command. When ready, they run /creative with the strategy ID.
