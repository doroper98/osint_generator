<!--
tier: 3
last_synced_with: v0.4.2
ssot_for: [llm-antipatterns]
depends_on: [README.md, ../ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md, ../../CLAUDE.md]
last_review: 2026-05-22
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

- **자동 조치 (mitigation)**:
  - v0.2.5 — `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False` 도입. `run()`
    시작에서 `llm_mode == "agent" and not allow_agent_mode` 면 LLM 호출 전 즉시
    `TaskResult(status=FAILED)` 로 종료. 회귀 `tests/test_base_llm_worker_run.py::TestAgentModeGate`.
  - v0.3.3 — `workers/prompt_safety.py:wrap_untrusted` 신설. 외부 자료를
    `<untrusted_source>` envelope 으로 격리하는 순수 함수. content / label 안의 동일
    태그 토큰을 case-insensitive / whitespace-tolerant 로 escape 해 envelope 가
    일찍 닫히거나 새로 열리지 않게 한다. opener 의 label 속성은 `"`·newline 안전화.
    Phase 5 의 `source_collector_worker` (BaseLLMWorker, `llm_mode="agent"`) 에서
    본격 사용 예정.
  - v0.4.0 — codex agent CLI 매핑에 `--sandbox workspace-write` 추가. `--cd` 를
    `{project_dir}` → `{scratch_dir}` (= `projects/{pid}/scratch/{task_id}/`) 로 변경.
    `BaseLLMWorker._scratch_dir_for_task` 헬퍼가 task 별 scratch 디렉토리를 mkdir.
    `_invoke_llm` 의 placeholder 치환 시 `llm_mode == "agent"` 일 때만 scratch dir
    경로로 치환 (response 모드는 빈 문자열). 의도된 가정 하에서 — codex 가
    `--sandbox workspace-write` 를 honor 하고, scratch 경로상 symlink 가 없으며,
    task_id 가 단일 path 세그먼트인 경우 — agent 는 (a) 사용자 자료 / (b) 다른
    worker 산출물 / (c) git 추적 코드 모두 건드릴 수 없다. v0.4.0 시점에는 본
    가정들의 실제 검증이 정적 정합성에 그침.
  - v0.4.1 — codex 1차 리뷰 흡수. v0.4.0 의 "의도된 가정" 들을 명시적 가드로 승격:
    (i) `_is_safe_path_segment` 로 task_id path traversal 거부 (C1),
    (ii) `_assert_no_symlinks_in_path` 로 scratch_root → scratch_dir 경로상 symlink
    검사 — sandbox 경계가 symlink 인 escape 시나리오 차단 (C2),
    (iii) `clean_scratch_on_start: ClassVar[bool] = True` 기본 — 잔존물 노출 차단 (M1),
    (iv) `_invoke_llm` 의 placeholder 치환을 template-driven 화: 치환 후 `{name}`
    잔존 토큰 fail-fast + response 모드 template 이 `{scratch_dir}` 를 가지면
    raise (H1+H2),
    (v) `tests/test_base_llm_worker_sandbox.py` 17 메소드로 위 가드를 회귀 잠금 (H3).
  - 후속 (Phase 5) — `source_collector_worker` 의 실제 agent 모드 호출 + e2e
    smoke test (실제 codex 프로세스를 띄워 sandbox escape 시나리오 테스트).

- **회귀 테스트 (regression_test)**:
  - `tests/test_base_llm_worker_run.py::TestAgentModeGate::test_agent_mode_without_opt_in_fails_early`
    — agent 모드 + 기본 `allow_agent_mode=False` 인 worker 가 LLM 호출 전 FAILED 로
    종료하고 `llm_calls/` 디렉토리 자체가 생성되지 않음을 확인.
  - `tests/test_prompt_safety.py` (v0.3.3, 13 메소드) — wrap 형식 / close-tag
    injection / open-tag injection / case·whitespace 변형 / label 안전화 5 카테고리.
  - `tests/test_base_llm_worker_sandbox.py` (v0.4.1, 11 메소드) — task_id 안전
    세그먼트 / scratch dir 멱등성 / clean_scratch_on_start 동작 / symlink preflight /
    codex-agent argv 의 `--sandbox workspace-write` + `--cd {scratch_dir}` 존재 /
    response argv 의 sandbox 부재 / placeholder 미해결 fail-fast / response 모드
    template 이 `{scratch_dir}` 가지면 raise 5 카테고리.
  - 실제 codex 프로세스 띄우는 sandbox escape 회귀는 Phase 5 worker 도입과 함께
    별도 (현재는 정적/단위 회귀에 그침).

- **발견 버전 (discovered)**: v0.2.5 외부 코드 리뷰 (codex `exec review`).

