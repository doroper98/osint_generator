"""diesel_road_2026 연출 v2 — AI 연출 초안(llm_20261018_073432_a522)에 D-0229 §4·D-0238 지시를 얹는 구현 세션 보강.
입력 = direction.yaml(AI 초안), 출력 = 같은 파일. 다시 돌려도 같은 결과(멱등)가 되게 표식 키로 찾는다."""
import sys
from pathlib import Path

import yaml

P = Path(sys.argv[1])
d = yaml.safe_load(P.read_text(encoding="utf-8"))
ev = d["events"]


def find(pred):
    return [e for e in ev if pred(e)]


def sid_of(e):
    s = e.get("start")
    if isinstance(s, dict):
        return s.get("sid") or (s.get("word") or {}).get("sid")
    return None


# 0) 무대 — v1 과 같은 dark(D232 U8 장르 예외)
d["stage_config"] = {"mercator": {"theme": "dark", "theme_reason": "타격 중심 군사 전황 — D154 장르 예외, D232 U8"}}

# 1) 오프닝(D-0229 §4.1·D-0238): 랴잔 인셋 cold_3 끝까지 왼쪽 아래 유지, AP 기사 카드 한 장(cold_2~cold_3) + 백악관 공식 사진(press)
fl = next(e for e in ev if e["type"] == "flight" and sid_of(e) == "cold_0")
fl["inset"] = {"mid": "inset_ryazan_hls", "side": "down_left", "hold_until": {"sid": "cold_3", "edge": "end"}}
fl["end"] = {"sid": "cold_3", "edge": "end", "off": 0.3}
art = next(e for e in ev if e["type"] == "article" and e.get("mid") == "diesel_road_2026_art_0032")
art.update(start={"sid": "cold_2", "off": 0.1}, end={"sid": "cold_3", "edge": "end", "off": 0.4}, press="diesel_road_2026_trump_1006")
ev[:] = [e for e in ev if not (sid_of(e) == "cold_3" and e["type"] in ("badge", "card"))]   # 카드 위에 겹쳐 올리지 않는다
ev[:] = [e for e in ev if not (e["type"] == "article" and e.get("mid") == "diesel_road_2026_art_0001" and sid_of(e) == "cold_4")]
if not find(lambda e: e["type"] == "marker" and sid_of(e) == "cold_4"):
    ev.append({"type": "marker", "start": {"word": {"sid": "cold_4", "text": "울산항"}}, "end": {"card": "title", "edge": "end"},
               "at_place": "ulsan", "label": "울산항", "side": "right", "hl": True})

# 2) 트럼프 사진은 기사 카드 press 로(5막 휴전 발표 카드 재사용), 연결 문장(act5_0)에는 새 정보 요소를 두지 않는다(§4.4)
ev[:] = [e for e in ev if not (e["type"] == "photo" and e.get("mid") == "diesel_road_2026_trump_1006")]
a30 = next(e for e in ev if e["type"] == "article" and e.get("mid") == "diesel_road_2026_art_0030")
a30["press"] = "diesel_road_2026_trump_1006"

# 3) 2막 점 패널(D-0229 §4.3, UF-113) — 7척 중 3척(척수 기준), 열네 번은 항해 횟수
ev[:] = [e for e in ev if not (e["type"] == "card" and sid_of(e) in ("act2_21", "act2_22"))]
if not find(lambda e: e["type"] == "panel" and sid_of(e) == "act2_21"):
    ev.append({"type": "panel", "kind": "dots", "start": {"sid": "act2_21", "off": -0.2}, "end": {"sid": "act2_22", "edge": "end", "off": 0.5},
               "data": {"title": "러시아 극동을 오간 유조선", "subtitle": "일곱 척 · 열네 번 항해 · 가디언", "total": 7, "highlight": 3,
                        "accent": "ru", "big": "3 / 7", "caption": "영국·유럽연합 제재 대상",
                        "provenance": {"sources": ["clm_0002", "clm_0003"], "verification": "verified"}}})

# 4) 굴절 항로 꺾임점(D-0229 §4.3): 니가타 앞바다 해안 밖
d["paths"]["layla2"][4] = [138.6, 38.15]

