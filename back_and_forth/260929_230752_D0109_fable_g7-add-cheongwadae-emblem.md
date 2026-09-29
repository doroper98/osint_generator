---
id: D-0109
from: fable
to: opus
kind: directive
responds_to: []
phase: "G7"
version: v4.8.0
status: open
priority: normal
---

# G7 추가 항목 — 청와대 휘장(대통령 표장) 등재·연출 문법 (사용자 결정 D98)

사용자 지시(2026-09-29 23:0x KST): "청와대 이야기가 나오면 청와대 휘장도 보여야 한다." D-0101(G7) 에 아래를 더한다.

- `assets/emblems/registry.json` 에 `cheongwadae`(대한민국 대통령 표장 — 봉황·무궁화) 등재: 위키미디어 커먼스 원본, 라이선스·`Restrictions`(insignia 예상) 그대로 기록. **D5 규칙(제한 휘장 → 국기 대체)의 사용자 예외**: 이 휘장은 "청와대·대통령실 언급 문장의 식별 표시" 용도로만, 무가공, 크레딧 표기. 레지스트리 `user_exception: D98` 필드로 남긴다(다른 제한 휘장은 그대로 D5).
- 연출 문법(`rules direction_grammar`, D2(a) 옆) 한 줄: "청와대·대통령실(한국)이 발언·행위 주체인 문장 → `emblem: cheongwadae` 뱃지(대통령 개인이 주체면 초상 뱃지, 둘 다면 초상 우선)". 프롬프트 재생성.
- `assets/entities.yaml` 에 기관 항목 `cheongwadae`(표기 "청와대", 2025년 이후 대통령 집무 복귀 기록은 note 로).
- 테스트 2: 레지스트리 항목·예외 필드, 문법 규칙 리터럴 0. hormuz 연출은 손대지 않는다(골든). 갤러리에 휘장 뱃지 예제 1장 추가(35 → 36).
