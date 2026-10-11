---
id: R-0219
from: opus
to: fable
kind: decision_request
responds_to: [D-0193]
phase: "D-0193"
version: v5.21.12
commit: (이 보고 — 코드는 작업 트리, 결정 뒤 커밋)
status: blocked
---

# D-0193 기사 카드 무대 통일 — light 골든 2컷 변화(결정 요청)

## 1. 한 일(작업 트리)
| 항목 | 내용 |
|---|---|
| 원인 실측 | 사진 없는 카드의 블러 무대 평균 밝기(Rec.709): dark 지도 0.066·0.070(hormuz 골든 기사 2장), light 지도 0.33~0.38(gulf 6장). 113초는 카드 theme 이 light(흰 덮개)였다 |
| 고침 ① | `article_card.press_fallback.max_luma: 0.075` — 블러·dim 뒤 평균 밝기가 상한을 넘으면 그만큼 더 어둡게(`fallback_gain`). 지도 테마와 무관하게 같은 어두운 무대 |
| 고침 ② | 검사 `article_backdrop` hard — 한 영상 기사 카드 theme 이 둘 이상이면 실패. 연출 문법 한 줄. gulf art_0014 theme light → dark |
| 범위 밖(기록) | 인용(quote) 덮개는 지도 위 반투명 scrim 이라 light 지도에서 회색이다. 이번 의견(기사 카드)에는 넣지 않았다. 필요하면 다음 항목 |

## 2. 골든
- **dark 25/25 바이트 동일**(골든 기사 2장 0.066·0.070 < 0.075).
- **light 2컷 변화**: `p_0145.33`·`p_0189.96`(hormuz light 판 기사 카드) — 블러 무대가 dark 와 같은 밝기로 어두워짐. 글자·배치 무변경. 증거 `docs/handoff/reports/phaseD0191/golden_light_article_backdrop.jpg`.

| 선택지 | 내용 |
|---|---|
| **A(권고)** | light 기준선 두 컷 md5 갱신(superseded 기록). 지시 그대로 "지도 테마와 무관하게 같은 모습"의 직접 결과 |
| B | 상한을 light 에만 적용하지 않음 | 지시와 어긋남(테마별 다른 무대) |

## 3. 막히는 범위
결정 전까지 v5.21.12 커밋 보류, 그 사이 D-0194(인용 ⊂ 화면 문장 검사) 분석.
