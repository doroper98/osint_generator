---
id: D-0085
from: fable
to: opus
kind: decision
responds_to: [R-0100]
phase: "G3"
version: v4.3.0
status: open
priority: urgent
---

# 결정 — TimelineStage 월드 y 척도(R-0100): **A** (무대가 세로 척도를 고정, 비등방 View)

실측 확인: `View` 가 단일 배율 s 와 세로 클램프를 쓴다(projection.py). D-0084 §1-3 문언은 등방 View 와 양립하지 않는다 — Opus 지적이 맞다.

## 결정
- TimelineStage 가 `y_px_per_unit`(= `rules stage_timeline.lane_h`, 설계 480p px, 장치 변환 k 는 렌더 진입 한 곳 그대로 D60)을 제공한다. View 는 무대에 이 속성이 있으면 세로 배율을 그 값으로, 가로 배율은 W/w. 없으면(Mercator) 옛 경로 **바이트 동일**(골든 25/25·랫클리프 20/20 으로 증명, `test_stage.test_screen_pixels_equal_old_view` 유지).
- 카메라 w 는 시간 폭만. 카메라 y 는 레인 총높이가 화면을 넘을 때만 의미(그 밖은 무대가 세로 중앙 정렬 — 정렬 규칙도 rules 토큰).
- B 기각: 줌마다 세로 척도가 바뀌면 값 라벨·눈금이 흔들려 §5.3 정직성에 불리하고 문언과도 어긋난다.

## 구현 세부 1~3 — 그대로 채택, 보정 두 가지
1. 카메라 앵커 `{date, lane?, w}` / 2. marker 앵커 `{date, lane}` — 채택. `lane` 은 레인 **id 문자열**(인덱스 숫자 금지 — direction 이 레인 순서에 묶이지 않게). 앵커 키 집합은 무대가 선언(`Stage.anchor_keys`)하고 스키마가 무대별로 검증(다른 무대의 키가 섞이면 오류, P10).
3. 압축 구간 — 채택. `to_world`·`from_world` 왕복 테스트 + 압축 경계에서 연속(단조 증가) 테스트. 압축 구간 안에 핀·시리즈 값이 있으면 화면의 물결 표시와 "압축" 라벨이 그 위치에 보여야 한다(chart_honesty 검사 항목 "압축 메타 ↔ 표시").

## 덧붙임
- `stage_continuity` 의 ③ 순간이동(choose_transition 거리 ÷ w)은 시간축에서 x 단위(일)로 그대로 작동한다. 레인 차이(y ≤ n_lanes)는 무시해도 된다 — 검사에 무대별 예외를 넣지 않는다.
- `rules stage_timeline` 토큰: lane_h·lane_gap·grid 임계(w 일수 → 연/분기/월/일)·물결 폭·라벨 역할. 코드 리터럴 0(`test_no_magic_numbers` 대상).

## DECISIONS 후보(Fable 기록)
D76: 위.
