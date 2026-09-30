<!--
tier: 1
last_synced_with: v5.0.0
ssot_for: [ai-assistant-rules, code-style, commit-conventions]
depends_on: [GOAL.md, DOCS_GOVERNANCE.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-29
-->

# CLAUDE.md — AI Assistant Operating Rules

본 문서는 본 저장소에서 일하는 모든 AI 어시스턴트(Claude Code 포함)와 개발자가
따라야 하는 작업 규칙을 정의합니다. 위반 시 코드 리뷰 또는 git hook에서 차단됩니다.

---

## C0. 최우선 가치 — 영상미 (Cinematic Quality First)

본 시스템의 **최우선 미덕은 "영상미"**다 — "정적 보고서를 화면에 박은 것"이 아니라 **영상다운 영상**.
설계·구현에서 선택지가 갈릴 때 더 정적이고 쉬운 길보다 영상미가 높은 길을 택한다.

**영상 기준의 정본은 `docs/handoff/`(01·02·04~11·14)이다.** 기준 작품은 v3『호르무즈와 한국』
(`docs/handoff/golden/`, 문장 앵커 기준 프레임 25장). 이전 영상 기준(섹션=장면, 고정 막,
HyperFrames/Remotion 문법, `docs/07/08/09` 구판)은 **v2.0.0에서 폐기**됐고, `docs/07·08·09·10`은 **v4.0.0에서 handoff·규칙 파일을
가리키는 요약본으로 재작성**됐다(수치는 규칙 키로만 인용, 값 복사 금지).
구체 수치(두께·알파·타이밍·색·글자 크기)는 `rules/video_rules.yaml`과
`docs/handoff/reference_code/v3_hormuz_korea/`가 정본이며 사용자 합격 값이다. 근거 없이 바꾸지 않는다.

**되돌리면 안 되는 것 (사용자 합격 판정 완료, `docs/handoff/KICKOFF_PROMPT.md` §5):**
- 고정 막 구성
- 모서리의 브랜드명, 섹션 번호, 섹션 제목 (모서리에는 날짜만)
- 도장
- 비네팅
- 문장마다 카메라 이동, 줌이 튀어 오르는 연출
- 한꺼번에 튀어나오는 관계선
- AI 상투 문구 (`docs/handoff/03` §2, `rules/video_rules.yaml banned_phrases`)
- 발음 텍스트 안의 숫자와 기호

**경계(반드시)**: 영상미는 **사실 정확성·검증(GOAL G4)·권리(C9) 위에서** 추구한다. 검증 라벨,
미검증 정보 취급, 권리 기록, TTS 발음 안전을 희생한 화려함은 금지 — **정확성을 깨는 영상미는
영상미가 아니다.** 출처 없는 수치 금지, 논쟁 사안은 양측을 같은 무게로, 자료사진·자료 영상
표기, 사실 장면의 AI 생성 금지, 권리 기록과 크레딧(엔딩 카드 유지).

### C0.1 byte-equal 비적용

이번 개편에는 **"기존 출력 불변(byte-equal)" 원칙을 적용하지 않는다.** 기준은 v3 골든 재현이다
(`docs/handoff/15` §3 P7). "flag OFF 면 출력이 같아야 한다"는 이유로 새 기능을 추가형·OFF 기본값에
가두지 않는다.

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
| **MAJOR** | `GOAL.md` G1·G2·G3·G4 변경(G3 는 v4.0.0 D64 추가 — GOAL §G3 머리말), 또는 JSON `schema_version` 증분 |
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
| `schemas/models.py` | `docs/05_DATA_SCHEMA_SPEC.md`, `docs/02_SYSTEM_ARCHITECTURE.md` |
| 새 Worker 클래스 | `docs/03_AGENT_ARCHITECTURE.md` |
| 새 Review Gate | `docs/12_QA_AND_REVIEW_SPEC.md`, `GOAL.md` G3 |
| `__version__` 증분 | `CHANGELOG.md`, 모든 Tier 1·2 YAML 헤더 |
| 새 카테고리 | `GOAL.md` G2, `docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md` |
| `rules/video_rules.yaml` | `prompts/` 재생성 결과 확인, `tests/anti_inertia/` 통과 |
| 새 이벤트 타입·패널 종류·미디어 형태 | 스키마·렌더러·프리뷰 예제 **세 곳 동시** (`rules/video_rules.yaml registries`) |
| `docs/handoff/*` | `docs/handoff/19` §3 판정표, `docs/handoff/DECISIONS.md` |

## C8. 작업 흐름 (AI 에이전트용)

0. **`docs/handoff/15`(관성 방지 원칙)를 읽지 않고 오케스트레이터·워커·엔진을 수정하지 않는다.**
1. **읽기 우선**. 기존 파일을 수정하기 전에 반드시 Read.
2. **작은 단위 커밋**. 한 커밋은 한 가지 의도.
3. **테스트 가능한 산출물**. 매 Phase는 `python -m py_compile`과 import smoke test 통과.
4. **무리하게 미래 기능을 만들지 않는다**. 본 Phase 범위 안에서만 구현.
5. **사용자가 명시적으로 요청하지 않은 PR 생성 금지**.

## C9. 보안 / 권리

- `.env`, `credentials.json`, OAuth 토큰을 커밋하지 않습니다.
- X / Telegram / 기사 영상 다운로드 시 `rights_status`를 반드시 기록합니다.
- AI 이미지 가공은 GOAL G4-10(v1.0.0 개정) 조건 하에 허용: 실존 요소는 실자료 입력 가공만,
  무입력 사실 생성 금지, 도구·원본·프롬프트 기록 의무, 사실 텍스트는 코드 렌더.
- 미검증·논평 정보는 영상 본문(자막·내레이션·카드·패널)에 `<미검증>` 같은 라벨을 **넣지 않는다**(사용자 결정 2026-09-29, D85).
  표기는 엔딩 카드 맨 마지막 줄에 **가장 작은 글씨** 한 줄(`rules end_card.notice_unverified`)로만 한다. 검증 상태 자체는 claims·provenance 에 그대로 기록한다(제목·썸네일 금지는 GOAL G4-7 그대로).

## C10. (폐지) 외부 코드 리뷰 — codex review

프로젝트 극초반 codex 코워킹 실험용 절차였음. **v0.43.1 에서 사용자 결정으로 완전 폐지** —
트리거·역할 분담·review-prompt 전달 규칙 모두 효력 없음. AI 어시스턴트는 본 절차를
실행하지 않는다. (과거 실행 기록은 DEVLOG / CHANGELOG / HANDOFF 의 이력으로만 남음.)


## C11. 관성 방지 규칙 (필독 `docs/handoff/15`)

"새 기능을 만들었는데 결과물에 나타나지 않는다"를 막는 규칙이다. **주입하지 말고 교체한다.**
근거는 agents_reviewer 실제 사고(미배선 게이트, 조용한 드롭, 모델 상수 override, 파국 폴백,
byte-equal 원칙)다. 위반은 `tests/anti_inertia/`가 잡는다.

| # | 규칙 |
|---|---|
| P1 | 새 엔진(`engine/`, `script/`, `audio/`)은 오케스트레이터 밖 독립 패키지 + CLI. 오케스트레이터는 얇은 어댑터(`engine_service.py`)로 호출만 하고 입력 파일을 쓰지 않는다. |
| P2 | 옛 경로는 플래그가 아니라 **삭제**로 끝낸다. 보존은 `archive/hyperframes-briefing` 브랜치. |
| P3 | 규칙 SSOT는 `rules/video_rules.yaml` 하나. **워커 프롬프트 코드 상수 금지** → `prompts/*.md` 템플릿 + 규칙 파일에서 생성. 모델명·주요 설정은 `config.yaml` 한 곳, 모듈 상수 override 금지. |
| P4 | 프롬프트가 예시로 보여 주는 출력은 해당 Pydantic 스키마를 그대로 통과해야 한다(테스트로 강제). |
| P5 | 영상마다 `out/provenance.json`으로 "이번 영상에 실제로 쓰인 기능"을 증명한다. 돌지 않은 단계는 기록하지 않는다. |
| P6 | **조용한 드롭·폴백 금지.** 검증 실패는 오류 또는 `drops[]` 기록 후 실패. **폴백으로 옛 스타일 영상을 내보내지 않는다.** |
| P7 | 헌법(CLAUDE.md·GOAL.md)의 영상 기준이 먼저 바뀐다(C0, G7). |
| P8 | 장면 구성·연출은 LLM+사용자, 렌더 수치·검증·권리는 코드. **코드가 "정규화"로 LLM 구성을 옛 모양으로 되돌리지 않는다.** |
| P9 | 각 LLM 단계는 자기 몫의 입력만 본다. 이전 버전 산출물·옛 템플릿을 "참고"로 넣지 않는다. |
| P10 | 레지스트리에 없는 이벤트 타입·패널·미디어 형태 = 오류. 레지스트리에 있는데 렌더러가 없음 = 오류. |
| P11 | QA 판정·사용자 피드백을 live 프롬프트에 **자동 편입 금지**. 반복 지적은 규칙 파일 개정(사람 승인) → 프롬프트 재생성. |
| P12 | 변경은 한 번에 하나, 결과는 영상(프리뷰 컨택트 시트 + provenance)으로 확인. 코드 리뷰만으로 "적용됨" 판정 금지. |

개편 중 결정은 `docs/handoff/DECISIONS.md`에 한 줄씩 append 한다(판정 기준 ① 되돌릴 수 있는 선택
우선 ② 핸드오프 문서를 따름 ③ 핸드오프와 저장소 실측 규칙이 충돌하면 저장소 규칙 + 기록).
**결정 주체(2026-09-27 사용자 지시)**: 구현 세션은 결정을 혼자 내리지 않는다. `back_and_forth/`에
`decision_request`를 올리고 감독 세션(Fable)이 결정한다(`back_and_forth/README.md` §6.4). 사용자 고유 결정
(같은 문서 §7)은 Fable도 결정하지 않고 사용자에게 묻는다.

---

본 문서를 위반하는 PR은 자동으로 차단되어야 합니다. 차단 메커니즘이 아직 없다면
관련 PR과 함께 git hook 또는 CI 검증기를 추가합니다.
