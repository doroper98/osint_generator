"""썸네일 CLI (v7.4.0 사용자 의견 UF-923·UF-924, D938).

    python -m engine.thumbnail <proj>   → out/thumbnail.png

사용자 원문(2026-11-17): "썸네일 이미지도 같이 줘. 제목이 표시 되는 이미지있지? 그거면 될거 같아.
그리고 내가 옅은 테두리를 썸네일로 하기로 규약을 정한거 같은데."
· "저 이미지 외곽 테두리가 아니라 이미지 외곽에서 몇 px 들어와서 그려지는 고급진 테두리를 말하느거잖아"

썸네일 = 제목 카드 프레임 + 안쪽 액자선. 프레임은 완성 영상과 같은 렌더러(engine.render.render_frame)로 그린다 — 영상에 없는 화면을 따로 만들지 않는다.
액자선은 이미지 맨 가장자리가 아니라 가장자리에서 rules thumbnail.border.inset 만큼 안으로 들어와 가는 선 한 줄로 그린다.
engine.mux 가 완성본을 만들 때 같이 부른다(전달물에서 빠지지 않게). 제목 카드가 없는 프로젝트는 만들지 않고 그 사실을 돌려준다(조용히 건너뛰지 않는다).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cairo

from engine.style import FPS, H_OUT, hexc, output_profile
from rules import load_rules

T = load_rules().thumbnail
FILE = "thumbnail.png"


def title_time(cards: list) -> float | None:
    """썸네일을 뜰 시각 — 제목 카드 구간의 title_at 비율 지점. 제목 카드가 없으면 None."""
    for c in cards:
        if c.kind == "title":
            return c.t0 + (c.t1 - c.t0) * T.title_at
    return None


def frame_rect(w: int, h: int) -> tuple[float, float, float, float, float]:
    """안쪽 액자선의 (x, y, 폭, 높이, 선 두께) — 장치 px. 선의 바깥 가장자리가 이미지 가장자리에서 inset 만큼 안쪽이다."""
    k = h / H_OUT
    inset, lw = T.border.inset * k, T.border.w * k
    return inset + lw / 2, inset + lw / 2, w - 2 * inset - lw, h - 2 * inset - lw, lw


def draw_border(surf: cairo.ImageSurface) -> tuple[float, float]:
    """안쪽 액자선을 그린다 — 이미지 가장자리에서 inset 만큼 들어온 가는 선 한 줄. 돌려주는 값 = (안쪽 거리, 선 두께) 장치 px."""
    w, h = surf.get_width(), surf.get_height()
    x, y, rw, rh, lw = frame_rect(w, h)
    ctx = cairo.Context(surf)   # 새 문맥 = 장치 좌표(설계 좌표 변환 없음)
    ctx.set_source_rgba(*hexc(T.border.rgb), T.border.alpha)
    ctx.set_line_width(lw)
    ctx.rectangle(x, y, rw, rh)
    ctx.stroke()
    surf.flush()
    return x - lw / 2, lw


def make(proj: Path) -> dict:
    """out/thumbnail.png 를 쓰고 기록을 돌려준다(provenance thumbnail). 제목 카드가 없으면 written False 와 사유."""
    from engine.project import load_plan, load_project  # noqa: PLC0415 — 순환 import 회피
    from engine.render import render_frame  # noqa: PLC0415

    dest = proj / "out" / FILE
    t = title_time(load_plan(proj).cards)
    if t is None:
        if dest.exists():
            dest.unlink()   # 지난 실행의 썸네일이 이번 영상 것처럼 남지 않게
        return {"written": False, "reason": "제목 카드 없음 — 썸네일을 만들지 않았다(rules thumbnail = 제목 카드 프레임)"}
    P = load_project(proj, out=output_profile(T.profile))  # noqa: N806
    surf, _ = render_frame(P, min(P.n_frames - 1, int(t * FPS)))
    inset, lw = draw_border(surf)
    dest.parent.mkdir(exist_ok=True)
    surf.write_to_png(str(dest))
    return {"written": True, "file": FILE, "t": round(t, 3), "size": [surf.get_width(), surf.get_height()], "profile": P.R.out.name,
            "border": {"inset_px": round(inset, 2), "w_px": round(lw, 2), "rgb": T.border.rgb, "alpha": T.border.alpha},
            "sha1": hashlib.sha1(dest.read_bytes()).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    from engine.project import ProjectError  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="engine.thumbnail")
    ap.add_argument("proj", type=Path)
    proj = ap.parse_args(argv).proj.resolve()
    try:
        rec = make(proj)
        if not rec["written"]:
            raise ProjectError(rec["reason"])
        res = StageResult(ok=True, stage="thumbnail", artifacts={"thumbnail": str(proj / "out" / FILE)})
        print(f"thumbnail ok t={rec['t']} {rec['size'][0]}x{rec['size'][1]} frame inset {rec['border']['inset_px']}px line {rec['border']['w_px']}px",
              file=sys.stderr)
    except (ProjectError, KeyError, ValueError, OSError) as ex:
        res = StageResult(ok=False, stage="thumbnail", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
