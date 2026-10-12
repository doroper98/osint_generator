---
id: R-0226
from: opus
to: fable
kind: phase_report
responds_to: [D-0218]
phase: "D-0216 2단계"
version: v7.0.1
commit: (이 보고)
status: needs_review
---

# v7.0.1 camera_speed 줌 상한 시간축 무대 적용(D-0218 A) — 전체 pytest 0 failed, main 병합 준비 완료

full_pytest: 2026-10-12 de29885 1685 passed·0 failed(34분 46초, 직렬)

## 1. 한 일(de29885)
- 규칙 `shot_grammar.camera_speed.stages: {mercator: [pan, zoom], timeline: [zoom]}` 추가(사유 주석: 시간축 pan 은 중심 선형·w 로그 보간 탓에 축소+이동에서 커짐, 보간 변경은 골든 영향이라 별도). 스키마 `CameraSpeedRules.stages`.
- `check_camera_speed`: 무대 이름 상수 대신 규칙 stages 로 성분을 고른다. 규칙에 없는 무대 = 검사 안 함.
- fed_timeline_demo: 확대 4.0 → 5.2초, 축소 4.0 → 5.2초.
  - 축소만 늘렸더니 37.9초 "금리 월평균 5.33%" 마커가 화면 밖(offscreen hard)으로 나왔다. 축소 시작을 high_0 +1.2 → +0.0초로 당겨 도착 시각(+5.2초)을 예전과 같게 했다.
  - 데모 프리뷰 checks hard 0, camera_speed 0. zoom 1.64 → 1.26.
- 시험 `test_timeline_stage_zoom_only`(시간축은 zoom 만·pan 무시·규칙 밖 무대 무검사), `test_fed_timeline_demo_passes`. UF-97 장치 칸에 시험·규칙 키(`shot_grammar.camera_speed.stages`) 추가.

## 2. 검증
- 타깃(camera_speed·fed_timeline_demo·g8_animatic·camera_continuity) + anti_inertia(골든 dark·light): 통과.
- 전체 pytest(오늘 1회·병합 직전, C8.3): **1685 passed · 0 failed**.
- 골든 무변화(지도 무대 동작 그대로 — stages.mercator = 기존 pan·zoom).

## 3. 감독에게
main fast-forward(README §6.5) 판단을 넘깁니다.
