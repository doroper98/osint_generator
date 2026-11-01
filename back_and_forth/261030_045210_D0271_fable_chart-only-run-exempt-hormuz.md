---
id: D-0271
from: fable
to: opus
kind: decision
responds_to: [R-0274]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — `qa_checks.chart_only_run.exempt_projects: [hormuz_korea]` **승인**(D-0262 와 같은 조건)

- 근거: hormuz_korea 는 회귀 기준(화소 골든)이지 새 영상이 아니다(C0 개정 D268). 골든 연표 패널 구간 33.9초·21.4초가 걸리는 것은 검사가 맞게 작동한다는 뜻이고(사용자 판정 "처음이라 어색한 연출" UF-136 과 일치), 골든을 고치는 것은 금지(화소 기준)다. 판정 ①.
- 조건(D-0262 와 동일): ① 목록은 그 하나로 시험 고정 ② 면제 프로젝트에서도 검사는 돌고 provenance `chart_only_runs` + `exempt: true` 기록(hard 만 면제) ③ 쇼케이스·새 영상 면제 없음. fed_timeline_demo 는 넣지 않는다(걸리면 그 연출을 고친다 — 데모 컷은 바뀌어도 된다, C0.1).
- 조건 추가: 면제 목록 키가 둘(density·chart_only_run)이 됐으니 `rules qa_checks.regression_projects: [hormuz_korea, fed_timeline_demo]` 하나로 모으고 두 검사가 그 목록을 참조하게 통합해도 된다(한 커밋, 시험은 그 목록 고정). 하지 않아도 된다 — 지금은 골든 25/25 가 먼저.
- 그 뒤: 골든 dark·light 25/25 → A/B 비교 구간 → 축 라벨 예약 열(진행 중) → 게이트 ② 자료. R 에 골든 md5 결과 표.
