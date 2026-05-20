<!--
tier: 3
last_synced_with: v0.2.0
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

## 2026-05-20 v0.2.0 — Phase 2: Project Manager / State Machine

- **무엇을**: `ProjectManifest` 의 생성·재진입·상태 전이를 책임지는 Project Manager 와, 24-state 전이표를 강제하는 State Machine 을 추가. CLI `new-project / resume / transition` 서브커맨드 도입.
- **왜**: Phase 3 (Dynamic Intake) 이후로는 모든 산출물이 "어떤 프로젝트의 어느 상태에서 만든 것인가"라는 좌표 위에 놓여야 한다. 그 좌표계가 없으면 후속 Worker 들이 자기 산출물을 어디에 둘지·다음 누구를 깨울지 정할 수 없다. 그래서 본 Phase 가 Phase 1(실행 인프라) 와 Phase 3+ (도메인 작업) 사이의 단단한 뼈대로 들어가야 했다.
- **어떻게**:
  - `schemas/models.py` 에 `StateHistoryEntry` 를 추가하고 `ProjectManifest.state_history` (append-only) 를 도입. additive 변경이라 `schema_version` 은 1 유지.
  - `orchestrator/state_machine.py`: `docs/02 §4` 의 24-state 선형 흐름을 `_LINEAR_ORDER` 로 코드화하고, 어디서든 `ARCHIVED` 도달을 허용. `validate_transition` 은 동일 상태 self-loop 도 거부. 표에 없는 전이는 `InvalidTransitionError`(`ValueError` 하위) 와 함께 "현 상태에서 허용된 다음 상태" 목록을 반환해 호출자가 즉시 알 수 있게 함.
  - `orchestrator/project_manager.py`: 디스크 SSOT 책임자. `save_manifest` 는 `tmp → replace` atomic write. `new_project` 는 manifest 작성과 동시에 `03_tasks/`, `03_tasks/task_results/`, `logs/workers/` 표준 폴더를 보장 (command_center 와 일치).
  - `orchestrator/main.py` 에서 `command-center` 의존성(`textual`) 을 함수 안으로 내려 비-TUI CLI 가 textual 없이도 동작하도록 함. (사용자가 서버/CI 환경에서 `new-project` 만 빠르게 돌릴 수 있다.)
  - `orchestrator/command_center.py` 는 더 이상 inline `json.loads` 로 `current_state` 만 빼오지 않고 `resume_project` 를 호출해 전체 매니페스트를 SSOT 로 적재. 매니페스트가 없으면 진입 거부.
  - 기존 `projects/demo/` 에 manifest 마이그레이션 1회 (Phase 1 더미 프로젝트, category=`geopolitics`).
  - smoke test 로 9개 시나리오 검증: 생성·중복 거부·재개·정상 전이·점프 거부·self-loop 거부·ARCHIVED 도달·미존재 프로젝트 거부·history 영속화 (3 entries).
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - CLI 종단 테스트: `new-project _clitest --category economy` → `resume` → `transition --to intake_planning` → 잘못된 점프 `--to render_final` 시 exit=3 + 명확한 한국어 에러 메시지 + 허용된 다음 상태 안내.
  - DoD 6개 항목 모두 충족 (manifest 생성·재개·invalid transition ValueError·py_compile·last_synced_with 갱신·CHANGELOG/DEVLOG 엔트리).
- **연관**: 없음 (Phase 2 신규 작업, 카탈로그에 추가할 신규 antipattern 미발견).

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

---
