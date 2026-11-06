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
import subprocess
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


def resolve_theme(proj: Path, theme: str | None = None, reason: str | None = None) -> tuple[str, str, str | None]:
    """(테마 이름, 출처, 사유) — v7.4.0 D-0321(UF-178, CLAUDE.md C13). 기본 = order.yaml genre → rules thumbnail.theme_default_by_genre
    (order.yaml 이 없으면 direction.yaml genre, 둘 다 없으면 genres.load.DEFAULT_GENRE). 매핑에 없는 장르 = theme_fallback.
    --theme 로 덮어쓰면 사유 필수(provenance theme_reason)."""
    import yaml  # noqa: PLC0415

    from genres.load import DEFAULT_GENRE  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    T = load_rules().thumbnail  # noqa: N806
    if theme is not None:
        if theme not in T.themes:
            raise ThumbnailError(f"--theme {theme!r} 는 rules thumbnail.themes 에 없다: {sorted(T.themes)}")
        if not (reason or "").strip():
            raise ThumbnailError("--theme 로 장르 기본 테마를 덮어쓸 때는 --theme-reason 이 필요하다(C13)")
        return theme, "override", reason
    genre = None
    for f in ("order.yaml", "direction.yaml"):
        if (proj / f).exists():
            genre = (yaml.safe_load((proj / f).read_text(encoding="utf-8")) or {}).get("genre")
            if genre:
                break
    genre = genre or DEFAULT_GENRE
    return T.theme_default_by_genre.get(genre, T.theme_fallback), f"genre:{genre}", None


