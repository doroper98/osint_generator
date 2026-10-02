<!--
tier: 2
last_synced_with: v5.3.0
ssot_for: [prompt-genre_visual_qa]
depends_on: [rules/video_rules.yaml, genres/load.py, workers/prompt_loader.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
note: 장르 프롬프트 층(v4.4.0, back_and_forth D-0090 작업 1) — prompts/visual_qa.md 끝 {{GENRE_BLOCK}} 자리에 들어간다. 기본 장르(rules genre_prompt.base_genre)는 쓰지 않는다. 이 주석은 로더가 떼어 낸다.
-->
장르 규칙 — 이 영상은 지정학이 아니다 (장르 {{GENRE.name}}, 프로필 {{GENRE.status}})
------------------------------------------------------------------
주 무대는 {{GENRE.stages}} 이다. 위 루브릭의 지도 항목(도시·국가 채움·대륙붕)은 무대에 맞게 읽는다(시간축이면 눈금·레인·핀).

무대 문법(20 §6 — 카메라 판정 기준)
{{GENRE.stage_grammar}}

색 의미(장르 프로필)
{{GENRE.colors}}

장르 루브릭 추가 {{GENRE.rubric_n}}항목(20 §9) — **항목마다 판정해 `rubric[]` 에 적는다**(빠지면 판정 전체가 거부된다)
{{GENRE.rubric}}
- `rubric[]`: `{"item": 번호, "ok": true|false, "evidence": 본 것}`. 1번은 슬라이드처럼 보이면 ok false.
  ok false 인 항목은 issues 에도 같은 근거로 적는다(category: honesty·wording 또는 위 목록).

예시 (형식 참고)
```json
{"schema_version": 1, "verdict": "revise",
 "issues": [{"frame": "p_0042.10", "severity": "hard", "category": "honesty",
             "evidence": "금리 레인에 단위 표시가 보이지 않고 출처 줄이 자막에 가려 읽히지 않는다",
             "fix": {"event_ref": "series:FEDFUNDS", "suggest": "자막과 겹치지 않는 레인으로 옮긴다"}}],
 "praise": ["핀 확대에서 일 단위 눈금이 나와 시점이 분명하다"],
 "rubric": [{"item": 1, "ok": true, "evidence": "12컷 모두 같은 시간축 위에서 카메라만 움직인다"},
            {"item": 2, "ok": true, "evidence": "왼쪽에서 오른쪽으로 이어지는 이동, 새 캔버스 없음"},
            {"item": 3, "ok": false, "evidence": "p_0042.10 출처 줄이 자막에 가려진다"},
            {"item": 4, "ok": true, "evidence": "자막 3.63% 와 레인 끝점 값 3.63% 가 같다"},
            {"item": 5, "ok": true, "evidence": "인하 핀이 차가운 색으로 프로필과 같다"},
            {"item": 6, "ok": true, "evidence": "점도표를 처음 말할 때 한 문장 정의 자막이 있다"},
            {"item": 7, "ok": true, "evidence": "매수·매도 권유로 읽히는 문장이 없다"}]}
```
