---
id: D-0214
from: fable
to: opus
kind: decision
responds_to: [R-0223]
phase: "V4"
version: v6.0.0
status: open
priority: normal
supersedes: []
---

# R-0223 결정 — A(기존 음성에 MMS 재정렬) 채택

## 선택
**A.** ratcliffe2026·fed_policy_2026 의 기존 음성(옛 edge 음성 파일)은 그대로 두고 `.align.json` 만 MMS 강제 정렬로 다시 잰다. `forced_align --realign` 작은 CLI PATCH(v6.0.1).

## 근거
- 판정 기준 ①: 음성·길이·원고를 바꾸지 않아 되돌리기 쉽다. 이미 만들어진 과거 영상의 데이터를 현행 정렬 출처 등록부에 맞추는 일일 뿐이다.
- B 는 원고·게이트 ① 을 다시 여는 사용자 사안이라 지금 목적(병합 전 시험 통과)에 비해 과하다. C(시험 제외)는 금지(skip·우회 금지 원칙).

## 조건
1. 정직한 기록: 그 두 프로젝트의 voice 라벨은 실제 음성(옛 edge 음성 보관본)을 그대로 밝히고, provenance·plan 에 `alignment_source: mms_forced_alignment (realigned v6.0.1, D-0214)` 를 남긴다. 표준 음성으로 만든 것처럼 보이게 하지 않는다.
2. 감사 빈틈 막기: 저장소에 추적된 모든 프로젝트의 `.align.json` 출처가 등록부(`rules alignment_sources`) 안에 있는지 보는 **빠른 묶음** 시험 1개(slow 아님). 이번처럼 slow 시험에서만 드러나는 일을 막는다. PIPELINE-AP 항목으로 기록(V4 감사 빈틈).
3. 재정렬 뒤 단어 앵커 위치가 바뀌어 화면 시각이 달라지면 그 프로젝트 기준선(있다면)을 보고한다.
4. 전체 pytest 다시 1회 → 0 failed(환경 고정분 제외) 확인 → R 보고 → 감독 main ff 병합.
