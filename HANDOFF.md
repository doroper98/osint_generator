<!--
tier: 1
last_synced_with: v0.34.2
ssot_for: [session-handoff]
depends_on: [CLAUDE.md, GOAL.md, VERSION, docs/13_IMPLEMENTATION_ROADMAP.md, docs/REVIEW_PROMPT.md, docs/PROFESSIONAL_REBUILD_PLAN.md]
last_review: 2026-06-05
-->

# HANDOFF — 다음 세션 AI 인계 문서

본 문서는 **다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 문서**입니다.
짧고 행동 지향적으로 유지합니다. 과거 항목은 `DEVLOG.md` 가, 미래 항목은 `docs/13_IMPLEMENTATION_ROADMAP.md` 가 정식 SSOT 입니다.

---

## ⏳ 다음 할 일 (사용자가 명시적으로 보류 — 까먹지 말고 먼저 상기시킬 것)

> agents_reviewer 외부 연동 슬라이스 진행 중(v0.18~0.23). 아래는 **사용자가 순서를 미룬**
> 작업이다. 세션 재개 시 **사용자에게 이 목록을 먼저 상기**시켜라.

1. **forced-alignment (자막 정밀 싱크)** — 현재 자막 큐 타이밍은 글자수 비례 추정
   (`render_io.split_subtitle_cues`). 정밀 싱크는 교체형 백엔드(TTS 패턴, `OSINT_ALIGN_*`)
   + 비례 폴백으로. **실제 음성 + 정렬 모델은 사용자 Windows 머신에서만**(이 클라우드는
   음성=stub + huggingface 차단). → 사용자가 "나중에(1)".
2. **③ 자동 캐치 트리거** — 지금은 수동(`import-bundle --file`). agents_reviewer 가
   `--bundle` 로 Pages 에 올린 새 번들을 감시→자동 import 하는 워처 CLI + push 알림 설계.
   상시 데몬/실행 위치 결정 필요. → 사용자가 "나중에(2)".
3. **차트·자막·타이포 프로페셔널 재빌드** (v0.30.0 ~ v0.36.0 사이클 — **진행 중**).
   사용자 평가 "전반적으로 너무 구려"에 대한 구조적 대응. 비주얼 기준은 **날리지식**
   (YouTube `FaOqn3-YdkI`, `ucl9RED4Ye4` — **YTN 세계는 날리지가 아님**).
   SSOT: `docs/PROFESSIONAL_REBUILD_PLAN.md` (Phase 0–5+E, MVP Professional Bar 20).
   - **v0.30.0 (완료)**: Phase 0 디자인 시스템 토대 — `design.ts` 토큰 + 공용 컴포넌트
     `ChartFrame` / `Axis` / `Callout` / `ReferenceRegion` + npm `d3-scale d3-shape
     d3-time-format d3-array d3-scale-chromatic labella`.
   - **v0.31.0 (완료)**: Phase 1 XY family 정통 재구현 — `charts/util.ts`(time-aware x
     스케일 + nice ticks y 스케일 + Material easing 결정론 t→y + 1D 라벨 충돌 회피 자체
     구현) + `XYChart`(line/area/stacked_area/small_multiples) + `DualLineChart` +
     `ForecastChart`. clipPath wipe, 끝점 직접 라벨, Subject+Note+Connector 콜아웃,
     ReferenceRegion 자동 노출.
   - **v0.32.0 (완료)**: Phase 2 Bar/Point family 정통 재구현 — `charts/cat/`{BarChart
     (bar/lollipop/range), StackedBarChart, Waterfall, PointChart(scatter/bubble),
     SlopeChart, CandleChart}. scaleBand + 카테고리 stagger + Material decelerate + 직접
     값 라벨 + bubble 면적 비례 + slope 양쪽 라벨 충돌 회피. legacy ~200 LOC 청산.
     15/21 차트가 design.ts 토큰 100% (71%).
   - **v0.33.0 (다음)**: Phase 3 Specialty — Donut(외부 라벨 + %), Gantt(time-wipe
     stagger + 마일스톤 별), Heatmap(셀 행→열 stagger + sequential color), Network
     (d3-force 헤드리스 사전 시뮬레이션 + degree 큰 노드부터 등장), Sankey(d3-sankey
     실 사용), Choropleth(world-atlas + ISO 매핑 + sequential color).
   - 이후: Phase 4 모멘트 음성 싱크 (v0.34.0) → Phase 5 자막/타이포 표준 (v0.35.0) →
     Phase E 최종 mp4 검수 (v0.36.0).
   - agents_reviewer 정적 SVG 는 **아직 렌더러 없는 복잡 타입의 폴백**으로만.
     `network/sankey/choropleth` 는 Phase 3 에서 d3-force / d3-sankey / world-atlas
     로 정통 재구현 예정.
