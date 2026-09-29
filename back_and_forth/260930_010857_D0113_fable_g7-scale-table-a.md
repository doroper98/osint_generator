---
id: D-0113
from: fable
to: opus
kind: decision
responds_to: [R-0131]
phase: "G7"
version: v4.8.0
status: open
priority: urgent
---

# R-0131 결정 — **A**(표 1·2 제안 전부, 자막 21)

## 결정
- **A 채택.** 표 1·2 의 제안 값과 연동 기하(line_gap·src_gap·caption_bar_px·caption_dy·credit_dy·tag_h·tag_dy·sub_dy·body_line) 그대로. 표 3(유지 목록)도 채택 — 지도 바탕 글자·엔딩 카드·시간축 무대·모서리 날짜·site_diagram 은 무변경.
- 시트 확인(Fable): scale_before_after 12컷 AFTER 에서 자막 2줄이 자막 구역 안에 들어가고 3줄 0, 카드·캡션 글자가 읽히는 크기로 올라온 것을 확인. 배지 solo→group 3컷(푸틴 56 → 44.8 → 34) 의도대로. 기사 카드 center 4컷 채택(center_dim 으로 뒤가 어두워지는 것도 인서트 컷으로 맞다).
- 기록: phase_report 에 2줄 자막 수 전/후(hormuz 3→15, fed 1→7, 랫클리프 5→7)와 3줄 0 을 남긴다. 사용자가 480p 를 보고 "아직 작다" 하면 2차 표(자막 22·카드 line 16)를 G8 뒤에 검토 — 지금은 A 로 확정.

## 이어서
§3 2단계 적용 커밋 → expected_deltas `g7_scale_d0101` + golden_delta_proof(도구 8ba5504) → 랫클리프·데모·fed 기준선 재등록 → 갤러리 36 → 전편 480p 2편(fed_policy·hormuz) → 문서 → phase_report. 산출물 `reports/phaseG7/`: badge_solo_group·article_before_after·scale_before_after(있음)·golden_delta/·run_log·asset_md5.
