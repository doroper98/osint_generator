<!--
tier: 2
last_synced_with: v7.4.0
ssot_for: [prompt-genre_map_visual_qa]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md]
last_review: 2026-11-02
note: 지도형 장르 프롬프트 층(v7.4.0, 사용자 의견 UF-400) — 주 무대가 mercator 인 비기본 장르(정치사 등)에서 prompts/visual_qa.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 지도 문법은 위 본문 그대로 쓴다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 지도 위 장르 {{GENRE.name}} (프로필 {{GENRE.status}})
------------------------------------------------------------------
주 무대는 {{GENRE.stages}} 이다. 위 루브릭의 지도 항목은 그대로 적용한다.

색 의미(장르 프로필)
{{GENRE.colors}}

장르 루브릭 추가 {{GENRE.rubric_n}}항목(20 §9) — **항목마다 판정해 `rubric[]` 에 적는다**(빠지면 판정 전체가 거부된다). 이 장르에 해당하지 않는 항목(차트·투자 권유 등)은 ok true, evidence "해당 없음 — 차트 없음" 처럼 적는다.
{{GENRE.rubric}}
- `rubric[]`: `{"item": 번호, "ok": true|false, "evidence": 본 것}`. ok false 인 항목은 issues 에도 같은 근거로 적는다.