4. **(사용자 액션) Windows 실제 음성 풀 렌더 검증** — 이 클라우드는 stub(무음)이라 지도+
   자막+실제 음성이 함께 도는 영상을 사용자가 본 적 없음. 브랜치 pull → `build-audio
   --backend elevenlabs` + `render-debug` 로 확인 (현재 사용자가 이걸 먼저 하는 중).

(이 블록은 v0.23.0 기준 최신. 처리되면 DEVLOG 에 반영하고 본 블록에서 제거.)

---

## 0. 너의 역할

너는 OSINT 영상 자동 생성 시스템을 단계별로 구축하는 본인 사용자의 페어 프로그래머다.
사용자는 한국어로 대화하며, **버전(vX.Y.Z) 중심으로 소통**한다.
모든 작업 규칙은 `CLAUDE.md` 에 정의되어 있다. **반드시 먼저 정독하라.**

핵심 원칙:

1. **단순함을 우선**. 만들지 않아도 되는 추상화는 만들지 마라.
2. **버전 표기 의무**. 모든 산출물에 버전 박기 (C5).
3. **append-only 카탈로그**. Antipatterns / CHANGELOG / DEVLOG 는 과거 항목 수정 금지.
4. **Worker 는 사용자에게 질문하지 않는다**. 판단이 필요하면 `status="needs_user_confirmation"`.
5. **사용자가 명시적으로 요청하지 않은 PR 생성 금지**.

---

## 1. 지금 어디까지 와 있나 (v0.3.3 기준)

### 완료된 Phase

