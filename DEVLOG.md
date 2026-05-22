<!--
tier: 3
last_synced_with: v0.4.2
ssot_for: [development-log]
depends_on: [CHANGELOG.md]
last_review: 2026-05-22
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
    - `last_synced_with: v0.3.0 → v0.2.6`, `depends_on` 에 `docs/REVIEW_PROMPT.md` 추가.
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

## 2026-05-20 v0.2.7 — 평행 브랜치 흡수: SCHEMA-AP + TUI 라이브 reload + atomic write

- **무엇을**: 같은 출발점 (`v0.1.5` main) 에서 두 Claude Code 세션이 평행으로 Phase 2 를 구현한 것을 발견. 본 브랜치 (`n9ird` 계열) 가 정본이고, 평행 브랜치 `claude/start-after-handoff-Ij1TX` 의 차별점 3 가지만 본 PATCH 로 흡수.
- **왜**: 평행 브랜치는 양적·질적으로 본 브랜치가 훨씬 깊었지만 (BaseLLMWorker 등 +2,500 줄), Ij1TX 에 있는 다음 3 가지는 본 브랜치에 부재했고 모두 채택 가치가 있었다:
  1. **SCHEMA-AP 안티패턴 카탈로그**: 상태 머신을 우회한 임의 점프 / self-loop 라는 클래스의 안티패턴을 카탈로그화. Phase 3+ 에서 새로운 schema 위반이 발견됐을 때 들어갈 자리.
  2. **TUI 라이브 manifest reload**: 외부 프로세스가 `transition` 으로 state 를 바꿔도 본 브랜치의 TUI 는 stale state 를 보여줬다. 사용자는 "지금 어디까지 왔는가"라는 기본 질문에 답할 수 없게 된다. Phase 3+ 의 IntakePlannerWorker 가 `created → intake_planning → intake_pending_user` 로 전이시킬 때 즉시 시각화 필요.
  3. **Atomic write**: 본 브랜치의 `_write_manifest` 는 `path.write_text` 직접 호출 — 외부 reader (위 2번 reload) 가 half-written 상태를 잠깐도 볼 수 있는 race. TUI reload 를 도입하는 순간 이 race 가 실제로 발현될 수 있어 함께 차단.
- **어떻게**:
  - `orchestrator/project_manager.py:_write_manifest`: tmp 파일에 쓴 뒤 `Path.replace` 로 교체. POSIX rename / Windows `os.replace` 모두 atomic. tmp 파일 잔존 가능성 없음 (`replace` 가 unlink 까지 보장).
  - `orchestrator/tui_app.py`:
    - imports: `JSONDecodeError`, `pydantic.ValidationError`, `orchestrator.project_manager.load_manifest`, `schemas.models.ProjectState`.
    - `_tick_loop` 에 `_reload_manifest_state()` 호출 1 줄 추가.
    - 새 메서드 `_reload_manifest_state`: 매 tick 마다 `load_manifest` 호출, 실패 모드 3 분류 (`FileNotFoundError` → `unknown` / `JSONDecodeError|ValidationError` → `invalid` / 정상 → 변경 시 log). 동일 상태 진입 시에만 1 회 stderr 로그 (noise 억제). 모든 예외 swallow → tick loop 유지.
  - `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` 신설 + `SCHEMA-AP-001 — ProjectState 임의 점프 / self-loop 전이`. mitigation 칸은 본 브랜치의 API 이름 (`LINEAR_SEQUENCE`, `allowed_next_states`, `transition_state`) 에 맞춰 작성. atomic write 도 4중 방어의 한 축으로 명시.
  - `docs/ANTIPATTERNS/README.md` SCHEMA-AP 줄 갱신.
  - VERSION 0.2.6 → 0.2.7, 모든 Tier 1·2·3 마크다운 `last_synced_with` 일괄 갱신.
  - smoke test 5 케이스: ① new_project 성공 ② tmp 파일 잔존 없음 (atomic) ③ transition + history append ④ 손상된 manifest 로드 시 `ValidationError` ⑤ non-JSON manifest 로드 시 `JSONDecodeError` — TUI reload 가 의존하는 모든 경로 검증.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - 5 케이스 smoke test 모두 의도대로.
  - 외부 `transition` 호출 → manifest 디스크 갱신 → 다음 tick (≤ `tui_refresh_interval_sec`, 기본 0.5s) 에 TUI 가 `state changed: A → B` log + Dashboard 라이브 반영.
  - 평행 브랜치 `claude/start-after-handoff-Ij1TX` 의 가치 있는 부분 모두 본 브랜치에 흡수됨. 그 브랜치는 외부 codex review 통과 후 폐기 예정.
- **연관**: SCHEMA-AP-001 (신설). 평행 브랜치 발견 자체는 거버넌스 문제 (PR 없이 두 세션이 동시 작동) 라 별도 카탈로그 항목으로 등록은 보류 — 본 PATCH 자체가 그 사고의 복구.

## 2026-05-20 v0.2.8 — Codex 2차 리뷰 H2 반영: atomic write durability + tmp cleanup

- **무엇을**: `claude/phase-2-finalize` (v0.2.7) 에 대한 Codex Cloud 3-way 통합 리뷰 결과 (High 2 / Medium 3 / Low 4) 중 코드 측 High 1 건 (H2 — atomic write durability + tmp leftover) 을 머지 전 PATCH 로 흡수.
- **왜**: v0.2.7 의 `_write_manifest` 는 `tmp.write_text(...) + tmp.replace(path)` 로 **visibility** (rename atomicity) 만 보장했으나, durability (전원장애·강제종료 시 마지막 write 유실 방지) 는 별개. 또한 write 와 replace 사이에서 예외가 발생하면 tmp 파일이 leftover 로 남는 문제. TUI 라이브 reload 가 동시에 manifest 를 읽는 본 PATCH 시점부터는 이 두 갭이 실제 운영 리스크로 격상됨. Codex H2 의 지적이 정확함.
- **어떻게**:
  - `orchestrator/project_manager.py:_write_manifest` 전면 재작성:
    - `path.write_text` 를 `open() / write() / flush() / os.fsync(fileno())` 4단으로 분해. fsync 가 OS 버퍼 → 디스크 매체까지 강제. `f.flush()` 만으로는 OS 버퍼만 비우고 디스크 도달은 미보장이므로 둘 다 필요.
    - rename 후 부모 디렉토리도 `os.fsync(dir_fd)`. POSIX `rename(2)` 의 원자성과 디렉토리 entry 의 durability 는 별개라서 dir fsync 가 필요 (널리 알려진 함정). `O_DIRECTORY` 가 없는 Windows 환경은 `OSError` 로 떨어지므로 best-effort skip.
    - write/replace 단계 전체를 `try/except` 로 감싸 leftover tmp 를 `unlink` (cleanup 실패는 swallow, 원본 예외만 전파). `replace` 성공 후엔 tmp 가 이미 path 로 옮겨졌으므로 잔존 불가.
    - docstring 을 "atomic visibility" vs "durability" 로 분리. 향후 reader 가 "이 함수가 무엇을 보장하고 무엇을 안 하는지" 한눈에 알 수 있게.
  - `os` 모듈 import 추가 (`fsync`, `O_DIRECTORY`, `open` 헬퍼).
  - smoke test 에 `Path.replace` mock 으로 의도적 실패를 흉내내 cleanup 동작 검증 1 케이스 추가. 정상 happy path / corrupt manifest ValidationError / non-JSON JSONDecodeError 와 함께 5 케이스 모두 통과.
  - n9ird 의 기존 30 단위 테스트 회귀 전부 통과.
