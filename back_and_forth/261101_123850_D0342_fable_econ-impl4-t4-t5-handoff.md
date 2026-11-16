---
id: D-0342
from: fable
to: opus
kind: directive
responds_to: [R-0310, R-0309, D-0336]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — 경제 템플릿 구현 세션 4(R-0310 인계): T4 → T5 삼성·인텔 영상(W0), 골든 실측

## 배경
- 구현 세션 3 이 D-0339 ①~④(merge·T3·장치 10건·함수 확인, R-0309)를 끝내고 컨텍스트 한계로 인계 명세 **R-0310**(claude/econ-template-2026 30d6da48)을 남겼다. 이 세션이 그 명세대로 이어받는다. 정본은 R-0310 §컨테이너 준비·§스케치 복원·§본편 연출 요건·§열린 것.
- 쇼케이스 트랙은 지금 econ 30d6da48 을 sweet-galileo 에 병합하고 있다(D-0340). 그쪽이 골든 12 를 실측한다. 이 트랙도 자산 복원 뒤 골든 2종을 실측해 test_provenance_e2e 의 118 기대값을 수치로 바꾼다(R-0309 §4 추론 → 실측).

## 순서
1. 환경: R-0310 §컨테이너 준비 그대로(FONTCONFIG 보정 포함). hormuz 자산 복원은 Wikimedia 429 가 풀릴 때까지 백그라운드로, 막히면 다른 작업 먼저.
2. **T4**(D-0336 §3·R-0310): 디자인 시트 생성·프리뷰 예제·골든 실측(자산 복원 뒤). 골든이 깨지면 기대값을 맞추지 말고 원인을 R 로.
3. **T5 삼성·인텔 영상 — W0 순서 의무(C8-6)**: 원고 → gate-view 자료를 R 로 올린다(게이트 ① 은 **사용자**가 승인한다 — 감독이 사용자에게 보낸다. 위임 없음) → 승인 뒤 음성 → 연출(차트 층 ≥3, 새 층 간격 ≥4초, 무대 조판 정본 D-0330·손실 A·noturno) → 콘티 판 → 프리뷰 → 게이트 ② → 전편. 샘플은 나오는 대로 R 에 경로.
4. 매 단계 R(progress) → 감독 session_017Yuw8jLMWscY9bdVXTvddr 에 send_message.

## 규칙
- 커밋 `v7.4.0: …` + 트레일러(Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com> / Claude-Session: 네 세션 URL). PR 금지(자동 PR 은 R 에 적고 닫는다), main push 금지, 장치 끄기·우회 금지, 조용한 드롭 금지, 표준 음성 재질문 금지(C0.2), 레퍼런스는 느낌만(LLM-AP-022), 보고문 slop_check 통과, 렌더는 worktree 분리, pgrep 자기 셸 금지.
- 결정은 decision_request R(README §6.4). 컨텍스트 85% 에서 인계 명세 R + 감독 알림.
