# database (uses playbook `feature`)

This is not a catalog id. `playbooks.select` assigns `playbook_id=feature` when `task_type == database`. Follow [feature.md](feature.md) and `playbooks.catalog.feature`. These notes do not override those steps (QUAL-1).

## Type-specific notes

- State the compatibility and integrity contract in the `design_note` (QUAL-2) before editing: what existing data must still read, what may be rewritten, and what is irreversible.
- The matching surface for QUAL-7 includes reading back the written value (`code_quality.surfaces.storage`) and running migrations against representative non-production data. A migrated empty database is not evidence for a data-rewriting change. Do not use production data in an implementer workspace.
- A destructive or irreversible step is a protected operation: do not perform it without explicit authorization in the order (AUTH-4).
