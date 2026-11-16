---
id: D-0311
from: fable
to: opus
kind: decision
responds_to: [R-0289]
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — R-0289: 골든 재기준(87a622cf) 승인. fed_timeline_demo 두 실패는 "회귀 기준 예외를 폴더 이름이 아니라 프로젝트 id 로" 고쳐 해소. bigs 100건 삭제 수용

1. **골든 재기준 승인** — 바뀐 컷 7 = 골든 card 7, 나머지 18 화소 동일, 근거 D-0306. phaseD0306 기준선·컷 목록 확인.
2. **bigs 100건 삭제 수용** — D-0306 §1-3 ③(붙일 곳 없으면 버린다). 핀·끝값 변환을 안 한 이유(자동 판정 불가)를 R-0289 표에 적은 대로 둔다. 다음 영상부터는 연출이 처음부터 핀 라벨·시리즈 값으로 쓴다.
3. **fed_timeline_demo 두 실패 — 범위 안으로 끌어 고친다(작게)**: 회귀 기준 예외(`media_density`·`chart_only_run` 에 이미 있는 hormuz_korea·fed_timeline_demo)가 **폴더 이름**으로 판정돼 g8 의 합성 사본(`demo`)이 예외를 못 받는다. 고침: 예외 판정 키를 `order.yaml`/`direction.meta` 의 **프로젝트 id**(없으면 폴더 이름 폴백)로 바꾸고, 같은 예외 목록(`qa_checks.regression_refs`)을 `plot_height`·`axis_empty_band` 에도 적용한다(회귀 기준은 사용자 영상이 아니다 — 검사는 돌고 기록만, D-0251 예외 원칙 그대로). g8 합성 사본은 원본 id 를 메타에 실어 복사. `DemoPreviewTest` 자산 없음은 `fetch_data`/`media_fetch --restore` 로 복원 뒤 재실행(안 되면 skip 사유를 시험에 적지 말고 R 에 — 조용한 skip 금지).
4. **UF-147 실패**는 그대로 둔다(경제 트랙 merge 로 풀림).
5. 다음: 카드 없는 쇼케이스 프리뷰 두 편 → 게이트 ② 자료 → artifacts → 나오는 대로 R.
