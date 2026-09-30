# artifacts/phaseG13-v5.2.0 — G13 산출물 (back_and_forth D-0129·D-0132·D-0133)

| 파일 | 내용 |
|---|---|
| `fed_policy_2026/out/final_480p.mp4` | fed_policy 480p 한 편(md5 `3173b7b8c29513abd7b9ef2653b334d6`, 307.66초, I −14.06 LUFS·TP −1.78). 연출 = AI v16(연출가 v12 → 수정 v13·v14·v15·v16). checks hard 0, 검수 v2 hard 1·soft 7 |
| `fed_policy_2026/out/{provenance_480p.json,audio_qa.json,final.srt,credits.txt,description.txt}` | 전편 기록. provenance 의 모델 값은 백엔드 이름(`claude`) — config.yaml 이 단일 출처 |
| `fed_policy_2026/prev_g13/` | v16 프리뷰(auto 22컷)·checks·frames·provenance·시트 |
| `fed_policy_2026/ai_direction/` | D-0133 §4 수정 회차 1회: v15 검수 v1(hard 3) → 수정 v16(`revision.v16.json`) → 검수 v2(hard 1), qa_loop(선택 v16), ai_run 로그, checks·시트 v15·v16, direction.meta.json(재구성 — 아래) |
| `sheets/backdrop_sweep_fed.jpg`(+`.json`) | §A 배경 스윕: 43.65·91.83·250초 × (blur 4·dim 0.30 / 6·0.38 규칙 값 / 10·0.45) |
| `sheets/fed_before_after_g12v9_g13v16.jpg` | 전/후 6컷 — 왼쪽 = artifacts/phaseG12-v5.1.0 prev_g12(G12 코드·v9), 오른쪽 = G13 v16. 71.41·108.39·184.50·249.80·276.56·290.41초 |
| `sheets/fed_card_to_article_v9_v16.jpg` | 보도 인용 카드(v9, 현재 코드로 그림) → article(v16) 같은 문장 3개(open_1·hold_2026_6·markets_0) |

- hormuz 는 무변경(mercator) — 골든 25/25 = G12 기준선, 기록은 본 브랜치가 아니라 `overhaul/v2-map-engine` 의 `docs/handoff/reports/phaseG13/hormuz_label_clip.json`.
- `direction.meta.json` 은 추적되지 않는 파일이라 컨테이너 회수로 유실됐다. prompt_sha1 은 v12 기록 커밋 직전(a015a2e1~1) 트리에서 연출가 시스템 프롬프트를 다시 계산한 값이다.
- 슬롯 `backdrop_right_low [594,212,236]` 은 **미합격 값**(사용자 판정 전). 영상 최종 판정은 사용자.
