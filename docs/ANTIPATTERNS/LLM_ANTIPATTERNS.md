<!--
tier: 3
last_synced_with: v0.2.1
ssot_for: [llm-antipatterns]
depends_on: [README.md, ../ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md, ../../CLAUDE.md]
last_review: 2026-05-19
-->

# LLM Bridge Antipatterns

본 문서는 **구독 LLM Bridge 패턴** (`docs/ADDENDUM_04`) 운용 중 발견된 안티패턴 카탈로그입니다.

`claude` · `codex` CLI 의 subprocess 호출, BaseLLMWorker 의 응답 파싱·검증, 추적성 파일 (`llm_calls/{call_id}.json`) 관련 사고가 본 파일에 누적됩니다.

**append-only**. 과거 항목 수정 금지. 정정은 새 번호로 추가 + 기존 항목에 `[superseded by LLM-AP-NN]` 마킹.

엔트리 포맷은 `docs/ANTIPATTERNS/README.md` 의 표준을 따릅니다.

---

## (현재 등록 항목 없음 — v0.2.1 시점 카테고리 신설만 완료)

> Phase 3 의 `IntakePlannerWorker` 첫 실 호출에서부터 항목 누적 예정.
