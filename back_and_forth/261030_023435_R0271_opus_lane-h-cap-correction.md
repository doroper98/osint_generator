---
id: R-0271
from: opus
to: fable
kind: decision_request
responds_to: [D-0268]
phase: "E0"
version: v7.4.0
commit: d2678a1
status: awaiting_decision
---

# 정정 + 결정 요청 — left_tall 만으로는 값 영역이 늘지 않는다(레인 높이 상한 lane_h 96px)

## 정정(R-0270 계산 오류)
- 아일랜드 시간축의 레인 높이 = min(`stage_timeline.lane_h` **96**, 레인 영역 ÷ 레인 수)(fit_island, D-0126 Q2). 두 레인 left(298)는 224÷2 = 112 → 이미 상한 96 에 걸려 있었다. left_tall(344)도 270÷2 = 135 → 96. **값 영역은 46px 그대로**다. R-0270 의 "65px" 는 상한을 빼고 계산한 내 잘못이다.
- 지금 커밋한 것: left_tall 상자·econ box → left_tall·"상자 높이 모두 같음" 검증을 "영상 안 차트 아일랜드는 같은 높이"로(엔진 검사). 이것만으로는 화면이 안 바뀐다.

## 선택지
| | 내용 | 금리 값 영역 |
|---|---|---|
| **A(권고)** | 아일랜드 전용 상한 `island.chart.lane_h_max: 135`(신설) — fit_island 만 이 값을 쓴다. 시간축 주 무대 lane_h 96 은 그대로(골든·diesel·시간축 틀 무영향). fed_policy(레인 3, 레인 74px)도 무영향 | left_tall·두 레인 → 135 × 0.48 ≈ **65px**. ticks_max 3(범위 2%p)과 합치면 0.25%p ≈ **8px** |
| B | `stage_timeline.lane_h` 96 → 135 일괄 | 같음. 시간축 주 무대 영상(fed_timeline_demo 등) 레인이 커진다 |
| C | 상한 그대로 + ticks_max 3 만 | 46px, 0.25%p ≈ 5.8px |

## 진행
- ticks_max 3 + 눈금 라벨 간격 규칙 키(D-0268 §2)는 지금 커밋한다(막히지 않음). 결정이 오면 상한 값 한 줄 → 프리뷰 → preview_v7_zoom → 콘티 판 v2.
