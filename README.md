# jev_task_routing

멀티 에이전트 코딩 파이프라인용 **작업 라우팅·거버넌스 정책**입니다. 호스트 세션(코디네이터)이 Jev(TypeSafe 의미 분류기)로 작업을 분류하고, 리스크에 맞는 최소 워크플로를 고른 뒤, 범위가 제한된 작업 지시서로만 워커를 움직이게 합니다.

> 이 저장소는 **정책**입니다. 그 자체로는 아무것도 실행하거나 강제하지 않습니다. 실제 강제는 호스트 실행기가 구현해야 하며(ROUTING_POLICY.md §11 ENF), 그 전까지는 섀도 모드로만 운용합니다.

## 구성

| 파일 | 내용 |
|---|---|
| `jev_task_routing.json` | 기계 판독용 정책(버전은 파일 안 `version`) — 임계값, 7개 역할의 권한·발동 조건, 워크플로·스테이지, Jev 14문항 루브릭, inspector/researcher 트리거, 템플릿. **모델 설정은 없음** |
| `models.json` | **모델 설정의 유일한 위치** — 역할별 harness/model/effort, 기본값, 프로필(`standard`, `high_assurance`), 라우터(Jev) 연결 정보, 어댑터별 허용 effort |
| `models.schema.json` | `models.json`의 JSON Schema |
| `resolve_models.py` | 역할별 최종 harness/model/effort와 그 출처(오버라이드/프로필/역할/기본값)를 출력하고 어댑터 preflight 수행 |
| `jev_task_routing.schema.json` | 설정 파일과 런타임 객체(request, evidence_packet, work_order, worker_question, task_record)의 JSON Schema |
| `ROUTING_POLICY.md` | 규칙 ID(AUTH·MODEL·ROLE·ORDER·Q·EVID·CLS·WF·MOD·VER·SAFE·ENF·VAL) 단일 출처 문서. JSON의 `rule_refs`가 여기를 가리킴 |
| `AGENTS_ROUTING.md` | 프로젝트의 CLAUDE.md / AGENTS.md에 삽입되는 호스트 지시 블록 |
| `repo_checks.example.json` | 저장소 필수 CI·명령을 적는 템플릿 |
| `verify_routing.py` | 설치 검증 스크립트 |
| `init_routing.sh` | 설치 스크립트 (아래) |

## 설치

프로젝트 루트에서 한 줄로 실행합니다. 프로젝트는 **git 저장소**여야 하고, GitHub에 **인증**되어 있어야 합니다(비공개 저장소인 경우).

```bash
curl -fsSL https://raw.githubusercontent.com/DomineYH/jev_task_routing/main/init_routing.sh | bash
```

또는 저장소를 받아서 실행:

```bash
git clone https://github.com/DomineYH/jev_task_routing.git /tmp/jtr
cd /path/to/your-project
bash /tmp/jtr/init_routing.sh
```

### 스크립트가 하는 일

1. **의존성 확인** — `git`, `python3 ≥ 3.8`
2. **git 저장소·인증 확인** — 현재 폴더가 git 저장소가 아니면 `git init` 안내 후 종료(exit 2). 원격에 접근할 수 없으면 `gh auth login` / `gh auth setup-git` 또는 credential helper·SSH 설정을 안내 후 종료(exit 3)
3. **다운로드** — 저장소를 임시 폴더에 얕게 복제
4. **설치** — `.routing/` 아래에 정책·스키마·`models.json`(**없을 때만** 생성, 있으면 유지하고 `models.example.json`만 갱신) + `verify_routing.py`·`resolve_models.py` + `repo_checks.json`(없을 때만 예시로 생성) + `tasks/`·`evidence/` 생성, `.gitignore`에 `.routing/tasks/*.json`·`.routing/evidence/*.json` 추가, 구버전 `jev_task_routing_v*.json`은 `.bak`으로 이름 변경, `INSTALLED.json`에 버전·원본 커밋 기록. 기존 파일과 내용이 다르면 `.bak`으로 백업 후 교체
5. **에이전트 지시 블록 삽입** — 하네스를 감지해 `CLAUDE.md`(Claude Code) 또는 `AGENTS.md`(codex·agy·opencode 등)에 `AGENTS_ROUTING.md` 내용을 추가. 파일이 없으면 생성, 있으면 끝에 추가. 마커(`<!-- jev-routing:start/end -->`) 사이만 관리하므로 **재실행해도 중복되지 않고 갱신**됩니다
6. **검증** — `verify_routing.py` 실행(아래 참조)

