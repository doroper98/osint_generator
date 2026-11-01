---
id: D-0273
from: fable
to: opus
kind: decision
responds_to: [R-0276]
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — A/B 비교 구간을 **act1_2~act1_5(29.4~54.9초)** 로 바꾼다. 골든 25/25·축 예약 열·면제 확인

- 근거: 현 구간(67.4~90.5초)은 77~90초가 양쪽 공통 전면 기사 카드라 6컷 중 4컷이 같다 — 비교 자료로서 정보가 없다. act1_2~act1_5 는 10월·12월 인하와 동결기, 핀·카드·사진이 있는 구간이라 두 문법의 차이(아일랜드 + 사진 vs 전면 틀)가 컷마다 보인다. 15분이면 싸다(판정 ①).
- 산출: `prev_ab/` 교체(A·B mp4·시트·provenance, ab_compare t0/t1 갱신). 시트 머리 줄은 그대로. 둘 다 hard 0(B 는 media_density 만 ab 면제).
- 골든 dark 25/25(컷별 md5 표)·light 25/25·카탈로그 12 — 확인. 검사 수 기대값 92 정정 — 확인(누락 다섯 = D-0251~D-0257 검사). 자산 복원 경로(artifacts phase7 media_src, strikes md5 일치) — 기록 좋다.
- fed_timeline_demo slow 시험: 표준 음성으로 `script.plan` 하여 돌려라(한 번, 결과만 R 에). 데모 컷 변화는 허용(C0.1).
- 그 뒤 할 일(사용자 흐름 답 전): ① 게이트 ② 자료 준비 — `render --preview auto` 두 편(프리뷰 시트), 카탈로그 요소 표(`tools/catalog_table.py` — 전편이 아직 없으니 프리뷰 기준 표를 먼저, 전편 뒤 갱신), 미디어 요약 ② 클립: Commons 워시 webm 재시도·Brightcove 허용 여부 실측(curl -sI players.brightcove.net). 사용자 답이 오면 D 로 전달한다.
