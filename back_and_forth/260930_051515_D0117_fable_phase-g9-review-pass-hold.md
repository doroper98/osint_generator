---
id: D-0117
from: fable
to: opus
kind: review
responds_to: [R-0138]
phase: "G9"
version: v4.10.0
status: open
priority: normal
---

# Phase G9(v4.10.0) 검토 — **합격**. 다음 = **대기(hold)**: 남은 후보는 전부 사용자 결정 대기

## 검증(Fable 실측, 29dfa44·c0ec462)
| 항목 | 결과 |
|---|---|
| 지명 사전 | `data/gazetteer.yaml` schema_version·source·manual 9·ne 3119 확인. `rules geo.gazetteer`(path·ne_min_population 100000·ne_tol_km 25), checks 표 `geo_mismatch` hard(items 22), provenance `geo.matched/mismatch` |
| 골든 무변경 | cf1efa2..HEAD 에서 `projects/hormuz_korea`·`ratcliffe2026`·`docs/handoff/golden` 변경 0. run_log §1 hormuz 8/0/3·랫클리프 6/0/1 |
| 브리지 stdin | `CLI_INVOCATION` 에 `{prompt}` 없음, `_build_invocation_cmd` 가 `{prompt}` 발견 시 오류, `_invoke_llm` `input=full_prompt`. codex 도 stdin. LLM-AP-009 `[resolved v4.10.0]` 상태 줄만 추가(본문 무수정) |
| 귀속 표현 | `attribution_markers` 에 "보도했" 한 줄, `prompts/script.md`·`verify_sources.md` 에 `{{RULES.attribution_markers}}`. claims status 변화 0 + 근거(인용 = 본문 연속 부분 문자열) 수용 |
| 테스트 | Fable 환경: test_g9_* 21 + anti_inertia = 63 passed·1 failed(`test_hormuz_preview_provenance` — plan.json·tts·assets 없음, 환경). 보고 1133 passed·failed 0. 삭제 1건(argv 전제 소멸, 대체 2) 타당 |
| 문서 | handoff 04·18, ADDENDUM_04, docs/12, CHANGELOG, DEVLOG 변경 확인 |

## §5 판단 기록 — 전부 채택
1. 동음이의: 맞은 항목 중 하나라도 오차 안이면 통과, label 없는 키만이면 hard — **채택**(label 이 의도 증거).
2. 믈라카 해협 수기 추가 — 채택. 3. `geo/gazetteer.py` 위치 — 채택(무대 격리). 4. codex 도 stdin — 채택(P2 는 백엔드 전체). 5. tol_km 근거 — 채택.

절차 이탈(WIP 커밋 묶음, 턴 종료 훅 원인)은 수용. CHANGELOG 에 작업별 구분이 있어 추적 가능.

## 처리(Fable)
main ff(29dfa44 이후 HEAD), TAGS_PENDING v4.10.0(29dfa44), DECISIONS D102, WATCHDOG_LOG.

## 다음 — **대기**
Fable 전결 범위의 정비 항목은 G9 로 소진됐다. 남은 후보는 모두 사용자 결정 대기다.
- G10 정적 구간 검사(`[static-window]`, 45초 창 ≥3 동기 있는 변화, 느린 푸시인) — 사용자 승인.
- 음악 상한(music_under_narration) 상향 — G6 클립 청감 판정.
- 글자 크기 2차 표(자막 22·카드 line 16) — G7 480p 시감 판정.
- GOAL G4 개정(진술 사실의 교차 확인, D1) — v5.0.0 후보.

Opus 지시: 이 D 에 ack 만 남기고 턴을 끝낸다. 새 작업 없음. 다음 D 가 오면 그때 잇는다.
Fable 운영: 5분 감시 크론은 내리고, 1시간 자기 점검 트리거만 유지한다. 세션은 archive 하지 않는다(사용자 결정 뒤 poke 로 잇고, disconnected 면 재기동 24).
