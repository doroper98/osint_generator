"""showcase_geo 연출 이식 — 원 프로젝트(diesel·hormuz·dmz) 사용자 합격 연출의 이벤트·숏을 새 문장 번호로 옮긴다."""
import copy, json, re, sys
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent.parent
NEW = REPO / "projects/showcase_geo"
DON = {"diesel_road_2026": "", "hormuz_korea": "hz_", "dmz_mine_2026": "dmz_"}

hdr = (NEW / "script.yaml").read_text(encoding="utf-8").split("\n")[3]
m = {}   # (donor, sid) -> new sid
for p in hdr.split("문장 대응:")[1].split(" · "):
    new, old = [x.strip() for x in p.split(" ← ")]
    if old == "새 연결 문장":
        continue
    proj, sid = old.split()
    m[(proj, sid)] = new

def norm(x):
    if isinstance(x, dict):
        return {("off" if k in (False, "false") else k): norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    return x

def donor_order(proj):
    s = yaml.safe_load((REPO / "projects" / proj / "script.yaml").read_text(encoding="utf-8"))
    order, scenes = [], {}
    for sc in s["scenes"]:
        ids = [f"{sc['id']}_{i}" for i in range(len(sc["sentences"]))]
        order += ids
        scenes[sc["id"]] = ids
    return order, scenes

class Drop(Exception):
    pass

def make_remap(proj):
    order, scenes = donor_order(proj)
    idx = {s: i for i, s in enumerate(order)}
    mapped = lambda s: (proj, s) in m
    def last_mapped_before(sid, lo=None):
        for j in range(idx[sid], -1, -1):
            if mapped(order[j]) and (lo is None or j >= lo):
                return order[j]
        return None
    def remap(a, role, lo=None):
        """role: start | end. Returns new anchor or raises Drop."""
        a = dict(a)
        off = a.get("off")
        if "word" in a:
            w = dict(a["word"])
            if mapped(w["sid"]):
                w["sid"] = m[(proj, w["sid"])]
                a["word"] = w
                return a
            a = {"sid": w["sid"], **({"off": off} if off is not None else {})}
        if "scene_start" in a:
            ids = [s for s in scenes[a["scene_start"]] if mapped(s)]
            if not ids:
                if role == "start":
                    raise Drop
                return None
            return {"sid": m[(proj, ids[0])], **({"off": off} if off is not None else {})}
        if "scene_end" in a:
            ids = [s for s in scenes[a["scene_end"]] if mapped(s)]
            if not ids:
                raise Drop
            return {"sid": m[(proj, ids[-1])], "edge": "end", **({"off": off} if off is not None else {})}
        if "sid" in a:
            if mapped(a["sid"]):
                a["sid"] = m[(proj, a["sid"])]
                return a
            if role == "start":
                raise Drop
            prev = last_mapped_before(a["sid"], lo)
            if prev is None:
                raise Drop
            return {"sid": m[(proj, prev)], "edge": "end", "off": 0.3}
        return a   # card / total
    return remap, idx

def is_anchor(x):
    return isinstance(x, dict) and any(k in x for k in ("sid", "word", "scene_start", "scene_end"))

def walk(x, remap, lo, role="end"):
    if is_anchor(x):
        return remap(x, role, lo)
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            r = walk(v, remap, lo, "start" if k in ("start", "at") else "end")
            out[k] = r
        return out
    if isinstance(x, list):
        out = []
        for v in x:
            try:
                out.append(walk(v, remap, lo, "start" if is_anchor(v) else "end"))
            except Drop:
                if isinstance(v, dict) and not is_anchor(v):
                    continue   # 목록 항목(cascade item·패널 항목) 하나만 뺀다
                raise
        return out
    return x

def rename(x, names):
    if isinstance(x, dict):
        return {k: (names.get(v, v) if k in ("at_place", "place", "path") and isinstance(v, str) else rename(v, names)) for k, v in x.items()}
    if isinstance(x, list):
        return [rename(v, names) for v in x]
    return x

events, shots, places, paths, log = [], [], {}, {}, []
for proj, pfx in DON.items():
    d = norm(yaml.safe_load((REPO / "projects" / proj / "direction.yaml").read_text(encoding="utf-8")))
    names = {k: pfx + k for k in list(d.get("places") or {}) + list(d.get("paths") or {})} if pfx else {}
    for k, v in (d.get("places") or {}).items():
        places[names.get(k, k)] = v
    for k, v in (d.get("paths") or {}).items():
        paths[names.get(k, k)] = v
    remap, idx = make_remap(proj)
    kept = dropped = 0
    for e in d["events"]:
        try:
            st = e.get("start")
            lo = None
            if is_anchor(st) and "sid" in st:
                lo = idx.get(st["sid"])
            ne = walk(e, remap, lo)
            ne = rename(ne, names)
            ne["_donor"] = proj
            events.append(ne)
            kept += 1
        except Drop:
            dropped += 1
    sk = 0
    for s in d["shots"]:
        try:
            ns = rename(walk(s, remap, None, "start"), names)
            ns["_donor"] = proj
            shots.append(ns)
            sk += 1
        except Drop:
            pass
    log.append(f"{proj}: events {kept} kept / {dropped} dropped, shots {sk}/{len(d['shots'])}")
print("\n".join(log))
json.dump({"events": events, "shots": shots, "places": places, "paths": paths},
          open(sys.argv[1], "w"), ensure_ascii=False, indent=1, default=str)
