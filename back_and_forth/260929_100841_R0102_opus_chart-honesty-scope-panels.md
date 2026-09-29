---
id: R-0102
from: opus
to: fable
kind: decision_request
responds_to: [D-0085]
phase: "G3"
version: v4.3.0
commit: baa757c
status: in_progress
---

# 결정 요청 — 정직성 검사 4종의 패널 적용 범위(D-0084 §1-5)

D-0085(월드 y 척도 A) 확인 — 그대로 구현한다.

## 쟁점
D-0084 §1-5 는 대상을 "series 이벤트 + 수치 축 패널(dots·gantt·dual_line·timeline)"로 정했다.
실측: hormuz(`direction.yaml:267`)·랫클리프(`:328`)는 둘 다 **timeline 패널**을 쓴다. 날짜 축뿐이고 값·단위·출처 줄이 없다.
문언대로 네 패널 모두에 4검사를 걸면 두 예제가 `units_visible`·`as_of_visible` hard 가 된다.
지침은 "기존 패널이 걸리면 규칙 해석을 decision_request, 예제를 고치지 않는다"이다. 그래서 묻는다.
실측 보조: dual_line 은 단위 필드가 없다(`y_prefix` 만). dots 는 `unit` 필드가 있다. 두 패널의 출처는 `ChartProvenance`(08 §9 추정 태그)로 이미 화면에 나온다. as_of 필드는 어느 패널에도 없다.
막대·이중 축·로그 척도를 그리는 요소는 지금 **없다**(series style 은 step|line).

## 선택지

### A. 축 종류로 적용 범위를 나눈다 — 권고
- **series**: 4검사 전부 hard. 단위(레인 라벨 = 레코드 unit, %/%p 대조), as_of·출처 줄(레코드에서 코드가 그림), 레인당 계열 ≤ 3, 압축 구간 ↔ 물결 표시.
- **값 축 패널(dots·dual_line)**: `series_limit_3`(dual_line 계열 수)·`units_visible`(dots `unit`, dual_line 에 선택 필드 `unit` 추가 — rules data.units 안)·`chart_honesty` %/%p. `as_of_visible` 은 08 §9 체계로 충족한다(출처 목록 = 출처 줄, 없으면 "추정 · 출처 미기재" 태그가 화면에 뜸).
- **날짜 축 패널(timeline·gantt)**: 값 축이 없어 units·as_of·series_limit 는 해당 없음. checks 상세에 "n/a(날짜 축)"로 적는다(조용한 생략 아님). chart_honesty 의 압축·막대 항목만 본다(해당 표시 없음 → 통과).
- 막대 0 기준선·이중 축·로그 척도: 검사 함수는 차트 메타(`kind`·`baseline`·`axes`·`log_scale`)를 보고 판정한다. 지금은 그런 요소가 없어 합성 메타로만 주입 테스트한다. 새 요소가 생기면 메타를 채워야 레지스트리 테스트를 통과하게 한다.
- 결과: hormuz·랫클리프 hard 0, 예제·렌더러 무변경.
- 되돌리기: 대상 표 한 곳.

### B. 문언 그대로 네 패널 전부
- hormuz·랫클리프 timeline 패널이 hard. 고치려면 예제(금지) 또는 timeline 패널 렌더러(출처 줄 추가 → 골든 변경, 금지)를 바꿔야 한다. 비권고.

### C. 기존 패널은 warning, series 만 hard
- 규칙이 요소마다 등급이 달라진다. 새 패널이 warning 뒤로 숨을 수 있다(P6 취지에 어긋남).

## Opus 권고 — A
- ② 문서: 20 §5.3 의 대상은 "수치 차트"다. 날짜 축 패널은 값 단위·기준 시점이 없는 요소다. 08 §9 는 패널 출처 표기를 이미 정했다.
- ③ 실측: 두 예제의 패널은 날짜 축뿐. 골든·예제 무변경 조건(D-0084 §3) 유지.
- ① 되돌리기: 대상 표 한 곳, dual_line 선택 필드 하나.

## 근거 자료
- `engine/events.py` PanelTimeline·PanelGantt(날짜만)·PanelDots(`unit`)·PanelDualLine(`y_prefix`, unit 없음)·ChartProvenance.
- `engine/panels/base.py:59-65` prov_tag_text("추정" / "추정 · 출처 미기재").
- D-0084 §1-5 "hormuz·랫클리프 hard 0 … 예제를 고치지 않는다".

## 막히는 범위
- 기다림: 작업 5 의 패널 대상 부분.
- 계속함: 작업 3 TimelineStage(D-0085 A), 작업 4 series 레이어, 작업 5 의 series 대상 검사와 합성 주입 테스트.
- R-0101(CPI 빈 달)도 결정 대기다.

## §7 해당 여부
아니다.
