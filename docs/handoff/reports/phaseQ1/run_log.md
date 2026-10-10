<!--
tier: 3
last_synced_with: v5.14.0
ssot_for: [phaseQ1-run-log]
depends_on: [docs/handoff/23_QUALITY_GUIDE_20261010.md, docs/handoff/08_PANELS_AND_CARDS.md, engine/cascade.py, engine/island.py, rules/video_rules.yaml]
last_review: 2026-10-10
-->

# Phase Q1 실행 기록 — cascade V2 (v5.14.0)

지침은 D-0153 §4 와 D-0157 보강 3 입니다. 근거는 사용자 결정 D148(cascade V2 적용)과 가이드 23 §6 입니다.

## 1. 바뀐 것

| 파일 | 내용 |
|---|---|
| `rules cascade` | V2 값으로 교체. `y`→`y0`, `step`→`dx`, `dy` 추가, `back_dy` 삭제, `back_h_drop`·`frame{radius, edge_w, occluder_pad}`·`surface{bg, front, back, text, text_sub, edge}`·`front.{date,title,line}_font` 추가 |
| `schemas/rules_models.py` | `CascadeFrame`·`CascadeSurface`(RGB 0~1 검증), 검증기에 "dy < 뒤 카드 높이" 추가 |
| `engine/island.py` | `draw_frame(ctx, box, a, style=None, occluders=())`. 둘 다 없으면 종전 그리기 그대로 |
| `engine/cascade.py` | slot 식, 뒤 카드 높이, 상자 가림, `visible_rects`·`cascade_boxes`(같은 기하), V2 글꼴·색, 글자 클립은 따로 |
| `tools/cascade_demo.py` | 가이드 §6 가상 기관 8항목 데모 프레임(바탕 = `surface.bg`) |
| 문서 | handoff `08` §15·§15.1, `19` §3 3.21 |

### 1.1 V2 값(가이드 §6 표 그대로)

| 항목 | v5.13.0(D117) | v5.14.0(V2) |
|---|---|---|
| slot | `x = 22 + 68·s`, y = 60 + 슬라이드 + `back_dy 5`·깊이 | `x = 22 + 64·s`, `y = 60 + 12·s`(슬라이드·깊이 Y 없음) |
| 앞 카드 | 214×82, pad 13 | 230×108, pad 14 |
| 날짜·제목·부제 y | 16 / 41 / 61 | 19 / 56 / 82(날짜 x 18 그대로) |
| 글꼴 | 제목 13 SemiBold, 부제 10, 날짜 10.5 Mono SemiBold | 제목 18 **Bold**, 부제 11.5, 날짜 10.5 Mono **Medium** |
| 뒤 카드 | ×0.86 | ×0.86, 높이 (108 − 20·back)·0.86 |
| 상자 | island 공통(모서리 10, 흰 테두리 1, 알파 .18) | 모서리 3, 테두리 0.65 `#4D5851`, 표면 `#1B211D`/`#171C19` |
| 윗선 | 3 | 1.8 |
| 글자색 | 제목 흰색, 부제 `muted` | 제목 `#EDF0E9`, 부제 `#A2AAA5` |
| 그대로 | focus 0.5·shift 0.6·back_fade_px 12·max_back 4·width_cap 560·back_dim 0.06·back_text_alpha 0.5·flag_R 12·actor accent | |

### 1.2 가림(가이드 §6 "확인된 뒤 카드 테두리 단절")

- 옛 원인: `ctx.rectangle(0, 0, clip_x1, H); clip()` 이 `draw_frame` 에도 걸려 상자까지 잘랐습니다.
- 새 방식: 뒤 카드 상자(그림자·바탕·테두리)를 그룹에 그립니다. 앞쪽 카드마다 실제 둥근 사각형(+ 0.325, 테두리 폭 절반)을 `DEST_OUT` 으로 차례로 지웁니다.
  - 남는 알파 = Π(1 − 가림 알파)입니다. 합집합이라 겹친 가림끼리 다시 열리지 않습니다(EVEN_ODD 단일 마스크 아님).
  - 가림 알파 = 앞 카드의 등장·밀려남 알파입니다. 새 카드가 페이드로 나타나는 동안 밑 카드가 같은 비율로 사라져, 반투명끼리 겹쳐 비치지 않습니다.