| Phase | 버전 | 무엇 | 검증 |
|---|---|---|---|
| Phase 0: Governance | v0.1.0 | 저장소 구조, CLAUDE.md, GOAL.md, 16개 docs, 3개 ADDENDUM, Antipatterns, .githooks | commit-msg hook 통과 |
| Phase 1: Command Center MVP | v0.1.0 | Textual TUI (좌상단 Orch CLI Log, 좌하단 Job Dashboard, 우측 Worker Slot 1–4), WorkerSlotManager, dummy worker × 4 종료 코드 모두 검증 | `python -m py_compile`, smoke test, 6 tasks 병렬 실행 |
| 호스팅 / 인증 | v0.1.1 | Vercel 정적 호스팅 셋업, PAT 인증 다이얼로그, default branch `main` 통합 | 사용자 측 Vercel 연결 완료 |
| 호스팅 hotfix | v0.1.2 | Vercel 루트 URL 404 수정 (`docs/index.html` 추가) | 사용자 측 재배포 확인 |
| 브랜치 뷰어 그래프화 | v0.1.3 | `@gitgraph/js` 라이브러리로 진짜 git 토폴로지 SVG 그래프 렌더링 | 사용자 시각 확인 |
| 한글 라벨 + 분기 검증 | v0.1.4 | `COMMIT_DESCRIPTIONS` 한글 override, `BRANCH_PRIORITY` 정렬, `test/graph-demo` 분기 시연 | 사용자 스크린샷 확인 |
| 검증 정리 | v0.1.5 | `test/graph-demo` 삭제 + dead code 청소 | 원격 브랜치 목록 2개로 복귀 |
| Phase 2: Project Manager / State Machine | v0.2.0 | `state_machine.py` + `project_manager.py` 신설, `ProjectManifest.state_history` 추가, CLI `new-project / resume / transition` 정식 구현, 전이 검증 | py_compile 통과, smoke test 10케이스 (정상/중복/불법/archived) 모두 의도대로 |
| LLM Bridge 패턴 정립 (문서 PATCH) | v0.2.1 | `ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설, `docs/03 §4.5` 에 `BaseLLMWorker` 계약 추가, `CLAUDE.md C6` 에 `LLM-AP-N` 카테고리 추가, `LLM_ANTIPATTERNS.md` 골격. **시스템은 LLM API 키를 사용하지 않으며 사용자 구독의 `claude` / `codex` CLI 를 subprocess 로 호출한다 (G4 와 동등한 강제력)**. | 문서 only, 코드 변경 없음 |
| BaseLLMWorker 코드 도입 + LLM-AP-001 | v0.2.2 | `workers/base_llm_worker.py` 신설 (CLI_INVOCATION 매핑, `OSINT_LLM_STUB` 환경변수, 3-파일 영속화), `schemas/models.py` 에 `LLMCallRecord` 추가, `dummy_llm_worker.py` 로 4 케이스 smoke test. 실 `claude` CLI 호출 시 응답 wrapper 발견 → **LLM-AP-001** 등록. | py_compile 통과, 4 케이스 모두 의도대로 |
| LLM-AP-001 구조적 조치 | v0.2.3 | `_unwrap_response` / `_unwrap_claude_response` / `_extract_json_block` 도입. `run()` 의 검증 직전 backend 별 unwrap. `raw.txt` 는 원본 보존. `tests/test_base_llm_worker.py` 13 케이스. | 13/13 단위 테스트 |
| LLM-AP-002 (codex JSONL) | v0.2.4 | `codex exec --json` 이 단일 wrapper 아닌 JSONL stream 발견 (`thread.started` / `turn.started` / `item.completed` / `turn.completed`). `_unwrap_codex_response` 실 구현 (마지막 `agent_message.text` 채택). `CLI_INVOCATION` codex 매핑에 `--skip-git-repo-check` / `--color never` 추가. 단위 테스트 13 → 20. | 20/20 통과, codex-cli 0.130.0 실 캡쳐 fixture 보존 |
| 외부 코드 리뷰 1차 반영 + LLM-AP-003 | v0.2.5 | codex `exec review` 결과 (Critical 0 / High 6 / Medium 3) 일괄 흡수. `LLMSubprocessError.stdout/stderr/exit_code` 첨부, `parse_failed` vs `validation_failed` 분리, `try/finally` 로 record 영속화 보장, `_validate_output_path` 컨테인먼트, `allow_agent_mode` opt-in 가드 (LLM-AP-003), claude wrapper subtype 엄격화, `exit_code: Optional[int]`. `tests/test_base_llm_worker_run.py` 8 케이스. 단위 테스트 20 → 30. | 30/30 통과 |
| codex review 절차 정형화 | v0.2.6 | `CLAUDE.md` 에 **C10. 외부 코드 리뷰 의무화** 추가. `docs/REVIEW_PROMPT.md` 신설 (표준 프롬프트 + Windows/Linux 호출 명령어 + 결과 처리 가이드). MINOR/MAJOR/Phase 완료 직전 codex review 필수화. | 문서 only |
| 평행 브랜치 흡수 (Ij1TX) | v0.2.7 | 동일 출발점의 다른 세션 브랜치 `claude/start-after-handoff-Ij1TX` 의 차별점 3 가지 흡수: (1) **SCHEMA-AP 카탈로그** + SCHEMA-AP-001 (임의 상태 점프 / self-loop), (2) **TUI 라이브 manifest reload** (`_tick_loop` 가 매 tick 마다 `load_manifest` → 외부 transition 즉시 반영, 실패 모드 3 분류: unknown/invalid/정상), (3) **`_write_manifest` atomic write** (tmp→`Path.replace`, half-written race 차단). | py_compile + 5 케이스 smoke (atomic / corrupt JSON ValidationError / non-JSON JSONDecodeError 포함) 통과 |
| codex 2차 리뷰 H2 반영 | v0.2.8 | v0.2.7 atomic write 의 내구성(`durability`) 보강: `flush()` + `os.fsync()` (파일 fd) + 부모 디렉토리 fsync (POSIX, Windows best-effort skip). 예외 발생 시 leftover tmp best-effort cleanup. docstring 을 visibility vs durability 로 분리 명시. H1 (Ij1TX 원본 커밋 부재) 은 절차 이슈로 별도 처리 — Codex Cloud 가 비교 브랜치를 fetch 하도록 안내. | py_compile + 5 케이스 smoke (정상 / replace 실패 시 tmp cleanup / corrupt JSON / non-JSON 포함) 통과, 30/30 회귀 통과 |
| codex 3차 리뷰 흡수 (H+M+L) | v0.2.9 | dir fsync `OSError` swallow → `logging.warning` (platform·errno 포함) 으로 신호화. `_print_manifest_summary` 타입 힌트 보강 (`# type: ignore` 제거). `_SLUG_RE` 주석을 실제 정규식 (하이픈·언더스코어 허용) 과 정합화. 본 저장소 첫 표준 `logging.getLogger(__name__)` 도입. | py_compile + 5 smoke (dir fsync 실패 warning 로그 검증 포함) + 30/30 단위 테스트 회귀 통과 |
| Phase 3: Dynamic Intake Page + IntakePlannerWorker | v0.3.0 | **첫 도메인 LLM Worker** (`workers/intake_planner_worker.py`, BaseLLMWorker 상속, `response_model=IntakePlan`, claude 기본/codex 전환 가능, `CATEGORY_GUIDANCE` 5 카테고리), **FastAPI 인테이크 페이지** (`web/intake_page_app.py`: `GET /intake/{pid}` 렌더 + `POST /intake/{pid}/submit` 가 `UserDecision[]` → `SourceIntake` 영속화 + `source_collecting` 전이, `html.escape` XSS 방지), **CLI 확장** (`plan-intake <pid> [--backend ...]` + `submit-intake <pid> --file ...`). 단위 테스트 30 → 49 (IntakePlanner 13 + 인테이크 flow 6 + 회귀 30). fastapi/uvicorn/python-multipart 의존성 추가. | py_compile + 49/49 통과. DoD 8 항목 중 7 항목 충족, 마지막 1 항목 (C10.1 codex review) 은 사용자 머신에서 실행 필요 (본 컨테이너 codex CLI 미설치). |
| **Codex 4차 리뷰 흡수 (C/H/M/L/Nit 11항목)** | **v0.3.1** | **web 보안** — `validate_project_id` 공개 가드 분리 (`{project_id}` path traversal 차단), 404 detail 의 절대경로 누출 차단 (logger.warning 으로만), form body 한도 `MAX_FORM_BYTES=256KiB` + 413. **state 견고성** — `plan-intake` idempotency (`--force` + 유효 plan 발견 시 worker skip), `submit-intake` 가 tmp write → transition → atomic rename (CLI), web 은 state precondition → transition → write 순으로 재배열. **추적성** — `plan-intake` 가 `worker.write_result()` 호출로 task_result.json 영속화 (C4 stopgap). **테스트** — IntakePlanner 의 `parse_failed`/`subprocess_error` 분기 + web 의 traversal/대문자 PID/404 generic/413/M1 race/M2/H3 idempotent skip 회귀 신설. 단위 테스트 49 → **60**. | py_compile + 60/60 통과. C10.3 self-exemption 적용 (외부 리뷰 결과 흡수 PATCH 는 추가 review 면제). |
| **SCHEMA-AP-001 회귀 테스트 명시** | **v0.3.2** | `tests/test_state_machine.py` 신설. 5 카테고리 × 10 메소드 — ① 정상 선형 (`LinearSequenceTransitions`, 인접 페어 + str coerce) ② 임의 점프 거부 (정·역) ③ self-loop 거부 (비-archived + archived) ④ ARCHIVED 어디서든 도달 ⑤ ARCHIVED 종착성. 메시지 contract ("잘못된 상태 전이"/"동일 상태"/"허용된 다음 상태") 도 회귀화. `SCHEMA_ANTIPATTERNS.md` 의 `regression_test: pending` → 실제 경로 + 매핑 갱신 (v0.2.7 카탈로그 등록 이래 누적 부채 청산). 코드 동작 변경 없음. | py_compile + **70/70 통과** (60 → 70). |
| **`<untrusted_source>` envelope 헬퍼 도입** | **v0.3.3** | `workers/prompt_safety.py:wrap_untrusted` 순수 함수 신설 — content / source_label 안의 envelope 태그 (case-insensitive / whitespace 변형 포함) 를 명시적 escape 마킹으로 치환. label 의 `"` → `&quot;`, newline 평탄화로 opener 속성 안전화. `tests/test_prompt_safety.py` 13 메소드 (5 카테고리: ① 정상 wrap ② close-tag injection ③ open-tag injection ④ case/whitespace 변형 ⑤ label 안전화). `LLM_ANTIPATTERNS.md` 의 LLM-AP-003 mitigation / regression / resolved 갱신. status 는 여전히 `resolved-partial` — Phase 4 의 sandbox + scratch dir 격리까지 끝나야 `resolved`. 호출하는 worker 는 아직 없음 (Phase 4 의 `source_collector_worker` 가 사용). 코드 동작 변경 없음. | py_compile + **83/83 통과** (70 → 83). |

