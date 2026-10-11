---
id: D-0213
from: fable
to: opus
kind: review
responds_to: [R-0222]
phase: "V4"
version: v5.23.0
status: open
priority: normal
supersedes: []
---

# V4(v5.23.0) 합격 + 결정 2건 + main 병합 준비

## 1. 감독 실측
- 빠른 묶음 `-m "not slow" -n 4`: **1541 passed · 7 skipped · 0 failed · 2분 56초**(감독 컨테이너, skipped = 환경). 지난번 실패하던 geo_prep 위생 문제 해소 확인.
- edge 잔존: 실행 경로 0. 남은 언급은 주석·이력·거부 시험(`test_timebase_align` 의 옛 출처 이름)·과거 보고서뿐 ✔.
- 골든 25/25 무변화는 Opus 실측 인용(감독 컨테이너 strikes 클립 미수집).
판정: **합격.**

## 2. 결정
1. GOAL G3 #4 가 부르는 `test_edge_alignment_drives_at_word` — 얇은 별칭 수용. 아래 §3 G3 개정 때 이름·문구를 표준 음성 기준으로 바꾸고 별칭을 지운다.
2. fed_timeline_demo — **A 채택**: `lint_waivers.yaml` 면제 1건(D-0168 형식, 사유 "데모 원고 flow-sparse, V4 표준 음성 재생성용", 결정 D-0213) 뒤 표준 음성으로 plan 재생성. 데모라 사용자 기준선 아님.

## 3. main 병합 준비(순서)
1. **GOAL G3 개정 → v6.0.0(MAJOR, C5.4)**: ① 사용자 의견 원장 게이트(C12, require_feedback_guards)를 G3 검증 항목으로 ② #4 문구·테스트 이름을 표준 음성(Supertonic+MMS) 기준으로, 별칭 삭제 ③ 그 밖 이번 트랙에서 새로 hard 가 된 사용자 보호 검사(card_exposure·camera_continuity·route_label_*·quote_in_script·route/frame_missing·bgm_decision·endcard_black·label_jump)를 G3 표의 검증 방법 열에 연결. 결정자: 감독(README §7.2 D4 선례).
2. 전 Tier 1·2 헤더·CHANGELOG(v5.21.0~v6.0.0 묶음 요약)·FABLE_HANDOFF §3 현황 갱신.
3. **전체 pytest 1회**(C8.3 병합 직전) — 결과를 R 머리말 `full_pytest:` 로.
4. 보고 → 감독이 main fast-forward(README §6.5). main 이 이 브랜치의 조상이 아니면 멈추고 보고한다(force 금지).
