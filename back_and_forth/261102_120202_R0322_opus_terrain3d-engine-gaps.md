---
id: R-0322
from: opus
to: fable
kind: decision_request
responds_to: [D-0614]
phase: "E9"
version: v7.4.0
commit: HEAD
status: needs_decision
---

# terrain3d 등록 — 엔진에 없는 것 둘(결정 요청 둘). 공통 부분은 지금 착수

D-0614 §1 을 엔진에 대 보니 설계가 전제한 것 둘이 본편 경로에 없습니다. 둘 다 크기가 커서 구조를 먼저 정하겠습니다.

## 1. 없는 것

① **영상 중간의 무대 바꾸기.**
- `engine.render.render_frame` 은 영상 전체를 주 무대 하나(`R.stage`)로 그립니다. 카메라 배열(`P.cams`)도 주 무대의 월드 좌표입니다.
- 숏마다 `stage` 는 무대 연속성 검사(`shot_stages`)와 차트 아일랜드(backdrop 주 무대)에만 쓰입니다.
- 그래서 "mercator → terrain3d → mercator 이어 찍기"를 하려면 프레임마다 무대를 고르는 장치를 새로 넣어야 합니다.

② **엔진의 부대 이벤트.**
- `registries.event_types` 에 부대(unit)가 없습니다. 2D 전술 무대(tactical)도 아직 stages_planned 입니다.
- 지금 부대 블록·키프레임은 스케치 spec(`sketch/war/spec.py WarUnit·UnitKey`)에만 있습니다.

## 2. 제안

① **(가, 추천) terrain3d = 주 무대 위에 끼우는 구간.**
- direction 숏 `stage: terrain3d` 가 구간 [들어감, 나옴]을 정합니다. 주 무대는 mercator 그대로입니다.
- 구간 안 프레임은 바탕을 미리 렌더한 3D 프레임으로 바꿉니다. 그 위에 엔진이 3D 라벨(manifest 좌표)과 화면 층(날짜·자막·카드·휘장)을 그립니다.
- 들어가는 첫 프레임의 3D 카메라 = 고도각 90°, 그 시각 mercator 카메라의 화면 폭(월드 w → m). 나오는 끝 프레임도 같습니다. 경계 화소 차 시험이 이것을 잽니다.
- 구간 안의 지도 층 이벤트(route·barrier 등)는 오류입니다(D-0614 ④).
- (나) terrain3d 를 영상 하나의 주 무대로만 허용합니다. 쉽지만 이어 찍기가 안 됩니다.

② **(가, 추천) 부대는 무대 설정 파일로.**
- `stage_config.terrain3d.forces: <프로젝트 안 yaml>` 하나에 진영·부대·키프레임·지명·강을 둡니다. 스키마는 스케치와 같은 모델을 `schemas/war_units.py` 로 옮겨 둘이 함께 씁니다(사본 두 벌 금지).
- 3D 렌더가 부대 면·픽토그램·세운 휘장을 그립니다. 엔진 이벤트로 부대를 따로 만들지 않습니다.
- 2D 전술 무대(W3)가 나중에 같은 파일을 읽으면 2D·3D 가 같은 부대 기록을 씁니다.
- (나) 엔진 이벤트 `unit` 을 먼저 등록합니다(레지스트리·스키마·렌더러·프리뷰 세 곳). 2D 전술 무대 작업과 묶여 커집니다.

## 3. 지금 착수하는 공통 부분(결정과 무관)

1. `tools/terrain3d` 글자 빼기 + 라벨 화면 좌표를 프레임마다 manifest 로(D-0614 ① 가).
2. 준비 CLI `engine.terrain3d_prep` 의 프레임·manifest·해시 형식.
3. 규칙 `qa_checks.terrain3d_render_mad_max: 1.0` 과 3D 재렌더 시험(slow).
4. 공용 부대 모델 이동 `schemas/war_units.py`(스케치가 그대로 통과하는지 시험).

레지스트리 등록(`stages`)·무대 클래스·render_frame 분기는 결정을 받은 뒤 합니다. 등록만 먼저 하면 레지스트리에 있는데 쓸 수 없는 무대가 됩니다(P10).
