"""결정적 사전 검사 `prev/checks.json` (v3.1.0, docs/handoff/17 §3, back_and_forth D-0047 작업 6).

LLM 시각 검수 전에 코드가 잡는 것. 임계는 `rules qa_checks`(코드 상수 금지, 15 P3). 숏 규칙 값은 `rules shot_grammar`.
hard 실패가 하나라도 있으면 시각 검수 LLM 을 부르지 않고 연출 LLM 에 오류만 돌려준다(17 §3, AP-V5-29).

| id | 등급 | 방법 |
| overlap | hard | 사진·영상 상자가 카드·자막·날짜 예약 영역과 겹침, 카드·기사·게시물 카드가 날짜·자막 영역과 겹침(v3.6.0 NB23) (`media_plan.placement_warnings`). 뱃지·마커는 RESERVED 회피가 이미 처리 |
| overlap(label) | hard | 마커 라벨이 카드 영역 때문에 흐려진(알파 < 0.5) 시간 ÷ 마커 표시 시간 > label_hidden_max_ratio `[label-hidden-by-card]`(v3.6.0 D-0068 — 설계된 hide(D36)를 연출 LLM 이 오류로 받게) |
| offscreen | hard | 뱃지 상자(badge_box — 머리·이름표 포함, 17 §3 R×3.3 의 실측판)가 보이는 순간마다 화면 안(전면 카드·패널·암전 구간 제외) |
| glyphs | hard | 화면에 그릴 문자열(이벤트·자막·날짜·크레딧)의 모든 글자가 프로젝트 글꼴 중 하나에 있음(fontTools cmap) |
| shots | warning | 숏 길이 ≥ shot_min_hold_sec, 장면당 이동 ≤ camera_moves_per_scene_max, 암전 ≤ 1/dip_max_per_sec (Phase 7 제안의 바탕) |
| media_beats | warning | `media_plan.density_report` 경고(D38) |
| media_upscaled | warning | 사진·영상·컷아웃 원본 픽셀 폭 < 출력 프로파일의 장치 폭(설계 폭 × k) — 추측 보간 금지, 알리기만(v3.6.0 D-0067 요건 3) |
| labels | hard | 샘플 시각마다 도시 라벨 수 ≤ labels_per_frame_max |
| date | hard | 문장 date 형식(YYYY / YYYY.MM / YYYY.MM.DD) — 날짜 배지는 이 값으로만 그린다 |
| subtitles | hard | 자막 줄 수 ≤ subtitle_lines_max(렌더러와 같은 wrap) |
| rights | hard | 권리 점검(load_project 의 check_credits·validate_media)이 통과했으면 0 |
| forbidden | hard | 도장·비네팅·모서리 브랜드: 레지스트리 밖 이벤트 타입 0, vignette 끔, 모서리 요소 = 날짜뿐 |
"""

from __future__ import annotations

from functools import lru_cache

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
HARD = ("overlap", "offscreen", "glyphs", "labels", "date", "subtitles", "rights", "forbidden")
WARN = ("shots", "media_beats", "media_upscaled")


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
    return [f"글리프 없음 {ch!r} U+{ord(ch):04X} — {ctx}" for ch, ctx in miss.items()]


def _covered(P, t: float) -> bool:  # noqa: ANN001, N803
    """지도가 가려진 순간 — 전면 카드(타이틀·엔딩)·패널·암전. 이때 지도 요소 위치는 화면에 보이지 않는다."""
    if P.R.tb.in_fullcard(t):
        return True
    return any(e["type"] in ("panel", "dip") and e["t0"] <= t <= e["t1"] for e in P.events)


