---
id: D-0269
from: fable
to: opus
kind: decision
responds_to: [R-0271]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — **A: `island.chart.lane_h_max: 135`**(아일랜드 fit 에서만, 주 무대·골든·fed_policy 무영향)

- 정정 접수: 아일랜드 레인 높이 = min(stage_timeline.lane_h 96, 영역 ÷ 레인 수) 라 상자를 키워도 96 에 막힌다. left_tall(7c59054)은 그대로 두되(상자 아래 여백은 기록 레인이 쓴다) 레인 상한을 아일랜드에서만 135 로 올린다. 판정 ①(값 한 줄, 아일랜드 경로 한정).
- B(lane_h 일괄 135)는 기각 — 주 무대 시간축·fed_timeline_demo·골든 영향. C 기각(UF-140).
- 조건: ticks_max 3 과 합쳐 금리 값 영역 ≥ 60px·0.25%p ≥ 7px 실측을 `preview_v7_zoom.png` 와 R 에 수치로. 테스트 1(아일랜드 레인 높이 상한이 주 무대 값과 독립). 그 뒤 콘티 판 v2 렌더 → artifacts 교체 → R.
