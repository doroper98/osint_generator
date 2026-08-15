"""인물 사진 → **인쇄 스크리닝(screening)** 스타일라이저 — Phase 1 PoC.

실존 인물의 공식/퍼블릭도메인 사진을 **결정론 알고리즘**으로 신문·잡지 인쇄물
느낌의 흑백 자산으로 바꾼다. AI 이미지 생성은 쓰지 않는다 (GOAL G4-10).

설계 원칙 — **사진의 디테일을 버리지 않는다**. 획을 합성해 얼굴을 새로 그리지
않고(그건 반드시 기계적 텍스처 도배가 된다), 원본 사진의 계조를 살린 뒤 그 위에
**규칙적인 인쇄 스크린**을 얹는다. 확률적 점묘(스티플)는 화면에서 노이즈로
읽히므로 쓰지 않는다.

제공 스타일 3종:

* ``stylize_mono``       — 기준. 강한 S-커브 + 하이라이트 클리핑으로 펀치 있는
  고대비 듀오톤 사진. 배경은 플러드필 마스크로 투명. 래스터(PNG) 출력.
* ``stylize_halftone``   — mono 톤 위에 **45° 규칙 격자 AM 망점**. 셀 평균
  명도 → 점 반경. SVG ``<circle>`` + 동일 지오메트리 PNG.
* ``stylize_linescreen`` — 같은 원리의 **45° 직선 평행선 스크린**. 국소 명도 →
  선 굵기. 물결·warp 없음. SVG ``<path>`` + 동일 지오메트리 PNG.

그리고 콜라주 합성용:

* ``compose_mono_shadow`` — NYT 기사 콜라주 에딧처럼, mono 컷아웃 뒤에 **같은
  실루엣**을 강조색으로 채운 섀도를 깔아 합성. 섀도 문법은 두 축으로 고른다.

  - ``shadow_mode``: ``"offset"`` (실루엣을 dx,dy 만큼 밀어 깐 오프셋 섀도) /
    ``"outline"`` (실루엣을 원형으로 팽창시켜 인물을 균일하게 두르는 스티커
    키라인). 둘은 상호 배타다.
  - ``shadow_fill``: ``"solid"`` (먹면) / ``"hatch"`` (45° 평행선) /
    ``"dots"`` (45° 격자 도트). 패턴은 섀도 영역에서 정확히 클리핑되고,
    선·점 사이로는 종이색이 비친다.

난수는 ``seed`` 로 시작한 :class:`numpy.random.Generator` 에서만 뽑고, 스크린의
**격자 위상(phase)** 에만 쓴다(격자 자체는 항상 규칙적이다). 같은 입력 + 같은
seed + 같은 파라미터 → 바이트 단위로 같은 SVG/PNG.

CLI::

    python -m workers.engraving_stylizer <img> --style mono --out-png out.png
    python -m workers.engraving_stylizer <img> --style mono_shadow \
        --accent "#B03A2E" --out-png out.png
    python -m workers.engraving_stylizer <img> --style halftone \
        --out-svg out.svg --out-png out.png --seed 7

주: 본 모듈은 순수 라이브러리 + CLI 다. ``BaseWorker`` 래핑(C4)은 다음 Phase.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# --------------------------------------------------------------------------
# 상수
# --------------------------------------------------------------------------

#: 잉크 색 — 인쇄 자산은 단일 잉크색만 쓴다 (배경은 투명).
INK_COLOR: str = "#1C1A17"

#: 종이 색 — 듀오톤 보간의 밝은 끝.
PAPER_COLOR: str = "#FFFFFF"

#: SVG 좌표 반올림 자릿수 (파일 크기 ↔ 정밀도 절충).
_COORD_NDIGITS: int = 1


# --------------------------------------------------------------------------
# 지오메트리 데이터 구조
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Dot:
    """망점 하나. 좌표계는 원본 픽셀."""

    x: float
    y: float
    r: float


@dataclass(frozen=True)
class Stroke:
    """스크린 선 한 조각. ``points`` 는 폴리라인, ``width`` 는 굵기(px)."""

    points: tuple[tuple[float, float], ...]
    width: float


@dataclass
class PrintTone:
    """스타일라이저 공통 전처리 결과 — "인쇄용 톤".

    Attributes
    ----------
    ink:
        0(종이 = 잉크 없음) ~ 1(먹) 실수 배열. 배경 마스크가 이미 곱해져 있고,
        하이라이트는 **정확히 0** 이다.
    value:
        ``1 - ink``. 듀오톤 래스터를 만들 때 쓰는 밝기.
    foreground:
        0(배경) ~ 1(피사체) 마스크. 가장자리 플러드필로 구한다.
    levels:
        실제로 쓰인 (black_point, white_point) 쌍 — 튜닝·로그용.
    """

    ink: np.ndarray
    value: np.ndarray
    foreground: np.ndarray
    levels: tuple[float, float] = (0.0, 1.0)

    @property
    def height(self) -> int:
        return int(self.ink.shape[0])

    @property
    def width(self) -> int:
        return int(self.ink.shape[1])


@dataclass
class MonoResult:
    """``stylize_mono`` 산출물 — 래스터(듀오톤 RGBA) 한 장.

    사진 디테일 보존이 목적이므로 벡터(SVG)로는 내보내지 않는다.
    """

    width: int
    height: int
    style: str
    seed: int
    image: Image.Image
    tone: PrintTone | None = None
    params: dict[str, float | int | str] = field(default_factory=dict)

    @property
    def ink_area(self) -> float:
        """잉크 총량 지표(px^2 환산). 파라미터 튜닝·테스트용."""
        if self.tone is None:
            return 0.0
        return float(self.tone.ink.sum())

    def to_png(
        self,
        path: str | Path,
        *,
        out_width: int | None = None,
        background: str | None = None,
        supersample: int = 1,  # noqa: ARG002 - 시그니처 호환용(래스터는 불필요)
    ) -> Path:
        """PNG 저장. ``background`` 가 ``None`` 이면 배경 투명(RGBA)."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        image = self.image
        if out_width is not None and int(out_width) != self.width:
            target_w = max(1, int(out_width))
            target_h = max(1, int(round(self.height * target_w / float(self.width))))
            image = image.resize((target_w, target_h), Image.LANCZOS)
        if background is None:
            image.save(out)
        else:
            flat = Image.new("RGB", image.size, background)
            flat.paste(image, mask=image.split()[3])
            flat.save(out)
        return out


@dataclass
class ScreenResult:
    """스크린(망점/선) 산출물 — SVG 와 PNG 프리뷰의 단일 출처."""

    width: int
    height: int
    style: str
    seed: int
    dots: tuple[Dot, ...] = ()
    strokes: tuple[Stroke, ...] = ()
    ink: str = INK_COLOR
    params: dict[str, float | int | str] = field(default_factory=dict)

    # -- 통계 -----------------------------------------------------------
    @property
    def ink_area(self) -> float:
        """대략적인 잉크 면적(px^2). 파라미터 튜닝·테스트용 지표."""
        area = sum(math.pi * d.r * d.r for d in self.dots)
        for stroke in self.strokes:
            length = 0.0
            for (x0, y0), (x1, y1) in zip(stroke.points, stroke.points[1:]):
                length += math.hypot(x1 - x0, y1 - y0)
            area += length * stroke.width
        return area

    # -- SVG ------------------------------------------------------------
    def to_svg(self, *, ndigits: int = _COORD_NDIGITS) -> str:
        """SVG 문자열 생성. 배경은 칠하지 않는다(투명)."""

        def f(value: float) -> str:
            text = f"{round(float(value), ndigits):.{ndigits}f}"
            return text.rstrip("0").rstrip(".") if "." in text else text

        lines: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                '<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{self.width}" height="{self.height}" '
                f'viewBox="0 0 {self.width} {self.height}">'
            ),
            f"<title>screen-stylizer {self.style} seed={self.seed}</title>",
        ]

        if self.dots:
            lines.append(f'<g fill="{self.ink}" stroke="none">')
            for dot in self.dots:
                lines.append(
                    f'<circle cx="{f(dot.x)}" cy="{f(dot.y)}" r="{f(dot.r)}"/>'
                )
            lines.append("</g>")

        if self.strokes:
            lines.append(
                f'<g fill="none" stroke="{self.ink}" '
                'stroke-linecap="butt" stroke-linejoin="miter">'
            )
            for stroke in self.strokes:
                head = stroke.points[0]
                path = [f"M{f(head[0])} {f(head[1])}"]
                for x, y in stroke.points[1:]:
                    path.append(f"L{f(x)} {f(y)}")
                lines.append(
                    f'<path stroke-width="{f(stroke.width)}" d="{"".join(path)}"/>'
                )
            lines.append("</g>")

        lines.append("</svg>")
        return "\n".join(lines) + "\n"

    def write_svg(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_svg(), encoding="utf-8")
        return out

    # -- PNG (프리뷰) ----------------------------------------------------
    def to_png(
        self,
        path: str | Path,
        *,
        out_width: int | None = None,
        supersample: int = 3,
        background: str | None = "white",
    ) -> Path:
        """같은 지오메트리를 PIL 로 직접 래스터화해 PNG 저장.

        Parameters
        ----------
        out_width:
            출력 가로 픽셀. ``None`` 이면 원본 크기.
        supersample:
            내부 확대 배율 — 그린 뒤 축소해 안티에일리어싱한다.
        background:
            PNG 배경색. ``None`` 이면 투명(RGBA).
        """
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        target_w = int(out_width or self.width)
        scale = target_w / float(self.width)
        target_h = max(1, int(round(self.height * scale)))
        ss = max(1, int(supersample))
        canvas_w, canvas_h = target_w * ss, target_h * ss
        k = scale * ss

        image = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        ink_rgb = _hex_to_rgb(self.ink)
        ink = (*ink_rgb, 255)

        for dot in self.dots:
            r = max(dot.r * k, 0.35)
            cx, cy = dot.x * k, dot.y * k
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ink)

        for stroke in self.strokes:
            pts = [(x * k, y * k) for x, y in stroke.points]
            width = max(1, int(round(stroke.width * k)))
            if len(pts) == 1:
                x, y = pts[0]
                r = width / 2.0
                draw.ellipse((x - r, y - r, x + r, y + r), fill=ink)
            else:
                draw.line(pts, fill=ink, width=width)

        image = image.resize((target_w, target_h), Image.LANCZOS)
        if background is not None:
            flat = Image.new("RGB", image.size, background)
            flat.paste(image, mask=image.split()[3])
            flat.save(out)
        else:
            image.save(out)
        return out


