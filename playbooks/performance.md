# performance

Catalog id: `performance`

Selected when: `task_type == performance`.

Source of truth: `playbooks.catalog.performance` in `jev_task_routing.json`. This file restates that entry for reading. If this file and the JSON disagree, the JSON wins (QUAL-1).

## Steps

1. Capture a baseline with a repeatable command on the path a user waits on; record environment and run count.
2. Find the measured cause from a profile or trace before changing code.
3. Try remedies cheapest first: stop doing the work, stop repeating it, do less, defer it, do it concurrently, make it cheaper. Stop when the target is met.
4. Re-measure with the same harness over alternating runs and confirm behavior is unchanged.

## Required report evidence

- baseline, after, delta, range and run count
- what limits the number now
- artifact path of the measurements
- behavior-preservation check result

## Rule refs

`QUAL-4`, `QUAL-7`

## Notes

A measured number is reported with its baseline, run count, range and what limits it (QUAL-7). Do not treat a single warm run, a different harness, or a type-check as the comparison.
