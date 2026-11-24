# dependency_update (no catalog playbook)

This is not a catalog id. `playbooks.select` assigns `playbook_id=null`. There is no playbook ceremony (QUAL-11). Do not invent a playbook id for this type. Applicable QUAL rules still come from `code_quality.applies`.

## Type-specific notes

- Change only the dependencies and lockfiles the order names. Do not refactor callers "while here" (QUAL-3).
- Verify on the surfaces the order and `repo_checks` require after the version change (QUAL-7). Record the before/after identifiers and the commands run.
- A major or irreversible upgrade that the order did not authorize is a host question, not an implementer expansion (AUTH-4).
