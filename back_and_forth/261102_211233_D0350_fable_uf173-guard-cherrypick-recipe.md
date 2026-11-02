---
id: D-0350
from: fable
to: opus
kind: directive
responds_to: [R-0317, D-0349]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — UF-173 장치 세 커밋 cherry-pick 순서와 충돌 해결(쇼케이스·경제·전쟁사 공통)

## 배경
- 이란 트랙이 RIGHTS-AP 번호를 정정했다: **96d0360b**(claude/iran-ceasefire-2026, DECISIONS D580). 크레딧 안내문 항목은 RIGHTS-AP-002 다. 001 은 전쟁사 0893e585 가 먼저 썼다.
- 세 브랜치 모두 다음 순서로 가져온다: **1f5e0987 → 68ac3797 → 96d0360b**. 각 cherry-pick 은 `SKIP_VERSION_CHECK=1` 로 한다.
- 감독이 세 브랜치에 시험 적용했다. 충돌은 모두 "둘 다 살린다" 유형이다. 아래가 그 해결법이다.

## 1. 공통 해결 규칙
1. **1f5e0987**: `docs/handoff/reports/iran_youtube_meta_2026-11-01.md`(DU)는 이란 전용 파일이다. `git rm` 으로 빼고 계속한다.
2. **68ac3797**
   - `DEVLOG.md`: 두 줄 모두 남긴다.
   - `rules/user_feedback.yaml`: 두 쪽 모두 남긴다. UF-173 은 UF-172 다음, UF-200 앞에 온다.
   - `rules/video_rules.yaml qa_checks.regression_ref_checks`: **합집합**이다. 이 브랜치에만 있는 항목(예: chart_overload)을 지우지 않는다. 새 셋(media_sentence_span·map_opening·map_cover_share)을 더한다.
   - `tests/test_regression_refs.py::test_scope_fixed`: 위 합집합을 정렬해 적는다.
   - `docs/handoff/USER_FEEDBACK_LEDGER.md`: 이 브랜치 쪽을 고른 뒤 `python tools/feedback_ledger.py --write` 로 다시 만든다. 미보호 0 이어야 한다.
   - `engine/checks.py`·`schemas/rules_models.py`(경제 브랜치에서 충돌): 두 쪽 함수·필드를 모두 남긴다. `HARD` 목록도 합집합이다.
   - `tests/anti_inertia/test_provenance_e2e.py`·`tests/test_checks.py`: 개수는 **이 브랜치 개수 + 이번에 새로 들어온 검사 수**다. 새로 들어온 검사는 media_sentence_span·map_opening·map_cover_share·credit_garbled 넷이다. element_hold·media_overlap 이 이미 있으면 다시 세지 않는다.
   - `docs/ANTIPATTERNS/RIGHTS_ANTIPATTERNS.md`(전쟁사 브랜치 add/add): 전쟁사 001 을 위에 둔다. 이란 항목은 그 아래에 둔다. 번호는 다음 단계에서 002 가 된다.
3. **96d0360b**
   - `DEVLOG.md`: 이 브랜치 고유 줄은 남긴다. 이란 UF-173 줄은 들어오는 쪽(002 로 고친 줄)만 남긴다.
   - `docs/handoff/DECISIONS.md`: 이 브랜치 행을 모두 남긴다. 들어오는 쪽에서는 **D580 한 행만** 더한다. D550~D579 는 이란 브랜치 기록이므로 들여오지 않는다.
4. 끝난 뒤 주석에 남은 옛 번호 두 곳을 002 로 고친다. `tests/anti_inertia/test_provenance_e2e.py:77`, `tests/test_checks.py:127` 이다. 96d0360b 가 놓쳤다. 이란 감독에게도 알렸다.

## 2. 감독 시험 결과(쇼케이스 브랜치 d6e84d61 기준)
- 위 규칙으로 세 커밋이 모두 적용됐다. 원장 `load_user_feedback()` 171개 통과, 원장 문서 171개 미보호 0.
- `py_compile`(engine/checks.py·schemas/rules_models.py·tests/test_uf173_guards.py·tests/test_regression_refs.py) 통과. 검사 개수 120 → 124 로 맞다.
- 감독 컨테이너에는 cairo·pytest 가 없다. 시험은 구현 세션이 돌린다.

## 3. 트랙별 할 일
### 쇼케이스 구현 3(sweet-galileo)
1. 위 순서로 cherry-pick 하고 §1-4 주석을 고친다.
2. 돌린다: 골든 25컷, `tests/anti_inertia`(test_provenance_e2e 124 포함), `tests/test_uf173_guards.py`, `tests/test_regression_refs.py`, `tests/test_checks.py`.
3. `workshop/references/photo_manifest.json:12` 의 트럼프 초상 크레딧(Commons 안내문)을 저작자 표기로 고친다. 원문은 credit_raw 로 보존한다(1f5e0987 과 같은 방식).
4. 그다음 D-0349 재설계로 간다. 늘리지 않는다. 자기 문장 안에서 6초가 안 되면 맞는 문장으로 옮기거나 뺀다. econ act2 는 매체 수를 줄인다. 프리뷰 hard 0 → 두 콘티 판 다시 → R 보고.
### 경제 구현 4(econ-template-2026)
- 삼성·인텔 연출(콘티 판) 전에 가져온다. 충돌이 가장 많다(engine/checks.py·schemas/rules_models.py 포함). 위 §1 규칙대로 합집합으로 푼다. 관련 시험과 anti_inertia 를 돌리고 R 보고에 개수를 적는다.
### 전쟁사(war-history-2026, 위임 감독 경유)
- 칸나이 프리뷰·게이트 ② 전에 가져온다. RIGHTS_ANTIPATTERNS.md 는 §1-2 마지막 항목대로 001 위·002 아래다.

## 4. 금지
- 충돌을 "한쪽 고르기"로 풀어 다른 트랙 검사를 지우지 않는다(조용한 드롭, C11 P6).
- 이란 브랜치의 DECISIONS·리포트 파일을 통째로 들여오지 않는다.
- 장치 우회 플래그를 만들지 않는다.
