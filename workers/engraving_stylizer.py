"""판화(engraving) 초상 스타일라이저 — Phase 1 PoC.

실존 인물의 공식/퍼블릭도메인 사진을 **결정론 알고리즘**으로 흑백 판화풍
**벡터 SVG** 로 변환한다. AI 이미지 생성은 사용하지 않는다 (GOAL G4-10).

두 가지 스타일을 제공한다.

* ``stylize_stipple``   — 점묘(stipple). 톤 맵에서 어두울수록 촘촘하고 굵은 점을
  찍는다. SVG ``<circle>`` 목록으로 나온다.
* ``stylize_engraving`` — 클래식 line engraving. 평행 물결 스캔라인이 명도에 따라
  굵기·진폭을 바꾸고, 어두운 영역에는 교차 해칭(크로스해치) 한 겹을 덧댄다.
  SVG ``<path>`` 목록으로 나온다.

두 함수 모두 :class:`EngravingResult` 를 돌려주며, 결과 객체는 **같은 지오메트리**
에서 SVG 문자열(:meth:`EngravingResult.to_svg`)과 PIL 프리뷰 PNG
(:meth:`EngravingResult.to_png`)를 만든다. 외부 SVG 래스터라이저에 의존하지 않는다.

난수는 전부 ``seed`` 로 시작한 :class:`numpy.random.Generator` 에서만 뽑는다.
같은 입력 + 같은 seed + 같은 파라미터 → 바이트 단위로 같은 SVG.

CLI::

    python -m workers.engraving_stylizer <img> --style stipple \
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
from typing import Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# --------------------------------------------------------------------------
# 상수
# --------------------------------------------------------------------------

#: 잉크 색 — 판화 자산은 단일 잉크색만 사용한다 (배경은 투명).
INK_COLOR: str = "#1C1A17"

#: SVG 좌표 반올림 자릿수 (파일 크기 ↔ 정밀도 절충).
_COORD_NDIGITS: int = 1


# --------------------------------------------------------------------------
# 지오메트리 데이터 구조
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Dot:
    """점묘 한 점. 좌표계는 원본 픽셀."""

    x: float
    y: float
    r: float


@dataclass(frozen=True)
class Stroke:
    """해칭 선 한 획. ``points`` 는 폴리라인, ``width`` 는 획 두께(px)."""

    points: tuple[tuple[float, float], ...]
    width: float


@dataclass
class ToneMap:
    """스타일라이저 공통 전처리 결과.

    Attributes
    ----------
    darkness:
        0(밝음)~1(어두움) 실수 배열. 배경 억제 마스크가 이미 곱해져 있다.
    edges:
        0~1 로 정규화한 경계 세기(소벨 근사). 이목구비 강조에 쓴다.
    foreground:
        0(배경)~1(피사체) 마스크. 가장자리 플러드필로 구한다.
    """

    darkness: np.ndarray
    edges: np.ndarray
    foreground: np.ndarray

    @property
    def height(self) -> int:
        return int(self.darkness.shape[0])

    @property
    def width(self) -> int:
        return int(self.darkness.shape[1])


@dataclass
class EngravingResult:
    """스타일라이즈 산출물 — SVG 와 PNG 프리뷰의 단일 출처."""

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
            f"<title>engraving-stylizer {self.style} seed={self.seed}</title>",
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
                'stroke-linecap="round" stroke-linejoin="round">'
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
        supersample: int = 2,
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
                draw.line(pts, fill=ink, width=width, joint="curve")

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


def _simplify_polyline(
    points: Sequence[tuple[float, float]], epsilon: float
) -> list[tuple[float, float]]:
    """Douglas–Peucker 단순화 (스택 기반, 재귀 없음)."""
    n = len(points)
    if n <= 2 or epsilon <= 0.0:
        return list(points)

    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack: list[tuple[int, int]] = [(0, n - 1)]
    while stack:
        start, end = stack.pop()
        if end <= start + 1:
            continue
        x0, y0 = points[start]
        x1, y1 = points[end]
        dx, dy = x1 - x0, y1 - y0
        norm = math.hypot(dx, dy)
        best_idx = -1
        best_dist = 0.0
        for i in range(start + 1, end):
            px, py = points[i]
            if norm == 0.0:
                dist = math.hypot(px - x0, py - y0)
            else:
                dist = abs(dy * (px - x0) - dx * (py - y0)) / norm
            if dist > best_dist:
                best_dist = dist
                best_idx = i
        if best_idx >= 0 and best_dist > epsilon:
            keep[best_idx] = True
            stack.append((start, best_idx))
            stack.append((best_idx, end))
    return [points[i] for i in range(n) if keep[i]]


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
    work_dim: int = 320,
    seed_edges: str = "top,left,right",
    side_fraction: float = 0.62,
    edge_stop: float = 26.0,
    opening: int = 3,
    keep_largest: bool = True,
    dilate: int = 1,
    feather: float = 2.5,
) -> np.ndarray:
    """가장자리 플러드필로 전경(피사체) 마스크를 구한다.

    테두리 픽셀을 씨앗으로 삼아, 각 씨앗의 **원래 색**과의 색거리가 ``tolerance``
    미만인 4-연결 성분을 배경으로 본다. 인물 사진은 보통 몸통이 아래 테두리에
    닿으므로 기본값은 아래 테두리를 씨앗에서 제외하고, 좌우 테두리는 위쪽
    ``side_fraction`` 만 쓴다. ``keep_largest`` 면 플러드필이 놓친 배경 잔재
    (떨어진 작은 섬)를 최대 연결성분만 남겨 정리한다.

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
        # 배경을 조금 깎아 피사체 실루엣이 잘려 나가지 않게 한다.
        fg_img = fg_img.filter(ImageFilter.MaxFilter(size=2 * int(dilate) + 1))
    mask_img = fg_img.resize((full_w, full_h), Image.BILINEAR)
    if feather > 0.0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=float(feather)))
    return np.asarray(mask_img, dtype=np.float32) / 255.0


