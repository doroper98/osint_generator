---
id: R-0024
from: opus
to: fable
kind: decision_request
responds_to: [D-0029]
phase: "5"
version: v2.4.0
commit: c6e000a
status: awaiting_decision
---

# 결정 요청 — 엔딩 카드에 폰트 권리 행을 넣을 것인가 (D-0029 작업 7 × 합격 조건 25컷)

## 쟁점
- D-0029 작업 7: 엔딩 크레딧에 rights_registry **전 자산**(인물·휘장·국기·미디어·BGM·**폰트**·지도) 자동 나열. 누락 → `RightsError`.
- v3 골든 END 컷(288.44초, 25컷 중 하나)의 크레딧 카드에는 **폰트 행이 없다**. 나머지(인물 4·휘장 1·국기·지도·사진·영상 5·음악·내레이션)는 이미 있다.
- 폰트를 카드에 넣으면 END 컷이 바뀐다 → "25컷 mean ≤ 0.01, max ≤ 0.1" 행과 충돌. 넣지 않으면 "카드에 전 자산" 행과 충돌.
- 07 §7.3: 폰트(SIL OFL·G마켓 무료)는 영상 내 표기 의무가 없다. 카드 유지는 사용자 결정(C0).

## 선택지
| | 내용 | END 컷 | 되돌리기 |
|---|---|---|---|
| **A (권고)** | 카드 "휘장 · 국기 · 지도" 절에 `폰트 — IBM Plex Sans KR · IBM Plex Mono · GmarketSans · Noto Serif CJK KR` 한 행 추가. END 컷은 `expected_deltas.json` 에 의도된 차이로 등재(D34 방식), 새 기준 프레임을 phase5 보고서에 둔다 | 1컷 변경(텍스트 한 행) | credits.yaml 한 행 |
| B | 폰트는 카드 대신 설명문(description.txt) 자동 크레딧 블록에만. 검사는 "카드 ∪ 설명문"에 전 자산 | 무변경 | 규칙 한 줄 |

## 권고 근거
- A는 D-0029 합격 조건 "엔딩 카드에 rights_registry 전 자산"을 문자 그대로 만족한다. 25컷 조건의 괄호("뱃지 픽셀 무변경")는 뱃지 컷에 관한 것으로 읽힌다.
- 코드 경로는 A·B 공통이다(`rights:` 참조 + 누락 검사 + `auto:` 절). 차이는 hormuz `credits.yaml` 한 행과 expected_deltas 한 항목뿐 — 되돌릴 수 있다(판정 기준 ①).
- B는 카드가 "전 자산"이 아니게 되어 이후 영상에서 규칙이 흐려진다.

## 막히는 범위
- hormuz 최종 렌더(작업 9)의 END 컷과 credits.yaml 폰트 행만. 코드·테스트·레지스트리·도구 작업은 계속한다.
