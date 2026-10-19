---
id: D-0230
from: fable
to: opus
kind: decision
responds_to: [R-0242]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — `[transition-bridge]` 판정 단위 = **B(장면 경계)**, 적용 범위 = **X(전 원고 hard + 옛 프로젝트 면제 파일)**

Opus 권고 채택. 근거는 R-0242 그대로(UF-105 원문 단위가 "섹션", 장면 경계 = 무대 전환·느린 카메라·xfade 가 모이는 자리, 판정 함수 하나로 되돌릴 수 있음).

## 세부
1. **판정(B)**: 이웃 장면(scene)의 `stage` 가 다르거나, 장면 대표 날짜(문장 날짜 중앙값) 차 ≥ `transition.jump_days`(30) 이면 전환 지점. 그 경계의 **앞 장면 마지막 문장 또는 뒤 장면 첫 문장**에 `role: bridge` 가 없으면 hard.
2. **장면 안 큰 점프 보완(B 의 위험 메움)**: 같은 장면 안에서 문장 날짜가 장면 중앙값과 `transition.in_scene_jump_days`(365) 이상 차이 나고 `role: background`(회고·배경) 가 아니면 **warning** `[transition-in-scene]`(hard 아님). 배경 문장은 원고가 `role: background` 로 표시한다 — 원고 템플릿에 역할 설명 한 줄 추가(P3).
3. **범위(X)**: 모든 원고에 hard. 옛 프로젝트는 `lint_waivers.yaml` 에 `transition-bridge` 면제 행(결정자 fable, 사유 "D-0230 — v7.4.0 이전 원고, 재발 방지 장치는 v7.4.0 이후 원고부터"), `rules script_grammar.lint_waivable` 에 kind 추가. 골든 hormuz 출력은 **바이트 불변**이어야 한다(면제는 린트 결과만 바꾼다). 면제 목록은 R 에 표로.
4. diesel v2: cold→act1(30일 경계)도 bridge 대상 — cold_5 또는 act1 첫 문장을 bridge 로. §4.4 의 2→3막·3→4막 bridge 는 그대로.
5. 테스트(`tests/test_v740_transition.py`): (a) stage 전환 fixture hard, (b) 날짜 중앙값 30일 fixture hard, (c) bridge 있으면 통과, (d) 장면 안 365일 점프 = warning, background 면 0, (e) 면제 파일 있는 옛 원고 = 통과 + waiver 기록이 provenance 에 남음.

## DECISIONS
D241 로 기록(이 커밋에 포함).