# --------------------------------------------------------------------------
# 톤 맵
# --------------------------------------------------------------------------


def build_tone_map(
    image: Image.Image,
    *,
    gamma: float = 1.0,
    contrast: float = 1.45,
    black_point: float = 0.06,
    white_point: float = 0.96,
    detail_strength: float = 1.1,
    detail_radius: float = 4.0,
    shadow_ceiling: float = 0.88,
    remove_background: bool = True,
    bg_tolerance: float = 45.0,
    bg_seed_edges: str = "top,left,right",
    bg_side_fraction: float = 0.62,
) -> ToneMap:
    """사진 → 판화용 톤 맵(어두움 0~1) + 경계 세기 + 전경 마스크.

    언샤프 마스크로 국소 대비를 올려 이목구비가 살아나게 한 뒤, 레벨/감마로
    계조를 판화용으로 눌러 준다.
    """
    rgb_img = image.convert("RGB")
    gray_img = rgb_img.convert("L")
    gray = np.asarray(gray_img, dtype=np.float32) / 255.0

    if detail_strength > 0.0 and detail_radius > 0.0:
        blurred = np.asarray(
            gray_img.filter(ImageFilter.GaussianBlur(radius=float(detail_radius))),
            dtype=np.float32,
        ) / 255.0
        gray = np.clip(gray + detail_strength * (gray - blurred), 0.0, 1.0)

    span = max(1e-6, float(white_point) - float(black_point))
    leveled = np.clip((gray - float(black_point)) / span, 0.0, 1.0)
    centered = np.clip((leveled - 0.5) * float(contrast) + 0.5, 0.0, 1.0)
    toned = np.power(centered, 1.0 / max(1e-6, float(gamma)))

    # 그림자 상한 — 어두운 덩어리(정장 등)가 완전히 뭉개져 "먹칠"이 되는 것을 막고
    # 최대 밀도에서도 종이(여백)가 조금 비치게 한다.
    darkness = (1.0 - toned) * float(shadow_ceiling)

    # 소벨 근사 경계 세기 — 이목구비/윤곽 강조용.
    smooth = np.asarray(
        gray_img.filter(ImageFilter.GaussianBlur(radius=1.2)), dtype=np.float32
    ) / 255.0
    gy, gx = np.gradient(smooth)
    magnitude = np.hypot(gx, gy)
    peak = float(np.percentile(magnitude, 99.0)) or 1.0
    edges = np.clip(magnitude / peak, 0.0, 1.0)

    if remove_background:
        foreground = background_mask(
            rgb_img,
            tolerance=bg_tolerance,
            seed_edges=bg_seed_edges,
            side_fraction=bg_side_fraction,
        )
    else:
        foreground = np.ones_like(darkness, dtype=np.float32)

    darkness = np.clip(darkness * foreground, 0.0, 1.0).astype(np.float32)
    edges = (edges * foreground).astype(np.float32)
    return ToneMap(darkness=darkness, edges=edges, foreground=foreground)


