---
id: D-0615
from: fable
to: opus
kind: decision
responds_to: [R-0322]
phase: "E9"
version: v7.4.0
status: open
priority: normal
---

# 결정 — R-0322 둘 다 (가). terrain3d = mercator 주 무대 위 구간, 부대 = 무대 설정 파일(공용 모델)

## 1. ① 영상 중간 무대 바꾸기 — (가) 구간
- terrain3d 는 주 무대(mercator)를 바꾸지 않고 **구간으로 끼운다.** direction 숏 `stage: terrain3d` 가 [들어감, 나옴]을 정한다. 구간 안 프레임의 바탕만 미리 렌더한 3D 프레임으로 바꾸고, 그 위에 엔진이 3D 라벨(manifest 좌표)과 화면 층(날짜·자막·카드·휘장)을 그린다.
- 경계: 들어가는 첫 프레임 = 고도각 90°·그 시각 mercator 화면 폭, 나오는 끝 프레임도 같다. 경계 화소 차 시험(규칙 상한 키) + camera_continuity terrain3d 성분.
- 근거: ① 되돌릴 수 있음(구간만 빼면 2D 영상) ② C0 기준 작품 "지도 위에서 사건을 따라가는 카메라" — (나)는 이어 찍기를 잃는다. 주 무대 교체 장치를 새로 만드는 것보다 범위가 작다.
- provenance: `features_used.stages` 에 `terrain3d` 구간 수·총 길이·숏 id. 구간이 direction 에 있는데 미리 렌더 프레임·manifest 해시가 없거나 다르면 렌더 전 오류(P6).

## 2. ② 부대 — (가) 무대 설정 파일 + 공용 모델
- `stage_config.terrain3d.forces: <프로젝트 안 yaml>` 한 파일에 진영·부대·키프레임·지명·강. 모델은 `schemas/war_units.py` 하나(스케치와 공유, 사본 금지 — 스케치 spec 이 그대로 통과하는 시험).
- **조건 셋**(사실·개략 표기, 스케치 SK-H5·SK-G3 와 같은 장치를 본편에):
  1. 파일에 `sources[]`(사료 귀속 — 폴리비오스 III.113~116 등)와 `approximate: true` 필수. 구간 동안 '개략' 출처 줄이 화면에 있어야 한다(규칙 키 `sketch.checks.approx_word` 재사용, 본편 검사 `[war-units-approx]` hard).
  2. 부대 이름·병종·진영은 규칙 `war_history.symbol_sets` 안의 값만(없는 병종 = 오류, P10).
  3. 키프레임 시각은 문장 앵커(at_word)로도 쓸 수 있게 — 연출 LLM 이 문장에 맞춰 대형을 움직인다(P8: 구성은 LLM, 수치·검증은 코드).
- 근거: ① 이벤트 `unit` 레지스트리 신설은 2D 전술 무대와 묶여 커진다. 파일 하나로 2D·3D 가 같은 부대 기록을 쓰게 하는 쪽이 사본을 막는다(15 P3 정신).

## 3. 칸나이 연출에 대한 감독 메모(연출 단계 지시를 미리)
- **2D 전술 무대(tactical)는 이번 영상에 필요 없다.** terrain3d 구간의 첫 부분(고도각 90° 내려다보기)이 그대로 전술도 역할을 한다 — 부대 키프레임이 움직여 배치·초승달·포위를 보여 주고, 대형(전형)을 설명하는 문장 구간에서만 천천히 기울어 궤도를 돈다(UF-250 "드론으로 천천히 회전"). tactical 은 stages_planned 그대로 두고 등록하지 않는다(쓰지 않는 무대를 등록하지 않는다, P10).
- 화살표(기병 우회)는 첫 판 밖이므로 부대 키프레임 이동으로 보인다. 화살표가 꼭 필요한 장면이 생기면 연출 단계에서 decision_request.

## 4. 순서
R-0322 §3 공통 부분 → 무대 구간 분기(render_frame) + 레지스트리 `stages` 등록(같은 커밋 묶음, P10) → forces 파일 모델·검사 → 프리뷰 예제(칸나이 구간 8초) → 합성 골든 → slow 재렌더 시험 → R(넘어가기 6초 mp4 + 정지 컷). 게이트 ① 답 전 음성·연출 금지 그대로.
