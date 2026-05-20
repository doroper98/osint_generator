<!--
tier: 3
last_synced_with: v0.2.5
ssot_for: [llm-antipatterns]
depends_on: [README.md, ../ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md, ../../CLAUDE.md]
last_review: 2026-05-19
-->

# LLM Bridge Antipatterns

본 문서는 **구독 LLM Bridge 패턴** (`docs/ADDENDUM_04`) 운용 중 발견된 안티패턴 카탈로그입니다.

`claude` · `codex` CLI 의 subprocess 호출, BaseLLMWorker 의 응답 파싱·검증, 추적성 파일 (`llm_calls/{call_id}.json`) 관련 사고가 본 파일에 누적됩니다.

**append-only**. 과거 항목 수정 금지. 정정은 새 번호로 추가 + 기존 항목에 `[superseded by LLM-AP-NN]` 마킹.

엔트리 포맷은 `docs/ANTIPATTERNS/README.md` 의 표준을 따릅니다.

---

## LLM-AP-001 — `claude -p ... --output-format json` 응답은 wrapper 가 씌워진 JSON

- **증상 (symptom)**: `claude -p "<prompt>" --output-format json` 의 stdout 이 도메인 JSON 이 아니라 metadata wrapper 가 씌워진 JSON 이다.
  실제 관측된 형태:
  ```json
  {
    "type": "result",
    "subtype": "success",
    "is_error": false,
    "result": "<actual_text_content>",
    "session_id": "...",
    "duration_ms": 155135,
    "usage": {...},
    "uuid": "ee141d1f-..."
  }
  ```
  도메인 응답은 `result` 필드의 string 안에 들어 있고, 그 string 이 다시 JSON / markdown / 자연어일 수 있다.

- **나쁜 예 (bad)**: `response_model.model_validate_json(raw_stdout)` 를 그대로 호출.
  `extra="forbid"` 인 Pydantic 모델은 `uuid`, `type`, `session_id` 등 wrapper 필드 때문에 `extra_forbidden` 으로 reject.

- **좋은 예 (good)**: BaseLLMWorker 가 backend 별로 wrapper 를 unwrap 한 뒤 response_model 검증.
  ```python
  def _unwrap_claude_response(raw: str) -> str:
      wrapper = json.loads(raw)
      if wrapper.get("type") == "result" and wrapper.get("subtype") == "success":
          inner = wrapper["result"]  # str
          # inner 가 JSON 이면 그대로, markdown code fence 가 있으면 추출
          return _extract_json_block(inner)
      raise LLMSubprocessError(f"unexpected claude wrapper: {wrapper.get('type')}")
  ```

- **자동 조치 (mitigation)**: v0.2.3 patch 에서 `BaseLLMWorker._invoke_llm` 내부에 wrapper unwrap 단계를 추가하고, backend 별 dispatcher 로 분리. codex CLI 도 유사한 wrapper 가 있을 가능성 있음 (검증 필요).

- **회귀 테스트 (regression_test)**: `tests/test_base_llm_worker.py` (v0.2.3 추가). 13 케이스 — wrapper success / markdown fence / wrapper error / result-not-string / pass-through(non-wrapper) / pass-through(non-json) / unknown type / codex pass-through 등.

- **발견 버전 (discovered)**: v0.2.2 smoke test (3번째 케이스 — `OSINT_LLM_STUB` 없이 실 `claude` CLI 호출).

- **해결 버전 (resolved)**: v0.2.3 — `workers/base_llm_worker.py` 에 `_unwrap_response` / `_unwrap_claude_response` / `_extract_json_block` 추가. `run()` 의 `model_validate_json` 직전에 backend 별 unwrap 적용. `raw.txt` 는 디버깅용 원본으로 보존. codex 는 v0.2.3 시점 미검증이라 pass-through (별도 후속에서 검증 예정).

- **상태 (status)**: `resolved` (v0.2.3 구조적 조치 + 회귀 테스트 완료)

