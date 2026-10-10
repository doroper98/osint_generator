---
id: R-0192
from: opus
to: fable
kind: phase_report
responds_to: [D-0153, D-0157]
phase: "Q1"
version: v5.14.0
commit: 5eae0d6
status: done
---

# Phase Q1 완료 — cascade V2 (v5.14.0)

상세는 `docs/handoff/reports/phaseQ1/run_log.md` 입니다(사용자 결정 D148, 가이드 23 §6).

## 1. 변경 요약(커밋)

| 커밋 | 내용 |
|---|---|
| `d9e7175` | VERSION 5.14.0·헤더·CHANGELOG(v5.13.0 Q0 마감) |
| Q1-1 커밋 | rules V2 값·`frame`·`surface`, slot 식, `draw_frame(style, occluders)`, `cascade_boxes` 같은 기하, handoff 08 §15.1·19 §3 3.21, `test_cascade` 값 단정 3 갱신 |
| `5eae0d6` | 테스트 15, `tools/cascade_demo.py`, 시트 4 |
| run_log 커밋 | phaseQ1 run_log |

## 2. 합격 조건 대조(D-0153 §4 + D-0157 보강)

| 조건 | 결과 |
|---|---|
| 테스트 ≥ 12 | 15개. 전체 **1445 passed · failed 0 · skip 0**(1430 + 15) |
| 실측 | 8항목 120Hz 2,160시점: 최대폭 **549.429**, 뒤 카드 **4**, dx/dy 오차 **5.7e−14** — 가이드 §6 값과 같음 |
| 보강 1 전/후 crop | `cascade_clip_before_after.png` — Q0 와 같은 입력·좌표 + 표본 4곳 좌표·RGB 는 run_log §2 |
| 보강 2 draw_frame 기본 바이트 동일 | 단위 12 경우(아일랜드 3·panel_box × 알파 3) 바이트 동일, AST(옵션 넘기는 곳 = cascade 하나), **fed_policy_2026 미리보기 22/22 md5 동일**(아일랜드 전 컷·기사 카드 2컷) |
| 보강 3 `cascade.surface` | `{bg, front, back, text, text_sub, edge}` RGB 0~1(검증기). rules 에는 hex 금지 규칙이 없다(금지는 프리미티브·sketch 모듈 소스) — 지시대로 RGB 실수 |
| 국기 원 | `cascade_flag_circles_480p.png` 480p 실크기 + 4배(de·nl·fr·ir·in) — 변형·띠 뭉개짐 없음(육안) |
| 골든 | hormuz 는 cascade 0 → 25컷 무변경(`test_provenance_e2e`) |

## 3. 판단 기록(되돌릴 수 있는 선택)

1. 가림 = 그룹 + `DEST_OUT` 차례 지우기(남는 알파 Π(1 − 가림)). "순차 complement clip" 과 같은 합집합이고, 앞 카드 페이드 중 밑 카드도 같은 비율로 사라져 등장 순간 튐이 없습니다.
2. 바탕 알파·그림자는 island 값 재사용(가이드에 값 없음). 테두리 알파 1.0.
3. `back_dim` 유지(표면색에 곱함) — 삭제 지시는 `back_dy` 뿐.
4. 새 카드 = 제자리 페이드(슬라이드 삭제, 가이드 "개별 Y slide 제거").
5. 가이드의 가상 기관용 강조색(gold `#BFB18F` 등)은 등재하지 않음(actor accent 유지 지시).
6. `surface.bg` 는 엔진 미사용, 데모 도구 바탕만.
7. `cascade_boxes` 는 가리는 상자를 모서리 반경만큼 줄여 재서 보수적으로(둥근 모서리 조각 포함).

## 4. 한계 — 검증 못 한 것

cascade 를 쓰는 3개 프로젝트(`hormuz-talks-2026`·`kaliningrad-suwalki`·`valdai-2026`)는 V2 글자 검사를 통과합니다. 하지만 이 환경에 `plan.json` 이 없어 전체 미리보기 검사를 돌리지 못했습니다(plan = Supertonic 합성, D-0155 로 V2 전 렌더 금지).
V2 차지 영역이 아래로 약 66px 커졌습니다(y 150.5 → 216). 다음 렌더에서 `[cascade-label-under]` hard 가 새로 나올 수 있습니다.

## 5. 다음

D-0157 대로 **Q2(v5.15.0) 인물 뱃지·국기 물결** 로 넘어가려 합니다. 착수 지시(또는 이 보고 검토)를 기다립니다.
