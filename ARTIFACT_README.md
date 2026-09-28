# artifacts/phase6.8-v3.0.0 — Phase 6.8 오케스트레이터 통합 (v3.0.0)

back_and_forth D-0040 §1-10 · D-0042 · D-0044 B · D-0045. 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| hormuz/out | Command Center e2e(CREATED→DONE) 결과. **final.mp4 md5 `003df086a1d6627cbdcfd3c773ffb0b2` = 엔진 CLI 직접 렌더와 바이트 동일**(같은 컨테이너, 같은 plan·tts). 292.441초 854×480@24. mix.flac = out/mix.f32(44.1kHz 스테레오 f32le) 무손실 |
| hormuz/tts, hormuz/plan.json | 이번 컨테이너 edge-tts 재합성(ko-KR-InJoonNeural) 결과와 타임라인(D-0042 — 다음 컨테이너부터 복원하면 바이트 동일 대조 가능) |
| hormuz/media_src | 영상 원본 2건 = **DVIDS 1차 출처**(strikes.dvids.mp4 1013909, niovi.dvids.mp4 881959, Public domain — Commons egress 차단 대체, 레지스트리 source_variants) + 가공 npy 2 + 사진 원본 3(Commons 정본, source_hash 일치) |
| hormuz/prev_provenance.json | preview 단계 provenance(stages render·mix·mux = false) |

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phase6.8-v3.0.0
P=projects/hormuz_korea; mkdir -p $P/tts /tmp/art6_8
git archive FETCH_HEAD hormuz/tts hormuz/plan.json hormuz/media_src | tar -x -C /tmp/art6_8
cp -r /tmp/art6_8/hormuz/tts/. $P/tts/ && cp /tmp/art6_8/hormuz/plan.json $P/
python tools/media_fetch.py $P --variant dvids --restore-from /tmp/art6_8/hormuz/media_src   # Commons 호출 0, md5 대조
```
Commons 원본이 풀리면 정본(webm)으로 다시 가공해 source_hash 7/7 을 대조하고 이 폴더에 함께 보존한다(D-0045 §4).

검수 자료: 작업 브랜치 `docs/handoff/reports/phase6_8/`(run_log, e2e_hormuz.log, direct_cli.log, gate_*.txt, hormuz_25, dvids_match.md, asset_md5.json).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v3.0.0), Opus 클라우드 컨테이너(재기동 5).