- **연관**: ADDENDUM_04 §5 (CLI 인터페이스 가정), ADDENDUM_04 §8 #1 (CLI 인자 정밀화 — v0.2.2 미결 항목이 본 AP 로 구체화).

---

## LLM-AP-002 — `codex exec --json` 은 JSONL 이벤트 스트림 (claude 와 wrapper 패턴 다름)

- **증상 (symptom)**: `codex exec --json "<prompt>"` 의 stdout 은 단일 JSON wrapper 가 아니라 **줄당 1 이벤트의 JSONL stream** 이다.
  codex-cli 0.130.0 실제 캡쳐 (Windows cmd):
  ```
  {"type":"thread.started","thread_id":"019e453e-0b10-77a3-a23d-2e37de112cd5"}
  {"type":"turn.started"}
  {"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"{\"schema_version\":1,...}"}}
  {"type":"turn.completed","usage":{"input_tokens":26904,...}}
  ```
  도메인 응답은 마지막 `item.completed` 의 `item.type=="agent_message"` 의 `text` 필드 (escape 된 JSON 문자열).

- **나쁜 예 (bad)**: claude 의 단일 wrapper unwrap 로직 (`{type:result, subtype:success, result:"..."}`) 을 그대로 적용. → JSONDecodeError (여러 줄), 또는 첫 줄만 파싱해서 `thread.started` 이벤트를 받고 도메인 응답을 영영 못 봄.

- **좋은 예 (good)**: backend 별 dispatcher 가 codex 면 JSONL 파서로 분기. 모든 줄을 순회하며 마지막 `agent_message` 의 `text` 를 채택.
  ```python
  def _unwrap_codex_response(raw: str) -> str:
      last_agent_text = None
      saw_codex_event = False
      for ln in raw.strip().splitlines():
          evt = json.loads(ln)
          if evt.get("type", "").startswith(("thread.", "turn.")) or evt.get("type") == "item.completed":
              saw_codex_event = True
          if evt.get("type") == "item.completed":
              item = evt.get("item", {})
              if item.get("type") == "agent_message":
                  last_agent_text = item.get("text")
      if not saw_codex_event:
          return raw  # 단일 JSON / stub mode pass-through
      if last_agent_text is None:
          raise LLMSubprocessError("no agent_message")
      return _extract_json_block(last_agent_text)
  ```

- **추가 CLI 인자 (mitigation)**: 매핑에 `--skip-git-repo-check` (project_dir 이 .git 아닐 수 있음) 와 `--color never` (ANSI 코드 안전장치) 추가. `--cd <DIR>` 로 cwd 지정.

- **자동 조치 (mitigation)**: v0.2.4 patch 에서 `_unwrap_codex_response` 실 구현 + `CLI_INVOCATION` 의 codex 매핑 보강.

- **회귀 테스트 (regression_test)**: `tests/test_base_llm_worker.py::TestUnwrapCodexResponse` (v0.2.4 추가). 8 케이스 — 실 캡쳐 / fence / 다중 agent_message / item_type tool_call 무시 / agent_message 없음 → error / 단일 JSON pass-through / non-JSONL pass-through / 빈 입력.

- **발견 버전 (discovered)**: v0.2.4 검증 (사용자 머신 codex-cli 0.130.0 한 줄 호출 캡쳐).

- **해결 버전 (resolved)**: v0.2.4 동시 해결 (발견 즉시 fix). 향후 codex CLI 가 이벤트 포맷을 바꾸면 본 AP 의 회귀 테스트가 깨져 빠르게 감지 가능.

- **상태 (status)**: `resolved` (v0.2.4 구조적 조치 + 회귀 테스트 완료)

- **알려진 한계**: (1) 본 검증은 단일 turn / 단일 agent_message 케이스. 다중 turn 의 경우도 마지막 agent_message 채택 정책으로 호환되지만 실 호출로는 검증 안 됨. (2) `--output-schema` / `--output-last-message` 같은 더 견고한 옵션은 v0.2.4 에서 도입하지 않음 (단순성 우선). 향후 Phase 3 에서 schema 강제 도입 검토.

