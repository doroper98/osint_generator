<!--
tier: 2
last_synced_with: v5.5.1
ssot_for: [project-brief]
depends_on: [../README.md, ../GOAL.md]
last_review: 2026-09-29
-->

# 00 — Project Brief

## 한 줄 요약

OSINT 자료를 받아 15~20분 분량의 세계 이슈 브리핑 영상을 **재현 가능·추적 가능·검수 가능** 한 방식으로 만들어내는 파이프라인 시스템.

## 이 시스템이 아닌 것

- 영상 한 편을 빨리 만드는 도구 (속도가 목표가 아님)
- 라이브 영상 편집 GUI
- 일반 유튜브 영상 자동 생성기
- 국내 정치 / 인물 음모론 콘텐츠 도구

## 이 시스템이 맞는 것

- 같은 채널을 1년 이상 운영하기 위한 **반복 제작 시스템**
- 모든 소스가 `source_id`로 역추적되는 **추적 가능한 시스템**
- Worker별 품질 튜닝이 가능한 **개선 가능한 시스템**
- 사용자와 AI가 명확히 역할을 나누는 **분업 시스템**

## 채널 운영 시나리오

1. 사용자가 Telegram/CLI에 "최근 3개월 러시아 본토 피격 18분" 같은 한 줄 지시.
2. Orchestrator가 주제를 분석해 `intake_plan.json` 생성.
3. 사용자는 Dynamic Intake Page에서 자기가 가진 자료만 넣고, 나머지는 AI Delegation.
4. 4개 Worker Slot에서 자료 수집·검증·자산 생성이 병렬 진행.
5. 사람 승인 게이트 2개(원고·프리뷰)를 거친다. 코드 검사·AI 시각 검수가 그 사이를 채운다(v3.0.0).
6. `final.mp4` + `thumbnail.png` + `youtube_metadata.json` 산출.

## 최소 산출물

[GOAL.md G1](../GOAL.md#g1-최종-산출물-final-outputs)을 참조.

## 성공 기준

[GOAL.md G3](../GOAL.md#g3-mvp-acceptance-criteria-v2-17)의 34개 항목.
