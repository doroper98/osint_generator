---
id: R-0011
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "2"
version: v2.1.0
commit: HEAD
status: in_progress
---

# 결정 요청 — `post` 이벤트 타입과 레지스트리 양방향 테스트의 충돌

## 쟁점

`rules/video_rules.yaml registries.event_types`에 `post`가 들어 있다(19 부록 A 원문 그대로).
그런데 `post` 카드는 19 §6 표상 **Phase 6.95**이고, D-0010 §3은 "이벤트 타입 추가·`post`"를 이번 Phase에서 하지 말라고 한다.
D-0010 §2는 `test_registry_complete`(규칙 ↔ REGISTRY **양방향 일치** + 타입마다 프리뷰 예제)를 xfail 해제 후 통과시키라고 한다.
세 조건을 동시에 만족할 수 없다.

## 선택지

| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| A | 규칙 파일에서 `post`를 `event_types` → `event_types_planned`로 옮긴다. `media_beats.kinds`의 `post`는 그대로(린트 어휘일 뿐 렌더 계약 아님) | 테스트 통과. P10 "레지스트리에 있는데 렌더러 없음 = 오류"를 규칙이 스스로 지킨다. 6.95에서 한 줄 되돌림 | YAML 한 줄 |
| B | `post`를 REGISTRY에 등록하되 렌더러가 `NotImplementedError`를 던진다 | 테스트 통과하지만 "렌더러가 있는 척"이라 P6·P10 정신에 어긋남 | 코드 삭제 |
| C | `post` 카드를 지금 구현 | D-0010 §3 위반, 범위 확대 | 코드 삭제 |
| D | 테스트를 `event_types - {post}`로 완화 | 테스트 약화(15 관성 방지 역행) | 테스트 복원 |

## Opus 권고: **A**

- ① YAML 한 줄, 되돌리기 가장 쉬움. ② 19 §6 표가 `post`를 6.95에 배정 — 규칙 파일 부록 A가 미래 타입을 앞당겨 적은 것. ③ P10 실측 규칙("등재 = 렌더러 존재")에 맞춘다.
- 규칙 파일 변경이라 C7 행(`rules/video_rules.yaml` → prompts 재생성 확인, anti_inertia 통과)을 함께 수행한다.

## 근거 자료

- `rules/video_rules.yaml:145`, `docs/handoff/19_…:280,283,459`, D-0010 §2·§3, `tests/anti_inertia/test_registry_complete.py`.

## 막히는 범위

- `test_registry_complete` xfail 해제 커밋만 막힌다. 나머지 엔진 분해·렌더·패리티는 계속한다.

## §7 해당 여부

아니다(규칙 어휘 배치, 영상 수치 무변경).
