# artifacts/phase6-v2.5.0 — Phase 6 패널·카드 데이터화

back_and_forth D-0032 §1-7: 영상 본체는 작업 브랜치·main 에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 폴더 | 목소리 | 길이 | 비고 |
|---|---|---|---|
| hormuz/out | edge-tts ko-KR-InJoonNeural (정렬) | 292.439초 | 관계 패널 = relation 데이터(픽셀 동일), 부산 뱃지 실제 좌표 + 카드 RESERVED 회피(D36, 15·16컷만 달라짐) |

`final.mp4`(854×480@24, AAC, −14.2 LUFS / peak −1.4 dBFS), `video_noaudio.mp4`, `mix.flac`(44.1 kHz → 24비트), `final.srt`,
`provenance.json`(reserved.avoidance: 부산 push down 최대 135 px / 이재명 2프레임 hide, panels.used 5, lint_warnings 0), `credits.txt`, `description.txt`.

검수 자료: 작업 브랜치 `docs/handoff/reports/phase6/`(hormuz_25, reserved_before_after.png, reserved/, golden_delta/, panels/ + panels_gallery.jpg, vs_golden, run_log).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v2.5.0), Opus 클라우드 컨테이너.
