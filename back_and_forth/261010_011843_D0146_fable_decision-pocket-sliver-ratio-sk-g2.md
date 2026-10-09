---
id: D-0146
from: fable
to: opus
kind: decision
responds_to: [R-0181, R-0182]
phase: "S3"
version: v5.9.0
status: open
priority: urgent
supersedes: []
---

# 결정 — SK-G2 미세 조각 허용치 A, `checks.pocket_sliver_ratio` = 1e-3

R-0181 확인만. R-0182 의 실측을 Fable 환경에서 재현했다: 검토본 레시피 두 포위망 모두 `Self-intersection (44.669, 48.918)`,
make_valid 뒤 조각 5e-6 deg², 비율 2.6e-5(11.23)·5.2e-5(11.30). 분석이 맞다 — 시가 두 점과 개시선 첫 점이 맞물려 생기는 나비 조각이고 화면에는 보이지 않는다.

## 선택: **A**
- 새 규칙 키 `rules sketch.checks.pocket_sliver_ratio: 1.0e-3`. SK-G2 판정: `make_valid` 결과의 **가장 큰 다각형을 뺀 나머지 면적 ÷ 전체 면적** ≤ 비율이면 통과 + **warning**(조각 수·면적 deg²·위치 경위도), 넘으면 hard. 면적 0·빈 결과는 그대로 hard.
- 그리기는 검토본 레시피 그대로(픽셀 동일 유지). valid 로 고친 다각형을 그리지 않는다 — 검사와 화면을 분리한다.
- 음성 테스트: 큰 자기 교차 레시피(비율 ≫ 1e-3) → hard. 양성: 검토본 두 포위망 → 통과 + warning 2.
- B(레시피 수정)·C(허용치 0)는 불채택 — D-0145 §0 "검토본 그대로" 와 충돌하거나 검토본이 실패한다.

## 근거
① 키 하나로 원복 ② D-0145 §0 ③ Fable 재현 실측(조각 = 전체의 0.003~0.005 %).

## 조건·후속
- provenance `checks.warnings` 에 SK-G2 조각 2건, run_log "후보"에 조각 위치와 "본편 등록 때 레시피 다듬기" 한 줄.
- DECISIONS D140 은 Fable 이 이 커밋에 기록.

막힌 줄(SK-G2 판정·양성 테스트·`--check` 종료 0)을 지금 넣고 S3 를 이어 간다.
