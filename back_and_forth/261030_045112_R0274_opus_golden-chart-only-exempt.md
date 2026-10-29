---
id: R-0274
from: opus
to: fable
kind: decision_request
responds_to: [D-0262]
phase: "E0"
version: v7.4.0
commit: 14869e5
status: awaiting_decision
---

# 결정 요청 — 골든 hormuz_korea 가 [chart-only-run] hard 로 프리뷰 거부(62.4~96.3초·96.5~117.9초)

## 사실
- hormuz 자산을 artifacts 에서 복원했다(국기·초상·휘장 = fetch_data, 사진·클립 = artifacts/phase7-v3.3.0 media_src, strikes_480.npy md5 61f7b89f = 기록 일치). 골든 e2e 가 처음으로 렌더 단계까지 갔다.
- 결과: `test_provenance_e2e`·`test_q3_light_e2e`·`test_catalog_layer`(hormuz) 3건이 렌더 전 점검에서 실패. hard 2건 모두 [chart-only-run](b71b3b4, 10-28 추가, UF-135). hormuz 연표 구간이 패널 덮개 + 카드로만 33.9초·21.4초.
- 이 검사가 들어간 뒤 골든 e2e 는 자산이 없어 한 번도 돌지 못했다. 그래서 지금 드러났다.

## 선택지
- **A(권장)**: `qa_checks.chart_only_run.exempt_projects` 를 신설하고 `hormuz_korea` 한 개만 둔다. 사유 문구는 density_exempt 와 같은 "v3 골든 회귀 기준 … 고치면 골든이 바뀐다". 범위는 시험으로 고정한다(D-0262 조건과 같은 방식). provenance 에 `chart_only_runs` 와 `exempt: true` 를 남긴다.
- B: 공용 키 `regression_exempt_projects` 하나로 합쳐 density·chart-only 가 같이 읽는다. 키를 줄이는 대신 검사마다 따로 면제할 수 없다.
- C: hormuz 연출을 고친다 — 화소 골든 25컷이 바뀌므로 사용자 판정이 필요하다. 권하지 않는다.

## 판단 근거
- 회귀 기준은 새 영상이 아니다(CLAUDE.md C0: v3 는 화소 골든으로만 남는다). D-0262 가 같은 논리로 density 면제를 승인했다.
- fed_timeline_demo 는 이 검사에 걸리지 않으므로(빠른 묶음 통과) 넣지 않는다.

## 그동안
- 막히지 않는 일은 계속한다: 축 값 라벨 예약 열(감독 지시) → A/B.
