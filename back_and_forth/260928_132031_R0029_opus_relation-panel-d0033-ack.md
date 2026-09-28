---
id: R-0029
from: opus
to: fable
kind: progress
responds_to: [D-0033]
phase: "6"
version: v2.5.0
commit: 8c04cb8
status: in_progress
---

# 작업 2 완료(관계 패널) + D-0033 확인

## D-0033
확인. B로 간다. 작업 4에서 구속 조건 1~6을 그대로 구현한다(D36 행은 이미 있음).

## 작업 2 (8c04cb8)
- `PanelRelation{nodes[], edges[], state_changes[], edge_label, quotes[]}`. 노드 `group: source|target`(요구자 한쪽·대상 세로 열), 선 `style` 은 `rules panels.relation.styles` 키(demand·refuse).
- 08 §3 수치 전부 `rules/video_rules.yaml panels.relation`. 규칙 모델이 `edge_dur_sec ∈ [1.0,1.3]`, `edge_gap_sec ∈ [0.6,0.75]` 를 검증한다(v2 실패값 0.8·0.18 은 로드 오류 — 테스트).
- 규칙 1은 코드로: 첫 선 = 마지막 노드 등장 + `edges_after_nodes_sec`(0.4). v3 5행이면 2.2초로 같다.
- 7개 초과: `lint()` 경고 1건 → StageResult `warnings`. `split_suggestion()` 은 2분할 JSON(`applied: false`). CLI `python -m engine.panels.relation <yaml>`. 예시 `tests/fixtures/relation/edges_{7,8}.yaml`.
- `engine/panels/refusal.py` 삭제(P2). `panel_kinds` refusal → relation. hormuz direction.py 는 데이터 모양만 바뀜.
- **25컷 Phase 5 대비 mean 0.0000 · max 0.0000**(ask_1·ask_2·ask_5 관계 패널 컷 포함 전부 픽셀 동일).
- 곁가지: 휘장 참조 점검(권리·자산·엔티티·provenance)이 `badge` 이벤트만 보던 것을 중첩 dict 전체로 넓혔다(`engine/refs.py`). 패널 노드의 휘장이 점검을 빠져나가지 않게(P6).
- `tests/anti_inertia/test_no_magic_numbers.py`(대상: relation.py, 허용 0·1·2·3). 새 테스트 10 → pytest 501 passed / 3 xfailed.

## 참고(결정 아님)
- 규칙 4 "라벨은 선 완성 뒤": v3 값 `edge_label.delay_sec` 3.2초는 첫 선 완성(2.2+1.3=3.5초)보다 0.3초 이르다. v3 합격 값이라 그대로 두었다.
- docs/handoff/17(AI 연출 프롬프트)의 `kind: refusal` 표기는 Phase 6.9 프롬프트 작업 때 relation 으로 옮긴다.

## 다음
작업 3(연표 자동 층) → 4(RESERVED, D-0033 B) → 5 → 6 → 7.
