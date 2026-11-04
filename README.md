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
| `repo_checks.example.json` / `repo_checks.schema.json` | 저장소 필수 CI·명령을 적는 템플릿과 그 스키마 — 하네스가 채울 수 있도록 README에 프롬프트 제공 |
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
| repo_checks | `repo_checks.json`이 `repo_checks.schema.json`을 통과, `required_ci`마다 `commands` 존재, 미편집·unknowns 경고 | FAIL/WARN |
| cross references | 워크플로→스테이지·역할 참조, Jev 14문항, JSON이 참조한 규칙 ID가 정책 문서에 정의됨, trusted flag마다 소비 규칙 존재, inspector/researcher 트리거 비어 있지 않음, Jev 예산 | FAIL |
| agent instructions | CLAUDE.md 또는 AGENTS.md에 라우팅 블록 존재 | FAIL |
| ORDER-9 guard hook | Claude Code 프로젝트면 user/project/local 중 한 곳에 훅 등록 여부, `hooks.json` mode 유효성 | WARN/FAIL |
| task records | 기록된 과제마다 발동한 inspector/researcher 트리거에 지시서 또는 skip 기록이 있는지 (EVID-7) | FAIL |
| install record | INSTALLED.json 버전 = 설정 버전 | WARN |
| environment | `TYPESAFE_API_KEY` 설정 여부 | WARN |
| ping (옵션) | 엔드포인트 도달·인증 확인, `response.model`이 고정 버전과 같은지 | FAIL/WARN |

`--ping`은 도달성·인증 스모크 테스트입니다. 요청 본문 형식은 TypeSafe 현재 API 문서로 확인해야 하며, 2xx가 아니더라도 401/403이 아니면 "도달 가능, 페이로드 형식 조정 필요"로 보고합니다.

## Claude Code 훅 (ORDER-9 가드)

Claude Code를 호스트로 쓸 때, 위임 역할을 Herdr pane 대신 Claude Code의 Agent/Task 서브에이전트로 돌리는 것을 **도구 호출 단계에서 차단**하는 PreToolUse 훅입니다. 정책 문서와 검증기는 "기록된 것"만 잡지만, 이 훅은 호출 자체를 막습니다.

설치 스크립트가 하네스를 Claude Code로 감지하면 자동으로 등록합니다. 스코프는 `--hooks`로 선택하고 **기본값은 `user`** 입니다.

| 스코프 | 설정 파일 | 스크립트 위치 | 적용 범위 |
|---|---|---|---|
| `user` (기본) | `~/.claude/settings.json` | `~/.claude/hooks/jev_order9_guard.py` | 이 컴퓨터의 모든 프로젝트. 단, `.routing/`이 없는 프로젝트에서는 아무 일도 하지 않음 |
| `project` | `.claude/settings.json` (커밋됨) | `.routing/hooks/jev_order9_guard.py` | 이 저장소를 쓰는 모든 사람 |
| `local` | `.claude/settings.local.json` (커밋 안 됨) | `.routing/hooks/jev_order9_guard.py` | 이 저장소, 나만 |
| `none` | — | — | 등록하지 않음 |

```bash
bash init_routing.sh                   # Claude Code 감지 시 user 스코프에 등록
bash init_routing.sh --hooks project   # 팀 공유
bash init_routing.sh --hooks local
bash init_routing.sh --hooks none
bash init_routing.sh --uninstall-hooks # 세 스코프에서 모두 제거
```

한 스코프에 등록하면 다른 스코프의 기존 등록은 제거해 중복 실행을 막습니다. 기존 `settings.json`의 다른 훅은 건드리지 않고 `hooks.PreToolUse` 배열에 항목 하나만 병합합니다. Claude Code 안에서 `/hooks`로 등록 상태를 볼 수 있습니다.

**판정 규칙** (`.routing/hooks.json`으로 조정):

| Agent/Task 호출 내용 | 판정 |
|---|---|
| `subagent_type`이 역할 ID, 또는 프롬프트에 "You are the implementer"류 역할 지정 | **deny** |
| 프롬프트에 작업 지시서 필드(`order_id`, `write_scope`, `acceptance_criteria` …) | **deny** |
| 구현·수정·테스트 실행·커밋·배포 등 쓰기/실행 의도(한국어 포함) | **deny** (AUTH-1) |
| `allow_subagent_types`(기본 `["Explore"]`)에 있고 위 신호 없음 | allow (조용히) |
| 목록에 없는 타입이고 위 신호 없음 | `unlisted_subagent_type`에 따라 **ask**(기본) / deny / allow |
| Agent/Task 이외 도구, 또는 `.routing/`이 없는 디렉터리 | 관여하지 않음 |

