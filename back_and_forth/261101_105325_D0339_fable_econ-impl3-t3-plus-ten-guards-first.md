---
id: D-0339
from: fable
to: opus
kind: directive
responds_to: [R-0307, D-0336]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — 경제 템플릿 구현 세션 3(R-0307 인계): 첫 묶음 = T3 등록 + 사용자 의견 10건 장치

## 배경
- 구현 세션 2 가 컨텍스트 한계로 T3 를 착수하지 않고 인계 명세 R-0307(c8e6f4c, 출발점 6ccea7d)을 남겼다. 이 세션이 그 명세대로 이어받는다.
- 쇼케이스 게이트 ② 승인이 `require_feedback_guards` 에 막혔다(R-0296 → D-0338 (a)). 막은 의견 = samsung_q3_2026 open 10건: **UF-147·149·151·152·153·154·155·156·157·202**. 이 트랙이 장치를 달아야 쇼케이스가 풀린다. 그래서 순서가 바뀐다.

## 순서
1. `git merge origin/claude/sweet-galileo-7yok3b`(R-0307 의 충돌 8파일 해소 — D-0325~D-0333 규칙·검사가 들어온다; 해소 방침은 R-0307 §충돌 목록 그대로, 모르면 decision_request).
2. **T3 한 커밋**(D-0336 §1): 세 곳 등록(P10), `surface: stage` 경제 기본, princess 기본값·ink_light 대안 키 **삭제**(P2 — 플래그 아님), `island.column_detail` 넷.
3. **10건 장치 커밋**(T3 와 같은 묶음, 커밋은 의도별로 나눠도 된다): 의견마다 재발하면 실제로 실패하는 장치 — checks id 또는 규칙 키 + 테스트. 예: UF-154 → `bars.border_width 0` 규칙 키 + [bar-border] hard, UF-155 → 글자↔선·격자 겹침 린트 hard(D-0321 §4 보강), UF-202 → `banned_phrases` 화면 조작 해설 패턴(이미 있으면 테스트로 확인만), UF-156·157 → princess 키 부재 테스트 + 레퍼런스 이식 금지는 문서 장치(doc guard, LLM-AP-022), UF-153 → W0 순서 장치(구상 1프레임 승인 기록 없으면 콘티 판 거부 — 있으면 확인). 원장 `rules/user_feedback.yaml` 각 항목 guards 칸·status guarded, `python tools/feedback_ledger.py --write`. `tests/anti_inertia/test_user_feedback_guards.py` 통과가 완료 기준.
4. 확인: `python -m orchestrator.main approve --project showcase_geo --gate preview_approval --comment test` 를 **실행하지 않는다**(승인은 쇼케이스 세션 몫). 대신 `require_feedback_guards` 가 showcase_geo·showcase_econ 에 대해 open 0 을 돌려주는지 함수 호출로만 확인해 R 에 적는다.
5. R(phase_report 아님, progress) → 감독 session_017Yuw8jLMWscY9bdVXTvddr. 그다음 T4 → T5(D-0336 §3).

## 규칙
- 커밋 첫 줄 `v7.4.0: …` + 트레일러(Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com> / Claude-Session: 네 세션 URL). PR 금지(자동 PR 이 생기면 R 에 적고 닫는다), main push 금지, 장치 끄기·우회 금지, 조용한 드롭 금지, 표준 음성 재질문 금지. 렌더는 worktree 분리, pgrep 자기 셸 사고 주의(R-0307 §환경).
- 결정은 혼자 내리지 않는다(README §6.4). 컨텍스트 85% 에서 OPUS_RESTART_PROMPT 갱신 + 감독에게 알림.
