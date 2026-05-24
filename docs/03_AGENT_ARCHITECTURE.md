<!--
tier: 2
last_synced_with: v0.12.0
ssot_for: [agent-catalog, worker-catalog]
depends_on: [02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-05-23
-->

# 03 — Agent & Worker Architecture

## 1. Agent vs Worker

| 구분 | Agent | Worker |
|---|---|---|
| 실행 형태 | in-process 함수 호출 | subprocess (CLI) |
| 입력 | dict/Pydantic | argparse → JSON |
| 출력 | Pydantic 객체 | task_result_{id}.json |
| 사용자 상호작용 | ❌ (Orchestrator 경유) | ❌ (task_result.status로 신호) |
| 병렬화 | 보통 직렬 | Worker Slot 단위 병렬 |
| LLM 사용 | 보통 사용 | 보통 사용 안 함 |

## 2. Agent 카탈로그

| Agent | 파일 | 입력 | 출력 | LLM | Phase |
|---|---|---|---|---|---|
| Dynamic Intake Planner | `workers/intake_planner_worker.py` (BaseLLMWorker) | project_manifest.json (title/category/duration/summary) | `01_intake/intake_plan.json` | ✅ | 3 |
| Source Registry Builder | `agents/source_registry_builder.py` | source_intake + task results | `source_registry.json` | ❌ | 5 |
| Research Agent | `workers/research_worker.py` (BaseLLMWorker) | source_registry + manifest.initial_links | `04_research/research_dossier.json` | ✅ | 6A |
| Evidence Guard | `agents/evidence_guard.py` | research_dossier | `qa_evidence_report.json` | ✅ | 6 |
| Script Agent | `workers/script_worker.py` (BaseLLMWorker) | research_dossier | `05_script/full_script.json` | ✅ | 6 (수직 슬라이스: blueprint 흡수) |
| Scene Planner | `orchestrator/scene_builder.py` (V2 결정론적) / 추후 LLM | full_script | `06_scene/scene_manifest.json` | ❌ (V2 슬라이스, LLM 추후) | 6 (수직 슬라이스 V2) |
| Thumbnail Agent | `agents/thumbnail_agent.py` | full_script + project_manifest | `thumbnail_brief.json` | ✅ | 10 |
| YouTube Metadata Agent | `agents/youtube_metadata_agent.py` | full_script + thumbnail | `youtube_metadata.json` | ✅ | 11 |

## 3. Worker 카탈로그

| Worker | 파일 | 입력 | 출력 | parallelizable | Phase |
|---|---|---|---|---|---|
| Dummy Worker | `workers/dummy_worker.py` | task spec | `task_result_*.json` | ✅ | 1 |
| Intake Planner | `workers/intake_planner_worker.py` | project_manifest.json | `01_intake/intake_plan.json` | ❌ (LLM 호출, slot 1개) | 3 |
| Video Acquisition | `workers/video_acquisition_worker.py` | url + rights flag | mp4 clip + manifest 행 | ✅ | 7 |
| Article Capture | `workers/article_capture_worker.py` | url | png screenshot + manifest 행 | ✅ | 7 |
| X Source Card | `workers/x_card_worker.py` | tweet metadata | png card | ✅ | 7 |
| Telegram Source Card | `workers/telegram_card_worker.py` | tg msg metadata | png card | ✅ | 7 |
| Translation | `workers/translation_worker.py` | text + lang | translated text | ✅ | 7 |
| Terminology | `workers/terminology_worker.py` | text | normalized text | ✅ | 7 |
| Map | `workers/map_worker.py` | map spec | png/mp4 + manifest 행 | ✅ | 7 |
| Earthquake | `workers/earthquake_worker.py` | epicenter + magnitude | map+chart pair | ✅ | 7 |
| Chart | `workers/chart_worker.py` | data + chart spec | png + manifest 행 | ✅ | 7 |
| Annotation | `workers/annotation_worker.py` | source asset + annotation spec | png overlay | ✅ | 7 |
| TTS | `workers/tts_backends.py` + `orchestrator/audio_service.py` (V4) | full_script segments | wav + `08_audio/audio_manifest.json` | ❌ (engine rate limit) | 8 (V4: backend 교체 local/elevenlabs/stub) |
| TTS QA | `workers/tts_qa_worker.py` | wav + original text | `tts_qa_report.json` | ✅ | 8 |
| Music | `workers/music_worker.py` | mood + duration | wav loop | ✅ | 8 |
| Remotion Job Builder | `workers/remotion_job_builder.py` | scene + asset + audio manifests | `remotion_job_*.json` | ❌ | 9 |
| Render | `workers/render_worker.py` | remotion_job.json | mp4 | ❌ (heavy) | 9 |
| FFmpeg | `workers/ffmpeg_worker.py` | input(s) | mp4/aac | ✅ | 9 |

## 4. BaseWorker 계약

> **LLM 호출이 필요한 Worker 는 BaseWorker 가 아니라 `BaseLLMWorker` 를 상속해야 합니다.**
> §4.5 와 [ADDENDUM_04](ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md) 를 참조하십시오.
> Agent 카탈로그(§2) 의 "LLM ✅" 항목들은 본 시스템에서 **모두 `BaseLLMWorker` 기반 Worker 로 구현**됩니다.
> ("Agent" 는 도메인 역할명, "Worker" 는 구현 형태. LLM 활용은 구독 CLI subprocess 만 허용 — ADDENDUM_04 §2.1)

모든 Worker는 `workers/base_worker.py:BaseWorker`를 상속하고 다음을 구현합니다.

```python
class BaseWorker(ABC):
    worker_name: str
    task_type: str

    def parse_args(self) -> WorkerArgs: ...
    def load_inputs(self, args: WorkerArgs) -> Inputs: ...
    @abstractmethod
    def run(self, inputs: Inputs) -> TaskResult: ...
    def write_result(self, result: TaskResult) -> None: ...
    def main(self) -> int: ...
```

Worker 실행 진입점:

```bash
python -m workers.{worker_module} \
  --project-id {pid} \
  --task-id {tid}
```

Worker는 종료 코드로 결과를 전달합니다.
- `0`: 성공 → status=completed
- `2`: 사용자 입력 필요 → status=needs_user_upload / needs_user_confirmation
- `3`: 권리 검토 필요 → status=rights_review_required
- `1` (기타): 실패 → status=failed

## 4.5 BaseLLMWorker 계약 (구독 LLM Bridge)

LLM 호출이 필요한 Worker 는 `workers/base_llm_worker.py:BaseLLMWorker` 를 상속합니다.
본 절은 인터페이스 요약만 두고, 정식 명세는 [ADDENDUM_04](ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md) 입니다.

```python
class BaseLLMWorker(BaseWorker):
    llm_backend: Literal["claude", "codex"]   # 구독 인증된 CLI
    llm_mode: Literal["response", "agent"]    # one-shot JSON / 도구 사용 모드
    system_prompt: str

    def build_user_prompt(self, task) -> str: ...
    def parse_response(self, raw_text: str) -> VersionedModel: ...
    # _invoke_llm / _log_llm_call 은 base 가 제공
```

**핵심 강제**:

- LLM API 키 (`ANTHROPIC_API_KEY` 등) 를 코드/환경변수에 두지 않는다.
- `anthropic` / `openai` SDK 를 requirements 에 추가하지 않는다.
- 모든 LLM 호출은 사용자 머신의 **구독 인증된 CLI subprocess** (`claude`, `codex`) 로만 수행한다.
- 모든 LLM 호출은 `projects/{pid}/llm_calls/{call_id}.json` 으로 영속화한다.

위 강제는 GOAL.md G4 와 동등한 강제력으로 운용됩니다 (위반 시 PR 차단).

### 4.5.1 호출 모드

| 모드 | 의미 | 적용 |
|---|---|---|
| `response` | one-shot JSON 응답, 도구 사용 없음 | intake planner, research, script, scene planner, thumbnail brief, youtube metadata |
| `agent` | CLI 가 파일 IO·외부 명령 사용, task_result.json 까지 직접 작성 | source collector 류 복합 작업 |

### 4.5.2 백엔드 선택 가이드

| 작업 | 추천 |
|---|---|
| 한국어 자연어 (intake, script) | `claude` |
| 구조화 JSON one-shot | `claude` |
| 코드/셸 생성 | `codex` |
| 다국어 cross-check | A/B |

(강제 아님, 각 Worker 가 선택.)

## 5. 새 Worker 추가 절차

[WORKFLOWS.md W3](../WORKFLOWS.md#w3-worker-추가) 참조.
