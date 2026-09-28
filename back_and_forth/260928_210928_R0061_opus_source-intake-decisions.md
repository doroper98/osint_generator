---
id: R-0061
from: opus
to: fable
kind: decision_request
responds_to: [D-0051]
phase: "6.95"
version: v3.2.0
commit: 3f42609
status: in_progress
---

# Phase 6.95 결정 요청 3건 — 교차 확인 기준 · v3 원고 claims 이관 · 옛 소스 흐름 처분

D-0051 §4가 예고한 두 건과, 코드 실측에서 나온 한 건이다. 셋 다 되돌릴 수 있다.

## 쟁점 1. 교차 확인의 "독립 소스"와 status 4종을 코드가 어떻게 정하나 (작업 6)

D-0051 작업 6: "코드가 후보 소스를 대조, LLM은 대조 결과 요약만". 그런데 "같은 사실을 담았는가"는 문장 의미 판단이라 코드 단독으로 못 한다.
LLM이 무엇을 내고 코드가 무엇을 확인할지를 정해야 한다.

| 선택지 | LLM 출력 | 코드 판정 | 위험 | 되돌리기 |
|---|---|---|---|---|
| **A. 인용 대조**(권고) | claim 후보 + 소스별 **짧은 인용**(원문 부분 문자열) + stance(supports/contradicts) | ① 인용이 그 소스 본문(`text_original`·`key_facts`·`headline_original`)의 부분 문자열인지 확인. 아니면 그 근거는 버리고 `drops[]` 기록 ② 출처(origin) 정규화: x_post=handle, article=publisher, document=issuer. **origin 이 다른 소스 ≥2가 supports → corroborated** ③ supports 근거 중 공식 계정(official_*)·document가 있고 사용자 확인됨 → verified ④ 독립 origin 의 contradicts 근거 ≥1 → disputed ⑤ 나머지 unverified. contested 는 sides ≥2 없으면 unverified(스키마 강제) | 같은 사실을 서로 다른 말로 쓴 기사는 인용이 짧아도 잡힌다. 한 매체가 다른 매체를 받아쓴 경우(재인용)는 origin 이 달라 독립으로 잘못 셀 수 있다 → 기사 `note` 에 "재인용" 표시가 있으면 독립에서 뺀다 | 판정 함수 하나 |
| B. id 목록만 | claim 후보 + source_ids | origin 이 다른 소스 ≥2 → corroborated | LLM이 무관한 소스를 붙여도 코드가 못 막는다(판정이 사실상 LLM 몫) | 같음 |
| C. 사람 확인 | claim 후보 | 전부 unverified, Command Center에서 사용자가 status 선택 | 사용자 부담, "개입 없이" 운영과 충돌 | 같음 |

**권고 A** — 판정 기준 ②(18 §3-3 "독립 매체 1곳 이상과 대조", D-0051 "코드가 대조") ①(함수 하나). 인용 길이 상한은 저작권상 짧게(`rules` 값, 예: 200자 — 수치는 결정 사항이라 D가 정해 주면 따른다).
verified 의 뜻은 18에 정의가 없다. 권고: "공식 1차 출처가 직접 밝힌 사실 + 사용자 확인". 이 해석도 함께 결정 부탁.

## 쟁점 2. hormuz v3 원고 claims 이관 범위 (합격표 "claim id 강제" 행)

실측: `projects/hormuz_korea/script.yaml` 45문장 **전부 `sources: []`**. 출처는 credits.yaml '보도 · 자료' 6곳(Reuters 9.4, Korea Herald 9.7, UPI 기고 9.8, Foreign Policy 9.10, IMO 6.11 기준, 위키백과 "2026 Strait of Hormuz campaign")뿐이고, **문장↔매체 대응 기록과 기사 URL이 저장소에 없다**(R-0036 pending 그대로, `golden/youtube_description.txt` 도 매체명·날짜만).

