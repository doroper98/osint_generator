<!--
tier: 1
last_synced_with: v4.5.0
ssot_for: [project-goals, acceptance-criteria, prohibitions]
depends_on: [README.md, docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-29
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
| `out/thumbnail_candidates/` | 썸네일 후보 — (v4.0.0) v2 파이프라인에 없다. 필요하면 별도 계획(back_and_forth D-0073) |
| `out/provenance.json` | 이번 영상에 실제로 쓰인 기능·규칙 해시·프롬프트 해시·drops (`docs/handoff/15` P5) |
| `script.yaml` | 원고 (승인본에 `approved_at`) |
| `plan.json` | 문장 타임라인·음성·정렬 |
| `direction.yaml` | 연출 (버전별 보관) |
| `assets.lock.json` | 이 영상이 쓴 자산 목록·해시·권리 |
| `prev/sheet.jpg`, `prev/checks.json`, `prev/qa_verdict.v*.json` | 프리뷰 컨택트 시트·결정적 검사·시각 검수 판정 |
| `intake/sources.json`, `intake/claims.json` | 소스 레코드·주장-출처 매핑 |
| `project_manifest.json` | 프로젝트 메타·상태·경로 인덱스 |
| `approval_log.json` | 승인 게이트 2개(SCRIPT_APPROVAL·PREVIEW_APPROVAL) 기록 — v3.0.0부터 `project_manifest.json` `gate_decisions`(`schemas.models.GateDecision`)에 남는다(v4.0.0 실측 정정) |

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

## G3. 합격 기준 v2 (v4.0.0 — 19 부록 C + D4 17번, 결정 D-0005·D64)

본 목록은 변경 시 v{X+1}로 **메이저 버전**이 올라갑니다(CLAUDE.md C5.4).

아래 17개가 모두 충족되어야 v2 파이프라인 합격입니다. 수치는 규칙 키로만 가리킵니다(값의 정본은 `rules/video_rules.yaml`·`config.yaml`, 15 P3).
"검증 방법" 열은 `tests/…::test_…`(자동 테스트), `checks:항목`(프리뷰 결정적 검사 `prev/checks.json`, `engine/checks.py`),
`gate:…`(사람 판정 — 승인 게이트), `pending:…`(검사가 아직 없음 — 예정 Phase) 중 하나 이상입니다. `tests/test_goal_g3.py`가 이 열이 가리키는 것이 실제로 있는지 대조합니다.

| # | 기준 | 검증 방법 |
|---|---|---|
| 1 | `python -m orchestrator.main command-center`가 새 상태 머신(`docs/handoff/16` §2)으로 프로젝트를 CREATED→DONE까지 진행한다. | `tests/test_state_machine.py::test_sequence_matches_16_s2` · `tests/test_gates_pipeline.py::test_engine_states_to_gate2_then_done` |
| 2 | SCRIPT_APPROVAL·PREVIEW_APPROVAL 두 게이트에서 승인·반려(되돌림)가 동작하고 게이트 기록(`project_manifest.json` `gate_decisions` — 누가·언제·코멘트·본 것·되돌린 상태, append-only)에 남는다. (부록 C 초안의 `approval_log.json` 은 v3.0.0 에서 manifest 로 옮겨졌다 — 실측 정정) | `tests/test_gates_pipeline.py::test_approve_records_and_advances` · `tests/test_gates_pipeline.py::test_reject_script_rolls_back_with_comment` · `tests/test_gates_pipeline.py::test_reject_preview_three_targets` · `tests/test_gates_pipeline.py::test_config_two_gates_only` |
| 3 | `script.yaml`이 `Script` 스키마를 통과하고 린트(금지 문구·발음 기호·강조어·출처)를 통과한다. 장면 수·길이는 고정되지 않는다. | `tests/test_engine_phase2.py::test_schema_rejects_missing_emphasis` · `tests/test_script_lint.py::test_banned_samples_all_detected` · `tests/test_script_lint.py::test_tts_symbols_detected` · `tests/test_script_lint.py::test_numeric_sentence_without_sources_is_error` · `tests/test_script_lint.py::test_v3_script_passes` |
| 4 | `plan.json`이 실제 음성 길이로 계산되고, 목소리(edge/ElevenLabs)를 바꿔도 `direction`을 수정하지 않는다(문장·단어 앵커). | `tests/test_timebase_align.py::test_aligned_uses_pronunciation_start_minus_trim` · `tests/test_timebase_align.py::test_edge_alignment_drives_at_word` · `tests/test_script_tts.py::test_cache_key_salted_by_voice` · `tests/test_direction_schema.py::test_word_anchor_uses_at_word` |
| 5 | `direction.yaml`이 레지스트리·스키마·예약 영역 검사를 통과한다. | `tests/test_direction_schema.py::test_schema_errors` · `tests/anti_inertia/test_registry_complete.py::test_bidirectional` · `tests/test_reserved_phase6.py::test_multiple_zones_cleared` · `checks:overlap` |
| 6 | 프리뷰가 `prev/sheet.jpg`와 `prev/checks.json`(hard 0)을 만들고, AI 연출의 시각 검수 루프는 2회 이내에 끝난다. 상한에 닿고도 남은 판정은 게이트 ② 사람 판정으로 넘긴다(D49). | `tests/test_checks.py::test_hard_fails_stage` · `tests/test_ai_direction.py::test_loop_cap` · `tests/test_ai_direction.py::test_loop_cap_with_hard_left_stays` · `gate:PREVIEW_APPROVAL` |
| 7 | 출력 프로파일(`config:engine.output` — 트라이얼 480p·최종 1080p, D-0067 장치 변환)로 `out/final.mp4`, `final.srt`, `description.txt`(챕터·출처·크레딧)가 생성된다. 1080p 는 480p 와 같은 비율이다(`rules:golden.res_compare_mad_max`). | `tests/test_phase10_profile.py::test_aliases` · `tests/test_phase10_profile.py::test_k_1080` · `tests/test_engine_phase2.py::test_srt_and_description` · `checks:media_upscaled` |
| 8 | `out/provenance.json`의 `features_used`가 실제 사용 기능과 일치하고 `drops`가 비어 있다. | `tests/anti_inertia/test_provenance_e2e.py::test_hormuz_preview_provenance` · `tests/test_engine_service.py::test_drops_propagate_as_failure` |
| 9 | 화면 모서리에는 날짜 배지만 있고 도장·비네팅·브랜드·섹션 표기가 없다(결정적 검사). | `checks:forbidden` · `checks:date` · `tests/test_checks.py::test_forbidden` |
| 10 | 확대 장면에 행정구역·도시 라벨이 표시되고 라벨 겹침·카드에 가린 라벨이 없다. | `checks:labels` · `checks:overlap` · `tests/test_phase10_label_hidden.py::test_boundary` · `tests/test_checks.py::test_offscreen_marker_label` |
| 11 | 모든 사용 자산(인물·휘장·국기·지도·지형·미디어·음악)이 권리 레지스트리에 있고 엔딩 카드·설명문에 크레딧이 나온다(`rules:credits`). | `checks:rights` · `tests/test_credits_phase5.py::test_complete_credits_pass` · `tests/test_credits_phase5.py::test_missing_registry_entry_is_error` · `tests/test_media_gate_phase65.py::test_every_media_in_card_and_articles_required` |
| 12 | 미디어 비트 밀도가 규칙 `rules:media.density` 안이고(D-0037·D38), 자료사진 표기·출처 줄이 검사에서 통과한다. | `checks:media_beats` · `tests/test_media_plan_phase65.py::test_b_three_in_40s_warns` · `tests/test_media_registry_phase65.py::test_file_photo_label_required` · `tests/test_media_registry_phase65.py::test_credit_line_from_fields` |
| 13 | 오디오 최종 음량이 `rules:audio.loudnorm` ± `rules:audio.qa.i_tol_lu`, 내레이션 중 음악이 `rules:audio.qa.music_under_narration_db`(v3 사용자 합격본 기준, D57) 안이다. | `tests/test_audio_qa.py::test_rules_follow_user_approved_v3` · `tests/test_audio_qa.py::test_music_level_inside_and_outside` · `tests/test_audio_qa.py::test_loudness_and_true_peak_issues` |
| 14 | 모든 JSON/YAML 산출물이 `schema_version`을 갖고 Pydantic으로 검증된다. | `tests/test_state_machine.py::test_new_manifest_is_v2_and_round_trips` · `tests/test_rules_ssot.py::test_loads_and_validates` · `tests/anti_inertia/test_prompt_schema_parity.py::test_examples_validate` |
| 15 | 관성 방지 테스트(`tests/anti_inertia/`)가 전부 통과한다(xfail 0). | `tests/anti_inertia/` |
| 16 | 실패 시 옛 스타일로 폴백하지 않고 해당 상태에 멈춰 사용자에게 보고한다. | `tests/anti_inertia/test_no_silent_fallback.py::test_a_unregistered_event_type` · `tests/test_gates_pipeline.py::test_failure_and_drops_stay` · `tests/test_engine_service.py::test_drops_propagate_as_failure` |
| 17 | 장르 확장(`docs/handoff/20`) 영상도 1~16을 만족하고 무대 연속성 검사(20 §12)를 통과한다. | `checks:stage_continuity`(v4.1.0 G1, `rules:stage`) · `checks:genre_elements`(v4.2.0 G2) · `checks:chart_honesty`(v4.3.0 G3, `rules:qa_checks.chart_targets`) · `tests/test_stage_continuity.py::test_fail_switch_without_dip` · `tests/test_stage_continuity.py::test_pass_main_secondary_round_trip_all_dip` · `gate:PREVIEW_APPROVAL` · `pending:G4` (비지정학 영상 판정) |

### G3-legacy. v1 MVP 기준 34개 [legacy v1 — deprecated v4.0.0]

> [legacy v1 — deprecated v4.0.0] v1(Command Center·Remotion·scene_manifest) 기준이다. 합격 판정에 쓰지 않는다. 삭제하지 않고 보존한다(DOCS_GOVERNANCE §6.4).

<details>
<summary>v1 34개 (펼치기)</summary>

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

</details>

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
  `18` 소스 인테이크 / `20` 장르 확장(지정학이 아닌 주제의 자유 제작 — 불변·장르·자유 3층).
- 골든 기준: `docs/handoff/golden/`(문장 앵커 기준 프레임 25장). 동작 원본: `docs/handoff/reference_code/v3_hormuz_korea/`.
- 규칙 SSOT: `rules/video_rules.yaml` (`docs/handoff/15` P3).

---

이 문서의 변경은 [DOCS_GOVERNANCE.md](DOCS_GOVERNANCE.md)의 변경 전파 체크리스트를 따릅니다.
삭제는 금지되며, 폐기 항목은 `[deprecated]` 마크만 남깁니다.
