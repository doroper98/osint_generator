<!--
tier: 2
last_synced_with: v0.1.2
ssot_for: [official-terminology]
depends_on: []
last_review: 2026-05-19
-->

# ADDENDUM 03 — Official Terminology

본 문서는 본 프로젝트에서 사용하는 공식 용어의 단일 정의 출처(SSOT)입니다.

| 용어 | 정의 |
|---|---|
| **Dynamic Intake Page** | 주제별로 동적으로 생성되는 자료 입력 페이지. 고정 폼이 아니다. |
| **Pre-production Debug Layer** | `draft_debug.mp4`에만 표시되는 디버그 오버레이. scene 추적용. |
| **Orchestrator Command Center Layout** | Orch CLI / Job Dashboard / Worker Slot 패널이 한 TUI에 모인 운영 화면. 방식 B. |
| **Orch CLI** | 파이프라인 전체를 지휘하는 Orchestrator CLI. 단일 인스턴스. |
| **Worker CLI** | Orch CLI 지시에 따라 단일 task를 수행하는 subprocess 기반 CLI. |
| **Worker Slot** | Worker CLI subprocess가 배정되어 실행되는 논리적 슬롯. 기본 4개. |
| **Job Dashboard** | 전체 작업 현황판. queued/running/done/failed/대기 사용자 등을 표시. |
| **Source Registry** | 모든 소스의 정규화 등록부. `source_registry.json`. |
| **AI Delegation** | 특정 자료 항목을 AI에게 위임하는 사용자 선택. |
| **Task Queue** | Orch CLI가 Worker CLI에 배정할 작업 목록. `task_queue.json`. |
| **Task Result** | Worker CLI가 완료 후 남기는 결과. `task_result_*.json`. |
| **Source Completeness Check** | 영상 제작에 필요한 소스가 충분한지 판단하는 단계. |
| **Scene Provenance** | scene이 어떤 Worker·source·asset·manifest에서 왔는지 추적 데이터. |
| **Review Gate** | 사용자가 중간 산출물을 승인하거나 수정 요청하는 검수 지점. 9개. |
| **Render Mode** | `debug` / `preview` / `final` 중 하나. |
| **Source Card** | X/TG/기사 핵심 내용을 영상 안에 재구성한 카드. |
| **Video Source Frame** | X/TG 원본 영상 클립을 액자처럼 배치하는 컴포넌트. |
| **Annotation Layer** | 빨간 형광펜·밑줄·동그라미·화살표 강조 레이어. |
| **TTS Pronunciation QA** | TTS 발음 오류 검수·수정 단계. ASR 재인식 기반. |
| **Thumbnail System** | 썸네일 기획/생성/QA/승인을 다루는 하위 시스템. |

## 동의어 / 금지 동의어

| 권장 | 비권장 |
|---|---|
| Worker Slot | "Worker Window" (방식 B에서는 창이 아님) |
| Orch CLI | "메인 컨트롤러", "Master CLI" |
| Pre-production Debug Layer | "Debug Watermark" (워터마크 아님) |
| `final.mp4` | "release.mp4" |
| `draft_debug.mp4` | "internal.mp4" |
| `draft_preview.mp4` | "review.mp4" |
| Review Gate | "Checkpoint" |

문서·코드·커밋 메시지·UI 라벨은 모두 위 권장 용어를 사용합니다.
