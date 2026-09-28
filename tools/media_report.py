"""미디어 재현 표 (D-0036 작업 9) — 영상에 쓰인 미디어마다 레지스트리 항목·구간·화면 시각·화면 문구를 한 표로,
그리고 화면 문구가 **레지스트리 조립 결과와 옛 연출(v2.5.0 direction.py) 문자열이 글자 단위로 같은지** 대조한다.

    python tools/media_report.py projects/hormuz_korea --old-rev 615ddd7 --out docs/handoff/reports/phase6_5
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.layers.media import article_text  # noqa: E402
from engine.media_registry import credit_line  # noqa: E402
from engine.project import load_project  # noqa: E402

TYPE_FIELDS = {"photo": ("caption", "credit"), "clip": ("caption", "credit"), "cutout": ("label", "sub"),
               "article": ("pub", "date", "headline", "hl", "sub", "note")}


def old_direction_strings(proj: Path, rev: str) -> dict[str, dict[str, str]]:
    """옛 direction.py 의 ev(...) 호출에서 mid(또는 기사 pub)별 문자열 키워드 인자."""
    rel = proj.resolve().relative_to(REPO) / "direction.py"
    src = subprocess.run(["git", "show", f"{rev}:{rel.as_posix()}"], capture_output=True, text=True, check=True, cwd=REPO).stdout
    out: dict[str, dict[str, str]] = {}
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ev" and node.args):
            continue
        typ = node.args[0].value if isinstance(node.args[0], ast.Constant) else None
        if typ not in TYPE_FIELDS:
            continue
        kw = {k.arg: k.value.value for k in node.keywords if isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)}
        key = kw.get("mid") or kw.get("pub")
        out[f"{typ}:{key}"] = {f: kw[f] for f in TYPE_FIELDS[typ] if f in kw}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--old-rev", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    P = load_project(args.proj)  # noqa: N806
    reg = P.R.assets.media_assets
    old = old_direction_strings(args.proj, args.old_rev)
    rows, ok_all = [], True
    for e in sorted((e for e in P.events if e["type"] in TYPE_FIELDS), key=lambda e: e["t0"]):
        a = reg[e["mid"]]
        if e["type"] == "article":
            now = {k: v for k, v in article_text(e).items() if v is not None}
            key = f"article:{now['pub']}"
        elif e["type"] == "cutout":
            now, key = {"label": a.caption, "sub": credit_line(a)}, f"cutout:{e['mid']}"
        else:
            now, key = {"caption": a.caption, "credit": credit_line(a)}, f"{e['type']}:{e['mid']}"
        was = old.get(key, {})
        same = bool(was) and all(now.get(k) == v for k, v in was.items())
        ok_all &= same
        rows.append({"mid": e["mid"], "type": e["type"], "registry_kind": a.kind, "url": a.url, "source_ref": a.source_ref, "pending_source": a.pending_source, "license": a.license,
                     "segment": list(a.segment) if a.segment else None, "t0": round(e["t0"], 2), "t1": round(e["t1"], 2),
                     "placement": P.R.cache["media_placement"].get(e["mid"], "-"), "screen": now, "old_direction": was,
                     "equal_to_old": same, "rights_status": a.rights_status, "verified_by": a.verified_by.by})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "media_reproduction.json").write_text(json.dumps({"schema_version": 1, "old_rev": args.old_rev, "count": len(rows),
                                                                 "all_equal": ok_all, "rows": rows}, ensure_ascii=False, indent=1),
                                                     encoding="utf-8")
    md = ["| # | mid | 형태 | 출처 | 구간 | 화면 시각 | 화면 캡션 / 출처 줄 | 옛 연출과 같음 |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        scr = " / ".join(str(v) for v in r["screen"].values() if v)
        seg = "–".join(f"{x:g}" for x in r["segment"]) + "초" if r["segment"] else "—"
        src = f"[{r['license']}]({r['url']})" if r["url"] else f"{r['license']} — {r['source_ref']} (url 대기: {r['pending_source']})"
        md.append(f"| {i} | {r['mid']} | {r['type']} | {src} | {seg} | {r['t0']}–{r['t1']}초 | {scr} | "
                  f"{'예' if r['equal_to_old'] else '**아니오**'} |")
    (args.out / "media_reproduction.md").write_text("# 미디어 7종 재현 표 (Phase 6.5, v2.5.5)\n\n"
                                                    f"화면 문구 = 레지스트리 조립 결과. 옛 연출({args.old_rev} direction.py) 문자열과 글자 단위 대조.\n\n"
                                                    + "\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(rows)}건, 전부 같음={ok_all}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
