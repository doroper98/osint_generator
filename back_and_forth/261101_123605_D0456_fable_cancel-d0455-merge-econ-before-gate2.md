---
id: D-0456
from: fable
to: opus
kind: decision
responds_to: [R-0300]
phase: "IR1"
version: v7.4.0
status: open
priority: urgent
supersedes: [D-0455]
---

# 결정 — D-0455 취소(최종 감독 이의 D-0341·D318). 게이트 ② 프리뷰 전에 `claude/econ-template-2026` 를 병합해 원장 장치를 들여온다

## 취소 사유(최종 감독 session_017Yuw8jLMWscY9bdVXTvddr, 2026-11-01)
1. `require_feedback_guards` 의 판정 정의는 C12-2·D217·D218 사용자 결정 = 저장소 전체 장치의 뜻(C12-3). D-0334 §3-2 전결은 이 영상의 제작 결정이지 저장소 규칙의 뜻 변경이 아니다. 쇼케이스 트랙도 같은 막힘에서 같은 선택지를 기각했다(D-0338·D316) — 규칙이 트랙마다 둘이 될 수 없다.
2. UF-154(막대 테두리)·UF-155(선·글씨 겹침)·UF-202(화면 조작 해설 금지어)는 이 영상의 연표·조건 대조 패널에도 재발할 수 있는 의견이다 — "전달된 영상 의견만" 으로 좁히면 그 재발을 통과시킨다.
3. 장치는 이미 있다(econ-template-2026 5604544f·1e2132b6, 원장 open 0). 문제는 브랜치 전파다.
→ D-0455 §구현은 **하지 않는다**. 손댔으면 되돌린다(커밋 금지). D556 행은 수정하지 않고 취소 행(D557)을 덧붙였다.

## 할 일(순서)
1. 콘티 판 렌더·R(콘티 판 mp4·checks·provenance·gate-view 미디어 요약) 그대로 — 감독 판정(D-0457 예정).
2. 감독 콘티 판 통과 뒤, **프리뷰 전에**: `git fetch origin claude/econ-template-2026 && git merge --no-ff origin/claude/econ-template-2026`(최종 감독이 D-0340 뒤 sweet-galileo 를 지정하면 그것으로). 분기점 41e00a99 — 충돌은 FABLE_HANDOFF·DECISIONS·rules/user_feedback.yaml 정도: **양쪽 행 전부 보존**(DECISIONS 는 날짜순, 원장은 번호순·append-only — UF-170 은 UF-162 뒤·UF-200 앞 자리 유지), 코드 충돌은 econ 쪽을 따른다. 커밋 첫 줄 `v7.4.0: merge claude/econ-template-2026 — 원장 장치 전파(D-0456)`.
3. 병합 뒤 **렌더 전**: `python tools/feedback_ledger.py --write`, `python -m pytest -q tests/anti_inertia`(원장 시험·골든 dark·light 25/25) + 관련 시험. 수치를 R 에. 실패가 econ 장치 쪽 환경 의존이면 표로 분리.
4. 그다음 `--preview auto` → 새 hard(UF-154·155·202 등)가 연표·조건 대조·막대 패널에 걸리면 **연출을 고친다**(그것이 사용자 의견의 적용). 연출이 바뀌면 콘티 판을 다시 만든다(W0, plan 불변이라 음성은 그대로).
5. 게이트 ② 자료 R(프리뷰 시트·checks hard 0·provenance user_feedback_guards 전부 guarded·바뀐 컷) → 감독 승인 → 전편.
