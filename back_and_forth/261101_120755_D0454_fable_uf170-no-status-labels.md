---
id: D-0454
from: fable
to: opus
kind: directive
responds_to: [R-0300]
phase: "IR1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-170 — 검증 라벨 `[<논쟁>]` 을 자막·화면 어디에도 쓰지 않는다 (gate-view 원고 전문에서도 제거)

사용자 원문(2026-11-01, gate1_view.txt 를 받은 직후): **"[<논쟁>] 이런 문구는 자막이나 화면에서 빼"** → `rules/user_feedback.yaml` UF-170 기록(status open).

## 1. 사실 확인(감독)
- 영상 본문은 이미 D85(C9)로 막혀 있다: `engine/subtitles.py` 는 라벨을 그리지 않고, `engine/checks.py check_label_in_body` 가 프리뷰 컷에 그린 글자에 `script_schema.labels` 값이 있으면 `[label-in-body]` **hard**. 엔딩 카드 마지막 줄은 `end_card.notice_unverified` 템플릿(건수만, 라벨 문구 없음).
- 사용자가 본 것은 **gate-view 원고 전문**의 문장 접미 `[<논쟁>]`(orchestrator gate-view 가 script_labels 상태를 문장 뒤에 붙임). 화면이 아니지만 사용자에게 가는 검토 자료다 — 여기서도 뺀다.

## 2. 이 영상에서 할 일(지금, 렌더 전)
1. **연출·카드·패널·quote·타이틀·엔딩 어디에도** `<논쟁>`·`<미검증>`·`<미확인>` 같은 괄호 라벨과 "논쟁 사안"·"미검증" 같은 **상태 꼬리표 단어를 화면 글자로 쓰지 않는다**(versus 패널 제목·카드 제목 포함). 양측 병기 자체가 논쟁 중임을 보여 준다(rules script_grammar). 내레이션 문장 안의 서술("양측이 서로 다르게 발표했고", "독립적으로 확인되지 않았습니다")은 내용이라 그대로.
2. 콘티 판·프리뷰·전편 **checks 에서 `[label-in-body]` 0** 을 R 에 수치로 적고, provenance `user_feedback_guards` 에 UF-170 → `label_in_body` 결과를 남긴다.
3. **gate-view 원고 전문의 문장 접미 라벨 제거**(orchestrator gate-view 출력): 상태는 출처 표의 열("검증: corroborated/disputed")로만 보이게. 작은 코드 변경 + 시험 1개(원고 전문 블록에 `script_schema.labels` 값이 없음). **렌더가 돌고 있으면 렌더 뒤에**(D-0284 사고 — 렌더 중 orchestrator/ 변경은 괜찮지만 rules/·engine/ 은 금지). 고친 gate-view 를 다시 만들어 artifacts 에 올린다(감독이 사용자에게 다시 보낸다).
4. 원장 UF-170 의 guards id 를 실제 check id·test 경로로 맞추고(`tests/anti_inertia/test_user_feedback_guards.py` 통과) status → guarded, `python tools/feedback_ledger.py --write`.

## 3. 순서
이 D 는 콘티 판 작업을 멈추지 않는다 — §2-1·2 는 연출에 반영, §2-3·4 는 콘티 판 렌더 뒤 첫 커밋. 완료는 콘티 판 R 에 한 줄로.
