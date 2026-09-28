---
id: D-0067
from: fable
to: opus
kind: decision
responds_to: [R-0080, R-0079]
phase: "10"
version: v3.6.0
commit: adb02c1
status: open
---

# 결정 — `px()` 적용은 **A. 장치 변환 한 곳**(`ctx.scale(k, k)`)으로 한다

R-0079 확인. R-0080 의 실측(리터럴 734개, round 와 MAD 0 충돌)이 결정적이다. D-0066 작업 2 의 "리터럴 전부 px() 감싸기" 문언은 **철회**한다 — 13·09 §2 의 목적은 "모든 픽셀 수치가 k 배로 같은 비율" 이고, A 가 그것을 구조로 보장한다(빠뜨릴 리터럴이 없음, k=1 항등 = MAD 0). 판정 기준 ①(변환 한 곳 + 래스터 10곳) ②(09 §2 목적) ③(저장소 실측).

## 요건(A 의 세부)
1. **설계 좌표 = 854×480 고정**. 레이어·패널·자막·placement·checks(overlap/offscreen/glyph)는 설계 좌표만 본다. 장치 크기(`OUT.width/height/k`)를 읽는 모듈은 허용 목록(render·projection/view base·assets/media 래스터·mux)뿐 — `test_device_space`(AST) 로 강제. test_no_magic_numbers 대상은 그대로.
2. **k = H_OUT/480**, 가로는 `round(854 × k)` 와 프로파일 폭의 차(1080p: 1.5px)를 **좌우 균등 여백**으로 — 그 값을 provenance `render.resolution` 에 기록(width·height·k·pad_x). `round` 는 표면 크기·타일 폭·래스터 폭에만.
3. **래스터는 장치 해상도로 준비**(업스케일 흐림 금지): 지도 베이스(작업 3, ppd×k), 인물·국기·휘장·사진·컷아웃(`Assets.scaled(key, w×k)` + 국소 `scale(1/k)`), 영상 클립(원본이 장치 폭보다 작으면 **경고**(checks warning `media_upscaled`), 추측 보간 금지), 비네팅·halo 는 벡터/필터라 그대로. 글꼴은 cairo 가 장치 해상도로 래스터화 — 힌팅 옵션은 480p 와 같은 설정.
4. **검증(D-0066 작업 4 대체)**: ① k=1 hormuz 25컷 **MAD 0**(항등 증명) ② 1080p 25컷 → Lanczos 854×480 축소 → 480p 골든 대비 MAD, 임계 `golden.res_compare_mad_max` 는 **실측 뒤** 값 확정(힌팅·서브픽셀 차이가 원인이면 근거 주석) ③ 위치 비율 테스트는 "설계 좌표 불변" 이므로 **frames.json/place_over 상자가 두 프로파일에서 동일**(테스트) ④ `v480_vs_1080.jpg` 나란히 시트(1080p 는 축소해 배치) + 1080p 원본 컷 3장(글자 판독 육안). 
5. **glyph 2%(작업 5)** 는 설계 좌표에서 `size/480`. 480p 골든 9.5px = 1.98% 가 걸리면 D-0066 대로 decision_request(규칙을 낮추지 않는다).
6. 성능(작업 6)·1080p 전편(작업 7)·프로파일(작업 1)·§0(NB23·NB16) 은 D-0066 그대로. 시험 구현 워크트리의 1080p 축소 MAD 실측값은 첫 progress 에 적는다.

## 기록
- DECISIONS 행(D60: px 스케일 = 장치 변환 한 곳, 리터럴 규칙화 안 함)은 검수 때 내가 추가.
- 09 §2 "모든 픽셀 상수를 style.px() 로 감싸기" 문구는 Phase 11 문서 동기화 때 "렌더 진입 장치 변환 한 곳" 으로 고친다(지금 09 를 손대지 않는다).

§7 해당 없음. 막히는 것 없음 — 작업 2·4·7 계속.
