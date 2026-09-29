"""지명 사전 대조 — 렌더 엔진 밖 지오 도구(구면 거리 계산이라 engine 무대 격리 밖에 둔다, anti_inertia test_stage_isolation) (v4.10.0 back_and_forth D-0116 작업 1, B-1 — D-0107 D2(b) 의 후속).

지도 무대의 이름 붙은 좌표를 `data/gazetteer.yaml`(추적 파일, `rules geo.gazetteer.path`)과 대조한다.

- 대조 이름: place 키 + 그 place 를 쓰는(`at_place`) marker 의 label, 인라인 좌표 marker 의 label.
  이름 정규화 = 소문자·`_`/`-` → 공백·공백 하나로(`norm_name`).
- 이름이 사전 항목(여러 개일 수 있다 — 동음이의)과 맞으면: 연출 좌표가 **맞은 항목 중 하나라도** 그 항목의 `tol_km` 안이면 통과,
  모두 밖이면 `[geo-mismatch]`(checks hard). 가장 가까운 항목과 거리를 기록한다.
- 맞는 이름이 없으면 종전대로 `[geo-unsourced]`(warning). 사건 지점은 사전에 넣지 않는다(연출 문법: sub "좌표 비공개").
- paths·인라인 route 는 이름이 점 하나를 가리키지 않아 대조하지 않는다(unsourced 그대로).

사전 = `manual`(수기 — 해협·섬·만·공항·기지·국가, 항목마다 출처·tol_km) + `ne`(`tools/build_gazetteer.py` 가 NE 10m populated places 에서 생성).
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
EARTH_R_KM = 6371.0088   # 평균 지구 반경(IUGG)


class GazetteerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    names: list[str] = Field(min_length=1)          # 영문·한국어 등 대조 이름(정규화 전)
    lonlat: tuple[float, float]
    tol_km: float = Field(gt=0)
    kind: str = Field(min_length=1)                 # capital·city·strait·island·gulf·airport·landmark·country …
    src: str = Field(min_length=1)                  # 출처(manual 은 문헌·좌표 표기, ne 는 "ne")


class Gazetteer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    source: dict[str, Any]                          # 원본 URL·md5·라이선스·수록 기준(C9 권리 기록)
    manual: list[GazetteerEntry]
    ne: list[GazetteerEntry]

    def entries(self) -> list[GazetteerEntry]:
        return [*self.manual, *self.ne]


def norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[_\-]", " ", s.strip().casefold())).strip()


def haversine_km(a: tuple[float, float] | list[float], b: tuple[float, float] | list[float]) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_R_KM * math.asin(math.sqrt(min(1.0, h)))


def gazetteer_path() -> Path:
    return REPO / load_rules().geo.gazetteer.path


@lru_cache(maxsize=4)
def load_gazetteer(path: Path | None = None) -> Gazetteer:
    """사전 로드(한 번). 파일이 없거나 형식 오류면 예외 — 조용히 대조를 건너뛰지 않는다(15 P6)."""
    p = path or gazetteer_path()
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return Gazetteer.model_validate(yaml.load(p.read_text(encoding="utf-8"), Loader=loader))  # noqa: S506 — SafeLoader


def name_index(g: Gazetteer) -> dict[str, list[GazetteerEntry]]:
    """정규화 이름 → 항목들(동음이의 여러 개)."""
    idx: dict[str, list[GazetteerEntry]] = {}
    for e in g.entries():
        for n in dict.fromkeys(norm_name(x) for x in e.names):
            idx.setdefault(n, []).append(e)
    return idx


def lookup(idx: dict[str, list[GazetteerEntry]], names: list[str]) -> list[GazetteerEntry]:
    """이름들 중 하나라도 맞는 항목(중복 없이, 사전 순서)."""
    seen: dict[str, GazetteerEntry] = {}
    for n in names:
        for e in idx.get(norm_name(n), []):
            seen.setdefault(e.id, e)
    return list(seen.values())


def judge_point(idx: dict[str, list[GazetteerEntry]], names: list[str], lonlat: list[float]) -> dict[str, Any] | None:
    """None = 사전에 없는 이름(unsourced). 아니면 {"ok", "entry", "km", "tol_km"} — 가장 가까운(오차 대비) 항목 기준."""
    cands = lookup(idx, names)
    if not cands:
        return None
    best = min(cands, key=lambda e: haversine_km(lonlat, e.lonlat) / e.tol_km)
    km = haversine_km(lonlat, best.lonlat)
    return {"ok": km <= best.tol_km, "entry": best.id, "km": round(km, 1), "tol_km": best.tol_km}


def check_doc(doc: Any, items: list[dict[str, Any]], g: Gazetteer | None = None) -> dict[str, list[dict[str, Any]]]:
    """`engine.direction.geo_unsourced(doc)` 후보 → {"unsourced", "matched", "mismatch"}.

    place 는 키 + 그 place 를 쓰는 marker label, 인라인 marker 는 label 로 대조한다. path·route 는 unsourced 그대로.
    """
    idx = name_index(g or load_gazetteer())
    labels: dict[str, list[str]] = {}
    for e in doc.events:
        f = {**e, **(e.get("data") or {})}
        if e.get("type") == "marker" and e.get("at_place") and f.get("label"):
            labels.setdefault(str(e["at_place"]), []).append(str(f["label"]))
    out: dict[str, list[dict[str, Any]]] = {"unsourced": [], "matched": [], "mismatch": []}
    for it in items:
        if it["kind"] == "place":
            names = [it["name"], *labels.get(it["name"], [])]
        elif it["kind"] == "marker":
            names = [it["name"].split(" ", 1)[1]] if " " in it["name"] else []   # "events[i] label"
        else:
            out["unsourced"].append(it)
            continue
        j = judge_point(idx, names, it["lonlat"]) if names else None
        if j is None:
            out["unsourced"].append(it)
        else:
            out["matched" if j["ok"] else "mismatch"].append({**it, "gazetteer": j["entry"], "km": j["km"], "tol_km": j["tol_km"]})
    return out


__all__ = ["Gazetteer", "GazetteerEntry", "check_doc", "gazetteer_path", "haversine_km", "judge_point", "load_gazetteer", "lookup",
           "name_index", "norm_name"]
