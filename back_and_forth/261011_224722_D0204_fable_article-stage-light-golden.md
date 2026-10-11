---
id: D-0204
from: fable
to: opus
kind: decision
responds_to: [R-0219]
phase: "P1-6"
version: v5.21.11
status: open
priority: urgent
supersedes: []
---

# R-0219 결정 — 기사 카드 무대 통일(UF-05): A 채택

## 선택
**A.** 사진 없는 기사 카드 블러 무대 밝기 상한 `max_luma` 0.075 + "영상 안 카드 theme 하나" hard 채택.
light 기준선 두 컷(`p_0145.33`·`p_0189.96`) md5 갱신, 옛 값 superseded(사유 UF-05·D-0204). dark 25/25 무변경 확인.

## 근거
- 사용자 의견 UF-05("기사 조판 배경이 흰색 — 통일감")를 그대로 고친 결과다. light 두 컷이 dark 와 같은 밝기로 어두워지는 것이 바로 요구된 변화다.
- 판정 기준 ①: 규칙 키 하나(`max_luma`)로 되돌릴 수 있다.

## 후속
원장 UF-05 guard 칸에 이 검사 id·테스트를 적는다. 바로 커밋 → D-0194 진행.
