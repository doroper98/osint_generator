"""메르카토르 도 단위 투영과 뷰 (v2.1.0, 19 부록 D `ym, ymv, View, to_uv`).

좌표계: u = 경도, v = degrees(ln(tan(π/4 + 위도/2))). 두 축이 모두 '도'라 ppd 하나로 스케일이 정해진다(00 §5).
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

from engine.style import H_OUT, W_OUT
from engine.timebase import smooth


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


class View:
    """한 프레임의 뷰포트. cam = (lon, v, w), w 는 화면 가로가 덮는 경도 폭."""

    def __init__(self, cam: "np.ndarray", tiers: dict, base: dict) -> None:
        lon, v, w = cam
        self.tiers = tiers
        self.base_img = base
        tw_ = tiers["W"]
        umin, umax = tw_["lon0"], tw_["lon1"]
        vmin, vmax = ym(tw_["lat0"]), ym(tw_["lat1"])
        w = min(w, umax - umin - 0.01, (vmax - vmin - 0.01) * W_OUT / H_OUT)
        self.w = w
        self.h = w * H_OUT / W_OUT
        self.s = W_OUT / w
        self.u0 = min(max(lon - w / 2, umin), umax - w)
        self.v1 = min(max(v + self.h / 2, vmin + self.h), vmax)

    def xy(self, lon: float, lat: float) -> tuple[float, float]:
        return (lon - self.u0) * self.s, (self.v1 - ym(lat)) * self.s

    def uvs(self, uv: "np.ndarray") -> "np.ndarray":
        return np.column_stack([(uv[:, 0] - self.u0) * self.s, (self.v1 - uv[:, 1]) * self.s])

    def visible(self, mn: "np.ndarray", mx: "np.ndarray") -> bool:
        return not (mx[0] < self.u0 or mn[0] > self.u0 + self.w or mx[1] < self.v1 - self.h or mn[1] > self.v1)

    def inside(self, T: dict, m: float = 0.05) -> bool:  # noqa: N803
        return (self.u0 >= T["lon0"] + m and self.u0 + self.w <= T["lon1"] - m
                and self.v1 <= ym(T["lat1"]) - m and self.v1 - self.h >= ym(T["lat0"]) + m)

    def base(self) -> Image.Image:
        need = W_OUT / self.w
        im = self._tier("W", need)
        for n in ("G", "K"):
            if self.inside(self.tiers[n]):
                a = smooth((need - 26) / 18)
                if a > 0.01:
                    im = Image.blend(im, self._tier(n, need), a)
        return im

    def _tier(self, n: str, need: float) -> Image.Image:
        T = self.tiers[n]  # noqa: N806
        lvs = sorted(T["levels"])
        lv = next((lv_ for lv_ in lvs if lv_ >= need * 0.95), lvs[-1])
        im = self.base_img[(n, lv)]
        x0 = (self.u0 - T["lon0"]) * lv
        y0 = (ym(T["lat1"]) - self.v1) * lv
        return im.resize((W_OUT, H_OUT), Image.BILINEAR,
                         box=(max(0.0, x0), max(0.0, y0), min(x0 + self.w * lv, im.width), min(y0 + self.h * lv, im.height)))
