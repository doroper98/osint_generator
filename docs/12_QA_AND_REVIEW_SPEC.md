<!--
tier: 2
last_synced_with: v5.0.0
ssot_for: [review-gates, qa-policy]
depends_on: [docs/handoff/16_ORCHESTRATOR_INTEGRATION.md, docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md, docs/handoff/18_SOURCE_INTAKE_ARTICLES_X.md, 07_VIDEO_STYLE_GUIDE.md, 08_AUDIO_AND_TTS_SPEC.md, ../GOAL.md]
last_review: 2026-09-30
-->

# 12 — QA·검수 명세 (v4.0.0 동기화)

v1의 9개 Review Gate·`qa_evidence_report.json`·Remotion 라벨 배지는 v3.0.0에서 폐기됐다.
지금은 **사람 게이트 2개 + 코드 검사 + AI 시각 검수 루프**다. 정본은 handoff 16 §2·§5, 17 §3~§4, 18이다.
데이터 모델은 Pydantic 코드가 SSOT다(DOCS_GOVERNANCE §6.5). 이 문서는 클래스 이름만 가리킨다.

---

## 1. 사람 게이트 2개

| 게이트 | 상태 | 보는 것 | 반려 시 되돌림 |
|---|---|---|---|
| ① 원고 승인 | `SCRIPT_APPROVAL` | 장면 목록·원고 전문(자막)·출처 표·린트·미디어 후보(`orchestrator/gate_view.py`) | 원고 단계 |
| ② 프리뷰 승인 | `PREVIEW_APPROVAL` | 컨택트 시트·checks·AI 검수 잔여 이슈·provenance·판 목록(AI 연출이면 판 선택 가능) | 연출·자산·음성 중 하나(handoff 16 §2) |

- 기록은 `project_manifest.json`의 `gate_decisions`(`schemas.models.GateDecision`)다. append-only다.
- 게이트 수는 설정 `config:review_gates.require_human_approval`과 테스트(`tests/test_gates_pipeline.py::test_config_two_gates_only`)로 고정된다.
- 반려 코멘트는 **그 프로젝트의 수정 지시로만** 쓴다. 규칙·프롬프트에 자동 반영하지 않는다(15 P11). 반복 지적은 규칙 개정 후보로 모아 사람이 승인한다.
- 사용자 최종 승인 없이 업로드하지 않는다(G4-12).

## 2. 프리뷰 판정 흐름

```
preview → prev/checks.json(결정적 검사 18항목)
   hard > 0  → (AI 연출) 수정 워커가 검사 오류만 받아 고친다 → 재검증·재프리뷰
   hard = 0  → (AI 연출) 시각 검수 워커(시트 이미지) → revise 면 수정 워커 → 재프리뷰 → 재검수
   루프 상한 = rules qa_checks.visual_qa_loop_max → 상한 도달 시 loop_pick_order 최선 판
   → 게이트 ② 사람 판정(잔여 이슈 목록과 함께)
```

| 항목 | 키·위치 |
|---|---|
| 검사 18항목(hard 15·warning 3) | [07](07_VIDEO_STYLE_GUIDE.md) §8, `engine/checks.py`, `rules:qa_checks` |
| 루프 상한 | `rules:qa_checks.visual_qa_loop_max` |
| 상한 도달 시 판 선택 순서(D-0049 쟁점 3) | `rules:qa_checks.loop_pick_order` |
| 루프 기록 | `prev/qa_loop.json`, `prev/sheet.v{n}.jpg`(`engine.qa.QALoopRecord`) |
| 루프 제어 | 코드(`orchestrator/ai_direction.py`). LLM이 종료를 정하지 않는다(AP-V6-2·5) |

- **사람 연출은 검수 루프를 돌지 않는다.** 골든 연출을 LLM이 고치지 않게 하기 위해서다. 사람이 게이트 ②에서 본다.
- 루프 상한에 닿고도 남은 지적은 게이트 ② 사람 판정으로 넘긴다(D49). 판정 근거는 back_and_forth D 파일과 DECISIONS에 남는다.
- 검사 hard가 하나라도 있으면 시각 검수 LLM을 부르지 않는다(17 §3).
- **게이트 ② 사람 판정은 지리 정합도 본다**(v4.1.0, D-0078·D69): 새 권역이 처음 나오는 컷은 원본 해상도로 열어 국가 육지·수역이 실제 지리와 맞는지 확인한다. 자동 검사는 `geo_report.json` 의 `fill_ratio`(`rules:geo.land_fill_min_ratio`)가 맡지만, 기준 프레임에 결함이 있으면 회귀 검사는 결함을 통과시키므로 사람이 한 번은 본다.

### 2.1 Phase 10에서 더한 검사

