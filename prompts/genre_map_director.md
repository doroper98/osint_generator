<!--
tier: 2
last_synced_with: v7.4.0
ssot_for: [prompt-genre_map_director]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md]
last_review: 2026-11-02
note: 지도형 장르 프롬프트 층(v7.4.0, 사용자 의견 UF-400) — 주 무대가 mercator 인 비기본 장르(정치사 등)에서 prompts/director.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 지도 문법은 위 본문 그대로 쓴다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 지도 위 장르 {{GENRE.name}} (프로필 {{GENRE.status}})
------------------------------------------------------------------
위의 지도 문법(경도·위도·places·paths·지도 슬롯·카메라·dip)은 그대로 쓴다. 영상미 기준·금지 사항·앵커 문법·출력 규칙도 그대로다.
최상위에 `"genre": "{{GENRE.name}}"` 를 쓴다. 무대: {{GENRE.stages}}

이 장르에서 쓸 수 있는 요소(장르 프로필 — 이 밖의 요소는 결정적 검사 genre_elements 가 막는다):
{{GENRE.elements}}
- 새 요소(`primitive`)는 `{"type": "primitive", "id": 요소 id, …데이터}` 로 부른다. 데이터 모양은 사용자 메시지 "이벤트 필드" 표.

요소 연출 문법(장르 요소에 있는 것만)
{{GENRE.element_grammar}}

색 의미(장르 프로필 — 영상 안에서 섞지 않는다)
{{GENRE.colors}}
- 위 색 의미 키는 `accent`·`col` 값이 아니다. 카드·마커·뱃지의 `accent` 는 팔레트 토큰만: {{GENRE.accents}}.
