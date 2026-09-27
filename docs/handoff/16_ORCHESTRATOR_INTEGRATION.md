<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-state-machine, v2-engine-adapter]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 16. 오케스트레이터 통합 설계 — 기존 서비스 연결 지도와 새 상태 머신

전제: `15`(관성 방지 원칙)를 먼저 읽는다. 오케스트레이터는 **지휘(상태·작업 큐·승인)**만 하고, 영상 판단은 새 엔진과 LLM 단계가 한다.

---

## 1. 현재 구조 (collage@v1.2.1 확인)

- 사용자 → Command Center(Textual TUI, `run_pipeline.bat` / `python -m orchestrator.main command-center --project …`) 또는 웹 인테이크(`web/intake_page_app.py`).
- 오케스트레이터 서비스: `intake_service`, `source_collection_planner`, `source_completeness_checker`, `source_registry_builder`, `research_service`, `script_service`, `scene_builder`, `audio_service`, `render_io`, `bundle_service`, `subtitle_align`, `tts_lint`, `tts_pronounce`, `dashboard`, `command_center`, `project_manager`, `state_machine`.
- LLM 호출: `workers/base_llm_worker.py`가 `claude -p --output-format json`(구독 브리지, `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md`) 또는 codex를 호출. 워커마다 `system_prompt: ClassVar[str]`.
- 상태: `LINEAR_SEQUENCE` = CREATED → INTAKE_PLANNING → INTAKE_PENDING_USER → SOURCE_COLLECTING → SOURCE_COMPLETENESS_REVIEW → RESEARCH_IN_PROGRESS → BLUEPRINT_REVIEW → SCRIPT_WRITING → SCRIPT_REVIEW → SCENE_PLANNING → ASSET_PRODUCTION → SCENE_REVIEW → AUDIO_PRODUCTION → RENDER_DEBUG → …

---

## 2. 새 상태 머신

```
CREATED
 → INTAKE              소스 접수(기사·X 게시물·자료) + 요청 정리          [18]
 → SOURCE_VERIFY       출처 검증·주장(claim) 추출·교차 확인              [18]
 → RESEARCH            보강 리서치(웹), 사실 목록 확정                    [03 §1, 17 §5.1]
 → SCRIPT_DRAFT        원고 YAML(장면 자유 구성, 자막/발음, 출처, 미디어) [03, 17 §5.2]
 → SCRIPT_APPROVAL     ★ 사용자 승인 게이트 ①
 → VOICE_TIMELINE      린트 → TTS(ElevenLabs) → plan.json               [03 §6~8]
 → ASSETS              지오 티어/라벨, 인물·휘장·국기, 미디어 수집·가공    [04, 07, 14]
 → DIRECTION           AI 연출가 → direction.yaml                        [17 §2]
 → PREVIEW_QA          결정적 검사 → AI 시각 검수 루프(≤2회) → 프리뷰 시트 [17 §3~4]
 → PREVIEW_APPROVAL    ★ 사용자 승인 게이트 ②
 → RENDER              전체 렌더(병렬 청크)                              [11]
 → AUDIO_MIX           내레이션·음악·효과음                              [10]
 → DELIVER             먹싱, SRT, 설명문, 썸네일 후보, provenance         [11, 15 §P5]
 → DONE
```
역전이(되돌리기):
- SCRIPT_APPROVAL 반려 → SCRIPT_DRAFT (반려 사유 첨부)
- PREVIEW_APPROVAL 반려 → DIRECTION (연출 문제) 또는 SCRIPT_DRAFT (내용 문제) 또는 ASSETS (자료 교체)
- 어느 단계든 게이트 실패(권리·출처·린트) → 해당 단계에 머물며 사용자에게 보고. **폴백으로 다음 단계 진행 금지**(15 §P6).

---

## 3. 기존 모듈의 운명

