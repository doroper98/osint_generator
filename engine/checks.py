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
| media_beats | warning | `media_plan.density_report` 경고(D38) |
| endcard_roll | warning | v4.7.0(D-0106): 엔딩 카드 크레딧이 한도를 넘어 롤(속도 ≤ end_card.scroll_max_px_per_sec) `[endcard-roll]`. 상한 초과는 offscreen `[endcard-overflow]` hard |
| media_upscaled | warning | 사진·영상·컷아웃 원본 픽셀 폭 < 출력 프로파일의 장치 폭(설계 폭 × k) — 추측 보간 금지, 알리기만(v3.6.0 D-0067 요건 3) |
| labels | hard | 샘플 시각마다 도시 라벨 수 ≤ labels_per_frame_max |
| date | hard | 문장 date 형식(YYYY / YYYY.MM / YYYY.MM.DD) — 날짜 배지는 이 값으로만 그린다 |
| subtitles | hard | 자막 줄 수 ≤ subtitle_lines_max(렌더러와 같은 wrap) |
| rights | hard | 권리 점검(load_project 의 check_credits·validate_media)이 통과했으면 0 |
| forbidden | hard | 도장·비네팅·모서리 브랜드: 레지스트리 밖 이벤트 타입 0, vignette 끔, 모서리 요소 = 날짜뿐. v4.5.0(D85): 프리뷰 컷에 그린 글자 중 검증 라벨 문구(`script_schema.labels`) 0 `[label-in-body]` |
| stage_continuity | hard | 무대 연속성(v4.1.0 D-0076·D-0077, GOAL G3-17): 보조 무대 ≤ stage.max_secondary, 무대 전환은 dip 만, 같은 무대 안 먼 cut 금지, 전환 ≤ stage.continuity.max_switches (`engine.shots.stage_continuity`) |
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
| stage_choice | warning | v5.1.0(D-0123 §2): 주 무대 ≠ 장르 기본 무대(default_stage = 장르 프로필 stage.primary)인데 direction stage_reason 없음 `[stage-choice]` |
| as_of_visible | hard | 기준 시점·출처 줄 — 시리즈는 프리뷰 컷에 그린 출처 줄, 패널은 08 §9 출처 체계. 적용 범위 = qa_checks.chart_targets(축 종류) |
"""

from __future__ import annotations

from functools import lru_cache
from typing import Callable

import cairo

from engine.layers.media import KEN_BURNS_MAX
from engine.media_plan import density_report, placement_warnings
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
HARD = ("overlap", "offscreen", "glyphs", "glyph_size", "labels", "date", "subtitles", "rights", "forbidden", "stage_continuity",
        "genre_elements", "chart_honesty", "series_limit_3", "units_visible", "as_of_visible", "boundary_as_route",
        "geo_mismatch", "timeline_rescale", "backdrop_rights", "backdrop_repeat", "island_overlap",
        "backdrop_main_missing", "island_label_clip", "chain")   # island_label_clip v5.2.0 D-0133 §2, backdrop_main_missing v5.2.0 D-0129 §B, island_overlap v5.1.0 D-0126 Q3, geo_mismatch v4.10.0 D-0116, timeline_rescale v5.1.0 D-0121 §A, backdrop_* v5.1.0 D-0123
WARN = ("shots", "media_beats", "media_upscaled", "endcard_roll", "geo_unsourced",   # endcard_roll v4.7.0 D-0106, geo_unsourced D-0107
        "static_window", "stage_choice", "card_island", "island_label_overlap")   # static_window v4.11.0 D-0118, stage_choice v5.1.0 D-0123, card_island v5.2.0 D-0129 §C, island_label_overlap D-0133 §3


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


CHAIN_STEP_SEC = 0.1   # 사건 띠 샘플 간격(접기 0.45·밀기 0.6초를 놓치지 않게)


def check_chain(P) -> list[str]:  # noqa: ANN001, N803
    """v5.2.0 사건 띠 v2(back_and_forth D-0135) — 띠 폭 ≤ width_cap, 보이는 칩 ≤ max_chips, 모서리 날짜 상자와 교차 0,
    지명(지도 라벨)이 띠 상자 밑에 깔리는 순간 0 — 도시·나라·도 이름은 렌더처럼 띠 상자를 회피한 뒤 본다(회피 장치가 없는 해역 이름이 걸리면
    연출이 구도를 바꾼다), 글자 넘침 0.
    문제마다 처음 시각 한 줄. 지도가 가려진 순간(패널·전면 카드·암전)은 깔림을 보지 않는다."""
    from engine.chain import chain_boxes, chain_width, check_text, chip_count  # noqa: PLC0415
    from engine.hud import date_box  # noqa: PLC0415
    from engine.style import CHAIN  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: list[str] = []
    db = date_box()
    for e in P.events:
        if e["type"] != "chain":
            continue
        out += check_text(ctx, e)
        seen: set[str] = set()
        t = e["t0"]
        while t <= e["t1"]:
            boxes = chain_boxes(t, e)
            w = chain_width(t, e)
            if w > CHAIN.width_cap and "w" not in seen:
                seen.add("w")
                out.append(f"[chain-width] t={t:.2f} 띠 폭 {w:.0f}px > width_cap {CHAIN.width_cap:.0f}")
            c = chip_count(t, e)
            if c > CHAIN.max_chips and "c" not in seen:
                seen.add("c")
                out.append(f"[chain-chips] t={t:.2f} 칩 {c}개 > max_chips {CHAIN.max_chips}")
            if any(_box_hit(b, db) for b in boxes) and "d" not in seen:
                seen.add("d")
                out.append(f"[chain-date] t={t:.2f} 띠가 모서리 날짜 상자와 겹침")
            if boxes and not _covered(P, t):
                v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
                for lb in P.R.stage.draw_labels(ctx, v, list(boxes), 0.0) or []:   # 렌더와 같이 띠 상자를 회피한 뒤 남는 지명(해역 등)
                    if any(_box_hit(lb, b) for b in boxes):
                        key = f"l{round(lb[0])}:{round(lb[1])}"
                        if key not in seen:
                            seen.add(key)
                            out.append(f"[chain-label-under] t={t:.2f} 지명 상자 {tuple(round(x) for x in lb)} 가 띠 밑에 깔림"
                                       " — 첫 숏 구도(camera lon·lat·w)를 바꾼다")
            t += CHAIN_STEP_SEC
    return out


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
        b = (b[0] + ex, b[1] + ey, b[2] + ex, b[3] + ey)
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
        "media_beats": lambda: list(density_report(P.events, P.R.tb, P.plan.total)["warnings"]),
        "media_upscaled": lambda: check_media_upscaled(P),
        "endcard_roll": lambda: check_endcard_roll(P),
        "labels": lambda: check_labels(P, times),
        "date": lambda: [f"{s.sid} 날짜 형식 {s.date!r}" for s in P.plan.sentences if not DATE_RE.match(s.date)],
        "subtitles": lambda: check_subtitles(P),
        "rights": lambda: [],   # load_project 가 권리 점검(check_credits·validate_media)에서 실패하면 여기까지 오지 않는다
        "forbidden": lambda: check_forbidden(P, provenance) + check_label_glyphs(drawn),
        "stage_continuity": lambda: check_stage_continuity(P),
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
        "chain": lambda: check_chain(P),
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

