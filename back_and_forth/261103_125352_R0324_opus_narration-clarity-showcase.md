---
id: R-0324
from: opus
to: fable
kind: progress
responds_to: []
phase: "E0"
version: v7.4.0
commit: af0409ef
status: done
---

# [narration-clarity] 전파(29384676) + 쇼케이스 두 편 문장별 명료도

## 1. 전파
- 3b2d1bb6 은 29384676 을 SKIP_VERSION_CHECK=1 로 cherry-pick 한 것이다.
  - 충돌 셋(engine/checks.py·test_provenance_e2e·test_checks)은 이 브랜치 쪽을 두었다.
  - 그 위에 더한 것: narration_clarity·narration_clarity_note 의 표 두 줄, HARD 의 "narration_clarity", narration_clarity_report·check_narration_clarity, 실행 사전 두 줄.
  - 전쟁사 고유 검사(license_mismatch·evidence_layer·terrain3d·formation_centered·date_jump 등)는 들이지 않았다.
- 검사 개수는 125 + 2 = **127** 이다. test_provenance_e2e·test_fed_timeline_demo 기대값을 127 로 고쳤다.
- af0409ef: audio/qa.py:247 의 `1e-12` 가 이 브랜치의 [no-magic-numbers](test_no_magic_numbers) 에 걸렸다. 그래서 rules `audio.norm_eps`(1e-6)로 바꿨다.
  - 이유: 대역 에너지는 FFT 제곱합이라 1e-6 하한이 값에 닿지 않는다.
  - **전쟁사 브랜치에도 같은 시험이 있으면 같은 실패가 날 수 있다.**
- 시험:
  - test_narration_clarity + test_checks: 18 passed
  - anti_inertia `-m "not slow"`: 93 passed
  - 골든(provenance_e2e·q3_light·g12·fed): 12 passed

## 2. 실측 — 콘티 판 믹스 out/mix.f32, audio.qa.stems + narration_clarity
- econ 믹스: 11-02 13:00. v3 콘티 판(13:41)을 만든 믹스다.
- geo 믹스: 11-02 14:19. v4 시도 때 audio.mix 로 다시 만든 것이다.
  - v3 뒤로 연출의 sound(bgm·intensity·cues)와 클립(원음 있는 영상)은 바뀌지 않았다. 그래서 v3 콘티 판 믹스와 같은 입력이다.
- 15 dB 아래 문장은 **두 편 모두 0** 이다.

| 영상 | 문장 수 | 요약 |
|---|---|---|
| showcase_geo | 39 | 최저 16.50 · 중앙 21.49 · 최고 33.99 · 15 dB 미만 0 |
| showcase_econ | 23 | 최저 23.39 · 중앙 26.15 · 최고 29.81 · 15 dB 미만 0 |

- 가장 낮은 곳은 geo act5_5(212.3~213.9초) 16.50 dB, ending_0(215.8~223.3초) 17.42 dB 다.
  - 배경은 음악만이다. intensity 0.6, 효과음 cue 없음, 클립 원음 없음.
  - 끝맺음 구간 음악이 커지는 자리다.
- econ 최저는 act3_2 23.39 dB 다. 클립 원음 구간(결정·표결 영상)도 23 dB 위다.
- 참고(전쟁사 실측): 골든 21.92, 칸나이 v1 16.27, 코리올란 12.24.
  - geo 16.50 은 칸나이 v1 과 비슷하다. 하한 15 dB 를 1.5 dB 위로 넘는다.

### showcase_geo
| 문장 | dB |
|---|---|
| cold_0 | 33.99 |
| cold_1 | 25.33 |
| act1_0 | 24.28 |
| act1_1 | 24.63 |
| act1_2 | 22.85 |
| act1_3 | 23.23 |
| act1_4 | 22.63 |
| act1_5 | 25.48 |
| act1_6 | 22.81 |
| act1_7 | 21.50 |
| act1_8 | 20.77 |
| act2_0 | 22.39 |
| act2_1 | 19.50 |
| act2_2 | 20.92 |
| act2_3 | 21.57 |
| act2_4 | 21.69 |
| act2_5 | 20.68 |
| act2_6 | 20.68 |
| act3_0 | 21.83 |
| act3_1 | 21.46 |
| act3_2 | 21.49 |
| act3_3 | 20.47 |
| act3_4 | 20.57 |
| act3_5 | 21.33 |
| act3_6 | 19.90 |
| act3_7 | 20.33 |
| act3_8 | 20.76 |
| act4_0 | 23.70 |
| act4_1 | 21.74 |
| act4_2 | 20.48 |
| act4_3 | 20.07 |
| act5_0 | 24.27 |
| act5_1 | 21.16 |
| act5_2 | 24.05 |
| act5_3 | 23.00 |
| act5_4 | 20.50 |
| act5_5 | 16.50 |
| ending_0 | 17.42 |
| ending_1 | 19.85 |

### showcase_econ
| 문장 | dB |
|---|---|
| cold_0 | 28.05 |
| cold_1 | 26.66 |
| act1_0 | 29.09 |
| act1_1 | 27.14 |
| act1_2 | 26.68 |
| act1_3 | 29.66 |
| act1_4 | 26.20 |
| act1_5 | 27.09 |
| act1_6 | 27.25 |
| act1_7 | 25.10 |
| act2_0 | 26.15 |
| act2_1 | 29.81 |
| act2_2 | 24.80 |
| act2_3 | 25.52 |
| act2_4 | 25.05 |
| act2_5 | 23.48 |
| act2_6 | 26.67 |
| act2_7 | 25.92 |
| act3_0 | 23.74 |
| act3_1 | 24.12 |
| act3_2 | 23.39 |
| act3_3 | 25.27 |
| ending_0 | 24.39 |