| 검사 | 등급 | 키 | 근거 |
|---|---|---|---|
| 카드 × 날짜·자막 겹침(`[card-over-date]`·`[card-over-subtitle]`) | hard(overlap) | `rules:layout_480p.reserved_zones` | NB23, back_and_forth D-0066 §0 |
| 카드에 가린 마커 라벨(`[label-hidden-by-card]`) | hard(overlap) | `rules:qa_checks.label_hidden_max_ratio` | D61 |
| 최소 글자(`glyph_size`) — 설계 px 판정, 예외 역할만 제외 | hard | `rules:layout_480p.min_font_px`, `rules:qa_checks.glyph_size_exempt` | D62 |
| 업스케일된 미디어(`media_upscaled`) | warning | `config:engine.output` | D60 |
| 경계선 이름을 단 경로(`boundary_as_route`, `[boundary-as-route]`) — 경계선은 지도 경계 레이어가 그린다 | hard | `rules:geo.boundary_names` | back_and_forth D-0107(M8) |
| 지도 좌표 근거 미대조(`geo_unsourced`, `[geo-unsourced]`) — 지명 사전에 없는 이름의 places·인라인 marker, paths·route, provenance `geo.unsourced[]` | warning | `rules:geo.gazetteer` | back_and_forth D-0107, v4.10.0 D-0116 |
| 지명 사전 좌표 불일치(`geo_mismatch`, `[geo-mismatch]`) — place 키·marker label 이 `data/gazetteer.yaml` 과 맞는데 좌표가 맞은 항목 모두의 tol_km 밖, provenance `geo.mismatch[]`·`geo.matched[]` | hard | `rules:geo.gazetteer`(`geo.gazetteer`, handoff 04 §11) | v4.10.0 back_and_forth D-0116(B-1) |
| 정적 구간(`static_window`, `[static-window] t0-t1 changes=n`) — 지도가 보이는 구간(전면 카드·패널 덮개 밖)의 어떤 window_sec 창이든 change_kinds 변화 < min_changes. 걸린 범위에 느린 푸시인(creep), provenance `pacing.static_windows[]`·`pacing.creep`. 콘티 판에서도 돈다 | warning | `rules:pacing.static_window`(`engine.pacing`, handoff 05 §7) | v4.11.0 back_and_forth D-0118 §1 |

### 2.2 장르 요소 검사 — v4.2.0

`genre_elements`(hard)는 연출이 쓴 요소 종류(패널은 kind, 프리미티브는 id, 뱃지는 badge와 kind)가 장르 프로필의 reuse ∪ new 안인지 본다. 프로필 밖 요소는 요소마다 `[genre-element]` 한 줄이다.
콘티 판(v4.9.0, handoff 11 §9)은 검사 프로파일 `animatic` 으로 돈다 — `rules:animatic.checks_skip` 은 건너뛰고 checks.json `skipped`·provenance `animatic_run.checks_skipped` 에 남는다(조용한 생략 아님).

장르 프로필의 `qa_extra` 는 이 표의 검사 id 또는 `rules:qa_checks.planned`(예정 검사)만 쓸 수 있다. 새 프리미티브는 스케치 프리뷰(`tools/primitive_sketch.py`, 실제 엔진 렌더)와 사람 승인 뒤에만 영상 연출에 쓴다(handoff 20 §4.1).

### 2.3 차트 정직성 검사 — v4.3.0

handoff 20 §5.3 표의 아홉 규칙을 네 검사(`chart_honesty`·`series_limit_3`·`units_visible`·`as_of_visible`, 모두 hard)로 본다. 구현은 `engine/honesty.py`, 판정은 차트 메타(요소 데이터 + 프리뷰 컷에 실제로 그린 글자)만 쓴다.
적용 범위는 요소의 축 종류(렌더러 모듈 `AXIS`)로 정한다 — 값 축(시리즈·dots·dual_line)은 넷 다, 날짜 축(timeline·gantt 패널·시간축 무대)은 chart_honesty 만. 적용되지 않는 검사는 checks.json `notes` 에 `n/a` 로 남는다(D-0087). 표는 `rules:qa_checks.chart_targets`.
위반 주입 아홉 건의 합성 판정은 `tools/chart_honesty_report.py --synthetic`, 테스트는 `tests/test_chart_honesty.py`.

### 2.4 장르 영상 검수 보강 — v4.4.0

`glyphs` 는 프리뷰 컷을 그리며 **그 글자를 그린 글꼴**에 글리프가 있는지 본다(`typography.GLYPH_MISS`). 프로젝트 글꼴 중 하나에만 있는 글자는 두부 상자가 되므로 hard 다.
프리미티브도 모듈 `AXIS` 로 정직성 적용 범위를 정한다(값 축이면 `chart_meta`). 시각 검수는 장르 영상에서 루브릭 추가 항목(handoff 20 §9, `rules:genre_prompt.rubric_extra`)을 항목마다 판정한다.
검증 라벨은 영상 본문에 그리지 않는다(v4.5.0, D85). 엔딩 카드 마지막 줄 안내 한 줄은 검수 지적 대상이 아니다(프롬프트에 규칙 값으로 명시).