하네스 감지 규칙: `CLAUDECODE` 환경변수·`CLAUDE.md`·`.claude/`가 있으면 Claude Code → `CLAUDE.md`. `AGENTS.md`·`.codex/`·`opencode.json` 등이 있으면 → `AGENTS.md`. 둘 다 없고 터미널이면 물어보고, 비대화형이면 `AGENTS.md`.

### 옵션

```
--harness claude|agents|both   하네스 자동 감지 대신 지정
--ping                         설치 후 Jev 엔드포인트 스모크 테스트 (TYPESAFE_API_KEY 필요)
--source <url|path>            다른 원격/로컬 경로에서 설치 (오프라인·포크·테스트용)
--ref <branch|tag>             특정 브랜치/태그 설치
--no-auth-check                인증 사전 확인 생략
```

종료 코드: `0` 정상 · `1` 검증 실패 · `2` git 저장소 아님 · `3` 인증 실패 · `4` 다운로드 실패 · `5` 의존성 없음

## 검증

설치 스크립트가 마지막에 자동으로 돌리며, 언제든 다시 실행할 수 있습니다.

```bash
python3 .routing/verify_routing.py            # 전체 검사
python3 .routing/verify_routing.py --quiet    # 경고·실패만
python3 .routing/verify_routing.py --ping     # + Jev 엔드포인트 스모크 테스트
```

검사 항목:

| 단계 | 내용 | 실패 시 |
|---|---|---|
| files | 정책 3종·verify·tasks/ 존재, repo_checks.json 존재 | FAIL / WARN |
| schema | 정책이 JSON Schema를 통과 | FAIL |
| models | `models.json`이 스키마 통과, 정책의 모든 역할이 harness/model/effort를 해석할 수 있음, `active_profile` 존재, 어댑터 허용 effort 위반 없음 (MODEL-1/3/5) | FAIL |
| cross references | 워크플로→스테이지·역할 참조, Jev 14문항, JSON이 참조한 규칙 ID가 정책 문서에 정의됨, trusted flag마다 소비 규칙 존재, inspector/researcher 트리거 비어 있지 않음, Jev 예산 | FAIL |
| agent instructions | CLAUDE.md 또는 AGENTS.md에 라우팅 블록 존재 | FAIL |
| task records | 기록된 과제마다 발동한 inspector/researcher 트리거에 지시서 또는 skip 기록이 있는지 (EVID-7) | FAIL |
| install record | INSTALLED.json 버전 = 설정 버전 | WARN |
| environment | `TYPESAFE_API_KEY` 설정 여부 | WARN |
| ping (옵션) | 엔드포인트 도달·인증 확인, `response.model`이 고정 버전과 같은지 | FAIL/WARN |

`--ping`은 도달성·인증 스모크 테스트입니다. 요청 본문 형식은 TypeSafe 현재 API 문서로 확인해야 하며, 2xx가 아니더라도 401/403이 아니면 "도달 가능, 페이로드 형식 조정 필요"로 보고합니다.

## 설치 후 해야 할 것

