---
id: R-0299
from: opus
to: fable
kind: progress
responds_to: [D-0315]
phase: "E4"
version: v7.4.0
commit: 3c5013f0
status: awaiting_user
---

# T2 덤벨 스케치 1컷(D-0315 §1-3 순서 2)

## 1. 스케치(artifacts `artifacts/econ-template-2026` c068fd2, 폴더 `t2_dumbbell/`)
- 인텔 부문 매출 2분기 → 3분기다. 레코드는 8-K 부문 표(INTC_SEG_DCAI_Q·CCG_Q·FOUNDRY_Q) 그대로다.
- 시간축 세계 안의 series 스타일 `dumbbell` 이다. 3분기 열 안에 부문 셋을 나란히 둔다. 독립 패널이 아니다(UF-135).
- 속빈 원 = 전분기, 채움 원 = 이번 분기, 사이는 선이다. 이름과 두 값은 열 오른쪽 지시선 라벨("DC 6.3→7.3")이다. 범례는 없다.
- accent 는 문장이 말하는 부문 하나다(12초 컷 DC 코랄).
- 감소(PC 8.9→8.1)는 흐린 채움 + down 윤곽이다. 라벨 글자는 잉크다. down 글자색은 코랄과 한눈에 같아서 뺐다(D-0314 §1-1 같은 이유).
- 컷: `frames/p_0006.00`(자라는 중) · `p_0012.00`(DC accent, 대표) · `p_0017.50`(PC 감소).

## 2. 구현(미등록 패치 `econ_sketch_v5.patch`)
- `SeriesEvent.style` 에 dumbbell·diverging 을 더했다. 둘 다 parts 를 읽는다(`PART_STYLES`).
- 열 분기 = series_id 레코드의 마지막 분기다. 기준은 dumbbell 전분기, diverging 전년 동기다(`pair_items`).
- 두 시점 값이 하나라도 없으면 렌더 전 오류다(P6).
- 규칙 키 5개를 `stage_timeline.bars` 에 더했다(pair_w_ratio·pair_dot_r·pair_line_w·pair_line_alpha·diverging_w_ratio). 감독 제안 값 성격이다.

## 3. 드러난 것
- 지시선 라벨이 오른쪽 축 값 열에 잘린다. 열 분기가 화면 오른쪽 끝에 가까우면 그렇다. 이 스케치는 무대 끝을 2027-06-30 으로 늘려 피했다.
  - T3 에서 [camera-bounds]·라벨 잘림 검사로 묶을지 판단이 필요하다.
- 열 하나만 차 있어 왼쪽이 비어 보인다. 본편에서는 같은 레인에 추이 층이 먼저 있으므로 문제가 아니라고 본다.
- 정직성 hard 2건(units_visible·as_of_visible)은 막대·쌓임과 같은 원인이다. T3 몫이다.

## 4. 다음
- diverging(부문 y/y ±%) 1컷. 이어 slope, 가이던스 범위.
