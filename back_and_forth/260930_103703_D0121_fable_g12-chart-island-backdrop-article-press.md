---
id: D-0121
from: fable
to: opus
kind: directive
responds_to: [D-0120]
phase: "G12"
version: v5.1.0
status: open
priority: normal
---

# G12(v5.1.0) 지침(확정, **D-0120 을 대체**) — 시간축 축 스케일 고정 · 차트 아일랜드 + 사진 배경 · 기사 프레스 규약 · 발음 사전 합성 직전 적용

**착수 = G11(v5.0.0) 합격 뒤.** 지금은 읽기만. 사용자 결정 D105·D106·D107(2026-09-30). D-0120 의 §1·§2 는 이 문서 §A·§D 로 옮겼고 fed 연출 재작성은 §E 로 한 번만 한다.

## 사용자 지시 원문 요지(2026-09-30)
- 차트가 주가 되는 주제(fed 금리)는 **차트를 전체 화면으로 띄우지 말고**, 미국·연준 건물 같은 이미지 몇 장을 **블러 배경**으로 깔고 **주제가 바뀔 때 전환**하며, 차트는 dmz 개념도처럼 **아일랜드 형태**로 띄운다.
- 기사는 **세리프 인용 서체**, 흰 바탕 검은 글씨 또는 검은 바탕 흰 글씨, **화면 중앙**. **공식 프레스 이미지를 먼저 보여주고 그 위에 약간 불투명하게 기사를 얹는** 규약.
- 참고 스크린샷(사용자 제공, 저장소에 넣지 않음): 어두운 프레스 사진 위 검정 반투명 덮개, 왼쪽 세로 굵은 선, 큰 세리프 영문 헤드라인 2줄에 “ ” 따옴표, 아래 작은 산세리프 한국어 번역 1줄, 그 아래 회색 "— Bloomberg, 2026.9.24". 텍스트 블록은 화면 세로 중앙·왼쪽 정렬(왼쪽 여백 약 11 %).

## §A 시간축 축 스케일 고정(D-0120 §1 그대로)
규칙 `stage_timeline.axis_scale` {`w_changes_per_video_max: 3`, `w_change_ratio_min: 1.5`, `scene_fixed: true`}, checks `timeline_rescale` **hard**(`[timeline-rescale] {at} w {a}→{b} ({이유})`, 지도 무대 제외), provenance `timeline.w_changes[]`, `direction_grammar` 한 줄 + 프롬프트 `{{RULES.stage_timeline.axis_scale}}`("시간축 무대는 축 스케일을 장면 단위로 고정. 확대·축소는 영상당 3회 이하, 그 밖은 pan. G4-16 과 같은 원리"). 테스트 ≥ 5.

## §B 차트 아일랜드 + 사진 배경(D106)
- 규칙 `stage_timeline.island`: 설계 px(480p) `box: [x, y, w, h]` = 가운데, 폭 ≈ 78 %·높이 ≈ 62 %(레인 영역 area_top/bottom 을 상자 안으로 재계산), `radius 10`, `fill_rgb` = 현 bg_rgb, `fill_alpha 0.78`, `edge_alpha 0.18`, `shadow`. 레인·축·눈금·핀·series·band·missing_mark 는 **전부 상자 안**에서 그린다(클립). 카메라·축 로직은 그대로(상자 = 뷰포트).
- 규칙 `stage_timeline.backdrop`: `kind: photo`, `blur_px 18`, `dim 0.55`, `desaturate 0.3`, `crossfade_sec 1.2`, `change_on: scene`(주제 전환), `min_photos 3`, `max_photos 6`. 사진은 **미디어 레지스트리의 권리 기록이 있는 실사진만**(연준 Flickr 8/9/10, 백악관 퍼블릭 도메인 등 — `media.flickr` 경로 재사용, C9). AI 생성·출처 불명 금지(G4-10). 배경은 장식이라 캡션 바 없음, 크레딧은 `media` 절 자동("배경 사진").
- 새 이벤트 타입 `backdrop`(레지스트리 세 곳 동시: 스키마·렌더러·프리뷰 예제, P10) — `{type: backdrop, at: scene_start, img: <media id>}`. 연출 LLM 이 장면마다 고른다. 같은 사진 연속 금지, 전환은 crossfade 만(줌 범프 금지).
- 위치 규칙 재검증: `timeline_badge [640,186]`·`timeline_photo` 상자·카드 예약 영역이 아일랜드와 겹치지 않게(겹치면 규칙 값 이동 + expected_deltas 근거). 자막 구역 불변.
- 콘티 판: 아일랜드 = 같은 상자 윤곽 + 막차트, 배경 = `[배경: <id>]` 자리표시.
- 골든(hormuz·랫클리프)은 지도 무대 → 무변경. fed·데모 기준선은 의도 변경으로 재등록(시트 전/후).
- 테스트 ≥ 6(상자 클립·배경 권리 없음 = 오류·연속 같은 사진 오류·crossfade 만·콘티 자리표시·레지스트리 세 곳).

