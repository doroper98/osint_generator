<!--
tier: 2
last_synced_with: v4.7.0
ssot_for: [prompt-genre_research]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
note: 장르 프롬프트 층(v4.4.0, back_and_forth D-0090 작업 1) — prompts/research.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 기본 장르(rules genre_prompt.base_genre)는 쓰지 않는다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 이 영상은 지정학이 아니다 (장르 {{GENRE.name}}, 프로필 {{GENRE.status}})
------------------------------------------------------------------
위의 "지정학" 표현은 이 영상에는 해당하지 않는다. 사실·출처·균형 원칙은 그대로 적용한다.

데이터 원칙(20 §5.1)
{{GENRE.data_sources}}

원고가 지킬 서술 규칙(사실 문장 `text` 도 이 규칙대로 쓴다)
{{GENRE.narration}}
- 피할 표현: {{GENRE.avoid}}
