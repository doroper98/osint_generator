<!--
tier: 1
last_synced_with: v0.1.3
ssot_for: [session-handoff]
depends_on: [CLAUDE.md, GOAL.md, VERSION, docs/13_IMPLEMENTATION_ROADMAP.md]
last_review: 2026-05-19
-->

# HANDOFF — 다음 세션 AI 인계 문서

본 문서는 **다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 문서**입니다.
짧고 행동 지향적으로 유지합니다. 과거 항목은 `DEVLOG.md` 가, 미래 항목은 `docs/13_IMPLEMENTATION_ROADMAP.md` 가 정식 SSOT 입니다.

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

## 1. 지금 어디까지 와 있나 (v0.1.3 기준)

### 완료된 Phase

| Phase | 버전 | 무엇 | 검증 |
|---|---|---|---|
| Phase 0: Governance | v0.1.0 | 저장소 구조, CLAUDE.md, GOAL.md, 16개 docs, 3개 ADDENDUM, Antipatterns, .githooks | commit-msg hook 통과 |
| Phase 1: Command Center MVP | v0.1.0 | Textual TUI (좌상단 Orch CLI Log, 좌하단 Job Dashboard, 우측 Worker Slot 1–4), WorkerSlotManager, dummy worker × 4 종료 코드 모두 검증 | `python -m py_compile`, smoke test, 6 tasks 병렬 실행 |
| 호스팅 / 인증 | v0.1.1 | Vercel 정적 호스팅 셋업, PAT 인증 다이얼로그, default branch `main` 통합 | 사용자 측 Vercel 연결 완료 |
| 호스팅 hotfix | v0.1.2 | Vercel 루트 URL 404 수정 (`docs/index.html` 추가) | 사용자 측 재배포 확인 |
| 브랜치 뷰어 그래프화 | v0.1.3 | `@gitgraph/js` 라이브러리로 진짜 git 토폴로지 SVG 그래프 렌더링 | 사용자 시각 확인 |

### 핵심 산출물

- 라이브 사이트: <https://osint-generator.vercel.app/> (PAT 필요, Private 저장소)
- TUI 진입: `python -m orchestrator.main command-center --project demo` 또는 `run_pipeline.bat`
- 더미 워커 directory: `workers/dummy_worker.py`

### 인프라 상태

- **default branch**: `main` (모든 푸시는 여기로)
- **Vercel**: `main` 푸시마다 자동 재배포. `osint-generator.vercel.app` 안정 도메인.
- **GitHub**: doroper98/osint_generator, Private. PAT 인증으로 브랜치 뷰어 접근.

### 알려진 antipattern 카탈로그

- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md` — TTS-AP-001 ~ TTS-AP-053
- `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` — PIPELINE-AP-001 ~ PIPELINE-AP-006

**문제 발생 시 반드시 이 카탈로그를 먼저 검색.** 중복 발견 시 동일 번호에 `[superseded by ...]` 마킹만, 새로 발견 시 다음 번호로 append.

---

## 2. 다음 작업 — Phase 2 (v0.2.0 예상)

### 목표: Project Manager / State Machine

사용자가 새 영상 프로젝트를 시작하고 중단/재개할 수 있는 상태 머신을 구현한다.

**Roadmap 출처**: `docs/13_IMPLEMENTATION_ROADMAP.md` Phase 2 절을 정식 SSOT 로 따른다.
**아키텍처 SSOT**: `docs/02_SYSTEM_ARCHITECTURE.md`, `docs/03_AGENT_ARCHITECTURE.md`.
**스키마 SSOT**: `docs/05_DATA_SCHEMA_SPEC.md`, `schemas/models.py`.

### 구체 작업 단위 (Phase 2 후보)

1. `orchestrator/project_manager.py` 신설.
   - `new_project(name) -> ProjectManifest`
   - `resume_project(name) -> ProjectManifest`
   - `transition_state(project, next_state) -> ProjectManifest`
2. `schemas/project_manifest.py` 의 `ProjectManifest` Pydantic v2 모델 확정.
   - `state` enum: `draft / intake / planning / collecting / scripting / rendering / qa / done / failed / paused`
   - `state_history` (append-only)
   - `current_phase`, `current_workers`, `output_refs`
3. CLI 명령 추가: `python -m orchestrator.main new-project <name>`, `... resume <name>`.
4. `projects/{name}/project_manifest.json` 디스크 영속화.
5. 상태 전이 시 검증 (불가능한 전이는 거부, `SCHEMA-AP` 카탈로그에 추가).
6. TUI 의 Job Dashboard 와 연동: 현재 프로젝트 / 상태 표시.

### Phase 2 의 종료 조건 (DoD)

- [ ] 사용자가 `new-project demo2` 하면 `projects/demo2/project_manifest.json` 이 `state: "draft"` 로 생성됨.
- [ ] 중단 후 `resume demo2` 하면 마지막 상태에서 이어짐.
- [ ] 잘못된 상태 전이는 `ValueError` + 명확한 메시지.
- [ ] `python -m py_compile` 통과.
- [ ] 모든 Tier 1·2 마크다운 `last_synced_with` 갱신.
- [ ] `CHANGELOG.md` `[v0.2.0]` 절 추가, `DEVLOG.md` 엔트리 추가.

### Phase 2 이후 (Phase 3 예고)

`docs/13_IMPLEMENTATION_ROADMAP.md` 의 Phase 3 절 참조. 대략:
- Intake Worker (사용자 입력 → 토픽 수집 계획)
- Source Collector Worker (X / Telegram / 기사 영상 수집, `rights_status` 필수)
- Source Verifier Worker (`<미검증>` 라벨 결정)

---

## 3. 작업 시작 전 체크리스트

다음 세션이 첫 번째로 실행할 일 (순서 중요):

1. **읽기**: `CLAUDE.md` → `GOAL.md` → `VERSION` (현재 `0.1.3`) → 본 `HANDOFF.md` → `docs/13_IMPLEMENTATION_ROADMAP.md` → 가장 최근 `DEVLOG.md` 엔트리 3 개.
2. **상태 확인**:
   ```bash
   git status                       # clean 인지
   git log --oneline -10            # 최근 커밋
   cat VERSION                       # 현재 버전
   python -m py_compile orchestrator/*.py workers/*.py schemas/*.py
   ```
3. **사용자 의도 확인**: "Phase 2 시작?" 또는 "그 외 작업?" 한 줄 질문.
4. **작업 진행**: 항상 작은 단위 커밋, 한 커밋 = 한 의도.

---

## 4. 자주 까먹는 규칙 (Reminder)

- ✅ 모든 커밋 첫 줄: `vX.Y.Z: {summary}` (영문 prefix + 한글/영문 요약 가능).
- ✅ 버전 증분 시: `VERSION` 한 줄 + 30 개 마크다운 `last_synced_with` 일괄 갱신 (`sed -i`).
- ✅ `orchestrator/__version__` 은 VERSION 을 동적으로 읽으므로 별도 편집 불필요.
- ✅ Worker subprocess 는 stdout 1 줄 1 이벤트, `task_result.json` 필수 종료.
- ✅ Worker `_finalize_slot` 종료 후 slot 은 즉시 idle 환원 (PIPELINE-AP-006).
- ✅ JSON 산출물은 `schema_version` 필드 필수.
- ✅ 도메인 데이터는 Pydantic v2 BaseModel 만 사용. raw dict 금지.
- ✅ 시스템 프롬프트 포맷팅은 `.replace()` (`format()` 은 JSON `{}` 와 충돌).
- ✅ 새 브랜치 만들면 `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에 **한국어** 설명 한 줄 추가.

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

마지막 갱신: v0.1.3, 2026-05-19.
