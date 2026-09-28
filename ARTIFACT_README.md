# artifacts/phase9-v3.5.0 — Phase 9 번들 어댑터 (v3.5.0)

back_and_forth D-0063 작업 6. 사용자 검수 대상이다. 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| ratcliffe2026/out/final.mp4 | 랫클리프 번들(`analysis_20260829_115457_ec53e620b2`, agents_reviewer v8.5.9) 자유 구성 영상. md5 `8145bf2cc74c5a57a6e49543b222d583`, 226.44초 854×480@24, AAC. 무음악(bgm null — 음악 크레딧 없음, F1) |
| ratcliffe2026/out/mix.flac | out/mix.f32(44.1kHz 스테레오 f32le) 무손실 |
| ratcliffe2026/out/{provenance,audio_qa}.json · final.srt · credits.txt · description.txt | provenance `bundle` 단계(draft_used true)·`ai_direction`(선택 v3)·오디오 QA(I −14.01·TP −1.69, 2패스 linear) |
| ratcliffe2026/direction.yaml | AI 연출 선택 판(v3) — 작업 브랜치 `projects/ratcliffe2026/direction.yaml` 과 같다 |
| shared/tts, shared/plan.json | edge-tts(ko-KR-InJoonNeural) 38문장 합성·타임라인 |

흐름: import-bundle → (대행 확인) → verify-sources → build-research → build-script(초안 블록) → AI 연출(재료 블록)·검수 루프 2회 → render·mix·mux.
검수 자료: 작업 브랜치 `docs/handoff/reports/phase9/`(ratcliffe/·rw_demo/·run_log.md). 모델 식별자는 `config.yaml llm.model` 참조로 바꿨다.

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phase9-v3.5.0
mkdir -p /tmp/art9 && git archive FETCH_HEAD shared | tar -x -C /tmp/art9
P=projects/ratcliffe2026; mkdir -p $P/tts && cp -r /tmp/art9/shared/tts/. $P/tts/ && cp /tmp/art9/shared/plan.json $P/
# 자산: docs/handoff/reports/phase9/run_log.md §0 (국기 PNG·라이브러리 초상·rights_registry, geo.prep)
python -m engine.render $P --jobs 4 && python -m audio.mix $P && python -m engine.mux $P
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v3.5.0), Opus 클라우드 컨테이너.
