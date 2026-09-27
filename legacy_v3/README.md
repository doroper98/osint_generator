<!--
tier: 2
last_synced_with: v2.0.1
ssot_for: [legacy-v3-runner]
depends_on: [docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, docs/handoff/19a_V3_CODE_INVENTORY.md]
last_review: 2026-09-27
-->

# legacy_v3 — v3 참조 코드 실행본 (Phase 1 골든 재현 전용)

`docs/handoff/reference_code/v3_hormuz_korea/*.py`의 복사본이다. **경로 줄만** 환경변수로 바꿨다(19 §3.9).
나머지 코드는 한 글자도 바꾸지 않는다. 수치·로직 수정은 Phase 2의 `engine/`에서 한다.

| 환경변수 | 기본값 | 원본 경로 |
|---|---|---|
| `V3_ROOT` | `projects/hormuz_korea_legacy` | `/home/claude/v3` |
| (`V3_ROOT/data`) | — | `/home/claude/data` (prep3 `D`) |
| `OG_ROOT` | `.` (저장소 루트) | `/home/claude/og` |

- mix3 BGM 경로는 v2.0.0 이동을 반영해 `OG_ROOT/assets/audio/bgm/…`이다(원본 `…/hyperframes/briefing/assets/audio/bgm/…`).
- import 줄에 `os` 추가 2건(mix3, render3) — 환경변수를 읽기 위해서다.
- 실행 순서와 명령은 `docs/handoff/reports/PHASE1_RUNBOOK_WSL2.md`.