`mode`를 `ask`로 두면 모든 deny가 사용자 확인으로 바뀌고, `log`로 두면 차단 없이 `.routing/hook_log.jsonl`에만 기록합니다(섀도 모드에서 오탐 확인용으로 유용). 모든 판정은 로그에 남습니다.

한계: 호스트가 역할 이름도 지시서 필드도 쓰기 동사도 없이 서브에이전트에 작업을 넘기면 통과합니다. 그런 경우는 `ask`로 사용자에게 올라오므로, 로그에서 `ask`가 반복되는 패턴을 보고 `allow_subagent_types`를 조정하세요.

## 설치 후 해야 할 것

1. **`.routing/repo_checks.json` 채우기** — 저장소의 필수 CI 잡 이름과 실제 명령을 CI와 똑같이 적습니다. 호스트가 verification_plan의 `required_by: repository` 항목을 여기서 채웁니다(VER-5). 브랜치 보호에 리뷰가 필수면 `require_review: true`로 두고, 그러면 minor 워크플로에도 독립 검토가 붙습니다(WF-3). 형식은 `.routing/repo_checks.schema.json`에 정의되어 있고 검증기가 검사합니다.

   직접 쓰지 않고 **하네스에게 채우게** 할 수 있습니다. 설치한 프로젝트 루트에서 호스트 세션(Claude Code, Codex, agy, opencode 등 — 모두 같은 프롬프트)을 열고 아래를 그대로 붙여 넣으세요. 이 작업은 라우팅 대상 "과제"가 아니라 설치 후 설정이므로 Jev 호출이나 워커 없이 호스트가 직접 수행해도 됩니다(제품 코드는 건드리지 않음).

   <details open>
   <summary><b>프롬프트 (English — 모든 하네스 공통)</b></summary>

   ```text
   Fill in .routing/repo_checks.json for this repository. This is post-install setup, not a routed task: do it yourself, read-only except for that one file. Do not call Jev, do not launch workers, do not touch product code.

   1. Read .routing/repo_checks.schema.json (the required shape) and .routing/repo_checks.example.json.
   2. Inspect, in this order and only what exists: CI workflow files (.github/workflows/*.yml, .gitlab-ci.yml, .circleci/, Jenkinsfile, azure-pipelines.yml), package manifests and task runners (package.json scripts, pyproject.toml / tox.ini / noxfile.py, Makefile, justfile, Cargo.toml, go.mod, build.gradle, pom.xml), lint/format/typecheck configs, test configs (jest/vitest/pytest/playwright/cypress), and any CONTRIBUTING or README section on running checks.
   3. If the gh CLI is available and authenticated, run: gh api repos/{owner}/{repo}/branches/{default_branch}/protection — use it to fill branch_protection.require_review and required_status_checks, and record the command in branch_protection.source. If it fails or gh is absent, set require_review to null and source to "not checked".
   4. Write .routing/repo_checks.json with:
      - required_ci: the check names a PR must pass (job names from CI, or the script names if there is no CI);
      - commands: for every required_ci entry, the exact command CI runs (copy it verbatim from the workflow or script; null if it only runs in CI with no local equivalent). Never invent a command that does not exist in the repository;
      - branch_protection as above;
      - e2e.command (null if none) and e2e.critical_flows: up to 8 named user journeys you can identify from routes, pages or existing E2E specs — leave empty if unsure;
      - sources: every file you read; generated_by: your harness and model; generated_on: today's date;
      - unknowns: anything you could not determine. Do not guess to make unknowns empty.
   5. Run: python3 .routing/verify_routing.py --quiet — it validates the file against the schema. Fix any [FAIL] about repo_checks.json and run it again.
   6. Reply with: the final required_ci list and commands, the branch_protection result and how you got it, and the unknowns list for me to resolve. Do not commit.
   ```
   </details>

   <details>
   <summary>같은 프롬프트 (한국어)</summary>

   ```text
   이 저장소의 .routing/repo_checks.json을 채워 줘. 설치 후 설정이므로 라우팅 과제가 아니다: Jev 호출·워커 실행 없이 네가 직접 하고, 그 파일 하나 외에는 읽기 전용으로, 제품 코드는 건드리지 마.

   1. .routing/repo_checks.schema.json(필수 형식)과 .routing/repo_checks.example.json을 읽어.
   2. 다음을 이 순서로, 존재하는 것만 조사해: CI 워크플로(.github/workflows/*.yml, .gitlab-ci.yml, .circleci/, Jenkinsfile, azure-pipelines.yml), 패키지 매니페스트·태스크 러너(package.json scripts, pyproject.toml/tox.ini/noxfile.py, Makefile, justfile, Cargo.toml, go.mod, build.gradle, pom.xml), 린트·포맷·타입체크 설정, 테스트 설정(jest/vitest/pytest/playwright/cypress), CONTRIBUTING·README의 검사 실행 안내.
   3. gh CLI가 있고 로그인돼 있으면 gh api repos/{owner}/{repo}/branches/{default_branch}/protection 를 실행해 branch_protection.require_review와 required_status_checks를 채우고, 실행한 명령을 branch_protection.source에 적어. 실패하거나 gh가 없으면 require_review는 null, source는 "not checked".
   4. .routing/repo_checks.json에 다음을 써:
      - required_ci: PR이 통과해야 하는 체크 이름(CI 잡 이름, CI가 없으면 스크립트 이름);
      - commands: required_ci 항목마다 CI가 실제로 실행하는 명령을 그대로 복사(CI에서만 돌고 로컬 대응이 없으면 null). 저장소에 없는 명령을 만들어 내지 마;
      - branch_protection: 위 결과;
      - e2e.command(없으면 null)과 e2e.critical_flows: 라우트·페이지·기존 E2E 스펙에서 식별한 핵심 사용자 흐름 최대 8개, 확신 없으면 비워 둬;
      - sources: 읽은 파일 전부; generated_by: 네 하네스와 모델; generated_on: 오늘 날짜;
      - unknowns: 알 수 없었던 것. unknowns를 비우기 위해 추측하지 마.
   5. python3 .routing/verify_routing.py --quiet 를 실행해 스키마 검증을 통과시켜. repo_checks.json 관련 [FAIL]이 있으면 고치고 다시 실행.
   6. 최종 required_ci와 commands, branch_protection 결과와 확인 방법, 내가 해결할 unknowns 목록을 답해. 커밋은 하지 마.
   ```
   </details>

   하네스별 실행 방법:

   | 하네스 | 방법 |
   |---|---|
   | Claude Code | 프로젝트 루트에서 `claude` 실행 후 프롬프트 붙여 넣기. ORDER-9 훅은 Agent 호출만 보므로 이 작업에는 관여하지 않음 |
   | Codex CLI | `codex` 대화형 세션에 붙여 넣기, 또는 `codex "<프롬프트>"` 로 한 번에 실행 |
   | agy / opencode / Herdr pane | 호스트 pane의 입력에 그대로 붙여 넣기 |

   결과를 눈으로 한 번 확인하세요 — 특히 `commands`가 CI와 글자 단위로 같은지, `unknowns`에 남은 항목이 무엇인지. 검증기는 `generated_by`·`sources`가 비어 있으면 "미편집"으로 경고하고, `required_ci`에 있는데 `commands`에 없는 항목은 FAIL로 잡습니다.

   <details>
   <summary>선택: models.json 어댑터 점검 프롬프트</summary>

   ```text
   Review .routing/models.json against the harnesses actually installed on this machine. Read-only except for that file; no workers, no Jev.
   For each harness in adapters (codex, agy, opencode, claude): check whether the CLI exists on PATH and which effort/reasoning strings it accepts (consult its --help or config docs if available). Correct adapters.<harness>.efforts to the accepted values, keep launch_channels as ["herdr_pane"], and note in adapters.<harness>.notes how you verified. Do not change roles, default, profiles or router. Then run python3 .routing/resolve_models.py and python3 .routing/verify_routing.py --quiet, and report any role whose effort is now BLOCKED so I can choose a valid value.
   ```
   </details>
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
- `herdr_orchestrator.md` (한국어) / `herdr_orchestrator_en.md` (English) — Herdr 운용 메커니즘만(점검, 재사용·분할, 지시 전달, 대기, 보고서 처리, 통합, 정리). 정책과 겹치던 문장은 규칙 ID 포인터로 대체

