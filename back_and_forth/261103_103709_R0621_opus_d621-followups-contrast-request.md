---
id: R-0621
from: opus
to: fable
kind: decision_request
responds_to: [D621]
phase: "B"
version: v7.4.0
commit: 3c038331
status: awaiting_decision
---

# D621 전달 뒤 작업 1~5 — 시험 포함 완료, 글자 대비 검사가 예산안 금색 글자를 잡음(결정 요청 1건)

## 1. 전체 pytest(같은 날 1회)
- 179a1683 기준 결과는 2123 통과, 39 실패, 44 건너뜀입니다(11분 25초).
- 이 트랙 실패는 24건이었습니다. 모두 5eef8953 에서 고쳤습니다.
  - 게이트 시험 고정물이 문장 둘에 하나 '또한' 을 붙였습니다. D-1007·D610 접속어 규칙에 걸려 게이트 ① 이 막혔습니다(gates_pipeline 18, g65_merge 2, rollback 3).
  - test_script_flow 고정 원고의 첫머리 접속어 2/4 를 뺐습니다.
  - test_g13 main_kinds 에 structure 를 넣었습니다. test_q1_cascade 는 boxed= 를 style 로 세지 않게 했습니다.
  - rank 요소 예제(prompts/examples/events/rank.yaml)가 빠져 있어 더했습니다.
- 남은 15건은 환경입니다. hormuz·fed_policy·fed_timeline_demo 자산과 Natural Earth 도로·도시 파일이 이 컨테이너에 없습니다.
- 수리 뒤 해당 묶음과 anti_inertia 를 다시 돌렸습니다. 환경 3건 외 통과입니다.
- 한계: rank 예제의 갤러리 렌더 시험은 hormuz 자산이 없어 여기서 돌지 않았습니다.

## 2. 배경 피사체 검사(D616 ④) — 3c038331
- backdrop 에 `for`(장면 주제)를 더했습니다. 레지스트리 main_subject 와 대조합니다(photo 대조 함수 공용).
- `[backdrop-subject-background]`·`[backdrop-subject-unmatched]` 는 hard 입니다.
- 연출 문법에 한 줄을 넣었습니다. 연출 미디어 목록에는 사진마다 주된 피사체를 보입니다.
- 예산안 배경 6개에 for 를 적었습니다. 실측 결과 0건입니다.

## 3. 글자 대비 측정 검사(D619) — 3c038331
- `[island-text-contrast]` hard 입니다. 렌더와 같은 경로로 바탕을 만듭니다(backdrop_surface → draw_frame boxed).
- 상자 안 밝은 쪽 97 백분위 휘도와 글자색의 WCAG 대비를 잽니다.
- 글자색은 rules `island.text_colors`(white·muted·green·ru·gold)입니다. 하한은 새 수치 없이 `qa_checks.map_contrast_text` 4.5 입니다.
- UF-304 guards 에 더했습니다. 원장은 178건, 미보호 0 입니다.

## 4. 게이트 기록 정직성(④⑤, PIPELINE-AP-027) — b854eef0
- 린트가 StageResult 없이 끝나면 '오류 N' 으로 세지 않습니다. 화면은 실행 실패로 보이고 approve_gate 가 기록을 거부합니다.
- prev/ 가 없으면 cuts·sheet 를 '확인 불가(prev/ 없음)' 로 적습니다.
- media_used 에 backdrop 수와 밀도 검사 값을 함께 적습니다. 예: `real 5 · backdrop 6 · 밀도 검사 11개 · 1.629/분`.
- 시험은 tests/test_gate_record_honesty.py 7건입니다.

## 5. 결정 요청 — 금색 글자 대비
- 예산안 실측에서 11구간 모두 실패합니다. 금색 글자 대비는 3.93~4.15 입니다(기준 4.5).
  - 가장 낮은 곳은 서해안고속도로 배경 3.93, 국회의사당 배경 3.99 입니다.
  - white 15 안팎, muted 7 안팎, green 8 안팎은 넉넉합니다.
- 금색 글자는 총지출 줄 강조 때만 나옵니다. "+12.8%" 와 note 가 금색으로 바뀝니다.
  - 크기는 설계 px 18(초점 큰 숫자)과 13(뒤 작은 줄)입니다.
- 이미 전달한 영상은 막지 않습니다(C12 — 다음 영상 게이트부터).
- 다음 영상 전에 아래 중 하나가 필요합니다.
  - A. 4.5 유지. fiscal 팔레트 accent(gold)를 밝게 하거나, 사진 배경에서 island.fill_alpha 0.78 을 올립니다. fill_alpha 는 사용자 결정 D106·D108 값이라 사용자 질의가 필요합니다.
  - B. 글자 크기별 하한. 큰 글자(설계 px 18 이상)는 WCAG 큰 글자 기준 3.0 입니다. 이때도 13px 금색 note 는 4.5 를 지켜야 해서 note 만 muted 로 둡니다. 새 규칙 키 2개(큰 글자 경계 px·큰 글자 하한)는 감독 승인이 필요합니다.
  - C. 금색 글자 자체를 없앱니다. 총지출 강조는 크기·굵기로만 하고 색은 white 를 씁니다. 연출 변화가 작고 새 수치가 없습니다.
- 추천은 C 입니다. 새 수치와 사용자 값을 건드리지 않습니다. 강조는 크기 변화로 남습니다.
- 검사는 결정 전까지 4.5 그대로 둡니다. 약화하지 않습니다.
