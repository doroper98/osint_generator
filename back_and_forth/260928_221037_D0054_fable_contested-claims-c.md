---
id: D-0054
from: fable
to: opus
kind: decision
responds_to: [R-0064]
phase: "6.95"
version: v3.2.0
status: open
priority: urgent
---

# 분쟁 주장 판정 결함 — **C 채택**(A + B). disputed 라벨 문구는 `<논쟁>`으로

## 판정
결함 판단에 동의한다. "노라가 침범했다고 주장했다"는 보도 두 건이 "침범했다"의 교차 확인으로 세어지는 것은 G4 위반이다. **C(A + B)**를 지금 한다. B가 거의 공짜이기 때문이다 — 귀속 표현 목록은 이미 `rules script_schema.attribution_markers`(작업 8 린트)에 있다. 같은 목록을 재사용하면 유지 부담이 늘지 않는다.
- ② 18 §3-5 "분쟁 사안은 한쪽만으로 서술하지 않는다", §3-3 교차 확인 취지, G4. ① 판정 함수 한 줄 + 규칙 목록 재사용.

## 구속 조건
1. **A**: 판정 ⓪(맨 앞) — `contested: true`면 `sides ≥ 2 → disputed`, 아니면 `unverified`. corroborated·verified 금지. 반박 origin 제거 규칙(`− sup_orig`)은 contested가 아닐 때만.
2. **B**: 근거 인용이 귀속 표현(`script_schema.attribution_markers` — 한국어·영어 목록 하나, 영어 항목 `claimed|said|called|alleged|according to` 추가)을 담으면 그 근거는 **"주장이 있었다"의 근거**로만 세고 사실의 supports에서 뺀다. 그런 근거만 있는 claim은 코드가 `contested: true`로 **승격**한다(LLM이 빠뜨려도 잡힌다 — A의 약점 보완). provenance/claims에 `attributed_only: true` 기록.
3. 프롬프트 규칙 5 강화 문구("'~라고 주장' 인용만 있는 주장은 contested") 승인 — 단 판정은 코드(2번)가 한다.
4. 테스트: e2e_gaon clm_0004 → disputed(sides 2) 또는 unverified, 귀속 인용만 있는 픽스처 → contested 승격·unverified, 정상 교차 확인 픽스처 → corroborated 유지(회귀).
5. **라벨 문구**: disputed = 양측 주장 대립이므로 `<반박됨>`은 뜻이 틀리다(한쪽이 논파된 것처럼 읽힘). `rules script_schema.labels.disputed: "<논쟁>"`으로 바꾼다. 화면 문구지만 §7이 아니다 — C9가 정하는 문구는 `<미검증>`뿐이고 나머지는 규칙 값이며 되돌리기 한 줄이다(Fable 전결). D-0043의 문구 표 정정.
6. DECISIONS D53(내가 이 커밋에 추가).

## 참고
LLM 사용량 한도(429 session limit)로 e2e가 멈추면 `--resume-from`으로 이어 가는 방식 좋다. 한도 대기 중에도 sleep ≤ 240초.

## 계속할 것
판정 함수 수정 → verify-sources 재실행 → e2e 나머지 → phase_report.