def _open_image(source: str | Path | Image.Image) -> Image.Image:
    if isinstance(source, Image.Image):
        return source
    return Image.open(Path(source))


# --------------------------------------------------------------------------
# 스타일 1 — 점묘 (stipple)
# --------------------------------------------------------------------------


def stylize_stipple(
    image: str | Path | Image.Image,
    *,
    seed: int,
    spacing: float = 3.0,
    jitter: float = 0.85,
    density_gamma: float = 0.9,
    min_radius: float = 0.35,
    max_radius: float = 1.35,
    radius_gamma: float = 0.9,
    threshold: float = 0.06,
    edge_boost: float = 0.7,
    tone: ToneMap | None = None,
    **tone_kwargs: float | bool | str,
) -> EngravingResult:
    """점묘 스타일 — 어두울수록 촘촘하고 굵은 점.

    지터드 그리드 위에 후보점을 깔고, 각 후보를 국소 어두움 ``d`` 에 비례한
    확률 ``d**density_gamma`` 로 채택한다. 채택된 점의 반지름도 ``d`` 에
    비례하므로 밀도와 굵기가 함께 계조를 만든다. 경계 세기(``edge_boost``)를
    어두움에 더해 눈·입술·머리카락 윤곽에 점이 몰리게 한다.

    Parameters
    ----------
    seed:
        지터·채택 난수의 유일한 출처. 같은 seed → 같은 결과.
    spacing:
        후보 그리드 간격(px). 작을수록 촘촘하고 무거워진다.
    threshold:
        이 어두움 미만은 아예 점을 찍지 않는다(하이라이트 보존).
    """
    img = _open_image(image)
    tone_map = tone if tone is not None else build_tone_map(img, **tone_kwargs)  # type: ignore[arg-type]
    height, width = tone_map.height, tone_map.width
    rng = np.random.default_rng(seed)

    step = max(0.5, float(spacing))
    cols = max(1, int(width / step))
    rows = max(1, int(height / step))
    gx, gy = np.meshgrid(
        (np.arange(cols) + 0.5) * step, (np.arange(rows) + 0.5) * step
    )
    xs = gx.ravel()
    ys = gy.ravel()

    amount = float(jitter) * step * 0.5
    xs = xs + rng.uniform(-amount, amount, size=xs.shape)
    ys = ys + rng.uniform(-amount, amount, size=ys.shape)
    xs = np.clip(xs, 0.0, width - 1.0)
    ys = np.clip(ys, 0.0, height - 1.0)

    darkness = _sample_bilinear(tone_map.darkness, xs, ys)
    edges = _sample_bilinear(tone_map.edges, xs, ys)
    weight = np.clip(darkness + float(edge_boost) * edges * (0.35 + darkness), 0.0, 1.0)

    alive = weight >= float(threshold)
    probability = np.power(weight, max(1e-6, float(density_gamma)))
    accepted = alive & (rng.random(size=weight.shape) < probability)

    kept_x = xs[accepted]
    kept_y = ys[accepted]
    kept_w = weight[accepted]
    radii = float(min_radius) + (float(max_radius) - float(min_radius)) * np.power(
        kept_w, max(1e-6, float(radius_gamma))
    )

    dots = tuple(
        Dot(float(x), float(y), float(r))
        for x, y, r in zip(kept_x.tolist(), kept_y.tolist(), radii.tolist())
    )
    return EngravingResult(
        width=width,
        height=height,
        style="stipple",
        seed=int(seed),
        dots=dots,
        params={
            "spacing": float(spacing),
            "jitter": float(jitter),
            "density_gamma": float(density_gamma),
            "min_radius": float(min_radius),
            "max_radius": float(max_radius),
            "edge_boost": float(edge_boost),
        },
    )


# --------------------------------------------------------------------------
# 스타일 2 — 라인 인그레이빙 (line engraving + cross-hatch)
# --------------------------------------------------------------------------


