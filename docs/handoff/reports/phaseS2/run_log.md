<!--
tier: 3
last_synced_with: v5.8.0
ssot_for: [phaseS2-run-log]
depends_on: [back_and_forth/261009_235608_D0143_fable_s1-review-pass-s2-globe-kickoff.md, back_and_forth/261010_001036_D0144_fable_decision-seam-threshold-keep-reviewed-geometry.md, rules/video_rules.yaml, sketch/missile/globe.py, sketch/missile/globe_scene.py, sketch/common/render.py]
last_review: 2026-10-10
-->

# Phase S2 실행 기록 — 미사일 3D 지구본 전환 이식 (v5.8.0)

지침 D-0143(S2 보강 8항목), 결정 D-0144(이음새 = 검토본 기하 + 회귀 임계 `checks.seam_px`).

## 0. 컨테이너 준비

S0 §0·§0.2 그대로(같은 컨테이너). 차이:
- 기준 프레임용 `git worktree add /tmp/…/wt4d9 4d9dc65`. 추적 안 되는 자산은 저장소 쪽으로 심볼릭 링크:
  `projects/d1_missile_sketch/assets`·`globe_tex/assets`, `data/geo`, `assets/fonts`.
- 글꼴: 기준·새 프레임 모두 `FONTCONFIG_FILE`(S0 §0.2 표준 설정).

## 1. 기준 프레임과 비교 (D-0143 §0)

옛 `globe3d.py --frames 1.0,4.5,6.5,9.0,12.5,15.0,17.5`(720p 고정) → `ref/`(PNG 미커밋), `ref_sheet.jpg`.
새 `sketch.missile --globe` 같은 7시각 `--res final` → `compare_sheet.jpg`(좌 옛 / 우 새).

| t(초) | 다른 픽셀 비율 | 최대 채널 차 | 원인 |
|---|---|---|---|
| 1.0 | 0.000 % | 0 | — (2D 이어받기) |
| 4.5 | 0.000 % | 0 | — |
| 6.5 | 0.000 % | 0 | — |
| 9.0 | 0.000 % | 0 | — |
| 12.5 | 0.987 % | 250 | 아래 결함 수정 2·3 |
| 15.0 | 0.985 % | 250 | 같음 |
| 17.5 | 0.989 % | 250 | 같음 |

### 검토본 결함 · 수정 (D-0143 §0 — 그대로 옮기지 않음)
1. **정점 라벨 위 잘림**(t ≈ 9.3~9.8): 정점이 화면 위로 오를 때 "정점 …" 줄이 화면 밖으로 잘리고 부제만 보였다.
   수정 = 3D 라벨 기준선을 위 여백(`text.label_edge_margin` + 글자 크기) 안으로. 7컷에는 이 구간이 없어 비율에 안 나온다.
2. **패널에 덮인 착탄 라벨**(t ≥ 10.6): 수평선 패널이 "착탄 추정 영역 / 일본 EEZ 안" 을 덮어 "착탄 추" 만 보였다.
   수정 = 라벨 상자가 패널 상자와 겹치면 패널 바로 아래로 내린다(provenance `label_moved_below_panel`). 12.5·15.0·17.5 차이의 대부분.
3. **정점 값 표기(SK-H1)**: 옛 "정점 약 6,040km" 는 발표값 6,040.9km 를 버림한 문자열이다. 새 화면은 포맷터 `{mod.apogee_km}` → "정점 6,040.9km".

그 밖의 수치·문구·타이밍은 검토본 그대로(`rules sketch.globe` = 원본 리터럴).

### 이식 중 찾은 단위 함정(기록)
- 옛 코드는 글자·패널은 `× SC`(설계 px), 선 굵기·대시·머리 반지름·**발사/착탄/정점 라벨 오프셋**은 720p 장치 px 로 적었다.
  규칙에 `globe.px_ref_height: 720` 을 두고 장치 = 값 × 출력 높이 / 720 로 옮겼다(720p 에서 정확히 원본, 480p 는 같은 비율).
