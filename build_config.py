"""Build jev_task_routing.json from the v2.4.0 policy.

Jev questions, enums and record templates are copied verbatim from the source
file. Everything else is restructured into short machine-readable fields that
reference rule IDs defined in ROUTING_POLICY.md.
"""
import copy
import hashlib
import json
import sys
from collections import OrderedDict

SRC = sys.argv[1]
OUT = sys.argv[2]
MODELS_OUT = sys.argv[3] if len(sys.argv) > 3 else None

raw = open(SRC, "rb").read()
src = json.loads(raw)
sha = hashlib.sha256(raw).hexdigest()

O = OrderedDict

# --------------------------------------------------------------------------
# Roles: settings verbatim, prose replaced by short structured fields.
# --------------------------------------------------------------------------
ROLE_META = {
    "planner": O(
        mission="Produce or revise the executable implementation plan under a planning order; return a proposal.",
        target_access="read_only",
        may_write=["plan_artifacts", "reports"],
        dispatch_when=["high_risk_delivery", "needs_design", "substantive_replanning"],
        order_purposes=["planning"],
        required_order_fields=[],
        rule_refs=["AUTH-3", "ROLE-1", "ROLE-7", "QUAL-2"],
    ),
    "implementer": O(
        mission="Execute an issued implementation, prototype or repair order within its scope, playbook and accepted testing_mode.",
        target_access="write_in_scope",
        may_write=["write_scope"],
        dispatch_when=["issued_implementation_order", "issued_repair_order", "issued_prototype_order"],
        order_purposes=["implementation", "repair", "prototype"],
        required_order_fields=["testing_decision_ref"],
        rule_refs=["AUTH-3", "ROLE-2", "ORDER-4", "QUAL-1", "QUAL-4", "QUAL-8"],
    ),
    "task-verifier": O(
        mission="Independently review the fixed current diff and evidence against the criteria and quality bar; report PASS/FAIL/BLOCKED with proven findings to the host.",
        target_access="read_only",
        may_write=["review_report", "disposable_diagnostics"],
        dispatch_when=["standard_delivery", "high_delivery", "emergency", "repository_rule", "require_independent_review"],
        order_purposes=["independent_review"],
        required_order_fields=["verification_plan_ref"],
        rule_refs=["AUTH-3", "ROLE-3", "ROLE-7", "QUAL-9"],
    ),
    "inspector": O(
        mission="Fill the evidence packet from repository facts (code, callers, tests, execution status) for a named gap; return a packet delta with source refs.",
        target_access="read_only",
        may_write=["evidence_report"],
        dispatch_when=["any evidence_orders.inspector_triggers condition holds (EVID-6)", "NEEDS_CONTEXT naming a repository fact"],
        order_purposes=["repository_evidence"],
        required_order_fields=["evidence_gap"],
        rule_refs=["AUTH-3", "ROLE-4", "EVID-6", "EVID-7", "ORDER-7"],
    ),
    "researcher": O(
        mission="Resolve a specific external API/dependency/platform fact from official sources; return a fixed-format fact record with source URL.",
        target_access="none",
        may_write=["evidence_report"],
        dispatch_when=["any evidence_orders.researcher_triggers condition holds (EVID-6)", "NEEDS_CONTEXT naming an external fact"],
        order_purposes=["external_research"],
        required_order_fields=["evidence_gap"],
        rule_refs=["AUTH-3", "ROLE-5", "EVID-6", "EVID-7", "ORDER-7"],
    ),
    "tester": O(
        mission="Execute uncovered specialized integration/E2E/performance/migration/post-deployment checks and report actuals.",
        target_access="read_only",
        may_write=["authorized_test_resources", "disposable_outputs"],
        dispatch_when=["uncovered_special_test_gap", "post_deployment_gap"],
        order_purposes=["special_test", "post_deployment_check"],
        required_order_fields=["verification_plan_ref"],
        rule_refs=["AUTH-3", "ROLE-6", "VER-8"],
    ),
    "advisor": O(
        mission="Give the host one evidence-based second opinion on a specific unresolved technical decision.",
        target_access="read_only",
        may_write=["consultation_report"],
        dispatch_when=["any consultation_orders.advisor_triggers condition holds (ROLE-9)", "explicit_host_consultation"],
        order_purposes=["technical_consultation"],
        required_order_fields=["decision_question"],
        rule_refs=["AUTH-3", "ROLE-8", "ROLE-9", "ORDER-10"],
    ),
}

roles = O()
for rid, r in src["roles"].items():
    e = O(settings="models.json#/roles/" + rid)
    e.update(ROLE_META[rid])
    roles[rid] = e

# models.json — the only place model settings live (MODEL-5)
models = O()
models["$schema"] = "./models.schema.json"
models["version"] = "1.0.0"
models["requires_policy_version"] = ">=2.5.2"
models["note"] = "Edit this file to change which harness/model/effort each delegated role runs on. The policy file never carries model settings. Prompt overrides in a request still take precedence (MODEL-1)."
models["default"] = O(harness=None, model=None, effort=None)
models["roles"] = O((rid, O(harness=r["harness"], model=r["model"], effort=r["effort"])) for rid, r in src["roles"].items())
models["active_profile"] = "standard"
models["profiles"] = O(
    standard=O(description="Settings as shipped; roles resolve from /roles.", roles=O()),
    high_assurance=O(
        description="Independent review on a model at least as strong as the implementer; use for security/data-sensitive repositories.",
        roles=O(**{"task-verifier": O(harness="codex", model="gpt-6-astra", effort="high")}),
    ),
)
models["router"] = O(
    provider=src["jev"]["provider"],
    base_url=src["jev"]["base_url"],
    endpoint=src["jev"]["endpoint"],
    method=src["jev"]["method"],
    api_key_env=src["jev"]["api_key_env"],
    model=src["jev"]["model"],
    model_checked_on="2026-10-02",
    availability_reverified=False,
)
models["adapters"] = O(
    codex=O(efforts=["low", "medium", "high"], launch_channels=["herdr_pane"], notes="verify effort strings against the installed codex adapter"),
    agy=O(efforts=["low", "medium", "high"], launch_channels=["herdr_pane"], notes="verify against the installed agy adapter"),
    opencode=O(efforts=["low", "medium", "high", "max"], launch_channels=["herdr_pane"], notes="'max' used by tester in shipped settings; confirm the adapter accepts it; must be started in its TUI"),
    claude=O(efforts=["low", "medium", "high"], launch_channels=["herdr_pane"], notes="same harness as a Claude Code host: still a Herdr pane, never the host's Agent/subagent tool (ORDER-9)"),
)
models["version"] = "1.1.0"
models["rule_refs"] = ["MODEL-1", "MODEL-3", "MODEL-5", "ORDER-9"]

