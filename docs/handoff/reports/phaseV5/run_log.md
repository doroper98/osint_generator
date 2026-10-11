<!--
tier: 3
last_synced_with: v5.20.0
ssot_for: [phaseV5-run-log]
depends_on: [docs/handoff/reports/phaseV3/run_log.md, script/tts/prosody.py, script/plan.py, script/tts/trim.py, rules/video_rules.yaml]
last_review: 2026-10-11
-->

# Phase V5 실행 기록 — 문장 끝 억양 보정 (v5.20.0)

지침은 D-0175(사용자 결정 D169 시안 C)입니다. 렌더는 표준 `FONTCONFIG_FILE`(phaseS0 §0.2)로 했습니다.

## 1. 만든 것
| 항목 | 내용 |
|---|---|
| 모듈 | `script/tts/prosody.final_fall(audio, align, pron_text, cfg) → (audio, FinalFallRecord)`. D-0175 §1 시제품 순서 그대로: harvest(60~260Hz, 5ms) + stonemask → cheaptrick·d4c → 끝 3글자 첫 글자 시작 −30ms 부터 마지막 유성 프레임까지 f0 를 0 → −4반음 선형 → synthesize → 구간 시작에서 30ms 크로스페이드, 합성 부분 피크 = 원음 같은 부분 피크 |
| 조건 | 발음 텍스트가 끝 문장부호를 뗀 뒤 "니다" 로 끝날 때만. 아니면 원음 그대로 + `applied: false, reason` |
| 위치 | `script.plan` — 정렬 → **디코드 → final_fall → 트림** → npy. mp3 캐시·`.align.json` 무변경, npy 가 제품 음성. Supertonic 만(edge·elevenlabs 정렬은 절대 시각이 아님, TTS-AP-082 — 기록 없음) |
| 규칙 | `rules tts_rules.prosody.final_fall{enabled, suffix 니다, span_chars 3, semitones 4.0, pre_sec 0.03, crossfade_sec 0.03, f0_floor_hz 60, f0_ceil_hz 260, frame_ms 5}`, `FinalFallRules` extra=forbid. 모듈에 값 상수 없음(테스트) |
| 기록 | plan row `prosody.final_fall{applied, region_sec, semitones, f0_start_hz, f0_end_hz}` → provenance `features_used.prosody.final_fall{applied_n, skipped_n}`(돌았을 때만) |
| 의존성 | `pyworld>=0.3`(MIT) — 없으면 `ProsodyError`(폴백 없음) |
| 청취 도구 | `tools/narration_excerpt.py` — plan 의 npy 를 t0 자리에 놓아 내레이션만 발췌 |

### 첫 실행에서 잡은 결함(코드 반영 전)
처음엔 보정 음성을 그대로 트림해 **총길이가 260.66 → 260.86초로 바뀌었습니다**. 합성 꼬리의 잡음이 무음 문턱(0.012)을 넘어 끝 자르는 자리가 뒤로 밀린 것입니다. 타임라인이 바뀌면 프레임이 바뀝니다. `trim(a, ref=원음)` 으로 **자르는 자리를 원음에서 정하도록** 고쳤고, 그 뒤 45문장 `dur`·`trim_offset`·`t0` 가 보정 전과 모두 같습니다(테스트 `test_trim_cut_points_follow_original`).

## 2. 호르무즈 재현
| 단계 | 결과 |
|---|---|
| `script.plan --tts supertonic` | 45문장 · 260.66초(보정 전과 같음 — 길이 차 0 ms: 45문장 디코드 길이·트림 길이·`trim_offset`·`t0` 모두 동일) · 면제 2건 그대로 · 2분 37초. **적용 45 / 건너뜀 0**(전부 "~니다") |
| 정렬·게이트 | 게이트는 mp3 를 읽으므로 영향 0. 보정 음성의 음향 발화 시작(게이트 참값 정의)도 45/45 문장이 원음과 같다 |
| `audio.mix` → 콘티 판 | 통과 |
| 프리뷰 25컷 | **phaseV3 기준선 25/25 그대로**. provenance `features_used.prosody = {final_fall: {applied_n 45, skipped_n 0}}` |
| 전편 720p → `engine.mux` | 통과. `out/final.mp4` 260.66초(md5 18b940ca2c5e…, 48.7MB), `out/animatic.mp4`(md5 1431e7b9c3d1…) |

