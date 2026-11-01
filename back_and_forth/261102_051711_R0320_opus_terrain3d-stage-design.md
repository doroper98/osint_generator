---
id: R-0320
from: opus
to: fable
kind: decision_request
responds_to: [D-0608, D717]
phase: "E9"
version: v7.4.0
commit: HEAD
status: needs_decision
---

# terrain3d 무대 등록 설계(구현 전) — 결정 넷

지금 terrain3d 는 스케치 전용입니다(`sketch/war/terrain3d.py` + `tools/terrain3d`, rules `registries.stages_planned`).
본편 `engine.render` 경로에 올리는 설계를 먼저 올립니다. 결정을 받은 뒤 구현합니다.

## 1. 구조(제안)

두 단계로 나눕니다. 3D 는 미리 렌더하고, 엔진이 그 위를 합성합니다.

- ① 준비: `python -m engine.terrain3d_prep projects/{pid}`.
  - direction 의 terrain3d 숏마다 scene.json 을 만들고 three.js 로 프레임을 미리 렌더합니다.
  - 결과는 `prev/terrain3d/<숏 id>/frame_%05d.png` 와 manifest(scene 해시·three.js 판·DEM 티어·프레임 수)입니다.
  - geo.prep 와 같은 자리입니다. 오케스트레이터는 어댑터로 부르기만 합니다(P1).
- ② 무대: `engine/stage_terrain3d.py: Terrain3DStage`.
  - `render_base` 는 그 시각 프레임을 깝니다. manifest 해시가 지금 direction 과 다르면 오류입니다(옛 프레임 재사용 금지, P6).
  - `STAGE_CLASSES` 와 `registries.stages` 에 함께 올리고 `stages_planned` 에서 뺍니다(P10).
- 같은 세계는 지금 스케치와 같습니다.
  - 텍스처 = 같은 영역 `MercatorStage.base_image`(relief).
  - 높이 = geo.prep Terrarium 티어.
  - 부대 = 진영 색 면 + 병종 픽토그램.

## 2. 결정 요청

① **글자를 누가 그리나** — 지금 스케치는 브라우저 canvas 가 지명·부대 이름을 그립니다.
- (가, 추천) three.js 는 글자 없이 렌더하고, 프레임마다 라벨 화면 좌표만 manifest 에 냅니다. 엔진이 `engine.typography` 로 그립니다.
  - 사실 텍스트는 코드 렌더라는 원칙(C9)과 같은 글꼴·후광이 됩니다.
  - map_contrast·label_collision 이 그대로 돕니다.
- (나) 지금처럼 브라우저가 그립니다. 엔진 검사가 글자를 보지 못합니다.

② **골든 방식** — 소프트웨어 WebGL(SwiftShader) 출력은 같은 기계에서 같지만, Chromium 판이 바뀌면 화소가 달라질 수 있습니다.
- (가, 추천) 둘로 나눕니다.
  - 합성 골든 = 미리 렌더한 프레임을 fixture 로 고정하고, 엔진 합성 25컷 md5 를 비교합니다(지금 골든과 같은 엄격도).
  - 3D 렌더 시험 = 같은 scene 으로 다시 렌더해 평균 화소 차가 rules 상한 이하인지 봅니다(slow 마커).
- (나) 3D 프레임까지 md5 로 고정합니다. Chromium 갱신 때마다 골든을 다시 찍어야 합니다.

③ **mercator ↔ terrain3d 넘어가기**
- (가, 추천) 이어 찍기. 3D 카메라가 위에서 내려다보는 고도각 90°, 같은 화면 폭에서 시작해 rules 고도각까지 기울입니다. 나올 때는 반대입니다.
  - 첫 프레임이 직전 2D 화면과 같은 그림이어야 합니다. 시험은 경계 프레임 화소 차로 겁니다.
  - camera_continuity 는 terrain3d 성분(방위·고도각·log 반경)을 같은 임계로 잽니다. 성분은 rules `shot_grammar.camera_speed.stages.terrain3d` 에 둡니다.
- (나) 컷(암전)으로 넘어갑니다. 구현은 쉽습니다. 다만 "지도 위에서 사건을 따라가는 카메라"(C0 기준 작품)와 멀어집니다.

④ **첫 등록 범위** — terrain3d 위에 올릴 수 있는 이벤트를 정합니다.
- (가, 추천) 부대(unit)·지명(marker)·강·날짜 뱃지·자막·카드(화면 고정 아일랜드)만 허용합니다. 3D 휘장은 진영 휘장(`BadgeEvent.emblem` 과 같은 재현 키·같은 권리 검사)을 부대 위 세운 판으로 넣습니다.
- 화살표(route)·포위망은 첫 판에 넣지 않습니다. 넣지 않은 이벤트를 terrain3d 숏에 쓰면 오류입니다(레지스트리 `stages` 칸, P10). 조용히 빼지 않습니다.
- (나) 화살표까지 한 번에 넣습니다. 3D 지표 위 곡선이라 품이 큽니다.

## 3. 검사 적용표(구현 때 provenance 에 남김)

| 검사 | terrain3d |
|---|---|
| map_contrast·label_collision·subtitle_overlap | 적용(① 가 기준) |
| camera_continuity·camera_speed | terrain3d 성분으로 적용 |
| route_frame·sea_only_frame·static_camera | 2D View 기준이라 그대로는 안 됩니다. 해당 없음 사유를 checks 결과에 적습니다(빈 통과로 두지 않음) |
| element_hold·media_overlap | 적용 |

## 4. 다음

- 결정을 받으면 순서는 이렇습니다: 레지스트리·무대 클래스 → 준비 CLI → 프리뷰 예제(`tests/fixtures/preview/war/terrain3d.yaml`) → 골든 → anti_inertia 시험.
- 그동안 W5 디자인 시트(`tools/design_sheet.py war_history`)를 먼저 만들겠습니다.
