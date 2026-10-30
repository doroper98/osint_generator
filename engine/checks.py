"""결정적 사전 검사 `prev/checks.json` (v3.1.0, docs/handoff/17 §3, back_and_forth D-0047 작업 6).

LLM 시각 검수 전에 코드가 잡는 것. 임계는 `rules qa_checks`(코드 상수 금지, 15 P3). 숏 규칙 값은 `rules shot_grammar`.
hard 실패가 하나라도 있으면 시각 검수 LLM 을 부르지 않고 연출 LLM 에 오류만 돌려준다(17 §3, AP-V5-29).

| id | 등급 | 방법 |
| overlap | hard | 사진·영상 상자가 카드·자막·날짜 예약 영역과 겹침, 카드·기사·게시물 카드가 날짜·자막 영역과 겹침(v3.6.0 NB23) (`media_plan.placement_warnings`). 뱃지·마커는 RESERVED 회피가 이미 처리 |
| overlap(label) | hard | 마커 라벨이 카드 영역 때문에 흐려진(알파 < 0.5) 시간 ÷ 마커 표시 시간 > label_hidden_max_ratio `[label-hidden-by-card]`(v3.6.0 D-0068 — 설계된 hide(D36)를 연출 LLM 이 오류로 받게) |
| glyph_size | hard | 프리뷰 컷에 그린 글자 크기(설계 px) < layout_480p.min_font_px(9.5), 역할(text role=)이 qa_checks.glyph_size_exempt 밖(v3.6.0 D-0069) |
| offscreen | hard | 뱃지 상자(badge_box — 머리·이름표 포함, 17 §3 R×3.3 의 실측판)가 보이는 순간마다 화면 안(전면 카드·패널·암전 구간 제외). v4.5.0(D-0098): 엔딩 카드 크레딧 두 열의 마지막 기준선 ≤ 하단 구분선 − end_card.bottom_margin `[endcard-overflow]` — v4.7.0(D-0106) 넘치면 롤, 롤 속도 > scroll_max_px_per_sec 일 때만 |
| glyphs | hard | 화면에 그릴 문자열(이벤트·자막·날짜·크레딧)의 모든 글자가 프로젝트 글꼴 중 하나에 있음(fontTools cmap) |
| shots | warning | 숏 길이 ≥ shot_min_hold_sec, 장면당 이동 ≤ camera_moves_per_scene_max, 암전 ≤ 1/dip_max_per_sec (Phase 7 제안의 바탕), 시간축 되돌아가기 `[timeline_backtrack]`(v4.3.0, reason 있으면 통과) |
| media_beats | warning | `media_plan.density_report` 경고(D38) + `media_plan.article_candidate_usage` `[article-unused]`·`[article-density]`(v5.19.0 D-0163 §2) |
| endcard_roll | warning | v4.7.0(D-0106): 엔딩 카드 크레딧이 한도를 넘어 롤(속도 ≤ end_card.scroll_max_px_per_sec) `[endcard-roll]`. 상한 초과는 offscreen `[endcard-overflow]` hard |
| media_upscaled | warning | 사진·영상·컷아웃 원본 픽셀 폭 < 출력 프로파일의 장치 폭(설계 폭 × k) — 추측 보간 금지, 알리기만(v3.6.0 D-0067 요건 3) |
| labels | hard | 샘플 시각마다 도시 라벨 수 ≤ labels_per_frame_max |
| date | hard | 문장 date 형식(YYYY / YYYY.MM / YYYY.MM.DD) — 날짜 배지는 이 값으로만 그린다 |
| subtitles | hard | 자막 줄 수 ≤ subtitle_lines_max(렌더러와 같은 wrap) |
| rights | hard | 권리 점검(load_project 의 check_credits·validate_media)이 통과했으면 0 |
| forbidden | hard | 도장·비네팅·모서리 브랜드: 레지스트리 밖 이벤트 타입 0, vignette 끔, 모서리 요소 = 날짜뿐. v4.5.0(D85): 프리뷰 컷에 그린 글자 중 검증 라벨 문구(`script_schema.labels`) 0 `[label-in-body]` |
| stage_continuity | hard | 무대 연속성(v4.1.0 D-0076·D-0077, GOAL G3-17): 보조 무대 ≤ stage.max_secondary, 무대 전환은 dip 만, 같은 무대 안 먼 cut 금지, 전환 ≤ stage.continuity.max_switches (`engine.shots.stage_continuity`) |
| camera_continuity | hard | 카메라 연속성(v5.21.9 D-0191 §1-1): `engine.camera.continuity` 1·2·3차 차분 ≤ rules sketch.checks(스케치 SK-C1 과 같은 식·임계), 컷 키 제외 |
| card_exposure | hard | 기사·인용 카드 완전 노출 ≥ qa_checks.card_full_exposure_min_sec(v5.21.10 D-0191 §1-2) — `article_full_span`·`quote_full_span`(그리기와 같은 구간) |
| route_label_cross | hard | 경로 선 ↔ 경로 이름표·마커 라벨/부제 글자 교차(v5.21.11 D-0191 §1-3·D-0192) — 이름표 자리는 렌더와 같은 `route_label_layout` |
| route_label_overlap | hard | 경로 이름표 ↔ 해역 이름·다른 이름표·뱃지·마커 겹침 또는 화면 밖(v5.21.11 D-0192·D-0199). 대비는 map_contrast(이름표 required) |
| article_backdrop | hard | 한 영상 기사 카드 theme 하나(v5.21.12 D-0193). 사진 없는 카드 블러 무대 밝기 상한은 그리기(`fallback_gain`, press_fallback.max_luma) |
| quote_in_script | hard | 인용(quote) text ⊂ 그 구간 문장 화면 원고(공백·문장부호 정규화, v5.21.13 D-0194) |
| route_missing · route_missing_other | hard · hard(v5.22.1 D-0205 — 둘 다 hard) | 이동·공격 동사(qa_checks.route_missing) + 문장이 부르는 마커 → 그 마커에 끝점이 닿는 경로가 문장 구간에 있어야 한다. 다른 경로만 보이면 hard(v5.21.14 D-0195·D-0197) |
| frame_missing · frame_missing_target | hard · hard(v5.22.1, 국기 뱃지 = 표시, 골든 story_geo_exempt) | 문장이 부르는 나라(라벨 점)·마커가 문장 구간 내내 화면 밖. 이동·공격 대상이면 hard(v5.21.14 D-0199) |
| battle_geo | warning | 전황 동사 문장에 지도 마커·경로 없음(v5.22.0 D-0200 UF-08) |
| bgm_decision | hard | 배경음악 없음은 sound.no_music_decision(결정 번호) 필수(v5.22.2 UF-16·30·93) |
| endcard_black | hard | 엔딩 카드 뒤~끝 프레임을 그려 평균 밝기 ≤ end_card.after_max_luma(v5.22.3 UF-35) |
| camera_per_sentence | hard | 연속 shot_grammar.max_consecutive_move_sentences 문장이 모두 카메라 이동 시작(v5.22.4 UF-19, C0) |
| label_jump | hard | 경로 이름표가 보이는 중에 자리를 옮김(한 프레임 사이 상대 위치 변화 > qa_checks.label_jump_px, v5.22.7 D209) — 자리는 `route_label_slots`(나타나는 순간 고정) |
| camera_speed | hard | 카메라 pan(화면 폭/초)·zoom(|d ln w/dt|) > rules shot_grammar.camera_speed(제목 카드 전 오프닝은 더 낮은 상한) — `engine.camera.speed`, 스케치 SK-C1 같은 함수(v6.0.2 UF-97·D-0216) |
| title_backdrop | hard | 제목 카드 직전 1초 장면 ≠ 제목 바탕(기사 카드·암전·지도) — 카드 → 지도 → 제목 깜박임(v6.0.2 UF-98·D-0216) |
| cutaway_churn | hard | 전면 컷어웨이(qa_checks.cutaway_full_types) 끝 → 지도 < shot_min_hold_sec → 다음 전면 컷어웨이 `[cutaway-churn]`(v7.4.0 UF-110·D-0229 §2.3) |
| unit_glyph_font | hard | display 글꼴로 그린 문자열에 라틴 소문자(단위 t 십자형) `[unit-glyph-font]` — 단위 꼬리는 rules fonts.unit_font(v7.4.0 UF-111·D-0229 §2.4) |
| ratio_graphic | warning | "N 척 중 M" 문장 구간에 dots·versus 패널·series 없음 `[ratio-without-graphic]`(v7.4.0 UF-113·D-0229 §2.6) |
| inset_overlap | warning | 위성 인셋(원+출처 줄)이 마커·경로 이름표·카드 자리·날짜와 겹침 `[inset-overlap]`(v7.4.0 UF-107·D-0229 §2.7) |
| tempo_density | warning | 1분 창 사실(귀속) 문장 > tempo.fact_sentences_per_min_max `[tempo-density]`(v7.4.0 UF-115·D-0229 §2.9, script.lint.tempo_density) |
| transition_camera | hard | 시점 전환(plan transitions) 호흡~bridge 문장 사이 카메라 이동 < transition.camera_move_min_sec `[transition-camera]`(v7.4.0 UF-105·D-0229 §2.2) |
| static_camera | hard | 20초 창 안에서 카메라가 멈추고 새 화면 요소도 없음 `[static-camera]`·drift 속도 초과 `[drift-too-fast]`(v7.4.0 D-0241 §1, UF-120) |
| route_speed | hard | 경로 grow 평균 속도 > rules route_speed.grow_speed_max_px_s `[route-too-fast]`(v7.4.0 D-0241 §4, UF-123) |
| sea_only_frame | hard | 지도 프레임 육지 비율 < rules camera.land_min_ratio `[sea-only-frame]`, 숏 allow_sea 사유 구간 예외(v7.4.0 D-0242, UF-125) |
| unit_ton_glyph | hard | 화면 문자열에 숫자 뒤 t `[unit-ton-glyph]` — ton 으로(v7.4.0 D-0241 §3, UF-122) |
| press_credit | hard | 기사 카드 press 가 공식 사진이면 자료사진 출처 줄 필수 `[press-credit-missing]`(v7.4.0 D-0240 §3) |
| inset_clipped | hard | 위성 인셋 원+출처 줄이 안전 영역(날짜 배지 아래·자막 띠 위) 밖 `[inset-clipped]` — side_order 대체 자리까지 모두 밖일 때(v7.4.0 D-0240 §2) |
| badge_clipped | hard | 지도 뱃지 원이 안전 영역(인셋과 같은 여백 — 화면 가장자리·자막 띠 위·날짜 배지 상자 밖) 밖 `[badge-clipped]` — 또는 위 가장자리 보정(edge_nudge)에 기대 붙음 — place_badge 뒤(v7.4.0 D-0244) |
| series_unused | hard | 주문 order.yaml data.series 의 시리즈를 그리는 패널이 없다 `[series-unused]` — direction drops(record·사유)만 예외(v7.4.0 D-0245·UF-126) |
| panel_dropped | hard | 이전 승인 연출(track_v*/direction.yaml)의 데이터 패널 레코드가 새 연출에 없다 `[panel-dropped]` — drops 사유만 예외(v7.4.0 D-0245·UF-126) |
| card_over_panel | hard | 패널이 페이드 뺀 구간에 떠 있는 동안 덮개(rules cover_types; 데이터 패널은 + cover_types_on_data_panels 사진·영상·컷아웃·뱃지)가 패널 상자를 덮는다(D-0249). 시간축 주 무대는 틀 안 시리즈 레인 상자도 데이터 패널로 센다(timeline_frame_cover_types, D-0259) `[card-over-panel]`(rules qa_checks.card_over_panel, v7.4.0 D-0248·UF-129) |
| media_density | hard | (photo+clip+cutout 이벤트) ÷ 영상 분 < rules media_beats.min_density_per_min(사유 통과 없음, 회귀 기준만 density_exempt_projects) `[media-density]`(v7.4.0 D-0261·UF-139) |
| flat_lane | hard | 시간축 레인: 카메라가 보여 준 날짜 구간 안 선·계단의 세로 폭 ÷ 레인 값 범위 < rules stage_timeline.lane_range.flat_lane_min_ratio `[flat-lane]`(v7.4.0 D-0263·UF-140) |
| article_outlet | hard | 기사 카드가 떠 있는 문장(겹침 ≥ outlet_min_overlap_sec)에 매체 이름이 나오는데 카드 매체(url 도메인·credit_author → rules qa_checks.outlet_names)가 다르다 `[article-outlet-mismatch]`(v7.4.0 D-0250·UF-130) |
| media_unused | hard | 프로젝트가 등재한 권리 통과 사진({pid}_ 접두 kind photo)이 연출 어디에도 없음 `[media-unused]` — media_notes drop 사유만 예외(v7.4.0 UF-118·D-0238) |
| badge_orphan | warning | 국기 뱃지가 카드·인용·마커에 붙지 않고 홀로 뜸 `[badge-orphan]`(v7.4.0 D-0240 §4) |
| article_press_missing | warning | 인물 발언·발표 문장 구간 기사 카드에 press 사진 없음 `[article-press-missing]`(v7.4.0 UF-109·D-0229 §6) |
| camera_bounds | hard | 요청 카메라가 무대 경계 밖이라 렌더 View 가 잘랐다 — 화면이 멈췄다가 이동 중간에 꺾임(지도·시간축·차트 아일랜드). camera_continuity·camera_speed 는 화면 궤적(`engine.camera.screen_track`)을 잰다(v7.1.0 UF-99·D-0220) |
| portrait_unused | warning | 인물 이름이 나오고 초상이 있는데 그 인물 뱃지·인용 없음(v5.22.0 D-0200 UF-10) |
| genre_elements | hard | 장르 요소(v4.2.0 D-0081 작업 3, GOAL G3-17): direction 이 쓴 이벤트·패널·뱃지·프리미티브 종류(genres.elements) ⊆ 장르 프로필 primitives.reuse ∪ new |
| chart_honesty | hard | 차트 정직성(v4.3.0 D-0084 작업 5·D-0087, 20 §5.3): 막대 0 기준선·압축 구간 ↔ 물결 라벨·%/%p·이중 축 라벨·색·로그 척도 표기 (`engine.honesty`) |
| series_limit_3 | hard | 한 차트(레인·패널)의 계열 ≤ qa_checks.series_max |
| units_visible | hard | 화면 단위(레인 이름·패널 unit·y_prefix) ∈ rules data.units·unit_prefixes |
| boundary_as_route | hard | v4.7.0(D-0107 D2(b), M8): rules geo.boundary_names 이름을 단 route 이벤트(label·{path:})·paths 키 `[boundary-as-route]` — 경계선은 지도 경계 레이어가 그린다 |
| geo_unsourced | warning | v4.7.0(D-0107 D2(b)): 지도 무대 places·paths·인라인 좌표 marker·route 가 지명 사전과 대조되지 않음 `[geo-unsourced]`(provenance geo.unsourced[]). v4.10.0: 사전(`data/gazetteer.yaml`)에 없는 이름·paths·route 만 |
| geo_mismatch | hard | v4.10.0(D-0116 B-1): place 키·그 place 를 쓰는 marker label·인라인 marker label 이 지명 사전과 맞는데 좌표가 맞은 항목 모두의 tol_km 밖 `[geo-mismatch]`(provenance geo.mismatch[]) — `geo.gazetteer` |
| static_window | warning | v4.11.0(D-0118 §1): 지도 무대(전면 카드·패널 덮개 밖)의 어떤 pacing.static_window.window_sec 창이든 change_kinds 변화(이벤트 등장 t0·카메라 키) < min_changes `[static-window] t0-t1 changes=n`(provenance pacing.static_windows[]). 표시된 범위에는 느린 푸시인(creep). `engine.pacing` |
| timeline_rescale | hard | v5.1.0(D-0121 §A): 시간축 무대 숏의 w 변화가 장면 안(scene_fixed)·영상당 > axis_scale.w_changes_per_video_max·비율 < w_change_ratio_min `[timeline-rescale] t w a→b (이유)`(provenance timeline.w_changes[]). 지도 무대 제외 `engine.shots` |
| backdrop_rights | hard | v5.1.0(D-0123 §3): backdrop 배경 사진이 미디어 레지스트리 kind photo·rights_clear·파일 있음이 아님 `[backdrop-rights]`(렌더 전 preflight 도 같은 게이트) `engine.layers.backdrop` |
| backdrop_repeat | hard | v5.1.0(D-0123 §3): 연속 두 배경이 같은 사진 `[backdrop-repeat]`, 서로 다른 사진 수가 stage_backdrop.min_photos~max_photos 밖 `[backdrop-photos]`(provenance backdrop.photos[]) |
| island_overlap | hard | v5.1.0(D-0126 Q3 A): backdrop 무대 아일랜드(차트 island·사진·영상·프리미티브·패널 상자) 제자리 상자끼리 같은 순간 교차 > 0, 자막 구역 교차, 동시 수 > island.max_concurrent `[island-overlap]` `engine.island` |
| backdrop_main_missing | hard | v5.2.0(D-0129 §B): backdrop 무대에서 주 아일랜드(island.main_kinds)가 하나도 보이지 않는 구간 > island.card_only_max_sec `[backdrop-main-missing] t0-t1 {n}s`(타이틀·엔딩 카드·기사 구간 제외, provenance backdrop.main_missing[]) `engine.island` |
| card_island | warning | v5.2.0(D-0129 §C): 카드·게시물 카드 제자리 상자와 같은 순간 보이는 아일랜드 상자 교차 > 0 `[card-island]`(provenance island.card_overlap[]) `engine.island` |
| island_label_clip | hard | v5.2.0(D-0133 §2): 차트 아일랜드 안 마커 라벨 글자 상자가 반전·클램프(island.chart.label_flip_pad, `markers.island_label`) 뒤에도 아일랜드 상자 밖 `[island-label-clip]`(provenance island.label_clip[]) `engine.island.label_check` |
| axis_empty_band | hard | 시간축 레인 축 범위 중 데이터 극값(실측 + 전망 점) 밖 빈 띠(한쪽) > rules stage_timeline.lane_range.empty_band_max_ratio `[axis-empty-band]`(v7.4.0 D-0277 §3·UF-142) |
| clip_date_mismatch | hard | 사진·영상 촬영일 ↔ 붙은 문장 날짜 차 ≥ rules media.file_clip_date_gap_days 인데 자료 표기(is_file_photo) 없음 `[clip-date-mismatch]`(v7.4.0 D-0283 §1) |
| inset_jump | hard | 위성 인셋 원 중심 프레임 간 이동 > rules flight.inset.jump_px_max `[inset-jump]`(v7.4.0 D-0300·UF-146) |
| inset_side_change | warning | 위성 인셋 자리 옮김 횟수(보간) `[inset-side-change]`(v7.4.0 D-0300) |
| clip_frame | hard | 레퍼런스 영상(clip.role main)이 액자 슬롯 clip_frame 밖, 또는 보이는 길이가 rules media_beats.clip_show_sec[role] 밖 `[clip-frame]`(v7.4.0 D-0274 §2·UF-141) |
| plot_height | hard | 시간축 주 무대 틀·차트 아일랜드: 값 레인 세로 합 < 액자 안쪽 높이 × rules island.chart.plot_min_ratio `[plot-height]`(v7.4.0 D-0274 §1①·UF-142) |
| island_pin_collision | hard | v7.4.0(D-0267 §2 → D-0274 §1②): 값 레인 위 핀 라벨(engine.pin_labels 단 배정) ↔ 핀 라벨·점·계열 선·띠·축 값·끝값·플롯 경계 교차 `[island-pin-collision]` |
| island_label_overlap | warning | v5.2.0(D-0133 §3): 차트 아일랜드 안 마커 라벨 글자 상자 ∩ 같은 순간 시리즈 출처 줄 글자 상자 > 0 `[island-label-overlap]`(provenance island.label_overlap[]) — 고치는 것은 연출 회차 |
| cascade | hard | v5.2.0 겹침 카드(v5.3.0 D-0139 채택): `[cascade-width]`·`[cascade-back]`·`[cascade-date]`·`[cascade-overflow]`, 문장 지명(마커·at_place·경로·봉쇄선 이름표)이 카드 밑 `[cascade-label-under]`(D-0137 §2) |
| cascade_label_hidden | warning | v5.3.0(D-0139 §3): 배경 지명(gazetteer·해역)이 겹침 카드 회피로 안 그려지거나 깔림 `[cascade-label-hidden]`(provenance cascade.hidden_labels[]) |
| subtitle_overlap | hard | v5.3.1(사용자 지적 2026-10-02): 뱃지(이름표·역할 포함)·마커(부제 포함)·인용 상자 ∩ 그 순간 실제 자막 글자 상자(줄 수·폭) > 0 `[subtitle-overlap]` |
| stage_choice | warning | v5.1.0(D-0123 §2): 주 무대 ≠ 장르 기본 무대(default_stage = 장르 프로필 stage.primary)인데 direction stage_reason 없음 `[stage-choice]` |
| as_of_visible | hard | 기준 시점·출처 줄 — 시리즈는 프리뷰 컷에 그린 출처 줄, 패널은 08 §9 출처 체계. 적용 범위 = qa_checks.chart_targets(축 종류) |
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from typing import Callable

import cairo
import numpy as np

from engine.layers.media import KEN_BURNS_MAX
from engine.media_plan import article_candidate_usage, density_report, placement_warnings
from engine.projection import View
from engine.style import FONT, FPS, H_OUT, ISLAND, TIMELINE, W_OUT
from engine.typography import FontMissingError, family_found, fc_match, require_family
from rules import load_rules
from script.schema import DATE_RE

R_ = load_rules()
QA = R_.qa_checks
SG = R_.shot_grammar
SAMPLE_SEC = 1.0          # 뱃지·라벨 샘플 간격
SHADOW_PX = 7             # badge_box 가 원 둘레에 더하는 그림자 여백 — 이만큼 잘리는 것은 허용
HARD = ("map_contrast", "overlap", "offscreen", "glyphs", "glyph_size", "labels", "date", "subtitles", "rights", "forbidden", "stage_continuity",
        "genre_elements", "chart_honesty", "series_limit_3", "units_visible", "as_of_visible", "boundary_as_route",
        "geo_mismatch", "timeline_rescale", "backdrop_rights", "backdrop_repeat", "island_overlap",
        "backdrop_main_missing", "island_label_clip", "cascade", "subtitle_overlap", "label_collision", "timeline_span", "route_frame", "panel_overflow", "flag_territory", "badge_over_panel", "opening_establish", "camera_continuity", "card_exposure", "route_label_cross", "route_label_overlap", "article_backdrop", "quote_in_script", "route_missing_other", "frame_missing_target", "route_missing", "frame_missing", "bgm_decision", "endcard_black", "camera_per_sentence", "label_jump", "camera_speed", "title_backdrop", "camera_bounds", "cutaway_churn", "unit_glyph_font", "transition_camera", "media_unused", "inset_clipped", "press_credit", "static_camera", "route_speed", "sea_only_frame", "unit_ton_glyph", "badge_clipped", "series_unused", "panel_dropped", "card_over_panel", "article_outlet", "catalog_label_overlap", "chart_only_run", "chart_world_split", "series_label_overlap", "chart_edge_bleed", "media_density", "flat_lane", "island_pin_collision", "plot_height", "clip_frame", "axis_empty_band", "clip_date_mismatch", "inset_jump")   # cutaway_churn v7.4.0 D-0229 §2.3, island_label_clip v5.2.0 D-0133 §2, backdrop_main_missing v5.2.0 D-0129 §B, island_overlap v5.1.0 D-0126 Q3, geo_mismatch v4.10.0 D-0116, timeline_rescale v5.1.0 D-0121 §A, backdrop_* v5.1.0 D-0123
WARN = ("shots", "media_beats", "media_upscaled", "endcard_roll", "geo_unsourced",   # endcard_roll v4.7.0 D-0106, geo_unsourced D-0107
        "static_window", "stage_choice", "card_island", "island_label_overlap", "cascade_label_hidden",
        "map_contrast_shape", "battle_geo", "portrait_unused", "ratio_graphic", "inset_overlap", "tempo_density", "article_press_missing", "badge_orphan", "inset_side_change")   # ratio_graphic v7.4.0 D-0229 §2.6   # v5.21.14 D-0195·D-0199. map_contrast_shape v5.18.0 D-0161 §4   # static_window v4.11.0 D-0118, stage_choice v5.1.0 D-0123, card_island v5.2.0 D-0129 §C, island_label_overlap D-0133 §3


def missing_fonts() -> list[str]:
    """`FONT` 표의 패밀리 중 fontconfig 가 그 이름으로 찾지 못하는(대체 글꼴로 넘어가는) 것. 없으면 `fetch_data fonts`."""
    return [fam for fam, _ in FONT.values() if not family_found(fam)]


@lru_cache(maxsize=None)
def _cmap(family: str) -> frozenset[int]:
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    require_family(family)   # 조용한 대체 금지(P6) — 대체 글꼴 cmap 으로 검사하면 전부 '글리프 없음'
    path = fc_match(family)[1]
    f = TTFont(path, fontNumber=0, lazy=True)
    return frozenset(f.getBestCmap() or {})


def _strings(v: object) -> list[str]:
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for k, x in v.items() if k not in ("type", "kind", "mid", "pid", "flag", "img", "accent", "col", "side",
                                                     "style", "group", "id", "src_id", "dst", "src", "at", "place") for s in _strings(x)]
    if isinstance(v, (list, tuple)):
        return [s for x in v for s in _strings(x)]
    return []


def check_glyphs(P) -> list[str]:  # noqa: ANN001, N803
    have = frozenset().union(*(_cmap(fam) for fam, _ in FONT.values()))
    texts: list[str] = [s.text for s in P.plan.sentences] + [P.plan.title, P.plan.subtitle, P.plan.date]
    for e in P.events:
        texts += _strings(e)
    miss: dict[str, str] = {}
    for s in texts:
        for ch in s:
            if not ch.isspace() and ord(ch) not in have and ch not in miss:
                miss[ch] = s[:40]
    out = [f"글리프 없음 {ch!r} U+{ord(ch):04X} — {ctx}" for ch, ctx in miss.items()]
    seen: set[tuple[str, str]] = set()
    for lab, name, ch, ctx in (getattr(getattr(P, "R", None), "cache", None) or {}).get("glyph_miss", []):   # v4.4.0 — 프리뷰 컷에서 그 글꼴에 없는 글자(실제 그린 글꼴 기준)
        if (name, ch) not in seen:
            seen.add((name, ch))
            out.append(f"글리프 없음(글꼴 {name}) {ch!r} U+{ord(ch):04X} — {lab} {ctx!r}")
    return out


def _covered(P, t: float) -> bool:  # noqa: ANN001, N803
    """지도가 가려진 순간 — 전면 카드(타이틀·엔딩)·패널·암전. 이때 지도 요소 위치는 화면에 보이지 않는다."""
    if P.R.tb.in_fullcard(t):
        return True
    return any(e["type"] in ("panel", "dip") and e["t0"] <= t <= e["t1"] for e in P.events)


CASCADE_STEP_SEC = 0.1   # 겹침 카드 샘플 간격(물러남 0.5·밀기 0.6초를 놓치지 않게)


def check_cascade(P) -> list[str]:  # noqa: ANN001, N803
    """v5.2.0 겹침 카드(cascade, 사용자 재구성 2026-10-01, v5.3.0 D-0139 채택) — 전체 폭 ≤ width_cap, 뒤 카드 ≤ max_back,
    모서리 날짜 상자와 교차 0, 글자 넘침 0, **문장 지명**(지금 보이는 마커·at_place·경로·봉쇄선 이름표)이 카드 밑에 깔리는 순간 0(hard, D-0137 §2).
    배경 지명(gazetteer)이 회피로 안 그려지거나 해역 이름이 깔리는 것은 warning(`check_cascade_label_hidden`). 문제마다 처음 시각 한 줄."""
    from engine.cascade import back_count, cascade_boxes, cascade_width, check_text  # noqa: PLC0415
    from engine.hud import date_box  # noqa: PLC0415
    from engine.style import CASCADE  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    db = date_box()
    for e in P.events:
        if e["type"] != "cascade":
            continue
        out += check_text(ctx, e)
        seen: set[str] = set()
        t = e["t0"]
        while t <= e["t1"]:
            boxes = cascade_boxes(t, e)
            w = cascade_width(t, e)
            if w > CASCADE.width_cap and "w" not in seen:
                seen.add("w")
                out.append(f"[cascade-width] t={t:.2f} 겹침 카드 폭 {w:.0f}px > width_cap {CASCADE.width_cap:.0f}")
            c = back_count(t, e)
            if c > CASCADE.max_back and "c" not in seen:
                seen.add("c")
                out.append(f"[cascade-back] t={t:.2f} 뒤 카드 {c}개 > max_back {CASCADE.max_back}")
            if any(_box_hit(b, db) for b in boxes) and "d" not in seen:
                seen.add("d")
                out.append(f"[cascade-date] t={t:.2f} 겹침 카드가 모서리 날짜 상자와 겹침")
            t += CASCADE_STEP_SEC
    return out + cascade_label_report(P)["under"]


SUB_STEP_SEC = 0.25   # 자막 겹침 표본 간격
SUB_TOL_PX = 2.0      # 자막 겹침 허용 — 경계 접촉(≤ 2px)은 겹침이 아니다(글자 상자는 근사, offscreen 의 SHADOW_PX 와 같은 취지)


def _overlap_px(a: tuple, b: tuple) -> float:
    return min(min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1]))


def check_subtitle_overlap(P) -> list[str]:  # noqa: ANN001, N803
    """v5.3.1(사용자 지적 2026-10-02 — 인물 뱃지 이름·국적이 두 줄 자막과 겹침, hormuz-talks v11 에서도 손으로만 고침) —
    뱃지(원·이름표·역할)·마커(점·라벨·부제)·인용(quote) 상자가 **그 순간 실제 자막 글자 상자**(줄 수·폭 그대로)와 교차하면 hard.
    이벤트마다 첫 시각 한 줄. 지도가 가려진 순간은 뱃지·마커를 보지 않는다(place_over 와 같은 규칙)."""
    from engine.subtitles import subtitle_boxes  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    for e in P.events:
        if e["type"] not in ("badge", "marker", "quote"):
            continue
        t = e["t0"] + 0.3
        while t < e["t1"] - 0.3:
            subs = subtitle_boxes(ctx, P.R.tb, t)
            if subs:
                if e["type"] == "quote":
                    from engine.quote import quote_box  # noqa: PLC0415

                    b = quote_box(ctx, e)
                else:
                    r = place_over(P, ctx, e, t)
                    b = r[1] if r is not None else None
                if b is not None and any(_overlap_px(b, s) > SUB_TOL_PX for s in subs):
                    who = e.get("label") or e.get("speaker") or e.get("pid") or e.get("flag")
                    out.append(f"[subtitle-overlap] {e['type']} {who!r} t={t:.2f} 상자 {tuple(round(v) for v in b)} 가 자막 글자와 겹침 — 자리(place·side·lon/lat)를 옮긴다")
                    break
            t += SUB_STEP_SEC
    return out


def route_frame_report(P) -> list[tuple[str, float, float]]:  # noqa: ANN001, N803
    """경로(route)마다 다 그려진 뒤 보이는 동안 '화면 밖 곡선 비율'의 최댓값 → [(label, 시각, 비율)]."""
    from engine.layers.routes import catmull  # noqa: PLC0415

    out: list[tuple[str, float, float]] = []
    for e in P.events:
        if e["type"] != "route":
            continue
        t, worst, wt = e["t0"] + max(e.get("grow") or 0.0, 0.0) + 0.3, 0.0, 0.0
        while t <= e["t1"] - 0.3:
            if not _covered(P, t):
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                S_ = v.to_screen_arr(e.get("curve") if "curve" in e else catmull(e["world_pts"], 12))  # noqa: N806
                xs, ys = S_[:, 0], S_[:, 1]
                frac = float(((xs < 0) | (xs > W_OUT) | (ys < 0) | (ys > H_OUT)).mean())
                if frac > worst:
                    worst, wt = frac, t
            t += 0.5
        out.append((e.get("label") or e.get("path") or "route", wt, worst))
    return out


def check_route_frame(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 RENDER-AP-012(사용자 지적 2026-10-04 — 철도 훈련 장면의 철도 구간이 프레임 밖) — 경로 곡선의
    `rules panels... route_frame.max_out` 넘는 비율이 화면 밖이면 hard."""
    mx = R_.route_frame.max_out
    return [f"[route-frame] 경로 {nm!r} t={t:.2f} 곡선 {f:.0%} 가 화면 밖(허용 {mx:.0%}) — 카메라가 경로를 담게 하거나 경로를 문장 지역으로 줄인다"
            for nm, t, f in route_frame_report(P) if f > mx]


