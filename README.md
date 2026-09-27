# artifacts/phase1-v2.0.1 — Phase 1 골든 재현 영상 본체

back_and_forth D-0006 §2: 영상 본체는 작업 브랜치·main 에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 파일 | 내용 |
|---|---|
| out/final.mp4 | 최종본 854×480@24, 292.438초, AAC 192k, loudnorm −14 LUFS |
| video_noaudio.mp4 | 무음 영상(render3 4조각 concat) |
| mix.flac | mix3 출력 mix.f32(103MB, GitHub 100MB 제한 초과)를 24비트 FLAC 로 무손실 압축 |

생성: overhaul/v2-map-engine, Opus 클라우드 컨테이너. 검수 자료: docs/handoff/reports/phase1/.
