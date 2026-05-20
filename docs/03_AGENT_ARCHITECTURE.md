<!--
tier: 2
last_synced_with: v0.2.2
ssot_for: [agent-catalog, worker-catalog]
depends_on: [02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-05-19
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
| Dynamic Intake Planner | `agents/dynamic_intake_planner.py` | user command + topic_summary | `intake_plan.json` | ✅ | 3 |
| Source Registry Builder | `agents/source_registry_builder.py` | source_intake + task results | `source_registry.json` | ❌ | 5 |
| Research Agent | `agents/research_agent.py` | source_registry | `research_dossier.json` | ✅ | 6 |
| Evidence Guard | `agents/evidence_guard.py` | research_dossier | `qa_evidence_report.json` | ✅ | 6 |
| Script Agent | `agents/script_agent.py` | research_dossier + blueprint | `full_script.json` | ✅ | 6 |
| Scene Planner | `agents/scene_planner.py` | full_script + asset_manifest | `scene_manifest.json` | ✅ | 6 |
| Thumbnail Agent | `agents/thumbnail_agent.py` | full_script + project_manifest | `thumbnail_brief.json` | ✅ | 10 |
| YouTube Metadata Agent | `agents/youtube_metadata_agent.py` | full_script + thumbnail | `youtube_metadata.json` | ✅ | 11 |

## 3. Worker 카탈로그

| Worker | 파일 | 입력 | 출력 | parallelizable | Phase |
|---|---|---|---|---|---|
| Dummy Worker | `workers/dummy_worker.py` | task spec | `task_result_*.json` | ✅ | 1 |
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
| TTS | `workers/tts_worker.py` | narration segments | wav files | ❌ (engine rate limit) | 8 |
| TTS QA | `workers/tts_qa_worker.py` | wav + original text | `tts_qa_report.json` | ✅ | 8 |
| Music | `workers/music_worker.py` | mood + duration | wav loop | ✅ | 8 |
| Remotion Job Builder | `workers/remotion_job_builder.py` | scene + asset + audio manifests | `remotion_job_*.json` | ❌ | 9 |
| Render | `workers/render_worker.py` | remotion_job.json | mp4 | ❌ (heavy) | 9 |
| FFmpeg | `workers/ffmpeg_worker.py` | input(s) | mp4/aac | ✅ | 9 |

## 4. BaseWorker 계약

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

## 5. 새 Worker 추가 절차

[WORKFLOWS.md W3](../WORKFLOWS.md#w3-worker-추가) 참조.