def make_thumbnail(proj: Path, theme: str | None = None, reason: str | None = None, name: str = "thumbnail") -> dict:
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
    th, th_src, th_reason = resolve_theme(proj, theme, reason)
    thumb = {"scale": T.title_scale, "line_gap": T.title_line_gap, "max_lines": T.max_lines, "border": T.border, "theme": T.themes[th]}
    surf, buf = render_frame(P, min(P.n_frames - 1, int(tm * FPS)), thumb)
    if "drawn" not in thumb:
        raise ThumbnailError(f"{tm:.2f}초 프레임에 타이틀 카드가 그려지지 않았다")
    img = Image.frombuffer("RGBX", (out.width, out.height), bytes(buf), "raw", "BGRX", 0, 1).convert("RGB")
    od = proj / "out"
    od.mkdir(exist_ok=True)
    png = od / f"{name}.png"
    img.save(png, optimize=True)
    b = io.BytesIO()
    img.save(b, "JPEG", quality=T.jpg_quality, optimize=True)
    if b.tell() > T.jpg_max_bytes:
        raise ThumbnailError(f"thumbnail.jpg {b.tell()} B > rules thumbnail.jpg_max_bytes {T.jpg_max_bytes}")
    jpg = od / f"{name}.jpg"
    jpg.write_bytes(b.getvalue())
    rec = {"schema_version": 1, "frame_t": round(tm, 3), "title_card": [round(t0, 3), round(t1, 3)],
           "title": P.plan.title, "title_lines": thumb["drawn"]["lines"], "title_size_px": thumb["drawn"]["size"],
           "title_scale": T.title_scale, "group_shift_px": thumb["drawn"]["shift_px"], "border": T.border.model_dump(),
           "theme": th, "theme_source": th_src, **({"theme_reason": th_reason} if th_reason else {}),
           "size": [out.width, out.height], "png": {"bytes": png.stat().st_size, "md5": hashlib.md5(png.read_bytes()).hexdigest()},
           "jpg": {"bytes": jpg.stat().st_size, "md5": hashlib.md5(jpg.read_bytes()).hexdigest(), "quality": T.jpg_quality}}
    (od / f"{name}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    pv = od / "provenance.json"
    if pv.exists() and name == "thumbnail":   # 확인용 표본(--name)은 provenance 에 넣지 않는다 — 전달본만
        prov = json.loads(pv.read_text(encoding="utf-8"))
        prov["thumbnail"] = rec
        pv.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


FULLSCREEN_EVENTS = ("quote", "article")   # 화면 전체를 덮는 글자 카드 — 썸네일 바탕이면 큰 제목 뒤로 글자가 비친다(D-0324)


def fullscreen_card_at(proj: Path, plan: object, t: float) -> str | None:
    """시각 t 에 보이는 전면 카드 종류(quote·article 이벤트, plan 엔딩 카드) — 없으면 None. 연출 원본에서 그 두 종류의 시작·끝 앵커만
    plan 시각으로 푼다(지난 영상은 정렬 파일·자산이 없어 연출 전체를 빌드할 수 없다). 앵커를 못 풀면 오류(추정 금지, P6)."""
    from engine.direction import resolve_anchor  # noqa: PLC0415
    from engine.project import read_direction  # noqa: PLC0415
    from engine.timebase import Timebase  # noqa: PLC0415

    for c in plan.cards:
        if c.kind == "end" and c.t0 <= t <= c.t1:
            return "end"
    tb = Timebase(plan)
    for e in read_direction(proj).events:
        if e["type"] not in FULLSCREEN_EVENTS:
            continue
        try:
            a, b = resolve_anchor(e["start"], tb), resolve_anchor(e["end"], tb)
        except Exception as ex:  # noqa: BLE001 — 앵커 종류별 오류를 한 가지로
            raise ThumbnailError(f"전면 카드 {e['type']} 시각을 풀 수 없다({ex}) — --bg 를 명시한다") from ex
        if a <= t <= b:
            return e["type"]
    return None


def make_thumbnail_from_video(proj: Path, video: Path, theme: str | None = None, reason: str | None = None, name: str = "thumbnail",
                              bg: str | None = None) -> dict:
    """--from-video(v7.4.0 back_and_forth D-0322) — out/ 준비물(geo·자산)이 없는 지난 영상. 바탕 = 전달본의 타이틀 카드 t0 − 1/fps 프레임
    (카드 그라데이션이 아직 없는 원 장면), 그 위에 같은 draw_title_card(plan 의 제목·부제·날짜)를 alpha 1 로. 기하·색은 make_thumbnail 과 같다.
    bg = "after" 면 카드가 끝난 직후(t1 + 1/fps) 프레임 — 카드 앞 장면이 글자 카드(인용 등)라 제목 뒤에 글자가 겹칠 때(provenance source.bg)."""
    import subprocess  # noqa: PLC0415

    import cairo  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    from engine.fullcards import draw_title_card  # noqa: PLC0415
    from engine.project import load_plan  # noqa: PLC0415
    from engine.style import FPS, output_profile  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    T = load_rules().thumbnail  # noqa: N806
    out = output_profile("final")
    if (out.width, out.height) != (T.width, T.height):
        raise ThumbnailError(f"출력 프로파일 final {out.width}×{out.height} ≠ rules thumbnail {T.width}×{T.height}")
    if not video.exists():
        raise ThumbnailError(f"전달본 영상 없음: {video}")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                            str(video)], capture_output=True, text=True, check=True).stdout.strip()
    if probe != f"{out.width},{out.height}":
        raise ThumbnailError(f"전달본 해상도 {probe} ≠ {out.width},{out.height}")
    plan = load_plan(proj)
    t0, t1, _ = title_card_time(plan)
    bg_reason = "explicit" if bg is not None else "default"
    if bg is None:   # D-0324(D544) — 기본 before, 그 시각이 전면 카드(quote·article·엔딩) 구간이면 자동 after
        hit = fullscreen_card_at(proj, plan, max(0.0, t0 - 1.0 / FPS))
        bg, bg_reason = ("after", f"auto: before 시각이 전면 카드 {hit} 구간") if hit else ("before", "default")
    if bg not in ("before", "after"):
        raise ThumbnailError(f"--bg {bg!r} — before|after")
    ft = max(0.0, t0 - 1.0 / FPS) if bg == "before" else t1 + 1.0 / FPS
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ft:.4f}", "-i", str(video), "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "bgra", "-"], capture_output=True, check=True).stdout
    if len(raw) != out.width * out.height * 4:
        raise ThumbnailError(f"{ft:.3f}초 프레임을 읽지 못했다({len(raw)} B)")
    buf = bytearray(raw)
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, out.width, out.height, out.width * 4)
    ctx = cairo.Context(surf)
    ctx.translate(out.pad_x, 0)
    ctx.scale(out.k, out.k)
    th, th_src, th_reason = resolve_theme(proj, theme, reason)
    drawn = draw_title_card(ctx, plan, 1.0, 99.0, scale=T.title_scale, line_gap=T.title_line_gap, max_lines=T.max_lines,
                            border=T.border, theme=T.themes[th])
    surf.flush()
    img = Image.frombuffer("RGBX", (out.width, out.height), bytes(buf), "raw", "BGRX", 0, 1).convert("RGB")
    od = proj / "out"
    od.mkdir(exist_ok=True)
    png, jpg = od / f"{name}.png", od / f"{name}.jpg"
    img.save(png, optimize=True)
    b = io.BytesIO()
    img.save(b, "JPEG", quality=T.jpg_quality, optimize=True)
    if b.tell() > T.jpg_max_bytes:
        raise ThumbnailError(f"{name}.jpg {b.tell()} B > rules thumbnail.jpg_max_bytes {T.jpg_max_bytes}")
    jpg.write_bytes(b.getvalue())
    rec = {"schema_version": 1, "frame_t": round(ft, 3), "title_card": [round(t0, 3), round(t1, 3)], "title": plan.title,
           "title_lines": drawn["lines"], "title_size_px": drawn["size"], "title_scale": T.title_scale, "group_shift_px": drawn["shift_px"],
           "border": T.border.model_dump(), "theme": th, "theme_source": th_src, **({"theme_reason": th_reason} if th_reason else {}),
           "source": {"mode": "from_video", "file": video.name, "md5": hashlib.md5(video.read_bytes()).hexdigest(), "frame_t": round(ft, 3), "bg": bg, "bg_reason": bg_reason},
           "size": [out.width, out.height], "png": {"bytes": png.stat().st_size, "md5": hashlib.md5(png.read_bytes()).hexdigest()},
           "jpg": {"bytes": jpg.stat().st_size, "md5": hashlib.md5(jpg.read_bytes()).hexdigest(), "quality": T.jpg_quality}}
    (od / f"{name}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    from engine.fullcards import TitleOverflowError  # noqa: PLC0415
    from engine.project import ProjectError  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="썸네일(타이틀 카드 장면 + 큰 제목 + 금빛 테두리)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--theme", default=None, help="rules thumbnail.themes 이름 — 장르 기본을 덮어쓸 때만(--theme-reason 필수)")
    ap.add_argument("--theme-reason", default=None)
    ap.add_argument("--name", default="thumbnail", help="출력 파일 이름(확인용 표본만 바꾼다 — provenance 에 넣지 않음)")
    ap.add_argument("--from-video", type=Path, default=None,
                    help="지난 영상(out/ 준비물 없음) — 전달본 mp4 의 타이틀 카드 직전 프레임을 바탕으로(D-0322)")
    ap.add_argument("--bg", default=None, choices=["before", "after"],
                    help="--from-video 바탕: 카드 직전·직후 프레임. 생략 = 직전, 단 직전이 전면 카드(quote·article·엔딩)면 직후(D-0324)")
    a = ap.parse_args(argv)
    proj = a.proj.resolve()
    try:
        rec = (make_thumbnail_from_video(proj, a.from_video.resolve(), a.theme, a.theme_reason, a.name, a.bg) if a.from_video
               else make_thumbnail(proj, a.theme, a.theme_reason, a.name))
        res = StageResult(ok=True, stage="thumbnail", artifacts={"png": str(proj / "out" / f"{a.name}.png"),
                                                                 "jpg": str(proj / "out" / f"{a.name}.jpg")}, provenance={"thumbnail": rec})
    except (ThumbnailError, TitleOverflowError, ProjectError, OSError, ValueError, subprocess.CalledProcessError) as ex:
        res = StageResult(ok=False, stage="thumbnail", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
