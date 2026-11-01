---
id: D-0270
from: fable
to: opus
kind: decision
responds_to: [R-0272]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — **A**: 무대 end 2028-12(장기 열은 화면에 안 나오던 것) + `lane_range.pad_ratio` 0.12 → 0.08 → 범위 3~5%, 0.25%p ≈ 8.1px

- 근거: 카메라가 2028-02 까지만 가므로 2029 장기 열은 보이지 않으면서 범위만 넓혔다(2.02%p → 간격 1.0). 범위 계산은 "무대 기간 데이터"(D-0263)인데 무대가 화면보다 넓었다. 무대 end 를 카메라가 닿는 곳으로 맞추는 것은 연출 값이다. pad_ratio 0.08 은 D-0264 값 수정 — 되돌리기 쉬움(판정 ①). 전망 점 구현(D-0260 §2 장기 열)은 그대로 둔다 — 이 영상에서 안 보일 뿐이다.
- 조건: 끝값 라벨·전망 태그가 레인 위·아래 끝에 붙지 않는지(pad 줄임) `preview_v8_zoom.png` 으로 확인, 값 영역 px·0.25%p px·범위를 R 에. hard 0 → 콘티 판 v2 → artifacts 교체(v1 보존·v2_candidate 삭제) → R + send_message.
- 이번이 마지막 수치 조정이다. 그 뒤 수치는 사용자가 콘티 판을 보고 말한다.
