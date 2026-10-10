<!--
tier: 3
last_synced_with: v5.16.0
ssot_for: [phaseV2-run-log]
depends_on: [docs/handoff/reports/phaseV1/run_log.md, script/tts/forced_align.py, script/tts/align_gate.py, script/plan.py, engine/timebase.py, config.yaml, rules/video_rules.yaml]
last_review: 2026-10-11
-->

# Phase V2 실행 기록 — 강제 정렬(MMS_FA + uroman) (v5.16.0)

지침은 D-0164 §5 입니다. 게이트 기준은 D-0165(DECISIONS D159)로 정해졌습니다. 사용자 결정 D151(정렬 없음 = 오류)을 따릅니다.
V2 는 정렬을 만들고 검증하는 데까지입니다. 골든 플랜은 edge 그대로입니다(Supertonic 플랜 교체·영상 재현은 V3).

## 1. 만든 것

| 파일 | 내용 |
|---|---|
| `script/tts/forced_align.py` | `align_sentence(audio, pron_text) → [CharSpan]`, `align_file`(공통 형식 + `score_mean`·`elapsed_ms`), `word_starts`, `sentence_score`. 모델은 프로세스당 1회, 가중치 sha1 대조 뒤 로컬 파일로만 연다 |
| `script/tts/align_gate.py` | 게이트 3검사 CLI(`python -m script.tts.align_gate <proj>… [--edge]`). 참값·대응·간격 정의는 §3 |
| `script/tts/align.py` | `from_forced_alignment` — 글자 수·글자 불일치 = 오류 |
| `script/plan.py` | Supertonic 합성 직후 문장마다 정렬 → `.align.json`. 같은 발음 텍스트의 MMS 정렬은 재사용. 실패 = plan 실패 |
| `script/schema.py` | `PlanSentence.alignment {source, score_mean, elapsed_ms}`(optional) |
| `engine/provenance.py` | `features.alignment {sources, score_mean_min, elapsed_ms_total}` — plan 에 정렬 기록이 있을 때만(P5) |
| `engine/timebase.py` | `at_word` 정렬 파일 없음 = `AlignmentMissingError`(D151). 비율 추정은 "단어가 발음 텍스트에 없음"만 |
| `config.yaml tts.alignment` | 가중치 URL·sha1(`0300fd9a…`)·스레드 4 |
| `rules tts_rules.forced_align` | `min_score 0.62`, `silence_thr 0.012`, `silence_sec 0.15`, `match_window_sec 0.3`, `gate {median_ms 60, p90_ms 120}` |
| `tools/fetch_data.py mms_fa` | 없거나 sha1 이 다르면 받고 대조. 완료 메시지가 실제 저장 위치를 찍음(supertonic 도, D-0155) |

## 2. 가중치·성능

| 항목 | 값 |
|---|---|
| 가중치 | `assets/tts/mms_fa/model.pt` 1,262,047,414 B, sha1 `0300fd9ae57a63e3bd239ae1337e32127a587214`(미추적) |
| **라이선스** | **MMS 가중치 = CC-BY-NC 4.0(비상업).** 채널 수익화 여부에 따라 사용자 확인이 필요한 항목입니다. 코드(torchaudio)는 BSD |
| 모델 로드 | 10~13초(프로세스당 1회) |
| 문장당 정렬 | 중앙값 0.90초(Supertonic 45문장, plan 안), 0.92~1.13초(edge 93문장, CPU 4코어) |
| 호르무즈 45문장 합성 + 정렬 + 트림 | 195초(합성 포함) |
| 결정성 | 같은 입력 2회 = 같은 json(테스트 `test_deterministic`) |

## 3. 게이트 정의(D-0165 §2, 코드 = `script/tts/align_gate.py`)

1. **절대 시각**: 참값 = 음향 발화 시작. 원본 음성(44.1k mono)에서 `|a| ≤ 0.012` 가 0.15초 넘게 이어진 뒤 첫 초과 샘플, 그리고 문장 첫 소리.
   참값 k 번째 ↔ 정렬 어절 시작은 순서·단조로 대응합니다(±0.3초 안 가장 가까운 것). 대응 없는 참값은 0.3초 오차로 계상합니다.
2. **간격 일치**: 같은 문장 안 연속 어절의 간격 차 `|(MMS_b − MMS_a) − (edge_b − edge_a)|`. 두 어절 모두 edge 시각이 무음 밖일 때만 셉니다.
3. **제작 음성 반복**: 호르무즈 45문장 Supertonic(M3 ×0.95) 음성에 1 번.
4. **이동 불변**: 앞에 0.5초 무음 → 모든 어절 0.5초 ± 20ms(픽스처 테스트).

**신뢰도 문턱 근거(min_score 0.62)**: 어절 점수는 정답·오답을 가르지 못했습니다. 숫자 어절(육십일·육백삼십 등)은 철자 로마자와 실제 발음이 달라
점수가 0.01까지 떨어지지만, 시각은 맞았습니다(육백삼십: MMS 5.147초 ↔ 발화 시작 5.13초). 그래서 문턱을 **문장 점수**(어절 점수 평균)에 겁니다.
맞는 원고 93문장 최저 **0.679**(p5 0.758), 틀린 원고(7문장 뒤 원고를 붙인 93쌍) 최고 **0.569**(p95 0.506). 그 사이 0.62 입니다.