- **결과**:
  - `python -m py_compile` 통과.
  - 5 smoke + 30 unit = 35 케이스 모두 의도대로.
  - 머지 차단 사유 (H2) 해제. H1 (Ij1TX 원본 커밋 부재로 흡수 완전성 입증 불가) 은 코드 이슈가 아닌 절차 이슈로 분리:
    Codex Cloud 가 본 저장소 clone 시 모든 브랜치를 fetch 하지 않을 수 있음 → 다음 리뷰 시 사용자가 명시적으로 `claude/start-after-handoff-Ij1TX` 와 `claude/phase-2-implementation-n9ird` 를 비교 대상으로 지정. 본 저장소에서는 두 브랜치 모두 origin 에 존재.
- **연관**: Codex H2. M/L 5건은 v0.2.9 또는 Phase 3 진입 전 일괄 처리 후보로 분리.

## 2026-05-20 v0.2.9 — Codex 3차 리뷰 결과 흡수 (dir fsync 신호화 + 타입 힌트 + 주석 정합)

- **무엇을**: `claude/phase-2-finalize` HEAD 78f11bb (v0.2.8) 에 대한 Codex Cloud 단일 브랜치 리뷰 결과 (Critical 0 / High 1 / Medium 1 / Low 1) 를 v0.2.9 PATCH 로 흡수. 머지 차단 사유 해제.
- **왜**: 3차 리뷰의 H1 ("dir fsync 실패가 완전히 묵살되어 docstring 의 durability 보장과 어긋남") 이 머지 차단 사유였음. v0.2.8 에서 `try/except OSError: pass` 가 너무 적극적인 swallow 였다. POSIX 환경에서 권한·FS 특성·일시 오류로 dir fsync 가 실패하면 rename durability 가 약화되는데, 호출자에게도 로그에도 신호가 없으면 사후 추적 불가능. 운영자 기대치 (docstring 의 durability 보장) 와 runtime 현실의 정합이 필요.
- **어떻게**:
  - `orchestrator/project_manager.py`:
    - 모듈 레벨 `logger = logging.getLogger(__name__)` 도입. 본 저장소 첫 표준 logging 진입점.
    - dir fsync `except OSError as e:` 에서 platform (`os.name`) · errno · 메시지를 포함한 `logger.warning(...)`. 실패는 여전히 흡수 (rename 은 이미 visible) 하되 신호화. 호출 측이 logging 설정 없으면 root logger 가 stderr 로 송출.
    - `_SLUG_RE` 주석을 "하이픈만" 뉘앙스 → "하이픈·언더스코어 허용, 첫 글자는 영숫자" 로 실제 정규식 의도와 일치하게 정합화 (3차 리뷰 L 항목).
  - `orchestrator/main.py`:
    - `_print_manifest_summary(manifest)  # type: ignore[no-untyped-def]` → `_print_manifest_summary(manifest: ProjectManifest) -> None`. type ignore 제거. CLAUDE.md C2 "모든 함수 시그니처 타입 힌트 필수" 정합.
    - `from schemas.models import ... ProjectManifest` 추가.
  - smoke test 추가: `unittest.mock.patch('orchestrator.project_manager.os.fsync', ...)` 로 두 번째 fsync 호출 (dir fsync) 만 `OSError(13, ...)` 던지게 mock. warning 로그에 `errno=13` / `platform=posix` / 한국어 메시지 포함을 직접 검증.
  - 5 케이스 smoke (happy / dir fsync 실패 시 warning log / cleanup 회귀 / corrupt JSON / non-JSON) + 30 기존 단위 테스트 회귀 모두 통과.
  - VERSION 0.2.8 → 0.2.9, 갱신된 4 파일 (`CHANGELOG.md`, `DEVLOG.md`, `HANDOFF.md`, `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md`) 의 `last_synced_with` 만 v0.2.9 로 (n9ird 컨벤션: 수정한 파일만 갱신).
- **결과**:
  - `python -m py_compile` 통과.
  - 35 케이스 (5 smoke + 30 unit) 모두 의도대로.
  - Codex 머지 차단 사유 (H) 해제. M·L 도 같이 처리. main 머지 직전 단계.
  - 본 PATCH 자체에 대해 머지 전 한 차례 더 codex 리뷰를 돌리는 것이 안전 (코드 변경 있음, C10.3 self-exemption 미적용).
- **연관**: Codex 3차 리뷰 H1/M1/L1. 미반영 4 항목은 CHANGELOG v0.2.9 의 "Codex 3차 리뷰 미반영 항목" 절에 사유와 함께 기록.

## 2026-05-21 v0.3.0 — Phase 3: Dynamic Intake Page + IntakePlannerWorker

- **무엇을**: Phase 3 의 핵심 산출물 3 종 (도메인 LLM Worker + 웹 폼 + CLI) 을 단일 MINOR
  로 묶어 도입. HANDOFF §2.2 의 DoD 8 항목을 모두 충족.
- **왜**: BaseLLMWorker 인프라가 외부 리뷰 3 차까지 (v0.2.9) 견고해졌고, codex review 절차도
  정형화 (v0.2.6) 됐다. 다음 자연스러운 단계는 **첫 도메인 LLM Worker** 인 IntakePlannerWorker.
  이 Worker 가 도입되면 (a) Phase 0 의 IntakePlan Pydantic 모델이 처음으로 실 데이터로 채워지고,
  (b) BaseLLMWorker 의 4 parsed_status / output_path 가드 / agent 모드 opt-in 이 도메인 흐름에서
  실제로 검증되며, (c) 사용자가 처음으로 웹 UI 로 파이프라인과 상호작용하게 된다 (지금까지는
  CLI / TUI 만).
