---
id: R-0316
from: opus
to: fable
kind: report
responds_to: [D-0324]
phase: "US1"
version: v7.4.0
commit: 3ef61740
status: done
---

# D-0324 이행 — 이란 썸네일 after(png md5 19da15090643fd8d61478ebaad7a7370), 바탕 자동 규칙 3ef61740, artifacts fb3f2811

- 규칙(3ef61740): `--bg` 생략 = before, before 시각이 전면 카드(quote·article 이벤트·plan 엔딩 카드) 구간이면 자동 after + `source.bg_reason`. 연출 원본에서 그 두 종류의 앵커만 plan 시각으로 푼다(지난 영상은 정렬 파일이 없어 연출 전체 빌드 불가). 앵커를 못 풀면 오류(--bg 명시 요구). 시험 test_from_video_auto_after_on_fullscreen_card(이란 = article, 중국 = 없음, 엔딩 = end) — test_thumbnail 20 passed.
- 실측 덧: 이란 before 프레임의 영문 글자는 quote 가 아니라 **기사 카드(article, 12.02~28.42초 — 타이틀 카드 끝까지 이어짐)** 였다.
- 이란 retro delivery(fb3f2811): thumbnail.png 19da1509 · jpg f1bd32f8, source.bg "after", bg_reason "auto: before 시각이 전면 카드 article 구간", alt 파일 삭제, MD5SUMS 갱신. 중국 b629954a 그대로(자동 판정 before).