1. **`.routing/repo_checks.json` 편집** — 저장소의 필수 CI 잡 이름과 실제 명령을 CI와 똑같이 적습니다. 호스트가 verification_plan의 `required_by: repository` 항목을 여기서 채웁니다(VER-5). 브랜치 보호에 리뷰가 필수면 `require_review: true`로 두고, 그러면 minor 워크플로에도 독립 검토가 붙습니다(WF-3).
2. **역할 모델 조정** — `.routing/models.json`을 편집합니다. 정책 파일에는 모델 설정이 없습니다(MODEL-5).

   ```jsonc
   {
     "default":  { "harness": null, "model": null, "effort": null },
     "roles": {
       "planner":       { "harness": "codex",    "model": "gpt-6-astra",      "effort": "medium" },
       "implementer":   { "harness": "codex",    "model": "gpt-6.1-sol",      "effort": "high" },
       "task-verifier": { "harness": "agy",      "model": "gemini-3.8-flash", "effort": "high" },
       // inspector, researcher, tester, advisor ...
     },
     "active_profile": "standard",          // "high_assurance"로 바꾸면 task-verifier가 codex/gpt-6-astra로 상향
     "profiles": { "standard": {...}, "high_assurance": {...} },
     "router":   { "provider": "typesafe", "model": "jev-1.13.0", "api_key_env": "TYPESAFE_API_KEY", ... },
     "adapters": { "codex": { "efforts": ["low","medium","high"] }, ... }
   }
   ```

   우선순위(MODEL-1): 요청의 `prompt_overrides` → `profiles[active_profile]` → `roles` → `default` → 런타임 기본값. 각 필드(harness/model/effort)는 독립적으로 해석됩니다. 결과 확인:

   ```bash
   python3 .routing/resolve_models.py                        # 전체 역할
   python3 .routing/resolve_models.py --role task-verifier --profile high_assurance
   python3 .routing/resolve_models.py --overrides request.json
   ```

   `adapters.<harness>.efforts`에 없는 effort(예: codex에 `max`)는 preflight에서 BLOCKED 됩니다(MODEL-3). 실제 설치된 어댑터가 받는 문자열에 맞게 `adapters`를 먼저 손보세요. 보안·데이터 변경이 잦은 저장소는 `active_profile: "high_assurance"`를 권합니다.
3. **API 키** — `models.json#/router/api_key_env`에 적힌 변수(기본 `TYPESAFE_API_KEY`)를 `export` (셸 프로필이나 시크릿 매니저에; `.env`를 커밋하지 마세요). 그 뒤 `--ping`으로 확인.
4. **커밋** — `git add .routing CLAUDE.md|AGENTS.md .gitignore && git commit`

## 사용 흐름 (호스트 세션 기준)

작업마다 호스트는 다음 순서를 밟습니다. 자세한 규칙은 `ROUTING_POLICY.md`, 예시는 아래.

1. **증거 패킷** — 관련 파일·호출자·가까운 테스트만 읽고(최대 8개 파일) `templates.evidence_packet`을 채움 (EVID-1..5). `unknowns`는 `repo:` / `external:` 접두어로 적음
2. **trusted_flags** — 호스트가 직접 확인한 것만 true/false, 모르면 `null` (EVID-5)
3. **조사 지시서** — `evidence_orders.inspector_triggers`(INS-1..7)·`researcher_triggers`(RES-1..5)를 패킷에 대조. 하나라도 참이면 **Jev 호출 전에** inspector/researcher 지시서를 발행하고 결과를 패킷에 병합. 발행하지 않으면 `skip_reason`을 반드시 기록 — 조용히 건너뛰면 검증에서 FAIL (EVID-6, EVID-7). 조사 지시서는 Jev 예산을 쓰지 않음
4. **Jev 호출** — 14문항 한 번에 (CLS-1). 과제 리비전당 최대 5회(초기 1회 + 증거가 바뀐 뒤 재평가 4회)
5. **결정 규칙 적용** — `decision.rules`를 순서대로; 결과는 READY_FOR_PREFLIGHT / NEEDS_CONTEXT / NEEDS_DECOMPOSITION / NOT_APPLICABLE / BLOCKED. NEEDS_CONTEXT가 저장소 사실을 요구하면 INS-6, 외부 사실이면 RES-5가 다시 발동
6. **verification_plan** — 체크 패밀리 단위로 task_record에 기록 (VER-5)
7. **작업 지시서 발행** — 역할별, 스키마 검증 통과한 것만 (ORDER-1). 섀도 모드에서는 여기서 멈춤
8. **completion_gate** — 증거 대조 후 호스트만 수락 (AUTH-5)

task_record는 `.routing/tasks/<task_id>.json`에 저장합니다(`templates.task_record`).

### 예시: "비밀번호 8자 규칙인데 7자도 통과함"

- 패킷: `change_kind=change_behavior`, `spec_status=precise_enough`("abc1234는 거부, abcd1234는 허용"), `test_seam.status=ready`
- 호스트가 `validators/password.js`를 읽고 `security_sensitive: true` attest
- CLS-2 즉시 발동 → **risk=high**. Jev `testing_mode=test_first` → VER-3 가드 통과
- 워크플로 `high`: planner(짧은 계획) → implementer(red→fix→green) → task-verifier(독립 검토) → `security` modifier로 부정 케이스·회귀 테스트 필수

