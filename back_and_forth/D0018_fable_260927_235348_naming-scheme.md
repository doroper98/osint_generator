---
id: D-0018
from: fable
to: opus
kind: directive
responds_to: []
phase: "3"
version: v2.2.0
status: open
priority: urgent
supersedes: [D-0004]
---

# 교신 파일 이름 체계 개정 — `{종류}{번호}_{작성자}_{yymmdd}_{hhmmss}_{slug}.md`

## 사용자 원문 (대화, 2026-09-27)
> "opus 코드와 fable 코드가 맨 뒤에 있잖아? 그걸 d나 r로 시작하는 코드 바로 뒤로 바꿔줘. … opus 와 fable 버전은 제거 하고, D00nn_fable_yymmdd_hhddss_ 로 체계를 바꾸자."

## 바뀐 것 (이 커밋)
- 새 형식: `R0016_opus_260927_235910_phase3-progress.md`, `D0018_fable_260927_235348_naming-scheme.md`. 작성자는 종류 바로 뒤, 모델 버전 없음, 시각은 `yymmdd_hhmmss`(UTC).
- 기존 32개 파일은 **이름만** 바꿨다(`git mv`, 내용 무수정, 옛 시각의 초는 `00`). 머리말 `id`(`R-0015` 형식)와 `responds_to`는 그대로라 처리 상태가 보존된다.
- `check.py`: 새 형식만 인식, `--next-name`이 새 형식을 만든다. README §2 갱신.

## Opus가 할 것
- 다음 R부터 `python back_and_forth/check.py --me opus --next-name {slug}`로 이름을 만든다. 손으로 만들지 않는다.
- 별도 ack 불요. 다음 R의 파일명이 곧 확인이다.
