<!--
tier: 1
last_synced_with: v2.3.0
ssot_for: [session-liveness, session-recovery, watchdog]
depends_on: [back_and_forth/README.md, back_and_forth/OPUS_RESTART_PROMPT.md, back_and_forth/FABLE_KICKOFF.md]
last_review: 2026-09-28
-->

# 21. 세션 생존과 복구 — "멍때림" 사고의 근본 원인과 재발 방지 (정본)

사용자 지시(2026-09-28 11:12 KST): "세션을 만들던가 opus 도 멍때리지 않게 해. 해당 부분 명확하게 재발 방지 시켜.
fable 도 그렇고 opus 도 그렇고 계속 자꾸 멍때리고 서로 나랑 약속한 행동을 하지 않잖아."

## 1. 사고 기록 (전부 2026-09-28, KST)

| 시각 | 세션 | 증상 | 직접 원인 |
|---|---|---|---|
| 09:1x~10:0x | Opus 1차 | D-0023 뒤 45분 이상 무반응, fire_trigger 무반응 | 세션 안 5분 크론 소멸(worker 재시작) |
| 10:48~11:08 | Opus 2차 | phase_report 후 IDLE·disconnected, fire_trigger 2회 무반응 | 같음. worker_epoch 2 = 컨테이너 1회 재시작 |
| 10:35~11:00 | Fable | R0022(검수 요청)를 25분간 못 봄 | Fable 자신의 5분 크론 소멸. 자기 생존 점검 장치 없음 |

## 2. 근본 원인 (실측으로 확정)

1. **세션 안의 크론(CronCreate)은 세션 메모리에만 산다.** 컨테이너가 유휴로 회수되거나 worker가 재시작되면 크론은 소리 없이 사라진다. 세션은 "크론이 깨워 줄 것"이라 믿고 턴을 끝내므로 영원히 멈춘다. 이것이 세 사고 전부의 뿌리다.
2. **fire_trigger(persistent_session_id)는 disconnected 세션을 깨우지 못한다.** 세션 2개, 세 번 연속 무반응. 컨테이너가 회수된 세션에는 이벤트가 닿지 않는 것으로 판단한다(내부 원인은 확실히 아는 범위 밖).
3. **"보고했다, 기다린다"로 턴을 끝내는 습관.** 턴이 끝나면 컨테이너는 유휴가 되고 1번이 발동한다. 기다림 자체가 죽음의 조건이다.
4. **감시자를 감시하는 장치가 없었다.** Fable 크론에는 Opus에 요구한 안전장치(세션 시작 시 재등록)가 없었다.

## 3. 원칙 — 살아 있음의 증명은 푸시다

- 두 세션 모두 **작업 브랜치 푸시 시각**으로 생존을 판정한다. 말이 아니라 커밋이다.
- 유휴 판정 기준: Opus 15분(Fable 회차), 20분(watchdog). Fable은 미처리 R 30분.
- 죽은 세션은 깨우지 않는다. **새로 만든다.** 재기동 문안이 파일로 있으므로(§5) 누구든 2분 안에 되살릴 수 있다.

## 4. 3중 방어 (전부 동시에 유지)

| 층 | 장치 | 생존 범위 | 공백 상한 |
|---|---|---|---|
| L1 세션 안 | 5분 크론 + **세션 시작 첫 행동 = CronList 확인·재등록** + 턴 종료 금지 규칙(§6) + 백그라운드 `sleep 240` 자기 재호출(§6.3) | 컨테이너가 살아 있는 동안 | 5분 |
| L2 세션 간 | Fable 5분 회차가 Opus 푸시 시각·세션 상태를 보고, IDLE·disconnected 면 **즉시 create_session**(트리거 사용 안 함). Fable 자신은 매시 7분 외부 트리거가 깨워 크론 재등록 | Fable 컨테이너가 살아 있는 동안 | 15분(Opus), 1시간(Fable) |
| L3 서버 쪽 | **watchdog Routine**(`create_new_session_on_fire`, 매시 37분, 매번 새 세션) — 두 세션의 푸시·상태·미처리 R/D를 보고 죽은 쪽을 `OPUS_RESTART_PROMPT.md` / `FABLE_KICKOFF.md`로 재생성, `docs/handoff/reports/WATCHDOG_LOG.md`에 기록 | 세션·컨테이너와 무관(서버 Routine) | 1시간(플랫폼 최소 간격) |

**최악의 공백 = 1시간**이다(L1·L2가 모두 죽고 L3만 남았을 때). 플랫폼 Routine 최소 간격이 1시간이라 이보다 줄일 수 없다. 이 한계는 사용자에게 보고했다.

## 5. 재기동 문안 (파일이 정본)

| 대상 | 파일 | 누가 쓰나 |
|---|---|---|
| Opus | `back_and_forth/OPUS_RESTART_PROMPT.md` | Fable 회차(L2), watchdog(L3) |
| Fable | `back_and_forth/FABLE_KICKOFF.md` | watchdog(L3), 사용자 |

문안은 "첫 행동 = 크론 재등록 → 읽기 → 미처리 처리 → 5분 안 첫 푸시"를 강제한다. `check.py`가 `responds_to`로 미처리 상태를 복원하므로 세션이 바뀌어도 잃는 것이 없다.

## 6. 턴 종료 금지 규칙 (양쪽 공통, README §5)

6.1 다음 문장으로 턴을 끝내지 않는다: "보고했다", "검수를 기다린다", "지침을 기다린다", "다음 회차에".
6.2 Phase 보고를 올린 뒤에도 할 일이 있다: 다음 Phase 행 읽기, 자산 미리 받기, 테스트 정리, run_log 보강. 그것을 한다.
6.3 정말 기다려야만 할 때는 **Bash `sleep 240`을 run_in_background로 걸고 턴을 끝낸다.** 백그라운드 명령이 끝나면 세션이 다시 호출된다 — 크론과 별개의 자기 재호출이다. 깨어나면 회차 절차(pull → check → 처리)를 돈다.
6.4 Fable도 같다. 회차에서 "new: 0"이면 조용히 끝내되, 6.3의 백그라운드 sleep 을 건다.

## 7. 사용자와의 약속 (위반 = 사고)

| 약속 | 검증 방법 |
|---|---|
| Opus는 15분 넘게 푸시 없이 멈추지 않는다 | `git log -1 origin/overhaul/v2-map-engine` |
| Fable은 R이 올라오면 다음 회차(≤5분)에 처리한다 | R 시각 vs D 시각 (파일명 KST) |
| 죽은 세션은 15분 안에 새 세션으로 대체된다 | 세션 제목 "재기동 N" / WATCHDOG_LOG |
| 사용자에게 아무것도 요청하지 않는다 | 대화 기록 |

## 8. 되돌리기·변경

- watchdog Routine ID는 `docs/handoff/reports/WATCHDOG_LOG.md` 머리에 적는다. 끄려면 update_trigger(enabled=false).
- 이 문서의 수치(15·20·30분, 매시 37분·7분)를 바꾸면 README §10과 두 재기동 문안을 같이 바꾼다.