### 예시: "결제 웹훅 재시도 로직 수정" (researcher 발동)

- 패킷: `change_kind=change_behavior`, `targets=[server/webhooks/stripe.js]`, 저장소에 Stripe 재시도 정책을 설명하는 로컬 소스가 없음 → `external_contracts.status=unverified`, `unknowns=["external: Stripe webhook retry schedule and idempotency key semantics"]`
- RES-1·RES-2 발동 → Jev 호출 전에 researcher 지시서(`read_scope=["network:web"]`, `write_scope=[".routing/evidence/RM-051-res-1.json"]`, `evidence_gap="RES-1: Stripe webhook retry schedule"`) 발행
- researcher가 `{fact, source_url, retrieved_on, confidence, limitations}` 형식으로 반환 → 호스트가 패킷에 병합 → 그 다음 Jev 호출
- 호스트가 "내가 안다"며 건너뛰려면 `skip_reason=gap_already_closed_by_host_read`와 근거 `source_refs`를 적어야 하고, 기억에서 답하는 것은 허용되지 않음

### 예시: "README 오타 수정"

- `change_kind=nonbehavioral`, 호스트가 diff 확인 후 `minor_scope_verified: true`
- 리스크 4종 ≤ 0.1, `minor_eligible ≥ 0.95` → **minor**, implementer 하나, `checks_only`

## 섀도 모드 → 실행 전환

설치 직후 지시 블록에는 **SHADOW MODE: ON**이 들어 있습니다. 라우팅과 기록만 하고 워커를 띄우지 않습니다. 다음을 마친 뒤 사람이 그 줄을 지웁니다.

**(1) 교정** — 실제 이슈 30~50건을 라우팅하고 사람이 정답을 라벨링해 측정합니다 (`validation.priority_metrics` 순서):

- high를 놓친 건 → 0이어야 함
- minor로 잘못 허용된 건 → 0이어야 함
- NEEDS_CONTEXT / BLOCKED 비율, 2회차 재호출 비율 → 높으면 `risk_clear_max`(0.1) 상향 검토
- 한국어 요청의 정규화 손실(부정문·식별자)

임계값은 개발 세트로 튜닝하고 별도 holdout으로 보고합니다(VAL-1, VAL-3).

**(2) ENF 체크리스트** — 최소 다음이 코드로 존재해야 합니다:

- [ ] 작업 지시서가 스키마 검증을 통과해야만 워커 실행 (ORDER-1)
- [ ] 워커 실행 명령이 호스트 세션에서만 나감 — 워커 세션에는 spawn 권한 없음 (ENF-2)
- [ ] task-verifier·advisor·inspector는 read-only 워크트리에서 실행 (ENF-4)
- [ ] 워커에게는 지시서+관련 plan 항목만 전달, 호스트 프롬프트 전체·키 전달 금지 (ENF-7)
- [ ] 예산 카운터(Jev 2회, 자동 수리 2회)가 task_record에서 실제로 증가·차단 (CLS-11, VER-11)

하나라도 없으면 해당 역할만 BLOCKED로 두고 나머지만 켭니다(ENF-5).

## 예시: Herdr 프로젝트 문서

`examples/herdr/`에 이 정책과 함께 쓰는 프로젝트 문서의 정리본이 있습니다.

- `AGENTS.md` — 호스트 규칙(코드는 워커가 작성, 문서 우선순위, 워커 수 최소화는 구현 워커에만, 대기·생존 확인, 권한) + 라우팅 블록
- `herdr_orchestrator.md` — Herdr 운용 메커니즘만(점검, 재사용·분할, 지시 전달, 대기, 보고서 처리, 통합, 정리). 정책과 겹치던 문장은 규칙 ID 포인터로 대체

문서 간 우선순위(AUTH-7): 사용자 승인·저장소 보호 → 현재 작업 지시서 → 정책 → 하네스 운용 문서 → AGENTS.md의 나머지 산문.

## 업데이트

같은 명령을 다시 실행하면 됩니다. 변경된 파일은 `.bak`으로 백업되고, 지시 블록은 마커 사이만 교체되며, `repo_checks.json`과 `tasks/`는 건드리지 않습니다.

