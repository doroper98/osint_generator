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
| route_missing · route_missing_other | warning · hard | 이동·공격 동사(qa_checks.route_missing) + 문장이 부르는 마커 → 그 마커에 끝점이 닿는 경로가 문장 구간에 있어야 한다. 다른 경로만 보이면 hard(v5.21.14 D-0195·D-0197) |
| frame_missing · frame_missing_target | warning · hard | 문장이 부르는 나라(라벨 점)·마커가 문장 구간 내내 화면 밖. 이동·공격 대상이면 hard(v5.21.14 D-0199) |
| battle_geo | warning | 전황 동사 문장에 지도 마커·경로 없음(v5.22.0 D-0200 UF-08) |
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
from engine.style import FONT, FPS, H_OUT, W_OUT
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
        "backdrop_main_missing", "island_label_clip", "cascade", "subtitle_overlap", "label_collision", "timeline_span", "route_frame", "panel_overflow", "flag_territory", "badge_over_panel", "opening_establish", "camera_continuity", "card_exposure", "route_label_cross", "route_label_overlap", "article_backdrop", "quote_in_script", "route_missing_other", "frame_missing_target")   # island_label_clip v5.2.0 D-0133 §2, backdrop_main_missing v5.2.0 D-0129 §B, island_overlap v5.1.0 D-0126 Q3, geo_mismatch v4.10.0 D-0116, timeline_rescale v5.1.0 D-0121 §A, backdrop_* v5.1.0 D-0123
WARN = ("shots", "media_beats", "media_upscaled", "endcard_roll", "geo_unsourced",   # endcard_roll v4.7.0 D-0106, geo_unsourced D-0107
        "static_window", "stage_choice", "card_island", "island_label_overlap", "cascade_label_hidden",
        "map_contrast_shape", "route_missing", "frame_missing", "battle_geo", "portrait_unused")   # v5.21.14 D-0195·D-0199. map_contrast_shape v5.18.0 D-0161 §4   # static_window v4.11.0 D-0118, stage_choice v5.1.0 D-0123, card_island v5.2.0 D-0129 §C, island_label_overlap D-0133 §3


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

    from engine.layers.animatic import load_flat_polygons  # noqa: PLC0415

    return {k: MultiPolygon([Polygon(q[0], q[1:]) for q in v]).buffer(0) for k, v in load_flat_polygons(False).items()}


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
            if b.t - a.t < op.min_move_sec:
                return [f"[opening-establish] 들어가는 이동 {b.t - a.t:.1f}초 < {op.min_move_sec}초 — 천천히 들어간다"]
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
    evs = [e for e in P.events if e["type"] in ("badge", "marker") and not e.get("over_panel")]
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
        if e["type"] not in ("marker", "route", "barrier") or not e.get("label") or not e["t0"] <= t <= e["t1"]:
            continue
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


