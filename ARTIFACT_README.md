# artifacts/phase6.9-v3.1.0 — Phase 6.9 선언형 연출·결정적 검사·AI 연출 (v3.1.0)

back_and_forth D-0047 작업 10 · D-0048 · D-0049 · D-0045 §4. 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| hormuz_v3/out | 사람 연출(골든 변환 direction.yaml + D-0048 뱃지 위치). final.mp4 md5 `fc5dbe0cf64f08ef3004c91b54aacfe0`, 292.441초 854×480@24. mix.flac = out/mix.f32(44.1kHz 스테레오 f32le) 무손실 |
| hormuz_ai/out | AI 연출 — 원고만으로 DirectorWorker 초안(v1) → 검수 루프(실행 2) → 코드가 v2 선택. final.mp4 md5 `a3bd2bacd237ef3051c53989d630e324`. provenance stages ai_direction·visual_qa true, used_version 2 |
| hormuz_ai/direction.v1~v3.yaml, qa_loop.json | 판 보관본과 루프 기록(판정·수정 원문은 작업 브랜치 `docs/handoff/reports/phase6_9/hormuz_ai/run2/`) |
| */prev_provenance.json | preview 단계 provenance(render·mix·mux false) |
| shared/tts, shared/plan.json | 두 프로젝트 공용 edge-tts(ko-KR-InJoonNeural) 합성·타임라인 |
| shared/media_src/commons | **Commons 정본 복구**(19:19·19:59 KST): strikes.webm·niovi.webm(source_hash 레지스트리 일치) + 가공 npy 2(Phase 6.5 바이트 동일) + 사진 원본 3 |
| shared/media_src/dvids | Phase 6.8 대체 원본(DVIDS 1013909·881959) + 가공 npy — D-0044 B 에 따라 함께 보존 |

provenance 의 모델 이름은 저장소 `config.yaml llm.model` 을 가리키도록 적었다(이 브랜치엔 식별자를 넣지 않음).

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phase6.9-v3.1.0
mkdir -p /tmp/art6_9 && git archive FETCH_HEAD shared | tar -x -C /tmp/art6_9
for P in projects/hormuz_korea projects/hormuz_ai; do
  mkdir -p $P/tts && cp -r /tmp/art6_9/shared/tts/. $P/tts/ && cp /tmp/art6_9/shared/plan.json $P/
  python tools/media_fetch.py $P --restore-from /tmp/art6_9/shared/media_src/commons   # Commons 호출 0, md5 대조
done
```
hormuz_ai 의 AI 판 선택을 재현하려면 `hormuz_ai/direction.v2.yaml` 을 `projects/hormuz_ai/direction.yaml` 로(작업 브랜치에 이미 같은 내용).

검수 자료: 작업 브랜치 `docs/handoff/reports/phase6_9/`(run_log, asset_md5.json, hormuz_v3/, hormuz_ai/qa_loop.md·v3_vs_ai.jpg·ai_run1_vs_run2.jpg).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v3.1.0), Opus 클라우드 컨테이너.