### 2.5 검증 라벨 본문 표기 금지 — v4.5.0

| 검사 | 등급 | 키 | 근거 |
|---|---|---|---|
| 프리뷰 컷에 그린 글자 중 검증 라벨 문구(`[label-in-body]`) | hard(forbidden) | `rules:script_schema.labels` | 사용자 결정 D85, back_and_forth D-0096 |

## 3. 시각 검수 판정 형식

시각 검수 워커의 출력은 `engine.qa.QAVerdict`다. 지적(`QAIssue`)은 컷(`frame`)·등급(hard/soft)·분류·근거(evidence)를 가진다.
근거 없는 지적은 모델이 거부한다(AP-V6-8). 검수자는 연출 파일을 고치지 않는다. 수정 제안(`fix`)은 `event_ref`(대상 이벤트)와 제안 문장뿐이다.
수정 워커의 출력은 `engine.qa.Revision`(수정된 direction 전체 + 지적별 changelog)이다. 지적받지 않은 부분을 바꾸면 코드가 잡는다(17 §5.5).
프롬프트는 `prompts/visual_qa.md`·`prompts/revise_direction.md`, 예시 출력은 스키마를 그대로 통과해야 한다(15 P4, `tests/anti_inertia/test_prompt_schema_parity.py`).

## 4. 사실 검증과 영상 라벨

- 소스 레코드·주장(claim)·근거는 `intake/sources.json`·`intake/claims.json`이다(handoff 18).
- 교차 확인은 **인용 대조**다. LLM은 claim 후보·인용·입장만 내고 판정은 코드(`orchestrator/source_verify.py`)가 한다(D50).
  인용 길이·독립 출처 수·재인용 표지는 `rules:verification`.
- **귀속 인용은 교차 확인이 아니다(v5.0.0 GOAL G4-21).** claims `claim_kind` fact 는 귀속 인용을 supports 에서 빼고(D-0054 B), statement("발언이 있었다")는 귀속 인용·발언 주체 본인의 공식 원문을 supports 로 센다. statement 의 단정 인용은 폐기 + drops[](판정 실패 → 재검증). 판정 표·해석은 handoff 18 §9.
- 문장 라벨은 claims status로 코드가 계산한다. 문구는 `rules:script_schema.labels`, 우선순위는 `rules:script_schema.label_strength_order`([07](07_VIDEO_STYLE_GUIDE.md) §6).
- **라벨은 기록용이다(v4.5.0, 사용자 결정 D85, C9).** 자막·패널·카드에 그리지 않고, 엔딩 카드 맨 마지막 줄 가장 작은 글씨 한 줄(`rules:layout_480p.end_card.notice_unverified`)로만 건수를 적는다. 원고 라벨 ↔ claims 대조(`script.labels.check_project_labels`, 린트·렌더·mux)는 그대로다.
- 미검증 정보를 제목·썸네일에 쓰지 않는다(G4-7). 미검증 주장을 인용하는 문장은 누가 말했는지 귀속한다(`rules:script_schema.attribution_markers`, 린트 경고 — v4.10.0 "보도했" 추가, handoff 18 §8).

## 5. 원고·음성 QA

- 린트(`script/lint.py`): 금지 문구(`rules:banned_phrases`), 발음 텍스트 기호(`rules:tts_rules.forbidden_chars_regex`), TTS 위험 표기(`rules:tts_risk`), 강조어, 출처(claim id), 자막 줄 수.
- 오디오 QA(측정 경로 하나, `audio/qa.py`)는 [08](08_AUDIO_AND_TTS_SPEC.md) §7이다.

## 6. 권리

모든 사용 자산은 권리 레지스트리에 있어야 한다. 표기 위치는 `rules:credits`(엔딩 카드 ∪ 설명문 = 전 자산).
검증되지 않은 권리·빠진 레지스트리 항목·출처 줄 없는 미디어는 렌더 전에 오류다(checks `rights`, `tests/test_credits_phase5.py`, `tests/test_media_gate_phase65.py`).
위반을 발견하면 [06_SOURCE_AND_RIGHTS_POLICY.md](06_SOURCE_AND_RIGHTS_POLICY.md) §9를 따른다.

## 7. 합격 기준

v2 합격 기준 17개와 항목별 검증 방법은 [GOAL.md](../GOAL.md) G3이다(`tests/test_goal_g3.py`).
