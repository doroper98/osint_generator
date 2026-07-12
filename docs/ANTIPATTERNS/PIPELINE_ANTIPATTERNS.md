<!--
tier: 3
last_synced_with: v0.3.3
ssot_for: [pipeline-antipatterns]
depends_on: [../02_SYSTEM_ARCHITECTURE.md, ../ADDENDUM_01_ORCHESTRATOR_COMMAND_CENTER_LAYOUT.md]
last_review: 2026-05-19
-->

# Pipeline Antipatterns

본 문서는 Orchestrator·Worker·Task Queue·Log Router 관련 안티패턴 카탈로그입니다. **append-only**.

각 항목은 [README.md](README.md)의 표준 포맷을 따릅니다.

---

## PIPELINE-AP-001 — Worker가 사용자에게 직접 stdin으로 질문
- **증상**: Worker subprocess가 `input("계속하시겠습니까?")`를 호출 → TUI가 멈춤.
- **나쁜 예**: `confirm = input(...)`
- **좋은 예**: `TaskResult(status="needs_user_confirmation", warnings=["..."])` 반환.
- **자동 조치**: `workers/base_worker.py`가 stdin을 `/dev/null`로 묶어 차단. CI lint로 `input(` 패턴 검사.
- **회귀 테스트**: pending
- **발견 버전**: v0.1.0
- **상태**: active

## PIPELINE-AP-002 — Worker가 task_queue.json을 직접 갱신
- **증상**: Worker가 자기 자신의 status를 task_queue.json에 직접 쓴다 → Orchestrator의 단일 쓰기자 원칙 깨짐.
- **좋은 예**: Worker는 `task_result.json`만 작성. Orchestrator가 task_queue.json을 동기화.
- **자동 조치**: `task_queue.json`은 Orchestrator 프로세스만 쓰기. base_worker가 의도적 검증.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-003 — Worker subprocess hang 시 stale 미감지
- **증상**: 외부 API 호출이 무한 대기하면 Worker Slot이 영원히 running.
- **좋은 예**: heartbeat timeout (config: `command_center.heartbeat_timeout_sec`, 기본 60초) 후 `stale` 전환 + 재배정 옵션.
- **자동 조치**: Worker Slot Manager의 polling.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-004 — depends_on 순환 의존
- **증상**: task A가 B에 의존, B가 A에 의존 → 영원히 queued.
- **자동 조치**: `task_queue.json` 로드 시 토폴로지 정렬로 사이클 검출. 사이클이면 즉시 fail.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-005 — Log Router 패널 버퍼 무제한 증가
- **증상**: 긴 작업의 로그가 TUI 메모리를 잠식.
- **자동 조치**: `command_center.log_panel_max_lines` (기본 500)로 ring buffer.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-006 — Worker Slot finalize 시 terminal 상태 잔존
- **증상**: Worker subprocess 종료 후 slot 상태를 `completed` / `failed` / `waiting_user` 로 두면, 다음 tick 에서 `_find_idle_slot()` 이 None 을 반환하여 후속 task (예: `depends_on` 가 충족된 task) 가 영영 `queued` 로 남는다.
- **나쁜 예**: finalize 시 slot.status 를 `completed`로 유지.
- **좋은 예**: finalize 직후 즉시 `idle` 로 환원. "지금 누가 일하는가" 는 `worker_slots.json`, "누가 무엇을 끝냈는가" 는 `task_queue.json` 으로 책임 분리.
- **자동 조치**: `orchestrator/worker_slot_manager.py:_finalize_slot` 에서 slot.status = `idle` 즉시 적용. 마지막 worker 정보는 stdout 로그가 보존.
- **회귀 테스트**: `tests/orchestrator/test_worker_slot_manager.py::test_chained_depends_on` (Phase 1 후속에서 추가)
- **발견 버전**: v0.1.0 (Phase 1 smoke test 중)
- **상태**: active

## PIPELINE-AP-007 — 사진 자산 바이너리 미전달 + 차트가 사진 밀어냄 (사진 전량 미노출)
- **증상**: 실제 보고서 번들로 영상을 만들면 보도 사진이 하나도 안 나오고 씬이 전부 차트가 된다.
- **재현**: `python hyperframes/scripts/bundle_to_video.py json/analysis_*.bundle.json` → `photos: 0장 사용 / N건 스킵 (…로컬 파일 없음)`.
- **원인 ①(자산 부재)**: agents_reviewer 백필 번들의 이미지 `url` 이 계약(원본 직링크) 대신 로컬 캐시 상대경로(`img/xxx.webp`)였고, 그 바이너리는 osint_generator 로 전달되지 않았다. `fetch_photos` 는 로컬 경로를 **CWD 기준**으로 찾아 전량 "로컬 파일 없음" 스킵.
- **원인 ②(차트 독점)**: `photo` 씬은 4-d 스테이트먼트 승격 한 곳에서만 생성되는데, 그 앞에서 차트 씬이 섹션을 `consumed` 로 소진한다. 사진 2장이 붙은 리드 섹션에 차트가 8~10개면 그 섹션이 차트로 소진되어 사진이 조용히 버려진다.
- **좋은 예**: (①) 자산 확보를 3단계 폴백(직링크 → 번들 디렉토리 기준 로컬 → 원문 페이지 og:image 직접 회수)으로. `source_id`→원문 URL→대표 이미지 회수, `recovered="source_page"` 로 추적. LLM 무호출·결정론 유지. (②) 차트로 소진된 섹션이라도 cleared 사진이 있으면 인접 photo 씬을 별도 추가 (C0 영상미 우선). 섹션당 첫 1장 캡 유지.
- **자동 조치**: `hyperframes/scripts/bundle_to_video.py:fetch_photos` 폴백 + 4-d 씬 빌더 사진 공존. 실번들 5건 + 로컬 데모 1건 실변환으로 검증.
- **회귀 테스트**: pending (실물 검증 방침 — pydantic 미설치 환경이라 실변환 로그로 확인)
- **발견 버전**: v0.44.0 · **상태**: resolved (소비측). producer 가 `url` 을 원본 직링크로 emit 하면 폴백 없이 1단계로 동작.

---

> 새 패턴 발견 시 본 파일 끝에 append. 과거 항목 수정 금지.
