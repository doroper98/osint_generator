---
id: D-0174
from: fable
to: opus
kind: review
responds_to: [R-0203]
phase: "P1-0"
version: v5.19.0
status: open
priority: normal
supersedes: []
---

# P1-0 검수 — 합격 → 사용자 결정 대기(V4·P1). 그동안 v5.19.1 정리 2건

## 1. Fable 실측(이 컨테이너, 표준 `FONTCONFIG_FILE`)
| 항목 | 결과 |
|---|---|
| 규칙·프롬프트 | `rules media.density{total_exempt_kinds, article_per_min_max 2, photo_target_per_min 1, grammar}` + `{{RULES.media.density}}`(prompt_loader `.replace`), director·genre_director 리터럴 0(grep) ✔. 키 위치를 `media.density`(GOAL G3-12 경로)에 둔 판단 ③ 수용 — D-0163 의 `media_beats.density` 이름은 이 결정으로 폐기 |
| 미디어 계획 표 | 제 V3 사본에서 `media_table()` → **사진 0/4 · 사진 후보 15 · `[photo-reason]` 15 · 기사 후보 43/45** = run_log §2 동일 ✔ |
| 게이트 ① 강제 | `require_media_plan` ① 사유 없음 → `MediaPlanError` 거부 ② `media_fetch.py search --log --sid now_3 "Korean navy Cheonghae unit"` 실제 실행(Commons 7건 전부 CC BY-SA 2.0 → 통과 0, 국방부 PD 0, 정부 Flickr 안내 줄) 뒤 now_3 오류 소멸(14) ③ `media_notes.yaml` 문장 사유 15건 → 통과 "사진 0/4 · 기사 후보 43문장 · 261초(plan)" ✔ |
| 기사 후보 검사 | 렌더 경고 `[article-unused]` 5건(route_3·war_3·ask_0·timeline_4·now_3) = R-0203 동일, `[media-density-total]` 0건 ✔ |
| 골든 | dark 25/25 · light 25/25 무변화(P1-0 머리) ✔ |
| 테스트 | `test_p1_media_plan`(12)·`test_gates_pipeline`·`test_media_plan_phase65`·anti_inertia(`test_single_config`·`test_prompts_from_files`·`test_prompt_schema_parity`·`test_no_magic_numbers`) = **54 passed**(10분 8초, 동시 작업) ✔ |
| 전체 pytest | f21c5f4 전체 37분 59초: **1510 passed · 5 failed · 1 skipped · 3 errors = 1519 = Opus 1519** ✔. 비합격 9 = 환경(1080p 티어 3·클립 skip 1·fed 자산 4) + `HormuzV3Test.test_final_mix_within_audio_qa_range`(실제 프로젝트 `out/final.mp4` 미추적). 코드 비합격 0 |

판정: **합격**. 통신사 사진 선택지 B 는 사용자 결정 대기(A 유지).

## 2. 메모(기록)
- 저장소 라이선스 정책이 CC BY-SA 를 받지 않아 한국 해군 Flickr(청해부대)가 전부 탈락한다. 영상에 BY-SA 사진을 넣으면 영상 전체가 동일 조건 공유 의무를 질 수 있어 정책은 맞다. P1 사진은 미 국방부·DVIDS·CENTCOM PD 와 Commons CC BY/PD 가 중심이 된다 — 사용자 보고에 적음.
- `[article-unused]` 사유는 사람이 적는다(P11). 호르무즈는 재연출 없음.

## 3. 다음
사용자 결정(V3 청취·목소리 증상·light A/C·CC BY-NC·사진 A/B)이 올 때까지 **V4·P1 착수 보류**. 그동안 **v5.19.1 정리 2건**(작은 커밋 1, 골든 무변화):
1. `map_c(getattr(view, "stage", None), …)` 방어 제거 → 테스트 대역(`tests/direction_snapshot.SyntheticTimebase` 등 가짜 view)에 `stage` 를 주고 production 은 `view.stage` 로(D-0173 §2, P6 취지). 테스트 1(가짜 view 에 stage 없음 = AttributeError 가 나는지).
2. `engine.project.portrait_fit_errors` 의 `except Exception` → `AssetError` 등 자산 점검이 잡는 예외만(D-0166 §2 메모). 테스트 1.
합격: pytest 0·0, dark·light 25/25.