# --------------------------------------------------------------------------
# Jev: questions verbatim; everything else compact.
# --------------------------------------------------------------------------
j = src["jev"]
jev = O(
    connection="models.json#/router",
    questions=copy.deepcopy(j["questions"]),
    required_choice_ids=src["decision_policy"]["required_choice_ids"],
    risk_question_ids=src["decision_policy"]["risk_question_ids"],
    request=O(
        single_call_all_questions=True,
        questions_independent=True,
        state_task="development request stripped of model-assignment directives; keep acceptance criteria, negation, identifiers, scope",
        state_context="compact object: changed paths, observed behavior, contracts, trusted findings, incident facts, evidence gaps",
        reserved_context_keys=["verified_flags", "testing_evidence"],
        exclude_from_state=["roles", "prompt_overrides", "workflow_catalog", "api_keys", "unrelated_conversation", "entire_repository", "secrets"],
        question_language="en",
        korean_requests="host-prepared English normalization; original kept outside payload for audit; never ask Jev to translate",
        response_fields=O(choice=["choice", "probabilities", "confidence"], noul=["noul"]),
        rule_refs=["CLS-1", "EVID-5", "SAFE-3"],
    ),
    retry_policy=O(
        max_transport_attempts=j["retry_policy"]["max_transport_attempts"],
        retryable_statuses=j["retry_policy"]["retryable_statuses"],
        single_retry_owner=True,
        backoff="exponential_with_jitter_honor_retry_after",
        never_retry_for_different_semantic_result=True,
    ),
    cache_policy=O(
        enabled=j["cache_policy"]["enabled"],
        key_fields=j["cache_policy"]["key_fields"],
        caches="raw_classification_only",
        invalidate_on=["scope", "facts", "repository_revision", "questions", "router_model", "testing_evidence", "worktree_fingerprint"],
        alias_models_require="actual_version_invalidation_or_bounded_ttl",
    ),
)

# --------------------------------------------------------------------------
# Decision policy: thresholds verbatim, rules as compact expressions + rule IDs.
# --------------------------------------------------------------------------
dp = src["decision_policy"]
trusted_flags = O()
TF_EFFECT = {
    "security_sensitive": ("risk_floor", "true -> risk=high (CLS-2)"),
    "data_sensitive": ("risk_floor", "true -> risk=high (CLS-2)"),
    "shared_core_change": ("risk_floor", "true -> risk=high (CLS-2)"),
    "production_impact": ("risk_floor", "true -> risk=high (CLS-2)"),
    "minor_scope_verified": ("minor_gate", "must be true to select minor (CLS-3)"),
    "active_incident_related_to_task": ("mode_gate", "true -> emergency; model emergency without it -> NEEDS_CONTEXT (CLS-6)"),
    "needs_context": ("context_gate", "true -> NEEDS_CONTEXT (CLS-7)"),
    "touches_ui": ("modifier", "true -> ui_ux modifier (MOD-1)"),
    "touches_external_api": ("modifier", "true -> api_integration modifier (MOD-1)"),
    "changes_user_flow": ("e2e_scope", "true -> e2e=targeted at minimum (VER-6)"),
    "needs_special_test": ("role_candidate", "true -> tester candidate for uncovered gap (ROLE-6)"),
    "needs_design": ("role_candidate", "true -> planner candidate (ROLE-1)"),
    "needs_documentation": ("modifier", "true -> docs modifier (MOD-1); NEW consumption rule in 2.5.0"),
    "needs_specialist": ("consultation_trigger", "true -> advisor trigger ADV-5: the host writes a decision_question or records a skip (ROLE-9); never supplies consent or assigns planner; 2.5.6: was a hint consumed nowhere"),
    "needs_post_deployment_verification": ("post_deploy_schedule", "true AND deployment_requested AND deploy authorized -> tester post_deployment_check item (VER-8); NEW consumption rule in 2.5.0"),
    "require_independent_review": ("review_floor", "true -> add independent_review_and_ci to minor; task-verifier candidate (WF-3); NEW consumption rule in 2.5.0"),
}
for k in dp["trusted_flags"]:
    eff, note = TF_EFFECT[k]
    trusted_flags[k] = O(type="boolean|null", effect=eff, note=note)

decision = O(
    threshold_status="uncalibrated_illustrative; calibrate in shadow mode before automatic execution (VAL-1)",
    thresholds=copy.deepcopy(dp["thresholds"]),
    risk_values=dp["risk_values"],
    modes=dp["modes"],
    statuses=dp["statuses"],
    trusted_flags=trusted_flags,
    trusted_flag_semantics=O(
        source="host_inspection_only",
        null_means="unknown",
        true_risk_flag="imposes_risk_floor",
        false_risk_flag="cannot_cancel_positive_model_signal",
    ),
    rules=[
        O(id="CLS-1", when="response invalid (missing field, unknown choice, nonfinite/out-of-range, bad distribution, choice!=argmax)", then="status=BLOCKED"),
        O(id="CLS-2", when="any(trusted_risk_flag==true) OR max(risk_noul) >= risk_high_min", then="risk=high"),
        O(id="CLS-2b", when="NOT CLS-2 AND max(risk_noul) > risk_clear_max", then="risk=high (provisional_risk=true); request targeted context"),
        O(id="CLS-2c", when="request.inherited_risk_floor set", then="risk=max(risk, inherited_risk_floor)"),
        O(id="CLS-3", when="all(risk_noul <= risk_clear_max) AND minor_eligible >= minor_min_probability AND minor_scope_verified==true", then="risk=minor else risk=standard"),
        O(id="CLS-3b", when="risk==minor AND any(changes_user_flow, touches_external_api, needs_design, needs_special_test) >= include_optional_signal_min", then="risk=standard"),
        O(id="CLS-4", when="any required choice: probability < choice_min_probability OR confidence < choice_min_confidence", then="status=NEEDS_CONTEXT (no cross-question compensation)"),
        O(id="CLS-5", when="task_type==other OR work_mode==other (confident)", then="status=NOT_APPLICABLE; no workers"),
        O(id="CLS-6", when="work_mode==emergency AND active_incident_related_to_task!=true", then="status=NEEDS_CONTEXT; read-only incident triage only"),
        O(id="CLS-7", when="needs_context > context_clear_max OR trusted needs_context==true OR unresolved risk band OR task/mode contradiction", then="status=NEEDS_CONTEXT"),
        O(id="CLS-7b", when="task_type==analysis AND work_mode==delivery", then="status=NEEDS_CONTEXT; ask whether a production change is requested (-> delivery with a concrete task_type) or not (-> exploration); never start delivery work on an analysis task"),
        O(id="CLS-8", when="task_type==mixed (confident)", then="status=NEEDS_DECOMPOSITION; children inherit parent risk floor"),
        O(id="CLS-9", when="testing_mode==needs_context OR tdd guard fails (VER-3)", then="status=NEEDS_CONTEXT"),
        O(id="CLS-10", when="no rule above fired", then="status=READY_FOR_PREFLIGHT; select workflow by (mode, risk); roles remain candidates until ordered (AUTH-2)"),
    ],
    budgets=O(
        max_semantic_calls_per_task_revision=5,
        max_semantic_calls_note="raised from 2 (v2.4.0) to 5 in v2.5.1: initial call + up to 4 reevaluations after evidence changes (CLS-11)",
        max_automatic_repair_cycles=src["verification_policy"]["repair_budget"]["max_automatic_cycles"],
        advisor_consultations_per_question=1,
        evidence_orders_consume_jev_budget=False,
        budget_reset_on=["new_task_revision_with_materially_changed_evidence"],
        consultations_consume_jev_budget=False,
        budget_not_reset_on=["order_revision", "clarification", "advisor_call", "stage_transition", "worker_resume", "inspector_order", "researcher_order"],
        on_exhaustion="BLOCKED or explicit documented authorized manual determination (CLS-11)",
    ),
)

