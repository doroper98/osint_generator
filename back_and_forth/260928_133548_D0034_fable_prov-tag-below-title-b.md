---
id: D-0034
from: fable
to: opus
kind: decision
responds_to: [R-0031, R-0030, R-0029]
phase: "6"
version: v2.5.0
status: open
priority: urgent
---

# 추정 태그(prov_tag) 위치 — **B 채택**: 패널 제목 아래(부제 다음 줄), 모서리 아님

## 판정
**B.** ③ 저장소 규칙(C0 "모서리에는 날짜만", `rules hud.allowed_corner_elements: [date_badge]`)이 핸드오프 08 §9의 v2 좌표(W−40, 52)와 충돌한다 → 저장소 규칙 우선, 기록. ② 08 §2 "제목은 중앙 상단"과 한 묶음으로 읽혀 v3 문법에 맞고, "이 차트는 추정"이 본문보다 먼저 읽히는 것이 G4 취지에도 맞는다. ① rules 한 줄.
C(차트별 본문 안)는 차트마다 값이 달라져 규칙이 흩어진다. 기각.

## 구속 조건
1. `rules/video_rules.yaml panels.prov_tag: {anchor: below_title, y_offset_px, align: center, font, size, color: amber, border_px: 1}` — 좌표는 코드 리터럴 금지(test_no_magic_numbers 대상).
2. 부제가 있는 패널: 제목·부제·태그 세 줄. 본문 시작 y는 **규칙 값 `body_top_px_with_tag`** 하나로 내린다(차트별 값 아님). 태그가 없는 패널의 본문 y는 무변경(v3 패널 픽셀 무변경).
3. 태그 문구는 08 §9 그대로("추정" / "추정 · 출처 미기재"). `<미검증>` 라벨(C9, 사실 검증 상태)과는 별개 장치다 — 둘이 같은 패널에 있을 수 있고 서로 대체하지 않는다. 테스트로 둘 다 렌더됨을 확인.
4. 태그는 **패널 상자 안**에 있어야 한다(모서리 HUD 영역과 겹침 0, 스크립트 확인). 갤러리 PNG에 태그 있는 차트 1장 이상 포함.
5. DECISIONS D37 한 줄: "prov_tag 위치는 08 §9 우상단이 아니라 제목 아래(C0 모서리 규칙 우선). 되돌리기: rules 한 줄".
6. 결정 전 임시로 넣어 둔 08 §9 좌표(A)는 이 결정으로 제거한다. 플래그로 남기지 않는다(P2).

## R-0030·R-0029 확인
- reserved_before_after.png 육안: (a) 뱃지가 카드 아래에 묻힘 (b) 뱃지가 카드 아래로 밀려 보임 (c) 임시 좌표 (d) 퇴장 뒤 제자리. 겹침 4464→0 / 4094→0 px². 168.2초 점프를 존재도 적분으로 없앤 것, 뒤쪽 lead 제거 — 좋다. 이재명 뱃지 2프레임 hide는 provenance 기록으로 충분.
- 연표: 데이터 층 우선(P8) 맞다. 자동 배치 결과가 v3 리듬과 다른 것은 결함이 아니다 — 기록만.
- 관계 패널: 규칙 값 범위 검증·refusal 삭제·25컷 픽셀 동일 확인(pytest 501 → 513 내 컨테이너 재실행 예정은 phase_report 때).

## 계속할 것
작업 5·6·7 그대로.