- **해결 버전 (resolved)**:
  - v0.2.5 — opt-in 가드 (`allow_agent_mode`).
  - v0.3.3 — envelope 헬퍼 (`wrap_untrusted`). 순수 함수 + 회귀 테스트만, 호출은 Phase 5.
  - v0.4.0 — codex `--sandbox workspace-write` 매핑 + scratch dir 격리 (CLI 매핑 +
    `_scratch_dir_for_task` 헬퍼).
  - v0.4.1 — codex 1차 리뷰 흡수: task_id traversal 가드 + symlink preflight +
    scratch ephemeral + placeholder fail-fast + 17 회귀 테스트.
  - v0.4.2 — 실 codex 0.130.0 (Windows) sandbox boundary 검증 완료. 본 항목의
    "verified guarantees" 와 "known side channels" 를 ADDENDUM_04 §5.2.1 에
    명시. (코드 변경 없음, 문서/known-limits 만 갱신.)
  - Phase 5 (예정) — `source_collector_worker` 의 실 호출 + e2e 검증.

- **상태 (status)**: `resolved-partial` — opt-in 가드 + envelope 헬퍼 + sandbox /
  scratch dir 매핑 + 경로 안전 가드 + 회귀 테스트까지 마련. 실 호출하는 agent
  모드 worker (`source_collector_worker`) 의 도입과 실제 codex 프로세스를 띄우는
  e2e sandbox escape 검증은 Phase 5 에서 완료 예정.

- **알려진 한계 (v0.4.2 갱신, 실 codex 0.130.0 Windows 검증 후)**:
  - **검증된 보호** (codex 0.130.0 Windows): workdir 의 sibling (다른 task scratch),
    git 추적 코드, 사용자 자료 (Desktop 등), junction 우회 — 모두 sandbox 가 차단.
    상세는 `docs/ADDENDUM_04` §5.2.1 의 검증 표.
  - **검증된 side channels** (우리가 닫을 수 없음, codex CLI 의 디폴트):
    (a) `%TEMP%` (Unix `/tmp`) write 허용 — prompt injection 으로 임시 자료 누설 /
    trojan 파일 가능. (b) `~/.codex/memories` write 허용 — long-lived semantic
    injection 경로. codex 다음 세션들에 영향. 영향 최소화는 system prompt 명시
    + 운영 절차 (memories 주기 점검).
  - sandbox / scratch dir 매핑은 도입했지만 아직 호출하는 agent 모드 worker 가 없음.
    Phase 5 의 `source_collector_worker` 가 들어오면 비로소 실 사용 검증 가능
    (실제 task 의 prompt injection 시나리오 / 산출물 의도 일치).
  - sandbox 가 활성화돼도 envelope 안에서 일반 문장으로 LLM 을 속이는 semantic
    injection 은 막지 못한다 — 시스템 prompt + envelope 명시 책임.
  - codex `--sandbox workspace-write` 의 실효 영역은 codex 버전 / OS 마다 다름.
    v0.4.2 는 codex 0.130.0 Windows 기준. 사용자 머신의 codex 갱신 / Linux/macOS
    배포 시 ADDENDUM_04 §5.2.1 재검증 필요.
  - v0.4.1 의 `_assert_no_symlinks_in_path` preflight 는 검증 결과 codex 0.130.0
    이 OS-level 에서 같은 일을 함 (junction 차단 확인). 우리 preflight 는 **defense-in-depth**
    — 다른 codex 버전 / 다른 backend (claude agent 등) / Linux/macOS 의 alternate symlink
    semantic 에 대비. 폐기하지 않는다.
  - `input_item_id` 같이 "도메인적으로 필수지만 schema 호환성 위해 optional" 인
    필드는 worker 단 task_type 별 검증으로 강제 (Phase 5 `source_collector_worker`
    의 의무).

- **연관**: ADDENDUM_04 §5 / §7 (CLI 인터페이스 / agent 모드 권한), LLM-AP-001, LLM-AP-002.

---

## LLM-AP-004 — `claude -p ... --output-format json` (response 모드) 가 cwd 의 CLAUDE.md/훅/도구를 물고 에이전트로 변질

- **증상 (symptom)**: response 모드 worker (ResearchWorker 등) 가 `claude -p "<prompt>" --output-format json` 으로 한 방 JSON 을 받으려 했는데, 실제로는 중첩 실행된 `claude` 가 **에이전트로 22턴**을 돌며 repo 의 CLAUDE.md 지시(버전 증분·commit·push)를 수행하려다 권한 거부당하고, 최종 `result` 가 도메인 JSON 이 아니라 `"Write permissions are waiting for your approval…"` 같은 채팅 메시지였다. 1회 호출에 **약 6분 / $0.74** 소모 후 `parse_failed`. (v0.8.0 6A 실제 run 에서 발견 — stub 테스트는 subprocess 를 타지 않아 전혀 잡지 못함.)

- **원인 (root cause)**: `claude -p` 는 print(비대화) 모드여도 (a) 내장 **도구(Bash/Edit 등)** 가 활성이고 (b) **cwd 에서 상위로 CLAUDE.md / `.claude/settings` 훅을 자동 탐색**한다. worker subprocess 가 repo cwd 에서 실행되므로 repo 의 거버넌스 문서·stop hook 이 system 컨텍스트에 주입되어, 모델이 "이 repo 에서 작업하라"로 해석하고 도구를 호출한다. `--output-format json` 은 출력 wrapper 만 규정할 뿐 에이전트화를 막지 못한다.

