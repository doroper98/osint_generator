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

## P1-1 출처 → 검증 → 원고 → 게이트 ① 자료 (v5.20.0, D-0179)

### 1. 순서와 결과
| 단계 | 명령 | 결과 |
|---|---|---|
| 프로젝트 | `orchestrator.main new-project gulf_pact_2026 --category geopolitics --duration-min 5` + `order.yaml`(D156·D-0163 §4·§5 지침) | 장르 지정학(light 기본값) |
| 출처 | `add-source --kind article --fetch --lang en`(웹 검색으로 원문 URL 확인) | **16건**(파키스탄 3·걸프/중동 4·서방 4·남아시아 3·CSIS 1·ARY 1). 실패·교체: The Week(차단 페이지 → ARY·Dawn 으로 교체), Gulf Business·Arab News(403), Mehr(연결 끊김 → Minute Mirror 로) |
| 확인 | `confirm-source --by "opus(대행 …)"` | 16/16(사용자 주제 결정 D156 대행 — URL·매체·날짜 대조) |
| 검증 | `plan-intake` → `submit-intake` → `verify-sources` ×2 | 2차 채택: claim 46(corroborated 20 · unverified 23 · disputed 3, fact 29 · statement 17). 1차(42건)는 `scratchpad` 보관 |
| 원고 | `build-research` → `build-script` | 11장면 51문장(아래 수정 뒤), 글자 수 추정 459.6초 — 호르무즈 실측 비율(260.66/344.8 = 0.756)로 환산 **약 347초(5분 47초)** |
| 린트 | `lint-script` | 오류 0 · 경고 1(`[flow-overuse]` 연결어 76% > 70%) |
| 미디어 | `media_fetch.py search --log` 7문장 · `media_notes.yaml` 7행 · `article_register.py --write`(15건) | 표 판정 통과 — 사진 0/7(선택은 P1-2), 기사 카드 후보 51문장 |
| 게이트 ① 자료 | `gate-view` → `phaseP1/gulf_pact_gate1.txt` | 상태 `script_approval` — Fable 사실 대조 대기 |

### 2. 원고를 손으로 고친 곳(워커 출력 뒤, 최소 수정)
| 문장 | 수정 | 이유 |
|---|---|---|
| troop_numbers_0(새 문장) | "앞서 5월 로이터는 파키스탄이 병력 8,000명과 전투기 편대, 방공체계를 사우디에 보냈다고 보도했습니다." (clm_0026·0027·0028) | order "배치 규모는 두 수치를 같은 무게로 나란히" — 워커 원고에 5월 8,000명이 빠져 3만~4만만 있었다 |
| troop_numbers_1 | "이에 앞서 10월 2일" → "그리고 10월 2일" | 새 문장 뒤 시간 순서 |
| troop_numbers_4·5 | 출처에서 clm_0019(분쟁 사실) 제거 | 린트 `[disputed-claim]` — 이 두 문장은 정보부 반박(clm_0022·0023)을 말한다 |
| pact_origin_1·2 | "…협정에 서명했습니다" → "…협정을 맺었습니다" | TTS-AP-074(에 + 서 → '에서' 결합) |
| troop_numbers_8 | 뉴욕타임스 → 뉴욕 타임스 | TTS-AP-072 |
| riyadh_airport_8 | "불렀습니다" → "밝혔습니다" | unverified 귀속 표현 |
| troop_numbers_7 | 칸마 프레스 → 카마 프레스 | 매체명 표기(Khaama) |
`script_labels.json` 은 수정 뒤 `compute_labels` 로 다시 계산했습니다.

