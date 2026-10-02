# artifacts/valdai-2026-v5.3.1 — 발다이 포럼 배포용 720p (사용자 요청 2026-10-02)

| 파일 | 내용 |
|---|---|
| `valdai-2026/out/final_720p.mp4` | 배포용 1280×720. md5 `d805f7d1fcd9703613c1b2009edb85a4`, 340.84초, I −14.0 LUFS · TP −1.7 dBFS · LRA 3.3. 연출 v4 |
| `valdai-2026/out/{provenance,audio_qa}.json, final.srt, credits.txt, description.txt` | 전편 기록. provenance `quote{prototype, 6}`·`border_glow{prototype, on}`·`cascade{adopted, 3}` |
| `valdai-2026/out/animatic.mp4`, `animatic_provenance.json` | 같은 음성 타임라인의 콘티 판(W0 기록) |
| `valdai-2026/prev/` | `--preview auto` checks(hard 0)·frames·provenance·시트 |
| `shared/tts/`, `shared/plan.json` | edge-tts 50문장(발음 수정 TTS-AP-071~073 반영) — 복원용 |

## 복원
```bash
git fetch origin artifacts/valdai-2026-v5.3.1 && mkdir -p /tmp/artV && git archive FETCH_HEAD shared | tar -x -C /tmp/artV
P=projects/valdai-2026; mkdir -p $P/tts && cp /tmp/artV/shared/tts/* $P/tts/ && cp /tmp/artV/shared/plan.json $P/
# 자산: 국기 flag-icons(ru ua pl lt by us cn ee de fi eu lv)·라이브러리 초상(putin trump xi_jinping zelensky)·record_bundles → $P/assets
python -m geo.prep $P && python -m geo.prep $P --res 720p
python -m engine.render $P --res 720p --jobs 4 && python -m audio.mix $P && python -m engine.mux $P
```
생성: claude/brave-rubin-qiha47 (v5.3.1). 인용·국경 글로우는 시안(사용자 판정 대기).
