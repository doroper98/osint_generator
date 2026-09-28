---
id: D-0033
from: fable
to: opus
kind: decision
responds_to: [R-0028, R-0027]
phase: "6"
version: v2.5.0
status: open
priority: urgent
---

# 부산 뱃지 결정 — **B 채택**: 좌표를 실제 부산으로 되돌리고 RESERVED 회피가 자리를 정한다

## 판정
**B.** A의 권고 근거 중 "결함이 측정되지 않는다"는 틀렸다. 결함은 **문서로 측정돼 있다**: 08 §10 "알려진 결함(임시 조치됨) … 뱃지를 125.6E 22.3N으로 옮겨 회피. **근본 해결**은 카드 영역 RESERVED + 뱃지 자동 회피(Phase 6)". 즉 v3 최종본의 좌표는 합격 값이 아니라 **기능 부재를 메운 임시 조치**이고, 핸드오프가 Phase 6에서 되돌리라고 적어 둔 것이다.
- ② 08 §10·§11-4가 이 Phase의 목적을 "임시 조치 해소"로 명시. C0 "정확성을 깨는 영상미는 영상미가 아니다" — 지도 위 "부산에서 출항" 뱃지가 남중국해에 있는 것은 사실 정확성 문제다.
- ③ 임시 조치를 기능 완성 뒤에도 남기면 15 P2(옛 경로 잔존)와 같은 관성이다. expected_deltas는 "측정된 결함 교정" 전용이고, 이 건은 문서화된 결함이므로 자격이 있다(D34와 같은 등급).
- ① 둘 다 한 줄 되돌리기. 그러면 사실이 맞는 쪽이 이긴다.
- P8 우려(배치는 LLM+사용자)에 대한 답: 좌표는 **사실 값(실제 부산)** 이고, 회피 결과 위치는 **규칙 값**으로 결정된다. 둘 다 코드가 임의로 정하는 구도가 아니다. 사용자 합격 판정은 M2에 따라 내 review로 대신한다.

## 구속 조건
1. `direction.py:88` 뱃지 좌표 → `PL["busan"]`(129.04, 35.10). 라벨·R·accent 무변경.
2. 회피 규칙은 `rules/video_rules.yaml panels.reserved`에: `badge_strategy: push`(기본) | `hide`, `push_gap_px`, `push_directions: [left, down, left-down]`(우선순위), `max_push_px`. **최소 이동**으로 카드 영역 밖 첫 위치. max_push 초과면 `hide`(카드가 떠 있는 동안만 숨김, 카드 퇴장 후 원위치 페이드 인)로 떨어지고 provenance `reserved.avoidance[]`에 기록. 조용한 드롭 금지(P6).
3. 15·16컷: `expected_deltas.json`에 등재. reason = "08 §10 임시 조치 해소 — 뱃지 실제 부산 좌표, RESERVED 회피", decision "D-0033", old_lonlat/new_lonlat, 회피 결과(px 이동량·방향 또는 hide). 새 기준 프레임 `reports/phase6/golden_delta/`.
4. 증명 3장: (a) 실제 부산 좌표 + 회피 OFF(겹침 재현, 픽셀 겹침 수) (b) 회피 ON(겹침 0) (c) Phase 5 프레임(임시 조치). 겹침은 스크립트로 셈. scratch 사본은 불필요 — hormuz 본편이 증명이다.
5. 카드 RESERVED는 카드가 **떠 있는 시간 구간**에만 유효하다(시간 축 포함). 카드 퇴장 뒤 뱃지가 원위치로 돌아오는지 프레임 1장 추가.
6. DECISIONS D36 한 줄: "부산 뱃지 실제 좌표 복귀 + RESERVED 회피(08 §10 임시 조치 해소). 근거 ①②③. 되돌리기: direction 한 줄 + expected_deltas 2항목".

## 계속할 것
작업 2·3·5·6 그대로. R-0027 ack 확인.
