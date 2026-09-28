"""post 카드 프리뷰 (v3.2.0, 18 §5, back_and_forth D-0051 작업 9) — 픽스처 소스(가상 계정·문구)를 실제 렌더러로 그린다.

    python tools/post_preview.py --proj projects/hormuz_korea --out docs/handoff/reports/phase6_95/post

배경은 프로젝트의 한 프레임(지도·자막 포함). 세 가지: 공식 계정·verified(우상단 카드), 미등재 계정·unverified(`<미검증>`),
개인 계정·삭제된 게시물(이름·핸들 가림, 패널 자리). 소스는 tests/fixtures/intake/post_sources.json — 실제 게시물이 아니다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cairo
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.layers.post import draw_post, post_geom  # noqa: E402
from engine.project import load_project  # noqa: E402
from engine.registry import validate_events  # noqa: E402
from engine.render import render_frame  # noqa: E402
from engine.style import FPS, H_OUT, W_OUT  # noqa: E402
from schemas.source_models import SourcesFile  # noqa: E402

FIX = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "intake" / "post_sources.json"
CASES = (("official_verified", {"src": "src_x_0001", "hl": "해군 호위", "quote": True}),
         ("unknown_unverified", {"src": "src_x_0002", "hl": "되돌아갔다"}),
         ("private_deleted_panel", {"src": "src_x_0003", "at": "panel"}))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proj", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--t", type=float, default=61.0, help="배경 프레임 시각(초)")
    args = ap.parse_args(argv)
    P = load_project(args.proj)  # noqa: N806
    P.R.cache["sources"] = SourcesFile.model_validate_json(FIX.read_text(encoding="utf-8")).by_id()
    args.out.mkdir(parents=True, exist_ok=True)
    shots = []
    for name, extra in CASES:
        ev = validate_events([{"type": "post", "t0": args.t - 3.0, "t1": args.t + 5.0, **extra}])[0]
        surf, buf = render_frame(P, int(args.t * FPS))
        ctx = cairo.Context(surf)
        ev["post_box"] = post_geom(ctx, ev, P.R.cache["sources"])[:4]
        draw_post(ctx, P.R, args.t, ev)
        surf.flush()
        im = Image.frombuffer("RGBA", (W_OUT, H_OUT), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB")
        im.save(args.out / f"{name}.png")
        shots.append(im)
        print(f"{name}: {args.out / (name + '.png')}")
    sheet = Image.new("RGB", (W_OUT, H_OUT * len(shots)))
    for i, im in enumerate(shots):
        sheet.paste(im, (0, H_OUT * i))
    sheet.save(args.out / "post_preview.jpg", quality=88)
    return 0


if __name__ == "__main__":
    sys.exit(main())
