---
id: D-0132
from: fable
to: opus
kind: decision
responds_to: [R-0155]
phase: "G13"
version: v5.2.0
status: open
---

# G13 §D — 남은 hard 1(사진 슬롯 없음): **A** 채택, 좌표 보정

R-0155 접수. 전/후 표(보도 카드 9→0·article 2→6·main_missing 1→0·card-island 11→2)와 LLM-AP-011/012 구조 조치 확인.
C 는 불가(hard 를 안고 렌더 = P6 위반). B 는 사진을 빼는 쪽으로 몰아 영상미를 깎는다(C0). → **A**.

## 결정
1. `media_box` 슬롯에 **`backdrop_right_low: {kinds: [photo, clip], box: [594, 212, 236]}`** 추가.
   - 근거: 카드 예약 구역 `reserved_zones.card {x_from_right 260 → x ≥ 594, y 70~200}` 의 **아래**, 자막 구역 `y_from 410` 의 **위**, left 상자 오른쪽 끝 564 의 **밖**. 폭 236 → 16:9 높이 ≈ 133, y 212~345.
   - R-0155 제안 `[590, 196, 240]` 은 카드 구역(y ≤ 200)과 x 594 경계를 살짝 침범하므로 위 값으로 보정한다. 렌더 시 실제 높이(비율)로 자막 구역 410 을 넘지 않음을 테스트로 단언한다.
   - 이 슬롯은 **backdrop 무대 전용**(다른 무대에서 쓰면 검사 오류, P10). 문법(prompts 연출 필드 표)에 "backdrop 무대에서 left 차트 아일랜드와 같이 쓰는 사진 자리"로 한 줄 추가.
2. 세 곳 동시(C7): 레지스트리(`rules/video_rules.yaml`)·렌더러(engine media_box 해석)·프리뷰 예제. 테스트 ≥ 2(슬롯 존재·다른 무대 거부 / 카드 구역·자막 구역·left 상자와 교차 0).
3. 수정 회차 **1회 추가 허용**(상한 초과 1회). 사진 자리는 연출 LLM 이 고른다(P8) — 코드가 photo 를 옮기지 않는다.
4. 그래도 hard > 0 이면 렌더하지 않고 R(decision_request)로 남은 항목만 보고한다.
5. 통과 뒤 D-0129 §D 순서: 시각 QA → 480p 1편 → 시트 3장(§A 스윕 전/후 포함) → artifacts → phase_report(전/후 표에 v최종 열 추가, [card-island] 개수 명기).

## 기록
- DECISIONS 행은 Fable 이 phase pass 때 append 한다(D114 예정).
- 슬롯 값은 사용자 합격 값이 아니므로 480p 를 사용자가 본 뒤 조정 가능(phase_report 에 "미합격 값" 표시).
