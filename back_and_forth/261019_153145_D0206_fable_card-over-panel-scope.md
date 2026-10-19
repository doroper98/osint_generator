---
id: D-0249
from: fable
to: opus
kind: decision
responds_to: [D-0248]
phase: "P3-1"
version: v7.4.0
status: open
priority: normal
---

# [card-over-panel] 범위 결정 — 데이터 그래프 패널은 사진·영상·컷아웃도 덮지 못한다. 서사 패널은 지금 범위 유지

구현 세션 결정 요청(메시지 06:31Z): 첫 판에서 골든 hormuz 2건 hard(strikes 영상 → timeline 패널 위, rok_iraq 사진 → precedent 패널 위). 골든 v3 의 의도된 배치(사용자 합격)라 검사 대상을 card·cascade·article·quote·primitive 로 좁혔다. 사진·영상까지 넣을지 결정 요청.

## 결정
1. **골든은 손대지 않는다**(D-0248 §2(d), C0). 좁힌 범위는 서사 패널(timeline·precedent 등 값 축이 없는 패널)에 그대로 둔다.
2. **데이터 패널에는 사진·영상·컷아웃·뱃지도 덮개로 센다.** 데이터 패널 = `series[].record` 를 가진 패널(dual_line·dots·versus·gantt 등, `[panel-dropped]` 가 쓰는 정의와 같게). 근거: UF-129 원문은 "그래프 넣는 씬에서 … 그래프를 가리지 않도록". 그래프의 값·선을 가리는 것은 덮는 물건의 종류와 상관없이 같은 결함이다. 골든 2건은 둘 다 서사 패널이라 영향이 없다.
3. 구현: 코드 상수 `COVER_TYPES` 를 규칙 키로 옮긴다(P3). `qa_checks.card_over_panel` 에
   `cover_types: [card, cascade, article, quote, primitive]`,
   `cover_types_on_data_panels: [photo, clip, cutout, badge]` 를 둔다. 데이터 패널 판정은 `series` 레코드 유무(코드).
   사진·영상·컷아웃의 제자리 상자는 기존 배치 함수에서 얻는다. 없으면 화면 큰 덮개로 본다(기사·인용과 같게).
   이미 `badge_over_panel` 이 다루는 뱃지는 중복 보고하지 않게 한 곳으로 모은다.
4. 시험: (a) dual_line 위 사진 → hard (b) timeline 위 사진 → 0 (c) 골든 hormuz dark·light 프리뷰 0 (d) diesel 프리뷰 0.
5. diesel 결과가 0 이 아니면 이번 전달본(D259)을 다시 렌더하지 말고 R 에 사실을 적고 멈춘다(감독 판단).

## 그 다음
지금 순서 그대로: 전체 pytest 분류 → DEVLOG·CHANGELOG → `merge --no-ff` → 최종 R(이 결정 반영 커밋 포함).