- 3D 레이더 라벨 이름은 2D 와 다르다("AN/TPY-2 · 성주") → spec `sensors[].globe_name`.

## 2. 이음새 (D-0143 §4 → D-0144)

첫 3D 프레임(t_2d, k = 80)과 2D 마지막 프레임(handoff 41.0 + 2.0 × 0.3 = 41.6초)의 지상 궤적 양 끝 화면 좌표 차(설계 px):

| 해상도 | 발사점 |Δx|·|Δy| | 착탄점 |Δx|·|Δy| |
|---|---|---|
| 480p(trial) | 11.34 · 11.70 | 0.31 · 4.72 |
| 720p(final) | 11.08 · 11.74 | 0.17 · 4.66 |

임계 `checks.seam_px` = 12.5(D-0144). 원인 = 메르카토르(2D) 대 접점 방위 등거리(3D) 투영 본질 차 + 시작 줌 차. 근본 해결(투영 혼합)은 본편 globe 무대 과제.

## 3. SK-C1(3D, D135) 실측

| 항목 | 검토본 최대 | 임계 |
|---|---|---|
| 발사점 화면 궤적 |Δ²|/W | 0.00051 | 0.01 |
| 착탄점 화면 궤적 |Δ²|/W | 0.00055 | 0.01 |
| 초점 거리 |Δ ln f| | 0.0042 | 0.07 |
| 음성(ease 제거 → 선형 키프레임) | 0.0142(t = 3.00 위반) | — |

2D 이어받기 구간(t < t_2d)은 S1 카메라 검사를 handoff 시각들로.

## 4. 전편 렌더

| 프로파일 | 시간 | mp4 | md5 | 프레임 |
|---|---|---|---|---|
| 480p(trial) | **2분 4초**(기준 ≤ 180초) | 1,570,171 B | `dd1fb5b5360e0fd2db5db9a1085dedb4` | 456 |
| 720p(final) | **4분 17초**(기준 ≤ 10분, 렌더 248.9초) | 2,983,730 B | `6486ed5d55a0ddf924db4c8fb94c48a9` | 456, 19.0초, 1280×720 |

mp4 미커밋. `sketch_globe_sheet.jpg`(7컷)·`sketch_provenance.json`(final) 커밋.
provenance: kind `missile_globe`, checks hard 0 · warning 0, `numbers_computed` 6(수평선 거리 3 · 고도 3, 식·입력), `numbers_shown`(발표값·sensor 개념값·지구 반지름 상수).

## 5. 테스트

`FONTCONFIG_FILE` 표준 설정, S0 §0.2 자산:

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S1 끝 | 1349 | 0 | 0 | 0 |
| S2 끝 | **1363** | **0** | **0** | 0 |

- 새 테스트 14개(요구 ≥ 10, `tests/test_sketch_globe.py`): to_local 거리 보존(k = 1·80, 10점 < 1 m), 큰 k 평면 수렴, 가림(대척점), 볼륨 경계(방위·거리·고각 안/밖),
  업 벡터 연속, SK-C1(3D) 양성·음성(선형 키프레임), SK-H6 양성·음성 2(주석 없음 / 값 조작·주석 빠진 프레임), 포맷(레이더 개념값·상수), 교차 전환 합성,
  프레임 렌더 provenance, 이음새 회귀(≤ `checks.seam_px`, 두 해상도), el_deg 범위 거부.
- 커밋 4faf90b 메시지의 "테스트 15" 는 오기 — 그 시점 13개, 7a550ad 이음새 1개 더해 14개.
- 바뀐 옛 테스트 1: `test_sketch_missile.CliTest` 의 "`--globe` 종료 코드 2(이식 전)" 단정 삭제(이제 동작). 테스트 수 변화 없음.
- P2 삭제: `globe3d.py`(테스트 없음). 기준 = 1349 − 0 + 14 = 1363.