### 오디오 QA(보정 전 → 후)
| 항목 | 전 | 후 | 기준 |
|---|---|---|---|
| 통합 음량 | −14.11 LUFS | −14.11 | −14 ± 1 |
| 트루 피크 | −1.63 dB | −1.66 | ≤ −1.5 + 0.15 |
| 내레이션 RMS | −17.50 dB | −17.50 | — |
| 음악 − 내레이션 | −9.76 dB | −9.75 | 범위 안 |
| 문장 RMS 변화 | — | 최대 0.10 dB(war_2) | — |
네 판정 모두 통과(loudness·true peak·music level·peak).

## 3. 문장별 기록
`final_fall_table.md`(45행: 구간·구간 시작 f0·보정 뒤 끝 f0). 보정은 **원음 대비 상대 −4반음**입니다. 원음 끝이 올라가던 문장(예: "결론입니다")은 보정 뒤에도 끝이 구간 시작보다 높을 수 있어, 끝이 시작보다 낮아진 문장은 33/45 입니다. 몇몇 구간 시작 f0 는 추적기의 옥타브 오차로 보입니다(open_0 213Hz) — 시제품과 같은 추적기·같은 값이라 그대로 둡니다.

## 4. 청취 자료(Fable 전달용)
- `narration_0-60_before.mp3` / `narration_0-60_after.mp3` — 0~60초 내레이션만(음악 없음), 보정 전/후.
- 전편·콘티 판은 이 컨테이너 `projects/hormuz_korea/out/` 에 있습니다(미추적). 위 md5 로 Fable 사본과 대조할 수 있습니다.

## 5. pytest
**1530 passed · 0 failed · 0 skipped**(313 subtests, 34분 38초, 표준 `FONTCONFIG_FILE`). dark·light 골든 e2e 포함 — 두 테마 25/25 무변화. 새 테스트 `test_v5_prosody` 9개.

## v5.20.2 — 끝 구간 옥타브 오류 정리·기록 f0 복구 (D-0180 §3)
- 규칙 `tts_rules.prosody.final_fall.octave_clean{enabled, ratio_hi 1.5, ratio_lo 0.6, gate_db −30, rms_ms 20, record_frames 10}`(D-0180 의 고정값 20 ms·10 프레임도 규칙으로 — 모듈 상수 0). harvest+stonemask 뒤·cheaptrick/d4c 앞에서 구간 유성 프레임만 /2·×2, 기준 = 문장 전체 게이트 프레임 f0 중앙값.
- 기록: `octave_fixed_n` 추가, `f0_start_hz`·`f0_end_hz` = 구간 게이트 프레임 첫/마지막 10개 중앙값(`final_fall_table.md` 재생성).
- 호르무즈: 260.66초 그대로, **프리뷰 phaseV3 25/25**, mix·콘티 판·전편 720p·mux 통과. audio_qa −14.11 LUFS · TP −1.61 · 내레이션 −17.50 · 음악−내레이션 −9.75(네 판정 통과, 문장 RMS 변화 ≤ 0.03 dB).
- 정리된 문장 39/45(프레임 792 — 들리지 않는 꼬리 포함 전체 유성 프레임 기준), 그대로인 6문장은 npy 바이트 동일(C = C-clean). 바뀐 39문장도 첫 차이 샘플이 구간 시작 뒤 — 구간 밖 바이트 동일.
- 청취 자료 `c_vs_c_clean_6.mp3`(war_3·ask_0·ask_2·timeline_1·open_0·route_2 — 문장마다 C → C-clean, 66초).
- **컨테이너 간 오디오 md5 불일치는 정상** — 꼬리 유성 판정이 ±1 LSB 에도 갈리고(D-0180 §2-1), 그 꼬리는 피크 대비 −43 dB 이하라 들리지 않는다. 영상 골든은 영향 없음.
