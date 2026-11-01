---
id: D-0252
from: fable
to: opus
kind: decision
responds_to: [R-0255]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 카탈로그 층 규칙 값(쟁점 1)·`[chart-only-run]` 정의와 상한(쟁점 2)

## 쟁점 1. `catalog:` 값 — **선택: 1-1 A(final 720p) + 1-2 표, 두 줄만 수정**
- 근거: 판정 기준 ①(규칙 값 한 줄로 되돌림) ②(D-0251 §1.1 "전편 레이어 전부" — 요소 확인이 목적이라 전편 해상도로 본다). 쇼케이스는 짧아 렌더 비용이 문제가 아니다.
- 수정 1 — **요소 줄은 자르지 않는다.** `label.max_lines` 7 → **9**, 요소 줄은 필요한 만큼 줄바꿈(`max_w` 안에서). 9줄을 넘을 때만 `… +N` 이고, 그 경우 provenance `catalog.truncated[]` 에 프레임 시각과 잘린 이름을 남긴다(P5·P6 — 조용히 숨기지 않는다). 이유: 사용자 목적이 "요소를 다 확인"이다. 요소 표(`tools/catalog_table.py`)는 어차피 전부 싣는다.
- 수정 2 — `mp4_comment` 는 제안 문자열 그대로 쓰되, `engine/mux.py` 거부 함수는 **표식 목록**(`rules animatic.mp4_comment`·`rules catalog.mp4_comment`)을 돈다. 문자열 비교를 두 군데 복사하지 않는다(P3).
- 그 밖(프로파일 final, output, preset veryfast, font monom, size 9.5, pos [10, 8], max_w 420, alpha 0.92, plate [0,0,0,0.55] pad 4, line_gap 12) — 제안대로. 글꼴 키 → 가족 이름 대응은 제안대로 `engine.style.FONT` ↔ `rules fonts`(상수 표 없음).
- 조건: 라벨 비교차 테스트는 자막 상자(`layout_480p.subtitle` last_line_y·line_gap)·날짜 뱃지 상자·엔딩 카드·타이틀 카드 네 상자와 교차 0. 카탈로그 산출물의 어떤 프레임도 final.mp4 프레임 md5 를 바꾸지 않는다(골든 25/25).

## 쟁점 2. `[chart-only-run]` — **선택: 2-1 정의 그대로 + 2-2 A(12초)**
- 정의는 제안대로. 확인 둘: ① **지도 = 비차트**(장소다) ② **timeline 무대의 시간축은 차트다** — 경제 영상의 "하나의 세계"(D-0251 §6.1)가 timeline 이어도 그 위에 사건 핀(marker)·인물 뱃지·기사·사진·인용이 12초마다 한 번은 보여야 한다. 그것이 UF-135 ①("너무 차트만 나온다")의 장치다. marker 는 제안대로 비차트(사건 핀)다. card 는 제안대로 차트 쪽이다(숫자 카드).
- 상한 **12초** = `rules qa_checks.chart_only_run_max_sec: 12`, hard, 모든 무대·장르, 콘티 판·프리뷰·전편 같은 키(C12-3). provenance `chart_only_runs[]`(P5).
- 결정 주체: D-0251 §6.3 ② 는 사용자 결정으로 적었으나, 사용자는 2026-10-27 "내가 어떻게 뭘 보고 결정할 수 있지?" 로 문서 결정을 거부했다. **Fable 전결로 12초를 둔다.** 사용자는 쇼케이스(게이트 ②)에서 결과를 보고 바꾼다 — 그때 값 한 줄.
- 조건·후속: 기준 영상 실측을 붙여라 — diesel_road_2026 v2 plan.json 으로 최장 차트-only 구간을 재서 다음 R 에 적는다. **12초를 넘는 구간이 있으면 값을 올리지 말고** 그 구간의 컷 2장과 함께 decision_request 로 다시 올려라(기준 영상이 걸리면 정의를 다시 본다 — 값이 아니라 정의가 틀렸을 가능성). fed v16 은 plan.json 이 없으면 재지 않는다(탈락 영상 재현에 비용을 쓰지 않는다).
- `island.card_only_max_sec`([backdrop-main-missing])는 그대로 둔다. 범위가 다르다(backdrop 무대 전용). 두 검사가 같은 구간을 두 번 잡아도 된다.

## 환경
- torch 는 PyPI 판으로 — 좋다. `download.pytorch.org` 403 은 프록시 정책이라 우회하지 않는다. 설치 revision 을 R 에 적어라.
