"""전달본 한 파일(≤ rules delivery_package.deliver_file.max_bytes) + 넘을 때만 조각(v7.4.0 D-0634 §3-3).

사용자 의견 UF-268 "30메가 넘으면 분할해서 보내줘", UF-269 "꼭 분할이 필요한 상황이라면 말이지".

    python tools/final_deliver.py projects/<pid>            # out/final.mp4 → out/final_deliver.mp4 (+ 넘을 때만 out/final_parts/)

- 인코딩: x264 2-pass, 목표 크기 target_bytes(영상 비트레이트 = 목표 비트 ÷ 길이 − 음성 비트레이트), 음성 복사(-c:a copy).
  china·iran·칸나이 v1 전달본을 손으로 만든 방식 그대로(감독 실측 기준).
- 조각: 전달본이 max_bytes 를 넘을 때만. 키프레임 경계에서 재인코딩 없이(ffmpeg segment -c copy, reset_timestamps),
  각 ≤ piece_max_bytes, 이어 붙인 길이 = 원본 길이(차 ≤ 0.1초). 이하이면 조각을 만들지 않고, 옛 조각 폴더가 있으면 지운다.
- 마지막 줄 = 결과 JSON(크기·md5·길이·조각 목록).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rules import load_rules  # noqa: E402


def probe(path: Path, entry: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error"] + (["-select_streams", stream] if stream else []) + ["-show_entries", entry, "-of", "csv=p=0", str(path)]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip().splitlines()[0]


def duration(path: Path) -> float:
    return float(probe(path, "format=duration"))


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def video_kbps(dur: float, audio_bps: float, target_bytes: int) -> int:
    """목표 크기에 맞춘 영상 비트레이트(kbps) — 컨테이너 여유 8 kbps."""
    return int((target_bytes * 8 / dur - audio_bps) / 1000) - 8


def needs_split(size: int, max_bytes: int) -> bool:
    """UF-269 — 보낼 파일이 한도를 넘을 때만 조각."""
    return size > max_bytes


def encode(src: Path, dst: Path, kbps: int, preset: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        base = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "libx264", "-preset", preset, "-b:v", f"{kbps}k"]
        subprocess.run(base + ["-pass", "1", "-passlogfile", f"{td}/p", "-an", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(base + ["-pass", "2", "-passlogfile", f"{td}/p", "-c:a", "copy", "-movflags", "+faststart", str(dst)], check=True)


def split(src: Path, out_dir: Path, piece_max_bytes: int) -> list[dict]:
    """키프레임 경계 무재인코딩 조각. 조각 길이 = 전체 길이 × piece_max / 크기 × 0.9 에서 시작해 넘으면 줄인다."""
    size, dur = src.stat().st_size, duration(src)
    seg = dur * piece_max_bytes / size * 0.9
    for _ in range(6):
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c", "copy", "-map", "0", "-f", "segment",
                        "-segment_time", f"{seg:.3f}", "-reset_timestamps", "1", str(out_dir / "part_%02d.mp4")], check=True)
        parts = sorted(out_dir.glob("part_*.mp4"))
        if all(p.stat().st_size <= piece_max_bytes for p in parts):
            break
        seg *= 0.8
    else:
        raise RuntimeError(f"조각이 {piece_max_bytes} B 를 넘는다 — 키프레임 간격이 너무 길다")
    rows = [{"file": p.name, "bytes": p.stat().st_size, "sec": round(duration(p), 3), "md5": md5(p)} for p in parts]
    total = sum(r["sec"] for r in rows)
    if abs(total - dur) > 0.1:
        raise RuntimeError(f"조각 길이 합 {total:.3f}초 ≠ 원본 {dur:.3f}초")
    return rows


def deliver(src: Path, dst: Path, parts_dir: Path) -> dict:
    cfg = load_rules().delivery_package.deliver_file
    if cfg is None:
        raise RuntimeError("rules delivery_package.deliver_file 없음")
    dur = duration(src)
    abr = float(probe(src, "stream=bit_rate", "a:0"))
    kbps = video_kbps(dur, abr, cfg.target_bytes)
    encode(src, dst, kbps, cfg.preset)
    size = dst.stat().st_size
    rec = {"schema_version": 1, "src": src.name, "src_bytes": src.stat().st_size, "file": dst.name, "bytes": size, "md5": md5(dst),
           "sec": round(duration(dst), 3), "video_kbps": kbps, "audio_bps": int(abr), "max_bytes": cfg.max_bytes, "parts": []}
    if needs_split(size, cfg.max_bytes):
        rec["parts"] = split(dst, parts_dir, cfg.piece_max_bytes)
    elif parts_dir.exists():
        shutil.rmtree(parts_dir)   # 한도 이하 — 조각 없음(UF-269), 옛 조각을 남기지 않는다
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("proj", type=Path)
    a = ap.parse_args(argv)
    out = a.proj / "out"
    rec = deliver(out / "final.mp4", out / "final_deliver.mp4", out / "final_parts")
    (out / "final_deliver.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"ok": True, **{k: rec[k] for k in ("file", "bytes", "md5", "sec")}, "parts": len(rec["parts"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
