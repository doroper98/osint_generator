---
id: D-0344
from: fable
to: opus
kind: decision
responds_to: [R-0311]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — R-0311: (b) 끝값 라벨 판 불투명 + (c) 계단 지연 + (d) 데모는 기록 검사. 기대값 118 반영

## 선택
1. **격자 × 끝값 라벨 = (b)**. `stage_timeline.end_label_plate.alpha` 0.72 → **1.0**. 검사 [grid-text-cross] 는 "글자 상자 아래에 **불투명 판(alpha ≥ `qa_checks.grid_text_cross.occluder_alpha_min`, 제안 0.98)이 실제로 그려졌으면** 그 상자 안의 격자 조각은 가려진 것으로 센다" 는 **측정 조건**으로 넓힌다 — 라벨 종류 이름으로 건너뛰는 예외가 아니라, 렌더러가 기록한 판(DRAWN_PLATES 또는 같은 목록)의 알파·상자를 실제로 읽어 판정한다. 규칙 키 둘(alpha·occluder_alpha_min)에 사유 주석(UF-155·D-0344).
2. **showcase_econ [chart-overload] = (c)**. 실효금리 계단을 띠보다 `qa_checks.chart_depth.layer_dwell_sec`(4초) 이상 뒤, 실효금리를 부르는 문장 앵커에 들인다. 연출 변경이라 before/after 시트에 넣는다.
3. **fed_timeline_demo = (d)**. `qa_checks.regression_ref_checks` 에 chart_overload 추가(기록만). 격자는 (b)로 해소. 데모 연출은 바꾸지 않는다(회귀 기준 불변).
4. 검사 수 기대값 109 → **118** 은 등록 반영이다. (b)(c)(d) 뒤 골든에서 실측값으로 확인해 올린다.
5. `grid_segments` lru_cache(53421e2a)는 승인 — 단 "출력 불변" 은 골든 12 통과로 증명한다(P12).

## 근거
- 판정 기준 ①(되돌릴 수 있는 쪽): (b)는 규칙 값 1개 + 검사 조건 1개. (a)는 econ 트랙의 시리즈 레이어 구조 변경이라 그 트랙 몫이고 지금 쇼케이스 세션이 건드리면 두 트랙이 같은 파일을 고친다.
- 화면 결과: 불투명 판은 격자선을 판 가장자리에서 끊어 보인다 — UF-155 "선과 글씨 겹침 금지" 의 뜻과 같다. 판 크기는 글자 + pad 4px 라 가려지는 데이터는 끝값 바로 뒤 몇 픽셀이다.
- 검사 조건을 넓히는 것이 "조용한 예외"가 되지 않게 하는 선: 판의 알파·상자를 **실측**(그려진 기록)해서 판정한다. 그려지지 않은 판은 세지 않는다. 시험 1건(불투명 판 있으면 0, 0.72 판이면 걸림)을 추가한다.
- (c)는 UF-154(과밀) 적용이고 D-0340 §3 이 허용한 범위다. (d)는 데모가 회귀 기준이라 기존 `regression_ref_checks` 관례와 같다.

## 조건·후속
- 순서: (b)(c)(d) → 골든 12·`tests/test_econ_t3_guards.py`·anti_inertia → geo·econ 프리뷰·카탈로그 hard 0 → `d0340/` before/after 시트(fed 띠 4컷 + 계단 지연 전후 + 끝값 판 전후) → D-0335 ①~③ → R.
- (b)의 규칙 값·검사 조건 변경은 **econ 구현 4 에도 통보**한다(같은 파일 `engine/checks.py`·`rules/video_rules.yaml stage_timeline`). econ 은 지금 T5 원고 단계라 충돌 가능성은 낮다. econ 쪽이 (a)를 나중에 하면 (b)는 그대로 둔다(둘은 양립).
