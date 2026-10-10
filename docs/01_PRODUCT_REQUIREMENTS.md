<!--
tier: 2
last_synced_with: v5.13.0
ssot_for: [product-requirements]
depends_on: [00_PROJECT_BRIEF.md, ../GOAL.md]
last_review: 2026-09-29
-->

# 01 — Product Requirements

본 문서는 사용자 관점의 기능 요구사항을 명세합니다. 합격 기준은 `GOAL.md G3`에 위임합니다.

## 1. 사용자 역할

| 역할 | 책임 |
|---|---|
| Owner (사용자) | 주제 지시, 소스 넣기·확인, 승인 게이트 2개(원고·프리뷰) 판정 |
| Orchestrator | 전체 파이프라인 지휘, task 배정, 상태 전이 |
| LLM 워커 | 소스 판독·검증 초안·리서치·원고·연출·시각 검수([03](03_AGENT_ARCHITECTURE.md) §2) |
| 엔진 | 린트·음성·지오·렌더·검사·믹스·먹싱(결정적 코드, [10](10_RENDERING_PIPELINE_SPEC.md)) |

## 2. 핵심 사용자 시나리오 (Top 5)

### S1. "한 줄 지시로 18분 영상"

사용자가 텔레그램에 한 줄을 보낸다 → 24시간 내에 검수 가능한 초벌 영상을 받아본다.

### S2. "내 자료 + AI 보완"

사용자는 자기가 모은 X 링크 12개만 제공하고, 나머지 (지도, 기사, 차트, 과거 비교)는 AI Delegation으로 위임한다.

### S3. "Worker 품질 튜닝"

프리뷰 시트·`prev/checks.json`·`provenance.json`을 보고 어느 단계(원고·연출·자산·엔진)가 문제인지 추적해 그 단계만 고친다. 반복 지적은 규칙 파일 개정(사람 승인)으로만 반영한다(15 P11). (v1 `draft_debug.mp4` 방식은 v2.0.0 폐기)

### S4. "권리 위험 사전 차단"

영상에 들어간 모든 영상 클립의 `rights_status`를 확인하고, `do_not_use`인 경우 자동 제외한다.

### S5. "장기 채널 운영"

같은 채널에 50편의 영상을 만들면서 썸네일 톤·내레이션 톤·자막 폰트가 일관되게 유지된다.

## 3. 비기능 요구사항

| 항목 | 요구 |
|---|---|
| 운영 OS | Windows 10/11 우선, Linux 호환 |
| Python | 3.11+ |
| 렌더 | cairo·numpy·FFmpeg(`requirements-engine.txt`). Node 불필요(v2.0.0 Remotion 삭제) |
| 추적성 | 모든 문장에서 claim id → 소스, 모든 자산에서 권리 레지스트리 역추적 가능, 영상마다 provenance |
| 재현성 | 같은 manifest로 다시 렌더 시 결과가 일치 |
| 검수 | 사람 게이트 2개(원고·프리뷰) 기록 — manifest `gate_decisions` |
| 안정성 | 실패하면 그 상태에 멈추고 보고한다. 옛 스타일로 폴백하지 않는다(G4-20) |
| 오프라인 | 인터넷 없이도 manifest만으로 재렌더 가능 |

## 4. 우선순위

[docs/13_IMPLEMENTATION_ROADMAP.md](13_IMPLEMENTATION_ROADMAP.md)의 Phase 순서를 따릅니다.
