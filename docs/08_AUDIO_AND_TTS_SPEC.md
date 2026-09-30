<!--
tier: 2
last_synced_with: v5.2.0
ssot_for: [audio-tts-index]
depends_on: [docs/handoff/03_SCRIPT_NARRATION_TTS.md, docs/handoff/10_AUDIO.md, rules/video_rules.yaml, config.yaml, assets/audio/bgm/registry.yaml, docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md]
last_review: 2026-09-29
-->

# 08 — 오디오·TTS 명세 (v4.0.0 재작성)

원고 → 음성 → 믹스 → 먹싱의 안내도다. 정본은 handoff 03(원고·내레이션·TTS)과 10(오디오)이다.
수치의 정본은 `rules/video_rules.yaml`(`rules:audio`, `rules:tts_rules`)과 `config.yaml`(`config:tts`)이다. 이 문서는 값을 복사하지 않는다.
옛 판(v0.3.3 — 워커별 세그먼트 TTS, `pronunciation_ko.yaml` 초안)은 폐기됐다.

---

## 1. 흐름

```
script.yaml ── script.lint ──▶ script.plan --tts edge|elevenlabs ──▶ plan.json + tts/*.mp3(.align.json)
                                                                    │
direction.yaml(sound:) ─────────────────────────────▶ audio.mix ──▶ out/mix.f32
                                                                    │
out/video_noaudio.mp4 ──────────────────────────────▶ engine.mux ──▶ out/final.mp4 (2패스 loudnorm) · final.srt · description.txt · provenance.json
```

| 단계 | 모듈 | 정본 |
|---|---|---|
| 린트(금지 문구·발음 기호·강조어·출처) | `script/lint.py` | handoff 03 §2·§4 |
| 합성·캐시·트림·정렬 | `script/plan.py`, `script/tts/{edge,elevenlabs,cache,trim,align}.py` | handoff 03 §6~§8 |
| 믹스(베드·덕킹·효과음) | `audio/mix.py` | handoff 10 §2~§5 |
| BGM 레지스트리 | `audio/registry.py`, `assets/audio/bgm/registry.yaml` | handoff 10 §7-1 |
| 오디오 QA(측정 경로 하나) | `audio/qa.py` | handoff 10 §7-5 |
| 먹싱·자막·설명문 | `engine/mux.py` | handoff 03 §9, 10 §5 |

## 2. 원고와 발음

자막 텍스트(`text`)와 발음 텍스트(`tts`)는 **한 문자열로 합치지 않는다**(TTS-AP-066).
발음 텍스트에는 숫자·기호를 넣지 않는다(G4-19, `rules:tts_rules.forbidden_chars_regex`).

| 항목 | 규칙 키 | 근거 |
|---|---|---|
| 한자어 수사 안 띄어쓰기 | `rules:tts_rules.sino_numbers_no_inner_space` | TTS-AP-058 |
| 고유어·한자어 수 단위 | `rules:tts_rules.native_count_units`, `rules:tts_rules.sino_count_units` | TTS-AP-064 |
| 달 이름 읽기 | `rules:tts_rules.month_readings` | TTS-AP-065 |
| 약어 한국어 풀이 | `rules:tts_rules.abbreviation_policy` | handoff 03 §4 |
| 소수점 읽기(D6, 저장소 정책 유지) | `rules:tts_rules.decimal_policy` | TTS-AP-059 |
| 강조어 = 자막의 부분 문자열 | `rules:tts_rules.emphasis_must_be_substring` | handoff 03 §4.1 |
| TTS 위험 표기 경고(URL·경로·버전·시각·화살표…) | `rules:tts_risk.patterns` | TTS-AP 목록 |
| 음차 사전 경로 | `rules:pronounce.dict_path` | 번들 어댑터 |
| AI 상투 문구 금지 | `rules:banned_phrases` | handoff 03 §2, G4-18 |

안티패턴 전체는 [TTS_ANTIPATTERNS](ANTIPATTERNS/TTS_ANTIPATTERNS.md)(append-only)다.

## 3. 음성 백엔드

설정은 `config:tts` 한 곳이다(15 P3). API 키·voice id는 `.env`로만 받는다(C9).

| 백엔드 | 설정 키 | 정렬 출처 |
|---|---|---|
| edge-tts(현재 실측 기준 음성) | `config:tts.edge_voice`, `config:tts.edge_rate`, `config:tts.edge_pitch` | `WordBoundary` 단어 경계 |
| ElevenLabs(목표 기본) | `config:tts.backend_default`, `config:tts.eleven_model_env`, `config:tts.voice_settings` | with-timestamps 글자 정렬 |

