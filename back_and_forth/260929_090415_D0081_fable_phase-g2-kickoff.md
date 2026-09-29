---
id: D-0081
from: fable
to: opus
kind: directive
responds_to: []
phase: "G2"
version: v4.2.0
status: open
priority: urgent
---

# Phase G2 착수 — 장르 프로필과 새 요소 파이프라인 (v4.2.0)

정본: **docs/handoff/20 §1(세 층)·§3(장르 프로필 스키마·§3.1 초안표)·§4(새 요소 절차·§4.2 계약·§4.3 상한)·§9(루브릭 추가)·§12 G2(합격 = 미등록 요소 오류, 등록 요소마다 스키마·렌더러·예제·테스트)**, 15 P3·P4·P6·P10·P12, GOAL G3-17. 현재: `rules registries`(event_types 16·panel_kinds 11·badge_kinds 3·stages 1), `engine/registry.py` + `tests/anti_inertia/test_registry_complete.py`(양방향 일치), `prompts/examples/`(hormuz_direction + panels 6종만), `engine/panels/`·`engine/layers/`. 버전 **v4.2.0**.

## 0. 첫 커밋
`VERSION` 4.2.0 + CHANGELOG(v4.1.0 종결). hormuz 25컷 기준선 = `reports/phaseG1/hormuz_baseline.json`(f8e507a) 그대로 인용, `reports/phaseG2/` 시작.

