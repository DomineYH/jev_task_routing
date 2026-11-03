# jev_task_routing

멀티 에이전트 코딩 파이프라인용 **작업 라우팅·거버넌스 정책**입니다. 호스트 세션(코디네이터)이 Jev(TypeSafe 의미 분류기)로 작업을 분류하고, 리스크에 맞는 최소 워크플로를 고른 뒤, 범위가 제한된 작업 지시서로만 워커를 움직이게 합니다.

> 이 저장소는 **정책**입니다. 그 자체로는 아무것도 실행하거나 강제하지 않습니다. 실제 강제는 호스트 실행기가 구현해야 하며(ROUTING_POLICY.md §11 ENF), 그 전까지는 섀도 모드로만 운용합니다.

## 구성

| 파일 | 내용 |
|---|---|
| `jev_task_routing_v2.5.0.json` | 기계 판독용 설정 — 임계값, 7개 역할의 harness/model/effort, 워크플로·스테이지, Jev 14문항 루브릭, 템플릿 |
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
4. **설치** — `.routing/` 아래에 정책 3종 + `verify_routing.py` + `repo_checks.json`(없을 때만 예시로 생성) + `tasks/` 생성, `.gitignore`에 `.routing/tasks/*.json` 추가, `INSTALLED.json`에 버전·원본 커밋 기록. 기존 파일과 내용이 다르면 `.bak`으로 백업 후 교체
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
| schema | 설정이 JSON Schema를 통과 | FAIL |
| cross references | 워크플로→스테이지·역할 참조, Jev 14문항, JSON이 참조한 규칙 ID가 정책 문서에 정의됨, trusted flag마다 소비 규칙 존재 | FAIL |
| agent instructions | CLAUDE.md 또는 AGENTS.md에 라우팅 블록 존재 | FAIL |
| install record | INSTALLED.json 버전 = 설정 버전 | WARN |
| environment | `TYPESAFE_API_KEY` 설정 여부 | WARN |
| ping (옵션) | 엔드포인트 도달·인증 확인, `response.model`이 고정 버전과 같은지 | FAIL/WARN |

`--ping`은 도달성·인증 스모크 테스트입니다. 요청 본문 형식은 TypeSafe 현재 API 문서로 확인해야 하며, 2xx가 아니더라도 401/403이 아니면 "도달 가능, 페이로드 형식 조정 필요"로 보고합니다.

## 설치 후 해야 할 것

1. **`.routing/repo_checks.json` 편집** — 저장소의 필수 CI 잡 이름과 실제 명령을 CI와 똑같이 적습니다. 호스트가 verification_plan의 `required_by: repository` 항목을 여기서 채웁니다(VER-5). 브랜치 보호에 리뷰가 필수면 `require_review: true`로 두고, 그러면 minor 워크플로에도 독립 검토가 붙습니다(WF-3).
2. **역할 모델 조정** — `jev_task_routing_v2.5.0.json`의 `roles`는 건드리지 말고, 요청의 `prompt_overrides`로 덮습니다(MODEL-2). 보안·데이터 변경이 잦다면 `task-verifier`를 implementer와 동급 이상으로 올리기를 권합니다. 실제 뜨는 어댑터·모델 ID와 맞지 않는 조합은 preflight에서 BLOCKED 됩니다(MODEL-3).
3. **API 키** — `export TYPESAFE_API_KEY=...` (셸 프로필이나 시크릿 매니저에; `.env`를 커밋하지 마세요). 그 뒤 `--ping`으로 확인.
4. **커밋** — `git add .routing CLAUDE.md|AGENTS.md .gitignore && git commit`

## 사용 흐름 (호스트 세션 기준)

작업마다 호스트는 다음 순서를 밟습니다. 자세한 규칙은 `ROUTING_POLICY.md`, 예시는 아래.

1. **증거 패킷** — 관련 파일·호출자·가까운 테스트만 읽고 `templates.evidence_packet`을 채움 (EVID-1..5)
2. **trusted_flags** — 호스트가 직접 확인한 것만 true/false, 모르면 `null` (EVID-5)
3. **Jev 1회 호출** — 14문항 한 번에 (CLS-1)
4. **결정 규칙 적용** — `decision.rules`를 순서대로; 결과는 READY_FOR_PREFLIGHT / NEEDS_CONTEXT / NEEDS_DECOMPOSITION / NOT_APPLICABLE / BLOCKED
5. **verification_plan** — 체크 패밀리 단위로 task_record에 기록 (VER-5)
6. **작업 지시서 발행** — 역할별, 스키마 검증 통과한 것만 (ORDER-1). 섀도 모드에서는 여기서 멈춤
7. **completion_gate** — 증거 대조 후 호스트만 수락 (AUTH-5)

task_record는 `.routing/tasks/<task_id>.json`에 저장합니다(`templates.task_record`).

### 예시: "비밀번호 8자 규칙인데 7자도 통과함"

- 패킷: `change_kind=change_behavior`, `spec_status=precise_enough`("abc1234는 거부, abcd1234는 허용"), `test_seam.status=ready`
- 호스트가 `validators/password.js`를 읽고 `security_sensitive: true` attest
- CLS-2 즉시 발동 → **risk=high**. Jev `testing_mode=test_first` → VER-3 가드 통과
- 워크플로 `high`: planner(짧은 계획) → implementer(red→fix→green) → task-verifier(독립 검토) → `security` modifier로 부정 케이스·회귀 테스트 필수

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
| `--ping`에서 401/403 | `TYPESAFE_API_KEY` 확인 |
| `--ping`에서 4xx(401/403 제외) | 엔드포인트는 도달 가능. 요청 형식을 TypeSafe API 문서와 대조 |
| 잘못된 하네스에 블록이 들어감 | 해당 파일에서 마커 블록을 지우고 `--harness`로 재실행 |

## 버전

- **2.5.0-draft** — v2.4.0을 기계 판독 설정 + 규칙 ID 문서로 분리. 선언만 되고 소비되지 않던 trusted flag 3개(`needs_documentation`, `require_independent_review`, `needs_post_deployment_verification`)와 `inherited_risk_floor`에 소비 규칙·슬롯 부여. Jev 14문항·임계값·역할 설정·스테이지는 v2.4.0과 동일. 상세는 `ROUTING_POLICY.md` 부록 A.