| 선택지 | 내용 | 위험 |
|---|---|---|
| **A. 매체 단위 이관**(권고) | 6곳을 `ArticleSource` 6건(url=null, `note: "v3 credits.yaml 이관 — 원문 URL 미확보"`, key_facts=미디어 레지스트리 헤드라인이 있는 2건은 헤드라인, 나머지는 크레딧 표기)으로. 문장마다 claim 1개, source_ids = **장면(챕터) 단위로 v3 레퍼런스(`reference_code/v3_hormuz_korea/*.md`)가 근거로 적은 매체**, 근거가 없는 장면은 6곳 묶음. status 는 영상 무변경(25컷 MAD 0)을 위해 `corroborated`(라벨 없음) — 이관 claim 은 `notes: "v3 이관, 사용자 합격본"` | 문장별 정밀 출처가 아니다. 대신 지어낸 대응은 없다(장면 근거가 없으면 묶음이라고 적는다) |
| B. 문장 단위 정밀 이관 | 45문장 각각 매체 특정 | 근거 기록이 없어 Opus 추측이 된다(출처 날조 위험, G4) — 비권고 |
| C. v3 예외 | hormuz 는 claims 없는 프로젝트로 린트 예외 | D-0051 합격표가 명시적으로 금지 |

**권고 A** — ①(파일 두 개), ②(D-0051 "credits.yaml 기준"), G4(추측 금지). URL 은 계속 pending(null)로 두고 R-0036 은 "URL 미확보, 매체·날짜만"으로 닫는 것을 제안.
`corroborated` 부여가 과한지 판단 부탁 — 대안은 새 status 를 만들지 않고 `verified`/`corroborated` 중 하나, 또는 라벨 규칙에 "이관" 예외(비권고: 라벨은 status 만 본다, D42).

## 쟁점 3. 옛 소스 흐름(01_intake·02_sources·04_research)의 처분 범위 (작업 7·11)

실측: 옛 흐름 = `IntakePlan`(01_intake/intake_plan.json) → `SourceIntake` → `SourceCollectorWorker`(**운영 호출처 없음**) → `SourceRegistry`/`SourceEntry`(02_sources) → `SourceCompletenessReport` → `ResearchDossier`(04_research). D-0051은 ResearchDossier·research_io 삭제만 명시했다.
`research_service` 의 진입 조건이 `source_completeness_report.json` 이고 `bundle_service`(import-bundle)도 SourceRegistry·ResearchDossier 를 쓴다.

| 선택지 | 내용 |
|---|---|
| **A. 새 흐름으로 교체, 번들은 Phase 9 까지 유지**(권고) | INTAKE: 웹·CLI 가 `intake/sources.json` 을 만든다(IntakePlanner 는 "무엇을 더 모을지" 안내로 유지). SOURCE_VERIFY: 캡처 판독 → 사용자 확인 → 검증 워커 → `claims.json`. RESEARCH 진입 조건 = claims.json 유효. **삭제(P2)**: ResearchDossier·research_io·SourceCollectorWorker·source_collection_planner·SourceCollectionPartial·source_registry_builder/io·SourceEntry/SourceRegistry. `source_completeness_checker` 는 "claim id 없는 주장 문장 차단"으로 개조. `bundle_service` 는 번들 → sources/claims 변환으로 바꾸거나, 불가하면 Phase 9(번들 어댑터)까지 import-bundle 을 비활성 오류로 둔다 |
| B. 최소 교체 | ResearchDossier·research_io 만 삭제, 나머지 옛 모듈은 호출 없이 남김 | 죽은 코드가 남아 C11 P2 위반 소지 |

**권고 A** — ②(16 §3 "주장-출처 매핑으로 개조", 15 P2 "옛 경로는 삭제"), ③(운영 호출처 없음 실측). 삭제 목록·사용처는 작업 7 progress 에 적는다.

## 막히는 범위
- 쟁점 1 → 작업 6(검증 워커 판정 코드)·e2e. 쟁점 2 → 작업 8의 hormuz 통과 부분. 쟁점 3 → 작업 7 삭제 범위·작업 11.
- **막히지 않고 계속하는 것**: 작업 5(캡처 판독 워커), 9(post 카드), 10(크레딧·설명란 경로), 8의 린트 규칙 자체(claims 밖 id 오류·수치 문장 공란 오류·귀속 동사 경고), 12의 해당 테스트, NB11 taiwan AI(진행 중).
- §7(사용자 고유 결정) 해당 없음.

## 참고 — 작업 4 확인 방법
`rules/official_accounts.yaml` 17개는 기관 공식 사이트(centcom.mil 등)가 이 환경에서 403 이라 **Wikidata P2002(X username)** 를 SPARQL 로 조회해 채웠다. 항목마다 `source_url`(Wikidata 항목)·`check_method: wikidata_P2002`·`checked_on`. 공식 사이트 확인으로 바꿀 때는 필드만 고친다.
