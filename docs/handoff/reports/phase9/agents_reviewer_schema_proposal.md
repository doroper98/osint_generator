<!--
tier: 3
last_synced_with: v3.5.0
ssot_for: [agents-reviewer-bundle-schema-proposal]
depends_on: [docs/handoff/12_BUNDLE_ADAPTER_AGENTS_REVIEWER.md, schemas/models.py, bundle/, tools/bundle_corpus_stats.py]
last_review: 2026-09-29
-->

# agents_reviewer 번들 스키마 개선 제안 (D7 — 제안만)

이 문서는 **제안서**다. osint_generator 는 agents_reviewer 저장소를 고치지 않는다(DECISIONS D7, back_and_forth README §7.1).
반영 여부와 방식은 사용자가 agents_reviewer 쪽에서 정한다.

근거는 두 가지다.
- 코퍼스 **68건** 실측(`corpus_stats.json` — `json/` 63 + `samples/` 5, agents_reviewer v5~v8 생성).
- 랫클리프 번들 1건 실측(`ratcliffe_stats.json`, v8.5.9, `analysis_20260829_115457_ec53e620b2`)과 그 번들의 영상화 실증(`ratcliffe/`).

수치 재현: `python tools/bundle_corpus_stats.py json samples/<5개 폴더> --out docs/handoff/reports/phase9/corpus_stats.json`.

---

## 0. 먼저 알려 둘 변화 — 번들 수신은 이제 fail-closed

v3.5.0 부터 osint_generator 의 번들 모델은 **모르는 필드를 오류로 거부한다**(`extra="forbid"`, back_and_forth D-0064).
v3.4.0 까지는 모르는 필드를 조용히 버렸다. 그 결과 코퍼스 68건 **전부**에서 마커 종류·호 종류·논쟁 영상 문구가 버려지고 있었다.

**번들 스키마 변경은 `schemas/models.py` 번들 모델 선언과 같이 간다. 필드 추가(additive)도 선언이 필요하다.**
선언 전에 새 필드가 든 번들을 넣으면 import 가 멈추고, 오류가 새 필드 경로를 모두 나열한다. 의도된 동작이다.

이번에 선언한 8경로(코퍼스 실측, 번들 수):

| 경로 | 번들 수 | 쓰임 |
|---|---|---|
| `charts[].display` | 66 | 쓰지 않음(보고서 표시 폭) |
| `contradictions[].video`(label_a/b·line_a/b·narration·narration_tts) | 61 | versus 재료, 논쟁 후보 양측 라벨 |
| `map.markers[].kind` · `.value` · `.label_side` | 30 · 32 · 31 | 장소 종류·값 표기(재료) |
| `map.arcs[].kind` · `.weight` · `.label_t` | 30 · 30 · 28 | 이동 경로(flow) vs 긴장선(tension) |

---

## 1. 제안 표 (12 §6 + 실측)

각 행의 "못 한 것"은 이번 어댑터(`bundle/`)가 그 필드가 없어서 실제로 하지 못했거나 추측 대신 비워 둔 것이다.

