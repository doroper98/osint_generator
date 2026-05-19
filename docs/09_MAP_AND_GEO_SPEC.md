<!--
tier: 2
last_synced_with: v0.1.1
ssot_for: [map-spec, geo-data-policy]
depends_on: [06_SOURCE_AND_RIGHTS_POLICY.md]
last_review: 2026-05-19
-->

# 09 — Map & Geo Spec

## 1. 지도 우선순위

1. Google Maps Tiles — 시각 품질 최상. **약관 검토 필수**.
2. Mapbox — 유료 한도 내, 상업 사용 가능.
3. OpenStreetMap (Carto / Stamen 스타일) — 무료, ODbL 라이선스, 저작자 표시 필요.

기본값: **OpenStreetMap**. Google Maps 사용은 [06_SOURCE_AND_RIGHTS_POLICY.md §8](06_SOURCE_AND_RIGHTS_POLICY.md#8-외부-지도-데이터)의 검토를 통과한 경우에만.

## 2. 스타일

| 카테고리 | 스타일 |
|---|---|
| 군사 / 전쟁 | 지형 + 위성 혼합 (terrain + satellite) |
| 지정학 | 다크맵 (정치 경계 강조) |
| 경제 / 산업 | 다크맵 (해운 항로·공급망 라인) |
| 지진 / 재난 | 지형 + 진앙·여진 마커 |

## 3. 도시명 표기

- 한국어 우선. 영어 병기는 작은 글씨.
- 작은 도시·진앙은 한국어 + 위경도 보조.

## 4. 국가 하이라이트

| 구도 | 색상 |
|---|---|
| 단일 주체 | 기본 붉은색 |
| 양자 대치 | 빨강 / 파랑 |
| 3자 이상 | 빨강 / 파랑 / 녹색 / 노랑 |

## 5. 폴리라인

- 항로·미사일·드론 궤적은 굵기 2–3px, 점선 또는 실선.
- 시작·끝점에 작은 아이콘.
- 애니메이션 그리기 1–2초.

## 6. 지진 전용 요소

- 진앙: 원형 마커, 규모에 비례한 반경.
- 여진: 옅은 원, 시간순 페이드 인.
- 쓰나미 경보: 해안 라인 강조.
- 판 경계: 굵은 점선.
- 해구: 음영선.

## 7. 출처 표기

지도 화면 우측 하단에 작게 데이터 출처 + 라이선스 표기 필수.

예: `© OpenStreetMap contributors / ODbL`

## 8. 좌표 / 시각 정규화

- 좌표: WGS84, 소수점 4자리.
- 시각: UTC + 현지시각 병기.
- 진원 깊이: km 단위, 정수 또는 1자리 소수.

상세 구현은 `workers/map_worker.py` (Phase 7).
