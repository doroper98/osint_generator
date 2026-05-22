<!--
tier: 1
last_synced_with: v0.3.3
ssot_for: [ai-assistant-rules, code-style, commit-conventions]
depends_on: [GOAL.md, DOCS_GOVERNANCE.md]
last_review: 2026-05-19
-->

# CLAUDE.md — AI Assistant Operating Rules

본 문서는 본 저장소에서 일하는 모든 AI 어시스턴트(Claude Code 포함)와 개발자가
따라야 하는 작업 규칙을 정의합니다. 위반 시 코드 리뷰 또는 git hook에서 차단됩니다.

---

## C1. 언어와 톤

- **세션 톤**: 한국어, 친절하고 평이한 문장, 어려운 개념은 풀어서 설명.
- **코드**: 식별자는 영문 snake_case / PascalCase. 주석·docstring은 한글 허용.
- **시스템 프롬프트**: 한국어 + 영어 혼용 가능.
- **commit message body**: 한글/영문 자유, 첫 줄은 영문 prefix + 한글 요약 가능.

## C2. Python 코드 규칙

| 항목 | 규칙 |
|---|---|
| Python | 3.11+ (3.10 이하 호환성 보장 안 함) |
| 타입 힌트 | **필수**. 모든 함수 시그니처에 적용 |
| 데이터 모델 | **Pydantic v2 BaseModel만 사용**. raw dict로 도메인 데이터를 다루지 않는다 |
| 문자열 포맷 | 시스템 프롬프트는 `.replace()` 사용. `.format()`은 JSON `{}`와 충돌하므로 금지 |
| import | 표준 라이브러리 → 서드파티 → 로컬, 각 블록 사이 빈 줄 1개 |
| 비동기 | TUI / subprocess 라우팅은 `asyncio` 기반 |
| 검증 | 코드 변경 후 `python -m py_compile <file>` 통과 |

## C3. JSON 계약

- 모든 JSON 산출물은 `schema_version` 필드를 가져야 합니다. (현재 v1)
- 모든 JSON 산출물은 `schemas/models.py`의 Pydantic 모델로 파싱/검증 가능해야 합니다.
- 신규 필드 추가는 호환되는 방향(optional)부터 시도. Breaking change는 `schema_version`을 올립니다.

## C4. Worker 작성 규칙

1. Worker는 **반드시 `workers/base_worker.py:BaseWorker`를 상속**합니다.
2. Worker는 **사용자에게 질문하지 않습니다**. 판단이 필요하면 task_result에 `status="needs_user_confirmation"`을 남기고 종료합니다.
3. Worker는 **다른 Worker의 산출물을 수정하지 않습니다**. 자기 자신의 `output_refs`만 씁니다.
4. Worker는 **`task_result.json`을 반드시 남기고 종료**합니다. (성공/실패/사용자필요 모두 마찬가지)
5. Worker는 **stdout 로그를 1줄 1이벤트** 원칙으로 출력합니다. Log Router가 파싱합니다.

## C5. 커밋 / 버전 규칙 (모든 곳에 버전 표기 의무)

> 사용자는 브랜치보다 **버전**을 기준으로 본 시스템과 소통합니다. 모든 산출물에 버전을 박아 둡니다.

### C5.1 버전의 단일 출처 (SSOT)

- **`VERSION` 파일** (저장소 root) 한 줄. 예: `0.1.0`.
- 모든 다른 곳은 본 파일을 읽거나 동기화됩니다.

### C5.2 버전 표기 의무 대상

| 대상 | 형식 | 갱신 책임 |
|---|---|---|
| `VERSION` 파일 | `MAJOR.MINOR.PATCH` 한 줄 | 버전 증분 시 |
| `orchestrator/__init__.py:__version__` | `"X.Y.Z"` | 버전 증분 시 |
| 모든 마크다운 YAML 헤더 `last_synced_with` | `vX.Y.Z` | 버전 증분 시 |
| 모든 JSON 산출물 `schema_version` | 정수 | schema_version 증분 시 (별개) |
| 커밋 메시지 첫 줄 | `vX.Y.Z: {summary}` | 커밋 시 |
| `docs/branches.html` 헤더 | 현재 `VERSION` 표시 | 자동 (JS가 raw 파일 fetch) |

### C5.3 커밋 prefix 검증

- `.githooks/commit-msg`가 첫 줄을 검사:
  - 정규식: `^v\d+\.\d+\.\d+: .+`
  - `VERSION` 파일과 일치하는지 확인.
- rebase/cherry-pick 시에만 `SKIP_VERSION_CHECK=1` 허용.

### C5.4 버전 증분 규칙

| 종류 | 트리거 |
|---|---|
| **MAJOR** | `GOAL.md` G1·G2·G4 변경, 또는 JSON `schema_version` 증분 |
| **MINOR** | Phase 완료, 새 Worker 추가, 새 Review Gate 추가 |
| **PATCH** | 버그 수정, 문서 보강, 비기능 개선 |

### C5.5 한 커밋 = 한 버전 증분 (원칙)

여러 변경을 한 커밋에 묶지 마십시오. 한 커밋 당 한 가지 의도, 한 버전 prefix.

## C6. Antipattern / Incident 기록

문제가 발생하면 다음 순서로 처리합니다.

