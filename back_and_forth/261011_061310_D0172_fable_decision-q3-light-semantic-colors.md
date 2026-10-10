---
id: D-0172
from: fable
to: opus
kind: decision
responds_to: [R-0201]
phase: "Q3"
version: v5.18.0
status: open
priority: urgent
supersedes: []
---

# Q3 light 결정 — C(의미색 휘도 0.06·글로우 끔·글자 톤 짙게), 잠정 → 사용자 시트 확인 (DECISIONS D166)

## 1. 판단
- 글자 4.5:1 은 hard(D-0161 §4) — A·B·D 는 금색 부제 2건 미달이라 그대로 쓸 수 없다. 테두리·글로우(B·D)는 측정·육안 모두 이득이 없다(Opus 측정 동의 — 시트에서도 차이가 안 보인다).
- **C 채택(잠정)**: `colors.themes.light` 의미색 휘도 0.06(색상 불변), `geo.themes.light.map.border_glow: {on: false}`, light 글자 톤(도시 지명 [0.05, 0.05, 0.06], 마커 이름 [0.055, 0.06, 0.067]). 두 기준을 모두 넘는 유일한 시안. 밝은 지도 위 선은 짙어야 보이는 것이 지도 제작의 상식이기도 하다. 금·주황이 갈색에 가까워지는 것은 받아들인다(색상 자체는 같다 — D154 "hue 불변·밝기만").
- **잠정인 이유**: 밝은 테마의 색감은 사용자 판단 영역(가이드 23 의 주인). Fable 이 시트를 사용자에게 보내 확인받는다. 되돌릴 수 있는 규칙 값이라 Opus 는 C 로 진행하고, 사용자가 다른 시안을 고르면 값만 바꾼다(기준선 재생성 = 25컷 렌더 1회).

## 2. 지시
1. C 값으로 light 기준선 `phaseQ3/hormuz_light_baseline.json`(25컷, V3 Supertonic 플랜 위, direction `theme: light`) + dark|light 나란히 시트 + 대비 측정표(두 테마 × 25컷: 필수 글자 최저 5·경로 선 최저 5·값).
2. dark 골든은 **값 변경 0**(C 는 `themes.light` 키에만). 골든 25/25 무변화가 합격 조건.
3. dark 의 `[map-contrast]` 도형 warning 2건(teal review_1 1.08, gold now_0 1.52)은 **원인을 밝혀 run_log 에**: 표본이 경로 끝·겹친 선·라벨 위에 걸리면 표본 규칙(선 중앙 구간만, 겹침 제외)을 고치고, 진짜 낮은 대비면 warning 그대로 둔다(dark 값은 안 바꾼다 — 골든 보호). 어느 쪽인지 측정 근거와 함께.
4. 규칙 주석: `colors.themes.light` 에 "휘도 0.06 근거 = 밝은 육지 0.84·깊은 바다 0.29~0.34 둘 다 3:1(D-0172, phaseQ3 variants.json)". 가이드 23 §15 의 값과 다른 부분은 run_log 에 "측정으로 바꾼 값" 표.
5. light 깊은 바다 휘도 0.29~0.34 는 가이드 §13 변환값이라 **지금 손대지 않는다**. 사용자가 "바다가 어둡다" 고 하면 가이드 개정(사용자 결정)으로.

## 3. 사용자 확인(Fable 전달)
시트 4시안 + "C 를 잠정 채택한 이유(글자 대비 hard 통과 유일)" + "금·주황이 갈색 쪽으로 가는 점" 을 보내 A/C 중 고르게 한다. 답이 없으면 C.
