<!--
tier: 3
last_synced_with: v2.1.0
ssot_for: [phase2-run-log]
depends_on: [engine/render.py, script/plan.py, audio/mix.py, engine/mux.py, tools/golden_compare.py]
last_review: 2026-09-27
-->

# Phase 2 실행 기록 — 새 엔진 전편 (v2.1.0, Opus 클라우드 컨테이너)

## 준비

Phase 2 에는 자산 단계(prep3 → `geo/`) 이식이 없다(D-0010 범위 밖). Phase 1 에서 받은 자산을 하드링크로 연결했다.

```bash
L=projects/hormuz_korea_legacy; P=projects/hormuz_korea
cp -al $L/assets $P/assets && cp -al $L/media $P/media && mkdir -p $P/tts && cp -al $L/tts/*.mp3 $P/tts/
```

TTS 캐시 키가 plan3 와 같아(sha1(발음 텍스트)) 음성 재합성 없이 같은 mp3 를 쓴다.

## 명령 (각 CLI 마지막 줄 = StageResult JSON)

| 단계 | 명령 | 결과 |
|---|---|---|
| 원고 | `python -m script.plan projects/hormuz_korea --tts edge` | ok, 45문장, total 292.44s |
| 프리뷰 대조 | `python tools/golden_compare.py --engine new` | 25컷 MAD **0.0000**/255 (평균·최대) → PASS |
| 전편 렌더 | `python -m engine.render projects/hormuz_korea --jobs 4` | ok, 7018프레임 4조각, 98초 |
| 믹스 | `python -m audio.mix projects/hormuz_korea` | ok, 292.9s, peak 0.911 |
| 먹싱 | `python -m engine.mux projects/hormuz_korea` | ok, final.mp4·srt·description·provenance |
| 시트 | `python tools/contact_sheet.py {sheet,pairs} --dir docs/handoff/reports/phase2`, `transitions --engine new` | sheet·sheet_vs_golden·transitions.jpg |

## Phase 1 대비 (parity.json)

| 파일 | 결과 |
|---|---|
| plan.json | 경로 외 전 필드 동일 |
| video_noaudio.mp4 | **md5 동일** (framemd5 도 동일) |
| final.mp4 | **md5 동일** |
| mix.f32 | 25,837,098 샘플 전부 동일 |
| mix.flac | md5 동일 |
| final.srt, description.txt | 바이트 동일 |
| provenance features_used | 동일(badges 8 — D23) |
| loudnorm 측정 | I −14.23 / TP −1.43 / LRA 3.60 (Phase 1 과 같음) |

ffprobe: 292.438s, 854×480, 24fps, h264 + aac.

## 스키마 거부 실측

`direction.py` 끝에 `ev("stamp", 10.0, 12.0, label="TOP SECRET")` 한 줄을 넣은 사본으로 `engine.render --preview 10.5`:

```
{"ok": false, "stage": "preview", ..., "errors": ["이벤트 검증 실패(렌더 시작 전):\n[48] stamp: 이벤트 타입 'stamp': 레지스트리에 없음 — rules/video_rules.yaml registries (15 P10)"]}
exit=1   (prev/ 폴더도 생기지 않음 = 렌더 시작 전)
```

## 알려진 차이

없음. 음악-내레이션 차 12.69dB(목표 14~18 밖)는 Phase 1 과 같은 값이다 — v3 이득 0.47 유지(D-0009 §3-1, Phase 8 전 사용자 질의).