# 5) 사진 추가(D-0239, UF-119) — 시설·항구 소개 문장에만(사건 장면처럼 쓰지 않는다), 모두 자료사진 표기(레지스트리 file_note)
PHOTOS = [("act2_6", "diesel_road_2026_khabarovsk_ref_2005"), ("act2_17", "diesel_road_2026_vladivostok_port_1992"),
          ("act4_12", "diesel_road_2026_ras_laffan_lng_2012"), ("act4_19", "hormuz_transit")]
for sid, mid in PHOTOS:
    if not find(lambda e, m=mid: e["type"] == "photo" and e.get("mid") == m):
        ev.append({"type": "photo", "start": {"sid": sid, "off": 0.3}, "end": {"sid": sid, "edge": "end", "off": 0.3}, "mid": mid, "place": "map_left"})
ev[:] = [e for e in ev if not (e["type"] == "card" and sid_of(e) == "act4_12")]   # 사진과 같은 자리의 요지 카드는 뺀다(급전환 방지)

# 6) 계단 카드 제목 폭(cascade-overflow) — 긴 제목은 줄이고 나머지는 line 으로
for e in ev:
    if e["type"] == "cascade":
        for it in e["items"]:
            if it["title"] == "6대 경유 정유소 중 세 곳 감산·중단":
                it.update(title="6대 정유소 중 3곳", line="감산·중단")
            elif it["title"] == "경유 해상 수출 하루 약 14만 6천 배럴":
                it.update(title="경유 해상 수출 감소", line="하루 약 14만 6천 배럴")

# 7) 카메라(D-0229 §4.1·§4.2·UF-106) — 넓은 지도 오프닝, 타격지·항구 근접 숏(w 6~10), 전후 이동은 느리게(≥ 4초)
def cam(lon, lat, w):
    return {"lon": lon, "lat": lat, "w": w}
