---
id: R-0076
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "9"
version: v3.5.0
commit: 49b3b80
status: awaiting_decision
---

# Phase 9 결정 요청 4건 — 로더 엄격도·번들 출처 변환·claim 후보·원고 sources

실측 근거: `docs/handoff/reports/phase9/corpus_load.json`(68건), 랫클리프 번들(받음, 264,023 B — `samples/ratcliffe2026/` 는 작업 6 커밋에 넣는다).
막히지 않는 작업(작업 1 엔티티, 작업 3 장면 경계·문장·tts·금지 문구 표시, 작업 4 재료·direction 초안, 작업 7 문서)은 계속한다.

## 쟁점 1 — 로더: 미지 필드를 오류로 할 것인가 (D-0063 §1-8 "로더 fail-closed(미지 필드 오류)")

**실측**: 현 `ReportBundle` 은 모든 번들 모델이 `extra="ignore"`(관대한 수신자, 계약 §1 "additive 는 schema_version 무증분"). 68건 전부 통과. 그러나 **68건 전부**가 모델에 없는 중첩 필드를 갖는다(모든 깊이 실측, 번들 수):

| 경로 | 번들 수 | 어댑터에 필요한가 |
|---|---|---|
| `$.charts[].display` | 66 | 아니오(보고서 표시 폭) |
| `$.contradictions[].video` (label_a/b·line_a/b·narration·narration_tts) | 61 | **예** — versus 패널 양측 문구, 논쟁 문장 |
| `$.map.markers[].kind` · `.value` · `.label_side` | 30 · 32 · 31 | **예** — 마커 종류·값 표기(12 §1) |
| `$.map.arcs[].kind`(flow/tension) · `.weight` · `.label_t` | 30 · 30 · 28 | **예** — 경로(plane) vs 긴장선 구분(12 §2) |

지금 상태로는 어댑터가 `markers.kind`·`arcs.kind`·`contradictions.video` 를 **읽지 못한다**(모델이 버림 = 조용한 드롭).

- **A (권고)**: 8개 경로를 번들 모델에 optional 로 선언하고, 번들 모델 전부 `extra="forbid"` 로 바꾼다. 68건 통과 유지, 앞으로 미지 필드 = 로드 오류(필드 경로를 오류에 적음). 되돌리기: 모델 설정 한 줄.
- **B**: 8개 선언 + `extra="ignore"` 유지. 미지 필드는 모든 깊이 경고·corpus 표에만(지금 구현). D-0063 테스트 "미지 필드 오류"는 "미지 필드 기록" 테스트로 바뀐다.
- 위험: A 는 agents_reviewer 가 필드를 추가하면 import 가 멈춘다(사람이 모델에 선언해야 진행). B 는 새 필드를 놓칠 수 있다(경고만).
- 권고 근거: ② D-0063 §1-8 문면 ③ 15 P6·P10(조용한 드롭 금지, 시끄럽게 실패) — 실측으로 이미 3개 필드가 조용히 버려지고 있었다. ① 설정 한 줄.

## 쟁점 2 — 번들 `sources[]` → `intake/sources.json` 레코드 모양

**실측**(68건 784개 출처): 게시일 필드 **0건**, 제목 3건, 본문 0건. url 은 순수 http 628건, "매체, '제목', YYYY-MM-DD (url)" 인용 문자열 17건(랫클리프 16건이 이 형식, publisher 빈칸), 그 밖 139건.
6.95 계약: `ArticleSource` 는 `published_at`(필수)·`headline_original`(필수)·`key_facts`(≥1). `DocumentSource` 는 `published_at` 선택이지만 판정 코드 `is_official()` 이 **DocumentSource 를 공식 1차 출처로 본다** → 사용자 확인 시 `verified` 가 된다. 번들 출처(2차 자료가 가리킨 기사)를 DocumentSource 로 넣으면 판정이 부풀려진다.

- **A (권고)**: 번들 출처는 **ArticleSource 로만** 만든다. 게시일·제목·매체는 ① 인용 문자열에서 읽고(랫클리프 형식) ② 없으면 `--fetch` 로 기존 `fetch_article`(add-source --url 과 같은 경로, 본문 → `intake/bodies/`)로 채운다. 둘 다 안 되면 sources.json 에 넣지 않고 `intake/bundle_import.json unresolved_sources[]` 에 사유와 함께 남긴다(P6, 조용히 버리지 않음 — 사용자는 add-source 로 직접 넣을 수 있다). 모든 레코드 `note: "번들 이관"`, `confirmed_by` 비움(18 §7 사용자 확인 필수). 차트 provenance 의 데이터 제공자(provider·code) 는 출처 레코드로 만들지 않고 패널 `provenance.sources` 표기에만 쓴다.
- **B**: `ArticleSource.published_at` 을 Optional 로 풀고(+ `pending_source` 사유) 784개 전부 넣는다. 본문이 없어 인용 대조가 거의 불가능 → 대부분 unverified. 6.95 계약(18 §2) 변경.
- **C**: 새 소스 유형 `bundle_ref` 추가. 계약·웹 폼·판정 코드 세 곳 변경.
- 권고 근거: ② 18 §2 계약·D50 판정 코드 무변경, D-0063 "번들은 2차 자료" ③ 실측 — 게시일 0건이라 B 는 빈 레코드가 대부분 ① A 는 어댑터 함수 하나.
- 네트워크: 이 컨테이너는 외부 기사 fetch 가 된다(랫클리프 번들 200). 사이트별 차단은 unresolved 로 기록.

