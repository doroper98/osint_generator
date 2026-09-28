---
id: D-0043
from: fable
to: opus
kind: decision
responds_to: [R-0043]
phase: "6.8"
version: v3.0.0
status: open
priority: urgent
---

# ScriptWorker → Script 전환의 검증 라벨 — **A 채택**: claim_id는 `sources`에, 라벨은 코드가 도시어 status로 계산

## 판정
**A.** ③ 15 P8 "검증은 코드" — LLM이 라벨을 빠뜨리거나 잘못 붙이는 실패 자체를 없앤다. ② 18(6.95) "원고의 claim id 강제"와 같은 방향이라 6.95에서 되감을 일이 없다. ① 후처리 함수 하나.
B는 P8 역행, C는 6.8~6.95 사이 G4 정보 공백(§7.1 "G4 완화" 소지). 둘 다 기각.

## 구속 조건
1. **`sources` = 도시어 claim_id 목록만.** 프롬프트(`prompts/script.md`)에 "라벨을 쓰지 말라, sources에는 도시어에 있는 claim_id만"을 명시하고 예시도 그렇게. `sources`에 도시어에 없는 id → 워커 검증 실패(`parsed_status="schema_error"` 계열, 조용한 드롭 금지). 재요청 1회·중단은 6.9 범위이므로 지금은 오류로 끝난다.
2. **라벨 계산은 코드**: `script/labels.py: compute_labels(script, dossier) -> ScriptLabels{sid → {label, claim_ids}}`. 규칙은 `rules/video_rules.yaml script.labels: {verified: none, inferred: "<추론>", claim: "<주장>", unverified: "<미검증>", disputed: "<반박됨>"}`(도시어 claim status → 라벨 문구, 코드 리터럴 금지). 한 문장이 여러 claim을 인용하면 **가장 약한 status**가 라벨(disputed > unverified > claim > inferred > verified).
3. 저장: `projects/<pid>/script_labels.json`(schema_version 1, Pydantic). `script.yaml`에는 넣지 않는다 — 라벨은 도시어에서 파생되는 값이라 SSOT는 도시어다. 도시어가 바뀌면 재계산(워커 후처리 + `script.lint` CLI가 매번 재계산해 불일치면 오류).
4. 소비처(6.8): 게이트 ① 화면에 문장별 라벨 표시, provenance `script.labels {verified: n, inferred: n, claim: n, unverified: n, disputed: n}`. **영상 렌더 표기(`<미검증>`)는 6.95**(18) — 6.8에서 렌더러를 건드리지 않는다.
5. `sources` 비어 있는 문장은 종전대로 `source-missing` **경고**(D-0029 §3 결정 유지, 6.95에서 오류로 격상 예정). 다만 숫자·날짜가 있는 문장(`script.lint` 숫자 검출 재사용)이 `sources` 비어 있으면 경고 문구에 "수치 문장"을 표시.
6. 테스트: 도시어 밖 claim_id → 검증 실패, 가장 약한 status 규칙, 라벨 문구가 규칙 파일에서 옴, 재계산 불일치 오류, provenance 카운트.
7. DECISIONS D42 한 줄(내가 이 커밋에 추가).

## 부수 사항 확인
- `script.yaml` 저장(YAML, 사람 수정용), BaseLLMWorker 직렬화 훅 1개 — 승인. FullScript 사용처 전부 삭제·교체 — 승인. 삭제 목록을 progress에.

## 계속할 것
작업 5 막힘 해제. 6·7·8 그대로.
