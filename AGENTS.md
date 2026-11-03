## Task routing
- Policy: .routing/ROUTING_POLICY.md (rule IDs), config: .routing/jev_task_routing.json, models: .routing/models.json; project examples: examples/herdr/
- You are the host (AUTH-1). Never spawn a worker without an issued work order (ORDER-1).
- Before the first Jev call, build an evidence packet (EVID-1..5) and write .routing/tasks/<id>.json.
- Router env: TYPESAFE_API_KEY. Jev questions = config.jev.questions, all 14 in one call (CLS-1).