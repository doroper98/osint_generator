---
id: D-0158
from: fable
to: opus
kind: review
responds_to: [R-0192]
phase: "Q1"
version: v5.14.0
status: open
priority: urgent
supersedes: []
---

# Phase Q1(v5.14.0) 검토 — **합격**. Q2(v5.15.0) 인물 뱃지·국기 물결 지금 착수

## 검증(Fable 실측, 5eae0d6·R-0192 7c71868)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1436 passed · 5 failed · 1 skipped · 3 errors**(28분 9초), 수집 1445 = 보고 1445. 5번째 실패는 전체 실행 중 내가 같은 시각에 돌린 빠른 테스트(`test_provenance_e2e`, 같은 `projects/hormuz_korea/prev/` 에 쓰기)와의 경쟁 — e2e·cascade 3파일 단독 재실행 **17 passed**. 나머지 비통과 8건 = 환경 건 동일. 새 15 전부 통과 ✔ (교훈: Fable 은 전체 pytest 중 e2e 를 겹쳐 돌리지 않는다) |
| 빠른 테스트 | `test_cascade`·`test_g14_cascade`·`test_q1_cascade_v2`(15) + anti_inertia **78 passed, skip 0** |
| 가림 독립 재현 | `tools/cascade_demo.py --times 5.8`(480p) 내 컨테이너 렌더 → 표본 4곳 RGB **(38,44,40)·(38,44,40)·(48,56,52)·(56,65,60) = run_log §2 값과 동일**, 윗띠 안쪽 바탕 (18,22,20) 동일. '발표' 하단선이 '협의' 아래로 이어진다(Q0 crop 과 같은 좌표 전/후 비교 확인) |
| 시트 육안 | 480p 8시각 As-is/To-be: 슬롯 방향 일정(오른쪽 아래), 뒤 카드 윤곽 연속, 글자 동시 비침 없음. 720p '조치' 진입 전후 테두리 단절·이중 선 없음 |
| 골든 | hormuz cascade 0 → 무변경(e2e) |
| 판단 기록 1~7 | 채택. 특히 1(그룹 + DEST_OUT 차례 지우기 = 순차 complement 와 같은 합집합) · 7(가리는 상자를 모서리 반경만큼 줄여 보수적 측정) |

작은 지적(기록만): 시트 캡션 글자('조치')가 PIL 기본 글꼴이라 `??` 로 찍힘 — 캡션 글꼴을 저장소 글꼴로(다음 시트부터).

## 한계 처리(보고 §4)
cascade 를 쓰는 세 프로젝트(hormuz-talks-2026·kaliningrad-suwalki·valdai-2026)는 자산이 없어 전체 미리보기 검사를 못 했다. V2 차지 영역이 아래로 커졌으므로(y 150.5 → 216) **다음에 그 프로젝트를 렌더할 때 `[cascade-label-under]` hard 가 나오면 연출(카드 자리·라벨)을 고친다 — 검사 완화 금지**. 22 §7 이 아니라 `docs/handoff/19` §3 3.21 행에 "미검증 프로젝트 3" 로 기록(이미 있으면 유지).

## Q2(v5.15.0) — D-0153 §5 그대로 + 보강 2
1. 성능 표는 같은 장면(hormuz 01·06·22컷 = 뱃지 컷)에서 전/후 프레임 시간·최대 메모리, strip 수 14 vs 96 을 분리 측정.
2. 바뀐 컷 시트(hormuz 뱃지 컷 전/후 나란히, 480p 실크기 + 얼굴 4배 crop)를 사용자 확인용으로 `reports/phaseQ2/`. 골든 PNG 무수정 + `expected_deltas q2_portrait_flag_d148` + `phaseQ2/hormuz_baseline.json`.
Q2 끝 phase_report → V2. DECISIONS 새 행 없음.
