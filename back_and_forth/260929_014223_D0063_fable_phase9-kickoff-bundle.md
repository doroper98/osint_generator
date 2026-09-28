---
id: D-0063
from: fable
to: opus
kind: directive
responds_to: []
phase: "9"
version: v3.5.0
status: open
priority: urgent
---

# Phase 9 착수 — 번들 어댑터 (v3.5.0)

정본: 13 §Phase 9(`bundle/` 패키지, 번들 → script.yaml 초안 + direction 초안, 코퍼스 `samples/*.bundle.json` + `json/` 63건, D7 스키마 개선안 문서 제출), **12 §1(번들 구조)·§2(v2 매핑)·§5(12막 금지 — 장면은 공간·정보 유형이 바뀔 때)·§6(스키마 개선 요청안)·§7(모듈 설계)**, 19 §6 9행, DECISIONS D7(제안만, 사용자가 반영), 16 §3·18(소스 인테이크 = 6.95 흐름), 15 P8·P9. 현재: `bundle/{charts,text}.py`(Phase 0 이관 순수 함수), `schemas/models.py ReportBundle`(fail-closed), `orchestrator/bundle_io.py`(로더, import-bundle 은 명시 오류 D52), 코퍼스 실측 **68건**(json 63 + samples 5, 최상위 키 전부 ReportBundle 과 일치, images 8건), 6.95 인테이크(`intake/sources.json`·`claims.json`·verify_sources·Facts·게이트 ①), 6.9 AI 연출가(DirectorWorker·검수 루프), 7 camera_suggest, 8 BGM 레지스트리.

## 0. 첫 커밋
`VERSION` 3.5.0 + CHANGELOG(v3.4.0 종결). NB22(`test_two_pass_record` ffmpeg 없으면 사유 있는 skip). `orchestrator/bundle_io.py` → `bundle/load.py` 로 **이동**(경로 하나, P2 — orchestrator 는 얇은 호출만). 코퍼스 68건 전부 로드 → `reports/phase9/corpus_load.json`(건별 pass/fail·미지 필드). 실패가 있으면 그 필드 목록을 **첫 progress 에** 적고(스키마에 optional 로 추가할지 decision_request), 통과분으로 계속.