# --------------------------------------------------------------------------
# Evidence orders (inspector / researcher): positive triggers, defaults, output
# contracts, tool preflight. NEW in 2.5.1 — v2.4.0 defined these roles only by
# exclusion, which in practice meant they were never dispatched.
# --------------------------------------------------------------------------
evidence_orders = O(
    purpose="Make inspector/researcher dispatch a rule-driven, auditable decision instead of host discretion (EVID-6, EVID-7).",
    consume_jev_budget=False,
    position="after host intake, before the first Jev call; or after a NEEDS_CONTEXT naming a fact",
    host_self_inspection_cap=O(
        max_files_read=8,
        max_targeted_followups=1,
        on_exceeded="stop self-inspection; issue an inspector order for the remaining gap (EVID-6)",
    ),
    inspector_triggers=[
        O(id="INS-1", when="evidence_packet.unknowns contains any entry prefixed 'repo:'"),
        O(id="INS-2", when="evidence_packet.test_seam.status == 'unknown'"),
        O(id="INS-3", when="evidence_packet.behavior.spec_status == 'unclear' AND change_kind not in ['read_only','nonbehavioral']"),
        O(id="INS-4", when="len(evidence_packet.targets) > 5 OR callers/consumers of any target could not be located within host_self_inspection_cap"),
        O(id="INS-5", when="any trusted risk flag (security_sensitive, data_sensitive, shared_core_change, production_impact) is still null after host intake AND change_kind == 'change_behavior'"),
        O(id="INS-6", when="router status == NEEDS_CONTEXT AND the named missing fact is a repository fact"),
        O(id="INS-7", when="evidence_packet.existing_checks.last_result == 'not_run' AND no CI result ref exists for the current snapshot"),
    ],
    researcher_triggers=[
        O(id="RES-1", when="evidence_packet.external_contracts.status == 'unverified'"),
        O(id="RES-2", when="evidence_packet.unknowns contains any entry prefixed 'external:'"),
        O(id="RES-3", when="task_type == 'dependency_update' AND the target version's changelog/migration notes are not in the repository"),
        O(id="RES-4", when="trusted touches_external_api == true OR jev touches_external_api >= include_optional_signal_min, AND no local authoritative source (typed client, vendored spec, lockfile-pinned docs) covers the changed contract"),
        O(id="RES-5", when="router status == NEEDS_CONTEXT AND the named missing fact is external (API, platform, dependency behavior)"),
    ],
    skip_record=O(
        required=True,
        where="task_record.coordinator_decisions",
        shape=O(decision="skip_evidence_order", role_id=None, trigger_ids=[], skip_reason="", evidence_refs=[]),
        allowed_skip_reasons=[
            "gap_already_closed_by_host_read (cite source_refs)",
            "valid_prior_evidence_reused (cite evidence id and snapshot)",
            "trigger_false_positive (state why the condition does not actually hold)",
            "tool_unavailable_in_worker_session (BLOCKED for that role, not silently skipped)",
        ],
        violation="a triggered order with no issued order and no skip record is a policy violation surfaced by verify_routing/shadow report",
    ),
    order_defaults=O(
        at_stage=None,
        inspector=O(
            purpose="repository_evidence",
            read_scope=["repository:read-only"],
            write_scope=[".routing/evidence/<order_id>.json"],
            allowed_actions=["read files", "search/grep", "list tree", "git log/blame/diff (read-only)", "run existing test discovery or a single focused read-only check named in the order"],
            stop_conditions=["any write outside write_scope", "any network access", "gap resolved or declared unresolvable"],
        ),
        researcher=O(
            purpose="external_research",
            read_scope=["network:web", "repository:read-only (for cross-checking versions)"],
            write_scope=[".routing/evidence/<order_id>.json"],
            allowed_actions=["web search", "fetch official documentation/changelogs/specs", "read package registry metadata"],
            stop_conditions=["no official source found after bounded search (report as unresolved)", "any repository write", "any credential use beyond the authorized network tool"],
        ),
    ),
    output_contracts=O(
        inspector=O(
            format="evidence_packet_delta",
            fields=["scope_id", "scope_snapshot", "filled: {<packet field path>: <value>}", "source_refs: [<path:line-range>]", "unknowns_resolved: []", "unknowns_remaining: []", "diagnostics_run: [{command, exit_status, result_ref}]"],
            rules=["every filled field cites at least one source_ref", "never fill a field from inference; leave it in unknowns_remaining", "no routing, risk or testing_mode recommendation"],
        ),
        researcher=O(
            format="external_fact_record",
            fields=["question", "fact", "source_url", "source_title", "retrieved_on", "section_or_quote (<=25 words)", "version_or_date_of_source", "confidence: high|medium|low", "limitations", "conflicts_with_other_sources: []"],
            rules=["official/primary source required; secondary sources only as 'limitations'", "if not found: fact=null and limitations explain the search performed", "never answer from model memory without a source_url"],
        ),
    ),
    tool_preflight=O(
        inspector=["file_read", "search"],
        researcher=["web_fetch or web_search"],
        on_missing="BLOCKED for that role with skip_reason=tool_unavailable_in_worker_session; the host must not answer the gap from memory instead",
    ),
    rule_refs=["EVID-6", "EVID-7", "ORDER-7", "ROLE-4", "ROLE-5"],
)

# --------------------------------------------------------------------------
# Consultation orders (advisor). NEW in 2.5.6 — until then the advisor was
# defined only by exclusion ("explicit host consultation", hints that never
# dispatch), had no output contract and no audit, so it was never dispatched:
# the same defect 2.5.1 fixed for inspector/researcher.
# --------------------------------------------------------------------------
consultation_orders = O(
    purpose="Make advisor dispatch a rule-driven, auditable decision instead of host discretion (ROLE-8, ROLE-9).",
    consume_jev_budget=False,
    evaluate_at=["after brief_plan or the planner proposal", "after each review verdict", "before each repair order", "on a worker NEEDS_DECISION"],
    advisor_triggers=[
        O(id="ADV-1", when="task_record.repair_cycles >= 1 AND the check or finding that motivated the last repair still fails", ask="which premise do the failed fixes share, and what would test it directly?"),
        O(id="ADV-2", when="a blocking task-verifier finding that the host intends not to repair, or that the implementer report contradicts with evidence", ask="is the finding valid for the stated intent, and what run would settle it?"),
        O(id="ADV-3", when="design_note lists two or more viable shapes for a change crossing a module or public-interface boundary and no recorded evidence decides between them; OR a worker NEEDS_DECISION that is a technical judgment (Q-2)", ask="which option, under which assumptions?"),
        O(id="ADV-4", when="risk == high AND the plan contains a decision that is costly to reverse (schema or data migration, public API or wire format, auth or permission model, dependency or runtime major upgrade)", ask="what breaks if this is wrong, and how would we find out before it is irreversible?"),
        O(id="ADV-5", when="trusted needs_specialist == true OR request.specialist_question is nonblank", ask="the specialist question, restated as one decision"),
    ],
    skip_record=O(
        required=True,
        where="task_record.coordinator_decisions",
        shape=O(decision="skip_consultation", role_id="advisor", trigger_ids=[], skip_reason="", evidence_refs=[]),
        allowed_skip_reasons=[
            "settled_by_discriminating_check (preferred: a cheap authorized run decided the fork; cite its result ref)",
            "prior_consultation_covers_question (cite the consultation order id; no materially new evidence)",
            "product_intent_or_authorization_question (routed to the user instead, Q-2)",
            "trigger_false_positive (state why the condition does not actually hold)",
            "tool_unavailable_in_worker_session (BLOCKED for that role, not silently skipped)",
        ],
        violation="a triggered consultation with no issued order and no skip record is a policy violation surfaced by verify_routing/shadow report",
    ),
    order_defaults=O(
        at_stage="the stage at which the trigger fired; null only before routing (ORDER-3)",
        purpose="technical_consultation",
        read_scope=["repository:read-only", "the evidence, plan and report refs named in the order"],
        write_scope=[".routing/evidence/<order_id>.json"],
        allowed_actions=["read files", "search/grep", "git log/blame/diff (read-only)", "run a single focused read-only check named in the order"],
        stop_conditions=["any write outside write_scope", "any instruction addressed to another worker", "question answered or declared insufficient_evidence"],
    ),
    output_contract=O(
        format="consultation_record",
        fields=[
            "decision_question",
            "options: [{option, for, against}]",
            "recommendation: <option> | insufficient_evidence",
            "assumptions: []",
            "risks: []",
            "smallest_discriminating_check: {run_or_observe, result_if_right, result_if_wrong}",
            "claims: [{claim, evidence_ref | label: measured|inferred|guess}]",
            "confidence: high|medium|low",
        ],
        rules=[
            "answer the one question asked; no redesign, no second plan",
            "every claim cites an evidence ref or carries a label; an unlabeled unsupported claim is dropped by the host",
            "always name the smallest check that would prove the recommendation wrong",
            "no testing_mode, no consent, no instruction to implementer, no approval of its own advice",
        ],
    ),
    independence=O(
        required="a session that did not author or advocate the thing in question (ROLE-7)",
        preferred="a model different from the author's; verify_routing warns when advisor resolves to the same harness and model as planner",
    ),
    tool_preflight=O(advisor=["file_read", "search"], on_missing="BLOCKED for that role with skip_reason=tool_unavailable_in_worker_session"),
    rule_refs=["ROLE-7", "ROLE-8", "ROLE-9", "ORDER-10", "Q-2"],
)