- 글자는 따로입니다. 다음 카드 왼쪽 끝(`clip_x1`)까지, 경계 12px 알파 그라데이션, 앞/뒤 절반 순서 그대로입니다.
- 회피 상자 `cascade_boxes` = 카드마다 국기 원 상자 + 같은 기하의 보이는 영역 사각형 분해입니다. 가리는 상자는 모서리 반경만큼 줄여 재므로, 둥근 모서리로 드러나는 조각까지 포함합니다(보수적).

## 2. 기준 프레임 — 가림 전/후(D-0157 보강 1)

Q0 과 같은 입력입니다. 가이드 §6 8항목, t = 5.8초, 480p, 바탕 `surface.bg`, 국기 자리표시 `eu`.
`cascade_clip_before_after.png` 는 두 crop 으로 되어 있습니다.
- Q0 과 같은 좌표(x 60~200, y 112~152, ×6).
- 표본이 보이는 넓은 좌표(x 40~230, y 50~145, ×4, 빨간 원 = 표본).

V2 의 '발표'(x 22, y 60, 197.8×75.68)는 '협의'(x 86, y 72)·'조치'(x 150, y 84) 밑에 깔립니다. 드러난 윤곽은 왼쪽 dx 띠와 윗띠(y 60~72)입니다.

| 표본(x, y) | 위치 | v5.13.0 RGB | v5.14.0 RGB |
|---|---|---|---|
| (150, 60) | '발표' 윗변(협의 위) | (147, 140, 65) — 옛 배치의 '조치' 국기 테 | **(38, 44, 40)** 테두리 |
| (200, 60) | '발표' 윗변 | (232, 184, 96) — 옛 '조치' 윗선 | **(38, 44, 40)** 테두리 |
| (219, 66) | '발표' 오른변 | (9, 11, 16) — 옛 '조치' 바탕 | **(48, 56, 52)** 테두리 |
| (50, 135) | '발표' 아랫변 왼쪽 | (8, 10, 14) — 옛 '발표' 안쪽 | **(56, 65, 60)** 테두리 |

- 비교값: 윗띠 안쪽 바탕 (150, 66) = (18, 22, 20), 데모 바탕 = (17, 21, 20).
- 네 표본 모두 V2 에서 바탕보다 밝은 테두리입니다. 테스트 `test_back_card_hidden_under_front_and_border_continuous` 가 같은 좌표를 검사합니다.
- 같은 테스트가 '협의' 밑 (120, 100)·'조치' 밑 (170, 140) 에서 '발표' 상자 알파 0 을 확인합니다.

## 3. 시트

| 파일 | 내용 |
|---|---|
| `cascade_asis_tobe_480p.jpg` | 8항목 데모 t = 1.0·3.0·5.8·7.2·9.4·11.5·13.6·17.0, 위 As-is(v5.13.0) / 아래 To-be(V2), 480p 실크기 |
| `cascade_720p_enter_crop.png` | 720p, '조치' 진입(4.7초) 전 4.6·후 5.3, As-is / To-be |
| `cascade_flag_circles_480p.png` | 480p 실크기 + 4배, 줄무늬 국기(de·nl·fr·ir·in) 원 — 변형·띠 뭉개짐 없음(육안) |
| `cascade_clip_before_after.png` | §2 |

As-is 는 Q1 착수 직전 커밋(`d9e7175`)의 worktree 에서 같은 데모를 그렸습니다(옛 함수 그대로).

## 4. 실측(8항목, 120Hz, 18초 = 2,160시점)

