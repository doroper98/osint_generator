# 덤벨 — 열 확대 인셋 판 (D-0318 §1)

분기 매출 막대(INTC_REV_Q, 최신 accent) 위 3분기 열을 리더선으로 가리키는 인셋. 인셋 안 = 같은 레코드(INTC_SEG_DCAI·CCG·FOUNDRY_Q) 2분기 → 3분기.

- `island kind: column_detail`(style dumbbell). engine.direction.build 가 차트 아일랜드 레인에 매달린 층(series detail)으로 바꾼다 — 같은 뷰·카메라
- 머리 줄 "2026년 2분기 → 3분기 · 부문 매출(십억 달러)"(기간·단위는 코드). 글자 12px · 점 반지름 6px(rules island.column_detail)
- 해당 열 = accent 띠, 리더선은 열 변 → 인셋 변 수평(값 라벨을 가로지르지 않음)
- 자리 = 인셋 생애 모든 프레임에서 열을 가리지 않는 첫 자리(side_order left·right, 예측). 카메라는 열을 화면 오른쪽 1/3 에 둔다
- 문장마다 accent 만 옮기는 이어 붙임(사이 페이드 없음). 등장 0.5초 미끄럼+페이드, 값 0.6초 자람
- 바탕 불투명(뒤 막대·글자 비침 없음), 높이 = 레인 플롯 높이(레인 이름·출처 줄을 덮지 않음)
- 컷: p_0007.50(등장) · p_0012.00(DC accent, 대표) · p_0017.50(PC 감소)

econ_sketch_v7.patch — v6 + column_detail(dumbbell·diverging·slope·range 인셋). dumbbell·diverging·slope 는 인셋 전용(열 안 직접 그리기 폐기).
