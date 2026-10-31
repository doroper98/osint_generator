---
id: R-0306
from: opus
to: fable
kind: progress
responds_to: [D-0330]
phase: "E4"
version: v7.4.0
commit: 2f7c8e24
status: awaiting_user
---

# 무대 조판 정본으로 네 요소 컷 + 승인 프레임 재렌더(손실 A, UF-204)

## 1. 컷(artifacts `artifacts/econ-template-2026` 2c0ef7f, 폴더 `t2_stage_v3/`)
- `stage/p_0015.50`: 승인 프레임 재렌더다. 손실 막대 −3.1 = A(down 과 바탕을 섞은 면), 원고 "약 23달러에서".
- `guidance/sheet.jpg`(대표 p_0016.50): 열 안은 옅은 몸통(0→16) + 15~16 띠 + 시장 예상 점·획이다. 테두리는 없다.
  - 인셋은 키운 열 + 직접 라벨("가이던스 15~16"·"시장 예상 17.1"·"예상 대비 -2.1 ~ -1.1") + 짧은 이름 하나다.
- `slope/sheet.jpg`(대표 p_0011.50): 삼성 부문 매출 1년 전 → 지금, 값 그대로(C2)다. DS 가 accent, 라벨은 리더선이다.
- `dumbbell/sheet.jpg`(대표 p_0012.00): accent 가 문장마다 파운드리 → DC → 없음으로 옮겨 간다. PC 감소 점은 흐리게, 글자는 잉크다.
- `diverging/sheet.jpg`(대표 p_0013.00): PC −5 % 막대는 A 면이다.

## 2. 조판 변경(미등록 패치 `t2_stage_v3/econ_sketch_v10.patch`)
- 인셋은 머리 줄·캡션·테두리 없이 짧은 이름 하나(연출 title)다. 모서리 0, 바탕은 card_deep 이다.
- 가이던스 그림은 무대 표면에서 테두리를 쓰지 않는다. 몸통은 사다리 가장 옅은 면이고 범위는 진한 띠다.
- 감소 항목의 글자는 잉크다. 면만 흐리게 둔다. ink_light 판에서 PC 글자가 바탕에 묻혔던 것을 고쳤다.
- `bars.negative_fill: muted_fill`(UF-204). ink_light·neg_ink_step 은 대안 키로 남겼다. T3 에서 쓰지 않는 쪽을 지운다(P2).

## 3. 원고
- 네 스케치 원고를 대상만 말하도록 다시 썼다. "~보겠습니다" 화면 해설을 모두 뺐고 금지어 린트를 통과했다.

## 4. 다음
- 컷 판정 뒤 T3 한 커밋이다. 레지스트리·렌더러·프리뷰 예제 세 곳을 함께 바꾼다.
  - 르포 카드 코드는 이미 지웠다. princess 기본값을 지우고 surface: stage·noturno 를 경제 기본으로 둔다.
  - 정직성 검사에서 detail 층·보조 계열을 따로 센다. 분기 린트(quarter_of·파생 레코드)와 [grid-text-cross] 도 넣는다.
- 작업 위치를 옮겼다. 스케치 worktree 는 이제 `/home/user/econ_work/wt` 다(이전 임시 폴더 사용 중지).
