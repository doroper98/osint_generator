---
id: R-0129
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G7"
version: v4.8.0
commit: f9549a2
status: awaiting_decision
---

# 결정 요청 — 인물 뱃지의 연출 `R:` 가 적응 크기를 끈다 (D-0101 §1)

## 쟁점
D-0101 §1 은 "연출 `R:` 를 명시하면 그 값 우선(hormuz 부산 국기 R 18 처럼)" 이라고 했다. 그런데 **지금 저장소의 인물 뱃지는 전부 `R:` 를 적고 있다.**
문언대로면 적응 크기가 어느 영상에서도 작동하지 않는다(합격 조건 "fed_policy·hormuz 에서 solo 구간 R = R_person_solo" 를 만족할 수 없다).

실측(연출 파일의 badge, kind person):

| 프로젝트 | 인물 뱃지 | R |
|---|---|---|
| hormuz_korea | 이재명 ×2, 하메네이 | 34, 34, 32 |
| ratcliffe2026 | 젤렌스키, 트럼프 ×2, 푸틴 | 32 ×4 |
| fed_policy_2026 | 워시 ×2 | 30, 28 |

원인: 연출 프롬프트 예시가 인물 뱃지에 R 를 넣는다(`prompts/examples/badges/person.yaml` R 34, `prompts/genre_director.md` 51행 R 28, `prompts/director.md` 86행 R 34).
그리고 `BadgeEvent.R` 기본값이 30 이라 R 를 안 적어도 "명시" 와 구분할 수 없었다(작업 1 에서 기본 None 으로 바꿨다).

## 선택지
| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| **A** | **인물 뱃지의 연출 R 은 쓰지 않는다**(코드가 항상 적응 크기, P8). 불러올 때 버리고 provenance `badge.R_ignored[]` + lint 경고 한 줄. 국기·휘장 R 은 그대로 우선. 프롬프트 예시 3곳에서 인물 R 삭제 | 연출 파일을 안 고쳐도 모든 영상에 적용. LLM 이 R 를 또 적어도 무시된다. 패널 안 뱃지(statement·precedent·network·relation)는 패널 코드가 R 를 주므로 무관 | 규칙 한 줄(또는 커밋 revert) |
| B | D-0101 문언 유지(명시 R 우선). hormuz·ratcliffe·fed_policy 연출 파일과 프롬프트 예시 3곳에서 인물 R 삭제 | 연출 파일 3개 수정(hormuz 는 골든 연출). 앞으로 LLM 이 R 를 적으면 조용히 적응이 꺼진다 — 검사로 막으려면 결국 A 와 같은 경고가 필요 | 연출 파일 revert |
| C | 연출 R 은 "group 크기 힌트" 로만 쓴다(solo 는 항상 R_person_solo) | 규칙이 복잡(연출 값과 규칙 값이 섞임) | revert |

## Opus 권고 — A
- ② D-0101 §1 제목이 "코드가 계산, 연출은 배치만 — P8" 이다. 문언의 예시(부산 **국기** R 18)도 국기다. 인물 R 우선은 예시를 일반화한 표현으로 읽힌다.
- ① A 는 규칙 한 줄로 되돌릴 수 있고, 연출 파일(특히 hormuz 골든 연출)을 건드리지 않는다.
- ③ 실측: 인물 R 9건이 전부 v3 범위 28~34 — "크기 의도" 라기보다 예시 값을 따른 것이다.

## 같이 확인할 해석 두 가지(작업 1 에 구현, 틀리면 알려 달라)
1. `R_person_group: [30, 34]` 범위의 쓰임: **n = 2 → 34, n ≥ 3 → 30**(사람이 더 늘면 더 작아진다).
2. "보이는 인물 뱃지 수" = 같은 풀(지도·시간축 무대 / 패널 위 뱃지 — D2(c))에서 **표시 구간**(팝인 완료 ~ 페이드 아웃 시작)인 인물 뱃지. 카메라 화면 밖 여부는 세지 않는다(t 만의 함수로 결정적이게 — 화면 안 판정은 카메라 경로에 묶여 연출 수정 때 크기가 흔들린다). 새 뱃지는 자기 자신을 세어 처음부터 group 크기로 뜨고, 먼저 있던 뱃지는 새 뱃지 팝인 완료 순간부터 resize_sec 동안 줄어든다.

## 근거 자료
- 코드: `engine/layers/badges.py` `assign_person_sizes`·`badge_R`(f9549a2), `engine/events.py` BadgeEvent.R
- 테스트: `tests/test_g7_badge_adaptive.py`(명시 R 우선 = 현 문언으로 구현)

## 막히는 범위
- 막힘: 작업 1 의 영상 적용(합격표 "배지 적응" 프레임 실측 3컷), `timeline_badge` 슬롯 point 이동 여부(solo 56 이면 위로 잘림 — 상자 top = y − 2.2R), 골든 expected_deltas·기준선 재등록·전편 렌더.
- 계속: D2(c) 패널 뱃지 자리, 기사 카드 조판(작업 2), D6 켄 번스, D-0109 청와대 휘장, §3 크기 표 준비.

## §7 해당 여부
아니다(README §7.2 표 밖 — Fable 전결).
