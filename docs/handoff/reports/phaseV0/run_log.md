<!--
tier: 3
last_synced_with: v5.11.0
ssot_for: [phaseV0-run-log]
depends_on: [back_and_forth/261010_145002_D0152_fable_voice-track-supertonic-m3-kickoff.md, config.yaml, tools/fetch_data.py, script/tts/supertonic_assets.py]
last_review: 2026-10-10
-->

# Phase V0 실행 기록 — 내레이션 음성 자산·설정·기록 (v5.11.0)

지침은 D-0152 입니다. 사용자 결정은 D146(Supertonic 3 남성 프리셋 M3, 속도 0.95, edge-tts 대체, ElevenLabs 금지 유지)이고, 설계는 D147 입니다.
V0 는 목소리를 아직 바꾸지 않습니다. 모델을 받고 대조하는 길과 설정만 놓습니다. 백엔드는 V1 입니다.

## 1. 자산 받기·대조

`python tools/fetch_data.py supertonic` 이 `config.yaml tts.supertonic` 을 읽습니다. 저장소 `Supertone/supertonic-3` 의 고정 revision `3cadd1ee6394adea1bd021217a0e650ede09a323` 에서 없거나 sha1 이 다른 파일만 받습니다(임시 `.part` 파일 → 끝나면 이름 바꿈). 그 뒤 전부 대조합니다.
받는 곳은 `assets/tts/supertonic/` 이고, git 에는 넣지 않습니다(`.gitignore`, 381MB). 파일이 없거나 sha1 이 다르면 받는 명령을 담은 오류를 냅니다. 다른 목소리로 넘어가지 않습니다(15 P6).

이 컨테이너 실측(2026-10-10)입니다. 8개 모두 D-0152 §1 의 Fable 값과 앞자리가 같습니다.

| 파일 | sha1 | D-0152 §1 |
|---|---|---|
| `onnx/duration_predictor.onnx` | `7506c6781997d06c7e0f203e8c16555fe39ad115` | `7506c678…` ✔ |
| `onnx/text_encoder.onnx` | `bef43a4d0bd4889e08aaa2c2e107ecc5aebd6e00` | `bef43a4d…` ✔ |
| `onnx/vector_estimator.onnx` | `6460a27d6787bead8f0cc6973c28be6281930076` | `6460a27d…` ✔ |
| `onnx/vocoder.onnx` | `5e94809905565e9bfbc54a130137c37e03bc2048` | `5e948099…` ✔ |
| `onnx/tts.json` | `310fe80fdba5a36d03a4c0c85561be5c3e1c2da7` | `310fe80f…` ✔ |
| `onnx/unicode_indexer.json` | `c8133b892e49c85f47880f1ac0226f91579ea5ac` | `c8133b89…` ✔ |
| `voice_styles/M3.json` | `7764333982bc4d4d27b3872ead13dfe4b0400d81` | `77643339…` ✔ |
| `LICENSE` | `e6ab935ad6e8025ce4bf68e7382bd5332f4329ea` | `e6ab935a…` ✔ |

받기 경로 확인: `LICENSE` 를 지운 뒤 `--dry-run` 이 그 한 파일만 받을 대상으로 보였고, 다시 받은 sha1 이 같았습니다.

## 2. 설정

`config.yaml tts.supertonic` 이 단일 출처이고, `SupertonicConfig`(extra=forbid, 기본값 없음)로 검증합니다.
- 값: `voice_style: M3`, `speed: 0.95`, `total_step: 16`, `silence_sec: 0.3`, `max_chunk_len: 120`, `seed_salt: "v1"`, 파일 8개의 sha1.
- `max_chunk_len` 120 은 원 `helper.py` 의 한국어 기본값입니다(`max_len = 120 if lang in ("ko", "ja") else 300`).
- `backend_default` 는 아직 `edge` 입니다. Supertonic 백엔드가 생기는 V1 에서 바꿉니다(V0 에서 바꾸면 없는 백엔드를 부름).
- `tests/anti_inertia/test_single_config` 는 저장소 이름·revision 문자열과 `total_step`·`silence_sec`·`max_chunk_len` 숫자의 코드 재정의를 막습니다.

의존성(`requirements-engine.txt`)입니다.
- 합성은 이미 있는 `onnxruntime` 으로 돌고, wav 입출력은 `scipy` 를 씁니다.
- D-0152 §1 의 `soundfile`·`librosa` 는 원 `helper.py` 가 쓰지 않아(리샘플 없음) 넣지 않았습니다.
- V2 정렬용 `torch`·`torchaudio`(CPU 휠 index 주석)·`uroman` 은 미리 적어 두었고, 설치는 V2 에서 합니다.

## 3. Fable 청취 시험 기록(D-0152 §5)

| 샘플 | 엔진·설정 | 중앙 f0(Hz) | p10–90 |
|---|---|---|---|
| 참고 영상 | 사용자 제공 29.9초 | 137 | 94–178 |
| InJoon 현재 | edge −3%·−2Hz | 157 | 118–198 |
| Hyunsu | edge −3%·−2Hz | 142 | 105–178 |
| Supertonic M1/M2/M3/M4/M5 | ×1.0 | 150/97/105/119/92 | — |
| **Supertonic M3 ×0.95** | **채택(D146)** | 105 | 88–134 |
| Qwen3-TTS VoiceDesign Q1~Q4 | 1.7B CPU, 문단당 약 2분 | 152/176/94/171 | 지시에 따라 흔들림 — 불채택(결정성 부족) |

참고 샘플은 `samples/S_M3_speed0.95.mp3` 입니다(Fable 합성, 373,699 B, 23.3초, sha1 `8bf96c17eb5bc883224e88a5e18f0ac9a98ab137`).

## 4. 테스트

`tests/test_tts_supertonic_assets.py` 7개입니다(요구 ≥ 4).

| 테스트 | 내용 |
|---|---|
| `test_user_decision_values` | 설정 = M3 × 0.95, 스타일 파일이 자산 목록에 있음, revision 40자 |
| `test_extra_and_sha1_format_rejected` | 모르는 키·짧은 sha1 거부 |
| `test_match_passes` | 임시 자산 sha1 일치 → 폴더 반환 |
| `test_sha1_mismatch_fails` | 바뀐 파일 → 오류에 파일 이름과 받는 명령 |
| `test_missing_assets_names_fetch_command` | 자산 없음 → 몇 건·어느 파일·받는 명령 |
| `test_no_config_fails` | 설정 없음 → 오류 |
| `test_repo_assets_match_config` | 이 컨테이너 자산 = 설정 sha1(자산 없으면 사유 있는 skip) |

`tests/anti_inertia` 와 TTS·설정 관련 테스트를 함께 돌려 108 passed 였습니다(skip 0).
