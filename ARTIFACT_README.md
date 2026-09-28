# artifacts/phase5-v2.4.0 — Phase 5 뱃지·엔티티·권리

back_and_forth D-0029 §1-9: 영상 본체는 작업 브랜치·main 에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 폴더 | 목소리 | 길이 | 비고 |
|---|---|---|---|
| hormuz/out | edge-tts ko-KR-InJoonNeural (v3 기준, 정렬) | 292.439초 | 엔티티·휘장 레지스트리, 권리 대조 크레딧(D35). 휘장 navcent 만 사용(use), flag_fallback 사용 0 |

`final.mp4`(854×480@24, AAC, −14.2 LUFS / peak −1.4 dBFS), `video_noaudio.mp4`, `mix.flac`(mix.f32 44.1 kHz 스테레오 → 24비트 FLAC, D24),
`final.srt`, `provenance.json`(assets.images_used·emblems·badges, credits card/description_only, at_word aligned 7), `credits.txt`, `description.txt`(폰트 자동 블록).

검수 자료: 작업 브랜치 `docs/handoff/reports/phase5/`(hormuz_25/ 25컷·시트, credits_frame.png, emblems_registry_report.md, emblem_fallback_demo, asset_md5, people_md5, run_log).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다.
생성: overhaul/v2-map-engine (v2.4.0), Opus 클라우드 컨테이너(재기동 4).
