<!--
tier: 1
last_synced_with: v0.3.3
ssot_for: [project-goals, acceptance-criteria, prohibitions]
depends_on: [README.md]
last_review: 2026-05-19
-->

# GOAL

본 시스템의 최종 목적과 성공 기준을 정의합니다. 이 문서는 SSOT(Single Source of Truth)입니다.
어떤 기능도 본 문서의 목표나 합격 기준에 우선할 수 없습니다.

---

## G1. 최종 산출물 (Final Outputs)

하나의 프로젝트가 완료되면 다음 산출물이 모두 생성되어야 합니다.

| 파일 | 설명 |
|---|---|
| `final.mp4` | 업로드용 최종 영상 (Debug Layer 없음) |
| `draft_debug.mp4` | Pre-production Debug Layer가 표시된 내부 검수 영상 |
| `draft_preview.mp4` | 사용자 검수용 초벌 영상 (Debug Layer 없음) |
| `thumbnail.png` | 최종 선택된 썸네일 |
| `youtube_metadata.json` | 제목·설명·태그·챕터·카테고리 |
| `source_registry.json` | 모든 소스의 정규화 등록부 |
| `qa_evidence_report.json` | 주장·근거·검증 결과 |
| `render_report.json` | 렌더 모드별 결과 보고서 |
| `approval_log.json` | 9개 Review Gate 승인 기록 |
| `project_manifest.json` | 프로젝트 메타·상태·경로 인덱스 |

## G2. 지원 주제 (Topic Scope)

| 카테고리 | 예시 |
|---|---|
| 지정학 | 미중 갈등, 대만해협, 중동, 에너지 운송로 |
| 전쟁/군사 | 러·우 전쟁, 드론 공격, 정유시설 타격, 방공망 |
| 경제/금융/산업 | 유가, 환율, 해운 운임, 반도체, 공급망 |
| 정보전/해외 음모론 | 해외 이슈 한정. 국내 정치/인물 음모론은 범위 외 |
| 자연재해/지진 | 일본·대만·중국·한반도, 류큐 해구, 난카이 해곡 |

## G3. MVP Acceptance Criteria (v2 §17)

다음 34개 항목이 모두 충족되어야 v2 MVP로 인정합니다. 본 목록은 변경 시 v{X+1}로 메이저 버전이 올라갑니다.

1. `run_pipeline.bat` 실행 시 Orchestrator Command Center Layout이 열린다.
2. Command Center는 방식 B (단일 Textual TUI)로 구현된다.
3. Orch CLI Log, Job Dashboard, Worker Slot 4개가 동시에 표시된다.
4. Worker CLI는 별도 창이 아니라 subprocess로 실행된다.
5. Worker CLI 로그는 각 Worker Slot 패널에 실시간 표시된다.
6. Telegram 또는 CLI 주제 입력으로 프로젝트가 생성된다.
7. `intake_plan.json`이 생성된다.
8. Dynamic Intake Page가 `intake_plan.json`을 기반으로 렌더링된다.
9. 사용자는 각 항목별로 AI Delegation을 선택할 수 있다.
10. `source_intake.json`이 생성된다.
11. `task_queue.json`이 생성된다.
12. Worker Slot Manager가 task를 Worker Slot에 배정한다.
13. Worker CLI는 `task_result.json`을 생성한다.
14. `source_registry.json`이 생성된다.
15. `source_completeness_report.json`이 생성된다.
16. `research_dossier.json`이 생성된다.
17. `episode_blueprint.json`이 생성된다.
18. `full_script.json`이 생성된다.
19. `scene_manifest.json`이 생성된다.
20. `scene_manifest`에는 `worker_provenance`가 포함된다.
21. TTS가 생성된다.
22. TTS Pronunciation QA가 수행된다.
23. 최소 1개 지도 장면이 생성된다.
24. 최소 1개 Source Card가 생성된다.
25. 최소 1개 Article Capture Scene 또는 Video Source Frame이 생성된다.
26. `remotion_job_{debug,preview,final}.json` 세 가지가 모두 생성된다.
27. `draft_debug.mp4`에는 Pre-production Debug Layer가 표시된다.
28. `draft_preview.mp4`에는 Debug Layer가 없다.
29. `final.mp4`에는 Debug Layer가 없다.
30. `thumbnail_manifest.json`이 생성된다.
31. 사용자 승인 로그가 `approval_log.json`에 남는다.
32. 모든 JSON은 `schema_version`을 가진다.
33. 모든 주요 산출물은 Pydantic 모델로 검증 가능하다.
34. 실패 시 시스템은 중단 대신 `needs_user_upload` 또는 `needs_user_confirmation` 상태로 전환할 수 있다.

## G4. 금지사항 (Prohibitions)

이 규칙은 절대 위반할 수 없습니다.

1. Worker가 전역 pipeline state를 직접 전진시키면 안 된다.
2. Worker가 사용자에게 직접 질문하면 안 된다. (Orch CLI / Review Dashboard만 사용자와 상호작용)
3. Worker가 다른 Worker의 산출물을 임의 수정하면 안 된다.
4. Orchestrator 없이 task를 실행하면 안 된다.
5. Pydantic 모델 검증 없이 중간 산출물을 만들면 안 된다.
6. Pre-production Debug Layer가 `final.mp4`에 포함되면 안 된다.
7. 미검증 정보를 제목이나 썸네일에 사용하면 안 된다.
8. 권리 상태가 기록되지 않은 영상을 최종 영상에 삽입하면 안 된다.
9. TTS Pronunciation QA 없이 최종 음성을 확정하면 안 된다.
10. AI 생성 이미지를 기본 영상 자산으로 사용하면 안 된다.
11. Google Maps 약관 검토 없이 상업적 영상 자산으로 고정 사용하면 안 된다.
12. 사용자 최종 승인 없이 업로드하면 안 된다.

## G5. 비목표 (Non-goals)

- 라이브 방송 송출
- 실시간 자막 생성
- 영상 편집 GUI (모든 편집은 JSON manifest 기반 선언)
- 국내 정치 / 인물 음모론
- 영상 한 편을 빨리 만드는 것 (속도보다 추적성과 재현성)

## G6. 성공 지표 (Beyond MVP)

- 한 채널을 1년 이상 운영하면서 평균 영상당 사람 개입 시간이 줄어드는가
- Worker별 품질 튜닝이 가능한가 (Pre-production Debug Layer 기반)
- 소스가 100% `source_id`로 역추적 가능한가
- TTS Pronunciation QA 실패율이 0에 수렴하는가

---

이 문서의 변경은 [DOCS_GOVERNANCE.md](DOCS_GOVERNANCE.md)의 변경 전파 체크리스트를 따릅니다.
삭제는 금지되며, 폐기 항목은 `[deprecated]` 마크만 남깁니다.
