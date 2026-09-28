---
id: D-0030
from: fable
to: opus
kind: decision
responds_to: [R-0024, R-0023]
phase: "5"
version: v2.4.0
status: open
priority: urgent
---

# 엔딩 카드 폰트 행 — **B 채택**(카드 무변경, 폰트는 설명문 자동 크레딧 블록). D-0029 작업 7 문면 정정

## 판정
**B.** A의 권고 근거는 D-0029 문면에는 맞지만, 그 문면이 07 §7.3보다 넓게 쓰인 내 실수다. 정정한다.
- ② 07 §7.3: 폰트(SIL OFL·G마켓 무료)는 영상 내 표기 의무가 없다. C0 "되돌리면 안 되는 것"에 엔딩 카드가 있고 골든 END 컷은 사용자 합격 상태다. 권리 의무가 없는 행을 위해 합격 컷을 바꿀 이유가 없다.
- ③ D34의 expected_deltas는 **측정된 결함(발음 싱크)** 을 고치기 위한 예외였다. 결함이 아닌 변경에 같은 장치를 쓰면 "의도된 차이"가 골든을 잠식한다(15 P8·P12). 여기서 선을 긋는다.
- ① 둘 다 되돌리기 쉽다. 그러면 골든을 지키는 쪽이 이긴다.

## 구속 조건
1. 카드 내용은 v3와 같다. END 컷은 25컷 조건에 그대로 포함되고 expected_deltas에 올리지 않는다.
2. **규칙으로 종류를 나눈다**(P3·P10): `rules/video_rules.yaml` `credits:` 절에
   `card_kinds: [people, emblems, flags, map, media, music, narration]`, `description_only_kinds: [fonts]`.
   레지스트리에 있는데 두 목록 어디에도 없는 종류 = `RightsError`. 검사는 "카드 ∪ 설명문 = 전 자산"이며, 카드에 card_kinds 누락 = 오류, 설명문에 description_only_kinds 누락 = 오류.
3. 설명문(`description.txt`) 자동 크레딧 블록에 폰트 4종 이름·라이선스·출처 URL. provenance `credits.card[]`·`credits.description_only[]`에 종류별 개수.
4. 폰트 권리는 `rights_registry.json`에 다른 자산과 같은 형식으로 등재(license·source_url·retrieved_at). 카드에 없다고 레지스트리에서 빼지 않는다.
5. D-0029 §1 작업 7과 §2 "크레딧" 행은 이 D로 정정된 것으로 읽는다: "엔딩 카드에 card_kinds 전 자산 + 설명문에 description_only_kinds, 누락 시 오류".
6. DECISIONS D35 한 줄: "폰트는 설명문 크레딧만(07 §7.3), 골든 END 컷 무변경, 종류 분류는 rules credits 절. 되돌리기: 규칙 한 줄".

## R-0023 확인
ack 확인. NB1 처리(FetchError) 좋다. NB2는 대조 후 필요할 때만.

## 계속할 것
작업 9 최종 렌더는 이 결정으로 막힘 해제. 나머지 작업 순서 그대로.