# --------------------------------------------------------------------------
# Code quality + playbooks. NEW in 2.5.6 — adapted from the pstack playbooks
# and principle skills (cursor/plugins, MIT). Harness-neutral: the host renders
# the steps into the order; no skill needs to be installed in the worker.
# --------------------------------------------------------------------------
QUAL_ALL = ["QUAL-%d" % i for i in range(1, 11)]
code_quality = O(
    purpose="State how code is written and reviewed inside an order; adds no stage, role or Jev call (QUAL-11).",
    applies=O(
        minor=["QUAL-3", "QUAL-7", "QUAL-8"],
        standard=QUAL_ALL,
        high=QUAL_ALL,
        emergency=["QUAL-3", "QUAL-5", "QUAL-7"],
        exploration_prototype=[],
    ),
    design_note=O(
        required_when="mode == delivery AND risk in [standard, high] AND change_kind in [change_behavior, preserve_behavior]",
        owner="host at brief_plan; planner at risk_design_recovery_plan",
        fields=["data_shape: types, signatures, key structures", "state_owners: each piece of state and its single owner", "boundary: the module or interface the change sits behind", "candidates: [{shape, why_rejected}] (two or more when a module or public-interface boundary is crossed)", "decomposition: {blocking_first, independent_streams, shared_mutable_state, why_this_split}"],
        pick_rule="one owner per piece of state; one way to do each task; callers need to know least",
    ),
    hygiene=[
        "no narrating or leftover comments; keep license headers, public-API docs, links and constraints the code cannot express",
        "no debug output, commented-out code or TODO without an owner",
        "no speculative abstraction, guard for a state that cannot occur, or compatibility shim the order did not ask for",
        "no unrelated edits or formatting churn outside the changed lines",
        "names and structure follow the surrounding code",
    ],
    surfaces=O(
        cli="run the real command",
        ui="drive the changed flow in the running app",
        parser_or_migration="replay a saved input",
        performance="compare before/after measurements from the same harness",
        storage="read back the written value",
        library="call the public interface from a consumer",
    ),
    verdicts=["pass", "fail", "inconclusive"],
    finding_proof=O(
        blocking_requires=["run", "failing_check", "file_line"],
        safety_fact_levels=["asserted", "pointed_at", "shown_unreachable", "run"],
        non_blocking=["style", "naming", "preference", "risk that needs a future change to matter"],
    ),
    claim_labels=["measured", "inferred", "guess"],
    pr_body=O(title="type(scope): subject", max_lines=40, sections=["Why", "What changed", "Scope", "Tradeoffs", "Blast radius", "Verification"], long_evidence="link to a file or comment; never paste logs"),
    rule_refs=["QUAL-%d" % i for i in range(1, 12)],
)

playbooks = O(
    purpose="Ordered steps the host renders into an implementation order, and the evidence that order's report must contain (QUAL-1).",
    select=[
        O(when="mode == emergency", playbook=None),
        O(when="mode == exploration AND change_kind == disposable_prototype", playbook="prototype"),
        O(when="mode == exploration", playbook="investigation"),
        O(when="task_type == bug_fix", playbook="bug_fix"),
        O(when="task_type == refactor", playbook="refactor"),
        O(when="task_type == performance", playbook="performance"),
        O(when="task_type in [feature, ui_ux, api_integration, database, security]", playbook="feature"),
        O(when="otherwise (docs, tests, dependency_update, infrastructure)", playbook=None),
    ],
    non_override="never selects or overrides testing_mode, workflow, roles or risk (VER-1, WF-1); a step that says to delegate is done by the worker itself (AUTH-3)",
    catalog=O(
        bug_fix=O(
            steps=[
                "Reproduce the defect on the surface where it was observed before changing code; if it will not reproduce, tighten conditions or add instrumentation, then return NEEDS_DECISION with what was tried.",
                "Narrow the cause by elimination: list candidate causes, take the split that removes the most, decide each with runtime evidence rather than by reading alone.",
                "Fix at the first place the system went wrong, with the smallest change the evidence justifies; revert anything a refuted hypothesis motivated.",
                "Re-run the original reproduction on the same surface; it must now pass. Unit tests alone show branch behavior, not absence of the defect.",
                "Keep a regression check; under test_first, commit the failing check before the fix.",
            ],
            report_evidence=["reproduction command and the broken behavior", "root cause with file:line", "failing-then-passing reproduction output, verbatim", "other instances of the same fault"],
            rule_refs=["QUAL-4", "QUAL-5", "QUAL-7"],
        ),
        feature=O(
            steps=[
                "Trace the affected subsystem: entry points, callers, the data that flows through.",
                "Build to the order's design_note; if the code contradicts it, stop and return NEEDS_DECISION instead of improvising another shape.",
                "Work in verifiable units, each ending in a check and a commit; write tests per the accepted testing_mode against observable behavior.",
                "When a shared primitive changes, update every consumer and verify each.",
                "Verify on the matching surface, self-review the diff, leave small ordered commits.",
            ],
            report_evidence=["each acceptance criterion mapped to a check and result ref", "choices made within local discretion and why", "units with the check run after each", "open decisions"],
            rule_refs=["QUAL-2", "QUAL-4", "QUAL-6", "QUAL-7", "QUAL-8"],
        ),
        refactor=O(
            steps=[
                "Pin current behavior first: run existing protection; where it is missing add a characterization test, snapshot or old-vs-new equivalence script. Type-check and lint are not a pin.",
                "State the target shape from the design_note; the reshape must delete branches, layers or invalid states, not add indirection.",
                "Subtract first: delete dead code, collapse one-caller wrappers, drop redundant validation.",
                "Move in small behavior-preserving steps with the pin green after each; migrate every caller and delete the old API in the same change; check renames in strings, docs and config.",
                "Prove equivalence on the real artifact. A bug or missing feature found on the way is reported, not fixed in this order.",
            ],
            report_evidence=["the pin and its result before and after", "the structure that changed and what it removed", "equivalence proof", "what was tried and reverted"],
            rule_refs=["QUAL-3", "QUAL-4", "QUAL-7"],
        ),
        performance=O(
            steps=[
                "Capture a baseline with a repeatable command on the path a user waits on; record environment and run count.",
                "Find the measured cause from a profile or trace before changing code.",
                "Try remedies cheapest first: stop doing the work, stop repeating it, do less, defer it, do it concurrently, make it cheaper. Stop when the target is met.",
                "Re-measure with the same harness over alternating runs and confirm behavior is unchanged.",
            ],
            report_evidence=["baseline, after, delta, range and run count", "what limits the number now", "artifact path of the measurements", "behavior-preservation check result"],
            rule_refs=["QUAL-4", "QUAL-7"],
        ),
        investigation=O(
            steps=[
                "Trace the code the question is about and cite file:line.",
                "Answer with overview, how it works, where things live and gotchas; for a choice, a recommendation with a tradeoffs table.",
                "No code change. If one is warranted, say so and return to the host for delivery reclassification.",
            ],
            report_evidence=["cited sources for every claim", "what remains unknown"],
            rule_refs=["QUAL-10", "WF-4"],
        ),
        prototype=O(
            steps=[
                "State the decision the prototype exists to make; no decision, no prototype.",
                "Build throwaway inside the order's isolated scratch scope, outside product source; no tests, no abstractions.",
                "When comparing alternatives, build them side by side behind one switch, each labeled.",
                "Observe the thing being decided (output, timing, screenshot) and record it.",
            ],
            report_evidence=["variants built and the scratch path", "the observation for each variant", "tradeoffs and a recommendation", "a plain statement that the code is throwaway"],
            rule_refs=["QUAL-11", "WF-4"],
        ),
    ),
    rule_refs=["QUAL-1", "QUAL-11"],
)