1. **재현**: 최소 재현 절차를 확보합니다.
2. **분류**: 어느 카테고리인지 결정합니다.
   - `TTS-AP-N`: TTS 발음/억양 관련
   - `PIPELINE-AP-N`: Orchestrator·Worker·Task Queue 관련
   - `RIGHTS-AP-N`: 권리·라이선스 관련
   - `RENDER-AP-N`: Remotion·FFmpeg 관련
   - `SCHEMA-AP-N`: JSON 계약 위반
   - `LLM-AP-N`: 구독 LLM Bridge / `claude`·`codex` CLI subprocess 호출 관련 (docs/ADDENDUM_04 참조)
3. **기록**: `docs/ANTIPATTERNS/{CATEGORY}_ANTIPATTERNS.md`에 새 N번을 **append**합니다.
4. **구조적 조치**: 같은 클래스의 버그가 재발하지 않도록 검증기·테스트·git hook을 추가합니다.
5. **DEVLOG**: `DEVLOG.md`에 한 줄 요약과 AP 번호를 남깁니다.

**과거 항목 수정은 금지**입니다. 잘못된 항목은 `[superseded by TTS-AP-NN]`로 마킹만 합니다.

## C7. 문서 변경 전파

코드 변경 시 다음 문서 동기화가 필요한지 확인합니다.

| 코드 변경 | 동기화 대상 |
|---|---|
| `schemas/models.py` | `docs/05_DATA_SCHEMA_SPEC.md`, `docs/ARCHITECTURE.md` |
| 새 Worker 클래스 | `docs/03_AGENT_ARCHITECTURE.md`, `docs/CATALOGS.md` |
| 새 Review Gate | `docs/12_QA_AND_REVIEW_SPEC.md`, `GOAL.md` G3 |
| `__version__` 증분 | `CHANGELOG.md`, 모든 Tier 1·2 YAML 헤더 |
| 새 카테고리 | `GOAL.md` G2, `docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md` |

## C8. 작업 흐름 (AI 에이전트용)

1. **읽기 우선**. 기존 파일을 수정하기 전에 반드시 Read.
2. **작은 단위 커밋**. 한 커밋은 한 가지 의도.
3. **테스트 가능한 산출물**. 매 Phase는 `python -m py_compile`과 import smoke test 통과.
4. **무리하게 미래 기능을 만들지 않는다**. 본 Phase 범위 안에서만 구현.
5. **사용자가 명시적으로 요청하지 않은 PR 생성 금지**.

## C9. 보안 / 권리

- `.env`, `credentials.json`, OAuth 토큰을 커밋하지 않습니다.
- X / Telegram / 기사 영상 다운로드 시 `rights_status`를 반드시 기록합니다.
- AI 생성 이미지는 기본 자산으로 사용하지 않습니다. (예외는 risk_flag 명시)
- 미검증 정보는 영상 내에서 `<미검증>` 라벨로만 표기.

## C10. 외부 코드 리뷰 (codex review) 의무화

본 시스템은 자기 자신을 만든 AI 의 사각지대를 보정하기 위해 **다른 LLM CLI (`codex exec`) 로
주기적 코드 리뷰를 실행**합니다. 운영 매뉴얼은 `docs/REVIEW_PROMPT.md` 에 있습니다.

### C10.1 실행 의무 시점

| 트리거 | 실행 | 비고 |
|---|---|---|
| **MINOR / MAJOR 증분 직전** | **필수** | 리뷰의 Critical/High 모두 흡수한 뒤에만 증분 가능 |
| **Phase 완료 직전** | **필수** | Phase DoD 의 마지막 체크 항목 |
| **새 Worker / 새 도메인 모델 도입 PATCH** | 권장 | 사용자 판단 |
| **단순 bug fix / docs 보강 PATCH** | 면제 | 단, 같은 카테고리 fix 3 회 누적 시 한 번 실행 |
| **외부 리뷰 결과 반영 PATCH** | 면제 | 본 절차의 산출물을 다시 리뷰하지 않는다 (무한 루프 방지) |

### C10.2 절차 요약

1. `docs/REVIEW_PROMPT.md` §2 의 표준 프롬프트 템플릿에 변경 범위 (버전, 핵심 파일, 우선순위) 만
   채워 `review-prompt.txt` 작성.
2. 사용자 머신에서 `codex exec --skip-git-repo-check --color never -C <repo> -` 에 stdin 으로
   전달 → stdout JSONL 을 `review-out.jsonl` 로 저장.
3. 마지막 `agent_message.text` 가 리뷰 본문. 사용자가 AI 어시스턴트 세션에 paste.
4. 결과의 Critical/High/Medium 을 **단일 PATCH** ("외부 코드 리뷰 N차 반영") 로 흡수.
5. False positive 라고 판단되는 항목은 **사용자 합의 후** 무시. DEVLOG 다음 엔트리에 근거 명시.

명령어 / 인코딩 / 프롬프트 전문은 `docs/REVIEW_PROMPT.md` 참고.

### C10.3 본 절차의 자기 검증 면제

본 절차 자체를 도입/수정하는 PATCH 는 codex review 면제 (자기 검증 회피).
외부 리뷰 결과를 흡수하는 PATCH 도 면제 (이미 리뷰된 변경의 반영이므로).

### C10.4 산출물 처리

- `review-prompt.txt`, `review-out.jsonl` 은 **커밋 금지**. 일회용 산출물.
  - 개인 환경 전용: `.git/info/exclude` 에 추가.
- 리뷰 본문 자체는 commit message body 또는 DEVLOG 에 발췌하여 남기는 것을 **권장**.
  완전 사본은 GitHub Discussions / Issue 등 별도 채널에 보존.

---

본 문서를 위반하는 PR은 자동으로 차단되어야 합니다. 차단 메커니즘이 아직 없다면
관련 PR과 함께 git hook 또는 CI 검증기를 추가합니다.
