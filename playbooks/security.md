# security (uses playbook `feature`)

This is not a catalog id. `playbooks.select` assigns `playbook_id=feature` when `task_type == security`. Follow [feature.md](feature.md) and `playbooks.catalog.feature`. These notes do not override those steps (QUAL-1).

A security defect whose goal is to restore a broken control can be classified as `bug_fix` and then uses the `bug_fix` playbook instead.

## Type-specific notes

- Name the trust boundary being enforced while tracing the subsystem.
- Reproduce or characterize the unsafe behavior on a representative path before claiming a hardening (QUAL-5, QUAL-7).
- Make the smallest change that enforces the boundary (QUAL-3). Do not weaken neighboring checks, log secrets, or commit credentials.
- Verify with negative authorization and regression cases on the real enforcement point, not only a unit test of a helper. Secret handling is checked by inspection of what is written, logged, and transmitted.
