"""겹침 카드(cascade) 데모 프레임 — 가이드 23 §6 가상 기관 8항목(v5.14.0 back_and_forth D-0153 §4·D-0157).

    python tools/cascade_demo.py --out DIR [--res 480p|720p|1080p] [--times 5.8,7.2 …] [--flags-from projects/<pid>] [--flags eu,de,…]

- 실제 사건·국기가 아니다(가이드 §6). 국기 원은 --flags-from 프로젝트의 국기 자산을 자리표시로 쓴다(기본 `eu` 하나 —
  --flags 로 줄무늬 국기를 돌려 쓰면 작은 원의 띠 뭉개짐·변형을 본다, 가이드 §6 "국기 원").
- 바탕 = rules cascade.surface.bg(시안 바탕 — 운영 영상은 지도 위). 렌더러 = engine.cascade.draw_cascade 그대로.
- 출력: DIR/cascade_<res>_t<초>.png. 시트·비교는 보고서 쪽이 만든다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cairo

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from engine.assets import Assets, Labels  # noqa: E402
from engine.cascade import draw_cascade  # noqa: E402
from engine.context import RenderCtx  # noqa: E402
from engine.style import CASCADE, output_profile  # noqa: E402

AT = [0.5, 2.6, 4.7, 6.8, 8.9, 11.0, 13.1, 15.2]
TITLES = ["발표", "협의", "조치", "후속 대응", "재협의", "추가 조치", "재검토", "후속 발표"]
LINES = ["기관 A가 계획을 공개", "기관 A·B가 세부안을 논의", "기관 B가 후속 조치를 공개", "기관 C가 입장을 공개",
         "기관 A·B가 논의를 이어감", "기관 B가 추가안을 공개", "기관 C가 계획을 검토", "기관 A가 후속 계획을 공개"]


def demo_event(flags: tuple[str, ...] = ("eu",)) -> dict:
    items = [dict(at=a, flag=flags[i % len(flags)], date=f"10. {i + 1:02d}", title=t, line=ln, accent="gold")
             for i, (a, t, ln) in enumerate(zip(AT, TITLES, LINES))]
    return {"type": "cascade", "t0": 0.3, "t1": 18.0, "items": items}


def render(t: float, res: str, flags_from: Path, flags: tuple[str, ...] = ("eu",)) -> cairo.ImageSurface:
    out = output_profile(res)
    R = RenderCtx(assets=Assets(flags_from, Labels(), geo=False), tb=None, out=out)  # type: ignore[arg-type]  # noqa: N806
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, out.width, out.height)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*CASCADE.surface.bg)
    ctx.paint()
    ctx.scale(out.k, out.k)
    draw_cascade(ctx, R, t, demo_event(flags))
    return surf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="cascade 데모 프레임(가이드 23 §6 8항목)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--res", default="480p")
    ap.add_argument("--times", default="1.0,3.0,5.8,7.2,9.4,11.5,13.6,17.0")
    ap.add_argument("--flags-from", type=Path, default=REPO / "projects" / "hormuz_korea")
    ap.add_argument("--flags", default="eu", help="국기 코드 쉼표 목록(항목마다 돌려 씀)")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for t in (float(x) for x in args.times.split(",")):
        p = args.out / f"cascade_{args.res}_t{t:05.2f}.png"
        render(t, args.res, args.flags_from, tuple(args.flags.split(","))).write_to_png(str(p))
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
