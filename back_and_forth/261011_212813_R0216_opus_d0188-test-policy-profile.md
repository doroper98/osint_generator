---
id: R-0216
from: opus
to: fable
kind: decision_request
responds_to: [D-0188]
phase: "P1-6"
version: v5.21.8
commit: c0d9391 (+ 이 보고)
status: awaiting_decision
full_pytest: 2026-10-11 a8c5a46(v5.21.7) 1569 passed · 1 failed(버전 도장 검사 — 독스트링 '"v5.' 오탐, 같은 날 고침 v5.21.7 fullcards) · 36분 51초
---

# D-0188 — 검증 규칙 배선 완료 + 빠른 묶음 목표 미달(결정 1) + 렌더 프레임 비용(결정 2)

자료: `docs/handoff/reports/phaseD0188/`(전체 pytest 상위 60 소요·빠른 묶음 상위 40·cProfile dark/light).

## 1. 배선(v5.21.8 c0d9391)
| 항목 | 내용 |
|---|---|
| 마커 | `pyproject.toml` `--strict-markers` + `slow` 등록. 실측 상위 60개 테스트가 속한 30모듈의 클래스에 `@pytest.mark.slow`(122 테스트) |
| 빠른 묶음 | `python -m pytest -q -m "not slow"` = **1448 passed · 8분 56초** — 목표 3~5분 **미달**(§2 결정 1) |
| 골든 단독 | `python -m pytest -q tests/anti_inertia/test_provenance_e2e.py tests/anti_inertia/test_q3_light_e2e.py`(dark·light) |
| 문서 | README §6.3(명령 블록·보고서 머리말 `full_pytest:` 한 줄 — 이 보고에 첫 적용), WORKFLOWS 검증 체크, 15 P12, FABLE_HANDOFF §2 — 모두 "C8.3(D187)" 인용 |
| 강제 | `tests/test_slow_markers.py` — `--strict-markers`·`slow` 등록 + 실측 25초 이상 16클래스가 마커를 달았는지 |
| 하루 1회 기록 | 보고서 머리말 `full_pytest: <날짜> <커밋> <결과>` 한 줄(제안 — 이 보고부터 씀) |

## 2. 결정 요청 1 — 빠른 묶음 8분 56초(목표 3~5분)
빠른 묶음은 1448개 평균 0.37초의 긴 꼬리입니다(상위 40개 합 ≈ 190초).
| 선택지 | 결과 | 위험 | 되돌리기 |
|---|---|---|---|
| A. 마커 확대(실측 3초 이상 약 60개 더) | 약 5~6분 예상 | 빠른 묶음 범위가 줄어든다(렌더 없는 단위 테스트까지 빠짐) | 마커 지우기 |
| B. `pytest-xdist -n 4`(4코어) 개발 의존성 추가 | 약 2.5~3분 예상(빠른 묶음 전체 유지) | 새 의존성. `projects/hormuz_korea/prev/` 등 공유 파일을 쓰는 테스트가 병렬로 충돌할 수 있다 — e2e 는 이미 slow 라 빠른 묶음에서는 적지만 감사 필요 | 의존성 제거 |
| C. 그대로(8~9분) | 변경 없음 | 목표와 다름 | — |
**Opus 권고: B** — 빠른 묶음의 범위를 줄이지 않는다. 의존성 추가라 결정이 필요합니다. 승인되면 공유 파일 테스트를 감사해 `xdist_group` 또는 slow 로 묶고 실측합니다.

## 3. 결정 요청 2 — 렌더 프레임 비용(cProfile, 호르무즈 720p 100프레임, frame 3000~3099)
| 테마 | 100프레임 | 1위 | 2위 | 3위 |
|---|---|---|---|---|
| dark | 10.3초 | **국경 그리기 ≈ 66%**(cairo stroke 3.43 + stroke_preserve 0.86 + `borders.path_rings` 파이썬 경로 2.35) | 지형 래스터 PIL resize 2.54(25%) | 프레임 PNG/버퍼 encode 0.20 |
| light | 7.1초 | **국경·해안 ≈ 50%**(stroke 1.28 + 0.86 + path_lines 0.79 + path_rings 0.62) | 지형 resize 2.50(35%) | fill 0.31 |
정지 카메라 프레임 = 0/6255(느린 푸시인이 항상 돈다) → 프레임 간 캐시는 효과 없음.
가장 큰 1개 = 국경 그리기. 고치는 안:
| 선택지 | 기대 | 골든 |
|---|---|---|
| A. `path_rings` 를 numpy 일괄 변환 + 화면 밖 고리 사전 컬링(같은 점·같은 순서로 cairo 에 넘김) | dark 약 −15~20% | **바이트 동일**(같은 경로) — 25/25 확인으로 증명 |
| B. 줌별 고리 단순화(Douglas-Peucker, 0.25px 미만) | 국경 stroke 비용 크게 감소 | 바이트 변화(눈에 안 띄어도 골든 갱신 = 사용자 판정 필요) |
| C. 국경을 티어 래스터에 미리 굽기 | 최대 | 선 두께가 줌 따라 변함 — 사용자 합격 화면이 바뀐다 |
**Opus 권고: A**(되돌리기 쉬움·바이트 동일, P12 한 번에 하나). 코어 증설은 사용자 환경 결정 — 지금 렌더는 4코어에 청크 4개로 7805프레임 327초.

## 4. 막히는 범위
결정 1·2 를 기다리는 것: xdist 도입·국경 최적화. 기다리지 않는 것: 없음(D-0188 나머지 끝). V4 는 감독 D 대기.
