"""카탈로그 판 요소 표 — out/catalog_frames.json → 초 → 요소·글꼴 표(md) (v7.4.0, back_and_forth D-0251 §1.1).

    python tools/catalog_table.py projects/<pid>            → projects/<pid>/out/catalog_table.md (+ 표준 출력)
    python tools/catalog_table.py projects/<pid> --out X.md

표의 값은 `engine.render --catalog` 가 라벨을 그린 것과 같은 기록(catalog_frames.json)에서만 온다 — 손으로 쓴 표는 받지 않는다(P12).
연속된 표본의 요소·글꼴이 같으면 한 줄(구간)로 묶는다. 끝에 영상 전체에서 쓰인 요소·글꼴 목록과 provenance catalog_run 지문을 붙인다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from schemas.engine_models import CatalogFrame, CatalogFrames  # noqa: E402


def mmss(t: float) -> str:
    m, s = divmod(int(round(t)), 60)
    return f"{m}:{s:02d}"


def runs(frames: list[CatalogFrame], step: float) -> list[tuple[float, float, list[str], list[str]]]:
    """같은 (요소, 글꼴) 이 이어지는 표본을 [시작, 끝] 구간 하나로."""
    out: list[tuple[float, float, list[str], list[str]]] = []
    for f in frames:
        if out and out[-1][2] == f.elements and out[-1][3] == f.fonts:
            out[-1] = (out[-1][0], f.t, f.elements, f.fonts)
        else:
            out.append((f.t, f.t, f.elements, f.fonts))
    return [(a, b + step, e, g) for a, b, e, g in out]


def build_table(proj: Path) -> str:
    outd = proj / "out"
    src = outd / "catalog_frames.json"
    if not src.exists():
        raise FileNotFoundError(f"{src} 없음 — 먼저 `python -m engine.render {proj} --catalog`")
    cf = CatalogFrames.model_validate_json(src.read_text(encoding="utf-8"))
    prov_p = outd / "catalog_provenance.json"
    prov = json.loads(prov_p.read_text(encoding="utf-8")) if prov_p.exists() else {}
    run = prov.get("catalog_run") or {}
    lines = [f"# 카탈로그 요소 표 — {proj.name}", "",
             f"출처: `out/catalog_frames.json`(표본 {len(cf.frames)}개, {cf.sample_every_sec:g}초 간격) · "
             f"연출 지문 {str(run.get('direction_sha1', '-'))[:8]} · 음성 {run.get('voice', '-')}", "",
             "| 구간 | 요소(레지스트리 이름) | 글꼴 |", "|---|---|---|"]
    for a, b, els, fonts in runs(cf.frames, cf.sample_every_sec):
        lines.append(f"| {mmss(a)}–{mmss(b)} | {' · '.join(els) or '-'} | {' · '.join(fonts) or '-'} |")
    all_el = sorted({x for f in cf.frames for x in f.elements})
    all_fn = list(dict.fromkeys(x for f in cf.frames for x in f.fonts))
    lines += ["", f"## 영상 전체 요소 ({len(all_el)})", "", " · ".join(all_el) or "-",
              "", f"## 영상 전체 글꼴 ({len(all_fn)})", "", " · ".join(all_fn) or "-", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="카탈로그 요소 표(md)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    md = build_table(args.proj)
    dst = args.out or args.proj / "out" / "catalog_table.md"
    dst.write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
