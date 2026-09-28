# artifacts/phase8-v3.4.0 — Phase 8 오디오 (v3.4.0)

back_and_forth D-0060 작업 8·10. 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| taiwan_f1_music/out | 음악 크레딧 **있는** taiwan_ai 사본의 AI 연출(선택 v3) 전편. `sound.bgm: music.zabriskie_patriarch`(BGM 레지스트리 id). final.mp4 md5 `4bb65cd18e2046320dd700bc0bd680c5`, 22.64초 854×480@24. audio_qa: 최종 I −16.98 LUFS(단일 패스 loudnorm 이 짧은 영상에서 목표 밖 — R-0071/R-0072) |
| taiwan_f1_nomusic/out | 음악 크레딧 **없는** 사본의 AI 연출(선택 v1) 전편. `sound.bgm: null`(음악 없음 명시 상태 — 내레이션+효과음만). final.mp4 md5 `6c2b682f7e96bcda9aa3260a2f526edb`, 22.64초. audio_qa: I −13.78 LUFS |
| */out/mix.flac | out/mix.f32(44.1kHz 스테레오 f32le) 무손실 |
| */direction.yaml | 선택 판 연출 |
| shared/tts, shared/plan.json | taiwan_ai 와 같은 edge-tts 합성·타임라인 |

- **곡 교체 교차 페이드 실곡 시연판은 없다** — 미사용 CC BY 2곡이 저장소 이력에 없어(registry available: false) 두 곡을 쓸 수 없다. 합성 사인 시연은 작업 브랜치 `docs/handoff/reports/phase8/crossfade_demo.png`.
- **hormuz 는 재렌더하지 않았다** — mix 무변경을 md5 로 증명: `projects/hormuz_korea/out/mix.f32` = `c1314fb98d086dc116d7475562ca2c07` = Phase 7 artifacts `hormuz_camauto/out/mix.flac` 원본.
- provenance 의 모델 이름은 저장소 `config.yaml llm.model` 을 가리키도록 적었다(이 브랜치엔 식별자를 넣지 않음).

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phase8-v3.4.0
mkdir -p /tmp/art8 && git archive FETCH_HEAD shared | tar -x -C /tmp/art8
for P in projects/taiwan_f1_music projects/taiwan_f1_nomusic; do
  mkdir -p $P/tts && cp -r /tmp/art8/shared/tts/. $P/tts/ && cp /tmp/art8/shared/plan.json $P/
done   # assets 는 python tools/fetch_data.py … (taiwan_ai 와 같은 geo) — 작업 브랜치 run_log 참조
```
검수 자료: 작업 브랜치 `docs/handoff/reports/phase8/`(taiwan_f1/, hormuz_audio_qa.json, sentence_rms.json, crossfade_demo.png, bgm_registry.yaml, run_log.md, asset_md5.json).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v3.4.0), Opus 클라우드 컨테이너.
