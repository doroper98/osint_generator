<!--
tier: 3
last_synced_with: v5.0.0
ssot_for: [phaseG11-rejudge]
depends_on: [tools/g11_rejudge.py, orchestrator/source_verify.py, back_and_forth/260930_101753_D0119_fable_phase-g10-review-pass-g11-goal-g4-kickoff.md]
last_review: 2026-09-30
-->

# Phase G11 재판정 표 — claim_kind 도입 전/후 (v5.0.0, GOAL G4-21)

지침 D-0119 §5. 도구 `tools/g11_rejudge.py`(읽기만, 결정적). 원자료 `rejudge.jsonl`.

```bash
python tools/g11_rejudge.py projects/hormuz_korea projects/ratcliffe2026 projects/fed_policy_2026 projects/dmz_mine_2026 \
  docs/handoff/reports/phase6_95/e2e/project > docs/handoff/reports/phaseG11/rejudge.jsonl
```

## 1. 입력

| 프로젝트 | claims.json md5 | 출처 |
|---|---|---|
| hormuz_korea | `fbe42077…` | v3 이관(`tools/migrate_v3_claims.py`) |
| ratcliffe2026 | `930c98ab…` | phase9 verify-sources |
| fed_policy_2026 | `2e7ca00d…` | G4 verify-sources |
| dmz_mine_2026(참고) | `75ad01bf…` | G6.5 병합본 |

과거 실행은 `intake/verify_draft.json` 을 프로젝트에 남기지 않았다(artifacts 브랜치 포함 전 브랜치 검색 — 보고서 사본 phase6_95 e2e 하나뿐, 그것도 기사 본문 보관본 없음).
그래서 인용 대조를 다시 돌릴 수 없는 프로젝트는 **기록 투영**으로 적는다(§3).

## 2. 재판정 결과 — status 변화 0

| 프로젝트 | claims | 전 → 후 변화 | 이유 |
|---|---|---|---|
| hormuz_korea | 45 | **대상 아님** | v3 이관 claims(checks `v3_user_approved`) — 판정 경로를 거치지 않은 사용자 합격본 |
| ratcliffe2026 | 17 | 0 (corroborated 6·unverified 7·disputed 4 그대로) | 기존 draft 에 `claim_kind` 없음 → fact(기본). fact 경로 코드 무변경 |
| fed_policy_2026 | 42 | 0 (verified 20·corroborated 8·unverified 11·disputed 3 그대로) | 같음 |
| phase6_95 e2e 사본 | 4 | 판정 불가 | 기사 본문 보관본 없음(`no_bodies`) |

fact 경로가 무변경이라는 증명: 옛 모양 draft(`claim_kind` 필드 없음)를 v5.0.0 `judge` 로 다시 돌려 claims 가 같다(테스트 `RejudgeToolTest`),
그리고 v4.11.0 판정 테스트(`tests/test_source_verify.py`·`test_g9_attribution.py`) 전부 통과.

**화면 영향 0(D85)**: claims.json 파일은 바뀌지 않았다(도구는 읽기만, md5 위 표). 렌더·원고 경로(engine·script·bundle·audio)는
`claim_kind` 를 읽지 않는다. 검증 상태는 엔딩 카드 맨 끝 한 줄에만 쓰이고 그 입력(status)이 같다. 전편 렌더 없음.

## 3. statement 로 다시 뽑는다면(투영) — 새 프롬프트로 LLM 을 다시 돌릴 때의 예상

투영 대상 = 문장이 발언 모양(`attribution_markers` 가 문장에 있음, "확인되지 않" 제외)이고 귀속 근거(checks `attributed:`)가 있는 claim.

| 프로젝트 | 발언 모양 claim | 바뀔 수 있는 것 |
|---|---|---|
| ratcliffe2026 | 0 | 없음 |
| fed_policy_2026 | 0 | 없음(clm_0030 "요구했다"는 귀속 표현 목록 밖 — LLM 이 statement 로 다시 쓰면 대상) |
| dmz_mine_2026 | 6 | 아래 |

dmz_mine_2026(참고, D-0119 대상 밖):

| claim | 전 | statement(contested 유지) | statement(새 프롬프트, contested 없음) | 귀속 origin | 폐기될 단정 인용 |
|---|---|---|---|---|---|
| clm_0009 합참 "조사 중이라고 밝혔다" | unverified | unverified | unverified | 1 | 0 |
| clm_0014 합참 "가능성이 매우 높다고 발표했다" | unverified | unverified | **corroborated** | 2(시사저널·한국일보) | 8 |
| clm_0025 합참 "상응 조치를 하겠다고 밝혔다" | unverified | unverified | unverified | 1 | 3 |
| clm_0030 국방장관 "유실 아닌 것으로 보인다고 말했다" | unverified | unverified | unverified | 1 | 0 |
| clm_0032 국방장관 "단계적으로 시행하겠다고 말했다" | unverified | unverified | unverified | 1 | 1 |
| clm_0034 청와대 "관련이 없다고 밝혔다" | disputed | disputed | unverified | 1 | 2 |

읽는 법: G4-21 이 뜻하는 변화는 **clm_0014 한 건**이다 — 두 매체가 같은 공식 발표를 전하므로 "발표가 있었다"는 corroborated.
그 내용("북한군 지뢰일 가능성이 매우 높다")은 여전히 교차 확인이 아니다. 단정 인용 8건은 statement 의 근거가 아니어서 폐기된다
(현재 apply_draft 는 drops 가 있으면 실패 — R-0143 ①).
