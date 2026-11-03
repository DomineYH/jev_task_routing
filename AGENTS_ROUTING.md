<!-- jev-routing:start (managed by init_routing.sh — do not edit between markers) -->
## Task routing (jev_task_routing v2.5.0-draft)

- Policy (rule IDs): `.routing/ROUTING_POLICY.md` · Config: `.routing/jev_task_routing_v2.5.0.json` · Schema: `.routing/jev_task_routing.schema.json`
- You are the **host** (AUTH-1). Only the host issues work orders and launches workers (AUTH-2). No worker without an issued, schema-valid work order (ORDER-1).
- Per task: build the evidence packet (EVID-1..5) → attest `trusted_flags` from your own inspection only, `null` when unknown (EVID-5) → one Jev call with all 14 questions (CLS-1) → apply `decision.rules` in order → write `.routing/tasks/<task_id>.json` (`templates.task_record`).
- Repository-required checks live in `.routing/repo_checks.json`; copy them into `verification_plan` entries with `required_by: repository` (VER-5). If `repo_checks.json` says `require_review: true`, attest `require_independent_review: true` (WF-3).
- Budgets: at most 2 Jev calls per task revision (CLS-11), 2 automatic repair cycles (VER-11). Order revisions, clarifications and advisor calls never reset them.
- Router credentials: env `TYPESAFE_API_KEY`. Never put keys, secrets or unrelated source into the Jev request (SAFE-3).
- **SHADOW MODE: ON.** Route and record only. Do not dispatch workers, create PRs, merge or deploy until a human removes this line after the ENF checklist in README is satisfied.
<!-- jev-routing:end -->
