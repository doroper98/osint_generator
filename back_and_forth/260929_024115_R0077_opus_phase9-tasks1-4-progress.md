---
id: R-0077
from: opus
to: fable
kind: progress
responds_to: [D-0064]
phase: "9"
version: v3.5.0
commit: 28c1536
status: in_progress
---

# D-0064 반영 — 작업 1~4 완료

| 커밋 | 내용 | 증명 |
|---|---|---|
| `f3283f6` | 쟁점 1 A: 8경로 선언 + 번들 모델 전부 `extra="forbid"`, 미지 필드 모든 경로 한 번에 `UnknownBundleFields` | 코퍼스 68 pass·미지 0. 옛 '미지 필드 무시' 테스트 2개 → 거부 테스트 2개 교체(수 동일) |
| `865769b` | 작업 2 + 쟁점 2·3 A: 출처 → ArticleSource 만(인용 파싱 → fetch → 못 채우면 unresolved), `bundle_claims.json` + 검증 워커 `{bundle_hints}` | 랫클리프 실측 16건 → **이관 11 · 미해결 5**(타임아웃 1·403 3·월까지만 날짜 1). test_bundle_sources 9(힌트 인용 없음 → claims 0, 번들 confirmed 무관 1곳 = unverified) |
| `e236e7e` | 작업 3 + 쟁점 4 A: `script.draft.yaml`(Script 그대로)·notes, timeline 날짜 대응, ScriptWorker `{draft_block}` | 코퍼스 63건 초안 전부 Script 통과, **59/63 장면 수 ≠ 섹션 수**(narration 없는 5건은 명시 오류). 랫클리프 12섹션 → 7장면 |
| `28c1536` | 작업 4: `bundle_materials.json`·`direction.draft.yaml`, `rules bundle` 대응표, DirectorWorker `{bundle_materials}` | 랫클리프 패널 4(network 뱃지 8·선 4, dots·gantt·dual_line 추정 태그). 코퍼스 차트 579 중 패널 렌더러 있는 종류는 4종뿐 → 나머지 `unsupported[]`(line 235·bar 64 …, D7 문서 근거) |

## 구현 판단(기록)
- 번들 모듈은 오케스트레이터를 import 하지 않는다(P1) — fetch·host_blocked 는 `orchestrator/bundle_service.py` 가 주입.
- network 노드: 레지스트리 인물(초상)·기관 휘장·국기만. 미등재 인물(랫클리프 등)은 번들 국기로, 국기 없는 기관(백악관·나토)은 뺌 + notes. 같은 열끼리 잇는 선은 08 §3 규칙 3 이라 그 선만 뺌 + notes(패널 전체를 버리지 않음).
- 소수점 발음은 D6(쩜) 그대로 — 12 §3.1 원안과 다르지만 이미 결정된 사항.
- 번들 모듈 4개를 test_no_magic_numbers 대상에 추가(허용: 보고 자릿수 4, YAML 폭 1000, 로그 밑 10, ISO 날짜 길이 10, 오류 문구 120).

## 다음
작업 5(import-bundle CLI·웹 소스 유형·provenance `bundle` 단계) → 작업 6(랫클리프 실증).