### 핵심 산출물

- 라이브 사이트: <https://osint-generator.vercel.app/> (PAT 필요, Private 저장소)
- TUI 진입: `python -m orchestrator.main command-center --project demo` 또는 `run_pipeline.bat`
- 프로젝트 라이프사이클 CLI:
  - `python -m orchestrator.main new-project <pid> --title ... --category geopolitics`
  - `python -m orchestrator.main resume <pid>`
  - `python -m orchestrator.main transition <pid> --to intake_planning --reason "..."`
  - **`python -m orchestrator.main plan-intake <pid> [--backend claude|codex]`** (v0.3.0)
  - **`python -m orchestrator.main submit-intake <pid> --file <source_intake.json>`** (v0.3.0)
- 더미 워커 directory: `workers/dummy_worker.py`
- **첫 도메인 LLM Worker: `workers/intake_planner_worker.py`** (Phase 3)
- **인테이크 웹 페이지: `web/intake_page_app.py`** — `uvicorn web.intake_page_app:app` 또는 `python -m web.intake_page_app` (Phase 3)
- Project Manager 모듈: `orchestrator/project_manager.py` (project_manifest.json 의 유일한 쓰기자)
- State Machine 모듈: `orchestrator/state_machine.py` (`LINEAR_SEQUENCE`, `allowed_next_states`, `validate_transition`)
- **Prompt Safety 모듈: `workers/prompt_safety.py`** — `wrap_untrusted(content, source_label="")` 순수 함수. Phase 4 의 agent 모드 worker 가 외부 자료를 prompt 에 넣을 때 호출 (v0.3.3)

