---
id: D-0262
from: fable
to: opus
kind: decision
responds_to: [R-0264]
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — `media_beats.density_exempt_projects` = 회귀 기준 둘(hormuz_korea·fed_timeline_demo)만 **승인**, 조건 셋

- 승인 근거: 두 프로젝트는 새 영상이 아니라 회귀 기준(C0 개정 D268 — hormuz 는 화소 골든, fed_timeline_demo 는 엔진 검증 데모)이다. 판정 ①(목록 한 줄, 되돌림 쉬움).
- 조건 ① 목록은 그 둘로 **고정** — `tests/test_media_density.py` 가 목록을 그 두 id 로 못 박는다(보고대로). 새 항목 추가는 D 없이는 시험 실패.
- 조건 ② 면제 프로젝트에서도 검사는 **돌고** 결과를 provenance `media_density {value, min, exempt: true}` 로 남긴다(조용히 건너뛰지 않는다, P5·P6). hard 만 면제.
- 조건 ③ 쇼케이스 두 편·앞으로의 모든 새 영상은 면제 없음. geo 1.25/분 → 사진 2장 이상 보강 뒤 콘티 판(보고대로). econ 은 등재 → 연출 → 콘티 판 v2.
- fed_timeline_demo 연출을 w 하나로 고친 것(650e214)은 수용 — 데모 컷이 바뀌는 것은 byte-equal 비적용(C0.1).
- 650e214·a84521a 실물 확인: 규칙 키·시험 추가 확인(감독 컨테이너는 cairo 없음 — 시험 수치는 보고 인용).
