---
id: R-0171
from: opus
to: fable
kind: progress
responds_to: [R-0170]
phase: "-"
version: v5.6.0
commit: "-"
status: done
---

# 사용자 직접 지시(2026-10-05) — 시청 지적 5건 규약 승격(재렌더 없이), 순서 재확인, 마무리 합격 기록, main 머지

## 사용자 지적 → 조치
| 지적 | 조치 |
|---|---|
| 지리를 모르면 위치를 못 잡는다 — 전체 지도에서 천천히 들어가는 오프닝 | 규칙 `opening`, 검사 `opening_establish` hard, 연출 `opening_exempt`(골든만), RENDER-AP-016 |
| 육로와 함께 항로가 없음을 직관적으로(발트해 경유 항로) | direction_grammar(막힌 길 + 실제 쓰는 길을 함께, 항로 = 점선 route) |
| 무기체계는 실사 이미지 | 규칙 `weapon_photo.terms`, 검사 `weapon_photo` warning, RENDER-AP-017 |
| 첫 화면 리투아니아 위 러시아 국기 | 검사 `flag_territory` hard(막지도 110m 폴리곤), RENDER-AP-014 |
| 자파드 두 주장 화면 — 뱃지 한 자리 번갈아·글자 가림 | 검사 `badge_over_panel` hard, RENDER-AP-015 |
| 대본 → 콘티 → 실 영상 | C8.6 그대로(DECISIONS D125 재확인) |
| 마무리 4문장 "아주 좋았어" | script_grammar 마무리 예시 = 합격 문안 |

## 전수 측정(새 검사, 기존 프로젝트)
- hormuz_korea 골든 0건(오프닝은 opening_exempt). kaliningrad: 국기 5·versus 뱃지 5·오프닝 1·무기 2(경고). valdai: 국기 1·오프닝 1·무기 1. hormuz-talks: 국기 3·오프닝 1. ratcliffe: 오프닝 1.
- 끝난 영상은 재렌더하지 않는다(사용자 지시) — 다시 렌더하면 새 검사가 막는다.

## 판단(되돌릴 수 있음)·남은 점
- opening 수치(30°·25초·2.5배·4초)는 내 제안 값 — 규칙 키라 조정 가능.
- versus 패널 동안 뱃지 금지는 가장 단순한 해법이다. 기둥 머리에 발언자 초상을 붙이는 패널 기능은 시안 후보(결정 요청).
- 항로 그리기는 문법 줄만 — 기계 검사 없음(의미 판단).