### 인프라 상태

- **default branch**: `main` (모든 푸시는 여기로)
- **Vercel**: `main` 푸시마다 자동 재배포. `osint-generator.vercel.app` 안정 도메인.
- **GitHub**: doroper98/osint_generator, Private. PAT 인증으로 브랜치 뷰어 접근.

### 알려진 antipattern 카탈로그

- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md` — TTS-AP-001 ~ TTS-AP-053
- `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` — PIPELINE-AP-001 ~ PIPELINE-AP-006
- `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` — SCHEMA-AP-001 (v0.2.7 신설, 임의 상태 점프 / self-loop)
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md`:
  - LLM-AP-001 (resolved v0.2.3) — claude `--output-format json` 단일 wrapper
  - LLM-AP-002 (resolved v0.2.4) — codex `exec --json` JSONL 이벤트 stream
  - LLM-AP-003 (**resolved-partial** v0.2.5) — agent 모드 prompt injection. opt-in 가드 (`allow_agent_mode`) 만 완료. 본격 sandbox (`--sandbox`, scratch dir, 외부 자료 `<untrusted_source>` 격리) 는 Phase 3+ 후속.

**문제 발생 시 반드시 이 카탈로그를 먼저 검색.** 중복 발견 시 동일 번호에 `[superseded by ...]` 마킹만, 새로 발견 시 다음 번호로 append.

