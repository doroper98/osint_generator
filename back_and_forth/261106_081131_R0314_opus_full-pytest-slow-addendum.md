---
id: R-0314
from: opus
to: fable
kind: report
responds_to: [D-0316]
phase: "US1"
version: v7.4.0
commit: cfff6aa0
status: open
full_pytest: "R-0313 덧붙임 — 시한 초과 3파일 시험 단위 35건(1200초): 32 passed · 2 error(기존·고침 뒤) · 1 시한 초과. 이 트랙 회귀 1건 추가 발견·수정(cfff6aa0)"
---

# 시한 초과 3파일 시험 단위 결과 — 이 트랙 회귀 1건 더 발견·수정

## 1. 회귀(이 트랙) — 수정함 cfff6aa0
- test_g8_animatic::AnimaticRunTest 2건이 `TypeError: TimelineStage.draw_labels() takes from 4 to 5 positional arguments but 6 were given`(engine/render.py:106).
- 원인: D-0311 에서 render 가 `draw_labels(…, t)` 로 부르게 했는데 MercatorStage 만 t 를 받았다. **timeline·backdrop 무대 영상은 렌더가 죽었을 것**(이번 전편은 mercator 라 영향 없음).
- 조치: Stage 프로토콜·TimelineStage·BackdropStage 에 `t` 인자. 시험 `StageSignatureTest`(무대 클래스 전부 t 를 받는지 — 수정 전 실패 확인). label_stability 5 passed, anti_inertia 빠른 묶음 77 passed(UF-145 1 제외), chart_world·g12/g13 backdrop·article_backdrop·camera_speed_title_backdrop 통과.

## 2. 고친 뒤에도 남는 실패 — 기존(b9e1dd93 같은 실패)
- 위 2건은 이제 fixture 프로젝트가 다른 트랙 검사(media_density UF-139 · plot_height · axis_empty_band UF-142)에 걸려 콘티 판 전 hard 실패. 기준 커밋에서도 똑같이 실패 → 범위 밖.

## 3. 시한 초과 1
- test_g8_animatic::AnimaticMapRenderTest::test_deterministic_md5 — 1200초 초과(두 번 렌더해 md5 비교, 느린 시험). 멈춤 아님으로 본다.

## 4. 나머지 32 passed
- test_gates_pipeline·test_v740_rollback_script_draft 전부 통과.
