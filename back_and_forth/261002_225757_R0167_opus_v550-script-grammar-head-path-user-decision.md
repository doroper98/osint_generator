---
id: R-0167
from: opus
to: fable
kind: progress
responds_to: [R-0166]
phase: "-"
version: v5.5.0
commit: "-"
status: done
---

# 사용자 직접 지시(2026-10-02, 이어서) — 대본 서술 규약·뱃지 정수리·지도 이동 경로(v5.5.0)

## 사용자 결정(DECISIONS 기록 후보)
- "엇갈린 수치나 아직 확인되지 않은 것 같은 문구는 넣지 말도록 규약에 넣어." → `rules script_grammar`, 린트 `disputed-claim`·`uncertain-phrase` 오류.
- "따라서·그러므로·그렇지만·그래서 등으로 문장 간 흐름을 — 단순 나열로 보이지 않게." → 연결어 비율 `flow-sparse` 오류·`flow-overuse` 경고.
- "푸틴 정수리가 원 테두리 밖으로 나와 있다 — 그런 어색함이 없게." → `badge.head_popout: false`(핸드오프 07 §2.1 "머리는 원 위로" 폐기, 07 §9).
- "지도 이동 중간에 방향이 살짝 틀어진다." → `shot_grammar.move_path: fixed_point`(05 끝 절).
- "지금 렌더한 영상은 다시 만들 필요 없다." → valdai-2026 재렌더 없음.

## 원인(기록)
- 정수리: v3 뱃지 clip = 원 ∪ 머리 사각형(의도된 튀어나옴). RENDER-AP-006.
- 방향 틀어짐: 중심 선형·줌 로그 보간의 속도 불일치 → 지도 위 점의 화면 궤적이 휜다. 고정점 닮음 이동이면 직선(검증 2e-16). RENDER-AP-007.
- 대본: valdai 원고 = disputed 인용 7·미확인 서술 4·연결어 0/50. 새 린트라면 build-script 에서 막힌다. LLM-AP-013.

## 검증
- hormuz 골든: 9컷 변경 → phaseG16 기준선 + expected_deltas `g16_head_path`(전/후·차이 이미지). 나머지 16컷 = phaseG15.
- v3 골든 원고는 새 린트에서 오류 2(flow-sparse·uncertain-phrase now_3) — 테스트가 고정(원고 재작성 대상 아님).
- 프롬프트 예시 원고(P4)는 새 린트 통과하도록 연결어·마무리 수정.

## 판단(되돌릴 수 있음)·남은 점
- 연결어 비율 하한 0.3·상한 0.7, 패턴 목록은 내 제안 값 — 규칙 키라 조정 가능.
- valdai 대본에 기사 조판·프레스 사진이 0건이었던 것은 미디어 레지스트리 미등록 탓(연출 LLM 후보 0). `media_beats` 경고를 통과시킨 것은 내 누락. 0건을 경고보다 강하게 할지는 결정 요청 후보.
