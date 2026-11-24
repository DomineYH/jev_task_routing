# tests (no catalog playbook)

This is not a catalog id. `playbooks.select` assigns `playbook_id=null`. There is no playbook ceremony (QUAL-11). Do not invent a playbook id for this type. Applicable QUAL rules still come from `code_quality.applies`.

Adding, repairing, or reorganizing tests without intentionally changing application behavior is recorded as `change_kind = test_only` (EVID-2a). This is never automatically minor.

## Type-specific notes

- State the behavior each new or changed test claims, from the requirement or an independent contract, not from the current implementation (QUAL-6, VER-2).
- Confirm that a broken behavior would fail the test, and that an equivalent internal rewrite would not. Delete or rewrite tests that fail this check.
- Do not skip, weaken, or delete assertions to obtain a green run. Expected-value changes need an independently supported reason (VER-10).
- Run the changed tests and the nearest related family. A skipped test is not a pass (QUAL-7).