---

## 2. 다음 작업 — Phase 4 (v0.4.0) source_intake → task_queue + 첫 agent 모드 Worker

Phase 3 (v0.3.0) 가 완료되어 `intake_plan.json` → `source_intake.json` 의 인테이크 흐름이
사용자 손에 들어왔다. 다음은 그 결정을 **자동 실행 가능한 task 로 변환** 하는 Phase 4.

### 2.1 Phase 4 의 범위 (v0.4.0 — MINOR)

#### 새 변환기 (`orchestrator/task_queue_builder.py` 가칭)

- `source_intake.json` 의 `UserDecision[]` 을 읽어 `task_queue.json` 의 `TaskQueueItem[]` 생성.
- `mode == "ai_delegate"` (+`"mixed"` 의 잔여분) → `source_collector_worker` 에 위임할 task.
- `mode == "direct_provide" / "link_provide" / "file_upload"` → 이미 사용자가 자료 제공 완료
  로 마킹된 task (실행 불필요, status=completed 또는 skipped 처리).
- `mode == "skip"` → 큐에 넣지 않음.
- `mode == "must_use"` → priority=`must_use` 로 승격, 자료 제공 모드 한 번 더 묻기 (UX 후속).

#### 새 Worker (`workers/source_collector_worker.py`) — 첫 agent 모드 Worker

- `BaseLLMWorker` 상속, `llm_mode="agent"`, **`allow_agent_mode = True`** (LLM-AP-003 opt-in).
- backend 는 codex 권장 (`--sandbox read-only` 또는 `workspace-write` 매핑 도입).
- `ai_delegate_task` 를 입력으로 외부 자료 (URL) 를 읽어 `source_registry.json` 후보를 생성.
- 출력 단계는 Phase 5 의 `source_registry_builder` 가 합치므로 본 Worker 는 항목별 부분 결과만.

#### LLM-AP-003 후속 (Phase 4 의 의무 선결 작업)

agent 모드 Worker 도입과 동시에 본격 sandbox 가 필요:
- `CLI_INVOCATION` 의 codex agent 엔트리에 `--sandbox read-only|workspace-write` 매핑.
- agent 모드 Worker 용 scratch dir 격리 (`projects/{pid}/scratch/{task_id}/`).
- 외부 자료를 prompt 에 넣을 때 `<untrusted_source>...</untrusted_source>` envelope 자동 wrap
  헬퍼. `BaseLLMWorker` 또는 별도 `prompt_safety.py` 모듈.

#### Command Center 통합

