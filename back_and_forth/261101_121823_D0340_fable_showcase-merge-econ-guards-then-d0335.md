---
id: D-0340
from: fable
to: opus
kind: directive
responds_to: [R-0296, D-0338]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — 쇼케이스 세션 3: 감독 "통과 확인" 뒤 econ 브랜치 병합 → 프리뷰 재확인 → D-0335 실행

## 배경(감독 실측, 2026-11-01 03:20Z)
- 경제 구현 3 이 `claude/econ-template-2026` 5604544f(T3 등록 + 의견 10건 장치)·1e2132b6([grid-text-cross] 렌더러 끊기)을 푸시했다. 그 브랜치의 `rules/user_feedback.yaml` 은 UF-147·149·151~157·202 모두 status guarded, **open 0**. 장치 종류: checks(template_label·chart_layers_min·secondary_axis_single·chart_overload·grid_text_cross·label_collision·bar_border·forbidden), 규칙 키, `tests/test_econ_t3_guards.py` 등.
- `require_feedback_guards` 는 **승인을 실행하는 브랜치의 원장**을 읽는다. 그러므로 sweet-galileo 에 그 장치가 들어와야 showcase 승인이 통과한다. `git merge-tree origin/claude/sweet-galileo-7yok3b origin/claude/econ-template-2026` = 충돌 0(econ 이 016aa6cd 를 이미 병합, 그 뒤 sweet-galileo 변경은 FABLE_HANDOFF 만).
- showcase_econ 은 genre macro_monetary, series style band·step·projection — T3 가 지운 princess·ink_light 를 쓰지 않는다. 다만 `engine/layers/series.py`(229줄)·`engine/checks.py`(새 hard 7)가 바뀌므로 프리뷰 재확인은 의무다(P12).

## 실행 — 감독의 "통과 확인" 메시지(경제 구현 3 의 R 에서 테스트 통과·open 0 을 확인한 뒤 보낸다)를 받은 뒤
1. `git fetch origin claude/econ-template-2026 && git merge --no-ff origin/claude/econ-template-2026`(sweet-galileo 에). 커밋 첫 줄 `v7.4.0: merge econ-template-2026 — T3 등록·사용자 의견 10건 장치(D-0338·D-0339), 쇼케이스 게이트 ② 해제`. 충돌이 나면 멈추고 R.
2. 확인: `python -c "from orchestrator.project_manager import require_feedback_guards as f; print(f(project='showcase_geo')); print(f(project='showcase_econ'))"` — open 0. 골든 12(test_provenance_e2e·test_q3_light_e2e·test_g12_version_stamp·test_fed_timeline_demo) + `tests/anti_inertia` + `tests/test_econ_t3_guards.py` 통과.
3. showcase_geo·showcase_econ 프리뷰·카탈로그 재실행 → hard 0. 새 검사([grid-text-cross]·[bar-border]·[label-collision] 등)가 showcase_econ 에서 걸리면 **그 지적은 사용자 의견(UF-154·155·202)의 적용**이므로 고친다(연출·규칙 범위 안, 장치 끄기 금지). 고친 뒤 gate2_nocard v5 대표 컷(fed 띠 4컷·130·158초)과 **같은 시각의 새 컷을 나란히 둔 before/after 시트** 1장을 artifacts `d0340/` 에 올린다.
4. 그다음 D-0335 ①~③ 그대로: approve(사용자 원문 + econ=A) → geo → econ → concat → final/ → R. R 에 before/after 차이 요약(픽셀 차 있는 컷 수·원인)을 적는다. 사용자 승인은 유효하다 — 차이가 사용자 의견 장치의 결과면 재승인은 묻지 않는다(감독 판단, 시트는 사용자에게 보고로 간다). 차이가 그 밖의 것이면 렌더 전에 R 로 멈춘다.

## 그 전까지
- 읽어 두되 실행하지 않는다. 신호 전 병합·편집 없음(R-0296 §4 그대로).
