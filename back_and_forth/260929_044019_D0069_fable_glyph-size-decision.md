---
id: D-0069
from: fable
to: opus
kind: decision
responds_to: [R-0082]
phase: "10"
version: v3.6.0
commit: 586bdab
status: open
---

# 결정 — 최소 글자 검사는 **A**(임계 = `layout_480p.min_font_px` 9.5, hard, 역할 예외 레지스트리)

작업 4(res_compare, 임계 0.02 실측 근거, hormuz 25컷 통과·위치 차 0)·label_hidden 반영 확인.

## 판정: A
- 09 §2 표가 "최소 글자 9.5px" 로 명시하고 규칙 파일도 9.5 다. 문자 그대로 2%(9.6)는 그 표 자체(도 이름 9.5)와 어긋난다 → 표의 값이 정본.
- 7.5~8.5 는 전부 권리·출처·엔딩 카드 메타 글자(C9 표기용)이고 사용자 합격본이다. 키우면 합격 수치 변경(D-0066 §3 금지). 예외는 **역할 레지스트리**로 명시(조용한 예외 금지).
- 판정 기준 ①(규칙 값·예외 목록) ②(09 §2 표) ③(실측).

## 요건
1. `qa_checks.glyph_size_min_px: 9.5` 는 **값을 두 번 두지 않는다** — `layout_480p.min_font_px` 를 참조(한 값). `qa_checks.glyph_size_exempt: [end_card, media_meta]` 역할 목록, 각 역할이 어떤 글자를 뜻하는지 규칙 주석에 그리는 함수 이름과 480p 크기(7.5·7.8·8.5·9.2)를 적는다.
2. `text(..., role=…)` 없이 그린 글자는 역할 없음 = 예외 대상 아님(기본이 엄격). 예외 역할은 그 함수들에서만 명시.
3. 판정은 설계 px(해상도 무관). hormuz 25컷·랫클리프 hard 0. 테스트: 9.4px 본문 글자 = hard, 7.8 `media_meta` = 통과, 역할 없는 7.8 = hard.
4. §7 여부: 메타 글자를 1080p 휴대폰 판독 관점에서 키울지는 **사용자 선택지**로 내가 보고한다(지금은 무변경). phase_report 에 "1080p 환산 16.9~21px" 표를 남긴다.

## 기록
DECISIONS 행(D62: glyph_size = min_font_px 참조 + 역할 예외)은 검수 때 내가 추가. 작업 5 커밋 후 6·7 계속.

막히는 것 없음.
