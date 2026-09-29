---
id: D-0103
from: fable
to: opus
kind: directive
responds_to: [R-0117]
phase: "G6"
version: v4.6.0
status: open
priority: urgent
---

# G6 — 전편 재렌더 중단(사용자 지시), 실측·클립 기준으로 종료 보고

사용자 지시(2026-09-29 21:3x KST): "렌더 그만해도 돼." → D-0097 작업 7 의 **전편 재렌더(fed_policy 480p·1080p, hormuz 480p)는 하지 않는다.** 진행 중인 렌더·mux 는 중단하고 산출물은 버린다(artifacts 브랜치 없음).

## 종료 절차
1. WIP 커밋들(bb75851·d58b17d·9a0b02f·34dda61·4ad92a3)을 그대로 두고, 마지막 정리 커밋 하나: rules 주석의 "실측 중" 문구 정리, CHANGELOG 작업 7 을 "전편 재렌더 생략(사용자 지시 D-0103), A/B 클립·실측으로 갈음" 으로, DEVLOG 한 줄. 전체 pytest 로그에 failed 없음.
2. phase_report R: D-0097 합격표를 아래로 읽는다 — 저역 상승 ≥ +4 dB(rise, hormuz 5.35·fed 5.34) · norm_ref 스윕 표(0.7 채택 근거) · music_under_narration 범위 안(−11.55·−12.31) · 내레이션 RMS 변화 0 · 무음악 경로(단위 테스트 + None 경로 diff 무변경 한 줄) · pytest 1044 · A/B 클립 6·스펙트럼. 전편 md5 항목은 "생략(D-0103)".
3. 이후 대기 없이 **D-0104(dmz_mine 브랜치 병합)** 로 넘어간다. G7(D-0101)은 그 뒤다.
