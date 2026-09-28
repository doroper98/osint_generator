<!--
tier: 2
last_synced_with: v4.0.0
ssot_for: [map-geo-index]
depends_on: [docs/handoff/04_MAP_ENGINE.md, docs/handoff/05_CAMERA_SHOTS_TRANSITIONS.md, docs/handoff/06_OVERLAYS_AND_DATA_LAYERS.md, rules/video_rules.yaml, config.yaml]
last_review: 2026-09-29
-->

# 09 — 지도·지오 명세 (v4.0.0 재작성)

지도 엔진의 안내도다. 정본은 handoff 04(지도 엔진)·05(카메라)·06(오버레이)이다.
수치의 정본은 `rules/video_rules.yaml`(`rules:labels`, `rules:geo`, `rules:camera`)과 프로젝트별 `geo.yaml`·`labels.yaml`이다. 값은 복사하지 않는다.
옛 판(v0.3.3 — 장면 템플릿용 지도)은 폐기됐다.

---

## 1. 좌표계와 투영

메르카토르 "도 단위"를 쓴다. u = 경도, v = 메르카토르 위도를 도로 환산한 값이다. 두 축이 모두 도라서 ppd(도당 픽셀) 하나로 축척이 정해진다.
카메라는 (경도, 위도, w)로 쓴다. w는 화면 가로가 덮는 경도 폭이다. 구현은 `engine/projection.py`(`ym`, `View`), 정본은 handoff 04 §1.

## 2. 지오 자산 단계 — `geo.prep`

```bash
python -m geo.prep projects/<pid>                 # → assets/{geo.pkl, tiers.pkl, base_*.png, geo_report.json}
python -m geo.prep projects/<pid> --res 1080p     # → assets/res_1080p/ (480p 자산은 건드리지 않는다)
```

| 입력 | 뜻 | 정본 |
|---|---|---|
| 프로젝트 `geo.yaml` `bbox` | 국가 지오메트리 권역 | handoff 04 §3 |
| `admin1` | 1급 행정구역을 준비할 나라 | handoff 04 §6 |
| `crimea_to_ua` | 크림반도 재분류(우크라이나 관련 영상) | handoff 04 §3.2 |
| `tiers` | 지형 티어(이름·ppd·타일 줌·bbox) | handoff 04 §4 |

- 데이터는 Natural Earth 3종과 terrarium 지형 타일이다. 캐시는 `data/geo/`(gitignore)이고 `tools/fetch_data.py`가 받는다.
- 재귀 평탄화로 GeometryCollection 속 폴리곤을 놓치지 않는다(프랑스 버그, handoff 04 §3.3).
- 티어 박스가 덮는 타일이 하나라도 없으면 오류다(15 P6). 박스는 메르카토르 한계로 클램프한다.
- **land-miss**(대표점이 육지로 칠해지지 않은 나라)는 `geo_report.json`에 남긴다. 작은 섬은 허용, 그 이상은 drops로 올려 실패한다(`rules:geo.land_miss_allow_px2`, D29).
- 팔레트·힐셰이드·과장·블러는 v3 사용자 합격 값이다(handoff 04 §4.6, D27). 코드 상수로 새로 적지 않는다.
- 새 권역을 추가하는 절차는 handoff 04 §9 체크리스트를 따른다.

## 3. 티어와 해상도

| 항목 | 규칙·설정 키 | 정본 |
|---|---|---|
| 설계 좌표(한 벌) | `rules:layout_480p.base` | handoff 09 §2 |
| 출력 프로파일(장치 크기·fps·인코딩) | `config:engine.output`, `config:engine.trial`, `config:engine.final` | [10](10_RENDERING_PIPELINE_SPEC.md) §4 |
| 1080p 비율 검증 상한 | `rules:golden.res_compare_mad_max` | D60·D63 |

**해상도 변환은 렌더 진입 장치 변환 한 곳이다**(D60, back_and_forth D-0067). 레이어·패널·checks는 설계 854×480 좌표만 본다.
지도·지형·인물·국기·사진·클립 같은 래스터만 장치 해상도로 준비한다. 그래서 `geo.prep --res`가 ppd에 k를 곱한 티어를 따로 만든다.
k = 출력 높이 ÷ 480이고, 타일 줌은 round(log2 k)만큼 올린다. 블러 반경도 k배다.
옛 문구 "모든 픽셀 상수를 `style.px()`로 감싼다"(handoff 09 §2 초안)는 철회됐다. 리터럴을 감싸면 k=1에서 반올림 차이가 생겨 480p MAD 0이 깨졌다.
원본 해상도가 장치 폭보다 작으면 업스케일하지 않고 checks `media_upscaled`(warning)로 알린다. 영상 클립은 원본에서 프로파일별 npy를 따로 뽑는다([10](10_RENDERING_PIPELINE_SPEC.md) §4, D-0074).

## 4. 라벨 LOD

확대하면 정보가 늘어난다. 해역·국가·도(道)·도시 라벨이 화면 폭(w)에 따라 나타나고, 마커·뱃지·컷아웃이 차지한 자리는 피한다.

| 항목 | 키 | 정본 |
|---|---|---|
| 국경 LOD 폭 | `rules:labels.border_lod_w` | handoff 04 §6 |
| 행정구역 선 페이드 폭 | `rules:labels.admin1_fade_w` | handoff 04 §6 |
| 도(道) 라벨 최대 폭 | `rules:labels.province_w_max` | handoff 04 §7.4 |
| 국가·도시 순위 임계 | `rules:labels.country_rank_thr`, `rules:labels.city_rank_thr` | handoff 04 §7.3·§7.5 |
| 프레임당 도시 라벨 상한 | `rules:labels.city_max_per_frame`, `rules:qa_checks.labels_per_frame_max` | handoff 04 §7 |
| 카드에 가린 라벨(D61) | `rules:qa_checks.label_hidden_max_ratio` | back_and_forth D-0068 |

국가 한글 관용명·해역 이름과 표시 폭·도 라벨 대상국은 프로젝트 `labels.yaml`이 정한다. 구현은 `engine/layers/labels.py`.

## 5. 프레이밍

`engine/framing.py`의 `frame_points`가 장면 장소를 모두 한 화면에 넣는 최소 w와 중심을 구한다. 제안만 하고 연출에 자동 적용하지 않는다(P8).

| 항목 | 키 | 정본 |
|---|---|---|
| 여백·w 범위·탐색 격자 | `rules:camera.framing` | handoff 05 §2.1·§7-1 |
| 요소별 차지 상자(마커·뱃지·점) | `rules:camera.framing.marker_px`, `rules:camera.framing.badge_px`, `rules:camera.framing.point_px` | handoff 05 §2.1 |
| 맥락 폭 하한 = 숏 분류 추론(D54) | `rules:camera.framing.context_w_min`, `rules:shot_grammar.w_guide` | back_and_forth D-0058 |

맥락 폭 하한은 장소 종류가 아니라 현재 카메라 w가 속한 숏 구간으로 정한다. 같은 장소도 숏 의도에 따라 폭이 다르기 때문이다.
이벤트별 `scale` 필드는 보류 중이다(NB18, DECISIONS 기록 예정).

## 6. 지도 위 오버레이

마커·경로·유조선·호·봉쇄선·선박 입자·점령지·국가 강조의 그리기 명세는 handoff 06이 정본이다. 레이어 순서는 handoff 06 §9.
이벤트 타입은 `rules:registries.event_types`에 등재돼야 한다. 등재 안 된 타입은 오류다(P10).
