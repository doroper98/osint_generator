<!--
tier: 2
last_synced_with: v4.0.0
ssot_for: [official-terminology]
depends_on: []
last_review: 2026-09-29
-->

# ADDENDUM 03 — Official Terminology

본 문서는 본 프로젝트에서 사용하는 공식 용어의 단일 정의 출처(SSOT)입니다.

| 용어 | 정의 |
|---|---|
| **Dynamic Intake Page** | 주제별로 동적으로 생성되는 자료 입력 페이지. 고정 폼이 아니다. |
| **Pre-production Debug Layer** | (v2.0.0 폐기) v1 디버그 오버레이. 추적은 프리뷰 시트·`checks.json`·`provenance.json`이 맡는다. |
| **Orchestrator Command Center Layout** | Orch CLI / Job Dashboard / Worker Slot 패널이 한 TUI에 모인 운영 화면. 방식 B. |
| **Orch CLI** | 파이프라인 전체를 지휘하는 Orchestrator CLI. 단일 인스턴스. |
| **Worker CLI** | Orch CLI 지시에 따라 단일 task를 수행하는 subprocess 기반 CLI. |
| **Worker Slot** | Worker CLI subprocess가 배정되어 실행되는 논리적 슬롯. 기본 4개. |
| **Job Dashboard** | 전체 작업 현황판. queued/running/done/failed/대기 사용자 등을 표시. |
| **소스 레코드 / claims** | 소스 정규화 기록 `intake/sources.json`과 주장·근거·검증 status `intake/claims.json`(v3.2.0 — 옛 `source_registry.json` 대체). |
| **AI Delegation** | 특정 자료 항목을 AI에게 위임하는 사용자 선택. |
| **Task Queue** | Orch CLI가 Worker CLI에 배정할 작업 목록. `task_queue.json`. |
| **Task Result** | Worker CLI가 완료 후 남기는 결과. `task_result_*.json`. |
| **Source Verify** | 인용 대조로 claim status를 코드가 정하는 단계(`SOURCE_VERIFY`, D50). 옛 Source Completeness Check 대체. |
| **provenance** | 이번 영상에 실제로 쓰인 기능·규칙·프롬프트 해시·drops 기록 `provenance.json`(15 P5). 옛 Scene Provenance 대체. |
| **승인 게이트** | 사람이 승인·반려하는 지점. 2개 — ① `SCRIPT_APPROVAL` ② `PREVIEW_APPROVAL`(v3.0.0). |
| **출력 프로파일** | 렌더 해상도·인코딩 한 벌(`config.yaml engine.output`, 트라이얼 480p·최종 1080p). 옛 Render Mode 대체. |
| **프리뷰 / 결정적 검사** | `engine.render --preview` 컷·시트와 `prev/checks.json`(12항목). |
| **시각 검수 루프** | AI 연출 판을 시각 검수 워커가 보고 수정 워커가 고치는 반복(상한은 규칙). |
| **장치 변환** | 설계 854×480 좌표를 출력 해상도로 옮기는 렌더 진입 변환 한 곳(D60). |
| **게시물(post) 카드·기사 카드** | X 게시물·기사를 영상 안에 자체 조판한 카드(캡처 이미지 아님, handoff 18 §5·14 §9). |
| **Video Source Frame** | X/TG 원본 영상 클립을 액자처럼 배치하는 컴포넌트. |
| **Annotation Layer** | 빨간 형광펜·밑줄·동그라미·화살표 강조 레이어. |
| **발음 린트 / 오디오 QA** | 발음 텍스트 규칙 검사(`script/lint.py`)와 최종 음량·음악 레벨 측정(`audio/qa.py`). |
| **Thumbnail System** | 썸네일 기획/생성/QA/승인을 다루는 하위 시스템. |

## 동의어 / 금지 동의어

| 권장 | 비권장 |
|---|---|
| Worker Slot | "Worker Window" (방식 B에서는 창이 아님) |
| Orch CLI | "메인 컨트롤러", "Master CLI" |
| `final.mp4` | "release.mp4" |
| 승인 게이트 | "Review Gate 9개", "Checkpoint" |

문서·코드·커밋 메시지·UI 라벨은 모두 위 권장 용어를 사용합니다.
