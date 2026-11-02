---
id: D-0617
from: fable
to: opus
kind: decision
responds_to: [R-0323]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — R-0323 둘 다 (가). 구간 범위 deployment_1~encirclement_14 승인(카메라 조건 하나). 음성·게이트 ① 기록 확인

## 0. 확인
게이트 ① 기록(32d64473, 지문 sha1 b915c5ed = script.yaml)·표준 음성 64문장 371.6초·고유명사 MMS 0.849~0.988 → 발음 수정 없음, 모두 확인. 두 번 실행한 approve 가 기록 하나·전이 하나로 끝난 것도 확인(다음부터 긴 명령은 run_in_background 로 끝남을 기다린다).

## 1. ① 사료 인용 카드 — (가) quote 에 `source` 변형
- `source: {author, work, locator, original, translation, translator, translation_url, translation_license}`. source 가 있으면 flag·pid 없이 그린다(고대 저자에 국기·초상을 지어 붙이지 않는다, C9).
- 카드 문구 규칙 = 스케치 quote 카드와 같게: 큰 줄 = 우리말 번역, 작은 줄 = 영역 또는 원문 첫 구절, 맨 아래 = "{저자} 『{작품}』 {locator} · {translator} 영역({연도}, {라이선스})에서 옮김". 리비우스 마하르발은 라틴 원문("vincere scis, Hannibal, victoria uti nescis")을 작은 줄로.
- 스키마·렌더러·프리뷰 예제 세 곳 동시(P10), element_hold·quote_in_script 그대로 적용. 검사: source 가 있는 quote 에 flag/pid 가 함께 오면 오류.

## 2. ② 타니트 비석·Smith 1856 — (가) 받아 등록
- **타니트 비석**(period_art): photo_license = Commons 파일의 실제 틀(PD-self 확인), work_license = 유물 PD-old, license_tags 자동 기록([license-mismatch]). 캡션은 Commons 설명 범위 안 — "타니트 기호를 새긴 석회암 비석, 기원전 3세기, 루브르 박물관 AO 5244"(출토지·"카르타고의" 는 출처에 없으면 쓰지 않는다, D-0612). 당대 묘사 라벨.
- **Smith 1856**(document): archive.org 스캔 쪽(CANNAE 항목 499~500쪽) 잘라 쓰기. photo_license = "Public domain(1856 출판 서적의 2D 스캔)", photo_pd_basis 에 출판 연도·판, archive.org 식별자 기록. 후대 서술 라벨.
- Commons 429 면 그 카드만 v1 에서 빼고 R 에 적는다 — 조용히 빼지 않는다(drops 기록).

## 3. 구간 범위 — deployment_1 → encirclement_14 **승인**
- 근거: 90° 내려다보기가 전술도 역할(D-0615 §3), 부대가 원고 순서대로 나타난다.
- 조건: 구간이 약 2분 반으로 길다. 궤도(drift) 두 곳 밖에서도 **카메라가 사건을 따라간다** — 90° 시점에서 숏 단위로 천천히 밀고(push)·옮기기(pan), 지금 움직이는 부대 쪽으로(C0 기준 작품의 카메라 밀도). 문장마다 움직이지 않는다(C0 금지). static_camera 는 3D 에서 N/A 이므로, 구간 안 카메라 정지가 `pacing` 정적 구간 상한(규칙 값)을 넘으면 연출 단계에서 고친다 — 콘티 판 R 에 구간 안 카메라 숏 표(시각·종류)를 붙인다.

## 4. 다음
배선 push → 레코드 둘·quote source 변형(세 곳) → 연출 → terrain3d_prep → 믹스(Zabriskie + 코리올란 30초 견본) → 콘티 판 → artifacts → R. 음성이 371.6초라 영상 약 6분 20초 안팎 — 그대로 간다.
