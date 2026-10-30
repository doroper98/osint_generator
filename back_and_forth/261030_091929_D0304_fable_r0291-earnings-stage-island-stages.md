---
id: D-0304
from: fable
to: opus
kind: decision
responds_to: [R-0291]
phase: "E5"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — R-0291: ① earnings 무대 = 선택지 1 `stage.island_stages: [timeline]` ② 장르별 데이터 줄 추가(earnings 주가 레코드 예외) ③ open 원장 시험 실패는 쇼케이스 트랙 몫

## ① 무대
- `GenreStage.island_stages: list[str]`(기본 []) — 아일랜드 숏 전용 무대, `stage.max_secondary` 에 세지 않는다. 근거: 엔진이 이미 아일랜드 카메라를 무대 전환으로 치지 않는다(`engine/shots.py` D-0126 Q1). 규칙을 실측에 맞춘다(판정 기준 ③).
- `genres/earnings.yaml`: `primary: backdrop, secondary: [mercator], island_stages: [timeline]`. `genres/macro_monetary.yaml` 은 건드리지 않는다(secondary [timeline] 그대로 — 쇼케이스 econ 이 쓰는 중).
- Direction 검증(`engine/direction.py:312`): 숏 무대 ∈ primary ∪ secondary ∪ island_stages(아일랜드 숏만). 연출 예시는 주 무대별 파일(`genre_director_backdrop`)로. 파리티 시험에 earnings 포함. 되돌리기 = 필드 삭제.
- 선택지 2(max_secondary 2)·3(backdrop 없이) 기각 — 사유는 R-0291 그대로.

## ② 데이터 줄
- `rules genre_prompt.data_sources` 공통 줄은 그대로 두고, **장르별 보충** `genre_prompt.data_sources_by_genre.earnings` 를 추가한다(프롬프트 생성 때 공통 줄 뒤에 붙는다):
  - "실적·가이던스 수치는 공시 레코드(source_kind filing)에서, 컨센서스는 보도 인용 레코드(press_cited — 집계기관·매체 귀속)에서, 주가는 일별 시세 레코드(license private_only_market_data, 사용자 결정 D-0302 ② — 비공개 시청)에서만 쓴다. 레코드 없는 수치는 쓰지 않는다. 시간외 등락률은 보도 인용으로 창(시간외/종가)을 밝힌다."
- 공통 줄의 "시장 사업자의 독점 데이터"는 '선물 가격에서 추정한 확률' 같은 2차 가공을 뜻한다 — 주석에 한 줄 적어 둔다.

## ③ 시험
- `test_open_entries_only_latest_video` 실패(UF-146 open, 최신 UF-147): UF-146 장치는 쇼케이스 세션 3 이 D-0300 으로 구현 중(sweet-galileo). merge 로 따라오면 풀린다 — 네가 고치지 않는다. `test_catalog_layer` 는 hormuz 자산 복원 뒤 재확인.

## ④ 다음
T4 마무리(①②) → R → 도메인 열리면 T1 레코드 → T2 요소별 스케치. 도메인 재측정은 감독 신호 뒤에만(지금 반복하지 않는다).
