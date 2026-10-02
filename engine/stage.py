"""무대(Stage) — 월드 좌표계·배경·라벨 LOD (v4.1.0, docs/handoff/20 §2.3, back_and_forth D-0076 작업 1·2).

카메라와 `engine.projection.View` 는 무대와 무관한 월드 좌표 (x, y, w)만 안다. w = 화면 가로가 덮는 월드 폭.
연출의 앵커 좌표(지도 = 경위도)는 `stage.to_world(**anchor)` 로만 월드 좌표가 된다(D-0076 작업 3).
투영 수식(Mercator `ym`·`ymv`·`lat_of`·`to_uv`)은 **이 파일에만** 있다(tests/anti_inertia/test_stage_isolation).

무대 목록 = `rules registries.stages`. 목록에 없는 이름 = 오류, 목록에 있는데 구현이 없음 = 오류(15 P10).

`MercatorStage` 는 v3 지도 코드를 감싼 것이다 — 수식·연산 순서·그리는 순서 무변경(20 §2.3 "리팩터 후에도 v3 골든 프레임 동일").
- 월드 좌표: x = 경도, y = degrees(ln(tan(π/4 + 위도/2))). 두 축이 모두 '도'라 ppd 하나로 스케일이 정해진다(00 §5).
- 경계(bounds) = 티어 W(광역) 사각형 — 카메라 클램프.
- render_base = 지형 티어 래스터(장치 해상도) + 국경·행정구역 선, draw_labels = 해역·국가·도·도시 라벨 LOD(04 §6·§7).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

import cairo
import numpy as np
from PIL import Image

from engine.style import H_OUT, W_OUT, Output
from engine.timebase import smooth

if TYPE_CHECKING:
    from engine.assets import Assets
    from engine.projection import View

Bounds = tuple[float, float, float, float]


class StageError(ValueError):
    """무대 레지스트리·구성 오류(15 P6·P10 — 조용히 넘기지 않는다)."""


@runtime_checkable
class Stage(Protocol):
    """무대 프로토콜(20 §2.3). `from_world` 는 월드 → 앵커 역변환 — 카메라 제안이 연출(앵커)에 되돌려 줄 값을 만든다."""

    name: str
    bounds: Bounds                                            # 월드 좌표 x0, y0, x1, y1 — 카메라 클램프

    def to_world(self, **anchor: float) -> tuple[float, float]: ...
    def from_world(self, x: float, y: float) -> dict[str, float]: ...
    def render_base(self, ctx: cairo.Context, view: "View") -> None: ...
    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> None: ...
    def lod_rules(self) -> dict[str, Any]: ...


# ------------------------------------------------------------------ Mercator 수식(v2.1.0 projection.py 에서 이동, 19 부록 D)
def ym(lat: float) -> float:
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def ymv(lat: "np.ndarray") -> "np.ndarray":
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.clip(lat, -85, 85)) / 2)))


def lat_of(v: float) -> float:
    """ym 의 역함수."""
    return math.degrees(2 * math.atan(math.exp(math.radians(v))) - math.pi / 2)


def to_uv(rings: list) -> list:
    out = []
    for r in rings:
        uv = np.stack([r[:, 0], ymv(r[:, 1])], 1).astype(np.float64)
        out.append((uv, uv.min(0), uv.max(0)))
    return out


# 월드 폭 w 별 표시 규칙(v3 값 그대로 — 04 §6·§7). (w 초과 문턱, 값) 을 위에서부터 보고 처음 맞는 값, 없으면 마지막 값.
MERCATOR_LOD: dict[str, Any] = {
    "country_rank_max": ([(60, 2), (30, 4), (12, 6)], 9),          # 국가 라벨 rank 상한
    "city_rank_max": ([(60, 1), (25, 2), (12, 4), (5, 6)], 8),     # 도시 라벨 rank 상한(수도는 +2)
    "admin_names_below_w": 8.5,                                     # 도(道) 이름
    "borders_fine_below_w": 22,                                     # 국경 fine LOD
    "border_alpha": {"below_w": 40, "near": 0.36, "far": 0.26},
    "admin_lines_fade": {"w": 24, "span": 10, "alpha": 0.3},        # 행정구역 선 0.3·smooth((24 − w)/10)
    "tier_blend_ppd": {"from": 26, "span": 18},                     # 상세 티어 블렌딩 smooth((W_OUT/w − 26)/18)
    "tier_inside_margin": 0.05,                                     # 상세 티어는 화면이 티어 안(여백 0.05도)일 때만
    "city_labels_max": 18,
    "sea_labels": "labels.yaml seas[].wmin ≤ w ≤ wmax",
}


def by_w(w: float, rule: tuple[list[tuple[float, float]], float]) -> float:
    """`MERCATOR_LOD` 계단 규칙 — `a if w > t1 else b if w > t2 else … else last` 와 같다."""
    steps, last = rule
    for th, v in steps:
        if w > th:
            return v
    return last


class MercatorStage:
    """지도 무대(20 §2.1 `MercatorStage`). 앵커 = (lon, lat). assets 없이 만들면 좌표 변환만(tiers 가 있으면 경계까지) 쓴다."""

    name = "mercator"
    anchor_keys = ("lon", "lat")

    def __init__(self, assets: "Optional[Assets]" = None, *, tiers: Optional[dict] = None, out: Optional[Output] = None,
                 config: Optional[dict] = None) -> None:
        if config:
            raise StageError(f"mercator 무대에는 stage_config 가 없다: {sorted(config)}")
        self.assets = assets
        self.tiers = tiers if tiers is not None else (assets.tiers if assets is not None else None)
        self.out = out
        self._bounds: Optional[Bounds] = None
        if self.tiers is not None:
            if "W" not in self.tiers:
                raise KeyError("티어 W(광역, 카메라 경계)가 없다 — geo.yaml tiers 에 name: W 를 둔다")
            tw_ = self.tiers["W"]
            self._bounds = (tw_["lon0"], ym(tw_["lat0"]), tw_["lon1"], ym(tw_["lat1"]))
        self._sea_cache: dict[str, list] = {}
        if assets is not None:
            geo = assets.geo
            self.bord = {lod: {k: to_uv(v) for k, v in geo[lod].items()} for lod in ("coarse", "fine")}
            self.adm = {k: [dict(name=x["name"], xy=None if x["lx"] is None else self.to_world(lon=x["lx"], lat=x["ly"]),
                                 rings=to_uv(x["rings"])) for x in v]
                        for k, v in geo["admin1"].items()}
            self.countries = [(k, m, None if m["lx"] is None else self.to_world(lon=m["lx"], lat=m["ly"])) for k, m in geo["meta"].items()]
            self.seas = [(s, self.to_world(lon=s.lon, lat=s.lat)) for s in assets.labels.seas]
            plc = geo["places"]
            self.plc_x = np.array([p["lon"] for p in plc])
            self.plc_y = ymv(np.array([p["lat"] for p in plc]))

    # --- 좌표
    @property
    def bounds(self) -> Bounds:
        if self._bounds is None:
            raise StageError("MercatorStage: 티어가 없어 경계(bounds)를 모른다 — assets 또는 tiers 로 만든다")
        return self._bounds

    def to_world(self, **anchor: float) -> tuple[float, float]:
        if set(anchor) != {"lon", "lat"}:
            raise StageError(f"mercator 앵커는 lon·lat: {sorted(anchor)}")
        return anchor["lon"], ym(anchor["lat"])

    def from_world(self, x: float, y: float) -> dict[str, float]:
        return {"lon": x, "lat": lat_of(y)}

    def world_box(self, lon0: float, lat0: float, lon1: float, lat1: float) -> Bounds:
        """경위도 사각형 → 월드 사각형(카메라 제안의 경계 인자 등)."""
        return (lon0, ym(lat0), lon1, ym(lat1))

    # --- 배경
    def render_base(self, ctx: cairo.Context, view: "View") -> None:
        """지형 티어 래스터를 프레임 표면에 그대로 복사(장치 해상도, 변환 무시)하고 국경·행정구역 선을 그린다."""
        from engine.layers.borders import draw_borders  # noqa: PLC0415 — layers → stage 순환 회피

        im = self.base_image(view, self.out)
        surf = ctx.get_target()
        surf.flush()
        surf.get_data()[:] = im.tobytes("raw", "BGRX")
        surf.mark_dirty()
        draw_borders(ctx, self, view)

    def _inside(self, view: "View", T: dict, m: float = MERCATOR_LOD["tier_inside_margin"]) -> bool:  # noqa: N803
        return (view.x0 >= T["lon0"] + m and view.x0 + view.w <= T["lon1"] - m
                and view.y1 <= ym(T["lat1"]) - m and view.y1 - view.h >= ym(T["lat0"]) + m)

    def base_image(self, view: "View", out: Optional[Output] = None) -> Image.Image:
        """지형 베이스 — 장치 해상도(out, None = 설계 854×480). 티어 레벨은 장치 ppd 로 고르고, 상세 티어 블렌딩은
        설계 ppd 로 계산한다(해상도가 달라도 같은 순간에 같은 비율로 섞인다, v3.6.0 D-0067)."""
        tb = MERCATOR_LOD["tier_blend_ppd"]
        need = W_OUT / view.w
        dev = out is not None and out.k != 1
        need_dev = need * out.k if dev else need
        im = self._tier(view, "W", need_dev, out if dev else None)
        for n in self.tiers:  # 상세 티어: W 를 뺀 전부, 정의 순서대로(v3 는 G→K). 블렌딩 규칙은 v3 그대로
            if n == "W":
                continue
            if self._inside(view, self.tiers[n]):
                a = smooth((need - tb["from"]) / tb["span"])
                if a > 0.01:
                    im = Image.blend(im, self._tier(view, n, need_dev, out if dev else None), a)
        return im

    def _tier(self, view: "View", n: str, need: float, out: Optional[Output] = None) -> Image.Image:
        T = self.tiers[n]  # noqa: N806
        lvs = sorted(T["levels"])
        lv = next((lv_ for lv_ in lvs if lv_ >= need * 0.95), lvs[-1])
        im = self.assets.base[(n, lv)]
        x0 = (view.x0 - T["lon0"]) * lv
        y0 = (ym(T["lat1"]) - view.y1) * lv
        if out is None:
            return im.resize((W_OUT, H_OUT), Image.BILINEAR,
                             box=(max(0.0, x0), max(0.0, y0), min(x0 + view.w * lv, im.width), min(y0 + view.h * lv, im.height)))
        # 장치 화소 X ↔ 설계 x = (X − pad_x) / k ↔ 경도 x0 + x / s. 양옆 pad_x(1080p −0.75px)만큼 설계 화면보다 넓거나 좁다
        dx = -out.pad_x / out.k / view.s * lv
        wd = out.width / out.k / view.s * lv
        return im.resize((out.width, out.height), Image.BILINEAR,
                         box=(max(0.0, x0 + dx), max(0.0, y0), min(x0 + dx + wd, im.width), min(y0 + view.h * lv, im.height)))

    # --- 라벨·LOD
    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> list:
        from engine.layers.labels import draw_labels  # noqa: PLC0415

        return draw_labels(ctx, self, view, reserved, alpha)

    def lod_rules(self) -> dict[str, Any]:
        return dict(MERCATOR_LOD)

    # --- 지도 전용 보조
    def sea_points(self, box: tuple[float, float, float, float], n: int, seed: int) -> list[tuple[float, float, float]]:
        """육지를 피한 무작위 선박 위치(v3: rng 4, 150점, 페르시아만 상자) → [(x, y, 위상)] 월드 좌표. 무대에 한 번만 만든다."""
        key = f"ships:{box}:{n}:{seed}"
        if key not in self._sea_cache:
            from shapely.geometry import Point, Polygon  # noqa: PLC0415
            from shapely.prepared import prep  # noqa: PLC0415

            land = [prep(Polygon(r)) for k, rs in self.assets.geo["fine"].items() for r in rs if len(r) > 3]
            rng = np.random.default_rng(seed)
            pts = []
            while len(pts) < n:
                lo, la = rng.uniform(box[0], box[1]), rng.uniform(box[2], box[3])
                p = Point(lo, la)
                if not any(L.contains(p) for L in land):
                    pts.append((lo, la, rng.uniform(0, 1)))
            self._sea_cache[key] = [(*self.to_world(lon=lo, lat=la), ph) for lo, la, ph in pts]
        return self._sea_cache[key]


class FlatMercatorStage(MercatorStage):
    """지도 무대의 **막지도 모드**(v4.9.0 back_and_forth D-0108, 콘티 판). 좌표·경계·카메라 클램프는 MercatorStage 그대로,
    배경은 육지·바다 단색 + 국경선(`engine.layers.animatic.draw_flat_map`), 라벨 없음. 자산(티어 래스터·geo.pkl)을 읽지 않는다 —
    경계 = 프로젝트 geo.yaml 티어 W bbox(geo.prep 의 tier_record 와 같은 값), 지오메트리 = 저장소 막지도 자료(R-0135 A).
    `bord` 는 coarse·fine 이 같은 110m 고리다(country 강조·국경선이 같은 자료)."""

    def __init__(self, tier_w: dict, polygons: dict[str, list], out: Optional[Output] = None) -> None:
        super().__init__(None, tiers={"W": tier_w}, out=out)
        rings = {k: to_uv([np.asarray(r, np.float64) for poly in v for r in poly]) for k, v in polygons.items()}
        self.bord = {"coarse": rings, "fine": rings}
        self.adm: dict = {}
        self.countries: list = []
        self.seas: list = []
        self.polygons = polygons
        self.land_uv = [(uv, mn, mx) for k, v in polygons.items() for uv, mn, mx in to_uv([np.asarray(p[0], np.float64) for p in v])]

    def render_base(self, ctx: cairo.Context, view: "View") -> None:
        from engine.layers.animatic import draw_flat_map  # noqa: PLC0415 — layers → stage 순환 회피

        draw_flat_map(ctx, self, view)

    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> None:
        """막지도에는 라벨이 없다(D-0108 — 타일·지형·라벨 없음)."""

    def sea_points(self, box: tuple[float, float, float, float], n: int, seed: int) -> list[tuple[float, float, float]]:
        """선박 점 — MercatorStage 와 같은 난수 절차, 육지 판정만 막지도 폴리곤으로."""
        key = f"ships:{box}:{n}:{seed}"
        if key not in self._sea_cache:
            from shapely.geometry import Point, Polygon  # noqa: PLC0415
            from shapely.prepared import prep  # noqa: PLC0415

            land = [prep(Polygon(p[0])) for v in self.polygons.values() for p in v if len(p[0]) > 3]
            rng = np.random.default_rng(seed)
            pts = []
            while len(pts) < n:
                lo, la = rng.uniform(box[0], box[1]), rng.uniform(box[2], box[3])
                pt = Point(lo, la)
                if not any(L.contains(pt) for L in land):
                    pts.append((lo, la, rng.uniform(0, 1)))
            self._sea_cache[key] = [(*self.to_world(lon=lo, lat=la), ph) for lo, la, ph in pts]
        return self._sea_cache[key]


from engine.stage_backdrop import BackdropStage  # noqa: E402 — 사진 배경 무대(v5.1.0 D-0123)
from engine.stage_timeline import TimelineStage  # noqa: E402 — 시간축 무대(v4.3.0 D-0084 작업 3)

STAGE_CLASSES: dict[str, type] = {"mercator": MercatorStage, "timeline": TimelineStage,   # 구현 — rules registries.stages 와 같아야 한다(P10)
                                  "backdrop": BackdropStage}
# direction.yaml 에 stage 가 없을 때의 무대 = 장르 프로필 stage.primary(v4.2.0 D-0081 작업 3, 기본 장르 geopolitics → mercator).


def stage_class(name: str) -> type:
    from rules import load_rules  # noqa: PLC0415

    reg = list(load_rules().registries.stages)
    if name not in reg:
        raise StageError(f"미등록 무대 {name!r} — rules registries.stages: {reg}")
    if name not in STAGE_CLASSES:
        raise StageError(f"무대 {name!r} 는 레지스트리에 있는데 구현이 없다 — engine.stage.STAGE_CLASSES: {sorted(STAGE_CLASSES)}")
    return STAGE_CLASSES[name]


def make_stage(name: str, assets: "Optional[Assets]" = None, out: Optional[Output] = None, config: Optional[dict] = None) -> Stage:
    """config = 무대 설정(direction stage_config.<이름> + 장르 프로필 기본값, Direction.stage_settings). 지도는 없음."""
    return stage_class(name)(assets, out=out, config=config)


class StageSet:
    """영상 하나의 무대 인스턴스 — 이름마다 **한 번만** 만든다(D-0077 쟁점 3 B: 장면마다 새 캔버스 금지의 구조 쪽).
    `created` = 이름별 생성 수(provenance stage.instances). 같은 이름을 다시 부르면 같은 객체를 돌려준다."""

    def __init__(self, assets: "Optional[Assets]" = None, out: Optional[Output] = None,
                 configs: Optional[dict[str, dict]] = None, modes: Optional[dict[str, Any]] = None) -> None:
        """modes = 무대 이름 → 대체 생성 함수(config) → Stage. 콘티 판의 막지도(v4.9.0 D-0108) 한 곳만 쓴다 — 이름은 레지스트리 검사를 그대로 거친다."""
        self.assets = assets
        self.out = out
        self.configs = configs or {}
        self.modes = modes or {}
        self._by_name: dict[str, Stage] = {}
        self.created: dict[str, int] = {}

    def get(self, name: str) -> Stage:
        if name not in self._by_name:
            if name in self.modes:
                stage_class(name)   # 레지스트리 검사(P10)
                self._by_name[name] = self.modes[name](self.configs.get(name))
            else:
                self._by_name[name] = make_stage(name, self.assets, self.out, self.configs.get(name))
            self.created[name] = self.created.get(name, 0) + 1
        return self._by_name[name]


def attach_world(events: list[dict], stage: Stage, chart_stage: Optional[Stage] = None) -> None:
    """이벤트의 앵커 좌표 → 월드 좌표(제자리). 레이어·검사기는 이 값과 View 만 쓴다(D-0076 작업 3).
    world = 한 점(lon·lat 또는 시간축 date·lane — v4.3.0, 앵커 키는 무대가 검사: 다른 무대의 키 = StageError, P10),
    world_pts = 경로(pts), world_p0·world_p1 = 봉쇄선 양 끝."""
    for e in events:
        if e.get("lon") is not None and e.get("lat") is not None:
            e["world"] = stage.to_world(lon=e["lon"], lat=e["lat"])
        elif e.get("date") is not None and e.get("lane") is not None:   # chart_stage = 차트 아일랜드 시간축(v5.1.0 D-0126 Q1 A)
            e["world"] = (chart_stage or stage).to_world(date=e["date"], lane=e["lane"])
        if e["type"] in ("route", "tanker_loop") and e.get("pts"):
            e["world_pts"] = [stage.to_world(lon=lo, lat=la) for lo, la in e["pts"]]
        if e["type"] == "barrier":
            e["world_p0"] = stage.to_world(lon=e["p0"][0], lat=e["p0"][1])
            e["world_p1"] = stage.to_world(lon=e["p1"][0], lat=e["p1"][1])


__all__ = ["MERCATOR_LOD", "FlatMercatorStage", "MercatorStage", "STAGE_CLASSES", "Stage", "StageError", "StageSet", "attach_world", "by_w",
           "lat_of", "make_stage", "stage_class", "to_uv", "ym", "ymv"]
