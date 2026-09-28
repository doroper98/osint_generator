"""v3 vs 카메라 제안 사본 컷별 대조 (v3.3.0, back_and_forth D-0056 작업 6·9 `camauto_compare.json`).

    python tools/camauto_compare.py projects/hormuz_korea projects/hormuz_camauto <출력.json>

두 프로젝트 모두 `--preview golden`(25 앵커) 컷이 prev/ 에 있어야 한다. 컷마다
- mad: 픽셀 평균 절대차(0~1, 픽셀 동일은 요구하지 않음 — 참고값)
- inside: 그 시각 보이는 뱃지·마커 상자가 전부 화면 안인가(engine.checks.place_over — offscreen 검사와 같은 함수)
- reserved_avoidance: 카드 영역 때문에 비킨 뱃지(engine.reserved.avoidance_report — provenance 와 같은 함수)
를 적는다. 양쪽 checks(hard·warning)와 숏 규칙 경고도 붙인다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def _cut_inside(P, t: float) -> tuple[bool, list[str]]:  # noqa: ANN001, N803
    import cairo  # noqa: PLC0415

    from engine.checks import SHADOW_PX, place_over  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    bad = []
    for e in P.events:
        if e["type"] in ("badge", "marker") and e["t0"] <= t <= e["t1"]:
            r = place_over(P, ctx, e, t)
            if r is None:
                continue
            if r[0] > SHADOW_PX:
                bad.append(f"{e['type']}:{e.get('label') or e.get('pid')} {r[0]:.0f}px")
    return not bad, bad


def main(argv: list[str] | None = None) -> int:
    import numpy as np  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    from engine.golden import golden_times  # noqa: PLC0415
    from engine.project import load_project  # noqa: PLC0415
    from engine.reserved import avoidance_report  # noqa: PLC0415
    from engine.shots import shot_issues  # noqa: PLC0415

    a = argv if argv is not None else sys.argv[1:]
    src, dst, out = Path(a[0]).resolve(), Path(a[1]).resolve(), Path(a[2])
    Ps, Pd = load_project(src), load_project(dst)  # noqa: N806
    plan = json.loads((src / "plan.json").read_text(encoding="utf-8"))
    cuts = []
    for label, t in golden_times(plan):
        name = f"p_{t:07.2f}.png"
        A = np.asarray(Image.open(src / "prev" / name).convert("RGB"), float) / 255  # noqa: N806
        B = np.asarray(Image.open(dst / "prev" / name).convert("RGB"), float) / 255  # noqa: N806
        ins_s, bad_s = _cut_inside(Ps, t)
        ins_d, bad_d = _cut_inside(Pd, t)
        cuts.append({"label": label, "t": round(t, 2), "mad": round(float(np.abs(A - B).mean()), 5),
                     "inside_v3": ins_s, "inside_camauto": ins_d, "outside_camauto": bad_d, "outside_v3": bad_s})
    chk = {n: json.loads((p / "prev" / "checks.json").read_text(encoding="utf-8")) for n, p in (("v3", src), ("camauto", dst))}
    mp = json.loads((dst / "camauto_map.json").read_text(encoding="utf-8"))
    rep = {"schema_version": 1, "source": src.name, "copy": dst.name, "shots_replaced": len(mp["changes"]),
           "cuts": cuts, "inside_camauto_pct": round(100 * sum(c["inside_camauto"] for c in cuts) / len(cuts), 1),
           "inside_v3_pct": round(100 * sum(c["inside_v3"] for c in cuts) / len(cuts), 1),
           "mad_mean": round(sum(c["mad"] for c in cuts) / len(cuts), 5),
           "checks": {n: {"hard": c["hard"], "warnings": c["warnings"]} for n, c in chk.items()},
           "shot_issues": {"v3": shot_issues(Ps.keys, Ps.plan.sentences, Ps.events, Ps.plan.total),
                           "camauto": shot_issues(Pd.keys, Pd.plan.sentences, Pd.events, Pd.plan.total)},
           "reserved_avoidance": {"v3": avoidance_report(Ps), "camauto": avoidance_report(Pd)},
           "changes": mp["changes"]}
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}: 프레임 안 camauto {rep['inside_camauto_pct']}% · v3 {rep['inside_v3_pct']}% · MAD 평균 {rep['mad_mean']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
