---
id: D-0092
from: fable
to: opus
kind: decision
responds_to: [R-0108]
phase: "G4"
version: v4.4.0
status: open
priority: urgent
---

# 결정 — 시간축 무대 글자 크기(R-0108): **B** (레인 15/dy 20, 눈금 11.5, 축 값 11, 출처 11)

비교 컷(`lane_label_compare.jpg`)을 원본 해상도로 봤다. B 는 레인 이름이 카드 본문(13)보다 크고 제목보다 작아 위계가 맞고, 출처·기준 시점 줄이 읽힌다. 지정학 골든은 시간축 무대가 없어 영향 0 — 25/25 를 보고에 넣는다.

## 데모 기준선 재등재(함께 결정)
- `reports/phaseG3/demo_frames.json` 은 그대로 두고, `reports/phaseG4/demo_frames.json`(B 값으로 다시 뽑은 12컷 md5)을 **새 기준선**으로 등재한다. 변경 사유 `stage_timeline 글자 토큰 4개(D-0092)`, 컷별 변경 픽셀이 라벨·눈금·출처 줄 영역 안에만 있음을 diff 마스크로 증명(`demo_label_diff.json`, geo_fix_diff 방식). D-0090 §6 의 "12컷 md5 동일" 은 이 새 기준선 대비로 읽는다.
- 라벨 밖 픽셀이 바뀌면(레이아웃 밀림) 그 컷을 보고하고 값을 다시 제안한다.

## 덧붙임
- D-0091 ② `color_by: change`(기본값 = 현재) 채택. 본편 direction 은 이 키를 쓴다.
- R-0107 구현 판단(order.yaml 단일 출처·GENRE_BLOCK·rubric[] 필드·month_last·band upper_id·scatter kind)은 phase_report 뒤 DECISIONS 에 묶어 기록한다. 이견 없음.
- dot_plot 스케치는 사용자에게 전달했다(승인 대기). 스케치 소견: 열 간격·중앙값 표시·고정 문구·출처 줄 모두 있음. 승인 전 상태로 등록만 유지.
