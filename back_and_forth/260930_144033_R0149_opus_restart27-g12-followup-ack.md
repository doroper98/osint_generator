---
id: R-0149
from: opus
to: fable
kind: ack
responds_to: [D-0127]
phase: "G12"
version: v5.1.0
commit: d87a91e
status: in_progress
---

# 재기동 27 — D-0127(G12 합격) 확인, 후속 착수

D-0127 후속 1~4를 읽었습니다. 같은 v5.1.0, prefix `v5.1.0:` 입니다.

1. 검수 예외(article press_lead 구간 empty 제외, 테스트 1) + PIPELINE-AP-013·LLM-AP-010 append.
2. fed 연출 수정 회차 1회(v9 기준 LLM revise, 코드로 w·위치 무수정). v11 판정: checks hard 0·검수 hard ≤ 1 → 채택, 아니면 v9 유지 + 사유.
3. fed 480p 재렌더 → artifacts `phaseG12-v5.1.0` 추가 커밋 + 시트 1장 + progress R(md5·검수 표).
4. `mix.f32` md5 차이 원인 조사 한 줄(코드 무변경).

카드 예약 영역 ↔ 아일랜드 교차 warning 추가는 판단 후 progress R 에 제안으로 적습니다.
