---
id: R-0197
from: opus
to: fable
kind: decision_request
responds_to: [D-0167]
phase: "V3"
version: v5.17.0
status: open
priority: urgent
---

# V3 §3-1 — 골든 원고가 뒤에 생긴 린트 오류 2건에 걸린다. 예외 처리 방식 결정 요청

## 1. 쟁점
`python -m script.plan projects/hormuz_korea --tts supertonic` 이 린트에서 멈춥니다(합성 전, plan.json 무변경 확인).
- `[uncertain-phrase] now_3`: "…국회가 이 문제를 어떻게 다룰지는 아직 **정해지지 않았**습니다."
- `[flow-sparse]`: 연결어로 시작하는 문장 3/45 = 7% < 30%.

두 규칙은 v5.5.0(2026-10-02, b4b0e77 `script_grammar`)에 생겼습니다. 골든 `script.yaml` 마지막 수정은 2026-09-28(edc8a81)입니다.
저장소에는 린트 예외 장치가 없습니다. D-0167 §3-1 대로 원고는 고치지 않고(C8.6 게이트 ① 재승인 대상), 건너뛰기도 하지 않았습니다.

## 2. 선택지
| 안 | 내용 | 장단 |
|---|---|---|
| **A(권고)** | **프로젝트 단위 면제 목록** `projects/<pid>/lint_waivers.yaml`: 항목마다 `kind`·`sid`(전체 규칙은 `-`)·`reason`·`decided_by`(D 번호). `lint()` 는 그대로 돌고, plan 은 목록과 **정확히 일치하는** 오류만 통과시킨다. 면제는 경고로 낮춰 출력하고 provenance `lint.waived` 에 남긴다. 목록에 없는 오류·목록에 있는데 더는 안 나는 항목(낡은 면제) = 오류 | 좁고 감사 가능하다. 다른 원고·다른 오류는 그대로 막힌다(P6). 파일 1개 + plan 몇 줄. 면제는 사람(Fable·사용자) 결정 기록이 있어야 생긴다 |
| B | 규칙 시점 고정: 원고가 승인된 때의 `rules_version` 규칙으로 린트(승인 기록에 rules_version 저장) | 원칙상 깔끔. 규칙 이력 보관·옛 규칙 재현 장치가 필요해 크다. 지금 승인 기록에 rules_version 이 없는 프로젝트가 많다 |
| C | plan CLI 플래그 `--waive-lint <kind>` | 가장 작다. 기록이 명령행에만 남아 provenance 로 증명하기 어렵고, 우회 플래그 금지 취지(C8.6·PIPELINE-AP-014)와 어긋난다 — 비권고 |
| D | 원고 수정 + 게이트 ① 재승인 | D-0167 이 배제. 골든 재현(V3)의 비교 대상이 바뀐다 — 비권고 |

## 3. 권고
**A**. 호르무즈 `lint_waivers.yaml` 첫 항목 2개(`uncertain-phrase now_3`, `flow-sparse -`), `decided_by` = 이 결정의 D 번호.
테스트: 면제 정확 일치만 통과 / 목록 밖 오류 = 실패 / 낡은 면제 = 오류 / provenance 기록. C7 동기화: `docs/handoff/03` 린트 절 한 단락, 05 표 한 줄.

## 4. 막히는 범위
§3-1 합성부터 그 뒤 전부(콘티 판·프리뷰·기준선·전편·청취 자료)가 막힙니다.
그동안 막히지 않는 것을 진행합니다: VERSION 5.17.0 올림, 컷 대응표·25컷 나란히 시트 도구, 클릭음 표본 도구, 믹스 측정 표 도구, 테스트 뼈대.
