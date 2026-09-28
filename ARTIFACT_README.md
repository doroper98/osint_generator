# artifacts/phase10-v3.6.0 — Phase 10 해상도·성능 (v3.6.0)

back_and_forth D-0066 작업 7. 사용자 검수 대상이다. 영상 본체는 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| hormuz_1080/out/final.mp4 | 『호르무즈와 한국』 **1080p**. md5 `e194d84a04aff5b1c601b819ea8f202b`, 292.44초 1920×1080@24, AAC. 설계 좌표 854×480 을 렌더 진입에서 k=2.25 로 한 번 확대(D-0067), 지형 티어 ppd×2.25 |
| hormuz_1080/out/render.json | 출력 프로파일(1080p, k 2.25, pad_x −0.75)·jobs 4·328.1초·청크 피크 446MB |
| hormuz_1080/out/mix.flac | mix.f32 무손실 — md5(f32) `c1314fb9…` = Phase 8 과 같다(2패스 loudnorm·mix 무변경) |
| hormuz_1080/out/{provenance,audio_qa}.json · final.srt · credits.txt · description.txt | provenance `render.resolution` 1080p, 오디오 QA hard 0(I −14.03 · TP −1.47) |
| ratcliffe2026/out/final.mp4 | 『모스크바에 내린 수송기 한 대』 480p 재렌더(NB23·label_hidden 반영 AI 연출 재실행 2회차 선택 v2). md5 `75b921923c4d1157f65837519cd06619`, 226.44초 854×480@24 |
| ratcliffe2026/direction.yaml | 선택 판 v2 — 작업 브랜치 `projects/ratcliffe2026/direction.yaml` 과 같다 |
| ratcliffe2026/out/… | provenance(ai_direction 3판 v2 선택, checks hard 0), 오디오 QA hard 0(I −14.01 · TP −1.69), mix.f32 md5 `f3a5c880…`(Phase 9 와 같다) |

480p hormuz 는 재렌더해 배포하지 않는다 — 같은 코드의 480p `video_noaudio.mp4` 가 Phase 6.9·8 artifacts 와 바이트 동일(`692f228e`)함을 확인했다.
검수 자료: 작업 브랜치 `docs/handoff/reports/phase10/`(res_compare·v480_vs_1080.jpg·glyph_size·perf·nb23·ratcliffe_run2·run_log). 모델 식별자는 `config.yaml llm.model` 참조로 바꿨다.

## 복원·재현 (새 컨테이너)
hormuz: `docs/handoff/reports/phase10/run_log.md §0` 준비 뒤
```bash
python -m geo.prep projects/hormuz_korea --res 1080p
python -m engine.render projects/hormuz_korea --res 1080p && python -m audio.mix projects/hormuz_korea && python -m engine.mux projects/hormuz_korea
```
ratcliffe: tts·plan 은 `artifacts/phase9-v3.5.0 shared/`, 자산은 phase9 run_log §0.1. `python -m engine.render projects/ratcliffe2026 && python -m audio.mix … && python -m engine.mux …`.
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v3.6.0), Opus 클라우드 컨테이너.