def _hatch_pass(
    tone_map: ToneMap,
    *,
    angle_deg: float,
    spacing: float,
    wave_length: float,
    wave_amp: float,
    min_width: float,
    max_width: float,
    width_levels: int,
    threshold: float,
    weight_gamma: float,
    flow_strength: float,
    sample_step: float,
    simplify_eps: float,
    edge_boost: float,
    smooth_window: int,
    rng: np.random.Generator,
    flow: np.ndarray | None,
) -> list[Stroke]:
    """한 방향(``angle_deg``)의 물결 해칭 한 겹을 만든다.

    회전 좌표계에서 ``spacing`` 간격의 평행선을 긋고, 선을 따라가며 국소
    어두움으로 (a) 획 두께, (b) 물결 진폭을 변조한다. 두께는 ``width_levels``
    단계로 양자화해 같은 단계가 이어지는 구간을 하나의 ``<path>`` 로 잇는다.
    """
    height, width = tone_map.height, tone_map.width
    theta = math.radians(angle_deg)
    dir_x, dir_y = math.cos(theta), math.sin(theta)
    perp_x, perp_y = -dir_y, dir_x
    cx, cy = width / 2.0, height / 2.0

    diagonal = math.hypot(width, height)
    half = diagonal / 2.0 + spacing
    line_count = int(2 * half / spacing) + 1
    samples = max(2, int(diagonal / max(0.5, sample_step)))
    u_values = np.linspace(-half, half, samples)

    strokes: list[Stroke] = []
    levels = max(1, int(width_levels))
    phases = rng.uniform(0.0, 2.0 * math.pi, size=line_count)

    for index in range(line_count):
        offset = -half + index * spacing
        base_x = cx + perp_x * offset + dir_x * u_values
        base_y = cy + perp_y * offset + dir_y * u_values

        inside = (
            (base_x >= -2.0)
            & (base_x <= width + 2.0)
            & (base_y >= -2.0)
            & (base_y <= height + 2.0)
        )
        if not bool(inside.any()):
            continue

        # 흐름 왜곡 — 저주파 명암 기울기를 따라 선이 얼굴을 감싸며 휜다.
        if flow is not None and flow_strength > 0.0:
            warp = (_sample_bilinear(flow, base_x, base_y) - 0.5) * 2.0
            shift = warp * float(flow_strength) * spacing
            base_x = base_x + perp_x * shift
            base_y = base_y + perp_y * shift

        darkness = _sample_bilinear(tone_map.darkness, base_x, base_y)
        edges = _sample_bilinear(tone_map.edges, base_x, base_y)
        weight = np.clip(
            darkness + float(edge_boost) * edges * (0.3 + darkness), 0.0, 1.0
        )
        weight = np.power(weight, max(1e-6, float(weight_gamma)))
        weight = np.where(inside, weight, 0.0)
        # 선 방향 저역통과 — 두께가 픽셀 잡음마다 튀면 획이 잘게 끊겨
        # "점선 뭉치"가 된다. 완만하게 만들어야 획이 길게 이어진다.
        if smooth_window > 1:
            kernel = np.ones(int(smooth_window), dtype=np.float32)
            kernel /= kernel.sum()
            weight = np.convolve(weight, kernel, mode="same")

        amp = float(wave_amp) * spacing * (0.35 + 0.65 * weight)
        wave = np.sin(2.0 * math.pi * u_values / max(1.0, wave_length) + phases[index])
        px = base_x + perp_x * amp * wave
        py = base_y + perp_y * amp * wave

        level = np.where(
            weight < float(threshold),
            0,
            np.clip(
                np.ceil((weight - float(threshold)) / (1.0 - float(threshold)) * levels),
                1,
                levels,
            ),
        ).astype(np.int32)

        if not bool((level > 0).any()):
            continue

        # 한두 샘플짜리 계단 튐 제거 — 획을 더 길게 잇는다.
        if level.size >= 3:
            stacked = np.stack((level[:-2], level[1:-1], level[2:]))
            level[1:-1] = np.median(stacked, axis=0).astype(np.int32)

        boundaries = np.flatnonzero(np.diff(level)) + 1
        starts = np.concatenate(([0], boundaries))
        ends = np.concatenate((boundaries, [level.size]))
        for start, end in zip(starts.tolist(), ends.tolist()):
            value = int(level[start])
            if value <= 0 or end - start < 2:
                continue
            lo = max(0, start - 1)
            hi = min(level.size, end + 1)
            points = list(zip(px[lo:hi].tolist(), py[lo:hi].tolist()))
            points = _simplify_polyline(points, simplify_eps)
            if len(points) < 2:
                continue
            stroke_width = float(min_width) + (float(max_width) - float(min_width)) * (
                (value - 0.5) / levels
            )
            strokes.append(Stroke(points=tuple(points), width=stroke_width))

    return strokes


