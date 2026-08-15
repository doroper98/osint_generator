"""실번들 → 쇼츠 씬 플랜 (Phase 3 데모용, 계획 §5.3 슬롯 예산제).

Phase 4 의 정식 변환기(`bundle_to_shorts.py`)로 가기 전, **씬킷이 실제 번들 데이터로
조판되는지 확인**하기 위한 최소 추출기. 슬롯 예산제(§5.3.0)를 그대로 적용한다.

사용::

    python hyperframes/shorts/build_scene_plan.py                 # 기본 번들
    python hyperframes/shorts/build_scene_plan.py --url <URL>
    python hyperframes/shorts/build_scene_plan.py -o plan.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_URL = (
    "https://raw.githubusercontent.com/doroper98/agents_reviewer/main/"
    "reports/analysis_20260814_150031_252a4a5e85.bundle.json"
)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 계획 §5.4.1 실측 상수 (calibrate_pace.py 2026-08-15)
PACE_OVERHEAD, PACE_PER_CHAR = 0.225, 0.1298
SENTENCE_CAP = 24


def est_sec(text: str) -> float:
    return max(1.5, min(9.0, PACE_OVERHEAD + PACE_PER_CHAR * len(text)))


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def sec_score(section: dict) -> tuple[int, int, int]:
    """EVIDENCE 섹션 우선순위 — highlights 보유 > emphasis 밀도 > 차트 보유."""
    v = section.get("video") or {}
    return (
        len(v.get("highlights") or []),
        len(v.get("emphasis") or []),
        len(section.get("chart_refs") or []),
    )


def build_plan(b: dict) -> dict:
    rv = b.get("report", {}).get("video", {}) or {}
    intro = rv.get("intro_narration_tts") or rv.get("intro_narration") or []
    outro = rv.get("outro_narration_tts") or rv.get("outro_narration") or []

    scenes: list[dict] = []

    # --- HOOK (보장) -----------------------------------------------------
    headline = b.get("report", {}).get("headline", "")
    if intro:
        scenes.append({
            "scene": "HOOK", "id": "HOOK_01",
            "headline": headline,
            "lines": intro[:1],
        })
    # --- CONTEXT (보장) --------------------------------------------------
    if len(intro) > 1:
        scenes.append({
            "scene": "CONTEXT", "id": "CONTEXT_01",
            "deck": b.get("report", {}).get("deck", ""),
            "lines": intro[1:2],
        })

    # --- TURN (보장) — contradictions 가 화면 설계까지 준다 --------------
    turn = None
    for c in b.get("contradictions") or []:
        v = c.get("video") or {}
        if v.get("narration"):
            turn = {
                "scene": "TURN", "id": "TURN_01",
                "label_a": v.get("label_a", ""), "label_b": v.get("label_b", ""),
                "line_a": v.get("line_a", ""), "line_b": v.get("line_b", ""),
                "lines": (v.get("narration_tts") or v["narration"])[:3],
            }
            break

    # --- CLOSING (보장) --------------------------------------------------
    closing = {"scene": "CLOSING", "id": "CLOSING_01", "lines": outro[:2]} if outro else None

    reserved = sum(
        est_sec(s) for blk in (scenes, [turn] if turn else [], [closing] if closing else [])
        for sc in blk for s in sc["lines"]
    )
    reserved_n = sum(len(sc["lines"]) for blk in (scenes, [turn] if turn else [],
                                                  [closing] if closing else []) for sc in blk)

    # --- EVIDENCE (잔여 예산) -------------------------------------------
    charts = {c.get("chart_id"): c for c in (b.get("charts") or [])}
    budget = SENTENCE_CAP - reserved_n
    picked = []
    for sec in sorted(b.get("sections") or [], key=sec_score, reverse=True):
        v = sec.get("video") or {}
        lines = (v.get("narration_tts") or v.get("narration") or [])
        if not lines:
            continue
        if budget - len(lines) < 0:
            continue
        picked.append(sec)
        budget -= len(lines)
        if budget <= 0:
            break

    # 선정은 중요도로, 배치는 번들 원래 순서로 (§5.3.1-3)
    order = {s.get("section_id"): i for i, s in enumerate(b.get("sections") or [])}
    picked.sort(key=lambda s: order.get(s.get("section_id"), 0))

    evidence = []
    for i, sec in enumerate(picked, 1):
        v = sec.get("video") or {}
        refs = sec.get("chart_refs") or []
        chart = charts.get(refs[0]) if refs else None
        evidence.append({
            "scene": "EVIDENCE", "id": f"EVIDENCE_{i:02d}",
            "section_id": sec.get("section_id"),
            "heading": sec.get("heading", ""),
            "emphasis": v.get("emphasis") or [],
            "highlight": (v.get("highlights") or [None])[0],
            "chart": {
                "chart_id": chart.get("chart_id"), "type": chart.get("type"),
                "title": chart.get("title"), "data": chart.get("data"),
            } if chart else None,
            "lines": (v.get("narration_tts") or v.get("narration") or []),
        })

    ordered = scenes + evidence + ([turn] if turn else []) + ([closing] if closing else [])
    total_lines = sum(len(s["lines"]) for s in ordered)
    total_sec = sum(est_sec(t) for s in ordered for t in s["lines"])

    return {
        "report_id": b.get("report", {}).get("report_id", ""),
        "headline": headline,
        "sentence_count": total_lines,
        "estimated_sec": round(total_sec, 1),
        "scenes": ordered,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("-o", "--out", default=str(HERE / "scene_plan.json"))
    args = ap.parse_args()

    b = fetch(args.url)
    plan = build_plan(b)

    print(f"report_id = {plan['report_id']}")
    print(f"헤드라인  = {plan['headline']}")
    print(f"문장 {plan['sentence_count']}개 / 추정 {plan['estimated_sec']}초 "
          f"(타깃 90~120초, 상한 {SENTENCE_CAP}문장)\n")
    for s in plan["scenes"]:
        secs = sum(est_sec(t) for t in s["lines"])
        extra = ""
        if s.get("chart"):
            extra = f"  [chart {s['chart']['type']}]"
        if s["scene"] == "TURN":
            extra = f"  [{s['label_a']} vs {s['label_b']}]"
        print(f"  {s['id']:14} {len(s['lines'])}문장 {secs:5.1f}s{extra}")
        for t in s["lines"]:
            print(f"      · {t[:58]}")

    pathlib.Path(args.out).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n[저장] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
