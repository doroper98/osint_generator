<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [anti-inertia-principles]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 15. 오케스트레이터 관성 방지 원칙 — agents_reviewer 교훈 기반

> 사용자 문제 제기(원문): "오케스트레이터의 고집이(코드가) 너무 세서 우리가 새로운 기능을 주입 해도 오케스트레이터에 기존에 주입 된 성향이나 관점에 따라 기능이 주입 되지 않는 경우가 agent reviewer 에 너무 많이 발생했어. 어떻게 해결할 수 있을까?"
> 근거 저장소: `https://github.com/doroper98/agents_reviewer` (커밋 e62b3f2, 2026-09-27) — CLAUDE.md, CHANGELOG.md, DEVLOG.md, REFACTOR_V5/V6/V7_PLAN.md, docs/VISUAL_ENHANCEMENT_V9_PLAN.md, docs/V5_ACTIVATION.md

**Claude Code는 이 문서를 `13` 구현 계획보다 먼저 읽는다.** 이 원칙을 어기면 개편 결과물이 다시 옛 영상 문법으로 돌아간다.

---

## 1. 증상의 정의

"새 기능을 만들었는데 결과물에 나타나지 않는다." 원인은 거의 항상 아래 여섯 중 하나다.

| # | 패턴 | agents_reviewer 실제 사례 | 출처 |
|---|---|---|---|
| A | **만들었지만 연결되지 않음** | V5 chart_gate·sanity·critic·desk 게이트가 전부 flag OFF + 오케스트레이터에 호출 코드 자체가 없음. "목업은 좋은데 실보고서에서 사라진다". 반대로 구형 7-에이전트는 v4.0부터 미호출인데 v5.2.9까지 모듈이 남아 혼선 | V9 계획 §2, CLAUDE.md |
| B | **조용한 드롭** | composer SYSTEM_PROMPT가 가르친 heatmap·stacked 데이터 모양과 검증 가드가 요구하는 모양이 상호 배타 → 프롬프트를 지킨 출력이 **100% 무경고 드롭** | v8.5.11, CHART-AP-44 |
| C | **진실의 원천이 여럿** | `config.model_name`만 바꾸고 각 에이전트는 자기 상수로 override → 런타임 무변화 / has_data 판정이 두 템플릿에 복제, 한쪽에 폐기 분기 잔존 / 커밋 버전과 상수 불일치 3회 반복 | CHANGELOG, CLAUDE.md #12 |
| D | **폴백이 새 기능을 삼킴** | 1-섹션 파국 폴백을 발행본 335건 중 30건(9%)이 탔고 전부 시각물 0 | v8.5.12 |
| E | **결정적 코드가 LLM 결정을 덮어씀** | archetype 선택에서 LLM 후보와 매트릭스가 다르면 매트릭스 채택 | DEVLOG V3 Step 2 |
| F | **"기존 출력 불변" 원칙** | "flag OFF인데 출력이 달라짐 금지"(AP-V6-3), byte-equal 보존 → 새 기능이 추가형·OFF 기본값에 갇혀 기본 동작이 되지 못함 | REFACTOR_V6 §AP, V5_ACTIVATION |

부가 교훈:
- 레지스트리 미등재 기능은 emit 금지(AP-V5-27) — 좋은 장치지만 **등록을 잊으면 조용히 안 쓰인다**.
- 비평 로그를 live SYSTEM_PROMPT에 자동 편입 금지(AP-V6-9) — 프롬프트 오염·FP 영구화.
- 각 LLM 호출은 자기 몫의 상태만 입력(State Compaction, AP-V5-30) — 넓은 맥락이 들어가면 옛 관점이 새 단계로 스며든다.
- 실제로 돌지 않은 검수를 "검수됨"으로 표기 금지(AP-V6-10) — 배선 증명은 정직해야 한다.
- 설정은 시작 시 1회 로드 → 재시작 없이 플래그 변경 미반영(V5_ACTIVATION §4).

## 2. osint_generator에 이미 있는 같은 씨앗 (collage@v1.2.1 확인)

