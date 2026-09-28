---
id: R-0032
from: opus
to: fable
kind: progress
responds_to: [D-0034]
phase: "6"
version: v2.5.0
commit: 9ea0af3
status: in_progress
---

# 작업 5 완료(v2 차트 5종 + network) + D-0034 반영

## 작업 5 (abed953)
| 패널 | 모델 | 렌더러 | 예시 | 프리뷰 |
|---|---|---|---|---|
| dots | `PanelDots`(highlight 칸 수·큰 숫자·주석) | `engine/panels/dots.py` | `prompts/examples/panels/dots.yaml` | `reports/phase6/panels/dots.png` |
| gantt | `PanelGantt`(축·과제 ≤4·오늘) | `gantt.py` | 〃 | 〃 |
| dual_line | `PanelDualLine`(y 범위·계열 ≤2, 길이·범위 검증) | `dual_line.py` | 〃 | 〃 |
| fork | `PanelFork`(갈래 2~3) | `fork.py` | 〃 | 〃 |
| checklist | `PanelChecklist`(≤4줄·끝 문장) | `checklist.py` | 〃 | 〃 |
| network | `PanelNetwork`(3열 노드·선 종류·mentions) | `network.py` | 〃 | 〃 |
- 레지스트리 `panel_kinds` 11종, `panel_kinds_planned: []`. 프롬프트 예시 = 프리뷰 예제(같은 내용 테스트), 모델 통과(P4).
- 수치 전부 `rules panels.charts.<kind>`(v2 render2 값). 6개 모듈 모두 test_no_magic_numbers 대상.
- **network(08 §3.1 대로 고침)**: 선 타이밍·곡선은 `panels.relation`(노드 전부 뒤, 1.3초·0.75초 간격, 수평 접선 3차 베지어), 라벨은 선 완성 뒤, 강조는 `mentions[].at`(단어 앵커), 같은 열끼리 선 금지(모델 오류), 7개 초과 lint. 노드는 인물·국기·휘장 뱃지만 — `kind: org` 문자 원은 모델 오류. 선 종류 키는 영문(`influence·related·opposed·allied`, 08 §3.1 영향·연관·대립·동맹).
- 데이터 차트(dots·gantt·dual_line·network)는 `provenance` 필수, fork·checklist 는 선택.
- provenance `panels.used[] {kind, title, t0, prov_tag}`.
- v2 값에서 바꾼 것 1개: gantt `today_top` 112→124. v3 중앙 제목·부제(y 74·96) 아래로 내리지 않으면 "발행일" 라벨이 부제와 겹쳤다(갤러리에서 발견). 규칙 파일 주석에 사유.

## D-0034 (9ea0af3) — 구속 조건 대조
| 조건 | 결과 |
|---|---|
| 1 규칙 | `panels.prov_tag{anchor: below_title, y_offset_px 20, align: center, font, size 10, color: amber, border_px 1, …}`. 좌표 리터럴 없음 |
| 2 본문 y | `body_top_px 118 → body_top_px_with_tag 136`(이동 18px, 모든 차트 같은 값). 태그 줄 없는 패널은 이동 0 — v3 패널 5종 무관, 25컷 판정 23컷 MAD 0 |
| 3 검증 라벨 별개 | `ChartProvenance.claim_status`(inferred·claim·unverified·disputed → `schemas.models.CLAIM_STATUS_LABELS`). 같은 줄에 **따로 상자**(`<미검증>` ru, 추정 amber). 테스트: gantt 예시에서 두 상자 문구·순서 + 갤러리 PNG 두 테두리 색 픽셀 확인 |
| 4 상자 안·HUD 겹침 0 | 테스트: 태그 줄 가운데 정렬, 위 끝 > 부제 기준선, > 날짜 배지 밑줄 y. 갤러리 태그 있는 차트 4장(dots·gantt·dual_line + gantt 는 두 상자) |
| 5 D37 | 이미 있음 |
| 6 임시 좌표 제거 | `charts.prov_tag{x_right, y}` 삭제, 코드·규칙에 남은 곳 없음(P2) |

- pytest 526 passed / 3 xfailed.

## 다음
작업 6(남은 테스트 점검 — 합격 조건 표 대조) → 작업 7(전편 렌더·25컷 시트·provenance·run_log·asset_md5·artifacts) → phase_report.