- **어떻게**:
  - `workers/intake_planner_worker.py` 신설. BaseLLMWorker 상속. `system_prompt` 가 IntakePlan
    스키마 + IntakeMode 9 enum 값 + 출력 규칙을 LLM 에 강제. `CATEGORY_GUIDANCE` (모듈 레벨 dict)
    가 GOAL.md G2 의 5 카테고리별 baseline 항목 카탈로그. `build_user_prompt` 가 manifest 의
    title/category/duration/topic_summary 를 `.replace()` 로만 치환 (`.format()` 은 JSON `{}` 와
    충돌 — CLAUDE.md C2). `output_path` 는 `01_intake/intake_plan.json` 으로 고정.
    `load_manifest` 의존을 의도적으로 회피하고 `BaseWorker.project_dir(args)` 가 책임지는 경로 기반
    파일 read 로 가서 단위 테스트의 `args.projects_root=<tmp>` 가 정상 동작.
  - `web/intake_page_app.py` 신설. FastAPI + 인라인 HTML (Jinja 미도입). `_render_intake_html`
    이 manifest + plan 을 카드 폼으로 직렬화, 모든 사용자/manifest 유래 문자열에 `html.escape`.
    `_form_to_decisions` 가 form-urlencoded 입력을 `UserDecision[]` 로 검증된 변환 — 알 수 없는
    enum 값은 `default_mode` 폴백, 누락 mode 도 폴백. `submit` 핸들러는 `transition_state` 를 통해서만
    상태를 변경 (직접 manifest 쓰지 않음). 401·404 등은 `HTTPException` 으로 일관 응답.
  - `orchestrator/main.py` 에 `plan-intake` / `submit-intake` 서브커맨드 추가. `_cmd_plan_intake`
    가 합성 `TaskQueueItem` (output_refs=["01_intake/intake_plan.json"]) 으로 worker.run() 직접
    호출 + state 두 단계 전이. `_cmd_submit_intake` 가 입력 JSON 의 project_id 일치 검증 + 영속화 +
    `source_collecting` 전이. Phase 4 의 자동 task_queue.json 도입 전 단계라 의도적으로 task_queue
    파일 영속화는 하지 않음.
  - 의존성: `requirements.txt` + `pyproject.toml` 에 fastapi/uvicorn/python-multipart 추가.
  - 테스트: `tests/test_intake_planner_worker.py` (13 케이스) + `tests/test_intake_flow.py` (6
    케이스). 후자는 `orchestrator.config.REPO_ROOT` 와 `workers.base_worker.REPO_ROOT` 양쪽을
    임시 디렉토리로 monkeypatch 해 실제 `projects/` 를 건드리지 않으면서 CLI end-to-end (new-project
    → plan-intake → submit-intake) + FastAPI `TestClient` POST 흐름까지 검증. stub mode 로 실 LLM
    호출은 회피.
  - 문서: `docs/03_AGENT_ARCHITECTURE.md` Agent 카탈로그의 Dynamic Intake Planner 행을 실제 구현
    파일 (`workers/intake_planner_worker.py (BaseLLMWorker)`) 로 갱신 + Worker 카탈로그에 한 행
    추가. 본 저장소 정책에 따라 LLM 호출 worker 의 parallelizable 은 ❌ (slot 1개 점유 가정).
  - VERSION 0.2.9 → 0.3.0, 36 개 마크다운/HTML `last_synced_with` 일괄 갱신 (sed).
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 모두 통과.
  - 단위 테스트 49 케이스 (30 회귀 + 13 IntakePlanner + 6 인테이크 flow) 모두 통과.
  - DoD 8 항목 (HANDOFF §2.2) 충족 확인:
    - [x] plan-intake → intake_plan.json + intake_pending_user 상태 (test_intake_flow.TestPlanIntakeCLI 검증)
    - [x] 웹 제출 → source_intake.json + source_collecting (test_intake_flow.TestWebSubmit 검증)
    - [x] 모든 도메인 데이터 Pydantic 검증 통과 (IntakePlan / SourceIntake / UserDecision 통합 케이스)
    - [x] LLM 호출은 BaseLLMWorker 경유, llm_calls/{call_id}.{json,prompt.txt,raw.txt} 영속화
    - [x] codex backend 도 stub mode 케이스 추가 (test_codex_backend_passthrough). 실 호출은 Windows
          에서 사용자 검증 필요 — 본 컨테이너는 codex CLI 미설치.
    - [x] py_compile + 단위 테스트 49 케이스 통과 (35+ 초과)
    - [x] CHANGELOG.md `[v0.3.0]` + DEVLOG.md 본 엔트리
    - [ ] **C10.1 codex review** — 본 컨테이너에 codex CLI 부재. 사용자 머신에서 `docs/REVIEW_PROMPT.md`
          §3 절차로 실행 예정. 결과는 v0.3.1 PATCH 로 흡수 또는 false-positive 합의.
- **알려진 위험과 향후**:
  - Phase 4 (`task_queue.json` 자동 생성 + 일반 worker subprocess 흐름) 가 도입되면 IntakePlannerWorker
    도 합성 task 대신 실제 queue 의 task 로 호출되도록 plan-intake CLI 를 단순화.
  - LLM-AP-003 후속 (codex --sandbox, scratch dir, `<untrusted_source>` envelope) 은 Phase 4 의
    `source_collector_worker` 도입 전에 처리 — IntakePlanner 는 agent 모드 미사용이라 본 Phase 미해당.
  - SCHEMA-AP-001 회귀 테스트는 v0.2.9 에서 v0.3.x 후보로 분리되어 있었음 — 본 PATCH 에서도 다루지
    않음. intake flow 의 정상 전이 (6 케이스) 가 부분 cover 하지만 임의 점프 명시 회귀는 별도.
- **연관**: HANDOFF §2 Phase 3 DoD, GOAL.md G3 #7/#8/#10, docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md.

## 2026-05-21 v0.3.1 — Codex 4차 리뷰 흡수: web 보안 + state 견고성 + 테스트 보강

- **무엇을**: v0.3.0 (89f56f9) 에 대한 Codex 단일 브랜치 리뷰 결과 (Critical 1 / High 3 /
  Medium 4 / Low 1 / Nit 1, 총 11 항목) 를 단일 PATCH 로 흡수. False positive 없음.
- **왜**: Phase 3 는 본 저장소 첫 web-facing endpoint + 첫 도메인 LLM Worker 도입이라 보안
  표면이 처음으로 확장. C1 (path traversal), H1 (절대경로 누출), H2 (form DoS) 는 모두 web 표면
  의 신뢰 경계 미설정에서 비롯. H3/M1/M2 는 state machine 과 추적성의 일관성 문제로, 다음 Phase
  들의 task_queue 자동화가 들어오기 전에 베이스라인을 견고하게.
- **어떻게**:
  - **C1** — `orchestrator/project_manager.py` 에 공개 가드 `validate_project_id(pid)` 분리.
    `new_project` 내부 검증을 추출해 web/CLI/통합 코드가 공유. `_SLUG_RE` 와 동일 정책. 위반 시
    `ValueError`. `web/intake_page_app.py` 에 `_validated_pid` 헬퍼가 두 endpoint 진입점에서 강제,
    실패 시 400 + generic detail. CLI `plan-intake`/`submit-intake` 도 동일 호출.
  - **H1** — `web/intake_page_app.py` 의 두 핸들러 `except FileNotFoundError` 블록에서 절대경로가
    포함된 원본 메시지를 generic `"intake plan not found for the requested project"` 로 교체.
    원본 detail 은 `logger.warning("intake … 404 — pid=%s detail=%s", ...)` 로 서버 측 로그만.
  - **H2** — submit 핸들러가 `request.headers.get("content-length")` 검사를 `await request.form()`
    전에 수행. 한도는 모듈 변수 `MAX_FORM_BYTES = 256 * 1024`. 초과 시 413 즉시 거부. 변조된
    헤더는 swallow 하고 starlette 내부 한도가 fallback.
  - **H3** — `orchestrator/main.py:_cmd_plan_intake` 에 `--force` 옵션 + idempotent skip 로직
    추가. `intake_planning` 상태에서 `01_intake/intake_plan.json` 이 존재하고 `IntakePlan` 검증을
    통과하면 worker 호출을 건너뛰고 `intake_pending_user` 로 전이만 진행. 손상된 plan 은
    재실행 (이전 부분 산출물 복구). 출력에 `skipped=True/False` 명시.
  - **M1** — `_cmd_submit_intake` 의 흐름을 (1) state precondition (current_state == intake_pending_user)
    조기 검증 → (2) tmp 파일에 write → (3) `transition_state` 시도 → (4) 성공 시 `tmp.replace(out_path)`,
    실패 시 tmp `unlink` cleanup. Web 의 `submit_intake` 도 비슷한 흐름 (write 자체를 transition
    뒤로 이동) 으로 재배열. 잘못된 상태에서 파일 덮어쓰기 차단.
  - **M2** — `_cmd_plan_intake` 가 `worker.run()` 직후 `worker.write_result(worker_args, result)`
    를 명시 호출. `projects/{pid}/03_tasks/task_results/intake-plan-{pid}_result.json` 생성. Phase 4
    의 정식 task_queue 흐름 전까지 C4 추적성 stopgap.
  - **M3** — `tests/test_intake_planner_worker.py` 에 `TestRunParseFailed` (자연어 stub →
    JSONDecodeError) + `TestRunSubprocessError` (`_invoke_llm` monkeypatch, exit_code 7 record
    영속화 검증). IntakePlanner 가 BaseLLMWorker 의 4 parsed_status 분기 전부에 도달함을 명시.
  - **M4** — `tests/test_intake_flow.py::TestWebSecurityAndNegativePaths` 7 케이스 신설.
    traversal PID GET/POST, 대문자 PID, 없는 PID 의 generic 404 (절대경로 미노출 grep),
    MAX_FORM_BYTES 잠시 낮춰 413, M1 race (state precondition + 기존 파일 bytes 보존), M2
    task_result.json 존재, H3 idempotent skip (LLM stub unset 상태에서도 worker 미호출
    + llm_calls/ 미생성).
  - **L1** — `_render_item_card` HTML 에 google_drive_links / uploaded_files / ai_delegate_remaining
    입력 필드 추가. parser 가 처리하는 모든 UserDecision 필드를 UI 에 노출 (contract drift 해소).
  - **N1** — `TestRunValidationFailed` 의 코멘트가 실제 실패 원인 (extra="forbid" 위반) 과
    어긋났던 부분 정정.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 단위 테스트 49 → **60 케이스** (BaseLLMWorker 22 + run 통합 8 + IntakePlanner 15 + 인테이크
    flow 15). 모두 통과.
  - 머지 차단 사유 (Codex Critical/High 4건) 모두 해제. Medium/Low/Nit 도 같이 흡수.
  - last_synced_with 는 v0.2.9 의 n9ird 컨벤션 (수정한 마크다운만) 따름 — CHANGELOG.md /
    DEVLOG.md / HANDOFF.md 만 v0.3.1 로. PATCH 의 코드 4 파일 + 테스트 2 파일은 YAML 헤더 없음.
