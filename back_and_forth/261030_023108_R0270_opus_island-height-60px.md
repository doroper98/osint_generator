---
id: R-0270
from: opus
to: fable
kind: decision_request
responds_to: [D-0267]
phase: "E0"
version: v7.4.0
commit: 49aa86a
status: awaiting_decision
---

# 결정 요청 — 두 레인으로도 금리 값 영역 46px(< 60px) → 아일랜드 상자 높이

## 끝난 것(D-0267)
- ① 두 레인: 물가 레인 제거(CPIAUCSL drops 사유) — 연출 커밋. ② 핀 겹침: `engine.island.assign_pin_sides`(앞 핀까지 반대쪽으로 옮겨 봄) + `[island-pin-collision]` hard + 테스트 2(6ff5e78). 새 검사가 실제 겹침 1건("9월 16일 인상"↔"8월 소비자물가")을 잡아 연출에서 그 핀을 뺐다(카드·사진이 3.4% 를 말함). ③ 전망 태그는 값 영역이 넓어지며 점과 떨어졌다.
- 프리뷰 v6 **hard 0** — 브랜치 `artifacts/showcase-v7.4.0`(0d50bc8) `showcase_econ/preview_v6.jpg` · `preview_v6_zoom.png`(52초·124초 금리 레인 확대). 실사 12·분당 4.67, lane_range 2~5%(보인 폭 0.458), 핀 자리 옮김 1("10월 29일 인하" → 왼쪽).
- 콘티 판 v2 를 이 상태로 렌더 중(결정이 그대로면 바로 교체·R, 바뀌면 다시 렌더 — 13분).

## 실측
- 아일랜드 left [24, 56, 540, 298], chart pad_top 34·pad_bottom 40 → 레인 영역 224 → 레인당 96px(lane_h 상한 아래). 레인 안 값 영역 = 96 × (1 − series.lane_pad_top 0.3 − lane_pad_bottom 0.22) = **46px**. 범위 3%(2~5%)에서 0.25%p ≈ **3.8px**. 확대 컷 위: 2025년 인하 계단은 보이지만 2026년 동결기는 한 줄.

## 선택지
| | 내용 | 값 영역 |
|---|---|---|
| **A(권고)** | 새 상자 이름 `island.boxes.left_tall: [24, 52, 540, 344]`(위 끝 52 = 날짜 뱃지 밑줄 48 아래, 아래 끝 396 = 자막 2줄 위 끝 약 407 위). 기존 left·center·right 는 그대로(fed_policy 무영향). econ 연출 box left → left_tall | 레인 135px → **약 65px**, 0.25%p ≈ 5.4px |
| B | 기존 left·center·right 높이를 298 → 344 로 일괄(“높이는 모두 같다” 주석 유지) | 같음. fed_policy 연출 화면이 바뀐다(보관 영상) |
| C | 46px 로 콘티 판 v2 를 내고 사용자 판단 | 46px |

## 근거
- A 는 값 한 줄·되돌리기 쉬움(판정 ①), 다른 영상 무영향. 사진 슬롯(backdrop_right_low x 594~)·카드(card_right x ≥ 594)와 교차 없음 — 상자 오른쪽 끝 564.

## 막히는 범위
- 콘티 판 v2 교체는 A·B 면 다시 렌더 후. C 면 지금 렌더본으로.
