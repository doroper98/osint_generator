<!--
tier: 1
last_synced_with: v0.5.1
ssot_for: [ai-assistant-rules, code-style, commit-conventions]
depends_on: [GOAL.md, DOCS_GOVERNANCE.md]
last_review: 2026-05-22
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

### C10.0 역할 분담 (변경 불가)

| 역할 | 책임 |
|---|---|
| **AI 어시스턴트** | (a) 본 절차의 트리거 시점 (C10.1) 을 **스스로 인식** 한다. (b) 트리거 commit (MINOR/MAJOR) 을 만들고 `claude/...` 작업 브랜치에 **push 까지 완료** 한다 (codex 클라우드는 commit 된 브랜치를 fetch 하므로 push 가 선행되어야 한다). (c) push 직후 `review-prompt.txt` 본문을 **직접 작성** 하여 사용자에게 전달한다 — **SendUserFile 과 inline 코드블록 두 가지 형태를 동시에** (사용자가 SendUserFile 의 다운로드 위치를 못 찾을 때를 대비; 위반 사례 v0.4.x → v0.5.0 세션 참고). 사용자에게 템플릿 빈 칸을 메우게 시키지 않는다. (d) 사용자가 paste 해 준 codex 응답의 Critical/High/Medium 을 다음 PATCH (`vX.Y.(Z+1)` "외부 코드 리뷰 N차 반영") 로 흡수한다. |
| **사용자** | (a) AI 가 전달한 `review-prompt.txt` 본문을 **codex 클라우드** (권장 — ChatGPT codex agent 등 GitHub repo + 브랜치를 자동 fetch 하는 방식) 또는 **로컬 `codex exec`** (폴백) 에 전달한다. (b) codex 응답 본문 (markdown 리뷰 본체) 을 AI 세션에 paste 한다. (c) false positive 합의 / 절차 자체에 대한 결정. |

**AI 어시스턴트는 본 절차를 임의로 생략하지 못한다.** 트리거 시점에 절차를 *안내만* 하고
사용자의 명시적 요청을 기다리는 형태도 **위반** 으로 간주한다. 트리거 시점에 절차를 능동적으로
시작하지 않은 채 후속 MINOR/MAJOR/Phase 완료 커밋을 만들면 그 커밋 자체가 규칙 위반이다.

또한 review-prompt 본문을 SendUserFile **만** 으로 전달하고 inline 코드블록 동시 노출을
누락하는 형태도 위반이다 (사용자가 다운로드 파일을 못 찾는 사고가 v0.5.0 세션에서 실제로
발생). inline 노출이 길어 보여도 항상 동봉.

### C10.1 실행 의무 시점

| 트리거 | 실행 | 비고 |
|---|---|---|
| **MINOR / MAJOR commit + push 직후** | **필수** | push 가 선행되어야 codex 클라우드가 fetch 가능. 결과 흡수는 다음 PATCH (`vX.Y.(Z+1)`). v0.4.0 → v0.4.1, v0.5.0 → v0.5.1 패턴. |
| **Phase 완료 직전** | **필수** | Phase DoD 의 마지막 체크 항목. Phase 완료 marker commit 직전 또는 직후 (위와 동일 패턴). |
| **새 Worker / 새 도메인 모델 도입 PATCH** | 권장 | 사용자 판단 |
| **단순 bug fix / docs 보강 PATCH** | 면제 | 단, 같은 카테고리 fix 3 회 누적 시 한 번 실행 |
| **외부 리뷰 결과 반영 PATCH** | 면제 | 본 절차의 산출물을 다시 리뷰하지 않는다 (무한 루프 방지) |
| **본 C10 절차 자체를 도입/수정하는 PATCH** | 면제 | C10.3 자기 검증 면제 |

### C10.2 절차 요약

1. **(AI 어시스턴트 책임)** 트리거 commit (MINOR/MAJOR) 을 만들고 작업 브랜치에 push.
   commit message 는 `vX.Y.Z:` prefix 강제 (C5.3 commit-msg hook).
2. **(AI 어시스턴트 책임)** push 직후, `docs/REVIEW_PROMPT.md` §2 의 표준 프롬프트 템플릿의
   `Versions in scope` / `Key files` / `Review priorities` 세 절을 **모두 직접 채워서**
   완성된 `review-prompt.txt` 본문을 사용자에게 전달. 변경 SHA / 핵심 파일 / 우선순위는
   AI 가 diff 와 컨텍스트로부터 추론한다. **전달 형태는 SendUserFile + inline 코드블록
   두 가지 동시** (C10.0 위반 사례 방지). 사용자에게 "이 칸을 채우세요" 는 **금지**.
3. **(사용자 책임)** 본문을 codex 클라우드 (권장) 또는 로컬 `codex exec` (폴백) 에 전달.
   - codex 클라우드 패턴: 사용자가 GitHub repo + 브랜치명 (예: `claude/eager-ride-lfYXC`)
     을 codex 에 제시 + review-prompt 본문 paste. codex 가 commit 된 working tree
     를 fetch 한다. **commit 안 된 working-tree-only 변경은 못 봄** → AI 가 push 까지
     마치는 것이 본 패턴의 전제 조건 (C10.0(b)).
   - 로컬 codex CLI 패턴: `docs/REVIEW_PROMPT.md §3` 참고.
4. **(사용자 책임)** codex 응답 본문 (markdown 리뷰 본체) 을 AI 세션에 paste.
5. **(AI 어시스턴트 책임)** Critical/High/Medium 을 **다음 PATCH 한 번** ("외부 코드 리뷰
   N차 반영, `vX.Y.(Z+1)`") 으로 흡수. 같은 prefix 또는 흡수 PATCH 의 새 prefix 둘 다
   허용 — VERSION 파일과 일치만 하면 commit-msg hook 통과.
6. **(공동)** False positive 라고 판단되는 항목은 **사용자 합의 후** 무시. AI 는 DEVLOG
   다음 엔트리에 근거 (LLM-AP / ADDENDUM 위치 등) 를 명시.

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
