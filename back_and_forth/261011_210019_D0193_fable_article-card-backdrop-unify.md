---
id: D-0193
from: fable
to: opus
kind: directive
responds_to: []
phase: "P1-6"
version: v5.21.7
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 4 — 기사 카드 배경 통일(같은 재렌더에 포함)

사용자 원문: "이건 기사 조판의 배경이 흰색인 문제. 큰 문제는 아니나 통일감 문제가 있음" (113초 부근, `docs/handoff/reports/phaseP1/user_feedback/113s_article_white.jpg`).

## 감독 진단
- 같은 영상 안에서 기사 카드 배경이 두 가지다. 160·260초 등은 어두운 무대, 67·113초는 `article_card.press_fallback` 블러 무대가 light 지도를 흐려 **거의 흰색**이 된다.
- 테마가 light 라서 생긴 차이로 보인다. 카드 조판 자체(글자·막대)는 같다.

## 지시(결정, Fable)
- 프레스 사진이 없는 기사·인용 카드의 무대를 **한 가지로 통일**한다. 기준은 이 영상에서 다수인 어두운 무대(160·260초와 같은 모습)다. 지도 테마와 무관하게 같은 모습.
- 규칙 키 하나로 정하고(P3), "한 영상 안 기사 카드 무대 종류 1개" 를 checks 에 넣는다(warning 이상, Opus 가 hard 가능하면 hard).
- dark 골든에 기사 카드가 있으면 그 컷 변화 여부를 보고한다. 바뀌면 결정 요청.
- D-0191·D-0192 와 같은 재렌더에 넣는다. 전/후 크롭에 67·113초 추가.
