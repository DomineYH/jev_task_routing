# infrastructure (no catalog playbook)

This is not a catalog id. `playbooks.select` assigns `playbook_id=null`. There is no playbook ceremony (QUAL-11). Do not invent a playbook id for this type. Applicable QUAL rules still come from `code_quality.applies`.

## Type-specific notes

- Stay inside the issued scope: the modules, environments, and commands the order names (AUTH-3).
- Destructive, production, or rollout steps need explicit authorization (AUTH-4). A review PASS is not authorization.
- Verify with the actual command or environment the change affects (QUAL-7), and record what could not be run as `inconclusive`.
