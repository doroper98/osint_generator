---
id: R-0619
from: opus
to: fable
kind: progress
responds_to: [D619]
phase: "B"
version: v7.4.0
commit: 75fcbc1f
status: awaiting_user
---

# 프리뷰 v2 — 사진 배경 위 데이터 무대 = 아일랜드 상자, checks hard 0, artifacts 68213ff0 `preview_v2/`

## 1. 변경(D619)
- `engine/island.py` `on_backdrop(R)` 를 더했습니다. 주 무대가 backdrop 이면 구성·차트 아일랜드가 무대 표면 팔레트여도 표준 상자를 그립니다. 그림자, 바탕 `island_rgb(stage_timeline.bg_rgb)` × `island.fill_alpha`, 테두리, `island.radius` 입니다.
  - 새 수치는 없습니다. 무대 표면(D-0328)은 시간축·지도 주 무대에서 그대로입니다.
- 아일랜드 크기는 지금 무대 영역 그대로입니다(center_tall·left_tall).
- `[data-stage-bare-on-backdrop]` hard 를 더했습니다. 렌더와 같은 draw_frame + on_backdrop 으로 상자를 그리고, 가운데 알파 < fill_alpha × 0.9 면 실패합니다.
  - 시험 `tests/test_data_stage_on_backdrop.py`: 상자 있음 통과, R-0618 상태(on_backdrop False) 실패, 비 backdrop 무대 제외.
- UF-304 guards 에 data_stage_bare_on_backdrop·시험·structure_text_offscreen 을 더했습니다. 원장 176(미보호 0) 입니다.
- 관련 시험·anti_inertia 를 통과했습니다.

## 2. 결과
- 콘티 판 v3 md5 2ce129dd(같은 원고 1dc67dcb·변형 A·상자)입니다.
- 프리뷰 checks hard 0, warning 5 입니다(R-0618 과 같음).
- 점검표: 자동 통과 83, 실패 0, 눈 93, 미실행 4 입니다.
- 시트에서 구성 무대(01·02·04·05·08·10·12~14)와 시간축(09)이 짙은 상자 안에 있습니다. 배경 사진은 상자 밖 테두리로 보이고, 막대·글자가 또렷합니다.

## 3. 남은 것
- 배경 위 글자 대비 측정 검사는 영상 전달 뒤 첫 작업입니다(D619).
- 배경 피사체 검사(D616 ④)도 전달 뒤 첫 작업입니다.
- 게이트 ② 판단을 기다립니다. 승인 뒤 전편 720p → 전달 묶음입니다.
