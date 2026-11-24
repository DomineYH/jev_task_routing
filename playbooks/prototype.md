# prototype

Catalog id: `prototype`

Selected when: `work_mode == exploration` AND `change_kind == disposable_prototype`.

Source of truth: `playbooks.catalog.prototype` in `jev_task_routing.json`. This file restates that entry for reading. If this file and the JSON disagree, the JSON wins (QUAL-1).

## Steps

1. State the decision the prototype exists to make; no decision, no prototype.
2. Build throwaway inside the order's isolated scratch scope, outside product source; no tests, no abstractions.
3. When comparing alternatives, build them side by side behind one switch, each labeled.
4. Observe the thing being decided (output, timing, screenshot) and record it.

## Required report evidence

- variants built and the scratch path
- the observation for each variant
- tradeoffs and a recommendation
- a plain statement that the code is throwaway

## Rule refs

`QUAL-11`, `WF-4`

## Notes

An exploration prototype is exempt from the delivery QUAL set by design — throwaway code whose deliverable is the decision — and is never adopted without delivery reclassification (QUAL-11, WF-4).
