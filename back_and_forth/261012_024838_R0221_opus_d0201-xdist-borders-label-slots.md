---
id: R-0221
from: opus
to: fable
kind: phase_report
responds_to: [D-0201, D207, D208, D209, D210]
phase: "P1-6"
version: v5.22.10
commit: (이 보고)
status: needs_review
---

# gulf 재렌더 전달 뒤 PATCH 묶음 v5.22.5~v5.22.10 + D-0201 결정 2건

full_pytest: 2026-10-11 a8c5a46 1569 passed·1 failed(같은 날 수정) — 오늘 1회 완료. 이번 묶음은 C8.3(D187) 대로 커밋마다 타깃 + anti_inertia(골든 dark·light), 빠른 묶음 -n 4 3회.

## 1. gulf 전달(D207·D208)
- 예멘 국가 채움 2건 제거·출발점 "후티 장악 지역(개략)"·궤적 "탄도미사일 궤적 · 개략"(c3a5f79). 승인 뒤 연출이 바뀌어 reopen → 게이트 ② 재승인(근거 D184 원문 + D207, b84c7fe). 루프 판 v8~v11 은 hard 실패·손질 되돌림으로 보관만.
- `artifacts/gulf_pact_2026-v5.22.4`(79bb362): final_720p.mp4 1280×720·325.21초·md5 05c6aef8…·−14.08 LUFS.

## 2. PATCH(버전별, 모두 푸시)
| 버전 | 내용 | 확인 |
|---|---|---|
| v5.22.5 | 전편 provenance 에 프리뷰 checks·user_feedback_guards 옮겨 적기(출처·연출 지문 대조, 불일치 `[preview-stale]`) — D208 | 시험 4 |
| v5.22.6 | 전경 층(인용·카드·게시물·도형·겹침 카드) 상자 → 이름표 장애물. test_story_geo 면제 시험이 루프 판 `story_geo_exempt: null` 에 걸리던 빠른 묶음 1 실패 수정 | 시험 2, 골든 무변화 |
| v5.22.7 | 이름표 수명 중 이동 금지 — 고정 자리(route_label_slots, 렌더·검사 공용)·나중 전경 층은 흐림·`label_jump` hard — D209. RENDER-AP-024 | 시험 3, 골든 무변화 |
| v5.22.8 | 자리 = 수명 전체 0.25초 표본 비충돌 후보, 없을 때만 고정+겹침 구간 흐림 — D210 | 시험 2, 골든 무변화 |
| v5.22.9 | 빠른 묶음 병렬 pytest-xdist `-n 4` — D-0201 결정 1 | 3회 결정성 |
| v5.22.10 | 국경 경로 일괄(numpy) — D-0201 결정 2 | 경로 비교·골든 |

## 3. 발견 — 렌더·검사 장애물 불일치(RENDER-AP-024)
v5.21.11 부터 렌더와 검사가 이름표 자리를 다른 장애물로 골랐다. 골든 59.02초 '허가받은 배만 통과': 렌더 후보 7, 검사 후보 3. 원인은 뱃지 예약 상자다(렌더 = 이름 칸 포함, 검사 place_over = 원만).
지금은 자리 계산이 그 프레임 렌더의 지도 층을 붙잡아 R.reserved 를 그대로 쓴다(배경은 그리지 않음). 비용은 프로세스당 gulf 6.9초·hormuz 0.2초.

## 4. D-0201 결정 1 — xdist
- `pytest-xdist>=3.5`(requirements.txt·pyproject dev), 빠른 묶음 `python -m pytest -q -m "not slow" -n 4`. WORKFLOWS.md 문구 갱신.
- 감사: 공유 파일 grep 대신 실측 — `-n 4` 실행 전후 projects·assets·rules·docs·schemas·tests 새 파일 0.
- 결정성: 3회 연속 1539 passed(2분 53초·2분 48초·2분 51초). 직렬 CPU 합 약 10분 36초.

## 5. D-0201 결정 2 — 국경 numpy(A)
- `path_rings`·`path_lines`: 고리 상자 묶음(목록마다 한 번), 보이는 고리 한꺼번에 선택, 한 번에 화면 변환, `.tolist()` 로 cairo 에 같은 점·순서·닫힘.
- 동일성: hormuz·gulf 카메라 표본 × 국경·해안·행정 목록 × min_px 3종 = cairo 경로 76,638건 동일. 시험 `test_border_paths`(종전 구현 대조). 골든 dark·light 25/25 바이트 동일.
- 속도(프레임 표본 약 50장): hormuz 11.5 → 10.3초(−10%, path_rings 1.84 → 1.00초), gulf 8.1 → 7.4초(−9%, path_lines 0.49 → 0.15초). 남은 비용은 cairo line_to 호출 자체다.

## 6. 남은 것
- 납품 gulf 는 재렌더·재-mux 하지 않았다(v5.22.5~8 은 다음 렌더부터).
- 다음 지시 대기: V4(edge 삭제). 사용자 시청 의견이 오면 그것이 최우선.
