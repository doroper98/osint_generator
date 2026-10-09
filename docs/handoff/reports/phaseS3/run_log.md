<!--
tier: 3
last_synced_with: v5.9.0
ssot_for: [phaseS3-run-log]
depends_on: [back_and_forth/261010_010859_D0145_fable_s2-review-pass-s3-campaign-kickoff.md, back_and_forth/261010_011843_D0146_fable_decision-pocket-sliver-ratio-sk-g2.md, rules/video_rules.yaml, sketch/campaign/, sketch/common/svg_georef.py]
last_review: 2026-10-10
-->

# Phase S3 실행 기록 — 전황 작전도 이식 (v5.9.0)

이 단계의 지침은 D-0145(S3 시작)와 D-0146(SK-G2 미세 조각 허용치 A)입니다. 대상은 천왕성 작전 검토본(4d9dc65 `projects/uranus_sketch/uranus_sketch.py`·`prep_uranus.py`)입니다.

## 0. 컨테이너 준비

S0 §0·§0.2 와 같은 컨테이너를 썼습니다. S2 와 다른 점만 적습니다.
- 기준 프레임은 S2 와 같은 `git worktree`(4d9dc65)에서 뽑았습니다. 추적하지 않는 자산은 심볼릭 링크로 연결했습니다. 추가한 링크는 `projects/uranus_sketch/assets`(`python -m geo.prep projects/uranus_sketch` 산출) 하나입니다.
- 기준 프레임과 새 프레임 모두 `FONTCONFIG_FILE` 표준 설정으로 렌더했습니다.

## 1. 기준 프레임과 비교 (D-0145 §0 — 결함 수정 없음)

옛 `uranus_sketch.py --frames 11.5,20,30.5,38.5,42,51,55.5`(720p)의 결과는 `ref/`(PNG, 미커밋)와 `ref_sheet.jpg` 에 있습니다.
새 `python -m sketch.campaign projects/uranus_sketch --res final --frames …` 은 같은 7시각으로 렌더했습니다. 결과는 `compare_sheet.jpg` 입니다(좌 옛 / 우 새).
HEAD(56fc311)에서 다시 렌더해 재확인했습니다.

| t(초) | 다른 픽셀 비율 | 최대 채널 차 |
|---|---|---|
| 11.5 | 0.000 % | 0 |
| 20.0 | 0.000 % | 0 |
| 30.5 | 0.000 % | 0 |
| 38.5 | 0.000 % | 0 |
| 42.0 | 0.000 % | 0 |
| 51.0 | 0.000 % | 0 |
| 55.5 | 0.000 % | 0 |

7컷 모두 픽셀 동일합니다. 수치는 모두 `rules sketch.campaign`(원본 리터럴, 설계 px 480p)으로 옮겼습니다. 사실·연출은 `projects/uranus_sketch/sketch.yaml` 에 있습니다. 강 색은 RGB 그대로입니다(D138).

### 원본에 있었지만 옮기지 않은 것
- `FRONT_GROUPS`(소련 전선군 이름 3개·좌표·등장 시각)는 원본에 정의만 있고 아무 데서도 쓰지 않았습니다(`grep` 1회 = 정의 줄). 그래서 그려지지 않았습니다. spec·규칙에 옮기지 않았고, 화면 변화도 없습니다.

## 2. 정합 (SK-G1, `sketch/common/svg_georef.py`)

- 원본 `prep_uranus.py` 를 일반화했습니다. spec `fronts.style_map`(색·굵기·점선 → 층·편)과 `fronts.graticule`(눈금 색·굵기, 경도 42~44°E·위도 50~48°N)이 입력입니다.
- 눈금 교차점 9개로 2차 다항 최소제곱을 합니다. 잔차는 경도 0.008448°, 위도 0.004531°, 최대 **0.0084°** 로 임계 `checks.georef_residual_deg` 0.01 이하입니다.
- 세로·가로 눈금선 수가 spec 과 다르면 정합하지 않고 "SK-G1 눈금선…" 오류로 멈춥니다. 테스트로 음성을 확인했습니다.
- `python -m sketch.campaign.prep_georef projects/uranus_sketch` 의 결과 `fronts.json` 은 `layers`·`rivers` 가 옛 `uranus.json` 과 같습니다. 테스트는 저장소 `fronts.json` 과 다시 정합한 결과가 같다고 단정합니다.
- **도시 검산은 R-0183 답을 기다리고 있습니다.** 칼라치 0.0348° 는 통과하고, 스탈린그라드 0.0645° 는 지도 기호를 볼가강 기슭에 찍은 배치 차이입니다. 이 임계 하나만 막혀 있습니다.

## 3. 포위망 (SK-G2, D-0146)

- 포위망은 spec `pockets[].build` 레시피(조각 참조, 점, `lon_min`/`lon_min_of`, `start_near`, `reverse`)로 만듭니다. 테스트는 두 포위망이 4d9dc65 `pocket_1123`·`pocket_1130` 식과 **배열까지 같다**고 단정합니다.
- 검토본 다각형 두 개에 미세 자기 교차 조각이 1개씩 있습니다. 위치는 같은 점 **(44.669, 48.918)** 이고, 넓이는 5.05e-06 deg²(전체의 1.3e-05, 2.6e-05)입니다.
- 둘 다 `checks.pocket_sliver_ratio` 1e-3 이하라 warning 으로만 기록합니다. 그리기는 검토본 레시피 그대로이고, valid 로 고친 다각형은 쓰지 않습니다(D-0146 A).
- 이 점은 "도시 점(44.67, 48.92)과 북쪽 전선이 만나는 곳" 후보입니다. **본편에 등록할 때 레시피를 다듬어야 합니다.**
- 나비 모양 레시피와 빈 다각형은 hard 로 막힙니다(테스트).