| 위치 | 씨앗 | 패턴 |
|---|---|---|
| `orchestrator/scene_builder.py` | "ScriptSegment 1개를 SceneEntry 1개로 결정론적으로 매핑", 기본 `text_slide`, `DEFAULT_SEGMENT_SEC = 8.0` | E, F — 12막 문법의 코드상 뿌리 |
| `workers/*` `system_prompt: ClassVar[str]` | 프롬프트가 코드 상수 | C — 문서 규칙을 바꿔도 프롬프트는 옛 관점 |
| `orchestrator/state_machine.py` `LINEAR_SEQUENCE` + 서비스별 선행상태 검사 | 15단계 직선 강제(CREATED → … SCENE_PLANNING → ASSET_PRODUCTION → SCENE_REVIEW → AUDIO_PRODUCTION → RENDER_DEBUG …) | A — 새 단계(연출·시각검수)가 들어갈 자리 없음 |
| `orchestrator/command_center.py` | manifest 손상 시 `created`로 폴백 | D — 폴백이 상태를 덮음 |
| `hyperframes/scripts/bundle_to_video.py` | 섹션→장면 1:1, 정규화기가 데이터 모양을 강제 | B, E |

---

## 3. 원칙 (주입하지 말고 교체한다)

### P1. 새 엔진은 오케스트레이터 밖에 둔다 (스트랭글러)
- `engine/`, `script/`, `audio/`는 독립 패키지 + CLI. 오케스트레이터는 **얇은 어댑터 서비스 하나**(`engine_service.py`)로 CLI를 호출하고 결과(영상, provenance)만 받는다.
- 오케스트레이터 코드는 장면 구성·연출·레이아웃 판단에 **관여할 수 없다**(입력 파일을 쓰지 않는다).

### P2. 옛 경로는 플래그가 아니라 삭제로 끝낸다
- `scene_builder.py`, HyperFrames/Remotion 렌더 경로, 섹션=장면 로직을 `archive/*` 브랜치로 옮기고 main에서 삭제.
- 옛 경로가 없으면 조용히 그쪽으로 떨어질 수 없다(패턴 A·D 원천 차단).
- 삭제 확인 테스트: `test_no_legacy_imports` — `hyperframes`, `remotion`, `scene_builder` import가 main 코드에 없음.

### P3. 규칙은 한 파일에서 만들고 모두가 읽는다 (SSOT)
- `rules/video_rules.yaml`: 금지 문구, 원고 스키마 요약, TTS 표기 규칙, 미디어 비트, 균형 원칙, 레이아웃 핵심 수치.
- 워커 프롬프트는 **템플릿 파일 + 규칙 파일**에서 생성(코드 상수 금지). 린트·스키마 검증도 같은 파일을 읽는다.
- 모델명·주요 설정은 `config.yaml` 한 곳. 모듈별 상수 override 금지(lint로 검사). 시작 시 유효 설정을 로그로 덤프.

### P4. 프롬프트-검증 일치를 테스트로 강제 (CHART-AP-44 재발 방지)
- `test_prompt_schema_parity`: 각 워커 프롬프트가 예시로 보여 주는 출력 모양(원고 YAML, 연출 YAML, QA 판정 JSON)이 해당 Pydantic 스키마를 **그대로 통과**하는지.
- 새 필드·새 이벤트 타입을 추가하면 예시·스키마·렌더러 세 곳이 함께 바뀌지 않으면 실패.

### P5. 배선은 산출물로 증명한다 (provenance)
- 영상마다 `out/provenance.json`:
```json
{"engine": "2.3.0", "rules_hash": "…", "prompts": {"script": "sha1…", "director": "sha1…"},
 "features_used": {"camera_moves": 5, "dips": 4, "badges": 9, "panels": ["refusal","statement","timeline","precedent","versus"],
                   "media": {"clip": 2, "photo": 2, "cutout": 1, "article": 2}, "label_lod": true, "voice": "elevenlabs:<id>"},
 "qa": {"auto_iterations": 2, "user_approved": true}, "drops": []}
```
> [정정 D-0041: 실물 8, relation] 위 예시의 `"badges": 9` 는 실물(골든 연출 badge 이벤트) **8**, `"refusal"` 은 **`relation`**(v2.5.0 관계 패널)이다. 기대값 정본은 `tests/anti_inertia/test_provenance_e2e.py`.
- 합격 판정은 "기능 코드가 있다"가 아니라 **"이번 영상에 쓰였다"**. e2e 테스트가 provenance의 `features_used`를 검사한다.
- 실제로 돌지 않은 단계는 기록하지 않는다(AP-V6-10).

### P6. 드롭과 폴백을 숨기지 않는다 (fail loud)
- 검증에 실패한 이벤트·미디어·패널은 조용히 버리지 않는다 → 렌더 전 오류, 또는 `drops[]`에 기록하고 CI에서 `drops > 0`이면 실패.
- **폴백으로 옛 스타일 영상을 내보내지 않는다.** 실패하면 중단하고 사용자에게 보고한다.

