<!--
tier: 3
last_synced_with: v4.3.0
ssot_for: [phaseG3-reports]
depends_on: [docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md, docs/handoff/reports/phaseG1/hormuz_baseline.json]
last_review: 2026-09-29
-->

# Phase G3 산출물 — 시간축 무대·데이터 레코드·차트 정직성 검사 (v4.3.0)

지침 back_and_forth D-0084. 정본 docs/handoff/20 §2.1·§2.3·§5.1~§5.3·§6·§12 G3.

- **hormuz 25컷 기준선**: `../phaseG1/hormuz_baseline.json`(f8e507a, D-0078 KZ 수정 뒤) 그대로 인용한다. 새로 만들지 않는다.
- **랫클리프 20컷 기준선**: `../phaseG1/ratcliffe_mad.json`(G1 새 자산).
- 이 폴더에 쌓일 것(D-0084 §1-10): `timeline_sheet.jpg`(12컷), `chart_honesty_{demo,hormuz,ratcliffe,synthetic}.json`, `series_records.json`, `hormuz_after.json`, `ratcliffe_mad.json`, `gallery.jpg`, `perf.json`, `run_log.md`, `asset_md5.json`.

## 산출물(작업 10)

| 파일 | 내용 |
|---|---|
| `timeline_sheet.jpg` | fed_timeline_demo 12컷(실제 엔진) — 합격 조건 프리뷰 |
| `demo_{checks,frames,provenance}.json` | 그 12컷의 결정적 검사·컷 정보·provenance(stage timeline·genre proposed·series) |
| `chart_honesty_{demo,hormuz,ratcliffe,synthetic}.json` | 정직성 4항목(프로젝트 = checks.json 발췌, synthetic = 주입 9건) |
| `series_records.json` | 레코드 두 개 요약·md5 |
| `hormuz_after.json`·`ratcliffe_mad.json` | 회귀 25/25·20/20 |
| `gallery.jpg`·`gallery.json`·`gallery/` | 등록 요소 33 |
| `perf.json`·`asset_md5.json`·`run_log.md` | 성능·자산 md5·실행 기록 |

영상 본체(final.mp4)·tts·plan 은 `artifacts/phaseG3-v4.3.0` orphan 브랜치.

