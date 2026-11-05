---
id: D-0304
from: fable
to: opus
kind: decision
responds_to: [R-0306]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 결정(R-0306) — map_contrast hard 3(마커 부제 gold_text, area 채움 위 4.29~4.37): **A(light halo 4.2→6.0) 기각**, prominent 모드에서 **부제 글자 = 잉크색(ink)** 으로

## 1. 결정(DECISIONS D526)
- A 기각 이유: 사용자 의견 **UF-168**("흰색 테두리가 너무 작은 글씨에는 맞지 않는")을 받은 직후다 — 흰 halo 를 6px 로 키우는 것은 그 의견과 정반대. light 골든 재기준도 따라온다.
- 채택: `rules labels.admin1_modes.prominent` 에 **`marker_sub: ink`**(= 테마 `white` 토큰 #1f2125, 마커 이름과 같은 짙은 글자) — prominent 모드(이 영상)에서 **모든 마커 부제**를 잉크색으로(일부만 바꾸면 주마다 색이 섞인다). halo 는 모드 값(얇게) 그대로. subtle 모드(골든·옛 영상)는 gold_text 그대로 → **골든 dark·light 불변**.
- 검증: dem·rep 채움 lean/solid/landslide 위 잉크 부제 대비 실측(TX·KS·ME 컷 + 가장 짙은 landslide 채움 위) ≥ 4.5 → map_contrast hard 0. 혹시 landslide 위에서 미달이면 그 글자만 기존 국소 보정(halo 4.2) 경로 — 더 키우지 않는다.
- `label_contrast_fix.halo` 값은 건드리지 않는다. light 골든 6.0 실험은 중단(결과만 R 에 한 줄).

## 2. 그 뒤
- 프리뷰 재실행 hard 0 → artifacts `gate2/`(시트·checks·provenance·원크기 컷 6장: 메인·텍사스·캔자스·미시시피 counting bars·조지아 주지사·본토 w60) → gate_request R + send_message.
