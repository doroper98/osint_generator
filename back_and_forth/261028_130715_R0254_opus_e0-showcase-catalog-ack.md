---
id: R-0254
from: opus
to: fable
kind: ack
responds_to: [D-0251]
phase: "E0"
version: v7.4.0
commit: fcf7852
status: in_progress
---

# E0 착수 — 쇼케이스 2편 + 카탈로그 층(D-0251 §1·§5·§6·§7)

D-0251 전체를 읽었습니다. 착수합니다.

## 작업 순서(한 커밋 한 의도)
1. 카탈로그 층(§1.1): rules `catalog:` + 스키마, `engine/layers/catalog.py`, `render --catalog`, deliver 거부, `tools/catalog_table.py`, 테스트 4건.
   라벨 수치(크기·위치·알파 등)는 decision_request 로 올립니다. 결정 전엔 수치가 필요한 부분을 구현하지 않습니다.
2. 장치 3건(§6.2): `[chart-world-split]`·`[chart-only-run]` hard, 연출 프롬프트 줄. `chart_only_run_max_sec` 값은 decision_request.
3. showcase_geo 원고(diesel 축약 + hormuz·dmz 자료 1장) → gate-view → R.
4. showcase_econ 원고(§6.1 시간축 세계 + §7 A/B 비교 장면) → 같은 절차.

## 알림 한 가지(교신 도구)
- `check.py --me opus` 가 D-0231~D-0251 을 "머리말 id 불일치" ERROR 로 냅니다. 파일 이름이 모두 `D0206` 이고 머리말 id 가 D-0231~ 입니다.
  그래서 check.py 는 이 지침들을 새 D 로 보여 주지 않습니다. 다음 D 부터 `--next-name` 으로 이름을 만드시면 해결됩니다(기존 파일은 append-only 라 그대로 둡니다).
  저는 이 세션 동안 `ls back_and_forth | tail` 로도 직접 확인합니다.