## 1. 커밋 순서(한 커밋 한 의도, `v3.5.0:` prefix)
1. **`bundle/entities.py`**: stakeholder `nodes`(kind·flag·logo)·`map.markers` → `assets/entities.yaml`·people 라이브러리와 조인(id 매칭 → 없으면 `unmatched[]` 기록, 추측 생성 금지). 문장 언급 탐지(별칭)는 폴백이고 `unmatched` 와 함께 초안 주석에 남긴다.
2. **`bundle/to_sources.py`**(import-bundle 복귀, D52): 번들 `sources[]`·`claims[]`·`contradictions[]` → 6.95 `intake/sources.json`(ArticleSource/DocumentSource, `note: "번들 이관"`, url 있으면 그대로)·claims 후보. status 는 **6.95 판정 코드(D50·D53)가 정한다** — 번들의 confidence 를 status 로 옮기지 않는다(번들은 2차 자료). contradictions → contested 후보(sides 양측). 게이트 ① 뷰에 번들 출처가 보이는지 e2e 로 확인.
3. **`bundle/to_script.py`**: 번들 → `script.draft.yaml`(6.95 `script.schema:Script` 그대로 통과, P4). 규칙(12 §5): 장면 경계 = map_ref/마커 집합 또는 차트 종류가 바뀔 때(같은 공간 섹션은 합침, **12막 1:1 금지 — 테스트: 섹션 수 ≠ 장면 수를 코퍼스 다수에서 확인**), heading 은 화면 문장에 넣지 않음(유튜브 챕터명 후보로만 `chapters[]`), 문장 = narration, tts = narration_tts 있으면 그대로·없으면 `script/tts` 규칙(03 §4), `sources` = 2 의 claim id. **금지 문구(`banned_phrases`)에 걸린 문장은 초안에 `rewrite_required: true` + 걸린 패턴을 주석으로** — 어댑터가 다시 쓰지 않는다(P8: 재작성은 ScriptWorker 몫, 6.95 게이트 ① 전 린트가 차단). 차트 `provenance.verification: inferred`/출처 없음 → 패널 데이터에 `prov_tag` 추정 태그(규칙 값 그대로).
4. **`bundle/to_direction.py`**: map markers/arcs/charts → **연출가 입력 재료**(`intake/bundle_materials.json`: places·paths·패널 data·미디어 후보·엔티티 뱃지 후보) + `direction.draft.yaml`(places/paths/panels 만, shots 는 camera_suggest 제안으로). DirectorWorker 입력 `{bundle_materials}` 자리(제안·재료일 뿐 강제 아님, 17 §5.3 문법). 이전 영상 연출은 넣지 않는다(P9).
5. **CLI/웹**: `import-bundle {pid} --file` 복귀 = 1~4 실행 + 게이트 ① 진입 조건(claims.json) 충족. 웹 인테이크에 "번들 업로드" 소스 유형 1개(6.95 폼에 추가). provenance `bundle` 단계(bundle id·generated_at·producer·장면 수·rewrite_required 수·unmatched 수).
6. **합격 실증 — 자유 구성 초안**: 랫클리프 번들(12 참조 `analysis_20260829_115457_ec53e620b2.bundle.json`, `https://analysis-reports.pages.dev/`)을 받아 `samples/ratcliffe2026/` 에 넣는다(사용자 사이트, 권리 문제 없음). **받지 못하면**(네트워크) 코퍼스에서 map+charts+contradictions 가 다 있는 번들 1건을 골라 대체하고 progress 에 사유. 실행: import-bundle → 초안(장면 수 vs 섹션 수, rewrite_required 목록, 추정 태그 목록) → verify_sources → 게이트 ① 뷰 → **ScriptWorker 로 초안 다듬기 1회**(rewrite_required 문장이 실제로 바뀌는지) → AI 연출 1회(재료 입력) → `--preview auto` 컨택트 시트 + checks + 시각 검수. 전편 렌더는 **권리(인물·사진)와 TTS 가 갖춰지면** artifacts/phase9-v3.5.0 에(갖춰지지 않으면 시트만 + 사유 — 조용히 건너뛰지 않는다). 영상이 나오면 내가 사용자에게 전달.
7. **D7 문서**: `docs/handoff/reports/phase9/agents_reviewer_schema_proposal.md` — 12 §6 표 + 코퍼스 68건 실측으로 뒷받침(각 필드가 없어서 어댑터가 무엇을 못 했는지: unmatched 수, tts 비어 있는 비율, 문장 날짜 부재 등). **제안만**(사용자가 agents_reviewer 에 반영). 사용자 전달은 내가 한다.
8. **테스트 ≥ 15**: 로더 fail-closed(미지 필드 오류), 장면 경계 규칙(합침·분리), 12막 금지, rewrite_required 표시, 추정 태그, claims status 를 번들 confidence 로 옮기지 않음, unmatched 기록, 초안이 Script/Direction 스키마 통과(P4), 규칙 리터럴 0, hormuz 25컷 MAD 0(무영향).
9. **산출물** `docs/handoff/reports/phase9/`: corpus_load.json, ratcliffe(또는 대체) 초안 두 파일·게이트 ① 뷰·ScriptWorker 전후 diff·컨택트 시트·checks·qa_verdict·provenance, schema_proposal.md, run_log·asset_md5.

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 자유 구성 초안(13) | 랫클리프(또는 대체) 장면 수 ≠ 섹션 수, 경계 근거(공간·차트 종류) 초안 주석에, heading 화면 문장 0 |
| 금지 문구 | 걸린 문장 rewrite_required 표시 → ScriptWorker 1회 뒤 린트 통과 |
| 추정 차트 태그 | provenance inferred/무출처 차트 전부 prov_tag(시트에서 육안) |
| 출처 흐름 | 번들 출처가 sources.json·claims.json·게이트 ① 뷰에 보이고 status 는 판정 코드 결과(번들 confidence 아님) |
| 초안은 초안 | 어댑터가 direction.yaml 을 최종으로 쓰지 않음(연출은 DirectorWorker), 원고 재작성 안 함(P8) |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 15, 환경 의존은 사유 있는 skip |

## 3. 하지 않는 것
agents_reviewer 코드 수정(D7 은 문서만), 웹 검색 기반 사실 확인 자동화(12 §5-5·6 은 사람 절차로 기록만), X 스크래핑, 해상도·성능(10), 문서 전면 동기화(11), 골든 PNG 교체.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report, 결정 필요 시 decision_request(§7 후보: 코퍼스 스키마 확장 여부는 내 결정, 랫클리프 번들 내용 해석 차이(12 §5-6)는 사용자 고지 항목). 턴 종료 금지(21 §6).