```bash
bash /tmp/jtr/init_routing.sh --ref v2.5.0
```

## 문제 해결

| 증상 | 조치 |
|---|---|
| `This directory is not a git repository` | `git init` 후 재실행 |
| `Cannot reach ... with the current git credentials` | `gh auth login && gh auth setup-git`, 또는 SSH URL로 `--source git@github.com:DomineYH/jev_task_routing.git` |
| `[WARN] 'jsonschema' not installed` | `pip install jsonschema` 후 `python3 .routing/verify_routing.py` |
| `[FAIL] routing block ... not found` | `bash init_routing.sh --harness claude` 또는 `--harness agents`로 재삽입 |
| `[FAIL] ... triggers fired but no evidence order issued and no skip record` | 호스트가 inspector/researcher를 조용히 건너뜀. 해당 task_record의 `evidence_orders_evaluated`에 `issued` 또는 `skipped`를 채우고, AGENTS/CLAUDE.md 블록이 최신인지 확인 |
| inspector/researcher가 전혀 호출되지 않음 | task_record의 `evidence_orders_evaluated.inspector_triggers`가 비어 있는지 확인. 비어 있으면 호스트가 트리거를 평가하지 않은 것 — `unknowns`에 `repo:`/`external:` 접두어를 쓰는지, `external_contracts.status`를 채우는지 확인 |
| `--ping`에서 401/403 | `models.json#/router/api_key_env`에 적힌 환경변수 확인 |
| `[FAIL] ... effort 'x' not allowed by adapters` | `models.json`의 역할 effort를 어댑터 허용값으로 바꾸거나, 어댑터가 실제로 받는 값이면 `adapters.<harness>.efforts`에 추가 |
| 모델을 바꿨는데 적용이 안 됨 | `python3 .routing/resolve_models.py --role <id>`로 출처 확인. 요청의 `prompt_overrides`가 `models.json`보다 우선함(MODEL-1). 이미 해석된 과제는 다음 요청부터 반영 |
| `--ping`에서 4xx(401/403 제외) | 엔드포인트는 도달 가능. 요청 형식을 TypeSafe API 문서와 대조 |
| 잘못된 하네스에 블록이 들어감 | 해당 파일에서 마커 블록을 지우고 `--harness`로 재실행 |

## 버전

- **2.5.3-draft** — AGENTS.md·herdr_orchestrator.md와 대조해 상충 해소: 호스트는 제품 코드를 직접 쓰지 않음(AUTH-1), 문서 우선순위(AUTH-7), 검토 독립성은 '다른 세션 필수·다른 모델 권장'(ROLE-7), 워커 최소화는 구현 워커에만(WF-2), 대기·heartbeat·보고 없는 종료 처리(ORDER-8, `delegation.liveness`). `examples/herdr/` 추가.
- **2.5.2-draft** — 모델 설정을 `models.json`으로 분리(역할별 harness/model/effort, 기본값, 프로필, 라우터 연결, 어댑터 허용 effort). 정책 파일은 `settings: models.json#/roles/<id>`로 참조만 하며 스키마가 정책 안의 모델 설정을 거부. `resolve_models.py` 추가. 설치 시 `models.json`은 없을 때만 생성.
- **2.5.1-draft** — inspector/researcher가 전혀 호출되지 않던 문제 수정: 긍정 발동 트리거(INS-1..7, RES-1..5), 호스트 자가 조사 상한(8파일), skip 기록 의무, 조사 지시서 기본값·출력 계약·도구 preflight 추가. Jev 호출 예산 2→5회(조사 지시서는 예산 미소모). 설정 파일명을 `jev_task_routing.json`으로 변경. Jev 14문항·임계값은 그대로.
- **2.5.0-draft** — v2.4.0을 기계 판독 설정 + 규칙 ID 문서로 분리. 선언만 되고 소비되지 않던 trusted flag 3개(`needs_documentation`, `require_independent_review`, `needs_post_deployment_verification`)와 `inherited_risk_floor`에 소비 규칙·슬롯 부여. Jev 14문항·임계값·역할 설정·스테이지는 v2.4.0과 동일. 상세는 `ROUTING_POLICY.md` 부록 A.
