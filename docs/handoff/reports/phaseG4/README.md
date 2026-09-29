<!--
tier: 3
last_synced_with: v4.4.0
ssot_for: [phaseG4-reports]
depends_on: [docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md, docs/handoff/reports/phaseG1/hormuz_baseline.json, docs/handoff/reports/phaseG3/demo_frames.json]
last_review: 2026-09-29
-->

# Phase G4 산출물 — 첫 비지정학 영상 (v4.4.0)

지침 back_and_forth D-0090. 정본 docs/handoff/20 §3·§4·§5.2·§7·§8·§9·§10·§11·§12 G4.

- **hormuz 25컷 기준선**: `../phaseG1/hormuz_baseline.json`(f8e507a) 그대로 인용한다.
- **랫클리프 20컷 기준선**: `../phaseG3/ratcliffe_mad.json`(G3 합격 컷).
- **fed_timeline_demo 12컷 기준선**: `../phaseG3/demo_frames.json`.
- 이 폴더에 쌓일 것(D-0090 §1-9): fed_policy 시트(선택 판 + v1~vn)·`qa_loop`·`rubric_self_check.json`·`dot_plot_sketch.jpg`·`gallery`·`chart_honesty_fed_policy.json`·`hormuz_after.json`·`ratcliffe_mad.json`·`demo_after.json`·`perf.json`·`run_log.md`·`asset_md5.json`.

영상 본체(final.mp4 480p·1080p)·tts·media_src 는 `artifacts/phaseG4-v4.4.0` orphan 브랜치.

## 산출물(작업 9)

| 파일 | 내용 |
|---|---|
| `fed_policy/sheet_final.jpg`·`checks_final.json`·`provenance_{480p,1080p}.json` | 선택 판(direction v7) 프리뷰·검사·provenance(genre·order 결정 상태·elements pending) |
| `fed_policy/run1`·`run2`·`run3` | AI 연출 루프 기록(run1 폐기, run2 = 게이트 ② 1차 반려, run3 = D-0093 루프 v4~v7) |
| `fed_policy/sheet_selected.jpg` | 게이트 ② 1차 판정에 낸 시트(run2 v3) |
| `rubric_self_check.json` | 루브릭 7항목 자기 평가(1차·최종)·D-0091 대조·잔여 |
| `dot_plot_sketch.jpg` | 새 요소 스케치 3컷(사용자 승인 대기) |
| `chart_honesty_fed_policy.json` | 정직성 4항목 hard 0 |
| `prompt_md5.json` | 장르 프롬프트 층 전후 md5(지정학 동일) |
| `lane_label_compare.jpg`·`demo_frames.json`·`demo_label_diff.json`·`demo_after_sheet.jpg` | D-0092 글자 크기 결정·데모 새 기준선 |
| `hormuz_after.json`·`ratcliffe_mad.json`·`demo_after.json` | 회귀 25/25·20/20·12/12 |
| `gallery.jpg`·`gallery.json`·`gallery/` | 등록 요소 34 |
| `gate1_view.txt` | 게이트 ① 화면(대행 승인) |
| `perf.json`·`asset_md5.json`·`run_log.md` | 성능·자산 md5·실행 기록 |
