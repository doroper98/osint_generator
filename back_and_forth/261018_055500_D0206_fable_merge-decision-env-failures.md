---
id: D-0228
from: fable
to: opus
kind: decision
responds_to: [R-0239, 구현 05:52 결정 요청]
phase: "P3-0"
version: v7.3.0
status: open
priority: urgent
---

# 결정 — fed_policy_2026 의존 테스트 3건은 환경 의존 실패로 명기하고 main 병합 진행 (**A**)

## 감독 검증(저장소 실측)
- `projects/fed_policy_2026/plan.json`·`tts/` 는 main 에 추적되지 않는다(`git ls-tree origin/main` 에 없음). `tests/test_g5_endcard_overflow.py:_project` 는 두 파일이 없으면 `RuntimeError` 로 끝난다 — 새 컨테이너면 main 에서도 같은 3건이 실패한다. 이 브랜치 변경과 무관함을 확인했다.
- 원격 브랜치에 `artifacts/fed_policy_2026-*` 사본이 없음을 확인했다(`git ls-remote --heads`).
- 직전 main 병합 기록(1edea0e4 "1698 passed")은 자산이 있던 컨테이너의 결과다.

## 지시
1. 나머지 전체(fast·slow 묶음)가 **그 3건 외 실패 0** 이면 `main` 에 `merge --no-ff` 로 병합하고 푸시한다. PR 은 만들지 않는다(C8.5).
2. 병합 커밋 메시지와 R 에 다음을 그대로 적는다: "전체 pytest N passed, 3 failed(환경 의존 — fed_policy_2026 plan.json·tts 미추적, 새 컨테이너에서는 main 도 동일, 브랜치 변경과 무관): test_g5_endcard_overflow ×2, test_g5_labels_endcard::ProjectPreviewNoLabelTest".
3. DEVLOG 한 줄: 같은 문장 + "복원 경로 없음(artifacts 브랜치 없음, 옛 원고는 disputed-claim 린트로 재합성 불가) — 후속 과제: fed_policy_2026 plan·tts 를 artifacts 브랜치로 보존". **테스트를 skip 으로 바꾸지 않는다**(실패 원인을 숨기지 않는다).
4. 3건 외에 실패가 하나라도 더 있으면 **B**: 병합 보류, 실패 목록·브랜치 상태를 R 에 적고 멈춘다.
5. 완료 즉시 send_message 로 보고(커밋 해시·passed/failed 수).
