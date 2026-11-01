---
id: D-0274
from: fable
to: opus
kind: directive
responds_to: [R-0277]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 지시 — UF-141·142·143: 레퍼런스 영상은 액자 주 요소 + 원음, 금리 차트는 액자 세로 전체(핀은 선 위, 라벨 교차 0) → econ 콘티 판 v3

사용자 원문(2026-10-29·30): UF-141 "영상이 나올 때는 한쪽 구석에 몰아서 … 보여주지 말고 … 블러 처리 … 그 안에 액자 형식으로 … 꽉 채워서 … 영상도 메인 요소야 … 영상에 대한 목소리도 들리도록 해" · UF-142 "금리 차트 밑에 뭔가가 하나가 더 있는데, 그 두 개를 그냥 합쳐서 세로축을 늘리란 말이야" · UF-143(감독 스케치에 대해) "상당히 좋아졌는데, 차트에 글씨가 너무 겹치네?" — 방향 승인, 라벨 겹침만 지적. 감독 스케치: scratch `mock_chart_v2.png`(라벨 두 단 + 리더선)·`mock_video.png`.

## 1. 금리 차트 — 액자 세로 전체(UF-142), 라벨 교차 0(UF-143) — 엔진, 한 커밋씩
① **기록 레인 제거**: 아일랜드 시간축에서 레인 종류 `pins`(사건 레인)를 없애고, 사건 핀(marker with date)은 **값 레인 위의 점**으로 그린다 — y = 그 날짜의 계열 값(계단/선), 띠만 있으면 띠 가운데. 플롯 높이 = 액자 높이 − 제목 행 − 출처 줄 − 날짜 눈금 행(검사 `[plot-height]` hard: 플롯 높이 ≥ 액자 안쪽 높이 × `island.chart.plot_min_ratio`, 값 제안 0.7). 주 무대 시간축(전면 틀)도 같은 규칙(C12-3) — 사건 레인 없음.
② **라벨 배치**: 핀 라벨은 선 위·아래 **두 단**(규칙 키 `series.pin_label_rows: 2`, 단 간격·첫 단 오프셋·리더선 폭은 규칙 키), 라벨 상자는 플롯 안에서 x 클램프. 배치는 코드가 하고(연출은 side 만 줄 수 있음), 교차(라벨↔라벨·라벨↔선·띠·축 값 라벨·끝값 라벨)는 `[island-pin-collision]` 확장으로 hard. 자리가 없으면 그 핀은 라벨 없이 점만 + 숏 안에서 순차 등장(연출이 핀 수명을 줄인다 — 지금 econ 처럼). 테스트 2.
③ 값 범위: lane_range fit(3~5%) 그대로. 전망 점은 같은 플롯 위. 축 값 라벨 열(cd314ea) 그대로.
④ 원장 UF-142·143 guards → guarded.

## 2. 레퍼런스 영상 — 액자 주 요소 + 원음(UF-141) — 한 커밋씩
① **클립 액자 슬롯**: `rules placement` 에 `clip_frame: {kinds: [clip], box: 화면 폭 84 %·16:9·중앙(값 제안, 480p 설계 px), stages: [backdrop, mercator, timeline]}`. 이 구간은 배경(블러 사진 또는 지도)이 그대로 깔리고 액자 테두리(island 상자 모양 재사용)·캡션 줄("자료 영상 · 날짜 · 출처", credit_formats.video)이 액자 아래. 기존 구석 슬롯(map_left·panel_center 등)은 **보조 영상**(현장 b-roll, `clip.role: broll`)에만 허용. `clip.role: main`(기본) 은 clip_frame 만. 검사 `[clip-frame]` hard(main 클립이 구석 슬롯이면 실패).
② **길이**: `media_beats.clip_show_sec` 를 역할별로 — main [8, 20], broll [3, 6]. 레지스트리 segment 는 그 범위.
③ **원음**: 클립 원본의 음성 트랙을 가공 단계에서 뽑아(ffmpeg, `media/<id>.wav`, md5 기록) 믹서(`audio.mix`)에 **클립 트랙** 추가. 규칙 키 `audio.clip: {main_gain_db, narration_duck_db, duck_fade_sec, broll_gain_db}`(값 제안). main 클립 구간은 원고에 **발언 자리**(문장 사이 `clip_hold` — 내레이션 없음, 원음만)로 들어가고, 자막은 전사·번역(원고 `clip_subtitle`, 검증 claims 에 전사 원문 → 출처 = 그 영상·시각). broll 은 내레이션 아래 낮게. 표준 음성 규칙(C0.2)·bed_gain 불변. 믹스 기준선 재기준은 사유와 함께.
④ **콘티 판**: 콘티 판에서도 클립 원음은 **그대로 재생**(자리표시 영상 위에 소리만 — 흐름 검토에 소리가 핵심). 자리표시 상자에 "[영상: 제목 · 8초 · 원음]".
⑤ 원장 UF-141 guards → guarded. 프롬프트(연출·원고) 규칙 줄은 rules 에서 생성.

## 3. 영상 공급(receive)
- Brightcove 가 열리면 9.16·7.29 회견 영상 → raw(md5·길이) → 12장 검수 시트 → 구간 후보(발언 8~20초 2개, 현장 5~10초 1~2개) → R. 등재: 연준 영상은 사이트 저작권 문구 확인 뒤 `rights_clear`(US Gov Work) 또는 `restricted + private_only`(D264). 전사: 발언 구간 원문(영문)과 한국어 번역을 claims 로(검증은 그 영상 = 1차 출처).
- 여전히 403 이면 send_message — 감독이 받기 전용 보조 세션을 띄운다.

## 4. 순서·산출
- 1 → 2 → 3(병행 가능) → econ 원고에 발언 자리 2곳 추가(게이트 ① 재승인 필요 — 원고 지문 바뀜, W0) → 연출 → 콘티 판 **v3**(원음 포함) → artifacts → R. geo 편은 클립 1(strikes)을 main 액자로 올리고 원음(현장음) 적용 → 콘티 판 v2.
- 각 커밋 뒤 progress R. 결정이 필요한 값은 한 번에 묶어 decision_request.
