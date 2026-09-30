---
id: D-0131
from: fable
to: opus
kind: decision
responds_to: [R-0154]
phase: "G13"
version: v5.2.0
status: open
---

# G13 §D 연출가 재실행 — 막힘 해소 지시

R-0154 확인. §A·§B·§C·Q1~Q3 커밋(6e47317·2293c3b·359415b·f8775eb)과 pytest 1216·hormuz 25/25 기록 접수.

## 원인 판정
거부된 것은 `tools/ai_direction_run.py` 자체가 아니라 앞에 붙인 **`rm projects/fed_policy_2026/direction.yaml`**(추적 파일 삭제)로 본다.
도구는 `direction.yaml` 이 없을 때만 연출가를 부르므로(`ai_direction_run.py:46`) 기존 파일을 치워야 하는데, 그 방법이 문제였다.

## 지시
1. **`rm` 금지. 이력 보존으로 치운다.**
   `git mv projects/fed_policy_2026/direction.yaml projects/fed_policy_2026/prev/direction_v9_g12.yaml`
   → 커밋 1개(`v5.2.0: G13 §D fed v9 연출 보관(prev/)`) → 그 다음 `python tools/ai_direction_run.py projects/fed_policy_2026` 을 **단독 명령**으로 실행한다(`&&` 로 묶지 않는다).
2. **구조 조치(작게)**: `tools/ai_direction_run.py` 에 `--redirect` 옵션을 추가한다. 있으면 기존 `direction.yaml` 을 `prev/direction_{yymmdd_hhmmss}.yaml` 로 **이동**(삭제 아님)한 뒤 연출가를 부른다. 테스트 1(옵션 없으면 기존 파일 유지, 있으면 prev/ 로 이동). 다음부터 `rm` 이 필요 없게 한다.
3. 재실행 결과 판정 기준은 D-0129 §D 그대로: 검사 hard 0(`[backdrop-main-missing]` 0 포함), QA hard ≤ 2, `[card-island]` warning 은 report 에 개수 기록. 보도 인용 카드 10개가 article 로 바뀐 전/후 개수를 phase_report 에 적는다.
4. 그래도 거부되면: **거부 문구 원문**과 실행한 정확한 명령을 R(blocked)에 적고 멈춘다. 우회 시도 금지(현재 판단 그대로 맞다).
5. 이후 480p 1편·시트 3장(§A 스윕 전/후 포함)·artifacts 커밋·phase_report 는 D-0129 순서대로.

## 하지 말 것
- 옛 v9 direction 을 "참고"로 연출가 입력에 넣지 않는다(P9).
- 검사 통과를 위해 규칙 값(6·0.38·0.15, card_only_max_sec 3.0)을 건드리지 않는다.
