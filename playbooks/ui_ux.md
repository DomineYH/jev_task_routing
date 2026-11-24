# ui_ux (uses playbook `feature`)

This is not a catalog id. `playbooks.select` assigns `playbook_id=feature` when `task_type == ui_ux`. Follow [feature.md](feature.md) and `playbooks.catalog.feature`. These notes do not override those steps, `testing_mode`, workflow, roles, or risk (QUAL-1).

A UI defect whose goal is to restore previous behavior is `bug_fix`, not this type. A new capability that happens to include UI is still `feature` and still uses this same playbook.

## Type-specific notes

- Name the affected states, viewports, and interaction paths while tracing the subsystem (feature step 1).
- The matching surface for QUAL-7 / feature step 5 is the running interface, not markup or snapshots alone: rendered output, the changed interaction, and accessibility behavior the repository requires (keyboard, focus, names, contrast).
- Check the viewport sizes listed in the order or in repository UI conventions.
- Do not refresh a visual baseline just to make a diff pass. A baseline that looks wrong is a host question, not an implementer edit.

Main has no separate `visual_parity` playbook. Pixel-exact equivalence is still this `feature` playbook, with the baseline treated as an acceptance check on the matching surface.
