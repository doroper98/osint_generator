---
id: R-0030
from: opus
to: fable
kind: progress
responds_to: []
phase: "6"
version: v2.5.0
commit: a6d012b
status: in_progress
---

# 작업 3(연표 층)·4(RESERVED, D-0033 B) 완료

## 작업 3 (89fc0c5)
- 사건에 `side` 가 없으면 날짜 순으로 가장 안쪽 빈 층(직전 사건 반대쪽 먼저, ±1~±3). 라벨 상자 = 날짜·라벨 중 넓은 폭(실측). 같은 층 겹침과 **줄기가 안쪽 층 라벨을 뚫는 경우**를 모두 피한다. 빈 층이 없으면 경고(`timeline-no-free-layer`).
- **데이터가 준 `side` 는 그대로 쓴다**(P8). hormuz 는 v3 층을 데이터로 갖고 있어 12·13컷 MAD 0. 준 층끼리 겹치면 경고(`timeline-overlap`). hormuz v3 층은 경고 0.
- 참고: hormuz 연표에서 층을 지우고 자동 배치하면 `[-1, 1, -1, 2, -1, 1, -1, 1]` — v3 `[-1, 1, -2, 2, -1, 1, -2, 2]` 와 다르다(v3 는 겹침이 아니라 리듬으로 −2 를 골랐다). 둘 다 겹침 0.
- 연표 수치 전부 `panels.timeline`, test_no_magic_numbers 대상에 추가.

## 작업 4 (a6d012b) — D-0033 구속 조건 대조
| 조건 | 결과 |
|---|---|
| 1 좌표 | `lon=PL["busan"][0], lat=PL["busan"][1]`(129.04, 35.10). 라벨·R·accent 무변경 |
| 2 규칙 | `panels.reserved{badge_strategy: push, push_gap_px 8, push_directions [left, down, left-down], max_push_px 160, marker_label_strategy: hide, lead_sec 0.45}`. 최소 이동(같으면 목록 순). 초과 → hide(카드 존재도만큼 흐림), provenance `reserved.avoidance[]` |
| 3 expected_deltas | 15_review_0·16_review_1 등재(reason·decision D-0033·old/new_lonlat·회피 결과). 새 기준 `reports/phase6/golden_delta/`. golden_compare 가 좌표 쌍도 받게 고침 |
| 4 증명 | `reports/phase6/reserved_before_after.png` (a) OFF (b) ON (c) Phase 5 (d) 퇴장 뒤. 겹침 **15컷 4464→0 px², 16컷 4094→0 px²**(`reserved/reserved_proof.json`). 방향 down, 이동 134·112 px |
| 5 시간 구간 | 영역 존재도 = 카드 구간 1, **들어올 때 lead 0.45초 먼저**, 나갈 때 카드 페이드와 함께. 181.0초 프레임에서 제자리(이동 0) |
| 6 D36 | 이미 있음 |

- 25컷(Phase 5 대비): 판정 23컷 mean 0.0000 · max 0.0000, 의도된 차이 3컷(09·15·16).
- 구현 중 잡은 것 두 가지:
  - 기사 카드가 나가며 선택지 카드가 들어오는 168.2초에 목표가 바뀌어 **한 프레임 24 px 점프**가 있었다 → 이동 = 존재도 층별 적분(∫push({z: a_z ≥ s})ds)으로 바꿔 연속. 남은 최대 프레임 간 이동은 카드 퇴장 때 0.45초 복귀(15 px/프레임).
  - 처음엔 뒤쪽도 lead 를 줘서 장면 컷 뒤에 옛 카드 영역이 남아 이재명 뱃지를 5프레임 흐렸다 → 뒤쪽은 카드 페이드만. 지금 이재명 뱃지 기록은 **2프레임 hide**(254.58~254.62초, 장면 컷 순간 카드 알파 0.08이 남은 구간, 뱃지 자체도 퇴장 페이드 중) — provenance 에 그대로 남긴다. 25컷에는 없는 시각.
- 곁가지: 카드·기사 카드의 상자 계산을 `card_geom`·`article_geom` 으로 뽑았다(그리기와 영역이 같은 값을 쓴다, 픽셀 무변경).
- pytest 513 passed / 3 xfailed.

## 다음
작업 5(v2 차트 5종 + network) → 6 → 7(전편·갤러리·provenance).
