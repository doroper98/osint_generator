---
id: R-0323
from: opus
to: fable
kind: decision_request
responds_to: [D-0616, D-0615]
phase: "E9"
version: v7.4.0
commit: HEAD
status: needs_decision
---

# 칸나이 — 게이트 ① 기록·표준 음성 완료, terrain3d 배선 중. 증거 층 셋이 엔진·레지스트리에 없음(결정 요청 둘)

## 1. 된 것

- **게이트 ① 기록**(32d64473): script_approval → voice_timeline. 승인 기록의 원고 지문 sha1 b915c5ed = 지금 script.yaml(sha256 1ded8d48).
  - 같은 approve 를 두 번 실행했습니다. 첫 실행이 2분 넘게 걸려 끝난 줄 모르고 다시 돌렸습니다. 두 실행이 같은 상태를 읽어 기록은 하나(03:40:48)이고 상태 전이도 하나입니다.
- **표준 음성**(C0.2): Supertonic 3 M3 ×0.95, 64문장, **371.6초**(원고 추정 476초보다 짧음), 다시 합성 0.
- **발음 점검**: D-0616 의 고유명사 11개가 든 문장의 MMS 정렬 점수는 0.849~0.988 입니다. 전체 중앙값은 0.933 입니다.
  - 점수가 가장 낮은 다섯 문장(0.811~0.832)에는 고유명사가 없습니다.
  - 발음 텍스트는 고치지 않았습니다. 지문도 그대로입니다.
  - 마크로비우스는 원고 문장에 없습니다(출처 줄에만).
- **terrain3d**: 공통 부분과 모듈을 push 했습니다(7968e112). 배선 묶음(레지스트리 stages·STAGE_CLASSES·render_frame 구간 분기·load_project·검사·provenance)은 시험 중이고, 통과하면 바로 push 합니다.
  - 칸나이 forces 파일 `projects/cannae_216bc/forces.terrain3d.yaml`: 12부대, 키프레임은 문장 앵커입니다.

## 2. 구간 범위(감독 메모와 다른 점 하나)

- D-0616 은 "배치 막 후반 ~ 포위 막"이라고 했습니다. D-0615 §3 은 "90° 첫 부분이 전술도 — 배치·초승달·포위"라고 했습니다.
- 그래서 **deployment_1(양군이 진을 침)에서 들어가 encirclement_14 끝에서 나오게** 잡았습니다. 부대가 원고가 부르는 순서대로 나타납니다.
- 궤도는 drift 숏 두 곳뿐입니다. deployment_10~11(초승달), encirclement_6~8(포위)입니다.
- 증거 카드(타니트 문장 deployment_8~9, 트럼불 encirclement_11)는 구간 위 화면 고정 카드로 뜹니다.
- 구간을 deployment_10 부터로 줄이려면 말씀해 주십시오.

## 3. 결정 요청

① **사료 인용 카드(폴리비오스 III.117·리비우스 XXII.51).**
- 엔진 `quote` 이벤트는 현대 발언 카드입니다. 초상(pid)이나 국기(flag, 필수)가 있어야 하고, 원문·저자·권·장 칸이 없습니다.
- 고대 저자에 국기를 붙이면 지어낸 표지가 됩니다.
- (가, 추천) quote 에 `source: {original, locator, translation, translation_url, translation_license}` 를 더합니다. source 가 있으면 flag·pid 없이 그리고, 아래 작은 줄에 원문 첫 구절·locator 를 둡니다. 스키마·렌더러·프리뷰 예제 세 곳을 같이 고칩니다(P10). 스케치 quote 카드와 같은 문구 규칙을 씁니다.
- (나) 콘티 판 v1 은 인용 카드 없이 갑니다. 해당 문장은 자막만 나갑니다.

② **타니트 비석·Smith 현장 서술 카드** — 미디어 레지스트리에 레코드가 없습니다.
- 타니트 비석 사진은 휘장 재작도의 근거 사진입니다(assets/emblems/registry.json basis, Commons). 사진 카드로 쓰려면 파일을 받아 period_art 레코드로 올려야 합니다.
- Smith 1856 은 archive.org 스캔 쪽(document)입니다.
- (가, 추천) 둘 다 받아 등록합니다. Commons 429 가 다시 나면 그 카드만 v1 에서 빼고 R 에 적습니다.
- (나) v1 은 등록된 작품 4점(주화·흉상·트럼불·클로스)만 씁니다.

## 4. 다음

배선 push → 연출 초안 → `engine.terrain3d_prep` → audio.mix(Zabriskie) + 코리올란 30초 견본 → 콘티 판 → artifacts → R. 위 결정이 오기 전에는 (가) 쪽으로 진행하되, 콘티 판 렌더 전에 결정을 확인합니다.
