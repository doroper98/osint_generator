<!--
tier: 2
last_synced_with: v7.4.0
ssot_for: [prompt-genre_map_research]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md]
last_review: 2026-11-02
note: 지도형 장르 프롬프트 층(v7.4.0, 사용자 의견 UF-400) — 주 무대가 mercator 인 비기본 장르(정치사 등)에서 prompts/research.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 지도 문법은 위 본문 그대로 쓴다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 지도 위 장르 {{GENRE.name}} (프로필 {{GENRE.status}})
------------------------------------------------------------------
위의 사실·출처·균형 원칙은 그대로 적용한다. 이 장르는 정보기관·연구소·정부의 1차 문서(비밀 해제 보고서·사전·회의록)를 근거로 자주 쓴다 —
문서 이름·발행 기관·날짜와 인용할 원문 단락(소스 본문 그대로)을 claim 에 남긴다.

원고가 지킬 서술 규칙(사실 문장 `text` 도 이 규칙대로 쓴다)
{{GENRE.narration}}
- 피할 표현: {{GENRE.avoid}}
