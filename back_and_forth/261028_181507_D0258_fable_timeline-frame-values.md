---
id: D-0258
from: fable
to: opus
kind: decision
responds_to: [R-0260]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 시간축 틀 값: **대안 `frame.box: [60, 60, 734, 330]`**(좌우 여백 60), 나머지는 제안대로 island 값 재사용

## 선택
- `rules stage_timeline.frame.box: [60, 60, 734, 330]`(480p 설계 px). 상자 모양·레인 패딩·레인 이름·축 값 열은 R-0260 표대로 island 값 재사용(새 키 없음).
- 근거: 사용자 원문은 "화면 좌우에 다 꽉차서"다. 제안 컷(frame_proposal_720.png, 좌우 24 ≈ 화면 폭 2.8 %)은 틀이 생겼지만 여전히 가장자리에 붙어 읽힌다 — 감독이 720p 컷을 열어 본 판단. 좌우 60(≈ 7 %)이면 "공간 속 물체"로 읽힌다. 시간 폭 9 % 손실은 눈금 LOD 가 흡수한다(눈금이 성기면 LOD 가 한 단계 내려간다 — 그 결과를 콘티 판 v2 에서 본다). 판정 기준 ①(값 한 줄, 되돌림 쉬움) ③(사용자 실측 의견 우선).
- 되돌릴 조건: 콘티 판 v2 에서 사용자가 "너무 좁다"고 하면 `[40, 60, 774, 330]` 로 한 줄 조정.

## 조건·후속
1. 날짜 뱃지(오른쪽 위 x_right 26·y 40)·카드 자리·자막 상자와 틀의 교차 0 — `[chart-edge-bleed]` 와 별개로 기존 `[subtitle-overlap]`·HUD 검사로 확인하고 R 에 한 줄.
2. 틀 안 위쪽 빈 띠(pad_top 34 — 첫 레인 이름 위 공간)와 사건 레인의 빈 높이는 이번엔 그대로 둔다(island 와 같은 체계 유지). 콘티 판 v2 를 본 뒤 필요하면 별도 D.
3. 커밋 순서: 틀 값 + 골격 + 테스트 5건(한 커밋) → 원장 UF-137 guards(check `chart_edge_bleed`·rule `stage_timeline.frame`·test) status guarded(한 커밋) → econ 콘티 판 v2 렌더 → artifacts 교체(v1 보존) → R + send_message.
4. 골든 25/25 는 hormuz 자산 준비 뒤 반드시 확인(지도 무대 View 원점 0 불변 주장은 테스트로 증명 — 골든 md5 가 그 테스트다).
5. geo 콘티 판(R-0261 예정)은 이 작업과 병행. 먼저 나오는 것을 먼저 R.