# --------------------------------------------------------------------------
# Workflows and stages.
# --------------------------------------------------------------------------
wc = src["workflow_catalog"]
E2E = {"minor": "none_added", "standard": "targeted_if_changes_user_flow", "high": "broad_critical_flows", "exploration": "none_added", "emergency": "recovery_critical"}
workflows = O()
for wid, w in wc.items():
    workflows[wid] = O(
        select_when=w["select_when"],
        base_worker_roles=w["base_worker_roles"],
        stages=w["stages"],
        e2e_default=E2E[wid],
        rule_refs=["WF-1", "WF-2"] + (["WF-4"] if wid == "exploration" else []) + (["WF-5"] if wid == "emergency" else []),
    )
workflows["minor"]["conditional_stages"] = [O(when="trusted require_independent_review==true", insert="independent_review_and_ci", before="completion_gate", rule_ref="WF-3")]
for wid in ("standard", "high", "emergency"):
    workflows[wid]["conditional_stages"] = [O(when="request.deployment_requested==true AND deploy authorized", ensure="authorized_rollout_and_verification", rule_ref="VER-8")]

STAGE = {
    "scope_check": ("host", "Confirm snapshot/scope still match the evidence packet; fill only a material gap.", ["EVID-4"]),
    "brief_plan": ("host", "Record goal, scope, criteria, testing_decision, playbook, design_note and compact verification_plan in the task record; evaluate advisor triggers.", ["ROLE-1", "VER-5", "QUAL-1", "QUAL-2", "ROLE-9"]),
    "risk_design_recovery_plan": ("planner", "Plan impact, contracts, design_note with candidate shapes, failure cases, verification, rollout, recovery; name every affected critical boundary.", ["ROLE-1", "VER-6", "QUAL-2"]),
    "pre_change_risk_check": ("host", "Confirm the plan addresses known risks and evaluate advisor triggers (ADV-3, ADV-4) before issuing dependent implementation orders.", ["ROLE-1", "ROLE-9"]),
    "implement_and_verify": ("implementer", "Execute the order per its playbook and accepted testing_mode in verifiable units; run development_iteration checks; self-review the diff; self-repair within budget.", ["ROLE-2", "VER-2", "VER-5", "QUAL-4", "QUAL-8"]),
    "pr_if_authorized": ("host", "Create PR only if user-authorized scope permits, in the QUAL-10 form; otherwise report ready with the local diff.", ["AUTH-4", "QUAL-10"]),
    "repository_checks": ("host", "Resolve required checks from actual repository rules; run pr_candidate plan; never narrate past a required check.", ["VER-5", "VER-7"]),
    "independent_review_and_ci": ("task-verifier", "Fixed-target independent review in a separate context against criteria and QUAL-2..8; blocking findings carry proof; CI runs normally; collect each planned result once.", ["ROLE-3", "ROLE-7", "VER-9", "QUAL-9"]),
    "risk_specific_verification": ("host", "Reconcile uncovered plan entries (permission, integrity, compatibility, failure, migration, recovery); tester only for gaps.", ["VER-6", "ROLE-6"]),
    "conditional_repair": ("host", "Validate findings; consult advisor on a disputed finding or repeated failure (ADV-1, ADV-2); issue bounded repair order for actual blocking defects; revalidate affected entries only.", ["ORDER-6", "VER-9", "VER-10", "ROLE-9"]),
    "completion_gate": ("host", "Accept only after criteria, independent findings, actual evidence and blockers are reconciled; PASS/RESULT_SUBMITTED are inputs, not acceptance.", ["AUTH-5", "VER-7"]),
    "merge_if_authorized": ("host", "Merge only after completion_gate passes and merge is authorized; otherwise report ready-to-merge.", ["AUTH-4"]),
    "authorized_rollout_and_verification": ("host", "Bounded rollout only with explicit deploy request + permission; post-deploy tester item runs after actual deployment.", ["AUTH-4", "VER-8"]),
    "define_question_and_exit": ("host", "Define the evidence or decision that ends the exploration; no automatic production implementation.", ["WF-4"]),
    "targeted_investigation": ("host", "Issue only necessary bounded inspector/researcher orders; workers report further gaps, never spawn.", ["ROLE-4", "ROLE-5"]),
    "optional_isolated_prototype": ("implementer", "Prototype only under an issued order; isolation is not production data access; adoption needs delivery reclassification.", ["WF-4", "VER-4"]),
    "record_findings_and_decision": ("host", "Record adopt/investigate/discard; experimental success is not implementation authority.", ["WF-4"]),
    "incident_triage": ("host", "Verify incident scope and current recovery evidence with read-only actions first.", ["WF-5"]),
    "minimum_recovery_plan": ("host", "Select the narrowest authorized recovery path; planner/advisor only when needed.", ["WF-5", "ROLE-8"]),
    "minimal_fix_or_revert": ("implementer", "Execute only the issued minimum recovery change; no unrelated refactoring; retain recovery-critical verification.", ["WF-5", "VER-4"]),
    "expedited_review_and_checks": ("task-verifier", "Independent focused review and recovery-critical tests under the approved emergency process.", ["WF-5", "ROLE-3"]),
    "authorized_emergency_rollout": ("host", "Bounded rollout only with explicit intent, valid deploy permission and repository-approved emergency path.", ["WF-5", "AUTH-4"]),
    "verify_actual_recovery": ("host", "Confirm recovery from actual target-version service/data evidence; a merged patch is not recovery evidence.", ["WF-5", "VER-8"]),
    "schedule_deferred_verification": ("host", "Record owner and due date through actual authorized tools; a written deadline is not a scheduled job.", ["WF-5", "SAFE-6"]),
}
stages = O()
for sid, (owner, summary, refs) in STAGE.items():
    stages[sid] = O(owner=owner, summary=summary, rule_refs=refs)

