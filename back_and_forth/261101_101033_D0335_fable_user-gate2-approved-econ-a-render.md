---
id: D-0335
from: user
to: opus
kind: decision
responds_to: [R-0295]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정(사용자) — 쇼케이스 게이트 ② 승인 + showcase_econ A. 전편 렌더 시작

- 사용자 원문(2026-11-01, UF-206): **"1~4까지 승인."** — 감독 보고의 1번 = "쇼케이스 게이트 ② 승인과 showcase_econ A/B 선택(감독 추천 A)". 승인 = 게이트 ② 통과 + A(사진 배경 + 아일랜드). 사용자가 B 를 따로 말하지 않았다. B 를 말하면 그때 바꾼다(UF-204 선례).
- 대상: artifacts/showcase-v7.4.0 47427cc(gate2_nocard v5) 의 showcase_geo·showcase_econ 프리뷰·카탈로그(hard 0, 골든 12, 검사 109 — R-0295).

## 실행
1. showcase_geo·showcase_econ 각각 `approve --gate preview_approval` — 승인 기록에 사용자 원문 "1~4까지 승인."(UF-206) 과 econ = A 를 적는다. 콘티 판 기록(animatic_provenance)·`require_feedback_guards` 는 그대로 통과해야 한다(우회 플래그 없음). 막히면 R(decision_request) — 장치를 끄지 않는다.
2. 전편 렌더: geo → econ → `showcase_concat` 결합본. 720p 전달판 30 MB 이하 규칙 그대로(카탈로그 전달판 선례 760k 2패스).
3. 산출물 artifacts/showcase-v7.4.0 에 `final/`: final_deliver.mp4(geo·econ·concat)·srt·description·credits·provenance·MD5SUMS·카탈로그. R 한 장(렌더 시간·hard 0·md5·골든 결과) — 보고 주소 = 최종 감독 session_017Yuw8jLMWscY9bdVXTvddr.
4. 렌더 중 규칙·엔진 편집 없음. 중간 샘플(첫 60초 전편 컷 등)이 나오면 R 에 경로만 — 사용자 전달은 감독이 한다(UF-144).
