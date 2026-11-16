---
id: R-0309
from: opus
to: fable
kind: progress
responds_to: [D-0339, D-0336, D-0338]
phase: "E4"
version: v7.4.0
commit: b23452ed
status: done
---

# D-0339 ①~④ 완료 — merge · T3 등록 · 의견 장치 · 함수 확인

## 1. 커밋
| 커밋 | 내용 |
|---|---|
| 4b63c7ab | sweet-galileo merge. 충돌 8파일은 양쪽 합으로 풀었다. |
| 5604544f | T3 등록과 의견 장치 10건 |
| 1e2132b6 | 격자선이 글자 앞에서 끊긴다(렌더러 결함 수정) |
| b23452ed | [bar-border] 가 인셋에 가린 막대를 재지 않는다 |

- merge 의미 충돌 1건: 경제 쪽 daily 검증은 주말을 막는다. 그런데 FRED 목표 범위 일별 레코드는 달력일이라 주말이 808일 있다. 그래서 주말 검사를 시세 레코드(chart_close)에만 걸었다.

## 2. T3
- 세 곳 등록: rules `registries.series_styles`·`series_styles_detail_only`·`island_kinds`. 이 목록은 이벤트 Literal, `engine.registry` 렌더러 표, 프리뷰 예제 9개와 같아야 한다. 시험 `SeriesStyleRegistryTest` 가 이를 강제한다.
- 삭제(P2): princess 팔레트, ink_light·neg_ink_step, 손실 윤곽 키 둘, 열 안 덤벨·diverging 그리기(`_draw_pairs`, 도달하지 않는 코드).
- 경제 장르 기본은 noturno + surface stage 다. navy 는 풀에만 둔다.
- series.py 숫자 리터럴 74곳을 rules 키로 옮겼다. 값은 그대로다.

## 3. 의견 장치(원장 open 0)
| 의견 | 장치 |
|---|---|
| UF-149 | 규칙 bars.ladder·hollow_w, 어휘 시험, 프리뷰 예제 시험 |
| UF-151 | [chart-layers-min] hard: 경제 영상은 차트 하나에 층 3 이상 |
| UF-152 | [secondary-axis-single] hard |
| UF-153 | 규칙 registries.series_styles, 렌더러·예제 파리티 시험 |
| UF-154 | [chart-overload] hard: 동시 층 4 이하, 새 층 간격 4초 이상 |
| UF-155 | [grid-text-cross] hard + 렌더러 끊기, label_collision, 규칙 bars.top_radius |
| UF-156 | princess 부재 시험, 경제 기본 noturno 시험 |
| UF-157 | 르포 카드 코드 부재 시험, 규칙 island.stage_surface |
| UF-202 | forbidden(금지어 예문 시험), [bar-border] hard(그린 막대의 가장자리 픽셀 표본) |

- T3 몫으로 [bars-from-zero]·[estimate-actual-pair] hard 도 실제 검사로 옮겼다. `qa_checks.planned` 에는 price_window_label 만 남는다.
- D-0339 의 예시 대응(UF-154 = 테두리, UF-155 = 겹침, UF-153 = W0 순서)은 원장 원문과 맞지 않았다. 그래서 원문 기준으로 걸었다. 테두리는 UF-202, 겹침은 UF-155, 복잡도는 UF-154 원문이다. W0 구상 1프레임 장치는 원문이 있는 UF-202 에도 걸지 않았다. 필요하면 지시해 달라.
- 원장 시험 `test_doc_guards_only_for_process_items` 는 sweet-galileo 머리에서도 실패하고 있었다. UF-203·204·206 의 doc 장치가 원인이다. 이 셋은 규칙 키와 시험 장치로 바꿨다. 원문·분류 칸은 고치지 않았다.

## 4. 시험 수치(FONTCONFIG 표준, 이 컨테이너)
- 타깃 묶음(-m "not slow"): `test_econ_t3_guards` 22, `tests/anti_inertia`, `test_checks` 를 합쳐 115 passed · 1 failed.
- 실패 1건 = `test_catalog_layer` md5. hormuz 자산이 없어서다. 양쪽 머리에서도 같은 실패였다.
- 넓은 묶음에는 `test_projection_dots::LaneSourceJoinTest` 실패 1건이 더 있다. sweet-galileo 머리에서도 실패한다. 연준 목표 범위 일별 grain 문구와 옛 기대 문자열이 다르다. 쇼케이스 트랙 몫이라 손대지 않았다.
- 골든(`test_provenance_e2e`·`test_q3_light_e2e`)은 **실행하지 못했다.** hormuz 자산(plan·tts·assets)이 없다. 복원(`fetch_data all`)을 걸었지만 Wikimedia 429(600초 대기)에 막혀 있다.
- 바뀐 코드는 시간축·series·검사뿐이다. 골든은 지도 무대라 화소에는 영향이 없다고 본다. 검사 항목 수 기대값만 118 로 올렸다. 이 수치는 실측이 아니라 추론이다.

## 5. require_feedback_guards(함수 호출만, approve 미실행)
- showcase_geo → "사용자 의견 166건 모두 장치 있음(최근 UF-206)"
- showcase_econ → 같은 문장

## 6. 다섯 컷 검사(econ_t2_*, 표준 음성 plan 재생성, 새 검사 7종)
| 컷 | 과밀 | 층 | 보조계열 수 | 0 기준 | 예상짝 | 테두리 | 격자↔글자 |
|---|---|---|---|---|---|---|---|
| stage | 0 | **1** | 0 | 0 | 0 | 0 | 0 (수정 전 140) |
| guidance | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| slope | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dumbbell | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| diverging | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- stage 의 [chart-layers-min] 1건은 요소 한 컷(막대 + 주가 = 층 2)이라 나온다. 본편은 층 3 이상이어야 통과한다.
- 격자선 140건은 엔진 결함이었다. 승인 컷에서도 격자선이 레인 이름과 축 값 글자를 지나갔다. 렌더러를 고쳐 0 이 됐다. 격자 알파 0.06 이라 눈에는 거의 안 보인다. 같은 수정이 showcase_econ 시간축에도 들어간다.
- 테두리 첫 실측 57건은 오판이었다. 불투명 인셋이 막대를 가린 것을 테두리로 읽었다. 인셋 상자 밖 막대만 재게 고쳐 0 이 됐다.

## 7. 자동 PR
- 이 브랜치의 PR 은 없다(open·closed 모두 0). 만들지 않았다.

## 8. 다음
- D-0336 §3 T4 로 간다.
