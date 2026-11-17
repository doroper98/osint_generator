"""스튜디오 무대(StudioStage) — 지도가 필요 없는 장면의 밝은 회색 사진 스튜디오 (v7.4.0, 사용자 의견 UF-902·UF-903, 결정 D910).

바닥이 사분원 모서리로 벽에 이어지는 호리존트(모서리 선 없음) 위에 점 격자가 놓이고, 벽의 빛 웅덩이와 모서리 앞 바닥 반사광이
'끝없는 공간'이 아니라 '스튜디오 안'임을 보인다(UF-903). 조명은 **배경에만** 더한다 — 내용물 위에 덮는 가장자리 어둡게(비네팅)는
없다(C0 금지 목록). 모양은 하나: 어두운 판·테마·stage_config 없음(UF-903 "스튜디오 씬은 그거로만").

공간(가상 카메라)은 영상 전역 시각 t 의 느린 사인 합으로 늘 조금씩 흐른다(v7.4.0 사용자 지시 2026-11-17 "스튜디오 공간이 계속 조금씩 이동을
하는 느낌을 줘서 … 지루함을 느끼지 않도록"). 같은 t = 같은 바이트(무작위 없음), 다른 무대에 다녀와도 흐름이 이어진다. 점 격자·조명은 공간에
붙어 있어 시차대로 움직인다(가까운 바닥 점이 벽 점보다 많이). 시각은 렌더 진입이 `View.t` 로 준다 — 없으면 오류(P6, 조용히 t=0 으로 그리지 않는다).

내용물 계약은 backdrop 무대와 같다: 월드 좌표 = 화면 설계 px(854×480), 앵커 없음(카메라 `{}`), `fixed_w` = 화면 폭. 아일랜드·카드·패널·인용·
자막은 같은 화면 자리 그대로(흐르는 것은 뒤의 공간뿐). 사진 배경(`backdrop` 이벤트)은 받지 않는다(engine.project 가 오류로 막는다).

그리기: 배경 밝기(호 길이 s 의 함수 + 면 좌표 조명)를 설계 px 격자(rules bg_grid_px)로 계산해 이중선형으로 펼치고, 점은 cairo 로 부화소 위치에
그린다. 모든 길이는 m(공간)·설계 px(화면) — 장치 해상도는 렌더 진입의 변환 한 곳(D-0067)이 맡아 480p~2160p 가 같은 그림이다.
수치는 전부 `rules stage_studio`(코드 리터럴 0 — tests/anti_inertia/test_no_magic_numbers).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional

import cairo
import numpy as np

from engine.style import H_OUT, STUDIO, W_OUT

if TYPE_CHECKING:
    from engine.assets import Assets
    from engine.projection import View
    from schemas.rules_models import StudioLight


class StudioError(ValueError):
    """스튜디오 무대 구성·앵커·시각 오류(15 P6)."""


def surface_yz(s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """호 길이 s(바닥 → 모서리 → 벽, m) → 면 위 점의 (높이 y, 깊이 z). 가로(x)로는 같은 단면이 이어진다."""
    z0, r = STUDIO.fillet_z_m, STUDIO.fillet_radius_m
    q = r * math.pi / 2                                      # 사분원 호 길이
    a = np.clip((s - z0) / r, 0, math.pi / 2)
    y = np.where(s <= z0, 0.0, np.where(s <= z0 + q, r * (1 - np.cos(a)), r + (s - z0 - q)))
    z = np.where(s <= z0, s, np.where(s <= z0 + q, z0 + r * np.sin(a), z0 + r))
    return y, z


def tone_of(s: np.ndarray) -> np.ndarray:
    """조명 전 바탕 밝기(0~1) — 바닥 카메라 쪽 → 모서리 쪽 오름, 모서리 살짝 가라앉음, 벽 위로 내려감(rules stage_studio.tone)."""
    tn, z0 = STUDIO.tone, STUDIO.fillet_z_m
    s_near = STUDIO.arc_range_m[0]
    q = STUDIO.fillet_radius_m * math.pi / 2
    u_floor = np.clip((s - s_near) / (z0 - s_near), 0, 1)
    floor = tn.floor_near + (tn.floor_fillet - tn.floor_near) * u_floor ** tn.floor_gamma
    u_fil = np.clip((s - z0) / q, 0, 1)
    fillet = tn.floor_fillet - tn.fillet_dip * np.sin(u_fil * math.pi / 2)
    u_wall = np.clip((s - z0 - q) / tn.wall_span_m, 0, 1)
    wall = tn.floor_fillet - tn.fillet_dip - tn.wall_top_drop * u_wall
    return np.where(s <= z0, floor, np.where(s <= z0 + q, fillet, wall))


def light_arc(L: "StudioLight") -> float:  # noqa: N803
    """조명 가운데의 호 길이 — 벽 높이(height_m) 또는 바닥 z(z_m)."""
    if L.z_m is not None:
        return float(L.z_m)
    assert L.height_m is not None
    r = STUDIO.fillet_radius_m
    return STUDIO.fillet_z_m + r * math.pi / 2 + (L.height_m - r)


def drift_at(t: float) -> tuple[float, float, float]:
    """영상 전역 시각 t(초)의 카메라 위치 (x, y, z) m — 기준 위치 + 주기가 서로 맞지 않는 느린 사인 셋(옆·위아래·앞뒤). 좌우 회전·기울기 없음."""
    d, c = STUDIO.drift, STUDIO.camera

    def wave(amp: float, period: float, phase_deg: float) -> float:
        return amp * math.sin(math.tau * t / period + math.radians(phase_deg))

    return (wave(d.truck_m, d.truck_period_sec, d.truck_phase_deg),
            c.height_m + wave(d.rise_m, d.rise_period_sec, d.rise_phase_deg),
            c.z_m + wave(d.dolly_m, d.dolly_period_sec, d.dolly_phase_deg))


class StudioStage:
    """스튜디오 무대(UF-902·UF-903). 앵커 = 없음, 카메라 = 빈 카메라 {}(내용물은 움직이지 않는다 — 흐르는 것은 배경 공간뿐)."""

    name = "studio"
    anchor_keys: tuple[str, ...] = ()
    fixed_w: float = float(W_OUT)
    screen_space = True          # 화면 공간 무대(아일랜드·카드가 화면 설계 px 에 놓인다) — engine.stage.screen_stage
    photo_backdrop = False       # 사진 배경(backdrop 이벤트)을 받지 않는다 — engine.stage.photo_stage

    def __init__(self, assets: "Optional[Assets]" = None, *, out: object = None, config: Optional[dict] = None) -> None:
        if config:
            raise StudioError(f"studio 무대에는 stage_config 가 없다(모양은 하나 — 수치는 rules stage_studio, UF-903): {sorted(config)}")
        self.assets = assets
        lo, hi = STUDIO.arc_range_m
        self._ss = np.linspace(lo, hi, STUDIO.arc_samples)            # 화면 줄 ↔ 호 길이 대응표 표본
        self._ys, self._zs = surface_yz(self._ss)
        self._tone = tone_of(self._ss)
        step = STUDIO.dots.step_m
        js = np.arange(math.ceil(lo / step), math.floor(hi / step) + 1)
        self._dot_y, self._dot_z = surface_yz(js * step)              # 점 줄(같은 호 길이) — 화면 가로줄
        self._dot_x = np.arange(-STUDIO.dots.cols, STUDIO.dots.cols + 1) * step
        g = STUDIO.bg_grid_px
        self._nx, self._ny = math.ceil(W_OUT / g) + 1, math.ceil(H_OUT / g) + 1
        self._gu = (np.arange(self._nx) + 1 / 2) * g                   # 격자 칸 가운데(설계 px)
        self._gv = (np.arange(self._ny) + 1 / 2) * g
        self._pool = (STUDIO.light_pool, light_arc(STUDIO.light_pool))
        self._bounce = (STUDIO.floor_bounce, light_arc(STUDIO.floor_bounce))

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (0.0, 0.0, float(W_OUT) + 1.0, float(H_OUT) + 1.0)

    def to_world(self, **anchor: Any) -> tuple[float, float]:
        if anchor:
            raise StudioError(f"studio 무대 카메라는 빈 카메라 {{}} — 앵커 {sorted(anchor)} 금지(내용물은 화면 자리 그대로)")
        return W_OUT / 2, H_OUT / 2

    def from_world(self, x: float, y: float) -> dict[str, Any]:
        return {}

    # --- 투영(설계 px)
    def _cam_space(self, cam: tuple[float, float, float], y: np.ndarray, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """면 점 (y, z) → 카메라 공간 (세로 Y2, 깊이 Z2). 가로 x 는 깊이에 영향이 없다(좌우 회전 없음 — 같은 호 길이 = 같은 깊이)."""
        p = math.radians(STUDIO.camera.pitch_deg)
        Y, Z = y - cam[1], z - cam[2]  # noqa: N806
        return Y * math.cos(p) + Z * math.sin(p), -Y * math.sin(p) + Z * math.cos(p)

    @staticmethod
    def _f_px() -> float:
        return STUDIO.camera.focal * W_OUT / 2

    def background(self, t: float) -> np.ndarray:
        """시각 t 의 배경 밝기 격자(ny × nx × RGB, 0~1) — 조명 더하기 전 바탕 + 벽 빛 웅덩이 + 바닥 반사광. 결정적(같은 t = 같은 값)."""
        cam = drift_at(t)
        f = self._f_px()
        y2, z2 = self._cam_space(cam, self._ys, self._zs)
        ok = z2 > 0
        py = H_OUT / 2 - f * y2[ok] / z2[ok]                           # 호 길이가 커질수록 위로(작아진다)
        s_row = np.interp(self._gv, py[::-1], self._ss[ok][::-1])
        z_row = np.interp(self._gv, py[::-1], z2[ok][::-1])
        lum = np.repeat(np.interp(s_row, self._ss, self._tone)[:, None], self._nx, axis=1)
        x = cam[0] + (self._gu[None, :] - W_OUT / 2) / f * z_row[:, None]   # 그 화소가 닿은 면 위 가로 위치(m)
        for L, sc in (self._pool, self._bounce):  # noqa: N806
            ds = ((s_row - sc) / L.rs_m) ** 2
            lum += L.amp * np.exp(-L.falloff * (((x - L.x_m) / L.rx_m) ** 2 + ds[:, None]))
        return np.stack([lum, lum, lum * STUDIO.tone.blue_gain], -1)

    def dots(self, t: float) -> list[tuple[float, float, float, np.ndarray]]:
        """시각 t 의 점 줄 [(화면 y, 반지름, 알파, 화면 x 배열)] — 설계 px, 화면 안(± margin)만. 줄 하나 = 같은 깊이 = 같은 크기·알파."""
        D = STUDIO.dots  # noqa: N806
        cam = drift_at(t)
        f = self._f_px()
        y2, z2 = self._cam_space(cam, self._dot_y, self._dot_z)
        out = []
        for yy, d in zip(y2, z2):
            if d <= 0:
                continue
            py = H_OUT / 2 - f * yy / d
            if not -D.margin_px <= py <= H_OUT + D.margin_px:
                continue
            px = W_OUT / 2 + f * (self._dot_x - cam[0]) / d
            px = px[(px >= -D.margin_px) & (px <= W_OUT + D.margin_px)]
            if px.size:
                out.append((float(py), max(D.radius_min, D.radius_k / d), min(D.alpha_max, max(D.alpha_min, D.alpha_k / d)), px))
        return out

    def background_surface(self, t: float) -> cairo.ImageSurface:
        rgb = np.clip(self.background(t), 0, 1) * np.iinfo(np.uint8).max
        img = np.rint(rgb).astype(np.uint8)
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_RGB24, self._nx)
        buf = np.zeros((self._ny, stride), np.uint8)
        px = buf[:, :self._nx * (stride // self._nx)].reshape(self._ny, self._nx, stride // self._nx)
        px[..., 0], px[..., 1], px[..., 2] = img[..., 2], img[..., 1], img[..., 0]   # BGRX(리틀 엔디언 RGB24)
        self._bg_buf = buf   # 표면이 쓰는 동안 버퍼를 붙잡는다
        return cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_RGB24, self._nx, self._ny, stride)

    def render_base(self, ctx: cairo.Context, view: "View") -> None:
        """배경(밝기 격자 → 이중선형 확대) + 점 격자. 설계 좌표로 그린다 — 장치 변환은 렌더 진입이 이미 걸었다."""
        t = getattr(view, "t", None)
        if t is None:
            raise StudioError("studio 무대 배경은 영상 시각이 필요하다 — View(..., t=시각) 로 그린다(조용히 t=0 으로 그리지 않는다, P6)")
        surf = self.background_surface(float(t))
        ctx.save()
        g = STUDIO.bg_grid_px
        ctx.scale(g, g)
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_BILINEAR)
        pat.set_extend(cairo.EXTEND_PAD)
        ctx.set_source(pat)
        ctx.paint()
        ctx.restore()
        r, gg, b = STUDIO.dots.rgb
        for py, rad, a, xs in self.dots(float(t)):
            ctx.set_source_rgba(r, gg, b, a)
            for px in xs:
                ctx.new_sub_path()
                ctx.arc(float(px), py, rad, 0, math.tau)
            ctx.fill()

    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> None:
        """라벨 없음(무대는 장식 — 내용은 아일랜드·카드)."""

    def lod_rules(self) -> dict[str, Any]:
        return {}


__all__ = ["StudioError", "StudioStage", "drift_at", "surface_yz", "tone_of"]
