<!--
tier: 2
last_synced_with: v5.1.0
ssot_for: [agent-catalog, worker-catalog]
depends_on: [02_SYSTEM_ARCHITECTURE.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md, docs/handoff/16_ORCHESTRATOR_INTEGRATION.md, docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md]
last_review: 2026-09-29
-->

# 03 — Agent & Worker Architecture

## 1. 역할 경계 (v4.0.0)

| 층 | 형태 | 하는 일 | 하지 않는 일 |
|---|---|---|---|
| 오케스트레이터(`orchestrator/`) | 상태 머신·게이트·얇은 어댑터 | 상태 전이, 워커·엔진 호출, 게이트 기록 | 엔진 입력 파일 쓰기(15 P1), 연출 판단 |
| LLM 워커(`workers/*_worker.py`, `BaseLLMWorker`) | 구독 CLI 서브프로세스(ADDENDUM_04) | 소스 판독·claim 후보·사실 목록·원고·연출·시각 검수·연출 수정 | 검증 status 판정, 수치·좌표 계산, 다른 워커 산출물 수정(C4) |
| 엔진(`engine/`·`script/`·`audio/`·`geo/`, CLI) | 결정적 코드 | 린트·음성·지오·렌더·검사·믹스·먹싱·provenance | LLM 호출, 사용자 질문 |

**P8 경계**: 장면 구성·연출은 LLM+사용자가, 렌더 수치·검증·권리는 코드가 정한다. 코드가 "정규화"로 LLM 구성을 옛 모양으로 되돌리지 않는다.
검증 status는 LLM이 아니라 코드(`orchestrator/source_verify.py`, D50)가, 문장 라벨은 claims status로 코드가 계산한다.
루프 상한·종료도 코드가 정한다(`orchestrator/ai_direction.py`). 각 LLM 단계는 자기 몫의 입력만 본다(15 P9).
프롬프트는 `prompts/{prompt_name}.md` 템플릿 + 규칙 파일에서 온다. 코드 상수 금지(15 P3, `tests/anti_inertia/test_prompts_from_files.py`).

## 2. LLM 워커 카탈로그 (실측 `workers/`)

| 워커 | 파일·클래스 | 프롬프트 | 입력 | 출력 | 상태 |
|---|---|---|---|---|---|
| Intake Planner | `intake_planner_worker.py` `IntakePlannerWorker` | `intake_planner` | manifest(제목·분류·길이·요지) | `intake_plan.json` | INTAKE |
| Capture Read | `capture_read_worker.py` `CaptureReadWorker`(vision) | `capture_read` | `intake/screenshots/<id>.png` + 사용자 메모 | `intake/drafts/<id>.json` → 소스 레코드(사용자 확인 전 검증 불가) | INTAKE |
| Verify Sources | `verify_sources_worker.py` `VerifySourcesWorker` | `verify_sources`(+`verify_sources_hints` 번들 힌트) | 사용자 확인된 `intake/sources.json` + 본문 | `intake/verify_draft.json` → **코드 판정** → `intake/claims.json` | SOURCE_VERIFY |
| Research | `research_worker.py` `ResearchWorker` | `research` | manifest + sources + claims | `facts.json` | RESEARCH |
| Script | `script_worker.py` `ScriptWorker` | `script`(+`script_draft` 번들 초안) | `facts.json` + claims + manifest | `script.yaml`(문장 sources = claim id) | SCRIPT_DRAFT |
| Director | `director_worker.py` `DirectorWorker` | `director`(+`director_bundle` 번들 재료) | script + plan + 엔티티·미디어 레지스트리 + 지오 역량 + 이벤트 필드 표 | `direction.yaml`(+`direction.meta.json`) | DIRECTION |
| Visual QA | `visual_qa_worker.py` `VisualQAWorker`(vision) | `visual_qa` | `prev/sheet.jpg` + `frames.json` + checks 요약 | `prev/qa_verdict.v*.json`(`engine.qa.QAVerdict`) | PREVIEW_QA |
| Revise Direction | `revise_direction_worker.py` `ReviseDirectionWorker` | `revise_direction` | 직전 direction + 판정 + checks + 루프 이력 | 수정 direction + changelog(`engine.qa.Revision`) | PREVIEW_QA |
| Dummy / Dummy LLM | `dummy_worker.py`, `dummy_llm_worker.py` | `dummy` | — | 스모크 테스트용 | — |

- 새 워커를 추가하면 이 표와 `prompts/` 템플릿을 함께 바꾼다(CLAUDE.md C7).
- 번들 어댑터(`bundle/`)는 워커가 아니라 결정적 변환이다. 번들은 재료로만 쓴다(handoff 12 §5, [05](05_DATA_SCHEMA_SPEC.md)).
- 시각 검수 루프·게이트 ② 판정은 [12](12_QA_AND_REVIEW_SPEC.md) §2.

### 2.1 장르 프롬프트 층 — v4.4.0

research·script·director·revise_direction·visual_qa 다섯 프롬프트는 템플릿 끝 표지 `{{GENRE_BLOCK}}` 에 장르 문단(`prompts/genre_<이름>.md`)을 받는다.
문단의 문장은 `rules:genre_prompt`(서술 규칙·데이터 원칙·루브릭 추가 항목·무대별 문법)에서, 켜고 끄는 값은 장르 프로필에서 온다. 코드 문장은 없다(15 P3).
프로젝트 장르의 단일 출처는 주문 `order.yaml`(`schemas/order_models.py`, handoff 20 §11)이다. 주문이 없으면 기본 장르(지정학)이고, 기본 장르는 추가 문단이 없어 프롬프트가 바이트 그대로다.
연출 입력의 `{geo}` 자리는 시간축 무대면 무대 역량(레인·데이터 레코드·원문 문서)이 된다. 원고 입력은 주문 레코드 블록(`{series_block}`)을 받는다.
시각 검수는 장르 영상이면 루브릭 추가 항목을 `rubric[]` 에 항목마다 판정해야 한다(워커가 강제). provenance 는 `genre`·`genre_declared` 를 남긴다.

## 3. 엔진 단계 (워커 아님)

원고 린트·음성·지오·연출 점검·프리뷰·렌더·믹스·먹싱은 워커가 아니라 엔진 CLI다. 단계표는 [10](10_RENDERING_PIPELINE_SPEC.md) §1이다.
v1 계획의 영상·기사·지도·차트·TTS·Remotion·FFmpeg 워커(구 §3 표, v0.3.3)는 만들지 않았거나 v2.0.0에서 삭제됐다. 보존본은 `archive/hyperframes-briefing`.

## 4. BaseWorker 계약

> **LLM 호출이 필요한 Worker 는 BaseWorker 가 아니라 `BaseLLMWorker` 를 상속해야 합니다.**
> §4.5 와 [ADDENDUM_04](ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md) 를 참조하십시오.
> §2 의 LLM 워커는 **모두 `BaseLLMWorker` 기반 Worker 로 구현**됩니다.
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
    llm_mode: Literal["response", "agent", "vision"]    # one-shot JSON / 도구 사용 모드 / 이미지 첨부 읽기(v3.1.0 시각 검수)
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
| `response` | one-shot JSON 응답, 도구 사용 없음 | intake planner, verify_sources, research, script, director, revise_direction |
| `agent` | CLI 가 파일 IO·외부 명령 사용, task_result.json 까지 직접 작성 | (v3.2.0 `SourceCollectorWorker` 삭제, D52 — 현재 소스 수집 워커 없음) |
| `vision` | 이미지 첨부 읽기 | 시각 검수(v3.1.0), 캡처 판독 `capture_read`(v3.2.0) |

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
