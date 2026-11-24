# Playbooks

이 디렉터리는 [`jev_task_routing.json`](../jev_task_routing.json)의 `playbooks.catalog`를 읽기 쉽게 풀어 쓴 문서다. **규범적 출처는 JSON**이다. 이 파일과 JSON이 어긋나면 JSON을 따른다(QUAL-1).

호스트는 `playbooks.select`의 첫 일치 항목으로 `task_record.playbook_id`를 기록하고, 해당 catalog 항목의 `steps`와 `report_evidence`를 구현 지시서(`playbook_ref`)에 넣는다. playbook은 `testing_mode`, 워크플로, 역할, 리스크를 고르거나 덮어쓰지 않는다(QUAL-1). 테스트 순서가 충돌하면 `testing_mode`가 이기고, playbook이 요구하는 증거(예: 재현)는 그대로 필요하다.

스키마의 `playbook_ref` / `playbook_id`는 catalog 키이지 이 디렉터리의 파일 경로가 아니다. 설치 스크립트는 이 폴더를 프로젝트의 `.routing/`에 복사하지 않는다. 워커에 pstack이나 이 문서를 스킬로 설치할 필요는 없다.

## Catalog

| 파일 | catalog id | 선택 조건 (`playbooks.select`) |
| --- | --- | --- |
| [bug_fix.md](bug_fix.md) | `bug_fix` | `task_type == bug_fix` |
| [feature.md](feature.md) | `feature` | `task_type` in [feature, ui_ux, api_integration, database, security] |
| [refactor.md](refactor.md) | `refactor` | `task_type == refactor` |
| [performance.md](performance.md) | `performance` | `task_type == performance` |
| [investigation.md](investigation.md) | `investigation` | `work_mode == exploration` (프로토타입이 아닐 때) |
| [prototype.md](prototype.md) | `prototype` | `work_mode == exploration` AND `change_kind == disposable_prototype` |
| (없음) | `null` | `work_mode == emergency`, 또는 docs / tests / dependency_update / infrastructure |

`select`는 위 순서대로 첫 일치를 쓴다. emergency가 가장 먼저이므로, 긴급 모드에서는 작업 유형과 관계없이 playbook이 없다.

## Task-type notes (not catalog ids)

아래 파일은 **별도의 playbook이 아니다.** 선택 결과를 분명히 하고, catalog 단계를 덮어쓰지 않는 유형별 참고만 적는다.

| 파일 | 실제 `playbook_id` | 해당 유형 |
| --- | --- | --- |
| [ui_ux.md](ui_ux.md), [api_integration.md](api_integration.md), [database.md](database.md), [security.md](security.md) | `feature` | feature로 선택되는 유형 |
| [docs.md](docs.md), [tests.md](tests.md), [dependency_update.md](dependency_update.md), [infrastructure.md](infrastructure.md), [emergency.md](emergency.md) | `null` | playbook 의식이 없음 (QUAL-11). 적용 QUAL은 `code_quality.applies` |

규칙 본문은 [ROUTING_POLICY.md](../ROUTING_POLICY.md) 13절(QUAL-1..11)과 `code_quality`에 있다.

Attribution: [NOTICE.md](NOTICE.md) (pstack, MIT, Copyright (c) 2026 Lauren Tan).