| 항목 | 값 | 가이드 §6 |
|---|---|---|
| 최대 폭 | **549.429** ≤ 560 | 549.429 |
| 뒤 카드 최대 | **4** | 4 |
| 이웃 카드 Δx = 64·Δi, Δy = 12·Δi 오차 | **5.7e−14** | ≤ 5.7e−14 |
| 밀기 중 변위 | 모든 카드 같은 값(테스트) | 같은 offset |

정상 상태 차지 영역(뒤 4 + 앞 1)은 x 10~508, y 48~216 입니다. v5.13.0 은 x 10~508, y 48~150.5(가장 오래된 카드 60 + 5·4 + 70.52)였습니다. 아래로 약 66px 커졌습니다(자막 구역 위, 모서리 날짜 상자와 안 겹침).

## 5. draw_frame 기본 호출 바이트 동일(D-0157 보강 2)

- 단위 테스트: 아일랜드 상자 center·left·right·panel_box × 알파 1.0·0.63·0.2 = 12 경우 모두 v5.13.0 그리기와 바이트 동일.
- AST: style·occluders 를 넘기는 호출은 `engine/cascade.py` 하나(아일랜드·패널은 3인자 그대로).
- 실제 프레임: `fed_policy_2026` 미리보기 22컷을 옛 코드(worktree)·새 코드로 그렸습니다. **22/22 md5 동일**입니다. 모든 컷에 아일랜드가 있고, 7.15·206.97초는 기사 카드, 30.93초 등은 카드가 있습니다.
  - p_0007.15(아일랜드 + 기사) `7a0f703d…`, p_0030.93(아일랜드 + 카드) `54f2b47c…`, p_0206.97(아일랜드 + 기사) `55108aa4…`.
- backdrop 위 패널(`panel_box`)은 이 미리보기에 없습니다. 단위 테스트(panel_box 상자)가 맡습니다.
- 지도 위 패널·기사 카드는 hormuz 골든 25컷이 맡습니다(cascade 0 → 무변경, `test_provenance_e2e`).

## 6. cascade 를 쓰는 저장소 프로젝트

| 프로젝트 | 항목 | V2 글자 검사(`check_text`) |
|---|---|---|
| `hormuz-talks-2026` | 7 | 통과 |
| `kaliningrad-suwalki` | 4 | 통과 |
| `valdai-2026` | 3 | 통과 |

**한계(기록)**: 세 프로젝트 모두 이 환경에 `plan.json`(음성 타임라인)이 없어 전체 미리보기 검사(`[cascade-label-under]`·`[cascade-date]` 등)를 돌리지 못했습니다.
plan 을 만들려면 Supertonic 합성이 필요한데, D-0155 가 V2(정렬) 전 렌더를 막았습니다. 차지 영역이 아래로 약 66px 커졌으므로, 다음 렌더에서 지명 깔림 hard 가 새로 나올 수 있습니다.

## 7. 옛 테스트 갱신(값 단정)

`tests/test_cascade.py` 3개를 V2 의미로 바꿨습니다. 테스트 수는 그대로입니다.

| 테스트 | 전 | 후 |
|---|---|---|
| `test_width_never_exceeds_cap` | 정상 폭 = 4 × step + front.w | 4 × dx + front.w(486) |
| `test_front_on_top_and_back_clipped` | 첫 상자 폭 = step | 보이는 영역 = 왼쪽 dx 띠(전체 높이) + 윗띠(전체 폭), 다음 카드 밑은 안 보임, 첫 상자 = 국기 원 |
| `test_depth_monotonic` | 깊이·내려앉음 단조, y 차 = back_dy × 깊이 | 깊이 단조, 이웃 Δx = dx·Δy = dy(위치는 깊이와 무관) |

`test_g14_cascade.py` 는 바꾸지 않았습니다(글자 지연 단정이 V2 에서도 같음).

## 8. 판단 기록(되돌릴 수 있는 선택)

