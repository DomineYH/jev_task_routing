# api_integration (uses playbook `feature`)

This is not a catalog id. `playbooks.select` assigns `playbook_id=feature` when `task_type == api_integration`. Follow [feature.md](feature.md) and `playbooks.catalog.feature`. These notes do not override those steps (QUAL-1).

## Type-specific notes

- Trace and implement from an official or local authoritative contract (typed client, vendored spec, pinned docs, or a researcher fact record). Do not invent status codes, retry rules, or idempotency keys from model memory.
- Distinguish mocked tests from a real connectivity check. A mock-only pass is labeled as such and is not a substitute for a required real check (VER-6, QUAL-7).
- Record the contract version or retrieval date used.