## 4. 결과 — 합격

| 검사 | 모집단 | n | 중앙값 | p90 | 대응 없음 | 판정 |
|---|---|---|---|---|---|---|
| 1 절대 시각(edge 음성) | 호르무즈 45 + fed 48 | 173 | **21.1ms** | **40.1ms** | 0 | 합격 |
| 2 간격 일치(edge 음성) | 같은 93문장 | 519 | **24.5ms** | **68.5ms** | — | 합격 |
| 3 절대 시각(Supertonic) | 호르무즈 45 | 82 | **16.4ms** | **31.7ms** | 0 | 합격 |
| 4 이동 불변 | 픽스처 1문장 | 전 어절 | — | — | — | 0.5초 ± 20ms 합격 |
| 픽스처 게이트 | 픽스처 10문장(1·2) | — | — | — | — | 합격(테스트) |

행 데이터: `gate_edge_rows.json`(검사 1·2), `gate_supertonic_rows.json`(검사 3).
프로젝트별 절대 시각: 호르무즈 85개 23.8/38.1ms, fed 88개 18.1/40.8ms.

히스토그램(ms 구간 0·10·20·30·40·60·80·120·200·300):
- 검사 1: 30 · 49 · 48 · 28 · 12 · 6 · 0 · 0 · 0 (최대 78.4)
- 검사 2: 123 · 99 · 79 · 62 · 77 · 46 · 24 · 9 · 0 (최대 162.8)
- 검사 3: 23 · 28 · 20 · 8 · 3 · 0 · 0 · 0 · 0 (최대 56.6)

최악 5문장(문장 안 최대 오차):
- 검사 1: 호르무즈 route_1 78.4 · debate_2 76.1 · fed markets_2 69.5 · 호르무즈 war_1 66.9 · now_2 60.6
- 검사 2: 호르무즈 past_2 162.8 · fed decision_5 138.3 · prices_jobs_8 132.6 · 호르무즈 timeline_3 130.4 · fed markets_2 127.7
- 검사 3: route_1 56.6 · war_1 49.5 · route_0 42.7 · route_2 39.5 · ask_4 38.2

모집단 차이(기록): D-0165 는 fed 45문장이라 적었으나 fed `plan.json` 은 48문장이라 48을 다 넣었습니다. 간격 일치 n 은 Fable 시제품 계산 477 과 다른 519 입니다.
"쉼 뒤" 판정을 시제품의 보정 여부가 아니라 규칙(edge 시각이 0.15초 넘는 무음 안)으로 다시 했기 때문입니다.

## 5. 참고 — edge 대조(게이트 아님)

MMS ↔ edge 원값: |차| 중앙값 109.5ms · p90 266.6ms, 851어절 중 MMS − edge 음수 0개. 문장 안 부호 치우침 +102ms(R-0195).
edge `WordBoundary` 는 절대 시각이 아닙니다(TTS-AP-082). 현 골든 앵커는 edge 정렬이라 실제 발음보다 약 0.1초(쉼 뒤 약 0.3초) 이릅니다.
V2 에서는 고치지 않습니다. V3 에서 플랜이 Supertonic + MMS 로 바뀔 때 `expected_deltas` 사유 "시각(edge 치우침 제거)" 으로 적습니다.

참값 자체의 치우침: 문턱 교차(0.012)는 진짜 발화 시작보다 10~20ms 늦습니다. 기준에는 반영하지 않았습니다(D-0165 §3).

## 6. 측정 방식 메모

- 검사 3 의 Supertonic 합성은 프로젝트 사본에서 `script.plan.build` 를 그대로 돌렸습니다. 골든 원고가 이후 생긴 린트 규칙(`uncertain-phrase`·`flow-sparse`)에
  걸려, 측정 스크립트에서 린트만 건너뛰었습니다(V1 §2 와 같은 방식). 합성·정렬·트림 경로는 제품 코드 그대로입니다. 문장 점수 최저 0.710.
- 이 컨테이너 이미지에는 비표준 `/etc/fonts/conf.d/12-unhinted-grayscale.conf` 가 있습니다(phaseS0 §0.2). pytest 는 표준 `FONTCONFIG_FILE` 로 돌렸습니다.
  처음에 이를 빠뜨려 골든 25컷이 전부 어긋났고, 같은 설정으로 다시 돌려 25/25 일치를 확인했습니다(코드 원인 아님).

## 7. pytest

**1478 passed · 0 failed · 0 skipped**(313 subtests, 30분, 표준 `FONTCONFIG_FILE`). 새 테스트 `tests/test_v2_forced_align.py` 15개.
D151 로 바뀐 기대(옛 비율 폴백 전제) 5파일: `test_timebase_align`·`test_engine_phase2`(정렬 없음 = 오류), `test_direction_schema`(정렬 주입),
`test_g8_animatic`(합성 프로젝트에 글자 균등 `.align.json`), `test_tts_paid_block`·`test_tts_supertonic`(plan 정렬 mock — 가짜 mp3).
`test_direction_convert` 는 음성 없는 합성 plan 용 테스트 대역 `tests/direction_snapshot.SyntheticTimebase` 로 스냅샷 비교를 유지.

