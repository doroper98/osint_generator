---
id: R-0053
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "6.9"
version: v3.1.0
commit: 2a973eb
status: in_progress
---

# checks.json(17 §3)가 v3 골든 연출에서 hard 2건을 잡는다 — 중국·인도 뱃지가 화면 아래로 잘림

## 쟁점
작업 6 `checks.json` 을 hormuz(v3 합격 연출, direction.yaml 변환본)에 돌리면 **offscreen hard 2건**이다.
- war 장면 `badge 중국`(59.4E 23.35N, R 17)·`badge 인도`(60.9E 23.35N): t≈64.2~ 장면 끝까지 **뱃지 원 아래쪽과 이름표가 화면 밖 54px**(상자 y 468~534, 화면 480).
- 25컷 08 war_3(t=65.13) 골든·Phase 6.8 프레임을 보면 실제로 원 윗부분만 보이고 이름표 "중국"·"인도"가 **보이지 않는다**(`reports/phase6_9/hormuz_v3/frames/08_war_3.png`). 자막이 "대부분 중국과 인도로 가는 유조선"이라 뱃지 의도는 분명하다. 검사 오탐이 아니다.
- 다른 뱃지 6개는 통과(가려진 구간 — 타이틀 카드·패널·암전 — 은 검사에서 뺐고, 그림자 여백 7px 은 허용).

17 §3 는 "hard 실패 → LLM 검수 없이 연출에 오류 반환"이다. 이대로 배선하면 v3 연출 자체가 preview 단계에서 실패한다(e2e·provenance 테스트 포함). 그래서 **hard → 단계 실패 배선만 보류**하고 지금은 StageResult warnings 로 보고한다(`2a973eb`). checks.json 에는 hard 2 로 적힌다.

## 선택지
**A. v3 연출을 고친다(권고)** — 두 뱃지 위도를 화면 안으로(예: 23.35N → 24.4N, 이름표까지 들어오는 값을 실측) 옮기고 08 war_3 를 `expected_deltas`(reason "v3 뱃지 잘림 수정, checks offscreen", decision 이 D)에 등재. 그 뒤 hard → 단계 실패 배선.
- 17 §3 "잘림 0" 과 골든 문법이 함께 산다. 결함을 고치는 방향. 되돌리기: direction.yaml 두 줄 + expected_deltas 한 항목.
- §7.2 v3 합격 수치 변경에 해당 → Fable 결정 필요(그래서 올린다).
**B. v3 는 그대로, 프로젝트별 예외 목록**(`checks_allow: [offscreen:badge:중국, …]` + 사유) — 골든 무변경. 그러나 AI 연출도 같은 구멍을 쓸 수 있고, 예외 장치가 늘면 hard 의 뜻이 약해진다.
**C. offscreen 을 warning 으로** — 17 §3 표(잘림 0 hard)와 어긋난다. 권고하지 않는다.

## Opus 권고
**A.** ① 되돌리기 쉬움 ② 17 §3 그대로 ③ 실측(골든 프레임에 이름표가 없음). 수정 좌표는 결정 뒤 실측해 경계 안(상자 전체 + 그림자 7px)으로 정한다.

## 막히는 범위
- 막힘: hard → preview 단계 실패 배선(작업 6 마무리), 작업 8 의 "checks hard 0 → 시각 검수" 분기 실측.
- 계속: 작업 7 프롬프트, 작업 8 워커 코드, 10b 준비.

## §7 해당 여부
아니다(§7.2 v3 합격 수치 — Fable 전결).
