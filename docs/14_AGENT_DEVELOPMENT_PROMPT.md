<!--
tier: 2
last_synced_with: v4.4.0
ssot_for: [agent-prompts-template]
depends_on: [03_AGENT_ARCHITECTURE.md, ../CLAUDE.md]
last_review: 2026-09-29
-->

# 14 — Agent Development Prompt

본 문서는 LLM 워커(`workers/*_worker.py`, `BaseLLMWorker`)의 프롬프트 작성 규칙입니다. (v4.0.0: in-process `agents/*.py` 층은 없다 — [03](03_AGENT_ARCHITECTURE.md) §1)

**프롬프트는 코드 상수가 아니라 `prompts/{prompt_name}.md` 템플릿 파일이다**(15 P3, `tests/anti_inertia/test_prompts_from_files.py`). 규칙 값은 `rules/video_rules.yaml`에서 끼워 넣고, 프롬프트가 예시로 보여 주는 출력은 해당 Pydantic 스키마를 그대로 통과해야 한다(15 P4, `test_prompt_schema_parity`). QA 판정·사용자 피드백을 live 프롬프트에 자동 편입하지 않는다(15 P11).

## 1. 공통 규칙

- **문자열 포맷팅**: 반드시 `.replace()` 사용. `.format()` 금지 (JSON `{}`와 충돌).
- **출력 형식**: JSON 또는 Pydantic 모델 시리얼라이즈 가능한 형태.
- **금지**: Agent가 사용자에게 직접 질문하지 않는다.
- **로그**: 호출/응답은 `projects/{pid}/llm_calls/{call_id}.json`(`LLMCallRecord`, ADDENDUM_04)에 남는다.

## 2. 표준 프롬프트 골격

```
ROLE: 너는 {agent_name}이다. 본 시스템의 한 부품으로 동작한다.

CONTEXT:
- project_id: {project_id}
- topic_summary: {topic_summary}
- previous_artifacts: {refs}

TASK:
- {agent별 책임}

OUTPUT (JSON only):
- schema_version: 1
- {필드 명세}

CONSTRAINTS:
- 사용자에게 질문하지 않는다.
- 미검증 정보는 `<미검증>` 라벨로 분리한다.
- 모든 주장에 evidence_source_ids를 부여한다.
- {agent별 추가 제약}

DO NOT:
- 추측을 사실처럼 단정하지 않는다.
- 외부 URL을 직접 호출하지 않는다 (Worker에 위임).
```

## 3. 프롬프트 위치

- `prompts/{prompt_name}.md`(시스템) + `prompts/{prompt_name}_user.md`(사용자 메시지 템플릿). 워커 클래스는 `prompt_name` 만 가진다.
- 선택 블록(`script_draft`·`director_bundle`·`verify_sources_hints`)은 재료 파일이 있을 때만 끼운다.
- 변경은 git diff로 추적한다. 판을 바꿀 때는 파일을 고치고 규칙·스키마 파리티 테스트를 통과시킨다(코드 상수 `SYSTEM_PROMPT_V2` 같은 방식 금지).

## 4. 안전 검증

- LLM 응답을 Pydantic 모델로 즉시 파싱.
- 파싱 실패 시 한 번 재시도. 재실패 시 task `failed` 처리.

## 5. 프롬프트 보안

- 사용자 입력은 절대 system 메시지로 직접 들어가지 않는다.
- 사용자 입력은 user 메시지로 들어가며, system 메시지 안에 `{user_input}`처럼 들어가는 경우에도 `.replace("{user_input}", sanitize(text))`만 사용.

## 6. 신규 Agent 작성 체크리스트

- [ ] `BaseLLMWorker` 상속, `prompt_name`·`llm_mode` 선언
- [ ] `prompts/{prompt_name}.md`·`_user.md` 작성(`.replace()` 치환만)
- [ ] Pydantic 출력 모델 정의 (`schemas/models.py`에 추가)
- [ ] 단위 테스트 (예시 입력 → 예시 출력)
- [ ] `docs/03_AGENT_ARCHITECTURE.md` §2 워커 표 행 추가, 예시 출력이 있으면 파리티 테스트 대상에 추가
- [ ] `CHANGELOG.md` Added 섹션 기록
