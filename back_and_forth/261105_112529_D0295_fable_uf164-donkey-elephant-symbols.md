---
id: D-0295
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-164 — 당나귀·코끼리(정당 상징)를 화면에 보이게 한다 (D-0294 v1.2 작업에 합친다)

## 0. 사용자 원문(2026-11-05 11:35 KST)
> "민주 공화를 의미하는 그 당나귀와 코끼리 이미지도 보이게 되는거지?"
- 원장 UF-164(open, 장치는 전달 뒤). 감독 답: 현재 계획에 없었다 → 넣는다. **v1.2 와 같은 R 로** 올린다(게이트 ① 재요청 한 번에).

## 1. 무엇을 넣나
1. **basics 막에 상징의 유래 1~2문장**(사실, 1차·2차 출처): 당나귀 — 1828년 앤드루 잭슨을 반대파가 'jackass' 라 부른 것을 잭슨이 받아들인 데서 시작, 만평가 토머스 내스트가 1870년 하퍼스 위클리 만평 "A Live Jackass Kicking a Dead Lion" 으로 굳힘. 코끼리 — 내스트 1874-11-07 하퍼스 위클리 "The Third-Term Panic". 공화당은 코끼리를 공식 상징으로 쓰고, 민주당은 당나귀를 공식 채택한 적은 없지만 널리 쓴다(이 문장은 출처 2건 일치 때만). 출처: 의회도서관(loc.gov) 내스트 만평 설명 · 스미스소니언(smithsonianmag.com) · 하퍼스 위클리 원본 스캔(Commons). 발음 텍스트: "하퍼스 위클리", "토머스 내스트".
2. **사진 2장(PD)**: Commons 스캔 "A Live Jackass Kicking a Dead Lion"(Harper's Weekly 1870-01-15, Nast) · "The Third-Term Panic"(1874-11-07). 저자 1902년 사망·1870년대 출판 → PD-US·PD-old. 자료사진 표기(연·월). basics 문장에 가운데 큰 액자(UF-148 방식).
3. **범례용 emblem 뱃지 2개**(파랑 = 민주 당나귀, 빨강 = 공화 코끼리): Commons 에서 **CC0/PD 실루엣**(openclipart 계열, 예: "Donkey silhouette", "Elephant silhouette" — 라이선스 페이지 대조) 을 `assets/emblems` 레지스트리에 권리 기록과 함께 등록(badge kind emblem, 배경 원판 색은 `colors.dem`/`rep` — 뱃지 원판 색을 accent 로 줄 수 있는지 확인, 안 되면 기본 원판 + 라벨 "민주당"/"공화당"). 자리: cold_2("일곱 곳이 민주당으로")·act1 상원 versus 앞뒤(badge-over-panel 금지 — 패널 밖 시간)·act2 첫 주 투어(텍사스 dem 강조 옆) 등 **3~4회**, 매번 문장 사유. `asset_library.py promote` 로 공용 자산.
4. **공식 로고(DNC 당나귀·RNC 코끼리)는 쓰지 않는다** — D5(위키미디어 Restrictions insignia·trademarked → 쓰지 않고 대체, 예외 없음 — README §7.2). PD 만평과 CC0 실루엣이 있으니 D264 를 끌어올 필요가 없다. 레지스트리 `note` 에 사유 한 줄.

## 2. 처리
- claims 2~3건(상징 유래) + sources(loc.gov·smithsonianmag·Commons 파일 페이지). 린트 0. gate-view·gate1_elements(basics 행에 만평 2·emblem 뱃지)·media_notes 갱신.
- 실루엣이 CC0/PD 로 못 찾히면 뱃지는 생략하고 만평 2장만(사유 media_note) — 결정 요청 없이 진행, R 에 보고.
- D-0294 v1.2 R(gate_request) 에 이 항목을 함께 담아 올린다.
