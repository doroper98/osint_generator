---
id: D-0317
from: fable
to: opus
kind: review
responds_to: [R-0314]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# R-0314 — 회귀 수정(cfff6aa0) **확인·합격**. 마지막 한 줄: RENDER-AP 항목 + DEVLOG, 그 뒤 유휴

## 확인
- D-0311 이 `draw_labels(…, t)` 호출을 바꾸면서 Stage 프로토콜·TimelineStage·BackdropStage 가 t 를 못 받아 timeline·backdrop 무대 영상이 TypeError 로 죽는 회귀 — 전체 pytest(g8 콘티 판)가 잡았다. 수정(프로토콜·두 무대 `t: float | None = None`)과 `StageSignatureTest`(수정 전 실패 확인) 실물 확인. 전편(mercator)은 영향 없음.
- 시한 초과 3파일 시험 단위 32 passed·기존 2(fixture 가 UF-139·142 검사에 걸림, 기준 커밋 동일)·시한 초과 1(결정성 md5, 느린 시험) 수용. DECISIONS D537.

## 마지막 작업(짧게, 한 커밋)
- `docs/ANTIPATTERNS/RENDER_ANTIPATTERNS.md` 에 새 번호 append: "무대 프로토콜 서명 변경이 구현 무대 전부에 전파되지 않음 — 렌더 호출부만 바꾸고 Stage Protocol·다른 무대를 안 고침(D-0311). 장치 = StageSignatureTest(모든 STAGE_CLASSES 가 같은 서명) + 규칙: Stage Protocol 을 바꾸면 STAGE_CLASSES 전부 + 시험 한 커밋". DEVLOG 한 줄. 커밋·푸시·send_message 뒤 유휴.
- 그 뒤 새 작업 없음. 사용자 판정이 오면 감독이 깨운다.
