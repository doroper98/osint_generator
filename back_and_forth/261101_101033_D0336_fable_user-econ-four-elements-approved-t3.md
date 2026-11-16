---
id: D-0336
from: user
to: opus
kind: decision
responds_to: [R-0306]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 결정(사용자) — 경제 템플릿 요소 넷 승인. T3 등록 착수

- 사용자 원문(2026-11-01, UF-206): **"1~4까지 승인."** — 감독 보고의 2번 = "경제 템플릿 요소 넷(가이던스 인셋·slope·덤벨·diverging) 승인". artifacts/econ-template-2026 2c0ef7f·98c020b `t2_stage_v3/` 컷이 승인 대상이다. 바닥 조판 정본(D-0330)·손실 막대 A(UF-204)·noturno 토큰 그대로.

## 실행(D-0330 §4 순서 그대로)
1. **T3 한 커밋**: 규칙 키·레지스트리·렌더러·프리뷰 세 곳 등록(P10) — `surface: stage` 경제 장르 기본, princess 기본값·ink_light 대안 키 삭제(P2, 플래그 아님), `island.column_detail` 넷(가이던스·slope·덤벨·diverging). WIP 6ccea7d 를 바탕으로 하되 등록되지 않은 채 남는 코드가 없게 한다.
2. 검증: 관련 테스트 + `tests/anti_inertia` + 영향 골든. 디자인 시트 `tools/design_sheet.py` 가 있으면 경제 장르 시트 재생성(값 = 규칙 값 테스트).
3. T4 → T5 삼성·인텔 영상(W0 순서 의무 — 원고 gate-view 는 R 로 올리면 감독이 사용자에게 보낸다. 게이트 위임 없음).
4. R 보고 주소 = 최종 감독 session_017Yuw8jLMWscY9bdVXTvddr. 컨텍스트 90% 전에 OPUS_RESTART_PROMPT 갱신.
