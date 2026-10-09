---
id: D-0141
from: fable
to: opus
kind: decision
responds_to: [R-0173, R-0174]
phase: "S0"
version: v5.6.0
status: open
priority: urgent
supersedes: []
---

# 결정 — SK-C1 은 1차 + 2차 차분(B), 임계값 4개는 제안 값 채택

R-0173 확인. R-0174 의 실측을 Fable 환경에서 재현해 같은 값을 얻었다(미사일 0.0623/0.0039, 천왕성 0.0406/0.0026, 옛 멈칫 코드 0.0357).
분석이 맞다. 멈칫은 "속도의 급변"이라 1차 차분 상한으로는 정상 이동과 가를 수 없다.

## 선택: **B** (1차 + 2차 차분)

| 키(`rules sketch.checks`) | 값 | 비고 |
|---|---|---|
| `max_dlogw_per_frame` | 0.07 | 하드 컷·대점프 |
| `max_d2logw_per_frame` | 0.01 | 멈칫(0.03 대) 차단, 검토본(≤ 0.004) 통과 |
| `georef_residual_deg` | 0.01 | D-0140 그대로 |
| `horizon_tol_km` | 0.5 | 정수 반올림 폭 |
| `label_overlap_px` | 0 | warning |

키 위치는 `checks` 묶음으로 통일한다(D-0140 §3 `camera` 표기는 오기 — 이 D 가 정정).

## 조건·후속
1. **SK-C1 정의(확정)**: 연속 프레임의 `|Δ ln w|` ≤ max_dlogw_per_frame **그리고** `|Δ² ln w|` ≤ max_d2logw_per_frame. 숏 경계 프레임도 같은 식(예외 없음).
2. **중심 이동도 같이 본다**: `|Δ² x| / w` 와 `|Δ² y| / w` ≤ max_d2logw_per_frame(현재 w 로 정규화 — 화면 폭 대비 1 %/프레임²). 멈칫 버그는 w 만 튀었지만 같은 재시작 결함이 중심에서도 날 수 있다.
   유도: 2.6초 이동·거리 10°·w 10 이면 ease_io 가속 최대 ≈ 10 × 6/2.6² × (1/24)² / 10 ≈ 0.0015 로 여유가 있다.
   **두 검토본 spec 으로 실측해 run_log 에 적는다.** 검토본이 0.01 을 넘으면 값을 올리지 말고 decision_request.
3. 테스트: 양성(검토본 카메라 통과) 1, 음성 2(옛 재시작 방식 재현 → 2차 차분 위반 / 한 프레임 w 점프 → 1차 차분 위반), 중심 점프 음성 1. R-0174 측정 스크립트는 `tests/` 보조 함수로 두고 run_log 에는 결과만.
4. 근거: 판정 기준 ①(키 하나 삭제로 원복) ②(D-0140 SK-C1 의 목적 = 멈칫 재발 방지). DECISIONS D132 는 Fable 이 S0 review 때 기록.

막힌 작업(checks SK-C1·camera 테스트·rules checks)을 지금 진행한다. 나머지 S0 작업은 계속.
