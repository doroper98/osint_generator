<!--
tier: 2
last_synced_with: v0.3.3
ssot_for: [subscription-llm-bridge, base-llm-worker-contract, llm-call-traceability]
depends_on: [03_AGENT_ARCHITECTURE.md, ../GOAL.md, ../CLAUDE.md]
last_review: 2026-05-19
-->

# ADDENDUM 04 — Subscription LLM Bridge Pattern

> **본 시스템은 LLM API 키를 사용하지 않습니다.**
>
> 모든 LLM 활용은 사용자가 이미 구독 중인 **Claude 구독** (`claude` CLI · Claude Code 류) 과
> **ChatGPT 구독** (`codex` CLI) 을 **subprocess 로 자동 호출**하는 방식으로만 수행합니다.
>
> 본 부속서는 GOAL.md G4 와 **동등한 강제력**으로 운용됩니다. 위반은 PR 단계에서 거부됩니다.

---

## 1. 본 문서의 위상

- **Tier 2 ADDENDUM**. `docs/03_AGENT_ARCHITECTURE.md` 의 정식 부속서.
- **강제력**: `GOAL.md G4 #1~12` 와 동등. 본 문서를 위반하는 코드/설정/의존성은 PR 차단 대상.
- **흡수 계획**: v1.0.0 으로 갈 때 G4 본문에 "G4.13" 형태로 정식 흡수 (그 시점에 MAJOR 증분).
- **갱신**: BaseLLMWorker 인터페이스가 바뀌면 본 문서를 먼저 갱신 후 `last_synced_with` 동기화.

---

## 2. 핵심 원칙 (Hard Constraints)

### 2.1 절대 금지 (Hard NO)

1. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY` 등 **LLM 제공자 API 키를 코드/환경변수/설정파일에 둔다**.
2. `anthropic`, `openai`, `google-generativeai` 등 **LLM 제공자 공식 Python SDK 를 `requirements.txt` / `pyproject.toml` 에 추가한다**.
3. 구독 CLI 를 우회하여 **HTTP 클라이언트로 LLM provider endpoint 를 직접 호출한다** (`httpx.post("api.anthropic.com/...")` 류).
4. CLI 실행 결과를 **무검증 그대로 도메인 산출물로 채택한다** (Pydantic 모델 검증 누락).

위 4 항목은 git pre-commit hook / CI 단계에서 정적 스캔으로 차단해야 합니다 (구현은 후속 버전).

### 2.2 절대 준수 (Hard YES)

1. 모든 LLM 호출은 **`workers/base_llm_worker.py:BaseLLMWorker` 를 상속한 Worker** 가 수행한다.
2. 모든 LLM 호출은 **subprocess 호출**로 이루어지며 사용자 머신의 **구독 인증 세션** 을 그대로 활용한다.
3. 모든 LLM 호출의 입력/출력은 **`projects/{pid}/llm_calls/{call_id}.json`** 으로 디스크에 영속화된다 (§6).
4. LLM 응답은 **Pydantic 모델로 검증된 뒤에만** 도메인 산출물로 인정된다.

---

## 3. 왜 (Rationale)

| 사유 | 설명 |
|---|---|
| **비용 예측성** | 정액 구독은 영상 1편당 토큰 비용을 따로 계산할 필요가 없다. API 는 토큰당 과금이라 길이가 길어지는 대본/리서치에서 비용이 빠르게 증가. |
| **Rate limit 여유** | 구독은 사용자가 본인 한도 안에서 자유로움. API 의 organization-level rate limit 보다 일반적으로 후함. |
| **모델 업데이트 우선순위** | Anthropic/OpenAI 의 최신 모델 (Opus 4.7 등) 이 구독 측에 먼저 반영되는 경우가 많다. |
| **자원 활용** | 사용자가 이미 결제 중인 자원을 자동화 파이프라인이 흡수하여 활용도 극대화. |
| **이중 인증/관리 단일화** | API 키 회전·유출·해지 관리가 없어진다. 구독 만료만 신경 쓰면 됨. |
| **취향·문체 일관성** | 사용자가 평소 사용하는 LLM 의 응답 스타일과 자동화 파이프라인이 일관됨. |

---

## 4. BaseLLMWorker 설계 (코드 인터페이스)

> **v0.2.2 에 코드 도입 완료**: `workers/base_llm_worker.py:BaseLLMWorker`.
> `OSINT_LLM_STUB=1` 환경변수로 실 CLI 호출을 우회하는 stub 모드 지원 (smoke test 전용).
> Stub 모드 / 실 `claude` CLI 양쪽으로 v0.2.2 smoke test 통과. 단 실 응답 wrapper 처리는
> [LLM-AP-001](ANTIPATTERNS/LLM_ANTIPATTERNS.md#llm-ap-001) 으로 등록, 구조적 조치는 v0.2.3 patch 예정.

```python
# workers/base_llm_worker.py
from typing import Literal
from workers.base_worker import BaseWorker
from schemas.models import TaskResult, VersionedModel