- 정렬 출처는 등재된 것만 허용한다(`rules:tts_rules.alignment_sources`, D34). 형식은 `{mp3}.align.json` 하나다.
- 캐시 키에 목소리가 들어간다. 목소리를 바꾸면 새로 합성한다(옛 목소리 재사용 금지, 15 P6).
- 트림한 길이(`trim_offset`)를 정렬 시각에서 뺀다. 단어 앵커(`at_word`)는 트림된 음성 시각으로 계산된다.
- 그래서 **목소리를 바꿔도 `direction.yaml`을 고치지 않는다**(G3-4). 연출은 문장·단어 앵커로만 시각을 가리킨다.

## 4. 믹스

| 항목 | 규칙 키 | 정본 |
|---|---|---|
| 베드 이득(사용자 합격 값) | `rules:audio.bed_gain` | handoff 10 §3.3 |
| 덕킹 깊이·앞뒤 여유·평활 | `rules:audio.duck_depth`, `rules:audio.duck_pre_sec`, `rules:audio.duck_post_sec`, `rules:audio.duck_smooth_sec` | handoff 10 §2 |
| 내레이션·마스터 피크 | `rules:audio.narration_peak`, `rules:audio.master_peak` | handoff 10 §5 |
| 효과음 정책·합성 계수 | `rules:audio.sfx_policy`, `rules:audio.sfx`, `rules:audio.fx_duck` | handoff 10 §4 |
| BGM 반복·곡 교체 교차 페이드 | `rules:audio.loop_xfade_sec`, `rules:audio.crossfade_sec` | handoff 10 §3.2 |
| 시작·끝 페이드, 꼬리 여백 | `rules:audio.fade_in_sec`, `rules:audio.fade_out_sec`, `rules:audio.tail_sec` | handoff 10 §5 |
| 결정성(표본율·시드) | `rules:audio.sample_rate`, `rules:audio.seed` | v3 mix3 |

연출은 `direction.yaml`의 `sound:` 블록으로 곡(`bgm`)·장면별 강도(`intensity`)·추가 효과음(`cues`)을 준다.
원고 장면의 `music_intensity`는 연출가에게 주는 힌트다. 코드가 연출에 몰래 넣지 않는다(15 P8, `tests/test_music_intensity.py`).

## 5. BGM 레지스트리와 권리

음악 권리·표기의 SSOT는 `assets/audio/bgm/registry.yaml`이다. `RIGHTS.md`는 사람용 설명이다.
없는 id, 쓸 수 없는 곡(`available: false`), sha1 불일치는 오류다(P6·P10).
엔딩 카드·설명란의 음악 문구는 이 레지스트리에서 만든다(`rules:credits.music_card_license`, `rules:credits.music_description`).
음악 크레딧이 없는 프로젝트는 `sound.bgm: null`로 명시한다(D57). 절차 합성 음악 이식은 사용자 결정 후보로 남아 있다.

## 6. 먹싱 — 2패스 loudnorm

`engine/mux.py`가 `out/mix.f32`와 무음 영상을 합친다. 목표 음량은 `rules:audio.loudnorm`이다.
1패스로 측정하고 2패스에서 linear 보정한다. linear가 불가능하면 ffmpeg dynamic 모드를 쓰고 그 사실을 provenance에 적는다(D57).

## 7. 오디오 QA (D57)

측정 코드는 `audio/qa.py` 하나다. checks·mux provenance·`tools/audio_report.py`가 모두 이 모듈을 부른다.

| 항목 | 규칙 키 | 등급 |
|---|---|---|
| 최종 통합 음량 = 목표 ± 허용 | `rules:audio.loudnorm`, `rules:audio.qa.i_tol_lu` | hard |
| 트루 피크 ≤ 목표 + AAC 여유 | `rules:audio.loudnorm`, `rules:audio.qa.tp_codec_margin_db` | hard |
| 내레이션 중 음악 레벨(v3 사용자 합격본 기준) | `rules:audio.qa.music_under_narration_db` | hard |
| 믹스 피크 | `rules:audio.master_peak` | hard |
| 문장 RMS 편차(정규화하지 않음, 알리기만) | `rules:audio.qa.sentence_rms_dev_db`, `rules:audio.qa.sentence_rms_window_sec`, `rules:audio.qa.sentence_rms_floor_db` | warning |

음악 레벨 범위는 handoff 13 §Phase 8의 권장 범위가 아니라 v3 합격본 실측을 따른다.
v2 믹스는 "너무 작다"로 거절됐고 v3가 합격했다(handoff 10 §3.3). 음악이 없는 프로젝트는 음악 레벨을 판정하지 않는다.

## 8. 자막 파일과 설명문

SRT는 자막 텍스트(발음 텍스트 아님)로 만든다. 설명문은 프로젝트 `description.yaml` 문안에 챕터 시각·출처·크레딧을 붙인다(handoff 03 §9).
