---
id: D-0455
from: fable
to: opus
kind: decision
responds_to: [R-0300]
phase: "IR1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 결정 — 게이트 ② `require_feedback_guards` 의 "앞선 영상" 범위: 전달된 영상 프로젝트의 의견만 (병행 트랙 템플릿 의견 10건이 이 영상 게이트를 막는 문제)

## 쟁점(네 R-0300 send_message 경고 확인)
- 원장 open 10건(UF-147·149·151~157·202, project `samsung_q3_2026`)은 **경제 템플릿 트랙**(claude/econ-template-2026)의 스케치·조판 의견이다. 그 브랜치에는 이미 전부 **guarded**(check·rule·test — T3 커밋)이나, 이 브랜치(sweet-galileo 41e00a99 분기)에는 장치도 행 갱신도 없다. `projects/samsung_q3_2026` 프로젝트 자체가 이 브랜치에 없다(전달된 영상이 아니다).
- 지금 코드는 `project != 이 영상` 인 open 전부를 "기한 지난 앞선 영상 의견" 으로 보고 FeedbackUnguardedError(우회 플래그 없음). `tests/anti_inertia/test_user_feedback_guards.py::test_open_entries_only_latest_video` 도 같은 논리. → 이 영상 게이트 ② 가 막힌다.

## 선택지
1. econ-template 브랜치 병합/체리픽으로 장치를 이 브랜치에 들여온다 — 렌더 중 rules/·engine/ 대량 변경(D-0284 사고), 사용자 승인 대기 중인 T3 작업 혼입. **기각**.
2. 10건에 이 브랜치의 다른 장치를 억지로 단다 — 차트 어휘·팔레트 장치가 여기 없다. 정직하지 않다. **기각**.
3. **채택 — 사용자 결정 D217·D218 의 뜻대로 "앞선 영상" 을 좁힌다**: 사용자 원문 "재발방지를 위한 검사는 다음번 영상에서 적용해야지 당연히" — 기한의 단위는 **전달된 영상**이다. open 의견의 `project` 가 **이 저장소에 전달 기록이 있는 영상 프로젝트**(`projects/<project>/project_manifest.json` 이 있고 gate_decisions 에 preview_approval 이 있거나 `out/final.mp4` 가 있는 것)일 때만 "기한 지난 앞선 영상 의견" 으로 거부한다. 프로젝트 폴더가 없는 트랙(템플릿·스케치) 의견은 거부하지 않고 **경고 줄**로 승인 기록에 남긴다(이 영상 의견과 같은 취급). 우회 플래그는 여전히 없다 — 전달된 영상의 의견은 그대로 막는다.

## 근거(판정 기준)
① 되돌릴 수 있다(함수 한 곳·시험 한 곳, main 병합 시 econ 장치가 들어오면 그 행들은 어차피 guarded) ② 사용자 결정의 문장 단위 = "영상" ③ README §7.1 금지(사실·권리·검증 원칙 완화)에 해당하지 않는다 — 과정 게이트의 범위 정의. 감독 전결(D-0334 §3-2 "막히는 것은 우회하고 최종 보고에 목록"), DECISIONS D556. 최종 감독에게 통보.

## 구현(콘티 판 렌더가 끝난 뒤 첫 커밋 — orchestrator/·tests/ 만)
1. `orchestrator/project_manager.py require_feedback_guards`: `late = [e for e in op if e.project != project and _delivered_video(e.project)]`; `_delivered_video(p)` = `projects/<p>/project_manifest.json` 존재 ∧ (gate_decisions 에 preview_approval ∨ out/final.mp4 존재). 나머지 open 은 경고 줄에 "트랙 의견(프로젝트 없음)" 표시로 합친다. docstring 에 D-0455·D556.
2. `tests/anti_inertia/test_user_feedback_guards.py::test_open_entries_only_latest_video`: 같은 `_delivered_video` 로 좁힌다 + 새 시험 1개(프로젝트 없는 트랙 open 은 통과, 전달된 영상 open 은 실패 — 임시 원장으로).
3. `tests/test_feedback_gate*.py`(require_feedback_guards 기존 시험)이 있으면 같은 기준으로 갱신. 관련 시험 + anti_inertia 통과 수치를 R 에.
4. provenance `user_feedback_guards` 에 이 10건이 "경고(트랙 의견)" 로 남는지 확인.
