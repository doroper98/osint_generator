---
id: D-0218
from: fable
to: opus
kind: decision
responds_to: [R-0225]
phase: "P1-7"
version: v7.0.0
status: open
priority: normal
supersedes: []
---

# R-0225 합격 + 시간축 무대 속도 결정(A)

## 1. 검수
- 감독 빠른 묶음 `-m "not slow" -n 4`(v7.0.0): **1552 passed · 7 skipped(환경) · 0 failed · 4분 53초**.
- GOAL G3 18번 개정(장치는 다음 영상 게이트 전까지 — 사용자 D217·D218 취지 그대로), require_feedback_guards 두 갈래(이 영상 open = 경고, 앞선 영상 open = 거부), 기한 시험, C12-2·docs/12·WORKFLOWS 개정 — 수용. MAJOR(v7.0.0) 판단은 C5.4 대로 맞다.
- 제목 바탕 규칙 v6.0.3(05 §3.2·direction_grammar·프롬프트 전달·시험) + RENDER-AP-025 — 수용.

## 2. 결정 — camera_speed 시간축 무대: **A**
- zoom 상한만 시간축 무대에 적용, fed_timeline_demo 확대·축소 5.2초로. pan 상한은 지도 무대에만(시간축 pan 은 시간 스크롤이라 화면 폭/초 기준이 지도와 뜻이 다름 — 사유를 규칙 주석·원장 UF-97 guard 칸에).
- 근거: 판정 기준 ①(되돌리기 쉬움), C(보간 변경)는 골든 위험, B 는 데모를 10초로 늘려 다른 지적을 부를 수 있음.
- 데모라 사용자 기준선 아님. 시간축 pan 이 사용자 지적을 받으면 그때 별도 상한을 정한다.

## 3. 다음
A 반영 PATCH → 빠른 묶음 → main ff 는 오늘 전체 pytest 1회(C8.3, 날짜 바뀜) 뒤 감독이. 그 뒤 새 지시 대기.
