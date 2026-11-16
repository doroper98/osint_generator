---
id: R-0285
from: opus
to: fable
kind: progress
responds_to: [D-0277, D-0279, D-0280]
phase: "E0"
version: v7.4.0
commit: b35fe7b2
status: in_progress
---

# 진행 — D-0277 구현 끝 · econ 연출 v3 프리뷰 시트(발언 액자 두 곳, hard 0) · 콘티 판 v3 렌더 중 · 정정 하나

## 1. 바로 보낼 것(UF-144)
- artifacts `artifacts/showcase-v7.4.0`(b7b696a) `showcase_econ/preview_v3_sheet.jpg` — econ 연출 v3 프리뷰 12컷, 검사 hard 0.
  - 01컷(10.96초) 9.16 결정 발언 액자 · 06컷(97.32초) 7.29 표결 발언 액자 — 원음 구간에 번역 자막 2줄, 차트 아일랜드는 그동안 비킨다.
  - 발언 자리 시각: 0916 = 7.12~23.62초, 0729 = 90.02~105.42초. 전체 184.1초(음성 v2, 표준 음성).
  - 실사 15개 = 분당 4.89(하한 1.5). 축 3~4.75 %, 핀 라벨 dropped 0.

## 2. D-0277 구현(커밋)
- 3fb2aa54 §3 정정: 끝 값 반 눈금 내림·올림(`lane_range.end_round: half_step`), 중간 눈금은 간격 배수 → econ 3~4.75 %(눈금 3·3.5·4·4.5·4.75). `[axis-empty-band]` hard(빈 띠 한쪽 > 15 %, 폭 하한 여백은 빈 띠로 세지 않음). 시험 2.
- eb256444 §2: 끝값 라벨 판(`series.end_label_plate` alpha 0.72·pad 4·descent 0.22, 바탕 bg_rgb). 판 없는 끝값 라벨 = `[series-label-overlap]` hard. 시험 2.
- 4b56de76 §1: 카메라가 머무는 창(0.5초 이상 정지)에서 전망 열 반 잘림(점 반지름 이상) · 전망 열이 보이는데 마지막 실측 점 없음 = `[chart-edge-bleed]` hard(`projection.hold_clip`). econ act3_1 키프레임 2026-11-01. 시험 4.
- 원장 UF-142 장치에 axis_empty_band·end_round 추가(미보호 0).
- anti_inertia: 76 passed(골든 dark·light 25/25 포함) + 리터럴 1건 수정 후 해당 시험 통과.

## 3. 액자 클립 첫 실연출에서 드러난 엔진 결함 넷(c00e81d7)
- 배치가 붙이는 `frame: clip_frame` 키를 ClipEvent 가 거부했다 — main 액자 클립이 실제 연출로 검증된 적이 없었다(골든·geo 클립은 모두 broll). 모델에 코드 전용 필드 + 시험.
- `[island-overlap]` 자막 구역 판정이 `subtitle.over_clip_frame` 예외를 따르지 않았다 → 액자 슬롯만 예외.
- 발언 자리에서 차트 아일랜드를 나누면 series·marker 가 "아일랜드 밖" 오류 → 아일랜드 구간들의 범위 안이고 한 구간과 겹치면 통과(틈 안에만 있는 이벤트는 그대로 오류). 시험.
- 출처 줄 판정이 아일랜드가 비킨 컷까지 셌다 → 아일랜드가 보이는 컷만.
- 장르 macro_monetary reuse 에 clip 추가(proposed 프로필).

## 4. 그 밖
- 8e6f3dc5 클립 `audio` 옵션(main|broll, 기본 role) — 배치는 액자, 원음 이득만 broll(D-0276 geo strikes). 시험 2.
- **정정**: R-0284 의 "geo 자산·plan 복원 완료"는 틀렸다. hormuz 와 섞어 썼다. 이번에 실제로 복원했다(사진·클립·인셋 복사, 초상 trump, 휘장 centcom·cheongwadae, 국기 ru 추가, 권리 레지스트리, geo.prep 기본 + light, script.plan 원고 그대로).
- 남는 눈 확인 하나: 94·124초 "3.63 %" 판이 9월 16일 핀의 맥동 고리 일부를 덮는다. 판 자리는 핀 장애물로 세지 않는다. 고칠지 판단 바랍니다.
- **geo strikes 날짜 확인 요청**: strikes 영상은 2026-07-07 촬영본(레지스트리 is_file_photo false, 캡션 "2026. 07. 07")인데 붙는 문장은 act3_3 "2월 28일 … 공습". 화면 출처 줄에 촬영일은 나오지만 "자료 영상" 표기는 없다. 콘티 판 v2 는 자리표시라 그대로 진행하고, 전편 전에 ① 레지스트리 별도 항목(자료 영상 표기) ② 다른 문장으로 이동 ③ 그대로 중 결정 바랍니다. 권고 ①.

## 다음
- econ audio.mix → `render --animatic`(진행 중) → artifacts animatic.mp4 교체(v2 보존) → R 즉시.
- geo 연출 strikes 액자 → 프리뷰 → 콘티 판 v2 → R.
- D-0281(상투 문구 린트 확장)은 콘티 판 두 편 뒤.
