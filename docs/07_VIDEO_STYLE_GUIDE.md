<!--
tier: 2
last_synced_with: v5.13.0
ssot_for: [video-style-guide-index]
depends_on: [docs/handoff/05_CAMERA_SHOTS_TRANSITIONS.md, docs/handoff/06_OVERLAYS_AND_DATA_LAYERS.md, docs/handoff/08_PANELS_AND_CARDS.md, docs/handoff/09_TYPOGRAPHY_HUD_SUBTITLES.md, docs/handoff/14_MEDIA_PHOTO_VIDEO.md, docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md, rules/video_rules.yaml, CLAUDE.md]
last_review: 2026-09-29
-->

# 07 — 영상 스타일 가이드 (v4.0.0 재작성)

이 문서는 **영상 문법의 안내도**다. 무엇을 어디서 정하는지만 적는다.
구체 기준의 정본은 `docs/handoff/`(05·06·08·09·14·17)이고, 수치의 정본은 `rules/video_rules.yaml`이다.
이 문서는 수치를 복사하지 않는다. 값이 필요하면 아래 `rules:키`를 연다(15 P3, DOCS_GOVERNANCE §3).

기준 작품은 v3『호르무즈와 한국』이다. 골든 프레임 25장은 `docs/handoff/golden/`, 동작 원본은 `docs/handoff/reference_code/v3_hormuz_korea/`.
옛 판(쇼츠 콜라주·HyperFrames·Remotion 문법, v0.45.1)은 v2.0.0에서 폐기됐다. 보존본은 `archive/hyperframes-briefing` 브랜치다.

---

## 1. 화면 구성 원칙

| 원칙 | 규칙 키 | 정본 |
|---|---|---|
| 장면 수·길이는 원고가 정한다. 고정 막·섹션=장면 1:1 금지(G4-13) | `rules:script_schema.scene_count`, `rules:script_schema.duration_limit_sec` | handoff 02 §2.1, 03 §1.1 |
| 모서리에는 **날짜 배지만** 둔다 | `rules:hud.allowed_corner_elements`, `rules:hud.date_badge` | handoff 09 §5 |
| 도장·비네팅·브랜드·섹션 번호·섹션 제목·스크러버 금지 | `rules:hud.forbidden_components` | handoff 09 §5·§8 |
| 설계 좌표는 한 벌(854×480). 다른 해상도는 렌더 진입 장치 변환 한 곳에서 키운다(D60) | `rules:layout_480p.base`, `config:engine.output` | [10 렌더 파이프라인](10_RENDERING_PIPELINE_SPEC.md) §4 |
| 장면 구성·연출은 LLM+사용자, 렌더 수치·검증·권리는 코드(15 P8) | `rules:registries` | handoff 17 §2 |

## 2. 카메라 문법

카메라는 문장마다 움직이지 않는다. 장면당 이동 수와 숏 최소 유지 시간이 정해져 있다.
줌 범프(튀어 오르는 줌)는 쓰지 않는다. 멀리 이동할 때만 암전 컷(dip)을 쓴다.

| 항목 | 규칙 키 | 정본 |
|---|---|---|
| 장면당 이동 상한·숏 최소 유지 | `rules:shot_grammar.camera_moves_per_scene_max`, `rules:shot_grammar.shot_min_hold_sec` | handoff 05 §2 |
| 이동 길이·선행 시간 | `rules:shot_grammar.move_dur_sec`, `rules:shot_grammar.move_lead_sec` | handoff 05 §1.1 |
| 줌 범프 금지 | `rules:shot_grammar.zoom_bump` | handoff 05 §1.2 |
| 드리프트·엔딩 풀백 | `rules:shot_grammar.drift`, `rules:shot_grammar.ending_pullback` | handoff 05 §1.1 |
| 암전 길이·빈도·최대 불투명도 | `rules:shot_grammar.dip_total_sec`, `rules:shot_grammar.dip_max_per_sec`, `rules:shot_grammar.dip_alpha_peak` | handoff 05 §3 |
| 이동 대신 암전으로 넘어가는 거리·배율 | `rules:shot_grammar.auto_transition` | handoff 05 §7-2 |
| 용도별 화면 폭(w) 안내 | `rules:shot_grammar.w_guide` | handoff 05 §2.2 |
| 자동 프레이밍(frame_points)·맥락 폭 하한(D54) | `rules:camera.framing`, `rules:camera.framing.context_w_min` | handoff 05 §7 |

