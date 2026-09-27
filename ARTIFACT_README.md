# artifacts/phase2-v2.1.0 — Phase 2 새 엔진 전편

back_and_forth D-0006 §2·D-0010 §4: 영상 본체는 작업 브랜치·main 에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 파일 | 내용 |
|---|---|
| out/final.mp4 | `python -m engine.mux` 최종본 854×480@24, 292.438초, AAC 192k, loudnorm −14 LUFS |
| out/video_noaudio.mp4 | `python -m engine.render --jobs 4` 무음 영상(4조각 concat) |
| out/mix.flac | `python -m audio.mix` 출력 mix.f32 를 24비트 FLAC 로 무손실 압축(D24) |

Phase 1(artifacts/phase1-v2.0.1)과 final.mp4·video_noaudio.mp4 md5 동일, mix 샘플 동일.
생성: overhaul/v2-map-engine (v2.1.0), Opus 클라우드 컨테이너. 검수 자료: docs/handoff/reports/phase2/.