## 쟁점 3 — claims 후보는 어디서 오나

**실측**: 69건(랫클리프 포함) **전부 `claims: []`**. `contradictions[]` 는 65건에 있으나 양측 문장에 **출처 id 가 없다**(`side_a/side_b` 텍스트만). `Claim`·`ClaimSide` 는 `source_ids ≥ 1`, status 는 판정 코드가 인용 대조로만 정한다(D50).
- **A (권고)**: 어댑터는 claims.json 을 직접 쓰지 않는다. 번들 `claims[]`(있으면)·`contradictions[]`(양측 → contested 후보, 라벨 `video.label_a/b`)를 `intake/bundle_claims.json`(후보 목록, 번들 confidence·status 는 참고 필드로만)에 쓰고, 검증 워커 user 프롬프트에 **선택 블록 `{bundle_hints}`** 로 넣는다("후보일 뿐, 인용 근거가 소스 본문에 있어야 한다"). 판정은 기존 `judge()` 그대로 → claims.json. 게이트 ① 진입 조건(claims.json)은 verify_sources 뒤 충족.
- **B**: 힌트 없이 검증 워커가 소스 본문만 보고 후보를 만든다. contradictions 는 원고 초안 주석(논쟁 후보)에만.
- 권고 근거: ② D-0063 작업 2 "contradictions → contested 후보(sides 양측)", 18 §3-5 ③ status 는 코드(P8) ① 프롬프트 블록 하나·파일 하나.

## 쟁점 4 — 원고 초안 `sources` 와 ScriptWorker 다듬기 입력

**실측**: 번들 문장 → 출처 연결이 없다(69건 섹션 `claim_refs` 전부 빈 목록). claim id(`clm_NNNN`)는 verify_sources 판정 뒤에야 생긴다. `Script`·`Scene` 은 `extra="forbid"` — `rewrite_required`·`chapters` 를 필드로 넣으면 스키마를 못 통과한다(P4).
- **A (권고)**:
  1. `script.draft.yaml` = `Script` 그대로(P4 통과). 문장 `sources: []`. `rewrite_required: true — 걸린 패턴` 과 장면 경계 근거는 **YAML 주석**, 기계용 사본은 `script.draft.notes.json`(rewrite_required 목록·chapters·경계 근거·tts 출처·언급 폴백·unmatched·날짜 대체 수).
  2. 문장 `date` 는 번들에 없어(12 §6 개선안 1번) 번들 `generated_at` 날짜로 채우고 notes 에 `date_source: report` 로 표시(추측 날짜 금지 — 본문 "8월 23일" 을 연도 붙여 추정하지 않는다).
  3. ScriptWorker 에 **선택 블록 `{draft}`** 추가: `script.draft.yaml` 이 있으면 문장·장면 구성과 rewrite_required 표시를 넣고 "구성은 유지·수정 가능, 표시 문장은 금지 문구 없이 다시 쓴다, sources 는 claims 에서" 지시. 흐름: import-bundle → 사용자 확인 → verify_sources → build-research(facts) → build-script(초안 + facts) → 게이트 ①. 초안은 이 프로젝트의 입력 재료라 P9(이전 영상·옛 템플릿 금지) 대상이 아니다.
- **B**: 번들 전용 다듬기 워커를 새로 만든다(ScriptWorker 무변경). 워커·프롬프트·파리티 테스트 하나씩 추가.
- 권고 근거: ② D-0063 작업 3 "재작성은 ScriptWorker 몫"·작업 6 "ScriptWorker 로 초안 다듬기 1회" ③ 스키마 무변경(P4) ① 블록 하나.

## 막히는 범위
- 쟁점 1 → 작업 2·4 의 마커 종류·호 종류·versus 문구 사용, 작업 8 로더 테스트.
- 쟁점 2·3 → 작업 2(to_sources), 작업 5(import-bundle), 작업 6 의 verify 이후.
- 쟁점 4 → 작업 3 의 notes 형식·ScriptWorker 블록, 작업 6 의 ScriptWorker 1회.
- 막히지 않음: 작업 1(커밋), 작업 3 장면 경계·tts·금지 문구 표시(notes 형식 없이 함수로), 작업 4 재료 조립(마커 kind 없이), 작업 7 문서 실측.

## §7 해당 여부
없음(D7 은 문서만 — Fable 전결 범위). 랫클리프 번들 해석 차이(12 §5-6)는 작업 6 에서 사용자 고지 항목으로 따로 적는다.