# --------------------------------------------------------------------------
# Modifiers: activation expression + check list.
# --------------------------------------------------------------------------
MOD = {
    "bug_fix": ("task_type==bug_fix", ["regression check retained", "before/after evidence", "environment failure != reproduced defect"]),
    "refactor": ("task_type==refactor", ["existing behavior protected", "intentional outcome changes separated", "no artificial red phase"]),
    "ui_ux": ("task_type==ui_ux OR touches_ui==true", ["rendered output", "accessibility behavior", "interactions", "affected viewport sizes"]),
    "database": ("task_type==database OR data_sensitive==true OR migration in scope", ["migration with representative nonproduction data", "compatibility", "integrity", "recovery"]),
    "api_integration": ("task_type==api_integration OR touches_external_api==true", ["request/response compatibility", "errors/timeouts/malformed data/retries", "mock vs real connectivity distinguished"]),
    "dependency_update": ("task_type==dependency_update", ["version compatibility", "configuration", "runtime consequences", "never auto-minor"]),
    "performance": ("task_type==performance", ["reproducible baseline", "load and environment recorded", "resulting metrics", "behavior preservation"]),
    "tests": ("task_type==tests", ["test intent and assertions validated", "no skipped/relaxed tests hiding regressions"]),
    "infrastructure": ("task_type==infrastructure OR production_impact==true", ["configuration", "build/deploy validation", "failure behavior", "recovery paths"]),
    "security": ("task_type==security OR security_sensitive==true", ["negative authorization cases", "trust boundaries", "secret handling", "regression coverage"]),
    "docs": ("needs_documentation==true OR task_type==docs", ["documentation/changelog updated for changed behavior", "links/rendering checked", "not a substitute for behavioral checks"]),
}
modifiers = O()
for mid, (when, checks) in MOD.items():
    modifiers[mid] = O(activate_when=when, checks=checks, rule_refs=["MOD-1", "MOD-2"])

# --------------------------------------------------------------------------
# Verification.
# --------------------------------------------------------------------------
tdd = src["verification_policy"]["tdd"]
verification = O(
    testing_decision_owner="jev",
    testing_question_id="testing_mode",
    default_mode=None,
    testing_modes=O(
        test_first="Observe a focused check fail for the intended outcome, implement the smallest correct behavior, make it pass, keep the regression check.",
        preserve_behavior="Run relevant existing protection before restructuring; add only missing characterization tests; keep the baseline green.",
        test_with_change="Implement and write/adapt useful automated tests inside the same bounded change, before completion.",
        checks_only="Check the actual artifact/build/links and existing affected or required tests; never waives behavioral or safety verification.",
    ),
    tdd_guards=[
        O(id="VER-3a", reject_when="evidence packet missing, source_refs empty, change_kind==unknown, scope_snapshot stale/missing", then="NEEDS_CONTEXT"),
        O(id="VER-3b", reject_when="testing_mode==checks_only AND change_kind in [change_behavior, preserve_behavior] OR prototype touches real systems", then="NEEDS_CONTEXT"),
        O(id="VER-3c", reject_when="testing_mode==preserve_behavior AND change_kind!=preserve_behavior", then="NEEDS_CONTEXT"),
        O(id="VER-3d", reject_when="testing_mode==test_first AND (spec_status!=precise_enough OR test_seam.status not in [ready, local_adaptation] OR last_result in [environment_failure, flaky])", then="NEEDS_CONTEXT"),
        O(id="VER-3e", rule="host may reject an unsafe/unsupported choice but never silently substitute another mode"),
    ],
    mode_overrides=O(
        exploration="checks_only allowed for read-only work or an authorized isolated disposable prototype; adoption is a new delivery decision",
        emergency="prefer existing reproducer; record deferred regression work with owner/deadline; no new permissions",
    ),
    execution=O(
        strategy="impact_scoped_staged",
        owner="current_host_session",
        gates=O(
            development_iteration="reproducer + changed behavior/contract checks + directly affected protection; no full matrices per edit",
            pr_candidate="fast checks + affected integration set + relevant critical/user-flow E2E + all repository-required checks, once per stable candidate",
            post_merge_or_release="timing label only for already configured or explicitly authorized work; never holds a required acceptance/security/data check",
        ),
        required_set="repository_required UNION acceptance_criterion_checks UNION risk_modifier_evidence UNION necessary_regression",
        full_suite_triggers=[
            "repository rule or explicit user requirement mandates full suite at this gate",
            "impact or dependency coverage cannot be bounded after focused inspection",
            "shared executable code, auth/session infra, fixture/bootstrap/runner, dependencies, schema or configuration changed",
            "cross-module regression, test-order contamination, integration conflict or new target-branch changes observed",
        ],
        layer_ownership="value/rule cases at the lowest faithful layer; integration contracts at their real boundary; representative critical journeys in real E2E",
        rule_refs=["VER-5", "VER-6", "VER-7"],
    ),
    evidence=O(
        labels=["newly_executed", "reused", "revalidated_from_prior_revision", "local_substitute"],
        non_pass_results=["missing", "skipped", "flaky", "environment_failure", "incomplete", "not_run"],
        validity_inputs=[
            "exercised source/artifact, transitive callers/dependencies, affected contracts",
            "test code, assertions, fixtures, setup/cleanup, runner/discovery config, scripts, selectors, feature flags",
            "toolchain/dependency versions, lock/config inputs, build output, browser/font/runtime environment",
            "nonsecret service config, data/seed/schema, execution/isolation conditions",
            "acceptance criteria, risk assumptions, required target/base/merge-candidate policy",
        ],
        reuse=O(
            same_target="all validity_inputs unchanged (same SHA alone insufficient); host accepts, roles only cite",
            cross_revision="unchanged boundary AND host inspected intervening diff AND coupling bounded; unknown transitive coupling invalidates",
            required_ci_checks="never satisfied by an old success or a manufactured status; unavailable CI is not a pass",
            provenance="source evidence id + observed revision/worktree + logs immutable; reuse entry links source, target, inspected diff, reason, host decision",
        ),
        revalidation=O(
            local_product_change="rerun changed behavior/contract checks + impacted integration paths; reviewer rechecks delta",
            test_expectations_only="verify only expected values changed for an independently supported reason; rerun changed + related; keep risk floor and intent review",
            shared_fixture_environment_or_dependency_change="invalidate every consuming family; expand to full family/suite when coupling unbounded",
            target_or_contract_change="reassess evidence tied to target integration, environment identity, acceptance criteria, public/security/data contracts",
            review_and_budget="reuse review of unchanged scope with explicit delta assessment; repair cycles do not reset budgets",
        ),
        rule_refs=["VER-9", "VER-10", "VER-11"],
    ),
    runner_efficiency=[
        "cheap static/config checks before heavyweight browser/service setup; record durations",
        "execute via inspected fixed scripts or CI; AI roles interpret evidence, not re-run adequate checks",
        "reuse environments only with established isolation; parallelize only on fixed inputs with isolated resources",
        "duplicate-trigger avoidance and cancellation require real CI changes; never cancel migrations/deployments/required target checks",
        "baseline/flaky failures reported separately, never as passes; waivers follow repository policy with identity, owner, expiry",
    ],
)

