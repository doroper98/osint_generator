---
id: R-0306
from: opus
to: fable
kind: decision_request
responds_to: [D-0303]
phase: "US1"
version: v7.4.0
commit: 2aba88d6
status: open
priority: urgent
---

# 게이트 ② 직전 — 마커 부제가 주 채움 위에서 대비 4.29~4.37(< 4.5). light 테마 label_contrast_fix.halo 4.2 → 6.0 결정 요청

## 현황
- D-0303(UF-167~170) 구현 완료·푸시(f6fe9057 … 2aba88d6): admin1_modes(prominent)·area 외곽선 얇게·bars 16(자리 = 코드 resolve_sides). **골든 dark·light 25/25 통과**(2 passed, 13분), 관련 테스트 통과.
- `--preview auto`: **hard 0 · warning 73**. 그런데 게이트 ② 원크기 컷(202·215.5·290초)을 뽑자 같은 검사가 `map_contrast` hard 3건: 마커 부제 '1988년 이후 첫 민주 상원'(TX) 4.37 · '1932년 이후 첫 민주 상원'(KS) 4.33 · '잭슨 53.4 · 콜린스 46.5'(ME) 4.29. auto 표본 시각에 걸리지 않았을 뿐 실제 결함이다(숨기지 않는다).
- 원인 실측(프레임 직접 렌더, `engine.checks.measure_contrast` 같은 식): 국소 보정(D-0186 label_contrast_fix)은 **돌고 있다** — ME 부제 보정 전 2.93 → 보정 후 4.29. halo 선폭 4.2 = 글자 둘레 2.1px 라 글자 사이로 주 채움(민주 파랑 solid)이 보여 상자 중앙값 배경이 0.55 로 남는다.
- 보정 halo 만 바꿔 같은 3컷 최저 대비: 4.2 → [4.37, 4.33, 4.29] · **6.0 → [4.78, 6.48, 5.65]** · 7.0 → [4.78, 6.77, 5.65] · 8.0 동일. 6.0 이 최소 통과값.

## 선택지
- **A(권장)** `rules geo.themes.light.map.label_contrast_fix.halo` 4.2 → **6.0**(light 만, dark 그대로). 대비 미달 글자만 다시 그리는 국소 보정이라 통과 글자·전역 값 무변화. 근거 = 위 실측. 검증: light 골든(test_q3_light_e2e)·test_label_contrast_fix 를 6.0 으로 지금 돌리는 중(결과를 D 전에 메시지로). 되돌리기 = 값 하나.
- B area 알파를 낮춘다(D518 값 변경 — 이전 실험 lean 0.24·solid 0.38·landslide 0.56 에서 지명 4건 중 3건 해소, 마커 부제는 미측정). 사용자 지시 UF-169 이후의 채움 인상이 바뀐다.
- C 해당 마커의 부제를 빼거나 마커를 주 밖(바다·이웃 회색 지대)으로 — 정보 손실·지명 대조 경고.

## 다음
- A 결정이면: 값 변경 커밋 → `--preview auto` + 원크기 컷 10장(45 "석" 패널·132 민주 로고·202 텍사스 bars·215.5 캔자스·290 메인 w12·318.5 본토 w60 주 이름·334 미시시피 counting bars·354 1937 사진·403.9 조지아 주지사·427 플로리다 bars·동부 w36) hard 0 확인 → artifacts gate2/ → gate_request R + send_message.
