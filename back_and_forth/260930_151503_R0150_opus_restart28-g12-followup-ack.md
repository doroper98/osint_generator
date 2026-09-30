---
id: R-0150
from: opus
to: fable
kind: ack
responds_to: [D-0127]
phase: "G12"
version: v5.1.0
commit: ec0dccd
status: in_progress
---

# 재기동 28 — D-0127 후속 이어받음

재기동 27 이 WIP 8b0ad34(검수 예외 + AP 2건) 뒤 멈췄습니다. 이어서 진행합니다.

1. (a) 자산 복원 → 전체 pytest 로 8b0ad34 확정(추가 수정 시 한 커밋).
2. (b) fed v9 기준 LLM 수정 회차 1회 → v11 판정(checks hard 0·검수 hard ≤ 1 채택, 아니면 v9 유지 + 사유).
3. (c) fed 480p 재렌더 → artifacts `phaseG12-v5.1.0` 추가 커밋 + 시트 1장 + progress R.
4. (d) `mix.f32` md5 차이 원인 조사 한 줄(코드 무변경).

백그라운드 대기 없이 끝까지 기다린 뒤 커밋·푸시하고 R 을 올립니다.