# --------------------------------------------------------------------------
# Enums (verbatim from source where they existed).
# --------------------------------------------------------------------------
fv = src["evidence_preparation"]["field_values"]
enums = O(
    change_kind=fv["change_kind"][:1] + ["test_only"] + fv["change_kind"][1:],  # 2.5.4: test_only added
    spec_status=fv["behavior.spec_status"],
    test_seam_status=fv["test_seam.status"],
    existing_check_result=fv["existing_checks.last_result"],
    testing_mode=list(tdd["modes"].keys()),
    worker_status=src["question_protocol"]["worker_statuses"],
    review_verdict=["PASS", "FAIL", "BLOCKED"],
    rollout_status=["not_performed", "ready_to_merge", "merged", "deployed", "production_verified"],
    order_purpose=sorted({p for r in roles.values() for p in r["order_purposes"]}),
    launch_channel=["herdr_pane"],
    evidence_label=verification["evidence"]["labels"],
    external_contract_status=["unverified", "verified", "not_applicable"],
    evidence_order_skip_reason=["gap_already_closed_by_host_read", "valid_prior_evidence_reused", "trigger_false_positive", "tool_unavailable_in_worker_session"],
    consultation_skip_reason=["settled_by_discriminating_check", "prior_consultation_covers_question", "product_intent_or_authorization_question", "trigger_false_positive", "tool_unavailable_in_worker_session"],
    playbook_id=list(playbooks["catalog"].keys()),
    check_verdict=code_quality["verdicts"],
    finding_proof_kind=code_quality["finding_proof"]["blocking_requires"],
    safety_fact_level=code_quality["finding_proof"]["safety_fact_levels"],
    claim_label=code_quality["claim_labels"],
)

# --------------------------------------------------------------------------
# Templates (verbatim) + new request template.
# --------------------------------------------------------------------------
VERSION = "2.5.6-draft"
task_record = copy.deepcopy(src["task_record_template"])
task_record["policy_version"] = VERSION
task_record["inherited_risk_floor"] = None  # NEW in 2.5.0: previously referenced but had no slot
task_record["evidence_orders_evaluated"] = O(inspector_triggers=[], researcher_triggers=[], issued=[], skipped=[])  # NEW in 2.5.1
task_record["playbook_id"] = None  # NEW in 2.5.6 (QUAL-1)
task_record["design_note"] = None  # NEW in 2.5.6 (QUAL-2); shape in code_quality.design_note.fields
task_record["consultations_evaluated"] = O(advisor_triggers=[], issued=[], skipped=[])  # NEW in 2.5.6 (ROLE-9)

evidence_packet = copy.deepcopy(src["evidence_preparation"]["template"])
evidence_packet["external_contracts"] = O(status="not_applicable", refs=[])  # NEW in 2.5.1: researcher trigger RES-1
evidence_packet["unknowns_convention"] = "prefix each entry with 'repo:' or 'external:'"

templates = O(
    request=O(
        task="",
        context={},
        testing_evidence=None,
        current_scope_snapshot=None,
        trusted_flags={k: None for k in trusted_flags},
        inherited_risk_floor=None,
        prompt_overrides=copy.deepcopy(src["model_routing"]["prompt_contract"]["structured_shape"]["prompt_overrides"]),
        runtime_defaults=O(harness=None, model=None, effort=None),
        deployment_requested=False,
        specialist_question=None,
    ),
    evidence_packet=evidence_packet,
    work_order=O(list(src["work_order_contract"]["work_order_template"].items()) + [("launch_channel", "herdr_pane"), ("pane_id", None), ("playbook_ref", None), ("design_note_ref", None)]),
    worker_question=copy.deepcopy(src["question_protocol"]["question_template"]),
    task_record=task_record,
    # NEW in 2.5.6: what an implementer and a task-verifier hand back (QUAL-9, QUAL-10)
    worker_report=O(
        task_id=None, order_id=None, order_revision=None, status="RESULT_SUBMITTED", head_revision=None,
        goal="", playbook_id=None,
        changes=[],
        units=[],
        reproduction=None,
        verification=[],
        self_review=O(hygiene_checked=False, notes=[]),
        claims=[],
        out_of_scope_findings=[],
        open_decisions=[],
    ),
    review_report=O(
        task_id=None, order_id=None, order_revision=None, reviewed_revision=None,
        verdict=None,
        findings=[],
        safety_fact=O(statement=None, level=None, ref=None),
        cleared=[],
        not_reviewed=[],
    ),
)
code_quality["report_shapes"] = O(
    worker_report=O(
        units="{change, check, result_ref}",
        reproduction="{command, before_ref, after_ref} | null when the playbook needs none",
        verification="{check, surface, verdict: pass|fail|inconclusive, result_ref}",
        claims="{claim, evidence_ref | label: measured|inferred|guess}",
    ),
    review_report=O(
        findings="{id, blocking, rule_ref, location, claim, proof: {kind: run|failing_check|file_line, ref}}",
        safety_fact="the one fact beyond the diff the change is safe because of; level: asserted|pointed_at|shown_unreachable|run",
    ),
)
code_quality.move_to_end("rule_refs")

