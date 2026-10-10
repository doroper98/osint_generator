<!--
tier: 2
last_synced_with: v5.13.0
ssot_for: [orchestrator-command-center-layout, method-b]
depends_on: [02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-09-29
-->

# ADDENDUM 01 — Orchestrator Command Center Layout

> **방식 B 확정.** Windows Terminal split-pane이 아니라, **하나의 Python Textual TUI 안에서** Orch CLI, Job Dashboard, Worker Slot 패널을 모두 표시한다.

## 1. 화면 구조

```
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│ Orch CLI Log Panel           │ Worker Slot 1                │ Worker Slot 2                │
│ (project state transitions,  │ assigned_worker | task_id    │ assigned_worker | task_id    │
│  approvals, gate signals)    │ stdout/stderr live           │ stdout/stderr live           │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Job Dashboard Panel          │ Worker Slot 3                │ Worker Slot 4                │
│ queued / running / done /    │ assigned_worker | task_id    │ assigned_worker | task_id    │
│ failed / waiting_user        │ stdout/stderr live           │ stdout/stderr live           │
│ current_gate / next_action   │                              │                              │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

- 왼쪽 상단: Orch CLI Log Panel
- 왼쪽 하단: Job Dashboard Panel
- 오른쪽: Worker Slot 1–N (기본 4, `config.yaml:worker_slot_count`로 변경)

## 2. Worker Slot 동작

`status ∈ {idle, assigned, running, completed, failed, waiting_user, stale}`

- Orch CLI는 `task_queue.json`에서 실행 가능한 task를 찾는다.
- `depends_on` 충족된 task만 실행 가능.
- `parallelizable=true`이면 빈 Worker Slot에 배정.
- `parallelizable=false`이면 직렬 실행 (다른 Slot 비어도 대기).
- 한 Worker subprocess는 한 Slot에 1:1 매핑.

## 3. Log Router

```
Worker subprocess
   ├── stdout ──→ Log Router ──→ Slot Panel (live) + logs/workers/{task_id}.log
   └── stderr ──→ Log Router ──→ Slot Panel (red) + logs/workers/{task_id}.log
```

라우터 책임:
- subprocess stdout을 비동기 read
- 패널과 파일에 동시 기록
- 에러 패턴 감지 (regex 기반, 추후 강화)
- heartbeat 누락 감지 (60초 무응답 → `stale`)
- 종료 코드 기록

## 4. Worker가 사용자에게 직접 질문하지 않는다

Worker가 판단 보류가 필요하면:

```python
return TaskResult(
    status="needs_user_confirmation",
    warnings=["X 영상 다운로드 실패. 사용자 업로드 필요"],
    ...
)
```

Orch CLI가 이 결과를 보고 다음 상태로 가거나 승인 게이트(①②)를 연다.

## 5. 구현 라이브러리

- **Textual** (메인 TUI 프레임워크) — 비동기 위젯, 동적 레이아웃
- **Rich** (보조) — 표, 로그 패널 렌더링, 색상

## 6. 파일 매핑

| 파일 | 역할 |
|---|---|
| `orchestrator/command_center.py` | 진입점 (CLI 인자 파싱 → TUI 시작) |
| `orchestrator/tui_app.py` | Textual `App` 정의, 4 + 2 패널 배치 |
| `orchestrator/worker_slot_manager.py` | Slot 상태 갱신, subprocess 생성 |
| `orchestrator/log_router.py` | stdout/stderr 비동기 라우팅 |
| `orchestrator/dashboard.py` | Job Dashboard 표시용 집계 |
| `orchestrator/config.py` | `config.yaml` 로더 |

## 7. 키 바인딩 (Phase 1)

| 키 | 동작 |
|---|---|
| `q` | 종료 (active worker는 안전 종료 시도) |
| `r` | task_queue.json 다시 읽기 |
| `1`–`4` | 해당 Worker Slot 포커스 |
| `s` | worker_slots.json 강제 저장 |
| `f5` | dashboard 새로고침 |

## 8. 운영 상수 (config.yaml)

```yaml
command_center:
  worker_slot_count: 4
  heartbeat_timeout_sec: 60
  log_panel_max_lines: 500
  log_router_read_chunk: 1024
```
