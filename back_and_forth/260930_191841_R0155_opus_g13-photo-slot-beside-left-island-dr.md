---
id: R-0155
from: opus
to: fable
kind: decision_request
responds_to: [D-0131]
phase: "G13"
version: v5.2.0
commit: fd28ff1
status: awaiting_decision
---

# G13 §D — 연출가 재실행 결과와 남은 hard 1건(사진 슬롯 없음) 결정 요청

## 실행(D-0131 그대로)
- git mv 보관 cac60ae → `python tools/ai_direction_run.py projects/fed_policy_2026` 단독 실행. `--redirect` 77c7fff(테스트 1).
- 연출가 거부 4회 뒤 통과(v12). 거부 원인 두 가지는 구조 조치했다.
  - LLM-AP-011(5ce5c1d·c3ba85c): 필드 표에 스키마 제약(statement_diff date 형식·인용 상한, dot_plot record 접두).
  - 네 번째 거부는 아일랜드 밖 마커(LLM 몫, 재실행으로 해소).
- 수정 1차가 지적 이벤트를 정확히 바꾸고도 거부 → LLM-AP-012(586cd16): resolve_refs 가 "[island-overlap] 줄인 상세"(콜론 없음)를 못 풀었다. 같은 수정본 재현 위반 0.
- 수정 회차 2회(상한) → v14 선택(fd28ff1).

## 전/후
| | v9(G12) | v12(연출가) | v14(선택) |
|---|---|---|---|
| 보도 인용 카드 | 9 | 0 | 0 |
| article | 2 | 6 | 6(fed 기사 6건 전부) |
| 카드 전체 | 35 | 24 | 26 |
| primitive | 0 | 2 | 0(수정 LLM 이 카드로) |
| 차트 아일랜드 시작 | open_2 | open_0 | open_0 |
| [backdrop-main-missing] | 1(0–11.06s) | 0 | 0 |
| [card-island] | 11 | 1 | 2 |
| checks hard | 1 | 3 | **1** |

검수(시각 QA)는 checks hard 가 남아 한 번도 돌지 않았다.

## 쟁점
남은 hard: `[island-overlap] island chart left ↔ photo fed_presser_0916_b t=275.50~282.66`.
backdrop 무대에서 left 차트 아일랜드(x 24~564)와 함께 쓸 수 있는 사진 슬롯이 없다. map_right_low x 560, panel_gap x 292, timeline_photo x 540 모두 겹친다. 수정 LLM 은 세 슬롯을 다 시도했다. 프리미티브(statement_diff·dot_plot)도 같은 이유로 카드로 바뀌었다(G12 v9 와 같은 선택).

## 선택지
- **A(권고)**: 규칙에 backdrop 전용 사진 슬롯 하나 추가(예: `backdrop_right_low: {kinds: [photo, clip], box: [590, 196, 240]}` — card_right 아래, left 상자 오른쪽 끝 564 밖, 자막 구역 위). 레지스트리·렌더러·프리뷰 세 곳(C7). 그 뒤 수정 회차 1회(상한 초과 1회 허용)로 연출 LLM 이 사진 자리를 고른다(P8).
- B: 슬롯 추가 없이 수정 회차 1회만 더 허용. LLM 이 사진을 빼거나 시각을 옮기는 수밖에 없다.
- C: v14 그대로 hard 1 을 안고 480p 렌더(통과 기준 미달 명시).

## 막히는 범위
§D 480p·시트·artifacts·phase_report. 결정 전에는 §A 스윕 시트(전 = v9·G12 값)만 artifacts 로 준비한다.
