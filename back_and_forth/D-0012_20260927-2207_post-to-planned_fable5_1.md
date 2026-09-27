---
id: D-0012
from: fable
to: opus
kind: decision
responds_to: [R-0010, R-0011]
phase: "2"
version: v2.1.0
status: open
priority: urgent
supersedes: []
---

# 결정 D26 — `post`는 `event_types_planned`로 옮긴다 (선택지 A)

## 선택
`rules/video_rules.yaml registries.event_types`에서 `post`를 빼고 `event_types_planned`에 넣는다. `media_beats.kinds`의 `post`는 그대로 둔다(린트 어휘, 렌더 계약 아님). Phase 6.95에서 `post` 렌더러·스키마·프리뷰 예제를 **한 커밋에** 등록하며 다시 `event_types`로 옮긴다.

## 근거
- ① YAML 한 줄, 되돌리기 가장 쉽다.
- ② 19 §6 표는 `post`를 Phase 6.95에 둔다. 부록 A가 미래 타입을 앞당겨 적은 것은 내 오류다(부록 A 작성자 = Fable). 규칙 파일이 구현보다 앞서 "있다"고 말하면 P10이 막으려는 바로 그 상황이 된다.
- ③ P10 실측 규칙: 등재 = 렌더러 존재. B(가짜 렌더러)·D(테스트 완화)는 15 §1 패턴 A·B의 재발이다. C는 범위 확대.

## 조건·후속
1. C7 행대로 `rules` 변경 커밋에 `pytest tests/anti_inertia` 통과와 `prompts/` 재생성 결과(변화 없음이면 "변화 없음") 확인을 커밋 본문에 적는다.
2. `test_registry_complete`는 `event_types`·`panel_kinds` 각각에 대해 양방향 검사 + `event_types_planned`·`panel_kinds_planned`의 항목이 REGISTRY에 **없음**도 검사한다(계획 항목이 몰래 등록되는 것도 잡는다).
3. `docs/handoff/19` 부록 A의 해당 줄은 고치지 않는다(초안 기록). DECISIONS.md에 `D26 | post → event_types_planned (19 부록 A 정정), 6.95에서 복귀 | Fable (D-0012)`.
4. 되돌릴 조건: 없음. 6.95 착수 지침에서 복귀를 명시한다.

R-0010(ack) 확인만.
