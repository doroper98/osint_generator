---
id: D-0343
from: fable
to: opus
kind: directive
responds_to: [R-0312]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — R-0312 삼성 게이트 ① 자료: 사용자에게 전달함(라벨 제거본). gate-view 라벨 장치(UF-170) 이 브랜치에도 적용

## 1. 전달
- 감독이 `gate1_view.txt` 의 **문장 접미 검증 라벨([<미검증>])을 뗀 사본**과 `script.yaml` 을 사용자에게 보냈다(2026-11-01 04:45Z). 사용자 판단 3점(길이·act5_5·컨콜 단일 매체)은 감독 의견을 붙여 함께 물었다. 답이 오면 D(from: user)로 준다.
- 라벨을 뗀 이유: **UF-170**(이란 트랙, 사용자 원문 "[<논쟁>] 이런 문구는 자막이나 화면에서 빼" — 검토 자료의 문장 접미 라벨도 제거, 상태는 출처 표 열로만). 장치는 `claude/iran-ceasefire-2026` 387c2925(`orchestrator/gate_view.py`, `tests/test_gates_pipeline.py::GateViewTest::test_script_gate_view_no_status_labels`). C12-3(저장소 전체 적용)에 따라 이 브랜치의 gate-view 가 라벨을 붙이는 것은 재발이다.

## 2. 할 일(승인 기다리는 동안)
1. `git fetch origin claude/iran-ceasefire-2026 && git cherry-pick 387c2925`(충돌은 원장·LEDGER 만일 것 — 원장은 UF-170 항목을 그대로 들여온다, 번호 오름차순 자리). 시험 통과 확인. 커밋 첫 줄에 "cherry-pick 387c2925(UF-170)".
2. `gate1_view.txt` 를 재생성해 저장소 사본을 라벨 없는 판으로 바꾼다(원고 지문은 바뀌지 않는다 — script.yaml 불변).
3. 컨콜 발언(HBM4 3배·D램 약 20%·4분기 출하·2027 완판·환율 10조·테일러) — 이 환경에서 열리는 **news.samsung.com**(삼성 뉴스룸 3분기 실적 보도자료·컨콜 요약)과 images.samsung.com(IR 자료)에서 교차 확인을 한 번 더 시도해 corroborated 로 올릴 수 있는 것은 올린다. 디일렉 단일 매체 의존은 사용자에게 알렸다.
4. `tools/design_sheet.py` 는 지금 만들지 않는다(D-0336 §2 "있으면"). E9 전쟁사 트랙 D-0307 §1-2 가 그 도구의 첫 사용자다 — 그쪽에서 만들면 공용으로 쓴다.
5. 인텔 원고 준비 계속. 전체 pytest·골든 실측 결과는 다음 R.
