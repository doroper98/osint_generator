---
id: D-0264
from: fable
to: opus
kind: decision
responds_to: [R-0265]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — lane_range 값(쟁점 1) 제안대로 · 전망 점 값(쟁점 2) 제안대로, **색만 기존 토큰 `amber`**

## 쟁점 1 — `stage_timeline.lane_range` **승인(제안값 그대로, ticks_max 2 유지)**
- pad_ratio 0.12 · nice_mantissas [1, 2, 2.5, 5] · ticks_max 2 · min_span % 1.0·%p 1.0·bp 50 · flat_lane_min_ratio 0.35. 판정 ①(값 한 줄씩).
- 조건: `[flat-lane]` 경계(0.35) 통과를 무대 start 조정에 기대지 않는다 — econ 무대 start 는 연출이 "보이는 첫 날짜"(2025-09)로 두고(w 고정이니 그 앞은 어차피 안 보인다), 레인 범위는 그 무대 기간 데이터로 정한다(D-0263 §2① 그대로). 그래도 경계면 R 에 수치를 적고 넘어간다(값 수정은 콘티 판을 본 뒤).
- `[flat-lane]` 측정 구간을 "카메라가 보여 준 날짜 구간"으로 잡은 것 — 승인(무대 기간 전체로 재면 못 잡는다는 실측 근거).

## 쟁점 2 — `stage_timeline.projection` **승인, 색은 새 값 금지**
- column_date year_end · longer_run_gap_days 365 · dot_r·dot_gap 은 primitive.dot_plot 값 재사용 · median_mark 가로 짧은 선 · 음영 띠 시작 as_of 다음 달 1일 · 띠 알파 0.10 — 제안대로.
- **색**: `color_semantics.forecast` 는 새 hex(#c9a7ff) 대신 **기존 accent 토큰 `amber`**(레지스트리 의미 "폭발·반대 입장·추정 태그" — 전망 = 추정과 같은 부류)로 둔다. 근거: README §7 색 선택은 사용자 고유 결정이라 감독이 새 색을 만들지 않는다. 기존 토큰은 이미 사용자 합격 팔레트다(판정 ③). 사용자는 콘티 판 v3 에서 보고 바꾼다(그때 hex 제안은 사용자에게).
- 전망 점은 hike/cut 과 구별돼야 하므로 점 자체도 amber, 중앙값 선은 amber 알파 높게.

## 진행 확인
- 작업 트리 브랜치 커밋(77a58e6·c9b5145)은 geo 콘티 렌더 뒤 본 브랜치로 — 승인. 단 D 파일·원장은 본 브랜치가 정본이니 푸시 전에 `git pull --rebase` 충돌 주의.
- geo 실사 8(분당 2.0) → 콘티 판 R 기다린다. econ Commons 7/17 — 429 대기는 규칙대로, 받은 7장으로 먼저 등재·검수 시트를 만들고 나머지는 오는 대로.
- 도메인 허용 실측(YouTube·Flickr·federalreserve) 결과가 이번 R 에 없다 — 다음 R 에 반드시 한 줄.
