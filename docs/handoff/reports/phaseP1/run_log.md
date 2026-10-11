<!--
tier: 3
last_synced_with: v5.19.0
ssot_for: [phaseP1-run-log]
depends_on: [docs/handoff/14_MEDIA_PHOTO_VIDEO.md, script/media_table.py, engine/media_plan.py, tools/media_fetch.py, rules/video_rules.yaml]
last_review: 2026-10-11
-->

# Phase P1 실행 기록 — 『파키스탄군의 사우디 주둔』 영상 트랙

지침은 D-0163(사용자 결정 D156)·D-0173 §3 입니다. 이 문서는 단계마다 절을 더합니다.

## P1-0 기사·사진 노출 수정 (v5.19.0)

### 1. 만든 것
| 항목 | 내용 |
|---|---|
| 밀도 규칙 | `rules media.density` 에 `total_exempt_kinds [article]`·`article_per_min_max 2`·`photo_target_per_min 1`·`grammar` 를 더했다. 연출 프롬프트 두 곳의 "40~60초에 하나" 리터럴을 지우고 `{{RULES.media.density}}` 로 만든다(P3) |
| 키 위치(판단 ③) | D-0163 은 `media_beats.density{beat_gap_sec …}` 로 적었습니다. 같은 값이 이미 `media.density`(D-0037)에 있고 GOAL G3-12 가 그 경로를 가리킵니다. 두 곳에 두면 SSOT 가 깨지고, GOAL 을 고치면 MAJOR 라서 **기존 블록에 더했습니다**. `beat_gap_sec` = 기존 `per_item_sec` |
| 기사 = 비트 밖 | `[media-density-total]` 은 기사 카드를 세지 않는다. V3 의 "7개/261초 과밀" 경고는 비트 5개(52초당 1개)로 사라졌다 |
| 기사 카드 후보 | 확인된 기사 출처를 인용하고 그 기사가 레지스트리에 등록된 문장(`script/media_table.article_candidates`). url 이 없는 옛 항목(v3 이관 D51)은 매체·날짜로 잇는다. 연출 사용자 메시지에 "기사 카드 후보" 절을 더했다 |
| `[article-unused]` | 60초 구간(문장 시작)마다 기대 수 = min(후보 수, 2). 기사 이벤트가 문장 시간과 겹치면 쓴 것. 모자라면 긴 문장 먼저 골라 경고한다. `media_notes.yaml` article 사유가 있으면 경고 없이 provenance `media.articles.unused[].reason` 에 기록. 구간 상한 초과 = `[article-density]`. 둘 다 `media_beats` 검사(warning) 안이라 검사 항목 수는 그대로 |
| 미디어 계획 표 | `gate-view` 게이트 ① 화면에 문장별 표(인용 출처 · 기사 등록/미등록 · 사진 찾음/통과/선택 · 사유). 선택 = 원고 문장 `media` 의 사진 asset_id |
| 게이트 ① 강제 | 사진 선택 수 < 목표(러닝타임 분 × 1, 내림)이면 사진 후보 문장(트리거·검색 기록·원고 query)마다 사유가 있어야 한다. 사유 = `media_notes.yaml` photo, 또는 검색 기록의 권리 통과 0(검색어·결과·탈락 사유가 곧 사유). 통과 후보가 있는데 안 골랐으면 사유 필수. 후보 문장이 하나도 없으면 `project_photo`. 미통과면 `approve --gate script_approval` 거부(`MediaPlanError`, 우회 없음). 승인 기록 `shown.media_plan` |
| 기사 트리거 10개 | 보도했·전했·밝혔·인용·에 따르면·보도에 따르면·기고·사설·단독·확인했(어간, 부분 문자열). "매체 주어" 조건 = 기사 출처를 인용한 문장에서만 센다(`suggest_media(article_sids=…)`) |
| 사진 소싱 풀 | `rules media_beats.sources_order`: ① 미 국방부·DVIDS·CENTCOM(Commons `hastemplate:"PD-USGov-Military"`) ② Commons CC ③ 정부 Flickr CC BY(API 없음 → 안내 줄). `sources_excluded_licenses [NC, ND]`. `tools/media_fetch.py search "검색어" --log projects/{pid} --sid {문장}` 이 풀 순서로 찾고 `media_search.json` 에 남긴다 |
| 통신사 사진(선택지 B) | 사용자 결정 대기 — 손대지 않음(A 유지) |