- TUI 가 `task_queue.json` 의 task 를 Worker Slot 에 배정 (Phase 1 의 dummy 흐름 위에 실 worker).
- v0.3.0 의 `plan-intake` 합성 task 경로를 일반 task_queue 흐름으로 단순화.

### 2.2 Phase 4 종료 조건 (DoD)

- [ ] `submit-intake` 결과로 `task_queue.json` 자동 생성.
- [ ] task 가 Worker Slot 에 배정되고 첫 `source_collector_worker` 가 정상 실행.
- [ ] agent 모드 호출에 `--sandbox` 가 실제 매핑됨. scratch dir 외부 write 차단 검증.
- [ ] `<untrusted_source>` envelope 가 적어도 1 케이스 단위 테스트로 검증.
- [ ] `python -m py_compile` + 단위 테스트 49 → 60+.
- [ ] CHANGELOG / DEVLOG / 일괄 last_synced_with 갱신.
- [ ] **C10.1 의무**: v0.4.0 직전 codex review 1 회.

### 2.3 Phase 4 의 알려진 risk

1. **agent 모드 prompt injection (LLM-AP-003)** — 외부 자료를 LLM 에 보이는 첫 단계. sandbox + envelope 둘 다 필요. 미적용 시 worker 가 사용자 머신의 다른 디렉토리에 쓰거나 다른 명령을 실행할 위험.
2. **codex `--sandbox` 매핑 신뢰성** — codex-cli 버전별 옵션 차이 가능. 실 호출 캡쳐로 검증 후 fixture 갱신.
3. **task_queue 의 의존성 관리** — `depends_on` 필드 활용. Phase 4 에선 단순 (source_collector → registry_builder) 만 다루고, 본격 DAG 는 Phase 5.

### 2.4 v0.3.x PATCH 후보 (Phase 4 전에 처리 가능)

- ✅ v0.3.1: **C10.1 codex review 결과 흡수** (사용자가 본 v0.3.0 에 대해 1 회 실행).
- ✅ v0.3.2: SCHEMA-AP-001 회귀 테스트 명시 (v0.2.9 부터 누적된 미반영 항목).
- ✅ v0.3.3: LLM-AP-003 후속의 사전 작업 (`workers/prompt_safety.py:wrap_untrusted`
  envelope 헬퍼 + 13 회귀 테스트). 실 sandbox 매핑 / scratch dir 격리는 Phase 4 와 함께.

  v0.3.x 후보 모두 처리. 다음은 Phase 4 (v0.4.0).

---

## 3. 작업 시작 전 체크리스트

다음 세션이 첫 번째로 실행할 일 (순서 중요):

1. **읽기 (필독)**: `CLAUDE.md` (특히 **C10**) → `GOAL.md` → `VERSION` (현재 `0.3.1`) → 본 `HANDOFF.md` → `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` → `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` (LLM-AP-001/002/003 정독, **003 은 Phase 4 의 핵심 위험**) → `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` (SCHEMA-AP-001) → `docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md` (v0.3.0 의 정식 구현 대상) → `docs/REVIEW_PROMPT.md` (codex review 절차) → `docs/13_IMPLEMENTATION_ROADMAP.md` → 가장 최근 `DEVLOG.md` 엔트리 (v0.2.2 ~ v0.3.1).
2. **상태 확인**:
   ```bash
   git status                                       # clean 인지
   git log --oneline -10                            # 최근 커밋
   cat VERSION                                      # 현재 버전 (0.3.3)
   git fetch origin main                            # 다른 세션이 main 에 push 했을 수 있음
   git log --oneline HEAD..origin/main              # 비어 있으면 OK, 아니면 pull/rebase 필수
   python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py
   python -m unittest discover -s tests -t .                # 83 케이스 통과 확인
   ```