- **구조적 조치 (structural fix, v0.8.1)**:
  - `CLI_INVOCATION[("claude","response")]` 에 `--tools ""` (내장 도구 전체 비활성) + `--no-session-persistence` 추가. 도구가 없으면 파일 IO/Bash 불가 → 순수 텍스트 생성으로 강제.
  - `_invoke_llm` 이 subprocess 를 **repo 밖 중립 cwd**(`<tmp>/osint_llm_neutral_cwd`)에서 실행 → CLAUDE.md/훅 자동 탐색 차단. (도구만 꺼도 cwd 가 repo 면 CLAUDE.md 가 컨텍스트를 오염시켜 모델이 가짜 function_calls 를 내뱉는 것을 실측 확인.)
  - 효과 (실측): 22턴/6분/$0.74/JSON 아님 → **1턴/1.3초/$0.005/요청 JSON 정확 반환**.

- **발견 버전 (discovered)**: v0.8.0 (Phase 6A ResearchWorker 실제 claude 실행).

- **해결 버전 (resolved)**: v0.8.1 — CLI 매핑 `--tools ""`/`--no-session-persistence` + 중립 cwd. stub 테스트 242개 유지 통과, 실 run 으로 정상 dossier 생성 확인.

- **상태 (status)**: `resolved` (response 모드). 단 **agent 모드 claude (`--add-dir {project_dir} -p`)** 는 의도적으로 도구·repo 접근을 주므로 같은 hijack 면적이 남아 있다 — 본 모드는 codex 가 주 backend 이고 codex 는 자체 `--cd`/sandbox 로 cwd 비의존이라 영향이 다르다. claude agent 모드를 실제로 쓰게 되면 별도 검증 필요 (LLM-AP-003 와 함께).

- **알려진 한계**:
  - `--tools ""` 가 미래 claude CLI 버전에서 의미가 바뀌면 재검증 필요 (CLI 인터페이스는 ADDENDUM_04 §5 가정에 묶임).
  - 중립 cwd 의 상위 경로(예: `/tmp` 위)에 CLAUDE.md 가 있으면 여전히 탐색될 수 있음 — 운영 환경 가정상 극히 낮은 위험.
  - 본 조치는 **에이전트화/거버넌스 오염**을 막을 뿐, 모델이 소스 본문 없이 일반 지식으로 evidence quote 를 재구성하는 **인용 충실도 한계**(6A 품질이 source_registry 본문 적재량에 묶임)는 별개 — Phase 5 소스 수집이 본문까지 캡처해야 해소.

- **연관**: ADDENDUM_04 §5 (CLI 인터페이스), LLM-AP-001 (response wrapper), LLM-AP-003 (agent 모드 injection 면적).

---

## LLM-AP-005 — 비대한 입력(bundle 전체 prose)을 ScriptWorker 에 넣으면 LLM 이 출력을 쪼개고 형식을 깬다

- **증상 (symptom)**: 외부 연동(agents_reviewer report_bundle) 경로에서 build-script 가
  `parse_failed: Expecting value: line 1 column 1 (char 0)` 로 실패. 실제 claude 응답은
  빈 값이 아니라 (a) 서두 나레이션 prose + (b) "JSON 이 잘렸으니 두 부분으로 나눠
  출력하겠다" + (c) ```json 펜스 2개로 쪼갠 불완전 JSON + (d) 병합 설명 텍스트였다.
  latency 526초(ttft 430초)로 비정상.

- **재현 (repro)**: v5.5.0 real emit 번들(geo, 7 섹션·약 4,800자 prose)을 bundle 어댑터가
  섹션 prose 전체를 `research_dossier.summary` 로 통째 실어 ScriptWorker 에 넘김 →
  모델이 4~6분/12세그먼트 대본으로 압축하려다 출력이 비대해져 스스로 분할.

- **원인 (root cause)**: 두 겹.
  1. **입력 비대화**: 완성된 보고서 본문(수천 자)을 그대로 넘기면 모델이 그 디테일을
     보존하려 해 출력이 커지고, perceived token limit 에서 응답을 분할한다. (손으로 쓴
     작은 예시 번들은 같은 5분 대본을 한 블록으로 성공 — 차이는 입력 크기였다.)
  2. **추출기 취약**: `_extract_json_block` 이 텍스트가 ``` 로 **시작할 때만** 펜스를
     벗겨, 서두 prose 가 붙은 경우 통과시키지 못했다.

- **구조적 조치 (structural fix, v0.20.x)**:
  - 어댑터(`orchestrator/bundle_io.py`): 섹션당 prose 를 문장 경계에서 발췌
    (`_SECTION_PROSE_CAP=320`)해 '구조적 개요'만 summary 로 전달. 살은 ScriptWorker 가
    붙인다(5분 대본은 어차피 응축). geo summary 4,833 → 2,462자.
  - 추출기(`workers/base_llm_worker.py:_extract_json_block`): 서두 prose + 본문 중간
    ```json 블록, 또는 첫 균형 {...} 객체(문자열 내 중괄호/이스케이프 고려)를 추출하도록
    견고화. 단 모델이 **두 개의 분리된 JSON 객체**로 쪼개면 병합 불가 → 입력 캡으로
    분할 자체를 예방하는 것이 1차 방어.

