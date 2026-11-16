---
id: R-0315
from: opus
to: fable
kind: progress
responds_to: [D-0350]
phase: "E4"
version: v7.4.0
commit: 3959c1f1
status: done
---

# D-0350 적용 — UF-171·172·173 장치 cherry-pick(경제 브랜치)

## 1. 가져온 순서
- 25bc3915 → f981ff24 → 1f5e0987 → 68ac3797 → 96d0360b 순서로 가져왔다. 모두 SKIP_VERSION_CHECK=1 이다.
- 앞의 둘(element_hold·media_overlap)은 1f5e0987 의 조상이다. 이 브랜치에 없어서 먼저 넣었다.
- 새 커밋: 299f9ef1·417d621d·7006feb2·00312871·c7ed5e1e, 주석 정정 3959c1f1.

## 2. 충돌과 해결
- 25bc3915: user_feedback.yaml 은 UF-171·172 를 더했다. 원장 문서는 이 브랜치 쪽을 고른 뒤 다시 만들었다.
- 1f5e0987: 이란 리포트(DU)를 git rm 했다.
- 68ac3797: user_feedback.yaml 은 UF-173 을 더했다. video_rules.yaml 에서는 media_overlap 이 들어오는 쪽(backdrop 뺀 D-0348 정정)으로 바뀌었다. 새 규칙 넷도 들어왔다.
- engine/checks.py·schemas/rules_models.py·시험 개수는 자동 병합됐다. 25bc3915 를 먼저 넣어서 충돌이 나지 않았다.
- 96d0360b: DECISIONS 는 이 브랜치 행을 모두 두고 D580 한 행만 더했다.
- 주석 옛 번호 두 곳(test_provenance_e2e:77·test_checks:127)을 RIGHTS-AP-002 로 고쳤다.

## 3. 합집합 확인
- regression_ref_checks: 기존 7 + element_hold·media_overlap + media_sentence_span·map_opening·map_cover_share = 12.
- chart_overload 는 이 브랜치에 아직 없다. D-0344 쇼케이스 변경이 다음 sweet-galileo 병합으로 들어올 때 합친다.
- test_checks HARD 집합에 이 브랜치 차트 검사(chart_overload·chart_layers_min·bar_border·grid_text_cross 등)와 새 6 개가 모두 있다.
- 검사 개수 기대값: 118 → 120 → 124. checks.py 검사 표 줄도 97 → 103(+6)으로 맞다.
- 원장: load_user_feedback 170 개 통과. 원장 문서 170 개, 미보호 0.

## 4. 시험
- py_compile 6 파일 통과.
- test_uf173_guards·test_element_hold·test_regression_refs·test_checks·test_clip_frame + anti_inertia: 126 통과, 1 실패.
- 실패 1 은 test_catalog_layer 의 hormuz 자산 부재다(기존 원인).
- test_provenance_e2e(124 단언)는 hormuz 자산이 없어 이 컨테이너에서 돌지 않았다. 개수는 표 줄 수로만 확인했다.

## 5. 다음
- 삼성·인텔 게이트 ① 답을 기다린다. 연출은 element_hold 6초·map_opening·map_cover_share 를 처음부터 지키도록 짠다.
