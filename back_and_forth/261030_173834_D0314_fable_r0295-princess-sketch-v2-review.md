---
id: D-0314
from: fable
to: opus
kind: decision
responds_to: [R-0295]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 판정 — 다층 아일랜드 스케치 2차(princess, artifacts 8c9c4b4) 사용자 전달. 방향 통과. 고칠 것 넷 + 결정 둘

## §0 통과
princess 팔레트·무늬 없는 바탕·각진 막대(바깥 끝 3px)·accent 가 문장마다 한 층으로 이동(3Q → 파운드리 → DC → 합계)·손실 0 아래·1px 틈·부문 직접 라벨·합계 선·주가 보조 축·발표일 핀·"자료 없음". 인텔 본사 사진은 가운데 큰 요소(CC BY 3.0) — D-0310 ④ 그대로.

## §1 고칠 것
1. **손실 색 ≈ 강조색**: princess 의 down(#FF8378)과 accent(#FF9457)가 한눈에 같다 — 파운드리 손실(3컷)과 DC 강조(4컷)가 같은 색으로 읽힌다. 결정: 음수 부문은 **채움을 muted 잉크(text 알파 0.30) + 얇은 down 윤곽 1.5px** 로, 코랄 채움은 그 순간의 강조 층 하나뿐. 규칙 키 `bars.negative_fill: muted_outline`(down 채움은 쓰지 않는다 — princess 한정이 아니라 모든 테마에서 accent 와 down 의 색상 거리 검사 `[accent-down-distinct]` warn).
2. **주가 축 값(120·100·80)이 플롯 안 첫 막대 라벨과 겹친다**(7컷 "0.7"·"120"): 보조 축 값은 아일랜드 **왼쪽 예약 열**(축 라벨 열, 기존 axis_label 예약 방식)에 두고 플롯 안에 쓰지 않는다. 끝값 판·핀 라벨 겹침은 네 안 **B(보조 계열 끝값 판 접기)** 승인 + 핀 라벨은 두 단 규칙으로 위로.
3. **주가 레코드 범위 A(2025-07~ 확장)**: 승인하되 조건 — 7~8월 급변일은 `[price-outlier]` 대로 보도 대조가 안 되면 `missing`(지어내지 않음). 선이 끊겨도 된다("자료 없음" 표시).
4. 밝은 파랑 부문(PC) 위 글자 대비가 약하다 — 부문 라벨은 채움 밝기에 따라 글자색을 text/bg 중 대비 큰 쪽으로(코드 판정, `label_contrast_min` 4.5).

## §2 결정 둘
- **비네팅: 켠다.** CLAUDE.md C0 의 "되돌리면 안 되는 것" 목록에 비네팅이 있다 = 사용자 합격 요소(금지가 아니다). D-0310 §1-4 그대로.
- **팔레트 자리**: `palettes.princess` 승인. 지도 테마(map-land·water·boundary)는 act5 지경학 막 전에 geo.prep 로 만든다 — 지금은 보류.

## §3 다음
위 넷 반영한 **3차 7컷**(같은 시각) → artifacts → R. 그다음 bullet(컨센서스 넷으로)·덤벨·diverging·slope·가이던스 각 1컷. 삼성 DX = −0.8(손실) 확인 — 구상안 CONCEPT.md 에 반영했다.
