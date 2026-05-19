<!--
tier: 3
last_synced_with: v0.1.0
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

---
