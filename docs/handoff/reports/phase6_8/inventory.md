<!--
tier: 3
last_synced_with: v2.5.5
ssot_for: [phase6_8-inventory]
depends_on: [docs/handoff/16_ORCHESTRATOR_INTEGRATION.md, docs/handoff/13_IMPLEMENTATION_PLAN_FOR_CLAUDE_CODE.md, docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md]
last_review: 2026-09-28
-->

# Phase 6.8 준비 — 오케스트레이터 현 상태 인벤토리 (초안, v2.5.5 @ 8fb525f)

back_and_forth D-0038 §2. 착수 지침 전 조사 기록이다. 코드는 바꾸지 않았다.
정본: 16 전체, 13 §Phase 6.8, 19 §3.6·§6 6.8 행·부록 B.

## 1. 상태 머신 (현재)

| 항목 | 현재 | 16 §2 목표 |
|---|---|---|
| `schemas/models.py:40` `ProjectState` | 24개 값(CREATED … PUBLISHED, ARCHIVED) | 14개(CREATED·INTAKE·SOURCE_VERIFY·RESEARCH·SCRIPT_DRAFT·SCRIPT_APPROVAL·VOICE_TIMELINE·ASSETS·DIRECTION·PREVIEW_QA·PREVIEW_APPROVAL·RENDER·AUDIO_MIX·DELIVER·DONE) |
| `orchestrator/state_machine.py` (100줄) | `LINEAR_SEQUENCE` 선형 + 어디서든 ARCHIVED. 역전이 없음 | 역전이 표 3종(SCRIPT_APPROVAL→SCRIPT_DRAFT, PREVIEW_APPROVAL→DIRECTION·SCRIPT_DRAFT·ASSETS) |
| manifest `schema_version` | `schemas/models.py:22` 전역 1 | 19 §3.6: 2. 옛 manifest는 변환 없이 "v1 manifest — 재생성 필요" 오류 |
| 테스트 | `tests/test_state_machine.py` 10개 | 새 상태·역전이로 교체 |

**옛 상태를 직접 쓰는 곳** (새 상태로 옮기거나 삭제 대상):

| 파일:줄 | 쓰는 상태 |
|---|---|
| `orchestrator/intake_service.py:84-146` | CREATED → INTAKE_PLANNING → INTAKE_PENDING_USER |
| `orchestrator/main.py:429-557` (submit-intake·build-source-registry) | INTAKE_PENDING_USER → SOURCE_COLLECTING → SOURCE_COMPLETENESS_REVIEW |
| `web/intake_page_app.py:282-300` | INTAKE_PENDING_USER → SOURCE_COLLECTING |
| `orchestrator/research_service.py:79-148` | SOURCE_COMPLETENESS_REVIEW → RESEARCH_IN_PROGRESS |
| `orchestrator/bundle_service.py:72-114` | SOURCE_COMPLETENESS_REVIEW → RESEARCH_IN_PROGRESS |
| `orchestrator/script_service.py:59-124` | RESEARCH_IN_PROGRESS → BLUEPRINT_REVIEW → SCRIPT_WRITING |
| `orchestrator/project_manager.py:231` | new_project → CREATED |
| `orchestrator/command_center.py:32-41` | 손상 manifest → CREATED 폴백 (xfail c) |
| 테스트 | test_intake_flow·test_script_flow·test_research_flow·test_intake_planner_worker·test_state_machine |

옛 → 새 대응 초안(결정 아님, 착수 지침 확인용): INTAKE_PLANNING·INTAKE_PENDING_USER → INTAKE, SOURCE_COLLECTING·SOURCE_COMPLETENESS_REVIEW → SOURCE_VERIFY, RESEARCH_IN_PROGRESS·BLUEPRINT_REVIEW → RESEARCH, SCRIPT_WRITING → SCRIPT_DRAFT, SCRIPT_REVIEW → SCRIPT_APPROVAL. 나머지 옛 상태(SCENE_*·RENDER_DEBUG·THUMBNAIL_*·PUBLISH_*)는 대응 없음 → 삭제.

## 2. 승인 게이트

| 항목 | 현재 | 목표 |
|---|---|---|
| `config.yaml review_gates.require_human_approval` | 9개(intake·source_completeness·blueprint·script·scene·draft_debug·draft_preview·thumbnail·final) | 2개(script_approval·preview_approval, 16 §5, 19 §6) |
| `main.py approve` | "Phase 11 에서 구현 예정" 출력만 하고 exit 0 | 승인/반려 기록 + 역전이. 반려 코멘트는 프로젝트 수정 지시로만(P11) |
| TUI | `tui_app.py` 392줄: OrchLogPanel·DashboardPanel·WorkerSlotPanel, `current_state` 문자열 표시 | 게이트 ① 장면 목록·원고·출처·린트·미디어 후보, ② 컨택트 시트 경로·provenance 요약·예상 러닝타임 |

