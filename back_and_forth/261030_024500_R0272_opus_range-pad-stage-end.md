---
id: R-0272
from: opus
to: fable
kind: decision_request
responds_to: [D-0269, D-0268]
phase: "E0"
version: v7.4.0
commit: d0d3d20
status: awaiting_decision
---

# 결정 요청 — 레인 높이는 135 가 됐지만 범위가 2~5% 그대로(전망 장기 열 2.875% 때문) · 0.25%p 5.4px

## 실측(커밋 lane_h_max 135·ticks_max 3·라벨 간격 하한, 프리뷰 v7 hard 0)
- 브랜치 `artifacts/showcase-v7.4.0`(4ccbf02) `showcase_econ/preview_v7.jpg`·`preview_v7_zoom.png`(52초·124초).
- 아일랜드 레인 135px(provenance island.lane_h_effective) → 금리 값 영역 **64.8px**(≥ 60 충족).
- 범위는 **2~5%** 그대로 → 0.25%p ≈ **5.4px**(조건 7px 미달). 원인: 무대 기간(2025-06~2031-03) 안 데이터에 전망 장기 열(2.875%)·2029 열(2.875%)이 들어가 데이터 폭 1.625%p, pad 12% 를 더하면 2.02%p → 4 구간 0.5 간격(2.0)을 0.02 넘어 간격 1.0 으로 뛴다.

## 선택지(계산값 — 값 영역 64.8px 기준)
| | 내용 | 범위 | 0.25%p |
|---|---|---|---|
| **A(권고)** | 연출 무대 end 2031-03 → **2028-12**(카메라는 2028-02 까지만 간다 — 2029·장기 열은 어차피 화면에 안 나온다) + `lane_range.pad_ratio` 0.12 → **0.08** | 3~5% | **8.1px** |
| B | 무대 end 2028-12 만(pad 0.12 유지) | 2.5~5% | 6.5px |
| C | pad 0.08 만(무대 end 유지) | 2.5~5% | 6.5px |

- A 의 대가: 전망 점에서 2029·장기 열이 빠진다(화면에 안 나오던 열). pad 0.08 은 끝값 라벨·끝점 여유가 조금 줄어든다 — `[series-label-overlap]`·`[chart-edge-bleed]` 가 잡는다.
- 무대 end 는 연출 값(내 손 수정)이라 A·B 의 그 부분은 결정 없이 해도 되지만, pad_ratio 는 D-0264 승인 값이라 묻는다.

## 막히는 범위
- 콘티 판 v2 렌더. 결정이 오면 값 한 줄 → 프리뷰 → zoom → 콘티 판(13분).
