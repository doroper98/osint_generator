<!--
tier: 3
last_synced_with: v4.3.0
ssot_for: [phaseG3-run-log]
depends_on: [engine/stage_timeline.py, engine/layers/series.py, engine/honesty.py, data/series.py, schemas/data_models.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
-->

# Phase G3 실행 기록 — 시간축 무대·데이터 레코드·차트 정직성 검사 (v4.3.0)

새 Opus 클라우드 컨테이너(재기동 14 뒤). 시각은 KST. 지침 D-0084, 결정 D-0085(세로 척도)·D-0086(CPI 빈 달)·D-0087(정직성 적용 범위)·D-0088(원고 레코드 참조).

## 0. 컨테이너 준비

phaseG2 run_log §0 그대로(하위 에이전트가 수행). 차이만 적는다.

| 단계 | 결과·주의 |
|---|---|
| 의존성·CA·자산 복원·fetch_data·hormuz geo.prep(480p·1080p)·media_fetch 1080p | OK. certifi 에 CA 를 덧붙이기 전 첫 확인이 잘못 "이미 있음"으로 나와 다시 붙였다 |
| ratcliffe 자산 | G2 와 같음. 지오 자산 md5 = G2 `asset_md5.json`(hormuz 21/21·ratcliffe 15/15) |
| FRED | `curl https://fred.stlouisfed.org/graph/fredgraph.csv?id=…` 200. 시리즈 페이지 저작권 칸 두 건 모두 "Public Domain: Citation Requested" |
| fed_timeline_demo 자산 | 지오 자산 없음(시간축만). `tools.commons_fetch.record_bundles` → `assets/rights_registry.json`(글꼴·음성 권리), `script.plan --tts edge` |

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 | e5fec31 | reports/phaseG3 시작 |
| 1 SeriesRecord·로더·fetch_series | cdc44bd | test_series_record |
| 2 시리즈 2개 + missing | fd5791f | `series_records.json`(md5), D-0086 |
| 3 TimelineStage | eba50a8 | test_stage_timeline, hormuz 25/25·랫클리프 20/20(View 분기 뒤) |
| 4 series 이벤트 | 44f2afd | test_series_layer, 갤러리 series 예제 |
| 5 정직성 검사 | 32697e0 | test_chart_honesty(주입 9 + 실제 경로 5), `chart_honesty_*.json` |
| 6 준비·원고 참조·실증 | d6148e1·9329b19·2c0fba8·4088f2f·4b4d9e5·37dbaa0 | test_timeline_project_assets·test_script_series_refs·test_fed_timeline_demo, `timeline_sheet.jpg`, mp4 |
| 8 문서 | c2aa1c7 | test_docs_sync·test_goal_g3 |
| 7·9·10 회귀·산출물 | 이 커밋 | `hormuz_after`·`ratcliffe_mad`·`gallery`·`perf`·`asset_md5` |

## 2. 명령

```bash
python tools/fetch_series.py FEDFUNDS --start 2019-01 --transform raw --unit % --source "FRED(세인트루이스 연은) · 원출처 연준 이사회 H.15" --license us_gov_public_domain --revision-note "월평균 실효금리. 과거 값은 수정될 수 있음"
python tools/fetch_series.py CPIAUCSL --start 2019-01 --transform yoy_pct --unit % --source "FRED(세인트루이스 연은) · 원출처 미 노동통계국(BLS) CPI-U" --license us_gov_public_domain --revision-note "계절조정 지수에서 계산. 잠정치는 이후 수정될 수 있음" --missing-note "2025-10-01=BLS 미발표 — …(BLS URL)"
python -m script.lint projects/fed_timeline_demo && python -m script.plan projects/fed_timeline_demo --tts edge
python -m engine.render projects/fed_timeline_demo --preview 6.4,15.7,22.1,26.4,31.5,34.7,40.0,44.5,47.4,53.5,58.0,71.5   # 12컷 → timeline_sheet.jpg
python -m engine.render projects/fed_timeline_demo --jobs 4 && python -m audio.mix projects/fed_timeline_demo && python -m engine.mux projects/fed_timeline_demo
python -m engine.render projects/hormuz_korea --preview golden        # 25컷 md5 ↔ phaseG1/hormuz_baseline.json
python -m engine.render projects/ratcliffe2026 --preview auto         # 20컷 md5 ↔ phaseG2/ratcliffe_mad.json
python tools/element_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phaseG3/gallery
python tools/chart_honesty_report.py --synthetic --out docs/handoff/reports/phaseG3/chart_honesty_synthetic.json
```

## 3. 측정

| 항목 | 값 |
|---|---|
| hormuz 25컷 | 25/25(phaseG1 기준선), checks 18항목 hard 0, 정직성 해당 없음 메모만(패널 5개 = none·date 축) |
| 랫클리프 20컷 | 20/20(G2 합격 컷), checks 18항목 hard 0(warning 은 G2 와 같은 2건) |
| 갤러리 | 33/33(series 예제는 시간축 무대로) |
| 실증 | 10문장 78초(edge-tts), 12컷 checks hard 0(warning media_beats 1 — 미디어 없음), stage_continuity 0, 원고 수치 대조 오류 0 |
| 실증 mp4 | `out/final.mp4` md5 70984b29, I −14.02 LUFS, 무음악(bgm null) |
| 정직성 합성 | 주입 9건 전부 hard(`chart_honesty_synthetic.json` all_hard true) |
| 성능 | hormuz golden 프리뷰 9.7초, 실증 전편 렌더 11.7초(4조각) — `perf.json` |
| pytest | 956 passed · skip 0 · xfail 0(G2 881 + 새 75, 삭제 0) |

## 4. 운영 기록

- 2c0fba8 을 `pytest … | tail -2 && git commit` 으로 올렸다 — tail 의 종료 코드가 0 이라 실패 2건(test_checks 가짜 프로젝트의 shots 없음)이 푸시됐다. 4088f2f 로 고쳤고, 이후 커밋은 로그에 failed 가 없을 때만 했다.
- 37dbaa0·c2aa1c7 은 커밋 메시지 본문의 줄바꿈이 빠져 Co-Authored-By 가 첫 줄에 붙었다(훅 통과, 내용 무관).
- 실증 연출 1차: 한 문장짜리 장면마다 이동해 숏 머무름 경고 3건 → 이동 5회로 줄이고(핀 확대 뒤 이동을 문장 안으로) 경고 0.
- 실증 연출 2차: 이동 중 핀(2026년 8월 기준)이 화면 밖(hard) → 등장 시각을 이동 뒤로. 2023년 8월 핀이 왼쪽 끝에서 잘려 카메라 중심·폭 조정(2024-11, 1300일).
