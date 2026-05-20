<!--
tier: 3
last_synced_with: v0.2.6
ssot_for: [development-log]
depends_on: [CHANGELOG.md]
last_review: 2026-05-19
-->

# DEVLOG

본 문서는 개발 과정의 의사결정·시행착오·구조적 학습을 시간 순서로 누적합니다.
**append-only**입니다. 과거 항목 수정 금지.

각 엔트리 포맷:

```
## YYYY-MM-DD vX.Y.Z — {짧은 제목}

- 무엇을: …
- 왜:    …
- 어떻게: …
- 결과:  …
- 연관:  AP-번호, 이슈, PR 번호 등
```

---

## 2026-05-19 v0.1.0 — Phase 0 + Phase 1 착수

- **무엇을**: 빈 저장소를 받아 v2 확정서의 Phase 0(초기화)과 Phase 1(Command Center MVP)을 한 번에 셋업.
- **왜**: 영상 한 편을 빨리 만드는 것이 아니라 **재현 가능한 시스템**을 만드는 프로젝트이므로, 초기에 거버넌스·스키마·Antipattern 카탈로그 골격이 반드시 함께 있어야 후속 Phase에서 무너지지 않는다.
- **어떻게**:
  - `doroper98/agents_reviewer`의 3-Tier 거버넌스 컨벤션을 채택.
  - Tier 1 4종 + Tier 3 3종 + Tier 2 19종 동시 생성.
  - Pydantic v2를 도메인 데이터 SSOT로 고정 (`schemas/models.py`).
  - Textual + Rich로 단일 TUI Command Center를 구성, Worker는 `asyncio.create_subprocess_exec`로 띄우고 stdout을 Log Router가 각 Slot 패널로 라우팅.
  - 사용자가 직접 제공한 TTS 안티패턴 50+ 항목을 `TTS-AP-N` 포맷으로 초회 기록.
- **결과**:
  - `run_pipeline.bat`로 Command Center 진입, 4개 dummy worker가 subprocess로 동시 실행되고 각 Slot 패널에 로그가 흐르는 것을 확인.
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - Phase 1 smoke test 중 PIPELINE-AP-006 발견 즉시 수정: worker slot finalize 시 terminal 상태를 잔존시키면 `depends_on` 후속 task 가 영원히 queued 로 남는 문제. fix → `_finalize_slot`에서 즉시 idle 환원. 카탈로그 append.
- **연관**: PIPELINE-AP-006

## 2026-05-19 v0.1.1 — 호스팅 / 인증 / default branch 통합

- **무엇을**: branches.html 의 즐겨찾기 URL 을 위해 Vercel 호스팅 경로 확정, GitHub PAT 입력 UI 추가, default branch 가 `main` 으로 통합된 것을 로컬에도 반영.
- **왜**: 저장소가 **Private** 이라 GitHub Pages 무료 플랜이 막혀 있고, `htmlpreview.github.io` 도 raw 접근이 안 됨 → Vercel 만이 무료로 Private 저장소 정적 호스팅을 지원. 그리고 같은 이유로 페이지 안에서 GitHub API 를 호출하려면 사용자 토큰이 필요함.
- **어떻게**:
  - `vercel.json` 추가: `outputDirectory: docs`, `/` → `/branches.html` rewrite, cleanUrls.
  - `branches.html`: token 입력 다이얼로그 + `localStorage` 저장 + `Authorization: Bearer` 헤더 부착. raw.githubusercontent.com 대신 contents API 사용.
  - GitHub UI 가 `claude/osint-video-system-IaGd0 → main` rename 안내 → 로컬도 `git branch -m`, `git fetch`, `git branch -u`, `git remote set-head` 으로 정리.
  - VERSION 0.1.0 → 0.1.1, 30개 마크다운/HTML 의 `last_synced_with` 일괄 갱신.
- **결과**:
  - vercel.json 1개 커밋만으로 Vercel 가져오기 후 즉시 배포 가능.
  - branches.html 이 Private 저장소에서도 정상 동작.
- **연관**: 없음 (호스팅·운영 영역 PATCH)

## 2026-05-19 v0.1.2 — Vercel 루트 404 수정

- **무엇을**: Vercel 첫 배포 후 루트 URL (`/`) 이 `404: NOT_FOUND` 를 띄우던 문제 수정. `docs/index.html` 정적 파일 추가, `vercel.json` 의 `rewrites` 룰 제거.
- **왜**: `outputDirectory: "docs"` + `rewrites: [{ source: "/", destination: "/branches.html" }]` 조합이 Vercel 의 정적 호스팅 모드에서 안정적으로 매칭되지 않음. 실측 시 deployment URL 루트가 404. `/branches.html` 직접 접근은 정상.
- **어떻게**:
  - `docs/index.html` 신설: meta-refresh + `window.location.replace('/branches.html')` 양쪽으로 즉시 리다이렉트.
  - `vercel.json` 의 `rewrites` 블록 삭제. cleanUrls / 캐시 헤더는 유지.
  - VERSION 0.1.1 → 0.1.2, 30 개 마크다운 `last_synced_with` 일괄 갱신.
