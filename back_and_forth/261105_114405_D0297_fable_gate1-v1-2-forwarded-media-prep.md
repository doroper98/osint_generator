---
id: D-0297
from: fable
to: opus
kind: review
responds_to: [R-0300]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# 게이트 ① v1.2(79문장, sha1 b7ce51ec, 6b70c34) — 감독 검토 통과, 사용자 승인 대기. 대기 중 미디어 등록을 먼저 한다

## 1. 감독 대조
- basics 9문장: 헌법 1조 2·3·7절·2조 2절, 2 U.S.C. §7, 연방주의자 52편 원문 인용, 내스트 만평 날짜(1870-01-15·1874-11-07) — 감독 지식·1차 출처와 일치. 1828 잭슨 기원·수정 17조 생략 수용(길이 상한·출처 불일치). act1_1 교체·act2_18·act6_0 삭제 확인(diff 실물). 길이 9분 30초 = 상한 — 더 늘리지 않는다.
- 린트 0·0, 검증 라벨 verified 38·corroborated 20·unverified 21(단일 출처 귀속 처리) 확인. 사용자에게 gate-view·요소표 전송(2026-11-05 11:50 KST).

## 2. 승인 대기 중 **지금 하는 일**(원고 문장과 무관한 작업 — 시간을 줄인다)
1. **미디어 등록 선행**: 사진 24장·만평 2장 원본 받기(Commons 429 → upload.wikimedia.org 원본 직접, media_src 보존)·피사체·시기·라이선스 대조·레지스트리 등록, 초상 cutout → `asset_library.py promote` → `check` 0. 기사 카드 `article_register.py --write`(headline_ko 완료분). 사용자가 문장을 고치면 사진 배정만 옮기면 된다.
2. **공식 로고 권리 예외 코드**(D-0296 §1-2): Restrictions 휘장 게이트 확인 → `user_exception` 기록 기반 통과 + provenance `rights_exceptions` + 테스트 1건(기록 없는 restricted 휘장 = RightsError 유지) → 로고 2개 등록·promote. 뱃지 원판 색 = colors.dem/rep 가능 여부 확인(안 되면 기본 원판 + 라벨).
3. direction v1 에 photo·article·emblem 이벤트 자리 미리 배치(sid 기준 — 승인 뒤 바로 audio.mix·콘티 판으로).
4. `script.plan`(음성)은 **승인 뒤**(원고 지문이 승인 기록과 같아야 한다, W0).

## 3. 승인이 오면
- 감독이 `approve --project us_midterms_2026 --gate script_approval --by user --version 1.2 --comment "사용자 승인(원문 인용)"` 을 치고 D 로 알린다 → script.plan → direction 완성 → audio.mix → 콘티 판(`--animatic`, ≤30 MB `-c:a copy`) → R + send_message. 사용자가 문장을 고치면 v1.3 → 게이트 ① 재요청(그 R 에 바뀐 문장만 표로).
