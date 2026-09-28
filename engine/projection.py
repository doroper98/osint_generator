"""메르카토르 도 단위 투영과 뷰 (v2.1.0, 19 부록 D `ym, ymv, View, to_uv`).

좌표계: u = 경도, v = degrees(ln(tan(π/4 + 위도/2))). 두 축이 모두 '도'라 ppd 하나로 스케일이 정해진다(00 §5).
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

from engine.style import H_OUT, W_OUT, Output
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
        if "W" not in tiers:
            raise KeyError("티어 W(광역, 카메라 경계)가 없다 — geo.yaml tiers 에 name: W 를 둔다")
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

    def base(self, out: "Output | None" = None) -> Image.Image:
        """지형 베이스 — 장치 해상도(out, None = 설계 854×480). 티어 레벨은 장치 ppd 로 고르고, 상세 티어 블렌딩은
        설계 ppd 로 계산한다(해상도가 달라도 같은 순간에 같은 비율로 섞인다, v3.6.0 D-0067)."""
        need = W_OUT / self.w
        dev = out is not None and out.k != 1
        need_dev = need * out.k if dev else need
        im = self._tier("W", need_dev, out if dev else None)
        for n in self.tiers:  # 상세 티어: W 를 뺀 전부, 정의 순서대로(v3 는 G→K). 블렌딩 규칙은 v3 그대로
            if n == "W":
                continue
            if self.inside(self.tiers[n]):
                a = smooth((need - 26) / 18)
                if a > 0.01:
                    im = Image.blend(im, self._tier(n, need_dev, out if dev else None), a)
        return im

    def _tier(self, n: str, need: float, out: "Output | None" = None) -> Image.Image:
        T = self.tiers[n]  # noqa: N806
        lvs = sorted(T["levels"])
        lv = next((lv_ for lv_ in lvs if lv_ >= need * 0.95), lvs[-1])
        im = self.base_img[(n, lv)]
        x0 = (self.u0 - T["lon0"]) * lv
        y0 = (ym(T["lat1"]) - self.v1) * lv
        if out is None:
            return im.resize((W_OUT, H_OUT), Image.BILINEAR,
                             box=(max(0.0, x0), max(0.0, y0), min(x0 + self.w * lv, im.width), min(y0 + self.h * lv, im.height)))
        # 장치 화소 X ↔ 설계 x = (X − pad_x) / k ↔ 경도 u0 + x / s. 양옆 pad_x(1080p −0.75px)만큼 설계 화면보다 넓거나 좁다
        dx = -out.pad_x / out.k / self.s * lv
        wd = out.width / out.k / self.s * lv
        return im.resize((out.width, out.height), Image.BILINEAR,
                         box=(max(0.0, x0 + dx), max(0.0, y0), min(x0 + dx + wd, im.width), min(y0 + self.h * lv, im.height)))
