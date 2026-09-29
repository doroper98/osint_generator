"""지명 사전 만들기 (v4.10.0 back_and_forth D-0116 작업 1, B-1).

    python tools/build_gazetteer.py [--ne-dir data/geo/ne] [--out data/gazetteer.yaml]

`data/gazetteer.yaml`(저장소 추적 파일)의 `ne` 절을 Natural Earth 10m populated places(퍼블릭 도메인)에서 다시 만든다.
`manual` 절(해협·섬·만·공항·기지·국가 — 사람이 출처와 허용 오차를 적은 항목)은 **그대로 둔다**.

- 수록 기준 = 수도(ADM0CAP 1 또는 FEATURECLA 에 "Admin-0 capital") 또는 POP_MAX ≥ `rules geo.gazetteer.ne_min_population`.
- 이름 = NAME·NAMEASCII·NAME_EN·NAMEALT·NAME_KO(+ 행정 접미사 뗀 한국어, 있는 것, 중복 제거). 좌표 소수 4자리. 허용 오차 = `rules geo.gazetteer.ne_tol_km`.
- 기록: 원본 URL·md5·라이선스·수록 기준을 `source` 에 남긴다(C9 권리 기록). 원본 파일은 `python tools/fetch_data.py ne`(또는 geo.prep)가 받는다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from engine.gazetteer import Gazetteer, GazetteerEntry  # noqa: E402
from rules import load_rules  # noqa: E402
from tools.fetch_data import NE_URL  # noqa: E402

NE_NAME = "ne_10m_populated_places"
LICENSE = "Natural Earth — public domain (naturalearthdata.com/about/terms-of-use)"
DIGITS = 4
HEADER = """\
# 지명 사전 (v4.10.0 back_and_forth D-0116 작업 1, B-1) — engine.gazetteer 가 checks [geo-mismatch]·[geo-unsourced] 에 쓴다.
# manual = 사람이 적은 항목(출처 src·허용 오차 tol_km 필수). ne = tools/build_gazetteer.py 가 생성(손으로 고치지 않는다).
"""


def _p(props: dict, key: str) -> object:
    return props.get(key, props.get(key.lower()))


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.casefold()).strip("_") or "x"


KO_ADMIN_SUFFIX = re.compile(r"(특별자치시|특별시|광역시|직할시|시)$")   # "서울특별시" → "서울"(자막·라벨 표기)


def _names(p: dict) -> list[str]:
    """NAME·NAMEASCII·NAME_EN·NAMEALT(| 구분)·NAME_KO·NAME_KO 행정 접미사 뗀 것."""
    out = [str(_p(p, k) or "").strip() for k in ("NAME", "NAMEASCII", "NAME_EN")]
    out += [a.strip() for a in str(_p(p, "NAMEALT") or "").split("|")]
    ko = str(_p(p, "NAME_KO") or "").strip()
    short = KO_ADMIN_SUFFIX.sub("", ko)
    return [*out, ko, short if len(short) >= 2 else ""]


def ne_entries(raw: bytes, min_pop: int, tol_km: float) -> list[GazetteerEntry]:
    doc = json.loads(raw)
    out: list[GazetteerEntry] = []
    used: set[str] = set()
    for f in doc["features"]:
        p = f["properties"]
        cap = _p(p, "ADM0CAP") in (1, 1.0) or "admin-0 capital" in str(_p(p, "FEATURECLA") or "").casefold()
        pop = _p(p, "POP_MAX") or 0
        if not (cap or pop >= min_pop):
            continue
        names = list(dict.fromkeys(n for n in _names(p) if n))
        if not names:
            continue
        base = f"{_slug(str(_p(p, 'NAMEASCII') or names[0]))}_{_slug(str(_p(p, 'ADM0_A3') or _p(p, 'SOV_A3') or 'xx'))}"
        eid, k = base, 2
        while eid in used:
            eid, k = f"{base}_{k}", k + 1
        used.add(eid)
        x, y = f["geometry"]["coordinates"][:2]
        out.append(GazetteerEntry(id=eid, names=names, lonlat=(round(x, DIGITS), round(y, DIGITS)), tol_km=tol_km,
                                  kind="capital" if cap else "city", src="ne"))
    return out


def dump(g: Gazetteer) -> str:
    """한 항목 한 줄(흐름 형식) — diff 가 항목 단위로 보이게."""
    def line(e: GazetteerEntry) -> str:
        d = e.model_dump()
        d["lonlat"] = list(d["lonlat"])
        return "  - " + yaml.safe_dump(d, default_flow_style=True, allow_unicode=True, sort_keys=False, width=10**6).strip()

    head = yaml.safe_dump({"schema_version": g.schema_version, "source": g.source}, allow_unicode=True, sort_keys=False)
    body = ["manual:", *(line(e) for e in g.manual), "ne:", *(line(e) for e in g.ne)]
    return HEADER + head + "\n".join(body) + "\n"


def build(raw: bytes, manual: list[GazetteerEntry]) -> Gazetteer:
    gr = load_rules().geo.gazetteer
    ne = ne_entries(raw, gr.ne_min_population, gr.ne_tol_km)
    ids = [e.id for e in manual]
    if len(set(ids)) != len(ids):
        raise ValueError(f"manual id 중복: {sorted({i for i in ids if ids.count(i) > 1})}")
    return Gazetteer(schema_version=1, manual=manual, ne=ne, source={
        "ne": NE_URL.replace("{name}", NE_NAME), "ne_md5": hashlib.md5(raw).hexdigest(), "license": LICENSE,  # noqa: S324 — 식별용
        "ne_filter": f"capital or POP_MAX >= {gr.ne_min_population}", "ne_tol_km": gr.ne_tol_km, "ne_count": len(ne),
        "manual": "사람이 적은 항목 — 항목마다 src(출처)·tol_km", "built_by": "tools/build_gazetteer.py"})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="tools.build_gazetteer")
    ap.add_argument("--ne-dir", type=Path, default=REPO / "data" / "geo" / "ne")
    ap.add_argument("--out", type=Path, default=REPO / load_rules().geo.gazetteer.path)
    args = ap.parse_args(argv)
    src = args.ne_dir / f"{NE_NAME}.geojson"
    if not src.exists():
        print(f"없음: {src} — `python tools/fetch_data.py ne` 먼저", file=sys.stderr)
        return 1
    manual: list[GazetteerEntry] = []
    if args.out.exists():   # manual 절 보존
        old = yaml.safe_load(args.out.read_text(encoding="utf-8")) or {}
        manual = [GazetteerEntry.model_validate(e) for e in old.get("manual") or []]
    g = build(src.read_bytes(), manual)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dump(g), encoding="utf-8")
    Gazetteer.model_validate(yaml.safe_load(args.out.read_text(encoding="utf-8")))   # 다시 읽어 검증
    print(f"{args.out}: manual {len(g.manual)} · ne {len(g.ne)} · {args.out.stat().st_size} B", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
