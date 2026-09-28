---
id: R-0064
from: opus
to: fable
kind: decision_request
responds_to: [D-0052, D-0053]
phase: "6.95"
version: v3.2.0
commit: 018702e
status: in_progress
---

# 결정 요청 — 분쟁 주장(contested)이 corroborated 로 판정되는 결함 (D50 판정 ①~⑤ 보완)

D-0053 확인(삭제 조정 기준선 — 최종 보고에 삭제 목록·새 테스트 표로).

## 쟁점
e2e(가상 픽스처, `projects/e2e_gaon`) 실측: `clm_0004 "호위 선단이 노라 영해를 침범했다"` 가 **corroborated**.
근거 인용은 두 기사가 **"노라 정부는 … 침범했다고 주장했고"**, **"Norra's foreign ministry called the escort a violation"** — 즉 "노라가 그렇게 주장했다"는 보도다.
반박 인용(가온 외교부)도 같은 두 기사에서 나와 `con_orig − sup_orig = ∅` 이 되어 disputed 가 되지 않았다. LLM 은 `contested: true` + 양측 sides 를 정확히 적었다.
결과: 라벨 규칙상 corroborated = 라벨 없음 → 원고가 "침범했습니다"를 단정해도 린트·라벨이 막지 못한다. **사실 정확성(G4·C0 경계)을 깨는 결함**이라 판단한다.
원인: D50 ②는 "같은 사실"을 인용 존재로만 보므로, "누가 X라고 주장했다"를 인용한 근거가 "X"의 교차 확인으로 세어진다. 같은 매체가 양측을 함께 보도하면 반박이 지워진다.

## 선택지
| 선택지 | 내용 | 위험 | 되돌리기 |
|---|---|---|---|
| **A. 분쟁이면 corroborated·verified 금지**(권고) | `contested: true` 인 claim 은 코드가 status 를 **sides ≥ 2 → disputed, 아니면 unverified** 로만 준다(판정 ⓪ 으로 맨 앞). 반박 origin 제거 규칙(`− sup_orig`)은 contested 가 아닐 때만 | contested 여부는 여전히 LLM 이 표시 — LLM 이 contested 를 빠뜨리면 같은 문제. 보완으로 프롬프트 규칙 5 강화(“~라고 주장” 인용만 있는 주장은 contested”) | 판정 함수 한 줄 |
| B. 귀속 인용 감지 | 인용이 귀속 표현(주장·called·said…)을 담으면 그 근거는 "주장이 있었다"만 뒷받침하는 것으로 보고 사실의 교차 확인에서 뺀다 | 규칙 목록 유지 부담, 영어·한국어 표현 누락 | 규칙 값 |
| C. A + B | 둘 다 | 가장 보수적 | 같음 |

**권고 A**(C 는 다음 Phase 후보) — 판정 기준 ①(한 줄), ②(18 §3-5 "분쟁 사안은 한쪽 게시물만으로 서술하지 않는다"·§3-3 교차 확인 취지), G4.
라벨 문구: disputed 의 규칙 문구는 `<반박됨>` 이다. 분쟁(양측 주장 대립)에는 "반박됨"보다 "논쟁" 류가 정확할 수 있다 — 화면 문구라 **§7(사용자 고유 결정) 해당 여부 판단 부탁**. 문구를 바꾸지 않는 한 이번 Phase 에서는 규칙 값 그대로 둔다.

## 막히는 범위
- 판정 함수 수정·테스트·e2e 재검증(verify-sources 재실행)만 이 결정을 기다린다.
- 막히지 않고 계속: e2e 나머지(build-research → build-script → 게이트 ① 출처 검사), post 카드 컷, phase_report 준비.
- 참고: e2e 는 LLM 사용량 한도(429 "session limit", 13:04 UTC)로 build-research 에서 한 번 멈췄고 한도 해제 뒤 `--resume-from build-research` 로 이어 가는 중.
