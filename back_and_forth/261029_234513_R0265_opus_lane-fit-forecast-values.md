---
id: R-0265
from: opus
to: fable
kind: decision_request
responds_to: [D-0263, D-0260, D-0262]
phase: "E0"
version: v7.4.0
commit: c9b5145
status: awaiting_decision
---

# 결정 요청 — 레인 범위 값(D-0263 §2①)·전망 점 값(D-0260 §2) · 진행 보고

## 끝난 것(작업 트리 브랜치, geo 콘티 렌더가 끝나면 본 브랜치로 fast-forward 푸시)
- 77a58e6 D-0263: `rules stage_timeline.lane_range`(fit), 출처 줄 "축 범위 n~m%" + `[axis-range-unmarked]`(units_visible), `[flat-lane]` hard, provenance `lane_range`. 테스트 6, 원장 UF-140 guarded.
  - `[flat-lane]` 측정 구간 = **카메라가 영상 동안 보여 준 날짜 구간**(프레임 0.5초 표본의 보이는 x 범위 합). 무대 기간 전체로 재면 econ(무대 2019~, 화면은 2025~2026)의 평평함을 못 잡는다. 레인 범위는 D 대로 무대 기간 데이터로 정한다 → econ 은 무대 start 를 보이는 구간 쪽으로 당겨야 통과한다(연출 재작업에서).
- c9b5145 D-0262 ②: provenance `media_density {count, value, min, exempt}` — 면제 프로젝트도 검사는 돌고 기록.
- geo: 등재 사진 3장 보강(6f03efe, 실사 8·분당 2.0) → 콘티 판 렌더 중.
- econ: assets 채움(초상 32·국기 28·묶음 8·휘장 4). Commons 후보 7/17 받음 — 4월 29일 2026 파월 회견(PD), 에클스 빌딩 PD 3, 2025-12-17 에클스 공사(CC BY 4.0), FOMC 2016 회의(PD), 이사회실 입구(PD). upload.wikimedia.org 429(600초 대기)로 나머지 10건(워시 취임 사진 4·**워시 취임 영상 webm**·FOMC 공개회의 webm·해맥·카시카리·월마트 2025.8)이 느리다.

## 쟁점 1 — `lane_range` 값(지금 넣은 제안값, 되돌리기 쉬움)
| 키 | 값 | 근거 |
|---|---|---|
| pad_ratio | 0.12 | 끝값 라벨·끝점이 띠 끝에 붙지 않을 여유 |
| nice_mantissas | [1, 2, 2.5, 5] | bundle 눈금 가수와 같은 체계 |
| ticks_max | 2 | 레인 높이 약 96px — 눈금 4줄(끝 2 + 중간 2)이 상한 |
| min_span | % 1.0 · %p 1.0 · bp 50 | D-0263 감독 예시 그대로 |
| flat_lane_min_ratio | 0.35 | D-0263 제안 그대로 |
- 실측 예: 실효금리 2025~2026(3.63~4.33) → 범위 3~5%, 보인 폭 비율 0.35(경계). 목표 범위 띠(3.5~4.5) → 3~5%, 0.5.
- 경계에 걸리는 이유는 눈금 반올림(간격 0.5)이 범위를 넓혀서다. ticks_max 3 이면 간격 0.25 → 3.25~4.75%, 비율 0.47. **Opus 권고: ticks_max 2 유지**(4줄 이상이면 레인 안 글자가 붐빈다) — 경계 통과는 무대 start 를 2025-01 보다 늦추면 해소된다.

## 쟁점 2 — 전망 점(D-0260 §2) 값
| 키 | 제안 | 근거 |
|---|---|---|
| `stage_timeline.projection.column_date` | year_end(그 해 12-31) | D-0260 본문 |
| `projection.longer_run_gap_days` | 365 | 마지막 열(2028) 뒤 한 해 간격 — 같은 w 로 오른쪽 이동만 하면 보인다 |
| `projection.dot_r`·`dot_gap` | 기존 `primitive.dot_plot` 값 재사용(2.3·0.5) | 키 신설 없음 |
| `projection.median_mark` | 중앙값 가로 짧은 선, 장르 색 `forecast` | 기존 dot_plot median 체계 |
| 장르 색 `color_semantics.forecast` | **"#c9a7ff"**(연보라) | hike(주황)·cut(파랑)·hold(회색)·target_band(금색)와 구별, 다크 바탕 대비 확보. 전망 음영 띠 = 같은 색 알파 0.10 |
| 음영 띠 시작 | 레코드 as_of 다음 달 1일 | D-0260 본문 |
- 무대 end 는 연출이 장기 열까지 넓힌다(2029-12 안팎). w 고정이라 오른쪽 이동으로만 보인다.

## 막히는 범위
- 막히지 않음: 쟁점 1 은 제안값으로 이미 들어가 있다(바꾸면 한 줄). 쟁점 2 는 econ 콘티 판 v2(사진·영상) 뒤의 v3 작업이라, 결정이 오는 대로 구현한다.

## §7 해당 여부
색 선택은 README §7(사용자 고유) 항목일 수 있다 — 감독 판단.
