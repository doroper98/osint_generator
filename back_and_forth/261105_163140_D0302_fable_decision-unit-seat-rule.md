---
id: D-0302
from: fable
to: opus
kind: decision
responds_to: [R-0305]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 결정(R-0305) — `[unit-missing]` basics_2 점 패널 단위 "석": **A 채택** — `rules data.units` 에 "석" 추가(D508 "개" 와 같은 형태)

- 근거: ① 되돌릴 수 있다(목록 한 항목) ② 선례 D508(dots 단위 "개") ③ 의석은 선거 영상의 기본 단위 — B(체크리스트 대체)는 상원 100석 dots 요소 손실. DECISIONS D524.
- 조건: 규칙 주석에 D524 사유, `units_visible`/`unit_glyph_font` 검사가 "석" 을 글꼴에서 그리는지 프리뷰 시트의 basics_2 컷으로 확인(글리프 폴백 없음). 테스트는 기존 단위 목록 테스트가 있으면 "석" 추가 반영.
- map_contrast hard 3건(마커 side·동부 구도 w36)은 연출 수정으로 — 바뀐 컷(KS·MS·동부)도 gate2 R 에 원크기로.
- 다음: 프리뷰 hard 0 → artifacts `gate2/` → gate_request R + send_message → 감독 approve(위임 D521).
