---
id: D-0015
from: fable
to: opus
kind: directive
responds_to: [R-0013]
phase: "3"
version: v2.1.0
status: open
priority: normal
supersedes: []
---

# Phase 3 착수 — 지오 일반화 (v2.2.0)

## 0. 목표 하나
prep3의 지오·티어 생성을 **권역을 인자로 받는 `geo/` 패키지**로 옮기고, hormuz_korea 자산을 같은 결과로 재생성한 뒤, 새 권역(대만해협)을 명령 한 줄로 준비한다. 렌더 코드·수치는 건드리지 않는다.

## 1. 작업 (한 커밋 한 의도)
1. `VERSION` 2.2.0.
2. `geo/prep_geometry.py`: prep3 `polys`(재귀 평탄화)·`rings`·`geo()`. 인자 `--bbox lon0,lat0,lon1,lat1`, `--admin1 KR,IR,…`, `--crimea-to-ua`(옵션, 기본 off — 우크라이나 영상에서만 on, 04 §3.2). 출력 `geo.pkl`(coarse/fine/meta/admin1/places).
3. `geo/prep_tiers.py`: prep3 `build_tier`. 인자 `--tier NAME:ppd:z:lon0,lat0,lon1,lat1` 반복. 타일 범위 자동 계산(19a §H 값과 테스트 일치), 병렬 다운로드·캐시(`fetch_data tiles` 재사용), v3 팔레트·힐셰이드·3단 피라미드, **박스 클램프**, **커버리지 검사**(`land-miss` 목록 반환).
4. `python -m geo.prep <proj>`: 프로젝트 `geo.yaml`(bbox·tiers·admin1·labels 참조)에서 2·3을 실행, StageResult JSON. `projects/hormuz_korea/geo.yaml`은 v3 값(W 24ppd z5 28~140/−12~48, G 96 z7 46~62/20.5~32.5, K 96 z7 122.5~131.8/32.3~39.8).
5. 라벨 설정: `labels.yaml`에 해역 목록·KO 관용명·admin1 대상국이 이미 있으면 유지, 없으면 옮긴다. 렌더러는 이 파일만 읽는다(코드 상수 KO/SEAS 제거).
6. `projects/taiwan_strait/geo.yaml`(예시 권역: lon 115~125, lat 20~28, 티어 1~2개) + 최소 `script.yaml`(문장 2개, 발음 텍스트 규칙 준수) + `direction.py`(카메라 1개, 마커 1개). 프리뷰 3컷.
7. 테스트: 재귀 평탄화(GeometryCollection 안 MultiPolygon 픽스처 → 프랑스 회귀), 타일 범위 계산, 커버리지(작은 섬 국가 면적 임계 이하만 허용), 박스 클램프(부동소수 초과 케이스), `crimea` 옵션 on/off.
8. `legacy_v3/` 처리: Phase 3 합격 후 **삭제 여부는 내가 결정**한다. 이번 Phase에서는 삭제하지 않는다. 삭제 근거 자료로 "legacy_v3 없이 `tools/golden_compare.py`가 골든 PNG(H.264 추출본)와 새 엔진을 비교할 수 있는가"를 `--reference golden` 옵션으로 만들어 둔다.

## 2. 합격 조건
| 조건 | 명령·수치 |
|---|---|
| hormuz_korea 재생성 | `python -m geo.prep projects/hormuz_korea` → `land-miss` W=['MV'], G·K=[]. 생성된 `base_*.png` 3티어×3레벨이 Phase 1 자산과 **md5 동일**(같은 타일·같은 코드면 동일해야 한다). 다르면 MAD와 원인을 보고 |
| 전편 회귀 | 재생성 자산으로 `engine.render --preview` 25컷 MAD = 0(Phase 2 frames 대비) |
| 새 권역 | `python -m geo.prep projects/taiwan_strait` 한 줄로 티어 생성, 프리뷰 3컷에서 육지/바다·라벨(대만·중국 도시) 정상, land-miss 소도서 외 없음 |
| 프랑스 회귀 | 유럽 bbox 픽스처에서 FR 대표점이 육지 |
| pytest | 420 이상, 실패 0, xfail 6 유지 |
| 관성 | `test_single_config`·`test_no_legacy_imports` 통과. `geo/`가 `legacy_v3`를 import하지 않음 |

## 3. 하지 않는 것
렌더 수치 변경, 라벨 LOD 임계 변경(04 §7 값 유지), 티어 블렌딩 규칙 변경, Stage 추상화(G1), legacy_v3 삭제.

## 4. 보고
`phase_report` + `docs/handoff/reports/phase3/`(hormuz 25컷 시트·MAD, taiwan 3컷 시트, land-miss 로그, 자산 md5 표). 영상 본체는 Phase 2와 바이트 동일이면 `artifacts/phase3-v2.2.0`을 만들지 않고 그 사실만 적는다(D-0006 §2 예외, 결정 D28).
