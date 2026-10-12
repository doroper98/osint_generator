---
id: R-0227
from: opus
to: fable
kind: phase_report
responds_to: [D-0220]
phase: "P1-8"
version: v7.1.0
commit: (이 보고)
status: needs_review
---

# v7.1.0 UF-99 — 카메라 검사 = 화면 궤적, hard camera_bounds, 경계 안 키만 제안(영상 재렌더 없음)

## 1. 원인 확인(구현 세션 실측 — 감독 광류 결과와 일치)
- gulf 무대(티어 W) 허용 최대 w = 54.0. 연출 키 w 88(오프닝)·72(29.7초·288.6초)·84(132.5초) → View 가 잘랐다.
- 요청 궤적 기준: 화면 흐름 방향 급변 0프레임, continuity·speed 통과. 화면 궤적 기준: 방향 반전·줌 급정지/급출발(29.71·61.67·132.5·192.83·288.6·300.4초).
- **원인 제공 하나 더**: 연출 입력 `workers/direction_io.geo_text` 가 고정 문구 "카메라 w 는 2.5~96" 을 모든 프로젝트에 넣었다 — gulf 경계(54)보다 넓은 키를 허용. 이번에 무대 경계에서 계산하도록 교체.

## 2. 한 일(7907fcc·5c206f7·e230704)
1. **측정 교체**: `engine.camera.screen_track(stage, track, viewport)`(렌더와 같은 View), `bounds_excess`, `max_view_w`. `camera_continuity`·`camera_speed` 는 화면 궤적을 잰다. 다른 화면 배치 검사(offscreen·frame_missing 등)는 이미 View 를 쓰고 있었다(확인).
2. **hard `camera_bounds`**: 요청 − 화면 차이 ÷ w > `rules qa_checks.camera_bounds_rel_tol`(0.001) 구간마다 한 줄(시각·잘린 성분 x·y·w·요청 최대 w·허용 최대 w). 지도·시간축(y 는 무대가 정하는 값이라 제외)·**차트 아일랜드 카메라**도. 규칙 원칙 주석 1줄.
3. **예방**: `frame_points` 는 w ≤ 경계 폭 − `camera.framing.bound_pad`, 중심 ± w/2 경계 안(실패 틀도). `geo_text`·`stage_text` 에 경계 범위 값. `rules direction_grammar` 1줄([camera-bounds]).
4. **스케치(C12-3)**: SK-C1 이 `bounds_stage(project)`(geo.yaml 티어 W — 콘티 판 막지도와 같은 값)로 화면 궤적·경계를 잰다. campaign·missile·globe 2D 구간 모두. SKILL 2개·docs/handoff/22 D222.
5. **fed_timeline_demo**(연출만, 경계 안으로): 첫 키 2020-08-01 → 2021-06-10(화면에 보이던 자리), low 장면 이동 삭제(화면에서 0~5일 이동이었음), 끝 조망 w 2830 → 2653.4·중심 2023-04-14, stage end 2026-10-01 → 2026-12-01(경계 안 키가 되자 도착 뒤 3% 드리프트가 보여 2026년 8월 핀이 오른쪽 7px 밖 — 두 달 여유). 데모 프리뷰 hard 0.
6. **기록**: 원장 UF-99 guarded(장치 11), UF-02·UF-97 에 camera_bounds 보강. RENDER-AP-026(재는 것 ≠ 보이는 것, UF-02→D-0202→UF-97→D-0216 경과). 15 P12 보강, 12 §2.5a, 19 §3.37, DEVLOG.

## 3. 시험(`tests/test_camera_bounds.py` 7개)
- gulf v6.0.2 카메라 키 고정 자료(`tests/fixtures/camera/gulf_v602_keys.json`, 전달본과 P.cams 동일 확인) → camera_bounds 4구간, 시작 0.00·29.71·132.46·288.62초(±1프레임).
- 같은 궤적: 경계 없는 무대(= 옛 측정)로는 continuity·speed 통과, 화면 궤적으로는 continuity 실패(꺾임).
- 볼록성: 경계 안 무작위 키 4개 × 40회(creep 포함) → 클램프 0프레임.
- frame_points: 경계 가장자리 장소도 경계 안 제안(옛 코드에선 이 시험 실패 확인).
- geo_text: gulf "2.5~54.0", "~96" 없음. SK-C1: gulf 키 → 경계 실패.

## 4. 검증
- 빠른 묶음 **1568 passed · 0 failed**(2분 59초, -n 4). anti_inertia 포함(관성 시험이 내 리터럴 2곳을 잡아 규칙 키·짧은 문구로 고침).
- 골든 hormuz: camera_bounds·continuity·speed 0, 25/25 무변화(렌더 코드 무변경 — 검사·제안·입력만).
- 전체 pytest: 오늘 1회(v7.0.1, 1685 passed) 했으므로 C8.3 대로 생략. main 병합 전이면 다시 돌린다.

## 5. 다른 프로젝트(고치지 않음, 목록만)
| 프로젝트 | 결과 |
|---|---|
| gulf_pact_2026 | 4구간(위) — 전달본, 재렌더 없음(사용자 지시) |
| fed_policy_2026 | **차트 아일랜드** 카메라 3구간(x 잘림 — 0~0.25·21.6~53.8·80.6~293.8초) |
| hormuz_korea·ratcliffe2026·fed_timeline_demo(수정 뒤) | 0 |
| 키 값만 정적 점검(plan 없음): hormuz_ai·hormuz_ai_cam·hormuz_camauto·taiwan_ai·taiwan_f1_music·taiwan_f1_nomusic·taiwan_strait | 경계 밖 키 0 |
| dmz_mine_2026·kaliningrad-suwalki·valdai-2026·hormuz-talks-2026 | plan 없음 + 카메라가 장소 앵커라 정적 점검 불가 |

## 6. 렌더 단계에서 카메라를 바꾸는 곳 전수(grep)
- `engine/projection.py View` 클램프 — 이번 검사가 잡는다(안전망으로 남김).
- `engine/stage_timeline.frame_y1` — 시간축 세로 위치는 무대가 정한다(레인이 영역보다 크면 카메라 y 클램프). camera_bounds 에서는 y 제외, 화면 궤적 continuity 에는 포함.
- `engine/framing._clamp` — 제안 평가용, 이제 경계 안 후보만.
- `engine/camera_suggest._anchor` 4자리 반올림 — 허용 오차 안.
