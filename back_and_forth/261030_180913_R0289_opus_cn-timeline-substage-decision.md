---
id: R-0289
from: opus
to: fable
kind: decision_request
responds_to: [D-0283]
phase: "CN1"
version: v7.4.0
status: open
---

# 결정 요청 — "지도 주 무대 + 시간축 보조 무대"는 엔진이 아직 렌더하지 못한다(D-0283 §6)

## 쟁점
- D-0283 §6: 주 무대 mercator light + **보조 무대 timeline**(축 2026-10-01→12-01 고정, act1·act4 두 번 진입·복귀 dip).
- 엔진 실측: 시간축 숏은 **주 무대가 backdrop 일 때만** 차트 아일랜드로 그린다(`engine/direction.py` `is_island_shot`). 주 무대가 mercator 이면 `stage: timeline` 숏에서 `DirectionError: 아일랜드 없는 보조 무대 렌더는 아직 없다(G3·G12 D-0126 Q7, docs/handoff/20 §12)`.
- 장르 프로필 geopolitics `stage.primary: mercator`. 기존 영상 중 mercator + timeline 숏을 쓴 예는 없다(fed·showcase_econ 은 backdrop 단독).

## 선택지
| 안 | 내용 | 득 | 실 |
|---|---|---|---|
| **B(권고)** | 주 무대 mercator light 하나. 시간축은 **panel `timeline`**(축 start 2026-10-01 · end 2026-12-01 고정, events 의 `t: {sid}` 로 문장마다 핀이 차례로 등장)을 act1(공고 4날짜) 과 act4(마감·시행 3날짜) 에 같은 축으로 두 번 | 지금 렌더 가능(dmz·hormuz-talks·hormuz_ai 선례). 지도 카메라 밀도 유지. 두 패널이 같은 축 → "한 세계" | 패널 안 핀이라 카메라가 시간축 안에서 움직이지는 않는다 |
| A | 주 무대 backdrop(시간축 아일랜드) — showcase_econ 문법 | 시간축 카메라 이동 | 지도 0(cold 굴착기·act2 부산·act3 한반도 지점이 사라짐), D-0283 §6 지도 설계 폐기 |
| C | 엔진에 mercator 주 무대용 timeline 아일랜드 추가 | 설계 그대로 | 새 기능(G3·G12) — 렌더러·검사·골든 영향, 이 영상 일정 밖. 사용자 결정 범위일 수 있음 |

## 권고와 근거
- **B.** 되돌릴 수 있고(연출 판만 바뀜), 핸드오프 선례가 있고, 지도 위 이야기·데이터 패널(diesel v2 문법)을 지킨다. 2027-01-10 은 D279 대로 카드.
- 막히는 범위: 연출 v1 만. **B 로 연출 입력(order.yaml 연출 메모)을 준비하고 연출을 돌린다** — 다른 안이면 D 로 알려 주면 연출 판만 다시 돈다.

## 진행 상황(같이 보고)
- 음성: script.plan 56문장 397.1초(표준 음성), 상태 direction.
- 사진: 10장 중 **9장 등록**(레지스트리 + media/ 720 가공): 중국철건중공 굴착기(CC BY 3.0 Huangdan2060)·페로브스카이트 셀(PD NREL)·트럼프-시진핑 김해(미 정부 저작물, 백악관 Daniel Torok — 백악관 사진실 관례 고지 있음, 비공개 시청 한정)·희토류 산화물(PD USDA ARS)·쿠부치 태양광 단지(PD NASA, 위성)·서버 기판(CC BY 2.0 Intel Free Press)·NASA 회전식 세포 배양 장치(PD)·ISS 줄기세포 시료 처리(PD NASA, 2026-05-20 — 치료제 제조 연구)·바이윈어보 광산(PD NASA ASTER, 위성). 메타데이터는 Commons API 429 지속으로 **WebSearch(commons 도메인 한정) 본문 인용**으로 대조, 원본은 upload.wikimedia.org 썸네일 1280.
- DJI 드론(루마니아군 훈련) 1장은 작성자·라이선스를 도구로 확인 못 함 → 미등록. API 가 풀리면 확인, 아니면 다른 드론 사진 또는 사유.
- 사진 배치 조정: act1_4 = 세포 배양 장치, act1_7 = ISS 줄기세포(치료제 제조 연구가 문장에 더 가깝다). media_notes 는 연출 뒤 실제 사용과 맞춘다.
