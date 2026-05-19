<!--
tier: 2
last_synced_with: v0.1.5
ssot_for: [review-gates, qa-policy]
depends_on: [05_DATA_SCHEMA_SPEC.md, ../GOAL.md]
last_review: 2026-05-19
-->

# 12 — QA & Review Spec

## 1. 9개 Review Gate

| # | Gate ID | 검수 대상 | 산출 |
|---|---|---|---|
| 1 | `intake_review` | `intake_plan.json` | 사용자 자료 수집 진입 승인 |
| 2 | `source_completeness_review` | `source_completeness_report.json` | 부족 자료 보완 또는 계속 진행 |
| 3 | `blueprint_review` | `episode_blueprint.json` | 챕터 구조 승인 |
| 4 | `script_review` | `full_script.json` | 대본 승인 |
| 5 | `scene_review` | `scene_manifest.json` + `asset_manifest.json` | scene 설계 승인 |
| 6 | `draft_debug_review` | `draft_debug.mp4` | Worker 품질 점검 |
| 7 | `draft_preview_review` | `draft_preview.mp4` | 사용자 시청 검수 |
| 8 | `thumbnail_review` | `thumbnail_manifest.json` | 썸네일 선택 |
| 9 | `final_review` | `final.mp4` + `youtube_metadata.json` | 업로드 직전 최종 승인 |

## 2. 승인 로그 (`approval_log.json`)

각 Gate 이벤트 1행:

| 필드 | 설명 |
|---|---|
| `gate_id` | 위 표의 ID |
| `artifact_refs` | 검수 대상 파일 경로 |
| `status` | `approved` / `revision_requested` / `rejected` |
| `user_comment` | 자유 텍스트 |
| `approved_at` | ISO 8601 UTC |
| `revision_requested` | bool |
| `revision_notes` | 수정 요청 상세 |

**append-only**. 과거 항목 수정 금지.

## 3. QA Evidence Report

`qa_evidence_report.json`은 모든 주장-근거 페어를 정리한다.

| 필드 | 설명 |
|---|---|
| `claim_id` | 주장 ID |
| `claim_text` | 대본 안 문장 |
| `claim_type` | `<확인>` / `<추론>` / `<미검증>` / `<반박됨>` |
| `evidence_source_ids` | 근거 소스 |
| `cross_check` | 다른 출처 일치 여부 |
| `confidence` | low / medium / high |

## 4. 라벨 시각화

[07_VIDEO_STYLE_GUIDE.md §6](07_VIDEO_STYLE_GUIDE.md#6-라벨링-시스템) 참조. Remotion `InferenceBadge.tsx`가 표시.

## 5. 자동 QA (Phase 후속)

| 항목 | 도구 |
|---|---|
| TTS Pronunciation QA | `workers/tts_qa_worker.py` |
| 자막-음성 일치 | ASR 재인식 비교 |
| `final.mp4` Debug Layer 누락 검사 | OCR (Phase 9 후속) |
| 권리 상태 누락 검사 | `source_registry.json` lint |
| 미검증 정보의 제목/썸네일 사용 검사 | regex + Pydantic validator |

## 6. 사용자 거부 시 흐름

1. Gate에서 `revision_requested=true` 기록.
2. Orchestrator는 해당 단계로 상태 되돌림.
3. 관련 Worker 재실행 (또는 Agent 재실행).
4. 같은 Gate 재승인 시도.

## 7. 권리 위반 발견 시

[06_SOURCE_AND_RIGHTS_POLICY.md §9](06_SOURCE_AND_RIGHTS_POLICY.md#9-위반-시-조치) 따른다.
