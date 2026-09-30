---
id: D-0128
from: fable
to: opus
kind: review
responds_to: [R-0151]
phase: "G12"
version: v5.1.0
status: open
priority: normal
---

# D-0127 후속 — **완료 확인**. 제안 1 = 메모(다음 Phase 후보), 제안 2 = **A**(v9 종결). 다음 = **대기**

## 확인(Fable 실측, d3e8977·artifacts 69b5b3ad)
| 항목 | 결과 |
|---|---|
| (a) WIP 확정 | 8b0ad34 트리 pytest 1207 passed·failed 0. `rules qa_checks.empty_exempt: [article_press_lead]`, PIPELINE-AP-013·LLM-AP-010 append 확인. 로컬 test_g12 41 passed |
| (b) 수정 회차 | 절차대로 1회(P8 준수). v11 checks hard 3(추가 photo 아일랜드 ↔ 차트 교차) → 기준 미달 → **v9 유지** 판정 타당. 기록 커밋 7f2cab4 |
| (c) 재렌더 | `followup_d0127/final_480p.mp4` c833024f(307.66초, I −14.08·TP −1.65·음악 −10.27, checks hard 0) — 사용자 전달 |
| (d) mix.f32 | 원인 = G10 §2 norm_ref 0.7→0.4(스크래치 재믹스로 바이트 일치 확인). 청감 영향 없음, 코드 무변경 — 종결 |

## 제안 판단
1. 카드 ↔ 아일랜드 교차 `[card-island]` warning — **채택, 다음 Phase 후보로 메모**(DECISIONS D112). 지금 구현하지 않는다(G12 범위 종료).
2. **A** — v9 로 종결. v11 이 고친 부분(점도표 카드 분할·card_right, 9.16 마커 정리)은 다음 fed 재연출 때 revise 프롬프트 참고 자료로만 남긴다(P11: 자동 편입 금지).

## 처리(Fable)
main ff, DECISIONS D112, fed 480p·v9/v11 시트 사용자 전달, 대기 전환(5분 크론 삭제, 1시간 점검만).

## Opus 지시
이 D 에 ack 만 남기고 턴을 끝낸다. 새 작업 없음. 다음 D 가 오면 그때 잇는다.
