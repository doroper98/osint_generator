"""새 요소 스케치 프리뷰 (v4.2.0, docs/handoff/20 §4.1-2, back_and_forth D-0081 작업 5) — 실제 엔진 렌더(목업 금지).

    python tools/primitive_sketch.py statement_diff --proj projects/hormuz_korea --genre macro_monetary \
        --extra tests/fixtures/primitives/statement_diff_long.yaml --out docs/handoff/reports/phaseG2/statement_diff_sketch.jpg

컷: ① 모듈 PREVIEW_FIXTURE 등장 중(t0 + fade_sec/2) ② 같은 예제 등장 완료 ③ --extra 예제(줄바꿈) 등장 완료.
색 의미는 --genre 장르 프로필 color_semantics(프리미티브 COLOR_KEYS 가 없으면 오류). 배경은 프로젝트 첫 카메라의 무대
(프리미티브는 무대 무관 오버레이다). 그린 글자는 checks glyph_size 로 검사해 결과를 옆 JSON 에 남긴다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.checks import check_glyph_size  # noqa: E402
from engine.primitives import module  # noqa: E402
from engine.project import load_project  # noqa: E402
from engine.sheet import grid  # noqa: E402
from engine.style import H_OUT, PRIMITIVES, W_OUT  # noqa: E402
from tools._element_render import prepare, render_event, set_genre  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("primitive")
    ap.add_argument("--proj", type=Path, required=True)
    ap.add_argument("--genre", required=True)
    ap.add_argument("--extra", type=Path, action="append", default=[], help="추가 예제 YAML(event: …)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    P = load_project(args.proj)  # noqa: N806
    set_genre(P, args.genre)
    fx = module(args.primitive).PREVIEW_FIXTURE
    fade = PRIMITIVES[args.primitive].fade_sec  # type: ignore[attr-defined]
    shots = [("fixture-appearing", fx, fx["t0"] + fade / 2), ("fixture", fx, fx["t1"] - fade)]
    for p in args.extra:
        ev = yaml.safe_load(p.read_text(encoding="utf-8"))["event"]
        shots.append((p.stem, ev, ev["t1"] - fade))
    cells, drawn, frames = [], [], []
    for name, raw, t in shots:
        ev = prepare(P, raw)
        im, glyphs = render_event(P, ev, t)
        png = args.out.parent / f"{args.out.stem}_{len(cells) + 1}.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        im.save(png)
        cells.append((im, f"{len(cells) + 1}. {name} t={t:.2f} genre={args.genre}"))
        drawn += [(name, size, role, s) for size, role, s in glyphs]
        frames.append({"cut": name, "t": t, "png": png.name, "glyphs": len(glyphs)})
    grid(cells, 1, args.out, cell=(W_OUT, H_OUT))
    rep = {"schema_version": 1, "primitive": args.primitive, "genre": args.genre, "project": args.proj.name, "frames": frames,
           "glyph_size": check_glyph_size(drawn), "min_font_drawn": min(s for _, s, _, _ in drawn)}
    args.out.with_suffix(".json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(args.out, json.dumps(rep["glyph_size"], ensure_ascii=False), rep["min_font_drawn"])
    return 0 if not rep["glyph_size"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
