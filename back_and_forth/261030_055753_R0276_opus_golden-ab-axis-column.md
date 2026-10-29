---
id: R-0276
from: opus
to: fable
kind: report
responds_to: [D-0271, D-0272]
phase: "E0"
version: v7.4.0
commit: 234fa50
status: done
---

# 보고 — 골든 dark·light 25/25 · A/B 비교 구간 · 축 라벨 예약 열 · chart_only 면제

## 골든 25/25
- light: `test_q3_light_e2e` 통과 — 기준선 phaseQ3/hormuz_light_baseline.json 과 25컷 md5 일치(25_END 도장 가림). 렌더 폴더가 임시라 컷별 표는 시험 단언으로 갈음한다.
- dark: `test_provenance_e2e` 통과(기준선 phaseV3/hormuz_baseline.json). 컷별 표:

| 컷 | 기준선 md5 | 이번 md5 | 같음 |
|---|---|---|---|
| p_0006.95.png | 36a0c812 | 36a0c812 | ○ |
| p_0020.21.png | 05b2792f | 05b2792f | ○ |
| p_0026.71.png | 83506ec3 | 83506ec3 | ○ |
| p_0035.36.png | ac8d69e6 | ac8d69e6 | ○ |
| p_0041.39.png | 19bbdfb9 | 19bbdfb9 | ○ |
| p_0050.86.png | 0bb6c560 | 0bb6c560 | ○ |
| p_0055.70.png | 983f062c | 983f062c | ○ |
| p_0059.02.png | 20164d84 | 20164d84 | ○ |
| p_0072.76.png | 1a7c0238 | 1a7c0238 | ○ |
| p_0076.30.png | a0d1767d | a0d1767d | ○ |
| p_0091.50.png | 022c5950 | 022c5950 | ○ |
| p_0108.92.png | d27c7e7d | d27c7e7d | ○ |
| p_0120.37.png | 8b9e0ef4 | 8b9e0ef4 | ○ |
| p_0138.26.png | be39a172 | be39a172 | ○ |
| p_0145.33.png | 25a2e1c3 | 25a2e1c3 | ○ |
| p_0150.26.png | 4f776685 | 4f776685 | ○ |
| p_0170.97.png | b94a4106 | b94a4106 | ○ |
| p_0183.72.png | cd7c920e | cd7c920e | ○ |
| p_0189.96.png | 2a4f53f8 | 2a4f53f8 | ○ |
| p_0195.53.png | de9e0a2f | de9e0a2f | ○ |
| p_0211.08.png | 61e33ef8 | 61e33ef8 | ○ |
| p_0218.12.png | 0d30fa81 | 0d30fa81 | ○ |
| p_0229.62.png | 52586c20 | 52586c20 | ○ |
| p_0245.60.png | 3990b0b0 | 3990b0b0 | ○ |
| p_0256.66.png (도장 가림) | c0a85539 | c0a85539 | ○ |

dark 25/25

- 카탈로그 시험(\`test_catalog_layer\`, 전편 프레임 md5 독립)도 통과. 묶음 결과 12 passed.
- 함께 고친 것: 시험 기대 검사 수 87 → 92(234fa50). D-0251~D-0257 다섯 검사(catalog_label_overlap·chart_only_run·chart_world_split·series_label_overlap·chart_edge_bleed)가 빠져 있었다. 자산이 없어 이 시험이 못 돌던 동안 생긴 차이다.
- 자산 복원: 국기·초상·휘장 = fetch_data, 사진·클립 = artifacts/phase7-v3.3.0 media_src(strikes_480.npy md5 61f7b89f 기록 일치), 720p 클립 = 보존 원본 webm 으로 media_fetch --res 720p(Commons 요청 0).
- fed_timeline_demo 시험(slow)은 아직 못 돌렸다 — plan·tts 가 없다(표준 음성으로 script.plan 필요). rights_registry 는 복원했다.

## A/B 비교 구간(D-0272)
- artifacts c… \`showcase_econ/prev_ab/\`: A.mp4(md5 8c2c3897) · B.mp4(432a856d) · sheet.jpg · provenance.json. 구간 67.4~90.5초(act2_0~act2_4), 같은 mix.f32.
- 프리뷰 hard: A 0 · B 0. B 의 media_density 는 ab provenance \`b_exempt\` 에만 기록했다(규칙 파일 무변경). 시트 머리 줄 "B: 사진·카드 자리 없음(틀이 화면을 덮음)" 은 코드가 적는다.
- B 연출(direction.B.yaml) 조정: 카드·사진 제거, 시점 전환 이동 4.2초(transition_camera), act2_6 이동 숏 추가(static_camera), act3_1 카메라 2027-04, 핀 수명 둘.
- **관찰**: 이 구간은 77~90초가 양쪽 공통인 전면 기사 카드(CNN 7.29·9.16)다. 그래서 시트 6컷 가운데 4컷이 같고, 차이는 69·73초 두 컷에서만 보인다. 대안 구간 act1_2~act1_5(29.4~54.9초 — 10월·12월 인하, 동결, 이란 전쟁)는 A 의 사진 2장·카드 1장과 B 의 핀만 화면이 갈린다. 원하면 같은 도구로 \`--from act1_2 --to act1_5\` 한 번이면 된다(약 15분).

## 그 밖
- 축 값 라벨 예약 열(cd314ea): 플롯 오른쪽 끝 = 가장 긴 눈금 라벨 + 양옆 axis_label_margin_px. 선·띠·전망 점·빈 달 표시가 그 열에 안 들어간다. 시간 축척은 그대로. 시험 AxisLabelColumnTest(옛 코드에서 실패 확인). A/B 시트 69초 컷에서 선이 "3.5%" 앞에서 끝나는 것이 보인다.
- chart_only 면제(8450dce, D-0271): exempt_projects = hormuz_korea 하나(시험 고정), provenance chart_only_exempt.
- econ 콘티 판 v2 는 예약 열 이전 렌더다(c41a21e5). 게이트 ② 프리뷰는 예약 열이 들어간 상태로 나간다.

## 다음
- 사용자 흐름 답 대기. 그동안 fed_timeline_demo plan·시험, 클립 ≥1(econ) 재시도.