d["shots"] = [
    {"at": 0.0, "mode": "cut", "dur": 0.0, "camera": cam(46.0, 52.0, 40.0)},
    {"at": {"sid": "cold_0", "off": 0.5}, "mode": "move", "dur": 11.0, "camera": cam(39.0, 54.9, 12.0), "reason": "랴잔 근접(모스크바·랴잔·M5 도로)"},
    {"at": {"sid": "cold_1", "off": -0.5}, "mode": "move", "dur": 6.5, "camera": cam(38.5, 54.0, 30.0), "reason": "러시아·우크라이나 한 화면(출발지와 함께)"},
    {"at": {"sid": "cold_4", "off": -0.4}, "mode": "dip", "dur": 2.6, "camera": cam(129.6, 36.3, 14.0), "reason": "무대 전환 — 울산"},
    {"at": {"sid": "cold_4", "off": 2.3}, "mode": "move", "dur": 6.0, "camera": cam(129.35, 35.6, 8.0), "reason": "울산항 근접 — 느린 이동 뒤 타이틀(§4.1)"},
    {"at": {"card": "title", "off": 2.9}, "mode": "dip", "dur": 3.0, "camera": cam(42.0, 55.4, 38.0), "under": True},
    {"at": {"sid": "act1_13", "off": -0.6}, "mode": "move", "dur": 4.5, "camera": cam(40.3, 54.8, 36.0), "reason": "키리시·사라토프·시즈란"},
    {"at": {"sid": "act1_14", "off": 0.0}, "mode": "move", "dur": 5.0, "camera": cam(42.0, 55.4, 38.0)},
    {"at": {"scene_start": "act2", "off": -0.55}, "mode": "dip", "dur": 3.0, "camera": cam(130.5, 47.0, 26.0)},
    {"at": {"sid": "act2_6", "off": -0.5}, "mode": "move", "dur": 4.5, "camera": cam(136.1, 49.4, 10.0), "reason": "하바롭스크·콤소몰스크 정유소 근접"},
    {"at": {"sid": "act2_10", "off": -3.0}, "mode": "move", "dur": 5.0, "camera": cam(131.0, 46.0, 24.0)},
    {"at": {"sid": "act2_13", "off": -0.6}, "mode": "move", "dur": 4.5, "camera": cam(131.0, 38.0, 26.0)},
    {"at": {"sid": "act2_23", "off": -0.5}, "mode": "move", "dur": 4.5, "camera": cam(131.2, 39.3, 21.0), "reason": "니가타 꺾임점까지"},
    {"at": {"sid": "act2_29", "off": -0.4}, "mode": "move", "dur": 4.0, "camera": cam(128.3, 34.75, 8.0), "reason": "여수 앞바다 근접"},
    {"at": {"sid": "act2_29", "off": 4.0}, "mode": "move", "dur": 4.5, "camera": cam(130.2, 38.4, 26.0)},
    {"at": {"scene_start": "act3", "off": -0.8}, "mode": "move", "dur": 4.5, "camera": cam(127.4, 37.3, 9.0)},
    {"at": {"scene_start": "act4", "off": -0.55}, "mode": "dip", "dur": 3.0, "camera": cam(50.5, 27.5, 26.0)},
    {"at": {"sid": "act4_3", "off": -0.4}, "mode": "move", "dur": 4.5, "camera": cam(50.6, 28.8, 9.0), "reason": "하르그섬 근접"},
    {"at": {"sid": "act4_5", "off": -0.3}, "mode": "move", "dur": 5.0, "camera": cam(44.5, 29.5, 24.0), "reason": "이스라엘·이란·사우스파르스 한 화면"},
    {"at": {"sid": "act4_9", "off": -0.4}, "mode": "move", "dur": 4.5, "camera": cam(51.6, 26.3, 9.0), "reason": "라스라판 근접"},
    {"at": {"sid": "act4_13", "off": -0.4}, "mode": "move", "dur": 5.0, "camera": cam(50.7, 27.6, 24.0)},
    {"at": {"sid": "act4_25", "off": -3.0}, "mode": "move", "dur": 5.0, "camera": cam(60.0, 50.0, 64.0), "reason": "러시아와 걸프를 한 화면에(경유 부족 두 원인)"},
    {"at": {"scene_start": "act5", "off": -0.55}, "mode": "dip", "dur": 3.0, "camera": cam(38.0, 54.0, 30.0)},
    {"at": {"sid": "act5_24", "off": -2.6}, "mode": "move", "dur": 4.5, "camera": cam(35.6, 50.0, 12.0), "reason": "하르키우·폴타바"},
    {"at": {"sid": "act5_25", "off": -0.4}, "mode": "move", "dur": 4.5, "camera": cam(38.9, 54.0, 10.0), "reason": "랴잔 재타격 근접"},
    {"at": {"sid": "act5_26", "off": -0.3}, "mode": "move", "dur": 5.0, "camera": cam(38.0, 54.0, 30.0)},
    {"at": {"scene_start": "ending", "off": -0.55}, "mode": "dip", "dur": 3.0, "camera": cam(89.0, 43.5, 94.0)},
]

# 8) 문장이 부르는 나라가 화면 밖일 때(frame_missing) — 그 나라 국기 뱃지(rules: 국기 뱃지 = 표시)
FLAGS = [("act2_0", "ru", "러시아 극동", 141.5, 50.0, "act2_5", 0.2), ("act2_10", "ua", "우크라이나에서 약 6,500km", 138.2, 44.6, None, 0.3),
         ("act2_14", "ru", "러시아", 136.0, 40.5, "act2_17", 0.2), ("act2_31", "ru", "러시아", 134.4, 42.4, "act2_32", 0.2),
         ("act3_1", "ua", "우크라이나", 129.6, 38.9, None, 0.2), ("act3_15", "ru", "러시아", 129.6, 38.9, None, 0.2),
         ("act3_17", "ua", "우크라이나", 129.6, 38.9, "act3_21", 0.2), ("act3_18", "ru", "러시아", 124.6, 36.9, None, 0.2),
         ("act3_27", "ua", "우크라이나", 129.6, 38.9, None, 0.2), ("act5_24", "ru", "러시아", 38.6, 51.4, None, 0.5), ("act3_28", "kp", "북한", 126.6, 38.25, None, 0.2)]
for f in FLAGS:
    sid, cc, lab, lon, lat, upto, off = f
    upto = upto or sid
    if not find(lambda e, s=sid, c=cc: e["type"] == "badge" and e.get("kind") == "flag" and e.get("flag") == c and sid_of(e) == s):
        ev.append({"type": "badge", "kind": "flag", "flag": cc, "label": lab, "lon": lon, "lat": lat,
                   "start": {"sid": sid, "off": off}, "end": {"sid": upto, "edge": "end", "off": 0.3}, "accent": "ru" if cc == "ru" else "teal"})