- **상태 (status)**: 입력 캡 + 추출기 견고화. 실 run 재검증은 v0.20.x seam 에서.

- **알려진 한계**: 캡은 보고서 디테일 일부를 떨군다(5분 포맷의 본질적 응축). 더 충실한
  반영이 필요하면 섹션 단위 분할 생성(다중 LLM 호출) 또는 더 긴 영상 포맷이 별도 과제.

- **연관**: LLM-AP-001(claude wrapper), 계약 v1 §6(prose=나레이션 원천), CHANGELOG v0.20.x.

---

## LLM-AP-006 — 원고 LLM 의 AI 상투 문구(수렴 은유·해석 강요·예언형 결론)

- **증상 (symptom)**: 원고에 "n가지 화살이 한곳으로 모인다", "~로 읽으면 이렇다", "~의 방향을 정한다",
  "말하는 것, 그리고 말하지 않는 것" 같은 문장이 반복된다. 사실 대신 작가의 구도를 강요한다.
- **원인 (root cause)**: LLM 문체 관성. 결함 8종(수렴 은유·과장된 동시성·숫자 겹 은유·예언형 결론·
  회귀 수사·해석 강요·가짜 대구·"진짜 이유"류 메타 발언)은 `docs/handoff/03` §2.
- **구조적 조치 (structural fix, v2.3.0)**: 금지 패턴의 **정본은 `rules/video_rules.yaml`
  `banned_phrases.patterns` 하나**다(15 P3). 이 문서는 패턴을 따로 두지 않고 참조만 한다.
  `script/lint.py`가 plan 단계에서 검사해 하나라도 맞으면 음성 합성 전에 실패한다.
  새 문구는 `banned_phrases.candidates`에 넣고 사람 승인 뒤 patterns 로 승격한다.
- **회귀 테스트 (regression_test)**: `tests/test_script_lint.py` — 사용자 지정 12문구 전부 검출,
  v3 원고 45문장 통과. 띄어쓰기 변형("같은자리로", "않는것")도 잡도록 v2.3.0 에 패턴 3개를 `\s?`로 넓혔다.
- **연관**: 03 §2·§2.1, back_and_forth D-0021 작업 2.

## LLM-AP-007 — 새 호출 모드를 추가하고 호출 기록 스키마에 넣지 않음
- **증상 (symptom)**: 시각 검수(vision 모드)가 판정 파일을 쓰고 나서 `LLMCallRecord.mode` 검증 실패로 단계 실패.
- **원인 (root cause)**: `BaseLLMWorker.llm_mode` 에 `vision` 을 더하고 `schemas/models.py LLMCallRecord.mode` Literal 은 그대로 뒀다. 스텁 워커 테스트는 기록 경로를 타지 않았다.
- **구조적 조치 (structural fix, v3.1.0)**: Literal 에 `vision` 추가(하위 호환). 모드마다 실제 기록 경로를 타는 테스트.
- **회귀 테스트 (regression_test)**: `tests/test_base_llm_worker_run.py::TestVisionModeRecord` — 수정 전 실패 확인.
- **연관**: back_and_forth D-0047 작업 8·10, hormuz_ai 실측.

## LLM-AP-008 — 선택 객체 안의 필수 필드를 프롬프트가 "선택"으로만 적어 LLM 이 빼먹음
- **증상 (symptom)**: 시각 검수 판정 JSON 에서 `fix` 에 `suggest` 만 쓰고 `event_ref` 를 빠뜨려 스키마 오류 → 재요청이 반복됐다(taiwan 4회·hormuz_ai_cam 1회, back_and_forth D-0062 NB21).
- **원인 (root cause)**: 프롬프트가 `fix`(선택: `event_ref`, `suggest`) 처럼 **바깥 객체가 선택**이라는 것만 적었다. 안쪽 두 필드가 둘 다 필수(`engine.qa.QAFix`)라는 것과, 대상을 못 집을 때 쓸 값이 없었다.
- **구조적 조치 (structural fix, v4.0.0)**: `prompts/visual_qa.md` 에 "fix 를 쓰면 event_ref·suggest 둘 다 필수, 대상을 못 집으면 컷 이름, 제안이 없으면 fix 를 쓰지 않는다" 를 명시. 판정·피드백을 자동 편입하지 않고 사람 승인(D-0072) 문구 개정만 했다(15 P11).
- **회귀 테스트 (regression_test)**: `tests/test_phase11_nb21.py` — 스키마 필수 필드 = 프롬프트 필수 규칙 문구(파리티), 컷 이름 event_ref 가 코드에서 해석됨. 옛 문구에서는 파리티 테스트가 실패한다.
- **연관**: back_and_forth D-0062 NB21, D-0072 작업 11, PIPELINE-AP-008(표지 해석).


