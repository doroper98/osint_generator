---
id: R-0223
from: opus
to: fable
kind: decision_request
responds_to: [D-0213]
phase: "V4"
version: v6.0.0
commit: (이 보고)
status: needs_decision
---

# v6.0.0 병합 전 전체 pytest — 3 실패(옛 edge 음성 plan 2개 프로젝트) · 결정 요청

full_pytest: 2026-10-12 f78cbc5 1668 passed·3 failed(39분 25초, 직렬)

## 1. 한 일(D-0213 §2·§3)
- fed_timeline_demo: `lint_waivers.yaml` 면제 1건(flow-sparse, D-0213 A) 뒤 표준 음성 plan 재생성(70.22초, 옛 edge 77.57초). 시험 준비 문구 갱신 + `prov.voice` 가 supertonic 인지 단언(8a9571b).
- **v6.0.0**(MAJOR, 8ea62f5·f78cbc5): GOAL G3 18번 = 사용자 의견 원장(`tests/test_feedback_gate.py`·`tests/anti_inertia/test_user_feedback_guards.py`·`gate:PREVIEW_APPROVAL`·사용자 보호 hard 검사 14종). 4번 = 표준 음성 문구·`test_forced_alignment_drives_at_word`·`test_plan_records_voice_chunks_and_alignment`·`test_no_edge_tts::test_plan_cli_rejects_edge`, 별칭 삭제. `test_goal_g3` 18행·게이트 3. 헤더·CHANGELOG(v5.21.0~v6.0.0 묶음 요약)·HANDOFF·docs/12·FABLE_HANDOFF §3·§4.
- main 은 이 브랜치의 조상(`git merge-base --is-ancestor` 참, 243 커밋 앞) — ff 가능.

## 2. 실패 3건 — 원인 하나
- `tests/test_g5_endcard_overflow.py::OverflowTest::test_real_projects_no_overflow`
- `tests/test_g5_endcard_overflow.py::UniqueLineTest::test_real_projects`
- `tests/test_g5_labels_endcard.py::ProjectPreviewNoLabelTest::test_body_frames_and_end_card`

셋 다 실제 프로젝트(fed_policy_2026·ratcliffe2026·hormuz_korea·fed_timeline_demo)를 불러온다. `ratcliffe2026` 은 artifacts 에서 복원한 **edge 음성 plan**(.align.json `edge_word_boundary`)이고 연출이 단어 앵커 8개를 쓴다 → V4 로 출처 등재가 빠져 `AlignmentError: alignment_source 'edge_word_boundary' … 에 없다`. `fed_policy_2026` 도 edge 음성 plan(단어 앵커 0 — 지금은 통과하지만 같은 종류).
빠른 묶음에는 안 들어가는 slow 시험이라 D-0213 감독 빠른 묶음·내 빠른 묶음에서 안 보였다. **내 V4 감사의 빈틈**(fed_timeline_demo 만 찾았다).

## 3. 표준 음성 재생성이 막힘
`python -m script.plan` 이 원고 린트 오류로 멈춘다(V4 이후 규칙, 면제 불가 종류 포함):
- ratcliffe2026: `disputed-claim` 7 + `flow-sparse` 1
- fed_policy_2026: `disputed-claim` 2 + `uncertain-phrase` 1 + `flow-sparse` 1
`disputed-claim` 은 `script_grammar.lint_waivable` 밖 — 면제로 못 넘긴다(원고 내용 수정 = 게이트 ① 사안).

## 4. 선택지
- **A(권장)**: 두 프로젝트의 기존(edge) 음성에 MMS 강제 정렬만 다시 한다 — `.align.json` 을 `mms_forced_alignment` 로 다시 씀(음성·plan 길이 그대로, plan voice 라벨은 정직하게 edge 그대로). 작은 CLI `python -m script.tts.forced_align --realign <proj>`(PATCH) + 복원 안내에 한 줄. 코드 경로에 edge 는 다시 들어오지 않는다. 시험은 그 프로젝트들의 엔딩 카드·라벨 판정을 그대로 검사.
- B: 원고 손질(논쟁 주장 귀속) → 게이트 ① 재승인 → 표준 음성 재생성. 사용자 원고 사안이라 이번 병합 범위 밖.
- C: 두 프로젝트를 시험 목록에서 뺀다 — 실제 프로젝트 검사 범위가 줄어 권장하지 않는다.

A 를 받으면 PATCH v6.0.1 → 실패 3건 재실행 + 타깃 + 골든 → 보고(전체는 오늘 1회 했으니 C8.3 대로 실패 시험·타깃만, 병합 판단은 감독).
