<!--
tier: 2
last_synced_with: v5.17.0
ssot_for: [prompt-genre_revise_direction]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
note: 장르 프롬프트 층(v4.4.0, back_and_forth D-0090 작업 1) — prompts/revise_direction.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 기본 장르(rules genre_prompt.base_genre)는 쓰지 않는다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 이 영상은 지정학이 아니다 (장르 {{GENRE.name}}, 프로필 {{GENRE.status}})
------------------------------------------------------------------
위의 지도 문법(경도·위도·지도 슬롯·dip 거리 기준)은 이 영상의 주 무대에 쓰지 않는다. 고칠 때도 무대는 {{GENRE.stages}} 이다.
`genre`·`stage`·`stage_config` 는 지적이 없으면 그대로 둔다.

무대 문법(20 §6)
{{GENRE.stage_grammar}}

색 의미(장르 프로필)
{{GENRE.colors}}
