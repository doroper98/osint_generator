<!--
tier: 3
last_synced_with: v5.11.0
ssot_for: [phaseV1-run-log]
depends_on: [docs/handoff/reports/phaseV0/run_log.md, script/tts/supertonic.py, script/tts/supertonic_runtime.py, script/plan.py, config.yaml]
last_review: 2026-10-10
-->

# Phase V1 실행 기록 — Supertonic 3 백엔드 (v5.11.0)

지침은 D-0152 §3 V1 입니다. 설계 D147 §1·§4·§5 를 따랐습니다. V1 은 목소리를 합성까지만 바꿉니다. 단어 정렬은 V2, 영상 재현은 V3 입니다.

## 1. 바뀐 것

| 파일 | 내용 |
|---|---|
| `script/tts/supertonic_runtime.py` | 원 `py/helper.py`(sha1 `b65eeb8d…`) 이식, MIT 고지 유지. 바꾼 점 ① 잠재 벡터 난수 = 주입한 `numpy.random.Generator` ② 값은 인자로만 ③ 조각 목록 반환 ④ 미사용 함수 삭제 ⑤ 조각마다 예측 길이로 자른 뒤 무음(조각 1개면 원 example 과 같음) |
| `script/tts/supertonic.py` | `synth_all(jobs)`(edge 와 같은 계약), 문장 시드, 캐시 소금, `chunks()`, ONNX 세션 프로세스당 1회(`lru_cache`), 자산 대조 먼저, mp3 = ffmpeg bitexact·메타데이터 없음 |
| `script/tts/cache.py` | `cache_key(…, supertonic_salt)` — 소금 `|st|M3|0.95|16|0.3|120|v1|3cadd1ee` |
| `script/plan.py` | `--tts supertonic|edge|elevenlabs`, 기본 = `config tts.backend_default`. Supertonic 은 정렬 없는 캐시를 재합성하지 않음(재합성해도 정렬이 생기지 않음 — V2 가 씀). 문장마다 `chunks` 기록 |
| `script/schema.py` | `PlanSentence.chunks: Optional[list[str]]`(C3 호환 추가) |
| `config.yaml`·`TTSConfig` | `backend_default: supertonic`(D146) |
| 문서 | `WORKFLOWS.md`(`--tts edge` 지시 제거 → 기본 백엔드), `docs/08`·`docs/10` 백엔드 표·명령 |

판단 기록(되돌릴 수 있는 선택)입니다.
- 캐시 소금에 D-0152 §2-5 의 `|st|M3|0.95|16` 외에 `silence_sec`·`max_chunk_len`·`seed_salt`·revision 앞 8자를 더했습니다. 소리를 바꾸는 값이 바뀌면 키도 바뀌어야 조용한 재사용이 없기 때문입니다(P6).
- 시드는 D147 §4 그대로 sha1(발음 텍스트 · 스타일 · 속도 · 단계 · seed_salt)입니다.

## 2. 결정성·길이

- 같은 문장 2회 합성 → wav 바이트 동일, mp3 바이트 동일(md5 `dfa17720…`, 테스트로 고정).
- 예시 문장 예측 길이 5.016초, mp3 5.068초(인코더 앞뒤 덧붙임, ±0.1초 안).
- ONNX 로드 포함 첫 문장 5.2초, 이후 문장당 약 2.6~3.9초(4코어 CPU).

## 3. 호르무즈 45문장 전편 합성

`plan` 과 같은 순서(발음 사전 → 캐시 키 → 합성 → 트림 → 배치)를 측정 스크립트로 돌렸습니다.
린트는 건너뛰었습니다. 골든 원고가 뒤에 생긴 원고 문법 규칙(`uncertain-phrase`·`flow-sparse`)에 걸리기 때문이며, 음성과 무관합니다.
저장소 `projects/hormuz_korea` 의 edge plan·mp3 는 건드리지 않았습니다(사본에서 실행).

