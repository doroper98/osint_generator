# artifacts/phase4-v2.3.0 — Phase 4 원고·음성: 목소리 교체 무수정 싱크

back_and_forth D-0021 §1-9·D-0026: 영상 본체는 작업 브랜치·main 에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 폴더 | 목소리 | 길이 | 비고 |
|---|---|---|---|
| sunhi/out | edge-tts ko-KR-SunHiNeural (교체) | 293.925초 | D31 (b) 전편 재합성. direction.py 무수정(sha1 동일) |
| injoon/out | edge-tts ko-KR-InJoonNeural (v3 기준) | 292.439초 | 정렬 재합성 — 국가별 "거절" 전환이 발음 시각으로(D34). Phase 2 와 09_ask_1 컷 부근만 다름 |

각 폴더: `final.mp4`(854×480@24, AAC, loudnorm −14 LUFS), `video_noaudio.mp4`, `mix.flac`(mix.f32 24비트 FLAC, D24),
`final.srt`, `provenance.json`(word_anchor=aligned, at_word aligned 7 / ratio 0, tts.resynthesized 45).

검수 자료: 작업 브랜치 `docs/handoff/reports/phase4/`(voice_swap/ 증명표·시트·거절 전환 스트립, injoon_aligned/·sunhi/ 25컷).
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다.
생성: overhaul/v2-map-engine (v2.3.0), Opus 클라우드 컨테이너.