### P7. 헌법 문서부터 바꾼다
- Claude Code는 `CLAUDE.md`, `GOAL.md`를 최상위 규칙으로 따른다. 옛 영상 기준이 남아 있으면 새 기능을 "규칙 위반"으로 되돌린다.
- 개편 첫 커밋에서: (1) 영상 기준 조항을 이 문서 묶음 참조로 교체, (2) **"기존 출력 불변(byte-equal) 원칙은 이번 개편에 적용하지 않는다. 기준은 v3 골든 재현"** 명시, (3) 이 문서(15)를 필독 목록 최상단에.

### P8. 권한표: LLM이 정할 것 vs 코드가 정할 것
| 결정 | 주체 | 코드의 역할 |
|---|---|---|
| 장면 구성, 문장, 강조어 | LLM(원고 단계) + 사용자 승인 | 스키마·린트 검증만. **개수·길이를 정규화하지 않는다** |
| 카메라·패널·미디어 배치 | LLM(연출 단계) + 시각 검수 | 스키마 검증, 예약 영역 충돌 검사(보고만) |
| 렌더 수치(두께·알파·타이밍 곡선·글자 크기) | 코드(`style.py`) | 결정 |
| 사실·출처·권리 판정 | 코드 게이트 + 사람 | 결정(미충족 시 중단) |
- 코드가 "정규화"라는 이름으로 LLM의 구성 결정을 옛 모양으로 되돌리는 것 금지(패턴 E).

### P9. 단계별 입력 경계 (State Compaction 계승)
- 연출 LLM은 원고·타이밍·자산 목록·규칙만 본다(옛 scene_manifest, 옛 템플릿 금지). 원고 LLM은 검증된 소스 레코드와 규칙만 본다.
- 이전 버전 산출물을 "참고"로 넣지 않는다 — 옛 스타일이 복제된다.

### P10. 레지스트리는 시끄럽게 실패한다
- 이벤트 타입·패널 종류·미디어 형태 레지스트리에 없는 것을 연출이 쓰면 **오류**. 레지스트리에 있는데 렌더러 구현이 없으면 **오류**(AP-V5-27의 조용한 미사용 방지).

### P11. 프롬프트 오염 금지 (AP-V6-9 계승)
- QA 판정·사용자 피드백을 live 프롬프트에 자동으로 붙이지 않는다. 반복되는 지적은 규칙 파일 개정(사람 승인) → 프롬프트 재생성으로만 반영.

### P12. 변경은 한 번에 하나, 결과는 영상으로 확인
- 단계마다 프리뷰 컨택트 시트 + provenance를 사용자에게 보여 준다. 코드 리뷰만으로 "적용됨"을 판정하지 않는다.

---

## 4. "기능이 안 먹는다" 디버깅 순서 (Claude Code용)
1. **호출되나?** provenance `features_used`에 있나 → 없으면 배선(P1·P5).
2. **검증에서 떨어졌나?** `drops[]`, 스키마 오류 로그 → 프롬프트·스키마 불일치(P4).
3. **다른 값이 덮나?** 모듈 상수, 중복 템플릿, 옛 프롬프트 → SSOT 위반(P3).
4. **폴백을 탔나?** 폴백 로그 → P6.
5. **헌법과 충돌하나?** CLAUDE.md/GOAL의 옛 조항 → P7.
6. **LLM이 옛 관점을 가져왔나?** 입력에 옛 산출물·옛 예시가 섞였나 → P9.

## 5. 관성 방지 테스트 목록 (Phase 0에서 먼저 만든다)
| 테스트 | 검사 |
|---|---|
| `test_no_legacy_imports` | main 코드에 hyperframes/remotion/scene_builder import 없음 |
| `test_prompts_from_files` | `system_prompt` 문자열 상수 없음, 프롬프트는 템플릿 파일에서 로드 |
| `test_prompt_schema_parity` | 프롬프트 예시 출력 = 스키마 통과 |
| `test_single_config` | 모델명·주요 수치 상수의 중복 정의 없음 |
| `test_registry_complete` | 레지스트리 항목마다 렌더러·스키마·프리뷰 예제 존재 |
| `test_provenance_e2e` | 골든 프로젝트 렌더 후 `features_used`가 기대값과 일치, `drops == []` |
| `test_no_silent_fallback` | 강제 오류 주입 시 옛 스타일 출력 없이 중단 |
| `test_constitution` | CLAUDE.md/GOAL이 이 문서 묶음을 참조하고 byte-equal 비적용을 명시 |
