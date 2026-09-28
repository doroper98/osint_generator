# watchdog 기록 — 세션 생존 감시견 (docs/handoff/21)

- Routine: `trig_01KqLiKzkjjFKcj5vKdEZETx` (매시 37분, 새 세션, KST 표기)
- Fable 자기 생존 점검: `trig_015Xzm8MRheqrSNDsmveeUA9` (매시 7분, Fable 세션 session_01MtZZPVZpTNRDV7W9fwuUqj)
- 첫 회차 예정: 2026-09-28 11:37 KST

| 시각(KST) | Opus | Fable | 마지막 푸시 | 미처리 R/D |
|---|---|---|---|---|
| 2026-09-28 11:11 (설치, 수동) | 재기동 3 session_01VcECYiN54XnDAkGZx7Sxyw RUNNING | Fable 크론 9437727c 재등록 | 11:09 | 0/2 |
| 2026-09-28 12:19 (Fable 회차, 수동) | 재기동 3 IDLE·connected, updated_at 12:00 정지 18분(크론 사망, 'strikes.webm 대기 3/6') → archive, **재기동 4 session_0147v8bbQQSmzdbLyTubyZfo** 생성 | Fable 크론 e5ed60dd 재등록(판정에 'connected 여부 무관, updated_at 정지' 추가) | 12:00 | 1(progress)/0 |
