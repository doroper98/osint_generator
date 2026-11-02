"""terrain3d 무대 기하 — 지역 평면(m) 투영·부대 키프레임 보간·부대 윤곽(v7.4.0 전쟁사, back_and_forth D-0614·D-0615).

스케치(`sketch.war.terrain3d`·`sketch.war.units`)와 본편 terrain3d 구간(`engine.terrain3d_prep`)이 같은 함수를 쓴다(사본 금지).
수치는 rules(sketch.war.unit·sketch.war.terrain3d — 스케치와 본편이 같은 모양). 이 모듈은 engine.render·engine.project 를 import 하지 않는다
(스케치가 이 모듈을 쓴다 — tests/anti_inertia/test_sketch_no_literals (d) 방향).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from engine.timebase import clamp01, smooth
from rules import load_rules
from schemas.war_units import UnitKey, WarForces, WarUnit
from sketch.common.geodesy import dest   # 순수 수식(numpy) — 측지 전진 한 함수

if TYPE_CHECKING:
    from engine.project import Project
    from engine.terrain3d_prep import Segment

RIGHT = 90
M_PER_DEG_LAT = 110540.0      # 지구 타원체 근사(위도 1도 m) — 지역 좌표 변환식 상수(geodesy 와 같은 수준)
M_PER_DEG_LON_EQ = 111320.0   # 적도 경도 1도 m


def hexs(rgb: tuple) -> str:
    return "#" + "".join(f"{int(round(c * 255)):02x}" for c in rgb[:3])


class Local:
    """경위도 ↔ 지역 평면 m(x 동쪽, z 남쪽). three.js: 북 = −z."""

    def __init__(self, lon0: float, lat0: float) -> None:
        self.lon0, self.lat0 = lon0, lat0
        self.kx = M_PER_DEG_LON_EQ * math.cos(math.radians(lat0))

    def xz(self, lon: float, lat: float) -> list[float]:
        return [round((lon - self.lon0) * self.kx, 2), round(-(lat - self.lat0) * M_PER_DEG_LAT, 2)]


def key_at(u: WarUnit, t: float) -> UnitKey:
    """시각 t 의 부대 상태 — 앞뒤 키 사이 smooth 보간(첫 키 전 = 첫 키, 마지막 키 뒤 = 마지막 키). 키 시각 t 는 초(앵커는 미리 풀어 둔다)."""
    turn_first = load_rules().sketch.war.unit.turn_first_deg
    ks = u.keys
    if t <= ks[0].t:
        return ks[0]
    for a, b in zip(ks, ks[1:]):
        if t < b.t:
            raw = clamp01((t - a.t) / (b.t - a.t))
            k = smooth(raw)
            dh = (b.heading - a.heading + 180) % 360 - 180
            kz = smooth(clamp01(raw * 2 - 1)) if abs(dh) > turn_first else k   # 큰 회전 = 방위 먼저, 크기는 뒤 절반(D-0602 ⑤)
            return UnitKey(t=t, lon=a.lon + (b.lon - a.lon) * k, lat=a.lat + (b.lat - a.lat) * k, heading=a.heading + dh * k,
                           length_km=a.length_km + (b.length_km - a.length_km) * kz, depth_km=a.depth_km + (b.depth_km - a.depth_km) * kz)
    return ks[-1]


def unit_poly(k: UnitKey) -> list[tuple[float, float]]:
    """정면 폭 × 종심 사각형(경위도) — 뒤-왼, 뒤-오른, 앞-오른, 앞-왼."""
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
        out = [r[0], r[1], r[1] + (tip - r[1]) * load_rules().sketch.war.unit.wedge_ratio, tip]
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


class Terrain3DError(ValueError):
    """terrain3d 구간 구성 오류(15 P6 — 조용히 2D 로 바꾸지 않는다)."""


class Terrain3DStage:
    """terrain3d 무대(v7.4.0 D-0614·D-0615 ① 가) — 주 무대(mercator) 위에 끼우는 **구간**. 주 무대가 될 수 없다.

    월드 좌표 = mercator 와 같다(lon, ym(lat)) — 구간에 들어가고 나오는 카메라·무대 연속성 검사가 한 좌표계에서 잰다.
    바탕은 `engine.terrain3d_prep` 가 미리 렌더한 3D 프레임(엔진 render_frame 구간 분기). 설정 = direction stage_config.terrain3d
    {forces: 프로젝트 안 부대 기록 파일(schemas.war_units.WarForces)}.
    """

    name = "terrain3d"
    anchor_keys = ("lon", "lat")
    segment_only = True   # 주 무대 불가 — 숏 단위 구간만(engine.terrain3d_prep.segments 가 주 무대 지정을 오류로)
    CONFIG_KEYS = frozenset({"forces"})

    def __init__(self, assets: object = None, *, out: object = None, config: "dict | None" = None) -> None:
        cfg = dict(config or {})
        extra = set(cfg) - self.CONFIG_KEYS
        if extra:
            raise Terrain3DError(f"terrain3d stage_config 에 모르는 키 {sorted(extra)} — 허용 {sorted(self.CONFIG_KEYS)}")
        if not cfg.get("forces"):
            raise Terrain3DError("terrain3d 구간에는 stage_config.terrain3d.forces(부대 기록 파일)가 필요하다(D-0615 §2)")
        self.forces_path = str(cfg["forces"])
        self.assets, self.out = assets, out

    def to_world(self, **anchor: float) -> tuple[float, float]:
        from engine.stage import StageError, ym  # noqa: PLC0415 — stage → stage_terrain3d 등록 순환 회피

        if set(anchor) != {"lon", "lat"}:
            raise StageError(f"terrain3d 앵커는 lon·lat: {sorted(anchor)}")
        return anchor["lon"], ym(anchor["lat"])

    def from_world(self, x: float, y: float) -> dict[str, float]:
        from engine.stage import lat_of  # noqa: PLC0415

        return {"lon": x, "lat": lat_of(y)}

    def render_base(self, ctx: object, view: object) -> None:
        raise Terrain3DError("terrain3d 는 주 무대가 아니다 — 구간 바탕은 미리 렌더한 3D 프레임(engine.terrain3d_prep)")

    def draw_labels(self, ctx: object, view: object, reserved: list, alpha: float = 1.0) -> None:
        raise Terrain3DError("terrain3d 라벨은 구간 레이어(engine.layers.terrain3d)가 manifest 좌표로 그린다")

    def lod_rules(self) -> dict:
        return {}


PLACES_FILE = Path("ancient_geo") / "places.json"


def _places(proj: Path) -> dict[str, dict]:
    p = proj / PLACES_FILE
    return {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.is_file() else {}


def build_scene(P: "Project", seg: "Segment", forces: WarForces, out: Path) -> dict:  # noqa: N803
    """scene.json·height.json·texture.png — 지형·텍스처는 들어가는 순간의 mercator 화면과 같은 세계(같은 base_image, 더 넓게)."""
    from engine.projection import View  # noqa: PLC0415
    from engine.stage import lat_of  # noqa: PLC0415
    from engine.style import C  # noqa: PLC0415
    from geo.prep import CACHE, load_conf  # noqa: PLC0415
    from geo.prep_tiers import TILE, TierSpec, mosaic  # noqa: PLC0415

    R = load_rules()  # noqa: N806
    T3, ST, WS = R.sketch.war.terrain3d, R.stage_terrain3d, R.war_history.symbol_sets  # noqa: N806
    from engine.style import FPS as fps  # noqa: PLC0415, N811
    i0, i1 = int(round(seg.t_in * fps)), int(round(seg.t_out * fps))
    stage = P.R.stage
    v_in = View(stage, P.cams[i0])
    cx, cy = v_in.x0 + v_in.w / 2, v_in.y1 - v_in.h / 2
    lon_c, lat_c = cx, lat_of(cy)
    region = View(stage, np.array([cx, cy, v_in.w * ST.region_factor]))
    out.mkdir(parents=True, exist_ok=True)
    stage.base_image(region, P.R.out).convert("RGB").save(out / "texture.png")
    lat_n, lat_s = lat_of(region.y1), lat_of(region.y1 - region.h)
    lon_w, lon_e = region.x0, region.x0 + region.w
    conf = load_conf(P.root)
    tc = next((x for x in conf.tiers if x.name == T3.dem_tier), None)
    if tc is None:
        raise Terrain3DError(f"geo.yaml 에 고도 티어 {T3.dem_tier} 가 없다 — terrain3d 높이는 geo.prep 티어(rules sketch.war.terrain3d.dem_tier)")
    TS = TierSpec(tc.name, tc.ppd, tc.z, *tc.bbox)  # noqa: N806
    M, x0, y0 = mosaic(CACHE / "tiles", TS)  # noqa: N806
    n = TILE * 2**TS.z

    def px(lon: float, lat: float) -> tuple[float, float]:
        gx = (lon + 180) / 360 * n - x0 * TILE
        gy = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n - y0 * TILE
        return gx, gy

    W, H = P.R.out.width, P.R.out.height  # noqa: N806
    nx = T3.grid
    ny = max(2, int(round(nx * region.h / region.w)))
    hh = np.zeros((ny, nx), np.float32)
    for j, la in enumerate(np.linspace(lat_n, lat_s, ny)):
        for i, lo in enumerate(np.linspace(lon_w, lon_e, nx)):
            gx, gy = px(lo, la)
            hh[j, i] = M[min(M.shape[0] - 1, max(0, int(gy))), min(M.shape[1] - 1, max(0, int(gx)))]
    hh = np.maximum(hh, 0)
    L = Local(lon_c, lat_c)  # noqa: N806
    sw, ne = L.xz(lon_w, lat_s), L.xz(lon_e, lat_n)
    size_m = [ne[0] - sw[0], sw[1] - ne[1]]
    ctr = L.xz((lon_w + lon_e) / 2, (lat_n + lat_s) / 2)
    (out / "height.json").write_text(json.dumps({"nx": nx, "ny": ny, "h": [round(float(v), 1) for v in hh.ravel()]}), encoding="utf-8")

    def rel(lon: float, lat: float) -> list[float]:
        x, z = L.xz(lon, lat)
        return [round(x - ctr[0], 2), round(z - ctr[1], 2)]

    from engine.terrain3d_prep import camera_at, resolved_units  # noqa: PLC0415

    units = resolved_units(forces, P.R.tb)

    def unit_recs(t: float) -> list[dict]:
        recs = []
        for u in units:
            if u.keys[0].t > t or (u.t_out is not None and t >= u.t_out):
                continue
            k = key_at(u, t)
            shape = WS.shape_of(u.symbol)
            rect = [rel(lo, la) for lo, la in unit_poly(k)]
            col = C[forces.factions[u.faction].token]
            rec: dict[str, Any] = {"shape": shape, "c": rel(k.lon, k.lat), "name": u.name, "color": hexs(col), "faction": u.faction,
                                   "side": hexs(tuple(v * WS.depth.side_dark for v in col)), "glyph_name": WS.glyph_of(u.symbol)}
            if shape in ("dots", "big_dots"):
                r = np.array(rect)
                p0, p1 = (r[0] + r[3]) / 2, (r[1] + r[2]) / 2
                rad = T3.dot_r_m * (2 if shape == "big_dots" else 1)
                m = max(2, int(np.linalg.norm(p1 - p0) / (rad * 3)))
                rec["dots"] = [[round(float(v), 2) for v in p0 + (p1 - p0) * q / m] for q in range(m + 1)]
                rec["dot_r"], rec["poly"] = rad, rect
            else:
                rec["poly"] = shape_poly(shape, rect)
                if shape in WS.rank_grid.shapes:
                    rec["posts"] = rank_posts(rec["poly"], T3.rank.gap_m, T3.rank.max_posts)
            recs.append(rec)
        return recs

    hfov = 2 * math.atan(math.tan(math.radians(T3.camera.fov_deg) / 2) * W / H)
    w_m = v_in.w * L.kx   # mercator 화면 폭(경도°) → 지표 m(중심 위도)
    radius = w_m / (2 * math.tan(hfov / 2))
    db = _places(P.root)
    places = []
    for p in forces.places:
        lon, lat = (db[p.pleiades]["lon"], db[p.pleiades]["lat"]) if p.pleiades else (p.lon, p.lat)
        if lon_w <= lon <= lon_e and lat_s <= lat <= lat_n:
            places.append({"name": p.name, "c": rel(lon, lat), "t": p.t, "t_out": p.t_out})
    frames, prev = [], None
    for i in range(i0, i1):
        t = i / fps
        az, el = camera_at(t, seg)
        fr: dict[str, Any] = {"az": round(az, 4), "elev": round(el, 4), "radius": round(radius, 2), "target": [0.0, 0.0], "t": round(t, 4)}
        us = unit_recs(t)
        if us != prev:
            fr["units"] = us
            prev = us
        frames.append(fr)
    first_units = frames[0].get("units", [])
    scene = {"width": W, "height": H, "size_m": size_m, "center": [0, 0], "exaggeration": T3.exaggeration, "text_in_engine": True,
             "camera": {"fov": T3.camera.fov_deg, "elev_deg": 90.0, "radius_m": radius, "target": [0.0, 0.0]},
             "light": T3.light.model_dump(), "sky": T3.sky, "fog": [radius * T3.fog[0], radius * T3.fog[1]],
             "lift_m": T3.lift_m, "label_lift_m": T3.label_lift_m, "unit_opacity": T3.unit_opacity,
             "unit_height_m": T3.unit_height_m, "shadow_offset_m": T3.shadow_offset_m, "shadow_alpha": WS.depth.shadow_alpha,
             "rank": T3.rank.model_dump(), "glyph_px": T3.glyph_px, "rim_alpha": WS.depth.rim_alpha,
             "river": {"w_m": T3.river_w_m, "color": hexs(load_rules().sketch.war.river.rgb)}, "text": T3.text.model_dump(), "halo": T3.halo,
             "units": first_units, "places": places, "rivers": [{"pts": [rel(lo, la) for lo, la in r.pts]} for r in forces.rivers],
             "frames": frames}
    (out / "scene.json").write_text(json.dumps(scene, ensure_ascii=False), encoding="utf-8")
    return {"i0": i0, "i1": i1, "radius_m": round(radius, 1), "size_m": size_m, "dem": f"Terrarium z{TS.z}",
            "region": [lon_w, lat_s, lon_e, lat_n]}


__all__ = ["build_scene", "Terrain3DError", "Terrain3DStage", "Local", "hexs", "key_at", "rank_posts", "shape_poly", "unit_poly"]
