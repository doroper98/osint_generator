# artifacts/phaseG14-v5.3.0 — G14 산출물 (back_and_forth D-0139, 사용자 결정 D116·판정 D117)

| 파일 | 내용 |
|---|---|
| `hormuz-talks-2026/out/final_720p.mp4` | hormuz-talks-2026 720p(1280×720) 완성본. md5 `f5342ad4168641b401d51703f91a5b42`, 330.50초, I −14.0 LUFS · TP −1.7 dBFS · LRA 3.0. 연출 = v11 그대로(direction.yaml = direction.v11.yaml) |
| `hormuz-talks-2026/out/{provenance.json,audio_qa.json,final.srt,credits.txt,description.txt}` | 전편 기록. provenance `cascade{status: adopted, events 1, items 7, hidden_labels 15}`, rules_hash `c81a0d1e…` |
| `hormuz-talks-2026/prev/{checks,frames,provenance}.json` | 같은 코드·같은 연출의 `--preview auto` 24컷 검사 — hard 0, warning 20(cascade_label_hidden 15) |
| `hormuz-talks-2026/prev/cascade_sheet.jpg`, `cascade_strip_720.png` | 사용자 합격 시트(R-0162, 9c7fd1c) — 판정 D117 |
| `shared/tts/`, `shared/plan.json` | edge-tts(ko-KR-InJoonNeural) 54문장 330.50초 — 다음 컨테이너 복원용 |

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phaseG14-v5.3.0
mkdir -p /tmp/artG14 && git archive FETCH_HEAD shared | tar -x -C /tmp/artG14
P=projects/hormuz-talks-2026; mkdir -p $P/tts && cp -r /tmp/artG14/shared/tts/. $P/tts/ && cp /tmp/artG14/shared/plan.json $P/
# 자산: projects/hormuz_korea_legacy/assets(tools/fetch_data.py fonts ne tiles flags bgm commons people)의
#   emblems·flags·flags_svg·portraits·rights_registry.json 를 $P/assets/ 로 복사, 카타르 국기(qa)는 flag-icons SVG → PNG
python -m geo.prep $P && python -m geo.prep $P --res 720p
python -m engine.render $P --preview auto
python -m engine.render $P --res 720p --jobs 4 && python -m audio.mix $P && python -m engine.mux $P
```
- hormuz_korea 골든 25/25 기록은 작업 브랜치 `docs/handoff/reports/phaseG14/hormuz_cascade.json`(자산 = artifacts/phase7-v3.3.0 shared).
- VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: claude/brave-rubin-qiha47 (v5.3.0), Opus 클라우드 컨테이너. 사용자 전달은 Fable.
