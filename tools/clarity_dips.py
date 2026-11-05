"""문장별 국소 감쇠(그룹 최소값 없음): 세기(t) = 장면 기준(t) × 감쇠(t). 감쇠 = 문장 [t0−0.15, t1+0.15] 평탄, 사이 0.35초 경사(자리 없으면 이웃끼리 직선)."""
# v7.4.0 D-0630 §4 — 국소 감쇠 반복 도구(문장별, 그룹 최소값 없음). 사용: python tools/clarity_dips.py <proj 사본> 15.6 → audio.mix → 명료도 측정(clarity.json) 반복.
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/user/osint_generator")
from engine.project import load_plan
from engine.timebase import Timebase
from engine.direction import resolve_anchor
proj = Path(sys.argv[1]); target = float(sys.argv[2])
plan = load_plan(Path("/home/user/osint_generator/projects/cannae_216bc")); tb = Timebase(plan)
BASE = [[0.0, 0.55], [{"scene_start": "deployment"}, 0.6], [{"scene_start": "encirclement"}, 0.66], [{"scene_start": "aftermath"}, 0.55], [{"scene_start": "ending"}, 0.5]]
bk = [(resolve_anchor(t, tb), v) for t, v in BASE]
fb = lambda t: float(np.interp(t, [a for a, _ in bk], [b for _, b in bk]))
gp = proj / "out" / "gains2.json"
gains = json.load(open(gp)) if gp.exists() else {}
c = json.load(open(proj / "out" / "clarity.json"))
for sid, v in c.items():
    if v < target:
        gains[sid] = gains.get(sid, 1.0) * 10 ** (-(target - v + 0.3) / 20)
json.dump(gains, open(gp, "w"))
sent = {s.sid: s for s in plan.sentences}
PL, RAMP = 0.15, 0.35
plat = sorted((sent[k].t0 - PL, sent[k].t1 + PL, g) for k, g in gains.items())
gpts = []   # (t, gain)
for i, (a, b, g) in enumerate(plat):
    prev_b = plat[i - 1][1] if i else -1e9
    nxt_a = plat[i + 1][0] if i + 1 < len(plat) else 1e9
    if a - prev_b >= 2 * RAMP: gpts.append((a - RAMP, 1.0))
    gpts += [(a, g), (b, g)]
    if nxt_a - b >= 2 * RAMP: gpts.append((b + RAMP, 1.0))
gt = [t for t, _ in gpts]; gv = [v for _, v in gpts]
fg = lambda t: float(np.interp(t, gt, gv, left=1.0, right=1.0)) if gpts else 1.0
ts = sorted(set([round(t, 3) for t, _ in gpts] + [round(a, 3) for a, _ in bk]))
ts = [t for t in ts if t >= 0]
pts = [(t, round(fb(t) * fg(t), 3)) for t in ts]
lines = ["  intensity:"] + [f"  - [{t}, {v}]" for t, v in pts]
dp = proj / "direction.yaml"; s = dp.read_text(encoding="utf-8")
i = s.index("  intensity:\n"); rest = s[i:].split("\n"); j = 1
while j < len(rest) and rest[j].startswith("  - ["): j += 1
dp.write_text(s[:i] + "\n".join(lines) + "\n" + "\n".join(rest[j:]), encoding="utf-8")
print(len(plat), "dips;", {k: round(v, 3) for k, v in sorted(gains.items(), key=lambda kv: sent[kv[0]].t0)})
