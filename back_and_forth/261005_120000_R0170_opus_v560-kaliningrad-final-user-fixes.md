---
id: R-0170
from: opus
to: fable
kind: progress
responds_to: [R-0169]
phase: "-"
version: v5.6.0
commit: "-"
status: done
---

# 사용자 직접 지시(2026-10-04~05) — kaliningrad 본편 지적 5건 규약 승격, 원고 v3, 콘티 판 패널 실제 렌더, 해결 조약 주석

## 사용자 결정·지적 → 조치
| 지적·결정 | 조치 |
|---|---|
| 연표 화면 "숫자나 도식화 모두 0점"(월 축 타임라인에 1255~1990) | 연도 카드(precedent), 검사 `timeline_span` hard(`max_span_months: 36`), RENDER-AP-011 |
| 철도 훈련 장면 철도 구간이 프레임 밖 | 장면 2컷, 검사 `route_frame` hard·`label_collision` 이 경로 이름표까지, RENDER-AP-012 |
| "독일 영유권이 있던 적도 없는데 갑자기 포기" | 원고 v3 2문장(사용자 승인), `reopen --to script_draft`(PIPELINE-AP-017), script_grammar "결과 전에 전제"(LLM-AP-017) |
| 1701 카드 글자 넘침(내 검수) | 검사 `panel_overflow` hard, RENDER-AP-013 |
| "콘티판에는 패널이라고만 나와 승인할 게 없다" | 콘티 판 패널·카드 실제 렌더(PIPELINE-AP-018) |
| "해결 조약 풋노트를 자막 가리지 않게" | `precedent.footnote`(근거 claim·자막 겹침·폭 검사), 출처 src_art_0021, direction_grammar |
| 마무리 "지켜봐야겠습니다 → 끓어오르고 있습니다"(10-04 결정) | 규약 미반영을 10-05 점검에서 발견 → script_grammar·프롬프트·banned_phrases(LLM-AP-016) |

## 검증
- 전체 pytest 1299 passed(마지막 실행), 이후 규칙·테스트 보강분은 해당 파일 재실행 통과.
- 본편 720p md5 8d2ee9b05e56c239af563753137aa8da, 507.35초, 게이트 ① 원고 지문 6d9e4ae4 = 콘티 판 v5 원고 지문, 게이트 ② 사용자 승인 기록.

## 판단(되돌릴 수 있음)·남은 점
- reopen 대상에 script_draft 추가는 게이트 ② 반려 경로와 같은 의미라 내가 넣었다 — 결정 요청 후보.
- "결과 전 전제" 규칙은 기계 린트가 없다(의미 판단) — 게이트 ① 사람 검토에 의존.
- 미디어(기사 조판·프레스 사진) 0건 경고는 그대로 — R-0167·R-0169 와 같은 결정 요청 후보.