def check_panel_overflow(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 RENDER-AP-013 — 연도 카드(precedent) 글자가 카드 폭을 넘으면 hard(렌더 전에). 주석(footnote)은 폭·근거 claim·자막 겹침까지."""
    from engine.panels.precedent import overflow  # noqa: PLC0415

    import json  # noqa: PLC0415

    from engine.panels.precedent import footnote_box  # noqa: PLC0415
    from engine.subtitles import subtitle_boxes  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    cp = P.root / "intake" / "claims.json"
    claims = {c["claim_id"] for c in json.loads(cp.read_text(encoding="utf-8"))["claims"]} if cp.exists() else set()
    for e in P.events:
        if e["type"] != "panel" or e.get("kind") != "precedent":
            continue
        out += overflow(ctx, e)
        fn = e.get("footnote")
        if not fn:
            continue
        miss = [c for c in fn["sources"] if c not in claims]   # v5.6.0 — 주석도 출처 없는 문구 금지(C0)
        if miss:
            out.append(f"[panel-footnote] precedent 주석 근거 claim 없음: {', '.join(miss)}")
        fb = footnote_box(e)
        t = max(fn["t0"], e["t0"])
        while t < e["t1"]:   # 주석이 보이는 동안 실제 자막 글자 상자와 겹치면 오류(사용자 조건 "자막을 가리지 않는 선")
            hit = next((b for b in subtitle_boxes(ctx, P.R.tb, t) if _overlap_px(fb, b) > 0), None)
            if hit:
                out.append(f"[panel-footnote] precedent 주석이 자막과 겹침 t={t:.2f} 주석 {tuple(round(v) for v in fb)} 자막 {tuple(round(v) for v in hit)}")
                break
            t += 0.25
    return out


@lru_cache(maxsize=1)
def _land_polygons() -> dict:
    """국가 코드 → shapely 지오메트리(저장소 막지도 자료 110m, 콘티 판과 같은 자료)."""
    from shapely.geometry import MultiPolygon, Polygon  # noqa: PLC0415

    from geo.country_polygons import load_country_polygons  # noqa: PLC0415

    return {k: MultiPolygon([Polygon(q[0], q[1:]) for q in v]).buffer(0) for k, v in load_country_polygons(False).items()}


def _map_main(P) -> bool:  # noqa: ANN001, N803
    from engine.stage import MercatorStage  # noqa: PLC0415

    return isinstance(P.R.stage, MercatorStage)


def check_flag_territory(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 사용자 지적(2026-10-05 "첫 화면에 리투아니아 지역에 러시아 국기 뱃지가 있어 헷갈린다", RENDER-AP-014) —
    국기 뱃지(kind flag) 가운데가 **다른 나라 땅** 위면 hard. 바다·자기 나라 땅(역외 영토 포함)·지도 밖은 된다."""
    if not _map_main(P):
        return []
    from shapely.geometry import Point  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    land = _land_polygons()
    out: list[str] = []
    for e in P.events:
        if e["type"] != "badge" or e.get("kind") != "flag" or e.get("over_panel") or not e.get("flag"):
            continue
        t = e["t0"] + 0.5 * (e["t1"] - e["t0"])
        r = place_over(P, ctx, e, t)
        if r is None:
            continue
        b = r[1]
        v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
        wx, wy = v.to_world((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        ll = P.R.stage.from_world(wx, wy)   # 좌표 변환은 무대에만(15 P1 — 무대 격리)
        pt = Point(ll["lon"], ll["lat"])
        on = next((k for k, g in land.items() if g.contains(pt)), None)
        if on and on != e["flag"].upper():
            out.append(f"[flag-territory] 국기 뱃지 {e.get('label')!r}({e['flag'].upper()}) t={t:.1f} 가 {on} 땅 위 — 자기 나라 땅·바다·화면 가장자리로 옮긴다")
    return out


def check_badge_over_panel(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 사용자 지적(2026-10-05 "자파드 2025 두 주장 화면에서 인물 뱃지가 한 구역에 계속 떠 누구 의견인지 헷갈리고 글씨를 가린다",
    RENDER-AP-015) — 양측 비교(versus) 패널이 떠 있는 동안 뱃지가 있으면 hard. 발언자는 기둥 제목이 밝힌다(같은 무게, G4)."""
    out: list[str] = []
    vs = [e for e in P.events if e["type"] == "panel" and e.get("kind") == "versus"]
    for b in (e for e in P.events if e["type"] == "badge"):
        for p in vs:
            if min(b["t1"], p["t1"]) - max(b["t0"], p["t0"]) > 0.3:
                out.append(f"[badge-over-panel] 뱃지 {b.get('label') or b.get('pid')!r} t={max(b['t0'], p['t0']):.1f} — 양측 비교 패널 {p.get('title')!r} 위. "
                           "발언자는 기둥 제목이 밝힌다 — 뱃지는 패널 앞 문장에서 끝낸다")
    return out


def check_opening_establish(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 사용자 요청(2026-10-05 "지리를 잘 모르는 사람은 위치를 인지하기 어렵다 — 전체 지도에서 천천히 들어가는 오프닝", RENDER-AP-016) —
    지도 주 무대 영상의 첫 카메라는 넓게(rules opening.min_w 이상) 시작해, opening.max_sec 안에 opening.min_zoom 배 이상
    opening.min_move_sec 이상 걸려 천천히 들어가야 한다. 연출 opening_exempt(사유)가 있으면 건너뛴다."""
    if not _map_main(P) or not P.keys or P.R.cache.get("opening_exempt"):
        return []
    op = R_.opening
    k0 = P.keys[0]
    if k0.w < op.min_w:
        return [f"[opening-establish] 첫 화면 폭 {k0.w:.1f}° < {op.min_w}° — 넓은 지도(나라·지역이 보이는 폭)에서 시작해 대상 지역으로 들어간다"]
    for a, b in zip(P.keys, P.keys[1:]):
        if b.t > op.max_sec:
            break
        if b.w <= k0.w / op.min_zoom:
            # v6.0.2 D-0216 — 이동 길이 = 그 키의 dur(이동 키 t 는 시작 시각). 옛 식 b.t − a.t 는 앞 키부터 이동 시작까지의 머무름을 쟀다
            took = b.dur if b.mode == "move" else 0.0
            if took < op.min_move_sec:
                return [f"[opening-establish] 들어가는 이동 {took:.1f}초 < {op.min_move_sec}초 — 천천히 들어간다"]
            return []
    return [f"[opening-establish] {op.max_sec}초 안에 {op.min_zoom}배 이상 들어가지 않는다(첫 폭 {k0.w:.1f}°) — 전체 지도에서 대상 지역으로 들어가는 오프닝"]


def check_weapon_photo(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 사용자 요청(2026-10-05 "무기체계가 나올 때는 웬만하면 실사 이미지", RENDER-AP-017) — 문장에 무기체계 이름(rules weapon_photo.terms)이
    나오는데 그 문장 동안 사진·영상·컷아웃이 없으면 warning(권리 있는 실사가 없을 수 있어 경고 — 사람이 판단)."""
    media = [e for e in P.events if e["type"] in ("photo", "clip", "cutout")]
    out: list[str] = []
    for sid, s in P.R.tb.sent.items():
        hit = next((w for w in R_.weapon_photo.terms if w in s.text), None)
        if hit and not any(m["t0"] < s.t1 and s.t0 < m["t1"] for m in media):
            out.append(f"[weapon-photo] {sid} '{hit}' — 무기체계 실사 사진(권리 기록된 자료사진)이 없다")
    return out


def check_timeline_span(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0 RENDER-AP-011 — timeline 패널(월 눈금 축) 기간이 rules panels.timeline.max_span_months 를 넘으면 hard."""
    from datetime import date  # noqa: PLC0415

    mx = R_.panels.timeline.max_span_months
    out: list[str] = []
    for e in P.events:
        if e["type"] == "panel" and e.get("kind") == "timeline":
            d0, d1 = (date.fromisoformat(str(e[k])[:10]) for k in ("start", "end"))
            months = (d1.year - d0.year) * 12 + d1.month - d0.month + 1
            if months > mx:
                out.append(f"[timeline-span] '{e.get('title')}' {e['start']}~{e['end']} = {months}개월 > {mx} — 월 눈금 축이 뭉개진다. 연도 단위 경과는 precedent(연도 카드)로")
    return out


COLLIDE_STEP_SEC = 0.5   # v5.6.0 지도 글자 겹침 표본 간격


def _text_part(e: dict, box: tuple) -> tuple:
    """marker_box 에서 점·맥동 고리(점 ±14·16px)를 뺀 글자 영역. 마커가 아니면 그대로."""
    if e["type"] != "marker":
        return box
    x0, y0, x1, y1 = box
    side = e.get("side") or "right"
    if side == "right":
        return (x0 + 22, y0, x1, y1)
    if side == "left":
        return (x0, y0, x1 - 22, y1)
    if side == "top":
        return (x0, y0, x1, y1 - 24)
    return (x0, y0 + 24, x1, y1)


def check_label_collision(P) -> list[str]:  # noqa: ANN001, N803
    """v5.6.0(사용자 지적 2026-10-04 — 수바우키 장면 지명 글자가 서로 겹침, 나토 휘장이 발트해 마커의 날짜를 가림, RENDER-AP-009) —
    같은 순간 보이는 지도 뱃지·마커(점·라벨·부제)·경로/봉쇄선 이름표(RENDER-AP-012) 상자끼리 SUB_TOL_PX 넘게 교차하면 hard. 쌍마다 첫 시각 한 줄."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    evs = [e for e in P.events if e["type"] in ("badge", "marker") and not e.get("over_panel") and not own_pin_label(e)]   # 아일랜드 핀 = island label_check
    seen: set[tuple[int, int]] = set()
    out: list[str] = []
    lo = min((e["t0"] for e in evs), default=0.0)
    hi = max((e["t1"] for e in evs), default=0.0)
    t = lo
    while t < hi:
        live = []
        for k, e in enumerate(evs):
            if e["t0"] + 0.3 <= t <= e["t1"] - 0.3:
                r = place_over(P, ctx, e, t)
                if r is not None:
                    live.append((k, e, r[1]))
        if live and not _covered(P, t):   # v5.6.0 RENDER-AP-012 — 경로·봉쇄선 이름표도 같은 순간의 뱃지·마커와 대조
            v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
            for nm, lb in _place_label_boxes(ctx, P, v, t):
                rk = ("line", nm)
                if not any(e["type"] == "marker" and e.get("label") == nm for _, e, _ in live):
                    live.append((rk, {"type": "route/barrier", "label": nm}, lb))
        for i in range(len(live)):
            for j in range(i + 1, len(live)):
                (ka, ea, ba), (kb, eb, bb) = live[i], live[j]
                if "route/barrier" in (ea["type"], eb["type"]):   # 이름표 ↔ 마커는 마커 글자 영역만(점·맥동 고리는 선 위에 있는 게 정상)
                    ba, bb = _text_part(ea, ba), _text_part(eb, bb)
                if (ka, kb) not in seen and _overlap_px(ba, bb) > SUB_TOL_PX:
                    seen.add((ka, kb))
                    na = ea.get("label") or ea.get("pid") or ea.get("img")
                    nb = eb.get("label") or eb.get("pid") or eb.get("img")
                    out.append(f"[label-collision] {ea['type']} {na!r} ↔ {eb['type']} {nb!r} t={t:.2f} — 지도 글자·뱃지가 겹침. side·place·sub 길이를 바꾸거나 한쪽을 먼저 끝낸다")
        t += COLLIDE_STEP_SEC
    return out


def check_cascade_label_hidden(P) -> list[str]:  # noqa: ANN001, N803
    """v5.3.0 D-0139 §3(D-0137 §2) — 문장과 무관한 배경 지명(gazetteer)이 겹침 카드 회피로 안 그려지거나 카드 밑에 깔림 — warning.
    provenance cascade.hidden_labels[] 와 같은 값."""
    return cascade_label_report(P)["hidden"]


def _place_label_boxes(ctx: cairo.Context, P, v: View, t: float) -> list[tuple[str, tuple]]:  # noqa: ANN001, N803
    """지금 보이는 문장 지명 상자 — 마커(at_place 포함) 점·라벨, 항로 이름표, 봉쇄선 이름표. 렌더러와 같은 자리·같은 등장 조건."""
    from engine.layers.markers import marker_box  # noqa: PLC0415
    from engine.layers.routes import RL, catmull  # noqa: PLC0415
    from engine.timebase import ease_io, ease_out, window  # noqa: PLC0415
    from engine.typography import tw  # noqa: PLC0415

    out: list[tuple[str, tuple]] = []
    for e in P.events:
        if e["type"] not in ("marker", "route", "barrier") or not e.get("label") or not e["t0"] <= t <= e["t1"] or own_pin_label(e):
            continue   # 아일랜드 안 핀은 주 무대 지명과 겹침을 따지지 않는다(아일랜드 라벨은 island label_check)
        if e["type"] == "marker":
            if window(t, e["t0"], e["t1"], 0.35, 0.5) <= 0.01 or t - e["t0"] < 0.2:   # 라벨은 0.2초 뒤부터(draw_marker)
                continue
            x, y = v.to_screen(*e["world"])
            if -80 <= x <= W_OUT + 80 and -40 <= y <= H_OUT + 40:
                out.append((e["label"], marker_box(ctx, e, x, y)))
        elif e["type"] == "route":
            continue   # v5.21.11 — 경로 이름표는 렌더와 같은 자리 고르기(route_label_layout)로 아래에서 한꺼번에
        else:
            if ease_out((t - e["t0"]) / 0.8) <= 0.95:
                continue
            x0, y0 = v.to_screen(*e["world_p0"])
            x1, y1 = v.to_screen(*e["world_p1"])
            xr, yb = (x0 + x1) / 2 - 12, (y0 + y1) / 2 + 4
            w = tw(ctx, e["label"], RL.barrier_size, "sansb")
            out.append((e["label"], (xr - w, yb - RL.barrier_size, xr, yb + RL.barrier_size * 0.3)))
    out += [(e["label"], placed[2]) for e, placed, _ in route_label_layout(P, ctx, v, t)]
    return out


def _label_reserved(P, ctx: cairo.Context, v: View, act: list[dict], t: float) -> list:  # noqa: ANN001, N803
    """렌더 R.reserved 와 같은 예약 상자 — 뱃지(place_over)·마커 라벨·겹침 카드."""
    from engine.cascade import cascade_boxes  # noqa: PLC0415
    from engine.layers.markers import marker_box  # noqa: PLC0415

    reserved: list = []
    for e in act:
        if e["type"] == "badge" and not e.get("over_panel") and not e.get("in_island") and (r := place_over(P, ctx, e, t)) is not None:
            reserved.append(r[1])
        elif e["type"] == "marker" and not own_pin_label(e) and e["t0"] <= t <= e["t1"]:
            x, y = v.to_screen(*e["world"])
            reserved.append(marker_box(ctx, e, x, y))
        elif e["type"] == "cascade":
            reserved += cascade_boxes(t, e)
    return reserved


def _label_shown(e: dict, t: float) -> bool:
    """경로 이름표가 그려지는 조건(draw_route 와 같다) — 선이 다 자라고(≥0.99) 선이 보인다."""
    from engine.timebase import ease_io, window  # noqa: PLC0415

    return (e["t0"] <= t <= e["t1"] and (ease_io((t - e["t0"]) / e["grow"]) if e["grow"] > 0.05 else 1) >= 0.99
            and window(t, e["t0"], e["t1"], 0.35, 0.6) > 0.01)


def _capture_reserved(P, i: int) -> list:  # noqa: ANN001, N803
    """프레임 i 렌더의 예약 상자(뱃지·마커·겹침 카드) — render_frame 을 이름표 flush 에서 멈춰 R.reserved 를 그대로 받는다
    (검사 근사 아님, RENDER-AP-024). 배경은 그리지 않고 지도 글자 대비 기록도 끈다. 프레임마다 한 번(P.R.cache)."""
    memo = P.R.cache.setdefault("route_label_capture_memo", {})
    if i in memo:
        return memo[i]
    from engine import typography  # noqa: PLC0415
    from engine.layers.routes import LabelCapture  # noqa: PLC0415
    from engine.render import render_frame  # noqa: PLC0415

    cap: dict = {}
    P.R.cache["route_label_capture"], clog, typography.CONTRAST_LOG = cap, typography.CONTRAST_LOG, None
    try:
        render_frame(P, i)
    except LabelCapture:
        pass
    finally:
        P.R.cache["route_label_capture"], typography.CONTRAST_LOG = None, clog
    memo[i] = cap.get("reserved", [])
    return memo[i]


def route_label_slots(P) -> dict[int, int]:  # noqa: ANN001, N803
    """v5.22.7 D209·D210 — 경로 이름표마다 고정 후보 번호 {id(이벤트): k}. 렌더(flush_route_labels)·검사 공용, 결정적.
    이름표 수명(글자 불투명도 > 0.01 인 프레임 격자) 전체를 qa_checks.label_slot_sample_sec 간격으로 훑어, 모든 표본에서
    선·예약 상자·마커 글자·해역 이름·자막·전경 층·먼저 자리 잡은 이름표와 안 겹치는 후보 중 앞 번호를 고른다.
    그런 후보가 없으면 겹치는 표본이 가장 적은 후보로 고정하고, 겹치는 구간은 그 자리에서 흐린다
    (P.R.cache["route_label_fades"] = {id: [(시작, 끝)]}, 렌더 slot_fade·검사가 같은 값)."""
    if "route_label_slots" in P.R.cache:
        return P.R.cache["route_label_slots"]
    import math  # noqa: PLC0415

    from engine.layers.routes import catmull, label_candidates, label_extent, label_obstacles, route_lines, slot_route_label  # noqa: PLC0415
    from engine.layers.routes import _bad, _box  # noqa: PLC0415
    from engine.timebase import smooth, window  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    routes = [e for e in P.events if e["type"] == "route" and e.get("label") and not e.get("in_island")]
    step = max(1, round(QA.label_slot_sample_sec * FPS))
    lives = []
    for n, e in enumerate(routes):
        fr = [i for i in range(max(0, math.floor(e["t0"] * FPS)), min(P.n_frames - 1, math.ceil(e["t1"] * FPS)) + 1)
              if _label_shown(e, i / FPS) and window(i / FPS, e["t0"], e["t1"], 0.35, 0.6) * smooth((i / FPS - e["t0"] - e["grow"]) / 0.4) > 0.01]
        if fr:
            lives.append((fr[0], n, e, sorted(set(fr[::step]) | {fr[-1]})))
    slots: dict[int, int] = {}
    fades: dict[int, list[tuple[float, float]]] = {}
    P.R.cache["route_label_slots"] = slots   # render_frame(붙잡기)이 다시 부르지 않게 먼저 둔다
    P.R.cache["route_label_fades"] = fades
    half = step / FPS
    for _, _, e, samples in sorted(lives, key=lambda a: (a[0], a[1])):
        _, W = label_extent(ctx, P.R.stage, e["label"])  # noqa: N806
        bad_at: list[list[bool]] = []
        for i in samples:
            t = i / FPS
            v = View(P.R.stage, P.cams[i])
            act = [x for x in P.events if x["t0"] - 0.05 <= t <= x["t1"] + 0.05]
            obstacles = label_obstacles(ctx, v, act, t, _capture_reserved(P, i), P.R.tb)
            lines = route_lines(v, act, t)
            for o in routes:   # 먼저 자리 잡은 이름표(지금 보이는 것)
                if id(o) in slots and _label_shown(o, t):
                    So = v.to_screen_arr(o["curve"] if "curve" in o else catmull(o["world_pts"], 12))  # noqa: N806
                    obstacles.append(slot_route_label(ctx, v.stage, o["label"], So, slots[id(o)], [], [])[2])
            S_ = v.to_screen_arr(e["curve"] if "curve" in e else catmull(e["world_pts"], 12))  # noqa: N806
            bad_at.append([_bad(_box(cx, by, W), obstacles, lines) > 0 for cx, by in label_candidates(S_, W)])
        n_bad = [sum(row[k] for row in bad_at) for k in range(len(bad_at[0]))]
        k = min(range(len(n_bad)), key=lambda q: (n_bad[q], q))
        slots[id(e)] = k
        spans: list[tuple[float, float]] = []
        for i, row in zip(samples, bad_at):
            if row[k]:
                t = i / FPS
                if spans and t - half <= spans[-1][1] + 1e-9:
                    spans[-1] = (spans[-1][0], t + half)
                else:
                    spans.append((t - half, t + half))
        if spans:
            fades[id(e)] = spans
    return slots


def route_label_layout(P, ctx: cairo.Context, v: View, t: float) -> list[tuple[dict, tuple, list]]:  # noqa: ANN001, N803
    """시각 t 에 보이는 경로 이름표 자리 — 렌더 flush_route_labels 와 같은 고정 후보(route_label_slots, v5.22.7 D209).
    통과 = 지금 경로 선·예약 상자·마커 글자·해역 이름·자막·다른 이름표와 안 겹침(전경 층은 흐림으로 처리 — 제외).
    → [(이벤트, (x, y, 상자, 통과), 그 순간 경로 선들)]"""
    from engine.layers.routes import catmull, label_obstacles, route_lines, slot_route_label  # noqa: PLC0415

    act = [e for e in P.events if e["t0"] - 0.05 <= t <= e["t1"] + 0.05]
    labs = [e for e in act if e["type"] == "route" and e.get("label") and not e.get("in_island") and _label_shown(e, t)]
    if not labs:
        return []
    slots = route_label_slots(P)
    obstacles = label_obstacles(ctx, v, act, t, _label_reserved(P, ctx, v, act, t), P.R.tb, foreground=False)
    lines = route_lines(v, act, t)
    out = []
    for e in labs:
        if id(e) not in slots:
            continue
        S_ = v.to_screen_arr(e["curve"] if "curve" in e else catmull(e["world_pts"], 12))  # noqa: N806
        placed = slot_route_label(ctx, v.stage, e["label"], S_, slots[id(e)], obstacles, lines)
        obstacles.append(placed[2])
        out.append((e, placed, lines))
    return out


def check_label_jump(P) -> list[str]:  # noqa: ANN001, N803
    """v5.22.7 D209 — 같은 경로 이름표가 보이는 중에 자리를 옮기면 hard(C0 "튀어 오르는 연출"과 같은 종류).
    렌더와 같은 자리(route_label_layout)를 프레임마다 재서, 이름표 상자 가운데 ↔ 가장 가까운 경로 점의 상대 위치가
    한 프레임 사이 qa_checks.label_jump_px 넘게 바뀌면 이름표마다 첫 시각 한 줄(카메라 컷 프레임은 제외)."""
    from engine.layers.routes import catmull  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    cuts = {math.ceil(k.t * FPS - 1e-9) for k in P.keys if k.mode == "cut"}
    prev: dict[int, tuple[int, np.ndarray]] = {}
    out: list[str] = []
    bad: set[int] = set()
    routes = [e for e in P.events if e["type"] == "route" and e.get("label") and not e.get("in_island")]
    if not routes:
        return out
    lo = max(0, int(min(e["t0"] for e in routes) * FPS))
    hi = min(P.n_frames - 1, int(max(e["t1"] for e in routes) * FPS) + 1)
    for i in range(lo, hi + 1):
        t = i / FPS
        if _covered(P, t):
            prev.clear()
            continue
        v = View(P.R.stage, P.cams[i])
        for e, (_, _, b, _), _ in route_label_layout(P, ctx, v, t):
            S_ = v.to_screen_arr(e["curve"] if "curve" in e else catmull(e["world_pts"], 12))  # noqa: N806
            c = np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2])
            off = c - S_[int(np.argmin(((S_ - c) ** 2).sum(axis=1)))]
            p = prev.get(id(e))
            if (p is not None and p[0] == i - 1 and i not in cuts and id(e) not in bad
                    and float(np.hypot(*(off - p[1]))) > QA.label_jump_px):
                bad.add(id(e))
                out.append(f"[label-jump] 경로 이름표 {e['label']!r} 가 보이는 중에 자리를 옮김 t={t:.2f} "
                           f"({float(np.hypot(*(off - p[1]))):.1f}px > {QA.label_jump_px}) — 이름표 자리는 나타날 때 정한 대로 고정(D209)")
            prev[id(e)] = (i, off)
    return out


def route_label_report(P) -> dict[str, list[str]]:  # noqa: ANN001, N803
    """v5.21.11 D-0191 §1-3·D-0192 — 표본 시각마다 경로 이름표 자리를 렌더와 같게 골라
    cross: 경로 선(자기·남의)이 이름표 글자 상자를 지나감 + 마커 라벨·부제 글자를 경로 선이 지나감,
    overlap: 이름표가 해역 이름·다른 이름표·뱃지·마커와 겹침(어느 후보로도 피하지 못함). 쌍마다 첫 시각 한 줄. 결과는 캐시."""
    if "route_label" in P.R.cache:
        return P.R.cache["route_label"]
    from engine.layers.markers import marker_text_boxes  # noqa: PLC0415
    from engine.layers.routes import RL, route_lines, segs_cross_box  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    rep: dict[str, list[str]] = {"cross": [], "overlap": []}
    seen: set = set()
    from engine.layers.routes import slot_fade  # noqa: PLC0415

    route_label_slots(P)
    fades = P.R.cache["route_label_fades"]
    routes = [e for e in P.events if e["type"] == "route" and not e.get("in_island")]
    lo = min((e["t0"] for e in routes), default=0.0)
    hi = max((e["t1"] for e in routes), default=0.0)
    t = lo
    while routes and t < hi:
        if not _covered(P, t):
            v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
            for e, (_, _, b, ok), lines in route_label_layout(P, ctx, v, t):
                if slot_fade(fades, e, t) < 0.5:   # v5.22.7 D210 — 수명 전체에 안 겹치는 자리가 없어 그 구간 흐림(겹침은 보이지 않는다)
                    continue
                if any(segs_cross_box(L_, b, RL.line_clear_px) for L_ in lines) and ("x", id(e)) not in seen:
                    seen.add(("x", id(e)))
                    rep["cross"].append(f"[route-label-cross] 경로 이름표 {e['label']!r} 를 경로 선이 지나감 t={t:.2f} — 어느 자리 후보로도 선을 피하지 못함. "
                                        "라벨을 줄이거나 경로·카메라 구도를 바꾼다")
                elif not ok and ("o", id(e)) not in seen:
                    seen.add(("o", id(e)))
                    rep["overlap"].append(f"[route-label-overlap] 경로 이름표 {e['label']!r} 가 지명·뱃지·마커·다른 이름표와 겹치거나 화면 밖 t={t:.2f} — "
                                          "라벨을 줄이거나 겹치는 요소의 시간·자리를 바꾼다")
            lines = route_lines(v, P.events, t)
            for e in P.events:
                if e["type"] != "marker" or own_pin_label(e) or not e.get("label") or e.get("route_cross_exempt") or not e["t0"] + 0.3 <= t <= e["t1"] - 0.3:
                    continue
                x, y = v.to_screen(*e["world"])
                if not (-80 <= x <= W_OUT + 80 and -40 <= y <= H_OUT + 40):
                    continue
                if any(segs_cross_box(L_, tb, 0.0) for L_ in lines for tb in marker_text_boxes(ctx, e, x, y)) and ("m", id(e)) not in seen:
                    seen.add(("m", id(e)))
                    rep["cross"].append(f"[route-label-cross] 마커 {e['label']!r} 라벨·부제 글자를 경로 선이 지나감 t={t:.2f} — 마커 side 를 바꾸거나 부제를 줄인다")
        t += COLLIDE_STEP_SEC
    P.R.cache["route_label"] = rep
    return rep


def cascade_label_report(P) -> dict:  # noqa: ANN001, N803
    """겹침 카드 ↔ 지명(v5.3.0 D-0139 §3, D-0137 §2) → {under: [hard 줄], hidden: [warning 줄], hidden_labels: [{name, kind, t}]}.
    - 문장 지명(지금 보이는 마커·at_place·경로·봉쇄선 이름표)이 카드 상자와 교차 → `[cascade-label-under]` hard.
    - 배경 지명(gazetteer 나라·도·도시)이 카드 회피로 안 그려짐, 해역 이름이 카드 밑에 깔림 → `[cascade-label-hidden]` warning.
      같은 이름의 마커가 보이면 그 이름은 마커 라벨이 보여 준다(마커 라벨이 깔리면 위 hard) — 지도 라벨은 이름으로 문장 지명을 가리지 않는다.
    렌더와 같은 `draw_labels`(카드 상자 회피 전/후)로 잰다. 지도가 가려진 순간(패널·전면 카드·암전)은 보지 않는다. P.R.cache 에 한 번만 잰다."""
    if P.R.cache.get("cascade_check") is not None:
        return P.R.cache["cascade_check"]
    from engine.cascade import cascade_boxes  # noqa: PLC0415
    from engine.style import CASCADE  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    under: list[str] = []
    hidden: list[str] = []
    names: dict[str, dict] = {}
    for e in P.events:
        if e["type"] != "cascade":
            continue
        seen: set[str] = set()
        t = e["t0"]
        while t <= e["t1"]:
            boxes = cascade_boxes(t, e)
            if boxes and not _covered(P, t):
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                for nm, lb in _place_label_boxes(ctx, P, v, t):
                    if any(_box_hit(lb, b) for b in boxes) and f"p:{nm}" not in seen:
                        seen.add(f"p:{nm}")
                        under.append(f"[cascade-label-under] t={t:.2f} 문장 지명 {nm!r} 상자 {tuple(round(x) for x in lb)} 가 겹침 카드 밑에 깔림"
                                     " — 첫 숏 구도(camera lon·lat·w)나 마커 side 를 바꾼다")
                kept = P.R.stage.draw_labels(ctx, v, list(boxes), 0.0) or []   # 렌더와 같이 카드 상자를 회피한 뒤 그려지는 지명
                free = P.R.stage.draw_labels(ctx, v, [], 0.0) or []            # 카드가 없을 때 그려졌을 지명
                kept_names = {getattr(b, "name", None) for b in kept}
                gone = [(b, "깔림") for b in kept if any(_box_hit(b, c) for c in boxes)]
                gone += [(b, "회피") for b in free if getattr(b, "name", None) not in kept_names and any(_box_hit(b, c) for c in boxes)]
                for b, how in gone:
                    nm, kind = getattr(b, "name", "?"), getattr(b, "kind", "?")
                    if nm not in names:
                        names[nm] = {"name": nm, "kind": kind, "how": how, "t": round(t, 2)}
                        hidden.append(f"[cascade-label-hidden] t={t:.2f} 배경 지명 {nm!r}({kind}) 이 겹침 카드 때문에 안 보임({how})")
            t += CASCADE_STEP_SEC
    P.R.cache["cascade_check"] = {"under": under, "hidden": hidden, "hidden_labels": list(names.values())}
    return P.R.cache["cascade_check"]


def check_offscreen(P) -> list[str]:  # noqa: ANN001, N803
    """뱃지 상자(`badges.badge_box` — 원·그림자·인물 머리·이름표)와 지점 마커 상자(`markers.marker_box` — 점·라벨·부제,
    D-0049 쟁점 4)가 보이는 순간마다 화면 안. 그림자 여백만큼은 허용. 마커는 렌더러가 그리는 범위(화면 ±80·40px)만 본다."""
    out: list[str] = []
    for e, t, over, b in offscreen_hits(P):
        what = "마커" if e["type"] == "marker" else "뱃지"
        out.append(f"{what} {e.get('label') or e.get('pid') or e.get('flag')} t={t:.1f} 화면 밖 {over:.0f}px "
                   f"(상자 {[round(z) for z in b]})")
    return out


def check_endcard_roll(P) -> list[str]:  # noqa: ANN001, N803
    """엔딩 카드 롤(v4.7.0 back_and_forth D-0106 1-C) — 상한 안 롤은 warning(검수자가 보게). 같은 함수 `fullcards.endcard_roll`."""
    from engine.fullcards import credit_place, endcard_roll_note, notice_reserve, project_credit_sections  # noqa: PLC0415

    if P.R.credits is None or not any(c.kind == "end" for c in P.plan.cards):
        return []
    return endcard_roll_note(project_credit_sections(P.R), credit_place(P.R), notice_reserve(P.R))


def check_geo_unsourced(P) -> list[str]:  # noqa: ANN001, N803
    """지도 좌표 근거 미대조(v4.7.0 back_and_forth D-0107 D2(b)) — warning. 항목은 load_project 가 연출에서 모은 것(provenance 와 같은 값)."""
    out: list[str] = []
    for it in (P.R.cache.get("geo_check") or {}).get("unsourced") or []:
        where = it["lonlat"] if "lonlat" in it else f"{it['points']}점 {it['ends'][0]}→{it['ends'][1]}"
        out.append(f"[geo-unsourced] {it['kind']} {it['name']} {where} — 지명 사전에 없는 이름(또는 경로)이라 좌표를 대조하지 못함")
    return out


def check_geo_mismatch(P) -> list[str]:  # noqa: ANN001, N803
    """지명 사전 좌표 불일치(v4.10.0 back_and_forth D-0116 B-1) — hard. 항목은 load_project 가 `geo.gazetteer.check_doc` 로 모은 것."""
    return [f"[geo-mismatch] {it['kind']} {it['name']} {it['lonlat']} — 사전 {it['gazetteer']} 에서 {it['km']}km(허용 {it['tol_km']}km)"
            for it in (P.R.cache.get("geo_check") or {}).get("mismatch") or []]


def check_static_window(P) -> list[str]:  # noqa: ANN001, N803
    """정적 구간(v4.11.0 back_and_forth D-0118 §1) — warning. 범위는 load_project 가 `engine.pacing` 으로 한 번 계산한 것(creep·provenance 와 같은 값)."""
    pc = P.R.cache.get("pacing") or {}
    return [f"[static-window] {w['t0']:.1f}-{w['t1']:.1f} changes={w['changes']} (창 {pc.get('window_sec'):g}초, 기준 ≥ {pc.get('min_changes')}; "
            f"종류 {', '.join(w['kinds']) or '없음'})" for w in pc.get("static_windows") or []]


def check_timeline_rescale(P) -> list[str]:  # noqa: ANN001, N803
    """시간축 축 스케일(v5.1.0 D-0121 §A) — engine.shots.timeline_rescale 한 곳, 입력 = provenance timeline.w_changes 와 같은 값."""
    from engine.shots import timeline_rescale  # noqa: PLC0415

    return timeline_rescale((P.R.cache.get("timeline") or {}).get("w_changes") or [])


def check_island_overlap(P) -> list[str]:  # noqa: ANN001, N803
    """아일랜드 겹침(v5.1.0 D-0126 Q3 A) — engine.island 한 곳. backdrop 무대가 아니면 0."""
    from engine.island import island_boxes, island_overlap  # noqa: PLC0415

    return island_overlap(island_boxes(P.events, P.R.assets.media_assets, P.R.stage.name))


def check_main_missing(P) -> list[str]:  # noqa: ANN001, N803
    """주 아일랜드 상시(v5.2.0 D-0129 §B) — 구간은 load_project 가 engine.island.main_missing 으로 한 번 계산(provenance 와 같은 값)."""
    from engine.island import main_missing_details  # noqa: PLC0415

    return main_missing_details(((P.R.cache.get("island_check") or {}).get("main_missing")) or [])


def check_island_label_clip(P) -> list[str]:  # noqa: ANN001, N803
    """아일랜드 마커 라벨 잘림(v5.2.0 D-0133 §2) — hard. 항목은 load_project 가 engine.island.label_check 로 잰 것(provenance 와 같은 값)."""
    from engine.island import label_clip_details  # noqa: PLC0415

    return label_clip_details(((P.R.cache.get("island_check") or {}).get("label_clip")) or [])


def own_pin_label(e: dict) -> bool:
    """자기 라벨 배치·검사 경로가 따로 있는 마커 — 차트 아일랜드 안(island label_check) 또는 값 레인 위 핀(engine.pin_labels, D-0274).
    지도 무대 기준 라벨 상자 검사(offscreen·label_collision 등)가 재지 않는다."""
    return bool(e.get("in_island")) or e.get("pin_value") is not None


def check_island_pin_collision(P) -> list[str]:  # noqa: ANN001, N803
    """[island-pin-collision] hard(v7.4.0 back_and_forth D-0267 §2 → D-0274 §1②, UF-143) — 값 레인 위 핀 라벨이 다른 핀 라벨·점, 계열 선·띠·전망 점,
    축 값 라벨, 끝값 라벨, 플롯 경계와 교차. 단은 load_project 가 engine.pin_labels.assign_pin_rows 로 골랐다(주 무대 틀·차트 아일랜드 같은 키).
    표본·자리는 렌더와 같다(engine.pin_labels.pin_label_check)."""
    rows = ((getattr(P.R, "cache", None) or {}).get("pin_labels") or {}).get("collisions") or []
    return [f"[island-pin-collision] 핀 {r['a']!r} 라벨 ↔ {r['b']} t={r['t0']:.2f}~{r['t1']:.2f} — 선 위·아래 두 단 어디에도 자리가 없다면"
            " 연출이 핀 수명을 줄여 순차로 띄운다(D-0274)" for r in rows]


def check_island_label_overlap(P) -> list[str]:  # noqa: ANN001, N803
    """아일랜드 마커 라벨 ↔ 시리즈 출처 줄(v5.2.0 D-0133 §3) — warning."""
    from engine.island import label_overlap_details  # noqa: PLC0415

    return label_overlap_details(((P.R.cache.get("island_check") or {}).get("label_overlap")) or [])


def check_card_island(P) -> list[str]:  # noqa: ANN001, N803
    """카드 ↔ 아일랜드 교차(v5.2.0 D-0129 §C) — warning. 항목은 load_project 가 engine.island.card_overlap 으로 모은 것."""
    from engine.island import card_overlap_details  # noqa: PLC0415

    return card_overlap_details(((P.R.cache.get("island_check") or {}).get("card_overlap")) or [])


def check_endcard_overflow(P) -> list[str]:  # noqa: ANN001, N803
    """엔딩 카드 크레딧 넘침(v4.5.0 back_and_forth D-0098 §2) — draw_endcard 가 오류를 내는 것과 같은 함수(`fullcards.endcard_overflow`)."""
    from engine.fullcards import credit_place, endcard_overflow, notice_reserve, project_credit_sections, unverified_notice, version_stamp_overflow  # noqa: PLC0415

    if P.R.credits is None or not any(c.kind == "end" for c in P.plan.cards):
        return []
    return (endcard_overflow(project_credit_sections(P.R), credit_place(P.R), notice_reserve(P.R))
            + version_stamp_overflow(unverified_notice(P.R)))   # v5.1.0 D-0124 — 버전 도장 포함


def offscreen_hits(P) -> list[tuple[dict, float, float, tuple]]:  # noqa: ANN001, N803
    """check_offscreen 의 판정 본체(이벤트, 시각, 넘친 px, 상자) — 카메라 제안 검증(engine.camera_suggest)도 이 함수를 쓴다
    (검사기 하나, D-0056 §2). P.cams·P.events 를 바꾼 사본을 넘기면 그 카메라 경로(이동·드리프트 포함)로 본다."""
    out: list[tuple[dict, float, float, tuple]] = []
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    for e in P.events:
        if e["type"] not in ("badge", "marker") or own_pin_label(e):   # 아일랜드 안 핀은 아일랜드 뷰로 그린다 — 주 무대 좌표로 재지 않는다(island label_check)
            continue
        t = e["t0"] + 0.5
        while t < e["t1"] - 0.5:
            r = place_over(P, ctx, e, t)
            if r is not None and r[0] > SHADOW_PX:
                out.append((e, t, r[0], r[1]))
                break
            t += SAMPLE_SEC
    return out


def place_over(P, ctx: cairo.Context, e: dict, t: float) -> tuple[float, tuple] | None:  # noqa: ANN001, N803
    """시각 t 에 뱃지·마커 상자가 화면 밖으로 넘친 px(음수 = 안쪽 여유)와 상자. 지도가 가려졌거나 렌더러가 그리지 않는
    위치(마커 화면 ±80·40px 밖)면 None. offscreen 검사와 컷별 '장소 전부 프레임 안' 보고가 같이 쓴다."""
    from engine.layers.badges import badge_box  # noqa: PLC0415
    from engine.layers.markers import marker_box  # noqa: PLC0415

    from engine.layers.badges import edge_nudge, screen_xy  # noqa: PLC0415

    if _covered(P, t) and not e.get("over_panel"):   # 패널 위 뱃지(D2(c))는 패널이 떠 있어도 보인다
        return None
    v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
    x, y = screen_xy(e, v)
    if e["type"] == "marker":
        if x < -80 or x > W_OUT + 80 or y < -40 or y > H_OUT + 40:   # draw_marker 가 그리지 않는 위치
            return None
        b = marker_box(ctx, e, x, y, with_sub=True)
    else:
        b = badge_box(ctx, e, x, y, t)
        ex, ey = edge_nudge(b, x, y)            # v4.8.0 D-0112 — 렌더러와 같은 가장자리 보정 뒤 상자(보정 뒤에도 밖이면 hard)
        hx, hy = e.get("push_hold", (0.0, 0.0))  # v5.6.0 — 고정 이동(badge_hold)도 렌더러와 같게
        b = (b[0] + ex + hx, b[1] + ey + hy, b[2] + ex + hx, b[3] + ey + hy)
    return max(-b[0], -b[1], b[2] - W_OUT, b[3] - H_OUT), tuple(b)


LABEL_STEP_SEC = 0.1      # label_hidden 표본 간격
HIDDEN_ALPHA = 0.5        # 이 값 미만으로 흐려진 라벨 = 숨김(D-0068 정의)


def label_hidden_ratio(P, e: dict) -> tuple[float, list[str]]:  # noqa: ANN001, N803
    """마커 e 의 (숨김 시간 ÷ 표시 시간, 숨긴 카드 ref). 표시 = 마커가 그려지는 시각(지도 가려짐·화면 ±80·40 밖 제외)."""
    from engine.layers.markers import marker_box  # noqa: PLC0415
    from engine.reserved import card_zones, marker_label_alpha  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    shown = hidden = 0
    refs: set[str] = set()
    t = e["t0"] + LABEL_STEP_SEC / 2
    while t < e["t1"]:
        if not _covered(P, t):
            v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
            x, y = v.to_screen(*e["world"])
            if -80 <= x <= W_OUT + 80 and -40 <= y <= H_OUT + 40:   # draw_marker 가 그리는 위치
                shown += 1
                box = marker_box(ctx, e, x, y)
                zones = card_zones(ctx, P.events, t)
                if marker_label_alpha(box, zones) < HIDDEN_ALPHA:
                    hidden += 1
                    refs |= {z.ref for z in zones if _box_hit(box, z.box)}
        t += LABEL_STEP_SEC
    return (hidden / shown if shown else 0.0), sorted(refs)


def _box_hit(a: tuple, b: tuple) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def check_label_hidden(P) -> list[str]:  # noqa: ANN001, N803
    out: list[str] = []
    for e in P.events:
        if e["type"] != "marker":
            continue
        r, refs = label_hidden_ratio(P, e)
        if r > QA.label_hidden_max_ratio:
            out.append(f"[label-hidden-by-card] 마커 {e['label']!r} t0={e['t0']:.2f} 라벨이 카드 {refs} 뒤에서 표시 시간의 {r:.0%} 흐려짐"
                       f" > {QA.label_hidden_max_ratio:.0%} — 마커나 카드 자리를 옮겨라(카메라 구도·카드 y·place)")
    return out


def check_labels(P, times: list[float]) -> list[str]:  # noqa: ANN001, N803
    from engine.layers import labels as L  # noqa: N812, PLC0415

    out: list[str] = []
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    for t in times:
        cnt = [0]
        orig = L.text

        def counting(ctx, s, x, y, size, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202 — 도시 라벨(왼쪽 정렬 "l")만 센다
            if len(a) >= 4 and a[3] == "l":
                cnt[0] += 1
            return orig(ctx, s, x, y, size, *a, **k)

        L.text = counting
        try:
            P.R.reserved.clear()
            P.R.stage.draw_labels(cairo.Context(surf), View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))]), P.R.reserved, 1.0)
        finally:
            L.text = orig
        if cnt[0] > QA.labels_per_frame_max:
            out.append(f"t={t:.2f} 도시 라벨 {cnt[0]} > {QA.labels_per_frame_max}")
    return out


def check_shots(P) -> list[str]:  # noqa: ANN001, N803
    """숏 규칙 — engine.shots.shot_issues 한 곳(v3.3.0, 7 린트·제안과 같은 함수)."""
    from engine.shots import shot_issues, timeline_backtrack  # noqa: PLC0415

    return shot_issues(P.keys, P.plan.sentences, P.events, P.R.tb.total) + timeline_backtrack(P.shots)   # v4.3.0 시간축 되돌아가기


def check_camera_continuity(P) -> list[str]:  # noqa: ANN001, N803
    """카메라 연속성(v5.21.9 D-0191 §1-1, 사용자 의견 UF-02) — 스케치 SK-C1 과 같은 측정(engine.camera.continuity)·같은 임계
    (rules sketch.checks max_dlogw·max_d2logw·max_d3). 컷 키(암전 컷 포함)에 걸친 차분은 뺀다. 종류마다 최댓값 한 줄.
    v7.1.0 UF-99 D-0220: **화면 궤적**(engine.camera.screen_track — 렌더와 같은 View 클램프 뒤)을 잰다. 요청 궤적은 경계에서 잘리면 화면과 다르다."""
    from engine.camera import continuity, screen_track  # noqa: PLC0415

    if P.cams is None:
        return []
    th = R_.sketch.checks
    cuts = sorted({math.ceil(k.t * FPS - 1e-9) for k in P.keys if k.mode == "cut"})
    lim = {1: th.max_dlogw_per_frame, 2: th.max_d2logw_per_frame, 3: th.max_d3_per_frame}
    out = []
    for k, v in continuity(screen_track(P.R.stage, np.asarray(P.cams, dtype=float)), cuts).items():
        o = int(k[1])
        bad = np.flatnonzero(v > lim[o])
        if bad.size:
            i = int(bad[np.argmax(v[bad])])
            out.append(f"[camera-continuity] |Δ{o} {k[3:]}| {v[i]:.4f} > {lim[o]} — t={i / FPS:.2f}s 외 {bad.size - 1}프레임"
                       f"{' (이동 중간 꺾임 — rules shot_grammar.move_ease)' if o == 3 else ''}")
    return out


def check_camera_speed(P) -> list[str]:  # noqa: ANN001, N803
    """카메라 속도 상한(v6.0.2 UF-97·D-0216, recurs_of UF-02 — camera_continuity 는 매끄러움만 재고 빠르기는 재지 않았다).
    engine.camera.speed(스케치 SK-C1 과 같은 함수)로 pan·zoom 을 재고 rules shot_grammar.camera_speed 를 넘으면 hard.
    제목 카드 전(오프닝)은 opening_* 상한. 종류·구간마다 최댓값 한 줄. 무대마다 재는 성분은 rules camera_speed.stages
    (v7.0.1 D-0218 A — 지도 = pan·zoom, 시간축 = zoom 만, 없는 무대 = 검사 안 함)."""
    from engine.camera import screen_track, speed  # noqa: PLC0415

    lim = R_.shot_grammar.camera_speed
    kinds = lim.stages.get(getattr(P.R.stage, "name", None), [])
    if P.cams is None or not kinds:
        return []
    cuts = sorted({math.ceil(k.t * FPS - 1e-9) for k in P.keys if k.mode == "cut"})
    sp = speed(screen_track(P.R.stage, np.asarray(P.cams, dtype=float)), cuts, FPS)   # v7.1.0 D-0220 — 화면 궤적
    title = next((c.t0 for c in P.plan.cards if c.kind == "title"), None)
    n_open = 0 if title is None else min(len(sp["pan"]), int(title * FPS))
    out = []
    for kind, gen, opn, unit in (("pan", lim.max_pan_w_per_sec, lim.opening_max_pan_w_per_sec, "화면 폭/초"),
                                 ("zoom", lim.max_zoom_per_sec, lim.opening_max_zoom_per_sec, "/초")):
        if kind not in kinds:
            continue
        v = sp[kind]
        for lo, hi, cap, where in ((0, n_open, opn, "오프닝(제목 카드 전)"), (n_open, len(v), gen, "")):
            seg = v[lo:hi]
            bad = np.flatnonzero(seg > cap)
            if bad.size:
                i = lo + int(bad[np.argmax(seg[bad])])
                out.append(f"[camera-speed] {where}카메라 {kind} {v[i]:.3f}{unit} > {cap} — t={(i + 1) / FPS:.2f}s 외 {bad.size - 1}프레임 "
                           "— 이동을 길게(dur)·나눠서·이동 폭을 줄인다(rules shot_grammar.camera_speed)")
    return out


def _clamp_spans(d: "np.ndarray", tol: float) -> list[tuple[int, int, str]]:
    """프레임별 클램프 비율(n×3) → 넘는 구간 [(첫 프레임, 끝 프레임, 잘린 성분)]."""
    bad = np.flatnonzero(d.max(axis=1) > tol)
    out = []
    for g in (np.split(bad, np.flatnonzero(np.diff(bad) > 1) + 1) if bad.size else []):
        comp = "·".join(n for j, n in enumerate("xyw") if d[g, j].max() > tol)
        out.append((int(g[0]), int(g[-1]), comp))
    return out


def check_camera_bounds(P) -> list[str]:  # noqa: ANN001, N803
    """카메라 무대 경계(v7.1.0 UF-99 D-0220, recurs_of UF-02·UF-97) — 요청 궤적이 무대 경계 밖이라 렌더 View 가 잘랐으면 hard.
    잘린 동안 화면은 경계에 멈춰 있다가 요청 궤적이 경계 안으로 들어오는 순간 이동 중간 속도로 한 프레임 만에 출발·정지·방향을 바꾼다
    (사용자에게 "딱 꺾이는 지점"). 지도 무대·시간축 무대·차트 아일랜드 카메라 모두. 구간마다 한 줄(시각·잘린 성분·허용 최대 w)."""
    from engine.camera import bounds_excess, max_view_w  # noqa: PLC0415

    if P.cams is None:
        return []
    tol = R_.qa_checks.camera_bounds_rel_tol
    tracks = [("", P.R.stage, np.asarray(P.cams, dtype=float))]
    chart = getattr(P.R, "cache", {}).get("island_chart") if hasattr(P.R, "cache") else None
    if chart is not None:
        tracks.append(("차트 아일랜드 ", chart["stage"], np.asarray(chart["cams"], dtype=float)))
    out = []
    for name, st, tr in tracks:
        d = bounds_excess(st, tr)
        wmax = max_view_w(st)
        for a, b, comp in _clamp_spans(d, tol):
            out.append(f"[camera-bounds] {name}카메라가 무대 경계 밖 — t={a / FPS:.2f}~{b / FPS:.2f}s 잘린 성분 {comp}"
                       f"(요청 w 최대 {tr[a:b + 1, 2].max():.1f}, 허용 최대 w {wmax:.1f}). 렌더가 경계에서 잘라 화면이 멈췄다가 "
                       "이동 중간에 꺾인다 — 키를 경계 안(w ≤ 허용 최대, 중심 ± w/2 가 경계 안)으로 고른다(rules qa_checks.camera_bounds_rel_tol)")
    return out


def _title_backdrop(P, t: float) -> str:  # noqa: ANN001, N803
    """시각 t 에 화면 바탕 — 'black'(암전) · 'article:<mid>'(기사 카드가 화면을 덮음) · 'map'."""
    for e in P.events:
        if e["type"] == "dip" and e["t0"] <= t <= e["t1"]:
            return "black"
    for e in P.events:
        if e["type"] == "article" and e["t0"] <= t <= e["t1"]:
            return f"article:{e.get('mid')}"
    return "map"


def check_title_backdrop(P) -> list[str]:  # noqa: ANN001, N803
    """제목 카드 바탕(v6.0.2 UF-98·D-0216) — 제목 카드 바로 앞 1초 동안의 장면은 그 제목의 바탕(제목이 다 나온 순간의 장면)과 같아야 한다.
    오프닝 기사 카드 → 지도(깜박임) → 어둡게 → 제목 같은 끼어든 장면 = hard. 바탕 판정은 0.1초 간격."""
    out = []
    for c in P.plan.cards:
        if c.kind != "title":
            continue
        base = _title_backdrop(P, c.t0 + 0.7)   # 제목 덮개가 다 나온 순간(fullcards 페이드 0.7초)
        seen = [(round(c.t0 - 1.0 + 0.1 * k, 2), _title_backdrop(P, c.t0 - 1.0 + 0.1 * k)) for k in range(11)]
        bad = [(t, b) for t, b in seen if t >= 0 and b != base]
        if bad:
            out.append(f"[title-backdrop] 제목 카드(t={c.t0:.2f}) 바탕 {base!r} 인데 직전 1초에 {bad[0][1]!r}(t={bad[0][0]:.2f}) 장면이 끼어든다 "
                       "— 오프닝 기사 카드가 있으면 그 카드를 제목 끝까지 두어 제목을 그 위에 띄운다(D-0216)")
    return out


def transition_camera(transitions: list, sentences: list, keys: list) -> list[str]:
    """v7.4.0 D-0229 §2.2·§4.4(UF-105) — 시점 전환(plan transitions, 종류 있는 곳)의 호흡 시작 ~ bridge 문장 끝 사이에 시작하는 카메라 이동은
    rules transition.camera_move_min_sec 이상 걸려야 한다(느린 전환). 짧으면 hard. 이동이 없으면(암전·컷) 통과."""
    lim = R_.transition.camera_move_min_sec
    ends = {s.sid: s.t1 for s in sentences}
    out = []
    for tr in transitions:
        if not tr.kind:
            continue
        a, b = tr.pause_t0, ends.get(tr.sid, tr.pause_t0 + tr.pause_sec)
        for k in keys:
            if k.mode == "move" and a <= k.t <= b and k.dur < lim:
                out.append(f"[transition-camera] 시점 전환 {tr.sid}({'·'.join(tr.kind)}) t={k.t:.1f} 카메라 이동 {k.dur:.1f}초 < {lim}초 — 느리게(UF-105)")
    return out


def cutaway_churn(events: list[dict]) -> list[str]:
    """v7.4.0 D-0229 §2.3(UF-110) — 전면 컷어웨이(qa_checks.cutaway_full_types)가 끝난 뒤 지도로 돌아온 시간이
    shot_grammar 의 최소 머무름 초 미만인데 다음 전면 컷어웨이가 시작하면 hard. 붙어 있는(간격 ≤ 0) 둘은 한 장면이라 통과."""
    from engine.shots import min_hold_sec  # noqa: PLC0415

    min_hold = min_hold_sec()
    full = sorted((e for e in events if e["type"] in QA.cutaway_full_types), key=lambda e: e["t0"])
    out = []
    for a, b in zip(full, full[1:]):
        gap = b["t0"] - a["t1"]
        if 0 < gap < min_hold:
            out.append(f"[cutaway-churn] {a['type']} {a.get('mid') or ''}(~{a['t1']:.1f}) → 지도 {gap:.1f}초 → {b['type']} {b.get('mid') or ''}"
                       f"({b['t0']:.1f}~) — 지도 복귀 < {min_hold}초. 같은 문장 묶음이면 한 이벤트로 합치고, 아니면 지도에 머문다(UF-110)")
    return out


def ratio_graphic(sentences: list, events: list[dict]) -> list[str]:
    """v7.4.0 D-0229 §2.6(UF-113) — "N 척 중 M 척" 문장 구간에 비율 그래픽(qa_checks.ratio_graphic_kinds 패널·series)이 없으면 warning."""
    pats = [re.compile(p) for p in QA.ratio_patterns]
    out = []
    for s in sentences:
        if not any(p.search(s.text) for p in pats):
            continue
        if not any(e["t0"] < s.t1 and e["t1"] > s.t0 and (e["type"] == "series" or (e["type"] == "panel" and e.get("kind") in QA.ratio_graphic_kinds))
                   for e in events):
            out.append(f"[ratio-without-graphic] {s.sid} 'N 중 M' 문장인데 그 구간에 {QA.ratio_graphic_kinds}·series 그래픽이 없다 — 점 패널로 조판(UF-113): {s.text[:40]}")
    return out


NEW_ELEMENT_TYPES = ("card", "photo", "clip", "cutout", "route", "panel", "flight", "badge", "article", "marker", "quote", "cascade", "boom",
                     "post", "primitive", "backdrop", "island", "ships", "barrier", "country")   # [static-camera] — 등장하면 화면이 바뀐 것


def static_windows(times: list[float], track: list[tuple[float, float, float]], starts: list[float],
                   covered: Callable[[float], bool]) -> list[tuple[float, float]]:
    """v7.4.0 D-0241 §1(UF-120) — 화면 카메라(center x·y·w)가 rules camera.static_eps 안에 머물고 새 요소 등장(starts)도 없는
    rules camera.static_max_sec 이상 구간 [(시작, 끝)]. 지도가 가려진 시각(covered)은 구간을 끊는다."""
    C = R_.camera  # noqa: N806
    out: list[tuple[float, float]] = []
    i0 = None
    for i, t in enumerate(times):
        if covered(t) or any(times[max(0, i - 1)] < s <= t for s in starts):
            i0 = None if covered(t) else i
            continue
        if i0 is None:
            i0 = i
            continue
        x0, y0, w0 = track[i0]
        x, y, w = track[i]
        if abs(w - w0) / w0 > C.static_eps.w_rel or math.hypot(x - x0, y - y0) / w0 > C.static_eps.center_rel:
            i0 = i
            continue
        if t - times[i0] >= C.static_max_sec and (not out or out[-1][0] != times[i0]):
            out.append((times[i0], t))
        elif out and out[-1][0] == times[i0]:
            out[-1] = (times[i0], t)
    return out


def check_static_camera(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0241 §1 — [static-camera] hard(정지 구간) + [drift-too-fast] hard(drift 숏 속도 > rules camera.drift_speed_max)."""
    from engine.camera import screen_track, speed  # noqa: PLC0415

    if P.cams is None:
        return []
    C = R_.camera  # noqa: N806
    step = 0.5
    times = [round(k * step, 3) for k in range(int(P.plan.total / step))]
    idx = [min(P.n_frames - 1, int(t * FPS)) for t in times]
    tr = screen_track(P.R.stage, P.cams[idx])
    starts = sorted(e["t0"] for e in P.events if e["type"] in NEW_ELEMENT_TYPES)
    out = [f"[static-camera] {a:.1f}~{b:.1f}초({b - a:.0f}초) 카메라가 멈추고 새 화면 요소도 없다 — 숏 mode drift(느린 궤도 훑기)·카드·사진으로 "
           f"화면을 바꾼다(rules camera.static_max_sec {C.static_max_sec:g}, UF-120)"
           for a, b in static_windows(times, [tuple(x) for x in tr], starts, lambda t: _covered(P, t) or P.R.tb.in_fullcard(t))]
    full = screen_track(P.R.stage, P.cams)
    sp = speed(full, (), FPS)
    for k in P.keys:
        if k.mode != "drift":
            continue
        a, b = int(k.t * FPS), min(len(sp["pan"]), int((k.t + k.dur) * FPS))
        if b <= a:
            continue
        pan, zoom = float(sp["pan"][a:b].max()), float(sp["zoom"][a:b].max())
        if pan > C.drift_speed_max.pan_w_per_sec * 1.02 or zoom > C.drift_speed_max.zoom_per_sec * 1.02:
            out.append(f"[drift-too-fast] drift t={k.t:.1f}~{k.t + k.dur:.1f}초 pan {pan:.3f}화면 폭/초·zoom {zoom:.3f}/초 > "
                       f"{C.drift_speed_max.pan_w_per_sec}·{C.drift_speed_max.zoom_per_sec} — dur 를 늘리거나 이동 폭을 줄인다")
    return out


def route_speeds(P) -> list[tuple[dict, float, float]]:  # noqa: ANN001, N803
    """경로마다 (이벤트, 화면 길이 px, 평균 grow 속도 px/초) — 길이는 grow 가 끝나는 순간의 카메라로 잰다(설계 480p 좌표)."""
    out = []
    for e in P.events:
        if e["type"] != "route" or e.get("in_island") or not e.get("world_pts") or e.get("grow", 0) <= 0.05:
            continue
        t = min(P.plan.total, e["t0"] + e["grow"])
        v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
        pts = [v.to_screen(*p) for p in e["world_pts"]]
        n = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        out.append((e, n, n / e["grow"]))
    return out


def check_route_speed(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0241 §4(UF-123) — 경로 grow 평균 속도 > rules route_speed.grow_speed_max_px_s 면 hard.
    골든 기준 연출(story_geo_exempt — 사용자 합격본만, tests/test_story_geo 가 범위 강제)은 보지 않는다(합격 경로 75~217px/초, 바꾸면 골든 컷이 바뀐다)."""
    if P.cams is None or P.R.cache.get("story_geo_exempt"):
        return []
    lim = R_.route_speed.grow_speed_max_px_s
    return [f"[route-too-fast] 경로 {e.get('label') or 'route'!r} t={e['t0']:.1f} 화면 {n:.0f}px 를 {e['grow']:.1f}초에 — {v:.0f}px/초 > {lim:g}. "
            f"grow ≥ {n / lim:.1f}초로(문장이 짧으면 end 를 다음 문장까지)"
            for e, n, v in route_speeds(P) if v > lim]


@lru_cache(maxsize=4)
def _land_world(stage_key: tuple, to_world: Callable, from_world: Callable) -> object:  # noqa: ANN001
    from shapely.geometry import box  # noqa: PLC0415
    from shapely.ops import transform, unary_union  # noqa: PLC0415

    land = unary_union(list(_land_polygons().values()))
    if stage_key:   # 무대 경계(월드) → 경위도 상자로 먼저 자른다(극지방 투영 불가·속도)
        a, b = from_world(stage_key[0] - 1, stage_key[1] - 1), from_world(stage_key[2] + 1, stage_key[3] + 1)   # 월드 여백 1
        land = land.intersection(box(a["lon"], a["lat"], b["lon"], b["lat"]))
    else:
        land = land.intersection(box(-180, -80, 180, 84))   # 메르카토르는 극지방을 그리지 않는다
    return transform(lambda xs, ys, zs=None: tuple(zip(*(to_world(lon=x, lat=y) for x, y in zip(xs, ys)))), land)


def sea_ok_windows(P) -> list[tuple[float, float]]:  # noqa: ANN001, N803
    """숏 allow_sea(사유) 구간 — 그 숏 시각부터 다음 숏까지(v7.4.0 D-0242)."""
    from engine.direction import load_direction_doc, resolve_anchor  # noqa: PLC0415

    p = P.root / "direction.yaml"
    if not p.exists():
        return []
    shots = sorted(((resolve_anchor(s.at, P.R.tb), s.allow_sea) for s in load_direction_doc(p).shots), key=lambda x: x[0])
    return [(t, shots[i + 1][0] if i + 1 < len(shots) else P.plan.total) for i, (t, why) in enumerate(shots) if why]


def land_ratios(P) -> list[tuple[float, float]]:  # noqa: ANN001, N803
    """지도 프레임 육지 비율 [(t, 비율)] — rules camera.land_sample_sec 간격, 지도가 가려진 시각·기사·인용 전면 시각은 뺀다."""
    from shapely.geometry import box  # noqa: PLC0415

    st = P.R.stage
    land = _land_world(tuple(getattr(st, "bounds", ()) or ()), st.to_world, st.from_world)
    out = []
    t = 0.0
    while t < P.plan.total:
        if not (_covered(P, t) or any(e["type"] in ("article", "quote") and e["t0"] <= t <= e["t1"] for e in P.events)):
            v = View(st, P.cams[min(P.n_frames - 1, int(t * FPS))])
            r = box(v.x0, v.y1 - v.h, v.x0 + v.w, v.y1)
            out.append((round(t, 2), land.intersection(r).area / r.area))
        t += R_.camera.land_sample_sec
    return out


def check_sea_only(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0242(UF-125) — 지도 프레임 육지 비율 < rules camera.land_min_ratio 면 hard(숏 allow_sea 사유 구간 제외). 연속 구간은 한 줄."""
    if not _map_main(P) or P.cams is None:
        return []
    lim, ok = R_.camera.land_min_ratio, sea_ok_windows(P)
    bad = [(t, r) for t, r in land_ratios(P) if r < lim and not any(a <= t < b for a, b in ok)]
    out, run = [], []
    for t, r in bad + [(math.inf, 1.0)]:
        if run and t - run[-1][0] > R_.camera.land_sample_sec * 1.5:
            out.append(f"[sea-only-frame] {run[0][0]:.0f}~{run[-1][0]:.0f}초 육지 비율 최소 {min(x[1] for x in run):.2f} < {lim:g} — 해안선 쪽으로 "
                       "중심을 옮기거나(육지·도시 라벨이 화면 한쪽에) 바다가 주제면 그 숏에 allow_sea 사유")
            run = []
        if t != math.inf:
            run.append((t, r))
    return out


def unit_ton_hits(events: list[dict]) -> list[tuple[str, str]]:
    """v7.4.0 D-0241 §3(UF-122) — 연출 문자열(카드·패널·마커·경로 이름표)에 숫자 뒤 t(rules data.unit_ton_pattern)가 남은 곳 [(이벤트 종류, 문자열)]."""
    pat = R_.data.unit_ton_pattern
    if not pat:
        return []
    rx = re.compile(pat)
    skip = {"type", "mid", "pid", "img", "flag", "press", "src", "col", "accent", "side", "kind", "icon", "theme", "place"}
    out: list[tuple[str, str]] = []

    def walk(o: object, typ: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in skip:
                    walk(v, typ)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v, typ)
        elif isinstance(o, str) and rx.search(o):
            out.append((typ, o))

    for e in events:
        walk(e, e["type"])
    return out


def badge_orphans(events: list[dict]) -> list[str]:
    """v7.4.0 D-0240 §4 — 국기 뱃지(kind flag)가 카드·인용(시간 겹침 ≥ 절반)이나 같은 시각 마커(rules layout_480p.badge.anchor_marker_deg 안)에
    붙지 않고 홀로 뜨면 warning. 규칙 flag_requires_anchor 가 꺼져 있으면 보지 않는다."""
    B = R_.layout_480p.badge  # noqa: N806
    if not B.flag_requires_anchor:
        return []
    out = []
    for b in events:
        if b["type"] != "badge" or b.get("kind") != "flag" or b.get("over_panel"):
            continue
        dur = max(1e-6, b["t1"] - b["t0"])
        held = any(c["type"] in ("card", "quote") and min(b["t1"], c["t1"]) - max(b["t0"], c["t0"]) >= dur / 2 for c in events)
        bw = b.get("world")   # 무대 월드 좌표(투영은 무대만, 15 P1) — 메르카토르 월드 단위 ≈ 경도 1°
        near = bw is not None and any(
            m["type"] == "marker" and m["t0"] < b["t1"] and m["t1"] > b["t0"] and m.get("world") is not None
            and math.dist(m["world"], bw) <= B.anchor_marker_deg for m in events)
        if not (held or near):
            out.append(f"[badge-orphan] 국기 뱃지 {b.get('label')!r}({str(b.get('flag')).upper()}) t={b['t0']:.1f} — 카드·인용·마커에 붙지 않고 홀로 뜬다. "
                       "빼고 country 강조·지명 라벨로 채운다(rules layout_480p.badge.flag_requires_anchor)")
    return out


def check_inset_clipped(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0240 §2 — 위성 인셋 원+출처 줄이 안전 영역(날짜 배지 아래·자막 띠 위·좌우 여백, engine.layers.flight.inset_safe)을
    벗어나면 hard(side_order 대체 자리까지 다 벗어남). 0.5초 간격, 인셋마다 첫 시각 한 줄."""
    from engine.layers.flight import inset_alpha, inset_box, inset_fits  # noqa: PLC0415

    if not _map_main(P):
        return []
    out: list[str] = []
    for e in P.events:
        if e["type"] != "flight" or not e.get("inset"):
            continue
        t = e["t0"]
        while t <= e["t1"]:
            if inset_alpha(t, e) > 0.5:
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                box = inset_box(e, *v.to_screen(*e["world"]), t)
                if not inset_fits(box):
                    out.append(f"[inset-clipped] 인셋 {e['inset'].get('mid')} t={t:.1f} 원·출처 줄이 안전 영역 밖(상자 {tuple(round(x) for x in box)}) — "
                               "카메라 구도를 넓히거나 표적이 화면 가장자리에 오지 않게 한다(rules flight.inset.side_order 대체 자리도 모두 밖)")
                    break
            t += 0.5
    return out


def inset_centers(P, e: dict) -> list[tuple[int, float, float]]:  # noqa: ANN001, N803
    """인셋이 보이는 프레임마다 (프레임, 원 중심 x, y) — 렌더와 같은 inset_box(궤적 포함)."""
    from engine.layers.flight import inset_alpha, inset_box  # noqa: PLC0415

    out = []
    for i in range(max(0, int(e["t0"] * FPS)), min(P.n_frames, int(e["t1"] * FPS) + 1)):
        t = i / FPS
        if inset_alpha(t, e) > 0:
            x, y, w, h = inset_box(e, *View(P.R.stage, P.cams[i]).to_screen(*e["world"]), t)
            out.append((i, x + w / 2, y + h / 2))
    return out


def check_inset_jump(P) -> list[str]:  # noqa: ANN001, N803
    """[inset-jump] hard(v7.4.0 back_and_forth D-0300, 사용자 의견 UF-146 "위성사진을 보여주는 동그라미가 한순간 위치를 옮기고 사라져") —
    위성 인셋 원 중심의 연속 프레임 간 이동이 rules flight.inset.jump_px_max 를 넘으면 실패(자리 옮김은 move_sec 보간만)."""
    if not _map_main(P) or P.cams is None:
        return []
    mx = R_.flight.inset.jump_px_max
    out = []
    for e in P.events:
        if e["type"] != "flight" or not e.get("inset"):
            continue
        c = inset_centers(P, e)
        for (fa, xa, ya), (fb, xb, yb) in zip(c, c[1:]):
            d = math.hypot(xb - xa, yb - ya)
            if fb == fa + 1 and d > mx:
                out.append(f"[inset-jump] 인셋 {e['inset'].get('mid')} t={fb / FPS:.2f} 원이 한 프레임에 {d:.0f}px 이동 > {mx:g} — 자리는 등장 때 고정, 옮기면 보간(D-0300)")
                break
    return out


def check_inset_side_change(P) -> list[str]:  # noqa: ANN001, N803
    """[inset-side-change] warning(v7.4.0 D-0300) — 인셋 자리가 바뀐 횟수(보간 이동). 카메라 구도로 줄일 수 있는지 사람이 본다."""
    return [f"[inset-side-change] 인셋 {e['inset'].get('mid')} 자리 {len(e['inset_track']['moves'])}번 옮김 "
            + ", ".join(f"t={f / FPS:.1f} {a}→{b}" for f, a, b in e["inset_track"]["moves"])
            for e in P.events if e["type"] == "flight" and (e.get("inset_track") or {}).get("moves")]


def check_badge_clipped(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0244 — 지도 뱃지 원(R)이 안전 영역(인셋과 같은 여백 flight.inset.safe_margin_px: 화면 가장자리·자막 띠 위·날짜 배지 상자와
    겹치지 않음)을 벗어나거나, 위 가장자리 보정(edge_nudge 아래로)에 기대 화면 안에 붙어 있으면 hard — 앵커가 화면 위끝에 걸치면 보정이
    앵커 위치에 따라 꺼져 원이 반쯤 잘린다(offscreen 이 통과시킨 결함). 윗변은 날짜 배지 상자만 막고 좌우 보정은 허용한다 — 골든 v3
    인물 뱃지(상단·좌측 가장자리, 사용자 합격)가 그렇게 놓였기 때문. 위치는 렌더러와 같은 place_badge(가장자리 보정·카드 회피·고정 이동) 뒤.
    0.25초 간격+끝 프레임, 알파 > 0.5, 뱃지마다 첫 시각 한 줄."""
    from engine.layers.badges import badge_box, badge_R, edge_nudge, place_badge, screen_xy  # noqa: PLC0415
    from engine.framing import default_reserve  # noqa: PLC0415
    from engine.layers.flight import F as FL  # noqa: PLC0415
    from engine.reserved import card_zones  # noqa: PLC0415
    from engine.style import BADGE  # noqa: PLC0415
    from engine.timebase import window  # noqa: PLC0415

    if not _map_main(P):
        return []
    m = FL.inset.safe_margin_px
    sx0, sy0, sx1, sy1 = m, m, W_OUT - m, R_.layout_480p.reserved_zones.subtitle.y_from - m
    db = default_reserve()[0]
    db = (db[0] - m, db[1], db[2], db[3] + m)
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    for e in P.events:
        if e["type"] != "badge" or e.get("over_panel"):
            continue
        ts = [e["t0"] + k * 0.25 for k in range(int((e["t1"] - e["t0"]) / 0.25) + 1)] + [e["t1"] - 1.0 / FPS]   # 끝 프레임까지(D-0244: 끝에 걸림)
        for t in ts:
            if window(t, e["t0"], e["t1"], BADGE.fade_in_sec, BADGE.fade_out_sec) > 0.5 and not _covered(P, t):
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                x, y = screen_xy(e, v)
                dx, dy, ka = place_badge(ctx, e, x, y, t, card_zones(ctx, P.events, t))
                ey = edge_nudge(badge_box(ctx, e, x, y, t), x, y)[1]   # 위 가장자리에서 아래로 민 보정 = 앵커가 화면 위끝에 걸침(D-0244)
                cx, cy, r = x + dx, y + dy, badge_R(e, t)
                on_date = cx + r > db[0] and cy - r < db[3]
                if ka > 0.5 and (cx - r < sx0 or cy - r < sy0 or cx + r > sx1 or cy + r > sy1 or on_date or (ey > 0 and cy - ey - r < sy0)):
                    out.append(f"[badge-clipped] 뱃지 {e.get('flag') or e.get('kind')} '{e.get('label', '')}' t={t:.1f} 원이 안전 영역 밖"
                               f"{'(위 가장자리 보정에 기댐)' if ey > 0 and cy - ey - r < sy0 else ''}(중심 {cx:.0f},{cy:.0f} R {r:.0f}, 영역 {tuple(round(q) for q in (sx0, sy0, sx1, sy1))}, 날짜 배지 {tuple(round(q) for q in db)}) — 앵커를 화면 안쪽 육지로 옮기거나 구도를 넓힌다")
                    break
    return out


# v7.4.0 D-0245(UF-126 "그래프들 왜 다 사라졌어?") — 지정 시리즈·이전 승인 데이터 패널의 조용한 드롭 금지(P6)
def data_records(events: list[dict]) -> set[str]:
    """연출 이벤트가 그리는 데이터 레코드 id — 패널 series[].record·record, series 레이어 series_id."""
    out: set[str] = set()
    for e in events:
        if e.get("type") not in ("panel", "series"):
            continue
        for k in ("record", "series_id"):
            if isinstance(e.get(k), str):
                out.add(e[k])
        for ser in e.get("series") or []:
            if isinstance(ser, dict) and ser.get("record"):
                out.add(ser["record"])
    return out


def order_series(proj: "Path | None") -> list[str]:
    """프로젝트 주문 order.yaml data.series(구조 필드) — 연출이 패널로 그려야 하는 시리즈. 주문이 없으면 []."""
    if proj is None:
        return []
    from genres.load import load_order  # noqa: PLC0415

    o = load_order(proj)
    return list(o.data.series) if o is not None else []


def prior_panel_records(proj: "Path | None") -> set[str]:
    """이전 승인 연출(track_v*/direction.yaml)의 데이터 패널 레코드. 연출 초안(direction.v1.yaml 등)은 승인본이 아니라 보지 않는다."""
    import yaml  # noqa: PLC0415

    if proj is None:
        return set()
    out: set[str] = set()
    for f in sorted(proj.glob("track_v*/direction.yaml")):
        out |= data_records([e for e in yaml.safe_load(f.read_text(encoding="utf-8")).get("events", []) if e.get("type") == "panel"])
    return out


def _dropped(drops: list[dict]) -> set[str]:
    return {d["record"] for d in drops or [] if d.get("record") and (d.get("reason") or "").strip()}


def series_unused(want: list[str], events: list[dict], drops: list[dict]) -> list[str]:
    have, skip = data_records(events), _dropped(drops)
    return [r for r in want if r not in have and r not in skip]


def panels_dropped(prior: set[str], events: list[dict], drops: list[dict]) -> list[str]:
    have, skip = data_records(events), _dropped(drops)
    return sorted(r for r in prior if r not in have and r not in skip)


def check_series_unused(P) -> list[str]:  # noqa: ANN001, N803
    """[series-unused] hard — order.yaml data.series 의 시리즈가 연출 어느 패널에도 없다(direction drops 사유만 예외)."""
    miss = series_unused(order_series(P.root), P.events, P.R.cache.get("direction_drops", []))
    return [f"[series-unused] 주문 시리즈 {r} 를 그리는 패널이 없다 — 패널(dual_line 등 series.record)로 그리거나 direction.yaml drops 에 "
            f"record·사유를 적는다(UF-126)" for r in miss]


def check_panel_dropped(P) -> list[str]:  # noqa: ANN001, N803
    """[panel-dropped] hard — 이전 승인 연출(track_v*)에 있던 데이터 패널 레코드가 새 연출에 없다(direction drops 사유만 예외)."""
    miss = panels_dropped(prior_panel_records(P.root), P.events, P.R.cache.get("direction_drops", []))
    return [f"[panel-dropped] 이전 승인 연출의 데이터 패널 {r} 가 새 연출에 없다 — 다시 넣거나 direction.yaml drops 에 사유(UF-126)" for r in miss]


# v7.4.0 D-0248·D-0249 — 덮개 종류는 rules qa_checks.card_over_panel.cover_types·cover_types_on_data_panels(P3)


def panel_box() -> tuple[float, float, float, float]:
    """패널 상자(설계 좌표) — 화면 가운데 panel.min_screen_use 폭, 제목 위 ~ 자막 띠 위. 모든 kind 공통(보수값)."""
    pl = R_.layout_480p.panel
    m = W_OUT * (1 - pl.min_screen_use) / 2
    return m, pl.title_y - pl.title_size, W_OUT - m, R_.layout_480p.reserved_zones.subtitle.y_from


def cards_over_panel(events: list[dict], boxes: "Callable[[dict], list[tuple] | None]") -> list[tuple[dict, dict, float]]:
    """(덮는 요소, 패널, 겹친 시작 시각). boxes(e) = 그 요소의 제자리 화면 상자들(None = 화면 전체 덮개로 본다)."""
    cfg = R_.qa_checks.card_over_panel
    if cfg is None:
        return []
    fade = R_.layout_480p.panel.fade_sec
    pad = cfg.panel_pad_px
    px0, py0, px1, py1 = panel_box()
    out = []
    for p in (e for e in events if e["type"] == "panel"):
        a, b = p["t0"] + fade, p["t1"] - fade
        kinds = set(cfg.cover_types) | (set(cfg.cover_types_on_data_panels) if data_records([p]) else set())
        if p.get("kind") == "versus":
            kinds.discard("badge")   # badge_over_panel 이 보고한다(중복 없음)
        for e in events:
            if e["type"] not in kinds:
                continue
            ov = min(b, e["t1"]) - max(a, e["t0"])
            if ov <= cfg.min_overlap_sec:
                continue
            bx = boxes(e)
            if bx is None or any(x0 < px1 + pad and x1 > px0 - pad and y0 < py1 + pad and y1 > py0 - pad for x0, y0, x1, y1 in bx):
                out.append((e, p, max(a, e["t0"])))
    return out


def check_card_over_panel(P) -> list[str]:  # noqa: ANN001, N803
    """[card-over-panel] hard(v7.4.0 D-0248·UF-129) — 패널이 떠 있는 동안 카드·기사·사진 등이 패널 상자를 덮는다. 연출에서 패널 앞에 끝내거나 뒤에 시작."""
    from engine.cascade import cascade_boxes  # noqa: PLC0415
    from engine.reserved import card_box  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def boxes(e: dict) -> "list[tuple] | None":
        if e["type"] in ("card", "primitive"):
            return [tuple(card_box(ctx, e))]
        if e["type"] == "cascade":
            return [tuple(b) for t in (e["t0"] + 1.0, (e["t0"] + e["t1"]) / 2) for b in cascade_boxes(t, e)]
        return None   # 기사·인용·사진·영상·컷아웃·뱃지 = 화면 덮개로 본다(시간 겹침, D-0249)

    return [f"[card-over-panel] {e['type']} {e.get('tag') or e.get('mid') or e.get('title') or ''!s} t={t:.1f} — 패널 {p.get('kind')} {p.get('title')!r} 위. "
            "패널 앞에 끝내거나 뒤에 시작한다(UF-129)" for e, p, t in cards_over_panel(P.events, boxes)] + [
        f"[card-over-panel] {e['type']} {e.get('tag') or e.get('label') or e.get('mid') or e.get('title') or ''!s} t={t:.1f} — 시간축 틀 안 시리즈 레인 "
        f"{lane} 위({ov:.1f}초). 사건 레인·틀 밖 자리로 옮기거나 뺀다(UF-129, D-0259)" for e, lane, t, ov in timeline_lanes_covered(P)]


TIMELINE_COVER_STEP_SEC = 0.1   # 시간축 틀 덮개 표본 간격(label_hidden 과 같은 값)


def timeline_cover_box(P, ctx: cairo.Context, e: dict, t: float) -> "list[tuple] | None":  # noqa: ANN001, N803
    """시간축 주 무대에서 덮개의 제자리 화면 상자(설계 px). None = 화면 덮개로 본다(컷아웃 — D-0249 와 같은 보수값)."""
    from engine.cascade import cascade_boxes  # noqa: PLC0415
    from engine.media_plan import media_box  # noqa: PLC0415
    from engine.reserved import card_box  # noqa: PLC0415

    if e["type"] in ("card", "primitive"):
        return [tuple(card_box(ctx, e))]
    if e["type"] == "cascade":
        return [tuple(b) for b in cascade_boxes(t, e)]
    if e["type"] in ("photo", "clip") and "x" in e and e.get("mid") in P.R.assets.media_assets:
        return [tuple(media_box(e, P.R.assets.media_assets))]
    if e["type"] == "badge":
        r = place_over(P, ctx, e, t)
        return [] if r is None else [r[1]]
    return None


def series_lane_rects(P, t: float) -> list[tuple[str, tuple]]:  # noqa: ANN001, N803
    """시각 t 에 레코드가 그려지는 시리즈 레인의 화면 상자 — x = 틀 좌우, y = 레인 띠(시간축 주 무대에 틀이 있을 때만)."""
    st = P.R.stage
    if st.name == "timeline":
        if getattr(st, "frame", None) is None:
            return []
        lanes = list(dict.fromkeys(e["lane"] for e in P.events if e.get("type") == "series" and e.get("lane") and e["t0"] <= t <= e["t1"]))
        if not lanes:
            return []
        fx, _, fw, _ = st.frame
        v = View(st, P.cams[min(P.n_frames - 1, max(0, int(t * FPS)))])
        return [(ln, (fx, st.lane_screen(v, st.lane_index(ln))[0], fx + fw, st.lane_screen(v, st.lane_index(ln))[1])) for ln in lanes]
    chart = (getattr(P.R, "cache", None) or {}).get("island_chart")   # v7.4.0 — 차트 아일랜드도 같은 장치(C12 §3, UF-129)
    isl = next((e for e in P.events if e.get("type") == "island" and e.get("kind") == "chart" and e["t0"] <= t <= e["t1"]), None)
    if not chart or isl is None:
        return []
    from engine.island import chart_view, island_box  # noqa: PLC0415

    bx, by, bw, bh = island_box(isl)
    cst = chart["stage"]
    v = chart_view(chart, t, (bx, by, bw, bh))
    lanes = list(dict.fromkeys(e["lane"] for e in chart["events"] if e.get("type") == "series" and e.get("lane") and e["t0"] <= t <= e["t1"]))
    out = []
    for ln in lanes:
        top, bot = cst.lane_screen(v, cst.lane_index(ln))
        out.append((ln, (bx, by + top, bx + bw, by + bot)))
    return out


def timeline_lanes_covered(P, boxes: "Callable[[dict, float], list[tuple] | None] | None" = None) -> list[tuple[dict, str, float, float]]:  # noqa: ANN001, N803
    """(덮개, 시리즈 레인, 처음 겹친 시각, 겹친 시간) — v7.4.0 D-0259(UF-129 미보호 경로). 덮개 = rules
    qa_checks.card_over_panel.timeline_frame_cover_types, 시간 겹침 > min_overlap_sec 이면 보고. 사건 레인(레코드 없음)은 허용.
    boxes(e, t) = 덮개 제자리 상자(기본 timeline_cover_box)."""
    cfg = R_.qa_checks.card_over_panel
    if cfg is None or not cfg.timeline_frame_cover_types or chart_world(P) is None:
        return []
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    pad = cfg.panel_pad_px
    out = []
    for e in P.events:
        if e["type"] not in cfg.timeline_frame_cover_types:
            continue
        hits: dict[str, list[float]] = {}
        t = e["t0"]
        while t <= e["t1"]:
            bx = boxes(e, t) if boxes else timeline_cover_box(P, ctx, e, t)
            for ln, (x0, y0, x1, y1) in series_lane_rects(P, t):
                if bx is None or any(a < x1 + pad and c > x0 - pad and b < y1 + pad and d > y0 - pad for a, b, c, d in bx):
                    hits.setdefault(ln, []).append(t)
            t += TIMELINE_COVER_STEP_SEC
        for ln, ts in hits.items():
            ov = len(ts) * TIMELINE_COVER_STEP_SEC
            if ov > cfg.min_overlap_sec:
                out.append((e, ln, ts[0], ov))
    return out


# v7.4.0 D-0250(UF-130 "기사 조판과 자막 나래이션이 다름") — 기사 카드 매체 ↔ 그 구간 문장의 매체 이름
def _outlet_pat(name: str) -> "re.Pattern[str]":
    return re.compile(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])" if re.search("[A-Za-z]", name) else re.escape(name))


def outlet_of(asset: dict) -> "str | None":
    """미디어 레지스트리 기사 → 매체 id(rules qa_checks.outlet_names — url 도메인 우선, 다음 credit_author 이름)."""
    from urllib.parse import urlparse  # noqa: PLC0415

    host = urlparse(asset.get("url") or "").netloc.lower()
    who = asset.get("credit_author") or asset.get("author") or ""
    for oid, o in R_.qa_checks.outlet_names.items():
        if any(host == d or host.endswith("." + d) for d in o.domains):
            return oid
    for oid, o in R_.qa_checks.outlet_names.items():
        if any(_outlet_pat(n).search(who) for n in o.names):
            return oid
    return None


def outlets_named(text: str) -> set[str]:
    return {oid for oid, o in R_.qa_checks.outlet_names.items() if any(_outlet_pat(n).search(text) for n in o.names)}


def outlet_mismatches(events: list[dict], sentences: list[tuple[str, float, float, str]], assets: dict) -> list[tuple[dict, str, set, "str | None"]]:
    """(기사 이벤트, 문장 sid, 문장에 나온 매체, 카드 매체) — 문장이 매체를 말하는데 카드 매체가 그 안에 없을 때."""
    lim = R_.qa_checks.outlet_min_overlap_sec
    out = []
    for e in events:
        if e.get("type") != "article" or not e.get("mid"):
            continue
        card = outlet_of(assets.get(e["mid"]) or {})
        for sid, a, b, text in sentences:
            if min(b, e["t1"]) - max(a, e["t0"]) < lim:
                continue
            named = outlets_named(text)
            if named and card not in named:
                out.append((e, sid, named, card))
    return out


def check_article_outlet(P) -> list[str]:  # noqa: ANN001, N803
    """[article-outlet-mismatch] hard — 기사 카드가 떠 있는 문장이 다른 매체를 말한다(UF-130)."""
    from engine.media_registry import cached_registry  # noqa: PLC0415

    reg = {k: v.model_dump() for k, v in cached_registry().items()}
    sents = [(s.sid, s.t0, s.t1, s.text) for s in P.plan.sentences]
    return [f"[article-outlet-mismatch] 기사 {e['mid']}(매체 {card or '미등재'}) — {sid} 문장은 {', '.join(sorted(named))} 를 말한다. "
            "그 매체의 기사로 바꾸거나 매체 이름이 없는 문장으로 옮긴다(UF-130)" for e, sid, named, card in outlet_mismatches(P.events, sents, reg)]


def check_press_credit(P, times: list[float], drawn: list[tuple[str, float, str | None, str]]) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0240 §3 — 기사 카드 press 가 공식 사진(A)이면 자료사진 출처 줄이 있어야 한다(G4 자료사진 표기). 출처 줄을 만들 수 없거나
    (규칙 article_card.press_photo_credit 없음) 프레스 사진이 보이는 프리뷰 컷에 그 줄이 그려지지 않았으면 hard."""
    from engine.layers.article import article_phase, press_photo_credit_text  # noqa: PLC0415
    from engine.media_registry import cached_registry  # noqa: PLC0415
    from engine.style import ARTICLE  # noqa: PLC0415

    out: list[str] = []
    for e in P.events:
        if e["type"] != "article" or not e.get("press"):
            continue
        a = cached_registry().get(e["press"])
        if a is None or a.press_of is not None:
            continue
        s = press_photo_credit_text(e) if ARTICLE.press_photo_credit is not None else None
        if not s:
            out.append(f"[press-credit-missing] 기사 {e['mid']} press {e['press']} — 자료사진 출처 줄을 만들 수 없다(rules article_card.press_photo_credit)")
            continue
        for t in times:
            if article_phase(t, e)[0] > 0.5 and not any(lab == f"t={t:.2f}" and txt == s for lab, _, _, txt in drawn):
                out.append(f"[press-credit-missing] 기사 {e['mid']} t={t:.2f} press 사진에 출처 줄 {s!r} 이 그려지지 않았다")
                break
    return out


def check_inset_overlap(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0229 §2.7·§2.10(UF-107, v1 관찰 "인셋 출처 줄과 마커 라벨 겹침") — 위성 인셋 원+출처 줄이 마커·경로 이름표나
    (카드가 떠 있을 때) 카드 자리·날짜 배지와 겹치면 warning. 0.5초 간격, 인셋마다 첫 시각 한 줄. 자리는 inset.side(대각 포함)로 옮긴다."""
    from engine.framing import default_reserve  # noqa: PLC0415
    from engine.layers.flight import F as FL  # noqa: PLC0415
    from engine.layers.flight import inset_alpha, inset_box  # noqa: PLC0415

    if not _map_main(P):
        return []
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    for e in P.events:
        if e["type"] != "flight" or not e.get("inset"):
            continue
        t, hit = e["t0"], None
        while t <= e["t1"] and hit is None:
            if inset_alpha(t, e) > 0.5:
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                x, y, w, h = inset_box(e, *v.to_screen(*e["world"]), t)
                box = (x, y, x + w, y + h + FL.inset.caption_dy)
                card = any(c["type"] == "card" and c["t0"] <= t <= c["t1"] for c in P.events)
                for name, b in _place_label_boxes(ctx, P, v, t) + [("카드·날짜 자리", b) for b in default_reserve(card=card)]:
                    if _overlap_px(box, b) > 0:
                        hit = (t, name)
                        break
            t += 0.5
        if hit is not None:
            out.append(f"[inset-overlap] 위성 인셋 {e['inset'].get('mid')} t={hit[0]:.1f} 가 {hit[1]!r} 와 겹침 — inset.side 를 빈 쪽(대각 포함)으로")
    return out


from script.lint import tempo_density  # noqa: E402 — v7.4.0(원고·검사 같은 함수)


def check_unit_glyph_font(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0229 §2.4(UF-111) — display 글꼴(GmarketSans)로 그린 문자열에 라틴 소문자가 남으면 hard(십자형 t).
    단위 꼬리는 typography.unit_split 이 rules fonts.unit_font 로 떼어 그린다. 기록 = 프리뷰 컷마다 typography.DISP_LATIN."""
    seen: dict[str, str] = {}
    for lab, s in P.R.cache.get("disp_latin") or []:
        seen.setdefault(s, lab)
    return [f"[unit-glyph-font] {lab} display 글꼴 문자열 {s[:40]!r} 에 라틴 소문자 — 단위는 숫자 뒤 꼬리로 두거나(unit_font) 한글로 쓴다(UF-111)"
            for s, lab in seen.items()]


def check_card_exposure(P) -> list[str]:  # noqa: ANN001, N803
    """기사·인용 카드 완전 노출(v5.21.10 D-0191 §1-2) — 그리기와 같은 구간 함수(article_full_span·quote_full_span)로
    완전 불투명 구간 < qa_checks.card_full_exposure_min_sec 이면 카드마다 한 줄."""
    from engine.layers.article import article_full_span  # noqa: PLC0415
    from engine.quote import quote_full_span  # noqa: PLC0415

    span = {"article": article_full_span, "quote": quote_full_span}
    out = []
    for e in sorted(P.events, key=lambda e: e["t0"]):
        if e["type"] not in span:
            continue
        a, b = span[e["type"]](e)
        if b - a < QA.card_full_exposure_min_sec:
            name = e.get("mid") or e.get("speaker") or ""
            out.append(f"[card-exposure] {e['type']} {name} 완전 노출 {max(0.0, b - a):.2f}초 < {QA.card_full_exposure_min_sec} "
                       f"(t0 {e['t0']:.2f} ~ t1 {e['t1']:.2f}) — 끝을 다음 문장까지 늘리거나 시작을 앞당긴다")
    return out


def check_article_backdrop(P) -> list[str]:  # noqa: ANN001, N803
    """한 영상 안 기사 카드 무대 하나(v5.21.12 D-0193) — 기사 카드 theme(dark·light)가 둘 이상이면 hard.
    사진 없는 카드의 블러 무대 밝기는 그리기가 press_fallback.max_luma 로 묶는다(fallback_gain)."""
    from engine.layers.article import ARTICLE  # noqa: PLC0415

    by: dict[str, list[str]] = {}
    for e in P.events:
        if e["type"] == "article":
            by.setdefault(e.get("theme") or ARTICLE.theme_default, []).append(e.get("mid") or "")
    if len(by) <= 1:
        return []
    return [f"[article-backdrop] 기사 카드 무대가 {len(by)}종 — " + " · ".join(f"{k}: {', '.join(v)}" for k, v in sorted(by.items()))
            + " — 한 영상 안 기사 카드 theme 은 하나"]


def _norm_quote(s: str) -> str:
    """공백·문장부호를 뗀 비교용 글자열(한글·영숫자만)."""
    return re.sub(r"[^0-9A-Za-z가-힣]", "", s)


def check_quote_in_script(P) -> list[str]:  # noqa: ANN001, N803
    """인용 ⊂ 화면 원고(v5.21.13 D-0194, 사용자 의견 "나레이션과 화면 따옴표 불일치") — quote 이벤트 text 가 인용이 걸린
    문장들(t0~t1 과 겹치는 문장)의 화면 원고 text 안에 그대로 있어야 한다(정규화 뒤 부분 문자열). 번역 인용도 원고와 같은 번역."""
    out = []
    for e in P.events:
        if e["type"] != "quote":
            continue
        ss = [s for s in P.plan.sentences if s.t0 < e["t1"] and s.t1 > e["t0"]]
        if _norm_quote(e["text"]) not in "".join(_norm_quote(s.text) for s in ss):
            out.append(f"[quote-in-script] 인용 {e.get('speaker')!r} “{e['text']}” 가 그 문장 원고({', '.join(s.sid for s in ss) or '없음'})에 없다 — "
                       "내레이션이 말하는 문구를 그대로 쓰거나, 인용 대신 따옴표 없는 카드로")
    return out


def _story_markers(P, s) -> tuple[list[dict], bool]:  # noqa: ANN001, N803
    """문장 s 가 이름으로 부르는(라벨이 원고에 있는) 지도 마커들과, 문장에 이동·공격 동사가 있는지."""
    RM = QA.route_missing  # noqa: N806
    verb = any(v in s.text for v in RM.move_verbs + RM.attack_verbs)
    ms = [e for e in P.events if e["type"] == "marker" and e.get("label") and "world" in e and not own_pin_label(e)
          and e["t0"] < s.t1 and e["t1"] > s.t0 and e["label"].replace(" ", "") in s.text.replace(" ", "")]
    return ms, verb


def story_geo_report(P) -> dict[str, list[str]]:  # noqa: ANN001, N803
    """v5.21.14 D-0195·D-0197·D-0199 — 문장 단위 지리 정합.
    route_missing(warning)/route_missing_other(hard): 이동·공격 동사 + 문장이 부르는 마커가 있는데 그 마커에 끝점이 닿는 경로가 문장 구간에 없음
    (다른 경로만 보이면 hard — 화면이 사실 방향과 어긋나 오해).
    frame_missing(warning)/frame_missing_target(hard): 문장이 부르는 나라(라벨 점)·마커가 문장 구간 표본 시각 모두 화면 밖(이동·공격 대상이면 hard).
    지도 무대가 아니거나 문장 구간 내내 지도가 가려졌으면(전면 카드·패널·암전·기사·인용) 보지 않는다."""
    if "story_geo" in P.R.cache:
        return P.R.cache["story_geo"]
    RM, FM = QA.route_missing, QA.frame_missing  # noqa: N806
    rep: dict[str, list[str]] = {"route_missing": [], "route_missing_other": [], "frame_missing": [], "frame_missing_target": []}
    if not _map_main(P) or P.cams is None:
        P.R.cache["story_geo"] = rep
        return rep
    if P.R.cache.get("story_geo_exempt"):   # v5.22.1 D-0205 — 골든 기준 연출(사용자 합격본)만, 사유·결정 번호와 함께(테스트가 범위 강제)
        P.R.cache["story_geo"] = rep
        return rep
    names = {}
    codes: dict[str, str] = {}
    lab = getattr(getattr(P.R.stage, "assets", None), "labels", None)
    for k, m, mw in getattr(P.R.stage, "countries", []):
        if mw is not None:
            nm = lab.ko.get(k, m["ko"]) if lab is not None else m["ko"]
            names[nm] = mw
            codes[nm] = str(k).lower()
    for s in P.plan.sentences:
        ms, verb = _story_markers(P, s)
        routes = [e for e in P.events if e["type"] == "route" and not e.get("in_island") and e["t0"] < s.t1 and e["t1"] > s.t0]
        # v7.3.0 D-0206 — flight(출발 → 착탄)도 그 문장의 경로다. 끝점 = world_origin·world(착탄 마커 자리)
        routes += [{"world_pts": [e["world_origin"], e["world"]]} for e in P.events
                   if e["type"] == "flight" and "world_origin" in e and e["t0"] < s.t1 and e["t1"] > s.t0]
        targets = set()
        if verb:
            for m in ms:
                mx, my = m["world"]
                hit = any(min(math.hypot(r["world_pts"][j][0] - mx, r["world_pts"][j][1] - my) for j in (0, -1)) <= RM.endpoint_tol_deg
                          for r in routes)
                if hit:
                    continue
                targets.add(m["label"])
                if routes:
                    rep["route_missing_other"].append(f"[route-missing] {s.sid} 이동·공격 문장의 마커 {m['label']!r} 에 닿는 경로가 없고 다른 경로만 보인다 — "
                                                      "사실 방향과 화면이 어긋난다. 그 마커로 가는 route 를 더하고 다른 경로는 낮춘다")
                else:
                    rep["route_missing"].append(f"[route-missing] {s.sid} 이동·공격 문장의 마커 {m['label']!r} 에 닿는 경로가 없다 — route 를 더한다")
        # 화면 안 여부(문장 구간 표본)
        ts = [t for t in np.arange(s.t0, s.t1, FM.sample_sec) if not _covered(P, t)
              and not any(e["type"] in ("article", "quote") and e["t0"] <= t <= e["t1"] for e in P.events)]
        if not ts:
            continue
        want = {m["label"]: tuple(m["world"]) for m in ms}
        flat = s.text.replace(" ", "")
        want.update({nm: tuple(w) for nm, w in names.items() if len(nm) >= 2 and nm.replace(" ", "") in flat and nm not in want})
        flags = {str(e.get("flag")).lower() for e in P.events if e["type"] in ("badge", "quote") and e.get("flag") and e["t0"] < s.t1 and e["t1"] > s.t0}
        for nm, (wx, wy) in want.items():
            seen = codes.get(nm) in flags   # v5.22.1 D-0205 — 그 나라 국기 뱃지가 문장 구간에 보이면 표시로 인정
            for t in ts:
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                x, y = v.to_screen(wx, wy)
                if FM.margin_px <= x <= W_OUT - FM.margin_px and FM.margin_px <= y <= H_OUT - FM.margin_px:
                    seen = True
                    break
            if not seen:
                key = "frame_missing_target" if nm in targets or (verb and nm in {m["label"] for m in ms}) else "frame_missing"
                rep[key].append(f"[frame-missing] {s.sid} 문장이 부르는 {nm!r} 가 문장 구간 내내 화면 밖 — 카메라 구도(w·중심)를 넓혀 함께 담는다")
    P.R.cache["story_geo"] = rep
    return rep


def check_battle_geo(P) -> list[str]:  # noqa: ANN001, N803
    """v5.22.0 D-0200 UF-08 — 전황 동사(qa_checks.battle_geo.verbs) 문장 구간에 지도 마커·경로가 하나도 없으면 warning.
    지도 무대가 아니거나 문장 구간 전체가 가려졌으면(전면 카드·패널·기사·인용) 보지 않는다."""
    if not _map_main(P):
        return []
    out = []
    for s in P.plan.sentences:
        if not any(v in s.text for v in QA.battle_geo.verbs):
            continue
        if all(_covered(P, t) or any(e["type"] in ("article", "quote") and e["t0"] <= t <= e["t1"] for e in P.events)
               for t in np.arange(s.t0, s.t1, 0.5)):
            continue
        if not any(e["type"] in ("marker", "route") and e["t0"] < s.t1 and e["t1"] > s.t0 for e in P.events):
            out.append(f"[battle-geo] {s.sid} 전황 문장인데 지도에 지명 마커·진격 경로가 없다 — 어느 도시를 누가 장악·탈환했는지 marker(날짜 부제)·route 로")
    return out


def media_unused(pid: str, events: list[dict], registry: dict, drops: dict[str, str]) -> list[str]:
    """v7.4.0 D-0238(UF-118 "사진을 고른거 같은데 그 사진들이 누락되지 않고 영상에 잘 쓰이게 챙겨") — 이 프로젝트가 등재한
    권리 통과 사진(레지스트리 mid 가 `{pid}_` 로 시작하는 kind photo, rights_status rights_clear·restricted)이 어느 이벤트에도
    없으면 hard. media_notes.yaml drop(mid·사유)만 예외."""
    out = []
    for mid, a in registry.items():
        if not mid.startswith(f"{pid}_") or a.kind != "photo" or a.rights_status == "unverified" or mid in drops:
            continue
        if not any(f"'{mid}'" in repr(e) for e in events):   # photo mid·기사 카드 press 어디든
            out.append(f"[media-unused] 등재한 사진 {mid}({a.caption}) 이 연출에 없다 — 배치하거나 media_notes.yaml drop 에 사유(UF-118)")
    return out


def check_media_unused(P) -> list[str]:  # noqa: ANN001, N803
    from engine.media_registry import load_media_registry  # noqa: PLC0415
    from script.media_table import load_notes  # noqa: PLC0415

    drops = {d.mid: d.reason for d in load_notes(P.root).drop}
    return media_unused(P.root.name, P.events, load_media_registry(), drops)


def check_article_press_missing(P) -> list[str]:  # noqa: ANN001, N803
    """v7.4.0 D-0229 §6(UF-109 "트럼프가 에너지 휴전이 끝났다고 말하는 기사의 사진을 넣어") — 인물(엔티티 person 이름)의 발언·발표
    문장(rules script_vocab.statement_verbs) 구간에 뜬 기사 카드에 press 사진이 없으면 warning. 사진이 권리상 없으면 R 에 사유(블러 무대)."""
    from engine.entities import load_entities  # noqa: PLC0415

    names = [n.replace(" ", "") for e in load_entities().of_kind("person").values() for n in e.names if len(n.replace(" ", "")) >= 2]
    verbs = R_.script_vocab.statement_verbs
    out = []
    for e in P.events:
        if e["type"] != "article" or e.get("press"):
            continue
        for s in P.plan.sentences:
            flat = s.text.replace(" ", "")
            if e["t0"] < s.t1 and e["t1"] > s.t0 and any(v in s.text for v in verbs) and any(n in flat for n in names):
                out.append(f"[article-press-missing] 기사 {e.get('mid')} — {s.sid} 인물 발언·발표 문장인데 press 사진 없음(공식 사진·보도 인용 사진, UF-109)")
                break
    return out


def check_portrait_unused(P) -> list[str]:  # noqa: ANN001, N803
    """v5.22.0 D-0200 UF-10 — 문장에 인물 이름(엔티티 별칭)이 나오고 쓸 수 있는 초상(엔티티 portrait·라이브러리)이 있는데
    그 문장 구간에 그 인물의 뱃지·인용이 없으면 warning(문장마다 인물 한 줄)."""
    from engine.entities import load_entities  # noqa: PLC0415

    persons = [(e.portrait or e.library, e.names) for e in load_entities().of_kind("person").values() if (e.portrait or e.library)]
    out = []
    for s in P.plan.sentences:
        flat = s.text.replace(" ", "")
        for pid, names in persons:
            hit = next((n for n in sorted(names, key=len, reverse=True) if len(n.replace(" ", "")) >= 2 and n.replace(" ", "") in flat), None)
            if hit is None:
                continue
            if any(e["t0"] < s.t1 and e["t1"] > s.t0 and f"'pid': '{pid}'" in repr(e) for e in P.events):   # 뱃지·인용·패널 노드 어디든
                continue
            out.append(f"[portrait-unused] {s.sid} '{hit}' 가 나오는데 초상({pid})을 쓰지 않았다 — 인물 뱃지(kind person)나 인용으로 보인다")
    return out


def check_bgm_decision(P) -> list[str]:  # noqa: ANN001, N803
    """v5.22.2 UF-16·30·93(D-0205 §3) — 배경음악이 없으면(sound.bgm null·sound 없음) sound.no_music_decision(결정 번호)이 있어야 한다.
    음악 누락이 세 번 되풀이됐다(SK하이닉스·dmz·gulf) — 연출이 조용히 음악을 빼지 못하게 한다(P6)."""
    m = P.R.cache.get("music") or {"bgm": [], "no_music_decision": None}
    if m["bgm"] or m["no_music_decision"]:
        return []
    return ["[bgm-decision] 배경음악이 없다(sound.bgm null) — 표준은 음악 있음. 음악을 넣거나(assets/audio/bgm/registry.yaml id), "
            "사용자 결정으로 뺐으면 sound.no_music_decision 에 결정 번호를 적는다"]


def endcard_black_samples(P) -> list[float]:  # noqa: ANN001, N803
    """엔딩 카드 글자가 다 빠진 뒤~영상 끝 표본 시각(카드 끝 직후·가운데·끝 직전). 카드가 끝까지 이어지면 빈 목록."""
    end = next((c for c in P.R.tb.plan.cards if c.kind == "end"), None)
    total = P.plan.total
    if end is None or end.t1 >= total - 1.0 / FPS:
        return []
    a, b = end.t1 + 1.0 / FPS, total - 1.0 / FPS
    return sorted({round(a, 4), round((a + b) / 2, 4), round(b, 4)})


def check_endcard_black(P) -> list[str]:  # noqa: ANN001, N803
    """v5.22.3 UF-35(D-0205 §3, dmz U15 "엔딩 카드가 사라질 때 지도가 다시 보인다") — 카드 퇴장 뒤~끝 프레임을 실제로 그려
    평균 밝기(Rec.709)가 end_card.after_max_luma 를 넘으면 hard. 규칙 키(hold_black_after)만으로는 회귀를 못 잡는다."""
    from engine.render import render_frame  # noqa: PLC0415
    from engine.style import END_CARD  # noqa: PLC0415

    out = []
    for t in endcard_black_samples(P):
        i = min(P.n_frames - 1, int(round(t * FPS)))
        surf, buf = render_frame(P, i)
        a = np.frombuffer(buf, np.uint8).reshape(surf.get_height(), surf.get_width(), 4)[..., :3].astype(np.float32) / 255.0
        luma = float((0.0722 * a[..., 0] + 0.7152 * a[..., 1] + 0.2126 * a[..., 2]).mean())   # cairo RGB24 = BGRX
        if luma > END_CARD.after_max_luma:
            out.append(f"[endcard-black] t={t:.2f} 엔딩 카드 뒤 평균 밝기 {luma:.3f} > {END_CARD.after_max_luma} — 끝까지 검정이어야 한다(지도가 다시 보임)")
    return out


def check_camera_per_sentence(P) -> list[str]:  # noqa: ANN001, N803
    """v5.22.4 UF-19(C0 "문장마다 카메라 이동" 금지) — shot_grammar.max_consecutive_move_sentences 만큼 연속 문장이
    모두 카메라 이동(move 키)을 시작하면 hard. 장면당 이동 수(shots warning)와 별개로 '문장마다' 패턴만 본다."""
    n = SG.max_consecutive_move_sentences
    starts = [k.t for k in P.keys if k.mode == "move"]
    run: list[str] = []
    for s in P.plan.sentences:
        if any(s.t0 - 0.05 <= t < s.t1 for t in starts):
            run.append(s.sid)
            if len(run) >= n:
                return [f"[camera-per-sentence] 연속 {len(run)}문장({', '.join(run[-n:])})이 모두 카메라 이동을 시작한다 — "
                        "문장마다 카메라를 움직이지 않는다(C0). 숏을 장면 단위로 묶는다"]
        else:
            run = []
    return []


def check_stage_continuity(P) -> list[str]:  # noqa: ANN001, N803
    """무대 연속성 — engine.shots.stage_continuity 한 곳. 상세는 "[규칙 키] 설명"(D-0077: 영문 키)."""
    from engine.shots import stage_continuity  # noqa: PLC0415

    return [f"[{k}] {msg}" for k, msg in stage_continuity(P.shots)]


def check_genre_elements(P) -> list[str]:  # noqa: ANN001, N803
    """장르 요소 — 연출이 쓴 요소가 장르 프로필(reuse ∪ new) 밖이면 요소마다 한 줄. 상세는 "[genre-element] …"."""
    from genres.elements import outside  # noqa: PLC0415
    from genres.load import load_genre  # noqa: PLC0415

    g = P.R.cache["genre"]
    prof = load_genre(g["name"])
    return [f"[genre-element] {name!r} ×{n} — 장르 {prof.genre!r} 프로필 primitives(reuse ∪ new)에 없다"
            for name, n in outside(g["elements_used"], prof.elements()).items()]


def check_subtitles(P) -> list[str]:  # noqa: ANN001, N803
    from script.lint import subtitle_lines  # noqa: PLC0415

    return [f"{s.sid} 자막 {n}줄 > {QA.subtitle_lines_max}" for s in P.plan.sentences
            if (n := subtitle_lines(s.text)) > QA.subtitle_lines_max]


def check_forbidden(P, provenance: dict) -> list[str]:  # noqa: ANN001, N803
    out: list[str] = []
    allowed = set(R_.registries.event_types)
    out += [f"레지스트리 밖 이벤트 {e['type']}" for e in P.events if e["type"] not in allowed]
    if provenance.get("features_used", {}).get("vignette"):
        out.append("비네팅 켜짐")
    if list(R_.hud.allowed_corner_elements) != ["date_badge"]:
        out.append(f"모서리 요소 {R_.hud.allowed_corner_elements} — 날짜만 허용")
    return out


def check_label_glyphs(drawn: list[tuple[str, float, str | None, str]]) -> list[str]:
    """v4.5.0 사용자 결정 D85(C9) — 검증 라벨(<미검증> 등)은 영상 본문 어디에도 그리지 않는다. drawn = 프리뷰 컷에 그린 글자.
    엔딩 카드 안내 줄(end_card.notice_unverified)은 라벨 문구를 쓰지 않으므로 역할 예외가 필요 없다."""
    labs = [v for v in R_.script_schema.labels.values() if v]
    hits = sorted({(lab, s) for lab, _, _, s in drawn for v in labs if v in s})
    return [f"[label-in-body] {lab}: 검증 라벨 {s!r} 를 화면에 그렸다 — 본문 표기 금지(C9), 엔딩 카드 마지막 줄 건수만" for lab, s in hits]


def check_media_upscaled(P) -> list[str]:  # noqa: ANN001, N803
    """원본이 장치 해상도보다 작아 늘려 그리는 미디어(경고). 사진은 켄 번스 최대 배율까지 본다."""
    OP = P.R.out  # noqa: N806
    A = P.R.assets  # noqa: N806
    out: list[str] = []
    for e in P.events:
        if e["type"] not in ("photo", "clip", "cutout"):
            continue
        m = A.media_assets[e["mid"]]
        if e["type"] == "clip":
            A.load_clip(m.file)
            src = int(A.clips[m.file].shape[2])
        else:
            src = A.source_width(f"media:{m.file}")
        need = OP.px_i(e["w"] * (KEN_BURNS_MAX if e["type"] == "photo" else 1))
        if src < need:
            out.append(f"[media-upscaled] {e['type']} {e['mid']} 원본 폭 {src}px < {OP.name} 장치 폭 {need}px")
    return out


def check_glyph_size(drawn: list[tuple[str, float, str | None, str]]) -> list[str]:
    """drawn = [(컷 라벨, 크기, 역할, 문자열)] — 프리뷰가 컷을 그리며 모은 글자(typography.GLYPH_LOG). 같은 (크기·역할·문자열)은 한 번만."""
    lo = R_.layout_480p.min_font_px
    ex = set(QA.glyph_size_exempt)
    seen: set[tuple] = set()
    out: list[str] = []
    for lab, size, role, s in drawn:
        if size < lo and role not in ex and (size, role, s) not in seen:
            seen.add((size, role, s))
            out.append(f"[glyph-size] {lab} 글자 {size:g}px < 최소 {lo:g}px(화면 높이 {size / H_OUT:.2%}) 역할 {role or '없음'} — {s[:40]!r}")
    return out


def check_audio(P) -> tuple[list[str], list[str], dict]:  # noqa: ANN001, N803
    """오디오 QA(v3.4.0 D-0060 작업 6·D-0061) — audio/qa.py 한 경로. mux 단계(out/mix.f32·final.mp4 뒤)에서 부른다.
    (hard 지적: 통합 음량·트루 피크·음악 레벨·mix 피크, warning: 문장 RMS 편차, AudioQA dict)."""
    from audio.qa import audio_qa  # noqa: PLC0415

    has_music = any(r.startswith("music.") for r in (P.R.cache.get("credit_refs") or ()))
    q = audio_qa(P.root / "out", P.plan.sentences, has_music=has_music)
    return q.issues(), q.warnings(), q.model_dump()


def _rel_lum(rgb: "np.ndarray") -> "np.ndarray":
    """sRGB(0~1) → 상대 휘도(WCAG)."""
    c = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def _ratio(a: float, b: float) -> float:
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def measure_contrast(snap: tuple[bytes, int, int], log: list) -> list[dict]:
    """v5.18.0 D-0161 §4 — 렌더 프레임의 실제 합성 배경 대비(가이드 23 §7: 색상 코드끼리 비교하지 않는다).
    snap = 그 프레임의 지도 층 합성본(지형·국경·지도 이벤트·지명까지, 그 위 카드·패널·사진·전면 카드 전) — 가림이 대비를 흐리지 않게.
    글자: 상자(장치 px, 1px 여유) 휘도의 중앙값 = 배경(글자 테두리·지형 합성), 글자색 쪽 극값(3·97 백분위) = 글자.
    도형(경로 선): 선 점 2px 안의 선색 쪽 극값 ↔ 법선 양쪽 7px 의 3×3 중앙값. 알파 < map_contrast_min_alpha 는 재지 않는다."""
    import numpy as np  # noqa: PLC0415

    data, w, h = snap   # 지도 층 합성본(engine.render.render_frame — 카드·패널 전), RGB24 = BGRX
    buf = np.frombuffer(data, np.uint8).reshape(h, w, 4)[:, :, :3][..., ::-1]
    L = _rel_lum(buf.astype(np.float64) / 255.0)  # noqa: N806
    out: list[dict] = []
    for kind, geom, col, a, name in log:
        if kind != "aux" and a < QA.map_contrast_min_alpha:   # 보조 지명은 처음부터 반투명(설계) — 알파로 거르지 않고 기록만
            continue
        fl = float(_rel_lum(np.asarray(col, np.float64)))
        if kind == "shape":
            px, py, nx, ny = geom
            xi, yi = int(round(px)), int(round(py))
            if not (9 <= xi < w - 9 and 9 <= yi < h - 9):
                continue
            core = L[yi - 2:yi + 3, xi - 2:xi + 3].ravel()
            side = [L[int(round(py + s * 7 * ny)) - 1:int(round(py + s * 7 * ny)) + 2,
                      int(round(px + s * 7 * nx)) - 1:int(round(px + s * 7 * nx)) + 2] for s in (-1, 1)]
            bg = float(np.median(np.concatenate([x.ravel() for x in side if x.size])))
        else:   # v5.21.2 — 글자 대비는 engine.contrast 한 경로(국소 보정과 같은 식)
            from engine.contrast import text_box_ratio  # noqa: PLC0415

            m = text_box_ratio(L, geom, col)
            if m is not None:
                out.append({"kind": kind, "name": name, **m})
            continue
        fg = float(np.percentile(core, 3 if fl < bg else 97))
        out.append({"kind": kind, "name": name, "ratio": round(_ratio(fg, bg), 2), "fg": round(fg, 3), "bg": round(bg, 3)})
    return out


def check_map_contrast(P, kind: str) -> list[str]:  # noqa: ANN001, N803
    """[map-contrast] — required 글자 < map_contrast_text(hard) | shape 경로 < map_contrast_shape(warning). 요소마다 최저값 한 줄."""
    lim = QA.map_contrast_text if kind == "required" else QA.map_contrast_shape
    if kind == "shape":   # 선은 컷·경로마다 표본 중앙값(선이 해안·다른 선과 겹치는 한 점이 판정을 흔들지 않게)
        by: dict[tuple[str, str], list[float]] = {}
        for cut, m in P.R.cache.get("map_contrast") or []:
            if m["kind"] == "shape":
                by.setdefault((m["name"], cut), []).append(m["ratio"])
        bad = sorted((float(np.median(v)), n, c) for (n, c), v in by.items() if np.median(v) < lim)
        return [f"[map-contrast] 선 {n!r} 대비 중앙값 {r:.2f} < {lim:g} ({c})" for r, n, c in bad]
    worst: dict[str, tuple[float, str]] = {}
    for cut, m in P.R.cache.get("map_contrast") or []:
        if m["kind"] == kind and m["ratio"] < lim and (m["name"] not in worst or m["ratio"] < worst[m["name"]][0]):
            worst[m["name"]] = (m["ratio"], cut)
    return [f"[map-contrast] 글자 {n!r} 대비 {r:.2f} < {lim:g} ({cut})" for n, (r, cut) in sorted(worst.items())]


def contrast_summary(P) -> dict | None:  # noqa: ANN001, N803
    """provenance map_contrast — 종류별 최저 5개(이름·값·컷)와 측정 수. 측정이 없으면 None(P5)."""
    ms = P.R.cache.get("map_contrast") or []
    if not ms:
        return None
    out: dict = {}
    for kind in ("required", "aux"):
        rows = sorted((m["ratio"], m["name"], cut) for cut, m in ms if m["kind"] == kind)
        out[kind] = {"n": len(rows), "lowest": [{"ratio": r, "name": n, "cut": c} for r, n, c in rows[:5]]}
    by: dict[tuple[str, str], list[float]] = {}
    for cut, m in ms:
        if m["kind"] == "shape":
            by.setdefault((m["name"], cut), []).append(m["ratio"])
    rows = sorted((round(float(np.median(v)), 2), n, c) for (n, c), v in by.items())
    out["shape"] = {"n": sum(len(v) for v in by.values()), "routes": len(rows), "basis": "컷·경로별 표본 중앙값",
                    "lowest": [{"ratio": r, "name": n, "cut": c} for r, n, c in rows[:5]]}
    return out


def run_checks(P, times: list[float], provenance: dict, drawn: list[tuple[str, float, str | None, str]],  # noqa: ANN001, N803
               labels: list[str] | None = None) -> dict:
    """모든 검사 → checks.json 내용. hard 합계가 0 이어야 시각 검수로 간다. drawn = 프리뷰 컷에 그린 글자(glyph_size·정직성),
    labels = 컷 라벨(drawn 의 첫 칸, 없으면 preview 기본 "t=…")."""
    from engine.honesty import judge, project_metas  # noqa: PLC0415

    skip = profile_skips(P)
    run: dict[str, Callable[[], list[str]]] = {
        "overlap": lambda: [w for w in placement_warnings(P.events, P.R.assets.media_assets)] + check_label_hidden(P),
        "offscreen": lambda: check_offscreen(P) + check_endcard_overflow(P),
        "glyphs": lambda: check_glyphs(P),
        "glyph_size": lambda: check_glyph_size(drawn),
        "shots": lambda: check_shots(P),
        "media_beats": lambda: list(density_report(P.events, P.R.tb, P.plan.total)["warnings"])
        + article_candidate_usage(P.root, P.plan, P.events)["warnings"],   # v5.19.0 D-0163 §2 — [article-unused]·[article-density]
        "media_upscaled": lambda: check_media_upscaled(P),
        "endcard_roll": lambda: check_endcard_roll(P),
        "labels": lambda: check_labels(P, times),
        "date": lambda: [f"{s.sid} 날짜 형식 {s.date!r}" for s in P.plan.sentences if not DATE_RE.match(s.date)],
        "subtitles": lambda: check_subtitles(P),
        "rights": lambda: [],   # load_project 가 권리 점검(check_credits·validate_media)에서 실패하면 여기까지 오지 않는다
        "forbidden": lambda: check_forbidden(P, provenance) + check_label_glyphs(drawn),
        "stage_continuity": lambda: check_stage_continuity(P),
        "camera_continuity": lambda: check_camera_continuity(P),   # v5.21.9 D-0191 §1-1
        "card_exposure": lambda: check_card_exposure(P),           # v5.21.10 D-0191 §1-2
        "route_label_cross": lambda: route_label_report(P)["cross"],      # v5.21.11 D-0191 §1-3·D-0192
        "route_label_overlap": lambda: route_label_report(P)["overlap"],  # v5.21.11 D-0192·D-0199
        "article_backdrop": lambda: check_article_backdrop(P),           # v5.21.12 D-0193
        "quote_in_script": lambda: check_quote_in_script(P),             # v5.21.13 D-0194
        "route_missing": lambda: story_geo_report(P)["route_missing"],                 # v5.21.14 D-0195·D-0197(warning)
        "route_missing_other": lambda: story_geo_report(P)["route_missing_other"],     # v5.21.14 (hard — 다른 경로만 = 오해)
        "frame_missing": lambda: story_geo_report(P)["frame_missing"],                 # v5.21.14 D-0199(warning)
        "frame_missing_target": lambda: story_geo_report(P)["frame_missing_target"],   # v5.21.14 (hard — 이동·공격 대상 화면 밖)
        "battle_geo": lambda: check_battle_geo(P),            # v5.22.0 D-0200 UF-08(warning)
        "bgm_decision": lambda: check_bgm_decision(P),        # v5.22.2 UF-16·30·93(hard)
        "endcard_black": lambda: check_endcard_black(P),      # v5.22.3 UF-35(hard)
        "camera_per_sentence": lambda: check_camera_per_sentence(P),   # v5.22.4 UF-19(hard)
        "label_jump": lambda: check_label_jump(P),   # v5.22.7 D209(hard)
        "camera_speed": lambda: check_camera_speed(P),   # v6.0.2 UF-97 D-0216(hard)
        "camera_bounds": lambda: check_camera_bounds(P),   # v7.1.0 UF-99 D-0220(hard)
        "title_backdrop": lambda: check_title_backdrop(P),   # v6.0.2 UF-98 D-0216(hard)
        "cutaway_churn": lambda: cutaway_churn(P.events),     # v7.4.0 UF-110 D-0229 §2.3(hard)
        "transition_camera": lambda: transition_camera(P.plan.transitions, P.plan.sentences, P.keys),   # v7.4.0 UF-105 D-0229 §2.2(hard)
        "unit_glyph_font": lambda: check_unit_glyph_font(P),  # v7.4.0 UF-111 D-0229 §2.4(hard)
        "media_unused": lambda: check_media_unused(P),   # v7.4.0 UF-118 D-0238(hard)
        "inset_clipped": lambda: check_inset_clipped(P),   # v7.4.0 D-0240 §2(hard)
        "badge_clipped": lambda: check_badge_clipped(P),   # v7.4.0 D-0244(hard)
        "series_unused": lambda: check_series_unused(P),   # v7.4.0 D-0245(UF-126, hard)
        "panel_dropped": lambda: check_panel_dropped(P),   # v7.4.0 D-0245(UF-126, hard)
        "card_over_panel": lambda: check_card_over_panel(P),   # v7.4.0 D-0248(UF-129, hard)
        "article_outlet": lambda: check_article_outlet(P),   # v7.4.0 D-0250(UF-130, hard)
        "catalog_label_overlap": lambda: check_catalog_label_overlap(P),   # v7.4.0 D-0251 §1.1(hard, 카탈로그 판만)
        "chart_only_run": lambda: [f"[chart-only-run] {a:.1f}~{b:.1f}초 ({b - a:.1f}초) 차트·카드만 보인다 — 상한 {QA.chart_only_run.max_sec:g}초. "
                                   "사건 핀·인물·사진·기사·인용·지도 중 하나를 넣는다(UF-135)" for a, b in chart_only_runs(P)
                                   if b - a > QA.chart_only_run.max_sec and P.root.name not in QA.chart_only_run.exempt_projects],   # v7.4.0 D-0252(hard). D-0271 회귀 기준 면제
        "chart_world_split": lambda: check_chart_world_split(P),   # v7.4.0 D-0251 §6.2-2(hard, UF-135 ②)
        "series_label_overlap": lambda: check_series_label_overlap(P),   # v7.4.0 D-0256(hard)
        "chart_edge_bleed": lambda: check_chart_edge_bleed(P),   # v7.4.0 D-0257(hard, UF-137)
        "media_density": lambda: check_media_density(P),   # v7.4.0 D-0261(hard, UF-139)
        "plot_height": lambda: check_plot_height(P),
        "axis_empty_band": lambda: check_axis_empty_band(P),   # v7.4.0 D-0277 §3(hard, UF-142)
        "clip_frame": lambda: check_clip_frame(P),   # v7.4.0 D-0274 §2①②(hard, UF-141)
        "clip_date_mismatch": lambda: check_clip_date_mismatch(P),   # v7.4.0 D-0283 §1(hard)
        "inset_jump": lambda: check_inset_jump(P),   # v7.4.0 D-0300(hard, UF-146)
        "inset_side_change": lambda: check_inset_side_change(P),   # v7.4.0 D-0300(warning)
        "flat_lane": lambda: check_flat_lane(P),   # v7.4.0 D-0263(hard, UF-140)
        "press_credit": lambda: check_press_credit(P, times, drawn),   # v7.4.0 D-0240 §3(hard)
        "static_camera": lambda: check_static_camera(P),   # v7.4.0 D-0241 §1(hard, UF-120)
        "route_speed": lambda: check_route_speed(P),   # v7.4.0 D-0241 §4(hard, UF-123)
        "sea_only_frame": lambda: check_sea_only(P),   # v7.4.0 D-0242(hard, UF-125)
        "unit_ton_glyph": lambda: [f"[unit-ton-glyph] {k}: {s!r} — 화면 무게 단위는 ton(UF-122)" for k, s in unit_ton_hits(P.events)],   # v7.4.0 D-0241 §3(hard)
        "ratio_graphic": lambda: ratio_graphic(P.plan.sentences, P.events),   # v7.4.0 UF-113 D-0229 §2.6(warning)
        "inset_overlap": lambda: check_inset_overlap(P),   # v7.4.0 UF-107 D-0229 §2.7(warning)
        "article_press_missing": lambda: check_article_press_missing(P),   # v7.4.0 UF-109 D-0229 §6(warning)
        "badge_orphan": lambda: badge_orphans(P.events),   # v7.4.0 D-0240 §4(warning)
        "tempo_density": lambda: tempo_density(P.plan.sentences),   # v7.4.0 UF-115 D-0229 §2.9(warning, script.lint 와 같은 함수)
        "portrait_unused": lambda: check_portrait_unused(P),  # v5.22.0 D-0200 UF-10(warning)
        "genre_elements": lambda: check_genre_elements(P),
        "boundary_as_route": lambda: list((P.R.cache.get("geo_check") or {}).get("boundary") or []),
        "geo_unsourced": lambda: check_geo_unsourced(P),
        "geo_mismatch": lambda: check_geo_mismatch(P),
        "static_window": lambda: check_static_window(P),
        "timeline_rescale": lambda: check_timeline_rescale(P),
        "backdrop_rights": lambda: list((P.R.cache.get("backdrop") or {}).get("rights") or []),
        "backdrop_repeat": lambda: list((P.R.cache.get("backdrop") or {}).get("repeat") or []),
        "stage_choice": lambda: list(P.R.cache.get("stage_choice") or []),
        "island_overlap": lambda: check_island_overlap(P),
        "backdrop_main_missing": lambda: check_main_missing(P),
        "card_island": lambda: check_card_island(P),
        "island_label_clip": lambda: check_island_label_clip(P),
        "island_pin_collision": lambda: check_island_pin_collision(P),   # v7.4.0 D-0267(hard)
        "island_label_overlap": lambda: check_island_label_overlap(P),
        "cascade": lambda: check_cascade(P),
        "cascade_label_hidden": lambda: check_cascade_label_hidden(P),
        "subtitle_overlap": lambda: check_subtitle_overlap(P),
        "label_collision": lambda: check_label_collision(P),   # v5.6.0 RENDER-AP-009
        "timeline_span": lambda: check_timeline_span(P),       # v5.6.0 RENDER-AP-011
        "route_frame": lambda: check_route_frame(P),           # v5.6.0 RENDER-AP-012
        "panel_overflow": lambda: check_panel_overflow(P),     # v5.6.0 RENDER-AP-013
        "flag_territory": lambda: check_flag_territory(P),     # v5.6.0 RENDER-AP-014
        "badge_over_panel": lambda: check_badge_over_panel(P),  # v5.6.0 RENDER-AP-015
        "opening_establish": lambda: check_opening_establish(P),  # v5.6.0 RENDER-AP-016
        "weapon_photo": lambda: check_weapon_photo(P),         # v5.6.0 RENDER-AP-017(warning)
        "map_contrast": lambda: check_map_contrast(P, "required"),         # v5.18.0 D-0161 §4(hard)
        "map_contrast_shape": lambda: check_map_contrast(P, "shape"),      # v5.18.0 D-0161 §4(warning)
    }
    res = {k: f() for k, f in run.items() if k not in skip}
    notes: dict[str, list[str]] = {}
    if not set(HONESTY) <= skip:
        honesty, notes = judge(project_metas(P, times, labels or [f"t={t:.2f}" for t in times], drawn))
        res.update({k: v for k, v in honesty.items() if k not in skip})
    items = [{"id": k, "severity": "hard" if k in HARD else "warning", "count": len(v), "details": v[:20],
              **({"notes": notes[k][:20]} if notes.get(k) else {})} for k, v in res.items()]
    items += [{"id": k, "severity": "hard" if k in HARD else "warning", "count": 0, "details": [], "skipped": True}
              for k in sorted(skip)]
    hard = sum(i["count"] for i in items if i["severity"] == "hard")
    return {"schema_version": 1, "hard": hard, "warnings": sum(i["count"] for i in items if i["severity"] == "warning"),
            "passed": hard == 0, "profile": "animatic" if getattr(P, "animatic", False) else "catalog" if getattr(P, "catalog", False) else "full", "skipped": sorted(skip),
            "thresholds": QA.model_dump(), "items": items}


def chart_only_runs(P) -> list[tuple[float, float]]:  # noqa: ANN001, N803
    """차트·카드만 보이는 연속 구간(v7.4.0 D-0252, rules qa_checks.chart_only_run) — step_sec 표본. 타이틀·엔딩 카드 구간은 끊는다.
    provenance chart_only_runs 와 검사 [chart-only-run] 이 같은 값을 쓴다(P5)."""
    C = QA.chart_only_run  # noqa: N806
    shots = sorted((s for s in (getattr(P, "shots", None) or []) if not s.island), key=lambda s: s.t)

    def stage_at(t: float) -> str:
        return next((s.stage for s in reversed(shots) if s.t <= t), P.R.stage.name)

    def kind(e: dict) -> str:   # chart · neutral · other
        typ = e["type"]
        if typ == "island":
            return "chart" if e.get("kind") in C.chart_island_kinds else "neutral"
        if typ in C.chart_types or (typ == "primitive" and e.get("id") in C.chart_primitives):
            return "chart"
        return "neutral" if typ in C.neutral_types else "other"

    runs: list[tuple[float, float]] = []
    start: float | None = None
    n = int(P.plan.total / C.step_sec) + 1
    for i in range(n):
        t = i * C.step_sec
        act = [e for e in P.events if e["t0"] <= t <= e["t1"]]
        ks = {kind(e) for e in act}
        covered = any(e["type"] == "panel" for e in act)
        only = (not P.R.tb.in_fullcard(t) and "chart" in ks and "other" not in ks
                and not (stage_at(t) in C.map_stages and not covered))
        if only and start is None:
            start = t
        elif not only and start is not None:
            runs.append((round(start, 2), round(t, 2)))
            start = None
    if start is not None:
        runs.append((round(start, 2), round(P.plan.total, 2)))
    return runs


def check_chart_world_split(P) -> list[str]:  # noqa: ANN001, N803
    """[chart-world-split] hard(v7.4.0 D-0251 §6.2-2, UF-135 ② "같은 축척 혹은 같은 차트 안에서 움직이거나 보여주는게 아니니까") —
    island 이벤트가 2개 이상인 영상에서 같은 단위의 series 가 서로 다른 레인(= 다른 y 축척)에 그려지면 실패. 레인 범위는 무대가 정한다
    (engine.layers.series.lane_range — 사용자 값 아님). 같은 단위는 한 레인(한 축척) 위에서 카메라가 움직여 보여 준다."""
    if sum(1 for e in P.events if e["type"] == "island") < 2:
        return []
    from data.series import load_series  # noqa: PLC0415
    from engine.layers.series import record_ids  # noqa: PLC0415

    lanes: dict[str, set[str]] = {}
    for e in P.events:
        if e["type"] == "series":
            for sid in record_ids(e):
                lanes.setdefault(load_series(sid).unit, set()).add(e["lane"])
    rng = P.R.cache.get("series_range") or {}
    out = []
    for unit, ls in sorted(lanes.items()):
        scales = {ln: tuple(round(v, 6) for v in rng[ln]) for ln in sorted(ls) if ln in rng}
        if len(set(scales.values())) > 1:
            out.append(f"[chart-world-split] 단위 {unit!r} 시계열이 레인 {sorted(ls)} 에 다른 축척 {scales} 로 그려진다 — "
                       "같은 단위는 한 레인(한 축척)에 두고 카메라가 그 안에서 움직인다(UF-135)")
    return out


def unplated_end_labels(t: float, lane: str, placed: list) -> list[str]:
    """판 없이 그린 끝값 라벨(v7.4.0 back_and_forth D-0277 §2) — 강조 띠·채움 위에서 대비가 죽는다. 기록 (기준선, 값, 글자 상자, 판 사각형|None)."""
    return [f"[series-label-overlap] t={t:.2f} 레인 {lane} 끝값 라벨 {tuple(round(v, 1) for v in p[2])} 판 없음 — 띠·강조 채움 위 대비"
            " (rules stage_timeline.series.end_label_plate, D-0277 §2)" for p in placed if len(p) < 4 or p[3] is None]


def check_series_label_overlap(P) -> list[str]:  # noqa: ANN001, N803
    """[series-label-overlap] hard(v7.4.0 back_and_forth D-0256) — 같은 레인에 series 둘 이상이 떠 있는 순간, 실제로 그린 끝값 라벨
    글자 상자(engine.layers.series.place_end_label 기록)가 서로 교차하면 실패. 그런 구간만 1초 간격으로 프레임을 그려 잰다."""
    ser = [e for e in P.events if e.get("type") == "series" and e.get("style") != "projection"]
    if not ser:
        return []
    from engine.layers.series import axis_label_boxes  # noqa: PLC0415
    from engine.render import render_frame  # noqa: PLC0415

    world = chart_world(P)
    times: set[float] = set()
    for a in ser:   # v7.4.0 — 끝값 라벨 ↔ 축 눈금 라벨(감독 지적 preview_v8)도 보므로 시리즈 하나여도 1초 간격
        times |= {round(a["t0"] + k, 2) for k in range(int(max(0.0, a["t1"] - a["t0"])) + 1)}
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    rng = P.R.cache.get("series_range") or {}
    out: list[str] = []
    for t in sorted(times):
        P.R.cache.pop("series_end_labels", None)   # 이 프레임에 그린 라벨만
        render_frame(P, min(P.n_frames - 1, max(0, int(t * FPS))))
        reg = P.R.cache.get("series_end_labels") or {}
        for lane, placed in (reg.get("lanes") or {}).items():
            boxes = [p[2] for p in placed]
            out += unplated_end_labels(t, lane, placed)   # v7.4.0 D-0277 §2 — 끝값 라벨 ↔ 띠·강조 채움: 판이 곧 장치
            out += [f"[island-pin-collision] t={t:.2f} 레인 {lane} 끝값 라벨 판 {tuple(round(v, 1) for v in p[2])} 이 핀 맥동 고리를 덮는다 — 위·왼쪽 자리도"
                    " 막혔다(D-0283 §2)" for p in placed if len(p) > 4 and p[4]]
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                        out.append(f"[series-label-overlap] t={t:.2f} 레인 {lane} 끝값 라벨 {tuple(round(v, 1) for v in a)} ↔ "
                                   f"{tuple(round(v, 1) for v in b)} — rules stage_timeline.series.end_label_min_gap_px")
            v = _series_view(P, world, t)
            if v is None or lane not in rng:
                continue
            unit = next(load_series_unit(e) for e in ser if e["lane"] == lane)
            for a in boxes:
                for b in axis_label_boxes(ctx, v, world[0], lane, rng[lane], unit, boxes):   # 그리기와 같이 겹치는 눈금 라벨은 생략된다
                    if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                        out.append(f"[series-label-overlap] t={t:.2f} 레인 {lane} 끝값 라벨 {tuple(round(x, 1) for x in a)} ↔ 축 눈금 라벨 "
                                   f"{tuple(round(x, 1) for x in b)} — 끝값 라벨이 비키지 못했다")
    return list(dict.fromkeys(out))


def load_series_unit(e: dict) -> str:
    from data.series import load_series  # noqa: PLC0415

    return load_series(e["series_id"]).unit


def _series_view(P, world, t: float) -> "View | None":  # noqa: ANN001, N803
    """끝값 라벨을 그린 좌표계의 뷰 — 시간축 주 무대(틀 원점 포함) 또는 차트 아일랜드(상자 원점 0, 그리기가 상자로 옮긴 좌표)."""
    if world is None:
        return None
    st = P.R.stage
    if st.name == "timeline":
        return View(st, P.cams[min(P.n_frames - 1, max(0, int(t * FPS)))])
    chart = P.R.cache.get("island_chart")
    isl = next((e for e in P.events if e.get("type") == "island" and e.get("kind") == "chart" and e["t0"] <= t <= e["t1"]), None)
    if not chart or isl is None:
        return None
    from engine.island import chart_view, island_box  # noqa: PLC0415

    return chart_view(chart, t, island_box(isl))


def chart_text_boxes(stage, v: View, events: list[dict], t: float, rng: dict, dx: float = 0.0,  # noqa: ANN001
                     dy: float = 0.0) -> list[tuple[str, tuple]]:
    """시간축 세계의 글자 상자(화면 설계 px) — 레인 이름·레인 출처 줄·축 값(그리는 함수와 같은 자리). dx·dy = 아일랜드 상자 원점."""
    import cairo  # noqa: PLC0415

    from engine.layers.series import axis_label_values, fmt_value, lane_name, source_line_boxes, value_y  # noqa: PLC0415
    from engine.typography import tw  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    L, S = TIMELINE.lane_label, TIMELINE.series  # noqa: N806
    out: list[tuple[str, tuple]] = []
    for i, ln in enumerate(stage.lanes):
        top, _ = stage.lane_screen(v, i)
        x0 = v.ox + L.x
        out.append((f"레인 이름 {ln.id}", (x0 + dx, top + L.dy - L.size + dy, x0 + tw(ctx, lane_name(ln), L.size, L.font) + dx, top + L.dy + dy)))
    for e in events:
        if e.get("type") != "series" or not e["t0"] <= t <= e["t1"] or e.get("slot", 0):
            continue
        for k, (s, sx, by) in enumerate(source_line_boxes(ctx, v, stage, e)):   # v7.4.0 D-0265 — 접힌 줄마다(그리기와 같은 자리)
            out.append((f"출처 줄 {e['lane']}" + (f" {k + 1}" if k else ""), (sx + dx, by - S.source_size + dy, sx + tw(ctx, s, S.source_size, S.source_font) + dx, by + dy)))
        r = rng.get(e["lane"])
        if r is None:
            continue
        from data.series import load_series  # noqa: PLC0415

        unit = load_series(e["series_id"]).unit
        for val in axis_label_values(v, stage, e["lane"], r):   # v7.4.0 D-0263·D-0268 — 라벨을 단 축 값만(그리기와 같은 값)
            _, sy = v.to_screen(0.0, value_y(stage, e["lane"], r, val))
            s = fmt_value(val, unit)
            x1 = v.right - S.axis_label_margin_px
            out.append((f"축 값 {e['lane']} {s}", (x1 - tw(ctx, s, S.axis_label_size, S.axis_label_font) + dx,
                                                  sy + S.axis_label_dy - S.axis_label_size + dy, x1 + dx, sy + S.axis_label_dy + dy)))
    return out


FLAT_LANE_STEP_SEC = 0.5   # 카메라가 보여 준 날짜 구간 표본 간격


def chart_world(P) -> "tuple[object, object, list[dict]] | None":  # noqa: ANN001, N803
    """시간축 세계 (무대, 카메라 배열, 시간축 이벤트) — 시간축 주 무대, 아니면 차트 아일랜드(v7.4.0 — 같은 장치를 두 경로에, C12 §3)."""
    st = P.R.stage
    if st.name == "timeline":
        return st, P.cams, P.events
    chart = (getattr(P.R, "cache", None) or {}).get("island_chart")
    if chart:
        return chart["stage"], chart["cams"], chart["events"]
    return None


def visited_dates(st, P, cams=None) -> "tuple[date, date] | None":  # noqa: ANN001, N803
    """영상 동안 카메라가 화면에 보여 준 날짜 구간 — 프레임 표본의 보이는 x 범위 합(cams 없으면 주 무대 카메라)."""
    from datetime import timedelta  # noqa: PLC0415

    cams = P.cams if cams is None else cams
    if cams is None:
        return None
    xs0, xs1 = math.inf, -math.inf
    for i in range(0, len(cams), max(1, int(FLAT_LANE_STEP_SEC * FPS))):
        v = View(st, cams[i])
        xs0, xs1 = min(xs0, v.x0), max(xs1, v.x0 + v.w)
    if xs0 == math.inf:
        return None
    to_d = lambda x: st.cfg.start + timedelta(days=round(st.date_of(max(0.0, x))))  # noqa: E731
    return to_d(xs0), to_d(xs1)


def flat_lanes(P) -> list[tuple[str, float, tuple[float, float]]]:  # noqa: ANN001, N803
    """(레인, 그려진 세로 폭 ÷ 레인 값 범위, 보인 값 범위) — 카메라가 보여 준 날짜 구간 안의 그 레인 레코드 값으로 잰다(v7.4.0 D-0263)."""
    from data.series import load_series  # noqa: PLC0415
    from engine.layers.series import record_ids  # noqa: PLC0415

    from engine.layers.series import record_points  # noqa: PLC0415

    world = chart_world(P)
    rng = P.R.cache.get("series_range") or {}
    if world is None or not rng:
        return []
    st, cams, events = world
    span = visited_dates(st, P, cams)
    out = []
    for lane, (lo, hi) in rng.items():
        vs = [v for e in events if e.get("type") == "series" and e.get("lane") == lane for sid in record_ids(e)
              for d, v in record_points(load_series(sid)) if span is None or span[0] <= d <= span[1]]   # 전망 점(scatter)도 그려진 데이터
        if not vs or hi <= lo:
            continue
        out.append((lane, (max(vs) - min(vs)) / (hi - lo), (min(vs), max(vs))))
    return out


def plot_height(P) -> "tuple[float, float] | None":  # noqa: ANN001, N803
    """(플롯 세로 합 px, 액자 안쪽 높이 px) — 시간축 주 무대 틀 또는 차트 아일랜드 상자. series 없으면 None(P5).
    플롯 = 값 레인 띠 세로 합(레인 수 × 세로 척도). provenance plot_height 와 검사 [plot-height] 가 같은 값을 쓴다."""
    cw = chart_world(P)
    if cw is None or not any(e["type"] == "series" for e in cw[2]):
        return None
    st = cw[0]
    plot = st.n * st.y_px_per_unit
    if getattr(st, "island", False):
        from engine.island import island_box  # noqa: PLC0415

        hs = [island_box(e)[3] for e in P.events if e["type"] == "island" and e.get("kind") == "chart"]
        return (plot, max(hs)) if hs else None
    frame = getattr(st, "frame", None)
    return (plot, frame[3]) if frame is not None else None


MEDIA_DATE_RE = re.compile(r"(\d{4})\.\s?(\d{1,2})\.\s?(\d{1,2})")   # 화면 출처 줄 날짜("2026. 07. 07")
ISO_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def media_shot_date(a) -> "date | None":  # noqa: ANN001 — MediaAsset
    """사진·영상 촬영일 — 화면 출처 줄(file_note)의 연·월·일, 없으면 레지스트리 date 의 ISO 날짜. 일 단위로 못 읽으면 None(판정 안 함)."""
    from datetime import date  # noqa: PLC0415

    for rx, s in ((MEDIA_DATE_RE, a.file_note or ""), (ISO_DATE_RE, a.date or "")):
        m = rx.search(s)
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def sentence_date_at(P, t: float) -> "date | None":  # noqa: ANN001, N803
    """시각 t 에 걸린(또는 직전) 문장의 날짜(YYYY.MM.DD 만 — 월·연 단위 문장은 None)."""
    from datetime import date  # noqa: PLC0415

    sent = [s for s in P.plan.sentences if s.t0 <= t + 0.05]
    if not sent:
        return None
    m = re.fullmatch(r"(\d{4})\.(\d{2})\.(\d{2})", sent[-1].date)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def check_clip_date_mismatch(P) -> list[str]:  # noqa: ANN001, N803
    """[clip-date-mismatch] hard(v7.4.0 back_and_forth D-0283 §1, C0 "자료사진·자료 영상 표기") — 사진·영상 촬영일과 붙은 문장 날짜가
    rules media.file_clip_date_gap_days 이상 차이 나는데 자료사진·자료 영상 표기(is_file_photo)가 없으면 실패. geo strikes(7.7 촬영)가 2.28 공습 문장에."""
    gap = R_.media.file_clip_date_gap_days
    reg = P.R.assets.media_assets
    out = []
    for e in P.events:
        if e["type"] not in ("clip", "photo") or e.get("mid") not in reg:
            continue
        a = reg[e["mid"]]
        if a.is_file_photo:
            continue
        d_m, d_s = media_shot_date(a), sentence_date_at(P, e["t0"])
        if d_m is not None and d_s is not None and abs((d_m - d_s).days) >= gap:
            out.append(f"[clip-date-mismatch] {e['type']} {e['mid']} t={e['t0']:.2f} 촬영일 {d_m} ↔ 문장 날짜 {d_s}({abs((d_m - d_s).days)}일) — "
                       f"자료사진·자료 영상 표기 항목(is_file_photo true)으로 등재해 쓴다(D-0283 §1)")
    return out


def check_clip_frame(P) -> list[str]:  # noqa: ANN001, N803
    """[clip-frame] hard(v7.4.0 back_and_forth D-0274 §2①②, 사용자 의견 UF-141 "영상도 메인 요소야 … 보충물로서 쓰지 말고") —
    main 클립(clip.role 기본)이 액자 슬롯 clip_frame 밖이거나, 보이는 길이가 역할 범위(rules media_beats.clip_show_sec)를 벗어나면 실패."""
    rng = R_.media_beats.clip_show_sec
    out = []
    for e in P.events:
        if e["type"] != "clip":
            continue
        role = e.get("role", "main")
        if role == "main" and e.get("frame") != "clip_frame":
            out.append(f"[clip-frame] 클립 {e['mid']} t={e['t0']:.2f} 이 구석 상자 — 레퍼런스 영상(role main)은 액자 clip_frame 만."
                       " 현장 보조면 role: broll(UF-141)")
        lo, hi = rng[role]
        if not lo <= e["t1"] - e["t0"] <= hi:
            out.append(f"[clip-frame] 클립 {e['mid']} t={e['t0']:.2f} 길이 {e['t1'] - e['t0']:.1f}초 — {role} 범위 {lo:g}~{hi:g}초(D-0276)")
    return out


def check_axis_empty_band(P) -> list[str]:  # noqa: ANN001, N803
    """[axis-empty-band] hard(v7.4.0 back_and_forth D-0277 §3, 사용자 의견 UF-142 "세로축을 늘리란 말이야") — 축 범위 중 데이터 극값
    (무대 기간 안 실측 + 전망 점) 밖 빈 띠가 한쪽이라도 rules stage_timeline.lane_range.empty_band_max_ratio 를 넘으면 실패.
    플롯은 커졌는데 데이터가 그 안 일부만 쓰는 반쪽 확대(econ 3~5% 의 위 0.5%p)를 잡는다."""
    from engine.layers.series import empty_bands  # noqa: PLC0415

    world = chart_world(P)
    rng = P.R.cache.get("series_range") or {}
    if world is None or not rng:
        return []
    st, _, events = world
    mx = TIMELINE.lane_range.empty_band_max_ratio
    out = []
    for lane, r in rng.items():
        if TIMELINE.lane_range.mode == "zero":
            continue
        lo_r, hi_r = empty_bands(events, lane, r, st)
        for side, v in (("아래", lo_r), ("위", hi_r)):
            if v > mx + 1e-9:
                out.append(f"[axis-empty-band] 레인 {lane}: 축 {r[0]:g}~{r[1]:g} 중 {side} 빈 띠 {v:.0%} > {mx:.0%} — 범위를 데이터 극값의"
                           " 눈금 내림·올림으로(D-0277 §3, UF-142)")
    return out


def check_plot_height(P) -> list[str]:  # noqa: ANN001, N803
    """[plot-height] hard(v7.4.0 back_and_forth D-0274 §1①, 사용자 의견 UF-142 "그 두 개를 그냥 합쳐서 세로축을 늘리란 말이야") —
    플롯 세로 합 < 액자 안쪽 높이 × rules island.chart.plot_min_ratio. 레인을 쌓아 차트가 눌리면 실패(UF-137·140 부류)."""
    ph = plot_height(P)
    mn = ISLAND.chart.plot_min_ratio
    if ph is None or ph[0] >= ph[1] * mn:
        return []
    return [f"[plot-height] 플롯 세로 {ph[0]:.0f}px = 액자 안쪽 {ph[1]:.0f}px 의 {ph[0] / ph[1]:.0%} < {mn:.0%} — 레인을 줄여(사건은 선 위 핀)"
            " 값 레인이 액자 세로를 쓰게 한다(UF-142)"]


def check_flat_lane(P) -> list[str]:  # noqa: ANN001, N803
    """[flat-lane] hard(v7.4.0 back_and_forth D-0263, 사용자 의견 UF-140 "변동이 크지 않은 데이터… 가로로 펼쳐진 직선으로밖에 안보인다") —
    화면에 보인 구간의 선·계단 세로 폭이 레인 값 범위 × rules stage_timeline.lane_range.flat_lane_min_ratio 미만. 경고로 낮추지 않는다."""
    mn = TIMELINE.lane_range.flat_lane_min_ratio
    return [f"[flat-lane] 레인 {lane}: 화면에 보인 값 {a:g}~{b:g} 가 레인 범위의 {r:.0%} < {mn:.0%} — 무대 기간(stage_config.timeline start·end)을"
            " 보이는 구간에 맞추거나(값 범위는 무대 기간 데이터로 정해진다) 그 레인을 뺀다(UF-140)" for lane, r, (a, b) in flat_lanes(P) if r < mn]


MEDIA_DENSITY_TYPES = ("photo", "clip", "cutout", "backdrop")   # v7.4.0 D-0261 — 실사 이벤트(기사·인셋·뱃지는 세지 않는다). D-0265 §5 — 배경 사진(backdrop)도 실사, 이벤트마다 1장


def media_density(events: list[dict], total_sec: float) -> tuple[int, float]:
    """(실사 이벤트 수, 분당 개수) — provenance 와 검사 [media-density] 가 같은 값을 쓴다(P5)."""
    n = sum(1 for e in events if e.get("type") in MEDIA_DENSITY_TYPES)
    return n, n / max(total_sec / 60.0, 1e-9)


def check_media_density(P) -> list[str]:  # noqa: ANN001, N803
    """[media-density] hard(v7.4.0 back_and_forth D-0261, 사용자 의견 UF-139 "레퍼런스 사진이나 영상 풍부하게") — 사진·영상·컷아웃 이벤트가
    분당 rules media_beats.min_density_per_min 미만이면 실패. 사유로 통과 없음. 회귀 기준(density_exempt_projects)만 제외."""
    MB = R_.media_beats  # noqa: N806
    if P.root.name in MB.density_exempt_projects:
        return []
    n, d = media_density(P.events, P.plan.total)
    if d >= MB.min_density_per_min:
        return []
    need = math.ceil(MB.min_density_per_min * P.plan.total / 60.0)
    return [f"[media-density] 사진·영상·컷아웃 {n}개 / {P.plan.total / 60:.1f}분 = 분당 {d:.2f} < {MB.min_density_per_min:g} — {need}개 이상 필요. "
            "tools/media_fetch.py search 로 찾아 등재하고 연출에 넣는다(UF-139, 사유로 통과 없음)"]


def check_chart_edge_bleed(P) -> list[str]:  # noqa: ANN001, N803
    """[chart-edge-bleed] hard(v7.4.0 back_and_forth D-0257, 사용자 의견 UF-137 "금리 차트가 화면 좌우에 다 꽉차서") — 시간축 세계(주 무대
    timeline·차트 아일랜드)의 레인 이름·출처 줄·축 값 글자 상자가 그 틀(주 무대 = rules stage_timeline.frame, 아일랜드 = 상자) 밖에 닿으면 실패.
    시간축 주 무대에 틀이 없으면(화면 가득) 그 자체로 실패. 문장마다 가운데 시각에 잰다."""
    out: list[str] = []
    st = P.R.stage
    chart = P.R.cache.get("island_chart")
    rng = P.R.cache.get("series_range") or {}
    if st.name == "timeline":
        if getattr(st, "frame", None) is None:
            return ["[chart-edge-bleed] 시간축 주 무대에 틀(rules stage_timeline.frame)이 없다 — 레인이 화면 가장자리까지 찬다(UF-137)"]
        fx, fy, fw, fh = st.frame
        for s in P.plan.sentences:
            t = (s.t0 + s.t1) / 2
            v = View(st, P.cams[min(P.n_frames - 1, max(0, int(t * FPS)))])
            for name, b in chart_text_boxes(st, v, P.events, t, rng):
                if b[0] < fx or b[2] > fx + fw or b[1] < fy or b[3] > fy + fh:
                    out.append(f"[chart-edge-bleed] t={t:.2f} {name} 상자 {tuple(round(x, 1) for x in b)} 가 틀 {st.frame} 밖에 닿는다")
        # v7.4.0 D-0259 — 덮개(카드·프리미티브·사진·뱃지 등) 상자가 틀 테두리에 걸치면(일부만 안) 실패. 완전히 밖이면 틀과 무관
        cfg = R_.qa_checks.card_over_panel
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        for e in P.events:
            if cfg is None or e["type"] not in cfg.timeline_frame_cover_types:
                continue
            t = (e["t0"] + e["t1"]) / 2
            for b in timeline_cover_box(P, ctx, e, t) or []:
                inside = b[0] < fx + fw and b[2] > fx and b[1] < fy + fh and b[3] > fy
                within = b[0] >= fx and b[2] <= fx + fw and b[1] >= fy and b[3] <= fy + fh
                if inside and not within:
                    out.append(f"[chart-edge-bleed] t={t:.2f} {e['type']} {e.get('tag') or e.get('label') or e.get('mid') or ''!s} 상자 "
                               f"{tuple(round(x, 1) for x in b)} 가 틀 {st.frame} 테두리에 걸친다 — 틀 안에 담거나 밖에 둔다(D-0259)")
    elif chart is not None:
        from engine.island import chart_view, island_box  # noqa: PLC0415

        cst = chart["stage"]
        for e in P.events:
            if e.get("type") != "island" or e.get("kind") != "chart":
                continue
            bx, by_, bw, bh = island_box(e)
            for s in P.plan.sentences:
                t = (s.t0 + s.t1) / 2
                if not e["t0"] <= t <= e["t1"]:
                    continue
                v = chart_view(chart, t, (bx, by_, bw, bh))
                for name, b in chart_text_boxes(cst, v, chart["events"], t, rng, bx, by_):
                    if b[0] < bx or b[2] > bx + bw or b[1] < by_ or b[3] > by_ + bh:
                        out.append(f"[chart-edge-bleed] t={t:.2f} 아일랜드 {name} 상자 {tuple(round(x, 1) for x in b)} 가 상자 밖에 닿는다")
    out += projection_hold_issues(P)   # v7.4.0 D-0277 §1
    return list(dict.fromkeys(out))


PROJ_HOLD_MIN_SEC = 0.5   # v7.4.0 D-0277 §1 — 카메라가 이만큼 멈춰 있으면 "머무는 창"(이동 보간 중 통과는 허용)


def camera_holds(cams: np.ndarray) -> list[int]:
    """카메라가 PROJ_HOLD_MIN_SEC 이상 멈춘 구간마다 가운데 프레임 번호."""
    if cams is None or len(cams) < 2:
        return []
    still = np.r_[False, np.all(np.abs(np.diff(cams, axis=0)) < 1e-6, axis=1)]
    out, i, n = [], 0, len(cams)
    while i < n:
        if not still[i]:
            i += 1
            continue
        j = i
        while j < n and still[j]:
            j += 1
        if j - i + 1 >= PROJ_HOLD_MIN_SEC * FPS:
            out.append((i - 1 + j) // 2)
        i = j
    return out


def projection_hold_views(P) -> list[tuple[float, object, list[dict]]]:  # noqa: ANN001, N803
    """(시각, 그 프레임의 시간축 뷰, 시간축 이벤트) — 카메라가 머무는 창마다(주 무대 timeline 또는 그 시각 차트 아일랜드)."""
    st = P.R.stage
    if st.name == "timeline":
        return [(i / FPS, View(st, P.cams[i]), P.events) for i in camera_holds(P.cams)]
    chart = (getattr(P.R, "cache", None) or {}).get("island_chart")
    if not chart:
        return []
    from engine.island import chart_view, island_box  # noqa: PLC0415

    isl = [e for e in P.events if e.get("type") == "island" and e.get("kind") == "chart"]
    out = []
    for i in camera_holds(chart["cams"]):
        t = i / FPS
        e = next((x for x in isl if x["t0"] <= t <= x["t1"]), None)
        if e is not None:
            out.append((t, chart_view(chart, t, island_box(e)), chart["events"]))
    return out


def projection_column_issues(ctx: cairo.Context, st, v, t: float, events: list[dict], rng: dict) -> list[str]:  # noqa: ANN001
    """한 머무는 창의 전망 열 판정(v7.4.0 back_and_forth D-0277 §1) — ① 열(점 묶음)이 플롯 가장자리에 점 반지름 이상 잘리면 실패
    ② 전망 열이 하나라도 보이는데 같은 레인 마지막 실측 점이 플롯 밖이면 실패(선 → 점 연속, C0 chart_world)."""
    from data.series import load_series  # noqa: PLC0415
    from engine.layers.series import _dot_rules, projection_dots, record_ids, record_points  # noqa: PLC0415
    from engine.pin_labels import plot_bounds  # noqa: PLC0415

    out = []
    r = _dot_rules().dot_r
    stag = TIMELINE.projection.column_stagger_sec
    for e in events:
        if e.get("type") != "series" or e.get("style") != "projection" or not e["t0"] <= t <= e["t1"] or e["lane"] not in rng:
            continue
        rec = load_series(e["series_id"])
        L, _, R, _ = plot_bounds(ctx, v, st, e["lane"], rng[e["lane"]], rec.unit)
        seen = False
        for i, label, x, pts, _ in projection_dots(st, e, rec, rng[e["lane"]]):
            if t < e["t0"] + i * stag:
                continue
            sx, _ = v.to_screen(x, 0.0)
            c0, c1 = sx + min(dx for dx, _ in pts) - r, sx + max(dx for dx, _ in pts) + r
            if c1 <= L or c0 >= R:
                continue
            seen = True
            cut = max(0.0, L - c0) + max(0.0, c1 - R)
            if cut >= r:
                out.append(f"[chart-edge-bleed] t={t:.2f} 전망 열 {label} 이 플롯 가장자리에 {cut:.0f}px 잘린 채 카메라가 머문다 — 완전히 안 또는"
                           " 완전히 밖으로(D-0277 §1)")
        if not seen:
            continue
        last = max((d for o in events if o.get("type") == "series" and o.get("lane") == e["lane"] and o.get("style") != "projection"
                    for sid in record_ids(o) for d, _ in record_points(load_series(sid))), default=None)
        if last is not None:
            ax, _ = v.to_screen(st.x_of(last), 0.0)
            if not L <= ax <= R:
                out.append(f"[chart-edge-bleed] t={t:.2f} 전망 열이 보이는 머무는 창에 마지막 실측 점({last})이 없다 — 선 → 점 연속이 끊긴다(D-0277 §1, C0)")
    return out


def projection_hold_issues(P) -> list[str]:  # noqa: ANN001, N803
    """[chart-edge-bleed] 전망 열 홀드 판정(v7.4.0 D-0277 §1, rules stage_timeline.projection.hold_clip)."""
    if TIMELINE.projection.hold_clip != "hard":
        return []
    rng = P.R.cache.get("series_range") or {}
    world = chart_world(P)
    if world is None or not rng:
        return []
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    st = world[0]
    return [s for t, v, ev in projection_hold_views(P) for s in projection_column_issues(ctx, st, v, t, ev, rng)]


def catalog_label_times(P) -> list[float]:  # noqa: ANN001, N803
    """라벨 비교차 표본 — 문장마다 시작·가운데·끝(자막이 바뀌는 순간과 가장 긴 자막을 덮는다)."""
    return sorted({round(t, 3) for s in P.plan.sentences for t in (s.t0 + 0.05, (s.t0 + s.t1) / 2, s.t1 - 0.05) if s.t1 > s.t0})


def check_catalog_label_overlap(P) -> list[str]:  # noqa: ANN001, N803
    """[catalog-label-overlap] hard(v7.4.0 D-0251 §1.1) — 카탈로그 판 라벨 상자(그리기와 같은 label_box)가 날짜 뱃지 상자·자막 글자 상자와 교차.
    카탈로그 판만(전편·콘티 판은 라벨이 없다 → 빈 목록). 표본 시각마다 실제 프레임을 그려 그 프레임의 라벨 줄로 잰다."""
    if not getattr(P, "catalog", False):
        return []
    import cairo  # noqa: PLC0415

    from engine.hud import date_box  # noqa: PLC0415
    from engine.layers.catalog import label_box  # noqa: PLC0415
    from engine.render import render_frame  # noqa: PLC0415
    from engine.subtitles import subtitle_boxes  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    for t in catalog_label_times(P):
        render_frame(P, min(P.n_frames - 1, max(0, int(t * FPS))))
        lines = P.R.cache["catalog"]["last"]["lines"]
        if not lines:   # 전면 카드 구간 — 라벨을 그리지 않는다
            continue
        lb = label_box(lines)
        others = [("날짜 뱃지", date_box())] + [("자막", b) for b in subtitle_boxes(ctx, P.R.tb, t)]
        for name, b in others:
            if lb[0] < b[2] and b[0] < lb[2] and lb[1] < b[3] and b[1] < lb[3]:
                out.append(f"[catalog-label-overlap] t={t:.2f} 라벨 {tuple(round(v, 1) for v in lb)} ↔ {name} {tuple(round(v, 1) for v in b)}")
    return out


HONESTY = ("chart_honesty", "series_limit_3", "units_visible", "as_of_visible")   # engine.honesty.judge 가 내는 id


def profile_skips(P) -> set[str]:  # noqa: ANN001, N803
    """검사 프로파일(v4.9.0 back_and_forth D-0108) — 콘티 판은 rules animatic.checks_skip 을 건너뛴다(미디어·글꼴·정직성 없음).
    전편은 빈 집합. 건너뛴 id 는 checks.json items[].skipped·skipped[] 와 provenance animatic.checks_skipped 에 남는다(조용한 생략 아님)."""
    if not getattr(P, "animatic", False):   # 검사 스텁(SimpleNamespace)은 전편
        return set()
    sk = set(R_.animatic.checks_skip)
    bad = sorted(sk - set(HARD) - set(WARN))
    if bad:
        raise ValueError(f"rules animatic.checks_skip 에 없는 검사 id: {bad} — engine.checks HARD·WARN")
    return sk


def frames_info(P, times: list[float], names: list[str]) -> dict:  # noqa: ANN001, N803
    """prev/frames.json — 컷별 시각·문장·활성 이벤트(시각 검수 입력, 17 §4.1)."""
    tb = P.R.tb
    rows = []
    for i, (t, n) in enumerate(zip(times, names), 1):
        last = tb.cur_sentence(t)
        # 읽는 중인 문장만 sid 로 — 문장이 끝난 뒤(엔딩 카드 등)에 직전 문장을 "진행 중"으로 적으면 검수가 거짓 hard 를 낸다
        # (v3.2.0 taiwan_ai 실측: 엔딩 카드 컷을 open_1 진행 중으로 읽고 order hard 2건)
        sid = last if last and tb.sent[last].t0 - 0.3 <= t <= tb.sent[last].t1 + 0.3 else None
        card = next((c.kind for c in P.plan.cards if c.t0 <= t <= c.t1), None)
        act = [e for e in P.events if e["t0"] <= t <= e["t1"]]
        rows.append({"n": i, "file": f"p_{t:07.2f}.png", "label": n, "t": round(t, 3), "sid": sid,
                     "text": tb.sent[sid].text if sid else None, "after_sid": None if sid else last, "card": card,
                     "events": [{"type": e["type"], **{k: e[k] for k in ("kind", "label", "mid", "title", "tag") if k in e},
                                 **_article_phase(e, t)} for e in act]})
    return {"schema_version": 1, "frames": rows}


def _article_phase(e: dict, t: float) -> dict:
    """기사 이벤트 구간(v5.1.0 D-0127 §5) — 프레스 사진(블러 무대) 단독 + 헤드라인 페이드 인 동안 "press_lead", 그 뒤 "headline".
    검수는 press_lead 컷을 empty 로 지적하지 않는다(rules qa_checks.empty_exempt)."""
    if e.get("type") != "article":
        return {}
    A = R_.layout_480p.article_card  # noqa: N806
    return {"phase": "press_lead" if t < e["t0"] + A.press_lead_sec + A.overlay_fade_sec else "headline"}


__all__ = ["FontMissingError", "HARD", "HONESTY", "WARN", "check_audio", "frames_info", "profile_skips", "run_checks"]

