<!--
tier: 3
last_synced_with: v3.4.0
ssot_for: [phase8-run-log]
depends_on: [audio/mix.py, audio/registry.py, audio/qa.py, engine/credits.py, engine/mux.py, engine/direction.py]
last_review: 2026-09-29
-->

# Phase 8 실행 기록 — 오디오 (v3.4.0)

같은 Opus 클라우드 컨테이너(Phase 7 이어서). 시각은 KST. 지침 D-0060.

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| 0 VERSION·규칙 이관 | `103d032` | mix.f32 md5 `c1314fb9` 이관 전·후 동일, `tests/test_audio_rules.py`, test_no_magic_numbers 에 audio/mix.py·qa.py·registry.py |
| 1·2 BGM 레지스트리·sound.bgm id | `bac7943` | `tests/test_bgm_registry.py` 13, credits.txt·description.txt diff 0(hormuz_camauto 재mux), 25컷 MAD 0, DECISIONS D56 |
| 3 F1 | `fb6828a` | `tests/test_audio_f1.py` 5 — bgm null 믹스 = 무음 베드, {music_list}, 크레딧 불일치 오류 |
| 4 music_intensity | `ffb2ee3` | `tests/test_music_intensity.py` 3 — 코드 주입 0 |
| 5 교차 페이드 | `27c7426` | `tests/test_audio_crossfade.py` 6, `crossfade_demo.png`(합성 사인) |
| 6 오디오 QA | `6836639`·`f9be5ac` | `tests/test_audio_qa.py` 4 — 한 경로, 합성 픽스처 안/밖, 무음악 판정 없음 |
| 7 문장 RMS | `1edf0da` | `sentence_rms.json` — 결정 요청 R-0071 쟁점 2 |
| 8 taiwan F1 | `611b2ab` | `taiwan_f1/{nomusic,music}/` |
| D-0061 임계·2패스 | `8896344` | `tests/test_audio_qa.py` 7, hormuz_audio_qa.json·hormuz_final_provenance.json |

## 2. 명령

```bash
python -m audio.mix projects/hormuz_korea && md5sum projects/hormuz_korea/out/mix.f32     # c1314fb9 (각 작업 뒤)
python -m engine.mux projects/hormuz_camauto                                               # credits.txt·description.txt diff 0
python -m engine.render projects/hormuz_korea --preview golden                             # 25컷 MAD 0
python tools/audio_report.py projects/hormuz_camauto --out docs/handoff/reports/phase8/hormuz_audio_qa.json
python tools/ai_direction_run.py projects/taiwan_f1_nomusic   # 음악 크레딧 없음
python tools/ai_direction_run.py projects/taiwan_f1_music     # 음악 크레딧 있음
python -m engine.render P --jobs 4 && python -m audio.mix P && python -m engine.mux P     # 두 사본 전편
```

## 3. 측정

| 항목 | 값 |
|---|---|
| hormuz mix.f32 | md5 `c1314fb98d086dc116d7475562ca2c07` — Phase 7 artifacts 와 같음(bed_gain 0.47·duck 0.5 무변경) |
| hormuz 25컷 | MAD 0(평균·최대), END 카드 포함 |
| hormuz 오디오 QA(1패스) | I −14.23 LUFS · TP −1.38 dBTP · 음악 −12.67 dB(베드만 −12.82) · mix 피크 0.887 → 13 수치 둘 밖(R-0071) |
| hormuz 오디오 QA(2패스, D-0061) | 1패스 측정 I −14.14·TP −0.80 → 2패스 dynamic(linear 는 TP 초과라 ffmpeg 가 dynamic) → final I −14.03 · TP −1.47 · 음악 −12.67(mix)/−12.55(final 디코드) — hard 0 |
| 문장 RMS(45) | 평균 −16.08 dB · 표준편차 0.65 · 범위 2.83 · 3dB 초과 0 |
| taiwan F1 무음악 | 연출가 첫 시도 bgm null, 권리·스키마 오류 0, provenance audio.bgm null |
| taiwan F1 음악 | bgm 레지스트리 id, 1패스 I −16.98 → 2패스 I −14.89 · TP −1.35(AAC 여유 0.15 안) |
| taiwan F1 무음악(2패스) | linear, I −14.01 · TP −2.27 |
| pytest | 675 passed · skip 0 · xfail 0 (Opus 환경). Phase 7 639 − 삭제 0 → 새 테스트 36 |