class BaseLLMWorker(BaseWorker):
    """LLM 호출이 필요한 모든 Worker 의 공통 베이스.

    하위 클래스는 다음만 구현합니다:
      - llm_backend, llm_mode, system_prompt
      - build_user_prompt(task) -> str
      - parse_response(raw_text) -> VersionedModel
      - output_path(task) -> Path  (parse_response 결과를 어디에 저장할지)
    """

    llm_backend: Literal["claude", "codex"]
    llm_mode: Literal["response", "agent"]
    system_prompt: str

    def build_user_prompt(self, task) -> str: ...
    def parse_response(self, raw_text: str) -> VersionedModel: ...

    # 본 메서드는 base 가 제공하며 하위 클래스는 건드리지 않는다.
    def _invoke_llm(self, prompt: str) -> str: ...
    def _log_llm_call(self, ...) -> Path: ...
```

### 4.1 두 가지 호출 모드

| 모드 | 의미 | 호출 형태 (가정) | 적용 Worker |
|---|---|---|---|
| `response` | 단순 LLM 응답. 도구·파일 IO 없음. JSON one-shot. | `claude -p "<prompt>" --output-format json` | Phase 3 `dynamic_intake_planner`, Phase 6 `research_agent`, Phase 11 `youtube_metadata_agent` 등 |
| `agent` | CLI 가 도구·파일 IO 를 사용해 task 를 직접 처리. `task_result.json` 까지 CLI 가 작성. | `claude --print --add-dir <project_dir> -p "<task_spec>"` (또는 그에 상응하는 codex 호출) | Phase 7 `source_collector_worker` 처럼 외부 자료 수집·정리가 복잡한 경우 |

**구분 기준**: 산출물이 **단일 JSON 문서로 표현 가능**하면 `response`, **파일 시스템 위에서 다단계 작업**이 필요하면 `agent`.

### 4.2 백엔드 선택 기준 (가이드)

> 강제는 아닙니다. Worker 가 자신에게 더 적합한 백엔드를 선택합니다.

| 작업 성격 | 추천 백엔드 | 이유 |
|---|---|---|
| 한국어 자연어 생성 (intake_plan, full_script) | `claude` | 한국어 표현 자연스러움, 톤 일관성 |
| 구조화 JSON one-shot | `claude` | 스키마 준수도가 안정적 |
| 코드/셸 명령 생성 | `codex` | OpenAI 측 강점 |
| 다국어 번역·교차 검증 | 둘 다 (A/B) | 신뢰도 cross-check |
| 큰 파일 컨텍스트 분석 | `claude` | 긴 컨텍스트 안정성 |
| 도구 사용 chain (web search 등) | 사용자 머신 CLI 의 도구 정책에 따라 선택 | |

---

## 5. CLI 인터페이스 가정 (v0.2.1 기준)

> 본 절은 사용자 머신의 CLI 가 제공하는 인자에 따라 조정됩니다. 실제 호출 인자가 바뀌면
> `BaseLLMWorker._invoke_llm` 의 backend dispatcher 만 갱신하면 됩니다.

### 5.1 `claude` CLI (Claude Code 류 · Claude.ai 구독)

- 진입: `claude -p "<prompt>"` (response mode) / `claude --print --add-dir <dir> -p "<spec>"` (agent mode)
- 인증: 사용자 머신의 Claude.ai 로그인 세션을 자동 사용 (별도 키 주입 X)
- 출력: stdout 으로 응답 텍스트, optionally `--output-format json`
- 에러: 종료 코드 비-0, stderr 에 사유

### 5.2 `codex` CLI (ChatGPT Plus/Pro 구독)

- 진입: 사용자 머신 기준 정확한 인자는 v0.2.2 코드 도입 시점에 검증·기록.
- 인증: 사용자 머신의 ChatGPT 로그인 세션을 자동 사용.
- 출력: stdout 으로 응답.

### 5.3 추상화 원칙

각 Worker 는 **`self._invoke_llm(prompt)`** 만 호출하고, BaseLLMWorker 가 `llm_backend` 값을 보고
backend 별 인자 매핑·파싱·에러 처리를 흡수합니다. Worker 본문에서 `subprocess` 를 직접 호출하지
마십시오.

---

## 6. 추적성 · 재현성 (Traceability)

모든 LLM 호출은 디스크에 영속화됩니다. 본 시스템의 핵심 가치인
"영상 한 편의 모든 결정이 역추적 가능" (GOAL.md G6) 의 LLM 측 구현입니다.

### 6.1 디렉토리 구조

```
projects/{project_id}/
  llm_calls/
    {call_id}.json          # 호출 1건당 1파일 (append-only)
    {call_id}.prompt.txt    # 큰 프롬프트는 별도 파일
    {call_id}.raw.txt       # 큰 응답은 별도 파일