- **알려진 한계와 향후**:
  - H2 의 starlette 내부 form 크기 한도는 ASGI 서버 (uvicorn) 설정에 의존. 운영 배포 시
    `uvicorn --limit-max-requests N` / nginx 등의 reverse proxy 단에서 추가 강제 권장.
  - M1 의 web 흐름은 CLI 와 달리 tmp-rename 대신 transition-우선 순서를 채택. write 실패
    (디스크 full 등) 시 state 만 진행되는 좁은 race 존재. Phase 4 에서 web 도 tmp-rename
    패턴 통일 검토.
  - H3 의 `--force` 는 의도적 우회로 두되, Phase 4 의 task_queue 흐름이 도입되면 task
    재실행은 큐 레벨에서 결정 (worker 단의 `--force` 는 사라질 가능성).
- **연관**: Codex 4차 리뷰 11 항목 전부. C10.3 self-exemption 적용.

## 2026-05-22 v0.3.2 — SCHEMA-AP-001 회귀 테스트 명시 (누적 부채 청산)

- **무엇을**: `orchestrator.state_machine.validate_transition` 의 다섯 가지 보호 조건
  (정상 선형 / 임의 점프 거부 / self-loop 거부 / ARCHIVED 어디서든 도달 / ARCHIVED
  종착성) 을 단위 테스트로 회귀화. `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` 의
  `regression_test: pending` 을 실제 파일 경로 + 카테고리 매핑으로 갱신. 코드 동작
  변경 없음.
- **왜**: SCHEMA-AP-001 은 v0.2.7 에 카탈로그 등록되었지만 회귀 테스트가 5 케이스
  pending 으로 남아 있어 v0.2.9 부터 누적 부채. Phase 4 (task_queue + 첫 agent 모드
  Worker) 가 state 머신 위에 새 전이 사용처를 얹기 전에 가드의 정확성을 명시적으로
  고정해 두는 것이 안전. v0.3.x PATCH 후보 (HANDOFF §2.4) 의 첫 항목.
- **어떻게**:
  - `tests/test_state_machine.py` 신설. 5 카테고리 × 평균 2 메소드 = 10 테스트 메소드.
    각 카테고리를 별도 `TestCase` 클래스로 분리해 실패 시 어느 보호 조건이 깨졌는지
    즉시 식별 가능. `LINEAR_SEQUENCE` 의 모든 인접 페어를 `subTest` 로 순회해 정의가
    바뀌면 즉시 신호.
  - `_coerce` 가 str → enum 변환을 한다는 사실도 한 케이스로 명시
    (manifest 의 `use_enum_values=True` 와 정합).
  - 메시지 contract 도 회귀화: "잘못된 상태 전이" / "동일 상태" / "허용된 다음 상태"
    힌트가 메시지에 포함되는지 검증. CLI / web 의 사용자-facing 에러 메시지가 조용히
    바뀌는 것을 차단.
  - `SCHEMA_ANTIPATTERNS.md` 의 `regression_test` 필드를 `pending` 에서 실제 위치로
    갱신. README 가 명시한 `status` / 위치 정보의 운영 라이프사이클 갱신 (내용 자체
    수정 아님, append-only 정책 준수).
  - 테스트 디렉토리 구조는 카탈로그 표기 `tests/orchestrator/test_state_machine.py`
    대신 기존 평면 구조 `tests/test_state_machine.py` 채택 (CLAUDE.md 원칙 1
    "단순함을 우선"). 카탈로그도 평면 경로로 정정.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 단위 테스트 60 → **70 케이스**. 모두 통과.
  - 카탈로그의 `pending` 부채 1건 청산. v0.4.0 의 Phase 4 가 state 머신 위에 안심하고
    얹을 수 있는 기반 마련.
- **알려진 한계와 향후**:
  - `LINEAR_SEQUENCE` 자체의 진화 (예: 새 상태 삽입) 는 본 회귀가 자동으로 따라간다
    (인접 페어 순회). 그러나 ARCHIVED 의 특수 의미가 바뀌면 ④/⑤ 케이스 직접 수정 필요.
  - 메시지 contract 검증은 영어 → 한국어 / 표현 변경 시 함께 갱신해야 한다. 너무
    엄격하면 i18n 비용, 너무 느슨하면 회귀 가치 떨어짐. 현재는 핵심 키워드만 매치
    (substring) 로 균형.
- **연관**: SCHEMA-AP-001, HANDOFF §2.4 첫 항목.

## 2026-05-22 v0.3.3 — `<untrusted_source>` envelope 헬퍼 도입 (LLM-AP-003 후속 사전 작업)

- **무엇을**: `workers/prompt_safety.py:wrap_untrusted` 순수 함수 신설. 외부 자료를
  `<untrusted_source>...</untrusted_source>` envelope 으로 안전하게 wrap 하는
  헬퍼와 회귀 테스트 (13 메소드). 코드 동작 변경 없음 — 호출하는 worker 는 아직 없음
  (Phase 4 의 `source_collector_worker` 가 사용 예정).
- **왜**: LLM-AP-003 의 본격 mitigation 은 (a) opt-in 가드 (v0.2.5 완료), (b)
  envelope 격리, (c) sandbox 매핑 + scratch dir 의 세 요소. (c) 는 Phase 4 와 함께
  가야 의미가 있지만 (b) 는 순수 함수 + 회귀 테스트만 들어가는 작은 작업이라 미리
  분리. Phase 4 PATCH 가 커지는 것을 막고, envelope 의 정확한 시맨틱이 단위 테스트
  로 못박힌 상태에서 worker 가 호출할 수 있게.
- **어떻게**:
  - 위치는 `workers/prompt_safety.py` 신규 모듈로 결정 (BaseLLMWorker staticmethod
    대신). BaseLLMWorker 가 이미 573 줄로 비대해진 점, Phase 4 의 sandbox / scratch
    유틸이 같은 위치에 자라날 자리 확보를 위해. CLAUDE.md 원칙 1 "단순함을 우선"
    의 단순함은 "한 곳에 모음" 보다 "각각의 책임 모듈" 로 해석.
  - escape 전략은 명시적 마킹 (`<ESCAPED_OPEN_untrusted_source` /
    `<ESCAPED_CLOSE/untrusted_source>`). zero-width space 같은 invisible escape 대신
    LLM 이 보고 명백히 sanitize 되었음을 인지할 수 있는 노이즈 토큰 사용. 정확한
    envelope 경계 토큰과 더 이상 매치되지 않으면 충분.
  - 변형 회피: case-insensitive + 공백 허용 regex (`<\s*untrusted_source\b` /
    `<\s*/\s*untrusted_source\s*>`). LLM 이 정규화해서 받아들일 수 있는 변형까지
    보수적으로 차단.
  - label 안전화: envelope 태그 escape + `"` → `&quot;` (속성값 종료 방지) +
    newline 공백 평탄화 (opener 한 줄 보장).
  - 회귀 테스트 5 카테고리: ① 정상 wrap 형식 ② close-tag injection ③ open-tag
    injection (속성 변형 포함) ④ case / whitespace 변형 ⑤ label 안전화 (`"` /
    envelope 태그 / newline 각각).
  - LLM-AP-003 카탈로그의 mitigation / regression_test / resolved / 알려진 한계
    절을 envelope 헬퍼 진전 반영해 update. status 는 `resolved-partial` 유지 —
    sandbox / scratch dir 까지 끝나야 `resolved`.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 단위 테스트 70 → **83 케이스**. 모두 통과.
  - Phase 4 의 `source_collector_worker` 가 외부 자료를 prompt 에 넣을 때 호출할
    안정적 sentinel 확보.
