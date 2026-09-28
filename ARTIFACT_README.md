# artifacts/phase7-v3.3.0 — Phase 7 카메라 자동화 보조 (v3.3.0)

back_and_forth D-0056 작업 6·9, D-0057 §1, D-0058. 두 편 모두 사용자 검수 대상이다. 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| hormuz_camauto/out | **2차판(맥락 폭 하한 적용, D-0058)** — v3 사람 연출 사본에서 shots 10개 중 8개의 카메라·전환만 `engine.camera_suggest` 제안값으로 바꾼 전편. 제안 w 는 현재 카메라의 w_guide 분류 하한(`camera.framing.context_w_min`) 위에서 찾았다. final.mp4 md5 `72ecea7e79b603b60610768a1b49a40c`, 292.441초 854×480@24. mix.flac = out/mix.f32(44.1kHz 스테레오 f32le) 무손실 |
| hormuz_camauto_pre_context_w/out/final.mp4 | **1차판(하한 없음)** — 단일 장소 숏이 w_min 2.5까지 좁아진 판(호르무즈 route_0 w 2.5). md5 `9900b25102851d509f919146d755b7b5`. 비교용으로 남긴다(D-0057 §1) |
| hormuz_camauto/direction.yaml·camauto_map.json | 바뀐 숏 목록(before/after·fits·note) — 작업 브랜치 `projects/hormuz_camauto/` 와 같은 내용 |
| hormuz_camauto/camera_suggest.json | 받아들인 제안 파일(원본 hormuz_korea direction 에서 계산). provenance camera: suggested 8 · used 8 · from_current_direction false |
| hormuz_camauto/prev_provenance.json·prev_checks.json | preview(golden 25) 단계 provenance·checks(hard 0 · warning 0) |
| shared/tts, shared/plan.json | edge-tts(ko-KR-InJoonNeural) 합성·타임라인(hormuz_korea 와 같음) |
| shared/media_src | 프로젝트 media/ 전부(Commons 원본·가공 npy·사진) — Phase 6.9 artifacts 의 Commons 정본과 같은 파일 |

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phase7-v3.3.0
mkdir -p /tmp/art7 && git archive FETCH_HEAD shared | tar -x -C /tmp/art7
python tools/camauto_copy.py projects/hormuz_korea projects/hormuz_camauto   # 원본 prev/camera_suggest.json 필요(python -m engine.camera_suggest projects/hormuz_korea)
P=projects/hormuz_camauto; mkdir -p $P/tts $P/media
cp -r /tmp/art7/shared/tts/. $P/tts/ && cp /tmp/art7/shared/plan.json $P/ && cp -r /tmp/art7/shared/media_src/. $P/media/
python -m engine.render $P && python -m audio.mix $P && python -m engine.mux $P
```
검수 자료: 작업 브랜치 `docs/handoff/reports/phase7/`(v3_vs_camauto.jpg, camauto_compare.json, camera_suggest.json, resolution_check.json, run_log.md).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v3.3.0), Opus 클라우드 컨테이너.
