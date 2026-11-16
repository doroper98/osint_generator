<!--
tier: 2
last_synced_with: v7.4.0
ssot_for: [prompt-genre_map_script]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md]
last_review: 2026-11-02
note: 지도형 장르 프롬프트 층(v7.4.0, 사용자 의견 UF-400) — 주 무대가 mercator 인 비기본 장르(정치사 등)에서 prompts/script.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 지도 문법은 위 본문 그대로 쓴다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 지도 위 장르 {{GENRE.name}} (프로필 {{GENRE.status}})
------------------------------------------------------------------
주 무대는 {{GENRE.stages}} 이다. 사실·출처·균형·발음 규칙과 금지 문구는 위와 같다. 그 위에 아래를 더한다.

서술 규칙
{{GENRE.narration}}
- 피할 표현: {{GENRE.avoid}}. 마무리는 앵커 브리핑처럼 — 확인된 사실과 지금 상태를 단정하는 결론("지켜봐야 하겠습니다" 금지). 미래 전망 단정 금지(v5.6.0 script_grammar).
