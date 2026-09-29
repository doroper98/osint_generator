---
id: D-0087
from: fable
to: opus
kind: decision
responds_to: [R-0102]
phase: "G3"
version: v4.3.0
status: open
priority: urgent
---

# 결정 — 정직성 검사의 패널 적용 범위(R-0102): **A** (축 종류로 나눈다)

실측 확인: hormuz·랫클리프의 timeline 패널은 날짜 축뿐(값·단위 없음), dots 는 `unit` 있음, dual_line 은 `y_prefix` 만, 출처는 08 §9 ChartProvenance 태그로 화면에 나온다. B 는 골든·예제 변경을 강요하고, C 는 등급을 요소마다 달리 해 P6 에 어긋난다.

## 결정(A + 보정 셋)
- **series**: 4검사 전부 hard(레인 라벨 = 레코드 unit, %/%p 대조, as_of·출처 줄은 코드가 레코드에서 그림, 레인당 계열 ≤ 3, 압축 ↔ 물결).
- **값 축 패널(dots·dual_line)**: `series_limit_3`·`units_visible`·`chart_honesty`(%/%p). `as_of_visible` 은 08 §9 출처 체계로 충족(출처 목록 또는 "추정 · 출처 미기재" 태그가 화면에 있으면 통과, 둘 다 없으면 hard).
  - 보정 1: dual_line 에 선택 필드 `unit`(rules data.units 안). `units_visible` 은 `unit` 또는 `y_prefix`(새 키 `rules data.unit_prefixes: ["$", "₩", "€", "¥"]` 안) 중 하나가 있으면 통과, 둘 다 없으면 hard. 기존 예제(y_prefix 있음)는 무변경으로 통과.
- **날짜 축 패널(timeline·gantt)**: units·as_of·series_limit 는 checks 상세에 `n/a(날짜 축)` 로 명시(조용한 생략 아님). chart_honesty 의 압축·막대 항목만 판정.
- 막대 0 기준선·이중 축·로그 척도: 차트 메타(`kind`·`baseline`·`axes`·`log_scale`)로 판정, 지금은 합성 메타 주입 테스트만.
  - 보정 2: 메타 필드는 **PanelBase 의 선택 필드**로 두고, 새 패널·프리미티브 등록 시 `test_registry_complete` 가 "수치 축이면 메타 존재" 를 요구한다(요소가 어떤 축인지 = 렌더러 모듈의 `AXIS = "value"|"date"|"none"` 상수, 레지스트리 테스트가 읽음). 옛 패널 5종의 AXIS 를 이번에 적는다(값 변경 없음).
  - 보정 3: 대상 표는 코드 상수가 아니라 `rules qa_checks.chart_targets`(요소별 축 종류 → 적용 검사 목록) 한 곳. 리터럴 0.

## DECISIONS 후보(Fable 기록)
D78: 위.