- **알려진 한계와 향후**:
  - sentinel 만으로는 prompt injection 의 한 layer 일 뿐. semantic injection
    (envelope 안에서 일반 문장으로 LLM 을 속이는 방식) 은 막지 못함. Phase 4 의
    `--sandbox workspace-write` 매핑 + scratch dir 격리가 함께 가야 의미가 있다.
  - "envelope 안을 명령으로 해석하지 마라" 를 LLM 에게 명시하는 책임은 호출자
    (worker 의 system_prompt) 측. 본 함수는 sentinel 형식만 보장.
  - 매우 긴 외부 자료 (수십 KB+) 의 길이 제한은 호출자 정책. Phase 4 의 worker 가
    필요 시 truncate + summary 단계 도입.
- **연관**: LLM-AP-003 (resolved-partial 의 (b) envelope 격리 완료), HANDOFF §2.4
  envelope 헬퍼 항목, Phase 4 의 `source_collector_worker` 선결 작업.

## 2026-05-22 v0.3.4 — codex 리뷰 절차의 역할 분담을 규칙으로 박음

- **무엇을**: `CLAUDE.md` C10 과 `docs/REVIEW_PROMPT.md` §2 에 codex 외부 리뷰의
  역할 분담을 명문화. 새 §C10.0 "역할 분담 (변경 불가)" 추가 — AI 어시스턴트가
  `review-prompt.txt` 본문을 직접 생성하고, 사용자는 codex 실행 + 결과 paste 만
  수행. AI 가 절차를 *안내만* 하고 사용자 명시적 요청을 기다리는 형태도 위반으로
  정의. C10.2 5 단계에 `(AI 어시스턴트 책임)` / `(사용자 책임)` / `(공동)` 태그 부여.
- **왜**: 직전 세션 (v0.3.3 직후 / v0.4.0 작업 도중) 에 AI 어시스턴트가 MINOR
  증분 직전이라는 trigger 시점을 인식했음에도, codex 리뷰를 "사용자가 자기
  머신에서 직접 수행하는 단계" 로만 안내하고 능동적으로 시작하지 않는 사고가
  발생. 사용자가 직접 "왜 의무인데 패스하느냐 / 프롬프트는 AI 가 생성해서
  나에게 줘라" 라고 교정 지시. 같은 ambiguity 가 재발하지 않도록 규칙 자체를
  닫음. (v0.2.6 의 절차 정형화 PATCH 가 *언제 실행하나* / *어떻게 실행하나* 까지는
  박았지만 *누가 채우나* 는 암묵적이었음.)
- **어떻게**:
  - C10 머리에 새 §C10.0 표로 AI 어시스턴트 / 사용자 책임을 분리 명시. 표
    아래에 "AI 어시스턴트는 본 절차를 임의로 생략하지 못한다" 를 굵게 명문화.
    "trigger 시점에 절차를 안내만 하고 사용자의 명시적 요청을 기다리는 것" 도
    위반으로 정의.
  - C10.2 의 5 단계 각각에 책임자 태그 부여. step 1 은 "AI 가 세 절을 모두
    직접 채워서 완성된 `review-prompt.txt` 를 SendUserFile 또는 코드블록으로
    전달" 로 강화. 사용자에게 "이 칸을 채우세요" 는 명시적 금지.
  - `docs/REVIEW_PROMPT.md` §2 의 템플릿 안내 직후에 인용 블록으로 같은 규칙을
    재진술 (작업자가 CLAUDE.md 까지 안 봐도 매뉴얼만 보고 알 수 있도록).
  - 본 PATCH 는 `CLAUDE.md` C10.3 "본 절차 자체를 도입/수정하는 PATCH 는
    codex review 면제" 에 의해 외부 리뷰 면제. 자기 검증 회피 방지.
  - 버전 / 동기화: VERSION 0.3.3 → 0.3.4, CLAUDE.md / REVIEW_PROMPT.md /
    CHANGELOG / DEVLOG 헤더 last_synced_with 갱신.
- **결과**:
  - 다음 trigger 시점부터 AI 어시스턴트는 "리뷰 절차를 안내" 가 아니라
    **"완성된 review-prompt.txt 본문을 전달"** 을 의무로 수행. 사용자의 명시적
    요청 없이도 능동적으로 시작해야 함이 규칙으로 박힘.
  - 본 PATCH 직후 v0.4.0 (LLM-AP-003 sandbox + scratch dir mitigation) 작업에서
    본 규칙을 최초로 자기 자신에게 적용 — 코드 완성 후 review-prompt.txt 본문
    생성 → 사용자 paste → 흡수 → v0.4.0 커밋.
- **알려진 한계와 향후**:
  - "trigger 인식" 자체를 자동화하는 git hook / CI 검증기는 아직 없음. AI 가
    self-discipline 으로 수행. 향후 commit-msg hook 에 "MINOR/MAJOR 커밋이면
    직전 N 커밋 안에 'codex' 라는 단어가 포함된 commit body 가 있는지" 같은
    weak signal 검증을 추가 검토.
  - false positive 합의 / DEVLOG 근거 명시 의무는 C10.2 step 5 에 그대로.
- **연관**: CLAUDE.md C10, docs/REVIEW_PROMPT.md, v0.2.6 (절차 정형화의
  연속), v0.4.0 (본 규칙의 첫 적용 대상).

## 2026-05-22 v0.4.0 — LLM-AP-003 sandbox + scratch dir 본격 mitigation + SourceCollectionPartial

- **무엇을**: codex agent CLI 매핑에 `--sandbox workspace-write` 추가, `--cd` 를
  `{project_dir}` → `{scratch_dir}` (`projects/{pid}/scratch/{task_id}/`) 로 변경.
  `BaseLLMWorker._scratch_dir_for_task` 헬퍼 신설. `_invoke_llm` 의 placeholder
  치환 시 `llm_mode == "agent"` 인 경우만 scratch dir 경로로 치환. 동시에 Phase 5
  의 `source_collector_worker` 출력 모델 `SourceCollectionPartial` (VersionedModel,
  schema_version=1 유지) 선행 정의.
- **왜**: LLM-AP-003 의 mitigation 세 layer 중 마지막 한 칸. (a) opt-in 가드
  (v0.2.5 완료) (b) envelope 격리 (v0.3.3 완료) (c) OS 레벨 sandbox + 파일시스템
  격리 — 본 PATCH 의 본론. agent 모드의 LLM 이 prompt injection 으로 sandbox
  바깥 / scratch 바깥에 write 하지 못하도록 두 겹의 boundary 를 둔다.
  Phase 5 worker 가 들어와야 실 효과 실증되지만, CLI 매핑과 헬퍼는 worker 보다
  먼저 박혀 있어야 worker 가 일관된 sandbox 가정 위에서 동작할 수 있음.
  `SourceCollectionPartial` 도 같은 맥락 — Phase 5 PATCH 가 worker + 모델을
  동시에 도입하지 않아도 되도록 모델만 선행 (작은 단위 커밋 C8.2).