카메라 제안(`engine/camera_suggest.py`)은 **보조**다. 연출가가 쓴 숏을 코드가 옛 모양으로 되돌리지 않는다(15 P8).

## 3. 지도 위 요소

마커·경로·호·봉쇄선·선박 입자·국가 강조는 handoff 06이 정본이다. 관계선은 **하나씩, 정돈되게** 등장한다(G4-17).
라벨 밀도와 LOD는 [09 지도·지오](09_MAP_AND_GEO_SPEC.md) §4를 본다.

## 4. 패널·카드·뱃지·미디어

| 요소 | 규칙 키 | 정본 |
|---|---|---|
| 패널 종류 레지스트리(없는 종류 = 오류, P10) | `rules:registries.panel_kinds` | handoff 08 §1~§8 |
| 패널 공통 기하(가림막·제목·부제·화면 사용률) | `rules:layout_480p.panel`, `rules:panels` | handoff 08 §2 |
| 관계 패널·연표·차트 | `rules:panels.relation`, `rules:panels.timeline`, `rules:panels.charts` | handoff 08 §3·§5·§8 |
| 추정 태그 위치(제목 아래, D37) | `rules:panels.prov_tag` | handoff 08 §9 |
| 카드(우측 슬라이드)·예약 영역 | `rules:layout_480p.card`, `rules:layout_480p.reserved_zones`, `rules:panels.reserved` | handoff 08 §10 |
| 기사 카드·게시물(post) 카드 | `rules:layout_480p.article_card`, `rules:layout_480p.post_card` | handoff 14 §9, 18 §5 |
| 뱃지(인물·국기·휘장) 크기·등장 | `rules:layout_480p.badge`, `rules:registries.badge_kinds` | handoff 07 |
| 사진·영상·컷아웃 비트 | `rules:media_beats`, `rules:media.density` | handoff 14 §4·§10 |
| 미디어 배치 슬롯(좌표는 코드, LLM 은 슬롯 이름만) | `rules:placement.slots`, `rules:placement.auto_media` | handoff 17 §2 |
| 이벤트 타입 레지스트리 | `rules:registries.event_types` | handoff 17 §2 |

미디어는 권리 레지스트리에 있어야 그려진다. 자료사진·자료 영상 표기와 출처 줄은 빠지면 오류다(`rules:media_beats.file_photo_label_required`, `rules:media_beats.caption_credit_required`).
사실 장면을 AI로 생성하지 않는다(`rules:media_beats.ai_generated_forbidden`). 사상자를 식별할 수 있는 장면은 쓰지 않는다(`rules:media_beats.casualty_identifiable_forbidden`).

## 5. 타이포·자막·색

| 항목 | 규칙 키 | 정본 |
|---|---|---|
| 글꼴 스택 | `rules:fonts` | handoff 09 §1 |
| 자막 크기·위치·강조색 | `rules:layout_480p.subtitle` | handoff 09 §4 |
| 자막 줄 수·줄바꿈 폭 | `rules:script_schema.subtitle_max_lines`, `rules:script_schema.subtitle_wrap_px_480p` | handoff 09 §4 |
| 화면 글자 크기 전수 표(v4.8.0 D-0113 — 본문 ≥ 12·메타 ≥ 9, 자막 21) | `rules:layout_480p.subtitle`, `rules:layout_480p.card`, `rules:layout_480p.media_caption`, `rules:panels` | handoff 09 §9 |
| 최소 글자(설계 px) · 예외 역할(D62) | `rules:layout_480p.min_font_px`, `rules:qa_checks.glyph_size_exempt` | handoff 09 §2 |
| 타이틀 카드·엔딩 카드 | `rules:layout_480p.title_card`, `rules:layout_480p.end_card` | handoff 09 §6 |
| 페이드 | `rules:layout_480p.fade` | handoff 09 §8 |
| 색 토큰 | `rules:colors` | handoff 09 §7 |

## 6. 검증 라벨

문장 검증 라벨은 코드가 `intake/claims.json` status로 계산한다(15 P8). 문구는 `rules:script_schema.labels`다.
**v4.5.0(사용자 결정 D85, C9)부터 라벨은 영상 본문(자막·패널·카드)에 그리지 않는다.** 기록(claims·`script_labels.json`·provenance)만 남긴다.
`<미검증>`은 확인되지 않은 주장, `<논쟁>`은 양측 주장이 맞서는 사안이다. 논쟁 사안은 양측을 같은 무게로 다룬다(C0 경계).
한 문장이 여러 claim을 인용하면 `rules:script_schema.label_strength_order` 앞쪽(가장 약한 것)이 라벨이 된다.
화면에는 엔딩 카드 맨 마지막 줄에 가장 작은 글씨 한 줄(`rules:layout_480p.end_card.notice_unverified`, 라벨 문장 수 n, n = 0 이면 없음)만 쓴다.
미검증 주장을 인용하는 문장의 귀속 표현은 `rules:script_schema.attribution_markers`.

