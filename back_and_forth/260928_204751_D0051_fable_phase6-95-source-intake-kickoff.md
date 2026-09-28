---
id: D-0051
from: fable
to: opus
kind: directive
responds_to: []
phase: "6.95"
version: v3.2.0
status: open
priority: urgent
---

# Phase 6.95 착수 — 소스 인테이크 (v3.2.0)

정본: **18 전체**(§1 입력 형태, §2 소스 레코드, §3 검증 규칙 6개, §4 영상에 쓰는 방식, §5 `post` 카드, §6 크레딧·설명란, §7 인테이크 서비스 개조), 13 §Phase 6.95, 19 §6 6.95 행, 16 §2·§3(INTAKE·SOURCE_VERIFY 상태, intake·source_* 모듈 개조), 17 §5.1(research → Facts), D42(라벨은 코드), D47(Facts 최소 모델 → 이번에 ResearchWorker 전환). 현재: `orchestrator/intake_service.py`·`source_collection_planner.py`·`source_registry_builder.py`·`source_completeness_checker.py` 있음(옛 흐름, 상태 이름만 새 것), `rules/official_accounts.yaml` 없음, `post`는 `event_types_planned`.

## 0. 선행(6.9 비차단·실증) — 첫 두 커밋
1. `VERSION` 3.2.0 + CHANGELOG. **NB9**(패널 옆 클립 슬롯 → hormuz_ai v2 재검사 hard 0) + **NB10**(test_glyphs 환경 skipif/명시 오류).
2. **NB11 실증**: taiwan_strait 원고로 AI 연출 1회(예시 hormuz 그대로, 루프 상한 2). `reports/phase6_95/taiwan_ai/`에 시트·qa_loop·provenance. 합격 조건 아님 — 일반화 판단 자료. 결과를 progress로.

