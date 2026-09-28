<!--
tier: 3
last_synced_with: v2.5.0
ssot_for: [phase6-run-log]
depends_on: [engine/panels/relation.py, engine/panels/timeline.py, engine/reserved.py, engine/panels/base.py, tools/reserved_proof.py, tools/panel_gallery.py, tools/golden_compare.py]
last_review: 2026-09-28
-->

# Phase 6 실행 기록 — 패널·카드 데이터화 (v2.5.0, Opus 클라우드 컨테이너)

## 0. 컨테이너
Phase 5 컨테이너(재기동 4)를 그대로 썼다. 자산·plan 은 Phase 5 run_log §0 과 같다(재수집 없음).
`python tools/check_env.py` → 21 ok / 0 missing(새 항목 `tls proxy CA in certifi` 포함, NB5).

## 1. 커밋 단위 검증 (25컷 = `golden_compare --reference frames --ref docs/handoff/reports/phase5/hormuz_25/frames`)

| 작업 | 커밋 | 25컷(판정 컷) | 비고 |
|---|---|---|---|
| 1 VERSION·NB5 | 55a9a57 | — | check_env CA 검사 |
| 2 관계 패널 | 8c04cb8 | mean 0.0000 · max 0.0000 | ask_1·ask_2·ask_5(관계 패널) 픽셀 동일 |
| 3 연표 층 | 89fc0c5 | 0 / 0 | 12·13컷 픽셀 동일(데이터 층 우선) |
| 4 RESERVED | a6d012b | 0 / 0 (의도된 차이 3컷) | 15·16컷 = 부산 실제 좌표 + 회피(D36) |
| 5 차트 6종 | abed953 | 0 / 0 | 새 패널은 hormuz 에 없다 — 갤러리로 확인 |
| D-0034 태그 | 9ea0af3 | 0 / 0 | 태그 줄 없는 v3 패널 무변경 |
| 연표 띠 장애물 | f600556 | 0 / 0 | — |

## 2. 증명

| 항목 | 명령 | 결과 |
|---|---|---|
| 관계선 lint | `python -m engine.panels.relation tests/fixtures/relation/edges_8.yaml` | 경고 1 + 분할 제안(4+4, `applied: false`). `edges_7.yaml` → 경고 0 |
| 부산 뱃지 | `python tools/reserved_proof.py --proj projects/hormuz_korea --badge "부산에서 출항" --times 164.594,170.519 --after 181.0 --phase5 docs/handoff/reports/phase5/hormuz_25/frames --out docs/handoff/reports/phase6/reserved` | 겹침 15컷 4464.3→0 px², 16컷 4093.8→0 px². 이동 down 134.3·111.7 px. 181.0초 이동 0 |
| 이동 연속성 | (스크립트, run 기록) 162.1~186.2초 매 프레임 뱃지 y | 최대 프레임 간 이동 15.5 px(178.46초, 카드 퇴장 0.45초 복귀). 168.2초 카드 교대 구간 점프 없음 |
| 갤러리 | `python tools/panel_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phase6/panels` | 6종 PNG + `panels_gallery.jpg`. 태그 줄: dots·dual_line(추정), gantt(`<미검증>` + 추정 · 출처 미기재) |
| 연표 비교 | `panels/timeline_v3.png`(데이터 층) · `panels/timeline_auto.png`(층 삭제 → 자동) | 자동 `[-1, 1, -1, 2, -1, 1, -1, 1]`, 경고 0 |
| 골든 PNG | `golden_compare --reference golden --out .../phase6/vs_golden` | 평균 1.828 · 최대 3.10(의도된 차이 3컷 제외, Phase 4 1.833) |

## 3. 전편

| 단계 | 명령 | 결과 |
|---|---|---|
| 렌더·믹스·먹스 | `python -m engine.render projects/hormuz_korea --jobs 4 && python -m audio.mix … && python -m engine.mux …` | 7018프레임 100초. **292.439초**, −14.2 LUFS / peak −1.4 dBFS, final md5 `94d39281…`, StageResult warnings 0 |
| 사본 | `provenance_hormuz.json` | `reserved.avoidance` 2건(부산 push down 최대 135.2 px 399프레임 / 이재명 hide 2프레임 254.58~254.62초), `panels.used` 5(prov_tag 모두 null — v3 사실 패널), `lint_warnings` [], rules_hash `e38ae8d1…` |
| 자산 | `asset_md5.json` | Phase 5 대비 65/65 동일(재수집 없음) |
| 영상 본체 | orphan `artifacts/phase6-v2.5.0` (`0345bcd`) | hormuz/out: final.mp4·video_noaudio.mp4·mix.flac·final.srt·provenance·credits·description |

엔딩 카드는 Phase 5 와 같다(25컷 END MAD 0) — 크레딧 프레임은 다시 만들지 않았다.

## 알려진 차이
- 15·16컷(부산 뱃지)만 Phase 5·v3 골든과 다르다 — `expected_deltas.json` 등재(D36).
- 이재명 뱃지 2프레임 hide: 결정 장면 끝 카메라 컷 순간에 카드 알파 0.08 이 남아 뱃지 상자와 겹친다. 뱃지도 퇴장 페이드 중이라 육안 영향 없음. provenance 에 그대로 둔다(D-0034 review 에서 확인).
