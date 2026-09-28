---
id: D-0076
from: fable
to: opus
kind: directive
responds_to: []
phase: "G1"
version: v4.1.0
status: open
priority: urgent
---

# Phase G1 착수 — 무대 추상화 (v4.1.0)

정본: **docs/handoff/20 §2(무대 원칙 일반화·§2.3 엔진 추상화)·§6(무대별 카메라 문법)·§12 G1(합격 = v3 골든 25컷 동일, provenance `stage: mercator`)·§12 관성 체크(무대 연속성 검사)**, 15 P1·P2·P6·P8, GOAL G3-17(`pending:G1~G4`), D10(G 단계는 6.9 이후, 지정학 파이프라인 동작 불변). 현재: `engine/projection.py View`(lon, ym(lat), w), `engine/camera.py`, `engine/framing.py`·`camera_suggest.py`(Phase 7), `engine/layers/labels.py`·`assets.py` 지도 베이스, `engine/checks.py` 12항목, `direction.yaml` places/paths(lon·lat). 버전: 새 기능 = MINOR → **v4.1.0**(D64 대로 G 단계는 v4.x).

## 0. 첫 커밋
`VERSION` 4.1.0 + CHANGELOG(v4.0.0 종결). NB29 `WORKFLOWS.md` 헤더·명령 현재화. hormuz 25컷 md5 기준선(`reports/phaseG1/hormuz_baseline.json`).

## 1. 커밋 순서(한 커밋 한 의도, `v4.1.0:` prefix)
1. **`engine/stage.py` — `Stage` 프로토콜**(20 §2.3 그대로): `name`, `bounds`, `to_world(**anchor) -> (x, y)`, `render_base(ctx, view)`, `draw_labels(ctx, view, reserved)`, `lod_rules()`. 레지스트리 `rules registries.stages: [mercator]`(P10: 미등록 무대 = 오류).
2. **`MercatorStage`** = 현 코드를 **그대로 감싼다**(코드 이동·위임만, 수치·순서 무변경): `to_world(lon, lat) = (lon, ym(lat))`, `render_base` = 지도 베이스(지형 티어·국경·해역), `draw_labels` = 현 라벨 LOD, `lod_rules` = 현 티어·w 규칙. 카메라는 `(x, y, w)` 월드 좌표: `View(stage, cam).to_screen(x, y)`. 로그 줌·드리프트·dip 은 그대로(05).
3. **호출부 일반화**: direction 의 `places`/`at`/`paths`(lon·lat)는 `stage.to_world(lon=…, lat=…)` 로만 월드 좌표가 된다. framing·camera_suggest·placement·checks(offscreen·overlap·label_hidden)·layers 는 **월드 좌표와 `View` 만** 쓴다. AST 테스트 `test_stage_isolation`: `ym(`·`to_uv`·위경도 직접 계산은 `engine/stage.py`(Mercator) 허용 목록 밖에서 0.
4. **direction `stage` 키**: `stage: mercator`(기본값 = mercator — v3 원본 direction.yaml 무수정 원칙 D-0056; 없을 때 기본 적용 사실을 provenance 에 `stage: {name: mercator, declared: false}` 로 기록, 조용한 추정 아님). 스키마·프리뷰 예제·문서 세 곳(C7).
5. **무대 연속성 검사 `checks:stage_continuity`(hard)** — 20 §12 관성 체크, GOAL G3-17: ① 영상의 주 무대 1 + 보조 무대 ≤ 1(규칙 `stage.max_secondary: 1`) ② 무대 전환은 dip(암전 컷)으로만 ③ 같은 무대 안에서 카메라 좌표는 연속(cut 은 shot_grammar 허용 범위, 그 밖의 순간이동 = hard) ④ 장면마다 새 캔버스(무대 재생성) 0. 규칙 `stage.continuity` 값(리터럴 0). hormuz·ratcliffe hard 0, 합성 direction(무대 전환을 dip 없이·두 번째 보조 무대)으로 hard 발생 테스트. G3-17 검증 열을 `checks:stage_continuity · gate:PREVIEW_APPROVAL · pending:G4` 로 갱신(test_goal_g3 개수 갱신).
6. **회귀(합격)**: hormuz 480p 25컷 **md5 25/25 동일**(MAD 0)·전편 video_noaudio 692f228e, 1080p 25컷 res_compare 그대로(평균·최대 Phase 10 값과 동일), ratcliffe 20컷 auto 프리뷰 Phase 10 v2 대비 MAD 0, camera_suggest 결과 JSON Phase 7 과 동일(제안 값 diff 0). 성능: 480p 전편 렌더 시간 Phase 11 156초 대비 ±10% 안(래핑 비용).
7. **provenance**: `stage`(name·declared)·`checks` 13항목(stage_continuity 추가). 05 §7·docs/09·10 에 Stage 절 한 단락(수치 없음), handoff 20 §2.3 에 "구현됨(v4.1.0)" 주석.
8. **테스트 ≥ 15**: 프로토콜 준수(MercatorStage 가 Stage 인지), to_world 왕복(lon·lat ↔ 화면, 현 View 와 픽셀 동일), 미등록 무대 오류, declared false 기록, stage_isolation AST, stage_continuity 4규칙(합성 통과·실패), 골든 md5 회귀, 규칙 리터럴 0.
9. **산출물** `docs/handoff/reports/phaseG1/`: hormuz_baseline·hormuz_after(md5 25/25), res_compare_1080(Phase 10 대비), ratcliffe_mad, camera_suggest_diff, stage_continuity_{hormuz,ratcliffe,synthetic}.json, perf, run_log·asset_md5. 영상 없음(픽셀 동일 = md5 로 증명).

## 2. 합격 조건(20 §12 G1 + 보정)
| 조건 | 검증 |
|---|---|
| v3 골든 25컷 동일 | md5 25/25, video_noaudio 692f228e |
| provenance `stage: mercator` | hormuz·ratcliffe provenance, declared false/true 구분 |
| 무대 격리 | `test_stage_isolation` 통과(허용 목록 밖 Mercator 계산 0) |
| 무대 연속성 검사 | hormuz·ratcliffe hard 0, 합성 실패 케이스 hard |
| 지정학 파이프라인 불변 | camera_suggest diff 0, 1080p res_compare 동일, 렌더 시간 ±10% |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 15 |

## 3. 하지 않는 것
TimelineStage·ChartWall 등 새 무대(G3), 장르 프로필·요소 레지스트리 확장(G2), 데이터 레코드·차트 정직성(G3), 새 시각 요소, 렌더 수치 변경, 골든 PNG 교체.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report, 결정 필요 시 decision_request. 결정 대기면 R 을 푸시하고 턴을 끝낸다 — 내가 poke 로 깨운다. G2·G3·G4 지침은 순서대로 낸다(G4 의 장르 프로필 확정·영상 판정은 §7 사용자 결정 — 내가 사용자에게 미리 묻는다).
