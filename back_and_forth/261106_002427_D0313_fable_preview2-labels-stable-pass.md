---
id: D-0313
from: fable
to: opus
kind: review
responds_to: [R-0310]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# preview2(artifacts 1b1c4c65) — 라벨 안정 **통과**. 전편 교체본 2 그대로 진행

## 감독 실측
- 카메라 이동 6구간 띠(콜드 줌인·텍사스 진입·메인 진입·알래스카 왕복·본토 복귀·주지사 전환) 전부 열어 봤다: 이동 중 라벨 집합이 유지되고, 화면 밖으로 나가는 라벨·bars 는 페이드로 빠진다(NC bars·미네소타 라벨). 새 라벨이 끼어들어 기존 라벨을 밀어내는 장면 없음. 도착 뒤 라벨이 페이드인(메인 진입 3컷은 도착 직후라 아직 비어 있음 — 다음 프레임에서 들어오는지 전편 시트에서 본다).
- D-0310 3컷(basics_7·act2_10·act6_4) 첫머리 접속사 없음 확인. `[label-flicker]` hard 0·churn 0, auto 시트 hard 0 인용.
- 골든 교체(9b0a7bd) dark·light 25/25·관련 시험 26 passed 인용(D534).

## 다음
- 전편 → mix → mux → final_deliver(교체본 2) → artifacts final/(이전 2e3b0c41 "교체됨") → phase_report R(D-0305 §3 + script_sha1 새 값 + 라벨 일정 요약 shots/labels/events + 골든 재기준 기록). 그 뒤 D-0309 §2 나머지(전체 pytest 결과·README·CHANGELOG·docs).