## LLM-AP-009 — LLM 브리지가 프롬프트를 명령줄 인자(argv)로 넘겨 긴 입력에서 OSError
- **증상 (symptom)**: 소스 37건인 프로젝트(dmz_mine_2026)에서 verify-sources 가 `OSError: [Errno 7] Argument list too long` 으로 실패했다. 프롬프트 한 인자가 리눅스 한도(단일 인자 128KB, `MAX_ARG_STRLEN`)를 넘었다.
- **재현 (reproduction)**: 기사 본문을 붙인 소스 30건 이상으로 `python -m orchestrator.main verify-sources <pid>` — 프롬프트 문자열이 약 128KB 를 넘으면 subprocess 생성 단계에서 실패(LLM 호출 전).
- **원인 (root cause)**: 구독 LLM 브리지가 `claude -p "<프롬프트 전체>"` 처럼 프롬프트를 argv 한 칸으로 넘긴다. 입력 크기가 소스 수·본문 길이에 비례해 커지는데 한도를 보지 않는다.
- **우회 (workaround, 그 세션)**: 기사 본문의 메뉴·잡음을 덜어 약 110KB 로 줄였다(원본은 로컬 보관). 구조 해결이 아니다.
- **구조적 조치 (structural fix, 예정 — G8 후보, back_and_forth D-0104 S1)**: 프롬프트를 stdin 으로 넘긴다(`claude -p` 는 stdin 입력을 받는다). argv 형태를 고정한 회귀 테스트를 stdin 형태로 갱신하고, 128KB 넘는 합성 프롬프트로 실패하지 않음을 확인한다. 이번 병합(v4.7.0)에서는 기록만 한다.
- **회귀 테스트 (regression_test)**: 구조 조치 때 추가(현재 없음).
- **연관**: vibrant-mendel 브랜치 보고 R-0118(원 R-0111) S1, docs/ADDENDUM_04(구독 LLM 브리지), back_and_forth D-0104.
- **상태 (status)**: `[resolved v4.10.0]` — 프롬프트를 stdin 으로 넘기고 argv 경로 삭제(`CLI_INVOCATION` 에 `{prompt}` 없음, 있으면 빌드 오류). 회귀 테스트 `tests/test_g9_llm_stdin.py`(140KB 프롬프트 실 subprocess 통과·argv 대조군 OSError), back_and_forth D-0116.

## LLM-AP-010 — 수정 LLM 의 issue_ref 표기가 검사 id 와 달라 지적 이벤트가 "지적 없이 변경"으로 거부됨
- **증상 (symptom)**: fed_policy AI 연출 v8 의 수정 회차가 3번 연속 "지적받지 않은 부분을 바꿨다"(`unchanged_violations`)로 거부됐다. 바꾼 이벤트는 checks `island_overlap` 이 지적한 statement_diff·dot_plot 이었다.
- **재현 (reproduction)**: checks 항목 `island_overlap` 이 hard 인 프리뷰에서 수정 LLM 이 changelog `issue_ref` 를 "island-overlap: …"(하이픈·줄인 상세) 또는 "[island-overlap]" 으로 적음 → `resolve_refs` 가 검사 id 로 풀지 못함 → 지적 이벤트 집합이 비어 변경이 위반으로 잡힘.
- **원인 (root cause)**: ① 검사 상세 문장에 이벤트 이름이 없어("primitive statement_diff" 만) 상세 → 이벤트 대응이 안 됐다. ② `resolve_refs` 가 검사 id 정확 일치(밑줄)만 받았다. LLM 은 상세 태그 모양(`[island-overlap]`)을 그대로 옮겨 적고 상세를 줄여 쓴다.
- **우회 (workaround, 그 세션)**: 없음 — 구조 조치 후 v9·v10 수정 회차가 통과했다.
- **구조적 조치 (structural fix)**: `[island-overlap]` 상세에 이벤트 이름(2b9ae07), `resolve_refs` 가 태그 모양·하이픈·줄인 상세도 검사 id 로 받아 그 검사 상세 전부를 지적 이벤트로 푼다(c46573b).
- **회귀 테스트 (regression_test)**: `tests/test_g12_island.py::OverlapTest::test_details_name_events_for_revision`(태그 모양 3가지 issue_ref).
- **연관**: back_and_forth R-0148 §4 보정 ②, D-0127 §6, docs/handoff/17 §5.5.
- **상태 (status)**: active

