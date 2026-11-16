---
id: R-0296
from: opus
to: fable
kind: progress
responds_to: [D-0314]
phase: "E4"
version: v7.4.0
commit: b3691d5c
status: awaiting_user
---

# T2 다층 아일랜드 스케치 3차(D-0314 반영) · 안 A 미반영(Yahoo 429)

## 1. 스케치(artifacts `artifacts/econ-template-2026` 129a38ac, 폴더 `t2_multilayer_v3/`)
- 2차와 같은 7 문장·같은 시각(3.5·8.5·13.0·17.0·21.0·36.5·40.0초). 실제 엔진·실제 레코드.
- ① 손실 부문은 잉크 0.30 채움 + down 윤곽 1.5px 이다(`bars.negative_fill: muted_outline`·`neg_fill_alpha`·`neg_outline_w`). 코랄 채움은 그 순간 accent 부문 하나뿐이다.
  - 13초 컷은 파운드리만 코랄 채움이다. 17초 컷은 DC 가 코랄 채움이고 파운드리는 윤곽이다.
- ② 주가 축 값은 아일랜드 왼쪽 예약 열에 둔다(`plot_left`, `plot_right` 의 거울). 자료와 쌓임은 열 오른쪽부터 그린다. 보조 계열 끝값 판은 접었다(안 B).
- ④ 부문 이름 글자색은 칠(아일랜드 위 합성색)과의 대비로 코드가 고른다. text·바탕 중 큰 쪽이고, 기준은 `bars.label_contrast_min 4.5` 다.
  - 잉크 0.12~0.9 사이 칠은 둘 다 4.5 미만이다(실측 0.78 → 3.88). 이 경우 바탕색 작은 판 위 text 글자로 둔다(판 위 5.3). 판 위도 미달이면 오류다(P6).
  - 사다리 첫 단을 0.92 로 올려 PC 는 판 없이 어두운 글자로 둔다(`stack_ladder [0.92, 0.62, 0.40, 0.26]`).
- 비네팅은 넣지 않았다(감독 정정 확인). 축척은 w 636 한 벌이다. 첫 막대가 왼쪽 축 열에 잘리지 않도록 무대를 2025-04-01 부터로 했다(`[camera-bounds]` 통과).

## 2. 남은 것
- **안 A(주가 2025-07~ 확장) 미반영.** Yahoo chart API 가 429(요청 과다)를 돌려준다. 표준 도구로 30·90·240초 간격 세 번 모두 실패했다.
  - 다른 호스트로 돌아가는 시도는 하지 않았다(봇 차단 우회). 그래서 40초 컷 핀 라벨("실적 발표일 10월 29일")이 아직 주가 선 위에 있다.
  - 다음 세션 첫 작업으로 같은 도구로 다시 받는다. 급변일은 D-0314 ③ 대로 보도 대조가 안 되면 missing 이다.
- `[accent-down-distinct]` warn 은 아직 없다. 검사 추가는 골든 검사 수가 바뀌므로 T3 등록 때 넣는다.
- 정직성 검사 hard 4건(unit-mix·series-limit·units_visible·as_of_visible)이 이어 붙인 쌓임·보조 축을 모른다. 이것도 T3 에서 고친다(R-0295 §2 그대로).

## 3. 다음
- 안 A 데이터를 받아 40초 컷을 마감한다. 이어서 bullet(컨센서스 넷)·덤벨·diverging·slope·가이던스를 각 1컷씩 같은 princess 아일랜드로 그린다.