## 3. 엔진 어댑터 (`engine_service.py`)

- **파일 없음.** `StageResult`는 이미 `schemas/engine_models.py:95`에 있다(drops 비어 있지 않으면 ok=False 검증 포함). 16 §4 계약과 필드가 같은지 착수 때 대조.
- CLI 실측(16 §4 표 대비):

| 16 §4 | 저장소 | 비고 |
|---|---|---|
| `python -m script.plan` | 있음 | |
| `python -m geo.prep / assets` | `geo.prep` 있음, `assets` 단일 CLI 없음 | 인물·국기·미디어는 `tools/fetch_data`·`tools/media_fetch` |
| `python -m engine.validate` | **없음** | direction 검증은 6.9(17 §2) 범위와 겹침 |
| `engine.render --preview auto` | 있음. `auto` 또는 초 목록 | StageResult JSON 마지막 줄 |
| `engine.render --jobs N` | 있음 | |
| `audio.mix` | 있음 | |
| `engine.mux` | 있음 | provenance.json 은 mux 가 쓴다 |

## 4. 모듈 운명표 이행 현황 (16 §3)

| 모듈 | 16 판정 | 현재 |
|---|---|---|
| state_machine | 개조 | 옛 그대로 |
| project_manager (282줄) | 유지 | 새 디렉터리(script.yaml·plan.json·direction.yaml·prev·out) 관리 없음 |
| command_center (49줄) | 유지·개조 | 폴백 남음 |
| tui_app·dashboard·log_router | 유지·개조 | 옛 상태 문자열 |
| intake·source_* | 유지·개조 | 6.95(18) 범위와 겹침 |
| research_service·io | 유지 | |
| script_service·io, `workers/script_worker.py` | 개조 | `FullScript` 출력(D33 — 6.8 에서 `script.schema:Script` 로 전환, parity 대상도 변경) |
| scene_builder·scene_io | 삭제 | v2.0.0 에서 삭제됨 |
| tts_lint·tts_pronounce | `script/lint.py` 로 병합 | 둘 다 남음. 사용처: `main.py:713,734` lint-script, `bundle/text.py:13`, 테스트 2 |
| subtitle_align·audio_service·render_io | 대체 | v2.0.0 에서 삭제됨. `main.py` 4개 서브커맨드는 LegacyRemovedError |
| bundle_service·io | 개조 | Phase 9 범위 |
| workers/base_llm_worker | 유지·확장 | 프롬프트 파일 로드(prompt_loader) 있음. 이미지 입력·재요청 1회는 6.9 |
| workers/tts_backends (376줄) | 개조 | with-timestamps·정렬 저장은 Phase 4 에서 `script/tts/{elevenlabs,edge,align}.py` 로 새로 만들었다. `workers/tts_backends.py` 는 저장소 코드 어디서도 import 하지 않는다(참고 코드 주석 1곳만) → P2 삭제 후보 |

## 5. xfail 2건

| 테스트 | 위치 | 해제 조건 | 실측 차이(착수 전 결정 필요 후보) |
|---|---|---|---|
| `test_c_corrupt_manifest_is_error` | `tests/anti_inertia/test_no_silent_fallback.py:35` | `command_center.load_project_state(pid, cfg)` 신설, 손상 manifest → `orchestrator.errors.ManifestCorruptError` | 없음. 함수·예외 신설만 |
| `test_hormuz_preview_provenance` | `tests/anti_inertia/test_provenance_e2e.py:31` | `engine.render <proj> --preview golden` → `out/provenance.json` features_used 일치, drops [] | ① `--preview golden` 인자 없음(auto·초 목록만) ② preview 는 provenance 를 쓰지 않는다(mux 만) ③ 기대 `badges: 9` ↔ Phase 6.5 provenance `badges: 8`(person 3·flag 4·emblem 1). 나머지 키(camera_moves 5·dips 4·panels 5종·media 2/2/1/2·label_lod true·drops [])는 일치 |

③은 기대값(19 부록 B)과 실측이 다르다. 테스트 기대값을 고칠지, 뱃지 집계 방식을 볼지 착수 때 decision_request 대상이다.

## 6. 착수 전 확인할 쟁점 (지침·결정 대기)
1. 옛 → 새 상태 대응(§1 초안)과 intake·source 서비스의 상태 이관 범위(6.95 와 경계).
2. `engine.validate` 를 6.8 에서 만들지(스키마·레지스트리·예약영역 검사만) 6.9 로 둘지.
3. test_provenance_e2e 의 preview 경로(§5 ①②)와 badges 기대값(③).
4. tts_lint·tts_pronounce 병합 시점 — bundle/text.py 가 의존(Phase 9 와 경계).