### 3. Fable 사실 대조 때 볼 것
- **한국 연결 고리 없음**: 검증을 두 번 돌려도 CSIS(src_art_0010, 원유 수입 70% 호르무즈 경유·2026-04 기준) 에서 claim 이 나오지 않았다(다른 15건과 주제가 달라 검증 LLM 이 건너뜀). 원고에 한국 단락이 없다 — D-0163 §4 "재사용 가능" 수준이라 막지는 않았다.
- **길이**: 약 5분 47초(추정). "5분 내외" 보다 조금 길다.
- 배치 규모: 5월 8,000명(MEE 가 전한 로이터) / 10월 3만~4만 명(Khaama 가 전한 로이터) / 정보부 "추측성 보도" — 세 갈래 모두 원고에 있다. 로이터 원문은 직접 확보하지 못했다(재인용).
- 사상자: 10월 6~7일 공항 공격(타임, 3명), 10월 8일(알자지라 GACA, 3명), 10월 10일(사우디 12명 · GACA 309명 부상) — 날짜별로 따로 귀속돼 있다.
- 2025-09-17 양자 협정 조문 "한쪽에 대한 침략 = 양쪽" 은 ARY 기사 본문에만 있다(공동성명 원문 미확보).

## P1-1 수정 — D-0181 사실 대조 반영 (v5.20.x)

### 1. 검증 결과를 어떻게 이었나(claim id 보존)
- 보강 출처 4건 추가·대행 확인: Al Jazeera 10/6(src_art_0018), 이투데이 5/26 산업부 브리핑(0019), MEE 10/2 수송기 4대(0020), The Daily Star 5/18(0021). Arab News 10/8(조종사 사망)은 403 으로 못 받음 — 10/8 사망은 AJ 10/10 의 GACA 인용(clm_0038)으로 귀속.
- 게이트 ① 을 반려(→ script_draft)하고 검증을 다시 돌렸지만 상태 기계가 script_draft → source_verify 를 허용하지 않아, `orchestrator.source_verify.run_verify` 를 직접 불렀다(D-0181 §2-3 지시 — 상태 가드 우회를 여기 기록).
- **전체 재검증(3차)은 claim 집합이 크게 바뀌고**(10/8 조종사 사망·309명·전쟁범죄·트럼프 등 빠짐, 한국 claim 또 없음) id 도 바뀌어 Fable 이 대조한 원고 출처 표를 깨뜨린다(`verify_runs/run3_full_claims.json` 보관).
- 그래서 **Fable 이 대조한 2차 claims(clm_0001~0046)를 그대로 두고**, 보강 출처 5건(CSIS·이투데이·MEE 10/2·AJ 10/6·Daily Star)만으로 검증을 따로 돌려(`verify_runs/sub_d0181_claims.json`, 코드 판정 동일) 필요한 5건을 **clm_0047~0051 로 덧붙였다**(notes 에 원 id 기록). 검증 LLM 이 많은 출처를 한 번에 받으면 주제 밖 출처(CSIS)를 건너뛰는 문제의 우회.

| 새 id | 내용 | 출처 | 상태 |
|---|---|---|---|
| clm_0047 | 한국 원유 수입의 70% 가 호르무즈 경유 | CSIS 2026-04-02 | unverified(단일) |
| clm_0048·0049 | 중동산 비중 69.1%(2025) → 48.5%(2026년 5~7월) | 이투데이(산업부 브리핑) | unverified(단일) |
| clm_0050 | 미주산 비중 23.1% → 35.6% | 같음 | unverified |
| clm_0051 | 9월 수송기 4대(아덴) | MEE 10/2(로이터) | unverified |