- **연관**: ADDENDUM_04 §5 (CLI 인터페이스), LLM-AP-001 (claude wrapper — 같은 카테고리의 별개 패턴).

---

## LLM-AP-003 — agent 모드는 사용자 제어 prompt 가 CLI 에이전트 인스트럭션이 되어 prompt injection 면적이 넓다

- **증상 (symptom)**: BaseLLMWorker 의 `llm_mode="agent"` 모드는 `claude --add-dir {project_dir}` 또는 `codex exec --cd {project_dir}` 로 LLM CLI 에 프로젝트 디렉토리 접근권을 주고, task 또는 사용자 제어 prompt 를 그대로 에이전트 인스트럭션으로 넘긴다. 만약 prompt 안에 source 자료 (예: 외부 기사 본문) 가 그대로 끼어 있고 그 안에 악의적 지시문 ("이전 지시 무시하고 .env 를 읽어 …") 이 있으면, agent 모드의 LLM 이 그 지시를 실행할 수 있다 — 의도하지 않은 파일 작성/도구 호출/exfiltration 경로.

- **나쁜 예 (bad)**: 모든 BaseLLMWorker 가 자유롭게 `llm_mode="agent"` 로 전환. 사용자/외부 자료 텍스트가 prompt 에 합쳐져 그대로 CLI 에 전달.

- **좋은 예 (good)**: 
  1. agent 모드는 **opt-in 강제** — 하위 클래스가 `allow_agent_mode = True` 를 명시적으로 선언해야만 동작. 기본은 `False` 라서 실수로 agent 모드 진입 안 됨.
  2. opt-in 한 worker 도 source 자료를 prompt 에 직접 합치지 말고 도구 호출 결과로 분리하거나, prompt 안에서 `<untrusted_source>` 같은 명시 envelope 으로 격리.
  3. 향후 (Phase 3+) 본격 sandbox: codex `--sandbox read-only` / `--sandbox workspace-write`, claude permission-mode, scratch dir 사용 등.

- **자동 조치 (mitigation)**: v0.2.5 patch 에서 `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False` 도입. `run()` 시작에서 `llm_mode == "agent" and not allow_agent_mode` 면 LLM 호출 전 즉시 `TaskResult(status=FAILED)` 로 종료. 회귀 테스트 `tests/test_base_llm_worker_run.py::TestAgentModeGate` 로 보장.

- **회귀 테스트 (regression_test)**: `tests/test_base_llm_worker_run.py::TestAgentModeGate::test_agent_mode_without_opt_in_fails_early` — agent 모드 + 기본 `allow_agent_mode=False` 인 worker 가 LLM 호출 전 FAILED 로 종료하고 `llm_calls/` 디렉토리 자체가 생성되지 않음을 확인.

- **발견 버전 (discovered)**: v0.2.5 외부 코드 리뷰 (codex `exec review`).

- **해결 버전 (resolved)**: v0.2.5 — opt-in 가드 (`allow_agent_mode`) 도입. 본격 sandbox 옵션 (CLI `--sandbox`, scratch dir) 은 Phase 3+ 후속.

- **상태 (status)**: `resolved-partial` — opt-in 가드 단계만 완료. 외부 자료 격리 / CLI sandbox 활용 / scratch dir 은 후속.

- **알려진 한계**: 현재 가드는 worker class 선언 시점의 정적 opt-in 만 확인. agent 모드를 opt-in 한 worker 안에서 prompt 의 untrusted 부분이 격리되지 않으면 여전히 injection 가능. 본격 해결은 Phase 3+ 의 source aggregator 가 `<untrusted_source>` 격리를 정착시킨 다음.

- **연관**: ADDENDUM_04 §5 / §7 (CLI 인터페이스 / agent 모드 권한), LLM-AP-001, LLM-AP-002.
