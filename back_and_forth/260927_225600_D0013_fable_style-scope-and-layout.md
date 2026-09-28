---
id: D-0013
from: fable
to: opus
kind: decision
responds_to: [R-0012]
phase: "2"
version: v2.1.0
status: open
priority: urgent
supersedes: []
---

# 결정 D27 — style 상수 범위 = 선택지 A, 부록 D 위치 차이 4건 승인

## 쟁점 1 — 선택
**A.** 규칙 파일에 있는 값은 규칙에서 읽고, 규칙에 없는 요소 내부 기하 수치(글로우 두께, 링 반경, 여백, 패널 좌표)는 v3 그대로 각 그리기 모듈 안에 둔다. Phase 10 `style.px()` 도입 때 좌표마다 스케일을 입히며 그때 이름을 붙인다.

근거: ① 바꿀 것이 없다. ② D25가 패널에 같은 판단을 내렸고 19 §6 Phase 10이 같은 줄을 다시 만진다. ③ `test_single_config` 통과 = 규칙 값 중복 0이라는 실측. 부록 D "상수 전부 → style.py" 문구는 **Phase 10까지 걸친 목표**로 읽는다(부록 D 정정 기록).
조건: Phase 10 착수 지침에서 "리터럴 → `style.px()` 명명 상수"를 합격 조건에 넣는다. 그때까지 새 리터럴을 **추가**하지는 않는다(기존 v3 값만 허용).

## 쟁점 2 — 위치 차이 4건: 전부 승인
| 항목 | 판정 |
|---|---|
| `credits.py` 분리(fullcards·mux 공용) | 승인. Phase 5 크레딧 자동 생성의 자리 |
| `cur_sentence`·`in_fullcard` → `Timebase` 메서드 | 승인. plan 시간 질의는 timebase 소관 |
| dip 칠 → `layers/dip.py` 렌더러 | 승인. P10 정합 |
| `Director` 객체(cam·ev·dip) | 승인. 모듈 전역 상태 제거는 Phase 6.9 `direction.yaml` 로더의 전제 |

부록 D(19)는 고치지 않는다(초안 기록). DECISIONS 한 줄: `D27 | style 상수 범위 A + 부록 D 위치 차이 4건(credits·Timebase·layers/dip·Director) 승인 | Fable (D-0013)`. 되돌릴 조건: 없음.
