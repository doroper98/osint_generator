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

from engine.projection import to_uv, ymv


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


class Assets:
    def __init__(self, root: Path, labels: Labels) -> None:
        self.root = root
        self.labels = labels
        a = root / "assets"
        self.tiers = pickle.load(open(a / "tiers.pkl", "rb"))
        self.base = {(n, lv): Image.open(a / f"base_{n}_{lv}.png").convert("RGB")
                     for n, T in self.tiers.items() for lv in T["levels"]}
        self.geo = pickle.load(open(a / "geo.pkl", "rb"))
        # 권리·미디어 레지스트리: 파일이 없으면 빈 레지스트리 — 그 상태에서 인물·휘장·미디어를 쓰면
        # engine.project.preflight 가 렌더 전 오류로 막는다(C9). 조용히 통과시키는 경로가 아니다.
        self.rights = _read_json(a / "rights_registry.json", {"people": {}, "emblems": {}})
        self.bord = {lod: {k: to_uv(v) for k, v in self.geo[lod].items()} for lod in ("coarse", "fine")}
        self.adm = {k: [dict(name=x["name"], lx=x["lx"], ly=x["ly"], rings=to_uv(x["rings"])) for x in v]
                    for k, v in self.geo["admin1"].items()}
        plc = self.geo["places"]
        self.plc = plc
        self.plc_lon = np.array([p["lon"] for p in plc])
        self.plc_v = ymv(np.array([p["lat"] for p in plc]))
        self.plc_rank = np.array([p["rank"] for p in plc])
        self.plc_pop = np.array([p["pop"] for p in plc])
        self.plc_cap = np.array([bool(p["cap"]) for p in plc])
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
        p = self.root / "media" / f"{name}_480.npy"
        if not p.exists():
            raise AssetError(f"클립 없음: {p}")
        self.clips[name] = np.load(p, mmap_mode="r")

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
