# investigation

Catalog id: `investigation`

Selected when: `work_mode == exploration`, unless `change_kind == disposable_prototype` (that case selects `prototype`).

Source of truth: `playbooks.catalog.investigation` in `jev_task_routing.json`. This file restates that entry for reading. If this file and the JSON disagree, the JSON wins (QUAL-1).

## Steps

1. Trace the code the question is about and cite file:line.
2. Answer with overview, how it works, where things live and gotchas; for a choice, a recommendation with a tradeoffs table.
3. No code change. If one is warranted, say so and return to the host for delivery reclassification.

## Required report evidence

- cited sources for every claim
- what remains unknown

## Rule refs

`QUAL-10`, `WF-4`

## Notes

This is a read-only playbook. Findings may recommend a later delivery task; they do not start one.
