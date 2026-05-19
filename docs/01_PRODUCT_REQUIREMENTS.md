<!--
tier: 2
last_synced_with: v0.1.0
ssot_for: [product-requirements]
depends_on: [00_PROJECT_BRIEF.md, ../GOAL.md]
last_review: 2026-05-19
-->

# 01 — Product Requirements

본 문서는 사용자 관점의 기능 요구사항을 명세합니다. 합격 기준은 `GOAL.md G3`에 위임합니다.

## 1. 사용자 역할

| 역할 | 책임 |
|---|---|
| Owner (사용자) | 주제 지시, Dynamic Intake에서 자료 선택, 9개 Review Gate 승인 |
| Orchestrator | 전체 파이프라인 지휘, task 배정, 상태 전이 |
| Agent | 주제 분석·리서치·대본·scene 설계·썸네일 기획 등 인지형 작업 |
| Worker | 단일 산출물 생성 (영상 다운로드, 캡처, 지도, 차트, TTS 등) |

## 2. 핵심 사용자 시나리오 (Top 5)

### S1. "한 줄 지시로 18분 영상"

사용자가 텔레그램에 한 줄을 보낸다 → 24시간 내에 검수 가능한 초벌 영상을 받아본다.

### S2. "내 자료 + AI 보완"

사용자는 자기가 모은 X 링크 12개만 제공하고, 나머지 (지도, 기사, 차트, 과거 비교)는 AI Delegation으로 위임한다.

### S3. "Worker 품질 튜닝"

`draft_debug.mp4`를 보고 어느 scene이 어떤 Worker에서 만들어졌는지 추적하여 해당 Worker만 개선한다.

### S4. "권리 위험 사전 차단"

영상에 들어간 모든 영상 클립의 `rights_status`를 확인하고, `do_not_use`인 경우 자동 제외한다.

### S5. "장기 채널 운영"

같은 채널에 50편의 영상을 만들면서 썸네일 톤·내레이션 톤·자막 폰트가 일관되게 유지된다.

## 3. 비기능 요구사항

| 항목 | 요구 |
|---|---|
| 운영 OS | Windows 10/11 우선, Linux 호환 |
| Python | 3.11+ |
| Node | 20 LTS (Remotion) |
| 추적성 | 모든 scene에서 source_id, asset_id 역추적 가능 |
| 재현성 | 같은 manifest로 다시 렌더 시 결과가 일치 |
| 검수 | 9개 Review Gate 모두 승인 로그 기록 |
| 안정성 | 한 Worker 실패가 전체 파이프라인을 중단시키지 않음 |
| 오프라인 | 인터넷 없이도 manifest만으로 재렌더 가능 |

## 4. 우선순위

[docs/13_IMPLEMENTATION_ROADMAP.md](13_IMPLEMENTATION_ROADMAP.md)의 Phase 순서를 따릅니다.