## §C 기사 프레스 규약(D107) — 기존 오른쪽 기사 카드 경로 **삭제**(P2), 새 규약으로 교체
- 규칙 `article_card` 를 v2 로 재작성: `theme: dark|light`(기본 dark; 연출이 고른다), `press_lead_sec 1.0`(프레스 사진 단독), `overlay_alpha 0.82`(dark: 검정, light: 흰색), `overlay_fade_sec 0.5`, 텍스트 블록 = 세로 중앙·왼쪽 정렬 `x_left_ratio 0.11`, `max_w_ratio 0.78`, `rule: {w 4, color, gap 18}`(왼쪽 세로 선 = 헤드라인 높이), `headline: {font: serif(Noto Serif CJK KR), size 30, gap 38, max_lines 3, quotes: true}`(원문 언어 그대로, 인용 상한 `verification.quote_max_chars`), `sub: {font: sans, size 15, gap 20, max_lines 2}`(한국어 번역·요지), `source: {font: sans, size 13, color muted, format "— {publisher}, {date}"}`, `hold_sec` = 문장 길이에 맞춤(현 규약 유지), 퇴장 = 덮개·글자 페이드.
- **프레스 이미지 = 미디어 레지스트리의 권리 기록 있는 공식 사진만**(기관 프레스·Flickr 허용 라이선스·기사 자체 사진은 권리 없음 → 사용 금지). 없으면 **현재 무대를 블러(18)·dim** 한 위에 같은 카드(사진을 지어내지 않는다, G4-10·P6 — provenance `article.press: none` 기록).
- 자막·수치는 코드 렌더(G4-10). 헤드라인은 원문 verbatim(권리: 제목 인용은 짧은 인용).
- 골든 hormuz 214–221초 코리아헤럴드 카드가 바뀐다 → expected_deltas `g12_article_d0121`(컷·이유). fed 2건도.
- 콘티 판: `[프레스: <id>]` + 카드 윤곽·헤드라인 텍스트.
- 테스트 ≥ 6(theme 2종·프레스 없음 폴백 = 블러 무대·권리 없음 오류·인용 상한·세리프 글꼴 요구(FontMissingError)·콘티).

## §D 발음 사전 합성 직전 적용(D-0120 §2 그대로, TTS-AP-067·068 구조 조치)
`script/plan.py` 합성 직전에 명시 `tts` 에도 사전 치환(멱등), 캐시 키는 치환 뒤 텍스트. 회귀 테스트 4(거부꿘·연방 공개시장 위원회·명시 tts 경로·멱등). hormuz·fed 해당 문장 캐시 키 변화(= 재합성 대상)를 보고에. 재합성은 §E 의 fed 480p 한 편에서만.

## §E 연출 재작성(LLM, W1.1 사람 루프 = Fable 검토) + 산출물
- **fed_policy**: `reopen --to direction` 로 LLM 재연출 — §A(w 변경 ≤ 3), §B(장면별 backdrop, 사진 3~6장 = 연준 Flickr/백악관 등 권리 기록 후 레지스트리 등재), §C(기사 2건 theme). 코드가 w·사진을 고치지 않는다(P8). **fed 480p 한 편** 렌더(§D 재합성 포함) → artifacts `phaseG12-v5.1.0`. checks hard 0, `[timeline-rescale]` 0.
- **hormuz**: 기사 이벤트만 §C 규약으로(프레스 사진은 권리 기록 있는 것이 있을 때만, 없으면 블러 무대 폴백). 전편 렌더 없음 — **기사 구간 30초 클립**(480p) 1개 + 프리뷰 시트.
- 데모(시간축): §A·§B 검사 통과(걸리면 연출 재작성).
- 시트: fed 전/후(아일랜드·배경), 기사 전/후(hormuz·fed).

## §F 공통
§0 VERSION 5.1.0(MINOR: 새 검사·새 이벤트 타입), 헤더, CHANGELOG. 한 커밋 한 의도(§A·§B·§C·§D·§E 따로). 문서: handoff 05(축 스케일)·08(아일랜드·기사 규약 v2)·14(배경·프레스 사진 권리)·03(사전 적용 시점)·07(크레딧), docs/12 검사 표, ANTIPATTERNS 상태 줄, DEVLOG. pytest failed 0. 결정이 필요하면 decision_request(특히: 아일랜드 안 레인 높이 재계산, 프레스 사진 후보 출처).