```

### 6.2 `{call_id}.json` 스키마 (요약)

```json
{
  "schema_version": 1,
  "call_id": "llm_20260519_142312_a1b2",
  "task_id": "task_0007",
  "worker": "dynamic_intake_planner",
  "backend": "claude",
  "mode": "response",
  "system_prompt_hash": "sha256:...",
  "user_prompt_path": "llm_calls/llm_20260519_142312_a1b2.prompt.txt",
  "raw_response_path": "llm_calls/llm_20260519_142312_a1b2.raw.txt",
  "parsed_status": "ok",
  "started_at": "2026-05-19T14:23:12Z",
  "completed_at": "2026-05-19T14:23:25Z",
  "exit_code": 0,
  "retry_index": 0
}
```

> **Pydantic 모델**: `schemas/models.py` 의 `LLMCallRecord` (v0.2.2 코드 도입 시점에 추가).

### 6.3 `task_result.json` 연결

`TaskResult.outputs` 에 위 경로를 포함시킵니다. 이 규칙으로 모든 LLM 호출은 task 단위로
역추적됩니다.

---

## 7. 에러·실패 모드

| 케이스 | 처리 | task_result.status |
|---|---|---|
| CLI 미설치 (`claude` not found) | 즉시 종료, 사용자에게 설치 안내 | `FAILED`, errors=["claude CLI not installed"] |
| 구독 인증 만료 / 로그인 필요 | retry 안 함 (사용자 액션 필요) | `NEEDS_USER_CONFIRMATION`, "구독 재로그인 필요" |
| Rate limit / 일일 한도 초과 | retry_after 기록, 사용자 알림 | `NEEDS_USER_CONFIRMATION` |
| stdout JSON 파싱 실패 | system prompt 에 스키마 재명시 후 **1회 재시도**. 그래도 실패면 FAILED + LLM-AP 카탈로그 등록. | `FAILED` |
| Pydantic 검증 실패 (필드 누락) | retry 1회 (스키마 다시 강조). 그래도 실패면 FAILED. | `FAILED` |
| LLM 이 `<미검증>` 라벨을 누락 | Evidence Guard 가 catch (Phase 6). 단순 FAILED 가 아니라 `qa_status=fail`. | `COMPLETED` + `qa_status=FAIL` |
| LLM 환각 / 사실 오류 | `qa_evidence_report.json` 에 기록, Review Gate 단계에서 사용자가 차단. | 별도 흐름 |

---

## 8. 향후 확장 / 미결 항목

1. **CLI 응답 wrapper unwrap** (v0.2.3): [LLM-AP-001](ANTIPATTERNS/LLM_ANTIPATTERNS.md#llm-ap-001) 구조적 조치. `claude -p --output-format json` 의 wrapper 를 `BaseLLMWorker._invoke_llm` 내부에서 unwrap. codex wrapper 도 동시 검증.
2. **정적 스캔** (v0.2.3 이후): pre-commit 또는 CI 가 `requirements.txt` 에서 금지 SDK, 코드에서 금지 환경변수 사용을 자동 차단.
3. **LLM 호출 캐시** (Phase 6 이후): 동일 입력 프롬프트가 반복되면 디스크에서 재사용 (특히 retry / re-render 시).
4. **A/B 라우팅** (Phase 8 이후): 같은 task 를 claude/codex 양쪽에 보내 응답을 비교하는 검증 모드.
5. **G4 정식 흡수** (v1.0.0): 본 부속서의 §2.1 / §2.2 를 GOAL.md G4 #13 으로 흡수, MAJOR 증분.

---

## 9. 관련 안티패턴 카테고리

문제 발생 시 `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 에 `LLM-AP-N` 으로 append-only 기록.
(`CLAUDE.md` C6 카테고리 목록 참조)

---

본 부속서를 위반하는 PR 은 자동으로 차단되어야 합니다. 차단 메커니즘이 아직 없다면
관련 PR 과 함께 git hook 또는 CI 검증기를 추가합니다.
