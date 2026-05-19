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

---