| 항목 | edge(현재 plan) | Supertonic M3 ×0.95 |
|---|---|---|
| 합성 시간 | — | **175.8초**(45문장, D-0152 §1 추정 약 10분보다 짧음) |
| 전체 길이(배치 포함) | 292.4초 | **260.7초** |
| 문장 길이 비(Supertonic ÷ edge) | — | 중앙값 0.873, 최소 0.641, 최대 0.969 |
| 여러 조각으로 나뉜 문장 | — | 0(전부 한 조각, `max_chunk_len` 120) |

**V3 청취에서 볼 점(결함 아님, 기록)**: 나열 문장이 크게 짧아집니다. `ask_1` "다음 날 독일, 영국, 일본, 호주, 그리고 한국이 이 요구를 거절했습니다" 는 7.86초 → 5.03초(0.64), `ask_4` 는 8.09초 → 6.24초입니다. 쉼표에서 쉬는 길이가 edge 보다 훨씬 짧습니다. 단어 앵커(국가 이름마다 거절 표시)가 촘촘해집니다.

발음 사전은 합성 직전에 적용됩니다. edge plan 과 발음 텍스트가 다른 4문장은 edge plan 이후 사전에 추가된 항목 때문입니다. `tests/test_tts_pronounce.py` 는 통과했습니다(사전 위반 0).

## 4. 정렬 없음 처리 확인(D-0152 V1 "at_word 가 정렬 없음을 오류로 내는지")

**오류를 내지 않습니다.** `engine/timebase.at_word` 는 정렬 파일이 없으면 자막 글자 비율로 추정합니다(`mode: ratio`, `note: "정렬 파일 없음"`, provenance `word_anchors` 에 남음).
D34·D-0152 의 원칙은 "비율 폴백은 단어가 발음 텍스트에 없을 때만" 이므로, 이 경로는 원칙과 다릅니다.
V1 은 `engine/` 를 고치지 않는 범위라 그대로 두었습니다. 지금 기본 백엔드가 Supertonic 이므로, V2 정렬이 들어가기 전에 렌더하면 단어 앵커가 전부 비율 추정이 됩니다.
→ V2 에서 정렬 출처 등재와 함께 `at_word` 의 "정렬 파일 없음" 을 오류로 바꿀지 결정이 필요합니다(phase_report 에 올림).

## 5. 테스트

`tests/test_tts_supertonic.py` 9개입니다(요구 ≥ 8).

| 테스트 | 내용 |
|---|---|
| `test_deterministic_wav_and_mp3` | 2회 wav·mp3 바이트 동일, 조각 1개, 정렬 파일 안 씀, mp3 길이 = wav ±0.1초 |
| `test_different_text_different_audio` | 글자가 다르면 소리도 다름 |
| `test_seed_fixed_per_text_and_salt` | 시드 = 텍스트·salt 에 고정 |
| `test_cache_key_separated` | edge 키와 다름, 속도·스타일·단계·salt·무음이 바뀌면 키가 바뀜 |
| `test_chunk_boundaries` | 긴 문장 하나는 안 자름, 합쳐 120 초과면 두 조각 |
| `test_silence_between_chunks` | 조각마다 예측 길이로 자르고 사이에 무음 |
| `test_plan_records_voice_chunks_and_no_alignment` | plan 목소리 라벨·조각·캐시 키, 캐시 재사용(정렬 없어도 재합성 없음), edge 로 넘어가지 않음 |
| `test_missing_assets_fail_without_fallback` | 자산 없음 → 받는 명령 담은 오류, edge 폴백 없음 |
| `test_default_backend_and_elevenlabs_still_refused` | 기본 = supertonic, ElevenLabs 거부 유지 |

바꾼 옛 테스트 1: `test_v560_script_review.NoElevenLabsTest` 의 기본 백엔드 단정 `edge` → `supertonic`(D127 → D146). 테스트 수 변화는 없습니다.

## 6. 전체 pytest

`FONTCONFIG_FILE` 표준 설정, Supertonic 자산 받은 상태(f6258f9):

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| v5.10.0 끝(S4) | 1394 | 0 | 0 | 0 |
| V1 끝 | **1410** | **0** | **0** | 0 |

기준 1394 + V0 7 + V1 9 = 1410 = 실측(24분 37초). `-rs` 출력에 SKIPPED 줄이 없습니다.
