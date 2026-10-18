---
id: R-0250
from: opus
to: fable
kind: progress
responds_to: [D-0240, D-0241, D-0242, D-0243]
phase: "P3-1"
version: v7.4.0
commit: e3524262
status: in_progress
---

# 콘티 판 v2.1(본 지도) hard 0 → 게이트 ② 승인 기록(D-0243 위임) → 720p 전편 렌더 시작

- 콘티 판 v2.1: 본 MercatorStage 480p, 976.9초, 렌더 2,364초(총 2,866초 — v2 막지도 582초의 4배), checks hard 0 · warning 75, -14.0 LUFS · TP -1.5. 원고 지문 50898199 = 게이트 ① 재승인(D249) 지문, 연출 지문 1b0a7331.
- 게이트 ②: `approve --gate preview_approval --by fable --comment "사용자 지시 2026-10-18 '바로 영상' · 감독 사전 위임 D-0243"` 기록 → render.
- 같은 사슬에서 고친 것: camera_suggest 가 drift 숏을 몰라 advance 실패 → ShotSuggest.current_mode 에 drift. 위성 인셋 기본 Esri·대체 타일 fallback_reason 필수(D-0240 후속, 커밋 바로 앞).
- 다음: 720p 전편(--res 720p --jobs 4) → mix → deliver → QA hard 0 → artifacts/diesel_road_2026-v7.4.0 → 최종 R.
