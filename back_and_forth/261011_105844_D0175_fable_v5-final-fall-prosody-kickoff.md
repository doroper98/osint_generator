---
id: D-0175
from: fable
to: opus
kind: directive
responds_to: []
phase: "V5"
version: v5.19.1
status: open
priority: urgent
supersedes: []
---

# V5(v5.20.0) — 문장 끝 억양 보정(사용자 결정 D169: 시안 C) + 호르무즈 재현·재청취

## 0. 사용자 결정(2026-10-11, DECISIONS D169)
- 사용자 청취: "지금 믹스도 목소리 잘 들린다" → **음악 균형 bed_gain 0.43 승인**(P11, D-0169). 지적: "~ㅆ습니다 의 '습니다' 높낮이가 너무 중간톤 — '~니다' 로 가면서 아래로 내리는 형태로".
- Fable 이 WORLD 보코더로 시안 6개(원본·A·B·C·D·E)를 만들어 보냈고 사용자가 **"C 가 딱 좋다"** 고 골랐다.
- **C = 마지막 세 글자("습니다"·"입니다"·"였습니다" 의 끝 3글자) 구간에 걸쳐 끝까지 4반음 선형 하강.** 그 앞은 원음 그대로.

## 1. Fable 시제품(재현 기준 — 이 값·순서 그대로 구현)
측정: 호르무즈 Supertonic 문장 중앙 f0 ≈ 105Hz(p10 86). 대부분 문장은 "니다" 에서 80Hz 근처까지 내려가지만 전체가 낮게 깔려 하강이 작게 들리고, "결론입니다" 처럼 끝이 올라가는 문장(154Hz)도 있다.
```python
# pyworld(MIT) — 시제품 그대로. x = 문장 음성(float64, 44.1k mono), al = 그 mp3 의 .align.json(원본 mp3 기준 시각)
f0, t = pw.harvest(x, SR, f0_floor=60.0, f0_ceil=260.0, frame_period=5.0); f0 = pw.stonemask(x, f0, t, SR)
sp = pw.cheaptrick(x, f0, t, SR); ap = pw.d4c(x, f0, t, SR)
i = chars.rfind("니다"); t_start = char_start[i - 1] - 0.03          # 끝 3글자의 첫 글자(습/입) 시작 - 30ms
voiced = np.flatnonzero(f0 > 0); e = voiced[-1]; s0 = min(searchsorted(t, t_start), e - 4)
for k in range(s0, e + 1):                                           # 반음 0 → -4 선형(프레임 비율 u)
    u = (k - s0) / max(e - s0, 1)
    if f0[k] > 0: f0n[k] = f0[k] * 2 ** (-4.0 * u / 12)
y = pw.synthesize(f0n, sp, ap, SR, 5.0)                               # 길이 = 원본(잘라 맞춤)
# 구간 밖은 원음 그대로, 구간 시작에서 30ms 크로스페이드로 합성음 전환, 피크를 원본 피크에 맞춤
```
결과(5문장): 바뀐 구간만 다시 합성되고 길이·앞부분은 바이트 동일. 끝 음높이는 시작 대비 −4반음.

## 2. 범위(v5.20.0 MINOR — 새 단계)
1. **모듈** `script/tts/prosody.py`: `final_fall(audio: np.ndarray, align: dict, pron_text: str, cfg) -> (np.ndarray, FinalFallRecord)`. 조건: 발음 텍스트가 `suffix`("니다") + 문장부호로 끝날 때만. 아니면 원음 그대로 + 기록 `applied: false, reason`. 시각은 **원본 mp3 기준**(정렬 시각과 같은 축).
2. **위치**: `script/plan.py` 의 `trim_to_npy` 앞 — mp3 디코드 → 정렬(이미 있음) → `final_fall` → 트림 → npy. **mp3(캐시)·`.align.json` 은 손대지 않는다**(정렬 시각은 그대로 유효 — 합성이 프레임 시각을 보존, 테스트로 길이 ±1ms 확인). npy 가 제품 음성이다.
3. **규칙(P3)** `rules tts_rules.prosody.final_fall: {enabled: true, suffix: "니다", span_chars: 3, semitones: 4.0, pre_sec: 0.03, crossfade_sec: 0.03, f0_floor_hz: 60, f0_ceil_hz: 260, frame_ms: 5}` — Pydantic extra=forbid. 값은 사용자 결정 D169(시안 C). 모듈 상수 금지.
4. **provenance**: plan row `prosody.final_fall {applied, region_sec: [t0, t1], semitones, f0_start_hz, f0_end_hz}` → `features_used.prosody {final_fall: {applied_n, skipped_n}}`(P5 — 돌았을 때만).
5. **의존성** `pyworld>=0.3`(MIT) → `requirements-engine.txt`. 없으면 오류(폴백 금지, P6).
6. **결정성**: 같은 입력 2회 = 바이트 동일 npy(테스트).
7. **테스트 ≥ 7**: 구간 선택(끝 3글자, 문장부호 포함) / "니다" 로 안 끝나는 문장 = 바이트 동일 + 기록 / 구간 앞 샘플 바이트 동일 / 끝 f0 ≈ 시작 −4반음(±1, 같은 추적기) / 길이 ±1ms / 결정성 / 규칙 키 코드 상수 없음(anti_inertia) / 게이트 3(Supertonic 음향 발화 시작)은 정렬·트림 시각이 그대로라 영향 0 — 확인 1.
8. **호르무즈 재현**: `script.plan --tts supertonic`(면제 2건 그대로) → npy 45개 보정(적용 n/건너뜀 n 보고) → `audio.mix` → 콘티 판 → 프리뷰 25컷: **영상 프레임은 음성 내용과 무관하므로 phaseV3 기준선 25/25 그대로여야 한다**(바뀌면 결함) → 전편 720p → mux → audio_qa 표(음악−내레이션·LUFS·TP — 보정으로 RMS 가 조금 바뀔 수 있음, 범위 안 확인) → run_log `phaseV5/`.
9. **사용자 청취 자료(Fable 전달)**: 전편(재압축 27MB 급)·콘티 판·**끝 억양 전/후 발췌 0~60초**(내레이션만 전/후 두 파일). 사용자 최종 청취 합격 = V3·V5 동시 합격.
10. 문서: 03 §(TTS) 한 단락 "문장 끝 억양 보정 — 사용자 결정 D169, 값은 규칙", 19 §3 한 줄, CHANGELOG v5.20.0.

## 3. 금지·주의
- 원고·정렬·mp3 캐시 무변경. 골든 PNG 무변경·dark·light 25/25.
- 구간 밖 음성은 바이트 동일(전체 재합성 금지 — 음색 변화 방지).
- 모델 식별자·PR·force push·main push 금지. V4(edge 삭제)는 이 뒤(사용자 최종 청취 합격 뒤).