문서 간 우선순위(AUTH-7): 사용자 승인·저장소 보호 → 현재 작업 지시서 → 정책 → 하네스 운용 문서 → AGENTS.md의 나머지 산문.

## 업데이트

같은 명령을 다시 실행하면 됩니다. 변경된 파일은 `.bak`으로 백업되고, 지시 블록은 마커 사이만 교체되며, `repo_checks.json`과 `tasks/`는 건드리지 않습니다.

`models.json`은 사용자 편집 파일이라 **역할·기본값·프로필·라우터 설정을 그대로 두고**, 새 스키마가 요구하는 항목만 `migrate_models.py`가 추가합니다(예: `adapters.*.launch_channels`, 역할이 쓰는 하네스의 어댑터 항목). 마이그레이션 전 사본은 `models.json.pre-migrate.bak`에 남습니다. 수동 실행:

```bash
python3 .routing/migrate_models.py .routing/models.json .routing/models.example.json --dry-run
```

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
| `[FAIL] models.json violates models.schema.json ... 'launch_channels' is a required property` | 구버전 `models.json`. `init_routing.sh`를 다시 실행하면 자동 마이그레이션되며, 수동으로는 `python3 .routing/migrate_models.py .routing/models.json .routing/models.example.json` |
| `[FAIL] ... effort 'x' not allowed by adapters` | `models.json`의 역할 effort를 어댑터 허용값으로 바꾸거나, 어댑터가 실제로 받는 값이면 `adapters.<harness>.efforts`에 추가 |
| 워커가 Herdr pane 대신 백그라운드 서브에이전트로 실행됨 | 정책 위반(ORDER-9). task_record의 `role_work_items.*.launch_channel`을 확인 — `herdr_pane`이 아니면 검증 FAIL. AGENTS/CLAUDE.md 블록이 v2.5.5 이상인지 확인 |
| 모델을 바꿨는데 적용이 안 됨 | `python3 .routing/resolve_models.py --role <id>`로 출처 확인. 요청의 `prompt_overrides`가 `models.json`보다 우선함(MODEL-1). 이미 해석된 과제는 다음 요청부터 반영 |
| `--ping`에서 4xx(401/403 제외) | 엔드포인트는 도달 가능. 요청 형식을 TypeSafe API 문서와 대조 |
| 잘못된 하네스에 블록이 들어감 | 해당 파일에서 마커 블록을 지우고 `--harness`로 재실행 |

