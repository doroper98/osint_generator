"""지오 자산 단계 (v2.2.0, Phase 3) — 국가·행정구역·도시 지오메트리와 지형 티어를 권역 인자로 만든다.

prep3(legacy_v3) 의 `polys, rings, load_*, mosaic, build_tier` 를 그대로 옮기고 권역·티어를 인자로 받는다.
입력 캐시(Natural Earth·지형 타일)는 저장소 `data/geo/`(gitignore), 산출물은 프로젝트 `assets/`.
"""