## 4. 검사 실측

| 검사 | 결과 | 비고 |
|---|---|---|
| SK-H1 | hard 0 | 화면 문자열의 단위 숫자 = 포맷터만. 음성: 태그에 "약 300km" → hard |
| SK-G3 | hard 0 | 제대 XXXX/XXX/XX·병과 inf/arm/cav 외 값 → hard |
| SK-G1 | 잔차 0.0084° | §2 |
| SK-G2 | warning 2 | §3 |
| SK-H5 | hard 0 | 아래 정의 |
| SK-C1 | hard 0 | 1차·2차 차분(D-0141) |
| SK-R1 | hard 0 | 참고 SVG = 프로젝트 `RIGHTS.json`(D139), CC BY 3.0. 비상업 라이선스·항목 없음 → hard |
| SK-C2 | warning 1 | 아래 |

**SK-H5 창 정의.** 개략 층(전선 전부·부대 위치)은 화면이 열린 뒤부터 엔딩 직전까지 보입니다. 따라서 '개략'(`checks.approx_word`)이 든 출처 줄이 `fade.open_sec`(1.0초)부터 엔딩 시작 − `checks.approx_note_end_gap_sec`(53.0 − 1.0 = 52.0초)까지 이어져야 합니다. 엔딩 자료(`sources`)에도 '개략'이 있어야 합니다.
uranus spec 의 출처 줄은 1.0~52.0초라 경계에서 통과합니다. 문구에서 '개략'을 빼거나 중간에 끝나면 hard 입니다(테스트).

**SK-C2(warning) — 라벨 예약 상자 겹침 308프레임(45.17~57.96초).**
- 겹치는 것은 집게 태그 예약 상자(소베츠키, 폭 220)와 독일 제4기갑군 부호 상자입니다.
- 원본 4d9dc65 도 집게 상자를 태그가 사라진 뒤(45.6초 이후)까지 계속 예약합니다. 이식은 이 동작 그대로입니다.
- 눈에 보이는 겹침은 태그가 흐려지는 45.17~45.6초뿐입니다. 그 뒤는 보이지 않는 예약끼리의 겹침입니다.
- 예약을 태그 알파에 맞추면 지명 라벨 배치가 바뀌어 기준 프레임과 달라집니다. 그래서 S3 에서는 고치지 않았습니다. 본편 등록 때 고칠 후보입니다.

## 5. 전편 렌더

| 프로파일 | 시간 | mp4 | md5 | 프레임 |
|---|---|---|---|---|
| 720p(final) | **93초**(렌더 87.5초) | 11,216,738 B | `5e017e4a0c06556900e950ec530400cd` | 1392, 58.0초, 1280×720 |

mp4 는 커밋하지 않았습니다. `sketch_campaign_sheet.jpg` 와 `sketch_provenance.json`(final)은 커밋했습니다.
provenance 요약입니다.
- kind `campaign`, checks hard 0, warning 3(SK-G2 2, SK-C2 1).
- `data_files`: 참고 SVG·fronts.json(sha1, 출처, CC BY 3.0).
- `approximations`: 전선 정합 잔차와 부대·화살표 개략.
- `features_drawn`: 전선 3층, 포위망 2, 화살표, 부대 XXXX·XXX, 집게, 태그, 범례.

## 6. 삭제 (P2)

- `projects/uranus_sketch/uranus_sketch.py`·`prep_uranus.py`·`uranus.json` 을 지웠습니다. `fronts.json` 이 `uranus.json` 을 대체합니다.
- `tests/anti_inertia/test_no_code_direction.py` 에 "`projects/**/*.py` 0" 단정(`test_no_py_in_projects`)을 넣었습니다.
- `RIGHTS.json` 과 `.gitignore` 의 재생성 안내 문구를 새 CLI 로 바꿨습니다.

## 7. 테스트

`FONTCONFIG_FILE` 표준 설정과 S0 §0.2 자산으로 돌렸습니다.

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S2 끝 | 1363 | 0 | 0 | 0 |
| S3 끝 | **1378** | **0** | **0** | 0 |

- 새 테스트는 `tests/test_sketch_campaign.py` 의 14개입니다(요구 ≥ 12).
  - 정합: 잔차, 묶음 수와 저장소 데이터 동일, 눈금선 부족 오류.
  - 포위망: 검토본 통과와 warning 2, 자기 교차 레시피·빈 다각형 hard, 레시피 = 4d9dc65 식.
  - spec 검사: 제대·병과 오타(G3), H5 양성·음성 2, H1 음성, R1 음성 2.
  - 그리기: 부대 예약 상자, 화살표 성장 단조, 전선 이중선 오프셋 방향.
  - 프레임 렌더 provenance.
- `test_no_code_direction` 에 1개(`test_no_py_in_projects`)를 더했습니다.
- 지운 옛 스크립트에는 테스트가 없었습니다. 기준은 1363 + 14 + 1 = 1378 입니다. 실측 1378 passed(22분 53초).
