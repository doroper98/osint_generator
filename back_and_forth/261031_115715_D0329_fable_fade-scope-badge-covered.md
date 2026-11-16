---
id: D-0329
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — ① 영상 시작·끝 검정 페이드는 D-0325 ×1.5 대상이 아니다 ② 덮인 배지는 없는 요소 — 예약 영역 + [badge-covered] hard

- ① `layout_480p.fade {in 1.2, out 1.6}` 는 render.py 의 영상 시작·끝 검정 페이드다. D-0325 §1 표의 그 줄은 감독 오분류 — **그대로 둔다**(UF-159 는 요소 등장·퇴장). 표에서 삭제한 것으로 본다.
- ② 구현 발견(세션 3): showcase_geo 트럼프 인물 배지(206.84~211.88)가 같은 시각 기사 카드 전면 사진(206.64~211.78)에 거의 내내 덮인다. 덮인 배지 = 조용한 드롭(P6).
  - 엔진: 전면 사진 기사 카드 구간을 배지 **예약 영역**에 넣는다(reserved.py). 배지는 빈 슬롯으로 옮기고, 없으면 카드 끝 시각으로 미룬다(at_word 유지, 지연 초를 provenance reserve.avoidance 에 기록). 자막·날짜 HUD 예약과 같은 단계.
  - 장치: checks **`[badge-covered]` hard** — 배지 가시 구간의 덮임 비율 > `badge.covered_max_ratio`(0.5, 감독 제안 값 — 사용자 합격 값 아님)이면 실패. 모든 렌더 경로(C12 §3).
  - 그 구간 프레임 1장(배지가 보이는)을 R 에.
- 순서: 빠른 묶음 3건 → ② → D-0326 → D-0327 → 사용자 게이트 ② 답 → final.
