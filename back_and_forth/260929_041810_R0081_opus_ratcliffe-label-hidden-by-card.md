---
id: R-0081
from: opus
to: fable
kind: decision_request
responds_to: [D-0067]
phase: "10"
version: v3.6.0
commit: 5317cba
status: awaiting_decision
---

# 결정 요청 — NB23 재실행의 잔여 시각 검수 hard 3(카드 옆 마커 이름표 숨김)

D-0067 확인(A 채택). 작업 1·2 는 워크트리에서 구현·검증 중이고 곧 푸시한다(아래 §4).

## 1. NB23 결과(§0-2 ①~④)
| 항목 | 결과 | 증거 |
|---|---|---|
| ① 원인 | 연출 수정 판(v3)이 카드 `y: 0.56` 을 적었다(비율 뜻). `CardEvent.y` 는 480p 픽셀이라 카드가 y≈1 에 떠 날짜와 겹침. 검사기는 사진·영상만 봤다 | 커밋 `bcaea3c` 메시지 |
| ② checks | 카드·기사·게시물 카드 × 날짜 상자·자막 영역 → `overlap` hard(`[card-over-date]`·`[card-over-subtitle]`, "y 는 480p 픽셀" 안내). Phase 9 v3 연출에 돌리면 **hard 1** 로 잡힘 | `reports/phase10/nb23/ratcliffe_phase9_v3_checks.json` |
| ③ 슬롯 후보 | 날짜 상자 정의를 `engine.hud.date_box()` 하나로(beside_panel 후보·checks 공유). 카드 상자는 `reserved.card_box()` 하나 | 테스트 10(test_phase10_nb23_nb16) |
| ④ 재실행 | 연출가부터 새로 3판: **checks hard 0 · 카드×날짜 0**(세 판 모두). 시각 검수 hard **10 → 6 → 3**, 카드×날짜 지적 0(p_0191.86 해소). 선택 v3 | `reports/phase10/nb23/ratcliffe/nb23_summary.json`, `sheet.jpg` |
| hormuz | 25컷 MAD 0 | `reports/phase10/nb23/hormuz_mad.json` |

## 2. 쟁점
D-0066 §0-2 ④ 는 "시각 검수 hard 0(루프 1회)" 를 요구했다. 선택 v3 에 **hard 3** 이 남았다. 셋 다 같은 종류다.
- p_0054.32 · p_0063.35 · p_0206.38: 우상단 카드 바로 왼쪽의 모스크바 마커 **이름표가 보이지 않는다**(점만 보임).
- 원인: 규칙 `panels.reserved.marker_label_strategy: hide`(D36) — 카드 영역에 걸린 마커 라벨은 카드 알파만큼 흐린다. 설계대로 동작했지만
  검사기(checks)는 이것을 모른다. 그래서 연출 LLM 은 오류를 받지 못하고, 시각 검수만 hard 로 잡는다(NB23 과 같은 구조의 검사기 구멍).
- 카드×날짜(NB23 본건)와는 다른 결함이다.

## 3. 선택지
- **A(권고)**: checks 에 `label_hidden`(hard) 추가 — 마커 라벨이 카드 영역 때문에 흐려진(라벨 알파 < 0.5) 시간이 그 마커 표시 시간의
  `qa_checks.label_hidden_max_ratio`(제안 0.5) 를 넘으면 hard. 연출 LLM 이 오류로 받아 마커·카드 자리를 고친다. 그 뒤 랫클리프를 한 번 더
  재실행(checks hard 0 · 시각 hard 0 목표). 임계는 규칙 값 1개 신설(사람 승인 필요 → 이 요청).
- **B**: Phase 9 D49 와 같이 게이트 ② 사람 판정으로 v3 를 통과시키고 A 는 Phase 11 로 미룬다.
- **C**: 검사기 추가 없이 루프만 한 번 더(loop_max 3 임시). 원인이 검사기 구멍이라 재발 가능성이 높다.

## 4. 막히는 범위와 진행
- 막히는 것: §0-2 ④ 의 "시각 검수 hard 0" 판정, 그리고 작업 7 의 랫클리프 480p 재렌더(어느 판으로 할지).
- 막히지 않는 것(계속): 작업 1 출력 프로파일, 작업 2 장치 변환 렌더(1080p 25컷 축소 MAD 평균 **0.0097**·최대 **0.0178**, 1080p 티어 전 실측,
  k=1 MAD 0), 작업 3 지오 티어(hormuz 1080p 티어 prep 76초 실측), 작업 4~6.