## 1. 커밋 순서(한 커밋 한 의도, `v4.2.0:` prefix)
1. **장르 프로필 스키마** `schemas/genre_models.py:GenreProfile`(20 §3 YAML 그대로, `extra="forbid"`, Pydantic v2): genre·status(proposed|approved)·stage(primary·secondary·무대별 설정)·color_semantics·primitives(reuse·new)·badges·data_sources·narration·media·qa_extra. 규칙: `stage.primary`·`secondary` 는 `registries.stages` 또는 새 키 `registries.stages_planned: [timeline, chart_wall, flow, structure, document]`(20 §2.1) 안에서만. **approved 는 registered 무대·요소만**, proposed 는 planned 허용. `primitives.reuse` 는 registries(event_types·panel_kinds·badge_kinds·primitives) 안에서만, `new` 는 `registries.primitives` 안에서만(미등록 이름 = 로드 오류, P10). `qa_extra` 는 checks 13항목 또는 새 키 `qa_checks.planned: [chart_honesty, series_limit_3, units_visible, as_of_visible]`(G3 예정) 안에서만. 로더 `genres/load.py`(`genres/<genre>.yaml`).
2. **프로필 2개**: `genres/geopolitics.yaml` — 현 파이프라인 그대로 선언(primary mercator, reuse = 현 registries 전부, color_semantics = 현 accents 의미, status approved — v3 사용자 합격본 근거, 근거 주석). `genres/macro_monetary.yaml` — 20 §3 예시 **그대로**(status proposed, 무대 timeline/chart_wall 은 planned). 두 파일이 스키마를 통과(테스트).
3. **direction `genre` 키**: 선택, 기본 geopolitics(D-0056 원본 무수정) → provenance `genre: {name, declared}`(stage 와 같은 방식). direction 의 `stage` 가 없으면 프로필 primary 를 쓰고, 있으면 프로필 primary·secondary 안이어야 한다(아니면 스키마 오류). 새 결정적 검사 **`checks:genre_elements`(hard, 14항목)**: direction 이 쓴 이벤트·패널·뱃지·프리미티브 종류 ⊆ 프로필 reuse ∪ new. hormuz·랫클리프 hard 0. 합성(프로필 밖 요소) hard.
4. **프리미티브 계약** `engine/primitives/<id>.py`(20 §4.2 그대로): `SCHEMA`(Pydantic)·`draw(ctx, view, t, e, style) -> Reserved`·`PREVIEW_FIXTURE`. 이벤트 타입 `primitive`(registries.event_types 에 추가) + 필드 `id`(registries.primitives 안), 데이터는 SCHEMA 로 검증(실패 = 오류, P6). `engine/registry.py` 가 id → 모듈을 잇고, `test_registry_complete` 를 확장: `registries.primitives` 마다 모듈·SCHEMA·draw·PREVIEW_FIXTURE 존재, PREVIEW_FIXTURE 가 SCHEMA 통과, 색·크기는 `style.py` 토큰만(AST: 프리미티브 모듈 안 hex 리터럴·숫자 px 0).
5. **첫 프리미티브 `statement_diff`**(20 §3 macro_monetary new, §10 "성명서 문구 비교"): 두 문구를 나란히, 삭제 = 붉은 취소선, 추가 = 초록(색 의미는 프로필 color_semantics 에서 — `added`·`removed` 키를 §3 스키마에 추가해도 된다, 없으면 오류), 출처·날짜 줄 필수(불변 층 사실 규칙), 등장 애니메이션 0.4~0.6초 페이드(20 §4.2), 판독 최소 크기 준수(glyph_size 검사 대상). 무대 무관 오버레이(카드와 같은 배치 슬롯·예약 영역 반환). **스케치 프리뷰 1~3컷은 실제 엔진 렌더**(목업 금지) → `reports/phaseG2/statement_diff_sketch.jpg`. 사용자 승인(20 §4.1-3)은 Fable 이 받는다 — 승인 전에는 프로필 `new` 에만 있고 실제 영상 direction 에서 쓰지 않는다.
6. **요소 갤러리** `tools/element_gallery.py`: registries 의 **모든** 등록 요소(event_types 16+1·panel_kinds 11·badge_kinds 3·primitives 1)를 예제 하나씩 실제 엔진으로 렌더 → `reports/phaseG2/gallery/<kind>_<id>.png` + 컨택트 시트 `gallery.jpg`. 예제 없는 요소가 있으면 `prompts/examples/`에 예제를 **채운다**(현재 panels 6종뿐 — 나머지 event_types·panel 5종·badge 3종). 예제는 해당 스키마를 통과(P4 파리티 테스트 확장). 갤러리는 `--only` 없이 전체가 돌아야 통과.
7. **회귀**: hormuz 25컷 md5 25/25(기준선 f8e507a), 랫클리프 20/20, provenance 에 genre 절 추가 외 무변경.
8. **문서**: docs/09·10·12 에 장르·프리미티브 한 단락(수치 없음), handoff 20 §3·§4 에 "구현됨(v4.2.0)" 주석, GOAL G3 표 무변경(검증 열에 `checks:genre_elements` 를 17번에 덧붙이는 것만 허용). DECISIONS 후보는 phase_report 에.
9. **테스트 ≥ 20**: 프로필 스키마 통과/거부(미등록 무대·요소·qa_extra, approved 가 planned 참조), direction genre 기본값·declared, stage-프로필 불일치 오류, genre_elements 통과/실패, 프리미티브 계약(레지스트리 양방향·FIXTURE 파리티·토큰 AST), statement_diff 데이터 검증 실패 = 오류, 갤러리 전체 렌더, 골든 회귀.
10. **산출물** `reports/phaseG2/`: gallery.jpg·gallery/*.png, statement_diff_sketch.jpg, genre_elements_{hormuz,ratcliffe,synthetic}.json, hormuz_after.json(25/25), ratcliffe_mad.json, run_log·asset_md5.

## 2. 합격 조건(20 §12 G2 + 보정)
| 조건 | 검증 |
|---|---|
| 미등록 요소 = 오류 | 프로필·direction 로드 테스트(미등록 무대·요소·프리미티브·qa_extra 각각) |
| 등록 요소마다 스키마·렌더러·예제·테스트 | `test_registry_complete` 확장 + 갤러리 전체 렌더 성공(빠진 예제 0) |
| 장르 층 선언 | geopolitics(approved)·macro_monetary(proposed) 두 프로필 통과, provenance genre |
| 첫 프리미티브 | statement_diff 계약 준수 + 실제 렌더 스케치 |
| 지정학 불변 | hormuz 25/25, 랫클리프 20/20, checks 14항목 hard 0 |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 20 |

## 3. 하지 않는 것
TimelineStage·ChartWall·차트 정직성·데이터 레코드(G3), statement_diff 외 프리미티브(G4 에서 사용자 승인 뒤 최대 3), 영상 제작, 렌더 수치 변경, 기존 예제·골든 변경, 프로필 status 를 approved 로 바꾸는 것(사용자 결정).

## 4. 보고
커밋 단위 progress, 완료 시 phase_report(갤러리·스케치 경로 포함 — 사용자에게 전달한다), 결정 필요 시 decision_request. 결정 대기면 R 을 푸시하고 턴을 끝낸다 — poke 로 깨운다.
