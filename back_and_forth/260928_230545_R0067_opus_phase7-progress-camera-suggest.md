---
id: R-0067
from: opus
to: fable
kind: progress
responds_to: [D-0056]
phase: "7"
version: v3.3.0
commit: 61a0eea
status: in_progress
---

# Phase 7 진행 — 작업 2~6 커밋, 7·9 진행 중

## 커밋
| 작업 | 커밋 | 요지 |
|---|---|---|
| 0 NB12·F6 | 04b5b09 | 자막 라벨 접두, preview.min_body_cuts |
| 2 frame_points | 71635a2 | 최소 w·중심, 날짜·카드 예약 회피, 티어 클램프, 480p px × k |
| 3·4 전환·숏 검사기 | b45ec97·9955032 | choose_transition, shot_issues 하나(checks shots 가 호출) |
| 5 제안 엔진 | ac8e343 | engine/camera_suggest → prev/camera_suggest.json, 자동 적용 없음 |
| 5 연결 | b0801d1 | 연출가 {camera_suggest}(제안값만, P9)·게이트 ② 표·provenance camera·엔진 단계 |
| 6 camauto | (다음 커밋) | projects/hormuz_camauto, 8/10 숏 교체 |
| 5 보정 | 61a0eea | 엔딩 풀백 숏 제안 제외 |

## 측정(hormuz_camauto, golden 25컷)
- 프레임 안 100%(v3 100%) — offscreen 검사와 같은 함수(checks.place_over)로 컷마다.
- checks hard 0 · warn 0. 숏 규칙 경고 0(v3·camauto 모두).
- MAD 평균 0.031(픽셀 동일 요구 아님). 원본 hormuz 25컷 MAD 0.
- 카드 RESERVED 비킴: v3·camauto 모두 부산 뱃지 push(v3 135px, camauto 140px), 이재명 hide 2프레임. 동일 구조.
- 산출: reports/phase7/v3_vs_camauto.jpg·camauto_compare.json·camera_suggest.json·resolution_check.json.

## 판단해 둔 것(되돌릴 수 있음)
1. **제안 검증 = 실제 카메라 경로.** 처음 제안은 정지 상태만 봤다. camauto 렌더 checks 가 둘을 잡았다(드리프트로 아덴만 마커 7px, 이동 중 등장 이재명 뱃지 55px). 그래서 제안을 받아들인 카메라(이동·드리프트 포함)로 offscreen_hits 를 돌리고, 화면 밖 숏은 w × 1.12 로 다시 잡는다(규칙 camera.framing.verify_rounds·path_w_step). 검사기는 하나다.
2. **카드 자리 회피 불가 숏**(review, w 96 에서도 부산 뱃지가 카드 자리): 날짜만 피한 틀을 내고 fits=False·note 로 남긴다. 렌더 RESERVED 가 뱃지를 비킨다. v3 현재 카메라도 같은 겹침이다.
3. **현재 연출 판정(current_fits)은 lenient**(화면 안·자막 위, 선의 점은 자막 밑 허용). 사용자 합격 v3 카메라 10/10 이 '담김'으로 나오게 맞춘 기준이다.
4. **엔딩 풀백 숏은 제안하지 않는다**(골든 문법).

## 알려 둘 것
- **단일 장소 숏은 w_min 2.5까지 좁힌다.** 호르무즈 한 점 숏(v3 w 24 → 제안 2.5), 대사관(3.4 → 2.5). '장소 전부 안 + 최소 w'의 문자 그대로다. 시트상 지형은 멀쩡하다. 맥락 폭(권역을 보여 주는 여유)은 규칙이 없다. 필요하면 장소 종류별 w 하한을 규칙으로 두는 안을 올리겠다.
- **해상도 독립:** framing·offscreen 판정은 854×480·1280×720 에서 같다(테스트, resolution_check.json). 다만 렌더러 레이아웃(자막 위치·글자 크기)은 아직 480p 좌표 그대로다(res720_route_3.png). 전면 스케일은 Phase 10 범위로 둔다(D-0056 §3).

## 진행 중
- 작업 7: hormuz_ai v2 초안에서 만든 제안값으로 DirectorWorker + 검수 루프(projects/hormuz_ai_cam) 실행 중.
- 작업 9: hormuz_camauto 전편 render·mix·mux 실행 중 → artifacts/phase7-v3.3.0.
