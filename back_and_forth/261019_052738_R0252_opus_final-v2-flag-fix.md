---
id: R-0252
from: opus
to: fable
kind: phase_report
responds_to: [D-0244]
phase: "P3-1"
version: v7.4.0
commit: HEAD
status: info
---

# 전편 v2 교체 완료 — 국기 잘림(D-0244)

artifacts/diesel_road_2026-v7.4.0 3e3d4f9b 덮어씀: final.mp4 md5 36289c32fba455693af92a1f20c7c3ca · 976.939초 · 720p · −14.09 LUFS · TP −1.52 dBTP · checks hard 0 · warning 75. README 첫 줄 "v2 교체: 국기 잘림", MD5SUMS 갱신, 증거 컷 33(기존 31 재추출 + 뱃지 2).

## 1. 수정
- 검사 `badge_clipped` hard(engine/checks.py): 뱃지 원이 안전 영역(인셋 여백 6px·자막 띠 위·날짜 배지 상자 밖) 밖이거나, 위 가장자리 보정(edge_nudge 아래로)에 기대 붙으면 실패. place_badge 와 같은 위치, 0.25초+끝 프레임, 알파 > 0.5.
- 윗줄 띠 전체가 아니라 날짜 배지 상자만 막는다. 좌우 보정은 허용. 골든 v3 인물 뱃지(이재명 좌측 가장자리, 하메네이 상단)가 그 자리에 있어 엄격 판으로는 골든 2건 실패 — 골든 0 유지 판으로 정함.
- 시험 tests/test_v740_static_camera.py::BadgeClippedTest 3건(안쪽 통과·앵커 y≈3 재현 실패·날짜 배지 위 실패). provenance e2e 항목 수 80. RENDER-AP-029. 골든 hormuz 프리뷰 badge_clipped 0.

## 2. D-0244 보충(감독 승인, 메시지) — DECISIONS D252
- 국기 앵커: 위도 43.4 는 여전히 화면 위끝(y 19)이라 연해주 해안 (133.6, 42.9) 육지(y 41, 보정 없음) — 승인.
- 트럼프 뱃지(act4_4): 같은 부류로 검사에 걸려 (48.2, 30.3) 육지로 — 승인.
- 진단 정정: 전달본 프레임 단위 확인 결과 실제 잘림은 없었고 위 가장자리 보정으로 상단 7px 에 붙은 상태 — 접수. 검사 정의 "보정 의존 = 실패" 유지.

## 3. 비차단 관찰
- 트럼프 뱃지가 내려오면서 바탕 지도 글자 "쿠웨이트·쿠웨이트 시"가 그 순간 가려짐(배치 회피). 연출 마커는 아님 — 유지.

## 4. 다음
E 단계: UF-116·119 장치 guarded, 전체 pytest 1회, 골든 화소 비교, main merge --no-ff, DEVLOG·CHANGELOG, 최종 R.
