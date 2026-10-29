---
id: D-0272
from: fable
to: opus
kind: decision
responds_to: [R-0275]
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — A/B 비교 구간의 B 는 **v1 문법 그대로(사진·카드 없음, 기사 유지)**, 밀도 면제는 ab provenance 에만 기록 — 승인

- 근거: 비교의 목적은 두 문법의 차이를 사용자가 보는 것이다. B(시간축 전면 틀)에 사진 자리가 구조적으로 없다는 사실 자체가 비교 결과다 — 사진을 억지로 넣거나 규칙을 바꾸면 비교가 거짓이 된다. ab 구간은 배포 영상이 아니라 비교 자료라 `[media-density]` 를 ab provenance `exempt_reason: "B 문법에 사진 자리 없음(구조)"` 로 기록하고 규칙 파일은 바꾸지 않는다(판정 ①·③).
- 조건: ① A/B 시트 머리에 한 줄 "B: 사진·카드 자리 없음(틀이 화면을 덮음) — A 와의 차이" 를 코드가 적는다(사용자가 오해 없이 본다). ② A 구간은 본편 콘티 판 v2 와 같은 연출·같은 mix 구간(67.4~90.5초). ③ 산출: `prev_ab/A.mp4`·`B.mp4`·좌우 6컷 시트, provenance ab_compare{sentences, t0, t1, direction_a_sha1, direction_b_sha1, exempt_reason}. ④ 둘 다 그 밖의 검사 hard 0.
- 축 라벨 예약 열(cd314ea)·chart_only 면제(8450dce) 확인. 골든 e2e 결과를 다음 R 에(dark·light 25/25 표).
- 게이트 ② 자료는 사용자 흐름 승인 뒤: `render --preview auto` 두 편 → 프리뷰 시트·A/B 시트·미디어 요약·카탈로그 요소 표(tools/catalog_table.py).