- **결과**:
  - 푸시 후 Vercel 자동 재배포 → 루트 URL 이 `branches.html` 로 정상 진입.
  - 안정 도메인 (`osint-generator.vercel.app`) 도 동일하게 동작.
- **연관**: 없음 (호스팅 hotfix)

## 2026-05-19 v0.1.3 — branches.html 진짜 git graph 화 + 세션 인계 문서

- **무엇을**: `docs/branches.html` 의 flat list 렌더링을 `@gitgraph/js` 기반 SVG 그래프로 교체. `HANDOFF.md` (Tier 1) 신설.
- **왜**:
  - 사용자가 GitExtensions/Sourcetree 스타일의 "진짜 가지" 시각화를 원함. 현재는 모든 브랜치가 같은 SHA 를 가리켜서 가지 효과가 안 보이지만, Phase 2 부터 브랜치가 갈라지면 즉시 예쁜 그래프가 나오도록 프레임워크를 미리 깔아둠.
  - 세션이 멈췄을 때 다음 AI 가 빠르게 컨텍스트를 잡기 위한 인계 문서가 필요했음. `CLAUDE.md` 는 규칙, `GOAL.md` 는 목표, `DEVLOG.md` 는 과거 — "지금 어디까지 와 있고 다음에 뭘 하면 되는지" 를 한 페이지에 압축한 문서가 부재.
- **어떻게**:
  - `branches.html`: `@gitgraph/js` CDN 추가, `buildCommitGraph()` 가 모든 브랜치 commit 을 `Promise.all` 로 병렬 fetch → SHA 로 dedup → `commit.parents` 필드 보존 → 시간순 정렬 → `gitgraph.import(commits)` 호출. 다크 테마 / 폰트 커스텀 (Metro template extend).
  - 사이드 패널: 등록되지 않은 브랜치는 한글 경고 카드로 자동 노출. PR 배지 통합.
  - `HANDOFF.md` (Tier 1) 신설: 다음 세션의 0–6 절. 작업 시작 체크리스트, Phase 2 DoD, 자주 까먹는 규칙 reminder.
  - VERSION 0.1.2 → 0.1.3, 31 개 마크다운 (HANDOFF.md 포함) `last_synced_with` 일괄 갱신.
- **결과**:
  - 사용자 시각 확인 시 v0.1.3 헤더 + 단일 라인 그래프 (브랜치 두 개가 동일 SHA 라서 line 1 개가 정상) + 사이드 패널의 main 카드 노출.
  - Phase 2 시작 후 첫 분기점부터 자동으로 갈라지는 그래프가 그려질 것 (검증 예정).
- **연관**: 없음 (UX 개선 + 문서 추가)

## 2026-05-19 v0.1.4 — 분기 그래프 검증 + 한글 commit 라벨 + main 라벨 우선순위

- **무엇을**:
  1. `test/graph-demo` 임시 브랜치를 `d0c8771` 에서 분기시켜 그래프 분기 시각화를 사용자 측에서 검증.
  2. 영어로 작성된 과거 커밋의 첫 줄을 한글로 보여주는 `COMMIT_DESCRIPTIONS` SHA 맵을 `branches.html` 에 추가.
  3. 같은 SHA 에 여러 브랜치가 있을 때 라벨 우선순위 (`BRANCH_PRIORITY`) 도입. `main` 이 항상 먼저.
- **왜**:
  - **검증**: gitgraph.js 통합 후 실제 분기가 나타나는지 사용자 측에서 시각 확인이 필요했음. → 사용자 스크린샷에서 `d0c8771` → 두 갈래로 정확히 분기되는 그림 확인.
  - **한글 라벨**: 사용자가 버전 중심으로 소통하기로 했지만 commit 첫 줄은 영어로 작성되어 있어 페이지에서 가독성 떨어짐. 과거 commit 을 rebase 로 고치는 것은 destructive 이므로 디스플레이 레벨에서 override.
  - **main 우선**: `c359bd8` 처럼 두 브랜치가 동일 SHA 를 가리킬 때 `claude/resume-session-YLOYE` 가 알파벳 순으로 먼저 와서 main 라벨이 가려지는 시각 버그.
- **어떻게**:
  - `git checkout -b test/graph-demo d0c8771` → `docs/_GRAPH_DEMO.md` 추가 → `v0.1.2: graph divergence demo` commit → `git push -u origin test/graph-demo` → `git checkout main`.
  - `branches.html` 의 `<script>` 상단에 `COMMIT_DESCRIPTIONS` (SHA prefix 7자 → 한글 텍스트) 와 `BRANCH_PRIORITY` (정규식 배열) + `branchPriority()` + `sortBranchRefs()` 추가.
  - `renderGraph()` 의 `commits.map` 에서 한글 override + ref 정렬 적용. `onClick` 핸들러도 `sortBranchRefs` 사용.
  - VERSION 0.1.3 → 0.1.4, 31 개 마크다운 `last_synced_with` 일괄 갱신.