# --------------------------------------------------------------------------
# 유틸
# --------------------------------------------------------------------------


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def _sample_bilinear(arr: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """``arr`` 를 (xs, ys) 위치에서 이중선형 보간 샘플링."""
    h, w = arr.shape
    x = np.clip(xs, 0.0, w - 1.000001)
    y = np.clip(ys, 0.0, h - 1.000001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = x - x0
    fy = y - y0
    top = arr[y0, x0] * (1.0 - fx) + arr[y0, x1] * fx
    bot = arr[y1, x0] * (1.0 - fx) + arr[y1, x1] * fx
    return top * (1.0 - fy) + bot * fy


def _blur_array(arr: np.ndarray, radius: float) -> np.ndarray:
    """0~1 실수 배열을 가우시안 블러(8bit 경유). 셀 평균 근사에 쓴다."""
    if radius <= 0.0:
        return arr.astype(np.float32)
    src = Image.fromarray(
        np.clip(arr * 255.0, 0.0, 255.0).astype(np.uint8), mode="L"
    ).filter(ImageFilter.GaussianBlur(radius=float(radius)))
    return np.asarray(src, dtype=np.float32) / 255.0


def _erode_mask(mask: np.ndarray, pixels: float) -> np.ndarray:
    """0~1 마스크를 ``pixels`` px 침식."""
    size = 2 * max(1, int(round(float(pixels)))) + 1
    shrunk = Image.fromarray(
        np.clip(mask * 255.0, 0.0, 255.0).astype(np.uint8), mode="L"
    ).filter(ImageFilter.MinFilter(size))
    return np.asarray(shrunk, dtype=np.float32) / 255.0


def _extend_interior(
    gray: np.ndarray, core: np.ndarray, *, radius: float
) -> np.ndarray:
    """실루엣 바깥을 **피사체 내부 톤으로 메운다** (마스크 가중 블러 = 간이 인페인트).

    ``core`` (확실한 내부) 값들을 마스크 가중 블러로 바깥까지 번지게 해 배경
    자리를 채운다. 결과적으로 실루엣 근처의 배경색 오염(검은 테두리)과 언샤프
    후광이 사라진다.
    """
    span = max(2.0, float(radius) * 2.5)
    weight = _blur_array(core, span)
    filled = _blur_array(gray * core, span) / np.maximum(weight, 1e-3)
    filled = np.where(weight > 1e-3, filled, gray)
    blend = np.clip(core, 0.0, 1.0)
    return (gray * blend + filled * (1.0 - blend)).astype(np.float32)


def _s_curve(value: np.ndarray, strength: float, pivot: float) -> np.ndarray:
    """``pivot`` 기준 대칭 S-커브. ``strength`` 1.0 이면 항등.

    어두운 쪽은 더 어둡게, 밝은 쪽은 더 밝게 밀어 중간 회색(안개)을 없앤다.
    """
    exponent = max(1e-6, float(strength))
    p = min(max(float(pivot), 1e-3), 1.0 - 1e-3)
    v = np.clip(value, 0.0, 1.0)
    lower = p * np.power(v / p, exponent)
    upper = 1.0 - (1.0 - p) * np.power((1.0 - v) / (1.0 - p), exponent)
    return np.where(v < p, lower, upper).astype(np.float32)


def _screen_axes(angle_deg: float) -> tuple[float, float, float, float]:
    """스크린 각도 → (진행축 ux,uy, 수직축 vx,vy) 단위벡터."""
    theta = math.radians(float(angle_deg))
    ux, uy = math.cos(theta), math.sin(theta)
    return ux, uy, -uy, ux


def _screen_coords(width: int, height: int, angle_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """캔버스 전 픽셀의 (u, v) 회전 좌표 맵. 스크린 계열과 같은 축 정의를 쓴다."""
    ux, uy, vx, vy = _screen_axes(angle_deg)
    xs = np.arange(int(width), dtype=np.float32)[np.newaxis, :]
    ys = np.arange(int(height), dtype=np.float32)[:, np.newaxis]
    return (xs * ux + ys * uy, xs * vx + ys * vy)


# --------------------------------------------------------------------------
# 섀도 지오메트리 — 원형 팽창(거리변환) + 패턴 채움
# --------------------------------------------------------------------------


def _distance_outside(mask: np.ndarray, max_dist: float) -> np.ndarray:
    """``mask``(bool) 바깥 픽셀의 **정확한 유클리드 거리**. scipy 없이 numpy 만.

    2-패스 분리형 거리변환이다.

    1. 세로 패스 — 각 열에서 가장 가까운 True 까지의 세로 거리를 전/후 스캔
       두 번으로 구한다(이진 입력이라 1차원 EDT = 단순 누적 최소값).
    2. 가로 패스 — ``sqrt(dx² + col[y, x+dx]²)`` 의 최소값을 ``|dx| ≤ R`` 창에서
       취한다. 창 밖 후보는 이미 거리가 ``R`` 을 넘으므로, ``max_dist`` 이하
       구간에서 결과는 **정확한** 유클리드 거리다.

    맨해튼/체스보드 반복 팽창과 달리 등거리면이 마름모·사각으로 각지지 않아,
    팽창 경계가 원형으로 매끈하게 나온다.
    """
    height, width = mask.shape
    reach = max(0.0, float(max_dist))
    far = reach + 2.0

    col = np.where(mask, 0.0, far).astype(np.float32)
    for y in range(1, height):
        np.minimum(col[y], col[y - 1] + 1.0, out=col[y])
    for y in range(height - 2, -1, -1):
        np.minimum(col[y], col[y + 1] + 1.0, out=col[y])
    np.minimum(col, far, out=col)

    base = np.square(col)
    best = base.copy()
    span = int(math.ceil(reach))
    for dx in range(1, span + 1):
        cost = float(dx * dx)
        # 오른쪽 dx 칸 떨어진 열을 후보로
        np.minimum(best[:, : width - dx], base[:, dx:] + cost, out=best[:, : width - dx])
        # 왼쪽 dx 칸 떨어진 열을 후보로
        np.minimum(best[:, dx:], base[:, : width - dx] + cost, out=best[:, dx:])

    return np.minimum(np.sqrt(best), far).astype(np.float32)


def _dilate_alpha(alpha: np.ndarray, radius: float) -> np.ndarray:
    """0~1 알파를 반지름 ``radius`` px **원형 구조요소**로 팽창시킨다.

    거리변환을 ``radius`` 에서 자르는 방식이라 경계는 **하드 에지**다(블러 아님).
    다만 1px 폭의 커버리지 램프(``radius + 0.5 - dist``)를 남겨 계단 자국만
    없앤다 — 벡터 도형을 래스터화할 때와 같은 안티에일리어싱이다.
    """
    reach = float(radius)
    clean = np.clip(alpha, 0.0, 1.0).astype(np.float32)
    if reach <= 0.0:
        return clean
    core = clean >= 0.5
    if not bool(core.any()):
        return np.zeros_like(clean)
    dist = _distance_outside(core, reach + 1.0)
    grown = np.clip(reach + 0.5 - dist, 0.0, 1.0)
    return np.maximum(grown, clean).astype(np.float32)


def _hatch_alpha(
    width: int,
    height: int,
    *,
    spacing: float,
    thickness: float,
    angle: float,
    phase: float,
) -> np.ndarray:
    """45°(기본) 평행선 패턴의 0~1 커버리지 맵. 선 위 1, 선 사이 0."""
    _, v = _screen_coords(width, height, angle)
    gap = max(1.0, float(spacing))
    frac = np.mod(v / gap + float(phase), 1.0)
    dist = np.minimum(frac, 1.0 - frac) * gap
    return np.clip(max(0.0, float(thickness)) * 0.5 + 0.5 - dist, 0.0, 1.0).astype(
        np.float32
    )


def _dot_alpha(
    width: int,
    height: int,
    *,
    spacing: float,
    radius: float,
    angle: float,
    phase_u: float,
    phase_v: float,
) -> np.ndarray:
    """45°(기본) 회전 정격자 도트 패턴의 0~1 커버리지 맵."""
    u, v = _screen_coords(width, height, angle)
    step = max(1.0, float(spacing))
    du = (np.mod(u / step + float(phase_u), 1.0) - 0.5) * step
    dv = (np.mod(v / step + float(phase_v), 1.0) - 0.5) * step
    dist = np.hypot(du, dv)
    return np.clip(max(0.0, float(radius)) + 0.5 - dist, 0.0, 1.0).astype(np.float32)


def _fill_alpha(
    width: int,
    height: int,
    fill: str,
    *,
    seed: int,
    angle: float,
    hatch_spacing: float,
    hatch_width: float,
    dot_spacing: float,
    dot_radius: float,
) -> np.ndarray | None:
    """``shadow_fill`` → 커버리지 맵. ``"solid"`` 면 ``None``(전면 채움).

    격자 **위상만** ``seed`` 로 정한다(격자 자체는 항상 규칙적). 전역 난수는
    쓰지 않으므로 같은 인자 → 같은 출력이다.
    """
    if fill == "solid":
        return None
    rng = np.random.default_rng(int(seed))
    phase_u, phase_v = (float(value) for value in rng.uniform(0.0, 1.0, size=2))
    if fill == "hatch":
        return _hatch_alpha(
            width,
            height,
            spacing=hatch_spacing,
            thickness=hatch_width,
            angle=angle,
            phase=phase_v,
        )
    if fill == "dots":
        return _dot_alpha(
            width,
            height,
            spacing=dot_spacing,
            radius=dot_radius,
            angle=angle,
            phase_u=phase_u,
            phase_v=phase_v,
        )
    raise ValueError(f"알 수 없는 shadow_fill: {fill!r}")


# --------------------------------------------------------------------------
# 절차 생성 배경 — 꾸겼다 편 갱지
# --------------------------------------------------------------------------


def _smoothstep(t: np.ndarray) -> np.ndarray:
    """0~1 구간을 부드럽게 이어 주는 에르미트 보간 (밸류 노이즈 격자 자국 제거)."""
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def _value_noise(
    width: int, height: int, cells_x: int, cells_y: int, rng: np.random.Generator
) -> np.ndarray:
    """저해상 난수 격자를 스무스스텝 보간해 키운 0~1 밸류 노이즈."""
    cx = max(1, int(cells_x))
    cy = max(1, int(cells_y))
    grid = rng.random((cy + 1, cx + 1)).astype(np.float32)

    xs = np.linspace(0.0, float(cx), int(width), endpoint=False, dtype=np.float32)
    ys = np.linspace(0.0, float(cy), int(height), endpoint=False, dtype=np.float32)
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    fx = _smoothstep(xs - x0)
    fy = _smoothstep(ys - y0)
    x1 = np.minimum(x0 + 1, cx)
    y1 = np.minimum(y0 + 1, cy)

    rows = grid[:, x0] * (1.0 - fx) + grid[:, x1] * fx
    return (rows[y0] * (1.0 - fy)[:, None] + rows[y1] * fy[:, None]).astype(np.float32)


def _crumple_shading(
    width: int,
    height: int,
    rng: np.random.Generator,
    *,
    folds: int,
    softness: float,
    light_deg: float = 128.0,
) -> np.ndarray:
    """꾸김 음영 — **접힘면(fold plane)** 을 여러 장 겹친 종이의 기울기 조명.

    종이를 꾸기면 표면은 직선 크리즈로 나뉜 **평평한 조각(facet)** 들의 집합이
    된다. 그래서 높이장을 ``h = Σ aᵢ·|dᵢ|`` (dᵢ = i 번째 접힘선까지의 부호 거리)
    로 세우면 조각 안은 평면, 크리즈에서만 기울기가 꺾인다. 여기서는 조명에
    필요한 **기울기만** 해석적으로 누적한다.

    ``∂|d|/∂x = d/√(d²+ε²)·nₓ`` — ``ε`` 이 크리즈의 둥근 정도(px)다. 조각 안은
    기울기가 상수라 평평하게, 크리즈 위에서는 부호가 뒤집혀 **밝은 능선 +
    어두운 골** 한 쌍이 각지게 생긴다(가우시안 블러와 달리 방향성이 남는다).
    거기에 접힘선 위 폭 몇 px 짜리 **크리즈 하이라이트**를 따로 더한다 — 실제
    사진에서 꾸긴 자국이 가장 먼저 읽히는 요소다.

    각 접힘면에는 타원 가우시안 포락을 곱해 화면을 가로지르는 무한 직선이 아니라
    **국소 구김**이 되게 하고, 접힘면 절반은 크게(큰 조각) 절반은 작게(잔구김)
    잡아 크기 위계를 만든다.
    """
    w, h = int(width), int(height)
    xs = np.arange(w, dtype=np.float32)[np.newaxis, :]
    ys = np.arange(h, dtype=np.float32)[:, np.newaxis]
    grad_x = np.zeros((h, w), dtype=np.float32)
    grad_y = np.zeros((h, w), dtype=np.float32)
    ridge = np.zeros((h, w), dtype=np.float32)
    diag = math.hypot(float(w), float(h))
    total = max(0, int(folds))

    for index in range(total):
        local = index >= total // 2
        theta = float(rng.uniform(0.0, math.pi))
        nx, ny = math.cos(theta), math.sin(theta)
        px = float(rng.uniform(-0.1, 1.1)) * w
        py = float(rng.uniform(-0.1, 1.1)) * h
        eps = float(rng.uniform(0.6, 2.0)) * float(softness) * (0.7 if local else 1.0)
        reach = float(
            rng.uniform(0.05, 0.13) if local else rng.uniform(0.13, 0.30)
        ) * diag
        amp = float(rng.uniform(0.35, 1.0)) * (1.0 if rng.random() < 0.5 else -1.0)
        if local:
            amp *= 0.8
        wobble = float(rng.uniform(1.1, 2.4))
        phase = float(rng.uniform(0.0, 2.0 * math.pi))

        dx = xs - px
        dy = ys - py
        # 접힘선은 **직선**이다 — 휘게 하면 종이가 아니라 천처럼 보인다.
        along = dx * -ny + dy * nx
        across = dx * nx + dy * ny
        env = np.exp(-(np.square(along / reach) + np.square(across / (reach * 0.8))))
        # 능선 세기가 선을 따라 출렁여야 "레이저 선"이 아니라 접힌 자국으로 읽힌다.
        env = env * (0.55 + 0.45 * np.cos(along / reach * wobble * math.pi + phase))

        slope = across / np.sqrt(across * across + eps * eps)
        weight = (amp * env * slope).astype(np.float32)
        grad_x += weight * nx
        grad_y += weight * ny

        line = across / (eps * 1.7)
        ridge += (amp * env * np.exp(-0.5 * line * line)).astype(np.float32)

    light = math.radians(float(light_deg))
    facets = grad_x * math.cos(light) + grad_y * math.sin(light)
    facets /= max(1e-6, float(np.percentile(np.abs(facets), 99.0)))
    ridge /= max(1e-6, float(np.percentile(np.abs(ridge), 99.5)))
    return (facets + 0.85 * ridge).astype(np.float32)


def make_crumpled_paper(
    width: int,
    height: int,
    *,
    seed: int,
    base: str = "#DDD3BD",
    amplitude: float = 0.06,
    creases: int = 44,
    fleck_density: float = 0.00035,
) -> Image.Image:
    """**꾸겼다가 편 갱지**(재생지) 배경을 결정론 절차 생성한다.

    합성 순서는 (1) 저주파 굴곡 → (2) 접힘면 꾸김 음영(각진 크리즈 + 평평한
    조각) → (3) 잔주름 리지드 노이즈 → (4) 미세 섬유 그레인 + 티끌 →
    (5) 가장자리 감광 이다. ``amplitude`` 는 최종 명도 변동폭(±비율)이라
    기본값 0.06 이면 ±6% 안에서만 흔들린다 — 종이는 질감이고 주인공은
    인물이라는 원칙(C0) 때문이다.

    Parameters
    ----------
    width, height:
        캔버스 픽셀. 쇼츠 배경이면 1080×1920.
    seed:
        결정론 시드. 같은 (크기, seed, 파라미터) → 바이트 단위로 같은 이미지.
    base:
        갱지 바탕색(HEX).
    amplitude:
        명도 변동 폭(±비율). 0.06 = ±6%.
    creases:
        접힘면 개수. 많을수록 조각이 잘게 갈린다.
    fleck_density:
        재생지 티끌(어두운 섬유 조각) 밀도 — 픽셀당 확률.

    Returns
    -------
    PIL.Image.Image
        RGB 텍스처.
    """
    w, h = max(1, int(width)), max(1, int(height))
    rng = np.random.default_rng(int(seed))
    short = float(min(w, h))

    # (1) 저주파 굴곡 — 종이 전체가 완전히 평평하지 않다.
    swell = _value_noise(w, h, max(2, round(w / short * 3)), 3, rng) - 0.5

    # (2) 접힘면 꾸김 음영 — 이 텍스처의 주역.
    crumple = _crumple_shading(
        w, h, rng, folds=creases, softness=max(1.0, short / 620.0)
    )

    # (3) 잔주름 — 크리즈 사이 조각에 남는 미세 굴곡.
    fine = _value_noise(w, h, max(4, round(w / short * 22)), 22, rng)
    fine_ridged = 1.0 - np.abs(2.0 * fine - 1.0)
    fine_ridged = fine_ridged - float(fine_ridged.mean())

    # (4) 섬유 그레인 + 재생지 티끌.
    grain = rng.normal(0.0, 1.0, size=(h, w)).astype(np.float32)
    spread = max(1e-6, float(grain.max() - grain.min()))
    grain = _blur_array((grain - float(grain.min())) / spread, 0.45) - 0.5

    shade = (
        0.30 * swell
        + 1.00 * (crumple / max(1e-6, float(np.percentile(np.abs(crumple), 99.0))))
        + 0.22 * fine_ridged
        + 0.40 * grain
    ).astype(np.float32)

    # 정규화 — 꼬리를 뺀 실효 진폭을 ``amplitude`` 에 맞춘다.
    shade -= float(shade.mean())
    scale = float(np.percentile(np.abs(shade), 99.0))
    shade = shade / max(scale, 1e-6) * float(amplitude)

    # (5) 가장자리 감광.
    gx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[np.newaxis, :]
    gy = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, np.newaxis]
    vignette = 1.0 - 0.055 * np.clip(gx * gx * 0.85 + gy * gy * 0.85, 0.0, 1.6)

    tint = np.asarray(_hex_to_rgb(base), dtype=np.float32)
    rgb = tint[np.newaxis, np.newaxis, :] * ((1.0 + shade) * vignette)[..., np.newaxis]

    flecks = rng.random((h, w)) < max(0.0, float(fleck_density))
    if bool(flecks.any()):
        depth = 1.0 - 0.16 * rng.random((h, w)).astype(np.float32)
        rgb = np.where(flecks[..., np.newaxis], rgb * depth[..., np.newaxis], rgb)

    return Image.fromarray(np.rint(np.clip(rgb, 0.0, 255.0)).astype(np.uint8), "RGB")


def _paste_slices(
    canvas: tuple[int, int], patch: tuple[int, int], x: int, y: int
) -> tuple[tuple[slice, slice], tuple[slice, slice]] | None:
    """(캔버스 슬라이스, 패치 슬라이스) — 캔버스를 벗어나는 부분은 잘라 낸다."""
    ch, cw = canvas
    ph, pw = patch
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(cw, int(x) + pw), min(ch, int(y) + ph)
    if x0 >= x1 or y0 >= y1:
        return None
    dst = (slice(y0, y1), slice(x0, x1))
    src = (slice(y0 - int(y), y1 - int(y)), slice(x0 - int(x), x1 - int(x)))
    return dst, src


# --------------------------------------------------------------------------
# 배경 마스크 (가장자리 플러드필)
# --------------------------------------------------------------------------


def _largest_foreground_component(mask: np.ndarray) -> np.ndarray:
    """전경 마스크에서 가장 큰 4-연결 성분만 남긴다.

    플러드필은 배경 안의 밝은 장식(액자 조각·깃발 줄무늬 등)을 못 지운다.
    그 잔재는 피사체와 떨어진 **작은 섬**이므로, 최대 성분만 남기면 사라진다.
    """
    height, width = mask.shape
    label = np.zeros((height, width), dtype=np.int32)
    best_label = 0
    best_size = 0
    current = 0
    for sy in range(height):
        for sx in range(width):
            if not mask[sy, sx] or label[sy, sx]:
                continue
            current += 1
            size = 0
            queue: deque[tuple[int, int]] = deque([(sy, sx)])
            label[sy, sx] = current
            while queue:
                y, x = queue.popleft()
                size += 1
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and not label[ny, nx]
                    ):
                        label[ny, nx] = current
                        queue.append((ny, nx))
            if size > best_size:
                best_size = size
                best_label = current
    if best_label == 0:
        return mask
    return label == best_label


def background_mask(
    image: Image.Image,
    *,
    tolerance: float = 45.0,
    work_dim: int = 560,
    seed_edges: str = "top,left,right",
    side_fraction: float = 0.62,
    edge_stop: float = 26.0,
    opening: int = 3,
    keep_largest: bool = True,
    dilate: int = 1,
    smooth: float = 0.0,
    erode: float = 2.0,
    feather: float = 1.0,
) -> np.ndarray:
    """가장자리 플러드필로 전경(피사체) 마스크를 구한다.

    테두리 픽셀을 씨앗으로 삼아, 각 씨앗의 **원래 색**과의 색거리가 ``tolerance``
    미만인 4-연결 성분을 배경으로 본다. 인물 사진은 보통 몸통이 아래 테두리에
    닿으므로 기본값은 아래 테두리를 씨앗에서 제외하고, 좌우 테두리는 위쪽
    ``side_fraction`` 만 쓴다. ``keep_largest`` 면 플러드필이 놓친 배경 잔재
    (떨어진 작은 섬)를 최대 연결성분만 남겨 정리한다.

    컷아웃 가장자리 품질이 중요하므로(콜라주에서 후광·배경 잔재·계단 자국이 바로
    보인다) 원본 해상도로 되돌린 뒤 (1) 저해상 작업본의 계단을 ``smooth`` 블러 +
    소프트 임계로 펴고, (2) ``erode`` px 만큼 **침식**해 배경 띠를 잘라내고,
    (3) ``feather`` 로 아주 얇게만 부드럽게 만든다.

    Returns
    -------
    np.ndarray
        원본 해상도의 0(배경)~1(전경) float 마스크.
    """
    full_w, full_h = image.size
    scale = min(1.0, work_dim / float(max(full_w, full_h)))
    small_w = max(8, int(round(full_w * scale)))
    small_h = max(8, int(round(full_h * scale)))
    small = image.convert("RGB").resize((small_w, small_h), Image.BILINEAR)
    rgb = np.asarray(small, dtype=np.float32)

    edges = {token.strip() for token in seed_edges.split(",") if token.strip()}
    is_bg = np.zeros((small_h, small_w), dtype=bool)
    seed_color = np.zeros((small_h, small_w, 3), dtype=np.float32)
    queue: deque[tuple[int, int]] = deque()

    def push(y: int, x: int) -> None:
        if not is_bg[y, x]:
            is_bg[y, x] = True
            seed_color[y, x] = rgb[y, x]
            queue.append((y, x))

    side_limit = max(1, int(small_h * side_fraction))
    if "top" in edges:
        for x in range(small_w):
            push(0, x)
    if "bottom" in edges:
        for x in range(small_w):
            push(small_h - 1, x)
    if "left" in edges:
        for y in range(side_limit):
            push(y, 0)
    if "right" in edges:
        for y in range(side_limit):
            push(y, small_w - 1)

    # 두 조건 동시 만족일 때만 배경으로 번진다.
    #  (1) 씨앗 색과의 전역 색거리 < tolerance  → 배경 색역을 벗어나지 않게
    #  (2) 직전 픽셀과의 국소 색거리 < edge_stop → 뚜렷한 경계(옷깃 등)를 못 넘게
    tol_sq = float(tolerance) ** 2
    stop_sq = float(edge_stop) ** 2
    while queue:
        y, x = queue.popleft()
        base = seed_color[y, x]
        here = rgb[y, x]
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < small_h and 0 <= nx < small_w and not is_bg[ny, nx]:
                neighbor = rgb[ny, nx]
                diff = neighbor - base
                step = neighbor - here
                if float(diff @ diff) < tol_sq and float(step @ step) < stop_sq:
                    is_bg[ny, nx] = True
                    seed_color[ny, nx] = base
                    queue.append((ny, nx))

    foreground = ~is_bg
    if opening > 1:
        # 열림 연산 — 깃대·액자 모서리 같은 가느다란 배경 잔재를 끊어 낸다.
        size = int(opening) if int(opening) % 2 else int(opening) + 1
        opened = (
            Image.fromarray(np.where(foreground, 255, 0).astype(np.uint8), mode="L")
            .filter(ImageFilter.MinFilter(size))
            .filter(ImageFilter.MaxFilter(size))
        )
        foreground = np.asarray(opened) > 127
    if keep_largest:
        foreground = _largest_foreground_component(foreground)

    fg_small = np.where(foreground, 255, 0).astype(np.uint8)
    fg_img = Image.fromarray(fg_small, mode="L")
    if dilate > 0:
        # 저해상 작업본에서 잃은 실루엣을 조금 되돌린다.
        fg_img = fg_img.filter(ImageFilter.MaxFilter(size=2 * int(dilate) + 1))
    mask_img = fg_img.resize((full_w, full_h), Image.BILINEAR)

    mask = np.asarray(mask_img, dtype=np.float32) / 255.0
    radius = float(smooth)
    if radius <= 0.0:
        radius = 0.9 * max(full_w, full_h) / float(max(small_w, small_h))
    if radius > 0.0:
        # 저해상 마스크의 계단 자국 제거 — 크게 흐린 뒤 다시 날카롭게 임계.
        mask = _blur_array(mask, radius)
        mask = np.clip((mask - 0.5) * 3.0 + 0.5, 0.0, 1.0)
    if erode > 0.0:
        # 원본 해상도 침식 — 저해상 마스크를 키운 탓에 남는 배경 띠(후광)를 깎는다.
        size = 2 * int(round(float(erode))) + 1
        eroded = Image.fromarray((mask * 255.0).astype(np.uint8), mode="L").filter(
            ImageFilter.MinFilter(size)
        )
        mask = np.asarray(eroded, dtype=np.float32) / 255.0
    if feather > 0.0:
        blurred = Image.fromarray((mask * 255.0).astype(np.uint8), mode="L").filter(
            ImageFilter.GaussianBlur(radius=float(feather))
        )
        mask = np.asarray(blurred, dtype=np.float32) / 255.0
    return mask


# --------------------------------------------------------------------------
# 인쇄용 톤 (공통 전처리)
# --------------------------------------------------------------------------


def build_print_tone(
    image: Image.Image,
    *,
    denoise: int = 0,
    defringe: float = 3.0,
    detail_strength: float = 0.4,
    detail_radius: float = 0.0,
    micro_strength: float = 0.0,
    shadow_percentile: float = 3.0,
    highlight_percentile: float = 86.0,
    midtone_gamma: float = 1.8,
    contrast: float = 1.7,
    pivot: float = 0.52,
    remove_background: bool = True,
    bg_tolerance: float = 45.0,
    bg_edge_stop: float = 26.0,
    bg_seed_edges: str = "top,left,right",
    bg_side_fraction: float = 0.62,
    bg_work_dim: int = 560,
    bg_opening: int = 3,
    bg_smooth: float = 0.0,
    bg_erode: float = 2.0,
    bg_feather: float = 1.0,
) -> PrintTone:
    """사진 → 인쇄용 톤(잉크 0~1) + 전경 마스크.

    순서는 (1) 전경 마스크 → (2) 가장자리 디프린지 → (3) 언샤프 국소대비 →
    (4) 전경 기준 **자동 레벨** → (5) 중간톤 감마 → (6) S-커브 다.

    디프린지(``defringe``)는 실루엣 바깥을 **피사체 내부 색으로 메워** 배경을
    평평하게 늘린다. 이걸 안 하면 (a) 배경의 어두운 픽셀이 가장자리에 섞여
    검은 테두리로 남고, (b) 언샤프가 그 경계에서 후광을 만든다. 콜라주에서는
    둘 다 바로 "합성 티"로 보인다.

    레벨은 전경 픽셀의 백분위로 잡는다. ``highlight_percentile`` 위쪽 픽셀은
    **정확히 잉크 0** 이 되어 이마·볼 하이라이트가 깨끗한 흰 면으로 비고,
    ``shadow_percentile`` 아래는 완전한 먹이 된다. ``midtone_gamma`` 는 0 과 1 을
    고정한 채 중간톤만 눌러(값 > 1 이면 어둡게) 얼굴 명암을 되살리고, 마지막
    S-커브가 남은 중간 회색(안개)을 흑/백 양쪽으로 밀어낸다.
    """
    rgb_img = image.convert("RGB")
    gray_img = rgb_img.convert("L")
    gray = np.asarray(gray_img, dtype=np.float32) / 255.0
    height, width = gray.shape

    if denoise and int(denoise) > 1:
        # 미디언 = 경계 보존 잡음 제거. 이걸 안 하면 뒤의 언샤프가 피부 모공·
        # 센서 노이즈까지 키워서 "복사기 자국" 처럼 보인다.
        size = int(denoise) if int(denoise) % 2 else int(denoise) + 1
        gray = (
            np.asarray(
                gray_img.filter(ImageFilter.MedianFilter(size=size)), dtype=np.float32
            )
            / 255.0
        )

    if remove_background:
        foreground = background_mask(
            rgb_img,
            tolerance=bg_tolerance,
            edge_stop=bg_edge_stop,
            seed_edges=bg_seed_edges,
            side_fraction=bg_side_fraction,
            work_dim=int(bg_work_dim),
            opening=int(bg_opening),
            smooth=bg_smooth,
            erode=bg_erode,
            feather=bg_feather,
        )
        if defringe > 0.0:
            # 인페인트로 채운 자리는 **보여 주지 않는다** — 알파도 core 로 좁혀서
            # 실제 피사체 픽셀만 남긴다(가짜 회색 후광 방지).
            core = _erode_mask(foreground, float(defringe))
            gray = _extend_interior(gray, core, radius=float(defringe))
            foreground = _blur_array(core, max(0.6, float(bg_feather)))
    else:
        foreground = np.ones_like(gray, dtype=np.float32)

    radius = float(detail_radius)
    if radius <= 0.0:
        radius = max(2.0, max(width, height) / 140.0)

    if detail_strength > 0.0:
        blurred = _blur_array(gray, radius)
        gray = np.clip(gray + float(detail_strength) * (gray - blurred), 0.0, 1.0)
    if micro_strength > 0.0:
        micro = _blur_array(gray, max(1.0, radius * 0.28))
        gray = np.clip(gray + float(micro_strength) * (gray - micro), 0.0, 1.0)

    sample = gray[foreground > 0.5]
    if sample.size < 64:
        sample = gray.ravel()
    black_point = float(np.percentile(sample, float(shadow_percentile)))
    white_point = float(np.percentile(sample, float(highlight_percentile)))
    if white_point - black_point < 0.02:
        black_point, white_point = 0.0, 1.0

    leveled = np.clip((gray - black_point) / (white_point - black_point), 0.0, 1.0)
    if abs(float(midtone_gamma) - 1.0) > 1e-6:
        leveled = np.power(leveled, max(1e-6, float(midtone_gamma)))
    value = _s_curve(leveled, contrast, pivot)

    ink = np.clip((1.0 - value) * foreground, 0.0, 1.0).astype(np.float32)
    return PrintTone(
        ink=ink,
        value=(1.0 - ink).astype(np.float32),
        foreground=foreground.astype(np.float32),
        levels=(black_point, white_point),
    )


def _open_image(source: str | Path | Image.Image) -> Image.Image:
    if isinstance(source, Image.Image):
        return source
    return Image.open(Path(source))


def _duotone(
    tone: PrintTone, *, ink_color: str = INK_COLOR, paper_color: str = PAPER_COLOR
) -> Image.Image:
    """잉크량 → 종이색↔잉크색 듀오톤 RGBA (알파 = 전경 마스크)."""
    ink_rgb = np.asarray(_hex_to_rgb(ink_color), dtype=np.float32)
    paper_rgb = np.asarray(_hex_to_rgb(paper_color), dtype=np.float32)
    amount = tone.ink[..., np.newaxis]
    rgb = paper_rgb + (ink_rgb - paper_rgb) * amount
    alpha = np.clip(tone.foreground * 255.0, 0.0, 255.0)
    rgba = np.concatenate(
        (np.clip(rgb, 0.0, 255.0), alpha[..., np.newaxis]), axis=2
    ).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


# --------------------------------------------------------------------------
# 스타일 1 — 고대비 흑백 (mono)
# --------------------------------------------------------------------------


def stylize_mono(
    image: str | Path | Image.Image,
    *,
    seed: int = 0,
    ink_color: str = INK_COLOR,
    paper_color: str = PAPER_COLOR,
    tone: PrintTone | None = None,
    **tone_kwargs: float | bool | str,
) -> MonoResult:
    """고대비 흑백 듀오톤 — 기준 스타일.

    사진의 계조를 그대로 살리되 레벨/S-커브로 펀치를 준다. 배경은 투명이라
    바로 콜라주에 얹을 수 있는 컷아웃이다.

    Parameters
    ----------
    seed:
        결과에 영향은 없지만(결정론 래스터) 자산 메타데이터 일관성을 위해 기록.
    tone:
        미리 만든 :class:`PrintTone`. 없으면 ``tone_kwargs`` 로 새로 만든다.
    """
    img = _open_image(image)
    print_tone = tone if tone is not None else build_print_tone(img, **tone_kwargs)  # type: ignore[arg-type]
    raster = _duotone(print_tone, ink_color=ink_color, paper_color=paper_color)
    return MonoResult(
        width=print_tone.width,
        height=print_tone.height,
        style="mono",
        seed=int(seed),
        image=raster,
        tone=print_tone,
        params={
            "ink_color": ink_color,
            "paper_color": paper_color,
            "black_point": float(print_tone.levels[0]),
            "white_point": float(print_tone.levels[1]),
        },
    )


def compose_mono_shadow(
    image: str | Path | Image.Image,
    *,
    accent: str = "#B03A2E",
    offset: tuple[int, int] = (14, 18),
    shadow_mode: Literal["offset", "outline"] = "offset",
    outline_px: int = 22,
    shadow_fill: Literal["solid", "hatch", "dots"] = "solid",
    fill_angle: float = 45.0,
    hatch_spacing: float = 7.0,
    hatch_width: float = 2.6,
    dot_spacing: float = 8.0,
    dot_radius: float = 2.2,
    paper: str | Image.Image | None = "#E8DFC9",
    pad: tuple[int, int, int, int] = (0, 0, 0, 0),
    seed: int = 0,
    mono: MonoResult | None = None,
    tone: PrintTone | None = None,
    **tone_kwargs: float | bool | str,
) -> Image.Image:
    """mono 컷아웃 + **같은 실루엣**의 컬러 섀도 합성 (NYT 콜라주 에딧).

    인물 컷아웃 뒤에, 같은 배경 마스크 알파를 ``accent`` 색으로 채운 실루엣을
    깐다. 그림자는 사각형이 아니라 **인물 윤곽 그대로**다. 섀도 문법은 서로
    독립인 두 축으로 고른다 — **어디에 놓는가**(``shadow_mode``) 와 **무엇으로
    채우는가**(``shadow_fill``).

    Parameters
    ----------
    accent:
        섀도 색(HEX). 레퍼런스는 빨강 계열.
    offset:
        (dx, dy) 픽셀. 양수면 오른쪽/아래로 밀린다. ``shadow_mode="offset"``
        에서만 쓰인다.
    shadow_mode:
        ``"offset"`` — 실루엣을 ``offset`` 만큼 밀어 깐 오프셋 섀도(기본).
        ``"outline"`` — 실루엣을 ``outline_px`` 만큼 **원형 팽창**시켜 인물을
        균일하게 두르는 스티커/키라인 섀도. 이때 ``offset`` 은 무시된다
        (두 모드는 상호 배타 — 조합은 후속 과제).
    outline_px:
        ``"outline"`` 모드의 팽창 반경(px). 경계는 하드 에지다(블러 없음).
    shadow_fill:
        ``"solid"`` — 먹면(기본). ``"hatch"`` — 45° 평행선.
        ``"dots"`` — 45° 회전 정격자 도트. 패턴은 섀도 영역에서 정확히
        클리핑되고, 선·점 사이로는 종이(``paper``)가 비친다.
    fill_angle, hatch_spacing, hatch_width, dot_spacing, dot_radius:
        패턴 지오메트리. 격자 **위상**만 ``seed`` 로 정한다.
    paper:
        배경. HEX 문자열이면 단색, :class:`PIL.Image.Image` 면 그 **텍스처 위에**
        합성한다(크기가 다르면 캔버스 크기로 리샘플). ``make_crumpled_paper`` 로
        만든 갱지가 대표 사례다. ``None`` 이면 배경 투명(RGBA)으로 남긴다.
    pad:
        (좌, 상, 우, 하) 여백 픽셀. 인물이 원본 프레임을 꽉 채우면 섀도가
        캔버스 밖으로 잘려 안 보이므로, 여백을 줘서 실루엣이 종이 위에 놓인
        콜라주 조각처럼 보이게 한다. 기본값은 여백 없음(원본 해상도 유지).

    Returns
    -------
    PIL.Image.Image
        RGBA 합성 결과. 캔버스를 벗어나는 섀도는 그대로 클리핑된다.
    """
    if shadow_mode not in ("offset", "outline"):
        raise ValueError(f"알 수 없는 shadow_mode: {shadow_mode!r}")
    if shadow_fill not in ("solid", "hatch", "dots"):
        raise ValueError(f"알 수 없는 shadow_fill: {shadow_fill!r}")

    result = (
        mono
        if mono is not None
        else stylize_mono(image, seed=seed, tone=tone, **tone_kwargs)
    )
    cutout = result.image
    left, top, right, bottom = (int(value) for value in pad)
    width = result.width + left + right
    height = result.height + top + bottom

    cut_alpha = np.asarray(cutout.split()[3], dtype=np.float32) / 255.0
    cut_rgb = np.asarray(cutout.convert("RGB"), dtype=np.float32) / 255.0

    subject_alpha = np.zeros((height, width), dtype=np.float32)
    subject_rgb = np.zeros((height, width, 3), dtype=np.float32)
    placed = _paste_slices((height, width), cut_alpha.shape, left, top)
    if placed is not None:
        dst, src = placed
        subject_alpha[dst] = cut_alpha[src]
        subject_rgb[dst] = cut_rgb[src]

    shadow_alpha = np.zeros((height, width), dtype=np.float32)
    if shadow_mode == "offset":
        dx, dy = int(offset[0]), int(offset[1])
        shifted = _paste_slices((height, width), cut_alpha.shape, left + dx, top + dy)
        if shifted is not None:
            dst, src = shifted
            shadow_alpha[dst] = cut_alpha[src]
    else:
        shadow_alpha = _dilate_alpha(subject_alpha, float(outline_px))

    pattern = _fill_alpha(
        width,
        height,
        shadow_fill,
        seed=seed,
        angle=fill_angle,
        hatch_spacing=hatch_spacing,
        hatch_width=hatch_width,
        dot_spacing=dot_spacing,
        dot_radius=dot_radius,
    )
    if pattern is not None:
        shadow_alpha = shadow_alpha * pattern

    accent_rgb = np.asarray(_hex_to_rgb(accent), dtype=np.float32) / 255.0
    shadow_rgb = np.broadcast_to(accent_rgb, (height, width, 3))

    # 뒤 → 앞 순서로 premultiplied over 합성.
    if paper is None:
        out_rgb = np.zeros((height, width, 3), dtype=np.float32)
        out_alpha = np.zeros((height, width), dtype=np.float32)
    else:
        if isinstance(paper, Image.Image):
            sheet = paper.convert("RGB")
            if sheet.size != (width, height):
                sheet = sheet.resize((width, height), Image.LANCZOS)
            out_rgb = np.asarray(sheet, dtype=np.float32) / 255.0
        else:
            paper_rgb = np.asarray(_hex_to_rgb(paper), dtype=np.float32) / 255.0
            out_rgb = np.broadcast_to(paper_rgb, (height, width, 3)).astype(np.float32)
        out_alpha = np.ones((height, width), dtype=np.float32)

    for layer_rgb, layer_alpha in (
        (shadow_rgb, shadow_alpha),
        (subject_rgb, subject_alpha),
    ):
        a = np.clip(layer_alpha, 0.0, 1.0)[..., np.newaxis]
        out_rgb = layer_rgb * a + out_rgb * (1.0 - a)
        out_alpha = np.clip(layer_alpha, 0.0, 1.0) + out_alpha * (
            1.0 - np.clip(layer_alpha, 0.0, 1.0)
        )

    straight = out_rgb / np.maximum(out_alpha, 1e-6)[..., np.newaxis]
    rgba = np.concatenate(
        (
            np.clip(straight, 0.0, 1.0) * 255.0,
            np.clip(out_alpha, 0.0, 1.0)[..., np.newaxis] * 255.0,
        ),
        axis=2,
    )
    return Image.fromarray(np.rint(rgba).astype(np.uint8), mode="RGBA")


# --------------------------------------------------------------------------
# 스타일 2 — AM 망점 (halftone)
# --------------------------------------------------------------------------


def stylize_halftone(
    image: str | Path | Image.Image,
    *,
    seed: int,
    cell: float = 5.0,
    angle: float = 45.0,
    dot_gamma: float = 0.92,
    highlight_cut: float = 0.07,
    max_coverage: float = 1.35,
    min_radius: float = 0.22,
    tone: PrintTone | None = None,
    **tone_kwargs: float | bool | str,
) -> ScreenResult:
    """규칙 격자 AM 망점 스크린.

    ``angle`` 로 회전한 **정격자**의 각 셀에서 평균 잉크량을 재고, 그 값을
    점 면적으로 환산해 반지름을 정한다(면적 비례 = 인쇄 망점의 원리). 격자가
    규칙적이라 화면에서 "인쇄물"로 읽히고, 확률적 점묘처럼 노이즈로 뭉개지지
    않는다. 하이라이트(``highlight_cut`` 미만)는 점 반경 0 — 종이가 비어 있다.

    Parameters
    ----------
    cell:
        격자 간격(px). 4~7 권장. 작을수록 사진에 가깝고 점은 안 보인다.
    dot_gamma:
        면적 감마. <1 이면 중간톤이 진해진다.
    max_coverage:
        셀 대비 최대 점 면적 배율. 1.0 을 넘으면 어두운 곳에서 점이 붙어 먹면이 된다.
    """
    img = _open_image(image)
    print_tone = tone if tone is not None else build_print_tone(img, **tone_kwargs)  # type: ignore[arg-type]
    height, width = print_tone.height, print_tone.width
    rng = np.random.default_rng(seed)

    step = max(1.5, float(cell))
    # 셀 평균 근사 — 셀 크기의 가우시안으로 흐린 잉크 맵을 셀 중심에서 샘플.
    cell_ink = _blur_array(print_tone.ink, step * 0.34)

    ux, uy, vx, vy = _screen_axes(angle)
    corners = np.array(
        [[0.0, 0.0], [width, 0.0], [0.0, height], [width, height]], dtype=np.float64
    )
    us = corners[:, 0] * ux + corners[:, 1] * uy
    vs = corners[:, 0] * vx + corners[:, 1] * vy
    # 격자 위상만 seed 로 흔든다 — 격자 자체는 항상 규칙적이다.
    phase_u, phase_v = rng.uniform(0.0, 1.0, size=2)

    i0 = int(math.floor(us.min() / step)) - 1
    i1 = int(math.ceil(us.max() / step)) + 1
    j0 = int(math.floor(vs.min() / step)) - 1
    j1 = int(math.ceil(vs.max() / step)) + 1

    grid_i, grid_j = np.meshgrid(
        np.arange(i0, i1 + 1, dtype=np.float64),
        np.arange(j0, j1 + 1, dtype=np.float64),
        indexing="xy",
    )
    u = (grid_i.ravel() + phase_u) * step
    v = (grid_j.ravel() + phase_v) * step
    xs = u * ux + v * vx
    ys = u * uy + v * vy

    inside = (xs >= -step) & (xs <= width + step) & (ys >= -step) & (ys <= height + step)
    xs, ys = xs[inside], ys[inside]
    if xs.size == 0:
        return ScreenResult(width=width, height=height, style="halftone", seed=int(seed))

    amount = _sample_bilinear(cell_ink, xs, ys)
    cut = float(highlight_cut)
    coverage = np.clip((amount - cut) / max(1e-6, 1.0 - cut), 0.0, 1.0)
    coverage = np.power(coverage, max(1e-6, float(dot_gamma))) * float(max_coverage)

    radii = np.sqrt(np.clip(coverage, 0.0, float(max_coverage)) * step * step / math.pi)
    keep = radii >= float(min_radius)
    dots = tuple(
        Dot(float(x), float(y), float(r))
        for x, y, r in zip(xs[keep].tolist(), ys[keep].tolist(), radii[keep].tolist())
    )
    return ScreenResult(
        width=width,
        height=height,
        style="halftone",
        seed=int(seed),
        dots=dots,
        params={
            "cell": float(step),
            "angle": float(angle),
            "dot_gamma": float(dot_gamma),
            "highlight_cut": float(highlight_cut),
            "max_coverage": float(max_coverage),
        },
    )


# --------------------------------------------------------------------------
# 스타일 3 — 직선 평행선 스크린 (linescreen)
# --------------------------------------------------------------------------


def stylize_linescreen(
    image: str | Path | Image.Image,
    *,
    seed: int,
    spacing: float = 5.5,
    angle: float = 45.0,
    sample_step: float = 1.5,
    width_levels: int = 14,
    width_gamma: float = 1.0,
    highlight_cut: float = 0.07,
    max_coverage: float = 1.12,
    min_width: float = 0.18,
    tone: PrintTone | None = None,
    **tone_kwargs: float | bool | str,
) -> ScreenResult:
    """직선 평행선 스크린 — 굵기 변조로 계조를 만든다.

    ``angle`` 방향의 **완전한 직선**을 ``spacing`` 간격으로 깔고, 선을 따라가며
    국소 잉크량으로 굵기를 바꾼다(물결·warp 없음 — 그건 기계적 텍스처가 된다).
    굵기는 ``width_levels`` 단계로 양자화해 같은 단계가 이어지는 구간을 하나의
    ``<path>`` 로 합치므로, 시각적으로는 굵기가 변하는 연속선으로 읽힌다.
    어두운 영역은 굵기가 간격을 넘어 선이 붙으면서 검은 면이 된다.
    """
    img = _open_image(image)
    print_tone = tone if tone is not None else build_print_tone(img, **tone_kwargs)  # type: ignore[arg-type]
    height, width = print_tone.height, print_tone.width
    rng = np.random.default_rng(seed)

    gap = max(1.5, float(spacing))
    # 선 폭 방향 평균 — 한 선이 담당하는 띠의 평균 밀도를 쓴다.
    band_ink = _blur_array(print_tone.ink, gap * 0.30)

    ux, uy, vx, vy = _screen_axes(angle)
    corners = np.array(
        [[0.0, 0.0], [width, 0.0], [0.0, height], [width, height]], dtype=np.float64
    )
    us = corners[:, 0] * ux + corners[:, 1] * uy
    vs = corners[:, 0] * vx + corners[:, 1] * vy
    phase = float(rng.uniform(0.0, 1.0))

    step = max(0.5, float(sample_step))
    u_values = np.arange(us.min() - step, us.max() + step, step, dtype=np.float64)
    j0 = int(math.floor(vs.min() / gap)) - 1
    j1 = int(math.ceil(vs.max() / gap)) + 1

    levels = max(1, int(width_levels))
    cut = float(highlight_cut)
    half = step * 0.5 + 0.01
    strokes: list[Stroke] = []

    for j in range(j0, j1 + 1):
        v = (j + phase) * gap
        xs = u_values * ux + v * vx
        ys = u_values * uy + v * vy
        inside = (xs >= 0.0) & (xs <= width - 1.0) & (ys >= 0.0) & (ys <= height - 1.0)
        if not bool(inside.any()):
            continue

        amount = _sample_bilinear(band_ink, xs, ys)
        coverage = np.clip((amount - cut) / max(1e-6, 1.0 - cut), 0.0, 1.0)
        coverage = np.power(coverage, max(1e-6, float(width_gamma)))
        coverage = np.where(inside, coverage, 0.0) * float(max_coverage)

        level = np.rint(coverage * levels).astype(np.int32)
        level = np.clip(level, 0, int(round(float(max_coverage) * levels)))
        if not bool((level > 0).any()):
            continue

        boundaries = np.flatnonzero(np.diff(level)) + 1
        starts = np.concatenate(([0], boundaries))
        ends = np.concatenate((boundaries, [level.size]))
        for start, end in zip(starts.tolist(), ends.tolist()):
            value = int(level[start])
            if value <= 0:
                continue
            stroke_width = value / float(levels) * gap
            if stroke_width < float(min_width):
                continue
            u0 = u_values[start] - half
            u1 = u_values[end - 1] + half
            p0 = (u0 * ux + v * vx, u0 * uy + v * vy)
            p1 = (u1 * ux + v * vx, u1 * uy + v * vy)
            strokes.append(
                Stroke(
                    points=((float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1]))),
                    width=float(stroke_width),
                )
            )

    return ScreenResult(
        width=width,
        height=height,
        style="linescreen",
        seed=int(seed),
        strokes=tuple(strokes),
        params={
            "spacing": float(gap),
            "angle": float(angle),
            "sample_step": float(step),
            "width_levels": int(levels),
            "width_gamma": float(width_gamma),
            "highlight_cut": float(highlight_cut),
            "max_coverage": float(max_coverage),
        },
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m workers.engraving_stylizer",
        description="사진 → 인쇄 스크리닝 흑백 자산 (결정론, AI 생성 없음)",
    )
    parser.add_argument("image", help="입력 이미지 경로")
    parser.add_argument(
        "--style",
        choices=("mono", "mono_shadow", "halftone", "linescreen"),
        default="mono",
        help="스타일",
    )
    parser.add_argument("--seed", type=int, default=7, help="난수 시드 (스크린 위상)")
    parser.add_argument("--out-svg", default=None, help="SVG 출력 경로 (스크린 계열만)")
    parser.add_argument("--out-png", default=None, help="PNG 출력 경로")
    parser.add_argument("--png-width", type=int, default=1000, help="PNG 가로 픽셀")
    parser.add_argument(
        "--png-bg", default="white", help="PNG 배경색 ('none' 이면 투명)"
    )

    tone = parser.add_argument_group("톤")
    tone.add_argument("--denoise", type=int, default=0)
    tone.add_argument("--detail-strength", type=float, default=0.4)
    tone.add_argument("--detail-radius", type=float, default=0.0)
    tone.add_argument("--micro-strength", type=float, default=0.0)
    tone.add_argument("--shadow-percentile", type=float, default=3.0)
    tone.add_argument("--highlight-percentile", type=float, default=86.0)
    tone.add_argument("--midtone-gamma", type=float, default=1.8)
    tone.add_argument("--contrast", type=float, default=1.7)
    tone.add_argument("--pivot", type=float, default=0.52)
    tone.add_argument(
        "--keep-background",
        action="store_true",
        help="배경 억제(플러드필 마스크)를 끈다",
    )
    tone.add_argument("--bg-tolerance", type=float, default=45.0)
    tone.add_argument("--bg-seed-edges", default="top,left,right")
    tone.add_argument("--bg-side-fraction", type=float, default=0.62)
    tone.add_argument("--bg-erode", type=float, default=2.0)
    tone.add_argument("--bg-feather", type=float, default=1.0)

    shadow = parser.add_argument_group("mono_shadow")
    shadow.add_argument("--accent", default="#B03A2E", help="오프셋 섀도 색")
    shadow.add_argument("--shadow-dx", type=int, default=14)
    shadow.add_argument("--shadow-dy", type=int, default=18)
    shadow.add_argument(
        "--shadow-mode",
        choices=("offset", "outline"),
        default="offset",
        help="섀도 배치 — offset(밀어 깔기) / outline(원형 팽창 키라인)",
    )
    shadow.add_argument(
        "--outline-px", type=int, default=22, help="outline 모드 팽창 반경(px)"
    )
    shadow.add_argument(
        "--shadow-fill",
        choices=("solid", "hatch", "dots"),
        default="solid",
        help="섀도 채움 — solid(먹면) / hatch(45° 평행선) / dots(45° 격자 도트)",
    )
    shadow.add_argument(
        "--paper", default="#E8DFC9", help="배경 종이색 ('none' 이면 투명)"
    )
    shadow.add_argument(
        "--pad", default="0,0,0,0", help="여백 픽셀 '좌,상,우,하' (섀도가 잘릴 때)"
    )

    halftone = parser.add_argument_group("halftone")
    halftone.add_argument("--cell", type=float, default=5.0)
    halftone.add_argument("--dot-gamma", type=float, default=0.92)
    halftone.add_argument("--dot-max-coverage", type=float, default=1.35)

    linescreen = parser.add_argument_group("linescreen")
    linescreen.add_argument("--spacing", type=float, default=5.5)
    linescreen.add_argument("--sample-step", type=float, default=1.5)
    linescreen.add_argument("--width-levels", type=int, default=14)
    linescreen.add_argument("--width-gamma", type=float, default=1.0)
    linescreen.add_argument("--line-max-coverage", type=float, default=1.12)

    parser.add_argument("--angle", type=float, default=45.0, help="스크린 각도")
    parser.add_argument("--highlight-cut", type=float, default=0.07)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    image = Image.open(Path(args.image))
    tone = build_print_tone(
        image,
        denoise=args.denoise,
        detail_strength=args.detail_strength,
        detail_radius=args.detail_radius,
        micro_strength=args.micro_strength,
        shadow_percentile=args.shadow_percentile,
        highlight_percentile=args.highlight_percentile,
        midtone_gamma=args.midtone_gamma,
        contrast=args.contrast,
        pivot=args.pivot,
        remove_background=not args.keep_background,
        bg_tolerance=args.bg_tolerance,
        bg_seed_edges=args.bg_seed_edges,
        bg_side_fraction=args.bg_side_fraction,
        bg_erode=args.bg_erode,
        bg_feather=args.bg_feather,
    )
    background = None if str(args.png_bg).lower() == "none" else args.png_bg

    if args.style in ("mono", "mono_shadow"):
        mono = stylize_mono(image, seed=args.seed, tone=tone)
        print(
            f"style={args.style} seed={mono.seed} size={mono.width}x{mono.height} "
            f"levels={tone.levels[0]:.3f}/{tone.levels[1]:.3f} "
            f"ink_mean={float(tone.ink.mean()):.3f} "
            f"clean_white={float((tone.ink <= 0.0)[tone.foreground > 0.5].mean()):.3f}"
        )
        if args.out_svg:
            print("경고: mono 계열은 래스터 전용이라 SVG 를 쓰지 않습니다.", file=sys.stderr)
        if args.out_png:
            if args.style == "mono":
                path = mono.to_png(
                    args.out_png, out_width=args.png_width, background=background
                )
            else:
                paper = None if str(args.paper).lower() == "none" else args.paper
                pad_values = [int(part) for part in str(args.pad).split(",")]
                while len(pad_values) < 4:
                    pad_values.append(pad_values[-1])
                composed = compose_mono_shadow(
                    image,
                    accent=args.accent,
                    offset=(args.shadow_dx, args.shadow_dy),
                    shadow_mode=args.shadow_mode,
                    outline_px=args.outline_px,
                    shadow_fill=args.shadow_fill,
                    paper=paper,
                    pad=(pad_values[0], pad_values[1], pad_values[2], pad_values[3]),
                    seed=args.seed,
                    mono=mono,
                )
                target_w = int(args.png_width)
                if target_w and target_w != composed.width:
                    target_h = max(
                        1, int(round(composed.height * target_w / composed.width))
                    )
                    composed = composed.resize((target_w, target_h), Image.LANCZOS)
                out = Path(args.out_png)
                out.parent.mkdir(parents=True, exist_ok=True)
                composed.save(out)
                path = out
            print(f"png={path} bytes={path.stat().st_size}")
        elif not args.out_svg:
            print("경고: --out-png 가 없어 결과를 저장하지 않았습니다.", file=sys.stderr)
        return 0

    if args.style == "halftone":
        result = stylize_halftone(
            image,
            seed=args.seed,
            cell=args.cell,
            angle=args.angle,
            dot_gamma=args.dot_gamma,
            highlight_cut=args.highlight_cut,
            max_coverage=args.dot_max_coverage,
            tone=tone,
        )
    else:
        result = stylize_linescreen(
            image,
            seed=args.seed,
            spacing=args.spacing,
            angle=args.angle,
            sample_step=args.sample_step,
            width_levels=args.width_levels,
            width_gamma=args.width_gamma,
            highlight_cut=args.highlight_cut,
            max_coverage=args.line_max_coverage,
            tone=tone,
        )

    print(
        f"style={result.style} seed={result.seed} "
        f"size={result.width}x{result.height} "
        f"dots={len(result.dots)} strokes={len(result.strokes)}"
    )

    if args.out_svg:
        path = result.write_svg(args.out_svg)
        print(f"svg={path} bytes={path.stat().st_size}")
    if args.out_png:
        path = result.to_png(
            args.out_png, out_width=args.png_width, background=background
        )
        print(f"png={path} bytes={path.stat().st_size}")
    if not args.out_svg and not args.out_png:
        print("경고: --out-svg / --out-png 가 없어 결과를 저장하지 않았습니다.", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
