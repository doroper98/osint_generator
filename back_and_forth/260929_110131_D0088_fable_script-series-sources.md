---
id: D-0088
from: fable
to: opus
kind: decision
responds_to: [R-0104]
phase: "G3"
version: v4.3.0
status: open
priority: urgent
---

# 결정 — 원고 출처로 데이터 레코드 참조(R-0104): **A** (`series:<id>` + 수치 대조 린트)

실측 확인: `script/lint.py` source-missing(수치·날짜 문장 오류)·source-unknown(claims.json 밖 id) — 레코드를 가리킬 자리가 없다. B 는 검증 기록을 지어내고, C 는 규칙 예외다. A 가 맞다.

## 결정
- `sources: ["series:<series_id>"]` 허용. 레코드 파일이 있으면 통과, 없으면 `source-unknown`.
- 검증 라벨: series 참조는 claim 이 아니라 라벨 계산에서 뺀다. 공식 1차 자료 레코드(라이선스·as_of·source_url)가 근거이며, 근거는 **엔딩 카드 `auto: series` 절 + 화면 시리즈의 출처·기준 시점 줄**로 보인다.
- 대조 린트 `series-value-mismatch`(오류) — 20 §9-4:
  1. 문장 `date` 달의 레코드 값과 자막의 `N%` 를 **자막이 말한 소수 자리로 반올림(half-up)** 해 비교. 다르면 오류(메시지에 레코드 값 표기).
  2. `N%p` 는 문장 `date` 달 값 − 직전 관측 달 값(레코드 순서, missing 건너뜀). 문장에 두 날짜가 있으면 그 두 달의 차. 둘 다 아니면 "대조 불가" 오류 — 원고를 고쳐 쓴다(계산식을 린트가 추정하지 않는다).
  3. 문장 `date` 달이 `missing` 인데 `N%`·`N%p` 를 말하면 오류(D-0086 보정 2). "발표되지 않았다" 류 문장(수치 없음)은 통과.
  4. 문장에 `series:` 참조가 둘이면 단위·값이 어느 레코드인지 자막의 레인 라벨(레코드 `label`)로 구분 — 구분 불가면 오류.
- 발음 텍스트의 숫자 금지(03 §4)는 그대로. 대조는 자막 텍스트로 한다.
- 되돌리기: lint 분기 하나 + 테스트.

## 테스트(≥ 5)
series 참조 통과·미존재 오류·값 일치·불일치(반올림 경계 포함)·%p 계산·missing 달 오류·이중 참조 구분.

## DECISIONS 후보(Fable 기록)
D79: 위.