- **결과**:
  - 사용자 스크린샷 확인: `bb530d2 → 083a764 → d0c8771` 까지 단일 라인, `d0c8771` 에서 보라색 곡선이 분기되어 `c359bd8 (main)` 과 `0159299 (test/graph-demo)` 로 갈라짐. ✓
  - 한글 override / main 라벨 우선순위는 사용자 다음 새로고침에서 검증 예정.
- **연관**: 없음 (검증 + UX 개선)

## 2026-05-19 v0.1.5 — test/graph-demo 정리

- **무엇을**: 검증용 임시 브랜치 `test/graph-demo` 삭제, 관련 dead code 제거.
- **왜**: v0.1.3 그래프 분기 시각화 검증이 v0.1.4 사용자 스크린샷으로 완료됨. 임시 브랜치 / 더미 commit / 더미 파일을 더 이상 유지할 이유가 없음. 카탈로그를 깨끗이 유지하는 것이 다음 세션의 인지 부담을 줄임.
- **어떻게**:
  - 컨테이너 측 `git push origin --delete test/graph-demo` 가 HTTP 403 (Claude Code 인프라가 main / claude/* 외의 브랜치 삭제 차단) → 사용자가 GitHub 웹 UI 에서 직접 삭제.
  - `git fetch --prune origin` 으로 로컬 원격 추적 ref 정리.
  - `branches.html`: `BRANCH_DESCRIPTIONS["test/graph-demo"]` 제거, `COMMIT_DESCRIPTIONS["0159299"]` 제거.
  - VERSION 0.1.4 → 0.1.5, 31 개 마크다운 `last_synced_with` 일괄 갱신.
- **결과**:
  - 원격 브랜치 목록: `main`, `claude/resume-session-YLOYE` 두 개로 복귀.
  - `branches.html` 새로고침 시 단일 라인 그래프 (v0.1.3 시점과 동일 모양) + 현재 commit 5 개 (v0.1.0~v0.1.5).
- **연관**: 없음 (정리 PATCH)

## 2026-05-19 v0.2.0 — Phase 2: Project Manager / State Machine

- **무엇을**: 프로젝트의 라이프사이클을 관리하는 Project Manager 와 State Machine 을 정식 구현. `new-project / resume / transition` CLI 명령이 동작하고, `project_manifest.json` 이 디스크에 영속화되며, 모든 상태 전이는 검증을 거치고 `state_history` 에 append-only 로 기록된다.
- **왜**: Phase 1 까지는 더미 워커가 task_queue.json 만으로 돌아갔으나, Phase 3+ 의 Worker 들이 자기 산출물을 어디로 떨어뜨릴지·언제 다음 단계로 전진할지 결정하려면 "프로젝트가 지금 어떤 상태인가" 가 단일 출처로 박혀 있어야 한다. 임의 점프를 막아야 `created → render_final` 같은 사고를 차단할 수 있다.
- **어떻게**:
  - `schemas/models.py` 에 `StateTransition` 모델과 `ProjectManifest.state_history` (default `[]`) 추가. schema_version 은 1 유지 — 신규 optional 필드는 호환 방향 (C3).
  - `orchestrator/state_machine.py` 신설: docs/02 §4 의 24개 상태를 `LINEAR_SEQUENCE` 에 박고, `allowed_next_states` 가 (다음 선형 상태 + `archived`) 집합을 반환. `archived` 는 어디서든 종료 허용하지만 archived 에서 추가 전이 불가. `validate_transition` 이 실패 시 한글 메시지로 ValueError. Pydantic `use_enum_values=True` 때문에 manifest 로드 시 enum 이 str 로 들어오는 점을 `_coerce` 헬퍼로 흡수.
  - `orchestrator/project_manager.py` 신설: `MANIFEST_FILENAME` 상수, `_SLUG_RE` 로 project_id 검증, `new_project / resume_project / transition_state` 공개 API. 모든 디스크 쓰기는 `_write_manifest` 한 군데로 단일화 — `updated_at` 자동 갱신.
  - `orchestrator/main.py` 의 `new-project` placeholder 를 실 구현으로 교체. `resume`, `transition` 서브커맨드 신설. category / state 는 enum choices 로 argparse 가 자동 검증.
  - `orchestrator/command_center.py` 가 raw json 파싱 대신 `project_manager.load_manifest` 를 호출하도록 정리. manifest 가 손상되면 created 로 fallback (TUI 진입 자체는 막지 않음).
  - 스모크 테스트 (demo2): 정상 new-project, 중복 new-project (FileExistsError), 잘못된 project_id (ValueError), resume 정상, resume 미존재 (FileNotFoundError, 디렉토리도 안 만듦), 정상 전이 2회, 불법 점프 (created→render_debug 거부), 동일 상태 전이 거부, archived 종료, archived 에서 추가 전이 거부 — 모두 의도대로 동작. state_history 3개 엔트리 직렬화 확인.
  - 작업 중 `resume_project` 가 `_ensure_project_layout` 을 먼저 호출해서 미존재 프로젝트에도 빈 폴더가 생기는 버그 발견 → manifest 검증을 먼저 수행하도록 순서 교체.
  - VERSION 0.1.5 → 0.2.0 (MINOR · Phase 완료), 31 개 마크다운/HTML `last_synced_with` 일괄 갱신.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - HANDOFF DoD 6 항목 모두 충족: new-project 시 manifest 가 `state: "created"` 로 생성, resume 으로 마지막 상태에서 이어짐, 불법 전이는 ValueError + 한글 메시지, py_compile 통과, last_synced_with 갱신, CHANGELOG/DEVLOG 엔트리 추가.
  - Phase 3 (Dynamic Intake Page) 가 `intake_planning → intake_pending_user → source_collecting` 흐름을 그대로 호출하면 됨.
- **연관**: 없음 (새 Antipattern 없음. 잘못된 전이 시도는 schema_machine 이 ValueError 로 차단함 — 카탈로그에 등록할 만한 미발견 결함이 아니라 사전 차단된 케이스이므로 SCHEMA-AP 등록 보류)

## 2026-05-19 v0.2.1 — Subscription LLM Bridge 패턴 정립 (문서 PATCH)

- **무엇을**: 본 시스템이 LLM API 키 (`ANTHROPIC_API_KEY` 등) 와 공식 SDK (`anthropic`, `openai` 등) 를 사용하지 않고, 사용자가 이미 구독 중인 `claude` / `codex` CLI 를 subprocess 로 자동 호출한다는 핵심 아키텍처 결정을 정식 문서화. 코드 변경 없음.
- **왜**:
  - 사용자가 강하게 어필하고 싶다고 명시. 비용 예측성 / rate-limit 여유 / 최신 모델 우선 반영 / 결제 중인 자원 활용도 극대화 / API 키 관리 부담 제거.
  - "Agent 가 LLM API 직접 호출" 전제로 docs/03 이 작성되어 있었던 것을 정정해야 Phase 3 이후 코드가 잘못된 방향으로 가지 않음.
  - 한 번 의사결정 + 본 세션 안에서 짧은 시행착오: 처음에 "프롬프트 출력 → 사용자 복붙" 패턴으로 해석했으나 사용자가 즉시 정정 — "에이전트가 CLI 에서 JSON 응답을 만들어 낼 수 있다, 왜 복붙해야 하나" — 정확한 의도는 **구독 인증된 CLI subprocess** 였음. 이 정정을 DEVLOG 에도 남겨 둠.
- **어떻게**:
  - `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설 (9개 절): 위상·핵심원칙(Hard NO/YES)·rationale·BaseLLMWorker 설계 (`llm_backend`, `llm_mode`)·CLI 인터페이스 가정·추적성 (`llm_calls/{call_id}.json`)·에러 모드·향후 확장·관련 안티패턴.
  - `docs/03_AGENT_ARCHITECTURE.md` 의 §4 베이스워커 안내문에 "LLM 호출 Worker 는 BaseLLMWorker 상속 필수" 박스 추가, §4.5 신설 (BaseLLMWorker 계약 요약 + 호출 모드 표 + 백엔드 선택 가이드).
  - `CLAUDE.md` C6 안티패턴 카테고리 목록에 `LLM-AP-N` 추가.
  - `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 골격 신설, `docs/ANTIPATTERNS/README.md` 인덱스 행 추가.
  - 거버넌스 결정: GOAL.md G4 본문은 건드리지 않음. C5.4 에 따르면 G4 변경은 MAJOR 사유인데 본 변경은 PATCH 로 흡수하기 위함. ADDENDUM_04 자체에 "G4 와 동등한 강제력으로 운용" 을 명시해 어필 강도는 유지하고, v1.0.0 시점에 G4 #13 으로 정식 흡수 예정.
  - VERSION 0.2.0 → 0.2.1, 31 개 마크다운/HTML `last_synced_with` 일괄 갱신.
- **결과**:
  - 코드 변경 없음 → py_compile 영향 없음.
  - Phase 3 시작 시 `BaseLLMWorker` 구현 + IntakePlannerWorker 가 본 패턴을 그대로 채택. ADDENDUM_04 §4 의 시그니처를 코드로 옮기면 됨.
  - 다음 세션은 v0.2.2 (BaseLLMWorker 코드 도입) 또는 v0.3.0 (Phase 3 + BaseLLMWorker 동시) 중 사용자가 선택.
- **연관**: 없음 (안티패턴 카테고리 신설 1건. LLM-AP 항목은 Phase 3 첫 실 호출부터 누적 예정.)

## 2026-05-20 v0.2.2 — BaseLLMWorker 코드 도입 + LLM-AP-001 발견

- **무엇을**: ADDENDUM_04 §4 의 BaseLLMWorker 인터페이스 명세를 코드로 옮김. `workers/base_llm_worker.py` 신설, `schemas/models.py` 에 `LLMCallRecord` 추가, `workers/dummy_llm_worker.py` 로 4 케이스 smoke test. 실 `claude` CLI 호출 케이스에서 응답 wrapper 발견 → LLM-AP-001 등록 (구조적 조치는 v0.2.3 patch).
- **왜**:
  - v0.2.1 에서 패턴은 문서화했지만 코드가 없으면 Phase 3 의 IntakePlannerWorker 가 base 클래스를 직접 짜야 함. 작은 단위 (C8.2) 원칙에 따라 인프라 먼저 박고 Phase 3 진입.
  - 사용자가 "옵션 A (v0.2.2 — BaseLLMWorker 코드 도입)" 명시적으로 선택.
- **어떻게**:
  - `LLMCallRecord` Pydantic 모델: `call_id`, `task_id`, `worker`, `backend`, `mode`, `system_prompt_hash`, `user_prompt_path`, `raw_response_path`, `parsed_status`, `started_at/completed_at`, `exit_code`, `retry_index`, `error_message`. schema_version 1 유지 (신규 optional 모델 추가는 호환).
  - `BaseLLMWorker(BaseWorker)`: 클래스 변수 (`llm_backend`, `llm_mode`, `system_prompt`, `response_model`, `invoke_timeout_sec=600`), 추상 (`build_user_prompt`, `output_path`), `run` 오버라이드로 전체 흐름 흡수. `_invoke_llm` 가 `CLI_INVOCATION` 매핑 (`(backend, mode) → list[str]`) 으로 subprocess 호출하고 `FileNotFoundError` / `TimeoutExpired` / 비0 종료 모두 `LLMSubprocessError` 로 변환. `OSINT_LLM_STUB=1` + `OSINT_LLM_STUB_RESPONSE` 환경변수로 실 CLI 우회.
  - 모든 호출은 3 파일로 영속화: `{call_id}.prompt.txt` (system+user 합쳐서 sha256 해시 함께), `{call_id}.raw.txt` (subprocess stdout 그대로), `{call_id}.json` (LLMCallRecord). `TaskResult.outputs` 에 LLMCallRecord 경로 포함 → task ↔ LLM 호출 양방향 추적.
  - `DummyLLMWorker` + `DummyLLMResponse` 로 demo3 프로젝트에 task_queue 만들고 4 케이스 smoke test: (1) 정상 stub → completed/parsed_status=ok, (2) `"not a json"` → failed/validation_failed, (3) `{"unknown_field":42}` → failed/validation_failed (extra_forbidden), (4) `OSINT_LLM_STUB` 없이 실 `/opt/node22/bin/claude` 호출 → JSON 응답은 받았으나 wrapper 때문에 validation_failed.
  - 4번째 케이스에서 wrapper 구조 확인: `{"type":"result","subtype":"success","result":"<actual_text>","session_id":...,"duration_ms":...,"usage":{...},"uuid":"..."}` — 도메인 응답은 `result` 필드의 string. 이 발견을 LLM-AP-001 로 정식 등록. 구조적 조치는 v0.2.3 patch 에서 `BaseLLMWorker._invoke_llm` 내부에 backend 별 wrapper unwrap 단계 추가 예정.
  - VERSION 0.2.1 → 0.2.2 (MINOR — C5.4 "새 Worker 추가" 트리거). 31 개 마크다운 `last_synced_with` 일괄 갱신.
  - ADDENDUM_04 §4 인트로를 "v0.2.2 코드 도입 완료" 로 갱신, §8 #1 미결 항목을 LLM-AP-001 로 구체화.
- **결과**:
  - py_compile 통과. Pydantic 검증 + 추적성 파일 영속화 모두 의도대로 동작.
  - Phase 3 의 `IntakePlannerWorker` 는 `BaseLLMWorker` 를 그대로 상속하면 됨 — `system_prompt`, `response_model=IntakePlan`, `build_user_prompt(args, task)`, `output_path` 만 구현.
  - 다음 patch (v0.2.3) 는 LLM-AP-001 fix: wrapper unwrap 로직 + 회귀 테스트 fixture.
- **연관**: LLM-AP-001 (active, v0.2.3 대기)

---

## 2026-05-20 v0.2.3 — LLM-AP-001 구조적 조치 (wrapper unwrap)

- **무엇을**: v0.2.2 에서 발견한 LLM-AP-001 (claude CLI 응답 wrapper 로 인한 Pydantic `extra_forbidden` reject) 을 구조적으로 해결. `BaseLLMWorker` 가 backend 별 wrapper 를 벗긴 뒤 검증하도록 변경. 회귀 테스트 `tests/test_base_llm_worker.py` 신설.
- **왜**:
  - 실 `claude` CLI 호출이 stub 없이 정상 동작하려면 wrapper unwrap 이 필수. Phase 3 의 IntakePlannerWorker 가 stub 없이 돌아가야 의미가 있음.
  - 회귀 테스트가 없으면 같은 종류의 버그 (코덱스, 향후 CLI 갱신) 가 재발해도 알아채지 못함. C6.4 "구조적 조치" 요구.
- **어떻게**:
  - `workers/base_llm_worker.py` 에 모듈 레벨 헬퍼 3 종: `_unwrap_claude_response` (wrapper `{type:result, subtype:success}` 에서 `result` 필드 추출, `is_error=True` 면 `LLMSubprocessError`), `_unwrap_codex_response` (v0.2.3 시점 미검증 → pass-through), `_extract_json_block` (markdown code fence 제거).
  - `BaseLLMWorker._unwrap_response(raw)` 가 `self.llm_backend` 로 dispatch. `run()` 의 `model_validate_json` 직전에 호출. `LLMSubprocessError` 도 잡아서 `parsed_status="subprocess_error"` 로 기록.
  - `raw.txt` 는 unwrap 전 원본 그대로 보존 → 디버깅 추적성 유지.
  - `tests/__init__.py` + `tests/test_base_llm_worker.py` 신설. 13 케이스: extract_json_block 5 + claude unwrap 7 + codex pass-through 1. 모두 `python -m unittest tests.test_base_llm_worker` 로 통과.
  - LLM_ANTIPATTERNS.md 의 LLM-AP-001 status `active` → `resolved`, regression_test pending → 실제 파일 경로로 갱신. 본문 (증상/원인) 은 수정하지 않음 (C6 append-only 준수, 상태 라이프사이클만 진행).
  - VERSION 0.2.2 → 0.2.3 (PATCH — C5.4 "버그 수정" 트리거).
- **결과**:
  - py_compile 통과, import smoke 통과, 13 단위 테스트 통과.
  - 다음 단계: Phase 3 IntakePlannerWorker 착수 가능. 실 `claude` CLI 호출 시에도 도메인 JSON 검증이 정상 동작할 것으로 기대 (실 호출 검증은 Phase 3 smoke test 에서).
  - codex CLI wrapper 검증은 별도 작업 (LLM-AP-002 후보) 으로 분리.
- **연관**: LLM-AP-001 (resolved), ADDENDUM_04 §5

---

## 2026-05-20 v0.2.4 — codex JSONL stream 처리 + LLM-AP-002 발견 즉시 해결

- **무엇을**: v0.2.3 시점에 미검증 pass-through 였던 codex CLI 의 wrapper 를 사용자 머신 (codex-cli 0.130.0, Windows cmd) 한 줄 호출 캡쳐로 검증. 단일 JSON wrapper 가 아니라 JSONL 이벤트 스트림 패턴이라는 사실을 발견 → LLM-AP-002 등록 + 즉시 fix.
- **왜**:
  - v0.2.3 시점의 codex pass-through 는 "실 호출 시 검증 실패" 라는 알려진 risk 였음. Phase 3 진입 전에 해소되어야 IntakePlannerWorker 가 codex backend 도 안전히 쓸 수 있음.
  - 사용자가 codex CLI 보유 확인 → 즉석 검증 가능해짐.
- **어떻게**:
  - 검증 절차: `codex exec --json --skip-git-repo-check "<프롬프트>"` 를 사용자 머신에서 던져 stdout 캡쳐. 4 줄 JSONL: `thread.started` / `turn.started` / `item.completed`(agent_message) / `turn.completed`. 도메인 응답은 `item.completed` 의 `item.type=="agent_message"` 의 `text` 필드.
  - `_unwrap_codex_response` 실 구현: 모든 줄을 순회하며 codex 이벤트 (`thread.*`, `turn.*`, `item.completed`) 가 한 번이라도 보이면 codex stream 으로 인정. 마지막 agent_message 의 text 를 채택. markdown code fence 가 끼면 `_extract_json_block` 으로 한 번 더 벗김. codex stream 인데 agent_message 가 하나도 없으면 `LLMSubprocessError`. codex stream 패턴이 전혀 안 보이면 pass-through (단일 JSON / stub mode 보호).
  - 의도적 호환성: tool_call / reasoning 등 미지 item type 은 무시. codex 가 새 이벤트 타입을 추가해도 깨지지 않음. 그 대신 fixture 기반 회귀 테스트가 포맷 변경을 빠르게 감지.
  - `CLI_INVOCATION` codex 매핑 보강: `--skip-git-repo-check` (project_dir 이 git repo 아닐 수 있음), `--color never` (ANSI 코드 안전장치). agent 모드는 `--cd {project_dir}` 유지.
  - `tests/test_base_llm_worker.py::TestUnwrapCodexResponse` 8 케이스 추가 (실 캡쳐 / fence / 다중 message / unknown item / no message / 단일 JSON / non-JSONL / 빈 입력). 단위 테스트 13 → 20.
  - LLM_ANTIPATTERNS.md 에 LLM-AP-002 신규 등록 (status=resolved). LLM-AP-001 본문은 수정하지 않고 별개 항목으로 분리 (claude / codex 가 다른 패턴이라는 사실 자체가 카탈로그 가치).
  - VERSION 0.2.3 → 0.2.4 (PATCH — C5.4 "버그 수정/비기능 개선").
- **결과**:
  - py_compile 통과, import smoke 통과, 20/20 단위 테스트 통과.
  - codex backend 가 실제 호출 가능 상태로 진입. Phase 3 의 IntakePlannerWorker 가 claude/codex 양쪽 모두 안전히 사용 가능.
  - Windows cmd 환경에서 subprocess 매핑이 잘 도는지는 Phase 3 첫 실 호출에서 추가 검증 (인용부호 / shell=False 동작 확인).
- **연관**: LLM-AP-002 (resolved), LLM-AP-001 (자매 항목 — claude wrapper), ADDENDUM_04 §5

---

## 2026-05-20 v0.2.5 — 외부 코드 리뷰 1차 반영 (BaseLLMWorker 견고성 강화 + LLM-AP-003)

- **무엇을**: 사용자가 codex CLI 로 v0.2.2~v0.2.4 변경에 대해 코드 리뷰를 돌린 결과 (Critical 0 / High 6 / Medium 3 / Low+Nit 모두 OK) 의 High/Medium 항목을 한 PATCH 로 일괄 반영. 신규 LLM-AP-003 (agent 모드 prompt injection) 등록 + opt-in 가드 도입.
- **왜**:
  - 외부 리뷰는 BaseWorker 가 Phase 3 의 첫 도메인 worker (IntakePlannerWorker) 의 베이스로 들어가기 전 마지막 견고화 기회. 추적성·상태 분류·output 컨테인먼트는 한 번 합의된 뒤 깨면 회귀 비용이 크므로 지금 정리.
  - Critical 이 없었다는 사실 자체가 핵심 로직 (wrapper unwrap, subprocess 호출, Pydantic 검증) 의 방향성이 맞다는 확인. 다만 6 개 High 모두 정당해서 방어할 항목 없음.
- **어떻게**:
  - **(H1+H2)** `LLMSubprocessError` 에 `stdout`/`stderr`/`exit_code` 첨부. `_invoke_llm` 의 비0 종료 / `TimeoutExpired` / `FileNotFoundError` 모두 부분 출력과 exit_code 를 보존하도록 변경. `run()` 의 except 가 `e.stdout` 을 `raw_text` 로 복원해 `raw.txt` 영속화에 사용.
  - **(H3)** `model_validate_json(raw)` 한 줄을 `json.loads(raw)` → `model_validate(parsed_obj)` 2 단계로 분리. `JSONDecodeError` → `parsed_status="parse_failed"`, `ValidationError` → `validation_failed`. 4 `parsed_status` 가 의미적으로 구분됨.
  - **(H4)** `run()` 의 LLM 호출 + 검증 + output 저장을 `try` 안에, LLMCallRecord 영속화를 `finally` 안에 배치. 어떤 예외 경로에서도 record/prompt/raw 3 파일이 항상 남음. output write 실패 시 `parsed_status` 는 `ok` 유지 (LLM 응답은 정상이었음) 하되 `error_message` 에 명시하고 task 는 FAILED.
  - **(H5)** `_validate_output_path(args, task, outp)` 헬퍼 추가. project_dir 밖이면 `ValueError`. `task.output_refs` 가 비어있지 않으면 outp 의 상대경로가 그중 하나와 일치해야 함 (Windows `\` 와 POSIX `/` 차이 흡수). CLAUDE.md C4 "writes only own output_refs" 의 코드 단 가드.
  - **(H6 / LLM-AP-003)** `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False` 도입. `run()` 시작 직후 `llm_mode=="agent" and not allow_agent_mode` 면 즉시 `TaskResult(FAILED)` 반환 — LLM 호출 자체가 일어나지 않으므로 `llm_calls/` 디렉토리도 생성되지 않음. agent 모드 사용 worker 는 명시적으로 `allow_agent_mode = True` 선언 필요. LLM-AP-003 본문에 옵션 (1)~(3) 단계별 보강 (외부 자료 격리, CLI sandbox 옵션) 을 향후 Phase 3+ 후속으로 기록.
  - **(M1)** `_unwrap_claude_response` 의 subtype 검증 엄격화. `type=="result"` 면 `subtype=="success"` 강제, 아니면 `LLMSubprocessError`. 이전엔 `subtype != "success"` 도 pass-through 였어서 `validation_failed` 로 흡수돼 원인 추적 어려웠음.
  - **(M2)** `LLMCallRecord.exit_code: int = 0` → `Optional[int] = None`. 이전엔 CLI 호출 실패 (FileNotFoundError) 케이스도 `exit_code=0` 으로 남아 "정상 실행 후 실패" 와 구분 안 됐음. None = "미실행 또는 timeout" sentinel.
  - **(M3)** `tests/test_base_llm_worker_run.py` 신설. monkeypatch + stub mode 로 `_invoke_llm` 을 가짜 함수로 교체하거나 `OSINT_LLM_STUB` 으로 fake stdout 주입. 4 `parsed_status` 모두 도달성 + agent gate + output 컨테인먼트 (project_dir 밖 / output_refs 불일치) 총 8 케이스.
  - 단위 테스트 총 20 → 30. 모두 통과.
  - VERSION 0.2.4 → 0.2.5 (PATCH — C5.4 "버그 수정/비기능 개선"). schema_version 은 1 유지 (`exit_code` Optional 화는 호환 변경).
- **결과**:
  - py_compile 통과, import smoke 통과, 30/30 단위 테스트 통과.
  - BaseLLMWorker 의 추적성·상태 분류·output 컨테인먼트가 외부 리뷰가 요구한 수준에 도달. Phase 3 의 IntakePlannerWorker 가 안전하게 상속 가능.
  - 다음 후보: (a) Phase 3 IntakePlannerWorker 착수, (b) agent 모드 본격 sandbox (CLI `--sandbox` 매핑 + scratch dir) — LLM-AP-003 의 후속 단계.
- **연관**: LLM-AP-003 (resolved-partial), LLM-AP-001/002 (자매 항목), 외부 codex 리뷰 결과, ADDENDUM_04 §5/§7, CLAUDE.md C2/C4.

---

## 2026-05-20 v0.2.6 — codex review 절차 정형화 + 다음 세션 인계 정리

- **무엇을**: 외부 LLM (codex) 코드 리뷰를 일회성 실험에서 정식 거버넌스 절차로 격상. `CLAUDE.md C10` 신설, `docs/REVIEW_PROMPT.md` 운영 매뉴얼 신설, `HANDOFF.md` 를 v0.2.6 기준 + Phase 3 진입 준비로 전면 갱신. 코드/스키마/테스트 변경 없음.
- **왜**:
  - v0.2.5 의 외부 리뷰가 6 개 High 를 발견 — 자기 검증의 사각지대가 분명히 존재. 일회성으로 두면 재발. **MINOR/MAJOR/Phase 완료 직전 의무화** 로 강제력 부여.
  - 사용자가 매번 "어떤 프롬프트로 시켜야 하지?" / "어떻게 호출하지?" 를 묻지 않도록 운영 매뉴얼 분리. 변경 범위만 채워 재사용 가능한 영문 프롬프트 템플릿.
  - 다음 세션이 어떤 컨텍스트에서 시작할지 분명히 — Phase 3 의 IntakePlannerWorker 가 정식 다음 항목, BaseLLMWorker 인프라는 이미 외부 리뷰까지 거친 견고한 상태.
- **어떻게**:
  - **CLAUDE.md C10 신설** — 4 절 구조: C10.1 실행 의무 시점 표 (MINOR/MAJOR 필수, Phase 완료 필수, 새 Worker 권장, 단순 fix 면제), C10.2 절차 5 단계 요약, C10.3 자기 검증 면제 (본 절차 자체와 외부 리뷰 결과 흡수 PATCH 는 무한 루프 방지로 면제), C10.4 산출물 처리 (`review-prompt.txt`/`review-out.jsonl` 커밋 금지).
  - **`docs/REVIEW_PROMPT.md` 신설** (tier 2, ssot_for=codex-review-procedure) — 6 절 구조:
    1. 언제 실행하나 (표)
    2. 표준 영문 프롬프트 (재사용 템플릿 + 작성 가이드)
    3. 실행 명령어 (Windows cmd / macOS-Linux / .git/info/exclude)
    4. 결과 해석 (Critical/High/Medium/Low/Nit 처치표 + commit 컨벤션 + false positive 처리)
    5. 절차의 한계 (codex 가 ADDENDUM/AP 카탈로그 모름)
    6. 관련 문서
    프롬프트는 영문 고정 — codex 의 reasoning 일관성 + Windows 한글 코드페이지 이슈 회피.
  - **HANDOFF.md 전면 갱신**:
    - `last_synced_with: v0.2.2 → v0.2.6`, `depends_on` 에 `docs/REVIEW_PROMPT.md` 추가.
    - "1. 지금 어디까지 와 있나" 표에 v0.2.3 / v0.2.4 / v0.2.5 / v0.2.6 4 행 추가.
    - 알려진 antipattern 카탈로그 갱신 (LLM-AP-001/002/003 상태 명시).
    - "2. 다음 작업" 절을 v0.2.3/Phase 3 양자택일 → **Phase 3 (v0.3.0) IntakePlannerWorker 단독** 으로 교체. 도메인 모델 4 종, Worker 명세, 웹 페이지, CLI 확장, DoD 7 항목, 알려진 risk 4 종, Phase 4 예고 포함. 대안 절 (LLM-AP-003 후속 보안 강화 먼저) 도 명시.
    - "3. 작업 시작 전 체크리스트" 에 codex review 단계 + 30 단위 테스트 통과 확인 (`python -m unittest tests.test_base_llm_worker tests.test_base_llm_worker_run`) 추가.
    - "자주 까먹는 규칙" 에 6 개 항목 추가 — agent 모드 opt-in, codex review 의무, parsed_status 4 상태 의미, exit_code Optional 의미, output_path 컨테인먼트.
  - VERSION 0.2.5 → 0.2.6 (PATCH — C5.4 "문서 보강"). 코드 변경 없으므로 schema_version 영향 없음.
  - C10.3 self-exemption 의해 본 PATCH 자체에는 codex review 미실시.
- **결과**:
  - 다음 세션이 HANDOFF.md 의 §3 체크리스트만 따라가면 즉시 Phase 3 진입 가능.
  - codex review 가 일회성 실험에서 정식 거버넌스 절차로 격상. 같은 종류의 사각지대 (자기 검증 한계) 재발 위험 ↓.
  - 사용자가 매 리뷰 시점마다 절차 / 명령어 / 프롬프트 / 결과 처리를 새로 생각할 필요 없음.
- **연관**: CLAUDE.md C10, docs/REVIEW_PROMPT.md, HANDOFF.md.

---
