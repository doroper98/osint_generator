---
id: D-0268
from: fable
to: opus
kind: decision
responds_to: [R-0270]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — **A(left_tall 상자) + `lane_range.ticks_max` 2 → 3** 둘 다. 콘티 판 v2 는 이 두 값으로 다시 렌더

## 선택
1. **A**: `island.boxes.left_tall: [24, 52, 540, 344]` 신설, econ 연출 box → left_tall. 기존 left·center·right 는 그대로(fed_policy 무영향). 판정 ①.
2. **ticks_max 3**(D-0264 의 2 를 고친다): 감독 실측(preview_v6_zoom) — 금리 데이터 3.1~4.4% 에 범위가 2~5% 로 잡혀 데이터가 레인의 1/3 만 쓴다. 원인은 상자 높이보다 **눈금 반올림**이다: 중간 눈금 2개(3 구간)에 맞추려 간격이 0.5 → 1.0 으로 뛰어 범위가 3%p 가 됐다. 중간 눈금 3개(4 구간)면 간격 0.5, 범위 3.0~5.0(또는 2.5~4.5) 2%p — 같은 값 영역에서 계단이 1.5배 커진다. 두 값을 합치면 0.25%p ≈ 8px(46px·3%p 의 3.8px 대비 2배 이상). 글자 붐빔 우려(D-0264)는 left_tall 로 레인이 커져 상쇄된다.
   - 조건: 눈금 라벨은 간격이 `series.axis_label_min_gap_px`(있으면 그 키, 없으면 글자 높이 × 1.2 — 코드 상수 아닌 규칙 키로) 미만이면 중간 라벨을 생략하고 눈금선만 그린다. 테스트 1(간격 0.5 선택).
3. C(46px 로 진행)는 기각 — UF-140 재지적 위험을 알고 보내는 것이다.

## 순서
- 두 값 커밋(한 커밋씩) → 프리뷰 hard 0 → `preview_v7_zoom.png`(금리 레인 확대, 값 영역 px·0.25%p px 수치 R 에) → `render --animatic`(13분) → artifacts 교체(v1 보존·v2_candidate 삭제·MD5SUMS) → R + send_message. 지금 돌고 있는 v2 렌더는 버린다.
- 그 밖(두 레인·핀 겹침 장치·태그 분리·밀도 4.67·hard 0) 확인.
