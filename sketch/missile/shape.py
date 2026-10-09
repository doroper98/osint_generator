"""궤적 모양(개념)·이미지 준비 — 그리기 모듈 밖의 수식·형변환(test_sketch_no_literals b 대상 아님)."""

from __future__ import annotations

from pathlib import Path

import cairo
import numpy as np
from PIL import Image

LOFT_K = 4.0          # 4u(1 − u): u = 0.5 에서 1 이 되는 포물선
BYTE = 255.0


def loft(u: np.ndarray) -> np.ndarray:
    """고각 궤적 모양(개념): 거리 비율 u → 고도 비율. 정점 부근이 완만한 포물선. 정점 고도는 발표값을 곱한다."""
    return LOFT_K * u * (1 - u)


def card_surface(path: Path, crop: tuple[float, float, float, float], rotate_deg: float) -> cairo.ImageSurface:
    """도해 이미지 → cairo 표면(비율 자르기 → 빈 테두리 제거 → 회전). 파일이 없으면 오류(대체 문구로 넘어가지 않는다, P6)."""
    if not path.is_file():
        raise FileNotFoundError(f"카드 이미지 없음: {path}")
    im = Image.open(path).convert("RGBA")
    x0, y0, x1, y1 = crop
    im = im.crop((int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1)))
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    if rotate_deg:
        im = im.rotate(rotate_deg, expand=True)
    arr = np.asarray(im, dtype=np.float32)
    al = arr[:, :, 3:4] / BYTE
    pm = np.concatenate([arr[:, :, [2, 1, 0]] * al, arr[:, :, 3:4]], axis=2).round().astype(np.uint8)   # cairo ARGB32 = 미리 곱한 BGRA
    return cairo.ImageSurface.create_for_data(bytearray(pm.tobytes()), cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
