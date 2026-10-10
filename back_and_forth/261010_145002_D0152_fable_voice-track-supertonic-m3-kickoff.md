---
id: D-0152
from: fable
to: opus
kind: directive
responds_to: []
phase: "V0"
version: v5.11.0
status: open
priority: urgent
supersedes: []
---

# 내레이션 음성 트랙(V0~V4) 착수 — Supertonic 3 `M3` ×0.95 를 콘티 판·본편 음성으로, 단어 정렬은 강제 정렬로

사용자 결정(2026-10-10, DECISIONS **D146**): 참고 영상(중앙 음역 137Hz·억양 폭 94~178Hz)에 맞춰 무료 오픈소스 엔진을 비교한 결과
**Supertonic 3 남성 프리셋 M3, 속도 0.95** 를 채택한다. D127(edge-tts 사용)은 이 결정으로 대체된다. ElevenLabs 금지는 그대로.
비교 근거는 Fable 청취 시험(edge InJoon 변형 10종, Supertonic M1~M5·속도 4종, Qwen3-TTS VoiceDesign 4종) — 샘플·측정값은 `docs/handoff/reports/phaseV0/` 에 둔다(아래 V0).

## 0. 교신 규칙
- 브랜치 `claude/bold-mccarthy-ttmagk`(D129 그대로), 기준 커밋 = 현재 main(95a0b91). Phase 마다 `phase_report` + `reports/phaseV{n}/run_log.md`. main 머지는 Fable, V3 pass 뒤.
- 버전: V0·V1 = **v5.11.0**, V2 = v5.12.0, V3 = v5.13.0, V4 = v5.14.0. 결정은 README §6.4(Opus 는 `decision_request`). 사용자 고유 결정(§7)은 Fable 도 결정하지 않는다.
- **`docs/handoff/15` 를 읽지 않고 엔진·오케스트레이터를 고치지 않는다**(C8.0). 이 트랙은 `script/tts`·`audio`·`engine/timebase` 경계에 닿는다.

## 1. 사실(Fable 실측, 이 컨테이너 CPU 4코어·GPU 없음)
| 항목 | 값 |
|---|---|
| 엔진 | Supertonic 3 — ONNX Runtime, CPU 전용, 약 99M 파라미터. 코드 MIT, **가중치 OpenRAIL-M**(상업 사용 가능, Attachment A 사용 제한). 제작사 개발 종료·저장소 보관 상태(2026-08-31) → 모델 파일을 우리가 보관한다 |
| 자산 | HF `Supertone/supertonic-3`(거울 `supertone-oss-archive/supertonic-3`), `onnx/` 6파일 380MB + `voice_styles/M3.json`. sha1: duration_predictor `7506c678…`, text_encoder `bef43a4d…`, vector_estimator `6460a27d…`, vocoder `5e948099…`, tts.json `310fe80f…`, unicode_indexer `c8133b89…`, M3.json `77643339…`, LICENSE `e6ab935a…` |
| 속도 | 문단 5문장(약 22초 음성) 합성 9~15초(total_step 16). 호르무즈 45문장 ≈ 10분 |
| 음역 | M3 중앙 105Hz(p10–90 88~134). 참고 137Hz, 현재 InJoon 157Hz |
| 한계 ① | **단어 시각을 내지 않는다**(duration_predictor 는 문장 총길이만). edge `WordBoundary` 에 해당하는 것이 없다 → V2 강제 정렬 |
| 한계 ② | 잠재 벡터를 난수로 샘플링한다(`sample_noisy_latent`) → 시드를 고정하지 않으면 같은 문장이 매번 다르게 나온다. 캐시 결정성(cache.py "같은 발음 텍스트 = 같은 파일")을 위해 **문장별 시드 고정** 필수 |
| 한계 ③ | 긴 문장은 `chunk_text` 로 잘라 0.3초 무음을 끼운다 — 자막 앵커에 영향. 설정값으로 노출하고 provenance 에 기록 |
| 의존성 | `onnxruntime`(이미 있음), `soundfile`, `librosa`(helper 가 씀 — 리샘플만이면 빼고 scipy 로), 정렬용 `torch`(CPU)·`torchaudio`·`uroman`. requirements-engine.txt 에 명시, CPU 휠 index 주석 |