def stylize_engraving(
    image: str | Path | Image.Image,
    *,
    seed: int,
    line_spacing: float = 6.0,
    angle: float = 12.0,
    wave_length: float = 26.0,
    wave_amp: float = 0.35,
    min_width: float = 0.45,
    max_width: float = 3.2,
    width_levels: int = 6,
    threshold: float = 0.1,
    weight_gamma: float = 0.85,
    flow_strength: float = 0.55,
    cross_hatch: bool = True,
    cross_angle_offset: float = 78.0,
    cross_threshold: float = 0.52,
    cross_spacing_factor: float = 1.35,
    edge_boost: float = 0.75,
    sample_step: float = 1.5,
    simplify_eps: float = 0.12,
    smooth_window: int = 7,
    tone: ToneMap | None = None,
    **tone_kwargs: float | bool | str,
) -> EngravingResult:
    """클래식 라인 인그레이빙 — 물결 스캔라인 + 어두운 영역 교차 해칭.

    ``line_spacing`` 간격의 평행선이 사진을 훑으며, 국소 어두움에 따라 획
    두께와 물결 진폭이 동시에 커진다(밝은 곳은 가늘고 잔잔, 어두운 곳은
    굵고 크게 출렁). 저주파 명암 기울기로 선을 살짝 휘게 해(``flow_strength``)
    평면 줄무늬가 아니라 얼굴을 감싸는 뷰린(burin) 느낌을 낸다. 어두움이
    ``cross_threshold`` 를 넘는 영역에는 ``cross_angle_offset`` 만큼 돌린
    둘째 겹을 덧대 인탈리오식 크로스해치를 만든다.
    """
    img = _open_image(image)
    tone_map = tone if tone is not None else build_tone_map(img, **tone_kwargs)  # type: ignore[arg-type]
    rng = np.random.default_rng(seed)

    flow_img = Image.fromarray(
        (np.clip(tone_map.darkness, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L"
    ).filter(ImageFilter.GaussianBlur(radius=18.0))
    flow = np.asarray(flow_img, dtype=np.float32) / 255.0

    strokes = _hatch_pass(
        tone_map,
        angle_deg=angle,
        spacing=float(line_spacing),
        wave_length=wave_length,
        wave_amp=wave_amp,
        min_width=min_width,
        max_width=max_width,
        width_levels=width_levels,
        threshold=threshold,
        weight_gamma=weight_gamma,
        flow_strength=flow_strength,
        sample_step=sample_step,
        simplify_eps=simplify_eps,
        edge_boost=edge_boost,
        smooth_window=smooth_window,
        rng=rng,
        flow=flow,
    )

    if cross_hatch:
        strokes.extend(
            _hatch_pass(
                tone_map,
                angle_deg=angle + cross_angle_offset,
                spacing=float(line_spacing) * float(cross_spacing_factor),
                wave_length=wave_length * 1.3,
                wave_amp=wave_amp * 0.6,
                min_width=min_width,
                max_width=max_width * 0.62,
                width_levels=max(2, width_levels - 2),
                threshold=cross_threshold,
                weight_gamma=weight_gamma,
                flow_strength=flow_strength * 0.5,
                sample_step=sample_step,
                simplify_eps=simplify_eps,
                edge_boost=edge_boost * 0.5,
                smooth_window=smooth_window,
                rng=rng,
                flow=flow,
            )
        )

    return EngravingResult(
        width=tone_map.width,
        height=tone_map.height,
        style="engraving",
        seed=int(seed),
        strokes=tuple(strokes),
        params={
            "line_spacing": float(line_spacing),
            "angle": float(angle),
            "wave_length": float(wave_length),
            "wave_amp": float(wave_amp),
            "min_width": float(min_width),
            "max_width": float(max_width),
            "cross_hatch": int(bool(cross_hatch)),
        },
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m workers.engraving_stylizer",
        description="사진 → 흑백 판화풍 SVG (결정론, AI 생성 없음)",
    )
    parser.add_argument("image", help="입력 이미지 경로")
    parser.add_argument(
        "--style", choices=("stipple", "engraving"), default="stipple", help="스타일"
    )
    parser.add_argument("--seed", type=int, default=7, help="난수 시드 (결정론)")
    parser.add_argument("--out-svg", default=None, help="SVG 출력 경로")
    parser.add_argument("--out-png", default=None, help="PNG 프리뷰 출력 경로")
    parser.add_argument(
        "--png-width", type=int, default=1000, help="PNG 프리뷰 가로 픽셀"
    )
    parser.add_argument(
        "--png-bg", default="white", help="PNG 배경색 ('none' 이면 투명)"
    )

    tone = parser.add_argument_group("톤 맵")
    tone.add_argument("--gamma", type=float, default=1.0)
    tone.add_argument("--contrast", type=float, default=1.45)
    tone.add_argument("--black-point", type=float, default=0.06)
    tone.add_argument("--white-point", type=float, default=0.96)
    tone.add_argument("--detail-strength", type=float, default=1.1)
    tone.add_argument("--detail-radius", type=float, default=4.0)
    tone.add_argument("--shadow-ceiling", type=float, default=0.88)
    tone.add_argument(
        "--keep-background",
        action="store_true",
        help="배경 억제(플러드필 마스크)를 끈다",
    )
    tone.add_argument("--bg-tolerance", type=float, default=45.0)
    tone.add_argument("--bg-seed-edges", default="top,left,right")
    tone.add_argument("--bg-side-fraction", type=float, default=0.62)

    stipple = parser.add_argument_group("stipple")
    stipple.add_argument("--spacing", type=float, default=3.0)
    stipple.add_argument("--jitter", type=float, default=0.85)
    stipple.add_argument("--density-gamma", type=float, default=0.9)
    stipple.add_argument("--min-radius", type=float, default=0.35)
    stipple.add_argument("--max-radius", type=float, default=1.35)
    stipple.add_argument("--dot-threshold", type=float, default=0.06)

    engraving = parser.add_argument_group("engraving")
    engraving.add_argument("--line-spacing", type=float, default=6.0)
    engraving.add_argument("--angle", type=float, default=12.0)
    engraving.add_argument("--wave-length", type=float, default=26.0)
    engraving.add_argument("--wave-amp", type=float, default=0.35)
    engraving.add_argument("--min-width", type=float, default=0.45)
    engraving.add_argument("--max-width", type=float, default=3.2)
    engraving.add_argument("--width-levels", type=int, default=6)
    engraving.add_argument("--line-threshold", type=float, default=0.1)
    engraving.add_argument("--weight-gamma", type=float, default=0.85)
    engraving.add_argument("--flow-strength", type=float, default=0.55)
    engraving.add_argument("--no-cross-hatch", action="store_true")
    engraving.add_argument("--cross-threshold", type=float, default=0.52)
    engraving.add_argument("--cross-angle-offset", type=float, default=78.0)
    engraving.add_argument("--edge-boost", type=float, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    image = Image.open(Path(args.image))
    tone_map = build_tone_map(
        image,
        gamma=args.gamma,
        contrast=args.contrast,
        black_point=args.black_point,
        white_point=args.white_point,
        detail_strength=args.detail_strength,
        detail_radius=args.detail_radius,
        shadow_ceiling=args.shadow_ceiling,
        remove_background=not args.keep_background,
        bg_tolerance=args.bg_tolerance,
        bg_seed_edges=args.bg_seed_edges,
        bg_side_fraction=args.bg_side_fraction,
    )

    if args.style == "stipple":
        result = stylize_stipple(
            image,
            seed=args.seed,
            spacing=args.spacing,
            jitter=args.jitter,
            density_gamma=args.density_gamma,
            min_radius=args.min_radius,
            max_radius=args.max_radius,
            threshold=args.dot_threshold,
            tone=tone_map,
            **({"edge_boost": args.edge_boost} if args.edge_boost is not None else {}),
        )
    else:
        result = stylize_engraving(
            image,
            seed=args.seed,
            line_spacing=args.line_spacing,
            angle=args.angle,
            wave_length=args.wave_length,
            wave_amp=args.wave_amp,
            min_width=args.min_width,
            max_width=args.max_width,
            width_levels=args.width_levels,
            threshold=args.line_threshold,
            weight_gamma=args.weight_gamma,
            flow_strength=args.flow_strength,
            cross_hatch=not args.no_cross_hatch,
            cross_threshold=args.cross_threshold,
            cross_angle_offset=args.cross_angle_offset,
            tone=tone_map,
            **({"edge_boost": args.edge_boost} if args.edge_boost is not None else {}),
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
        background = None if str(args.png_bg).lower() == "none" else args.png_bg
        path = result.to_png(
            args.out_png, out_width=args.png_width, background=background
        )
        print(f"png={path} bytes={path.stat().st_size}")
    if not args.out_svg and not args.out_png:
        print("경고: --out-svg / --out-png 가 없어 결과를 저장하지 않았습니다.", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
