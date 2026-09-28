"""결정적 사전 검사 `prev/checks.json` (v3.1.0, docs/handoff/17 §3, back_and_forth D-0047 작업 6).

LLM 시각 검수 전에 코드가 잡는 것. 임계는 `rules qa_checks`(코드 상수 금지, 15 P3). 숏 규칙 값은 `rules shot_grammar`.
hard 실패가 하나라도 있으면 시각 검수 LLM 을 부르지 않고 연출 LLM 에 오류만 돌려준다(17 §3, AP-V5-29).

| id | 등급 | 방법 |
| overlap | hard | 사진·영상 상자가 카드·자막·날짜 예약 영역과 겹침(`media_plan.placement_warnings`). 뱃지·마커는 RESERVED 회피가 이미 처리 |
| offscreen | hard | 뱃지 상자(badge_box — 머리·이름표 포함, 17 §3 R×3.3 의 실측판)가 보이는 순간마다 화면 안(전면 카드·패널·암전 구간 제외) |
| glyphs | hard | 화면에 그릴 문자열(이벤트·자막·날짜·크레딧)의 모든 글자가 프로젝트 글꼴 중 하나에 있음(fontTools cmap) |
| shots | warning | 숏 길이 ≥ shot_min_hold_sec, 장면당 이동 ≤ camera_moves_per_scene_max, 암전 ≤ 1/dip_max_per_sec (Phase 7 제안의 바탕) |
| media_beats | warning | `media_plan.density_report` 경고(D38) |
| labels | hard | 샘플 시각마다 도시 라벨 수 ≤ labels_per_frame_max |
| date | hard | 문장 date 형식(YYYY / YYYY.MM / YYYY.MM.DD) — 날짜 배지는 이 값으로만 그린다 |
| subtitles | hard | 자막 줄 수 ≤ subtitle_lines_max(렌더러와 같은 wrap) |
| rights | hard | 권리 점검(load_project 의 check_credits·validate_media)이 통과했으면 0 |
| forbidden | hard | 도장·비네팅·모서리 브랜드: 레지스트리 밖 이벤트 타입 0, vignette 끔, 모서리 요소 = 날짜뿐 |
"""

from __future__ import annotations

import subprocess
from functools import lru_cache

import cairo

from engine.media_plan import density_report, placement_warnings
from engine.projection import View
from engine.style import FONT, FPS, H_OUT, W_OUT
from rules import load_rules
from script.schema import DATE_RE

R_ = load_rules()
QA = R_.qa_checks
SG = R_.shot_grammar
SAMPLE_SEC = 1.0          # 뱃지·라벨 샘플 간격
SHADOW_PX = 7             # badge_box 가 원 둘레에 더하는 그림자 여백 — 이만큼 잘리는 것은 허용
HARD = ("overlap", "offscreen", "glyphs", "labels", "date", "subtitles", "rights", "forbidden")
WARN = ("shots", "media_beats")


@lru_cache(maxsize=None)
def _cmap(family: str) -> frozenset[int]:
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    path = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True, check=True).stdout.strip()
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
    """뱃지 상자(`badges.badge_box` — 원·그림자·인물 머리·이름표)가 보이는 순간마다 화면 안. 그림자 여백만큼은 허용."""
    from engine.layers.badges import badge_box  # noqa: PLC0415

    out: list[str] = []
    A = P.R.assets  # noqa: N806
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    for e in P.events:
        if e["type"] != "badge":
            continue
        t = e["t0"] + 0.5
        while t < e["t1"] - 0.5:
            if not _covered(P, t):
                v = View(P.cams[min(P.n_frames - 1, int(t * FPS))], A.tiers, A.base)
                b = badge_box(ctx, e, *v.xy(e["lon"], e["lat"]))
                over = max(-b[0], -b[1], b[2] - W_OUT, b[3] - H_OUT)
                if over > SHADOW_PX:
                    out.append(f"뱃지 {e.get('label') or e.get('pid') or e.get('flag')} t={t:.1f} 화면 밖 {over:.0f}px "
                               f"(상자 {[round(z) for z in b]})")
                    break
            t += SAMPLE_SEC
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
    out: list[str] = []
    keys = sorted(P.keys, key=lambda k: k.t)
    for a, b in zip(keys, keys[1:]):
        hold = b.t - (a.t + a.dur)
        if hold < SG.shot_min_hold_sec and b.mode == "move":
            out.append(f"숏 t={a.t:.1f}→{b.t:.1f} 머무름 {hold:.1f}s < {SG.shot_min_hold_sec}s")
    tb = P.R.tb
    moves: dict[str, int] = {}
    for k in keys:
        if k.mode == "move" and k.t > 0:
            sc = P.plan.sentences[0].scene
            for s in P.plan.sentences:
                if s.t0 - 1.5 <= k.t:
                    sc = s.scene
            moves[sc] = moves.get(sc, 0) + 1
    out += [f"장면 {sc} 카메라 이동 {n} > {SG.camera_moves_per_scene_max}" for sc, n in moves.items()
            if n > SG.camera_moves_per_scene_max]
    dips = [e for e in P.events if e["type"] == "dip" and not e.get("under")]
    limit = max(1, int(tb.total // SG.dip_max_per_sec) + 1)
    if len(dips) > limit:
        out.append(f"암전 {len(dips)}회 > {limit}(1/{SG.dip_max_per_sec}s)")
    return out


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


def run_checks(P, times: list[float], provenance: dict) -> dict:  # noqa: ANN001, N803
    """모든 검사 → checks.json 내용. hard 합계가 0 이어야 시각 검수로 간다."""
    res: dict[str, list[str]] = {
        "overlap": [w for w in placement_warnings(P.events, P.R.assets.media_assets)],
        "offscreen": check_offscreen(P),
        "glyphs": check_glyphs(P),
        "shots": check_shots(P),
        "media_beats": list(density_report(P.events, P.R.tb, P.plan.total)["warnings"]),
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
        sid = tb.cur_sentence(t)
        act = [e for e in P.events if e["t0"] <= t <= e["t1"]]
        rows.append({"n": i, "file": f"p_{t:07.2f}.png", "label": n, "t": round(t, 3), "sid": sid,
                     "text": tb.sent[sid].text if sid else None,
                     "events": [{"type": e["type"], **{k: e[k] for k in ("kind", "label", "mid", "title", "tag") if k in e}} for e in act]})
    return {"schema_version": 1, "frames": rows}


__all__ = ["HARD", "WARN", "frames_info", "run_checks"]

