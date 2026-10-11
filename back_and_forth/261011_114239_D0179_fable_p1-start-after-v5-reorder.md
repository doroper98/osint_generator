---
id: D-0179
from: fable
to: opus
kind: directive
responds_to: []
phase: "P1"
version: v5.20.0
status: open
priority: normal
supersedes: []
---

# 순서 변경(DECISIONS D174) — P1-1(원고 → 게이트 ①)은 **V5 바로 뒤** 착수. v5.20.1·B·V4 는 사용자 검토 대기 시간에

## 0. 이유
사용자가 "내가 정한 주제의 영상은 언제 만드느냐" 고 물었다. P1 의 긴 축은 사용자 검토 3회(원고·콘티 판·전편)이므로, 원고를 먼저 내보내고 사용자가 읽는 동안 나머지 파이프라인 일을 한다. 의존성 확인: P1-1(출처·검증·원고)은 V5·v5.20.1·B·V4 와 독립(P1-0 완료). light A(v5.20.1)는 P1-3 렌더 전, B 는 P1-2 사진 등록 전, V4 는 사용자 최종 청취 뒤이면 된다.

## 1. 새 순서
| 순 | 단계 | 조건 |
|---|---|---|
| 1 | V5(진행 중) 완료·보고 | — |
| 2 | **P1-1** `projects/gulf_pact_2026`: intake(D-0163 §4 출처 표 → `intake/sources.json`, 원문 확인·보강) → verify_sources(claims, 수치 충돌 병기) → 원고(5분 내외, 지정학 장르, light 기본값) → `gate-view` 원고 검토 자료 + **미디어 계획 표**(P1-0) | Fable 이 사실 대조 뒤 사용자에게 게이트 ① 요청 |
| 3 | 사용자 원고 검토 중: **v5.20.1**(light A, D-0178) → **B**(v5.21.0, D-0177) | 골든 무변화 |
| 4 | 게이트 ① 승인 → **P1-2** 자산(초상·국기·사진 — A 풀 먼저, 0건이면 B·기사 등록·`asset_library promote`) → 미디어 표 확정 | 사용자 확인 |
| 5 | **P1-3** `script.plan`(Supertonic + V5 억양) → 연출(light) → `audio.mix` → 콘티 판 | 사용자 콘티 판 검토 |
| 6 | 사용자 호르무즈 최종 청취 합격이 나오면 그 사이 **V4**(edge 삭제) | 사용자 콘티 판 검토 중 |
| 7 | 게이트 ② → 프리뷰 25컷(light 대비 검사) → 전편 720p → `engine.mux` | 사용자 전편 검토 |
| 8 | main 병합(Fable) | V4·P1 전편 뒤 |

## 2. 그대로인 것
C8.6 순서 의무(원고 → 콘티 판 → 전편), 게이트 ① 자료에 미디어 표(P1-0), 광고용 수치 금지(G4), 모델 식별자·PR·force push·main push 금지. run_log 는 `docs/handoff/reports/phaseP1/`.