1. 가림을 "순차 complement clip" 대신 **그룹 + DEST_OUT** 으로 구현했습니다. 결과는 같은 합집합 가림입니다. 앞 카드가 페이드 중일 때 밑 카드도 같은 비율로 사라지게 할 수 있어서입니다(클립은 0/1 이라 등장 순간 튑니다).
2. 상자 바탕 알파는 island 의 `fill_alpha`(0.78), 그림자는 island 의 `shadow` 를 그대로 씁니다. 가이드 §6 에 값이 없어 새 수치를 만들지 않았습니다.
3. 테두리 알파 1.0(`#4D5851` 불투명). 가이드가 색만 줬습니다.
4. 깊이 어두움 `back_dim` 은 유지하고 표면색에 곱합니다. D-0153 이 삭제를 지시한 것은 `back_dy`(깊이 Y)뿐입니다.
5. 새 카드는 제자리 페이드로 나타납니다(옛 아래→위 슬라이드 삭제). 가이드 §6 "개별 Y slide 제거"를 따랐습니다.
6. 가이드의 절제된 강조색(gold `#BFB18F` 등)은 등재하지 않았습니다. 가이드가 "가상 기관용 후보, 실제 국가 identity palette 와 분리"라고 적었고, D-0153 이 actor accent 기존 키 유지를 지시했습니다.
7. `surface.bg` 는 엔진이 쓰지 않습니다(운영 영상은 지도 위). 데모 도구 바탕으로만 씁니다. D-0157 이 등재를 지시했습니다.

## 9. 테스트

`tests/test_q1_cascade_v2.py` 15개입니다(요구 ≥ 12).

| 테스트 | 내용 |
|---|---|
| `test_anchor_direction_every_frame` | 8항목 120Hz 전 시점 이웃 Δx·Δy = dx·dy × Δi(오차 ≤ 1e−9), 순서 역전 0 |
| `test_shift_moves_all_cards_equally` | 밀기 중 모든 카드 같은 변위, 방향 = (−dx, −dy) 비율 |
| `test_width_and_back_count_8_items` | 최대폭 549.429 ≤ 560, 뒤 카드 최대 4 |
| `test_occluders_are_union_not_xor` | 겹친 두 가림의 공통 영역 알파 0, 반투명 가림 = (1 − 알파) 배 |
| `test_back_card_hidden_under_front_and_border_continuous` | t = 5.8 밑 영역 알파 0, 노출 테두리 표본 4 |
| `test_boxes_cover_drawn_pixels` | 8시점, 그린 픽셀(알파 > 0.6) ⊆ 회피 상자 + 1px |
| `test_text_half_order` | 두 제목 동시 표시 0, 새 글자는 뒤 절반에만 |
| `test_overflow_is_error_v2_sizes` | V2 글꼴로 데모 통과, 긴 제목·긴 날짜 오류, draw 전 CascadeError |
| `test_missing_flag_is_schema_error` | 국기 없는 항목 = 모델 오류 |
| `test_item_counts_long_title_empty_line_dense` | 3/5/6/8항목·한계 제목·부제 없음/빈 부제·0.6초 촘촘한 앵커 |
| `test_output_profiles` | 480/720/1080 장치 크기·ARGB32·1초 = fps 프레임·그림 범위 k 배 |
| `test_default_draw_frame_bytes_equal` | §5 단위 12 경우 |
| `test_only_cascade_passes_frame_options` | §5 AST |
| `test_v2_values_and_surface_tokens` | V2 값 = 가이드 표, 표면 토큰 = 가이드 hex, `back_dy`·`step` 없음 |
| `test_validator_rejects_no_overlap` | dy ≥ 뒤 카드 높이 거부, 표면 0~1 밖 거부 |

## 10. 전체 pytest

`FONTCONFIG_FILE` 표준 설정입니다.

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| Q0 끝 | 1430 | 0 | 0 | 0 |
| Q1 끝 | PENDING | | | |
