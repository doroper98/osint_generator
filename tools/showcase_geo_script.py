"""showcase_geo 원고·intake 조립 (v7.4.0, back_and_forth D-0251 §1.1) — 기존 합격 프로젝트 문장을 글자 그대로 옮긴다(새 사실 없음).

    python tools/showcase_geo_script.py projects/showcase_geo   → script.yaml · intake/claims.json · intake/sources.json

문장 출처: diesel_road_2026 v2(기준 작품) · hormuz_korea · dmz_mine_2026. hormuz·dmz 의 claim·source id 는 접두(clm_hz_·clm_dmz_·src_hz_·src_dmz_)만
바꿔 diesel id 와 겹치지 않게 한다. 새로 쓴 문장은 NEW 하나(장 전환 고지, 사실·수치 없음). 역할(role)은 ROLE 로만 붙인다.
"""
import copy, json, re, sys
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = {"d": "diesel_road_2026", "h": "hormuz_korea", "z": "dmz_mine_2026"}
PFX = {"d": "", "h": "hz_", "z": "dmz_"}

def load(p):
    s = yaml.safe_load((REPO / "projects" / p / "script.yaml").read_text(encoding="utf-8"))
    out = {}
    for sc in s["scenes"]:
        for i, x in enumerate(sc["sentences"]):
            out[f"{sc['id']}_{i}"] = x
    return out

SCR = {k: load(v) for k, v in SRC.items()}

def ren(k, cid):
    return cid if not PFX[k] else cid.replace("clm_", f"clm_{PFX[k]}", 1)

def ren_src(k, sid):
    return sid if not PFX[k] else sid.replace("src_", f"src_{PFX[k]}", 1)

NEW = {  # 새로 쓴 연결 문장(사실·수치 없음 — 장 전환 고지만, D-0251 §1.1 "원고는 새로 쓴다")
    "dmz_bridge": {"date": "2026.09.21", "text": "이제 자료 장으로, 지난 9월 한반도의 비무장지대로 무대를 옮깁니다.",
                   "tts": "이제 자료 장으로, 지난 구월 한반도의 비무장지대로 무대를 옮깁니다.", "role": "bridge", "emphasis": [],
                   "sources": ["clm_0001"]},
}
ROLE = {("h", "route_0"): "background", ("z", "open_0"): "intro", ("z", "open_questions_0"): "outro", ("d", "act4_22"): "outro"}   # 역할만 지정(문장 글자 그대로)

PLAN = [
    ("cold", "cold", "러시아", [("d", "cold_0"), ("d", "cold_4")]),
    ("act1", "act", "러시아", [("d", "act1_0"), ("d", "act1_1"), ("d", "act1_3"), ("d", "act1_4"), ("d", "act1_7"), ("d", "act1_14"), ("d", "act1_15"),
                             ("d", "act1_18"), ("d", "act1_27")]),
    ("act2", "act", "극동", [("d", "act2_0"), ("d", "act2_1"), ("d", "act2_20"), ("d", "act2_21"), ("d", "act2_23"), ("d", "act2_25"),
                             ("d", "act2_35")]),
    ("act3", "act", "걸프", [("d", "act4_0"), ("d", "act4_1"), ("h", "route_0"), ("h", "war_0"), ("h", "war_2"), ("d", "act4_8"),
                             ("h", "ask_4"), ("d", "act4_21"), ("d", "act4_22")]),
    ("act4", "act", "한반도", [("z", "dmz_bridge"), ("z", "open_0"), ("z", "open_1"), ("z", "open_questions_0")]),
    ("act5", "act", "워싱턴", [("d", "act5_0"), ("d", "act5_1"), ("d", "act5_2"), ("d", "act5_5"), ("d", "act5_19"), ("d", "act5_28")]),
    ("ending", "ending", None, [("d", "ending_0"), ("d", "ending_1")]),
]

