<!--
tier: 1
last_synced_with: v2.0.0
ssot_for: [project-goals, acceptance-criteria, prohibitions]
depends_on: [README.md, docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
-->

# GOAL

본 시스템의 최종 목적과 성공 기준을 정의합니다. 이 문서는 SSOT(Single Source of Truth)입니다.
어떤 기능도 본 문서의 목표나 합격 기준에 우선할 수 없습니다.

---

## G0. 최우선 미덕 — 영상미 (Cinematic Quality First)

osint_generator 의 **최우선 가치는 영상미**다: "정적 보고서를 화면에 박은 것"이 아니라
연출·움직임·맥락 강조가 살아있는 영상다운 영상. **구체 기준의 정본은 `docs/handoff/`(G7)**이며
기준 작품은 v3『호르무즈와 한국』 골든이다. 이전 영상 기준(섹션=장면, 고정 막, HyperFrames/Remotion
문법)은 v2.0.0에서 폐기됐다. 운영 규칙·되돌리면 안 되는 목록은 [CLAUDE.md](CLAUDE.md) C0.

**단 G4(검증·미검증 라벨·권리·TTS QA)와 사실 정확성 위에서** 추구한다 — 정확성을 깬 화려함은
금지.

## G1. 최종 산출물 (Final Outputs)

하나의 프로젝트가 완료되면 다음 산출물이 모두 생성되어야 합니다 (v2.0.0 — `docs/handoff/16` §6).

| 파일 | 설명 |
|---|---|
| `out/final.mp4` | 최종 영상 (트라이얼 480p / 최종 1080p) |
| `out/final.srt` | 자막 |
| `out/description.txt` | 설명문 (챕터·출처·크레딧) |
| `out/thumbnail_candidates/` | 썸네일 후보 |
| `out/provenance.json` | 이번 영상에 실제로 쓰인 기능·규칙 해시·프롬프트 해시·drops (`docs/handoff/15` P5) |
| `script.yaml` | 원고 (승인본에 `approved_at`) |
| `plan.json` | 문장 타임라인·음성·정렬 |
| `direction.yaml` | 연출 (버전별 보관) |
| `assets.lock.json` | 이 영상이 쓴 자산 목록·해시·권리 |
| `prev/sheet.jpg`, `prev/checks.json`, `prev/qa_verdict.v*.json` | 프리뷰 컨택트 시트·결정적 검사·시각 검수 판정 |
| `intake/sources.json`, `intake/claims.json` | 소스 레코드·주장-출처 매핑 |
| `project_manifest.json` | 프로젝트 메타·상태·경로 인덱스 |
| `approval_log.json` | 승인 게이트 2개(SCRIPT_APPROVAL·PREVIEW_APPROVAL) 기록 |

v1 산출물 표 (이력 보존):

| 파일 | 설명 |
|---|---|
| `final.mp4` | 업로드용 최종 영상 (Debug Layer 없음) |
| `draft_debug.mp4` | Pre-production Debug Layer가 표시된 내부 검수 영상 **[deprecated v2.0.0]** |
| `draft_preview.mp4` | 사용자 검수용 초벌 영상 (Debug Layer 없음) **[deprecated v2.0.0]** |
| `thumbnail.png` | 최종 선택된 썸네일 |
| `youtube_metadata.json` | 제목·설명·태그·챕터·카테고리 |
| `source_registry.json` | 모든 소스의 정규화 등록부 |
| `qa_evidence_report.json` | 주장·근거·검증 결과 |
| `render_report.json` | 렌더 모드별 결과 보고서 **[deprecated v2.0.0]** |
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

> [legacy — v1 MVP 기준. v2 개정안: docs/handoff/19 부록 C, 사용자 승인 대기(D4). 승인 전까지 합격 판정에 쓰지 않는다.]

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
19. `scene_manifest.json`이 생성된다. **[deprecated v2.0.0]**
20. `scene_manifest`에는 `worker_provenance`가 포함된다. **[deprecated v2.0.0]**
21. TTS가 생성된다.
22. TTS Pronunciation QA가 수행된다.
23. 최소 1개 지도 장면이 생성된다.
24. 최소 1개 Source Card가 생성된다.
25. 최소 1개 Article Capture Scene 또는 Video Source Frame이 생성된다.
26. `remotion_job_{debug,preview,final}.json` 세 가지가 모두 생성된다. **[deprecated v2.0.0]**
27. `draft_debug.mp4`에는 Pre-production Debug Layer가 표시된다. **[deprecated v2.0.0]**
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
10. AI 이미지 도구는 자산 제작에 사용할 수 있다 (v1.0.0 전면 개정 — 사용자 결정 2026-08-14,
    구 조항 "AI 생성 이미지 기본 자산 금지" 폐기). 단 다음 경계는 절대 조건이다:
    - **실존 인물·장소·사물 자산은 실사진(실자료)을 입력으로 한 가공만** 허용 — 입력 없이
      상상으로 사실을 그려내는 것은 금지 (예: 사진 없이 "시진핑을 그려줘" 금지).
    - 산출물은 **검수 게이트 통과 후 라이브러리에 고정**해 사용하고, 도구·입력 원본
      출처/라이선스·프롬프트를 manifest 에 기록한다 (C9 — 재현성은 라이브러리 고정으로 확보).
    - **자막·수치·검증 라벨 등 텍스트는 항상 코드 렌더** — AI 이미지 안에 사실 텍스트를
      그리게 하지 않는다 (글자 왜곡·수치 오염 방지).
    - (v2.0.0 추가, `docs/handoff/14` §2.2) **생성 이미지로 사실 자료를 대체하지 않는다**,
      **사상자를 식별할 수 있는 장면을 쓰지 않는다**, **출처 불명 자료를 쓰지 않는다**.
11. Google Maps 약관 검토 없이 상업적 영상 자산으로 고정 사용하면 안 된다.
12. 사용자 최종 승인 없이 업로드하면 안 된다.
13. 고정 막 구성·섹션=장면 1:1 구성을 쓰면 안 된다. 장면 수·길이는 원고가 정한다 (v2.0.0).
14. 화면 모서리에 날짜 외 요소(브랜드명·섹션 번호·섹션 제목)를 두면 안 된다.
15. 도장(스탬프)·비네팅을 쓰면 안 된다.
16. 문장마다 카메라를 이동하거나 줌 범프(튀어 오르는 줌)를 쓰면 안 된다.
17. 관계선을 동시에 한꺼번에 등장시키면 안 된다 (하나씩, 정돈되게).
18. AI 상투 문구(`rules/video_rules.yaml banned_phrases`)를 원고·자막에 쓰면 안 된다.
19. 발음(TTS) 텍스트에 숫자·기호를 넣으면 안 된다.
20. 실패 시 옛 스타일로 폴백한 출력을 내보내면 안 된다 — 해당 단계에서 중단하고 사용자에게 보고한다.

## G5. 비목표 (Non-goals)

- 라이브 방송 송출
- 실시간 자막 생성
- 영상 편집 GUI (모든 편집은 JSON manifest 기반 선언)
- 국내 정치 / 인물 음모론
- 영상 한 편을 빨리 만드는 것 (속도보다 추적성과 재현성)
- 쇼츠·콜라주 트랙 (보관만 — `archive/hyperframes-briefing`, v2.0.0)
- 텔레그램 봇 인테이크, 유튜브 자동 업로드 (엔진 안정화 후 별도 계획)

## G6. 성공 지표 (Beyond MVP)

- 한 채널을 1년 이상 운영하면서 평균 영상당 사람 개입 시간이 줄어드는가
- Worker별 품질 튜닝이 가능한가 (Pre-production Debug Layer 기반)
- 소스가 100% `source_id`로 역추적 가능한가
- TTS Pronunciation QA 실패율이 0에 수렴하는가

## G7. 영상 기준 정본 (v2.0.0)

영상 생성 기준(구성·카메라·타이포·화면 문법·오디오)의 정본은 `docs/handoff/` 문서 묶음이다.

- 읽는 순서: `KICKOFF_PROMPT.md` → `00_INDEX.md` → `01`(피드백 원문) → `15`(관성 방지) → `02`(구조·이관)
  → `16`(오케스트레이터 통합) → `13`(구현 계획) → `19`(실행 계획·판정) → `DECISIONS.md`.
- 영역별 기준: `03` 원고·TTS / `04` 지도 / `05` 카메라 / `06` 오버레이 / `07` 인물·국기·휘장·권리 /
  `08` 패널·카드 / `09` 타이포·HUD·자막 / `10` 오디오 / `11` 렌더·QA / `14` 미디어 / `17` AI 연출·시각 검수 /
  `18` 소스 인테이크.
- 골든 기준: `docs/handoff/golden/`(문장 앵커 기준 프레임 25장). 동작 원본: `docs/handoff/reference_code/v3_hormuz_korea/`.
- 규칙 SSOT: `rules/video_rules.yaml` (`docs/handoff/15` P3).

---

이 문서의 변경은 [DOCS_GOVERNANCE.md](DOCS_GOVERNANCE.md)의 변경 전파 체크리스트를 따릅니다.
삭제는 금지되며, 폐기 항목은 `[deprecated]` 마크만 남깁니다.
