# docs (no catalog playbook)

This is not a catalog id. `playbooks.select` assigns `playbook_id=null`. There is no playbook ceremony (QUAL-11). Do not invent a playbook id for this type. Applicable QUAL rules still come from `code_quality.applies`.

Typical risk for documentation-only work is often minor, in which case only QUAL-3, QUAL-7, and QUAL-8 apply — no `design_note`, no playbook steps. The host still follows AUTH, VER, and the accepted `testing_mode`.

## Type-specific notes

- Change only the documentation the order names. Do not "fix" adjacent code or comments unless the order says so (QUAL-3).
- QUAL-7 for docs means the published artifact is checked as a reader would see it (rendered page, generated site, or the in-repo file that is the source of truth), not only that a file was written.