| # | 필드 | 위치 | 코퍼스 68건 실측 | 어댑터가 못 한 것 | 제안 |
|---|---|---|---|---|---|
| 1 | `date` | 문장 단위 | 문장 날짜 필드 **0건**. 초안 문장 1,736개 중 timeline 날짜와 "M월 D일" 로 대응된 것 **48개(2.8%)** | 나머지 97% 문장의 날짜 배지를 번들 발행일로 채우고 `date_source: report` 로 표시만 했다(본문 날짜에 연도를 추측해 붙이지 않음). 우상단 날짜 배지가 사건일이 아니다 | 문장마다 사건일 `YYYY.MM.DD`(모르면 `YYYY.MM`·`YYYY`) |
| 2 | `entity_refs: [id]` | 문장 단위 | 없음. 별칭 폴백으로 언급이 잡힌 문장 **102 / 1,736(5.9%)**. 랫클리프 19 / 52 | 호칭이 바뀌면("CIA 수장", "랫클리프 국장", "라트비아"→리가) 놓친다. 뱃지 등장 시점을 정확히 못 준다 | 문장이 부르는 노드·마커 id 목록 |
| 3 | `map_refs: [marker_id]` | 문장 단위 | 섹션 `map_ref` 가 채워진 섹션 **0 / 447**. 지도가 있는 번들 33건, 마커 152개 | 장면 경계의 "공간"을 문장 속 마커 이름 탐지로만 추정했다(12 §5-2) | 문장(또는 섹션)이 보여 줄 마커 id |
| 4 | `sources: [{publisher, date, url, title}]` | 문장·주장 단위 + 최상위 출처 칸 분리 | 출처 768개 중 게시일 읽힘 **70(9%)**, 제목 **56(7%)**. 랫클리프는 url 칸에 "매체, '제목', 날짜 (url)" 인용 문자열(16건)로 들어와 파싱했다. `claims[]` 는 68건 **전부 빈 목록**, 섹션 `claim_refs` 도 전부 비어 있다 | 문장 → 출처 연결이 없어 원고 초안 `sources` 를 비웠다(검증 뒤 ScriptWorker 가 claim id 로 채움). 게시일 없는 출처는 기사 가져오기(fetch)로 채웠고, 그것도 안 되면 `unresolved_sources[]`(랫클리프 5/16: 타임아웃 1·403 3·월까지만 날짜 1) | 출처를 `{publisher, title, published_at(YYYY-MM-DD), url}` 칸으로 나눠 주기. 문장·주장에서 출처 id 참조 |
| 5 | `narration_tts` | 문장 단위, 항상 채움 | 문장 1,736개 중 번들 `narration_tts` 사용 **1,663(95.8%)**, 나머지 73개는 03 §4 규칙 변환(변환 뒤 숫자·기호 잔존 0). 랫클리프는 **24 / 52(46%)**만 채워져 있다(s3·s4·s6·s10·s11·s12 빈 배열) | 규칙 변환은 됐지만 번들 생산자와 소비자가 같은 발음 규칙을 두 번 구현하는 셈이다 | 항상 채우고 숫자·%·~·/·:·→·괄호 금지(03 §4) |
| 6 | `entities` 사전 | 번들 최상위 | stakeholder 노드 **96개 중 엔티티 레지스트리 id 와 맞은 것 4개(4%)**. 국기도 조인도 없어 뱃지를 못 만든 노드 15개. 랫클리프 10개 중 4개(trump·cia·zelensky·putin) | 미등재 인물(랫클리프·나리시킨 등)은 번들 국기로만, 국기 없는 기관(백악관·나토)은 관계 패널에서 뺐다(문자 원 금지, 08 §3.1). 추측으로 엔티티를 만들지 않았다 | `{id: {kind: person\|org\|country, names[], iso2, org_domain, role, wikidata?}}` — id 를 안정 키(가능하면 Wikidata QID)로 |
| 7 | `shot_hint` | 문장·섹션 선택 | 없음 | 연출 힌트 없이 연출가(LLM)가 원고·재료만으로 짰다(강제 아님이 원칙이라 문제는 아님) | `"map:moscow"`, `"panel:gantt"` 같은 힌트(강제 아님) |
| 8 | 세계 좌표 커버리지 | map.markers | 랫클리프 마커가 미국 동부(-76.9)~호르무즈(56.4)까지 133° 폭 | 권역을 넓혀(W 티어 -88~70) 준비했다. 넓은 권역은 지형 해상도가 낮다 | 번들 쪽 제약 없음 — 마커는 그대로 두고, 먼 마커를 쓰는 섹션에 `map_refs` 를 주면 카메라가 나눠 잡을 수 있다(#3) |
| 9 | 금지 문구 | 생성 단계 | 초안 문장 1,736개 중 금지 문구 **5문장**(`만 보면` 3·`승부는` 1·`계약서에` 1) | 어댑터는 다시 쓰지 않고 `rewrite_required` 로 표시만 — ScriptWorker 가 다시 쓴다(15 P8) | agents_reviewer 원고 생성 프롬프트에 `rules/video_rules.yaml banned_phrases` 목록 주입 |

---

## 2. 12 §6 에 없던 추가 제안 (실측에서 나옴)

| # | 필드 | 실측 | 제안 |
|---|---|---|---|
| A | `contradictions[].sides[].source_ids` | 논쟁 84건, 양측 문장에 출처 id **0** | 양측 각각의 근거 출처 id. 지금은 검증 워커에 "후보"로만 넘기고, 소스 본문 인용이 없으면 버린다(판정은 osint_generator 코드) |
| B | `claims[]` 실제 채우기 | 68건 전부 빈 목록 | 주장 문장 + 근거 출처 id + 인용(`quote_or_data`). status·confidence 는 참고로만 받는다 — 영상 라벨은 우리 검증 코드가 정한다(번들은 2차 자료) |
| C | 차트 종류 | 차트 575개 중 영상 패널 렌더러가 있는 종류(stakeholder_map·dot_matrix·gantt·dual_line) **39개(7%)**. line 262·bar 69·candle 36 … | 번들 쪽 요청이 아니라 **osint_generator 쪽 과제**다(패널 종류 추가). 어댑터는 렌더러 없는 차트를 `unsupported[]` 에 사유와 함께 남긴다 |
| D | `dot_matrix` 합계 | 1건이 합 100 이 아님 | 100칸 패널이면 합 100 보장(아니면 단위 명시) |
| E | stakeholder `edges` 같은 열 연결 | stakeholder_map 12건 중 10건이 같은 열끼리 잇는 선을 가짐, 2건은 그런 선만 남아 관계 패널을 만들지 못함(선 0) | 영상 관계 패널은 같은 열 연결을 그리지 않는다(08 §3 규칙 3) — 그 선만 빼고 기록했다. 열 배치를 관계 방향과 맞추면 선이 살아남는다 |

---

## 3. 랫클리프 번들 영상화에서 본 것 (요약)

- 섹션 12 → 어댑터 초안 7장면 → ScriptWorker 최종 원고 9장면 38문장(12막 1:1 아님). 섹션 제목은 화면 문장 0, 챕터명 후보로만.
- 출처 16 → 기사 레코드 11(인용 문자열 + 기사 가져오기), 미해결 5. 검증 판정(코드): corroborated 6 · unverified 7 · disputed 4.
- 번들의 "푸틴이 만나지 않은 것은 계산된 선택" 해석(s4)은 소스 본문에 인용 근거가 없어 원고에 들어가지 않았다.
  12 §5-6 의 "예정된 만남을 푸틴이 취소" 보도와의 뉘앙스 차이는 **사용자 고지 항목**이다(Phase 9 보고서).

---

## 4. 반영 순서 권고 (사용자 판단용)

1. #4·B(출처 칸 분리·claims 채우기) — 검증 흐름이 바로 좋아진다.
2. #1·#5(문장 날짜·발음 텍스트) — 화면 날짜 배지·음성 품질.
3. #6·#2·#3(엔티티 사전·문장 참조) — 뱃지·카메라 자동화.
4. #9(금지 문구 주입) — 재작성 부담 감소.

어느 것을 반영하든 osint_generator 쪽 `schemas/models.py` 번들 모델 선언이 같이 가야 한다(§0).