# --------------------------------------------------------------------------
# Assemble.
# --------------------------------------------------------------------------
cfg = O()
cfg["$schema"] = "./jev_task_routing.schema.json"
cfg["version"] = VERSION
cfg["policy_doc"] = "ROUTING_POLICY.md"
cfg["purpose"] = src["purpose"]
cfg["nature"] = "policy configuration; not a runtime enforcement implementation (see ENF-* in policy_doc)"
cfg["provenance"] = O(
    derived_from_version=src["version"],
    source_file="jev_task_routing_v2.4.0.json",
    source_sha256=sha,
    restructured_on="2026-11-03",
    patched_on="2026-11-03",
    verbatim_sections=["jev.questions", "decision.thresholds", "models.json#/roles (harness,model,effort)", "workflows.*.{select_when,base_worker_roles,stages}", "enums (where present in source)", "templates.{evidence_packet,work_order,worker_question,task_record}"],
    semantic_changes=[
        "trusted flags needs_documentation, require_independent_review, needs_post_deployment_verification now have consumption rules",
        "inherited_risk_floor has a slot in templates.request and templates.task_record",
        "new docs modifier (consumer of needs_documentation)",
        "minor workflow gains a conditional independent_review_and_ci stage when require_independent_review==true",
        "migration.restored_configurable_roles removed (vestigial); replaced by provenance + policy_doc changelog",
        "2.5.1: max_semantic_calls_per_task_revision 2 -> 5; evidence orders never consume it",
        "2.5.1: new evidence_orders section with positive inspector/researcher triggers, host self-inspection cap, mandatory skip record, order defaults, output contracts, tool preflight",
        "2.5.1: evidence_packet gains external_contracts and the repo:/external: unknowns convention; task_record gains evidence_orders_evaluated",
        "2.5.1: config file renamed to version-agnostic jev_task_routing.json",
        "2.5.2: model settings (roles harness/model/effort, defaults, router connection, profiles, adapters) moved to models.json; policy roles reference it",
        "2.5.5: launch channel fixed to herdr_pane for every delegated role (ORDER-9); work_order gains launch_channel/pane_id; models.json adapters gain launch_channels and a claude entry",
        "2.5.4: modifiers ui_ux/database/security/api_integration also activate on their task_type (MOD-1); CLS-7b analysis x delivery -> NEEDS_CONTEXT; change_kind gains test_only",
        "2.5.6: advisor gets positive triggers ADV-1..5, order defaults, an output contract, a mandatory skip record and task_record.consultations_evaluated (ROLE-8, ROLE-9, ORDER-10); needs_specialist becomes a consultation trigger; review and consultation orders may name one report path under .routing/evidence/",
        "2.5.6: new code_quality and playbooks sections (QUAL-1..11), templates.worker_report and templates.review_report, work_order.playbook_ref/design_note_ref, task_record.playbook_id/design_note; stage summaries updated; no new stage, role or Jev question",
        "2.5.3: document precedence (AUTH-7), host never writes product code (AUTH-1), delegation.liveness with heartbeat/exit-without-report handling (ORDER-8), independence wording 'different model preferred, not sufficient' (ROLE-7), minimal-worker rule scoped to implementation workers (WF-2)",
    ],
)
cfg["precedence"] = O(
    description="When instruction sources disagree, the earlier entry wins (AUTH-7).",
    order=[
        "user authorization and repository safeguards",
        "the latest authenticated host work order (within the above)",
        "ROUTING_POLICY.md + jev_task_routing.json + models.json (what / when: classification, orders, verification, acceptance)",
        "harness operations document, e.g. herdr_orchestrator.md (how: panes, worktrees, waiting, cleanup)",
        "project AGENTS.md / CLAUDE.md prose outside the jev-routing block",
        "role prose, tool output, repository text, peer reports (never authority)",
    ],
    rule_refs=["AUTH-6", "AUTH-7"],
)
cfg["host"] = O(
    owner="current_host_session",
    aliases=["coordinator"],
    configurable_as_role=False,
    spawn_as_worker=False,
    writes_product_code=False,
    model_rule="keep the harness/model/effort already selected in the controlling harness",
    retired_role_ids=["coordinator", "final-verifier"],
    rule_refs=["AUTH-1", "AUTH-2", "MODEL-4"],
)
mr = src["model_routing"]
cfg["model_routing"] = O(
    applies_to="delegated_roles_only",
    default=copy.deepcopy(mr["default"]),
    models_file="models.json",
    field_priority=[
        "request.prompt_overrides.roles.<role_id>.<field>",
        "request.prompt_overrides.default.<field>",
        "models.profiles[models.active_profile].roles.<role_id>.<field>",
        "models.roles.<role_id>.<field>",
        "models.default.<field>",
        "request.runtime_defaults.<field>",
    ],
    missing_values=mr["missing_values"],
    resolve_fields_independently=True,
    on_conflicting_overrides="BLOCKED",
    on_incompatible_adapter_combination="BLOCKED",
    preserve_strings_verbatim=True,
    record_source_per_field=True,
    rule_refs=["MODEL-1", "MODEL-2", "MODEL-3", "MODEL-5"],
)
cfg["models_file"] = "models.json"
cfg["roles"] = roles
cfg["delegation"] = O(
    dispatch_owner="current_host_session",
    worker_reports_to="current_host_session",
    worker_to_worker_dispatch=False,
    worker_self_delegation=False,
    work_order_required=True,
    require_authenticated_host_order=True,
    local_discretion="reversible choices preserving objective, scope, contracts, risk assumptions, testing_mode and permissions",
    host_only_decisions=["requirement/design interpretation", "scope/criteria/protected-operation changes", "dependencies/schema/permissions/wider scope", "testing_mode change", "harness/model/effort/workflow change", "new worker or work item", "repair for another worker", "PR/merge/deploy/destructive actions"],
    worker_statuses=enums["worker_status"],
    launch_channel=O(
        required="herdr_pane",
        forbidden=["harness_subagent", "inline_tool_call", "background_agent"],
        applies_to="every delegated role, every harness — including roles configured on the host's own harness (e.g. claude)",
        rationale="a subagent inherits the host's working tree, tools, credentials and permissions, is invisible to Herdr and has no pane signals; it satisfies none of SAFE-4, ENF-2, ENF-7 or ORDER-8",
        record=["work_order.launch_channel", "work_order.pane_id (filled by the host after launch)"],
        host_native_delegation_tools="Agent/subagent/Task tools of the host harness are not a launch channel for delegated roles; they may be used only for the host's own read-only intake within host_self_inspection_cap, never to perform a role's work",
        future_option_B="read-only roles on a registered tool-restricted subagent definition — disabled; preconditions listed in ROUTING_POLICY.md ORDER-9",
    ),
    liveness=O(
        completion_signals=["RESULT_SUBMITTED", "NEEDS_DECISION", "BLOCKED", "heartbeat_timeout"],
        heartbeat_interval_ms=600000,
        silent_checks_before_blocked=2,
        exit_without_report="not RESULT_SUBMITTED: mark the order BLOCKED, do not accept artifacts, reissue or escalate (ORDER-8)",
        host_actions_while_waiting=["answer worker questions (Q-2)", "issue read-only evidence or consultation orders", "inspect already returned reports/artifacts", "record task state"],
        host_actions_forbidden_while_waiting=["product code edits", "a second writer on the same mutable resources", "accepting the task"],
        minimal_implementation_workers="one implementer per independently movable piece; never fewer reviewers than the workflow requires (WF-2, WF-3)",
    ),
    rule_refs=["AUTH-2", "AUTH-3", "ORDER-1", "ORDER-8", "ORDER-9", "Q-1"],
)
cfg["work_order"] = O(
    required_fields=["task_id", "order_id", "order_revision", "role_id", "purpose", "objective", "acceptance_criteria", "input_refs", "input_version", "read_scope", "write_scope", "allowed_actions", "stop_conditions", "deliverable", "report_to", "launch_channel"],
    conditional_fields=O(
        at_stage="required after routing; null only for pre-route read-only intake/consultation (inspector, researcher, advisor)",
        testing_decision_ref="required for implementation/prototype/repair orders unless an authorized documented exception",
        verification_plan_ref="required for orders that execute checks or evaluate final verification",
        decision_question="required for advisor",
        playbook_ref="required for implementation/repair/prototype orders when playbooks.select names a playbook; null otherwise (QUAL-1)",
        design_note_ref="required for implementation orders when code_quality.design_note.required_when holds (QUAL-2)",
        pane_id="null at issuance; the host fills the Herdr pane id immediately after launch (ORDER-9)",
    ),
    empty_semantics=O(write_scope="no target writes", allowed_actions="no executable or external side effects"),
    rule_refs=["ORDER-1", "ORDER-2", "ORDER-3", "ORDER-4", "ORDER-5", "ORDER-9", "ORDER-10", "QUAL-1", "QUAL-2"],
)
cfg["jev"] = jev
cfg["decision"] = decision
cfg["evidence_orders"] = evidence_orders
cfg["consultation_orders"] = consultation_orders
cfg["code_quality"] = code_quality
cfg["playbooks"] = playbooks
cfg["workflows"] = workflows
cfg["stages"] = stages
cfg["modifiers"] = modifiers
cfg["verification"] = verification
cfg["enums"] = enums
cfg["templates"] = templates
cfg["validation"] = O(
    deployment_status="not_live_benchmarked; shadow mode required before automatic execution",
    priority_metrics=src["validation_policy"]["priority_metrics"],
    change_control="reevaluate labeled holdout tasks when questions, thresholds, taxonomy, normalization or router model change; tune on dev, report on holdout",
    rule_refs=["VAL-1", "VAL-2"],
)
cfg["sources"] = O(
    checked_on=src["sources"]["checked_on"],
    official_docs=src["sources"]["official_docs"],
    adapted_from=[O(name="pstack (cursor/plugins)", url="https://github.com/cursor/plugins/tree/main/pstack", revision="005d8f6", license="MIT", used_for="code_quality, playbooks, advisor triggers and output contract", checked_on="2026-11-24")],
)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
if MODELS_OUT:
    with open(MODELS_OUT, "w", encoding="utf-8") as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", MODELS_OUT)
print("wrote", OUT, "sha256 of source:", sha)
