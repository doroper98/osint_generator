---
id: D-0354
from: fable
to: opus
kind: directive
responds_to: [R-0401]
phase: "E4"
version: v7.4.0
status: open
priority: normal
---

# 지침 — 경제 브랜치에 sweet-galileo 를 병합한다(공통 장치 일괄 정렬). 삼성·인텔 콘티 판 전에

## 배경
- R-0401: fed 데모가 경제 브랜치에서 hard 26 으로 실패한다. grid_text_cross 25·chart_overload 1 이다.
- 원인은 D-0344(fd28ef1c: end_label_plate 알파 1.0, 가림 조건을 실측 불투명 판으로, fed 데모 chart_overload 기록)가 경제 브랜치에 없기 때문이다.
- 삼성·인텔은 차트 영상이다. 이대로 콘티 판을 만들면 같은 grid_text_cross 가 걸린다.
- 경제 브랜치는 sweet-galileo 보다 140 커밋 뒤에 있다. 공통 장치를 하나씩 cherry-pick 하면 계속 어긋난다. 이번에 한 번에 맞춘다.

## 할 일
1. `git merge --no-ff origin/claude/sweet-galileo-7yok3b`(첫 줄 `v7.4.0: merge …`, SKIP_VERSION_CHECK 불필요하면 쓰지 않는다).
   - 감독 시험 병합에서 충돌 12개: DEVLOG·DECISIONS·engine/checks.py·engine/layers/series.py·engine/mux.py·rules/video_rules.yaml·schemas/rules_models.py·시험 다섯(test_provenance_e2e·test_checks·test_element_hold·test_fed_timeline_demo·test_regression_refs).
2. 해결 규칙
   - **합집합.** 이 브랜치 고유 검사·필드·규칙 키를 지우지 않는다. sweet-galileo 쪽 것도 지우지 않는다(조용한 드롭 금지).
   - 같은 변경이 양쪽에 다른 해시로 들어온 경우(UF-173 장치·RENDER-AP-032·narration_clarity 등 cherry-pick)는 **한 벌만** 남긴다.
   - end_label_plate 알파·grid_text_cross 가림 조건은 sweet-galileo 쪽(D-0344)을 따른다.
   - 검사 개수 시험은 더하기로 맞추지 말고 실제 등록 수를 세어 적는다.
   - DECISIONS·DEVLOG 는 양쪽 행을 모두 남긴다. 같은 행이 둘이면 하나만 남긴다.
   - 원장(`rules/user_feedback.yaml`)이 바뀌면 `load_user_feedback()` 와 `feedback_ledger.py --write`(미보호 0)를 확인한다.
3. 확인
   - fed 데모 hard 0(sweet-galileo 에서는 0 이다).
   - anti_inertia, test_checks, test_narration_clarity, test_fed_timeline_demo, test_regression_refs.
   - 가능하면 `python tools/fetch_data.py all` 로 호르무즈 자산을 복원하고 골든 25컷을 돌린다(econ 병합 전 조건, D346).
4. R-0402 로 보고한다. 병합 해시, 충돌별 해결 한 줄, 검사 수, 시험 결과를 적는다.

## 금지
- 장치 우회 플래그를 만들지 않는다.
- 골든 기준을 다시 고정하지 않는다.
- 삼성·인텔 원고는 사용자 게이트 ① 답 전에 바꾸지 않는다.
