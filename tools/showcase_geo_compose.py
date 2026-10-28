import copy, json, sys

import yaml
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent; P = REPO / "projects/showcase_geo"
T = json.load(open(sys.argv[1]))
AI = yaml.safe_load((P / "direction.v1.yaml").read_text())   # 연출가 판(AI) — 이식 이벤트가 없는 문장만 쓴다
ai = AI["events"]
def pick(cond):
    return [copy.deepcopy(e) for e in ai if cond(e)]
def lab(e):
    return e.get("label") or e.get("mid") or e.get("id") or e.get("kind") or ""
tr = []
for e in T["events"]:
    d = e.pop("_donor")
    nm = lab(e) if not e.get("tag") else e["tag"]
    if e["type"] == "panel" and e["kind"] == "relation":
        continue                                   # 끝 앵커가 시작보다 앞(관계 문장 act3 밖) — 원고 밖 사실
    if e["type"] == "card" and e.get("tag") == "폭발 지점":
        continue                                   # site_diagram 이 같은 거리(약 10m)를 그린다
    if e["type"] == "flight":   # 원 연출 끝 문장(cold_3)이 원고 밖 — cold_0 안에서 끝나게 시작을 앞당긴다(비행+착탄+인셋 7초)
        e["start"] = {"sid": "cold_0", "off": 1.0}
        e["end"] = {"sid": "cold_0", "edge": "end", "off": 0.3}
        e["inset"]["hold_until"] = {"sid": "cold_0", "edge": "end"}
    if e["type"] == "card" and e.get("bigs") == [["17만 6천 ton 이상", "대부분 경유"]]:   # [unit-glyph-font] — 단위는 숫자 뒤 꼬리로
        e["bigs"] = [["17만 6천 ton", "이상 · 대부분 경유"]]
    if e["type"] == "route" and e.get("label", "").startswith("레일라호 · 두 번째"):   # 원 연출은 다음 문장들까지 — 이 장 끝에서 멈춘다
        e["end"] = {"sid": "act2_6", "edge": "end"}
    e.pop("route_cross_exempt", None)   # 골든 프로젝트 전용 면제(D-0203) — 이식하지 않는다
    tr.append(e)
add = []
# act2 — 연출가 판: 극동 국가 강조·블라디보스토크·하바롭스크 사진·울산
add += pick(lambda e: e["type"] == "country" and e["start"].get("sid") == "act2_0")
add += pick(lambda e: e["type"] == "photo" and e.get("mid") == "diesel_road_2026_khabarovsk_ref_2005")
# act1 정리 문장 기사
add += pick(lambda e: e["type"] == "article" and e.get("mid") == "diesel_road_2026_art_0009")
# act3 — 바닷길·해협 사진·공습 경로·기사
add += [dict(e, grow=11.0, end={"sid": "act3_3", "edge": "end"}) for e in pick(lambda e: e["type"] == "route" and e.get("label") == "유일한 바닷길")]
add += pick(lambda e: e["type"] == "photo" and e.get("mid") == "hormuz_transit")
add += pick(lambda e: e["type"] == "card" and e.get("tag") == "2월 28일")
add += pick(lambda e: e["type"] == "article" and e.get("mid") == "diesel_road_2026_art_0020")
# act4 — DMZ 사진·현장 도식
add += pick(lambda e: e["type"] == "photo" and e.get("mid") == "dmz_mine_sign")
add += pick(lambda e: e["type"] == "primitive" and e.get("id") == "site_diagram")
# 새로: tanker_loop(바닷길 경로)·CENTCOM 휘장·트럼프 뱃지
route_ex = next(e for e in add if e["type"] == "route" and e.get("label") == "유일한 바닷길")
add.append({"type": "tanker_loop", "start": {"sid": "act3_2", "off": 1.2}, "end": {"sid": "act3_3", "edge": "end"},
            "pts": copy.deepcopy(route_ex["pts"])})
add.append({"type": "badge", "start": {"sid": "act3_3", "off": 0.6}, "end": {"sid": "act3_3", "edge": "end", "off": 0.3},
            "lon": 53.5, "lat": 31.6, "kind": "emblem", "img": "centcom", "label": "미 중부사령부", "role": "공습", "accent": "us"})
add.append({"type": "badge", "start": {"sid": "act5_4", "off": 0.3}, "end": {"sid": "act5_4", "edge": "end", "off": 0.5},
            "place": "map_upper_left", "kind": "person", "pid": "trump", "flag": "us", "label": "도널드 트럼프", "role": "미국 대통령", "accent": "us"})
events = tr + add
places = {**AI["places"], **T["places"]}
paths = {**AI["paths"], **T["paths"]}
shots = []
for s in T["shots"]:
    d = s.pop("_donor")
    if d != "diesel_road_2026":
        if not (d == "hormuz_korea" and s.get("at") == {"sid": "act3_3", "off": -1.2}):
            continue
    shots.append(s)
for s_ in shots:   # 걸프 장 공습 문장 — 이스라엘·이란이 함께 보이게(frame_missing)
    if s_.get("at") == {"sid": "act3_3", "off": -1.2}:
        s_["camera"] = {"lon": 47.0, "lat": 29.5, "w": 30.0}
dmz = copy.deepcopy(next(s for s in AI["shots"] if s["camera"].get("lon") == 126.95))
dmz["at"] = {"sid": "act4_0", "off": -0.5}
shots.append(dmz)
plan = json.loads((P / "plan.json").read_text())
st = {x["sid"]: x for x in plan["sentences"]}
cards = {c["kind"]: c for c in plan["cards"]}
def tt(a):
    if not isinstance(a, dict):
        return float(a)
    off = a.get("off", 0.0)
    off = sum(off) if isinstance(off, list) else off
    if "card" in a:
        c = cards[a["card"]]
        return (c["t1"] if a.get("edge") == "end" else c["t0"]) + off
    x = st[a["sid"]]
    return (x["t1"] if a.get("edge") == "end" else x["t0"]) + off
shots.sort(key=lambda s_: tt(s_["at"]))
for a_, b_ in zip(shots, shots[1:]):   # 원 연출 drift 길이는 원 영상 기준 — 다음 숏까지로
    if a_.get("mode") == "drift":
        a_["dur"] = round(tt(b_["at"]) - tt(a_["at"]) - 0.2, 2)
doc = copy.deepcopy(AI)
doc.update(events=events, shots=shots, places=places, paths=paths, drops=[],
           media_note=("요소 확인용 쇼케이스(D-0251). 연출은 원 프로젝트(diesel_road_2026 v2·hormuz_korea·dmz_mine_2026) 사용자 합격 연출의 같은 문장 이벤트·숏을 "
                       "새 문장 번호로 옮기고(이식), 원 연출에 없는 문장만 연출가 판(direction.v1)에서 가져왔다. 미포함 — quote(원고에 직접 인용 문장 없음), "
                       "ships·cutout(P-8A)·rok_iraq 사진·precedent 패널(원 프로젝트에서 이 사실을 말한 문장이 이번 원고에 없다), gantt·network·fork·checklist·versus·timeline 패널"
                       "(원고 안 사실 묶음이 패널 하나를 채우지 못한다), post(X 게시물 출처 없음)."))
(P / "direction.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(len(events), "events", len(shots), "shots")