def route_label_layout(P, ctx: cairo.Context, v: View, t: float) -> list[tuple[dict, tuple, list]]:  # noqa: ANN001, N803
    """시각 t 에 보이는 경로 이름표 자리(v5.21.11 D-0191 §1-3) — 렌더 flush_route_labels 와 같은 함수·같은 장애물 순서.
    예약 상자 = 뱃지(place_over)·마커 라벨·겹침 카드. → [(이벤트, (x, y, 상자, 통과), 그 순간 경로 선들)]"""
    from engine.cascade import cascade_boxes  # noqa: PLC0415
    from engine.layers.markers import marker_box  # noqa: PLC0415
    from engine.layers.routes import catmull, label_obstacles, place_route_label, route_lines  # noqa: PLC0415
    from engine.timebase import ease_io, window  # noqa: PLC0415

    act = [e for e in P.events if e["t0"] - 0.05 <= t <= e["t1"] + 0.05]
    labs = [e for e in act if e["type"] == "route" and e.get("label") and not e.get("in_island")
            and (ease_io((t - e["t0"]) / e["grow"]) if e["grow"] > 0.05 else 1) >= 0.99 and window(t, e["t0"], e["t1"], 0.35, 0.6) > 0.01]
    if not labs:
        return []
    reserved: list = []
    for e in act:
        if e["type"] == "badge" and not e.get("over_panel") and not e.get("in_island") and (r := place_over(P, ctx, e, t)) is not None:
            reserved.append(r[1])
        elif e["type"] == "marker" and not e.get("in_island") and e["t0"] <= t <= e["t1"]:
            x, y = v.to_screen(*e["world"])
            reserved.append(marker_box(ctx, e, x, y))
        elif e["type"] == "cascade":
            reserved += cascade_boxes(t, e)
    obstacles = label_obstacles(ctx, v, act, t, reserved, P.R.tb)
    lines = route_lines(v, act, t)
    out = []
    for e in labs:
        S_ = v.to_screen_arr(e["curve"] if "curve" in e else catmull(e["world_pts"], 12))  # noqa: N806
        placed = place_route_label(ctx, v.stage, e["label"], S_, obstacles, lines)
        obstacles.append(placed[2])
        out.append((e, placed, lines))
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
    routes = [e for e in P.events if e["type"] == "route" and not e.get("in_island")]
    lo = min((e["t0"] for e in routes), default=0.0)
    hi = max((e["t1"] for e in routes), default=0.0)
    t = lo
    while routes and t < hi:
        if not _covered(P, t):
            v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
            for e, (_, _, b, ok), lines in route_label_layout(P, ctx, v, t):
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
                if e["type"] != "marker" or e.get("in_island") or not e.get("label") or e.get("route_cross_exempt") or not e["t0"] + 0.3 <= t <= e["t1"] - 0.3:
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
    from engine.fullcards import endcard_roll_note, project_credit_sections  # noqa: PLC0415

    if P.R.credits is None or not any(c.kind == "end" for c in P.plan.cards):
        return []
    return endcard_roll_note(project_credit_sections(P.R), [s.column for s in P.R.credits.sections])


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
    from engine.fullcards import endcard_overflow, project_credit_sections, unverified_notice, version_stamp_overflow  # noqa: PLC0415

    if P.R.credits is None or not any(c.kind == "end" for c in P.plan.cards):
        return []
    return (endcard_overflow(project_credit_sections(P.R), [s.column for s in P.R.credits.sections])
            + version_stamp_overflow(unverified_notice(P.R)))   # v5.1.0 D-0124 — 버전 도장 포함


def offscreen_hits(P) -> list[tuple[dict, float, float, tuple]]:  # noqa: ANN001, N803
    """check_offscreen 의 판정 본체(이벤트, 시각, 넘친 px, 상자) — 카메라 제안 검증(engine.camera_suggest)도 이 함수를 쓴다
    (검사기 하나, D-0056 §2). P.cams·P.events 를 바꾼 사본을 넘기면 그 카메라 경로(이동·드리프트 포함)로 본다."""
    out: list[tuple[dict, float, float, tuple]] = []
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    for e in P.events:
        if e["type"] not in ("badge", "marker"):
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
    (rules sketch.checks max_dlogw·max_d2logw·max_d3). 컷 키(암전 컷 포함)에 걸친 차분은 뺀다. 종류마다 최댓값 한 줄."""
    from engine.camera import continuity  # noqa: PLC0415

    if P.cams is None:
        return []
    th = R_.sketch.checks
    cuts = sorted({math.ceil(k.t * FPS - 1e-9) for k in P.keys if k.mode == "cut"})
    lim = {1: th.max_dlogw_per_frame, 2: th.max_d2logw_per_frame, 3: th.max_d3_per_frame}
    out = []
    for k, v in continuity(P.cams, cuts).items():
        o = int(k[1])
        bad = np.flatnonzero(v > lim[o])
        if bad.size:
            i = int(bad[np.argmax(v[bad])])
            out.append(f"[camera-continuity] |Δ{o} {k[3:]}| {v[i]:.4f} > {lim[o]} — t={i / FPS:.2f}s 외 {bad.size - 1}프레임"
                       f"{' (이동 중간 꺾임 — rules shot_grammar.move_ease)' if o == 3 else ''}")
    return out


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
    ms = [e for e in P.events if e["type"] == "marker" and e.get("label") and "world" in e and not e.get("in_island")
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
    names = {}
    lab = getattr(getattr(P.R.stage, "assets", None), "labels", None)
    for k, m, mw in getattr(P.R.stage, "countries", []):
        if mw is not None:
            names[(lab.ko.get(k, m["ko"]) if lab is not None else m["ko"])] = mw
    for s in P.plan.sentences:
        ms, verb = _story_markers(P, s)
        routes = [e for e in P.events if e["type"] == "route" and not e.get("in_island") and e["t0"] < s.t1 and e["t1"] > s.t0]
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
        for nm, (wx, wy) in want.items():
            seen = False
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
            "passed": hard == 0, "profile": "animatic" if getattr(P, "animatic", False) else "full", "skipped": sorted(skip),
            "thresholds": QA.model_dump(), "items": items}


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

