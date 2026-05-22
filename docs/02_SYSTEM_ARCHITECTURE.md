<!--
tier: 2
last_synced_with: v0.3.0
ssot_for: [system-architecture, component-boundaries]
depends_on: [03_AGENT_ARCHITECTURE.md, 05_DATA_SCHEMA_SPEC.md, ADDENDUM_01_ORCHESTRATOR_COMMAND_CENTER_LAYOUT.md]
last_review: 2026-05-19
-->

# 02 — System Architecture

## 1. 컴포넌트 지도

```
+----------------------------------------------+
|     Orchestrator Command Center (TUI)        |
|  (orchestrator/command_center.py)            |
|                                              |
|  +-----------+ +----------+ +-------------+  |
|  | Orch CLI  | | Job Dash | | Worker Slot |  |
|  | Log Panel | | board    | | 1..N Panels |  |
|  +-----------+ +----------+ +-------------+  |
+----------------------+-----------------------+
                       |
              spawns subprocess
                       v
+-----------+ +-----------+ +-----------+ +-----+
|  Worker   | |  Worker   | |  Worker   | |  ...|
|  CLI #1   | |  CLI #2   | |  CLI #3   | |     |
+-----+-----+ +-----+-----+ +-----+-----+ +-----+
      \           |           /
       \          |          /
        v         v         v
    +----------------------------+
    |   Project FS (JSON SSOT)   |
    |   projects/{project_id}/   |
    +----------------------------+
                ^
                |
    +----------------------------+
    |   Agents (in-process)      |
    |   리서치·대본·scene·썸네일 |
    +----------------------------+
```

## 2. 책임 분리

| 컴포넌트 | 책임 | 금지사항 |
|---|---|---|
| Orchestrator | 상태 전이, task 배정, 사용자 입력 수집, Review Gate 처리, 파일 시스템 쓰기 권한 보유 | 도메인 자산 직접 생성 금지 |
| Agent | 주제 분석·논증 구조화·대본·scene 설계 (인지형, 단발 실행) | 사용자와 직접 대화 금지 |
| Worker | 단일 산출물 생성 (subprocess 실행) | 다른 Worker 산출물 수정 금지, 사용자 질문 금지 |
| TUI | 표시·입력 캡처만 | 비즈니스 로직 금지 |
| Schemas | Pydantic 모델 SSOT | I/O 금지 |

## 3. 데이터 흐름 (한 프로젝트의 생애주기)

```
user command
  → project_manifest.json (created)
  → intake_plan.json (by Dynamic Intake Planner agent)
  → user opens Dynamic Intake Page (web/intake_page_app.py)
  → source_intake.json (user submitted)
  → task_queue.json (by Orchestrator)
  → Worker subprocesses
  → task_result_{id}.json (per task)
  → source_registry.json
  → source_completeness_report.json  ─── Review Gate 2
  → research_dossier.json, argument_map.json
  → episode_blueprint.json           ─── Review Gate 3
  → full_script.json                 ─── Review Gate 4
  → scene_manifest.json (with worker_provenance)
  → asset_manifest.json              ─── Review Gate 5
  → narration_segments.json + audio_manifest.json
  → tts_qa_report.json
  → music_manifest.json
  → remotion_job_debug.json  → draft_debug.mp4   ─── Review Gate 6
  → remotion_job_preview.json → draft_preview.mp4 ─── Review Gate 7
  → thumbnail_manifest.json  → thumbnail.png      ─── Review Gate 8
  → remotion_job_final.json  → final.mp4          ─── Review Gate 9
  → youtube_metadata.json
```

## 4. 상태 머신 (project_manifest.current_state)

```
created
  → intake_planning
  → intake_pending_user
  → source_collecting
  → source_completeness_review
  → research_in_progress
  → blueprint_review
  → script_writing
  → script_review
  → scene_planning
  → asset_production
  → scene_review
  → audio_production
  → render_debug
  → debug_review
  → render_preview
  → preview_review
  → thumbnail_production
  → thumbnail_review
  → render_final
  → final_review
  → publish_ready
  → published
  → archived
```

각 상태 전이는 `orchestrator/state_machine.py`가 강제합니다. 임의 점프 금지.

## 5. 동시성 모델

- **단일 이벤트 루프**: TUI 메인 스레드의 asyncio loop.
- **Worker 실행**: `asyncio.create_subprocess_exec`로 비동기 subprocess.
- **Log Router**: 각 worker subprocess의 stdout/stderr를 별도 task가 read.
- **Worker Slot**: `worker_slots.json`을 단일 쓰기자 (Orchestrator)만 갱신.
- **Agent**: 동기 호출. 필요 시 `asyncio.to_thread`로 escape.

## 6. 외부 의존

| 외부 시스템 | 용도 | 대안 |
|---|---|---|
| Remotion (Node 20) | 영상 렌더링 | `npm run build` 호출, JSON manifest 전달 |
| FFmpeg | 영상 합치기·트랜스코딩 | `workers/ffmpeg_worker.py` |
| Anthropic / OpenAI API | Agent LLM 호출 | `agents/*.py`에서 사용. 키는 .env |
| yt-dlp | X / TG 영상 다운로드 | `workers/video_acquisition_worker.py` |
| Playwright | 기사 캡처 | `workers/article_capture_worker.py` |
| Google Maps Tiles | 지도 (약관 검토 필요) | 대체로 OpenStreetMap |
| TTS Engine | 음성 합성 | 별도 결정 (Phase 8) |

## 7. 파일 시스템 SSOT

모든 도메인 상태는 `projects/{project_id}/` 아래의 JSON에 살아 있습니다.
프로세스 인메모리 상태는 휘발성으로 간주합니다. 재기동 시 JSON에서 복구합니다.

상세 구조: [docs/05_DATA_SCHEMA_SPEC.md](05_DATA_SCHEMA_SPEC.md)
