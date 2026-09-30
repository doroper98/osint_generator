# artifacts/phaseG12-v5.1.0 — G12 산출물 (back_and_forth D-0121·D-0123·D-0124·D-0126)

| 파일 | 내용 |
|---|---|
| `fed_policy_2026/out/final_480p.mp4` | fed_policy 480p 한 편 — backdrop 무대(연준 Flickr 사진 6장 블러) + 차트 아일랜드(left) + 기사 프레스 v2 + 엔딩 카드 버전 도장. 연출 = AI 재연출 v9(검수 루프 2회 상한, checks hard 0). §D 재합성 9문장 반영 |
| `fed_policy_2026/out/{provenance_480p.json,audio_qa.json,final.srt,credits.txt,description.txt}` | 전편 기록 |
| `fed_policy_2026/prev_g12/` | v9 프리뷰(auto 22컷)·checks·frames·provenance·시트 |
| `fed_policy_2026/ai_direction/` | 연출가 v8 → 수정 v9·v10, 검수 판정 v1·v2, 수정 기록, qa_loop(선택 v9), ai_run 로그 |
| `hormuz_korea/hormuz_article_200-230s_480p.mp4` | hormuz 200–230초 30초 클립 — 19_debate_0 Korea Herald 기사 프레스 v2(블러 무대 폴백·번역 헤드라인) |
| `sheets/fed_sheet_before_v5.0.0_timeline.jpg` · `fed_sheet_after_v5.1.0_backdrop_island.jpg` | fed 전/후 |
| `sheets/article_before_after_{hormuz,fed}.jpg` | 기사 전(오른쪽 카드)/후(프레스 v2) |
| `sheets/endcard_before_after_{hormuz,fed}.jpg` | 엔딩 카드 전/후(버전 도장) |

전편 hormuz 렌더 없음(D-0125). 영상 최종 판정은 사용자.

## 후속 D-0127(같은 v5.1.0) — 수정 회차 1회·재렌더

| 파일 | 내용 |
|---|---|
| `fed_policy_2026/followup_d0127/final_480p.mp4` | fed_policy 480p 재렌더(md5 `c833024f…`, 307.66초, I −14.08·TP −1.65, checks hard 0). 연출 = v9 유지(v11 미채택). 검수 예외(press_lead) 반영 트리, 현재 plan·mix(`f4ff0ad2…`) |
| `fed_policy_2026/followup_d0127/{provenance_480p.json,audio_qa.json,final.srt,credits.txt,description.txt}` | 전편 기록(provenance 의 모델 이름 값은 가림 — config.yaml 이 단일 출처) |
| `fed_policy_2026/followup_d0127/ai_direction/` | 재검수 v3(v9) → 수정 v11(`direction.v11.yaml`·`revision.v11.json`) → v11 프리뷰 checks hard 3(`checks.v11.json`·`sheet.v11.jpg`) → v9 복원, qa_loop·ai_run |
| `sheets/fed_v9_vs_v11_d0127.jpg` | v9(왼쪽)·v11(오른쪽) 6컷 — 71.40·108.39·207.20·249.80·268.41·290.40초 |
