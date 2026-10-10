"""자산 로더·캐시 (v2.1.0, 19 부록 D `TIERS, BASE, GEO, BORD, ADM, PLC*, surf_from_pil, scaled, PIL_IMG`).

프로젝트 자산 폴더(`assets/`, `media/`)에서 지형 티어·지오메트리·인물·국기·휘장·미디어를 읽는다.
어떤 이미지를 읽을지는 연출(이벤트)이 쓰는 키로 정한다 — 없으면 오류(15 P6).
KO(국가 한글 관용명)·SEAS(해역 라벨)는 프로젝트 `labels.yaml`에서 온다.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import cairo
import numpy as np
import yaml
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field


class SeaLabel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    lon: float
    lat: float
    wmin: float
    wmax: float


class Labels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    ko: dict[str, str] = Field(default_factory=dict)
    seas: list[SeaLabel] = Field(default_factory=list)
    province_countries: list[str] = Field(default_factory=list)
    hide_country_label_below_w: dict[str, float] = Field(default_factory=dict)


class AssetError(RuntimeError):
    pass


def _read_json(p: Path, empty: dict) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else empty


def surf_from_pil(im: Image.Image) -> tuple[cairo.ImageSurface, bytearray]:
    im = im.convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    al = a[..., 3:4] / 255
    rgb = a[..., :3] * al
    bgra = np.ascontiguousarray(np.dstack([rgb[..., 2], rgb[..., 1], rgb[..., 0], a[..., 3]]).astype(np.uint8))
    h, w = bgra.shape[:2]
    buf = bytearray(bgra.tobytes())
    return cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, w * 4), buf


def set_raster(ctx: cairo.Context, surf: cairo.ImageSurface, k: float, x: float, y: float) -> None:
    """장치 해상도 래스터(설계 폭 × k 로 준비한 표면)를 설계 좌표 (x, y) 에 원천으로 건다(v3.6.0 D-0067 요건 3).
    패턴 행렬만 k 배 — 클립·paint 의미는 set_source_surface 와 같다. k=1 이면 set_source_surface 그대로(480p 항등)."""
    if k == 1:
        ctx.set_source_surface(surf, x, y)
        return
    pat = cairo.SurfacePattern(surf)
    pat.set_matrix(cairo.Matrix(xx=k, yy=k, x0=-x * k, y0=-y * k))
    ctx.set_source(pat)


class Assets:
    def __init__(self, root: Path, labels: Labels, res: str | None = None, geo: bool = True, theme: str | None = None) -> None:
        """res = 기본이 아닌 출력 프로파일 이름(v3.6.0 D-0066 작업 3) — 지형 티어를 assets/res_<이름>/(ppd × k)에서 읽는다.
        없으면 오류: 480p 티어를 늘려 쓰지 않는다(업스케일 흐림 금지, D-0067 요건 3). 티어 경계(도)는 두 벌이 같아야 한다.
        geo = 지도 무대를 쓰는가(v4.3.0) — False 면 지형 티어·지오메트리를 읽지 않는다(시간축만 쓰는 영상, geo.prep 불필요).
        theme = 지도 테마(v5.13.0 D-0153 Q0-2, direction stage_config.mercator.theme) — 기본이 아니면 assets/theme_<이름>/ 의 티어.
        없으면 오류(기본 테마 티어로 대신 그리지 않는다, 15 P6). geo.pkl 은 assets/ 한 벌."""
        self.root = root
        self.labels = labels
        self.res = res
        self.theme = theme
        a = root / "assets"
        self.tiers: dict = {}
        self.base: dict = {}
        self.geo: dict = {}
        if geo:
            self._load_geo(a)
        self._load_registries(a)

    def _load_geo(self, a: Path) -> None:
        from geo.prep import theme_root  # noqa: PLC0415

        root, res, theme = self.root, self.res, self.theme
        tr = theme_root(a, theme)
        td = tr if res is None else tr / f"res_{res}"
        if not (td / "tiers.pkl").exists():
            opt = "".join(f" --{k} {v}" for k, v in (("res", res), ("theme", theme)) if v is not None)
            raise AssetError(f"지형 티어 없음: {td / 'tiers.pkl'} — `python -m geo.prep {root}{opt}` 먼저")
        self.tiers = pickle.load(open(td / "tiers.pkl", "rb"))
        if td != a:
            base = pickle.load(open(a / "tiers.pkl", "rb"))
            key = ("lon0", "lon1", "lat0", "lat1")
            if {n: [T[k] for k in key] for n, T in base.items()} != {n: [T[k] for k in key] for n, T in self.tiers.items()}:
                raise AssetError(f"{td} 티어 경계가 assets/tiers.pkl 과 다르다 — geo.yaml 이 바뀐 뒤 geo.prep(--res·--theme)를 다시 돌린다")
        self.base = {(n, lv): Image.open(td / f"base_{n}_{lv}.png").convert("RGB")
                     for n, T in self.tiers.items() for lv in T["levels"]}
        self.geo = pickle.load(open(a / "geo.pkl", "rb"))
        plc = self.geo["places"]   # 국경·행정구역 고리와 도시 기준점의 월드 좌표는 무대가 만든다(engine.stage.MercatorStage, v4.1.0 D-0076)
        self.plc = plc
        self.plc_rank = np.array([p["rank"] for p in plc])
        self.plc_pop = np.array([p["pop"] for p in plc])
        self.plc_cap = np.array([bool(p["cap"]) for p in plc])

    def _load_registries(self, a: Path) -> None:
        # 권리·미디어 레지스트리: 파일이 없으면 빈 레지스트리 — 그 상태에서 인물·휘장·미디어를 쓰면
        # engine.project.preflight 가 렌더 전 오류로 막는다(C9). 조용히 통과시키는 경로가 아니다.
        self.rights = _read_json(a / "rights_registry.json", {"people": {}, "emblems": {}})
        from audio.registry import rights_music  # noqa: PLC0415 — v3.4.0 D-0060 작업 1: 음악 권리 SSOT = BGM 레지스트리
        self.rights["music"] = rights_music()
        from engine.media_registry import load_media_registry  # noqa: PLC0415 — 순환 import 회피

        self.media_assets = load_media_registry()   # v2.5.5 — 저장소 레지스트리(D-0036), 권리·화면 문구의 유일한 출처
        self.media = {k: v.model_dump() for k, v in self.media_assets.items()}
        # 자산 계약 검증(02 §2.5) — 틀리면 렌더 전 오류
        from schemas.engine_models import RightsRegistry, Tier  # noqa: PLC0415 — 순환 import 회피

        for T in self.tiers.values():  # noqa: N806
            Tier.model_validate(T)
        RightsRegistry.model_validate(self.rights)
        from engine.entities import load_emblem_registry  # noqa: PLC0415

        self.emblems = load_emblem_registry()   # D-0029 작업 3 — decision 은 코드가 정한다(D5)
        self.img: dict[str, Image.Image] = {}
        self.clips: dict[str, np.ndarray] = {}
        self._sc: dict[tuple[str, int], tuple[cairo.ImageSurface, bytearray]] = {}
        self._orig: dict[str, tuple[cairo.ImageSurface, bytearray]] = {}

    def emblem_flag(self, eid: str) -> str | None:
        """휘장 결정. `flag_fallback` 이면 대체 국기 코드, `use` 면 None. 미등재 휘장은 오류(15 P10)."""
        if eid not in self.emblems.emblems:
            raise AssetError(f"휘장 레지스트리에 없음: {eid} (assets/emblems/registry.json)")
        ent = self.emblems.emblems[eid]
        return ent.fallback_flag if ent.decision == "flag_fallback" else None

    # --- 이미지 키: portrait:<pid>, emblem:<id>, flag43:<cc>, flag11:<cc>, media:<file>
    def load_image(self, key: str) -> None:
        if key in self.img:
            return
        kind, _, name = key.partition(":")
        paths = {"portrait": f"assets/portraits/{name}.png", "emblem": f"assets/emblems/{name}.png",
                 "flag43": f"assets/flags/{name}_4x3.png", "flag11": f"assets/flags/{name}_1x1.png",
                 "media": f"media/{name}"}
        if kind not in paths:
            raise AssetError(f"알 수 없는 이미지 키 종류: {key}")
        p = self.root / paths[kind]
        if not p.exists():
            raise AssetError(f"자산 없음: {p} (키 {key})")
        self.img[key] = Image.open(p).convert("RGBA")

    def load_clip(self, name: str) -> None:
        if name in self.clips:
            return
        # v4.0.0 D-0074(NB28): 기본이 아닌 프로파일은 media/res_<프로파일>/{name}.npy — 없으면 오류(480p 클립을 늘려 쓰지 않는다, P6)
        p = self.root / "media" / (f"{name}_480.npy" if self.res is None else f"res_{self.res}/{name}.npy")
        if not p.exists():
            fix = "" if self.res is None else f" — `python tools/media_fetch.py {self.root} --res {self.res}` 먼저"
            raise AssetError(f"클립 없음: {p}{fix}")
        self.clips[name] = np.load(p, mmap_mode="r")

    def raster(self, key: str, w: float, k: float) -> tuple[cairo.ImageSurface, float, float]:
        """설계 폭 w 의 이미지를 장치 해상도(w × k)로 → (표면, 설계 폭, 설계 높이). 업스케일 흐림 없이(D-0067 요건 3)."""
        s = self.scaled(key, w * k)
        return s, s.get_width() / k, s.get_height() / k

    def source_width(self, key: str) -> int:
        """원본 이미지 픽셀 폭(업스케일 경고 checks media_upscaled)."""
        self.load_image(key)
        return self.img[key].width

    def original(self, key: str) -> cairo.ImageSurface:
        """원본 해상도 표면 하나(v4.8.0 D-0104 D6) — 켄 번스처럼 크기가 매 프레임 바뀌는 그림은 이 표면을 cairo 변환으로
        연속 배율로 그린다. `scaled` 는 폭을 3px 단위로 양자화해 다시 만들므로 배율이 계단처럼 튄다(R-0119 S8)."""
        if key not in self._orig:
            self.load_image(key)
            self._orig[key] = surf_from_pil(self.img[key])
        return self._orig[key][0]

    def scaled(self, key: str, w: float) -> cairo.ImageSurface:
        wq = max(8, int(round(w / 3.0) * 3))
        k = (key, wq)
        if k not in self._sc:
            self.load_image(key)
            pil = self.img[key]
            self._sc[k] = surf_from_pil(pil.resize((wq, max(1, int(pil.height * wq / pil.width))), Image.LANCZOS))
        return self._sc[k][0]


def load_labels(path: Path) -> Labels:
    return Labels.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