| 모듈 | 판정 | 새 역할 |
|---|---|---|
| `state_machine.py` | **개조** | §2 상태로 교체, 역전이 표 추가 |
| `project_manager.py` | 유지 | 프로젝트 디렉터리에 `script.yaml`, `plan.json`, `direction.yaml`, `out/` 관리 |
| `command_center.py`, `tui_app.py`, `dashboard.py`, `log_router.py` | 유지·개조 | 새 상태 표시, 두 승인 게이트 UI(컨택트 시트 경로·provenance 요약 표시). 손상 manifest를 `created`로 조용히 폴백하지 말고 오류 표시 |
| `intake_service.py`, `web/intake_page_app.py` | 유지·확장 | 기사 URL/본문, X 게시물 텍스트·캡처 접수 → 소스 레코드 [18] |
| `source_collection_planner.py`, `source_completeness_checker.py`, `source_registry_builder.py`, `source_registry_io.py` | 유지·개조 | 소스 레지스트리 = 주장-출처 매핑(claim ↔ source) [18] |
| `research_service.py`, `research_io.py` | 유지 | 프롬프트를 규칙 파일에서 생성(15 §P3), 출력 = 검증된 사실 목록 |
| `script_service.py`, `script_io.py` | **개조** | 출력 = 새 원고 스키마(`02` §2.1): 장면 자유 구성, text/tts 분리, sources, media |
| `scene_builder.py`, `scene_io.py` | **삭제** | 세그먼트→장면 1:1 매핑 폐기. DIRECTION 단계가 대체 |
| `tts_lint.py`, `tts_pronounce.py` | **병합** | `script/lint.py`(금지 문구·발음 기호·강조어·출처) + 발음 규칙은 규칙 파일로 |
| `subtitle_align.py` | **대체** | plan 타임라인 + ElevenLabs 글자 정렬(`03` §6.3) |
| `audio_service.py`, `audio_io.py`, `audio_demo.py` | **대체** | `audio/mix.py` |
| `render_io.py` | **대체** | `engine_service.py`(엔진 CLI 어댑터, §4) |
| `bundle_service.py`, `bundle_io.py` | 개조 | `bundle/` 어댑터 호출 → 원고 초안(`12` §7) |
| `workers/base_llm_worker.py` | 유지·확장 | `claude -p` 브리지 유지. 추가: 프롬프트 파일 로드, 이미지 입력(시각 검수), 출력 스키마 검증 실패 시 1회 재요청 후 중단 |
| `workers/tts_backends.py` | 개조 | ElevenLabs with-timestamps, 정렬 저장 |
| `workers/engraving_stylizer.py` | 유지(폴백) | 인물 흑백화 폴백 |

---

## 4. 엔진 어댑터 계약 (`engine_service.py`)

```python
def run_stage(project_dir: Path, stage: Literal['plan','assets','direction_validate','preview','render','mix','deliver']) -> StageResult:
    # 각 stage는 엔진 CLI를 subprocess로 호출하고, 표준 출력 JSON(StageResult)을 받는다.
    # 오케스트레이터는 입력 파일을 생성·수정하지 않는다(15 §P1). 입력은 LLM 단계가 쓴 YAML과 사용자 승인 기록뿐.

class StageResult(BaseModel):
    ok: bool
    artifacts: dict[str, str]          # 경로: plan.json, prev/sheet.jpg, out/final.mp4 …
    provenance: dict | None            # 15 §P5
    drops: list[dict] = []             # 비어 있지 않으면 ok=False
    errors: list[str] = []
```
CLI 대응:
```
python -m script.plan         <proj>               → plan.json, tts/
python -m geo.prep / assets   <proj>               → tiers, labels, portraits, media
python -m engine.validate     <proj>               → direction.yaml 스키마·레지스트리·예약영역 검사
python -m engine.render       <proj> --preview auto → prev/*.png, prev/sheet.jpg, prev/checks.json
python -m engine.render       <proj> --jobs N      → out/video_noaudio.mp4
python -m audio.mix           <proj>               → out/mix.f32
python -m engine.mux          <proj>               → out/final.mp4, .srt, description.txt, provenance.json
```

---

## 5. 승인 게이트 설계

| 게이트 | 사용자에게 보이는 것 | 승인/반려 입력 |
|---|---|---|
| ① SCRIPT_APPROVAL | 장면 목록(장면명·문장 수·예상 길이), 원고 전문(자막 텍스트), 출처 표, 린트 결과, 미디어 후보 요약 | 승인 / 문장 단위 수정 요청 / 장면 재구성 요청 |
| ② PREVIEW_APPROVAL | 프리뷰 컨택트 시트(장면별 2~3컷), 전환 구간 연속 컷, AI 검수 잔여 이슈, provenance 요약, 예상 러닝타임 | 승인 / 특정 컷 번호 + 코멘트로 반려 |

반려 코멘트는 **해당 프로젝트의 수정 지시**로만 쓰고, 규칙 파일·프롬프트에 자동 반영하지 않는다(15 §P11). 반복되는 지적은 규칙 개정 후보로 모아 사람이 승인한다.

---

## 6. 산출물 디렉터리 (프로젝트별)
```
projects/<slug>/
├─ intake/            sources.json (소스 레코드), claims.json, screenshots/ (비공개 보관)
├─ script.yaml        원고(승인본에 approved_at 기록)
├─ plan.json  tts/    타임라인·음성·정렬
├─ assets.lock.json   이 영상이 쓴 자산 목록·해시·권리
├─ direction.yaml     연출(버전별 보관: direction.v1.yaml, v2 …)
├─ prev/              프리뷰 PNG, sheet.jpg, checks.json, qa_verdict.v*.json
└─ out/               final.mp4, final.srt, description.txt, thumbnail_candidates/, provenance.json
```