### 2. 원고 수정(D-0181 §2·§3)
| 항목 | 수정 |
|---|---|
| §2-1 공항 사망 | riyadh_airport_0 → clm_0037. _1·_2 병합: "사우디 민간항공청은 이 공격으로 조종사를 포함한 사우디인 최소 3명이 숨졌다고 밝혔습니다."(clm_0038). briefing_2·3 의 clm_0036 → clm_0037(·0038 은 unverified 라 귀속 없는 맺음 문장에서 뺌). clm_0036 은 쓰지 않음 |
| §2-2 메카 | "9월 25일, 사우디는 후티가 메카를 겨냥한 공격을 시도했다고 비난했고, 3국 군 수뇌부도 메카를 겨냥한 공격을 규탄했습니다."(옛 _1·_2 병합) + "후티와 이란은 이를 부인했습니다." AJ 10/6 은 claim 이 나오지 않아 출처로 못 붙임 |
| §2-3 한국 | `korea` 장면 3문장(briefing 앞): CSIS 70%(2026-04) / 산업부 중동산 69.1 → 48.5%(2026년 5~7월) / 미주산 23.1 → 35.6%. 호르무즈 통과 비중과 중동산 비중은 다른 문장 |
| §2-4 길이 | 삭제 6: reactions_0(크림리)·mecca_attack_1(중복)·invocation_5(중복)·riyadh_airport_2(병합)·_4(미디어국장)·yemen_front_3(사나 집회), briefing_0 축약. **48문장 · 추정 5분 28초**(호르무즈 실측 비율 0.756 적용; gate-view 원값 433.7초는 320자/분 추정) |
| §2-4 연결어 | 76% → 30~70% 범위(린트 경고 0). 처음엔 17곳을 빼 23%(`[flow-sparse]` 오류)가 되어 5곳을 되살렸다 |
| §3 권장 | pact_origin_3 "3국 공동성명은 … 밝혔습니다" · roles_2 "로이터에 따르면 … 방어·기술 지원" · troop_numbers_7 MEE 10/2 로 교체 · invocation_4 이중 귀속 정리 · reactions(레자에이) 앞 "반면" → "한편" |
- 린트 **오류 0 · 경고 0**, `script_labels.json` 재계산, 기사 등록 +2(이투데이·MEE 10/2; AJ 10/6·Daily Star 는 claim 이 없어 미등록).
- 미디어 표: 통과 — 사진 0/7(사진 후보 8문장 검색 기록·사유; troop_numbers_7 검색 추가, riyadh_airport_10 → _8 로 사유 이동). 낡은 사유 검사가 문장 id 변경을 잡았다(P1-0 기능 실사용 확인).
- 상태 `script_approval`, `phaseP1/gulf_pact_gate1.txt` 재생성.

### 3. 남은 것(막지 않음)
- 출처 20건은 모두 Opus 대행 확인 — 사용자에게 목록과 함께 알림(D-0181 §4).
- 10/8 조종사 사망은 AJ(GACA 인용) 단일 — Arab News 403.
- 권장 중 MEE 5/18 두 번째 출처(Daily Star)로 8,000명 corroborated 만들기는 claim 이 붙지 않아 못 했다(부분 검증에서 Daily Star 단독 claim 은 disputed 로 나옴 — 원래 clm_0026 unverified 유지).

## P1-1 2차 수정 — D-0182(날짜·기준 시점 2건)
- mecca_attack_1: "9월 16일, 사우디는 후티가 메카를 겨냥한 드론 공격을 시도했다고 비난했고, 25일에는 3국 군 수뇌부도 메카 공격을 규탄했습니다." TIME 9/16(src_art_0022) 추가·대행 확인, 그 출처만 부분 검증(`verify_runs/sub_d0182_claims.json`) → clm_0052(알말키 대변인: 9/15 저녁 드론 발사·격추)·clm_0053(후티 사레아 대변인 부인) 덧붙임. mecca_attack_2(부인) 출처에 clm_0053.
- korea_1: "5월 26일 브리핑에서 중동산 원유 비중이 지난해 69.1%에서 48.5%로 줄었다" — 원문이 48.5% 에 기간을 달지 않음. clm_0048 텍스트에서 "2026년 5~7월" 삭제(notes 에 사유). korea_2: "미주산 … 지난해 23.1%에서 올해 5~7월 35.6%"(기간은 원문 그대로).
- 길이 추정 5분 30초(330.3초), 린트 0·0, 기사 등록 +1(TIME 9/16), 미디어 표 통과(mecca_attack_1 '드론' 트리거 — 검색 기록 + 사유).
- 권장(riyadh_airport_1 두 번째 출처 The Week·CNBC 10/9)은 하지 않았다 — 단일 출처(AJ·GACA 인용) 그대로, 사용자 알림 목록에 유지.

## P1-2·P1-3 — gulf_pact_2026 음성·사진·연출·콘티 판 (v5.20.2~v5.21.1)

