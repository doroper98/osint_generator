<!--
tier: 2
last_synced_with: v5.2.0
ssot_for: [system-architecture, component-boundaries]
depends_on: [03_AGENT_ARCHITECTURE.md, 05_DATA_SCHEMA_SPEC.md, ADDENDUM_01_ORCHESTRATOR_COMMAND_CENTER_LAYOUT.md]
last_review: 2026-09-29
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
    |   엔진 CLI (결정적 코드)    |
    |   script·geo·engine·audio  |
    +----------------------------+
```

썸네일 시스템은 v2 파이프라인에 없다(v4.0.0 삭제 — v1 명세 docs/11·`ThumbnailManifest`, 보존 `archive/hyperframes-briefing`). 필요하면 텔레그램·업로드처럼 별도 계획으로 다룬다(handoff 13 범위 밖 절).

v4.0.0: LLM 역할(소스 판독·검증 초안·리서치·원고·연출·시각 검수)은 모두 `workers/*_worker.py`(BaseLLMWorker, 구독 CLI 서브프로세스)다.
영상 제작은 엔진 CLI(`orchestrator/engine_service.py` 가 서브프로세스로 호출, [10](10_RENDERING_PIPELINE_SPEC.md) §1)다. in-process Agent 층은 없다.

## 2. 책임 분리

| 컴포넌트 | 책임 | 금지사항 |
|---|---|---|
| Orchestrator | 상태 전이, task 배정, 사용자 입력 수집, 승인 게이트 2개 처리, 파일 시스템 쓰기 권한 보유(엔진 입력 파일 제외, P1) | 도메인 자산 직접 생성 금지 |
| LLM 워커 | 소스 판독·claim 후보·사실 목록·원고·연출·시각 검수·연출 수정([03](03_AGENT_ARCHITECTURE.md) §2) | 사용자와 직접 대화 금지, 검증 status·수치·좌표 결정 금지(P8) |
| 엔진 CLI | 린트·음성·지오·렌더·검사·믹스·먹싱·provenance([10](10_RENDERING_PIPELINE_SPEC.md)) | LLM 호출 금지, 엔진 입력 파일을 오케스트레이터가 쓰지 않음(P1) |
| Worker | 단일 산출물 생성 (subprocess 실행) | 다른 Worker 산출물 수정 금지, 사용자 질문 금지 |
| TUI | 표시·입력 캡처만 | 비즈니스 로직 금지 |
| Schemas | Pydantic 모델 SSOT | I/O 금지 |

## 3. 데이터 흐름 (한 프로젝트의 생애주기)

```
user command
  → project_manifest.json (created)
  → intake_plan.json (by Dynamic Intake Planner agent)
  → user opens Dynamic Intake Page (web/intake_page_app.py)
  → intake/sources.json (v3.2.0 — add-source·웹 소스 넣기, X 캡처는 CaptureReadWorker 초안,
                          사용자 확인 confirm-source 후 submit-intake: intake → source_verify)
  → intake/verify_draft.json (VerifySourcesWorker) → intake/claims.json (코드 판정 source_verify.judge)
  → facts.json (ResearchWorker, verify-sources → build-research: source_verify → research)
  → script.yaml (ScriptWorker)                        ─── ★ 게이트 ① SCRIPT_APPROVAL
  → plan.json + tts/ (script.plan)
  → assets/ (geo.prep, 권리 레지스트리·크레딧)
  → direction.yaml (DirectorWorker 또는 사람)
  → prev/{sheet.jpg, checks.json, frames.json, qa_verdict.v*.json, qa_loop.json} (engine.render --preview, 시각 검수 루프)
                                                        ─── ★ 게이트 ② PREVIEW_APPROVAL
  → out/video_noaudio.mp4 (engine.render) → out/mix.f32 (audio.mix)
  → out/{final.mp4, final.srt, description.txt, provenance.json} (engine.mux)
```

## 4. 상태 머신 (project_manifest.current_state)

v3.0.0 (docs/handoff/16 §2, back_and_forth D-0040) — 옛 24개 상태는 삭제했다. manifest `schema_version` 2,
옛(v1) manifest 는 변환하지 않고 "재생성 필요" 오류다.

```
created → intake → source_verify → research → script_draft
  → script_approval ★ 승인 게이트 ①
  → voice_timeline → assets → direction → preview_qa
  → preview_approval ★ 승인 게이트 ②
  → render → audio_mix → deliver → done
```

역전이(반려, 사유 필수): script_approval → script_draft / preview_approval → direction · script_draft · assets.
게이트에서 나가는 전이는 `approve` / `reject` 로만 한다. 엔진 상태(voice_timeline~deliver)는 `advance` 가
`orchestrator/engine_service.py`(엔진 CLI 어댑터)로 단계를 돌리고, 실패·drops 면 그 상태에 머문다.
전이 규칙은 `orchestrator/state_machine.py`, 진행은 `orchestrator/pipeline.py` 가 강제한다. 임의 점프 금지.

## 5. 동시성 모델

- **단일 이벤트 루프**: TUI 메인 스레드의 asyncio loop.
- **Worker 실행**: `asyncio.create_subprocess_exec`로 비동기 subprocess.
- **Log Router**: 각 worker subprocess의 stdout/stderr를 별도 task가 read.
- **Worker Slot**: `worker_slots.json`을 단일 쓰기자 (Orchestrator)만 갱신.
- **Agent**: 동기 호출. 필요 시 `asyncio.to_thread`로 escape.

## 6. 외부 의존

| 외부 시스템 | 용도 | 비고 |
|---|---|---|
| cairo(pycairo) · numpy · Pillow | 프레임 렌더 | `requirements-engine.txt` |
| FFmpeg | 인코딩·먹싱·2패스 loudnorm·클립 추출 | 시스템 바이너리 |
| fontconfig + 프로젝트 글꼴 | 글자 렌더(대체 글꼴 금지) | `tools/fetch_data.py fonts` |
| Natural Earth · terrarium 타일 | 국경·라벨·지형 | `tools/fetch_data.py ne tiles`, 캐시 `data/geo/` |
| 위키미디어 Commons | 인물·휘장·국기·미디어 원본 | `tools/commons_fetch.py`, `tools/media_fetch.py`(429 대책) |
| edge-tts · ElevenLabs | 음성 합성·정렬 | `config.yaml tts`, 키는 `.env` |
| `claude` / `codex` CLI(구독) | LLM 워커 | ADDENDUM_04. API SDK 금지 |
| Google Maps | 쓰지 않음 | 약관 검토 전 상업 고정 사용 금지(G4-11) |

## 7. 파일 시스템 SSOT

모든 도메인 상태는 `projects/{project_id}/` 아래의 JSON에 살아 있습니다.
프로세스 인메모리 상태는 휘발성으로 간주합니다. 재기동 시 JSON에서 복구합니다.

상세 구조: [docs/05_DATA_SCHEMA_SPEC.md](05_DATA_SCHEMA_SPEC.md)
