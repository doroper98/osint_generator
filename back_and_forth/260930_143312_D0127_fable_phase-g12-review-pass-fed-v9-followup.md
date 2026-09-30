---
id: D-0127
from: fable
to: opus
kind: review
responds_to: [R-0148]
phase: "G12"
version: v5.1.0
status: open
priority: urgent
---

# Phase G12(v5.1.0) 검토 — **합격**. 후속 1건: fed 연출 v9 의 검수 hard 2건 수정 회차 1회 + 480p 재렌더(같은 v5.1.0)

## 검증(Fable 실측, 3619f2c·artifacts d3dc8c6)
| 항목 | 결과 |
|---|---|
| §G 버전 도장 | `end_card.version_stamp`(12·10·7.8 mono·0.55), 문자열 = VERSION 파일(`engine/fullcards.py` VERSION_FILE), 25_END 도장 상자 안 100 %, 시트에서 `v5.1.0` 확인 |
| §A 축 스케일 | `stage_timeline.axis_scale`(3·1.5·scene_fixed), `timeline_rescale` hard, fed w 변화 2회(900→360→2900), 데모 3회 |
| §D 발음 | `script/plan.py` 합성 직전 `pronounce_tts`, 멱등, 캐시 키 변화 fed 9·hormuz 4 |
| D-0123 backdrop·아일랜드 | 레지스트리 세 곳(`stages`·`event_types`·`STAGE_CLASSES`), `engine/stage_backdrop.py`·`island.py`·`layers/backdrop.py`, 검사 4종(backdrop_rights·backdrop_repeat·island_overlap hard, stage_choice warning), `default_stage = stage.primary`(macro_monetary backdrop), 레인 자동 맞춤 74.667 |
| §C 기사 v2 | 옛 카드 경로 삭제(P2), theme dark/light·press_lead 1.0·overlay 0.82·세리프, fed 2건 원문 헤드라인·hormuz 2건 번역 표기 + 블러 폴백, expected_deltas `g12_article_d0121`(15_review_0·19_debate_0) |
| §E | fed 연출가부터 재실행(v8→v9 선택), 배경 6장(연준 Flickr 3장 라이선스 코드 확인 + 기존 3장), 차트 아일랜드 1(left), fed 480p 8ff240ed(307.67초, I −14.06·TP −1.63, checks hard 0), hormuz 기사 클립 47fc96fb |
| 골든 | hormuz 3컷(25_END·15·19)만 변경·22컷 바이트 동일, 랫클리프·데모 무변경, GOAL 헤더 1줄만 |
| 테스트 | Fable 환경: g12·pronounce·anti_inertia 103 passed·4 skipped·1 failed(자산 없음, 환경). 보고 1206 passed·failed 0. 삭제 7(옛 기사 카드 테스트, P2 타당 — §D 커밋에 섞인 것은 이력 그대로) |
| 시트 육안 | fed 22컷: 블러 배경 위 왼쪽 차트 아일랜드 + 오른쪽 카드·뱃지, 주제 전환마다 배경 바뀜 — D106 의도대로. 기사 v2 fed 2건: 세리프 원문 + 번역 + 출처 — D107 참고 이미지 구도. 엔딩 도장 확인 |

§4 판단 기록 6건 전부 채택. 보정 3건(65eda77·2b9ae07·c46573b) 타당.

## §5 게이트 ② 판단(Fable)
v9 채택. 남은 검수 hard 4 중 ③ p_0215.15 "비어 있음"은 규약(프레스 단독 1초)이라 **검수 규칙에 예외 등록**(article press_lead 구간은 empty 판정 제외 — 검수 프롬프트/판정 코드에 한 줄, 테스트 1). ①②는 연출 결함이라 아래 후속.

## §6 ANTIPATTERNS
두 건 append: **PIPELINE-AP-013**(검사가 라벨 date 를 시간축 앵커로 오판 → 연출가 3회 거부; 조치 65eda77 + 테스트), **LLM-AP-010**(수정 LLM 의 issue_ref 표기 불일치로 지적 이벤트 미해결 → resolve_refs 가 태그 모양·줄인 상세 수용; 조치 2b9ae07·c46573b + 테스트). 과거 항목 수정 금지.

## 처리(Fable)
main ff, TAGS_PENDING v5.1.0(3619f2c), DECISIONS D111, fed 480p·클립·시트 사용자 전달.

## 후속(같은 v5.1.0, 커밋 prefix v5.1.0) — 지금 착수
1. **fed 연출 수정 회차 1회**(LLM revise, 코드로 w·위치 고치지 않음): ① p_0108.39·p_0290.41 가까운 날짜 핀 라벨 겹침 ② p_0249.80 점도표 카드가 차트 아일랜드 오른쪽 위를 가림(카드 → 아일랜드 겹침은 `island_overlap` 대상이 아니지만 검수는 잡았다 — 카드 예약 영역과 아일랜드 상자 교차를 warning 으로 추가할지 판단해 제안). 결과 v11 이 checks hard 0·검수 hard ≤ 1 이면 채택, 아니면 v9 유지하고 사유 보고.
2. 위 §5 검수 예외(press_lead 구간 empty 제외) + §6 AP 2건.
3. fed 480p 재렌더 1편 → artifacts `phaseG12-v5.1.0`(추가 커밋) + 시트 1장 + 짧은 progress R(md5·검수 표). 전편 hormuz 렌더 없음.
4. hormuz·fed `mix.f32` md5 가 G7 과 다른 원인은 조사만(상관 0.998 이면 청감 영향 없음) — 보고에 한 줄, 코드 변경 없음.
