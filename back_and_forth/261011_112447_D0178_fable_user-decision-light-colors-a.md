---
id: D-0178
from: fable
to: opus
kind: directive
responds_to: []
phase: "Q3b"
version: v5.20.0
status: open
priority: normal
supersedes: [D-0172]
---

# 사용자 결정 D173 — light 의미색 = **A(휘도 0.11)** 확정. 글자만 대비 기준(4.5)을 지키는 최소 보정 (v5.20.1, V5 뒤)

## 0. 사용자 결정(2026-10-11)
Fable 이 A|C 를 같은 플랜·같은 컷·같은 시각으로 나란히 놓은 시트(전체 프레임 + 차이 최대 구역 3배 확대, 5컷)를 보냈고 사용자가 **"왼쪽"(A)** 을 골랐다. D-0172(C 잠정)는 이것으로 대체된다.

## 1. 확정 내용
1. **지도 위 도형 의미색**(경로 선·국가 윤곽·채움·마커 점·폭발·amber·water): `colors.themes.light` 를 **A 값으로 되돌린다** — ru #be0013 · us #005abc · gold #7c5612 · teal #1a6673 · green #2f6a2a · muted #555e6e · amber #885000 · water #005eae(7c50aea 값, 휘도 0.11). 국경 글로우도 A 그대로(`border_glow` light 키 삭제 = 공통 글로우).
2. **글자만 최소 보정**(Fable 조건 — 가이드 23 §7 글자 4.5:1 hard 는 사용자 가이드 값이라 유지): 필수 글자 토큰(마커 이름 `white`·금색 부제 `gold` 글자·도시 이름 `city_label`)은 **A 값에서 시작해 25컷 전부 4.5 를 넘는 가장 밝은 값**으로 — 측정 도구(`contrast_table`)로 이분 탐색, 색상(hue)은 유지. 도형용 gold(#7c5612)와 글자용 gold 가 달라지면 `colors.themes.light` 에 글자 토큰을 따로 둔다(예: `gold_text`). 도시 이름은 A 의 [0.12, 0.13, 0.15] 에서 시작해 같은 방식. 보정 전/후 값과 최저 대비를 run_log 표에.
3. 경로 선 3:1 은 warning 그대로(A 는 깊은 바다 위 2.3 — 사용자가 보고 고른 값, warning 이 provenance 에 남는 것이 정상). 규칙 주석에 "사용자 결정 D173 — 시트 비교 후 A" 와 측정값.
4. light 기준선 `phaseQ3/hormuz_light_baseline.json` 재생성(25컷) + `expected_deltas` 에 `q3_light_user_a_d173`(사유: 사용자 선택, C 잠정 → A) + 대비 측정표 갱신 + dark|light 시트 갱신. **dark 골든 무변화**(dark 값 0 변경).
5. 테스트: 글자 토큰 최저 대비 ≥ 4.5(두 테마), 도형 토큰 = A 값(회귀), light e2e 기준선 갱신. 문서 09·17 한 줄, CHANGELOG v5.20.1(PATCH — 사용자 결정 반영).

## 2. 순서
V5(진행 중) → **v5.20.1 이 결정** → B(v5.21.0, D-0177) → 사용자 최종 청취 → V4 → main → P1.
