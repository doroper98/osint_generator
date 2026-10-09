"""스케치 프레임 루프 → mp4 + 컨택트 시트 + `out/sketch_provenance.json`(D-0140 §3, 15 P5).

종류별 장면은 `Scene` 계약(`frame(t) -> BGRA 바이트`, 크기 = 출력 프로파일 장치 px)만 지키면 된다.
출력 프로파일 = engine.style.output_profile(`--res` 기본 trial = 480p, 사용자 전달본 final = 720p).
인코딩 설정(crf·preset)도 그 프로파일 값이다(config engine.output — 코드에 다시 적지 않는다, P3).
"""

from __future__ import annotations

import hashlib
import subprocess
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from engine.sheet import grid
from engine.style import FPS, H_OUT, W_OUT, Output
from engine.timebase import smooth
from rules import rules_hash
from sketch.common.spec import RenderRecord, SketchProvenance

PROVENANCE_FILE = "sketch_provenance.json"
BGRA = 4            # 프레임 바이트 채널 수(cairo RGB24/ARGB32 = B·G·R·X)
SHEET_COLS = 2


class Scene(Protocol):
    out: Output

    def frame(self, t: float) -> bytes:
        """시각 t 의 한 프레임(BGRA, out.width × out.height)."""


class CrossfadeScene:
    """두 장면 잇기(D-0143 §4) — t_cut 전에는 앞 장면 a(시각 a_time(t)), [t_cut, t_cut + t_x] 동안 a 의 t_cut 정지 화면과
    뒤 장면 b 를 smooth 비율로 섞고, 그 뒤는 b. 전체에 열림·닫힘 검정. 두 장면은 같은 출력 프로파일이어야 한다."""

    def __init__(self, a: Scene, b: Scene, a_time: Callable[[float], float], t_cut: float, t_x: float,
                 duration_sec: float, fade_open: float, fade_close: float) -> None:
        if (a.out.width, a.out.height) != (b.out.width, b.out.height):
            raise ValueError(f"CrossfadeScene 출력 크기 다름 {a.out.name} ≠ {b.out.name}")
        self.a, self.b, self.out = a, b, b.out
        self.a_time, self.t_cut, self.t_x = a_time, t_cut, t_x
        self.duration, self.fade_open, self.fade_close = duration_sec, fade_open, fade_close
        self._held: np.ndarray | None = None

    def _arr(self, buf: bytes) -> np.ndarray:
        return np.frombuffer(bytes(buf), np.uint8).reshape(self.out.height, self.out.width, BGRA)

    def frame(self, t: float) -> bytes:
        if t < self.t_cut:
            g = self._arr(self.a.frame(self.a_time(t)))
        else:
            g = self._arr(self.b.frame(t))
            if t < self.t_cut + self.t_x:
                if self._held is None:
                    self._held = self._arr(self.a.frame(self.a_time(self.t_cut))).astype(np.float32)
                k = smooth((t - self.t_cut) / self.t_x)
                g = (self._held * (1 - k) + g.astype(np.float32) * k).astype(np.uint8)
        fa = 1 - min(smooth(t / self.fade_open), smooth((self.duration - t) / self.fade_close))
        return (g.astype(np.float32) * (1 - fa)).astype(np.uint8).tobytes()


def sha1_file(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def to_image(buf: bytes, out: Output) -> Image.Image:
    return Image.frombuffer("RGBA", (out.width, out.height), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB")


def write_frames(scene: Scene, times: Sequence[float], out_dir: Path, stem: str) -> list[Path]:
    """정지 화면(`--frames`) — 초마다 PNG 한 장."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for t in times:
        p = out_dir / f"{stem}_{t:05.1f}.png"
        to_image(scene.frame(t), scene.out).save(p)
        paths.append(p)
    return paths


def render_video(scene: Scene, duration_sec: float, sheet_times: Sequence[float], out_dir: Path, stem: str
                 ) -> tuple[Path, Path, RenderRecord]:
    """전편 → `{stem}.mp4` + `{stem}_sheet.jpg`. 시트 칸 = 설계 크기(W_OUT×H_OUT)로 줄인 프레임."""
    out = scene.out
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4, sheet = out_dir / f"{stem}.mp4", out_dir / f"{stem}_sheet.jpg"
    t_start = time.monotonic()
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{out.width}x{out.height}",
         "-r", str(out.fps), "-i", "-", "-c:v", "libx264", "-crf", str(out.crf), "-preset", out.preset,
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE)
    assert ff.stdin is not None
    n = int(duration_sec * FPS)
    half = 1 / (2 * FPS)
    cells = []
    for i in range(n):
        t = i / FPS
        buf = scene.frame(t)
        ff.stdin.write(bytes(buf))
        if any(abs(t - s) < half for s in sheet_times):
            cells.append((to_image(buf, out).resize((W_OUT, H_OUT)), f"t={t:.1f}s"))
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"ffmpeg 실패(종료 코드 {ff.returncode}) — {mp4}")
    missing = len(sheet_times) - len(cells)
    if missing:
        raise RuntimeError(f"시트 시각 {missing}개가 영상 길이 {duration_sec}s 밖이다: {list(sheet_times)}")
    grid(cells, SHEET_COLS, sheet, cell=(W_OUT, H_OUT))
    rec = RenderRecord(profile=out.name, frames=n, duration_sec=n / FPS, elapsed_sec=round(time.monotonic() - t_start, 1))
    return mp4, sheet, rec


def write_provenance(prov: SketchProvenance, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / PROVENANCE_FILE
    p.write_text(prov.model_dump_json(indent=2), encoding="utf-8")
    return p


def base_provenance(kind: str, spec_path: Path) -> SketchProvenance:
    """spec·규칙 지문만 채운 provenance. 단계가 돌면 그 단계가 자기 칸을 채운다(돌지 않은 단계는 비어 있다)."""
    return SketchProvenance(kind=kind, spec_sha1=sha1_file(spec_path), rules_hash=rules_hash())
