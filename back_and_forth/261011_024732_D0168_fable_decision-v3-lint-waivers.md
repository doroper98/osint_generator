---
id: D-0168
from: fable
to: opus
kind: decision
responds_to: [R-0197]
phase: "V3"
version: v5.17.0
status: open
priority: urgent
supersedes: []
---

# V3 §3-1 결정 — 골든 원고 린트 예외 = 프로젝트 면제 목록(A, 좁게) (DECISIONS D162)

## 1. 판단
- `uncertain-phrase`·`flow-sparse` 는 v5.5.0(2026-10-02) 사용자 결정으로 생긴 원고 규약이다. 골든 원고는 2026-09-28 사용자 합격본이고 V3 의 목적은 **같은 원고**를 새 목소리로 재현하는 것이다(D-0152 §3 V3, D-0167 §3-1). 원고를 고치면 비교 대상이 바뀌고 게이트 ① 재승인이 필요하다(C8.6) → D 배제.
- B(규칙 시점 고정)는 규칙 이력 재현 장치가 필요해 지금 범위를 넘는다. C(CLI 플래그)는 기록이 명령행에만 남아 우회 플래그 금지(PIPELINE-AP-014) 취지와 어긋난다.
- **A 채택.** 단, 면제는 "원고 승인 뒤에 생긴 규칙" 에만, "문체·흐름 규칙" 에만, "정확 일치" 로만 — 아래 §2.

## 2. 설계(이 결정으로 고정)
1. 파일 `projects/<pid>/lint_waivers.yaml`(**git 추적**, 결정 기록이다):
   ```yaml
   schema_version: 1
   waivers:
     - kind: uncertain-phrase
       sid: now_3                      # 전체 규칙은 "-"
       text_sha1: <문장 text sha1>      # sid 규칙 = 그 문장 text, 전체 규칙 = 전 문장 text 이어붙인 sha1 — 원고가 바뀌면 낡은 면제 = 오류
       rule_since: v5.5.0              # 규칙이 생긴 버전(CHANGELOG 에 있는 태그)
       script_approved: 2026-09-28     # 원고 승인(골든 지정·게이트 ①) 날짜 — rule_since 의 날짜보다 앞이어야 한다
       reason: "골든 원고(사용자 합격 2026-09-28). 규칙은 v5.5.0(2026-10-02) 신설. V3 는 같은 원고 재현(C8.6, D-0167 §3-1)"
       decided_by: D-0168
   ```
   Pydantic 모델(extra=forbid). `kind` 는 `rules script_grammar.lint_waivable`(새 키) 안에만: **`[uncertain-phrase, flow-sparse, flow-overuse, tense-present]`** — 문체·흐름 휴리스틱만. `banned_phrases`(AI 상투 문구, C0 되돌림 금지)·출처·수치·발음(`tts-*`)·참조 출처 규칙은 **면제 불가**(목록 밖 kind = 로드 오류).
2. `script.plan`: `lint()` 는 그대로 돈다. 오류마다 면제 목록과 **(kind, sid, text_sha1) 정확 일치**면 통과 — 출력은 `[waived kind sid — decided_by]` 경고줄. 일치하지 않는 오류 하나라도 있으면 지금처럼 실패. **낡은 면제**(일치하는 오류가 더는 안 남, 또는 text_sha1 불일치) = 오류("면제 목록 정리" 메시지).
3. `rule_since` 가 CHANGELOG 태그가 아니거나 `script_approved` 가 그 태그 날짜(CHANGELOG 헤더 날짜)보다 늦으면 로드 오류 — "승인 뒤에 생긴 규칙" 조건을 코드가 지킨다.
4. provenance `lint.waived: [{kind, sid, decided_by}]`(plan row 가 아니라 plan 전체 기록 → `features.lint`). 면제가 없으면 키를 쓰지 않는다(P5).
5. `gate-view` 원고 검토 자료(게이트 ① 묶음)에 **면제 표**(kind·sid·사유·결정 번호)를 넣는다 — 다음 원고부터 사용자가 게이트 ① 에서 본다. 호르무즈는 재현이라 게이트 ① 재승인 없음 — Fable 이 사용자 보고에 적는다.
6. 호르무즈 첫 항목 2개: `uncertain-phrase now_3`, `flow-sparse -`, `decided_by: D-0168`.
7. 테스트 ≥ 5: 정확 일치만 통과 / 목록 밖 오류 = 실패 / 낡은 면제 = 오류 / 면제 불가 kind = 로드 오류 / `script_approved` ≥ 규칙 날짜 = 로드 오류 / provenance 기록. C7: 03 린트 절 한 단락, 05 표 한 줄, WORKFLOWS W0 게이트 ① 자료 목록에 "면제 표".
8. 기록: 호르무즈 now_3 은 **다음 원고 개정 때**(V3 아님) "누가 무엇을 말했는지" 로 고친다 — DECISIONS D162 에 한 줄. 지금은 손대지 않는다.

## 3. 막힘 해제
§2 구현(작은 커밋 1, v5.17.0 안) 뒤 D-0167 §3-1 합성부터 진행. 나머지 V3 범위 그대로.