## 2. 설계 결정(Fable 전결, DECISIONS **D147** — 다시 묻지 않는다)
1. **백엔드 모듈** `script/tts/supertonic.py`: `synth_all(jobs, style, speed, total_step)` — edge 와 같은 계약(텍스트·경로 → mp3 + `.align.json`). 내부는 저장소 안 `script/tts/supertonic_runtime.py`(helper.py 를 옮겨 타입 힌트·Pydantic 설정으로 정리, MIT 고지 유지). ONNX 세션은 프로세스당 1회 로드.
2. **자산 위치** `assets/tts/supertonic/{onnx/*, voice_styles/*, LICENSE}` — **git 미추적**(.gitignore), `python tools/fetch_data.py supertonic` 이 HF 에서 받아 sha1 대조(위 표 값을 `config.yaml tts.supertonic.assets` 에 파일명·sha1 로 등재). 없으면 **오류**(P6, 폴백으로 edge 를 부르지 않는다).
3. **설정 SSOT** `config.yaml tts`: `backend_default: supertonic`, `supertonic: {voice_style: M3, speed: 0.95, total_step: 16, silence_sec: 0.3, max_chunk_len: <helper 기본값>, seed_salt: "v1"}`. `TTSConfig` 에 `SupertonicConfig`(extra=forbid). 모듈 상수 override 금지(P3).
4. **결정성**: 문장 시드 = `sha1(발음 텍스트 + style + speed + total_step + seed_salt)` 의 앞 8바이트 → numpy Generator. 같은 입력 2회 = **바이트 동일 wav**(테스트). mp3 인코딩은 ffmpeg 고정 옵션.
5. **캐시 키** `cache_key(tts, …, backend="supertonic", style, speed, total_step)` → salt `|st|M3|0.95|16`. 옛 edge 키와 절대 겹치지 않는다(조용한 재사용 금지, P6).
6. **정렬 출처** `rules tts_rules.alignment_sources` 에 `mms_forced_alignment` 추가. `align.py` 에 `from_forced_alignment(text, spans)` → 같은 글자 단위 형식. 정렬기 = `torchaudio.pipelines.MMS_FA`(wav2vec2 강제 정렬, 한국어는 uroman 로마자화로 토큰화) — 발음 텍스트(이미 숫자·기호 없음)를 그대로 넣는다. 정렬 실패·신뢰도 미달은 오류(P6).
7. **품질 게이트(V2)**: 정렬기 정확도는 **edge-tts 음성으로 측정**한다 — edge 가 준 `WordBoundary` 를 참값으로, 같은 mp3 를 강제 정렬해 단어 첫 글자 시각 오차 **중앙값 ≤ 60ms · p90 ≤ 120ms**(호르무즈 45문장 + fed 45문장). 미달이면 `decision_request`(후보 B = faster-whisper 단어 시각, 같은 게이트).
8. **골든 기준선**: 목소리가 바뀌면 단어 앵커 시각이 바뀌어 25컷 일부가 달라진다. 골든 PNG 는 수정 금지(D34·D36). V3 에서 바뀐 컷을 `golden/expected_deltas.json` 에 `v3_voice_supertonic_m3`(사유·이전/이후 시각)로 등재하고 `phaseV3/hormuz_baseline.json` 새 기준선. 컷이 바뀌는 이유가 "시각" 이외(레이아웃·요소)면 결함.
9. **옛 경로 삭제(P2)**: edge 백엔드·`--edge-voice`·`edge_word_boundary` 출처는 V3 pass 뒤 **V4 에서 삭제**(보존은 `archive/edge-tts-voice` 브랜치). 그 전까지는 `--tts edge` 로 남겨 V2 측정에 쓴다. ElevenLabs 모듈은 D127 대로 거부 상태 유지(이번 트랙에서 손대지 않음).
10. **믹스**: `audio/mix.py`·`audio/qa.py` 의 라우드니스 목표는 바꾸지 않는다. V3 에서 측정값(LUFS·피크)이 기존 허용 범위 안인지 보고. 벗어나면 `decision_request`.

