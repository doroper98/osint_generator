"""A/B 비교 구간 (v7.4.0, back_and_forth D-0253 §2·D-0265) — 같은 문장·같은 mix.f32 구간을 두 연출로 렌더해 나란히 본다.

    python tools/ab_compare.py projects/showcase_econ --from act2_0 --to act2_4

A = 본편 direction.yaml, B = direction.B.yaml. B 는 프로젝트 사본(prev_ab/b/<이름>/, 원본 파일은 심볼릭 링크 — 연출 파일만
바꿔 끼운다)에서 렌더한다. 두 연출 모두 프리뷰 검사 hard 0 이어야 한다(불리하게 만든 쪽은 비교가 아니다 — D-0253 조건 ①).
산출 prev_ab/: A.mp4·B.mp4(같은 구간 음성 포함)·sheet.jpg(같은 초 6컷, 왼쪽 A·오른쪽 B)·provenance.json(ab_compare).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.style import FPS  # noqa: E402

SKIP = {"direction.yaml", "direction.B.yaml", "out", "prev_ab"}   # B 사본에 링크하지 않는 것(prev* 는 아래에서 따로 거른다)
SHEET_N = 6
SAMPLE_RATE = 44100   # audio.mix 산출 형식(44.1kHz 스테레오 float32)
SHEET_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"   # 검수 시트 글씨(영상 글꼴 아님 — tools/media_fetch 와 같은 파일)


class AbCompare(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sentences: list[str]
    t0: float
    t1: float
    direction_a_sha1: str
    direction_b_sha1: str
    checks_hard: dict[str, int]
    sheet_times: list[float]


class AbProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    ab_compare: AbCompare


def sha1(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"실패: {' '.join(cmd)}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def b_project(proj: Path, dst: Path) -> Path:
    """B 사본 — 연출 파일만 direction.B.yaml 로, 나머지는 원본 링크. out/ 은 실제 폴더(원본 out 파일은 링크, 새 산출은 사본에만)."""
    b = dst / proj.name
    if b.exists():
        shutil.rmtree(b)
    (b / "out").mkdir(parents=True)
    for p in proj.iterdir():
        if p.name in SKIP or p.name.startswith("prev"):
            continue
        (b / p.name).symlink_to(p.resolve())
    for p in (proj / "out").iterdir():
        if p.is_file() and not p.name.startswith(("animatic", "catalog")):
            (b / "out" / p.name).symlink_to(p.resolve())
    shutil.copyfile(proj / "direction.B.yaml", b / "direction.yaml")
    return b


def preview_hard(proj: Path) -> int:
    """프리뷰(auto) 검사 hard 수 — 0 이 아니면 비교하지 않는다."""
    f = proj / "prev" / "checks.json"
    f.unlink(missing_ok=True)   # 렌더가 검사 전에 죽으면 옛 결과를 읽지 않는다
    r = subprocess.run([sys.executable, "-m", "engine.render", str(proj), "--preview", "auto"], cwd=REPO, capture_output=True, text=True)
    if not f.exists():
        raise SystemExit(f"프리뷰 검사 결과 없음: {proj}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    chk = json.loads(f.read_text(encoding="utf-8"))
    return int(chk["hard"])


def clip(proj: Path, mix: Path, t0: float, t1: float, out: Path) -> None:
    """[t0, t1) 프레임 구간 렌더 + 같은 구간 mix.f32 음성."""
    silent = out.with_suffix(".noaudio.mp4")
    run([sys.executable, "-m", "engine.render", str(proj), "--chunk", str(round(t0 * FPS)), str(round(t1 * FPS)), str(silent)])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "2", "-ss", f"{t0:.3f}",
         "-t", f"{t1 - t0:.3f}", "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", str(out)])
    silent.unlink()
    for side in out.parent.glob(f"{silent.stem}.*"):
        side.unlink()


def sheet(a: Path, b: Path, times: list[float], t0: float, out: Path) -> None:
    """같은 초 SHEET_N 컷 — 왼쪽 A, 오른쪽 B, 아래 초(영상 전체 기준)."""
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    rows = []
    for t in times:
        pair = []
        for src in (a, b):
            png = out.parent / f"_f_{src.stem}_{t:.2f}.png"
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t - t0:.3f}", "-i", str(src), "-frames:v", "1", str(png)])
            pair.append(Image.open(png).convert("RGB"))
            png.unlink()
        rows.append(pair)
    w, h = rows[0][0].size
    lab = h // 10
    img = Image.new("RGB", (w * 2, (h + lab) * len(rows)), (16, 16, 16))
    dr = ImageDraw.Draw(img)
    f = ImageFont.truetype(SHEET_FONT, int(lab * 0.6))
    for i, (ia, ib) in enumerate(rows):
        y = i * (h + lab)
        img.paste(ia, (0, y))
        img.paste(ib, (w, y))
        dr.text((w, y + h + lab / 2), f"{times[i]:.1f}초   ← A · B →", fill=(230, 230, 230), font=f, anchor="mm")
    img.save(out, quality=88)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proj", type=Path)
    ap.add_argument("--from", dest="sid0", required=True, help="첫 문장 sid")
    ap.add_argument("--to", dest="sid1", required=True, help="끝 문장 sid")
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    for need in ("direction.yaml", "direction.B.yaml", "plan.json", "out/mix.f32"):
        if not (proj / need).exists():
            raise SystemExit(f"없음: {proj / need}")
    ss = json.loads((proj / "plan.json").read_text(encoding="utf-8"))["sentences"]
    sids = [s["sid"] for s in ss]
    i0, i1 = sids.index(args.sid0), sids.index(args.sid1)
    if i1 < i0:
        raise SystemExit("--to 가 --from 보다 앞이다")
    pre = ss[i0 - 1]["t1"] if i0 else 0.0   # 앞 문장 끝과 뒤 문장 시작 사이의 가운데에서 자른다(문장 머리·꼬리를 자르지 않는다)
    post = ss[i1 + 1]["t0"] if i1 + 1 < len(ss) else ss[i1]["t1"]
    t0, t1 = round((pre + ss[i0]["t0"]) / 2, 2), round((ss[i1]["t1"] + post) / 2, 2)
    outd = proj / "prev_ab"
    outd.mkdir(exist_ok=True)
    b = b_project(proj, outd / "b")
    hard = {"A": preview_hard(proj), "B": preview_hard(b)}
    if any(hard.values()):
        raise SystemExit(f"프리뷰 hard 가 0 이 아니다: {hard} — 두 연출 모두 hard 0 이어야 비교한다(D-0253 조건 ①)")
    clip(proj, proj / "out" / "mix.f32", t0, t1, outd / "A.mp4")
    clip(b, proj / "out" / "mix.f32", t0, t1, outd / "B.mp4")
    step = (t1 - t0) / SHEET_N
    times = [round(t0 + step * (k + 0.5), 2) for k in range(SHEET_N)]
    sheet(outd / "A.mp4", outd / "B.mp4", times, t0, outd / "sheet.jpg")
    prov = AbProvenance(ab_compare=AbCompare(sentences=sids[i0:i1 + 1], t0=t0, t1=t1, direction_a_sha1=sha1(proj / "direction.yaml"),
                                             direction_b_sha1=sha1(proj / "direction.B.yaml"), checks_hard=hard, sheet_times=times))
    (outd / "provenance.json").write_text(json.dumps(prov.model_dump(), ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(outd), **prov.model_dump()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