def check_offscreen(P) -> list[str]:  # noqa: ANN001, N803
    """뱃지 상자(`badges.badge_box` — 원·그림자·인물 머리·이름표)와 지점 마커 상자(`markers.marker_box` — 점·라벨·부제,
    D-0049 쟁점 4)가 보이는 순간마다 화면 안. 그림자 여백만큼은 허용. 마커는 렌더러가 그리는 범위(화면 ±80·40px)만 본다."""
    out: list[str] = []
    for e, t, over, b in offscreen_hits(P):
        what = "마커" if e["type"] == "marker" else "뱃지"
        out.append(f"{what} {e.get('label') or e.get('pid') or e.get('flag')} t={t:.1f} 화면 밖 {over:.0f}px "
                   f"(상자 {[round(z) for z in b]})")
    return out


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

    if _covered(P, t):
        return None
    v = View(P.cams[min(P.n_frames - 1, int(t * FPS))], P.R.assets.tiers, P.R.assets.base)
    x, y = v.xy(e["lon"], e["lat"])
    if e["type"] == "marker":
        if x < -80 or x > W_OUT + 80 or y < -40 or y > H_OUT + 40:   # draw_marker 가 그리지 않는 위치
            return None
        b = marker_box(ctx, e, x, y, with_sub=True)
    else:
        b = badge_box(ctx, e, x, y)
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
            v = View(P.cams[min(P.n_frames - 1, int(t * FPS))], P.R.assets.tiers, P.R.assets.base)
            x, y = v.xy(e["lon"], e["lat"])
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
            L.draw_labels(cairo.Context(surf), P.R, View(P.cams[min(P.n_frames - 1, int(t * FPS))], P.R.assets.tiers, P.R.assets.base), t, 1.0)
        finally:
            L.text = orig
        if cnt[0] > QA.labels_per_frame_max:
            out.append(f"t={t:.2f} 도시 라벨 {cnt[0]} > {QA.labels_per_frame_max}")
    return out


def check_shots(P) -> list[str]:  # noqa: ANN001, N803
    """숏 규칙 — engine.shots.shot_issues 한 곳(v3.3.0, 7 린트·제안과 같은 함수)."""
    from engine.shots import shot_issues  # noqa: PLC0415

    return shot_issues(P.keys, P.plan.sentences, P.events, P.R.tb.total)


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


def check_audio(P) -> tuple[list[str], list[str], dict]:  # noqa: ANN001, N803
    """오디오 QA(v3.4.0 D-0060 작업 6·D-0061) — audio/qa.py 한 경로. mux 단계(out/mix.f32·final.mp4 뒤)에서 부른다.
    (hard 지적: 통합 음량·트루 피크·음악 레벨·mix 피크, warning: 문장 RMS 편차, AudioQA dict)."""
    from audio.qa import audio_qa  # noqa: PLC0415

    has_music = any(r.startswith("music.") for r in (P.R.cache.get("credit_refs") or ()))
    q = audio_qa(P.root / "out", P.plan.sentences, has_music=has_music)
    return q.issues(), q.warnings(), q.model_dump()


def run_checks(P, times: list[float], provenance: dict) -> dict:  # noqa: ANN001, N803
    """모든 검사 → checks.json 내용. hard 합계가 0 이어야 시각 검수로 간다."""
    res: dict[str, list[str]] = {
        "overlap": [w for w in placement_warnings(P.events, P.R.assets.media_assets)] + check_label_hidden(P),
        "offscreen": check_offscreen(P),
        "glyphs": check_glyphs(P),
        "shots": check_shots(P),
        "media_beats": list(density_report(P.events, P.R.tb, P.plan.total)["warnings"]),
        "media_upscaled": check_media_upscaled(P),
        "labels": check_labels(P, times),
        "date": [f"{s.sid} 날짜 형식 {s.date!r}" for s in P.plan.sentences if not DATE_RE.match(s.date)],
        "subtitles": check_subtitles(P),
        "rights": [],   # load_project 가 권리 점검(check_credits·validate_media)에서 실패하면 여기까지 오지 않는다
        "forbidden": check_forbidden(P, provenance),
    }
    items = [{"id": k, "severity": "hard" if k in HARD else "warning", "count": len(v), "details": v[:20]} for k, v in res.items()]
    hard = sum(i["count"] for i in items if i["severity"] == "hard")
    return {"schema_version": 1, "hard": hard, "warnings": sum(i["count"] for i in items if i["severity"] == "warning"),
            "passed": hard == 0, "thresholds": QA.model_dump(), "items": items}


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
                     "events": [{"type": e["type"], **{k: e[k] for k in ("kind", "label", "mid", "title", "tag") if k in e}} for e in act]})
    return {"schema_version": 1, "frames": rows}


__all__ = ["FontMissingError", "HARD", "WARN", "check_audio", "frames_info", "run_checks"]

