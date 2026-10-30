---
id: D-0281
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — UF-145 AI 상투 문구: 금지 패턴 13개 추가(감독이 규칙에 넣음) + 린트 범위를 화면 문자열 전부·감독 보고문으로 확장

사용자 원문(2026-10-30): "니가 작성하는 문구에 이런내용이 없도록 강하게 쪼여. 정말 ai slop 느껴지는 문구들이거든." + 예문 17종(원장 UF-145, `rules banned_phrases.examples`). agents_reviewer 에도 같은 내용이 전달됐다.

## 감독이 이미 한 것(이 커밋)
- `rules/video_rules.yaml banned_phrases.patterns` 끝에 13개 추가(주석 UF-145), `examples:` 17문장(사용자 예문 + 감독 변형 "한 점에 모여"). `schemas/rules_models.py BannedPhrases.examples` 필드. 기존 원고·골든·프롬프트 예시 오탐 0(diesel "물량이 남는다고 말했습니다" 는 문장 끝 앵커로 통과).
- `back_and_forth/FABLE_HANDOFF.md §6`: 감독 보고문도 같은 패턴으로 자기 점검.

## Opus 할 일(E0 콘티 판 뒤, E7-S1 앞)
1. **테스트** `tests/test_script_lint.py::BannedExamplesTest` — examples 모두가 patterns 중 하나에 걸린다(하나라도 안 걸리면 실패) + 기존 원고·골든 원고(hormuz·diesel·showcase 둘) 오탐 0.
2. **린트 범위 확장**(지금은 원고 `s.text` 만): description.yaml(headline·summary·chapters.label·footer) · direction.yaml 의 모든 화면 문자열(card·panel 텍스트·marker label/sub·badge·island 제목·cascade·catalog 라벨) · 엔딩 카드 줄 · gate-view 문서(`gate1_view*.txt`·`gate1_elements.md`) · `phase_report`·R 문서 본문. quote.text 는 발언 원문이라 제외. 위반 = 원고 린트와 같은 `slop` error(hard — 면제 불가 목록 유지).
3. **도구** `tools/slop_check.py <파일|->`: 표준입력·파일의 문장을 patterns 로 검사해 걸린 줄·패턴을 출력(종료 코드 1). 감독·구현 세션이 보고문을 보내기 전에 돌린다(FABLE_HANDOFF §6).
4. `prompts/` 재생성(prompt_loader `{{RULES.banned_phrases}}` 가 patterns 를 넣으므로 템플릿 변경 없음 — 생성 결과 확인) + `tests/anti_inertia` 통과.
5. 원장 UF-145 guards 에 테스트·도구를 추가(`tools/feedback_ledger.py --write`).
