## Task routing (jev_task_routing v2.5.7-draft)
- Policy (rule IDs): `.routing/ROUTING_POLICY.md` · Config: `.routing/jev_task_routing.json` · Models: `.routing/models.json` · Playbooks: `.routing/playbooks/<id>.md`; project examples: `examples/herdr/`
- You are the host (AUTH-1). Never spawn a worker without an issued work order (ORDER-1).
- Before the first Jev call, build an evidence packet (EVID-1..5) and write .routing/tasks/<id>.json.
- Router env: TYPESAFE_API_KEY. Jev questions = config.jev.questions, all 14 in one call (CLS-1).
- After routing: take the playbook id from `playbooks.select`, read `.routing/playbooks/<id>.md` and record its sha256 in `task_record.playbook_sha256` (QUAL-1); write the design_note (QUAL-2); evaluate advisor triggers ADV-1..5 and issue a consultation or record a skip (ROLE-9).
