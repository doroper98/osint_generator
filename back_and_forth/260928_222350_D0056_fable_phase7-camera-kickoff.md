---
id: D-0056
from: fable
to: opus
kind: directive
responds_to: []
phase: "7"
version: v3.3.0
status: open
priority: urgent
---

# Phase 7 착수 — 카메라 자동화 보조 (v3.3.0)

정본: 13 §Phase 7, 19 §6 7 행("옵션이지 강제 아님", P8), **05 §7 개선 과제 4개**(자동 프레이밍 `frame_points(points, reserve)`, 전환 자동 선택 dip/move 기준, 숏 머무름 검사, 해상도 독립), 05 §2 숏 문법(`rules shot_grammar` 값 이미 있음), 17 §3 숏 규칙 검사(6.9에서 warning으로 들어감 — 그 위에 제안), 09 §2 스케일. 현재: `engine/camera.py`(`cam`·`build_camera`·`Director`), `engine/direction.py` shots cut/move/dip, `placement.slots`·RESERVED(6·6.9), checks.json 숏 규칙 warning.

## 0. 선행(6.95 비차단) — 첫 커밋
1. `VERSION` 3.3.0 + CHANGELOG. **NB12** 자막 검증 라벨 표기(`<미검증>`·`<논쟁>` 접두, 규칙 문구·스타일, hormuz 무변경, 테스트). **F6** `--preview auto` 샘플 규칙: 본편 컷 최소 N장(규칙 `preview.min_body_cuts`, 짧은 영상에서 엔딩 카드만 뽑히지 않게) — 25 앵커 `golden` 모드는 무변경.

## 1. 커밋 순서(한 커밋 한 의도, 전부 `v3.3.0:` prefix)
2. **`frame_points(points, reserve) -> (lon, lat, w)`**(05 §7-1): 장면의 장소 목록(엔티티·마커·뱃지 좌표 + 뱃지 반지름 px) + 예약 영역(카드·자막·날짜·패널 — RESERVED 재사용)을 받아 모두 보이는 최소 w와 중심. 여백·최소/최대 w는 `rules camera.framing`(코드 리터럴 금지). 해상도 독립: w는 지도 단위, 픽셀 여백은 09 §2 스케일.
3. **전환 자동 선택**(05 §7-2): 이전·다음 숏의 (중심 거리 / 평균 w) ≥ 2.5 또는 w 비 ≥ 6 → dip, 아니면 move. 임계는 `rules camera.transition`. `dip(t, lon, lat, w)` 인자형 정리(13).
4. **숏 머무름 린트**(05 §7-3): 6초 미만 숏 경고 — 6.9 checks의 숏 규칙 warning과 **하나로 합친다**(중복 구현 금지, D-0047 §0-4). 장면당 이동 ≤1, dip 90초당 1회도 같은 검사기.
5. **연출가 제안 경로(P8: 옵션, 강제 아님)**: `engine/camera_suggest.py`가 direction.yaml의 각 장면에 대해 `frame_points`·전환 제안을 `prev/camera_suggest.json`으로 낸다. **자동 적용은 하지 않는다.** DirectorWorker 입력에 "제안값"으로 전달(17 §5.3 프롬프트에 자리표시), 사람 연출은 무변경. 게이트 ② 뷰에 "제안 vs 현재" 표.
6. **v3 대조(합격 조건)**: hormuz v3 direction.yaml의 cam/dip 6+5개를 제안값으로 **바꾼 사본**(`projects/hormuz_camauto/`)을 만들어 25컷 시트 + 골든 나란히(`v3_vs_camauto.jpg`) + 컷별 MAD·"장소 전부 프레임 안" 검사 결과. 원본 hormuz는 무변경(25컷 MAD 0).
7. AI 연출 재실증: hormuz_ai(6.9 v2 초안)에 제안값을 입력으로 준 DirectorWorker 1회 → checks·시각 검수 결과를 6.9 결과와 비교(hard·soft 수, 카메라 관련 지적 수).
8. 테스트: frame_points(장소 전부 안·예약 영역 회피·최소 w·스케일 독립), 전환 선택 임계, 숏 린트 3종(하나의 검사기), 제안 JSON 스키마·파리티, 사람 연출 무변경(회귀), 규칙 리터럴 0(test_no_magic_numbers 대상 추가).
9. 산출물 `docs/handoff/reports/phase7/`: `v3_vs_camauto.jpg`, `camauto_compare.json`(컷별 MAD·프레임 안 검사), `camera_suggest.json`(hormuz), hormuz_ai 재실증 `qa_compare.md`, hormuz 25컷 회귀(MAD 0), provenance(`camera.suggested/used`), run_log, asset_md5. 영상 본체 `artifacts/phase7-v3.3.0`(hormuz_camauto 전편, tts·media_src 동봉).

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 동등 이상(13 합격 기준, 사용자 검수 → Fable review M2) | v3 vs camauto 25컷 나란히 시트를 내가 본다. 기준: 장면의 장소가 전부 프레임 안(검사 100%), 예약 영역과 겹침 0, 골든 문법 유지, 숏 린트 경고 0. 픽셀 동일은 요구하지 않는다 |
| 원본 무변경 | hormuz 25컷 Phase 6.95 대비 MAD 0(NB12 라벨은 hormuz에 없음) |
| 제안은 옵션 | 사람 연출 direction.yaml에 자동 적용 0(테스트), provenance에 suggested/used 구분 |
| 하나의 검사기 | 숏 규칙 검사 코드 경로 1개(6.9 checks·7 린트 동일 함수) |
| 해상도 독립 | 같은 direction을 854×480·1280×720로 preview → 프레임 안 검사 결과 동일(픽셀 여백만 스케일) |
| pytest | 삭제 조정 기준(D-0053), xfail 0, 새 테스트 ≥ 15 |

## 3. 하지 않는 것
- 오디오(8, F1 포함), 번들(9), 성능·해상도 전면(10 — 해상도 독립 검사는 preview 2종만). 골든 PNG 교체. v3 direction 원본 수정.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report. 결정 필요 시 decision_request. 턴 종료 금지(21 §6).