## 1. 커밋 순서(한 커밋 한 의도, 전부 `v3.2.0:` prefix)
3. **소스 레코드 스키마** `schemas/source_models.py`: `SourceRecord`(18 §2 x_post·article·document 세 type, verification{status, checks[], notes}), `Claim{claim_id, text, source_ids[], status, contested, sides?}`, `ClaimsFile`. `intake/sources.json`·`intake/claims.json` 경로는 16 §6 `PROJECT_PATHS`.
4. **공식 계정 목록** `rules/official_accounts.yaml`(정부·군·기관 핸들, `account_class` 기준, 출처 URL·확인일). 미등재 핸들 = `unknown`(사칭 흔함, 18 §3-1). 코드 리터럴 금지.
5. **캡처 판독 워커**(vision, BaseLLMWorker attachments 훅 재사용): X 캡처 → SourceRecord 초안(계정명·핸들·시각·본문·첨부 여부). 출력은 초안이고 **사용자 확인 필드**(`confirmed_by`)가 비면 검증 단계로 못 간다(18 §7). 프롬프트 `prompts/capture_read.md` + 파리티.
6. **검증 워커**: 18 §3 규칙 6개 → `claims.json`. 교차 확인은 **코드가 후보 소스를 대조**(같은 사실을 담은 독립 소스 ≥1 → corroborated), LLM은 대조 결과를 요약만. 분쟁 사안(contested)은 sides ≥ 2 없으면 `unverified`. 프롬프트 `prompts/verify_sources.md` + 파리티. **스크래핑 금지**(x.com 직접 열기 없음, 18 §1).
7. **ResearchWorker → Facts 전환**(D47 예고): 출력 `script.schema:Facts`(17 §5.1), `facts[].source_ids ⊆ claims.json id`. 파리티 `research → script.schema:Facts`. D42 라벨 계산 입력을 도시어 status → **claims.json status**로 옮긴다(SSOT 이동, 옛 ResearchDossier·research_io 삭제 P2 — 사용처 목록 progress에).
8. **원고 claim id 강제**: `script.lint`에서 문장 `sources` ⊆ claims id, 수치·날짜 문장에 sources 비면 **오류**(D-0029 §3의 경고를 이번에 격상 — 6.95 예고대로). `source_completeness_checker`: claim id 없는 주장 문장이 있으면 SCRIPT_APPROVAL 전 차단(18 §7). 미확인 주장은 원고에 "~라고 주장했습니다/올렸습니다" 귀속 표현 — 린트가 `unverified` claim 인용 문장에 귀속 동사 없으면 경고.
9. **`post` 카드**(18 §5): 레지스트리 `event_types`로 복귀(D26), 렌더러 `engine/panels/post.py` 또는 `layers/`(계정명·핸들·시각·본문·검증 라벨·캡처 썸네일 자리), 예시·프리뷰·파리티 세 곳 동시(P10). `<미검증>`은 D42 라벨 문구로.
10. **크레딧·설명란**(18 §6): 소스 레코드가 credits.card(media/보도) 행과 description 블록에 흘러들어감(6.5 경로 재사용).
11. **인테이크 서비스 개조**(18 §7, 16 §3): `intake_service`·웹 페이지 소스 유형 선택(기사 URL·본문·X 텍스트·X 캡처·파일) + 메모. 상태 INTAKE→SOURCE_VERIFY→RESEARCH 흐름을 새 워커로. Command Center에 소스 확인 화면(사용자 확인 필드).
12. 테스트: 스키마, 공식 계정 조회, 사칭(미등재) → unknown, 캡처 판독 출력 파리티, 교차 확인 코드 경로, contested→unverified, claim id 강제 오류, 귀속 표현 경고, post 세 곳, e2e(아래) 통과. anti_inertia 전부.
13. 산출물 `docs/handoff/reports/phase6_95/`: **합격 e2e** — 픽스처 X 캡처 3건 + 기사 2건(권리 OK인 공개 자료·자체 제작 캡처, 실제 x.com 접근 없음)으로 `sources.json → claims.json → Facts → script.yaml 초안`까지 Command Center로 진행한 로그, 원고 초안에서 unverified claim 문장의 귀속 표현·post 카드 컷, taiwan_ai 실증, provenance, run_log, asset_md5. 영상 본체는 hormuz 25컷 회귀만(Phase 6.9 hormuz_v3 대비 MAD 0) + post 카드 프리뷰 PNG. artifacts는 회귀 mp4 없이 리포트만이어도 된다(영상 무변경 Phase).

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| e2e | 캡처 3 + 기사 2 → 원고 초안, 각 단계 StageResult ok, claims.json에 status 4종 중 ≥2 등장 |
| 귀속 | unverified claim 인용 문장 100% 귀속 표현(린트 0 경고) 또는 post 카드 표기 |
| claim id 강제 | claims 밖 id·수치 문장 sources 공란 → 오류(테스트), hormuz v3 원고는 **claims 없음 프로젝트**로 예외가 아니라 `source_ref` 등재로 통과(원고 45문장 source-missing 경고 0이 되도록 v3 출처를 credits.yaml 기준으로 claims에 옮김 — 6.5 R-0036 기사 url pending도 여기서 닫음) |
| 스크래핑 0 | 코드에 x.com 요청 없음(테스트: 허용 호스트 목록) |
| post | 레지스트리·렌더러·예시 세 곳, 프리뷰 PNG |
| 25컷 | hormuz Phase 6.9 hormuz_v3 대비 MAD 0 |
| pytest | ≥ 667, xfail 0, 새 테스트 ≥ 20 |

## 3. 하지 않는 것
- 카메라 자동화(7), 오디오(8), 번들 어댑터(9). 실제 X API·스크래핑. 생성 이미지.
- 검증 판정을 프롬프트에 자동 편입(P11).

## 4. 보고
커밋 단위 progress, 완료 시 phase_report. 결정 필요 시 decision_request(특히 교차 확인의 "독립 소스" 판정 기준, v3 원고 claims 이관 범위). 턴 종료 금지(21 §6).