- **어떻게**:
  - `CLI_INVOCATION` 의 `("codex", "agent")` 엔트리만 수정 (claude 와 codex
    response 는 동일). `--sandbox workspace-write` 의 의미는 codex `--cd` 디렉토리
    내부에서만 write 허용 — codex 자체의 OS 레벨 boundary.
  - `--cd` 인자를 `{scratch_dir}` 로 옮긴 이유: sandbox 가 active 여도 codex 의
    "현재 작업 디렉토리" 가 project_dir 이면 사용자가 무심코 거기에 write 가능한
    파일들 (다른 worker 산출물 / git 추적 코드) 이 sandbox 안에 포함된다. scratch
    dir 로 격리하면 sandbox + cwd 두 boundary 가 일치해 가장 좁아진다.
  - `_scratch_dir_for_task` 의 위치는 `BaseLLMWorker` 로. BaseWorker 에 두는 안도
    검토했지만, scratch dir 은 LLM agent 모드 의 sandbox 와 짝을 이루는 개념이라
    역할이 맞는 쪽에 둠. 비-LLM worker 가 scratch 공간이 필요해지면 그 때
    BaseWorker 로 lift.
  - placeholder 치환 분기: `llm_mode == "agent"` 일 때만 헬퍼 호출 (= mkdir 발생).
    response 모드는 빈 문자열 substitution → 만약 template 이 실수로 `{scratch_dir}`
    를 갖고 있어도 argv 가 빈 문자열로 변형되어 codex 측에서 명시적으로 실패
    (silent corruption 보다 낫다). 단 향후 response template 이 `{scratch_dir}`
    를 의도적으로 참조하지 않도록 코드 리뷰 / 회귀로 관리.
  - LLM-AP-003 카탈로그의 mitigation / regression_test / resolved / status /
    알려진 한계 절을 v0.4.0 진전 반영. status 는 `resolved-partial` 유지하되
    partial 의 의미가 "sandbox/scratch 매핑까지 마련, 실 호출 worker 는 Phase 5"
    로 이동.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 기존 단위 테스트 83 케이스 회귀 없이 통과.
  - codex agent CLI 가 자기 task 의 scratch 디렉토리 밖으로 write 못 하는 두 겹
    boundary 확보 — sandbox + cwd.
  - Phase 5 의 `source_collector_worker` 가 일관된 가정 위에서 도입 가능.
- **알려진 한계와 향후**:
  - 실 호출 worker (`source_collector_worker`) 가 아직 없음. sandbox 의 실제
    효과 — symlink escape, mount bind escape, codex 버전별 차이 — 는 worker
    도입 후 e2e smoke test 에서 검증.
  - scratch dir 은 task_id 단위 mkdir 만. 같은 task_id 재실행 시 잔존물 보임.
    현재 workers 가 멱등 실행 가정 없으므로 수용 가능. 필요 시 Phase 5 에서
    `shutil.rmtree → mkdir` 로 ephemeral.
  - codex `--sandbox workspace-write` 의 정확한 escape 경계는 codex 버전마다
    달라질 수 있어 `docs/ADDENDUM_04` §5 에 정기 갱신 필요.
  - 사용자 머신의 codex CLI 가 `--sandbox` 미지원이면 agent 모드 호출이 unknown
    flag 로 실패. 호출자가 분기 가능 (LLMSubprocessError exit_code != 0).
- **연관**: LLM-AP-003 (mitigation layer (c) 완료, status 는 여전히 resolved-partial
  — 호출 worker 도입까지), v0.3.3 (envelope 헬퍼), Phase 5 의
  `source_collector_worker` (본 PATCH 의 가정을 활용할 첫 worker).
- **codex 리뷰**: 본 PATCH 직후 v0.3.4 의 새 C10.0/C10.2 규칙에 따라 AI 가
  생성한 review-prompt.txt 로 codex 외부 리뷰 실행. 결과 흡수는 v0.4.1 PATCH
  ("외부 코드 리뷰 N차 반영") 로.

## 2026-05-22 v0.4.1 — codex 1차 외부 리뷰 흡수: sandbox 가드 승격 + 회귀 잠금

- **무엇을**: v0.4.0 의 codex 외부 리뷰 (Critical 2 / High 3 / Medium 3 / Low 1 /
  Nit 1) 단일 PATCH 흡수. v0.4.0 의 "의도된 가정" 들을 명시적 가드로 승격하고
  17 회귀 테스트로 잠금.
- **왜**: v0.4.0 는 codex `--sandbox workspace-write` + `--cd {scratch_dir}` 의
  "방향" 은 옳았지만 (i) task_id 가 path traversal 페이로드면 scratch 경계가
  깨지고, (ii) scratch 경로상 누군가 미리 깔아둔 symlink 가 있으면 codex 의
  sandbox resolve 가 우회될 수 있고, (iii) response 모드 template 에 누군가
  `{scratch_dir}` 를 끼우면 빈 문자열로 silent corruption 되며, (iv) 새
  placeholder 가 도입돼도 자동으로 알 방법이 없었다. 보안 mitigation 의 "intent"
  를 "verified guarantees" 로 끌어올리려면 가드 + 회귀 잠금이 필수.
- **어떻게**:
  - **C1 (task_id traversal)**: module-level helper `_is_safe_path_segment` 도입.
    `/`, `\\`, `..`, `.`, leading `.`, len > 128 거부 + `Path(s).name == s` 추가
    확인. `_scratch_dir_for_task` 진입 즉시 호출, 실패 시 `LLMSubprocessError`.
  - **C2 (symlink escape)**: module-level helper `_assert_no_symlinks_in_path`
    도입. scratch dir 부터 `project_dir` 까지 위로 올라가며 symlink 검사. 발견
    시 raise. codex 가 자기 안에서 만든 symlink 를 따라가는 행동은 codex 의
    책임이지만, scratch 경계 자체가 symlink 인 시나리오는 우리 쪽에서 차단.
  - **H1 (placeholder footgun)**: `_invoke_llm` 의 argv 빌드 로직을
    `_build_invocation_cmd` 로 추출 (subprocess 호출 없는 순수 함수 → 테스트
    가능). 그 안에서 치환 후 `cmd` argv 의 각 seg 에 `\{[A-Za-z_][A-Za-z0-9_]*\}`
    패턴이 잔존하면 `LLMSubprocessError`. `seg == full_prompt` 인 자리는 검사
    제외 (사용자 prompt 본문의 JSON `{}` 와 충돌 회피).
  - **H2 (mode/template drift)**: 같은 메서드에서 `template_uses_scratch =
    any("{scratch_dir}" in seg for seg in template)` 로 검사. (a) True 이면서
    `llm_mode != "agent"` 면 raise (silent empty-string 차단). (b) True 일
    때만 `_scratch_dir_for_task` 호출 (mode-driven → template-driven, 의도 drift
    제거).
  - **H3 (테스트 부재)**: `tests/test_base_llm_worker_sandbox.py` 신설. 17
    메소드, 4 클래스 (`TestPathSegmentSafety`, `TestScratchDirHelper`,
    `TestAssertNoSymlinks`, `TestInvocationCmdShape`, `TestPlaceholderFailFast`).
    POSIX 한정 symlink 테스트는 `sys.platform == "win32"` 일 때 skip.
  - **M1 (scratch lifecycle)**: `BaseLLMWorker.clean_scratch_on_start: ClassVar
    [bool] = True` 신설. `_scratch_dir_for_task` 가 mkdir 전에 `shutil.rmtree`
    수행. 기본값 True 로 ephemeral 보장 — 멱등 worker 가 잔존물 활용해야 하면
    클래스 변수로 `False` 명시 (현재 그런 worker 0 개).
  - **M2 (Phase 4 → 5)**: `SourceCollectionPartial` docstring 정정.
  - **M3 (notes 범용)**: `notes` → `collector_notes` rename. 모델이 v0.4.0
    신규로 영속 인스턴스 없어 호환성 부담 없음.
  - **L1 (input_item_id 도메인 불변식)**: schema 는 Optional 유지 (C3
    additive-first), 강제는 Phase 5 worker 단으로 미룸. LLM-AP-003 known-limits
    에 명시.
  - **N1 (단정 톤)**: LLM-AP-003 v0.4.0 mitigation 본문의 "scratch 밖으로도
    write 못 함" → "의도된 가정 하에서 — codex 가 `--sandbox workspace-write` 를
    honor 하고, scratch 경로상 symlink 가 없으며, task_id 가 단일 path 세그먼트
    인 경우 — agent 는 (a) 사용자 자료 / (b) 다른 worker 산출물 / (c) git 추적
    코드 모두 건드릴 수 없다." 로 톤다운. known-limits 의 symlink/mount 불확실성
    과 균형.
