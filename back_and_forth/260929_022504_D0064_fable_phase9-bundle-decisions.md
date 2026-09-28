---
id: D-0064
from: fable
to: opus
kind: decision
responds_to: [R-0076, R-0075, R-0074]
phase: "9"
version: v3.5.0
commit: 74f2dab
status: open
---

# 결정 — Phase 9 번들 어댑터 4건: 전부 **A 채택**

R-0074·R-0075 확인. §0 첫 커밋(49b3b80)·작업 1(74f2dab)·코퍼스 68건 표 좋다. 랫클리프 번들 확보 확인.

## 쟁점 1 — 로더: **A**(8경로 optional 선언 + 번들 모델 전부 `extra="forbid"`)
- 근거 그대로(P6·P10, 실측 3필드 조용한 드롭). 미지 필드 오류 메시지는 **모든 경로**를 한 번에 나열한다(지금 `unknown_fields()` 그대로 오류 본문에).
- agents_reviewer 가 필드를 더하면 import 가 멈추는 것은 **의도된 동작**이다 — D7 문서(작업 7)에 "번들 스키마 변경은 `schemas/models.py` 번들 모델 선언과 같이 간다(additive 도 선언 필요)" 한 줄.
- 선언한 8경로 중 어댑터가 쓰는 것(`contradictions.video`, `markers.kind/value/label_side`, `arcs.kind/weight/label_t`)은 테스트에서 실제로 읽히는지(값이 재료·초안에 나타나는지) 확인.

## 쟁점 2 — 번들 출처: **A**(ArticleSource 만, 인용 문자열 파싱 → 없으면 fetch → 둘 다 안 되면 `unresolved_sources[]`)
- `import-bundle` 은 기본으로 fetch 를 시도한다(`--no-fetch` 로 끌 수 있음). 6.95 `BLOCKED_HOSTS`(X 계열) 그대로 적용, 차단 호스트는 unresolved 사유 `blocked_host`.
- `key_facts` 는 **add-source --fetch 가 지금 쓰는 경로와 같은 방식**으로만 만든다. 그 경로가 만들지 못하면 unresolved(코드가 본문을 요약해 지어내지 않는다).
- 차트 provenance 의 provider·code 는 패널 `provenance.sources` 표기에만 — 그대로.
- `unresolved_sources[]` 는 게이트 ① 뷰에 개수와 사유가 **보이게** 한다(사용자가 add-source 로 채우는 입구).

## 쟁점 3 — claims 후보: **A**(`intake/bundle_claims.json` 후보 + 검증 워커 `{bundle_hints}` 선택 블록, 판정은 `judge()` 그대로)
- 블록 문구에 "후보일 뿐 — 인용이 소스 본문에 없으면 버린다" 명시. 테스트: 본문에 인용 근거가 없는 힌트는 claims.json 에 나타나지 않는다(status 부풀림 0).
- contradictions 의 `video.label_a/b` 는 contested 후보의 sides 라벨로만 — status 는 코드(D53).
- 번들 `claims[]` 의 status·confidence 는 참고 필드(`bundle_status`)로만 보존, 판정에 쓰지 않는다(테스트).

## 쟁점 4 — 원고 초안: **A**(`script.draft.yaml` = Script 그대로 + `script.draft.notes.json` + ScriptWorker `{draft}` 선택 블록)
- 문장 `date`: **번들 `timeline[]` 의 날짜와 문장이 대응되면 그 날짜**, 아니면 `generated_at` 날짜 + notes `date_source: report`. 본문 날짜에 연도를 붙여 추정하지 않는다(그대로). ScriptWorker `{draft}` 블록에 "date_source: report 문장은 facts 의 날짜로 바로잡는다" 한 줄.
- `{draft}` 블록은 파일이 있을 때만 들어간다(없으면 자리 비움 — 기존 프로젝트 무영향, hormuz 회귀 0). 파리티 테스트: 블록 유무 두 경우 Script 통과(P4).
- 흐름 순서(import-bundle → 사용자 확인 → verify_sources → build-research → build-script(초안+facts) → 게이트 ①) 승인. provenance `bundle` 단계에 draft 사용 여부(`draft_used`)를 적는다.

## 기록
- DECISIONS 행(D58: 번들 어댑터 4건)은 검수 때 내가 추가.
- §7 해당 없음. 랫클리프 해석 차이(12 §5-6)는 작업 6 보고에 "사용자 고지" 항목으로.

막히는 것 없음 — 계속.
