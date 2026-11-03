<!--
tier: 2
last_synced_with: v7.4.0
ssot_for: [prompt-genre_map_revise_direction]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md]
last_review: 2026-11-02
note: 지도형 장르 프롬프트 층(v7.4.0, 사용자 의견 UF-400) — 주 무대가 mercator 인 비기본 장르(정치사 등)에서 prompts/revise_direction.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 지도 문법은 위 본문 그대로 쓴다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 지도 위 장르 {{GENRE.name}} (프로필 {{GENRE.status}})
------------------------------------------------------------------
위의 지도 문법은 그대로 쓴다. 고칠 때도 무대는 {{GENRE.stages}} 이고 `genre` 는 지적이 없으면 그대로 둔다.

이 장르에서 자주 쓰는 요소(추천 — 등록 요소는 모두 쓸 수 있다): {{GENRE.elements}}

색 의미(장르 프로필)
{{GENRE.colors}}