## 버전

- **2.5.5-draft (+hooks)** — Claude Code PreToolUse 훅 `hooks/jev_order9_guard.py` 추가: Agent/Task 서브에이전트로 위임 역할을 돌리는 호출을 차단. `init_routing.sh --hooks user|project|local|none`(기본 user), `--uninstall-hooks`.
- **2.5.5-draft** — 실행 채널 고정(ORDER-9): 모든 위임 역할은 하네스를 불문하고 Herdr pane으로 실행, 호스트의 Agent/서브에이전트 도구는 역할 실행 채널이 아님. `work_order`에 `launch_channel`·`pane_id`, `models.json` 어댑터에 `launch_channels`와 `claude` 항목 추가. 옵션 B(읽기 전용 역할의 제한 서브에이전트)는 전제 조건과 함께 비활성으로 문서화.
- **2.5.4-draft** — 분류→작업 매핑 감사 반영: ui_ux·database·security·api_integration modifier가 task_type으로도 활성화(MOD-1), analysis×delivery → NEEDS_CONTEXT(CLS-7b), `change_kind`에 `test_only` 추가(EVID-2a).
- **2.5.3-draft** — AGENTS.md·herdr_orchestrator.md와 대조해 상충 해소: 호스트는 제품 코드를 직접 쓰지 않음(AUTH-1), 문서 우선순위(AUTH-7), 검토 독립성은 '다른 세션 필수·다른 모델 권장'(ROLE-7), 워커 최소화는 구현 워커에만(WF-2), 대기·heartbeat·보고 없는 종료 처리(ORDER-8, `delegation.liveness`). `examples/herdr/` 추가.
- **2.5.2-draft** — 모델 설정을 `models.json`으로 분리(역할별 harness/model/effort, 기본값, 프로필, 라우터 연결, 어댑터 허용 effort). 정책 파일은 `settings: models.json#/roles/<id>`로 참조만 하며 스키마가 정책 안의 모델 설정을 거부. `resolve_models.py` 추가. 설치 시 `models.json`은 없을 때만 생성.
- **2.5.1-draft** — inspector/researcher가 전혀 호출되지 않던 문제 수정: 긍정 발동 트리거(INS-1..7, RES-1..5), 호스트 자가 조사 상한(8파일), skip 기록 의무, 조사 지시서 기본값·출력 계약·도구 preflight 추가. Jev 호출 예산 2→5회(조사 지시서는 예산 미소모). 설정 파일명을 `jev_task_routing.json`으로 변경. Jev 14문항·임계값은 그대로.
- **2.5.0-draft** — v2.4.0을 기계 판독 설정 + 규칙 ID 문서로 분리. 선언만 되고 소비되지 않던 trusted flag 3개(`needs_documentation`, `require_independent_review`, `needs_post_deployment_verification`)와 `inherited_risk_floor`에 소비 규칙·슬롯 부여. Jev 14문항·임계값·역할 설정·스테이지는 v2.4.0과 동일. 상세는 `ROUTING_POLICY.md` 부록 A.
