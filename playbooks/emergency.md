# emergency (no catalog playbook)

This is not a catalog id. `playbooks.select` matches `mode == emergency` first and assigns `playbook_id=null`, regardless of `task_type`. There is no playbook ceremony. The workflow is `emergency` (WF-5). `code_quality.applies.emergency` binds QUAL-3, QUAL-5, and QUAL-7 only.

## Notes

- Do the smallest recovery or revert the incident requires (QUAL-3, QUAL-5). Do not start a feature or cleanup on the same order (QUAL-3, VER-11).
- Reproduce or confirm the incident on the relevant surface when that does not delay containment, and prove recovery on the real artifact (QUAL-5, QUAL-7).
- Expedited review, rollout, and deferred verification still follow the emergency stages and AUTH-4. Emergency does not grant PR, merge, or deploy permission by itself.