3. **사용자 의도 확인**: "v0.3.x PATCH (codex review 흡수 / SCHEMA-AP 회귀 / envelope 헬퍼) 먼저?" 또는 "Phase 4 (source_intake → task_queue + agent 모드 Worker) 직행?" 한 줄 질문.
4. **작업 진행**: 항상 작은 단위 커밋, 한 커밋 = 한 의도.
5. **MINOR / MAJOR / Phase 완료 직전**: C10.1 의무 — codex review 1 회 실행, 결과 흡수 후 증분.

---

## 4. 자주 까먹는 규칙 (Reminder)

- ✅ 모든 커밋 첫 줄: `vX.Y.Z: {summary}`. **`{summary}` 는 한국어로 작성** (사용자가 `branches.html` 에서 한글로 본다. 영문으로 쓰면 `COMMIT_DESCRIPTIONS` SHA 매핑을 추가해야 한다).
- ✅ 버전 증분 시: `VERSION` 한 줄 + 30 개 마크다운 `last_synced_with` 일괄 갱신 (`sed -i`).
- ✅ `orchestrator/__version__` 은 VERSION 을 동적으로 읽으므로 별도 편집 불필요.
- ✅ Worker subprocess 는 stdout 1 줄 1 이벤트, `task_result.json` 필수 종료.
- ✅ Worker `_finalize_slot` 종료 후 slot 은 즉시 idle 환원 (PIPELINE-AP-006).
- ✅ JSON 산출물은 `schema_version` 필드 필수.
- ✅ 도메인 데이터는 Pydantic v2 BaseModel 만 사용. raw dict 금지.
- ✅ 시스템 프롬프트 포맷팅은 `.replace()` (`format()` 은 JSON `{}` 와 충돌).
- ✅ 새 브랜치 만들면 `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에 **한국어** 설명 한 줄 추가.
- ✅ **LLM API 키 / `anthropic` / `openai` SDK 절대 금지** (ADDENDUM_04). LLM 호출은 `BaseLLMWorker` 가 `claude` / `codex` CLI 를 subprocess 로 호출하는 방식만 허용. 위반 시 PR 차단.
- ✅ **agent 모드 worker** 는 `allow_agent_mode = True` 명시 opt-in (LLM-AP-003). 기본은 `False`. 외부 자료 prompt 는 향후 `<untrusted_source>` envelope 으로 격리 예정.
- ✅ **MINOR/MAJOR/Phase 완료 직전**: `docs/REVIEW_PROMPT.md` 절차로 codex review 1 회 실행. Critical/High 흡수 후에만 버전 증분 (CLAUDE.md C10).
- ✅ **`parsed_status` 4 상태 의미**: `ok` / `parse_failed` (JSON 깨짐) / `validation_failed` (schema 위반) / `subprocess_error` (CLI 자체 실패). 새 상태 추가하지 말고 기존 4 개로 흡수.
- ✅ **`LLMCallRecord.exit_code` 는 `Optional[int]`**. None = "미실행 (FileNotFoundError) 또는 timeout".
- ✅ **`output_path` 는 project_dir 안 + task.output_refs 와 일치**해야 함 (`_validate_output_path` 가드).

---

## 5. 사용자 측 환경 (참고)

- OS: Windows (사용자), Linux (이 컨테이너).
- 진입 스크립트: `run_pipeline.bat` (Windows 더블클릭).
- Python: 3.11+ 가정.
- 브라우저: 사용자 측 PAT 는 `localStorage` (key: `osint_generator.github_token.v1`).

---

## 6. 본 문서의 갱신 규칙

- Phase 가 완료될 때마다 "1. 지금 어디까지 와 있나" 표 행 추가.
- Phase 가 시작될 때 "2. 다음 작업" 절 갱신 (현재 Phase 의 DoD 로 교체).
- 본 문서 자체도 `last_synced_with` 헤더 갱신 대상에 포함.
- append-only 가 아니라 **현재 상태 미러**. 과거 정보는 `DEVLOG.md` / `CHANGELOG.md` 로 흘려보낸다.

---

마지막 갱신: v0.3.3, 2026-05-22.
