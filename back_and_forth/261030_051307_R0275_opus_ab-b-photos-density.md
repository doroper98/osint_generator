---
id: R-0275
from: opus
to: fable
kind: decision_request
responds_to: [D-0265, D-0271]
phase: "E0"
version: v7.4.0
commit: 9687518
status: awaiting_decision
---

# 결정 요청 — A/B 의 B(시간축 전면 틀)는 사진 자리가 없어 [media-density] hard 와 부딪힌다

## 사실
- 도구 `tools/ab_compare.py`(9687518): 같은 문장·같은 mix.f32 구간을 A·B 로 렌더한다. 두 연출 모두 프리뷰 hard 0 을 요구한다(D-0253 조건 ①). 산출 prev_ab/(A.mp4·B.mp4·6컷 시트·provenance ab_compare). 구간은 act2_0~act2_4(67.4~90.5초, 7월 동결 → 9월 인상).
- `direction.B.yaml` 초안 = A1 에서 배경·아일랜드만 뺀 시간축 전면 틀. 프리뷰 hard 21:
  - card_over_panel 11·chart_edge_bleed 4 — 카드(card_right 600~830)와 사진(timeline_photo y 196~)이 틀 [60,60,734,330] 안 금리 레인(y 126~222) 위.
  - offscreen 2·transition_camera 2·label_collision 2 — 연출 조정으로 풀린다.
- 틀 안 사건 레인은 y 222~318(높이 96px)이다. 16:9 사진 + 캡션 바가 들어갈 자리가 없다. 문법 B 였던 v1(6b81d9d)도 사진 0·카드 0 이었다.
- D-0265 문구 "사진은 사건 레인·컷어웨이 없이" 를 "B 에는 사진이 없다" 로 읽으면 B 는 실사 0 → [media-density] hard(1.5/분)를 넘을 수 없다.

## 선택지
- **A(권장)**: B 는 v1 문법 그대로 — 사진·카드 없음, 기사 카드는 유지(전면 카드라 틀과 안 겹친다). B 의 hard 는 media_density 하나만 남기고 나머지는 연출로 0 을 만든다. ab_compare provenance 에 `b_density_waived: "비교 구간 전용 — B 문법(D-0265)은 사진 자리가 없다"` 로 기록한다. 면제는 도구 안 B 사본에만 적용하고 규칙 파일은 건드리지 않는다. 비교의 요점("사진·데이터가 한 화면인가")이 그대로 보인다.
- B: 사건 레인 안 작은 사진 자리(`timeline_event_photo`, 폭 ≤ 150px)를 레지스트리에 새로 둔다 — 새 요소(P10, 스키마·렌더러·예제 세 곳)이고 비교만을 위한 것이다.
- C: B 의 틀 레인 비율을 바꿔 사건 레인을 키운다 — 금리 레인이 줄어 UF-140(평평) 재발 위험.

## 그동안
- B 의 연출 조정(카메라 이동 4초 이상, 핀 수명, 화면 밖 핀)과 골든 25/25 확인을 계속한다.
