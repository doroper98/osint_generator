<!--
tier: 2
last_synced_with: v5.10.0
ssot_for: [phase-roadmap]
depends_on: [../GOAL.md, ../CHANGELOG.md, handoff/13_IMPLEMENTATION_PLAN_FOR_CLAUDE_CODE.md, handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, handoff/TAGS_PENDING.md]
last_review: 2026-09-29
-->

# 13 — Implementation Roadmap (v2 개편, v4.0.0)

v2 개편의 Phase 계획 정본은 [handoff 13](handoff/13_IMPLEMENTATION_PLAN_FOR_CLAUDE_CODE.md)(구현 계획)과 [handoff 19](handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md) §6(실행 요강·버전 보정)이다.
버전은 D39(Phase 6.8부터 재보정)·D64(Phase 11 = G3 개정 MAJOR)를 따른다. 합격 판정은 back_and_forth의 Fable review가 한다.
합격 커밋은 [TAGS_PENDING](handoff/TAGS_PENDING.md)에 한 줄씩 남는다. 여기서는 순서와 상태만 적는다.

| Phase | 버전 | 내용 | 상태 |
|---|---|---|---|
| 0 | v2.0.0 | 관성 차단 — 레거시 삭제(archive 보존)·규칙 SSOT·프롬프트 파일·관성 방지 테스트 | 합격 |
| 1 | v2.0.1 | 골든 재현(v3『호르무즈와 한국』) | 합격 |
| 2 | v2.1.0 | 모듈 분해·계약(engine·script·audio) | 합격 |
| 3 | v2.2.0 | 지오 일반화(`geo.prep`) | 합격 |
| 4 | v2.3.0 | 원고·음성(린트·edge/ElevenLabs·단어 정렬) | 합격 |
| 5 | v2.4.0 | 뱃지·엔티티·권리(D5 제한 휘장 → 국기) | 합격 |
| 6 | v2.5.0 | 패널·카드 데이터화 | 합격 |
| 6.5 | v2.5.5 | 사진·영상·컷아웃·기사 카드 | 합격 |
| 6.8 | v3.0.0 | 오케스트레이터 통합(상태 머신·게이트 2개·provenance, manifest sv 2) | 합격 |
| 6.9 | v3.1.0 | 선언형 연출·결정적 검사·AI 연출가·시각 검수 | 합격 |
| 6.95 | v3.2.0 | 소스 인테이크(기사·X 캡처·claims 인용 대조) | 합격 |
| 7 | v3.3.0 | 카메라 자동화 보조 | 합격 |
| 8 | v3.4.0 | 오디오(BGM 레지스트리·교차 페이드·오디오 QA) | 합격 |
| 9 | v3.5.0 | 번들 어댑터(D7 제안 문서) | 합격 |
| 10 | v3.6.0 | 해상도·성능(1080p·장치 변환·청크 병렬) | 합격 |
| 11 | v4.0.0 | 문서·정리·GOAL G3 개정(D4) | 진행 중 |
| G1~G4 | v4.0.x | 골든 최종 검증·장르 확장([handoff 20](handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md) §12, G3-17 무대 연속성) | 예정 |

범위 밖(사용자 결정, handoff 13): 텔레그램 봇 인테이크, 유튜브 자동 업로드.

v1 로드맵(Phase 0~11, v0.1.0~v1.2.2 — Command Center·Remotion·9개 Review Gate)은 폐기됐다. 원문은 git 이력(`0173642` 판)과 `archive/hyperframes-briefing`에 있다.
