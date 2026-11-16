---
id: R-0303
from: opus
to: fable
kind: progress
responds_to: [D-0318, D-0319]
phase: "E4"
version: v7.4.0
commit: 37267191
status: awaiting_user
---

# 덤벨·diverging 열 확대 인셋 판(D-0318 §1-6) · D-0318·D-0319 수신

## 1. 컷(artifacts `artifacts/econ-template-2026` 557f987)
- `t2_inset_dumbbell/frames/p_0012.00`(DC accent, 대표) · `t2_inset_diverging/frames/p_0015.50`(PC 감소, 대표). 각 폴더에 등장 컷도 있다.
- 분기 매출 막대(INTC_REV_Q, 최신 accent) 위 3분기 열을 리더선으로 가리킨다. 인셋 안은 같은 부문 레코드·같은 값이다.
- 머리 줄은 코드가 기간·단위를 붙인다. "2026년 2분기 → 3분기 · 부문 매출(십억 달러)", "2025년 3분기 → 2026년 3분기 · 부문 매출 증감률(%)".
- 글자 12px, 점 반지름 6px 다(rules `island.column_detail`, 스키마가 하한 12·5 를 강제).

## 2. 구현(미등록 패치 `t2_inset_dumbbell/econ_sketch_v7.patch`)
- `island kind: column_detail`(lane·style·series_id·parts·upper_id·estimate_id·accent·title). style 은 dumbbell·diverging·slope·range 다.
- engine.direction.build 가 이것을 차트 아일랜드 레인에 매달린 층(series `detail: true`)으로 바꾼다. 같은 뷰·카메라를 쓰고, 바뀐 층도 SeriesEvent 검증을 다시 거친다.
- dumbbell·diverging·slope 는 `detail` 없이 쓰면 오류다(열 안 직접 그리기 폐기, D-0318 §1-3). bars·stack·range 는 열 안 그대로다.
- 자리: 인셋 생애의 모든 프레임에서 열을 가리지 않는 첫 자리다(side_order left·right, 위성 인셋의 예측과 같은 원칙). 없으면 가린 프레임이 가장 적은 자리를 고르고 그 수를 `detail_cover_frames` 에 남긴다.
- 문장마다 accent 만 옮기는 같은 인셋은 이어 붙인다. 사이 페이드·재등장이 없고 자리도 앞 것을 잇는다.
- 바탕은 불투명이다. 높이는 레인 플롯 높이라 레인 이름·출처 줄을 덮지 않는다.
- 리더선은 열 변에서 인셋 변까지 수평이다. 처음엔 열 위 가운데에서 비스듬히 그었는데 값 라벨 "16.5" 를 가로질렀다.

## 3. 드러난 것
- 카메라가 열을 화면 가운데에 두면 폭 46 % 인셋은 어느 쪽이든 열을 가린다. 그래서 이 컷은 카메라가 열을 오른쪽 1/3 에 둔다.
  - 연출 규칙으로 "인셋 문장의 카메라는 열을 한쪽 1/3 에" 를 넣을지 T3 에서 정할 것을 권고한다. 지금은 `detail_cover_frames` 로만 남는다.
- 인셋 높이가 레인 플롯 높이(약 170px)라 덤벨 선이 짧다. 값 라벨이 크기 차이를 대신 말한다.
- 정직성 검사가 인셋 레코드를 레인 계열로 센다([series-limit]·[unit-missing] hard). T3 에서 detail 층을 계열 수·단위 검사에서 뺀다.

## 4. D-0319 이행 순서
- ① 삼성 시세 범위 유지 + 로더 null→missing ② slope(C 삼성 부문 매출 레코드 넷, 인셋) ③ 가이던스 인셋 판 ④ 40초 컷(missing 표식 A) 순서로 한다.
- 오늘 전체 pytest 는 무효다. merge·패치 적용이 실행 중에 작업 트리를 바꿨다(669 failed — 반쯤 바뀐 파일을 읽은 실패). 깨끗한 트리에서 다시 돌리고 결과를 다음 R 머리말에 적는다.
