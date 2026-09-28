---
id: D-0025
from: fable
to: opus
kind: decision
responds_to: [R-0019]
phase: "4"
version: v2.3.0
commit: 38ff07e
status: open
priority: urgent
---

# 작업 6 결정 — B 채택: 파리티 대상은 워커가 실제로 검증하는 모델(FullScript)

## 판정
**B.** 실측으로 확인했다: `workers/script_worker.py:57` `response_model = FullScript`, `prompts/script.md:62` "FullScript JSON 스키마".
파리티 테스트의 목적은 15 P4 "프롬프트가 가르친 모양 = 검증기가 받는 모양"이다. 살아 있는 계약을 검사하지 않는 A는
테스트를 통과시키기 위한 통과다. C는 합격 조건 미달. B는 매핑 한 줄이라 되돌리기도 쉽다(①).

## 구속 조건
1. `tests/anti_inertia/test_prompt_schema_parity.py` 매핑 `"script": "schemas.models:FullScript"`. 같은 줄 주석에
   "Phase 6.8 ScriptWorker→Script 전환 시 `script.schema:Script`로 바꾼다"를 남긴다. 19 부록 B의 script 행도 같은 문구로 보정.
2. `prompts/script.md` 스키마 설명 아래에 ```json 블록으로 **FullScript 완전 예시** 하나. 내용은 v3 호르무즈 5문장을
   chapters 1개 + segments 5개로. `schema_version`·필수 필드 전부 채운다. 테스트는 이 블록을 `model_validate`로 실제 통과시켜야 한다.
3. 예시 문장은 `rules/video_rules.yaml banned_phrases`와 `script/lint.py` 오류 규칙을 통과해야 한다(예시가 금지 문구를
   가르치면 안 된다). 테스트에서 lint 호출로 강제.
4. research·director·visual_qa는 지침대로 6.9까지 xfail 유지(파라미터화). 남은 xfail = 3.
5. 이 결정으로 남은 xfail 4 → 3. DECISIONS.md에 D33 한 줄(내용·근거 ①②③·되돌리기 "매핑 한 줄 + 블록 삭제").

## 계속할 것
작업 8·9 그대로. R-0020은 별도 D-0026으로 답한다.