## 3. Phase 계획
### V0 (v5.11.0 첫 커밋) 자산·설정·기록 — 테스트 ≥ 4
VERSION 5.11.0·헤더·CHANGELOG(v5.10.0 마감). `fetch_data.py supertonic`(sha1 등재·대조·LICENSE 복사), `.gitignore`, `config.yaml`·`TTSConfig`, `requirements-engine.txt`. `reports/phaseV0/`: Fable 샘플 목록·측정표(아래 §5 표를 run_log 에 옮김) + `samples/S_M3_speed0.95.mp3`(참고용, 170KB). DECISIONS D146·D147 은 Fable 이 이 D 커밋에 기록.
테스트: sha1 대조 통과/불일치 오류, 자산 없음 → 오류 메시지에 fetch 명령, `SupertonicConfig` extra 거부, 설정 키 코드 상수 없음(anti_inertia `test_single_config` 범위에 `script/tts`).
### V1 (v5.11.0) 백엔드 — 테스트 ≥ 8
`supertonic.py`·`supertonic_runtime.py`, `plan.py --tts supertonic`(기본), 캐시 키, 시드 결정성, 청크 무음 기록(plan row `chunks`), `voice` 라벨 `"supertonic-3 M3 ×0.95"`. **`.align.json` 은 V1 에서 쓰지 않는다** — at_word 가 정렬 없음을 오류로 내는지 확인(P6; 비율 폴백은 "단어 없음"만, D34). 호르무즈 45문장 전편 합성 + `tests/test_tts_pronounce` 재검증(발음 사전 위반 0).
테스트: 결정성(2회 바이트 동일), 캐시 키 분리, 자산 없음 오류, 청크 분할 경계, mp3 길이 = duration±0.1s, 금지 백엔드 거부 유지.
### V2 (v5.12.0) 강제 정렬 — 테스트 ≥ 8
`script/tts/forced_align.py`(MMS_FA + uroman), `align.from_forced_alignment`, 레지스트리 등재, plan 에서 합성 직후 정렬 → `.align.json`. **게이트 §2-7** 측정표(run_log, 문장별 오차 분포). `at_word` 경로 무수정(형식만 본다).
테스트: 레지스트리 밖 출처 오류, 글자 수 일치, 단조 증가 시각, 정렬 실패 오류(무음 파일), edge 참값 대비 오차 게이트(픽스처 10문장, 네트워크 없이).
### V3 (v5.13.0) 본편 재현·사용자 청취 — 테스트 ≥ 4
호르무즈 `--tts supertonic` → 콘티 판·프리뷰 25컷·전편 720p. 바뀐 컷 등재(§2-8), 믹스 측정(§2-10). **`out/animatic.mp4` 와 전편을 사용자에게**(C8.6 순서 그대로: 자막 지문 불변이므로 게이트 ① 재승인 불필요, 콘티 판은 다시 거친다). 사용자 청취 합격이 V3 합격.
### V4 (v5.14.0) 옛 경로 삭제(P2)
edge 백엔드·`edge_word_boundary`·`--edge-voice`·`tools/edge_word_probe.py` 삭제, `archive/edge-tts-voice` 브랜치, 문서(`docs/handoff/17·18`·TTS-AP) 동기화, `test_no_legacy_imports` 확장.

## 4. 공통 합격 조건
pytest failed 0·skip 0(자산 있는 환경), 기준 1394 + 새 테스트. `engine/` 변경은 V2 `timebase` 형식 호환 범위 밖에서 0. 골든 PNG 무수정. 새 외부 패키지는 §1 표의 것만. 모델 식별자·PR·force push 금지.

## 5. Fable 청취 시험 기록(run_log 로 옮길 것)
| 샘플 | 엔진·설정 | 중앙 f0 | p10–90 |
|---|---|---|---|
| 참고 영상 | 사용자 제공 29.9초 | 137 | 94–178 |
| InJoon 현재 | edge −3%·−2Hz | 157 | 118–198 |
| Hyunsu | edge −3%·−2Hz | 142 | 105–178 |
| Supertonic M1/M2/M3/M4/M5 | ×1.0 | 150/97/105/119/92 | — |
| **Supertonic M3 ×0.95** | **채택** | 105 | 88–134 |
| Qwen3-TTS VoiceDesign Q1~Q4 | 1.7B CPU, 문단당 약 2분 | 152/176/94/171 | 지시에 따라 흔들림 — 불채택(결정성 부족) |

## 6. 착수
V0 커밋 → `ack` R(자산 sha1 대조 결과 포함) → V1. V1 끝에 `phase_report`.
