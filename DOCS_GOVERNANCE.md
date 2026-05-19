<!--
tier: 1
last_synced_with: v0.2.1
ssot_for: [doc-governance, tier-system, change-propagation]
depends_on: [README.md, GOAL.md, CLAUDE.md]
last_review: 2026-05-19
-->

# DOCS_GOVERNANCE.md

본 저장소의 모든 마크다운 문서는 다음 거버넌스를 따릅니다.
참고 출처: `doroper98/agents_reviewer/DOCS_GOVERNANCE_V3.md`

---

## 1. 3-Tier 시스템

| Tier | 의미 | 위치 | 변경 빈도 | 책임자 |
|---|---|---|---|---|
| Tier 1 | Constitution (헌법) | repo root | 분기 1회 이하 | Owner |
| Tier 2 | Architecture (설계) | `docs/` | 릴리즈마다 | 개발 리드 |
| Tier 3 | Operational (운영) | `CHANGELOG`, `DEVLOG`, `WORKFLOWS`, `docs/ANTIPATTERNS/` | 매일 | 모든 기여자 |

### Tier 1 (필수)

- `README.md`: 진입점만, 사실 중복 금지
- `GOAL.md`: 최종 목표·합격 기준·금지사항 SSOT
- `CLAUDE.md`: AI 에이전트 / 개발자 작업 규칙
- `DOCS_GOVERNANCE.md`: 본 문서

### Tier 2 (필수)

- `docs/00_PROJECT_BRIEF.md` ~ `docs/16_TEST_PLAN.md` (v2 스펙 16종)
- `docs/ADDENDUM_01_ORCHESTRATOR_COMMAND_CENTER_LAYOUT.md`
- `docs/ADDENDUM_02_PRE_PRODUCTION_DEBUG_LAYER.md`
- `docs/ADDENDUM_03_TERMINOLOGY.md`
- `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, `docs/CATALOGS.md`, `docs/TESTING.md` (agents_reviewer 호환)

### Tier 3 (필수)

- `CHANGELOG.md`: 사용자 향 릴리즈 노트
- `DEVLOG.md`: 개발 로그, **append-only**
- `WORKFLOWS.md`: 실행 절차
- `docs/ANTIPATTERNS/*_ANTIPATTERNS.md`: 카테고리별 안티패턴, **append-only**

---

## 2. YAML 헤더 (모든 문서 필수)

```yaml
<!--
tier: 1|2|3
last_synced_with: vX.Y.Z
ssot_for: [topic-a, topic-b]
depends_on: [path/to/other.md]
last_review: YYYY-MM-DD
-->
```

- `tier`: 정수
- `last_synced_with`: 마지막으로 동기화된 코드 버전 (`orchestrator.__version__`)
- `ssot_for`: 이 문서가 단독으로 책임지는 주제 키워드
- `depends_on`: 본 문서가 참조하는 다른 문서 경로
- `last_review`: 마지막 리뷰 일자 (ISO 8601)

---

## 3. SSOT 원칙

> **같은 사실을 두 곳에 적지 않습니다. 한쪽은 링크가 됩니다.**

- 한 주제는 단 한 문서에만 살아 있는 정의를 둡니다.
- 다른 문서가 그 주제를 다룰 때는 SSOT 문서로 링크합니다.
- 사실 중복이 발견되면 PR 리뷰에서 즉시 단일화합니다.

---

## 4. Append-only 문서

다음 문서는 **과거 항목 수정 금지**입니다.

- `DEVLOG.md`
- `CHANGELOG.md` (released 항목)
- `docs/ANTIPATTERNS/*_ANTIPATTERNS.md`
- `projects/*/logs/approvals/approval_log.json`

수정이 필요한 항목은 **새 항목을 추가**하고, 과거 항목에는 `[superseded by ...]` 마킹만 남깁니다.

---

## 5. 변경 전파 매트릭스

| 트리거 | 동기화 대상 | 책임 |
|---|---|---|
| `orchestrator.__version__` 증분 | `README.md` 현재 상태표, 모든 Tier 1/2 YAML 헤더 `last_synced_with`, `CHANGELOG.md` | PR 작성자 |
| `schemas/models.py` 변경 | `docs/05_DATA_SCHEMA_SPEC.md`, `docs/DATA_MODELS.md` | PR 작성자 |
| 새 Worker 추가 | `docs/03_AGENT_ARCHITECTURE.md`, `docs/CATALOGS.md` | PR 작성자 |
| 새 Review Gate 추가 | `docs/12_QA_AND_REVIEW_SPEC.md`, `GOAL.md` G3 | PR 작성자 |
| 새 Antipattern 발견 | `docs/ANTIPATTERNS/{CAT}_ANTIPATTERNS.md`, `DEVLOG.md` 한 줄 | 발견자 |
| Phase 완료 | `README.md` 상태표, `CHANGELOG.md`, MINOR 버전 증분 | 리드 |

---

## 6. 절대 금지

1. 사실을 두 곳에 적기 → 한쪽은 링크
2. 버전 숫자 하드코딩 (코드의 `__version__` 또는 git tag만 참조)
3. `DEVLOG.md` 과거 항목 수정
4. `GOAL.md` 항목 삭제 (deprecated 마킹만)
5. 데이터 모델을 문서에 정의 (Pydantic 코드가 SSOT)
6. YAML 헤더 누락된 마크다운 머지

---

## 7. 신규 문서 추가 절차

1. `tier` 결정.
2. YAML 헤더 작성.
3. SSOT가 어디인지 명시 (`ssot_for`).
4. 의존 문서 명시 (`depends_on`).
5. 첫 줄 제목 = 파일명에 부합.
6. 신규 문서 추가는 `DEVLOG.md`에 기록.

본 거버넌스의 변경은 MAJOR 버전 증분과 함께만 가능합니다.
