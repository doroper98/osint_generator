---
id: R-0124
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G6.5"
version: v4.7.0
commit: 06cf4d3
status: in_progress
---

# G6.5 결정 요청 — D2(b) `[geo-unsourced]` 검사의 "좌표 근거" 정의

D2(a)(연출 문법 한 줄)는 06cf4d3 으로 넣었습니다. D2(b)는 그대로 구현하면 기존 합격 영상이 hard 로 걸립니다.

## 쟁점

D-0104 는 "marker·route·paths 좌표는 `geo.yaml`(출처 있는 지명·경계) 또는 claim 의 위치 수치에서 와야 한다"고 했습니다. 저장소 실측은 다릅니다.
- **geo.yaml 에는 지명이 없습니다.** bbox·admin1·지형 티어뿐입니다(hormuz·랫클리프 확인).
- 좌표는 전부 **연출(direction.yaml)의 `places`·`paths`** 에 있습니다. 사람이나 AI 연출가가 적은 근사값입니다.
  - hormuz(v3 골든): places 8(호르무즈·서울·울산·부산·하르그·아덴 …), paths 2(항로 `route` 20점·`cheong` 18점), marker 8, route 4.
  - 랫클리프: places 6, paths 1, marker 13, route 2. fed_policy·데모: 시간축 무대라 좌표 없음(marker 12·6 은 날짜·레인).
- 그래서 문자 그대로의 검사는 hormuz 항로(사용자 합격 v3)부터 "근거 없음"으로 막습니다.

## 선택지

- **B-1 (권고)**: 지명 사전을 새로 두고, "사건 지점"만 엄격하게 봅니다.
  - `data/gazetteer.yaml`(이름 → 좌표·출처: Natural Earth populated places / ports / 해협, 허용 오차 km).
  - 지도 무대 marker·place 가 사전 항목 오차 안이면 통과(도시·항구·해협). 밖이면 `sub` 에 "좌표 비공개"(또는 규칙 문구) 의무, 아니면 hard.
  - paths: 이동 경로(항로)는 양 끝이 사전 항목이면 통과(중간점은 근사 표시로 인정). 경계선 이름(규칙 목록: 군사분계선·국경 …)을 단 `route` = hard(연출 프롬프트 한 줄 + 검사).
  - 위험: 사전 준비(hormuz·랫클리프 지명 약 14개 + Natural Earth 도시) 작업이 있습니다. 골든 무변경 확인 필요.
- **B-2**: 연출 `places`·`paths` 에 출처 필드를 의무화합니다(`places: {hormuz: {lonlat: [...], source: "ne:..."|"claim:c12"|"approx"}}`).
  - `approx` 는 marker `sub` "좌표 비공개/근사" 의무. 스키마 변경이고, 기존 네 편 direction 을 고쳐야 합니다(연출 파일 변경 = 골든 회귀).
- **B-3**: 이번엔 warning 으로만 넣고(근거 모를 좌표 목록 기록), hard 전환은 사전(B-1)과 함께 G8 로 미룹니다. dmz M5·M8 같은 사고는 D2(a)와 프롬프트 한 줄("경계선을 route 로 그리지 않는다", "좌표 모르는 사건 지점엔 좌표 비공개")로 먼저 줄입니다.

권고 근거: 판정 기준 ①(B-1 은 규칙·데이터 추가라 되돌리기 쉬움, B-2 는 스키마 변경) ②(D-0104 의 hard 의도 유지) ③(저장소 실측 — geo.yaml 에 지명 없음).
시간이 우선이면 B-3 이 가장 가볍습니다.

## 막히는 범위

- 결정 대기: D2(b) 검사·프롬프트 줄.
- 계속: D3(W1 체크리스트)·D4(reopen)·D5(미사용 미디어 삭제)·S1(LLM-AP 기록)·회귀·오디오 재측정.
