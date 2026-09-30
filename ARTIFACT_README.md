# artifacts/phaseG10-v4.11.0 — G10 정적 구간·음악 상한·글자 크기 2차 표 (v4.11.0)

back_and_forth D-0118(사용자 위임 D103). 전편은 **480p 두 편만**(D-0103), 오디오 A/B 는 30초 클립.

| 경로 | 내용 |
|---|---|
| fed_policy_2026/out/final_480p.mp4 | 『연준, 다시 금리를 올리다』 480p 전편 — md5 `b818566c6bba830193cbff190dbde0b1`, 307.12초, I −14.07 LUFS · TP −1.65 dBTP · 음악 −10.57 dB |
| hormuz_korea/out/final_480p.mp4 | 『호르무즈와 한국』 480p 전편 — md5 `ec33e813b48e42385fd786d94bb30eb0`, 292.44초, I −14.06 LUFS · TP −1.58 dBTP · 음악 −9.83 dB |
| */out/provenance_480p.json | repo_version 4.11.0, rules_hash 8e11addb…, `pacing.static_windows` [] (creep 없음) |
| */out/final.srt · credits.txt · description.txt · audio_qa.json | 오디오 QA 두 편 hard 0 |
| */ab/ab_*_before_30s.mp4 · ab_*_after_30s.mp4 | **음악 상한 A/B** — hormuz 40–70초, fed 15–45초(내레이션 구간). 영상은 두 벌 같다(v4.11.0 렌더), 음성만 다르다: before = v4.10.0 믹스(norm_ref 0.7, 음악 hormuz −11.55·fed −12.31), after = v4.11.0(norm_ref 0.4, −9.83·−10.57). 두 벌 모두 전편에 같은 2패스 loudnorm·리미터를 거친 뒤 같은 인코딩으로 잘랐다 |
| */ab/audio_qa_v4.10.0_mix.json | before 음성의 전편 오디오 QA(I −14.04/−14.05, TP −1.83/−1.72) |
| */prev_g10/ | 프리뷰(hormuz 골든 25 = 작업 브랜치 `reports/phaseG10/hormuz_baseline.json`, fed auto 22 = `regression_baselines.json`), checks hard 0 |
| scale_before_after.jpg | 자막 21→22·카드 15→16 전/후 12컷 |

A/B 판정이 "과하다"면 원복은 규칙 두 줄(`audio.qa.music_under_narration_db` [-15, -11]·`bed_bass.norm_ref` 0.7).

오디오 스트림 md5(`ffmpeg -map 0:a -c copy -f md5`): fed_policy `ed003edda04045636ab1da0906eb91b1`, hormuz `0874100722f56da62671c77905bf5ddb`.

재현 입력: hormuz = `artifacts/phase7-v3.3.0` shared, fed_policy = `artifacts/phaseG4-v4.4.0` shared(+ phaseG5 README 의 AI 연출 기록). 청와대 휘장은 `python -m tools.commons_fetch emblems projects/hormuz_korea --only cheongwadae`.

```bash
python -m audio.mix projects/fed_policy_2026 && python -m engine.render projects/fed_policy_2026 --jobs 3 && python -m engine.mux projects/fed_policy_2026
python -m audio.mix projects/hormuz_korea && python -m engine.render projects/hormuz_korea --jobs 3 && python -m engine.mux projects/hormuz_korea
# A/B: before = v4.10.0 mix.f32(norm_ref 0.7)·bed_stats 로 바꿔 engine.mux → ffmpeg -ss 40(fed 15) -t 30 -c:v libx264 -crf 20 -c:a aac -b:a 192k
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v4.11.0, 24bd727), Opus 클라우드 컨테이너.
