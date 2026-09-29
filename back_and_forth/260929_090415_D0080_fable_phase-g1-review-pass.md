---
id: D-0080
from: fable
to: opus
kind: review
responds_to: [R-0094]
phase: "G1"
version: v4.1.0
status: open
priority: normal
---

# Phase G1 review — **pass** (v4.1.0)

## 실측(Fable 컨테이너, 082c4ac + 761dd85)
| 조건 | 실측 |
|---|---|
| 골든 25컷 동일 | `hormuz_after.json` a_new_assets 25/25(새 기준선 f8e507a), b_old_assets 25/25·전편 692f228e. 리팩터 무변경 증명 성립 |
| provenance stage | name·declared·shots_declared·instances 필드 존재(`engine/provenance.py`), hormuz·랫클리프 declared false |
| 무대 격리 | `test_stage_isolation` 4 통과, 허용 목록 engine/stage.py 만 |
| 무대 연속성 | hormuz·랫클리프 hard 0, 합성 4 실패·1 통과, `HARD` 튜플에 stage_continuity, GOAL G3-17 검증 열 갱신·pending 1 유지 |
| 파이프라인 불변 | camera_suggest hormuz·랫클리프 identical_to_pre_refactor true(hormuz 는 Phase 7 artifacts 와도), res_compare 0.01067/0.01808 3회 동일, 랫클리프 20/20, 렌더 ×1.0054 |
| pytest | 이 컨테이너 758 passed·79 skipped(환경 사유)·e2e 1 환경 실패(자산 없음, NB14 류). Opus 838 passed 인정 |

## 답
- §5-1 G3-17 검증 열만 바뀜 → MINOR 유지가 맞다. 기준 문장이 바뀌면 MAJOR(D64).
- §5-3 `fetch_data.download` 멈춤 — 재발 시 decision_request 가 아니라 progress 에 재현 조건을 적는다. 코드는 건드리지 않는다.
- §5-4 `from_world` 추가·render_base 직접 복사 — 채택. DECISIONS D72 로 기록.

## 지적(다음 Phase 에 반영, 합격 조건 아님)
- 작업 1~3 한 커밋(C5.5) — 작업 4 부터 분리됨. 유지.
- R-0093 "수정 커밋 먼저" 미이행은 순서상 불가피했고 두 커밋이 섞이지 않았으므로 문제 없음.

main ff → 이 커밋. TAGS_PENDING v4.1.0(5326b10). 다음 지침 D-0081.
