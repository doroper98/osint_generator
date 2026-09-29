---
id: R-0100
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G3"
version: v4.2.0
commit: 9e8e4f7
status: in_progress
---

# 결정 요청 — TimelineStage 월드 y 척도(레인 간격 1.0 ↔ 등방 View)

## 쟁점
D-0084 §1-3 은 "x = 기준일로부터 일수, y = 레인 인덱스(간격 1.0), bounds = [start, 0, end, n_lanes]" 이다.
그런데 현 `engine/projection.py:View` 는 가로·세로에 **같은 배율 s** 를 쓴다(지도용 등방 투영).
그대로 넣으면 View 가 `w ≤ (ymax − ymin) × 854/480` 으로 클램프한다. 레인 3개면 화면 폭 최대 **약 5.3일**이다.
반대로 w = 2,000일이면 레인 한 칸이 0.2px 이 된다. 문언 그대로는 구현이 불가능하다.
월드 y 를 화면에 어떻게 옮길지 정해야 한다.

## 선택지

### A. 무대가 세로 척도를 고정한다(비등방, 문언 그대로) — 권고
- TimelineStage 가 `y_px_per_unit` = `rules stage_timeline.lane_h`(설계 px, 지침의 "레인 높이" 토큰)를 준다.
- View 는 이 값이 있으면 세로 배율을 그 값으로, 가로 배율은 W/w 로 쓴다. 세로 클램프는 레인 총높이 기준이다.
- 카메라 w 는 **시간 폭만** 바꾼다. 확대해도 레인 띠 높이·계열 세로 척도는 그대로다. 카메라 y 는 레인이 화면보다 클 때만 의미가 있다.
- 결과: y = 레인 인덱스·간격 1.0·bounds 문언 그대로. 핀 확대 = 시간 확대 + 날짜 LOD(20 §6). 값 라벨·단위가 모든 줌에서 읽힌다.
- 위험: View 에 분기 하나. Mercator 는 속성이 없어 **옛 코드 경로 그대로**(골든 25/25 로 증명).
- 되돌리기: View 분기·무대 속성 삭제.

### B. 등방 View 유지, 월드 y 를 '일' 단위로 늘린다
- y = 레인 인덱스 × pitch(일). pitch 는 전체 구간을 볼 때 레인이 `lane_h` 가 되도록 코드가 계산한다.
- 카메라 확대 = 지도처럼 두 축 동시 확대. 핀에서 30일 폭으로 확대하면 레인이 화면의 수십 배로 커진다.
- 계열의 세로 척도가 줌마다 바뀐다 → 눈금·값 라벨을 줌마다 다시 계산해야 한다. 정직성(§5.3 축 표기)에 불리하다.
- 문언(간격 1.0·bounds)과 어긋난다. View 무변경.
- 되돌리기: stage_timeline.py 한 곳.

## Opus 권고 — A
- ② 핸드오프 문서: D-0084 §1-3 문언(레인 간격 1.0, bounds, "레인 높이" 토큰)과 20 §6("확대 시 일 단위 라벨")을 그대로 만족한다.
- ① 되돌리기: View 분기 하나, Mercator 경로 무변경. 골든 25/25·랫클리프 20/20 으로 검증한다.
- 정직성: 레인의 세로 척도가 영상 내내 하나다. 차트 벽처럼 확대할 때 축이 바뀌는 문제가 없다.

## 함께 확인할 구현 세부(A·B 공통, 이견 없으면 이대로)
1. 카메라 앵커: `camera: {date: "YYYY-MM-DD", lane?: 숫자, w: 일수}`. 지도 `lon·lat·place` 와 셋 중 하나만. Camera 모델에 선택 필드 2개.
2. 핀 = 기존 `marker` 에 앵커 `date`·`lane`(레인 id 문자열)을 더한다. `lon·lat` 과 둘 중 하나만. `attach_world` 는 무대의 앵커 키로 일반화.
3. 압축 구간: 월드 x = 압축을 적용한 일수(구간 안은 `일수 × factor`). `to_world`·`from_world` 가 왕복한다.

## 근거 자료
- `engine/projection.py:25-33`(View 클램프·단일 배율 s), `engine/stage.py:MercatorStage`(월드 y = ym(위도), '도' 단위로 x 와 같은 단위).
- D-0084 §1-3, docs/handoff/20 §2.3·§6.

## 막히는 범위
- 기다림: 작업 3 TimelineStage, 4 series 레이어, 6 실증 프로젝트.
- 계속함: §0 첫 커밋, 1 SeriesRecord·로더·fetch_series, 2 시리즈 2개, 5 정직성 검사 중 패널 대상 부분, 8 문서 일부.

## §7 해당 여부
아니다(엔진 구현 선택).
