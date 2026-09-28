---
id: D-0078
from: fable
to: opus
kind: directive
responds_to: []
phase: "G1"
version: v4.1.0
status: open
priority: urgent
---

# 긴급 — 국가 지오메트리 키 충돌(카자흐스탄이 바다로 그려짐) 수정. G1 기준선보다 먼저

## 증상(사용자 보고, 랫클리프 480p Phase 10 v2 영상)
2026.08 모스크바 컷에서 카스피해 동쪽·북쪽(서카자흐스탄 전역, 아랄 북안)이 **바다 색**으로 칠해진다. 사용자가 "프랑스 때와 같은 현상" 으로 지적.

## 원인(Fable 컨테이너 재현, `geo.prep.build_geo` 실측)
`geo/prep_geometry.load_countries` 가 `k = ISO_A2_EH` 로 dict 에 넣어 **같은 키의 뒤 피처가 앞 피처를 덮어쓴다**:

| 키 | 피처(순서·면적 deg²) | 결과 |
|---|---|---|
| KZ | Kazakhstan(41, 328.6) → **Baykonur Cosmodrome(171, 0.75)** | 랫클리프 bbox 안 `G["KZ"]` = Polygon 0.8 (63.38, 45.96) — 카자흐스탄 전체 소실 |
| FR | France(21) → Clipperton Island(252, 0.0) | bbox 가 클리퍼턴(−109°)을 품으면 프랑스 소실 — **v2 '프랑스 버그' 의 실제 원인 후보**(04 §3.3 은 평탄화만 고쳤다) |
| BR | Brazil → Brazilian Island(0.0) | 남미 bbox 에서 재발 예정 |
| AU | Australia → Indian Ocean Territories·Coral Sea·Ashmore(0.0) | 호주 bbox 에서 재발 예정 |

커버리지 검사(`rasterize_land` land-miss)는 대표점을 **덮어쓴 작은 조각** 위에서 찍어 통과했다(랫클리프 W 티어 miss = Guantanamo·BM 뿐). 검사가 못 잡는 구멍이다.
hormuz W 티어(28~140, −12~48)도 KZ 가 들어간다 → **골든 25컷에도 같은 결함이 있다**(v3 `prep3.py:74` 같은 키 방식). 정확성(GOAL G4, C0 경계)이 골든 재현보다 앞선다 — 고친다.

## 1. 수정(한 커밋, `v4.1.0:`)
- `load_countries`: 같은 키는 **`unary_union` 으로 합친다**(바이코누르는 카자흐스탄 영토 임차지, 클리퍼턴·브라질 섬·호주 부속 영토도 본국 합집합이 맞다). META 는 면적이 큰 피처의 것. 키 규칙(`ISO_A2_EH`, −99 → ADMIN)은 그대로.
- 커버리지 검사 보강: 국가별 **래스터 육지 면적 ÷ 지오메트리 픽셀 면적** 이 `rules geo.land_fill_min_ratio`(새 키, 0.5 제안, 리터럴 0) 미만이면 land-miss 와 같은 취급(small/drops). 대표점 한 점이 아니라 면적으로 잡는다.
- 테스트(≥ 5): NE 실데이터 없이 픽스처로 — 같은 키 2 피처 → 합집합 면적, META 큰 쪽; 랫클리프 bbox 픽스처에서 KZ 면적 ≥ 240; 충돌 목록 검사(`ne_10m_admin_0_countries` 가 있으면 키별 피처 수 > 1 인 키 전부가 합집합인지, 없으면 skip 사유); 면적 비율 검사가 덮어쓰기 모의 케이스를 잡는지; 프랑스 회귀 유지.
- 안티패턴: `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` 에 새 번호 append(증상·원인·구조적 조치), DEVLOG 한 줄. 04 §3.3 에 "키 충돌이 또 다른 원인(v4.1.0)" 주석 한 줄(과거 서술은 고치지 않음).

## 2. 자산·기준선·골든(순서 엄수)
1. 수정 뒤 `geo.prep` 두 프로젝트(480p + `--res 1080p`) 재생성. `geo_report.json` 에 KZ 면적·land-miss 기록.
2. **hormuz 25컷 before/after**: §0 기준선(2233392, 결함 포함) 대비 컷별 diff 마스크 → 달라진 픽셀이 **카자흐스탄·바이코누르 영역 안에만** 있음을 증명(`reports/phaseG1/geo_fix_diff.json`: 컷별 변경 픽셀 bbox·비율, 시트 `geo_fix_before_after.jpg` 3컷). KZ 가 안 보이는 컷은 md5 동일이어야 한다.
3. **새 기준선** `hormuz_baseline.json` 갱신(기존은 `hormuz_baseline_prefix.json` 으로 남김) + 전편 video_noaudio md5 새 값 기록. 이후 G1 작업 6 합격 기준은 **새 기준선 25/25**.
4. `docs/handoff/golden/` 25장 재생성(README 절차, `expected_deltas.json` 갱신). 커밋 메시지에 "골든 교체 사유: KZ 키 충돌(D-0078)" 명시. 골든 교체는 이 사유 한 가지만.
5. 랫클리프 480p 20컷 auto 프리뷰 재생성(연출 무변경, 렌더만) → 사용자 확인용 컷 1장(모스크바 2026.08 컷) `reports/phaseG1/ratcliffe_kz_after.jpg`.

## 3. G1 과의 관계
- 이 수정은 무대 추상화 커밋과 **섞지 않는다**. 이미 로컬에 작업 1~3 변경이 있으면 stash/워크트리로 분리해 이 수정 커밋을 먼저 올린다.
- 작업 6 회귀 비교의 상대는 새 기준선. 1080p res_compare·camera_suggest diff 는 그대로(지오메트리는 카메라 제안 입력이 아님 — 만약 제안이 바뀌면 사유와 함께 보고).
- D-0076 §3 "골든 PNG 교체 금지" 는 이 사유에 한해 해제.

## 4. 보고
수정 커밋 + 산출물 2~5 를 progress R 로 즉시(다른 작업보다 먼저). 사용자에게 보여 줄 before/after 시트가 필요하다.

## DECISIONS 후보(Fable 기록)
D69: 같은 ISO 키 피처는 합집합, 커버리지는 면적 비율, 골든 교체(사유 KZ).