## 7. 되돌리면 안 되는 것

사용자 합격 판정이 끝난 목록이다. 정본은 [CLAUDE.md](../CLAUDE.md) C0과 `docs/handoff/KICKOFF_PROMPT.md` §5다.
고정 막 구성, 모서리의 브랜드·섹션 표기, 도장, 비네팅, 문장마다 카메라 이동, 줌 범프, 한꺼번에 튀어나오는 관계선,
AI 상투 문구(`rules:banned_phrases`), 발음 텍스트 안의 숫자·기호(`rules:tts_rules.forbidden_chars_regex`).

## 8. 프리뷰 결정적 검사 (18항목)

프리뷰(`python -m engine.render <proj> --preview …`)는 `prev/checks.json`을 만든다. hard가 하나라도 있으면 시각 검수 LLM을 부르지 않는다.
구현은 `engine/checks.py`(`HARD`·`WARN`), 임계는 `rules:qa_checks`. 판정 흐름은 [12 QA·검수](12_QA_AND_REVIEW_SPEC.md) §2.

| id | 등급 | 무엇을 보나 | 규칙 키 |
|---|---|---|---|
| overlap | hard | 사진·영상 상자 × 카드·자막·날짜 예약 영역, 카드 × 날짜·자막, 카드에 가린 마커 라벨(D61) | `rules:layout_480p.reserved_zones`, `rules:qa_checks.label_hidden_max_ratio` |
| offscreen | hard | 뱃지 상자(머리·이름표 포함)가 화면 밖 | `rules:qa_checks.offscreen_clip` |
| glyphs | hard | 그릴 글자가 프로젝트 글꼴에 있음 | `rules:qa_checks.missing_glyphs` |
| glyph_size | hard | 그린 글자 크기 ≥ 최소 글자(예외 역할 제외, D62) | `rules:layout_480p.min_font_px`, `rules:qa_checks.glyph_size_exempt` |
| labels | hard | 프레임당 도시 라벨 수 | `rules:qa_checks.labels_per_frame_max` |
| date | hard | 문장 날짜 형식 | `rules:script_schema.date_formats` |
| subtitles | hard | 자막 줄 수 | `rules:qa_checks.subtitle_lines_max` |
| rights | hard | 권리 점검 통과 | `rules:qa_checks.rights_missing`, `rules:credits` |
| forbidden | hard | 레지스트리 밖 이벤트·비네팅·모서리 요소 | `rules:qa_checks.forbidden_components`, `rules:hud.forbidden_components` |
| stage_continuity | hard | 무대 연속성(v4.1.0) — 보조 무대 수, 무대 전환은 암전 컷만, 같은 무대 안 먼 cut 금지, 전환 횟수 | `rules:stage`, `rules:shot_grammar.auto_transition` |
| genre_elements | hard | 장르 요소(v4.2.0) — 연출이 쓴 이벤트·패널·뱃지·프리미티브 종류가 장르 프로필(`genres/<genre>.yaml`) reuse ∪ new 안 | `rules:registries` |
| chart_honesty | hard | 차트 정직성(v4.3.0, handoff 20 §5.3) — 막대 0 기준선·압축 구간 ↔ 물결 라벨·%/%p·이중 축 라벨·색·로그 척도 표기 | `rules:qa_checks.chart_targets` |
| series_limit_3 | hard | 한 차트(레인·패널)의 계열 수 | `rules:qa_checks.series_max` |
| units_visible | hard | 화면 단위 표시(레인 이름·패널 단위·통화 기호) | `rules:data.units`, `rules:data.unit_prefixes` |
| as_of_visible | hard | 기준 시점·출처 줄(시리즈는 그 컷에 그린 출처 줄, 패널은 추정 태그 체계) | `rules:qa_checks.chart_targets` |
| shots | warning | 숏 유지·장면당 이동·암전 빈도·시간축 되돌아가기(이유 없는 경우) | `rules:shot_grammar` |
| media_beats | warning | 미디어 밀도 | `rules:media.density` |
| media_upscaled | warning | 원본 폭 < 장치 폭(추측 보간 금지, 알리기만) | `config:engine.output` |
