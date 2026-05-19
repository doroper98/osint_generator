<!--
tier: 2
last_synced_with: v0.2.0
ssot_for: [agent-prompts-template]
depends_on: [03_AGENT_ARCHITECTURE.md, ../CLAUDE.md]
last_review: 2026-05-19
-->

# 14 — Agent Development Prompt

본 문서는 Agent (`agents/*.py`)의 LLM 시스템 프롬프트 작성 규칙입니다.

## 1. 공통 규칙

- **문자열 포맷팅**: 반드시 `.replace()` 사용. `.format()` 금지 (JSON `{}`와 충돌).
- **출력 형식**: JSON 또는 Pydantic 모델 시리얼라이즈 가능한 형태.
- **금지**: Agent가 사용자에게 직접 질문하지 않는다.
- **로그**: 호출/응답을 `logs/agents/{agent_name}_{ts}.jsonl`로 남긴다.

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

## 3. Agent별 프롬프트 위치

- `agents/{agent_name}.py` 안에 `SYSTEM_PROMPT = """..."""` 상수.
- 변경 시 git diff로 추적.
- A/B 테스트 시 `SYSTEM_PROMPT_V2` 등 변수명에 버전 명시.

## 4. 안전 검증

- LLM 응답을 Pydantic 모델로 즉시 파싱.
- 파싱 실패 시 한 번 재시도. 재실패 시 task `failed` 처리.

## 5. 프롬프트 보안

- 사용자 입력은 절대 system 메시지로 직접 들어가지 않는다.
- 사용자 입력은 user 메시지로 들어가며, system 메시지 안에 `{user_input}`처럼 들어가는 경우에도 `.replace("{user_input}", sanitize(text))`만 사용.

## 6. 신규 Agent 작성 체크리스트

- [ ] BaseAgent 추상 클래스 상속 (Phase 3에서 정의)
- [ ] 시스템 프롬프트 작성
- [ ] Pydantic 출력 모델 정의 (`schemas/models.py`에 추가)
- [ ] 단위 테스트 (예시 입력 → 예시 출력)
- [ ] `docs/03_AGENT_ARCHITECTURE.md` Agent 카탈로그 행 추가
- [ ] `CHANGELOG.md` Added 섹션 기록
