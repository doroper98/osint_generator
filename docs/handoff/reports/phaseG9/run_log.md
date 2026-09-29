<!--
tier: 3
last_synced_with: v4.10.0
ssot_for: [phaseG9-run-log]
depends_on: [rules/video_rules.yaml, geo/gazetteer.py, workers/base_llm_worker.py, back_and_forth/260930_042435_D0116_fable_phase-g8-review-pass-g9-kickoff.md]
last_review: 2026-09-30
-->

# Phase G9 실행 기록 — 정비 3건 (v4.10.0)

지침 D-0116. 재기동 23 세션. 전편 렌더 없음(D-0103) — checks·pytest 로만 확인.

## 0. 컨테이너 준비

phaseG8 run_log §0(= G7 §0) 그대로(하위 에이전트). 지오 자산 hormuz 21/21·랫클리프 15/15(G7 `asset_md5.json`), 청와대 휘장 md5 일치.
fed_policy `out/mix.f32` 는 G4 `mix.flac` 을 풀어 만들었다(G5 절차).

## 1. 지명 사전 대조 결과(`geo.gazetteer.check_doc`, 좌표 무변경)

| 프로젝트 | matched | mismatch | unsourced | 최대 오차 비율 |
|---|---|---|---|---|
| hormuz_korea(골든) | 8 | 0 | 3(paths 2·route 1) | 0.40(호르무즈 해협 15.9/40km) |
| ratcliffe2026(골든) | 6 | 0 | 1(path) | 0.30 |
| dmz_mine_2026 | 6 | 0 | 2(dmz_site·paju_2015 — 사건 지점) | 0.47 |
| hormuz_ai·_cam | 4 | 0 | 4 | 0.40 |
| taiwan_strait | 1(인라인 marker 타이베이) | 0 | 0 | 0.04 |
| taiwan_ai·f1 2종 | 0 | 0 | 3 | — |

- 수기 좌표 = 위키백과 API coordinates·위키데이터 P625(2026-09-30 조회), 폴란드 = NE 110m 폴리곤 무게중심.
- 믈라카 해협 수기 항목은 hormuz_ai 의 place `malacca`(label "믈라카 해협")가 도시 Malacca(NE)와 동음이의로 174km hard 가 나서 추가했다(골든 밖).
- 사전 크기 385KB(NE 3119 + 수기 9), PyYAML 순수 파이썬 로드 약 2.2초(프로세스당 1회 캐시).

## 2. 귀속 표현 "보도했" 영향

| 프로젝트 | 린트 attribution 경고 | claims status 변화 |
|---|---|---|
| hormuz_korea | 0 → 0 | 해당 없음(v3 이관 claims, 인용 대조 판정 아님) |
| ratcliffe2026 | 2 → 1 | 0 (supports 근거 본문에 "보도했" 없음) |
| fed_policy_2026 | 8 → 0 | 0 (같은 이유) |
| dmz_mine_2026 | 15 → 14 | (claims 재판정 대상 아님) |

추적된 verify draft 가 없어 judge 재실행은 불가 — 인용은 본문의 연속 부분 문자열이어야 하므로 본문에 없는 표현은 인용에도 없다(`tests/test_g9_attribution.py::test_judged_claims_cannot_change`).

## 3. 판단 기록(되돌릴 수 있는 선택)

| 쟁점 | 선택 | 근거 |
|---|---|---|
| 동음이의(aden = 도시·만) | 맞은 항목 중 하나라도 오차 안이면 통과, place 키 + 그 place 를 쓰는 marker label 로 대조 | 골든 label "아덴만" 이 의도를 밝힌다. label 없이 키만이면 hard |
| 모듈 위치 | `geo/gazetteer.py` | 구면 거리(삼각함수)는 engine 무대 격리(anti_inertia) 밖 |
| codex 도 stdin | `codex exec … -` | argv 경로 삭제(P2)를 백엔드 전체에 |
| stdin 인코딩 | UTF-8 고정 | Windows cp949·POSIX 로캘에서 한국어 프롬프트 |
| 프롬프트 | `{{RULES.attribution_markers}}` 를 script·verify_sources 에 | 린트·판정과 같은 목록(P3) |
