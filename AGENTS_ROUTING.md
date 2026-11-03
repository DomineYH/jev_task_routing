<!-- jev-routing:start (managed by init_routing.sh — do not edit between markers) -->
## Task routing (jev_task_routing v2.5.2-draft)

- Policy (rule IDs): `.routing/ROUTING_POLICY.md` · Config: `.routing/jev_task_routing.json` · Models: `.routing/models.json` (the only place harness/model/effort live; MODEL-5) · Schemas: `.routing/*.schema.json`
- You are the **host** (AUTH-1). Only the host issues work orders and launches workers (AUTH-2). No worker without an issued, schema-valid work order (ORDER-1).
- Per task: build the evidence packet (EVID-1..5; read at most 8 files yourself) → attest `trusted_flags` from your own inspection only, `null` when unknown (EVID-5) → **evaluate `evidence_orders.inspector_triggers` (INS-*) and `researcher_triggers` (RES-*)**; if any holds, issue that evidence order with `order_defaults` BEFORE calling Jev, or record a skip reason — silent skipping is a violation (EVID-6, EVID-7) → one Jev call with all 14 questions (CLS-1) → apply `decision.rules` in order → write `.routing/tasks/<task_id>.json` (`templates.task_record`, including `evidence_orders_evaluated`).
- Prefix every `evidence_packet.unknowns` entry with `repo:` or `external:`; set `external_contracts.status = unverified` when an external API contract changes and no local authoritative source covers it.
- Repository-required checks live in `.routing/repo_checks.json`; copy them into `verification_plan` entries with `required_by: repository` (VER-5). If `repo_checks.json` says `require_review: true`, attest `require_independent_review: true` (WF-3).
- Budgets: at most 5 Jev calls per task revision (CLS-11), 2 automatic repair cycles (VER-11). Evidence orders, order revisions, clarifications and advisor calls never consume or reset them.
- Resolve each delegated role's harness/model/effort with `python3 .routing/resolve_models.py --role <id>` (or the same precedence, MODEL-1) and record the source per field in `task_record.setting_sources`; never configure or resolve yourself, the host (MODEL-4).
- Router credentials: env named in `models.json#/router/api_key_env` (default `TYPESAFE_API_KEY`). Never put keys, secrets or unrelated source into the Jev request (SAFE-3).
- **SHADOW MODE: ON.** Route and record only. Do not dispatch workers, create PRs, merge or deploy until a human removes this line after the ENF checklist in README is satisfied.
<!-- jev-routing:end -->
