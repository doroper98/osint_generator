<!--
tier: 3
last_synced_with: v0.2.8
ssot_for: [release-notes]
depends_on: [README.md, GOAL.md]
last_review: 2026-05-19
-->

# CHANGELOG

본 문서는 사용자(또는 후속 개발자) 관점의 릴리즈 노트입니다.
released 항목은 **append-only**입니다.

본 저장소는 [Semantic Versioning](https://semver.org/)을 따릅니다.

---

## [Unreleased]

### Added
- 

### Changed
-

### Fixed
-

---

## [v0.2.8] — 2026-05-20

Codex 2차 리뷰 (3-way 통합 검수) 의 High 2건 중 코드 측 H2 반영. H1 은 절차 이슈로 별도 처리.

### Fixed (외부 코드 리뷰 2차 반영 — codex `exec review` H2)
- **`_write_manifest` durability + 예외 안전 보강** — v0.2.7 의 atomic write 는 visibility (rename atomicity) 만 보장했고, 전원장애·강제종료 시 마지막 write 유실 가능성이 있었음. tmp write 직후 `flush()` + `os.fsync(fd)` 로 데이터의 디스크 도달을 보장하고, rename 직후 부모 디렉토리 `os.fsync(dir_fd)` (POSIX 한정, Windows 는 `O_DIRECTORY` 미지원이라 best-effort skip) 로 rename 사실까지 durable. 또한 write/replace 도중 예외 발생 시 leftover tmp 파일을 best-effort `unlink` 로 cleanup (실패해도 원본 예외만 전파).
- docstring 을 "atomic visibility" vs "durability" 로 명시적으로 분리하여 향후 reader 가 어떤 보장이 어디까지 적용되는지 명확화.

### Notes
- 본 PATCH 는 외부 리뷰 결과 흡수 PATCH 이지만 C10.3 의 자기 검증 면제는 적용 안 함 (코드 변경 있음, M/L 항목은 다음 PATCH 로 분리하기 위해 본 PATCH 만 다시 검증 가능 상태로 둠).
- 5 케이스 smoke test: 정상 happy path / `Path.replace` 실패 시 tmp cleanup 검증 / corrupt manifest → `ValidationError` / non-JSON → `JSONDecodeError`. 30/30 기존 단위 테스트 회귀 통과.
- Codex H1 (Ij1TX 원본 커밋 `ef49e49` 부재) 은 코드가 아닌 절차 이슈. Codex Cloud 에 비교 브랜치를 fetch 하도록 안내 (다음 리뷰 요청 시 `claude/start-after-handoff-Ij1TX` 명시).
- Codex M/L 항목 (TUI reload `PermissionError`/`OSError` 분기, current_state 대입 조건 단순화, SCHEMA-AP-001 회귀 테스트 추가, _SLUG_RE 주석 정합화, state_machine ARCHIVED 중복 표현, CLAUDE.md C5.2 해석 충돌) 은 다음 PATCH (v0.2.9) 또는 Phase 3 진입 전 일괄 처리 후보.

---

## [v0.2.7] — 2026-05-20

평행 브랜치 (`claude/start-after-handoff-Ij1TX`) 흡수 — SCHEMA-AP 카탈로그 + TUI 라이브 manifest 반영 + atomic write.

배경: 동일 출발점 (`v0.1.5` main) 에서 두 Claude Code 세션이 평행으로 Phase 2 를 구현. 본 브랜치 (`claude/phase-2-finalize` ← `n9ird` 베이스) 가 정본이고, Ij1TX 의 차별점 3 가지만 본 PATCH 로 가져옴.

### Added
- **`docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md`** 신설 + **SCHEMA-AP-001** 등록: `ProjectState` 임의 점프 / self-loop 전이. mitigation 칸에 `LINEAR_SEQUENCE` + `allowed_next_states` + `transition_state` 단일 진입점 + atomic write 의 4중 방어 명시.
- **TUI Job Dashboard 라이브 manifest 반영** — `orchestrator/tui_app.py:_tick_loop` 가 매 tick 마다 `load_manifest` 로 디스크 재로딩. 외부 프로세스 (`python -m orchestrator.main transition ...`) 의 상태 변경을 TUI 가 즉시 따라잡음. 변경 감지 시 Orch CLI Log 에 `state changed: A → B` 한 줄 emit.

### Changed
- **`orchestrator/project_manager.py:_write_manifest`** atomic write 화. `path.write_text` 직접 호출 → tmp 파일에 쓴 뒤 `Path.replace` 로 교체. 외부 reader (TUI 라이브 reload) 가 half-written 상태를 보는 race 차단. POSIX rename / Windows `os.replace` 모두 atomic.
- `docs/ANTIPATTERNS/README.md` SCHEMA-AP 줄을 "Phase 2부터" → "Phase 2 v0.2.7 신설, SCHEMA-AP-001~" 로 갱신.
- 모든 Tier 1·2·3 마크다운 `last_synced_with: v0.2.6 → v0.2.7` 일괄 갱신.

### Fixed
- TUI 가 외부 `transition` CLI 호출 후에도 stale state 를 표시하던 문제.
- `_write_manifest` 의 partial-write race (드물지만 atomic 미적용 시 reader 가 깨진 JSON 을 볼 수 있었음).

### Failure modes added to `_reload_manifest_state`
- `FileNotFoundError` → state=`unknown` 표시, 다음 tick 재시도.
- `JSONDecodeError` / `pydantic.ValidationError` → state=`invalid` 표시, 다음 tick 재시도. 동일 상태 진입 시에만 1 회 stderr 로그 (noise 억제).
- 모든 예외 swallow → tick loop 유지.

### Notes
- 본 PATCH 는 코드 변경이 작아 (3 파일, ~70 줄 추가) C10 self-exemption 가 아닌 정식 codex review 대상. 통합 검수 시 본 브랜치 + n9ird + Ij1TX 3-way 비교를 권장.
- 평행 브랜치 `claude/start-after-handoff-Ij1TX` 는 본 흡수 완료 후 폐기 예정.
- 단위 테스트 5 케이스 smoke (생성·atomic·전이·corrupt manifest ValidationError·non-JSON JSONDecodeError) 모두 통과.

---

## [v0.2.6] — 2026-05-20

### Added
- **CLAUDE.md C10 — 외부 코드 리뷰 (codex review) 의무화**. MINOR/MAJOR/Phase 완료 직전 codex review 1 회 실행 필수. Critical/High 흡수 후에만 버전 증분 허용. 본 절차 자체와 외부 리뷰 결과 흡수 PATCH 는 자기 검증 면제.
- **`docs/REVIEW_PROMPT.md`** 신설 (tier 2 ssot_for=codex-review-procedure). 표준 영문 프롬프트 템플릿, Windows cmd / macOS-Linux 호출 명령어, 결과 해석 가이드 (Critical/High/Medium/Low/Nit), 거짓 양성 처리 절차, 절차의 알려진 한계.
- **`HANDOFF.md`** 의 신규 세션 체크리스트에 codex review 단계 + 30 단위 테스트 통과 확인 명령 추가.

### Changed
- `HANDOFF.md` 의 "1. 지금 어디까지 와 있나" 표에 v0.2.3 / v0.2.4 / v0.2.5 / v0.2.6 행 추가, "2. 다음 작업" 절을 Phase 3 (v0.3.0 — Dynamic Intake Page + IntakePlannerWorker) 로 갱신. 알려진 antipattern 카탈로그 갱신 (LLM-AP-001/002 resolved, LLM-AP-003 resolved-partial).
- "자주 까먹는 규칙" 에 agent 모드 opt-in, codex review 의무, parsed_status 4 상태, exit_code Optional, output_path 컨테인먼트 항목 추가.

### Notes
- 본 PATCH 는 거버넌스 강화 + 다음 세션 인계 정리. 코드/스키마/테스트 변경 없음.
- C10.3 의 self-exemption 에 의해 본 PATCH 자체에는 codex review 를 돌리지 않음.

---

## [v0.2.5] — 2026-05-20

### Fixed (외부 코드 리뷰 1차 반영 — codex `exec review`)
- **(H1) 비0 종료 stdout 보존** — `LLMSubprocessError` 에 `stdout`/`stderr`/`exit_code` 첨부. CLI 가 비0 으로 종료해도 stdout 부분이 `raw.txt` 에 영속화되어 postmortem 가능.
- **(H2) Timeout stdout/exit_code 보존** — `subprocess.TimeoutExpired.stdout/stderr` 를 동일 경로로 보존. `exit_code=None` 으로 "미완료" sentinel 기록.
- **(H3) `parse_failed` 도달 가능** — `model_validate_json` 대신 `json.loads` → `model_validate(dict)` 2 단계로 분리. JSON 파싱 실패와 schema 위반이 별도 `parsed_status` 로 기록.
- **(H4) `LLMCallRecord` 항상 영속화** — `run()` 전체를 `try/finally` 로 감싸 어떤 예외 경로에서도 record/prompt/raw 3 파일이 디스크에 남음. output write 실패 시에도 record 의 `error_message` 에 기록.
- **(H5) `output_path` 컨테인먼트 검증** — `_validate_output_path` 헬퍼 추가. project_dir 밖이면 거부, `task.output_refs` 가 비어있지 않으면 그중 하나와 일치해야 함. CLAUDE.md C4 "writes only own output_refs" 의 코드 단 가드.
- **(M1) claude wrapper subtype 엄격화** — `type=="result"` 인데 `subtype != "success"` 면 `LLMSubprocessError` raise (이전 pass-through 였음 → `validation_failed` 로 흡수돼 원인 추적 어려웠음).

### Added
- **(H6 / LLM-AP-003) agent 모드 opt-in 가드** — `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False`. `llm_mode="agent"` worker 가 `allow_agent_mode=True` 를 명시 선언하지 않으면 LLM 호출 전 즉시 `TaskResult(FAILED)`. prompt injection 면적 축소의 1 단계 가드. 본격 sandbox (CLI `--sandbox`, scratch dir) 는 Phase 3+ 후속.
- **(M3) `tests/test_base_llm_worker_run.py`** 신설 — 4 `parsed_status` 케이스 (ok / parse_failed / validation_failed / subprocess_error 2 종) + agent gate + output_path 컨테인먼트 (project_dir 밖 / output_refs 불일치) 총 8 케이스. 모든 케이스에서 prompt.txt / raw.txt / record.json 3 파일 영속화 검증.
- **(M1) `tests/test_base_llm_worker.py`** 에 wrapper subtype 검증 2 케이스 추가 (`subtype=partial`, subtype 누락).

### Changed
- **(M2) `schemas/models.py:LLMCallRecord.exit_code`** `int = 0` → `Optional[int] = None`. None = "CLI 호출 이전 실패" 또는 "timeout" sentinel. schema_version 1 유지 (호환 변경).
- `LLM_ANTIPATTERNS.md` 에 **LLM-AP-003** 신규 등록 (status=`resolved-partial`).

### Notes
- 단위 테스트 총 20 → 30 케이스 (unwrap 22 + run 통합 8). 전부 통과.
- 외부 리뷰 verdict ("방향성 OK, 추적성/상태 분류 정밀화 필요") 의 모든 High/Medium 항목 반영. Low/Nit 은 모두 OK 확인 항목이라 변경 없음.
- Phase 3 의 IntakePlannerWorker 가 BaseLLMWorker 를 상속할 때 보장되는 것: (a) record 가 어떤 실패 경로에서도 남음, (b) output_path 가 project_dir 안에 강제, (c) agent 모드는 의도적 opt-in 필요, (d) 모든 4 parsed_status 가 의미적으로 구분.

---

## [v0.2.4] — 2026-05-20

### Fixed
- **LLM-AP-002 발견 즉시 해결** — `codex exec --json` 의 stdout 은 단일 JSON wrapper 가 아니라 JSONL 이벤트 스트림 (`thread.started` / `turn.started` / `item.completed` / `turn.completed`). 도메인 응답은 마지막 `item.completed` 의 `item.type=="agent_message"` 의 `text` 필드. `_unwrap_codex_response` 가 JSONL 을 순회하며 마지막 agent_message 의 text 를 추출하고, markdown fence 가 끼면 `_extract_json_block` 으로 한 번 더 벗긴다.

### Changed
- `workers/base_llm_worker.py:CLI_INVOCATION` 의 codex 매핑 보강:
  - `--skip-git-repo-check` 추가 (project_dir 이 .git 아닐 수 있음)
  - `--color never` 추가 (ANSI 코드 안전장치)
  - agent 모드는 `--cd {project_dir}` 유지
- 검증 환경: codex-cli 0.130.0 (Windows cmd). 실제 한 줄 호출 캡쳐를 fixture 로 보존.

### Added
- `tests/test_base_llm_worker.py::TestUnwrapCodexResponse` 8 케이스 — 실 캡쳐 / markdown fence / 다중 agent_message / tool_call 등 미지 item type 무시 / agent_message 없음 → `LLMSubprocessError` / 단일 JSON pass-through / non-JSONL pass-through / 빈 입력. 총 단위 테스트 13 → 20 케이스.
- `LLM_ANTIPATTERNS.md` 에 **LLM-AP-002** 신규 등록 (status=resolved, 발견 즉시 해결).

### Notes
- 알려진 한계: 다중 turn / `--output-schema` / `--output-last-message` 같은 더 견고한 codex 옵션은 도입하지 않음 (단순성 우선). Phase 3 에서 schema 강제 도입 재검토.
- 본 fix 로 v0.2.2 시점의 "codex 는 별도 후속" 항목이 해소됨. Phase 3 의 IntakePlannerWorker 가 backend 를 claude/codex 어느 쪽으로 설정해도 BaseLLMWorker 가 정상 동작.

---

## [v0.2.3] — 2026-05-20

### Fixed
- **LLM-AP-001 구조적 조치** — `BaseLLMWorker` 가 `claude -p ... --output-format json` 의 wrapper (`{type:result, subtype:success, result:"...", ...}`) 를 벗긴 뒤 `response_model.model_validate_json` 을 호출하도록 변경. wrapper `is_error=True` 면 `LLMSubprocessError` 로 변환. `result` 문자열 안의 markdown code fence (```` ```json ... ``` ````) 도 자동 제거.
- `raw.txt` 영속화는 unwrap 전 stdout 그대로 유지 → 디버깅 추적성 보존.

### Added
- `tests/__init__.py`, `tests/test_base_llm_worker.py` — 13 케이스 단위 테스트 (extract_json_block 5 / claude wrapper 7 / codex pass-through 1). `python -m unittest tests.test_base_llm_worker` 통과.
- `workers/base_llm_worker.py` 에 모듈 레벨 헬퍼: `_unwrap_claude_response`, `_unwrap_codex_response`, `_extract_json_block`. `BaseLLMWorker._unwrap_response(raw)` 가 `self.llm_backend` 로 dispatch.

### Notes
- codex CLI wrapper 는 v0.2.3 시점 미검증 → pass-through. 실제 호출 가능 환경 확보 후 별도 작업 (LLM-AP-002 후보) 으로 분리.
- LLM-AP-001 status `active` → `resolved`.

---

## [v0.2.2] — 2026-05-20

### Added
- **`workers/base_llm_worker.py:BaseLLMWorker` 코드 도입** (ADDENDUM_04 §4 의 정식 구현).
  - 클래스 변수: `llm_backend ∈ {"claude", "codex"}`, `llm_mode ∈ {"response", "agent"}`, `system_prompt`, `response_model`.
  - 추상 메서드: `build_user_prompt(args, task)`, `output_path(args, task)`.
  - `_invoke_llm` 가 backend/mode 별 `CLI_INVOCATION` 매핑으로 subprocess 호출. `FileNotFoundError` / `TimeoutExpired` / 비0 종료 모두 `LLMSubprocessError` 로 흡수.
  - `OSINT_LLM_STUB=1` + `OSINT_LLM_STUB_RESPONSE` 환경변수로 실 CLI 우회 (smoke test 전용).
  - 전 호출이 `projects/{pid}/llm_calls/{call_id}.{json,prompt.txt,raw.txt}` 3 파일로 영속화.
- `schemas/models.py` 에 `LLMCallRecord` Pydantic 모델 추가. `parsed_status ∈ {"ok", "parse_failed", "validation_failed", "subprocess_error"}`.
- `workers/dummy_llm_worker.py` 신설 (`DummyLLMResponse` 응답 모델 포함). smoke test 전용.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 의 첫 항목 **LLM-AP-001** 등록 — `claude -p ... --output-format json` 응답이 wrapper JSON (`type/subtype/result/usage/uuid` 등) 으로 감싸여 있어 그대로는 도메인 Pydantic 모델 검증 통과 안 함. 구조적 조치 v0.2.3 patch.

### Changed
- `docs/ADDENDUM_04 §4` 인트로를 "v0.2.2 코드 도입 완료" 로 갱신, §8 #1 미결 항목을 LLM-AP-001 으로 구체화.

### Notes
- smoke test 4 케이스 (정상 stub / 잘못된 JSON / 스키마 위반 / 실 claude CLI) 모두 의도대로 동작. LLMCallRecord 4건 영속화 확인.
- `BaseLLMWorker` 는 새 Worker 베이스이므로 C5.4 의 MINOR 사유 ("새 Worker 추가") 에 해당. MINOR 0.2.1 → 0.2.2.

---

## [v0.2.1] — 2026-05-19

### Added
- **Subscription LLM Bridge 패턴 정식 문서화** — 본 시스템은 LLM API 키를 사용하지 않고, 사용자가 이미 구독 중인 `claude` (Claude.ai) 와 `codex` (ChatGPT Plus/Pro) CLI 를 subprocess 로 자동 호출한다는 핵심 아키텍처 결정 정립.
- `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설. GOAL.md G4 와 동등한 강제력으로 운용. `BaseLLMWorker` 인터페이스 명세, 호출 모드 (`response` / `agent`), 백엔드 선택 가이드, 추적성 (`projects/{pid}/llm_calls/{call_id}.json`), 에러 모드 정의.
- `docs/03_AGENT_ARCHITECTURE.md` §4.5 에 `BaseLLMWorker` 계약 요약 추가. §4 베이스워커 안내문에 "LLM 호출은 `BaseLLMWorker` 상속 필수" 명시.
- `CLAUDE.md` C6 안티패턴 카테고리에 `LLM-AP-N` 추가.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 골격 신설 (항목은 Phase 3 첫 실 호출부터 누적).
- `docs/ANTIPATTERNS/README.md` 인덱스에 `LLM-AP` 행 추가.

### Notes
- 본 변경은 **G4 본문은 건드리지 않는** PATCH. ADDENDUM_04 가 G4 와 동등한 강제력을 갖도록 본문에 명시. v1.0.0 시점에 G4 #13 으로 정식 흡수 (MAJOR 증분).
- 코드 변경 없음. `BaseLLMWorker` 코드는 v0.2.2 patch 또는 Phase 3 시작 시점에 도입.

---

## [v0.2.0] — 2026-05-19

### Added
- **Phase 2 완료: Project Manager / State Machine**.
- `orchestrator/state_machine.py` 신설. `LINEAR_SEQUENCE` 가 docs/02 §4 의 24개 상태 선형 흐름을 SSOT 로 보유. `allowed_next_states` / `validate_transition` 순수 함수 제공.
- `orchestrator/project_manager.py` 신설. `project_manifest.json` 의 유일한 쓰기자. `new_project` / `resume_project` / `transition_state` 공개 API.
- `schemas/models.py` 에 `StateTransition` 모델 추가, `ProjectManifest.state_history` (append-only) 필드 추가. schema_version 은 1 유지 (optional 필드 추가).
- CLI 명령 `new-project <pid> --title ... --category ... [--duration-min] [--topic-summary]`, `resume <pid>`, `transition <pid> --to <state> [--reason]` 정식 구현.
- 전이 규칙: 선형 다음 상태 또는 `archived` 만 허용. 동일 상태 전이 / 임의 점프는 명확한 한글 메시지와 함께 `ValueError` (CLI exit=2).

### Changed
- `orchestrator/command_center.py` 가 `project_manager.load_manifest` 를 통해 manifest 를 read-only 로 로드하도록 정리. raw json 파싱 코드 제거.
- `orchestrator/main.py` 의 `new-project` / `approve` placeholder 문구 제거, 실 구현으로 교체.

---

## [v0.1.5] — 2026-05-19

### Removed
- `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에서 `test/graph-demo` 항목 삭제 (브랜치 자체가 삭제됨).
- `COMMIT_DESCRIPTIONS` 에서 `0159299` 엔트리 삭제 (해당 commit 이 도달 가능한 브랜치가 없어 dead code).

### Changed
- `test/graph-demo` 원격 브랜치 사용자 측에서 삭제 완료 (v0.1.3 그래프 분기 시각화 검증 종료).

---

## [v0.1.4] — 2026-05-19

### Added
- `docs/branches.html` 에 `COMMIT_DESCRIPTIONS` 맵 추가. 영어로 작성된 과거 커밋의 한글 설명을 SHA(앞 7자) 기준으로 override. 신규 커밋은 처음부터 한글로 작성하면 맵 갱신 불필요.
- `BRANCH_PRIORITY` + `sortBranchRefs` 헬퍼 추가. 같은 SHA 에 여러 브랜치가 가리킬 때 라벨 표시 우선순위 결정 (main → develop → release/ → feature/ → test/ → claude/ → 그 외 알파벳).
- `BRANCH_DESCRIPTIONS` 에 `test/graph-demo` 항목 추가 (임시 검증 브랜치).

### Fixed
- 같은 SHA 를 두 브랜치가 가리킬 때 `main` 라벨이 안 보이고 부차 브랜치 라벨만 보이던 문제 수정. (`sortBranchRefs` 가 main 을 항상 앞에 배치)

---

## [v0.1.3] — 2026-05-19

### Added
- `HANDOFF.md` (Tier 1) 신설. 다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 인계 문서. 현재 상태, Phase 2 후보, 체크리스트, 자주 까먹는 규칙 정리.
- `docs/branches.html` 에 `@gitgraph/js` (jsDelivr CDN) 통합. 모든 브랜치를 단일 SVG git graph 로 렌더. 브랜치가 갈라지면 자동으로 가지 그림이 나옴.
- 사이드 패널이 등록되지 않은 브랜치를 자동 감지해서 "설명 미등록" 경고 카드로 노출 (한글).

### Changed
- `docs/branches.html` 의 데이터 모델을 commit-graph 중심으로 재작성. 브랜치별 commit 을 전역 SHA 맵으로 통합, parents 필드 활용해 토폴로지 보존. 모든 브랜치 commit fetch 병렬화 (`Promise.all`).

---

## [v0.1.2] — 2026-05-19

### Added
- `docs/index.html` 추가. 루트 URL (`/`) 접근 시 `/branches.html` 로 즉시 리다이렉트 (meta-refresh + JS 양쪽).

### Fixed
- Vercel 배포에서 루트 URL 이 `404: NOT_FOUND` 를 반환하던 문제 수정. `vercel.json` 의 `rewrites` 룰이 `outputDirectory: "docs"` 와 함께 쓰일 때 안정적이지 않아 실제 `index.html` 파일로 대체.

### Changed
- `vercel.json` 에서 `rewrites` 블록 제거 (정적 `index.html` 로 충분).

---

## [v0.1.1] — 2026-05-19

### Added
- `vercel.json` 루트 추가. Vercel 로 `docs/` 정적 호스팅 (Private 저장소 호환). 푸시마다 자동 재배포.
- `docs/branches.html` 에 Personal Access Token 입력 다이얼로그 추가. 토큰은 브라우저 localStorage 에만 저장. Private 저장소 GitHub API 호출에 사용.
- README 에 Vercel 설정 절차 + PAT 발급 절차 안내.

### Changed
- GitHub default branch 가 `main` 으로 통합됨에 따라 로컬 브랜치도 `main` 으로 rename, `branches.html:BRANCH_DESCRIPTIONS` 도 갱신.
- `branches.html:loadVersion` 이 raw.githubusercontent.com 대신 `/contents/VERSION` API 를 사용하도록 변경 (Private 저장소에서도 Bearer 인증으로 동작).
- 모든 Tier 1·2·3 마크다운/HTML 의 `last_synced_with: v0.1.0 → v0.1.1` 동기화.

### Fixed
- 없음 (Phase 1 PIPELINE-AP-006 은 v0.1.0 안에서 fix 됨).

---

## [v0.1.0] — 2026-05-19

### Added
- 저장소 초기화 (Phase 0)
- Tier 1 거버넌스 문서: `README.md`, `GOAL.md`, `CLAUDE.md`, `DOCS_GOVERNANCE.md`
- Tier 3 운영 문서: `CHANGELOG.md`, `DEVLOG.md`, `WORKFLOWS.md`
- Tier 2 스펙 문서 19종 (`docs/00_~16_`, `docs/ADDENDUM_01~03`)
- Antipattern 카탈로그 골격 (`docs/ANTIPATTERNS/README.md`, `TTS_ANTIPATTERNS.md`, `PIPELINE_ANTIPATTERNS.md`)
- 프로젝트 스캐폴딩: `pyproject.toml`, `requirements.txt`, `config.yaml`, `run_pipeline.bat`, `.gitignore`, `.githooks/commit-msg`
- Pydantic 스키마 모듈 `schemas/models.py` (project_manifest, task_queue, worker_slot, task_result 등)
- **Phase 1 MVP**: Orchestrator Command Center (Textual TUI)
  - `orchestrator/command_center.py` — TUI 진입점
  - `orchestrator/tui_app.py` — Orch CLI Log + Job Dashboard + Worker Slot 4개 패널
  - `orchestrator/worker_slot_manager.py` — Worker subprocess 배정
  - `orchestrator/log_router.py` — Worker stdout/stderr 라우팅
  - `orchestrator/dashboard.py` — 작업 현황 집계
  - `orchestrator/config.py` — config.yaml 로더
  - `workers/base_worker.py` — Worker CLI 공통 베이스
  - `workers/dummy_worker.py` — Phase 1 검증용 더미 워커
- 데모 프로젝트 `projects/demo/`와 4개 dummy task가 포함된 `task_queue.json`