def main(dst: Path):
    used = {k: set() for k in SRC}
    scenes = []
    origin = []
    for sid, kind, stage, items in PLAN:
        sents = []
        for k, key in items:
            x = copy.deepcopy(NEW[key] if key in NEW else SCR[k][key])
            if (k, key) in ROLE:
                x["role"] = ROLE[(k, key)]
            x["sources"] = [ren(k, c) for c in x.get("sources", [])]
            used[k] |= set(x["sources"])
            sents.append(x)
            origin.append(f"{sid}_{len(sents)-1} ← " + ("새 연결 문장" if key in NEW else f"{SRC[k]} {key}"))
        sc = {"id": sid, "kind": kind}
        if stage:
            sc["stage"] = stage
        sc["sentences"] = sents
        scenes.append(sc)
    # roles: 자료 장(act3·act5) 첫 문장 bridge 유지 — 원 문장 role 그대로
    claims, sources = [], []
    for k, p in SRC.items():
        c = json.loads((REPO / "projects" / p / "intake" / "claims.json").read_text(encoding="utf-8"))
        s = json.loads((REPO / "projects" / p / "intake" / "sources.json").read_text(encoding="utf-8"))
        need_src = set()
        for cl in c["claims"]:
            nid = ren(k, cl["claim_id"])
            if nid not in used[k]:
                continue
            cl = copy.deepcopy(cl)
            cl["claim_id"] = nid
            cl["source_ids"] = [ren_src(k, x) for x in cl["source_ids"]]
            cl["checks"] = [re.sub(r"src_", f"src_{PFX[k]}", ch) if PFX[k] else ch for ch in cl.get("checks", [])]
            cl["notes"] = (cl.get("notes") or "") + f" [쇼케이스 이관: {p} {cl['claim_id'] if not PFX[k] else cl['claim_id'].replace('clm_'+PFX[k], 'clm_')}]"
            need_src |= set(cl["source_ids"])
            claims.append(cl)
        for so in s["sources"]:
            nid = ren_src(k, so["id"])
            if nid in need_src:
                so = copy.deepcopy(so)
                so["id"] = nid
                if so.get("verification"):
                    so["verification"]["checks"] = [re.sub(r"src_", f"src_{PFX[k]}", ch) if PFX[k] else ch for ch in so["verification"].get("checks", [])]
                sources.append(so)
        miss = used[k] - {cl["claim_id"] for cl in claims}
        if miss:
            sys.exit(f"claims 없음 {p}: {sorted(miss)}")
    return scenes, claims, sources, origin

if __name__ == "__main__":
    dst = Path(sys.argv[1])
    scenes, claims, sources, origin = main(dst)
    head = ("# 『쇼케이스 — 지도 위의 경유』 원고 v1 (v7.4.0, back_and_forth D-0251 §1·§5). 요소·목소리·글꼴 확인용 데모(지경학).\n"
            "# 문장은 기존 합격 프로젝트 원고에서 글자 그대로 옮겼다(새 사실·새 수치 없음): 『경유의 길』 diesel_road_2026 v2(기준 작품) 축약 +\n"
            "# 호르무즈 hormuz_korea(자료 장) + DMZ dmz_mine_2026(자료 장, site_diagram). 출처 claim id 는 hormuz → clm_hz_*, dmz → clm_dmz_* 로 접두만 바꿨다.\n"
            "# 문장 대응: " + " · ".join(origin) + "\n")
    doc = {"schema_version": 1, "title": "쇼케이스 — 지도 위의 경유",
           "subtitle": "『경유의 길』 축약과 호르무즈·DMZ 자료 장 — 화면 요소·목소리·글꼴 확인용",
           "date": "2026.10.28", "scenes": scenes}
    (dst / "script.yaml").write_text(head + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    (dst / "intake").mkdir(exist_ok=True)
    (dst / "intake" / "claims.json").write_text(json.dumps({"schema_version": 1, "claims": claims}, ensure_ascii=False, indent=1), encoding="utf-8")
    (dst / "intake" / "sources.json").write_text(json.dumps({"schema_version": 1, "sources": sources}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(claims), "claims", len(sources), "sources", sum(len(s["sentences"]) for s in scenes), "sentences")
