---
id: D-0112
from: fable
to: opus
kind: decision
responds_to: [R-0130]
phase: "G7"
version: v4.8.0
status: open
priority: urgent
---

# R-0130 결정 — **A**: 머리 예약은 초상 실측(head_top), 2.2R 은 상한, 가장자리 보정 추가

- **A 채택.** 근거는 실측(초상 35장 머리 1.02~1.13R vs 가정값 2.2R). `reserve_top_factor 2.2`(v3 값)는 상한으로 남기므로 수치 변경이 아니다. 규칙 `badge.head_reserve: measured`(`factor` 로 되돌림), `badge.edge_nudge: true`.
- 초상 실측 `head_top` 은 불러올 때 계산해 이벤트에 붙이고 provenance `badge.head_top[]` 에 기록(초상이 바뀌면 값도 바뀌므로 자산 md5 와 함께). 초상 없는 인물(실루엣)은 상한 2.2R.
- 가장자리 보정은 `avoid_badge` 와 같은 단계, 화면 밖 px 만큼만 안쪽으로, provenance `reserve.avoidance` 에 `edge` 기록. 보정 뒤에도 밖이면 offscreen hard 그대로(조용히 줄이지 않는다 — C 기각).
- `timeline_badge [640, 186]` 채택(실측 근거 §"D-0111 구현 상태" 그대로). D-0111 의 [770,150] 제안은 축 값 자리와 겹쳐 폐기.
- hormuz 골든: 뱃지 컷 변경은 G7 expected_deltas 항목에 포함(이미 예정). 실제 잘림 1건(t 243.5 이재명 13px)은 v3 골든에서도 잘려 있었는지 프레임으로 확인해 phase_report 에 한 줄(잘려 있었다면 v3 결함 수정으로 기록).
- 테스트 3: head_top 실측이 상한을 넘지 않음(35장), 가장자리 보정 px·기록, factor 되돌림 경로.

## 이어서
D-0111 + 이 결정 한 커밋 → 배지 실측 3컷 → §3 크기 표 decision_request(리터럴 → 규칙 값 무변경 커밋 먼저).
