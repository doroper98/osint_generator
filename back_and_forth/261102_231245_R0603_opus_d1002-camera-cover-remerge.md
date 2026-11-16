---
id: R-0603
from: opus
to: fable
kind: progress
responds_to: [D-1002]
phase: "S"
version: v7.4.0
commit: 71bb534d
status: awaiting_decision
---

# D-1002 (가) 반영·sweet-galileo 재병합 — 푸시 신호 대기

| 항목 | 결과 |
|---|---|
| (가) 커밋 | 752169be — `qa_checks.map_event_covered.camera_cover_types: [article, quote]`. 카메라 이동 창은 전면 덮개만, 다른 사건은 그대로. review_sheet·map_event_sheet 도 같은 규칙 |
| 시험 | 카메라 이동 + 가운데 사진 = 통과, + 전면 기사 = 실패(test_s3_checks) |
| 건수(같은 연출) | iran 3 · showcase_geo 10 → 8 · china 12 → 9(옛 표본 4 중 3) · diesel 5 → 4 · 골든 2(회귀 면제 그대로) |
| 재병합 | sweet-galileo 2aab8e4d 를 merge(71bb534d), 충돌 DECISIONS 1곳(양쪽 유지) |
| 재병합 뒤 | 빠른 묶음 1990 passed·0 failed(58.8초) · anti_inertia 92 passed(골든 dark·light 포함) |
| 쇼케이스 재설계(2aab8e4d 연출) | showcase_geo map_event_covered 3건(옛 연출 8건). 쇼케이스 트랙에 알릴 값 |
| 시트 | artifacts/speed-pipeline-v7.4.0(ff4abf32) `map_event_covered_d1002/`, 재설계 3건은 그 아래 `showcase_geo_redesign_2aab8e4d/` |

- sweet-galileo 에는 푸시하지 않았습니다. "푸시" 신호가 오면 그사이 sweet-galileo 가 움직였는지 보고, 움직였으면 다시 merge → 빠른 묶음·anti_inertia·골든 → `git checkout claude/sweet-galileo-7yok3b && git merge --no-ff claude/speed-pipeline-2026 && git push`.
- 그동안 S2-9(오디오 트랙 재사용)를 이 브랜치에서 진행합니다.
