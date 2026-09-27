"""참고 사본 (v2.0.0) — 원본: hyperframes/scripts/bundle_to_video.py (archive/hyperframes-briefing).

실행 대상이 아니다. Phase 9 번들 map 이식 시 참고용 — 삭제된 권역 SVG 메타에 의존하므로 새 엔진 지오(04)로 다시 쓴다.
"""

def _load_map_metas() -> list[dict]:
    metas = []
    for f in sorted(MAPS_DIR.glob("*_map.meta.json")):
        metas.append(json.loads(f.read_text(encoding="utf-8")))
    return metas


def _project_merc(meta: dict, lng: float, lat: float) -> tuple[float, float]:
    """d3 geoMercator 와 동일: x = t0 + k·λ, y = t1 − k·ln(tan(π/4 + φ/2))."""
    k = meta["k"]
    tx, ty = meta["t"]
    x = tx + k * math.radians(lng)
    y = ty - k * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return round(x, 1), round(y, 1)


MAP_KIND_COLOR = {"flow": "ACCENT", "subject": "OXIDE", "ally": "SAGE", "rival": "SLATE"}


def norm_map(map_data: dict) -> dict | None:
    """번들 map → geo 씬 데이터. 마커 bbox 를 포함하는 권역 베이스맵 선택."""
    markers = map_data.get("markers") or []
    if len(markers) < 2:
        return None
    lngs = [m["lng"] for m in markers]
    lats = [m["lat"] for m in markers]
    meta = None
    for cand in _load_map_metas():
        (lo_lng, lo_lat), (hi_lng, hi_lat) = cand["bbox"]
        if all(lo_lng <= g <= hi_lng for g in lngs) and all(lo_lat <= a <= hi_lat for a in lats):
            meta = cand
            break
    if not meta:
        print(f"[bundle_to_video] map 권역 미지원 (lng {min(lngs)}~{max(lngs)}) — geo 씬 생략")
        return None
    out_markers = []
    for m in markers:
        x, y = _project_merc(meta, m["lng"], m["lat"])
        out_markers.append({"id": m["id"], "name": clip(m.get("name", ""), 12),
                            "note": clip(re.sub(r"\s*\([^)]*\)", "", m.get("value", "") or "").strip(), 26) or None,
                            "x": x, "y": y, "hi": bool(m.get("highlight"))})
    arcs = []
    for a in (map_data.get("arcs") or [])[:4]:
        arcs.append({"id": f'{a["from_id"]}-{a["to_id"]}', "from": a["from_id"], "to": a["to_id"],
                     "kind": a.get("kind", "flow"), "width": min(5, 2 + (a.get("weight") or 2)),
                     "label": clip(a.get("label", "") or "", 30) or None,
                     "labelT": a.get("label_t", 0.5)})
    legend = [{"label": clip(item.get("label", ""), 16), "kind": item.get("kind", "")}
              for item in (map_data.get("legend") or [])[:5]]
    inferred = ((map_data.get("provenance") or {}).get("verification") or "") != "official"
    return {"region": meta["region"], "markers": out_markers, "arcs": arcs,
            "legend": legend, "inferred": inferred}

