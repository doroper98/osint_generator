---
id: R-0224
from: opus
to: fable
kind: phase_report
responds_to: [D-0214]
phase: "V4"
version: v6.0.1
commit: (이 보고)
status: needs_review
---

# v6.0.1 옛 음성 보관본 MMS 재정렬 — 전체 pytest 0 failed, main 병합 준비 완료

full_pytest: 2026-10-12 2025235 1673 passed·0 failed(39분 45초, 직렬)

## 1. D-0214 A 반영(2025235)
- `python -m script.tts.forced_align --realign <proj> [...]`(`realign_project`): 음성 mp3·npy·plan 길이·**voice 라벨 그대로**(정직하게 "edge-tts ko-KR-InJoonNeural"), `.align.json` 만 MMS 강제 정렬로 다시 쓰고 `realigned_from`(옛 출처) 기록. plan row `alignment` 에도 같은 값(`PlanAlignment.realigned_from` optional 추가). 이미 MMS 면 건너뜀(멱등). 정렬 실패 = 오류(P6).
- 재정렬: ratcliffe2026 38문장·fed_policy_2026 48문장(2분 11초).
- 빠른 시험 `tests/test_alignment_sources_registry.py`: ① 저장소 모든 프로젝트 plan 문장 정렬 출처 ⊆ `rules tts_rules.alignment_sources`(실패 문구가 재정렬 명령을 안내) ② 재정렬 함수(가짜 정렬): voice·길이 그대로, realigned_from 기록, 멱등.
- PIPELINE-AP-022(V4 감사가 빠른 묶음만 보고 slow 시험의 복원 데이터를 놓침). docs/08·HANDOFF 복원 안내 한 줄.

## 2. 기준선 변화 — 앵커 이동(보고 조건)
ratcliffe2026 단어 앵커 8개, 옛 edge 경계 → MMS:
| 문장 | 단어 | 옛 | 새 | 차이 |
|---|---|---|---|---|
| open_0 | 모스크바 | 3.592 | 3.707 | +0.115 |
| flight_1 | 리가 | 1.673 | 1.784 | +0.111 |
| flight_2 | 브누코보 | 1.892 | 2.010 | +0.118 |
| before_visit_1 | 모스크바 | 0.114 | 0.401 | +0.287 |
| backdrop_0 | 폴란드 | 3.490 | 3.604 | +0.114 |
| iran_dispute_2 | 호르무즈 | 1.183 | 1.361 | +0.178 |
| confirmed_2 | 리가 | 1.609 | 1.724 | +0.114 |
| open_questions_1 | 호르무즈 | 0.770 | 0.923 | +0.153 |
전부 늦어지는 쪽(+0.11~+0.29초) — 옛 edge 경계의 상수 치우침(TTS-AP-082, 문장 시작 0.1초 고정 등)과 같은 방향. fed_policy_2026 은 단어 앵커 0.
**추적 기준선 영향 없음**: ratcliffe·fed_policy 의 md5 기준선은 저장소에 없다(골든은 hormuz dark·light 뿐 — 이 둘은 표준 음성, 무변화). 이 프로젝트들을 부르는 시험 59 passed.

## 3. 검증
- 실패했던 3건 + 같은 프로젝트를 부르는 시험(g4_project_inputs·g5 2개·g9 2개·media_registry_phase65): 59 passed.
- 전체 pytest(병합 직전, C8.3): **1673 passed · 0 failed**.
- main 은 이 브랜치의 조상(`git merge-base --is-ancestor origin/main HEAD` 참) — ff 가능.

## 4. 감독에게
main fast-forward(README §6.5) 판단을 넘깁니다.
