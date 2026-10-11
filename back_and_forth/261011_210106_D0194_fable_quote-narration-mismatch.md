---
id: D-0194
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

# 사용자 의견 5 — 인용 따옴표와 내레이션 불일치(같은 재렌더에 포함)

사용자 원문: "이건 나레이션과 화면의 따옴표간의 내용 불일치" (`docs/handoff/reports/phaseP1/user_feedback/troop6_quote_mismatch.jpg`).

## 감독 진단(direction.yaml·script.yaml 실측)
- quote 이벤트(direction.yaml 798행 부근): `troop_numbers_6` 에 붙어 `text: 여러 역량으로`.
- 그 문장 내레이션은 "10월 7일, 앞서 본 군 대변인의 CNN 인터뷰로 주둔 사실이 공식 확인됐습니다." — 인용 문구를 말하지 않는다.
- 더해서 **번역이 두 갈래다.** 같은 CNN 발언을 원고 open_1 은 "여러 역할로", 인용 카드는 "여러 역량으로" 로 옮겼다. 한 영상에서 같은 말을 다르게 옮기면 사실 신뢰를 깎는다(C0 경계).
- "여러 역량으로" 단독은 문장 조각이라 뜻이 서지 않는다.

## 지시(결정, Fable)
1. **이번 영상**: troop_numbers_6 의 quote 이벤트를 뺀다(그 문장은 앞 장면을 가리키는 요약이라 인용을 붙일 자리가 아니다). 사용자 의견에 따른 사람 손질로 기록(`base_human_edit`, 사유 D-0194).
2. **검사(hard, 저장소 전체)**: 인용 카드 `text` 는 그 인용이 붙은 문장(start~end 구간 문장들)의 화면 원고 `text` 안에 그대로 있어야 한다(공백·문장부호 정규화 후 부분 문자열). 번역 인용도 같은 번역을 써야 한다. 어기면 연출 검증 오류 → 연출가 수정 루프로 돌아간다(필드 표 description 에도 제약을 적는다 — LLM-AP-018 교훈).
3. 이 검사를 gulf 의 나머지 인용 2개와 호르무즈·다른 프로젝트 연출에 돌려 결과 표를 보고한다. 기존 영상이 걸리면 목록만(고치지 않음).
4. D-0191~0193 과 같은 재렌더에 넣는다. 전/후 크롭에 이 장면(troop_numbers_6 구간) 추가.
