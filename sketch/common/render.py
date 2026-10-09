"""스케치 프레임 루프 → mp4 + 컨택트 시트 + `out/sketch_provenance.json`(D-0140 §3, 15 P5).

종류별 장면은 `Scene` 계약(`frame(t) -> BGRA 바이트`, 크기 = 출력 프로파일 장치 px)만 지키면 된다.
출력 프로파일 = engine.style.output_profile(`--res` 기본 trial = 480p, 사용자 전달본 final = 720p).
인코딩 설정(crf·preset)도 그 프로파일 값이다(config engine.output — 코드에 다시 적지 않는다, P3).
"""

from __future__ import annotations

import hashlib
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from PIL import Image

from engine.sheet import grid
from engine.style import FPS, H_OUT, W_OUT, Output
from rules import rules_hash
from sketch.common.spec import RenderRecord, SketchProvenance

PROVENANCE_FILE = "sketch_provenance.json"
SHEET_COLS = 2


class Scene(Protocol):
    out: Output

    def frame(self, t: float) -> bytes:
        """시각 t 의 한 프레임(BGRA, out.width × out.height)."""


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
