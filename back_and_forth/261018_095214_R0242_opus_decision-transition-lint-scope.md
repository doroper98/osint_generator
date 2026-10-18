---
id: R-0242
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "P3-1"
version: v7.4.0
commit: fc7c449
status: awaiting_decision
---

# 결정 요청 — [transition-bridge] 판정 단위와 옛 프로젝트 적용 범위(D-0229 §2.2)

## 쟁점
지침 문구("이웃 문장 날짜 배지가 jump_days(30일) 이상 뛰면 전환, ±1문장 안 bridge 없으면 hard")를 그대로 구현해 저장소 원고 20개에 돌렸다.
- diesel_road_2026 v1: 전환 지점 **30곳**(act1 안에서만 act1_4·8·10·11·12·15 …). 배경 문장(IEA 9월 보고·2022년 이후 통계)이 날짜 배지를 앞뒤로 흔들 때마다 걸린다.
- hormuz_korea(골든): **9곳** → hard 면 `script.plan` 이 거부 → 골든 e2e 준비 자체가 막힌다. 그 밖 kaliningrad 39, fed_policy 18, gulf_pact 14 등 12개 프로젝트가 걸린다(0 = taiwan·ratcliffe 계열 5개).
- 문장 단위 그대로면 v2 원고에 bridge 문장이 20~30개 필요하다. UF-105 원문은 "시점을 건너뛰는 **섹션**이 나오면"이다.

## 선택지
| | 판정 단위 | 결과 | 위험 | 되돌리기 |
|---|---|---|---|---|
| A | 지침 그대로(이웃 문장 날짜 차 ≥ 30일) | diesel v2 에 bridge 20~30개 | 원고가 "시점을 옮깁니다" 투성이 — 호흡 개선이 아니라 소음 | 규칙 값 |
| B | **장면(막) 경계만**: 이웃 장면의 `stage`(이야기 무대) 가 다르거나, 장면 대표 날짜(중앙값) 차 ≥ jump_days | diesel v1 기준 cold→act1(30일)·act2→act3(39)·act3→act4(44) + stage 전환 = 3~4곳 | 장면 안의 큰 시대 점프(예: 2004년 회고 문장 하나)는 안 잡힘 | 판정 함수 하나 |
| C | 문장 단위 + 지속 조건: 새 날짜가 3문장 이상 이어질 때만 | 배경 문장 1~2개는 무시 | 규칙 하나 더(지속 문장 수), 설명이 어렵다 | 규칙 값 |

옛 프로젝트 적용 범위:
| | 내용 | 위험 |
|---|---|---|
| X | 모든 원고에 hard. 옛 프로젝트는 `lint_waivers.yaml` 에 `transition-bridge` 면제(결정자 Fable) — `rules script_grammar.lint_waivable` 에 kind 추가 | 골든 hormuz 에 면제 파일 행 추가 필요(골든 출력 불변) |
| Y | 원고 날짜(script.date) 가 v7.4.0 착수일(2026.10.18) 이후인 원고만 | 날짜를 옛날로 적으면 빠져나감 |
| Z | 원고에 `stage` 또는 `role` 이 하나라도 있으면 적용(옵트인) | 새 영상이 안 쓰면 미보호(C12 3 위반) |

## Opus 권고
**B + X.** UF-105 원문의 단위가 "섹션"이고(②원문 우선), 장면 경계는 연출의 무대 전환·느린 카메라와 같은 자리라 bridge·호흡·xfade 가 한곳에 모인다. 판정 함수만 바꾸면 되돌리기 쉽다(①). X 는 새 영상을 전부 보호하고(C12 3), 옛 영상은 면제 기록이 남는다(③).
B 로 diesel v1 을 다시 재면 cold→act1 이 30일 경계라 걸린다 — v2 원고는 cold 끝(cold_5)·act1 첫 문장 중 하나를 bridge 로 쓴다.

## 근거
- 실측 스크립트: `script.lint.transition_points`(이 브랜치 미커밋 작업본), 장면 중앙값 표: diesel cold 10-15 → act1 09-15 → act2 10-06 → act3 08-28 → act4 10-11; hormuz route 2025 → war 2026.03 … past 2004.
- UF-105 원문, D-0229 §2.2·§4.4.

## 막히는 범위
- 막힘: `[transition-bridge]` 린트 판정 함수와 면제 처리(커밋 보류).
- 계속: bridge 문장 호흡(timeline)·plan transitions·날짜 배지 xfade·원고 스키마(role·stage·kind), A 단계 2.3~2.10.

## §7 해당 여부
아니다(설계 선택). 단 옛 영상 면제(X)는 결정자 Fable 기록이 필요하다.