| 단계 | 결과 |
|---|---|
| 게이트 ① | 사용자 "대본 오케이"(DECISIONS D180) → `approve --gate script_approval`, script_sha1 023c5a3d… |
| 음성 | `script.plan --tts supertonic` 48문장 · **325.24초** · final_fall 47 적용 · 1 건너뜀(briefing_0 명사 종결 "메카 협정.") · octave_fixed 892 프레임 · MMS 정렬 게이트 통과. 첫 실행은 B 규칙 키 편집과 겹쳐 규칙 검증 오류로 끝났고(PIPELINE-AP-010 같은 클래스) 합성 캐시로 재실행 |
| 사진(A) | 5장 — `gulf_pk_jf17`(U.S. Air Force PD)·`gulf_pk_soldiers`(DVIDS PD)·`gulf_riyadh_skyline`(Commons PD)·`gulf_kkia_aerial`(U.S. Air Force PD)·`hormuz_transit`(공용 재사용). 탈락 사유는 `media_notes.yaml` |
| 사진(B) | 1장 — `gulf_pact_2026_art_0005_press`(Reuters via Al Jazeera, 공항 터미널 너머 연기, 사상자 없음). riyadh_airport_2 A 검색 통과 0(DoD 0·Commons 문서 2 → v5.21.0 mime 제외) |
| 자산 준비 | 국기 PNG 48(flag-icons 23개국)·`record_bundles`·라이브러리 초상 4(trump·khamenei·netanyahu·putin)·`asset_library check` 0·credits.yaml(기사 카드 행 + auto people·music) |
| AI 연출 | 연출가 5회째 통과. 거부 원인: ① person 뱃지 flag·인용문 따옴표 → v5.21.1 필드 표 제약(LLM-AP-018) ② tr 미등재 → entities 8개국 ③ 프로젝트 초상·크레딧 행 없음(환경). 실패한 4회는 모두 재요청 1/1 을 환경 오류에 썼다 |
| 수정 회차 | v1(연출가) → [cascade-overflow] 문구 11곳 구현 세션 축약 → 회차 1(v2)·2(v3), 상한 2 → v3 선택(hard 3) |
| 구현 세션 손질 | v3 뒤 콘티 판 hard 2건: 뱃지 '사우디아라비아'(pact_origin) at_place → lon 45.0·lat 26.5(자막 겹침), 마커 '사우디 내 파키스탄군' 시작 troop_numbers_2 → troop_numbers_6(겹침 카드 밑) |
| audio.mix | 325.7초 · peak 0.833. 연출 `sound.bgm: null`(음악 없음 — 연출가 선택) |
| 콘티 판 | `out/animatic.mp4` 22,725,077 B · md5 e8eab45540ae5204f1da7d55a0bae25b · 7805 프레임 · checks hard 0 · warning 15 · 자리표시 article 9·badge 13·cascade 3·photo 5·quote 3 |
| 남은 hard(전편) | `[map-contrast]` 무스카트 4.06 < 4.5(t=101.71, light) — 콘티 판은 검사 생략. 전편 전에 해결 필요 |
| 린트 | `script.lint` 경고 0 · 라벨 corroborated 23·unverified 19·disputed 6 |

## D-0186 처리 (v5.21.2)
- 지명 국소 대비 보정 — gulf 101.71초 '무스카트' 4.06 → 보정 후 `[map-contrast]` hard 0, provenance `map_contrast_fix.labels = {무스카트: 4.06}`(보정 전 값).
- [article-unused] korea_1·briefing_3 사유 `media_notes.yaml`(같은 키 중복을 손으로 합침 — YAML 은 중복 키를 조용히 덮는다).
- 겹침 카드 왼쪽: 콘티 판 원본 프레임 `gulf_animatic/frame_38s·148s·305s.png`, 전편 렌더 `full_0038.00·0148.00·0305.00.png` — 맨 뒤 카드 x ≈ 22px, 화면 안. 시트의 "[사건: 2026.0" 은 자리표시 글자가 뒤 카드 보이는 폭보다 넓은 것.
- 67·113초 흐림 = 기사 카드 프레스 사진 없음 → 블러 무대 폴백(press_lead 1초).
