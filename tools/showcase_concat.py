"""쇼케이스 결합본 — 두 전편 final.mp4 를 이어 붙인 showcase.mp4 하나 (v7.4.0, back_and_forth D-0251 §1.3).

장르 프로필은 프로젝트당 하나, 지도 테마는 영상당 하나(C0)라서 두 영상을 한 프로젝트로 합치지 않는다. 결합은 이 도구가
ffmpeg concat 으로만 한다(다시 그리지 않는다). 각 전편 md5·길이와 결합본 md5 를 README 줄로 출력한다.

    python tools/showcase_concat.py projects/showcase_geo/out/final.mp4 projects/showcase_econ/out/final.mp4 --out showcase.mp4

- 입력 스트림 조건(해상도·fps·코덱·오디오 샘플레이트·채널)이 다르면 오류로 멈춘다 — 재인코딩으로 맞추지 않는다(조용한 변환 금지, 15 P6).
- 입력이 콘티 판·카탈로그 판(mp4 comment 표식)이면 거부한다 — 결합본은 배포 전편만.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KEYS = ("codec_name", "width", "height", "r_frame_rate", "pix_fmt", "sample_rate", "channels")
REFUSE = ("animatic", "catalog")


def probe(p: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=" + ",".join(KEYS) + ",codec_type",
                          "-show_entries", "format=duration:format_tags=comment", "-of", "json", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def signature(info: dict) -> list[tuple]:
    return sorted((s.get("codec_type"), *(s.get(k) for k in KEYS)) for s in info["streams"])


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def concat(inputs: list[Path], out: Path) -> list[str]:
    infos = [probe(p) for p in inputs]
    for p, info in zip(inputs, infos):
        tag = ((info.get("format") or {}).get("tags") or {}).get("comment", "")
        if any(w in tag for w in REFUSE):
            raise ValueError(f"{p}: 콘티·카탈로그 판(comment {tag!r}) — 결합본은 배포 전편만")
    sig0 = signature(infos[0])
    for p, info in zip(inputs[1:], infos[1:]):
        if signature(info) != sig0:
            raise ValueError(f"{p}: 스트림 조건이 첫 영상과 다르다 {signature(info)} ≠ {sig0} — 재인코딩으로 맞추지 않는다")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in inputs:
            f.write(f"file '{p.resolve()}'\n")
        lst = f.name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", str(out)], check=True)
    rows = [f"- {p.name}({p.parent.parent.name}) md5 {md5(p)} · {float(i['format']['duration']):.2f}초" for p, i in zip(inputs, infos)]
    total = float(probe(out)["format"]["duration"])
    rows.append(f"- {out.name} md5 {md5(out)} · {total:.2f}초(입력 {len(inputs)}편 concat, 재인코딩 없음)")
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="쇼케이스 결합본(ffmpeg concat)")
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        print("\n".join(concat(a.inputs, a.out)))
    except (ValueError, subprocess.CalledProcessError) as ex:
        print(f"오류: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
