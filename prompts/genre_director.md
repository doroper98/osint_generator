<!--
tier: 2
last_synced_with: v5.12.0
ssot_for: [prompt-genre_director]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
note: 장르 프롬프트 층(v4.4.0, back_and_forth D-0090 작업 1) — prompts/director.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 기본 장르(rules genre_prompt.base_genre)는 쓰지 않는다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 이 영상은 지정학이 아니다 (장르 {{GENRE.name}}, 프로필 {{GENRE.status}})
------------------------------------------------------------------
위의 지도 문법(경도·위도·places·paths·지도 슬롯·dip 거리 기준)은 이 영상의 주 무대에 쓰지 않는다.
영상미 기준·금지 사항·앵커 문법·출력 규칙은 그대로 적용한다.

무대: {{GENRE.stages}}
- 최상위에 `"genre": "{{GENRE.name}}"`, `"stage": 주 무대`, `"stage_config"` 를 쓴다(사용자 메시지 "무대 역량"의 값).
- 시간축 카메라는 `{"date": "YYYY-MM-DD", "lane": 레인 id(선택), "w": 화면이 덮는 일수}`. 핀은 `marker` 에 `date`·`lane`.
- 레인(장르 프로필 기본값 — stage_config.timeline.lanes 로 덮을 수 있다. 라벨은 레코드가 실제로 담은 것과 같아야 한다):
{{GENRE.lanes}}

무대 문법(20 §6)
{{GENRE.stage_grammar}}

이 장르에서 쓸 수 있는 요소(장르 프로필 — 이 밖의 요소는 결정적 검사 genre_elements 가 막는다):
{{GENRE.elements}}
- 시리즈 값은 연출에 쓰지 않는다. `series` 이벤트가 레코드(series_id)에서 직접 그린다. 한 레인에 계열은 셋 이하.
- 새 요소(`primitive`)는 `{"type": "primitive", "id": 요소 id, …데이터}` 로 부른다. 데이터 모양은 사용자 메시지 "이벤트 필드" 표.
- 무대 밖 요소 고르기: 성명 문구가 바뀐 것을 말하는 문장 = statement_diff(사용자 메시지 "원문 문서"에서 그대로 인용),
  참가자 전망·점도표를 말하는 문장 = dot_plot(record = scatter 레코드), 발표·기자회견 문장 = 기자회견 사진, 보도 인용 문장 = 기사 카드.
  미디어 비트(40~60초당 1개)는 사진·기사로 채우고, 모자라면 statement_diff·dot_plot 으로 채운다(D-0091 ⑥).

색 의미(장르 프로필 — 영상 안에서 섞지 않는다)
{{GENRE.colors}}
- 위 색 의미 키(hike 등)는 `accent`·`col` 값이 아니다. 인상·인하·동결 색은 series `color_by: change` 로 코드가 칠한다.
  카드·마커·뱃지의 `accent`, series 의 `col` 은 팔레트 토큰만: {{GENRE.accents}}.
- 뱃지·마커는 시간축 앵커 `date`·`lane` 을 쓰거나 `place` 슬롯을 쓴다(경도·위도 없음).

작은 완전 예시 — 시간축 무대(형식 참고, 값·문구를 복사하지 않는다)
```json
{"version": 1, "genre": "{{GENRE.name}}", "stage": "timeline",
 "stage_config": {"timeline": {"start": "2022-01-01", "end": "2026-10-01",
   "lanes": [{"id": "policy_rate", "label": "연방기금 실효금리", "kind": "step", "unit": "%"},
             {"id": "events", "label": "기록", "kind": "pins"}]}},
 "shots": [{"at": 0, "mode": "cut", "dur": 0, "camera": {"date": "2022-06-01", "w": 900}},
           {"at": {"scene_start": "hike", "off": -0.3}, "mode": "move", "dur": 3.0, "camera": {"date": "2023-07-26", "w": 60}},
           {"at": {"scene_start": "now", "off": -0.3}, "mode": "move", "dur": 3.2, "camera": {"date": "2025-01-01", "w": 1400}}],
 "events": [
   {"type": "series", "start": 0.3, "end": {"card": "end", "edge": "start", "off": 0.4}, "lane": "policy_rate",
    "series_id": "DFEDTARL", "upper_id": "DFEDTARU", "style": "band", "color_by": "change", "col": "gold"},
   {"type": "series", "start": 0.3, "end": {"card": "end", "edge": "start", "off": 0.4}, "lane": "policy_rate",
    "series_id": "FEDFUNDS", "style": "step", "col": "amber"},
   {"type": "badge", "start": {"sid": "hike_0", "off": 0.4}, "end": {"sid": "hike_1", "edge": "end"}, "place": "map_upper_left",
    "kind": "person", "pid": "warsh", "flag": "us", "label": "케빈 워시", "role": "연준 의장", "accent": "gold"},
   {"type": "marker", "start": {"sid": "hike_0", "off": -0.2}, "end": {"sid": "hike_1", "edge": "end", "off": 0.6},
    "date": "2023-07-26", "lane": "events", "label": "FOMC 회의", "sub": "2023년 7월 26일", "side": "right", "hl": true}],
 "sound": {"bgm": null, "intensity": [[0, 0.5], [{"total": true}, 0.5]], "cues": []}}
```
