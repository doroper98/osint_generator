"""썸네일 (v7.4.0, back_and_forth D-0320, 사용자 의견 UF-177).

사용자 원문: "썸네일은 제목 페이지에서 제목을 좀 더 키우고(필요하다면 어색하지 않은 줄바꿈 가능) 주위에 금빛 얇은 선 테두리를
최외곽에서 조금 떨어진 곳에 고급지게 그려서 만들어. 이건 영상 줄때 매번 만들어서 주는 규칙으로 하자."

    python tools/thumbnail.py projects/<pid>   → out/thumbnail.png(1280×720) · out/thumbnail.jpg(≤ rules thumbnail.jpg_max_bytes) · out/thumbnail.json

- 장면 = 타이틀 카드 중간 시각(c.t0 + 길이/2)의 렌더 프레임 그대로(engine.render.render_frame). 타이틀 카드는 영상과 같은 함수
  engine.fullcards.draw_title_card 로 그리고(썸네일만 다른 모양 금지), 제목만 rules thumbnail.title_scale 배·필요하면 2줄, 금빛 테두리 rules thumbnail.border.
- 썸네일 전용 문구·화살표·얼굴 확대·AI 그림 없음. 타이틀 카드 구성 밖 요소를 넣지 않는다.
- provenance: out/thumbnail.json, out/provenance.json 이 있으면 `thumbnail` 항목으로 합친다(15 P5).
마지막 줄에 StageResult JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class ThumbnailError(RuntimeError):
    """썸네일을 만들 수 없다(타이틀 카드 없음·크기 불일치·용량 초과) — 조용히 다른 모양으로 내보내지 않는다(15 P6)."""


def title_card_time(plan: object) -> tuple[float, float, float]:
    """(t0, t1, 가운데 시각)."""
    cs = [c for c in plan.cards if c.kind == "title"]
    if not cs:
        raise ThumbnailError("plan 에 타이틀 카드가 없다 — 썸네일은 타이틀 카드 장면으로만 만든다")
    c = cs[0]
    return c.t0, c.t1, c.t0 + (c.t1 - c.t0) / 2


def make_thumbnail(proj: Path) -> dict:
    from PIL import Image  # noqa: PLC0415

    from engine.project import load_project  # noqa: PLC0415
    from engine.render import render_frame  # noqa: PLC0415
    from engine.style import FPS, output_profile  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    T = load_rules().thumbnail  # noqa: N806
    out = output_profile("final")
    if (out.width, out.height) != (T.width, T.height):
        raise ThumbnailError(f"출력 프로파일 final {out.width}×{out.height} ≠ rules thumbnail {T.width}×{T.height}")
    P = load_project(proj, out=out)  # noqa: N806
    t0, t1, tm = title_card_time(P.plan)
    thumb = {"scale": T.title_scale, "line_gap": T.title_line_gap, "max_lines": T.max_lines, "border": T.border}
    surf, buf = render_frame(P, min(P.n_frames - 1, int(tm * FPS)), thumb)
    if "drawn" not in thumb:
        raise ThumbnailError(f"{tm:.2f}초 프레임에 타이틀 카드가 그려지지 않았다")
    img = Image.frombuffer("RGBX", (out.width, out.height), bytes(buf), "raw", "BGRX", 0, 1).convert("RGB")
    od = proj / "out"
    od.mkdir(exist_ok=True)
    png = od / "thumbnail.png"
    img.save(png, optimize=True)
    b = io.BytesIO()
    img.save(b, "JPEG", quality=T.jpg_quality, optimize=True)
    if b.tell() > T.jpg_max_bytes:
        raise ThumbnailError(f"thumbnail.jpg {b.tell()} B > rules thumbnail.jpg_max_bytes {T.jpg_max_bytes}")
    jpg = od / "thumbnail.jpg"
    jpg.write_bytes(b.getvalue())
    rec = {"schema_version": 1, "frame_t": round(tm, 3), "title_card": [round(t0, 3), round(t1, 3)],
           "title": P.plan.title, "title_lines": thumb["drawn"]["lines"], "title_size_px": thumb["drawn"]["size"],
           "title_scale": T.title_scale, "group_shift_px": thumb["drawn"]["shift_px"], "border": T.border.model_dump(),
           "size": [out.width, out.height], "png": {"bytes": png.stat().st_size, "md5": hashlib.md5(png.read_bytes()).hexdigest()},
           "jpg": {"bytes": jpg.stat().st_size, "md5": hashlib.md5(jpg.read_bytes()).hexdigest(), "quality": T.jpg_quality}}
    (od / "thumbnail.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    pv = od / "provenance.json"
    if pv.exists():
        prov = json.loads(pv.read_text(encoding="utf-8"))
        prov["thumbnail"] = rec
        pv.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    from engine.fullcards import TitleOverflowError  # noqa: PLC0415
    from engine.project import ProjectError  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="썸네일(타이틀 카드 장면 + 큰 제목 + 금빛 테두리)")
    ap.add_argument("proj", type=Path)
    a = ap.parse_args(argv)
    proj = a.proj.resolve()
    try:
        rec = make_thumbnail(proj)
        res = StageResult(ok=True, stage="thumbnail", artifacts={"png": str(proj / "out" / "thumbnail.png"),
                                                                 "jpg": str(proj / "out" / "thumbnail.jpg")}, provenance={"thumbnail": rec})
    except (ThumbnailError, TitleOverflowError, ProjectError, OSError, ValueError) as ex:
        res = StageResult(ok=False, stage="thumbnail", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