## LLM-AP-011 — 연출가가 statement_diff date 를 ISO(하이픈)로, 인용을 상한 넘게 적어 렌더 전 검증에서 반복 거부
- **증상 (symptom)**: G13 fed_policy 연출가 재실행 3회가 모두 `check_parsed: 이벤트 검증 실패` 로 거부됐다 — primitive statement_diff `date '2026-09-16'`(형식 YYYY.MM.DD 아님)·`before` 174자 > quote_max_chars 160. G12 연출가 1~3·5~6회 거부의 일부도 같은 인용 상한이었다(reports/phaseG12 §3.1).
- **재현 (reproduction)**: `rm projects/fed_policy_2026/direction.yaml && python tools/ai_direction_run.py projects/fed_policy_2026 --preview auto` — 연출 프롬프트 필드 표에 `date*: str`·`before*: str` 만 있음.
- **원인 (root cause)**: 필드 표(`workers.direction_io.event_fields_table`)가 타입만 보이고 스키마 검증기의 제약(날짜 형식·인용 상한)을 보이지 않았다. LLM 은 intake 원문 날짜(ISO)와 성명서 문단을 그대로 옮긴다.
- **우회 (workaround, 그 세션)**: 없음 — 구조 조치 후 재실행.
- **구조적 조치 (structural fix)**: 모델 필드 `description` 을 필드 표에 괄호로 붙인다(코드가 정본, 손으로 프롬프트에 적지 않음). statement_diff `date`·`before`·`after` 에 형식·상한(규칙 값 quote_max_chars) description.
- **회귀 테스트 (regression_test)**: `tests/test_g13.py::PromptTest::test_field_table_shows_schema_constraints`.
- **연관**: back_and_forth D-0129 §D, LLM-AP-010.
- **상태 (status)**: active

## LLM-AP-012 — 수정 LLM 이 "[검사-태그] 줄인 상세" 를 콜론 없이 적어 지적 이벤트 변경이 "지적 없이 변경"으로 거부
- **증상 (symptom)**: G13 fed 연출가 통과 뒤 첫 수정 회차가 island_overlap 이 지적한 statement_diff·dot_plot·photo 를 정확히 옮겼는데도 `unchanged_violations` 3건으로 거부됐다.
- **재현 (reproduction)**: changelog issue_ref = `"[island-overlap] island chart left ↔ primitive statement_diff … t=28.36~37.90"`(교차 면적 생략, 콜론 없음) + checks island_overlap 상세 → `resolve_refs` 가 ("*", 원문)만 남김.
- **원인 (root cause)**: LLM-AP-010 조치는 검사 id 그대로·"id:상세" 꼴만 받았다. 태그 괄호 뒤 공백 + 줄인 상세 꼴은 검사 id 로 풀리지 않았다.
- **우회 (workaround, 그 세션)**: 없음 — 구조 조치 후 같은 연출로 루프 재개.
- **구조적 조치 (structural fix)**: `engine.qa.TAG_RE` — issue_ref 가 `[검사-태그]` 로 시작하고 그 태그가 checks 항목(밑줄·하이픈)이면 그 검사 상세 전부를 지적 이벤트로 푼다. 거부된 실제 수정본으로 위반 0 확인.
- **회귀 테스트 (regression_test)**: `tests/test_g13.py::ResolveRefsTest::test_bracket_tag_without_colon`.
- **연관**: LLM-AP-010, back_and_forth D-0129 §D·D-0131.
- **상태 (status)**: active

## LLM-AP-013 — 원고 LLM 이 엇갈린 수치·미확인 서술을 넣고, 문장을 연결어 없이 사실의 나열로 씀

- **증상 (symptom)**: valdai-2026 원고(ScriptWorker 초안, v5.3.0 — 사용자 시청 2026-10-02). ① "수바우키 회랑 약 80km … 이 길이 수치를 두고는 출처마다 설명이 엇갈립니다", 봉쇄 준비설·하이브리드 공방(논쟁 주장), 마지막 장면 "아직 확인되지 않았습니다" 4문장. ② 50문장 중 앞 문장을 연결어로 받는 문장 0개 — 사용자 판정 "단순히 문구의 나열".
- **원리 (root cause)**: 옛 원고 프롬프트가 "도입 → 핵심 → 맥락 → **미확인 쟁점** → 정리"와 "마무리는 **아직 정해지지 않은 사실**로"를 권장했다(15 P11 이전의 균형 원칙을 그대로 옮긴 문구). 논쟁(disputed) 주장은 "양측을 함께 쓴다"고만 해서, LLM 은 엇갈린 수치도 '균형'으로 넣었다. 문장 하나 = 주장 하나 = 자막 한 장 규칙만 있고 문장 사이 관계에 대한 규칙이 없어, LLM 은 claim 목록을 순서대로 한 문장씩 옮겼다(나열). 린트도 문장 단위만 봤다.
- **좋은 예**: 확인된 사실과 귀속 발언만 쓴다. 엇갈린 수치·논쟁 주장은 넣지 않는다. 문장 사이에 관계를 드러내는 연결어(그래서·따라서·그렇지만·반면·이에 대해 등)로 흐름을 만든다 — 단 인과·대조 관계가 출처로 성립할 때만(근거 없는 "그러므로"는 사실 왜곡). 마무리는 확인된 사실의 정리.
- **구조적 조치 (structural fix)**: `rules script_grammar`(lines·connectives·connective_min_ratio 0.3·connective_max_ratio 0.7·uncertain_patterns) → 프롬프트 `{{RULES.script_grammar}}`(prompts/script.md, genre_script.md 마무리 문구 교체) + `script.lint` 오류 `[disputed-claim]`·`[uncertain-phrase]`·`[flow-sparse]`, 경고 `[flow-overuse]`. 게이트 ① 화면의 린트 줄에 그대로 보인다.
- **회귀 테스트 (regression_test)**: `tests/test_v531_quote_glow.py::ScriptGrammarTest`. v3 기준 원고(hormuz_korea)는 규약 이전 원고라 고치지 않는다 — 새 두 항목(미확인 서술 1·흐름 부족)만 걸림을 단언(`tests/test_script_lint.py`).
- **연관**: 사용자 결정 2026-10-02(v5.5.0), docs/handoff/03 §2(상투 문구), CLAUDE.md C0 경계(정확성).
- **상태 (status)**: active [partially superseded by LLM-AP-014 — disputed 전면 금지 → 무귀속만 금지]

