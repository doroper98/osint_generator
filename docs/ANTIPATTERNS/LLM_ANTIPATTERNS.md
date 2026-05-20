<!--
tier: 3
last_synced_with: v0.2.3
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