### 2. 호르무즈 미디어 계획 표 — "0건 사유" 예시(재연출 없음)
전문은 `hormuz_media_table.txt` 입니다. 호르무즈는 다시 게이트 ① 을 지나지 않으므로 사유 파일을 만들지 않았습니다.
| 항목 | 값 |
|---|---|
| 사진 선택/목표 | **0/4**(260.7초 실측). v3 사진 2장은 원고가 아니라 연출에서 골랐다 — 원고 문장 `media` 가 비어 있다 |
| 사진 후보 문장 | 15(발표·공습·파병·초계기·부대·회담·미사일 트리거) |
| 표 오류 | `[photo-reason]` 15건 — 지금 규칙이면 게이트 ① 이 막힌다 |
| 기사 카드 후보 | 43/45 문장(Reuters·Korea Herald 등록). IMO(src_art_0005)·UPI·Foreign Policy 는 미등록 |

검색 기록이 사유가 되는 모습(저장소 밖 사본에서 실제 Commons 검색, `example_media_search.json`):
| 문장 | 검색 | 결과 | 표의 사유 |
|---|---|---|---|
| now_3(청해부대) | "Korean navy Cheonghae unit" | 국방부 PD 0건 · Commons 5건 통과 0(CC BY-SA 2.0) | 자동 — 검색 기록 |
| past_1(자이툰 부대) | "Zaytun division Erbil" | 국방부 PD 0건 · Commons 5건 통과 1(무관한 페슈메르가 추모식) | 없음 → `[photo-reason]` "권리 통과 후보 1건이 있는데 고르지 않았다" — 사람이 사유를 적어야 함 |

### 3. 호르무즈 렌더 경고(골든, 재연출 없음)
- `[media-density-total]` 0건(종전 1건 — 기사 제외).
- `[article-unused]` 5건: route_3·war_3(0~60초), ask_0·timeline_4(60~120초), now_3(240~300초). 기사 카드 2장이 120~240초 후보 4문장을 덮는다.
- 프레임 바이트에는 영향이 없다(경고·provenance 만).

### 4. 관찰(결정 불필요)
- 저장소 라이선스 정책(07 §3.2 `license_allowed`)은 **CC BY-SA 를 받지 않는다**. 한국 해군 Flickr 사진(청해부대)은 CC BY-SA 2.0 이라 통과 0 입니다. P1 소싱에서도 같은 벽이 예상됩니다 — 1순위 풀(미 국방부 PD)이 실제로 중요합니다.
- 정부 Flickr 풀은 검색 API 키가 없어 안내 줄만 냅니다. 찾은 사진은 레지스트리 URL 을 통해 기존 `media.flickr` 라이선스 검사를 탑니다.

### 5. pytest
전체 1차(c63b189): 1516 passed · 3 failed · 0 skipped(313 subtests, 34분 45초). 3 실패 = 같은 원인 — 새 함수 이름 `article_usage` 가 mux 안의 `engine.layers.article.article_usage` 와 겹쳤다. `article_candidate_usage` 로 바꾼 뒤(21825e0) 그 3개(dark 골든 e2e `test_provenance_e2e`, light e2e `test_q3_light_e2e`, `test_g8_animatic`)와 관련 묶음 재실행 **39 passed**. 합계 **1519 passed · 0 failed · 0 skipped**. dark 25/25·light 25/25 기준선 무변화.
