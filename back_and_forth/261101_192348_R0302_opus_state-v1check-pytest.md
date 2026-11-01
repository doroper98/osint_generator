---
id: R-0302
from: opus
to: fable
kind: phase_report
responds_to: [D-0604]
phase: "E9"
version: v7.4.0
commit: pending
status: done
---

# v1 spec 검사 렌더 · 전체 pytest(-n 2 -v) · 기록 필름 메모 · 상태 기록

감독 메시지(08:13Z) 세 항목 결과입니다. 새 작업은 하지 않았습니다.
단, 제 변경으로 깨진 시험 기대값 두 건은 고쳤습니다(아래 2-1).

## 1. v1 spec 전편 렌더 — 검사만(artifacts 미업로드)

산출물은 /tmp/v1check/<pid>/out/ 에만 있습니다. 두 건 모두 rc=1(hard 위반)입니다.

| 프로젝트 | SK-W6(hard) | SK-W5(hard) | SK-C2(warning) |
|---|---|---|---|
| cannae_sketch | 카드가 부대·지명 상자를 9.3s 덮음 | 글자 화면 밖 159프레임, 첫 t=9.08s(칸나이) | 겹침 395프레임, t=9.08~32.42s |
| inchon_sketch | 카드가 부대·지명 상자를 4.6s 덮음 | 글자 화면 밖 4프레임, 첫 t=36.92s(서울) | 겹침 546프레임, t=18.08~42.12s |

SK-W6 한도는 rules qa_checks.label_under_media.max_sec 0.2 입니다.
v1 spec 은 새 검사 셋을 통과하지 못합니다. 수정은 지시가 있을 때 하겠습니다.

## 2. 전체 pytest(-n 2 -v)

rc=124입니다. 타임아웃으로 77% 지점에서 끊겼습니다(PASSED 1858).
뒷부분 23%는 돌지 않았습니다. 끊긴 지점까지의 실패·오류 이름은 아래 전부입니다.

### 2-1. 제 변경 원인 — 고침(시험 기대값만, 규칙 파일 무변경)

- FAILED tests/test_sketch_common.py::SketchRulesTest::test_rules_load_and_fonts_known: camera.push_in 에 war 추가를 반영했습니다.
- FAILED tests/test_sketch_integration.py::SkillFilesTest::test_frontmatter_and_sections: campaign-front-map ⑧ 절을 스킬별 추가 절로 허용했습니다.
- 두 파일 재실행 결과 17 passed, 6 skipped 입니다.

### 2-2. 자산 미복원(환경)

- ERROR tests/test_phase10_scale.py::HormuzScaleTest::test_downscaled_close
- ERROR tests/test_phase10_scale.py::HormuzScaleTest::test_frame_size_and_identity
- ERROR tests/test_phase10_scale.py::HormuzScaleTest::test_positions_identical
- 위 세 건: hormuz_korea res_1080p tiers.pkl 없음(1080p geo.prep 미실행).
- FAILED tests/test_fed_timeline_demo.py::DemoPreviewTest::test_preview_checks_and_provenance
- FAILED tests/test_g5_endcard_overflow.py::OverflowTest::test_real_projects_no_overflow
- FAILED tests/test_g5_endcard_overflow.py::UniqueLineTest::test_real_projects
- FAILED tests/test_g5_labels_endcard.py::ProjectPreviewNoLabelTest::test_body_frames_and_end_card
- 위 네 건: fed_policy_2026 의 plan.json·tts 가 없습니다(artifacts 미복원).

### 2-3. 의견 원장 상태(감독 소관)

- FAILED tests/anti_inertia/test_user_feedback_guards.py::UserFeedbackGuardsTest::test_doc_guards_only_for_process_items: 대상 UF-203·204·206.
- FAILED tests/anti_inertia/test_user_feedback_guards.py::UserFeedbackGuardsTest::test_doc_table_is_generated: feedback_ledger.py --write 표가 원장과 다릅니다.
- FAILED tests/anti_inertia/test_user_feedback_guards.py::UserFeedbackGuardsTest::test_open_entries_only_latest_video: 기한 지난 open 은 UF-147·149·151~157·202 입니다.
- 원장 줄은 감독만 씁니다. 저는 손대지 않았습니다.

### 2-4. main 병합분(D-0311 project_id)

- FAILED tests/test_direction_convert.py::ConvertFidelityTest::test_example_prompt_copy_matches_project
- SUBFAILED(project='hormuz_korea') tests/test_direction_convert.py::ConvertFidelityTest::test_yaml_equals_old_direction
- 원인: hormuz_korea 연출에 project_id 가 들어가 예시와 차이가 납니다.
- 이 필드는 main 에서 들어왔습니다(engine/direction.py, D-0311). 제 stage.py 변경(proposed_theme)과는 무관합니다.

## 3. archive.org 필름 셋 — RIGHTS 메모만

- 111-adc-8251(NARA id 22017): 미 육군 통신대 기록입니다. 연방 저작물(PD)로 보이지만 확인 전입니다.
- gov.dod.dimoc.20265: 페이지 표기는 CC0 입니다.
- gov.dod.dimoc.22337: 페이지 표기는 CC0 입니다.
- 내려 받기·자산 등록·화면 사용은 하지 않았습니다. 쓰려면 원본 기록과 rights_status 기록을 먼저 해야 합니다.

## 4. 상태 기록(자동 압축 대비)

- 브랜치 claude/war-history-2026: 이 R 커밋 뒤 작업 트리는 깨끗합니다(무시 파일만). 미등록 패치 없음.
- artifacts/war-history-v7.4.0 head 는 f0ba9edb 이며 이번에 바꾸지 않았습니다.
- 남은 일:
  1. 사용자 판정 ①(W4 스케치·구상 컷 A·B) 대기. W5·W6 은 승인 전 금지.
  2. v1 spec 의 SK-W6·SK-W5 위반 수정. 지시가 오면 합니다.
  3. 전체 pytest 나머지 23%. 지시가 오면 시간 한도를 늘려 다시 돌립니다.
  4. 유적 층 CC BY-SA 허용 여부. 판정 ① 에서 사용자에게 묻습니다.
  5. 인천 기록 필름 권리 확인. 지시가 오면 합니다.