## LLM-AP-014 — 규약 과잉 일반화: "엇갈린 수치 금지"를 "논쟁 주장 전면 금지"로 구현해 양측 병기를 막음

- **증상 (symptom)**: LLM-AP-013 구조 조치(v5.5.0 첫 구현)가 disputed claim 을 인용한 문장을 모두 오류로 막았다. valdai-2026 의 "러시아 대사관들은 ~ 주장했습니다 / 나토는 ~ 밝혔습니다" 양측 병기 4문장, "AP통신은 약 80km라고 보도했습니다"까지 오류. 사용자 점검(2026-10-03): "막지 말고 논쟁 중이라는 사실을 언급하면 되는 것 아니야?"
- **원리 (root cause)**: claim status(disputed)는 **내용**의 논쟁 여부다. "누가 무엇을 말했다"는 문장은 내용을 단정하지 않으므로 사실이다. 구현이 이 둘을 구분하지 않아 CLAUDE.md C0 "논쟁 사안은 양측을 같은 무게로"와 직접 충돌했다. 같은 이유로 미확인 패턴("불확실"·"알려지지 않")이 귀속 문장("IMF는 불확실성이 커졌다고 밝혔습니다")까지 잡았고, 연결어 검사는 프롬프트가 "등"으로 예시만 준 목록 밖 접속어(그리고·다만·이후)를 세지 못했다. 또 새 오류가 게이트 ① 차단 목록에 없어 승인 뒤 음성 단계에서야 막혔다.
- **좋은 예**: 논쟁 주장 = 양측 귀속 병기(허용). 무귀속 단정·내레이터의 미확인 결론만 오류. 연결어 목록은 프롬프트에 린트와 같은 목록으로 노출, 단어 경계("즉시"≠"즉"). 새 원고 오류는 게이트 ① 전에.
- **구조적 조치 (structural fix)**: `script.lint` — disputed-claim·uncertain-phrase 는 귀속 표현이 있으면 면제("확인되지 않" 표지는 귀속에서 제외), `starts_with_connective`(단어 경계). `rules script_grammar` 문안·connectives 확장·uncertain_patterns 문장 끝 형태로 축소. `source_completeness_checker.BLOCKING` 에 세 항목. 프롬프트 `연결어 목록:` 줄.
- **회귀 테스트 (regression_test)**: `tests/test_v531_quote_glow.py::ScriptGrammarTest`(양측 병기 허용·무귀속 오류·귀속 미확인 허용·단어 경계·프롬프트 목록·게이트 차단).
- **연관**: 사용자 결정 2026-10-03, LLM-AP-013, CLAUDE.md C0 경계, docs/handoff/03 §3·§12.
- **상태 (status)**: active

## LLM-AP-015 — 원고가 참조 출처를 내레이션으로 반복하고("위키백과에 따르면"·"위키백과는 전했습니다"), 과거 일을 현재형으로 쓰고, "정리하면"으로 맺음