# 9) 겹침·가림 정리
for e in ev:
    if e["type"] == "marker" and e.get("at_place") in ("khabarovsk_ref", "komsomolsk_ref"):
        e["end"] = {"sid": "act2_10", "edge": "end", "off": 0.2}
    if e["type"] == "marker" and e.get("at_place") == "ryazan" and sid_of(e) == "act5_25":
        e["end"] = {"sid": "act5_25", "edge": "end", "off": 0.3}
    if e["type"] == "marker" and e.get("at_place") == "yeosu_off":
        e.update(side="top", sub="옮겨 싣기")
    if e["type"] == "marker" and e.get("at_place") == "ulsan" and sid_of(e) == "act2_14":
        e["end"] = {"sid": "act2_28", "edge": "end", "off": 0.3}
    if e["type"] == "marker" and e.get("at_place") == "poltava":
        e["side"] = "left"
    if e["type"] == "marker" and e.get("at_place") == "kharkiv":
        e["side"] = "right"
    if e["type"] == "badge" and e.get("pid") == "zelensky" and sid_of(e) == "act5_23":
        e.update(lon=31.0, lat=53.4)
    if e["type"] == "badge" and e.get("pid") == "zelensky" and sid_of(e) == "act5_27":
        e.update(lon=35.2, lat=55.2)
    if e["type"] == "marker" and e.get("at_place") in ("khabarovsk_ref", "komsomolsk_ref"):
        e["side"] = "left"
    if e["type"] == "badge" and e.get("pid") == "trump" and sid_of(e) == "act4_4":
        e.update(lon=48.6, lat=30.6)
    if e["type"] == "marker" and e.get("at_place") == "moscow" and sid_of(e) == "cold_0":
        e["end"] = {"sid": "cold_0", "edge": "end", "off": 0.3}
    if e["type"] == "marker" and e.get("at_place") in ("khabarovsk_ref", "komsomolsk_ref"):
        e["end"] = {"sid": "act2_9", "edge": "end", "off": 0.2}
    if e["type"] == "route" and e.get("label") == "철도":
        e["end"] = {"sid": "act2_5", "edge": "end", "off": 0.6}
    if e["type"] == "route" and e.get("label") == "청천호":
        e["start"] = {"sid": "act2_30", "off": 1.5}
    if e["type"] == "marker" and e.get("at_place") == "yeosu_off":
        e.update(start={"sid": "act2_29", "off": 2.0}, end={"sid": "act2_29", "edge": "end", "off": 0.2})
    if e["type"] == "marker" and e.get("at_place") == "ulsan" and sid_of(e) == "act2_14":
        e["end"] = {"sid": "act2_22", "edge": "end", "off": 0.3}
    if e["type"] == "marker" and e.get("at_place") == "fujairah":
        e["side"] = "left"
d["places"]["gulf_label"] = [51.5, 29.6]
for e in ev:
    if e["type"] == "marker" and e.get("at_place") == "hormuz":
        e["end"] = {"sid": "act4_21", "edge": "end", "off": 0.3}
    if e["type"] == "marker" and e.get("at_place") == "gulf_label":
        e["side"] = "top"
    if e["type"] == "marker" and e.get("at_place") == "kharkiv":
        e["side"] = "right"
    if e["type"] == "badge" and e.get("pid") == "novak":
        e.update(lon=41.0, lat=56.4)
ev[:] = [e for e in ev if not (e["type"] == "article" and e.get("mid") in ("diesel_road_2026_art_0010", "diesel_road_2026_art_0013"))]   # cutaway-churn(UF-110)
for e in ev:
    if e["type"] == "panel" and e.get("kind") == "dots":
        dd = e["data"]
        if dd.get("big") == "14건":
            dd.update(big="14", unit="건")
        elif dd.get("big") == "70%":
            dd.update(big="70", unit="%")
        elif dd.get("big") == "3 / 7":
            dd["unit"] = "척"
ev[:] = [e for e in ev if not (e["type"] == "marker" and e.get("at_place") == "gulf_label")]   # 러시아 라벨과 한 화면이면 늘 자막 띠 — 맺음 요약은 내레이션이 진다

P.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
print("events", len(ev))
