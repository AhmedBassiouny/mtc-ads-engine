Run the creative workflow for the strategy: $ARGUMENTS

Steps:

**1. Load the strategy**
Find and read the strategy file. Try these paths in order:
- `data/strategies/$ARGUMENTS.md`
- `data/strategies/$ARGUMENTS` (if operator omitted .md)
- Search `data/strategies/` for any file containing `$ARGUMENTS` in the filename

If not found, list the available strategy files in `data/strategies/` and ask the operator to confirm the correct ID.

**2. Check strategy status**
Read the front-matter. If status is `awaiting_approval` or `approved` — proceed.
If the critic review has 🛑 Blockers — warn the operator:
```
⚠️  The strategy critic flagged blockers. Review data/strategies/$ARGUMENTS.md before proceeding.
Type /creative $ARGUMENTS again to override and proceed anyway.
```
Only proceed if the operator re-runs the command (the second run is the override).

**3. Generate the creative pack**
Read @prompts/copywriter.md and execute it against the strategy. Also read:
- @prompts/_shared_context.md
- @config/courses.yaml
- @config/audience_definitions.yaml

Produce the full creative pack as defined in prompts/copywriter.md:
- 12 hooks (6 per angle)
- Paired body copy for each hook
- 12 image briefs (9:16 mobile-vertical, Arabic on-image text)
- 4 video scripts (hook in 0–3 seconds)
- Bilingual landing page copy

**4. Generate a unique ID**
Derive from the strategy ID: replace `strategy_` with `creative_`
Example: `strategy_20260515_decor` → `creative_20260515_decor`

**5. Save the creative pack**
Write to `data/creative/<id>.md`. Include at the top:
```
---
id: <id>
strategy_id: <strategy_id>
date: <today>
status: awaiting_critic
---
```

**6. Run the critic**
Read @prompts/critic.md and execute the creative branch (Branch B) against the creative pack you just wrote.

**7. Append critic review**
Append the critic review to `data/creative/<id>.md` under a `---` divider with heading `## Critic Review`.
Update status to `awaiting_approval`.

**8. Confirm to the operator**
Print:
```
✅ Creative pack + critic review saved to data/creative/<id>.md

Next steps:
1. Read the file and review the critic's findings
2. Add image links: edit the file and fill in the image URLs next to each image brief
3. Then run:
     /launch <id>
```