- **증상 (symptom)**: kaliningrad-suwalki 원고(v5.5.1, 사용자 시청 2026-10-04) — ① "위키백과에 따르면" 7회, "…라고 위키백과는 전했습니다" 1회 — 사용자: "너무 많이 나옴, 위키백과가 전했다는 말도 맞지 않음". ② "이 땅의 옛 이름은 쾨니히스베르크입니다"·"…세운 도시입니다"처럼 과거 일을 현재형으로 — "헷갈린다". ③ 마무리 "정리하면, …" — "앵커 브리핑처럼 맺어 달라".
- **원리 (root cause)**: unverified claim 은 귀속 표현이 없으면 린트 경고가 나서, 원고(LLM·나)가 경고를 없애려고 출처 이름을 내레이션에 붙였다(백과사전에 '보도·전달' 동사까지). 시제 규칙이 없었고, 마무리 규칙은 "확인된 사실의 정리"라 '정리하면'을 불렀다.
- **좋은 예**: 참조 출처는 화면 아래 작은 링크로(rules `source_note` — 그 문장 동안 자동, 버전 도장과 같은 크기), 내레이션은 사실만. 과거 사건·과거 상태는 과거형. 마무리 = 대상의 정체 한 문장 + 지금 상황 + 지켜볼 지점("1946년까지 쾨니히스베르크로 불렸던 칼리닌그라드." … "계속 지켜봐야 하겠습니다").
- **구조적 조치 (structural fix)**: 린트 `reference-in-narration`(오류 — `source_note.spoken_names`), `tense-present`(경고 — 문장 날짜가 영상 해보다 앞인데 현재형 종결), 화면 표기 귀속이면 attribution 경고 면제(`noted_claims`). `script_grammar.lines` 3줄(시제·참조 출처·앵커 브리핑 마무리) → 원고 프롬프트. `engine/source_note.py`(sid → 링크, provenance `source_note`).
- **회귀 테스트 (regression_test)**: `tests/test_v560_script_review.py::ScriptRulesTest`
- **연관**: 사용자 결정 2026-10-04, LLM-AP-013·014, CLAUDE.md C9(검증 상태는 기록, 화면 귀속).
- **상태 (status)**: active


## LLM-AP-016 — 사용자가 바꾼 마무리 결정이 규약에 반영되지 않음("지켜봐야 하겠습니다"가 모범 예시로 남음)

- **증상(실제 현상)**: 2026-10-04 사용자 결정 — "마지막에 지켜봐야겠습니다가 아니라, 끓어오르고 있습니다. hot war 같은 지정학 포럼 용어를 써서 다듬어 봐. 마무리를 네 문장 정도로." 그 뒤 kaliningrad 원고는 고쳤지만, `rules script_grammar`·`prompts/script.md`·`prompts/genre_script.md`는 여전히 "③ 시청자가 지켜볼 지점(…계속 지켜봐야 하겠습니다)"을 모범으로 들고 있었다(2026-10-05 기록 점검에서 발견). 다음 영상의 원고 LLM 은 사용자가 거부한 마무리를 다시 쓴다.
- **원리**: 결정을 그 영상의 원고에만 반영하고 규칙 파일(SSOT)을 고치지 않았다. 앵커 브리핑 규칙(같은 날 앞선 결정)을 만들 때 넣은 예시 문구가, 뒤의 결정과 충돌한 채 남았다.
- **원칙**: 사용자가 원고 문구를 고친 이유가 일반적이면(마무리 방식·어조) 그 영상만이 아니라 규칙을 고친다. 같은 날 규칙과 뒤 결정이 충돌하면 뒤 결정이 이긴다.
- **자동 조치**: script_grammar 마무리 ③ = 긴장의 현재 상태를 단정하는 결론("끓어오르고 있습니다"), 포럼 용어는 귀속, 3~4문장. `banned_phrases.patterns` 에 `지켜봐야\s?(하겠|할|겠)`·`귀추가 주목`(린트 slop 오류). 프롬프트 두 곳 수정. 테스트 `test_v560_script_review.test_closing_no_watch_phrase`·`test_rules_reach_prompt`.
- **발견 버전**: v5.6.0 · **상태**: active

## LLM-AP-017 — 결과(영유권 포기)를 말하면서 전제(독일 도시였던 시기)를 건너뜀

- **증상(실제 현상)**: kaliningrad-suwalki 본편(2026-10-04) 사용자 지적 — "독일의 영유권이 있던 적도 없는데 갑자기 영유권 포기 이야기가 나온다, 독일 이야기가 추가돼야". 원고가 1255년(튜턴 기사단) → 1945년(소련군 장악)으로 건너뛰어, 약 700년간 독일 도시였다는 전제 없이 1990년 "독일은 모든 영유권 주장을 포기했습니다"가 나왔다.
- **원리**: 원고 LLM(과 내 손질)이 검증된 claim 을 시간순으로 이어 붙이면서, claim 이 없는 구간(1255~1945)을 서사 공백으로 남겼다. 결과 문장의 주어(독일)가 앞에서 한 번도 소개되지 않았다.
- **원칙**: "포기·반환·철회·상실"을 말하면 그 전에 "보유·소유·지배"했던 사실과 시기를 쓴다. 근거 claim 이 없으면 출처를 더 모아 claim 을 만든다(근거 없는 연결 금지).
- **자동 조치**: `rules script_grammar` 줄 추가(원고 프롬프트에 그대로 들어감, 테스트 `test_rules_reach_prompt`). kaliningrad 원고 v3 = 프로이센 대관식 도시·전간기 동프로이센 2문장(clm_0066·0067). 기계적 린트는 없다(의미 판단) — 게이트 ① 원고 검토에서 사람이 본다.
- **발견 버전**: v5.6.0 · **상태**: active
