<!--
tier: 2
last_synced_with: v5.0.0
ssot_for: [prompt-genre_script]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
note: 장르 프롬프트 층(v4.4.0, back_and_forth D-0090 작업 1) — prompts/script.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 기본 장르(rules genre_prompt.base_genre)는 쓰지 않는다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 이 영상은 지정학이 아니다 (장르 {{GENRE.name}}, 프로필 {{GENRE.status}})
------------------------------------------------------------------
주 무대는 {{GENRE.stages}} 이다. 지도가 무대가 아니므로 장소 나열이 아니라 시간·수치의 흐름으로 장면을 짠다.
사실·출처·균형·발음 규칙과 금지 문구는 위와 같다. 그 위에 아래를 더한다(20 §7).

서술 규칙
{{GENRE.narration}}
- 피할 표현: {{GENRE.avoid}}. 마지막 문장은 전망 단정이 아니라 "아직 정해지지 않은 것"으로 끝낸다.

데이터 원칙
{{GENRE.data_sources}}
- 데이터 레코드 값을 말하는 문장은 `sources` 에 `series:<id>` 를 적는다(사용자 메시지의 "데이터 레코드" 목록 id 만).
  그 문장 `date` 는 값의 달(YYYY.MM)이고, 자막 수치는 레코드 값 그대로다(코드가 대조한다).
  한 문장에 레코드 둘을 참조하면 숫자를 쓰지 않는다(어느 값인지 구분할 수 없다).