- **결과**:
  - `python -m unittest discover tests` 100 케이스 통과 (기존 83 + 신규 17, 회귀 없음).
  - codex 1차 리뷰의 모든 Critical/High/Medium/Low/Nit 흡수.
  - argv shape 회귀가 잠겨 향후 CLI 매핑 변경 시 sandbox/scratch 플래그가
    실수로 누락되면 즉시 테스트 실패.
- **False positive**: 첫 번째 리뷰 round (commit 9b200a8 이전 working tree 기준,
  사용자 머신의 v0.3.4 코드를 본 결과) 의 모든 Critical 항목은 "구현 안 됨" 으로
  정확했지만 두 번째 round (commit 9b200a8 기준) 로 superseded — 모두 흡수 대상
  외. 두 번째 round 만 흡수.
- **codex 재리뷰 면제**: 본 PATCH 는 CLAUDE.md C10.3 ("외부 리뷰 결과 반영
  PATCH 는 면제 — 무한 루프 방지") 에 해당.
- **연관**: LLM-AP-003 (mitigation 의 v0.4.0 가정 → v0.4.1 가드 승격),
  v0.4.0 (본 PATCH 가 흡수하는 변경), Phase 5 의 `source_collector_worker`
  (본 가드들을 활용할 첫 worker).

## 2026-05-22 v0.4.2 — 실 codex sandbox 검증 → known-limits 갱신

- **무엇을**: 사용자 머신 (Windows 11 + ChatGPT Plus + codex-cli 0.130.0) 에서
  v0.4.0-v0.4.1 mitigation 의 실 효과를 호출 단위로 검증. 결과를 ADDENDUM_04
  §5.2.1 (신설) 과 LLM-AP-003 known-limits (재구성) 에 반영. 코드 변경 없음.
- **왜**: 단위 테스트는 "우리 가드가 의도대로 호출되는가" 만 보장하고, 실
  codex 가 `--sandbox workspace-write` 를 어떻게 honor 하는지 / Windows 의
  junction 을 처리하는지 등은 호출해 봐야 알 수 있다. v0.4.0 의 LLM-AP-003
  본문이 "intent" 만 적었고 v0.4.1 이 "intent → guarded intent" 로 끌어올렸으면,
  v0.4.2 는 "guarded intent → verified guarantees" 로 한 단계 더.
- **어떻게**:
  - Stage 1 (실 codex 호출, 4 회):
    - 1a `workdir 안 write` → ✅ inside.txt 정상 생성.
    - 1b `Desktop write` → ✅ codex 가 명시적 거부 ("workspace-write,
      writable paths are limited to …, Desktop is outside").
    - 1b-multi `C:\tmp\sibling / %TEMP% / .codex/memories` 각각 시도:
      - `C:\tmp\sibling_outside.txt` → 🚫 차단 (UnauthorizedAccessException).
        codex header 의 `/tmp` 라벨은 Windows literal `C:\tmp` 가 **아니라**
        `%TEMP%` 의 OS-relative 라벨.
      - `%TEMP%\temp_outside.txt` → ⚠️ 자동 허용.
      - `~/.codex/memories\memory_test.txt` → ⚠️ 자동 허용.
    - 1c `junction escape` → ✅ codex 가 OS-level resolve 한 뒤 차단
      (`PermissionDenied`).
  - Stage 2 (Python 가드 단독, 컨테이너):
    - `_is_safe_path_segment` 11 케이스 모두 기대값.
    - `_scratch_dir_for_task` 멱등 / clean_scratch True ephemeral / False opt-out 정상.
    - `_build_invocation_cmd` argv: codex agent 에 `--sandbox workspace-write
      --cd <scratch>` 포함, claude response 에 sandbox 부재 + scratch 미생성.
    - `_assert_no_symlinks_in_path` POSIX symlink 검출.
    - placeholder fail-fast + response + `{scratch_dir}` raise + 본문 brace 허용
      모두 동작.
  - 결과를 ADDENDUM_04 §5.2.1 (신설) 에 검증 표 + 우리가 닫을 수 없는 영역의
    의미 (side channel) + codex CLI 의 한계 + 버전 종속성으로 정리. 동일 핵심을
    LLM-AP-003 known-limits 에 요약. 두 문서는 ADDENDUM_04 가 source 의 위상.
- **결과**:
  - `%TEMP%` 와 `~/.codex/memories` 두 곳이 codex CLI 의 디폴트로 우리가 닫을
    수 없는 side channel 임을 명시. prompt 측 / 운영 절차로 보강.
  - v0.4.1 의 `_assert_no_symlinks_in_path` preflight 가 codex 0.130.0 의
    OS-level junction 차단과 중복하지만 defense-in-depth 로 유지 결정 (다른
    codex 버전 / Linux/macOS / 다른 backend 대비).
  - codex CLI 의 `--help` 에서 `workspace-write` 영역을 좁히는 옵션 부재 확인.
    `-c sandbox_permissions=[...]` 는 확장 방향 (예: disk-full-read-access),
    `--dangerously-bypass-approvals-and-sandbox` 는 우회. 따라서 본 두 side
    channel 은 codex CLI 의 디폴트 가정.
- **codex 재리뷰 면제**: 본 PATCH 는 외부 검증 결과를 반영하는 문서/메타 변경
  으로 CLAUDE.md C10.3 의 정신 ("외부 리뷰 결과 반영 PATCH 는 codex 재리뷰
  면제") 과 동일. 코드 변경이 0 이라 정적/동적 회귀의 새 표면이 없다.
- **연관**: LLM-AP-003 (mitigation 의 "verified guarantees" 절 신설),
  v0.4.0/v0.4.1 (본 PATCH 가 검증한 변경), ADDENDUM_04 §5.2.1 (신설), Phase 5
  의 `source_collector_worker` (sandbox 가정을 활용할 첫 worker).

## 2026-05-22 v0.5.0 — Phase 5 첫 PATCH: SourceCollectorWorker 도입 (codex agent 모드)

- **무엇을**: v0.4.0–v0.4.2 의 LLM-AP-003 mitigation (codex `--sandbox workspace-write`
  + per-task scratch dir + path 가드 + side-channel known-limits) 위에서 실 호출하는
  첫 agent 모드 worker 를 도입. `workers/source_collector_worker.py` (BaseLLMWorker
  상속, `allow_agent_mode=True`, `response_model=SourceCollectionPartial`),
  `orchestrator/source_collection_planner.py` (SourceIntake → TaskQueueItem 순수
  빌더), `tests/test_source_collector_worker.py` (29 케이스). 신규만, 기존 동작
  변경 없음. VERSION 0.4.2 → 0.5.0.
- **왜**: Phase 5 의 목적은 `SourceIntake.user_decisions` 중 AI 위임 항목 (`ai_delegate`
  / `mixed(ai_delegate_remaining=True)`) 을 자동 자료 수집 task 로 변환하고 실행하는
  것. v0.4.x 까지는 sandbox 가드와 envelope 헬퍼만 마련했고 실제 호출자가 없었다.
  본 PATCH 는 그 첫 호출자다. 단일 PATCH 의 부담을 줄이기 위해 task_queue 영속화 /
  CLI / SourceRegistryBuilder / 실 codex e2e 는 후속 PATCH 로 분리.
- **어떻게**:
  - **worker**: codex agent mode + opt-in 가드 통과. system prompt 가 ADDENDUM_04
    §5.2.1 의 verified side channels (`%TEMP%`, `~/.codex/memories`) 접근 금지를
    명시. `build_user_prompt` 는 source_intake.json 의 매칭 UserDecision 의
    외부 자료 4 종 (user_note + provided_links + google_drive_links +
    uploaded_files) 을 `wrap_untrusted` 로 단일 envelope 격리. mode 화이트리스트
    {ai_delegate, mixed} 외 항목은 ValueError 로 거부 (worker 책임 밖).
    input_item_id 누락 / unknown item_id / 파일 부재 모두 명시적 raise.
    output_path = `02_sources/partials/{task_id}.json`.
  - **planner**: 순수 함수 모듈. `task_id = src_collect__{item_id}` (단일 path
    세그먼트, `_is_safe_path_segment` 통과 보장). `existing_task_ids` set 인자로
    재제출 idempotency. mixed-with-ai_delegate_remaining=False 와 direct_provide /
    skip / link_provide / file_upload / reference_only / must_use 는 모두 제외.
  - **테스트**: 7 클러스터. (1) system_prompt 가 SourceCollectionPartial /
    SourceEntry 필드 + 8 개 RightsStatus enum 값 + sandbox 경계 + envelope
    guidance 를 모두 포함하고 `.format()` 시 raise. (2) build_user_prompt 의
    happy path / envelope tag-injection 격리 / 6 가지 에러 분기. (3) output_path
    위치 고정. (4) run() 의 4 가지 parsed_status 분기 (stub backend). (5) agent
    opt-in 가드 통과. (6) `_build_invocation_cmd` argv 가 `--sandbox
    workspace-write` + `--cd {scratch_dir}` 를 포함하고 scratch dir 이 실제
    생성됨 + task_id 가 `_is_safe_path_segment` 통과. (7) 빌더의 mode 필터링 /
    task shape / existing_task_ids idempotency / empty intake / needs_collection
    helper.
- **결과**:
  - `python -m py_compile workers/source_collector_worker.py
    orchestrator/source_collection_planner.py
    tests/test_source_collector_worker.py` 통과.
  - `python -m unittest discover -s tests` = **129/129 통과** (기존 100 + 신규 29).
  - 본 commit 은 push 직후 codex 클라우드 외부 리뷰 대상. CLAUDE.md C10.1 의
    "MINOR 증분 직전 필수" 는 v0.4.0 → v0.4.1 의 패턴 (push → 외부 리뷰 → 흡수
    PATCH) 으로 해석. 결과 흡수는 v0.5.1 (PATCH).
- **연관**: LLM-AP-003 (resolved-partial → 본 worker 가 첫 실 호출자), SCHEMA
  (SourceCollectionPartial 의 input_item_id Optional 인 채 worker 단 강제 — 본
  PATCH 가 worker 단 ValueError 로 강제), `wrap_untrusted` (v0.3.3 부터 호출
  대기 → 본 PATCH 에서 첫 사용), `_scratch_dir_for_task` + `_is_safe_path_segment`
  + sandbox argv (v0.4.0–v0.4.1) — 본 PATCH 가 그 가드 위에서 동작.

## 2026-05-22 v0.5.1 — C10 외부 코드 리뷰 절차 갱신: push-then-review + 전달 형태 의무화

- **무엇을**: CLAUDE.md C10.0 / C10.1 / C10.2 와 docs/REVIEW_PROMPT.md §3 갱신.
  (1) MINOR/MAJOR 의 codex 리뷰 트리거 시점을 "commit + push 직후" 로 명문화하고,
  (2) codex 클라우드 (권장) / 로컬 codex CLI (폴백) 두 패턴을 docs/REVIEW_PROMPT.md
  §3.0 으로 분기 정리하고, (3) AI 어시스턴트가 review-prompt 본문을 SendUserFile
  단독으로 전달하는 것을 위반으로 명시 (inline 코드블록 동시 전달 의무화).
  VERSION 0.5.0 → 0.5.1.
- **왜**: v0.5.0 세션에서 실 사용 중 두 가지 사고가 드러났다.
  (1) AI 가 review-prompt.txt 를 SendUserFile 만으로 전달했고 사용자가 다운로드된
  파일을 어디서 열어야 할지 못 찾았다 — 사용자 답답함 폭발 + 세션 시간 손실.
  (2) "MINOR 증분 직전 codex 리뷰" 라는 표현이 codex 클라우드 (commit 된 브랜치를
  fetch 하는 방식) 와 본질적으로 충돌했다. codex 클라우드는 push 된 SHA 만 보므로
  "commit 전 리뷰" 는 불가능하다. v0.4.0 → v0.4.1 사례도 사실은 "commit + push
  후 리뷰 → 다음 PATCH 흡수" 패턴이었는데 규칙이 그 점을 명확히 안 박았다.
- **어떻게**:
  - C10.0 표의 AI 어시스턴트 책임을 (a)-(d) 4 항목으로 확장. push 의무 (b) 와
    SendUserFile + inline 코드블록 동시 전달 (c) 명시. 위반 사례로 "SendUserFile
    단독" 도 명문화 ("위반 사례 v0.5.0 세션 참고").
  - C10.0 표의 사용자 책임에 codex 클라우드 (권장) / 로컬 codex CLI (폴백) 선택
    명시. AI 가 사용자 머신 OS / CLI 설치 상태를 모르므로 둘 다 지원.
  - C10.1 트리거 표의 "MINOR / MAJOR 증분 직전" 행을 "MINOR / MAJOR commit +
    push 직후" 로 갱신. 비고에 v0.4.0 → v0.4.1, v0.5.0 → v0.5.1 패턴 박음.
    "본 C10 절차 자체를 도입/수정하는 PATCH" 행 신설 (C10.3 정합).
  - C10.2 절차를 5 → 6 단계로 재구성. 1번이 "commit + push", 2번이 "review-prompt
    전달 (SendUserFile + inline)", 3번이 "codex 클라우드 / 로컬 CLI 분기".
  - docs/REVIEW_PROMPT.md §3 위에 §3.0 codex 클라우드 절 신설. 두 패턴의 비교
    표 (codex 가 코드를 읽는 위치 / 전제) + 클라우드 패턴의 장단점 명시. 기존
    Windows cmd / Linux 절은 "로컬 codex CLI (폴백)" 으로 재라벨.
  - 두 문서의 YAML 헤더 last_synced_with v0.3.4 → v0.5.1.
- **결과**:
  - 본 PATCH 는 문서 변경만. 코드 / 스키마 / 테스트 영향 없음.
  - CLAUDE.md C10.3 에 따라 codex 재리뷰 면제 (본 절차 자체의 수정 PATCH).
  - 다음 MINOR/MAJOR commit (v0.5.2+ 또는 v0.6.0+) 부터 본 절차 적용.
- **연관**: v0.4.0 → v0.4.1 (본 패턴의 첫 사례, 당시는 규칙에 박혀있지 않음),
  v0.5.0 (본 PATCH 의 트리거 — push 직후 review-prompt 전달 실패 사고).
