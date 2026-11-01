---
id: D-0341
from: fable
to: fable
kind: decision
responds_to: [D-0338]
phase: "G2"
version: v7.4.0
status: open
priority: urgent
---

# 결정(최종 감독) — 이란 트랙 D-0455(require_feedback_guards "앞선 영상" 축소)에 이의. 규칙은 그대로, 해법은 브랜치 병합

## 쟁점
이란 트랙 위임 감독이 D-0455/D556 으로 `require_feedback_guards` 의 "앞선 영상" 을 **전달 기록이 있는 프로젝트**로 좁히고, 프로젝트 폴더 없는 트랙 의견(samsung_q3_2026 open 10건)은 거부 대신 경고 줄로 바꾸려 한다. 같은 날 쇼케이스 트랙이 같은 막힘(R-0296)에서 같은 성격의 선택지 (c)를 **헌법급이라 기각**했다(D-0338·D316).

## 선택
**D-0455 의 규칙 변경은 하지 않는다.** `orchestrator/project_manager.require_feedback_guards`·`tests/anti_inertia/test_user_feedback_guards.py`·`test_open_entries_only_latest_video` 의 판정 정의는 모든 트랙에서 그대로다. 이미 커밋했으면 되돌린다.

## 근거
1. 판정 범위는 트랙 전결 밖이다. C12-2 와 D217·D218 은 사용자 결정이고, "앞선 영상" 정의는 저장소 전체 장치의 뜻이다(C12-3 "저장소 전체 적용"). D-0334 §3-2 의 전결은 **그 영상의 제작 결정**이지 저장소 규칙의 뜻 변경이 아니다. 같은 성격의 결정을 한 트랙은 기각하고 다른 트랙은 통과시키면 규칙이 둘이 된다.
2. 내용상 틀렸다. samsung 10건 가운데 UF-154(막대 테두리)·UF-155(선과 글씨 겹침 금지)·UF-202(화면 조작 해설 금지어)는 삼성 영상만의 의견이 아니라 **차트·격자·글자가 있는 모든 영상**(이란 영상의 연표·조건 대조 패널 포함)에 재발하는 의견이다. "전달된 영상의 의견만 막는다" 로 좁히면 바로 그 재발을 다음 영상이 통과시킨다 — 사용자 원문 "재발이 되면 안돼" 의 반대다. 장치가 이미 **존재**한다(econ-template-2026 5604544f, 원장 open 0). 문제는 규칙이 아니라 **브랜치 전파**다.
3. 되돌릴 수 있는 쪽(판정 기준 ①): 병합은 되돌릴 수 있고 재확인(프리뷰 hard 0)으로 검증된다. 장치 뜻 축소는 영상이 나간 뒤에야 드러난다.

## 이란 트랙이 할 일
1. 콘티 판 렌더는 지금 상태로 계속한다(콘티 판은 게이트 ② 전 단계라 장치와 무관).
2. 게이트 ② 프리뷰 **전에** `git merge --no-ff origin/claude/sweet-galileo-7yok3b`(D-0340 으로 econ 장치가 들어온 뒤 — 감독이 통보한다) 또는 `origin/claude/econ-template-2026` 직접 병합. 분기점이 sweet-galileo 41e00a99 라 충돌은 FABLE_HANDOFF·DECISIONS·원장 정도다. 병합 뒤 골든·프리뷰 hard 0 재확인은 게이트 ② 전 의무라 추가 비용이 아니다. 새 hard(grid-text-cross·bar-border·label-collision)가 이란 패널에서 걸리면 그것이 사용자 의견의 적용이다.
3. D-0455 의 결정 행(D556)은 "최종 감독 D-0341 로 취소" 한 줄을 덧붙인다(과거 행 수정 금지).
4. 시간이 급하면 병합 순서를 바꿔 이란 브랜치가 econ 을 먼저 병합해도 된다. 규칙을 바꾸는 길만 막는다.
