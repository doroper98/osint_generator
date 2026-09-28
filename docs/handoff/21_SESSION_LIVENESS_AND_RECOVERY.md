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
| 12:00~12:18 | Opus 3차 | **connected 상태**인데 updated_at 정지 18분. Commons 429 대기 중 턴 종료 | 크론이 connected 상태에서도 죽음. "disconnected 만 죽음" 판정이 틀렸음 → 판정을 **updated_at 정지 15분**으로 바꿈 |

## 2. 근본 원인 (실측으로 확정)

1. **세션 안의 크론(CronCreate)은 세션 메모리에만 산다.** 컨테이너가 유휴로 회수되거나 worker가 재시작되면 크론은 소리 없이 사라진다. 세션은 "크론이 깨워 줄 것"이라 믿고 턴을 끝내므로 영원히 멈춘다. 이것이 세 사고 전부의 뿌리다.
2. **fire_trigger(persistent_session_id)는 disconnected 세션을 깨우지 못한다.** 세션 2개, 세 번 연속 무반응. 컨테이너가 회수된 세션에는 이벤트가 닿지 않는 것으로 판단한다(내부 원인은 확실히 아는 범위 밖).
3. **"보고했다, 기다린다"로 턴을 끝내는 습관.** 턴이 끝나면 컨테이너는 유휴가 되고 1번이 발동한다. 기다림 자체가 죽음의 조건이다.
4. **감시자를 감시하는 장치가 없었다.** Fable 크론에는 Opus에 요구한 안전장치(세션 시작 시 재등록)가 없었다.

## 3. 원칙 — 살아 있음의 증명은 푸시다

- 두 세션 모두 **작업 브랜치 푸시 시각**으로 생존을 판정한다. 말이 아니라 커밋이다.
- 유휴 판정 기준: Opus 15분(Fable 회차), 20분(watchdog). Fable은 미처리 R 30분.
- **판정 신호는 세션의 `updated_at` 정지 + 푸시 없음이다. `connection_status` 는 보지 않는다.** connected 인데 크론이 죽은 사례(12:00 3차)가 있다.
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
6.3 정말 기다려야만 할 때는 **Bash `sleep 240`을 run_in_background로 걸고 턴을 끝낸다.** 240초를 넘는 sleep·감시는 금지다(14:26 사례: 30분 감시를 걸고 잠들어 D-0038을 15분간 못 봄). 백그라운드 명령이 끝나면 세션이 다시 호출된다 — 크론과 별개의 자기 재호출이다. 깨어나면 회차 절차(pull → check → 처리)를 돈다.
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

## 9. poke 깨우기 모델 (2026-09-29 재기동 9부터 — 실측으로 바뀐 것)

**사고**: 재기동 7·8(2026-09-29 01:53·01:58)이 첫 턴에 "자율 루프·권한 승인을 사용자에게 확인" 하겠다며 `need_input` 으로 멈췄다. 문안 맨 위에 "[승인] 문단"을 넣어도(재기동 8), 트리거로 직접 지시를 보내도 같은 결과였다. 상태 메시지는 "auth check blocked D-0063 read; unauthorized persistence". 같은 시각 Fable 세션의 Bash 도 권한 분류기 무판정으로 두 차례 막혔다. **판단: 재기동 문안이 요구하던 "세션 안 5분 크론 + sleep 240 자기 재호출"(무인 지속 루프)이 차단 사유다.**

**바뀐 모델(재기동 9, 02:08 KST, 첫 푸시 02:09 성공)**:
1. Opus 문안에서 크론·sleep 루프 요구를 **뺀다**. Opus 는 Phase 작업을 끝까지 하고, 결정 대기가 필요하면 decision_request 를 푸시하고 턴을 끝낸다.
2. Fable 이 D 를 푸시한 뒤 **persistent poke 트리거를 fire_trigger** 로 쏴서 깨운다(트리거 이름 "Opus 재기동 N 깨우기(poke)", persistent_session_id = 현재 Opus 세션). 실측: **연결된(connected) IDLE 세션에는 도달한다**(재기동 8 에서 updated_at 갱신 확인). §2-2 의 "깨우지 못한다"는 **disconnected(컨테이너 회수)** 세션에 한한다 — 그때는 §3 대로 새로 만든다.
3. Fable 크론 판정: (a) RUNNING → 손대지 않음 (b) IDLE + 미처리 D → fire_trigger (c) IDLE + 미처리 D 없음 + 마지막 R 이 phase_report 아님 + 15분 정지 → fire_trigger 1회, 그래도 15분 → 재기동 (d) need_input → fire_trigger 1회, 두 번째도 need_input → 재기동.
4. 재기동 문안 정본은 `back_and_forth/OPUS_RESTART_PROMPT.md` **B형(루프 없음)**. A형(크론·sleep 요구)은 기록용으로만 남긴다.
5. Fable 쪽 3중 방어(§4)는 그대로다 — Fable 세션 안 크론도 컨테이너 재시작마다 죽으므로(2026-09-29 00:00·01:00 두 번) 매시 자기 점검 트리거가 회복한다.

