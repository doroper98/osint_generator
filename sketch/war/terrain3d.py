"""terrain3d — 고도 높이맵 3D 궤도 구상 컷(v7.4.0 전쟁사 구상 컷 B, back_and_forth D-0604 §1-B, UF-250·UF-251). 무대 = proposed(stages_planned).

    python -m sketch.war.terrain3d projects/<pid> --t 36.5 [--spec <sketch.yaml>] [--theme relief] [--orbit]
        → projects/<pid>/out/terrain3d/{terrain3d_still.png, terrain3d_orbit.mp4, terrain3d_provenance.json}

같은 세계: 높이 = geo.prep 가 받은 Terrarium 고도 타일(K 티어), 텍스처 = 같은 영역의 지도 테마 바탕(MercatorStage.base_image),
부대 = spec 키프레임의 시각 t 상태(지표 위 납작한 면, 진영 색), 강 = spec rivers, 지명 = Pleiades 좌표.
렌더 = tools/terrain3d(headless Chromium + three.js 0.170.0, MIT). 카메라는 전장 중심 궤도(고도각·반경·주기·시작 방위 = rules sketch.war.terrain3d).
결정적: 무작위 없음, 프레임마다 방위만 정해진 곡선. 모서리에는 날짜 뱃지만(코드 조판, schemas.era_date.badge_text).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

import cairo
import numpy as np
import yaml
from PIL import Image

from engine.assets import Assets, load_labels
from engine.projection import View
from engine.stage import MercatorStage, ym
from engine.style import C, DATE_BADGE, output_profile
from engine.typography import text
from geo.prep import CACHE, load_conf
from geo.prep_tiers import TILE, TierSpec, mosaic
from rules import load_rules
from schemas.era_date import badge_text
from sketch.common.draw import SK
from sketch.common.geodesy import dest
from sketch.war.scene import LABELS_FILE, date_at, load_places
from sketch.war.spec import WarSpec
from engine.glyphs.arms import draw_glyph
from sketch.war.units import WS, key_at

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "terrain3d"
M_PER_DEG_LAT = 110540.0      # 지구 타원체 근사(위도 1도 m) — 지역 좌표 변환식 상수(geodesy 와 같은 수준)
M_PER_DEG_LON_EQ = 111320.0   # 적도 경도 1도 m
RIGHT = 90


def hexs(rgb: tuple) -> str:
    return "#" + "".join(f"{int(round(c * 255)):02x}" for c in rgb[:3])


class Local:
    """경위도 ↔ 지역 평면 m(x 동쪽, z 남쪽). three.js: 북 = −z."""

    def __init__(self, lon0: float, lat0: float) -> None:
        self.lon0, self.lat0 = lon0, lat0
        self.kx = M_PER_DEG_LON_EQ * math.cos(math.radians(lat0))

    def xz(self, lon: float, lat: float) -> list[float]:
        return [round((lon - self.lon0) * self.kx, 2), round(-(lat - self.lat0) * M_PER_DEG_LAT, 2)]


def unit_poly(k) -> list[tuple[float, float]]:  # noqa: ANN001 — UnitKey
    side = k.heading + RIGHT
    out = []
    for s_lat, s_dep in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lon, lat = dest(k.lon, k.lat, side if s_lat > 0 else side + 180, k.length_km / 2)
        out.append(dest(lon, lat, k.heading if s_dep > 0 else k.heading + 180, k.depth_km / 2))
    return out


def shape_poly(shape: str, rect: list[list[float]]) -> list[list[float]]:
    """2D 와 같은 윤곽(sketch.war.units) — rect = 뒤-왼, 뒤-오른, 앞-오른, 앞-왼(지역 m)."""
    r = np.array(rect)
    if shape == "wedge":
        tip = (r[2] + r[3]) / 2
        out = [r[0], r[1], r[1] + (tip - r[1]) * SK.war.unit.wedge_ratio, tip]
    elif shape == "triangle":
        out = [r[0], r[1], (r[2] + r[3]) / 2]
    else:
        out = list(r)
    return [[round(float(a), 2), round(float(b), 2)] for a, b in out]


def rank_posts(poly: list[list[float]], gap: float, limit: int) -> list[list[float]]:
    """윗면 대열 기둥 — 고정 간격 격자 중 윤곽 안 점(병력 비례 아님). 결정적(격자 순서)."""
    P = np.array(poly)  # noqa: N806
    c = P.mean(axis=0)
    Q = c + (P - c) * 0.85  # noqa: N806 — 가장자리에서 들인 윤곽
    lo, hi = P.min(axis=0), P.max(axis=0)

    def inside(x: float, z: float) -> bool:   # 짝홀 규칙
        hit = False
        for (x1, z1), (x2, z2) in zip(Q, np.roll(Q, -1, axis=0)):
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
                hit = not hit
        return hit

    inside_pts = [(x, z) for z in np.arange(lo[1] + gap / 2, hi[1], gap) for x in np.arange(lo[0] + gap / 2, hi[0], gap) if inside(x, z)]
    return [[round(float(a), 2), round(float(b), 2)] for a, b in inside_pts[:limit]]


def glyph_png(name: str, px: int, out: Path) -> str:
    """병종 빌보드 그림(투명 바탕, 흰 글리프 + 어두운 테두리) — 2D 와 같은 engine.glyphs.arms."""
    G = WS.glyph  # noqa: N806
    pad = 4
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, px + 2 * pad, px + 2 * pad)
    ctx = cairo.Context(surf)
    k = px / G.size_px
    draw_glyph(ctx, name, px / 2 + pad, px / 2 + pad, px, (1, 1, 1), G.alpha, G.halo_rgb, G.halo_px * k)
    f = f"glyph_{name}.png"
    surf.write_to_png(str(out / f))
    return f


def build(project: Path, spec: WarSpec, t: float, theme: str, out: Path) -> dict:
    T3 = SK.war.terrain3d  # noqa: N806
    sh = [s for s in spec.shots if s.t0 <= t][-1]
    lon_c, lat_c = sh.lon, sh.lat
    W_ = T3.region_w_deg
    H_ = W_ * T3.height / T3.width   # 메르카토르 y 폭(화면 비)
    out.mkdir(parents=True, exist_ok=True)
    # 텍스처 — 같은 영역의 테마 바탕(현대 국경·지명 없음)
    prof = output_profile(T3.texture_res)
    assets = Assets(project, load_labels(project / LABELS_FILE), prof.name, theme=theme)
    stage = MercatorStage(assets, out=prof, proposed_theme=theme if theme in load_rules().geo.themes.proposed else None)
    view = View(stage, np.array([lon_c, ym(lat_c), W_]))
    stage.base_image(view, prof).convert("RGB").save(out / "texture.png")
    lat_n = math.degrees(math.atan(math.sinh(math.radians(view.y1))))
    lat_s = math.degrees(math.atan(math.sinh(math.radians(view.y1 - view.h))))
    lon_w, lon_e = view.x0, view.x0 + view.w
    # 높이 — K 티어 모자이크에서 같은 영역을 격자로
    conf = load_conf(project)
    tc = next(x for x in conf.tiers if x.name == T3.dem_tier)
    TS = TierSpec(tc.name, tc.ppd, tc.z, *tc.bbox)  # noqa: N806
    M, x0, y0 = mosaic(CACHE / "tiles", TS)
    n = TILE * 2 ** TS.z

    def px(lon: float, lat: float) -> tuple[float, float]:
        gx = (lon + 180) / 360 * n - x0 * TILE
        gy = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n - y0 * TILE
        return gx, gy

    nx = T3.grid
    ny = max(2, int(round(nx * T3.height / T3.width)))
    lons = np.linspace(lon_w, lon_e, nx)
    lats = np.linspace(lat_n, lat_s, ny)
    hh = np.zeros((ny, nx), np.float32)
    for j, la in enumerate(lats):
        for i, lo in enumerate(lons):
            gx, gy = px(lo, la)
            hh[j, i] = M[min(M.shape[0] - 1, max(0, int(gy))), min(M.shape[1] - 1, max(0, int(gx)))]
    hh = np.maximum(hh, 0)
    L = Local(lon_c, lat_c)  # noqa: N806
    sw, ne = L.xz(lon_w, lat_s), L.xz(lon_e, lat_n)
    size_m = [ne[0] - sw[0], sw[1] - ne[1]]
    ctr = L.xz((lon_w + lon_e) / 2, (lat_n + lat_s) / 2)
    (out / "height.json").write_text(json.dumps({"nx": nx, "ny": ny, "h": [round(float(v), 1) for v in hh.ravel()]}), encoding="utf-8")

    def rel(lon: float, lat: float) -> list[float]:   # 메시 중심 기준
        x, z = L.xz(lon, lat)
        return [round(x - ctr[0], 2), round(z - ctr[1], 2)]

    units = []
    glyph_files: dict[str, str] = {}
    for u in spec.units:
        if u.keys[0].t > t or (u.t_out is not None and t >= u.t_out):
            continue
        k = key_at(u, t)
        shape = WS.shape_of(u.symbol)
        rect = [rel(lo, la) for lo, la in unit_poly(k)]
        col = C[spec.factions[u.faction].token]
        rec = {"shape": shape, "c": rel(k.lon, k.lat), "name": u.name, "color": hexs(col),
               "side": hexs(tuple(v * WS.depth.side_dark for v in col))}
        if shape in ("dots", "big_dots"):
            r = np.array(rect)
            p0, p1 = (r[0] + r[3]) / 2, (r[1] + r[2]) / 2
            rad = T3.dot_r_m * (2 if shape == "big_dots" else 1)
            n = max(2, int(np.linalg.norm(p1 - p0) / (rad * 3)))
            rec["dots"] = [[round(float(v), 2) for v in p0 + (p1 - p0) * i / n] for i in range(n + 1)]
            rec["dot_r"] = rad
            rec["poly"] = rect
        else:
            rec["poly"] = shape_poly(shape, rect)
            if shape in WS.rank_grid.shapes:
                rec["posts"] = rank_posts(rec["poly"], T3.rank.gap_m, T3.rank.max_posts)
        g = WS.glyph_of(u.symbol)
        if g:
            glyph_files.setdefault(g, glyph_png(g, int(T3.glyph_px * 2), out))
            rec["glyph"] = glyph_files[g]
        units.append(rec)
    places_db = load_places(project)
    places = []
    for p in spec.places:
        if p.t > t or (p.t_out is not None and t >= p.t_out):
            continue
        lon, lat = (places_db[p.pleiades]["lon"], places_db[p.pleiades]["lat"]) if p.pleiades else (p.lon, p.lat)
        if lon_w <= lon <= lon_e and lat_s <= lat <= lat_n:
            places.append({"name": p.name, "c": rel(lon, lat)})
    rivers = [{"pts": [rel(lo, la) for lo, la in r.pts]} for r in spec.rivers]
    # 궤도 중심·반경 = 전장(그 시각 부대 면 전체) — 반경 = 전장 폭 × radius_factor(D-0604 §1-B)
    allp = np.array([q for u_ in units for q in u_["poly"]]) if units else np.array([[0.0, 0.0]])
    target = [round(float(v), 2) for v in (allp.min(axis=0) + allp.max(axis=0)) / 2]
    radius = T3.camera.radius_factor * float(max(allp.max(axis=0) - allp.min(axis=0)))
    fps = T3.fps
    nfr = int(round(T3.orbit_sec * fps))
    step = 360.0 / (T3.camera.period_sec * fps)
    frames = [{"az": round(T3.camera.start_az_deg + i * step, 4)} for i in range(nfr)]
    scene = {"width": T3.width, "height": T3.height, "size_m": size_m, "center": [0, 0], "exaggeration": T3.exaggeration,
             "camera": {"fov": T3.camera.fov_deg, "elev_deg": T3.camera.elev_deg, "radius_m": radius, "target": target},
             "light": T3.light.model_dump(), "sky": T3.sky, "fog": [radius * T3.fog[0], radius * T3.fog[1]],
             "lift_m": T3.lift_m, "label_lift_m": T3.label_lift_m, "unit_opacity": T3.unit_opacity,
             "unit_height_m": T3.unit_height_m, "shadow_offset_m": T3.shadow_offset_m, "shadow_alpha": WS.depth.shadow_alpha,
             "rank": T3.rank.model_dump(), "glyph_px": T3.glyph_px, "rim_alpha": WS.depth.rim_alpha,
             "river": {"w_m": T3.river_w_m, "color": hexs(SK.war.river.rgb)}, "text": T3.text.model_dump(), "halo": T3.halo,
             "units": units, "places": places, "rivers": rivers, "frames": frames}
    (out / "scene.json").write_text(json.dumps(scene, ensure_ascii=False), encoding="utf-8")
    return {"region": [lon_w, lat_s, lon_e, lat_n], "size_m": size_m, "radius_m": radius, "frames": nfr,
            "units": len(units), "glyphs": sorted(glyph_files), "posts": sum(len(u_.get("posts", [])) for u_ in units), "places": len(places), "dem": f"Terrarium z{TS.z}", "theme": theme}


def badge(frame: Path, date: str, scale: float) -> None:
    """모서리 날짜 뱃지(유일한 모서리 요소, C0) — 2D 스케치와 같은 typography."""
    im = Image.open(frame).convert("RGBA")
    arr = np.array(im)[..., [2, 1, 0, 3]].copy()
    surf = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_ARGB32, im.width, im.height)
    ctx = cairo.Context(surf)
    ctx.scale(scale, scale)
    B = DATE_BADGE  # noqa: N806
    W = im.width / scale  # noqa: N806
    w = text(ctx, badge_text(date), W - B.x_right, B.y, B.size, B.font, (1, 1, 1), SK.fade.date_alpha, SK.fade.date_halo, "r")
    ctx.set_source_rgba(*C["gold"], SK.fade.date_line_alpha)
    ctx.rectangle(W - B.x_right - w, B.underline_y, w, B.underline_w)
    ctx.fill()
    surf.flush()
    Image.fromarray(arr[..., [2, 1, 0, 3]]).convert("RGB").save(frame)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="terrain3d 구상 컷(proposed 무대) — 높이맵 3D 궤도")
    ap.add_argument("project", type=Path)
    ap.add_argument("--t", type=float, required=True, help="부대 상태 시각(spec 초)")
    ap.add_argument("--spec", type=Path, default=None)
    ap.add_argument("--theme", default=None)
    a = ap.parse_args(argv)
    spec = WarSpec.model_validate(yaml.safe_load((a.spec or a.project / "sketch.yaml").read_text(encoding="utf-8")))
    T3 = SK.war.terrain3d  # noqa: N806
    theme = a.theme or T3.theme
    out = a.project / "out" / "terrain3d"
    info = build(a.project, spec, a.t, theme, out)
    subprocess.run(["node", str(TOOL / "render.js"), str(out)], check=True, cwd=TOOL,
                   env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()})
    frames = sorted((out / "frames").glob("f_*.png"))
    scale = T3.width / output_profile(None).width
    for f in frames:
        badge(f, date_at(spec, a.t), scale)
    still = out / "terrain3d_still.png"
    Image.open(frames[0]).save(still)
    mp4 = out / "terrain3d_orbit.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(T3.fps), "-i", str(out / "frames" / "f_%04d.png"),
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(mp4)], check=True)
    three = json.loads((TOOL / "node_modules" / "three" / "package.json").read_text(encoding="utf-8"))
    prov = {"schema_version": 1, "stage": "terrain3d(proposed)", "t": a.t, "spec_sha1": hashlib.sha1(
        (a.spec or a.project / "sketch.yaml").read_bytes()).hexdigest(), **info,
        "renderer": f"three.js {three['version']} ({three['license']}) · headless Chromium(playwright) swiftshader",
        "rules": {"sketch.war.terrain3d": T3.model_dump()}, "outputs": [still.name, mp4.name]}
    (out / "terrain3d_provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    print(still, mp4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
